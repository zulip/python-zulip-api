import asyncio
import json
import sys
import traceback
import urllib.parse
from typing import (
    IO,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import aiohttp

import zulip

API_VERSTRING = "v1/"


class RandomExponentialBackoff(zulip.CountingBackoff):
    async def fail(self) -> None:
        super().fail()
        # Exponential growth with ratio sqrt(2); compute random delay
        # between x and 2x where x is growing exponentially
        delay_scale = int(2 ** (self.number_of_retries / 2.0 - 1)) + 1
        delay = min(delay_scale + random.randint(1, delay_scale), self.delay_cap)
        message = f"Sleeping for {delay}s [max {delay_scale * 2}] before retrying."
        try:
            logger.warning(message)
        except NameError:
            print(message)
        await asyncio.sleep(delay)


class AsyncClient:
    def __init__(self, client: zulip.Client):
        self.sync_client = client
        self.session = None
        self.retry_on_errors = client.retry_on_errors
        self.verbose = client.verbose

    def ensure_session(self) -> None:
        # Check if the session has been created already, and return
        # immediately if so.
        if self.session:
            return

        # Build a client cert object for requests
        if self.sync_client.client_cert_key is not None:
            assert (
                self.sync_client.client_cert is not None
            )  # Otherwise ZulipError near end of __init__
            client_cert = (
                self.sync_client.client_cert,
                self.sync_client.client_cert_key,
            )  # type: Union[None, str, Tuple[str, str]]
        else:
            client_cert = self.sync_client.client_cert

        # Actually construct the session
        session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.sync_client.email, self.sync_client.api_key),
            # TODO: Support overriding TLS verification
            # verify = self.tls_verification,
            # cert = client_cert,
            headers={"User-agent": self.sync_client.get_user_agent()},
        )
        self.session = session

    async def do_api_query(
        self,
        orig_request: Mapping[str, Any],
        url: str,
        method: str = "POST",
        longpolling: bool = False,
        files: Optional[List[IO[Any]]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        if files is None:
            files = []

        if longpolling:
            # When long-polling, set timeout to 90 sec as a balance
            # between a low traffic rate and a still reasonable latency
            # time in case of a connection failure.
            request_timeout = 90.0
        else:
            # Otherwise, 15s should be plenty of time.
            request_timeout = 15.0 if not timeout else timeout

        request = {}
        req_files = []

        for (key, val) in orig_request.items():
            if isinstance(val, str) or isinstance(val, str):
                request[key] = val
            else:
                request[key] = json.dumps(val)

        for f in files:
            req_files.append((f.name, f))

        self.ensure_session()
        assert self.session is not None

        query_state = {
            "had_error_retry": False,
            "request": request,
            "failures": 0,
        }  # type: Dict[str, Any]

        async def error_retry(error_string: str) -> bool:
            if not self.retry_on_errors or query_state["failures"] >= 10:
                return False
            if self.verbose:
                if not query_state["had_error_retry"]:
                    sys.stdout.write(
                        "zulip API(%s): connection error%s -- retrying."
                        % (
                            url.split(API_VERSTRING, 2)[0],
                            error_string,
                        )
                    )
                    query_state["had_error_retry"] = True
                else:
                    sys.stdout.write(".")
                sys.stdout.flush()
            query_state["request"]["dont_block"] = json.dumps(True)
            await asyncio.sleep(1)
            query_state["failures"] += 1
            return True

        def end_error_retry(succeeded: bool) -> None:
            if query_state["had_error_retry"] and self.verbose:
                if succeeded:
                    print("Success!")
                else:
                    print("Failed!")

        while True:
            try:
                if method == "GET":
                    kwarg = "params"
                else:
                    kwarg = "data"

                kwargs = {kwarg: query_state["request"]}

                if files:
                    kwargs["files"] = req_files

                # Actually make the request!
                res = await self.session.request(
                    method,
                    urllib.parse.urljoin(self.sync_client.base_url, url),
                    timeout=aiohttp.ClientTimeout(total=request_timeout),
                    **kwargs,
                )
                print(res)

                self.has_connected = True

                # On 50x errors, try again after a short sleep
                if str(res.status).startswith("5"):
                    if await error_retry(f" (server {res.status})"):
                        continue
                    # Otherwise fall through and process the error normally
            except (aiohttp.ServerTimeoutError, aiohttp.ClientSSLError) as e:
                # Timeouts are either a ServerTimeoutError or a ClientSSLError. We
                # want the later exception handlers to deal with any
                # non-timeout other SSLErrors
                if (
                    isinstance(e, aiohttp.ClientSSLError)
                    and str(e) != "The read operation timed out"
                ):
                    raise zulip.UnrecoverableNetworkError("SSL Error")
                if longpolling:
                    # When longpolling, we expect the timeout to fire,
                    # and the correct response is to just retry
                    continue
                else:
                    end_error_retry(False)
                    return {
                        "msg": f"Connection error:\n{traceback.format_exc()}",
                        "result": "connection-error",
                    }
            except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError):
                if not self.has_connected:
                    # If we have never successfully connected to the server, don't
                    # go into retry logic, because the most likely scenario here is
                    # that somebody just hasn't started their server, or they passed
                    # in an invalid site.
                    raise zulip.UnrecoverableNetworkError(
                        "cannot connect to server " + self.sync_client.base_url
                    )

                if await error_retry(""):
                    continue
                end_error_retry(False)
                return {
                    "msg": f"Connection error:\n{traceback.format_exc()}",
                    "result": "connection-error",
                }
            except Exception:
                # We'll split this out into more cases as we encounter new bugs.
                return {
                    "msg": f"Unexpected error:\n{traceback.format_exc()}",
                    "result": "unexpected-error",
                }

            status_code = -1
            try:
                async with res:
                    status = res.status
                    json_result = await res.json()
            except Exception:
                json_result = None

            if json_result is not None:
                end_error_retry(True)
                return json_result
            end_error_retry(False)
            return {
                "msg": "Unexpected error from the server",
                "result": "http-error",
                "status_code": status_code,
            }

    async def call_endpoint(
        self,
        url: Optional[str] = None,
        method: str = "POST",
        request: Optional[Dict[str, Any]] = None,
        longpolling: bool = False,
        files: Optional[List[IO[Any]]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        if request is None:
            request = dict()
        marshalled_request = {}
        for (k, v) in request.items():
            if v is not None:
                marshalled_request[k] = v
        versioned_url = API_VERSTRING + (url if url is not None else "")
        return await self.do_api_query(
            marshalled_request,
            versioned_url,
            method=method,
            longpolling=longpolling,
            files=files,
            timeout=timeout,
        )

    async def event_iter(
        self,
        event_types: Optional[List[str]] = None,
        narrow: Optional[List[List[str]]] = None,
        **kwargs: object,
    ) -> None:
        if narrow is None:
            narrow = []

        async def do_register() -> Tuple[str, int]:

            while True:
                if event_types is None:
                    res = await self.register(None, None, **kwargs)
                else:
                    res = await self.register(event_types, narrow, **kwargs)
                if "error" in res["result"]:
                    if self.verbose:
                        print("Server returned error:\n{}".format(res["msg"]))
                    await asyncio.sleep(1)
                else:
                    return (res["queue_id"], res["last_event_id"])

        queue_id = None
        # Make long-polling requests with `get_events`. Once a request
        # has received an answer, pass it to the callback before making
        # a new long-polling request.
        while True:
            if queue_id is None:
                (queue_id, last_event_id) = await do_register()

            res = await self.get_events(queue_id=queue_id, last_event_id=last_event_id)
            if "error" in res["result"]:
                if res["result"] == "http-error":
                    if self.verbose:
                        print("HTTP error fetching events -- probably a server restart")
                elif res["result"] == "connection-error":
                    if self.verbose:
                        print(
                            "Connection error fetching events -- probably server is temporarily down?"
                        )
                else:
                    if self.verbose:
                        print("Server returned error:\n{}".format(res["msg"]))
                    # Eventually, we'll only want the
                    # BAD_EVENT_QUEUE_ID check, but we check for the
                    # old string to support legacy Zulip servers.  We
                    # should remove that legacy check in 2019.
                    if res.get("code") == "BAD_EVENT_QUEUE_ID" or res["msg"].startswith(
                        "Bad event queue id:"
                    ):
                        # Our event queue went away, probably because
                        # we were asleep or the server restarted
                        # abnormally.  We may have missed some
                        # events while the network was down or
                        # something, but there's not really anything
                        # we can do about it other than resuming
                        # getting new ones.
                        #
                        # Reset queue_id to register a new event queue.
                        queue_id = None
                # Add a pause here to cover against potential bugs in this library
                # causing a DoS attack against a server when getting errors.
                # TODO: Make this back off exponentially.
                await asyncio.sleep(1)
                continue

            for event in res["events"]:
                last_event_id = max(last_event_id, int(event["id"]))
                yield event


    async def call_on_each_event(
        self,
        callback: Callable[[Dict[str, Any]], None],
        event_types: Optional[List[str]] = None,
        narrow: Optional[List[List[str]]] = None,
        **kwargs: object,
    ) -> None:
        async for event in self.event_iter(event_types, narrow, **kwargs):
            await callback(event)

    async def call_on_each_message(
        self, callback: Callable[[Dict[str, Any]], None], **kwargs: object
    ) -> None:
        async def event_callback(event: Dict[str, Any]) -> None:
            if event["type"] == "message":
                await callback(event["message"])

        await self.call_on_each_event(event_callback, ["message"], None, **kwargs)

    async def get_messages(self, message_filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        See examples/get-messages for example usage
        """
        return await self.call_endpoint(url="messages", method="GET", request=message_filters)

    async def get_events(self, **request: Any) -> Dict[str, Any]:
        """
        See the register() method for example usage.
        """
        return await self.call_endpoint(
            url="events",
            method="GET",
            longpolling=True,
            request=request,
        )

    async def register(
        self,
        event_types: Optional[Iterable[str]] = None,
        narrow: Optional[List[List[str]]] = None,
        **kwargs: object,
    ) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.register(['message'])
        {u'msg': u'', u'max_message_id': 112, u'last_event_id': -1, u'result': u'success', u'queue_id': u'1482093786:2'}
        >>> client.get_events(queue_id='1482093786:2', last_event_id=0)
        {...}
        """

        if narrow is None:
            narrow = []

        request = dict(event_types=event_types, narrow=narrow, **kwargs)

        return await self.call_endpoint(
            url="register",
            request=request,
        )

    async def deregister(self, queue_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.register(['message'])
        {u'msg': u'', u'max_message_id': 113, u'last_event_id': -1, u'result': u'success', u'queue_id': u'1482093786:3'}
        >>> client.deregister('1482093786:3')
        {u'msg': u'', u'result': u'success'}
        """
        request = dict(queue_id=queue_id)

        return await self.call_endpoint(
            url="events",
            method="DELETE",
            request=request,
            timeout=timeout,
        )

    async def send_message(self, message_data: Dict[str, Any]) -> Awaitable[Dict[str, Any]]:
        """
        See examples/send-message for example usage.
        """
        return await self.call_endpoint(
            url="messages",
            request=message_data,
        )

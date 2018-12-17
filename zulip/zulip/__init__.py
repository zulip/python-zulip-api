# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Zulip, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import json
import requests
import time
import traceback
import sys
import os
import optparse
import argparse
import platform
import random
import types
from distutils.version import LooseVersion

from six.moves.configparser import SafeConfigParser
from six.moves import urllib
import logging
import six
from typing import Any, Callable, Dict, Iterable, IO, List, Mapping, Optional, Text, Tuple, Union

__version__ = "0.5.6"

logger = logging.getLogger(__name__)

# Check that we have a recent enough version
# Older versions don't provide the 'json' attribute on responses.
assert(LooseVersion(requests.__version__) >= LooseVersion('0.12.1'))
# In newer versions, the 'json' attribute is a function, not a property
requests_json_is_function = callable(requests.Response.json)

API_VERSTRING = "v1/"

class CountingBackoff(object):
    def __init__(self, maximum_retries=10, timeout_success_equivalent=None):
        # type: (int, Optional[float]) -> None
        self.number_of_retries = 0
        self.maximum_retries = maximum_retries
        self.timeout_success_equivalent = timeout_success_equivalent
        self.last_attempt_time = 0.0

    def keep_going(self):
        # type: () -> bool
        self._check_success_timeout()
        return self.number_of_retries < self.maximum_retries

    def succeed(self):
        # type: () -> None
        self.number_of_retries = 0
        self.last_attempt_time = time.time()

    def fail(self):
        # type: () -> None
        self._check_success_timeout()
        self.number_of_retries = min(self.number_of_retries + 1,
                                     self.maximum_retries)
        self.last_attempt_time = time.time()

    def _check_success_timeout(self):
        # type: () -> None
        if (self.timeout_success_equivalent is not None and
            self.last_attempt_time != 0 and
                time.time() - self.last_attempt_time > self.timeout_success_equivalent):
            self.number_of_retries = 0

class RandomExponentialBackoff(CountingBackoff):
    def fail(self):
        # type: () -> None
        super(RandomExponentialBackoff, self).fail()
        # Exponential growth with ratio sqrt(2); compute random delay
        # between x and 2x where x is growing exponentially
        delay_scale = int(2 ** (self.number_of_retries / 2.0 - 1)) + 1
        delay = delay_scale + random.randint(1, delay_scale)
        message = "Sleeping for %ss [max %s] before retrying." % (delay, delay_scale * 2)
        try:
            logger.warning(message)
        except NameError:
            print(message)
        time.sleep(delay)

def _default_client():
    # type: () -> str
    return "ZulipPython/" + __version__

def add_default_arguments(parser, patch_error_handling=True, allow_provisioning=False):
    # type: (argparse.ArgumentParser, bool, bool) ->  argparse.ArgumentParser

    if patch_error_handling:
        def custom_error_handling(self, message):
            # type: (Any, str) -> None
            self.print_help(sys.stderr)
            self.exit(2, '{}: error: {}\n'.format(self.prog, message))
        parser.error = types.MethodType(custom_error_handling, parser)  # type: ignore # patching function

    if allow_provisioning:
        parser.add_argument('--provision',
                            action='store_true',
                            dest="provision",
                            help="install dependencies for this script (found in requirements.txt)")

    group = parser.add_argument_group('Zulip API configuration')
    group.add_argument('--site',
                       dest="zulip_site",
                       help="Zulip server URI",
                       default=None)
    group.add_argument('--api-key',
                       dest="zulip_api_key",
                       action='store')
    group.add_argument('--user',
                       dest='zulip_email',
                       help='Email address of the calling bot or user.')
    group.add_argument('--config-file',
                       action='store',
                       dest="zulip_config_file",
                       help='''Location of an ini file containing the above
                            information. (default ~/.zuliprc)''')
    group.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Provide detailed output.')
    group.add_argument('--client',
                       action='store',
                       default=None,
                       dest="zulip_client",
                       help=argparse.SUPPRESS)
    group.add_argument('--insecure',
                       action='store_true',
                       dest='insecure',
                       help='''Do not verify the server certificate.
                            The https connection will not be secure.''')
    group.add_argument('--cert-bundle',
                       action='store',
                       dest='cert_bundle',
                       help='''Specify a file containing either the
                            server certificate, or a set of trusted
                            CA certificates. This will be used to
                            verify the server's identity. All
                            certificates should be PEM encoded.''')
    group.add_argument('--client-cert',
                       action='store',
                       dest='client_cert',
                       help='''Specify a file containing a client
                            certificate (not needed for most deployments).''')
    group.add_argument('--client-cert-key',
                       action='store',
                       dest='client_cert_key',
                       help='''Specify a file containing the client
                            certificate's key (if it is in a separate
                            file).''')
    return parser

# This method might seem redundant with `add_default_arguments()`,
# except for the fact that is uses the deprecated `optparse` module.
# We still keep it for legacy support of out-of-tree bots and integrations
# depending on it.
def generate_option_group(parser, prefix=''):
    # type: (optparse.OptionParser, str) ->  optparse.OptionGroup
    logging.warning("""zulip.generate_option_group is based on optparse, which
                    is now deprecated. We recommend migrating to argparse and
                    using zulip.add_default_arguments instead.""")

    group = optparse.OptionGroup(parser, 'Zulip API configuration')
    group.add_option('--%ssite' % (prefix,),
                     dest="zulip_site",
                     help="Zulip server URI",
                     default=None)
    group.add_option('--%sapi-key' % (prefix,),
                     dest="zulip_api_key",
                     action='store')
    group.add_option('--%suser' % (prefix,),
                     dest='zulip_email',
                     help='Email address of the calling bot or user.')
    group.add_option('--%sconfig-file' % (prefix,),
                     action='store',
                     dest="zulip_config_file",
                     help='Location of an ini file containing the\nabove information. (default ~/.zuliprc)')
    group.add_option('-v', '--verbose',
                     action='store_true',
                     help='Provide detailed output.')
    group.add_option('--%sclient' % (prefix,),
                     action='store',
                     default=None,
                     dest="zulip_client",
                     help=optparse.SUPPRESS_HELP)
    group.add_option('--insecure',
                     action='store_true',
                     dest='insecure',
                     help='''Do not verify the server certificate.
                          The https connection will not be secure.''')
    group.add_option('--cert-bundle',
                     action='store',
                     dest='cert_bundle',
                     help='''Specify a file containing either the
                          server certificate, or a set of trusted
                          CA certificates. This will be used to
                          verify the server's identity. All
                          certificates should be PEM encoded.''')
    group.add_option('--client-cert',
                     action='store',
                     dest='client_cert',
                     help='''Specify a file containing a client
                          certificate (not needed for most deployments).''')
    group.add_option('--client-cert-key',
                     action='store',
                     dest='client_cert_key',
                     help='''Specify a file containing the client
                          certificate's key (if it is in a separate
                          file).''')
    return group

def init_from_options(options, client=None):
    # type: (Any, Optional[str]) -> Client

    if getattr(options, 'provision', False):
        requirements_path = os.path.abspath(os.path.join(sys.path[0], 'requirements.txt'))
        try:
            import pip
        except ImportError:
            traceback.print_exc()
            print("Module `pip` is not installed. To install `pip`, follow the instructions here: "
                  "https://pip.pypa.io/en/stable/installing/")
            sys.exit(1)
        if not pip.main(['install', '--upgrade', '--requirement', requirements_path]):
            print("{color_green}You successfully provisioned the dependencies for {script}.{end_color}".format(
                color_green='\033[92m', end_color='\033[0m',
                script=os.path.splitext(os.path.basename(sys.argv[0]))[0]))
            sys.exit(0)

    if options.zulip_client is not None:
        client = options.zulip_client
    elif client is None:
        client = _default_client()
    return Client(email=options.zulip_email, api_key=options.zulip_api_key,
                  config_file=options.zulip_config_file, verbose=options.verbose,
                  site=options.zulip_site, client=client,
                  cert_bundle=options.cert_bundle, insecure=options.insecure,
                  client_cert=options.client_cert,
                  client_cert_key=options.client_cert_key)

def get_default_config_filename():
    # type: () -> Optional[str]
    if os.environ.get("HOME") is None:
        return None

    config_file = os.path.join(os.environ["HOME"], ".zuliprc")
    if (not os.path.exists(config_file) and
            os.path.exists(os.path.join(os.environ["HOME"], ".humbugrc"))):
        raise ZulipError("The Zulip API configuration file is now ~/.zuliprc; please run:\n\n"
                         "  mv ~/.humbugrc ~/.zuliprc\n")
    return config_file

def validate_boolean_field(field):
    # type: (Optional[Text]) -> Union[bool, None]
    if not isinstance(field, str):
        return None

    field = field.lower()

    if field == "true":
        return True
    elif field == "false":
        return False
    else:
        return None

class ZulipError(Exception):
    pass

class ConfigNotFoundError(ZulipError):
    pass

class MissingURLError(ZulipError):
    pass

class Client(object):
    def __init__(self, email=None, api_key=None, config_file=None,
                 verbose=False, retry_on_errors=True,
                 site=None, client=None,
                 cert_bundle=None, insecure=None,
                 client_cert=None, client_cert_key=None):
        # type: (Optional[str], Optional[str], Optional[str], bool, bool, Optional[str], Optional[str], Optional[str], Optional[bool], Optional[str], Optional[str]) -> None
        if client is None:
            client = _default_client()

        # Normalize user-specified path
        if config_file is not None:
            config_file = os.path.abspath(os.path.expanduser(config_file))
        # Fill values from Environment Variables if not available in Constructor
        if config_file is None:
            config_file = os.environ.get("ZULIP_CONFIG")
        if api_key is None:
            api_key = os.environ.get("ZULIP_API_KEY")
        if email is None:
            email = os.environ.get("ZULIP_EMAIL")
        if site is None:
            site = os.environ.get("ZULIP_SITE")
        if client_cert is None:
            client_cert = os.environ.get("ZULIP_CERT")
        if client_cert_key is None:
            client_cert_key = os.environ.get("ZULIP_CERT_KEY")
        if cert_bundle is None:
            cert_bundle = os.environ.get("ZULIP_CERT_BUNDLE")
        if insecure is None:
            # Be quite strict about what is accepted so that users don't
            # disable security unintentionally.
            insecure_setting = os.environ.get('ZULIP_ALLOW_INSECURE')

            if insecure_setting is not None:
                insecure = validate_boolean_field(insecure_setting)

                if insecure is None:
                    raise ZulipError("The ZULIP_ALLOW_INSECURE environment "
                                     "variable is set to '{}', it must be "
                                     "'true' or 'false'"
                                     .format(insecure_setting))
        if config_file is None:
            config_file = get_default_config_filename()

        if config_file is not None and os.path.exists(config_file):
            config = SafeConfigParser()
            with open(config_file, 'r') as f:
                config.readfp(f, config_file)
            if api_key is None:
                api_key = config.get("api", "key")
            if email is None:
                email = config.get("api", "email")
            if site is None and config.has_option("api", "site"):
                site = config.get("api", "site")
            if client_cert is None and config.has_option("api", "client_cert"):
                client_cert = config.get("api", "client_cert")
            if client_cert_key is None and config.has_option("api", "client_cert_key"):
                client_cert_key = config.get("api", "client_cert_key")
            if cert_bundle is None and config.has_option("api", "cert_bundle"):
                cert_bundle = config.get("api", "cert_bundle")
            if insecure is None and config.has_option("api", "insecure"):
                # Be quite strict about what is accepted so that users don't
                # disable security unintentionally.
                insecure_setting = config.get('api', 'insecure')

                insecure = validate_boolean_field(insecure_setting)

                if insecure is None:
                    raise ZulipError("insecure is set to '{}', it must be "
                                     "'true' or 'false' if it is used in {}"
                                     .format(insecure_setting, config_file))

        elif None in (api_key, email):
            raise ConfigNotFoundError("api_key or email not specified and file %s does not exist"
                                      % (config_file,))

        assert(api_key is not None and email is not None)
        self.api_key = api_key
        self.email = email
        self.verbose = verbose
        if site is not None:
            if site.startswith("localhost"):
                site = "http://" + site
            elif not site.startswith("http"):
                site = "https://" + site
            # Remove trailing "/"s from site to simplify the below logic for adding "/api"
            site = site.rstrip("/")
            self.base_url = site
        else:
            raise MissingURLError("Missing Zulip server URL; specify via --site or ~/.zuliprc.")

        if not self.base_url.endswith("/api"):
            self.base_url += "/api"
        self.base_url += "/"
        self.retry_on_errors = retry_on_errors
        self.client_name = client

        if insecure:
            logger.warning('Insecure mode enabled. The server\'s SSL/TLS '
                           'certificate will not be validated, making the '
                           'HTTPS connection potentially insecure')
            self.tls_verification = False  # type: Union[bool, str]
        elif cert_bundle is not None:
            if not os.path.isfile(cert_bundle):
                raise ConfigNotFoundError("tls bundle '%s' does not exist"
                                          % (cert_bundle,))
            self.tls_verification = cert_bundle
        else:
            # Default behavior: verify against system CA certificates
            self.tls_verification = True

        if client_cert is None:
            if client_cert_key is not None:
                raise ConfigNotFoundError("client cert key '%s' specified, but no client cert public part provided"
                                          % (client_cert_key,))
        else:  # we have a client cert
            if not os.path.isfile(client_cert):
                raise ConfigNotFoundError("client cert '%s' does not exist"
                                          % (client_cert,))
            if client_cert_key is not None:
                if not os.path.isfile(client_cert_key):
                    raise ConfigNotFoundError("client cert key '%s' does not exist"
                                              % (client_cert_key,))
        self.client_cert = client_cert
        self.client_cert_key = client_cert_key

        self.session = None  # type: Optional[requests.Session]

        self.has_connected = False

    def ensure_session(self):
        # type: () -> None

        # Check if the session has been created already, and return
        # immediately if so.
        if self.session:
            return

        # Build a client cert object for requests
        if self.client_cert_key is not None:
            assert(self.client_cert is not None)  # Otherwise ZulipError near end of __init__
            client_cert = (self.client_cert, self.client_cert_key)  # type: Union[None, str, Tuple[str, str]]
        else:
            client_cert = self.client_cert

        # Actually construct the session
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(self.email, self.api_key)
        session.verify = self.tls_verification  # type: ignore # https://github.com/python/typeshed/pull/1504
        session.cert = client_cert
        session.headers.update({"User-agent": self.get_user_agent()})
        self.session = session

    def get_user_agent(self):
        # type: () -> str
        vendor = ''
        vendor_version = ''
        try:
            vendor = platform.system()
            vendor_version = platform.release()
        except IOError:
            # If the calling process is handling SIGCHLD, platform.system() can
            # fail with an IOError.  See http://bugs.python.org/issue9127
            pass

        if vendor == "Linux":
            vendor, vendor_version, dummy = platform.linux_distribution()
        elif vendor == "Windows":
            vendor_version = platform.win32_ver()[1]
        elif vendor == "Darwin":
            vendor_version = platform.mac_ver()[0]

        return "{client_name} ({vendor}; {vendor_version})".format(
            client_name=self.client_name,
            vendor=vendor,
            vendor_version=vendor_version,
        )

    def do_api_query(self, orig_request, url, method="POST", longpolling=False, files=None):
        # type: (Mapping[str, Any], str, str, bool, Optional[List[IO[Any]]]) -> Dict[str, Any]
        if files is None:
            files = []

        if longpolling:
            # When long-polling, set timeout to 90 sec as a balance
            # between a low traffic rate and a still reasonable latency
            # time in case of a connection failure.
            request_timeout = 90
        else:
            # Otherwise, 15s should be plenty of time.
            request_timeout = 15

        request = {}
        req_files = []

        for (key, val) in six.iteritems(orig_request):
            if isinstance(val, str) or isinstance(val, Text):
                request[key] = val
            else:
                request[key] = json.dumps(val)

        for f in files:
            req_files.append((f.name, f))

        self.ensure_session()
        assert(self.session is not None)

        query_state = {
            'had_error_retry': False,
            'request': request,
            'failures': 0,
        }  # type: Dict[str, Any]

        def error_retry(error_string):
            # type: (str) -> bool
            if not self.retry_on_errors or query_state["failures"] >= 10:
                return False
            if self.verbose:
                if not query_state["had_error_retry"]:
                    sys.stdout.write("zulip API(%s): connection error%s -- retrying." %
                                     (url.split(API_VERSTRING, 2)[0], error_string,))
                    query_state["had_error_retry"] = True
                else:
                    sys.stdout.write(".")
                sys.stdout.flush()
            query_state["request"]["dont_block"] = json.dumps(True)
            time.sleep(1)
            query_state["failures"] += 1
            return True

        def end_error_retry(succeeded):
            # type: (bool) -> None
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
                    kwargs['files'] = req_files

                # Actually make the request!
                res = self.session.request(
                    method,
                    urllib.parse.urljoin(self.base_url, url),
                    timeout=request_timeout,
                    **kwargs)

                self.has_connected = True

                # On 50x errors, try again after a short sleep
                if str(res.status_code).startswith('5'):
                    if error_retry(" (server %s)" % (res.status_code,)):
                        continue
                    # Otherwise fall through and process the python-requests error normally
            except (requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
                # Timeouts are either a Timeout or an SSLError; we
                # want the later exception handlers to deal with any
                # non-timeout other SSLErrors
                if (isinstance(e, requests.exceptions.SSLError) and
                        str(e) != "The read operation timed out"):
                    raise
                if longpolling:
                    # When longpolling, we expect the timeout to fire,
                    # and the correct response is to just retry
                    continue
                else:
                    end_error_retry(False)
                    return {'msg': "Connection error:\n%s" % traceback.format_exc(),
                            "result": "connection-error"}
            except requests.exceptions.ConnectionError:
                if not self.has_connected:
                    # If we have never successfully connected to the server, don't
                    # go into retry logic, because the most likely scenario here is
                    # that somebody just hasn't started their server, or they passed
                    # in an invalid site.
                    raise ZulipError('cannot connect to server ' + self.base_url)

                if error_retry(""):
                    continue
                end_error_retry(False)
                return {'msg': "Connection error:\n%s" % traceback.format_exc(),
                        "result": "connection-error"}
            except Exception:
                # We'll split this out into more cases as we encounter new bugs.
                return {'msg': "Unexpected error:\n%s" % traceback.format_exc(),
                        "result": "unexpected-error"}

            try:
                if requests_json_is_function:
                    json_result = res.json()
                else:
                    json_result = res.json
            except Exception:
                json_result = None

            if json_result is not None:
                end_error_retry(True)
                return json_result
            end_error_retry(False)
            return {'msg': "Unexpected error from the server", "result": "http-error",
                    "status_code": res.status_code}

    def call_endpoint(self, url=None, method="POST", request=None, longpolling=False, files=None):
        # type: (Optional[str], str, Optional[Dict[str, Any]], bool, Optional[List[IO[Any]]]) -> Dict[str, Any]
        if request is None:
            request = dict()
        marshalled_request = {}
        for (k, v) in request.items():
            if v is not None:
                marshalled_request[k] = v
        versioned_url = API_VERSTRING + (url if url is not None else "")
        return self.do_api_query(marshalled_request, versioned_url, method=method,
                                 longpolling=longpolling, files=files)

    def call_on_each_event(self, callback, event_types=None, narrow=None):
        # type: (Callable[[Dict[str, Any]], None], Optional[List[str]], Optional[List[List[str]]]) -> None
        if narrow is None:
            narrow = []

        def do_register():
            # type: () -> Tuple[str, int]
            while True:
                if event_types is None:
                    res = self.register()
                else:
                    res = self.register(event_types=event_types, narrow=narrow)

                if 'error' in res['result']:
                    if self.verbose:
                        print("Server returned error:\n%s" % res['msg'])
                    time.sleep(1)
                else:
                    return (res['queue_id'], res['last_event_id'])

        queue_id = None
        # Make long-polling requests with `get_events`. Once a request
        # has received an answer, pass it to the callback and before
        # making a new long-polling request.
        while True:
            if queue_id is None:
                (queue_id, last_event_id) = do_register()

            res = self.get_events(queue_id=queue_id, last_event_id=last_event_id)
            if 'error' in res['result']:
                if res["result"] == "http-error":
                    if self.verbose:
                        print("HTTP error fetching events -- probably a server restart")
                elif res["result"] == "connection-error":
                    if self.verbose:
                        print("Connection error fetching events -- probably server is temporarily down?")
                else:
                    if self.verbose:
                        print("Server returned error:\n%s" % res["msg"])
                    # Eventually, we'll only want the
                    # BAD_EVENT_QUEUE_ID check, but we check for the
                    # old string to support legacy Zulip servers.  We
                    # should remove that legacy check in 2019.
                    if res.get("code") == "BAD_EVENT_QUEUE_ID" or res["msg"].startswith("Bad event queue id:"):
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
                time.sleep(1)
                continue

            for event in res['events']:
                last_event_id = max(last_event_id, int(event['id']))
                callback(event)

    def call_on_each_message(self, callback):
        # type: (Callable[[Dict[str, Any]], None]) -> None
        def event_callback(event):
            # type: (Dict[str, Any]) -> None
            if event['type'] == 'message':
                callback(event['message'])
        self.call_on_each_event(event_callback, ['message'])

    def get_messages(self, message_filters):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            See examples/get-messages for example usage
        '''
        return self.call_endpoint(
            url='messages',
            method='GET',
            request=message_filters
        )

    def get_raw_message(self, message_id):
        # type: (int) -> Dict[str, str]
        '''
            See examples/get-raw-message for example usage
        '''
        return self.call_endpoint(
            url='messages/{}'.format(message_id),
            method='GET'
        )

    def send_message(self, message_data):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            See examples/send-message for example usage.
        '''
        return self.call_endpoint(
            url='messages',
            request=message_data,
        )

    def upload_file(self, file):
        # type: (IO[Any]) -> Dict[str, Any]
        '''
            See examples/upload-file for example usage.
        '''
        return self.call_endpoint(
            url='user_uploads',
            files=[file]
        )

    def update_message(self, message_data):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            See examples/edit-message for example usage.
        '''
        return self.call_endpoint(
            url='messages/%d' % (message_data['message_id'],),
            method='PATCH',
            request=message_data,
        )

    def delete_message(self, message_id):
        # type: (int) -> Dict[str, Any]
        '''
            See examples/delete-message for example usage.
        '''
        return self.call_endpoint(
            url='messages/{}'.format(message_id),
            method='DELETE'
        )

    def update_message_flags(self, update_data):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            See examples/update-flags for example usage.
        '''
        return self.call_endpoint(
            url='messages/flags',
            method='POST',
            request=update_data
        )

    def mark_all_as_read(self):
        # type: () -> Dict[str, Any]
        '''
            Example usage:

            >>> client.mark_all_as_read()
            {'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='mark_all_as_read',
            method='POST',
        )

    def mark_stream_as_read(self, stream_id):
        # type: (int) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.mark_stream_as_read(42)
            {'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='mark_stream_as_read',
            method='POST',
            request={'stream_id': stream_id},
        )

    def mark_topic_as_read(self, stream_id, topic_name):
        # type: (int, str) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.mark_all_as_read(42, 'new coffee machine')
            {'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='mark_topic_as_read',
            method='POST',
            request={
                'stream_id': stream_id,
                'topic_name': topic_name,
            },
        )

    def get_message_history(self, message_id):
        # type: (int) -> Dict[str, Any]
        '''
            See examples/message-history for example usage.
        '''
        return self.call_endpoint(
            url='messages/{}/history'.format(message_id),
            method='GET'
        )

    def add_reaction(self, reaction_data):
        # type: (Dict[str, str]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.add_emoji_reaction({
                'message_id': '100',
                'emoji_name': 'joy',
                'emoji_code': '1f602',
                'emoji_type': 'unicode_emoji'
            })
            {'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='messages/{}/reactions'.format(reaction_data['message_id']),
            method='POST',
        )

    def remove_reaction(self, reaction_data):
        # type: (Dict[str, str]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.remove_reaction({
                'message_id': '100',
                'emoji_name': 'joy',
                'emoji_code': '1f602',
                'emoji_type': 'unicode_emoji'
            })
            {'msg': '', 'result': 'success'}
        '''
        return self.call_endpoint(
            url='messages/{}/reactions'.format(reaction_data['message_id']),
            method='DELETE',
            request=reaction_data,
        )

    def get_realm_emoji(self):
        # type: () -> Dict[str, Any]
        '''
            See examples/realm-emoji for example usage.
        '''
        return self.call_endpoint(
            url='realm/emoji',
            method='GET'
        )

    def get_realm_filters(self):
        # type: () -> Dict[str, Any]
        '''
            Example usage:

            >>> client.get_realm_filters()
            {'result': 'success', 'msg': '', 'filters': [['#(?P<id>[0-9]+)', 'https://github.com/zulip/zulip/issues/%(id)s', 1]]}
        '''
        return self.call_endpoint(
            url='realm/filters',
            method='GET',
        )

    def add_realm_filter(self, pattern, url_format_string):
        # type: (str, str) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.add_realm_filter('#(?P<id>[0-9]+)', 'https://github.com/zulip/zulip/issues/%(id)s')
            {'result': 'success', 'msg': '', 'id': 42}
        '''
        return self.call_endpoint(
            url='realm/filters',
            method='POST',
            request={
                'pattern': pattern,
                'url_format_string': url_format_string,
            },
        )

    def remove_realm_filter(self, filter_id):
        # type: (int) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.remove_realm_filter(42)
            {'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='realm/filters/{}'.format(filter_id),
            method='DELETE',
        )

    def get_server_settings(self):
        # type: () -> Dict[str, Any]
        '''
            Example usage:

            >>> client.get_server_settings()
            {'msg': '', 'result': 'success', 'zulip_version': '1.9.0', 'push_notifications_enabled': False, ...}
        '''
        return self.call_endpoint(
            url='server_settings',
            method='GET',
        )

    def get_events(self, **request):
        # type: (**Any) -> Dict[str, Any]
        '''
            See the register() method for example usage.
        '''
        return self.call_endpoint(
            url='events',
            method='GET',
            longpolling=True,
            request=request,
        )

    def register(self, event_types=None, narrow=None, **kwargs):
        # type: (Optional[Iterable[str]], Optional[List[List[str]]], **Any) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.register(['message'])
            {u'msg': u'', u'max_message_id': 112, u'last_event_id': -1, u'result': u'success', u'queue_id': u'1482093786:2'}
            >>> client.get_events(queue_id='1482093786:2', last_event_id=0)
            {...}
        '''

        if narrow is None:
            narrow = []

        request = dict(
            event_types=event_types,
            narrow=narrow,
            **kwargs
        )

        return self.call_endpoint(
            url='register',
            request=request,
        )

    def deregister(self, queue_id):
        # type: (str) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.register(['message'])
            {u'msg': u'', u'max_message_id': 113, u'last_event_id': -1, u'result': u'success', u'queue_id': u'1482093786:3'}
            >>> client.deregister('1482093786:3')
            {u'msg': u'', u'result': u'success'}
        '''
        request = dict(queue_id=queue_id)

        return self.call_endpoint(
            url="events",
            method="DELETE",
            request=request,
        )

    def get_profile(self, request=None):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.get_profile()
            {u'user_id': 5, u'full_name': u'Iago', u'short_name': u'iago', ...}
        '''
        return self.call_endpoint(
            url='users/me',
            method='GET',
            request=request,
        )

    def get_user_presence(self, email):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.get_user_presence('iago@zulip.com')
            {'presence': {'website': {'timestamp': 1486799122, 'status': 'active'}}, 'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='users/%s/presence' % (email,),
            method='GET',
        )

    def update_presence(self, request):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.update_presence({
                    status='active',
                    ping_only=False,
                    new_user_input=False,
                })
                {'result': 'success', 'server_timestamp': 1333649180.7073195, 'presences': {'iago@zulip.com': { ... }}, 'msg': ''}
        '''
        return self.call_endpoint(
            url='users/me/presence',
            method='POST',
            request=request,
        )

    def get_streams(self, **request):
        # type: (**Any) -> Dict[str, Any]
        '''
            See examples/get-public-streams for example usage.
        '''
        return self.call_endpoint(
            url='streams',
            method='GET',
            request=request,
        )

    def update_stream(self, stream_data):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            See examples/edit-stream for example usage.
        '''

        return self.call_endpoint(
            url='streams/{}'.format(stream_data['stream_id']),
            method='PATCH',
            request=stream_data,
        )

    def delete_stream(self, stream_id):
        # type: (int) -> Dict[str, Any]
        '''
            See examples/delete-stream for example usage.
        '''
        return self.call_endpoint(
            url='streams/{}'.format(stream_id),
            method='DELETE',
        )

    def get_members(self, request=None):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        '''
            See examples/list-members for example usage.
        '''
        return self.call_endpoint(
            url='users',
            method='GET',
            request=request,
        )

    def get_alert_words(self):
        # type: () -> Dict[str, Any]
        '''
            See examples/alert-words for example usage.
        '''
        return self.call_endpoint(
            url='users/me/alert_words',
            method='GET'
        )

    def add_alert_words(self, alert_words):
        # type: (List[str]) -> Dict[str, Any]
        '''
            See examples/alert-words for example usage.
        '''
        return self.call_endpoint(
            url='users/me/alert_words',
            method='POST',
            request={
                'alert_words': alert_words
            }
        )

    def remove_alert_words(self, alert_words):
        # type: (List[str]) -> Dict[str, Any]
        '''
            See examples/alert-words for example usage.
        '''
        return self.call_endpoint(
            url='users/me/alert_words',
            method='DELETE',
            request={
                'alert_words': alert_words
            }
        )

    def list_subscriptions(self, request=None):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        '''
            See examples/list-subscriptions for example usage.
        '''
        return self.call_endpoint(
            url='users/me/subscriptions',
            method='GET',
            request=request,
        )

    def add_subscriptions(self, streams, **kwargs):
        # type: (Iterable[Dict[str, Any]], **Any) -> Dict[str, Any]
        '''
            See examples/subscribe for example usage.
        '''
        request = dict(
            subscriptions=streams,
            **kwargs
        )

        return self.call_endpoint(
            url='users/me/subscriptions',
            request=request,
        )

    def remove_subscriptions(self, streams, principals=None):
        # type: (Iterable[str], Optional[Iterable[str]]) -> Dict[str, Any]
        '''
            See examples/unsubscribe for example usage.
        '''
        if principals is None:
            principals = []

        request = dict(
            subscriptions=streams,
            principals=principals
        )
        return self.call_endpoint(
            url='users/me/subscriptions',
            method='DELETE',
            request=request,
        )

    def mute_topic(self, request):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            See examples/mute-topic for example usage.
        '''
        return self.call_endpoint(
            url='users/me/subscriptions/muted_topics',
            method='PATCH',
            request=request
        )

    def update_subscription_settings(self, subscription_data):
        # type: (List[Dict[str, Any]]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.update_subscription_settings([{
                'stream_id': 1,
                'property': 'pin_to_top',
                'value': True
            },
            {
                'stream_id': 3,
                'property': 'color',
                'value': 'f00'
            }])
            {'result': 'success', 'msg': '', 'subscription_data': [{...}, {...}]}
        '''
        return self.call_endpoint(
            url='users/me/subscriptions/properties',
            method='POST',
            request={'subscription_data': subscription_data}
        )

    def update_notification_settings(self, notification_settings):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.update_notification_settings({
                'enable_stream_push_notifications': True,
                'enable_offline_push_notifications': False,
            })
            {'enable_offline_push_notifications': False, 'enable_stream_push_notifications': True, 'msg': '', 'result': 'success'}
        '''
        return self.call_endpoint(
            url='settings/notifications',
            method='PATCH',
            request=notification_settings,
        )

    def get_stream_id(self, stream):
        # type: (str) -> Dict[str, Any]
        '''
            Example usage: client.get_stream_id('devel')
        '''
        stream_encoded = urllib.parse.quote(stream, safe='')
        url = 'get_stream_id?stream=%s' % (stream_encoded,)
        return self.call_endpoint(
            url=url,
            method='GET',
            request=None,
        )

    def get_stream_topics(self, stream_id):
        # type: (int) -> Dict[str, Any]
        '''
            See examples/get-stream-topics for example usage.
        '''
        return self.call_endpoint(
            url='users/me/{}/topics'.format(stream_id),
            method='GET'
        )

    def get_user_groups(self):
        # type: () -> Dict[str, Any]
        '''
            Example usage:
            >>> client.get_user_groups()
            {'result': 'success', 'msg': '', 'user_groups': [{...}, {...}]}
        '''
        return self.call_endpoint(
            url='user_groups',
            method='GET',
        )

    def create_user_group(self, group_data):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:
            >>> client.create_user_group({
                'name': 'marketing',
                'description': "Members of ACME Corp.'s marketing team.",
                'members': [4, 8, 15, 16, 23, 42],
            })
            {'msg': '', 'result': 'success'}
        '''
        return self.call_endpoint(
            url='user_groups/create',
            method='POST',
            request=group_data,
        )

    def update_user_group(self, group_data):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.update_user_group({
                'group_id': 1,
                'name': 'marketing',
                'description': "Members of ACME Corp.'s marketing team.",
            })
            {'description': 'Description successfully updated.', 'name': 'Name successfully updated.', 'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='user_groups/{}'.format(group_data['group_id']),
            method='PATCH',
            request=group_data,
        )

    def remove_user_group(self, group_id):
        # type: (int) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.remove_user_group(42)
            {'msg': '', 'result': 'success'}
        '''
        return self.call_endpoint(
            url='user_groups/{}'.format(group_id),
            method='DELETE',
        )

    def update_user_group_members(self, group_data):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.update_user_group_members({
                'delete': [4, 8, 15],
                'add': [16, 23, 42],
            })
            {'msg': '', 'result': 'success'}
        '''
        return self.call_endpoint(
            url='user_groups/{}/members'.format(group_data['group_id']),
            method='POST',
            request=group_data,
        )

    def get_subscribers(self, **request):
        # type: (**Any) -> Dict[str, Any]
        '''
            Example usage: client.get_subscribers(stream='devel')
        '''
        response = self.get_stream_id(request['stream'])
        if response['result'] == 'error':
            return response

        stream_id = response['stream_id']
        url = 'streams/%d/members' % (stream_id,)
        return self.call_endpoint(
            url=url,
            method='GET',
            request=request,
        )

    def render_message(self, request=None):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.render_message(request=dict(content='foo **bar**'))
            {u'msg': u'', u'rendered': u'<p>foo <strong>bar</strong></p>', u'result': u'success'}
        '''
        return self.call_endpoint(
            url='messages/render',
            method='POST',
            request=request,
        )

    def create_user(self, request=None):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        '''
            See examples/create-user for example usage.
        '''
        return self.call_endpoint(
            method='POST',
            url='users',
            request=request,
        )

    def update_storage(self, request):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.update_storage({'storage': {"entry 1": "value 1", "entry 2": "value 2", "entry 3": "value 3"}})
            >>> client.get_storage({'keys': ["entry 1", "entry 3"]})
            {'result': 'success', 'storage': {'entry 1': 'value 1', 'entry 3': 'value 3'}, 'msg': ''}
        '''
        return self.call_endpoint(
            url='bot_storage',
            method='PUT',
            request=request,
        )

    def get_storage(self, request=None):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        '''
            Example usage:

            >>> client.update_storage({'storage': {"entry 1": "value 1", "entry 2": "value 2", "entry 3": "value 3"}})
            >>> client.get_storage()
            {'result': 'success', 'storage': {"entry 1": "value 1", "entry 2": "value 2", "entry 3": "value 3"}, 'msg': ''}
            >>> client.get_storage({'keys': ["entry 1", "entry 3"]})
            {'result': 'success', 'storage': {'entry 1': 'value 1', 'entry 3': 'value 3'}, 'msg': ''}
        '''
        return self.call_endpoint(
            url='bot_storage',
            method='GET',
            request=request,
        )

    def set_typing_status(self, request):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        '''
            Example usage:
            >>> client.set_typing_status({
                'op': 'start',
                'to': ['iago@zulip.com', 'polonius@zulip.com'],
            })
            {'result': 'success', 'msg': ''}
        '''
        return self.call_endpoint(
            url='typing',
            method='POST',
            request=request
        )

class ZulipStream(object):
    """
    A Zulip stream-like object
    """

    def __init__(self, type, to, subject, **kwargs):
        # type: (str, str, str,  **Any) -> None
        self.client = Client(**kwargs)
        self.type = type
        self.to = to
        self.subject = subject

    def write(self, content):
        # type: (str) -> None
        message = {"type": self.type,
                   "to": self.to,
                   "subject": self.subject,
                   "content": content}
        self.client.send_message(message)

    def flush(self):
        # type: () -> None
        pass

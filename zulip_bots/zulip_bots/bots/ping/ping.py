import requests
import time
from typing import Any, Dict, Optional

class PingHandler:
    PING_API = "https://check-host.net/check-ping"
    RESULT_API = "https://check-host.net/check-result/{request_id}"

    INITIAL_MESSAGE = "Checking availability of `{host}`, please wait..."
    EMPTY_HOST_MESSAGE = "The hostname is empty."
    INVALID_HOST_MESSAGE = "The hostname `{host}` is invalid."

    NODE_DATA = "{country}, {city} ({ip_address})"
    NODE_RESPONSES = {
        'UNKNOWN': ":cross_mark: {node_data} – Unknown host",
        'OK': ":heavy_check_mark: {node_data}",
        'MALFORMED': ":cross_mark: {node_data} – Malformed reply",
        'TIMEOUT': ":cross_mark: {node_data} – Timed out"
    }
    RESPONSE_MESSAGE = "Ping results for `{host}`:\n\n" \
                       "{node_responses}\n\n" \
                       "You can see the full report here: {link}."

    def usage(self) -> str:
        return '''
        This bot allows users to check availability of a given hostname
        or IP address across 10 random locations.
        '''

    def help(self, bot_handler: Any) -> str:
        return "Please enter a hostname or IP address."

    def ping(self, host: str) -> Any:
        response = requests.get(self.PING_API,
                                params={'host': host, 'max_nodes': '10'},
                                headers={'Accept': 'application/json'})
        return response.json()

    def get_ping_result(self, request_id: str) -> Any:
        # Waiting for the results to load for a maximum of 60 seconds.
        for i in range(20):
            time.sleep(3)
            response = requests.get(self.RESULT_API.format(request_id=request_id),
                                    headers={'Accept': 'application/json'})
            if None not in response.json():
                break

        return response.json()

    def render_node_response(self, node_data: str, status: str) -> str:
        rendered_node_data = self.NODE_DATA.format(country=node_data[1],
                                                   city=node_data[2],
                                                   ip_address=node_data[3])
        return self.NODE_RESPONSES[status].format(node_data=rendered_node_data)

    def get_node_response(self, node_data: str, ping_results: str) -> Optional[str]:
        # The node is unreachable, skipping it.
        if ping_results == [None, {'message': "Network is unreachable"}]:
            return None

        # The node is still performing the check, skipping it.
        elif ping_results is None:
            return None

        # The node is unable to resolve the domain name.
        elif ping_results == [[None]]:
            return self.render_node_response(node_data, status='UNKNOWN')

        statuses = [result[0] for result in ping_results[0]]

        # At least one ping was successful.
        if 'OK' in statuses:
            return self.render_node_response(node_data, status='OK')

        # At least one ping got a malformed reply.
        elif 'MALFORMED' in statuses:
            return self.render_node_response(node_data, status='MALFORMED')

        # All pings timed out.
        else:
            return self.render_node_response(node_data, status='TIMEOUT')

    def get_response(self, host: str, ping_json: Any, result_json: Any) -> str:
        response_data = {}
        for node, node_data in ping_json['nodes'].items():
            node_response = self.get_node_response(node_data=node_data,
                                                   ping_results=result_json[node])
            if node_response:
                response_data[node] = node_response

        node_responses = '\n'.join(response_data.values())
        return self.RESPONSE_MESSAGE.format(host=host,
                                            node_responses=node_responses,
                                            link=ping_json['permanent_link'])

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        if message['content'] == 'help':
            bot_handler.send_reply(message, self.help(bot_handler))
            return None

        host = message['content']
        if not host:
            bot_handler.send_reply(message, self.EMPTY_HOST_MESSAGE)
            return None

        ping_json = self.ping(host)
        if ping_json.get('error') == 'invalid_url':
            bot_handler.send_reply(message,
                                   self.INVALID_HOST_MESSAGE.format(host=host))
            return None

        bot_handler.send_reply(message, self.INITIAL_MESSAGE.format(host=host))
        result_json = self.get_ping_result(request_id=ping_json['request_id'])
        response = self.get_response(host, ping_json, result_json)
        bot_handler.send_reply(message, response)

handler_class = PingHandler

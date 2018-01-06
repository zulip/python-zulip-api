from typing import Any
import requests
import json
import socket

class JoinmeHandler(object):
    def usage(self) -> str:
        return '''
         A bot that will post a link to joinme call. Mention the bot and it will give out instructions.
        '''

    def handle_message(self, message: Any, bot_handler: Any) -> None:
        if 'ZISSHUDBUNIq' not in message['content']:
            payload = {'client_id': 'fvg6qhpans4z2jryq45crb69', 'scope': 'user_info scheduler start_meeting',
                       'redirect_uri': 'https://developer.join.me/io-docs/oauth2callback', 'state': 'ZISSHUDBUNIq', 'response_type': 'code'}
            r = requests.get('https://secure.join.me/api/public/v1/auth/oauth2', params=payload)
            content = "Please click the link below to log in and authorise Joinme:\n {} \nAnd please copy and " \
                      "send the url shown in browser after clicking accept. Don't forget to @ me!".format(r.url)
        else:
            authorisation_code = message['content']
            authorisation_code = authorisation_code.split('=')
            authorisation_code = authorisation_code[1].split('&')

            payload = {"client_id": "fvg6qhpans4z2jryq45crb69", "client_secret": "3BsfF8wRe5", "code": authorisation_code[0], "redirect_uri": "https://developer.join.me/io-docs/oauth2callback", "grant_type": "authorization_code"}
            req = requests.post('https://secure.join.me/api/public/v1/auth/token', data = payload)

            token = json.loads(req.text)
            if 'error' in token:
                if token['error'] == 'invalid_authorization_code':
                    content = 'The session has expired. Please start again by @Joinme bot.'

            else:
                token = token['access_token']
                s = socket.gethostbyname(socket.gethostname())

                headers = {'Authorization': 'Bearer {}'.format(token), 'Content-Type': 'application/json', 'X-Originating-Ip': s}
                data = {"startWithPersonalUrl": 'false'}

                req = requests.post('https://api.join.me/v1/meetings/start', headers = headers, data = json.dumps(data))
                req = req.json()
                content = "Click this link to join the call:\n {}".format(req['presenterLink'])
        bot_handler.send_reply(message, content)

handler_class = JoinmeHandler


# See readme.md for instructions on running this code.

from typing import Any
import requests
import json
import socket

class JoinmeHandler(object):
    def usage(self) -> str:
        return '''
        A bot that will post a link to joinme call.
        '''

    def handle_message(self, message: Any, bot_handler: Any) -> None:
        if 'ZISSHUDBUNIq' not in message['content']:
            payload = {'client_id':'fvg6qhpans4z2jryq45crb69', 'scope':'user_info scheduler start_meeting',
            'redirect_uri':'https://developer.join.me/io-docs/oauth2callback', 'state':'ZISSHUDBUNIq', 'response_type':'code'}
            r = requests.get('https://secure.join.me/api/public/v1/auth/oauth2', params=payload)
            content = "Please click the link below to log in and authorise Joinme:\n {} \nAnd please copy and send the url shown in browser after clicking accept. Don't forget to @ me!".format(r.url) # type: str
            bot_handler.send_reply(message, content)
        if 'ZISSHUDBUNIq' in message['content']:
            code1 = message['content']
            code1 = code1.split('=')
            code2 = code1[1].split('&')

            pay1 ={
                    "client_id": "fvg6qhpans4z2jryq45crb69",
                    "client_secret": "3BsfF8wRe5",
                    "code": code2[0],
                    "redirect_uri" : "https://developer.join.me/io-docs/oauth2callback",
                    "grant_type": "authorization_code"
                  }
            r1 = requests.post('https://secure.join.me/api/public/v1/auth/token', data = pay1)

            a = json.loads(r1.text)
            if a['error'] == 'invalid_authorization_code':
                content = 'The session has expired. Please start again by @Joinme bot.'
                bot_handler.send_reply(message, content)
            else:
                a = a['access_token']
                s = socket.gethostbyname(socket.gethostname())

                headers = {
                            'Authorization' : 'Bearer {}'.format(a),
                            'Content-Type' : 'application/json',
                            'X-Originating-Ip' : s
                           }
                data2 = {"startWithPersonalUrl":'false'}

                r2 = requests.post('https://api.join.me/v1/meetings/start', headers = headers, data = json.dumps(data2))
                re = r2.json()#dict
                content = "Click this link to join the call:\n {}".format(re['presenterLink'])
                bot_handler.send_reply(message, content)

handler_class = JoinmeHandler

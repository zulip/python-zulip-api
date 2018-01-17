import requests
import json
import socket

payload = {'client_id':'fvg6qhpans4z2jryq45crb69', 'scope':'user_info scheduler start_meeting',
'redirect_uri':'https://developer.join.me/io-docs/oauth2callback', 'state':'ABCD', 'response_type':'code'}
r = requests.get('https://secure.join.me/api/public/v1/auth/oauth2', params=payload)
print(r)
print(r.url)
#print('Please click the link below to log in and authorise Joinme:\n {}'.format(r.url))
code1 = input('Please copy and paste the url shown in browser after clicking accept: ')
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
print("Click this link to join the call:\n {}".format(re['presenterLink']))

import requests
from typing import Dict, Any, Tuple, Union

class SusiHandler(object):
    '''
    Susi AI Bot
    To create and know more of SUSI skills go to `https://skills.susi.ai/`
    '''

    def usage(self) -> str:
        return '''
    Hi, I am Susi, people generally ask me these questions:
    ```
    What is the exchange rate of USD to BTC
    How to cook biryani
    draw a card
    word starting with m and ending with v
    question me
    random GIF
    image of a bird
    flip a coin
    let us play
    who is Albert Einstein
    search wikipedia for artificial intelligence
    when is christmas
    what is hello in french
    name a popular movie
    news
    tell me a joke
    buy a dress
    currency of singapore
    distance between india and singapore
    tell me latest phone by LG
    ```
        '''
    def markdown_table_header(self, headers: List[str]):
        header_markdown = ''
        for heading in headers:
            header_markdown += '| ' + heading + ' '
        header_markdown += '\n'
        for heading in headers:
            header_markdown += '|' + '------' + ' '
        header_markdown += '\n'
        return header_markdown

    def markdown_table_body(self, table_data: List[str]):
        body_markdown = ''
        for item in table_data:
            if item[columns[0]]:
                column_first = item[columns[0]] if (type(item[columns[0]]) is str) else item[columns[0]][0]
                column_second = item[columns[1]] if (type(item[columns[1]]) is str) else item[columns[1]][0]
                column_third = item[columns[2]] if (type(item[columns[2]]) is str) else item[columns[2]][0]
                msg = '| ' + column_first + ' | ' + column_second + ' | ' + column_third + '| '
                body_markdown = body_markdown + msg + '\n'
        return body_markdown
        
    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        msg = message['content']
        if msg == 'help' or msg == '':
            bot_handler.send_reply(message, self.usage())
            return
        reply = requests.get('https://api.susi.ai/susi/chat.json', params=dict(q=msg))
        try:
            data = reply.json()
            actions = data['answers'][0]['actions']
            answer = ''
            for action in actions:
                if action['type'] == 'answer':
                    answer += action['expression'] + '\n'
                elif action['type'] == 'anchor':
                    text = action['text']
                    link = action['link']
                    answer += '[' + text + '](' + link + ')' + '\n'
                elif action['type'] == 'table':
                    table_data = data['answers'][0]['data']
                    msg = ''
                    columns = list(action['columns'].keys())
                    # using markdown make a table
                    answer += markdown_table_header(list(action['columns'].values()))
                    answer += markdown_table_body(table_data)
                    answer += '\n'
        except Exception as e:
            answer = 'I don\'t understand. Can you rephrase?'
        bot_handler.send_reply(message, answer)

handler_class = SusiHandler

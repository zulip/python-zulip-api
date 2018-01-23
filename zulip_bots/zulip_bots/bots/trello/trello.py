from typing import Any, List

import requests

supported_commands = [
    ('help', 'Get the bot usage information.'),
    ('list-commands', 'Get information about the commands supported by the bot.'),
    ('get-all-boards', 'Get all the boards under the configured account.'),
    ('get-all-cards <board_id>', 'Get all the cards in the given board.'),
    ('get-all-checklists <card_id>', 'Get all the checklists in the given card.'),
    ('get-all-lists <board_id>', 'Get all the lists in the given board.')
]

INVALID_ARGUMENTS_ERROR_MESSAGE = 'Invalid Arguments.'
RESPONSE_ERROR_MESSAGE = 'Invalid Response. Please check configuration and parameters.'

class TrelloHandler(object):
    def initialize(self, bot_handler: Any) -> None:
        self.config_info = bot_handler.get_config_info('trello')
        self.api_key = self.config_info['api_key']
        self.access_token = self.config_info['access_token']
        self.user_name = self.config_info['user_name']

        self.auth_params = {
            'key': self.api_key,
            'token': self.access_token
        }

        self.check_access_token(bot_handler)

    def check_access_token(self, bot_handler: Any) -> None:
        test_query_response = requests.get('https://api.trello.com/1/members/{}/'.format(self.user_name),
                                           params=self.auth_params)

        if test_query_response.text == 'invalid key':
            bot_handler.quit('Invalid Credentials. Please see doc.md to find out how to get them.')

    def usage(self) -> str:
        return '''
        This interactive bot can be used to interact with Trello.

        Use `list-commands` to get information about the supported commands.
        '''

    def handle_message(self, message: Any, bot_handler: Any) -> None:
        content = message['content'].strip()

        if content == '':
            bot_handler.send_reply(message, 'Empty Query')
            return
        elif content.lower() == 'help':
            bot_handler.send_reply(message, self.usage())
            return

        if content.lower() == 'list-commands':
            bot_reply = self.get_all_supported_commands()
        elif content.lower() == 'get-all-boards':
            bot_reply = self.get_all_boards()
        else:
            content = content.split()
            content[0] = content[0].lower()

            if content[0] == 'get-all-cards':
                bot_reply = self.get_all_cards(content)
            elif content[0] == 'get-all-checklists':
                bot_reply = self.get_all_checklists(content)
            elif content[0] == 'get-all-lists':
                bot_reply = self.get_all_lists(content)
            else:
                bot_reply = 'Command not supported'

        bot_handler.send_reply(message, bot_reply)

    def get_all_supported_commands(self) -> str:
        bot_response = '**Commands:** \n'
        for index, (command, desc) in enumerate(supported_commands):
            bot_response += '{}. **{}**: {}\n'.format(index + 1, command, desc)

        return bot_response

    def get_all_boards(self) -> str:
        get_board_ids_url = 'https://api.trello.com/1/members/{}/'.format(self.user_name)
        board_ids_response = requests.get(get_board_ids_url, params=self.auth_params)

        try:
            boards = board_ids_response.json()['idBoards']
            bot_response = '**Boards:** \n' + self.get_board_descs(boards)

        except (KeyError, ValueError, TypeError):
            return RESPONSE_ERROR_MESSAGE

        return bot_response

    def get_board_descs(self, boards: List[str]) -> str:
        bot_response = ''
        get_board_desc_url = 'https://api.trello.com/1/boards/{}/'
        for index, board in enumerate(boards):
            board_desc_response = requests.get(get_board_desc_url.format(board), params=self.auth_params)

            board_data = board_desc_response.json()
            bot_response += '{}.[{}]({}) (`{}`)\n'.format(index + 1, board_data['name'], board_data['url'],
                                                          board_data['id'])

        return bot_response

    def get_all_cards(self, content: List[str]) -> str:
        if len(content) != 2:
            return INVALID_ARGUMENTS_ERROR_MESSAGE

        board_id = content[1]
        get_cards_url = 'https://api.trello.com/1/boards/{}/cards'.format(board_id)
        cards_response = requests.get(get_cards_url, params=self.auth_params)

        try:
            cards = cards_response.json()
            bot_response = '**Cards:** \n'
            for index, card in enumerate(cards):
                bot_response += '{}. [{}]({}) (`{}`)\n'.format(index + 1, card['name'], card['url'], card['id'])

        except (KeyError, ValueError, TypeError):
            return RESPONSE_ERROR_MESSAGE

        return bot_response

    def get_all_checklists(self, content: List[str]) -> str:
        if len(content) != 2:
            return INVALID_ARGUMENTS_ERROR_MESSAGE

        card_id = content[1]
        get_checklists_url = 'https://api.trello.com/1/cards/{}/checklists/'.format(card_id)
        checklists_response = requests.get(get_checklists_url, params=self.auth_params)

        try:
            checklists = checklists_response.json()
            bot_response = '**Checklists:** \n'
            for index, checklist in enumerate(checklists):
                bot_response += '{}. `{}`:\n'.format(index + 1, checklist['name'])

                if 'checkItems' in checklist:
                    for item in checklist['checkItems']:
                        bot_response += ' * [{}] {}\n'.format('X' if item['state'] == 'complete' else '-', item['name'])

        except (KeyError, ValueError, TypeError):
            return RESPONSE_ERROR_MESSAGE

        return bot_response

    def get_all_lists(self, content: List[str]) -> str:
        if len(content) != 2:
            return INVALID_ARGUMENTS_ERROR_MESSAGE

        board_id = content[1]
        get_lists_url = 'https://api.trello.com/1/boards/{}/lists'.format(board_id)
        lists_response = requests.get(get_lists_url, params=self.auth_params)

        try:
            lists = lists_response.json()
            bot_response = '**Lists:** \n'

            for index, _list in enumerate(lists):
                bot_response += '{}. {}\n'.format(index + 1, _list['name'])

                if 'cards' in _list:
                    for card in _list['cards']:
                        bot_response += '  * {}\n'.format(card['name'])

        except (KeyError, ValueError, TypeError):
            return RESPONSE_ERROR_MESSAGE

        return bot_response

handler_class = TrelloHandler

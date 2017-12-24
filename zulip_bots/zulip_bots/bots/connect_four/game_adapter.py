import re
import json
from copy import deepcopy

class InputVerification(object):
    def __init__(self, move_regex, superusers):
        self.move_regex = move_regex
        self.verified_commands = {
            'waiting': ['start game with computer', 'start game with \w+@\w+\.\w+'],
            'inviting': [['withdraw invitation'], ['accept', 'decline']],
            'playing': [[move_regex, 'quit', 'confirm quit'], ['quit', 'confirm quit']]
        }
        self.all_valid_commands = ['help', 'status', 'start game with computer', 'start game with \w+@\w+\.\w+',
                                   'withdraw invitation', 'accept', 'decline', self.move_regex, 'quit', 'confirm quit', 'force reset']
        self.superusers = superusers

    verified_users = []

    def permission_lacking_message(self, command):
        return 'Sorry, but you can\'t run the command ```' + command + '```'

    def update_commands(self, turn):
        self.verified_commands['playing'] = [['quit', 'confirm quit'], ['quit', 'confirm quit']]
        self.verified_commands['playing'][turn].append(self.move_regex)

    def reset_commands(self):
        self.verified_commands['playing'] = [[self.move_regex, 'quit', 'confirm quit'], ['quit', 'confirm quit']]

    def regex_match_in_array(self, command_array, command):
        for command_regex in command_array:
            if re.compile(command_regex).match(command.lower()):
                return True

        return False

    def valid_command(self, command):
        return self.regex_match_in_array(self.all_valid_commands, command)

    def verify_user(self, user):
        return user in self.verified_users

    def verify_command(self, user, command, state):
        if state != 'waiting':
            command_array = self.verified_commands[state][self.verified_users.index(user)]
        else:
            command_array = self.verified_commands[state]

        return self.regex_match_in_array(command_array, command)

    def verify_superuser(self, user):
        return user in self.superusers

class StateManager(object):
    def __init__(self, main_bot_handler):
        self.users = None
        self.state = ''
        self.user_messages = []
        self.opponent_messages = []
        self.main_bot_handler = main_bot_handler

    # Updates to the main bot handler that all state managers must use
    def basic_updates(self):
        if self.users is not None:
            self.main_bot_handler.inputVerification.verified_users = self.users

        if self.state:
            self.main_bot_handler.state = self.state

        self.main_bot_handler.user_messages = self.user_messages

        self.main_bot_handler.opponent_messages = self.opponent_messages

    def reset_self(self):
        self.users = None
        self.user_messages = []
        self.opponent_messages = []
        self.state = ''

class GameCreator(StateManager):
    def __init__(self, main_bot_handler):
        super(GameCreator, self).__init__(main_bot_handler)
        self.gameHandler = None
        self.invitationHandler = None

    def handle_message(self, content, sender):
        if content == 'start game with computer':
            self.users = [sender]
            self.state = 'playing'
            self.gameHandler = GameHandler(self.main_bot_handler, 'one_player', self.main_bot_handler.model())

            self.user_messages.append('**You started a new game with the computer!**')
            self.user_messages.append(self.main_bot_handler.gameMessageHandler.parse_board(self.main_bot_handler.model().blank_board))
            self.user_messages.append(self.gameHandler.your_turn_message())

        elif re.compile('\w+@\w+\.\w+').search(content):
            opponent = re.compile('(\w+@\w+\.\w+)').search(content).group(1)

            if opponent == sender:
                self.user_messages.append('You can\'t play against yourself!')
                self.update_main_bot_handler()
                return

            self.users = [sender, opponent]
            self.state = 'inviting'
            self.gameHandler = GameHandler(self.main_bot_handler, 'two_player', self.main_bot_handler.model())
            self.invitationHandler = InvitationHandler(self.main_bot_handler)

            self.user_messages.append(self.invitationHandler.confirm_new_invitation(opponent))

            self.opponent_messages.append(self.invitationHandler.alert_new_invitation(sender))

        self.update_main_bot_handler()

    def update_main_bot_handler(self):
        self.basic_updates()

        self.main_bot_handler.player_cache = self.users

        self.main_bot_handler.gameHandler = deepcopy(self.gameHandler)

        if self.invitationHandler:
            self.main_bot_handler.invitationHandler = deepcopy(self.invitationHandler)

        self.reset_self()

class GameHandler(StateManager):
    def __init__(self, main_bot_handler, game_type, model, board = 'blank', turn = 0):
        super(GameHandler, self).__init__(main_bot_handler)
        self.game_type = game_type
        self.turn = turn
        self.game_ended = False
        self.model = model
        self.board = model.blank_board if board == 'blank' else board
        self.model.update_board(board)

    def your_turn_message(self):
        return '**It\'s your move!**\n' +\
               'type ```move <column-number>``` to make your move\n\n' +\
               'You are ' + self.main_bot_handler.gameMessageHandler.get_player_color(self.turn)

    def wait_turn_message(self, opponent):
        return 'Waiting for ' + opponent + ' to move'

    def invalid_move_message(self):
        return 'That\'s an invalid move. ' + self.main_bot_handler.gameMessageHandler.invalid_move_message()

    def append_game_over_messages(self, result):
        if result == 'draw':
            self.user_messages.append('**It\'s a draw!**')
            self.opponent_messages.append('**It\'s a draw!**')
        else:
            if result != 'the Computer':
                self.user_messages.append('**Congratulations, you win! :tada:**')
                self.opponent_messages.append('Sorry, but ' + result + ' won :cry:')
            else:
                self.user_messages.append('Sorry, but ' + result + ' won :cry:')

    def get_player_token(self, sender):
        player = self.main_bot_handler.inputVerification.verified_users.index(sender)
        # This computation will return 1 for player 0, and -1 for player 1, as is expected
        return (-2) * player + 1

    def toggle_turn(self):
        self.turn = (-1) * self.turn + 1

    def end_game(self):
        self.state = 'waiting'
        self.game_ended = True
        self.users = []

    def handle_move(self, move_info, token_number, player_one, player_two, computer_play = False):
        if not self.model.validate_move(move_info):
            self.user_messages.append(self.invalid_move_message())
            return

        self.board = self.model.make_move(move_info, token_number)

        if not computer_play:
            self.user_messages.append(self.main_bot_handler.gameMessageHandler.confirm_move_message(move_info))
            self.user_messages.append(self.main_bot_handler.gameMessageHandler.parse_board(self.model.current_board))

            self.opponent_messages.append(self.main_bot_handler.gameMessageHandler.alert_move_message(self.sender, move_info))
            self.opponent_messages.append(self.main_bot_handler.gameMessageHandler.parse_board(self.model.current_board))

        else:
            self.user_messages.append(self.main_bot_handler.gameMessageHandler.alert_move_message('the Computer', move_info))
            self.user_messages.append(self.main_bot_handler.gameMessageHandler.parse_board(self.model.current_board))

        game_over = self.model.determine_game_over(player_one, player_two)

        if game_over:
            self.append_game_over_messages(game_over)
            self.end_game()

        else:
            self.toggle_turn()

            self.main_bot_handler.inputVerification.update_commands(self.turn)

            if not computer_play:
                self.user_messages.append(self.wait_turn_message(self.opponent))

                self.opponent_messages.append(self.your_turn_message())

            else:
                self.user_messages.append(self.your_turn_message())

    def handle_message(self, content, sender):
        self.sender = sender
        move_regex = self.main_bot_handler.inputVerification.move_regex

        if self.game_type == 'two_player':
            opponent_array = deepcopy(self.main_bot_handler.inputVerification.verified_users)
            opponent_array.remove(sender)
            self.opponent = opponent_array[0]
        else:
            self.opponent = 'the Computer'

        if content == 'quit':
            self.user_messages.append('Are you sure you want to quit? You will forfeit the game!\n' +
                                      'Type ```confirm quit``` to forfeit.')

        elif content == 'confirm quit':
            self.end_game()

            self.user_messages.append('**You have forfeit the game**\nSorry, but you lost :cry:')

            self.opponent_messages.append('**' + sender + ' has forfeit the game**\nCongratulations, you win! :tada:')

        elif re.compile(move_regex).match(content):
            player_one = player_one = self.main_bot_handler.inputVerification.verified_users[0]
            player_two = 'the Computer' if self.game_type == 'one_player' else self.main_bot_handler.inputVerification.verified_users[1]

            human_move = re.compile(move_regex).search(content).group(1)
            human_move = self.model.parse_move(human_move)
            human_token_number = self.get_player_token(sender)

            self.handle_move(human_move, human_token_number, player_one, player_two)

            if not self.game_ended and self.game_type == 'one_player':
                computer_move = self.model.computer_move()
                computer_token_number = -1

                self.handle_move(computer_move, computer_token_number, player_one, player_two, computer_play = True)

        self.update_main_bot_handler()

    def update_main_bot_handler(self):
        if self.game_type == 'one_player':
            self.opponent_messages = []

        self.basic_updates()

        if self.game_ended:
            self.main_bot_handler.gameHandler = None

        self.reset_self()

class InvitationHandler(StateManager):
    def __init__(self, main_bot_handler):
        super(InvitationHandler, self).__init__(main_bot_handler)
        self.game_cancelled = False
        self.gameHandler = object
        self.game_name = main_bot_handler.game_name

    def confirm_new_invitation(self, opponent):
        return 'You\'ve sent an invitation to play ' + self.game_name + ' with ' +\
            opponent + '. I\'ll let you know when they respond to the invitation'

    def alert_new_invitation(self, challenger):
        # Since the first player invites, the challenger is always the first player
        return '**' + challenger + ' has invited you to play a game of ' + self.game_name + '.**\n' +\
            'Type ```accept``` to accept the game invitation\n' +\
            'Type ```decline``` to decline the game invitation.'

    def handle_message(self, content, sender):
        challenger = self.main_bot_handler.inputVerification.verified_users[0]
        opponent = self.main_bot_handler.inputVerification.verified_users[1]

        if content.lower() == 'accept':
            self.state = 'playing'

            self.user_messages.append('You accepted the invitation to play with ' + challenger)
            self.user_messages.append(self.main_bot_handler.gameHandler.wait_turn_message(challenger))

            self.opponent_messages.append('**' + opponent + ' has accepted your invitation to play**')
            self.opponent_messages.append(self.main_bot_handler.gameMessageHandler.parse_board(self.main_bot_handler.model().blank_board))
            self.opponent_messages.append(self.main_bot_handler.gameHandler.your_turn_message())

        elif content.lower() == 'decline':
            self.state = 'waiting'
            self.users = []
            self.gameHandler = None

            self.user_messages.append('You declined the invitation to play with ' + challenger)

            self.opponent_messages.append('**' + opponent + ' has declined your invitation to play**\n' +
                                          'Invite another player by typing ```start game with user@example.com```')

        elif content.lower() == 'withdraw invitation':
            self.state = 'waiting'
            self.users = []
            self.gameHandler = None

            self.user_messages.append('Your invitation to play ' + opponent + ' has been withdrawn')

            self.opponent_messages.append('**' + challenger + ' has withdrawn his invitation to play you**\n' +
                                          'Type ``` start game with ' + challenger + '``` if you would like to play them.')

        self.update_main_bot_handler()

    def update_main_bot_handler(self):
        self.basic_updates()

        self.main_bot_handler.invitationHandler = None

        if self.gameHandler is None:
            self.main_bot_handler.gameHandler = self.gameHandler

        self.reset_self()

class GameAdapter(object):
    '''
    Class that serves as a template to easily
    create one and two player games
    '''

    def __init__(self, game_name, bot_name, move_help_message, move_regex, model, gameMessageHandler):
        self.game_name = game_name
        self.bot_name = bot_name
        self.move_help_message = move_help_message
        self.model = model
        self.gameMessageHandler = gameMessageHandler()
        self.inputVerification = InputVerification(move_regex, [])

    def get_stored_data(self):
        return self.bot_handler.storage.get(self.bot_name)

    def update_data(self):
        self.state = self.data['state']

        if 'users' in self.data:
            self.inputVerification.verified_users = self.data['users']
        else:
            self.inputVerification.verified_users = []

        if self.state == 'inviting':
            self.invitationHandler = InvitationHandler(self)
            self.gameHandler = GameHandler(self, self.data['game_type'], self.model())

        elif self.state == 'playing':
            self.gameHandler = GameHandler(self, self.data['game_type'], self.model(),
                                           board = self.data['board'], turn = self.data['turn'])
            self.inputVerification.update_commands(self.data['turn'])

    def put_stored_data(self):
        self.data = {}

        self.data['state'] = self.state

        if self.inputVerification.verified_users:
            self.data['users'] = self.inputVerification.verified_users

        if self.state == 'inviting':
            self.data['game_type'] = self.gameHandler.game_type

        elif self.state == 'playing':
            self.data['game_type'] = self.gameHandler.game_type
            self.data['board'] = self.gameHandler.board
            self.data['turn'] = self.gameHandler.turn

        self.bot_handler.storage.put(self.bot_name, self.data)

    # Stores the current state of the game. Either 'waiting 'inviting' or 'playing'
    state = 'waiting'

    # Stores the users, in case one of the state managers modifies the verified users
    player_cache = []

    # Object-wide storage to the bot_handler to allow custom message-sending function
    bot_handler = None

    invitationHandler = None
    gameHandler = None
    gameCreator = None

    user_messages = []
    opponent_messages = []

    # Stores a compact version of all data the bot is managing
    data = {'state': 'waiting'}

    def status_message(self):
        prefix = '**' + self.game_name + ' Game Status**\n' +\
            '*If you suspect users are abusing the bot,' +\
            ' please alert the bot owner*\n\n'

        if self.state == 'playing':
            if self.gameHandler.game_type == 'one_player':
                message = 'The bot is currently running a single player game' +\
                          ' for ' + self.inputVerification.verified_users[0] + '.'

            elif self.gameHandler.game_type == 'two_player':
                message = 'The bot is currently running a two player game ' +\
                          'between ' + self.inputVerification.verified_users[0] +\
                          ' and ' + self.inputVerification.verified_users[1] + '.'

        elif self.state == 'inviting':
            message = self.inputVerification.verified_users[0] + '\'s' +\
                ' invitation to play ' + self.inputVerification.verified_users[1] +\
                ' is still pending. Wait for the game to finish to play a game.'

        elif self.state == 'waiting':
            message = '**The bot is not running a game right now!**\n' + \
                'Type ```start game with user@example.com``` '  +\
                'to start a game with another user,\n' +\
                'or type ```start game with computer``` ' +\
                'to start a game with the computer'

        return prefix + message

    def help_message(self):
        return '**' + self.game_name  + ' Bot Help:**\n' + \
            '*Preface all commands with @bot-name*\n\n' + \
            '* To see the current status of the game, type\n' + \
            '```status```\n' + \
            '* To start a game against the computer, type\n' + \
            '```start game with computer```\n' +\
            '* To start a game against another player, type\n' + \
            '```start game with user@example.com```\n' + \
            '* To quit a game at any time, type\n' + \
            '```quit```\n' + \
            '* To withdraw an invitation, type\n' + \
            '```cancel game```\n' + \
            self.move_help_message

    def send_message(self, user, content):
        self.bot_handler.send_message(dict(
            type = 'private',
            to = user,
            content = content
        ))

    # Sends messages returned from helper classes, where user, is the user who sent the bot the original messages
    def send_message_arrays(self, user):
        if self.opponent_messages:
            opponent_array = deepcopy(self.player_cache)
            opponent_array.remove(user)
            opponent = opponent_array[0]

        for message in self.user_messages:
            self.send_message(user, message)

        for message in self.opponent_messages:
            self.send_message(opponent, message)

        self.user_messages = []
        self.opponent_messages = []

    def parse_message(self, message):
        content = message['content'].strip()
        sender = message['sender_email']
        return (content, sender)

    def usage(self):
        return '''
        Bot that allows users to play another user
        or the computer in a game of ''' + self.game_name + '''

        To see the entire list of commands, type
        @bot-name help
        '''

    def initialize(self, bot_handler):
        self.config_info = bot_handler.get_config_info('connect_four')
        if self.config_info:
            self.inputVerification.superusers = json.loads(self.config_info['superusers'])
        self.gameCreator = GameCreator(self)
        self.inputVerification.reset_commands()

        if not bot_handler.storage.contains(self.bot_name):
            bot_handler.storage.put(self.bot_name, self.data)

    def force_reset(self, sender):
        for user in self.inputVerification.verified_users:
            self.send_message(user, 'A bot moderator determined you were abusing the bot, and quit your game.'
                                    ' Please make sure you finish all your games in a timely fashion.')

        self.send_message(sender, 'The game has been force reset')

        self.data = data = {'state': 'waiting'}
        self.update_data()
        self.put_stored_data()

    def handle_message(self, message, bot_handler):
        self.bot_handler = bot_handler

        self.data = self.get_stored_data()
        self.update_data()

        self.player_cache = self.inputVerification.verified_users
        content, sender = self.parse_message(message)

        if not self.inputVerification.valid_command(content.lower()):
            self.send_message(sender, 'Sorry, but I couldn\'t understand your input.\n'
                                      'Type ```help``` to see a full list of commands.')
            return

        elif self.inputVerification.verify_superuser(sender) and content.lower() == 'force reset':
            self.force_reset(sender)
            return

        elif content.lower() == 'help' or content == '':
            self.send_message(sender, self.help_message())
            return

        elif content.lower() == 'status':
            self.send_message(sender, self.status_message())
            return

        elif self.state == 'waiting':
            if not self.inputVerification.verify_command(sender, content.lower(), 'waiting'):
                self.send_message(sender, self.inputVerification.permission_lacking_message(content))

            self.gameCreator.handle_message(content, sender)

        elif not self.inputVerification.verify_user(sender):
            self.send_message(sender, 'Sorry, but other users are already using the bot.'
                                      'Type ```status``` to see the current status of the bot.')
            return

        elif self.state == 'inviting':
            if not self.inputVerification.verify_command(sender, content.lower(), 'inviting'):
                self.send_message(sender, self.inputVerification.permission_lacking_message(content))
                return

            self.invitationHandler.handle_message(content, sender)

        elif self.state == 'playing':
            if not self.inputVerification.verify_command(sender, content.lower(), 'playing'):
                self.send_message(sender, self.inputVerification.permission_lacking_message(content))
                return

            self.gameHandler.handle_message(content, sender)

        self.send_message_arrays(sender)
        self.put_stored_data()

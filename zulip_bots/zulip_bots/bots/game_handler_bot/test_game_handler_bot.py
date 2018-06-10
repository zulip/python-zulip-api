from zulip_bots.test_lib import BotTestCase, DefaultTests
from zulip_bots.game_handler import GameInstance

from mock import patch

from typing import Any, Dict, List


class TestGameHandlerBot(BotTestCase, DefaultTests):
    bot_name = 'game_handler_bot'

    def make_request_message(
        self,
        content: str,
        user: str='foo@example.com',
        user_name: str='foo',
        type: str='private',
        stream: str='',
        subject: str=''
    ) -> Dict[str, str]:
        message = dict(
            sender_email=user,
            sender_full_name=user_name,
            content=content,
            type=type,
            display_recipient=stream,
            subject=subject,
        )
        return message

    # Function that serves similar purpose to BotTestCase.verify_dialog, but allows for multiple responses to be handled
    def verify_response(
        self,
        request: str,
        expected_response: str,
        response_number: int,
        bot: Any=None,
        user_name: str='foo',
        stream: str='',
        subject: str='',
        max_messages: int=20
    ) -> None:
        '''
        This function serves a similar purpose
        to BotTestCase.verify_dialog, but allows
        for multiple responses to be validated,
        and for mocking of the bot's internal data
        '''
        if bot is None:
            bot, bot_handler = self._get_handlers()
        else:
            _b, bot_handler = self._get_handlers()
        type = 'private' if stream == '' else 'stream'
        message = self.make_request_message(
            request, user_name + '@example.com', user_name, type, stream, subject)
        bot_handler.reset_transcript()
        bot.handle_message(message, bot_handler)

        responses = [
            message
            for (method, message)
            in bot_handler.transcript
        ]
        first_response = responses[response_number]
        self.assertEqual(expected_response, first_response['content'])
        self.assertLessEqual(len(responses), max_messages)

    def add_user_to_cache(self, name: str, bot: Any=None) -> Any:
        if bot is None:
            bot, bot_handler = self._get_handlers()
        message = {
            'sender_email': '{}@example.com'.format(name),
            'sender_full_name': '{}'.format(name)
        }
        bot.add_user_to_cache(message)
        return bot

    def setup_game(self, id: str='', bot: Any=None, players: List[str]=['foo', 'baz'], subject: str='test game', stream: str='test') -> Any:
        if bot is None:
            bot, bot_handler = self._get_handlers()
        for p in players:
            self.add_user_to_cache(p, bot)
        players_emails = [p + '@example.com' for p in players]
        game_id = 'abc123'
        if id != '':
            game_id = id
        instance = GameInstance(bot, False, subject,
                                game_id, players_emails, stream)
        bot.instances.update({game_id: instance})
        instance.turn = -1
        instance.start()
        return bot

    def setup_computer_game(self) -> Any:
        bot = self.add_user_to_cache('foo')
        bot.email = 'test-bot@example.com'
        self.add_user_to_cache('test-bot', bot)
        instance = GameInstance(bot, False, 'test game', 'abc123', [
                                'foo@example.com', 'test-bot@example.com'], 'test')
        bot.instances.update({'abc123': instance})
        instance.start()
        return bot

    def help_message(self) -> str:
        return '''** foo test game Bot Help:**
*Preface all commands with @**test-bot***
* To start a game in a stream (*recommended*), type
`start game`
* To start a game against another player, type
`start game with @<player-name>`
* To start a game with the computer, type
`start game with` @**test-bot**
* To play game with the current number of players, type
`play game`
* To quit a game at any time, type
`quit`
* To end a game with a draw, type
`draw`
* To forfeit a game, type
`forfeit`
* To see the leaderboard, type
`leaderboard`
* To withdraw an invitation, type
`cancel game`
* To see rules of this game, type
`rules`
* To make your move during a game, type
```move <column-number>```'''

    def test_help_message(self) -> None:
        self.verify_response('help', self.help_message(), 0)
        self.verify_response('foo bar baz', self.help_message(), 0)

    def test_exception_handling(self) -> None:
        with patch('logging.exception'), \
                patch('zulip_bots.game_handler.GameAdapter.command_quit',
                      side_effect=Exception):
            self.verify_response('quit', 'Error .', 0)

    def test_not_in_game_messages(self) -> None:
        self.verify_response(
            'move 3', 'You are not in a game at the moment. Type `help` for help.', 0, max_messages=1)
        self.verify_response(
            'quit', 'You are not in a game. Type `help` for all commands.', 0, max_messages=1)

    def test_start_game_with_name(self) -> None:
        bot = self.add_user_to_cache('baz')
        self.verify_response('start game with @**baz**',
                             'You\'ve sent an invitation to play foo test game with @**baz**', 1, bot=bot)
        self.assertEqual(len(bot.invites), 1)

    def test_start_game_with_email(self) -> None:
        bot = self.add_user_to_cache('baz')
        self.verify_response('start game with baz@example.com',
                             'You\'ve sent an invitation to play foo test game with @**baz**', 1, bot=bot)
        self.assertEqual(len(bot.invites), 1)

    def test_join_game_and_start_in_stream(self) -> None:
        bot = self.add_user_to_cache('baz')
        self.add_user_to_cache('foo', bot)
        bot.invites = {
            'abc': {
                'stream': 'test',
                'subject': 'test game',
                'host': 'foo@example.com'
            }
        }
        self.verify_response('join', '@**baz** has joined the game', 0, bot=bot,
                             stream='test', subject='test game', user_name='baz')
        self.assertEqual(len(bot.instances.keys()), 1)

    def test_start_game_in_stream(self) -> None:
        self.verify_response(
            'start game',
            '**foo** wants to play **foo test game**. Type @**test-bot** join to play them!',
            0,
            stream='test',
            subject='test game'
        )

    def test_start_invite_game_in_stream(self) -> None:
        bot = self.add_user_to_cache('baz')
        self.verify_response(
            'start game with @**baz**',
            'If you were invited, and you\'re here, type "@**test-bot** accept" to accept the invite!',
            2,
            bot=bot,
            stream='test',
            subject='game test'
        )

    def test_join_no_game(self) -> None:
        self.verify_response('join', 'There is not a game in this subject. Type `help` for all commands.',
                             0, stream='test', subject='test game', user_name='baz', max_messages=1)

    def test_accept_invitation(self) -> None:
        bot = self.add_user_to_cache('baz')
        self.add_user_to_cache('foo', bot)
        bot.invites = {
            'abc': {
                'subject': '###private###',
                'stream': 'games',
                'host': 'foo@example.com',
                'baz@example.com': 'p'
            }
        }
        self.verify_response(
            'accept', 'Accepted invitation to play **foo test game** from @**foo**.', 0, bot, 'baz')

    def test_decline_invitation(self) -> None:
        bot = self.add_user_to_cache('baz')
        self.add_user_to_cache('foo', bot)
        bot.invites = {
            'abc': {
                'subject': '###private###',
                'host': 'foo@example.com',
                'baz@example.com': 'p'
            }
        }
        self.verify_response(
            'decline', 'Declined invitation to play **foo test game** from @**foo**.', 0, bot, 'baz')

    def test_quit_invite(self) -> None:
        bot = self.add_user_to_cache('foo')
        bot.invites = {
            'abc': {
                'subject': '###private###',
                'host': 'foo@example.com'
            }
        }
        self.verify_response(
            'quit', 'Game cancelled.\n!avatar(foo@example.com) **foo** quit.', 0, bot, 'foo')

    def test_user_already_in_game_errors(self) -> None:
        bot = self.setup_game()
        self.verify_response('start game with @**baz**',
                             'You are already in a game. Type `quit` to leave.', 0, bot=bot, max_messages=1)
        self.verify_response(
            'start game', 'You are already in a game. Type `quit` to leave.', 0, bot=bot, stream='test', max_messages=1)
        self.verify_response(
            'accept', 'You are already in a game. Type `quit` to leave.', 0, bot=bot, max_messages=1)
        self.verify_response(
            'decline', 'You are already in a game. Type `quit` to leave.', 0, bot=bot, max_messages=1)
        self.verify_response(
            'join', 'You are already in a game. Type `quit` to leave.', 0, bot=bot, max_messages=1)

    def test_register_command(self) -> None:
        bot = self.add_user_to_cache('foo')
        self.verify_response(
            'register', 'Hello @**foo**. Thanks for registering!', 0, bot, 'foo')
        self.assertIn('foo@example.com', bot.user_cache.keys())

    def test_no_active_invite_errors(self) -> None:
        self.verify_response(
            'accept', 'No active invites. Type `help` for commands.', 0)
        self.verify_response(
            'decline', 'No active invites. Type `help` for commands.', 0)

    def test_wrong_number_of_players_message(self) -> None:
        bot = self.add_user_to_cache('baz')
        bot.min_players = 5
        self.verify_response('start game with @**baz**',
                             'You must have at least 5 players to play.\nGame cancelled.', 0, bot=bot)
        bot.min_players = 2
        bot.max_players = 1
        self.verify_response('start game with @**baz**',
                             'The maximum number of players for this game is 1.', 0, bot=bot)
        bot.max_players = 1
        bot.invites = {
            'abc': {
                'stream': 'test',
                'subject': 'test game',
                'host': 'foo@example.com'
            }
        }
        self.verify_response('join', 'This game is full.', 0, bot=bot,
                             stream='test', subject='test game', user_name='baz')

    def test_public_accept(self) -> None:
        bot = self.add_user_to_cache('baz')
        self.add_user_to_cache('foo', bot)
        bot.invites = {
            'abc': {
                'stream': 'test',
                'subject': 'test game',
                'host': 'baz@example.com',
                'foo@example.com': 'p'
            }
        }
        self.verify_response('accept', '@**foo** has accepted the invitation.',
                             0, bot=bot, stream='test', subject='test game')

    def test_start_game_with_computer(self) -> None:
        self.verify_response('start game with @**test-bot**',
                             'Wait... That\'s me!', 4, stream='test', subject='test game')

    def test_sent_by_bot(self) -> None:
        with self.assertRaises(IndexError):
            self.verify_response(
                'foo', '', 0, user_name='test-bot', stream='test', subject='test game')

    def test_forfeit(self) -> None:
        bot = self.setup_game()
        self.verify_response('forfeit', '**foo** forfeited!',
                             0, bot=bot, stream='test', subject='test game')

    def test_draw(self) -> None:
        bot = self.setup_game()
        self.verify_response('draw', '**foo** has voted for a draw!\nType `draw` to accept',
                             0, bot=bot, stream='test', subject='test game')
        self.verify_response('draw', 'It was a draw!', 0, bot=bot, stream='test',
                             subject='test game', user_name='baz')

    def test_normal_turns(self) -> None:
        bot = self.setup_game()
        self.verify_response('move 3', '**foo** moved in column 3\n\nfoo\n\n!avatar(baz@example.com) It\'s **baz**\'s (:red_circle:) turn.',
                             0, bot=bot, stream='test', subject='test game')
        self.verify_response('move 3', '**baz** moved in column 3\n\nfoo\n\n!avatar(foo@example.com) It\'s **foo**\'s (:blue_circle:) turn.',
                             0, bot=bot, stream='test', subject='test game', user_name='baz')

    def test_wrong_turn(self) -> None:
        bot = self.setup_game()
        self.verify_response('move 5', '!avatar(foo@example.com) It\'s **foo**\'s (:blue_circle:) turn.', 0,
                             bot=bot, stream='test', subject='test game', user_name='baz')

    def test_private_message_error(self) -> None:
        self.verify_response(
            'start game', 'If you are starting a game in private messages, you must invite players. Type `help` for commands.', 0, max_messages=1)
        bot = self.add_user_to_cache('bar')
        bot.invites = {
            'abcdefg': {
                'host': 'bar@example.com',
                'stream': 'test',
                'subject': 'test game'
            }
        }
        self.verify_response(
            'join', 'You cannot join games in private messages. Type `help` for all commands.', 0, bot=bot, max_messages=1)

    def test_game_already_in_subject(self) -> None:
        bot = self.add_user_to_cache('foo')
        bot.invites = {
            'abcdefg': {
                'host': 'foo@example.com',
                'stream': 'test',
                'subject': 'test game'
            }
        }
        self.verify_response('start game', 'There is already a game in this stream.', 0,
                             bot=bot, stream='test', subject='test game', user_name='baz', max_messages=1)

    # def test_not_authorized(self) -> None:
    #    bot = self.setup_game()
    #    self.verify_response('move 3', 'You are not authorized to send messages in this stream', 0, bot=bot,
    #                         user_name='bar', stream='test', subject='test game', max_messages=1)

    def test_unknown_user(self) -> None:
        self.verify_response('start game with @**bar**',
                             'I don\'t know @**bar**. Tell them to say @**test-bot** register', 0)
        self.verify_response('start game with bar@example.com',
                             'I don\'t know bar@example.com. Tell them to use @**test-bot** register', 0)

    def test_is_user_not_player(self) -> None:
        bot = self.add_user_to_cache('foo')
        self.add_user_to_cache('baz', bot)
        bot.invites = {
            'abcdefg': {
                'host': 'foo@example.com',
                'baz@example.com': 'a'
            }
        }
        self.assertFalse(bot.is_user_not_player('foo@example.com'))
        self.assertFalse(bot.is_user_not_player('baz@example.com'))

    def test_move_help_message(self) -> None:
        bot = self.setup_game()
        self.verify_response('move 123', '* To make your move during a game, type\n```move <column-number>```',
                             0, bot=bot, stream='test', subject='test game')

    def test_invalid_move_message(self) -> None:
        bot = self.setup_game()
        self.verify_response('move 9', 'Invalid Move.', 0,
                             bot=bot, stream='test', subject='test game', max_messages=2)

    def test_get_game_id_by_email(self) -> None:
        bot = self.setup_game()
        self.assertEqual(bot.get_game_id_by_email('foo@example.com'), 'abc123')

    def test_game_over_and_leaderboard(self) -> None:
        bot = self.setup_game()
        bot.put_user_cache()
        with patch('zulip_bots.bots.game_handler_bot.game_handler_bot.MockModel.determine_game_over', return_value='foo@example.com'):
            self.verify_response('move 3', '!avatar(foo@example.com) **foo** won! :tada:',
                                 1, bot=bot, stream='test', subject='test game')
        leaderboard = '**Most wins**\n\n\
Player | Games Won | Games Drawn | Games Lost | Total Games\n\
 ---  |  ---  |  ---  |  ---  |  --- \n\
 **foo** | 1 | 0 | 0 | 1\n\
 **baz** | 0 | 0 | 1 | 1\n\
 **test-bot** | 0 | 0 | 0 | 0'
        self.verify_response('leaderboard', leaderboard, 0, bot=bot)

    def test_current_turn_winner(self) -> None:
        bot = self.setup_game()
        with patch('zulip_bots.bots.game_handler_bot.game_handler_bot.MockModel.determine_game_over', return_value='current turn'):
            self.verify_response('move 3', '!avatar(foo@example.com) **foo** won! :tada:',
                                 1, bot=bot, stream='test', subject='test game')

    def test_computer_turn(self) -> None:
        bot = self.setup_computer_game()
        self.verify_response('move 3', '**foo** moved in column 3\n\nfoo\n\n!avatar(test-bot@example.com) It\'s **test-bot**\'s (:red_circle:) turn.',
                             0, bot=bot, stream='test', subject='test game')
        with patch('zulip_bots.bots.game_handler_bot.game_handler_bot.MockModel.determine_game_over', return_value='test-bot@example.com'):
            self.verify_response('move 5', 'I won! Well Played!',
                                 2, bot=bot, stream='test', subject='test game')

    def test_computer_endgame_responses(self) -> None:
        bot = self.setup_computer_game()
        with patch('zulip_bots.bots.game_handler_bot.game_handler_bot.MockModel.determine_game_over', return_value='foo@example.com'):
            self.verify_response('move 5', 'You won! Nice!',
                                 2, bot=bot, stream='test', subject='test game')
        bot = self.setup_computer_game()
        with patch('zulip_bots.bots.game_handler_bot.game_handler_bot.MockModel.determine_game_over', return_value='draw'):
            self.verify_response('move 5', 'It was a draw! Well Played!',
                                 2, bot=bot, stream='test', subject='test game')

    def test_add_user_statistics(self) -> None:
        bot = self.add_user_to_cache('foo')
        bot.add_user_statistics('foo@example.com', {'foo': 3})
        self.assertEqual(bot.user_cache['foo@example.com']['stats']['foo'], 3)

    def test_get_players(self) -> None:
        bot = self.setup_game()
        players = bot.get_players('abc123')
        self.assertEqual(players, ['foo@example.com', 'baz@example.com'])

    def test_none_function_responses(self) -> None:
        bot, bot_handler = self._get_handlers()
        self.assertEqual(bot.get_players('abc'), [])
        self.assertEqual(bot.get_user_by_name('no one'), {})
        self.assertEqual(bot.get_user_by_email('no one'), {})

    def test_get_game_info(self) -> None:
        bot = self.add_user_to_cache('foo')
        self.add_user_to_cache('baz', bot)
        bot.invites = {
            'abcdefg': {
                'host': 'foo@example.com',
                'baz@example.com': 'a',
                'stream': 'test',
                'subject': 'test game'
            }
        }
        self.assertEqual(bot.get_game_info('abcdefg'), {
            'game_id': 'abcdefg',
            'type': 'invite',
            'stream': 'test',
            'subject': 'test game',
            'players': ['foo@example.com', 'baz@example.com']
        })

    def test_parse_message(self) -> None:
        bot = self.setup_game()
        self.verify_response('move 3', 'Join your game using the link below!\n\n> **Game `abc123`**\n\
> !avatar(foo@example.com)\n\
> foo test game\n\
> 2/2 players\n\
> **[Join Game](/#narrow/stream/test/topic/test game)**', 0, bot=bot)
        bot = self.setup_game()
        self.verify_response('move 3', '''Your current game is not in this subject. \n\
To move subjects, send your message again, otherwise join the game using the link below.

> **Game `abc123`**
> !avatar(foo@example.com)
> foo test game
> 2/2 players
> **[Join Game](/#narrow/stream/test/topic/test game)**''', 0, bot=bot, stream='test 2', subject='game 2')
        self.verify_response('move 3', 'foo', 0, bot=bot,
                             stream='test 2', subject='game 2')

    def test_change_game_subject(self) -> None:
        bot = self.setup_game('abc123')
        self.setup_game('abcdefg', bot, ['bar', 'abc'], 'test game 2', 'test2')
        self.verify_response('move 3', '''Your current game is not in this subject. \n\
To move subjects, send your message again, otherwise join the game using the link below.

> **Game `abcdefg`**
> !avatar(bar@example.com)
> foo test game
> 2/2 players
> **[Join Game](/#narrow/stream/test2/topic/test game 2)**''', 0, bot=bot, user_name='bar', stream='test game', subject='test2')
        self.verify_response('move 3', 'There is already a game in this subject.',
                             0, bot=bot, user_name='bar', stream='test game', subject='test')
        bot.invites = {
            'foo bar baz': {
                'host': 'foo@example.com',
                'baz@example.com': 'a',
                'stream': 'test',
                'subject': 'test game'
            }
        }
        bot.change_game_subject('foo bar baz', 'test2',
                                'game2', self.make_request_message('foo'))
        self.assertEqual(bot.invites['foo bar baz']['stream'], 'test2')

from unittest.mock import MagicMock, patch
from zulip_bots.test_lib import BotTestCase, DefaultTests

class TestXkcdBot(BotTestCase, DefaultTests):
    bot_name = "xkcd"

    def test_latest_command(self) -> None:
        bot_response = ("#1866: **Russell's Teapot**\n"
                        "[Unfortunately, NASA regulations state that Bertrand Russell-related "
                        "payloads can only be launched within launch vehicles which do not launch "
                        "themselves.](https://imgs.xkcd.com/comics/russells_teapot.png)")
        with self.mock_http_conversation('test_latest'):
            self.verify_reply('latest', bot_response)

    def test_random_command(self) -> None:
        bot_response = ("#1800: **Chess Notation**\n"
                        "[I've decided to score all my conversations using chess win-loss "
                        "notation. (??)](https://imgs.xkcd.com/comics/chess_notation.png)")
        with self.mock_http_conversation('test_random'):
            # Mock randint function.
            with patch('zulip_bots.bots.xkcd.xkcd.random.randint') as randint:
                mock_rand_value = MagicMock()
                mock_rand_value.return_value = 1800
                randint.return_value = mock_rand_value.return_value
                self.verify_reply('random', bot_response)

    def test_numeric_comic_id_command_1(self) -> None:
        bot_response = ("#1: **Barrel - Part 1**\n[Don't we all.]"
                        "(https://imgs.xkcd.com/comics/barrel_cropped_(1).jpg)")
        with self.mock_http_conversation('test_specific_id'):
            self.verify_reply('1', bot_response)

    @patch('logging.exception')
    def test_invalid_comic_ids(self, mock_logging_exception: MagicMock) -> None:
        invalid_id_txt = "Sorry, there is likely no xkcd comic strip with id: #"

        for comic_id, fixture in (('0', 'test_not_existing_id_2'),
                                  ('999999999', 'test_not_existing_id')):
            with self.mock_http_conversation(fixture):
                self.verify_reply(comic_id, invalid_id_txt + comic_id)

    def test_help_responses(self) -> None:
        help_txt = "xkcd bot supports these commands:"
        err_txt  = "xkcd bot only supports these commands, not `{}`:"
        commands = '''
* `{0} help` to show this help message.
* `{0} latest` to fetch the latest comic strip from xkcd.
* `{0} random` to fetch a random comic strip from xkcd.
* `{0} <comic id>` to fetch a comic strip based on `<comic id>` e.g `{0} 1234`.'''.format(
            "@**test-bot**")
        self.verify_reply('', err_txt.format('') + commands)
        self.verify_reply('help', help_txt + commands)
        # Example invalid command
        self.verify_reply('x', err_txt.format('x') + commands)

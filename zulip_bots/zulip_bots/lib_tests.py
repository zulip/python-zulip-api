from unittest import TestCase
from unittest.mock import MagicMock, patch, ANY, create_autospec
from zulip_bots.lib import (
    ExternalBotHandler,
    StateHandler,
    run_message_handler_for_bot,
)

class FakeClient:
    def __init__(self, *args, **kwargs):
        self.storage = dict()

    def get_profile(self):
        return dict(
            user_id='alice',
            full_name='Alice',
            email='alice@example.com',
        )

    def update_storage(self, payload):
        new_data = payload['storage']
        self.storage.update(new_data)

        return dict(
            result='success',
        )

    def get_storage(self):
        return dict(
            result='success',
            storage=self.storage,
        )

    def send_message(self, message):
        pass

class FakeBotHandler:
    def usage(self):
        return '''
            This is a fake bot handler that is used
            to spec BotHandler mocks.
            '''

    def handle_message(self, message, bot_handler):
        pass

class LibTest(TestCase):
    def test_basics(self):
        client = FakeClient()

        handler = ExternalBotHandler(
            client=client,
            root_dir=None,
            bot_details=None,
            bot_config_file=None
        )

        message = None
        handler.send_message(message)

    def test_state_handler(self):
        client = FakeClient()

        state_handler = StateHandler(client)
        state_handler.put('key', [1, 2, 3])
        val = state_handler.get('key')
        self.assertEqual(val, [1, 2, 3])

        # force us to get non-cached values
        state_handler = StateHandler(client)
        val = state_handler.get('key')
        self.assertEqual(val, [1, 2, 3])

    def test_state_handler(self):
        client = MagicMock()

        state_handler = StateHandler(client)
        client.get_storage.assert_not_called()

        client.update_storage = MagicMock(return_value=dict(result='success'))
        state_handler.put('key', [1, 2, 3])
        client.update_storage.assert_called_with(dict(storage=dict(key='[1, 2, 3]')))

        val = state_handler.get('key')
        client.get_storage.assert_not_called()
        self.assertEqual(val, [1, 2, 3])

        # force us to get non-cached values
        client.get_storage = MagicMock(return_value=dict(
            result='success',
            storage=dict(non_cached_key='[5]')))
        val = state_handler.get('non_cached_key')
        client.get_storage.assert_called_with(keys=('non_cached_key',))
        self.assertEqual(val, [5])

        # value must already be cached
        client.get_storage = MagicMock()
        val = state_handler.get('non_cached_key')
        client.get_storage.assert_not_called()
        self.assertEqual(val, [5])

    def test_send_reply(self):
        client = FakeClient()
        profile = client.get_profile()
        handler = ExternalBotHandler(
            client=client,
            root_dir=None,
            bot_details=None,
            bot_config_file=None
        )
        to = {'email': 'Some@User'}
        expected = [({'type': 'private', 'display_recipient': [to]},
                     {'type': 'private', 'to': [to['email']]}),
                    ({'type': 'private', 'display_recipient': [to, profile]},
                     {'type': 'private', 'to': [to['email']]}),
                    ({'type': 'stream', 'display_recipient': 'Stream name', 'subject': 'Topic'},
                     {'type': 'stream', 'to': 'Stream name', 'subject': 'Topic'})]
        response_text = "Response"
        for test in expected:
            client.send_message = MagicMock()
            handler.send_reply(test[0], response_text)
            client.send_message.assert_called_once_with(dict(test[1], content=response_text))

    def test_content_and_full_content(self):
        client = FakeClient()
        profile = client.get_profile()
        handler = ExternalBotHandler(
            client=client,
            root_dir=None,
            bot_details=None,
            bot_config_file=None
        )
        to = {'email': 'Some@User'}

    def test_run_message_handler_for_bot(self):
        with patch('zulip_bots.lib.Client', new=FakeClient) as fake_client:
            mock_lib_module = MagicMock()
            # __file__ is not mocked by MagicMock(), so we assign a mock value manually.
            mock_lib_module.__file__ = "foo"
            mock_bot_handler = create_autospec(FakeBotHandler)
            mock_lib_module.handler_class.return_value = mock_bot_handler

            def call_on_each_event_mock(self, callback, event_types=None, narrow=None):
                def test_message(message, flags):
                    event = {'message': message,
                             'flags': flags,
                             'type': 'message'}
                    callback(event)

                # In the following test, expected_message is the dict that we expect
                # to be passed to the bot's handle_message function.
                original_message = {'content': '@**Alice** bar',
                                    'type': 'stream'}
                expected_message = {'type': 'stream',
                                    'content': 'bar',
                                    'full_content': '@**Alice** bar'}
                test_message(original_message, {'mentioned'})
                mock_bot_handler.handle_message.assert_called_with(
                    message=expected_message,
                    bot_handler=ANY)

            fake_client.call_on_each_event = call_on_each_event_mock.__get__(
                fake_client, fake_client.__class__)
            run_message_handler_for_bot(lib_module=mock_lib_module,
                                        quiet=True,
                                        config_file=None,
                                        bot_config_file=None,
                                        bot_name='testbot')

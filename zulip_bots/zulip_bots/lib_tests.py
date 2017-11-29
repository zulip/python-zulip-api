from unittest import TestCase
from zulip_bots.lib import (
    ExternalBotHandler,
    StateHandler,
)

class FakeClient:
    def __init__(self):
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

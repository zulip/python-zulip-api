import configparser
import sys
from typing import IO, Any, Dict, Optional
from uuid import uuid4

from zulip_bots.lib import BotIdentity


class SimpleStorage:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = dict()

    def contains(self, key: str) -> bool:
        return key in self.data

    def put(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get(self, key: str) -> Any:
        return self.data[key]


class MockMessageServer:
    # This class is needed for the incrementor bot, which
    # actually updates messages!
    def __init__(self) -> None:
        self.message_id = 0
        self.messages: Dict[int, Dict[str, Any]] = dict()

    def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        self.message_id += 1
        message["id"] = self.message_id
        self.messages[self.message_id] = message
        return message

    def add_reaction(self, reaction_data: object) -> Dict[str, Any]:
        return dict(result="success", msg="", uri=f"https://server/messages/{uuid4()}/reactions")

    def update(self, message: Dict[str, Any]) -> None:
        self.messages[message["message_id"]] = message

    def upload_file(self, file: IO[Any]) -> Dict[str, Any]:
        return dict(result="success", msg="", uri=f"https://server/user_uploads/{uuid4()}")


class TerminalBotHandler:
    def __init__(self, bot_config_file: Optional[str], message_server: MockMessageServer) -> None:
        self.bot_config_file = bot_config_file
        self._storage = SimpleStorage()
        self.message_server = message_server

    @property
    def storage(self) -> SimpleStorage:
        return self._storage

    def identity(self) -> BotIdentity:
        return BotIdentity("bot name", "bot-email@domain")

    def react(self, message: Dict[str, Any], emoji_name: str) -> Dict[str, Any]:
        """
        Mock adding an emoji reaction and print it in the terminal.
        """
        print("""The bot reacts to message #{}: {}""".format(message["id"], emoji_name))
        return self.message_server.add_reaction(
            dict(message_id=message["id"], emoji_name=emoji_name, reaction_type="unicode_emoji")
        )

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Print the message sent in the terminal and store it in a mock message server.
        """
        if message["type"] == "stream":
            print(
                """
                stream: {} topic: {}
                {}
                """.format(message["to"], message["subject"], message["content"])
            )
        else:
            print(
                """
                PM response:
                {}
                """.format(message["content"])
            )
        # Note that message_server is only responsible for storing and assigning an
        # id to the message instead of actually displaying it.
        return self.message_server.send(message)

    def send_reply(self, message: Dict[str, Any], response: str) -> Dict[str, Any]:
        """
        Print the reply message in the terminal and store it in a mock message server.
        """
        print(
            "\nReply from the bot is printed between the dotted lines:\n-------\n{}\n-------".format(
                response
            )
        )
        response_message = dict(content=response)
        return self.message_server.send(response_message)

    def update_message(self, message: Dict[str, Any]) -> None:
        """
        Update a previously sent message and print the result in the terminal.
        Throw an IndexError if the message id is invalid.
        """
        self.message_server.update(message)
        print(
            """
            update to message #{}:
            {}
            """.format(message["message_id"], message["content"])
        )

    def upload_file_from_path(self, file_path: str) -> Dict[str, Any]:
        with open(file_path) as file:
            return self.upload_file(file)

    def upload_file(self, file: IO[Any]) -> Dict[str, Any]:
        return self.message_server.upload_file(file)

    def get_config_info(self, bot_name: str, optional: bool = False) -> Dict[str, Any]:
        if self.bot_config_file is None:
            if optional:
                return dict()
            else:
                print("Please supply --bot-config-file argument.")
                sys.exit(1)

        config = configparser.ConfigParser()
        with open(self.bot_config_file) as conf:
            config.read_file(conf)

        return dict(config.items(bot_name))

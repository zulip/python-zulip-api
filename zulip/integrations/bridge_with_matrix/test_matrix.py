import asyncio
import os
import shutil
import sys
from contextlib import contextmanager
from subprocess import PIPE, Popen
from tempfile import mkdtemp
from typing import Any, Awaitable, Callable, Final, Iterator, List
from unittest import TestCase, mock

import nio
from typing_extensions import override

from .matrix_bridge import MatrixToZulip, ZulipToMatrix, read_configuration

script_file = "matrix_bridge.py"
script_dir = os.path.dirname(__file__)
script = os.path.join(script_dir, script_file)

sample_config_path = "matrix_test.conf"

sample_config_text = """[matrix]
host = https://matrix.org
mxid = @username:matrix.org
password = password
room_id = #zulip:matrix.org

[zulip]
email = glitch-bot@chat.zulip.org
api_key = aPiKeY
site = https://chat.zulip.org
stream = test here
topic = matrix

[additional_bridge1]
room_id = #example:matrix.org
stream = new test
topic = matrix

"""

ZULIP_MESSAGE_TEMPLATE: str = "**{username}** [{uid}]: {message}"


# For Python 3.7 compatibility.
# (Since 3.8, there is unittest.IsolatedAsyncioTestCase!)
# source: https://stackoverflow.com/a/46324983
def async_test(coro: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


@contextmanager
def new_temp_dir() -> Iterator[str]:
    path = mkdtemp()
    yield path
    shutil.rmtree(path)


class MatrixBridgeScriptTests(TestCase):
    def output_from_script(self, options: List[str]) -> List[str]:
        popen = Popen(
            [sys.executable, script, *options], stdin=PIPE, stdout=PIPE, universal_newlines=True
        )
        return popen.communicate()[0].strip().split("\n")

    def test_no_args(self) -> None:
        output_lines = self.output_from_script([])
        expected_lines = [
            "Options required: -c or --config to run, OR --write-sample-config.",
            f"usage: {script_file} [-h]",
        ]
        for expected, output in zip(expected_lines, output_lines):
            self.assertIn(expected, output)

    def test_help_usage_and_description(self) -> None:
        output_lines = self.output_from_script(["-h"])
        usage = f"usage: {script_file} [-h]"
        description = "Bridge between Zulip topics and Matrix channels."
        self.assertIn(usage, output_lines[0])
        blank_lines = [num for num, line in enumerate(output_lines) if line == ""]
        # There should be blank lines in the output
        self.assertTrue(blank_lines)
        # There should be finite output
        self.assertTrue(len(output_lines) > blank_lines[0])
        # Minimal description should be in the first line of the 2nd "paragraph"
        self.assertIn(description, output_lines[blank_lines[0] + 1])

    def test_write_sample_config(self) -> None:
        with new_temp_dir() as tempdir:
            path = os.path.join(tempdir, sample_config_path)
            output_lines = self.output_from_script(["--write-sample-config", path])
            self.assertEqual(output_lines, [f"Wrote sample configuration to '{path}'"])

            with open(path) as sample_file:
                self.assertEqual(sample_file.read(), sample_config_text)

    def test_write_sample_config_from_zuliprc(self) -> None:
        zuliprc_template = ["[api]", "email={email}", "key={key}", "site={site}"]
        zulip_params = {
            "email": "foo@bar",
            "key": "some_api_key",
            "site": "https://some.chat.serverplace",
        }
        with new_temp_dir() as tempdir:
            path = os.path.join(tempdir, sample_config_path)
            zuliprc_path = os.path.join(tempdir, "zuliprc")
            with open(zuliprc_path, "w") as zuliprc_file:
                zuliprc_file.write("\n".join(zuliprc_template).format(**zulip_params))
            output_lines = self.output_from_script(
                ["--write-sample-config", path, "--from-zuliprc", zuliprc_path]
            )
            self.assertEqual(
                output_lines,
                [f"Wrote sample configuration to '{path}' using zuliprc file '{zuliprc_path}'"],
            )

            with open(path) as sample_file:
                sample_lines = [line.strip() for line in sample_file.readlines()]
                expected_lines = sample_config_text.split("\n")
                expected_lines[7] = "email = {}".format(zulip_params["email"])
                expected_lines[8] = "api_key = {}".format(zulip_params["key"])
                expected_lines[9] = "site = {}".format(zulip_params["site"])
                self.assertEqual(sample_lines, expected_lines[:-1])

    def test_detect_zuliprc_does_not_exist(self) -> None:
        with new_temp_dir() as tempdir:
            path = os.path.join(tempdir, sample_config_path)
            zuliprc_path = os.path.join(tempdir, "zuliprc")
            # No writing of zuliprc file here -> triggers check for zuliprc absence
            output_lines = self.output_from_script(
                ["--write-sample-config", path, "--from-zuliprc", zuliprc_path]
            )
            self.assertEqual(
                output_lines,
                [f"Could not write sample config: Zuliprc file '{zuliprc_path}' does not exist."],
            )

    def test_parse_multiple_bridges(self) -> None:
        with new_temp_dir() as tempdir:
            path = os.path.join(tempdir, sample_config_path)
            output_lines = self.output_from_script(["--write-sample-config", path])
            self.assertEqual(output_lines, [f"Wrote sample configuration to '{path}'"])

            config = read_configuration(path)

            self.assertIn("zulip", config)
            self.assertIn("matrix", config)
            self.assertIn("bridges", config["zulip"])
            self.assertIn("bridges", config["matrix"])
            self.assertEqual(
                {
                    ("test here", "matrix"): "#zulip:matrix.org",
                    ("new test", "matrix"): "#example:matrix.org",
                },
                config["zulip"]["bridges"],
            )
            self.assertEqual(
                {
                    "#zulip:matrix.org": ("test here", "matrix"),
                    "#example:matrix.org": ("new test", "matrix"),
                },
                config["matrix"]["bridges"],
            )


class MatrixBridgeMatrixToZulipTests(TestCase):
    user_name = "John Smith"
    user_uid = "@johnsmith:matrix.org"
    room = mock.MagicMock()
    room.user_name = lambda _: "John Smith"

    @override
    def setUp(self) -> None:
        self.matrix_to_zulip = mock.MagicMock()
        self.matrix_to_zulip.get_message_content_from_event = (
            lambda event: MatrixToZulip.get_message_content_from_event(
                self.matrix_to_zulip, event, self.room
            )
        )

    @async_test
    async def test_get_message_content_from_event(self) -> None:
        class RoomMemberEvent(nio.RoomMemberEvent):
            def __init__(self, sender: str = self.user_uid) -> None:
                self.sender = sender

        class RoomMessageFormatted(nio.RoomMessageFormatted):
            def __init__(self, sender: str = self.user_uid) -> None:
                self.sender = sender
                self.body = "this is a message"

        self.assertIsNone(
            await self.matrix_to_zulip.get_message_content_from_event(RoomMemberEvent())
        )
        self.assertEqual(
            await self.matrix_to_zulip.get_message_content_from_event(RoomMessageFormatted()),
            ZULIP_MESSAGE_TEMPLATE.format(
                username=self.user_name, uid=self.user_uid, message="this is a message"
            ),
        )


class MatrixBridgeZulipToMatrixTests(TestCase):
    room = mock.MagicMock()
    valid_zulip_config: Final = dict(
        stream="some stream",
        topic="some topic",
        email="some@email",
        bridges={("some stream", "some topic"): room},
    )
    valid_msg: Final = dict(
        sender_email="John@Smith.smith",  # must not be equal to config:email
        sender_id=42,
        type="stream",  # Can only mirror Zulip streams
        display_recipient=valid_zulip_config["stream"],
        subject=valid_zulip_config["topic"],
    )

    @override
    def setUp(self) -> None:
        self.zulip_to_matrix = mock.MagicMock()
        self.zulip_to_matrix.zulip_config = self.valid_zulip_config
        self.zulip_to_matrix.get_matrix_room_for_zulip_message = (
            lambda msg: ZulipToMatrix.get_matrix_room_for_zulip_message(self.zulip_to_matrix, msg)
        )

    def test_get_matrix_room_for_zulip_message_success(self) -> None:
        self.assertEqual(
            self.zulip_to_matrix.get_matrix_room_for_zulip_message(self.valid_msg), self.room
        )

    def test_get_matrix_room_for_zulip_message_failure(self) -> None:
        self.assertIsNone(
            self.zulip_to_matrix.get_matrix_room_for_zulip_message(
                dict(self.valid_msg, type="private")
            )
        )
        self.assertIsNone(
            self.zulip_to_matrix.get_matrix_room_for_zulip_message(
                dict(self.valid_msg, sender_email="some@email")
            )
        )
        self.assertIsNone(
            self.zulip_to_matrix.get_matrix_room_for_zulip_message(
                dict(self.valid_msg, display_recipient="other stream")
            )
        )
        self.assertIsNone(
            self.zulip_to_matrix.get_matrix_room_for_zulip_message(
                dict(self.valid_msg, subject="other topic")
            )
        )

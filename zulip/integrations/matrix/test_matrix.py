from unittest import TestCase
from subprocess import Popen, PIPE
import os

import shutil

from contextlib import contextmanager
from tempfile import mkdtemp

script_file = "matrix_bridge.py"
script_dir = os.path.dirname(__file__)
script = os.path.join(script_dir, script_file)

from typing import List, Iterator

sample_config_path = "matrix_test.conf"

sample_config_text = """[matrix]
host = https://matrix.org
username = username
password = password
room_id = #zulip:matrix.org

[zulip]
email = glitch-bot@chat.zulip.org
api_key = aPiKeY
site = https://chat.zulip.org
stream = test here
topic = matrix

"""

@contextmanager
def new_temp_dir():
    # type: () -> Iterator[str]
    path = mkdtemp()
    yield path
    shutil.rmtree(path)

class MatrixBridgeTests(TestCase):
    def output_from_script(self, options):
        # type: (List[str]) -> List[str]
        popen = Popen(["python", script] + options, stdin=PIPE, stdout=PIPE, universal_newlines=True)
        return popen.communicate()[0].strip().split("\n")

    def test_no_args(self):
        # type: () -> None
        output_lines = self.output_from_script([])
        expected_lines = [
            "Options required: -c or --config to run, OR --write-sample-config.",
            "usage: {} [-h]".format(script_file)
        ]
        for expected, output in zip(expected_lines, output_lines):
            self.assertIn(expected, output)

    def test_help_usage_and_description(self):
        # type: () -> None
        output_lines = self.output_from_script(["-h"])
        usage = "usage: {} [-h]".format(script_file)
        description = "Script to bridge"
        self.assertIn(usage, output_lines[0])
        blank_lines = [num for num, line in enumerate(output_lines) if line == '']
        # There should be blank lines in the output
        self.assertTrue(blank_lines)
        # There should be finite output
        self.assertTrue(len(output_lines) > blank_lines[0])
        # Minimal description should be in the first line of the 2nd "paragraph"
        self.assertIn(description, output_lines[blank_lines[0] + 1])

    def test_write_sample_config(self):
        # type: () -> None
        with new_temp_dir() as tempdir:
            path = os.path.join(tempdir, sample_config_path)
            output_lines = self.output_from_script(["--write-sample-config", path])
            self.assertEqual(output_lines, ["Wrote sample configuration to '{}'".format(path)])

            with open(path) as sample_file:
                self.assertEqual(sample_file.read(), sample_config_text)

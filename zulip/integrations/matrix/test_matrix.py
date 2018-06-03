from unittest import TestCase
from subprocess import Popen, PIPE
import os

script_file = "matrix_bridge.py"
script_dir = os.path.dirname(__file__)
script = os.path.join(script_dir, script_file)

from typing import List


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

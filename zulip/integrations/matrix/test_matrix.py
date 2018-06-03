from unittest import TestCase
from subprocess import Popen, PIPE
import os

script_file = "matrix_bridge.py"
script_dir = os.path.dirname(__file__)
script = os.path.join(script_dir, script_file)


class MatrixBridgeTests(TestCase):
    def test_no_args(self):
        # type: () -> None
        popen = Popen(["python", script], stdin=PIPE, stdout=PIPE, universal_newlines=True)
        output_lines = popen.communicate()[0].strip().split("\n")
        expected_lines = [
            "Options required: -c or --config to run, OR --write-sample-config.",
            "usage: {} [-h]".format(script_file)
        ]
        for expected, output in zip(expected_lines, output_lines):
            self.assertIn(expected, output)

    def test_help_usage_and_description(self):
        # type: () -> None
        popen = Popen(["python", script] + ["-h"], stdin=PIPE, stdout=PIPE, universal_newlines=True)
        output_lines = popen.communicate()[0].strip().split("\n")
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

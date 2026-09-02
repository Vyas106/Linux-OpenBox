"""Unit tests for ShellRunner live streaming and process management."""

import unittest
import tempfile
from pathlib import Path
from app.tools.shell import ShellRunner


class TestShellRunner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name).resolve()
        self.runner = ShellRunner(self.workspace)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_command_success(self):
        result = self.runner.execute_command("echo 'Agent Shell Ready'")
        self.assertTrue(result["success"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("Agent Shell Ready", result["output"])

    def test_run_command_live_streaming(self):
        lines_captured = []
        result = self.runner.execute_command(
            "echo 'Line 1'; echo 'Line 2'; echo 'Line 3'",
            on_stdout=lambda l: lines_captured.append(l.strip()),
        )
        self.assertTrue(result["success"])
        self.assertTrue(any("Line 1" in l for l in lines_captured))
        self.assertTrue(any("Line 2" in l for l in lines_captured))

    def test_run_command_exit_code_failure(self):
        result = self.runner.execute_command("false")
        self.assertFalse(result["success"])
        self.assertNotEqual(result["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()

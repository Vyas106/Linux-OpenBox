"""Unit tests for Agent class and Tool Registry dispatch."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from app.config import AppConfig
from app.agent.agent import Agent, AgentState


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name).resolve()
        self.config = AppConfig(
            model="qwen2.5:3b",
            workspace=str(self.workspace),
            require_confirmation=True,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tool_registry_registration(self):
        agent = Agent(config=self.config)
        tools = agent.registry.get_ollama_tools()
        tool_names = [t["function"]["name"] for t in tools]

        self.assertIn("list_directory", tool_names)
        self.assertIn("read_file", tool_names)
        self.assertIn("write_file", tool_names)
        self.assertIn("edit_file", tool_names)
        self.assertIn("create_directory", tool_names)
        self.assertIn("delete_file", tool_names)
        self.assertIn("move_file", tool_names)
        self.assertIn("search_files", tool_names)
        self.assertIn("run_command", tool_names)

    def test_execute_tool_via_registry(self):
        agent = Agent(config=self.config)
        res = agent.registry.execute("write_file", {"path": "test.py", "content": "print(42)"})
        self.assertTrue(res["success"])
        self.assertTrue((self.workspace / "test.py").exists())

    def test_permission_request_denial(self):
        perm_requested = []

        def on_perm(cmd, reason, callback):
            perm_requested.append((cmd, reason))
            callback(False, False)  # Deny

        agent = Agent(
            config=self.config,
            on_request_permission=on_perm,
        )

        res = agent._execute_run_command_tool("sudo pacman -S testpkg")
        self.assertFalse(res["success"])
        self.assertIn("Permission denied", res["error"])
        self.assertEqual(len(perm_requested), 1)


if __name__ == "__main__":
    unittest.main()

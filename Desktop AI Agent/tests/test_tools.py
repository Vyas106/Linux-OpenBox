"""Unit tests for filesystem tools."""

import unittest
import tempfile
from pathlib import Path

from app.security import SecurityGuard
from app.tools.filesystem import (
    write_file,
    read_file,
    edit_file,
    create_directory,
    delete_file,
    move_file,
    search_files,
    list_directory,
)


class TestFilesystemTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name).resolve()
        self.guard = SecurityGuard(self.workspace)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_and_read_file(self):
        # Write
        res_write = write_file("test.txt", "Hello World 123", guard=self.guard)
        self.assertTrue(res_write["success"])
        self.assertTrue((self.workspace / "test.txt").exists())

        # Read
        res_read = read_file("test.txt", guard=self.guard)
        self.assertTrue(res_read["success"])
        self.assertEqual(res_read["output"], "Hello World 123")

    def test_edit_file_with_diff(self):
        write_file("code.py", "def old_func():\n    return 1\n", guard=self.guard)
        res_edit = edit_file("code.py", "return 1", "return 42", guard=self.guard)
        self.assertTrue(res_edit["success"])
        self.assertIn("+    return 42", res_edit["diff"])

        # Verify content
        res_read = read_file("code.py", guard=self.guard)
        self.assertIn("return 42", res_read["output"])

    def test_create_and_list_directory(self):
        res_mkdir = create_directory("src/components", guard=self.guard)
        self.assertTrue(res_mkdir["success"])
        self.assertTrue((self.workspace / "src/components").is_dir())

        write_file("src/components/button.py", "class Button: pass", guard=self.guard)

        res_list = list_directory("src/components", guard=self.guard)
        self.assertTrue(res_list["success"])
        self.assertEqual(len(res_list["items"]), 1)
        self.assertEqual(res_list["items"][0]["name"], "button.py")

    def test_search_files(self):
        write_file("module_a.py", "# target_keyword inside", guard=self.guard)
        write_file("module_b.txt", "nothing here", guard=self.guard)

        # Name pattern search
        res_pattern = search_files(".", pattern="*.py", guard=self.guard)
        self.assertTrue(res_pattern["success"])
        self.assertIn("module_a.py", res_pattern["matches"])

        # Content search
        res_content = search_files(".", pattern="target_keyword", search_content=True, guard=self.guard)
        self.assertTrue(res_content["success"])
        self.assertIn("module_a.py", res_content["matches"])

    def test_move_and_delete_file(self):
        write_file("initial.txt", "data", guard=self.guard)
        res_mv = move_file("initial.txt", "renamed.txt", guard=self.guard)
        self.assertTrue(res_mv["success"])
        self.assertFalse((self.workspace / "initial.txt").exists())
        self.assertTrue((self.workspace / "renamed.txt").exists())

        res_del = delete_file("renamed.txt", guard=self.guard)
        self.assertTrue(res_del["success"])
        self.assertFalse((self.workspace / "renamed.txt").exists())


if __name__ == "__main__":
    unittest.main()

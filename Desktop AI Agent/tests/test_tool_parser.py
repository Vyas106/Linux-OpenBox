"""Unit tests for resilient tool parser."""

import unittest
from app.agent.tool_parser import parse_tool_calls


class TestToolParser(unittest.TestCase):
    def test_native_ollama_tool_calls(self):
        resp = {
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": {"path": "hello.py", "content": "print('hello')"},
                    }
                }
            ]
        }
        calls = parse_tool_calls(resp)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "write_file")
        self.assertEqual(calls[0]["arguments"]["path"], "hello.py")

    def test_xml_embedded_tool_calls(self):
        resp = {
            "content": """I will now create the file:
<tool_call>
{"name": "write_file", "arguments": {"path": "main.py", "content": "print(1)"}}
</tool_call>
"""
        }
        calls = parse_tool_calls(resp, valid_tool_names=["write_file", "run_command"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "write_file")
        self.assertEqual(calls[0]["arguments"]["path"], "main.py")

    def test_json_markdown_block_tool_calls(self):
        resp = {
            "content": """Let me run the test command:
```json
{
  "name": "run_command",
  "arguments": {
    "command": "python -m unittest discover"
  }
}
```
"""
        }
        calls = parse_tool_calls(resp, valid_tool_names=["run_command"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "run_command")
        self.assertEqual(calls[0]["arguments"]["command"], "python -m unittest discover")

    def test_function_call_regex_fallback(self):
        resp = {
            "content": 'I will read the file now: read_file(path="config.py")'
        }
        calls = parse_tool_calls(resp, valid_tool_names=["read_file"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "read_file")
        self.assertEqual(calls[0]["arguments"]["path"], "config.py")


if __name__ == "__main__":
    unittest.main()

"""Core Agent Loop and Execution Engine."""

import enum
import json
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..config import AppConfig
from ..ollama_client import OllamaClient
from ..security import SecurityGuard
from ..tools.registry import ToolRegistry
from ..tools.filesystem import (
    list_directory,
    read_file,
    write_file,
    edit_file,
    create_directory,
    delete_file,
    move_file,
    search_files,
)
from ..tools.shell import ShellRunner
from .prompts import get_system_prompt, AgentMode
from .tool_parser import parse_tool_calls


class AgentState(enum.Enum):
    IDLE = "IDLE"
    THINKING = "THINKING"
    RUNNING = "RUNNING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class Agent:
    """Autonomous agent orchestrating LLM reasoning, security checks, and tool executions."""

    def __init__(
        self,
        config: AppConfig,
        ollama_client: Optional[OllamaClient] = None,
        on_state_changed: Optional[Callable[[AgentState, str], None]] = None,
        on_activity: Optional[Callable[[str, str, Optional[str], Optional[Dict[str, Any]]], None]] = None,
        on_command_output: Optional[Callable[[str], None]] = None,
        on_request_permission: Optional[Callable[[str, str, Callable[[bool, bool], None]], None]] = None,
    ):
        self.config = config
        self.workspace = config.resolved_workspace
        self.ollama = ollama_client or OllamaClient(
            base_url=config.ollama_url,
            default_model=config.model,
        )
        self.security = SecurityGuard(self.workspace)
        self.shell_runner = ShellRunner(self.workspace)

        # Callbacks
        self.on_state_changed = on_state_changed
        self.on_activity = on_activity
        self.on_command_output = on_command_output
        self.on_request_permission = on_request_permission

        # State
        self.state = AgentState.IDLE
        self._stop_requested = False
        self._thread: Optional[threading.Thread] = None
        self._always_allowed_commands: set[str] = set()

        # Mode & Working Directory
        self.mode = AgentMode.TASK
        self.project_dir = self.workspace

        # Tool Registry
        self.registry = ToolRegistry()
        self._setup_tools()

    def set_mode(self, mode: AgentMode):
        """Switch agent operating mode (KNOWLEDGE, TASK, CODE)."""
        self.mode = mode

    def set_project_dir(self, path: Path):
        """Set project location for CODE mode."""
        self.project_dir = path.resolve()
        self.project_dir.mkdir(parents=True, exist_ok=True)
        # Update security guard and shell runner base
        self.security = SecurityGuard(self.project_dir)
        self.shell_runner = ShellRunner(self.project_dir)
        self._setup_tools()

    @property
    def active_directory(self) -> Path:
        """Return the current active working directory based on mode."""
        return self.project_dir if self.mode == AgentMode.CODE else self.workspace

    def _set_state(self, state: AgentState, detail: str = ""):
        self.state = state
        if self.on_state_changed:
            self.on_state_changed(state, detail)

    def _emit_activity(self, action_type: str, title: str, description: Optional[str] = None, meta: Optional[Dict[str, Any]] = None):
        if self.on_activity:
            self.on_activity(action_type, title, description, meta)

    def _is_informational_query(self, text: str) -> bool:
        """Detect if the user prompt is asking for explanation, guide, or information rather than direct execution."""
        clean = text.strip().lower()
        question_prefixes = (
            "how can i", "how do i", "how to", "how should i", "how would i",
            "what is", "what are", "what does", "explain", "tell me about",
            "why is", "why does", "why do", "can you explain", "guide for",
            "difference between", "help me understand", "show me how", "give me instructions",
            "teach me", "who is", "when should",
        )
        if any(clean.startswith(pref) for pref in question_prefixes):
            return True
        action_verbs = ("install", "download", "create", "delete", "remove", "run", "execute", "fix", "write", "make", "build", "setup", "set up", "start", "stop", "restart", "edit")
        if clean.endswith("?") and not any(clean.startswith(verb) for verb in action_verbs):
            return True
        return False

    def _setup_tools(self):
        """Register all local Linux tools targeting active working directory."""
        active_dir = self.active_directory

        # Filesystem tools
        self.registry.register(
            name="list_directory",
            func=lambda path=".": list_directory(path=path, guard=self.security, workspace=active_dir),
            description="List files and directories in a directory",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute directory path (defaults to current dir '.' )"}
                },
                "required": [],
            },
        )

        self.registry.register(
            name="read_file",
            func=lambda path, max_lines=500: read_file(path=path, max_lines=max_lines, guard=self.security, workspace=active_dir),
            description="Read content of a text file",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute path to the file"},
                    "max_lines": {"type": "integer", "description": "Maximum number of lines to read (default 500)"}
                },
                "required": ["path"],
            },
        )

        self.registry.register(
            name="write_file",
            func=lambda path, content: write_file(path=path, content=content, guard=self.security, workspace=active_dir),
            description="Create or overwrite a file with the given text content",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute path to the file"},
                    "content": {"type": "string", "description": "Text content to write into the file"}
                },
                "required": ["path", "content"],
            },
        )

        self.registry.register(
            name="edit_file",
            func=lambda path, old_text, new_text: edit_file(path=path, old_text=old_text, new_text=new_text, guard=self.security, workspace=active_dir),
            description="Replace an exact snippet of text (old_text) with new_text in a file",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute path to the file"},
                    "old_text": {"type": "string", "description": "Exact text substring to be replaced"},
                    "new_text": {"type": "string", "description": "Replacement text"}
                },
                "required": ["path", "old_text", "new_text"],
            },
        )

        self.registry.register(
            name="create_directory",
            func=lambda path: create_directory(path=path, guard=self.security, workspace=active_dir),
            description="Create a directory path recursively",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to create"}
                },
                "required": ["path"],
            },
        )

        self.registry.register(
            name="delete_file",
            func=lambda path: delete_file(path=path, guard=self.security, workspace=active_dir),
            description="Delete a file or directory inside the active directory",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file or directory to delete"}
                },
                "required": ["path"],
            },
        )

        self.registry.register(
            name="move_file",
            func=lambda source, destination: move_file(source=source, destination=destination, guard=self.security, workspace=active_dir),
            description="Move or rename a file or directory",
            parameters_schema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"}
                },
                "required": ["source", "destination"],
            },
        )

        self.registry.register(
            name="search_files",
            func=lambda path=".", pattern="*", search_content=False: search_files(path=path, pattern=pattern, search_content=search_content, guard=self.security, workspace=active_dir),
            description="Search for files by filename pattern or content within a directory",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to search within (default '.')"},
                    "pattern": {"type": "string", "description": "Filename pattern (e.g. '*.py') or search string"},
                    "search_content": {"type": "boolean", "description": "Whether to search inside file contents (default false)"}
                },
                "required": [],
            },
        )

        # Shell command tool
        self.registry.register(
            name="run_command",
            func=self._execute_run_command_tool,
            description="Execute a shell command with live streaming output",
            parameters_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash shell command to run"}
                },
                "required": ["command"],
            },
        )

    def _execute_run_command_tool(self, command: str) -> Dict[str, Any]:
        """Wrap shell command execution with security permission check."""
        is_dangerous, reason = self.security.assess_command(command)

        if is_dangerous and self.config.require_confirmation and command not in self._always_allowed_commands:
            self._set_state(AgentState.WAITING_FOR_PERMISSION, f"Permission requested: {command}")
            self._emit_activity("permission", "Permission required", f"Command: {command}\nReason: {reason}", {"command": command})

            decision_event = threading.Event()
            decision_result = {"allowed": False}

            def permission_callback(allowed: bool, always_allow: bool):
                decision_result["allowed"] = allowed
                if allowed and always_allow:
                    self._always_allowed_commands.add(command)
                decision_event.set()

            if self.on_request_permission:
                self.on_request_permission(command, reason or "Dangerous operation", permission_callback)
            else:
                # No UI permission handler registered, deny by default
                permission_callback(False, False)

            decision_event.wait()

            if not decision_result["allowed"]:
                return {
                    "success": False,
                    "exit_code": -1,
                    "output": "Command execution was denied by the user.",
                    "error": "Permission denied by user.",
                    "command": command,
                }

        self._set_state(AgentState.RUNNING, f"Executing: {command}")
        self._emit_activity("command_start", f"Running command: $ {command}", command, {"command": command})

        result = self.shell_runner.execute_command(
            command=command,
            cwd=self.active_directory,
            on_stdout=self.on_command_output,
        )

        if result["success"]:
            self._emit_activity("command_success", f"Command completed (exit 0)", result["output"], {"exit_code": 0, "command": command})
        else:
            self._emit_activity("command_failed", f"Command failed (exit {result['exit_code']})", result["output"], {"exit_code": result["exit_code"], "command": command})

        return result

    def stop(self):
        """Request immediate stop of the agent loop and any running child process."""
        self._stop_requested = True
        self.shell_runner.stop_current_process()
        self._set_state(AgentState.STOPPED, "Task stopped by user")
        self._emit_activity("stopped", "Task stopped by user")

    def run_task_async(self, user_instruction: str):
        """Launch task loop in a background thread."""
        self._stop_requested = False
        self._thread = threading.Thread(target=self._run_task_loop, args=(user_instruction,), daemon=True)
        self._thread.start()

    def _run_task_loop(self, user_instruction: str):
        """Main autonomous agent loop."""
        self._set_state(AgentState.THINKING, "Understanding request...")

        # Check Ollama connection first
        healthy, err_msg, models = self.ollama.check_health()
        if not healthy:
            self._set_state(AgentState.FAILED, err_msg)
            self._emit_activity("error", "Ollama connection failed", err_msg)
            return

        # ------------------------------------------------------------------
        # MODE 1: KNOWLEDGE MODE (Direct ChatGPT-style markdown responses)
        # ------------------------------------------------------------------
        if self.mode == AgentMode.KNOWLEDGE:
            self._emit_activity("start", "Knowledge Consultation", user_instruction)
            system_prompt = get_system_prompt(self.active_directory, mode=AgentMode.KNOWLEDGE)
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_instruction},
            ]
            try:
                response = self.ollama.chat(
                    messages=messages,
                    tools=None,  # Pure markdown response without tool calls
                    model=self.config.model,
                    temperature=0.3,
                    context_length=self.config.context_length,
                )
                content = response.get("content", "")
                self._set_state(AgentState.COMPLETED, "Response ready")
                self._emit_activity("done", "Knowledge Answer", content or "No response generated.")
                return
            except Exception as e:
                self._set_state(AgentState.FAILED, f"Model error: {str(e)}")
                self._emit_activity("error", "Model query failed", str(e))
                return

        # ------------------------------------------------------------------
        # MODES 2 & 3: TASK & CODE MODES (Autonomous execution engine)
        # ------------------------------------------------------------------
        mode_title = "Code Engineering" if self.mode == AgentMode.CODE else "Task Execution"
        self._emit_activity("start", mode_title, user_instruction)

        # Prepare system prompt and messages
        system_prompt = get_system_prompt(
            workspace=self.workspace,
            mode=self.mode,
            tool_descriptions=self.registry.get_tool_descriptions(),
            project_dir=self.project_dir,
        )
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_instruction},
        ]

        step = 0
        max_steps = self.config.max_tool_calls

        while step < max_steps and not self._stop_requested:
            step += 1
            self._set_state(AgentState.THINKING, f"Thinking (step {step}/{max_steps})...")

            try:
                response = self.ollama.chat(
                    messages=messages,
                    tools=self.registry.get_ollama_tools(),
                    model=self.config.model,
                    temperature=self.config.temperature,
                    context_length=self.config.context_length,
                )
            except Exception as e:
                self._set_state(AgentState.FAILED, f"Model error: {str(e)}")
                self._emit_activity("error", "Model query failed", str(e))
                return

            if self._stop_requested:
                break

            content = response.get("content", "")
            raw_tool_calls = parse_tool_calls(response, valid_tool_names=list(self.registry._tools.keys()))

            # Check if user asked an informational / how-to question vs an action command
            is_question = self._is_informational_query(user_instruction)

            # If no tools were called:
            if not raw_tool_calls:
                # If it's a question/explanation request, ensure the answer is substantive
                if is_question:
                    if len(content.split()) < 35 and step < 3:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({
                            "role": "user",
                            "content": f"Now provide a thorough, complete explanation answering the user's question: '{user_instruction}' with key concepts and architecture."
                        })
                        continue

                    messages.append({"role": "assistant", "content": content})
                    self._set_state(AgentState.COMPLETED, "Response ready")
                    self._emit_activity("done", "Explanation / Guidance", content or "Finished.")
                    return

                if step > 1:
                    messages.append({"role": "assistant", "content": content})
                    self._set_state(AgentState.COMPLETED, "Task completed")
                    self._emit_activity("done", "Task completed", content or "Finished successfully.")
                    return

                # If it's an action command and the model hesitated/asked clarifying questions on step 1:
                hesitant_signals = ("?", "clarif", "typo", "mean by", "could you", "would you", "can you", "please provide", "please specify", "not sure")
                is_hesitant = any(sig in content.lower() for sig in hesitant_signals)

                if is_hesitant and step < 3:
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": "Do not ask questions or hesitate. You are an autonomous Linux desktop agent with full permission to use tools. Infer the user's intent, resolve any typos, and invoke the appropriate tool (such as run_command, write_file, or search_files) right now."
                    })
                    continue

                # Default fallback response
                messages.append({"role": "assistant", "content": content})
                self._set_state(AgentState.COMPLETED, "Task completed")
                self._emit_activity("done", "Task completed", content or "Finished successfully.")
                return

            # Append assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": response.get("tool_calls", [])
            })

            # Execute each tool call
            for call in raw_tool_calls:
                if self._stop_requested:
                    break

                tool_name = call["name"]
                tool_args = call.get("arguments", {})

                # Pretty activity label
                if tool_name == "run_command":
                    # Activity is emitted inside _execute_run_command_tool
                    pass
                elif tool_name == "write_file":
                    self._set_state(AgentState.RUNNING, f"Writing file: {tool_args.get('path', '')}")
                    self._emit_activity("file_write", f"Writing {tool_args.get('path', '')}", f"Content length: {len(tool_args.get('content', ''))} chars")
                elif tool_name == "edit_file":
                    self._set_state(AgentState.RUNNING, f"Editing file: {tool_args.get('path', '')}")
                    self._emit_activity("file_edit", f"Editing {tool_args.get('path', '')}")
                elif tool_name == "read_file":
                    self._set_state(AgentState.RUNNING, f"Reading file: {tool_args.get('path', '')}")
                    self._emit_activity("file_read", f"Reading {tool_args.get('path', '')}")
                elif tool_name == "list_directory":
                    self._set_state(AgentState.RUNNING, f"Inspecting directory: {tool_args.get('path', '.')}")
                    self._emit_activity("inspect", f"Inspecting {tool_args.get('path', '.')}")
                else:
                    self._set_state(AgentState.RUNNING, f"Tool: {tool_name}")
                    self._emit_activity("tool", f"Running tool {tool_name}", str(tool_args))

                tool_result = self.registry.execute(tool_name, tool_args)

                # Emit success/fail for non-shell tools
                if tool_name != "run_command":
                    if tool_result.get("success"):
                        self._emit_activity("success", f"✓ {tool_name} completed", tool_result.get("output"), {"diff": tool_result.get("diff")})
                    else:
                        self._emit_activity("error", f"✗ {tool_name} error", tool_result.get("error"))

                # Format tool response for Ollama conversation
                tool_output_str = json.dumps(tool_result, ensure_ascii=False)
                messages.append({
                    "role": "tool",
                    "content": tool_output_str,
                })

        if step >= max_steps and not self._stop_requested:
            self._set_state(AgentState.FAILED, f"Reached maximum tool call limit ({max_steps})")
            self._emit_activity("error", "Step limit reached", f"The agent exceeded the maximum limit of {max_steps} actions.")

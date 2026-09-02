#!/usr/bin/env python3
"""Main entry point for Native Linux Desktop AI Agent."""

import argparse
import sys
from pathlib import Path

from app.config import load_config
from app.ollama_client import OllamaClient


def run_health_check(config) -> bool:
    """Perform health checks and print report."""
    print("========================================")
    print(" Local AI Agent - System Health Check")
    print("========================================")

    # 1. Python Check
    print(f"✓ Python Version: {sys.version.split()[0]}")

    # 2. GTK4 Check
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk
        print("✓ GTK4: Available (PyGObject loaded)")
    except Exception as e:
        print(f"✗ GTK4: Failed ({e})")
        return False

    # 3. Workspace Check
    try:
        ws = config.resolved_workspace
        print(f"✓ Workspace: {ws} (Writable)")
    except Exception as e:
        print(f"✗ Workspace: Error ({e})")
        return False

    # 4. Ollama Server Check
    client = OllamaClient(config.ollama_url, config.model)
    healthy, msg, models = client.check_health()
    if healthy:
        print(f"✓ Ollama Server: Connected at {config.ollama_url}")
        print(f"  Available Models: {', '.join(models) if models else 'None'}")
        
        # 5. Model Check
        has_model = any(config.model.split(":")[0] in m for m in models)
        if has_model:
            print(f"✓ Model '{config.model}': Ready")
        else:
            print(f"⚠ Model '{config.model}': Not found in Ollama. Pull it with: ollama pull {config.model}")
    else:
        print(f"✗ Ollama Server: Not reachable ({msg})")
        print("  Please start Ollama with: ollama serve")
        return False

    print("========================================")
    print("All core components checked!")
    return True


def run_cli_mode(config, task_prompt: str, mode_str: str = "task", project_dir_str: Optional[str] = None):
    """Run an agent task in headless CLI mode."""
    from app.agent.agent import Agent, AgentState
    from app.agent.prompts import AgentMode

    mode = AgentMode(mode_str.lower()) if mode_str.lower() in ("knowledge", "task", "code") else AgentMode.TASK

    print(f"\n[AI Agent CLI Mode - {mode.value.upper()} MODE]")
    print(f"Workspace: {config.resolved_workspace}")
    if mode == AgentMode.CODE and project_dir_str:
        print(f"Project Dir: {Path(project_dir_str).resolve()}")
    print(f"Model: {config.model}")
    print(f"Prompt: {task_prompt}\n")

    def on_state(state: AgentState, detail: str):
        print(f"[{state.value}] {detail}")

    def on_activity(action_type: str, title: str, desc: str, meta: dict):
        prefix = "●"
        if action_type in ("success", "done"):
            prefix = "✓"
        elif action_type in ("error", "stopped"):
            prefix = "✗"
        elif action_type.startswith("command") or action_type.startswith("file"):
            prefix = "▶"
        print(f"  {prefix} {title}")
        if desc:
            print(f"    {desc}")

    def on_output(line: str):
        print(f"    | {line}")

    def on_perm(cmd: str, reason: str, callback):
        print(f"\n⚠ Permission required for: {cmd}")
        print(f"  Reason: {reason}")
        ans = input("  Allow this command? [y/N/always]: ").strip().lower()
        if ans in ("y", "yes"):
            callback(True, False)
        elif ans == "always":
            callback(True, True)
        else:
            callback(False, False)

    agent = Agent(
        config=config,
        on_state_changed=on_state,
        on_activity=on_activity,
        on_command_output=on_output,
        on_request_permission=on_perm,
    )
    agent.set_mode(mode)
    if project_dir_str:
        agent.set_project_dir(Path(project_dir_str))

    agent._run_task_loop(task_prompt)


def run_gui_mode(config):
    """Launch GTK4 Native GUI Application."""
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, GLib
    from app.ui.window import MainWindow

    class DesktopAIAgentApp(Gtk.Application):
        def __init__(self):
            super().__init__(application_id="io.antigravity.desktop_ai_agent")

        def do_activate(self):
            window = MainWindow(self, config)
            window.present()

    app = DesktopAIAgentApp()
    return app.run(sys.argv[:1])


def main():
    parser = argparse.ArgumentParser(description="Native Linux Desktop AI Agent for Arch Linux & Openbox")
    parser.add_argument("--config", "-c", help="Path to config file", default=None)
    parser.add_argument("--model", "-m", help="Override Ollama model name", default=None)
    parser.add_argument("--workspace", "-w", help="Override workspace path", default=None)
    parser.add_argument("--mode", choices=["knowledge", "task", "code"], default="task", help="Operating mode: knowledge, task, or code")
    parser.add_argument("--project-dir", "-p", help="Target project directory for code mode", default=None)
    parser.add_argument("--check", action="store_true", help="Run system health check and exit")
    parser.add_argument("--task", "-t", help="Run a single task directly in CLI mode", default=None)

    args = parser.parse_args()

    config = load_config(args.config)
    if args.model:
        config.model = args.model
    if args.workspace:
        config.workspace = args.workspace

    if args.check:
        success = run_health_check(config)
        sys.exit(0 if success else 1)

    if args.task:
        run_cli_mode(config, args.task, mode_str=args.mode, project_dir_str=args.project_dir)
        sys.exit(0)

    # Launch GUI
    run_gui_mode(config)


if __name__ == "__main__":
    main()

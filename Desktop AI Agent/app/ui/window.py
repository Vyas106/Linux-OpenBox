"""Desktop Panel & Sidebar AI Widget for Openbox Linux."""

import os
import subprocess
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib
from typing import Optional

from ..config import AppConfig
from ..ollama_client import OllamaClient
from ..agent.agent import Agent, AgentState
from ..agent.prompts import AgentMode
from .theme import load_theme
from .input_box import InputBox
from .activity_view import ActivityView
from .permission_dialog import PermissionBanner


class MainWindow(Gtk.ApplicationWindow):
    """Native Desktop Panel & Sidebar AI Assistant Widget docked on the desktop."""

    def __init__(self, app: Gtk.Application, config: AppConfig):
        super().__init__(application=app, title="Desktop AI Assistant")
        self.config = config
        self.current_project_dir = config.resolved_workspace
        self.add_css_class("main-window")
        
        # Desktop Panel dimensions (compact sidebar widget)
        self.set_default_size(440, 620)
        self.set_decorated(False)  # Frameless desktop widget

        load_theme()

        # Initialize Agent
        self.agent = Agent(
            config=self.config,
            on_state_changed=self._on_agent_state_changed,
            on_activity=self._on_agent_activity,
            on_command_output=self._on_command_output,
            on_request_permission=self._on_request_permission,
        )

        # Build Widget Content
        self._build_content()

        # Default mode
        self._switch_mode(AgentMode.TASK)

        # Health check
        self._check_ollama_health()

    def _build_content(self):
        """Construct desktop widget panel layout."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # 1. Custom Widget Top Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hdr.add_css_class("widget-header")

        icon_lbl = Gtk.Label(label="󰚩")
        icon_lbl.add_css_class("widget-title")
        hdr.append(icon_lbl)

        title_lbl = Gtk.Label(label="AI ASSISTANT")
        title_lbl.add_css_class("widget-title")
        hdr.append(title_lbl)

        self.model_badge = Gtk.Label(label=self.config.model)
        self.model_badge.add_css_class("subtitle-badge")
        hdr.append(self.model_badge)

        self.health_icon = Gtk.Label(label="●")
        self.health_icon.set_tooltip_text("Checking Ollama status...")
        hdr.append(self.health_icon)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        hdr.append(spacer)

        # Open workspace folder button
        btn_ws = Gtk.Button(label="📁")
        btn_ws.add_css_class("btn-header-action")
        btn_ws.set_tooltip_text("Open workspace folder")
        btn_ws.connect("clicked", self._open_workspace_folder)
        hdr.append(btn_ws)

        # Close / Hide widget button
        btn_close = Gtk.Button(label="✕")
        btn_close.add_css_class("btn-header-close")
        btn_close.set_tooltip_text("Hide / Close Desktop Assistant")
        btn_close.connect("clicked", lambda b: self.close())
        hdr.append(btn_close)

        main_box.append(hdr)

        # 2. Mode Switcher Segmented Bar
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        mode_box.add_css_class("mode-bar")

        self.btn_mode_knowledge = Gtk.Button(label="💡 Knowledge")
        self.btn_mode_knowledge.add_css_class("mode-btn")
        self.btn_mode_knowledge.connect("clicked", lambda b: self._switch_mode(AgentMode.KNOWLEDGE))
        self.btn_mode_knowledge.set_hexpand(True)

        self.btn_mode_task = Gtk.Button(label="⚡ Task")
        self.btn_mode_task.add_css_class("mode-btn")
        self.btn_mode_task.connect("clicked", lambda b: self._switch_mode(AgentMode.TASK))
        self.btn_mode_task.set_hexpand(True)

        self.btn_mode_code = Gtk.Button(label="💻 Code")
        self.btn_mode_code.add_css_class("mode-btn")
        self.btn_mode_code.connect("clicked", lambda b: self._switch_mode(AgentMode.CODE))
        self.btn_mode_code.set_hexpand(True)

        mode_box.append(self.btn_mode_knowledge)
        mode_box.append(self.btn_mode_task)
        mode_box.append(self.btn_mode_code)
        main_box.append(mode_box)

        # 3. Project Location Bar (Visible in Code Mode)
        self.project_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.project_bar.add_css_class("project-bar")

        proj_prefix = Gtk.Label(label="<span weight='bold' color='#89b4fa'>Project:</span>", use_markup=True)
        self.project_bar.append(proj_prefix)

        self.project_path_label = Gtk.Label(label=str(self.current_project_dir), xalign=0)
        self.project_path_label.add_css_class("project-dir-label")
        self.project_path_label.set_hexpand(True)
        self.project_bar.append(self.project_path_label)

        btn_choose_dir = Gtk.Button(label="Change")
        btn_choose_dir.add_css_class("btn-small-browse")
        btn_choose_dir.connect("clicked", self._on_select_project_dir)
        self.project_bar.append(btn_choose_dir)

        self.project_bar.set_visible(False)
        main_box.append(self.project_bar)

        # 4. Status Bar
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status_bar.set_margin_start(12)
        self.status_bar.set_margin_end(12)
        self.status_bar.set_margin_top(4)

        self.status_badge = Gtk.Label(label="IDLE")
        self.status_badge.add_css_class("status-badge")
        self.status_badge.add_css_class("status-idle")
        self.status_bar.append(self.status_badge)

        self.status_detail = Gtk.Label(label="Ready for instructions", xalign=0)
        self.status_detail.add_css_class("activity-card-desc")
        self.status_detail.set_hexpand(True)
        self.status_bar.append(self.status_detail)

        main_box.append(self.status_bar)

        # 5. Permission Banner
        self.permission_banner = PermissionBanner(on_decision=self._handle_permission_decision)
        main_box.append(self.permission_banner)

        # 6. Task Input Box
        self.input_box = InputBox(on_submit=self._on_submit_task, on_stop=self._on_stop_task)
        main_box.append(self.input_box)

        # 7. Activity Timeline Section Header
        act_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        act_header.set_margin_start(12)
        act_header.set_margin_end(12)
        act_header.set_margin_top(6)
        act_header.set_margin_bottom(2)

        self.act_label = Gtk.Label(label="<span size='small' weight='bold' color='#a6adc8'>ACTIVITY &amp; TIMELINE</span>", use_markup=True, xalign=0)
        self.act_label.set_hexpand(True)
        act_header.append(self.act_label)

        btn_clear = Gtk.Button(label="Clear")
        btn_clear.add_css_class("btn-flat")
        btn_clear.connect("clicked", lambda b: self.activity_view.clear())
        act_header.append(btn_clear)

        main_box.append(act_header)

        # 8. Activity View (Scrollable Feed)
        self.activity_view = ActivityView()
        self.activity_view.set_vexpand(True)
        main_box.append(self.activity_view)

        self.set_child(main_box)

    def _switch_mode(self, mode: AgentMode):
        """Switch active agent mode and update UI elements."""
        self.agent.set_mode(mode)

        for btn in (self.btn_mode_knowledge, self.btn_mode_task, self.btn_mode_code):
            btn.remove_css_class("mode-btn-active")

        if mode == AgentMode.KNOWLEDGE:
            self.btn_mode_knowledge.add_css_class("mode-btn-active")
            self.project_bar.set_visible(False)
            self.input_box.set_prompt_title("Ask anything (Knowledge & Guides):")
            self.status_detail.set_text("Knowledge Mode — Guides & Q&A")
        elif mode == AgentMode.TASK:
            self.btn_mode_task.add_css_class("mode-btn-active")
            self.project_bar.set_visible(False)
            self.input_box.set_prompt_title("What system task should I execute?")
            self.status_detail.set_text("Task Mode — Terminal & System")
        elif mode == AgentMode.CODE:
            self.btn_mode_code.add_css_class("mode-btn-active")
            self.project_bar.set_visible(True)
            self.input_box.set_prompt_title("Describe code, project, or tests to build:")
            self.status_detail.set_text(f"Code Mode — {self.current_project_dir.name}")

    def _on_select_project_dir(self, button):
        """Open folder chooser dialog to select project location."""
        native = Gtk.FileChooserNative.new(
            title="Select Project Location",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            accept_label="_Select",
            cancel_label="_Cancel",
        )

        def on_response(dialog, response_id):
            if response_id == Gtk.ResponseType.ACCEPT:
                file = dialog.get_file()
                if file:
                    selected_path = Path(file.get_path()).resolve()
                    self.current_project_dir = selected_path
                    self.project_path_label.set_text(str(selected_path))
                    self.agent.set_project_dir(selected_path)
                    self.status_detail.set_text(f"Code Mode — {selected_path.name}")
            dialog.destroy()

        native.connect("response", on_response)
        native.show()

    def _open_workspace_folder(self, button):
        """Open the active workspace/project directory in file manager."""
        target = str(self.agent.active_directory)
        try:
            subprocess.Popen(["xdg-open", target])
        except Exception:
            pass

    def _check_ollama_health(self):
        """Check Ollama connectivity and update header icon."""
        def check():
            client = OllamaClient(self.config.ollama_url, self.config.model)
            healthy, msg, models = client.check_health()
            GLib.idle_add(self._update_health_ui, healthy, msg, models)

        import threading
        threading.Thread(target=check, daemon=True).start()

    def _update_health_ui(self, healthy: bool, msg: str, models: list[str]):
        if healthy:
            has_model = any(self.config.model.split(":")[0] in m for m in models)
            if has_model:
                self.health_icon.set_markup("<span color='#a6e3a1'>●</span>")
                self.health_icon.set_tooltip_text(f"Ollama connected (model {self.config.model} ready)")
            else:
                self.health_icon.set_markup("<span color='#f9e2af'>●</span>")
                self.health_icon.set_tooltip_text(f"Model '{self.config.model}' not found")
        else:
            self.health_icon.set_markup("<span color='#f38ba8'>●</span>")
            self.health_icon.set_tooltip_text(f"Ollama offline: {msg}")
        return False

    def _on_submit_task(self, task_prompt: str):
        """Handle task submitted by user."""
        self.activity_view.clear()
        self.input_box.set_running_state(True)
        self.agent.run_task_async(task_prompt)

    def _on_stop_task(self):
        """Handle stop button clicked."""
        self.agent.stop()
        self.input_box.set_running_state(False)

    def _on_agent_state_changed(self, state: AgentState, detail: str):
        """Callback from agent thread."""
        GLib.idle_add(self._ui_update_state, state, detail)

    def _ui_update_state(self, state: AgentState, detail: str):
        for cls in ("status-idle", "status-thinking", "status-running", "status-waiting", "status-completed", "status-failed"):
            self.status_badge.remove_css_class(cls)

        self.status_badge.set_text(state.value)
        self.status_detail.set_text(detail or "")

        if state == AgentState.IDLE:
            self.status_badge.add_css_class("status-idle")
            self.input_box.set_running_state(False)
        elif state == AgentState.THINKING:
            self.status_badge.add_css_class("status-thinking")
            self.input_box.set_running_state(True)
        elif state == AgentState.RUNNING:
            self.status_badge.add_css_class("status-running")
            self.input_box.set_running_state(True)
        elif state == AgentState.WAITING_FOR_PERMISSION:
            self.status_badge.add_css_class("status-waiting")
        elif state == AgentState.COMPLETED:
            self.status_badge.add_css_class("status-completed")
            self.input_box.set_running_state(False)
        elif state in (AgentState.FAILED, AgentState.STOPPED):
            self.status_badge.add_css_class("status-failed")
            self.input_box.set_running_state(False)

        return False

    def _on_agent_activity(self, action_type: str, title: str, description: Optional[str], meta: Optional[dict]):
        """Dispatched activity update."""
        GLib.idle_add(self.activity_view.add_activity, action_type, title, description, meta)

    def _on_command_output(self, line: str):
        """Dispatched command stdout line."""
        GLib.idle_add(self.activity_view.append_command_stream, line)

    def _on_request_permission(self, command: str, reason: str, callback):
        """Show permission banner on GTK thread."""
        GLib.idle_add(self.permission_banner.show_request, command, reason, callback)

    def _handle_permission_decision(self, allowed: bool, always_allow: bool):
        pass

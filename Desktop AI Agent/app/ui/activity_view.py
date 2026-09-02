"""Activity feed timeline showing step-by-step progress and tool operations."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango
from typing import Any, Dict, Optional
from .command_view import CommandView


class ActivityView(Gtk.ScrolledWindow):
    """Live activity panel displaying high-level actions and collapsible tool logs."""

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.container.set_margin_top(8)
        self.container.set_margin_bottom(16)
        self.set_child(self.container)

        self.current_cmd_view: Optional[CommandView] = None

    def clear(self):
        """Clear all activity cards."""
        while child := self.container.get_first_child():
            self.container.remove(child)
        self.current_cmd_view = None

    def add_activity(
        self,
        action_type: str,
        title: str,
        description: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """Add a new activity item card to the timeline."""
        meta = meta or {}

        # If it's starting a command, create a CommandView
        if action_type == "command_start":
            cmd = meta.get("command", title)
            cmd_view = CommandView(cmd)
            self.container.append(cmd_view)
            self.current_cmd_view = cmd_view
            self._scroll_to_bottom()
            return

        # If it's finishing a command, update active CommandView
        if action_type in ("command_success", "command_failed") and self.current_cmd_view:
            exit_code = meta.get("exit_code", 0 if action_type == "command_success" else 1)
            self.current_cmd_view.set_finished(exit_code, description)
            self.current_cmd_view = None
            self._scroll_to_bottom()
            return

        # Regular activity card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        if action_type == "done":
            card.add_css_class("knowledge-card")
        else:
            card.add_css_class("activity-card")

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Icon based on action_type
        icon_str = "●"
        if action_type in ("success", "done"):
            icon_str = "✓"
        elif action_type in ("error", "stopped"):
            icon_str = "✗"
        elif action_type in ("file_write", "file_edit", "inspect"):
            icon_str = "▶"
        elif action_type == "permission":
            icon_str = "⚠"

        icon_label = Gtk.Label(label=icon_str)
        icon_label.add_css_class("activity-card-title")
        header.append(icon_label)

        import html
        clean_title = html.unescape(title)
        title_label = Gtk.Label(label=f"<b>{GLib.markup_escape_text(clean_title)}</b>", use_markup=True, xalign=0)
        title_label.set_hexpand(True)
        title_label.set_wrap(True)
        header.append(title_label)

        card.append(header)

        # Optional detail/description or diff
        if description and description.strip():
            clean_desc = html.unescape(description.strip())
            desc_label = Gtk.Label(label=GLib.markup_escape_text(clean_desc), xalign=0)
            desc_label.set_wrap(True)
            desc_label.set_selectable(True)
            if action_type == "done":
                desc_label.add_css_class("knowledge-desc")
            else:
                desc_label.add_css_class("activity-card-desc")
            card.append(desc_label)

        # If diff exists in meta
        diff = meta.get("diff")
        if diff:
            expander = Gtk.Expander(label="View File Diff")
            diff_text = Gtk.TextView()
            diff_text.set_editable(False)
            diff_text.set_monospace(True)
            diff_text.add_css_class("diff-view")
            diff_text.get_buffer().set_text(diff)
            expander.set_child(diff_text)
            card.append(expander)

        self.container.append(card)
        self._scroll_to_bottom()

    def append_command_stream(self, line: str):
        """Forward stdout line to current CommandView."""
        if self.current_cmd_view:
            self.current_cmd_view.append_output(line)

    def _scroll_to_bottom(self):
        """Scroll adjustment to bottom."""
        GLib.idle_add(self._do_scroll)

    def _do_scroll(self):
        adj = self.get_vadjustment()
        adj.set_value(adj.get_upper())
        return False

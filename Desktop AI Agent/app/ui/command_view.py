"""Terminal-styled command output widget for live streaming execution."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango
from typing import Optional


class CommandView(Gtk.Box):
    """Expandable terminal viewer for command execution."""

    def __init__(self, command: str):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.command = command
        self.add_css_class("activity-card")

        # Top Header row
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.icon = Gtk.Label(label="▶")
        self.icon.add_css_class("activity-card-title")
        header.append(self.icon)

        title = Gtk.Label(label=f"<b>$ {GLib.markup_escape_text(command)}</b>", use_markup=True, xalign=0)
        title.set_hexpand(True)
        title.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        header.append(title)

        self.status_badge = Gtk.Label(label="running")
        self.status_badge.add_css_class("subtitle-badge")
        header.append(self.status_badge)

        self.append(header)

        # Scrolled output area
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_min_content_height(80)
        self.scrolled.set_max_content_height(240)
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.add_css_class("terminal-box")

        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        self.text_view.add_css_class("terminal-text")
        self.buffer = self.text_view.get_buffer()
        self.scrolled.set_child(self.text_view)

        self.append(self.scrolled)

    def append_output(self, text: str):
        """Append streamed stdout/stderr text and scroll to end."""
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert(end_iter, text + "\n")
        
        # Scroll to bottom
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper())

    def set_finished(self, exit_code: int, full_output: Optional[str] = None):
        """Update badge and status icon upon completion."""
        if exit_code == 0:
            self.icon.set_text("✓")
            self.status_badge.set_text("exit 0")
            self.status_badge.remove_css_class("status-running")
            self.status_badge.add_css_class("status-completed")
        else:
            self.icon.set_text("✗")
            self.status_badge.set_text(f"exit {exit_code}")
            self.status_badge.remove_css_class("status-running")
            self.status_badge.add_css_class("status-failed")

        if full_output and not self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), False):
            self.buffer.set_text(full_output)

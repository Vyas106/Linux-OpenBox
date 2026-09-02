"""Permission dialog and inline banner for authorizing dangerous commands."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from typing import Callable, Optional


class PermissionBanner(Gtk.Box):
    """An inline approval banner displayed when the agent requests permission."""

    def __init__(self, on_decision: Callable[[bool, bool], None]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.on_decision = on_decision
        self.add_css_class("permission-banner")
        self.set_visible(False)

        # Header with icon
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        title = Gtk.Label(label="<b>Permission Required</b>", use_markup=True)
        title.set_halign(Gtk.Align.START)
        header_box.append(warning_icon)
        header_box.append(title)
        self.append(header_box)

        # Reason / Description
        self.reason_label = Gtk.Label(label="", xalign=0)
        self.reason_label.set_wrap(True)
        self.append(self.reason_label)

        # Command terminal view
        self.cmd_box = Gtk.Label(label="", xalign=0)
        self.cmd_box.add_css_class("terminal-box")
        self.cmd_box.set_selectable(True)
        self.append(self.cmd_box)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.END)

        self.btn_deny = Gtk.Button(label="Deny")
        self.btn_deny.add_css_class("btn-danger")
        self.btn_deny.connect("clicked", self._on_deny_clicked)

        self.btn_always = Gtk.Button(label="Always Allow")
        self.btn_always.connect("clicked", self._on_always_clicked)

        self.btn_allow = Gtk.Button(label="Allow")
        self.btn_allow.add_css_class("btn-primary")
        self.btn_allow.connect("clicked", self._on_allow_clicked)

        btn_box.append(self.btn_deny)
        btn_box.append(self.btn_always)
        btn_box.append(self.btn_allow)
        self.append(btn_box)

    def show_request(self, command: str, reason: str, callback: Callable[[bool, bool], None]):
        """Present the permission request to user."""
        self.current_callback = callback
        self.reason_label.set_markup(f"The AI wants to run a sensitive command:\n<span color='#a6adc8'>{GLib.markup_escape_text(reason)}</span>")
        self.cmd_box.set_text(f"$ {command}")
        self.set_visible(True)

    def _on_allow_clicked(self, button):
        self.set_visible(False)
        if hasattr(self, "current_callback") and self.current_callback:
            self.current_callback(True, False)

    def _on_always_clicked(self, button):
        self.set_visible(False)
        if hasattr(self, "current_callback") and self.current_callback:
            self.current_callback(True, True)

    def _on_deny_clicked(self, button):
        self.set_visible(False)
        if hasattr(self, "current_callback") and self.current_callback:
            self.current_callback(False, False)

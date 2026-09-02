"""Task Input Box with Enter to submit and Shift+Enter for newline."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib
from typing import Callable


class InputBox(Gtk.Box):
    """Task input box with Run and Stop controls."""

    def __init__(self, on_submit: Callable[[str], None], on_stop: Callable[[], None]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.on_submit = on_submit
        self.on_stop = on_stop

        # Container styling
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.container.add_css_class("input-container")

        # Label prompt
        self.prompt_label = Gtk.Label(label="<b>What do you want me to do?</b>", use_markup=True, xalign=0)
        self.container.append(self.prompt_label)

        # Scrolled Text View
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(60)
        scrolled.set_max_content_height(140)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.text_view = Gtk.TextView()
        self.text_view.add_css_class("task-textview")
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.buffer = self.text_view.get_buffer()
        scrolled.set_child(self.text_view)
        self.container.append(scrolled)

        # Bottom row: hint & action button
        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.hint_label = Gtk.Label(
            label="<span size='small' color='#6c7086'>Press <b>Enter</b> to run, <b>Shift+Enter</b> for newline</span>",
            use_markup=True,
            xalign=0,
        )
        self.hint_label.set_hexpand(True)
        bottom_row.append(self.hint_label)

        # Run Button
        self.btn_run = Gtk.Button(label="Run")
        self.btn_run.add_css_class("btn-primary")
        self.btn_run.connect("clicked", self._on_run_clicked)
        bottom_row.append(self.btn_run)

        # Stop Button (initially hidden)
        self.btn_stop = Gtk.Button(label="Stop")
        self.btn_stop.add_css_class("btn-danger")
        self.btn_stop.connect("clicked", self._on_stop_clicked)
        self.btn_stop.set_visible(False)
        bottom_row.append(self.btn_stop)

        self.container.append(bottom_row)
        self.append(self.container)

        # Setup key event controller for Enter vs Shift+Enter
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.text_view.add_controller(key_controller)

    def set_prompt_title(self, title: str):
        """Update prompt title dynamically."""
        self.prompt_label.set_markup(f"<b>{GLib.markup_escape_text(title)}</b>")

    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle Enter key to submit or Shift+Enter to newline."""
        is_enter = (keyval == Gdk.KEY_Return or keyval == Gdk.KEY_KP_Enter)
        is_shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        if is_enter and not is_shift:
            self._trigger_submit()
            return True  # Handled
        return False

    def _trigger_submit(self):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        text = self.buffer.get_text(start, end, False).strip()
        if text and self.btn_run.get_visible():
            self.on_submit(text)

    def _on_run_clicked(self, button):
        self._trigger_submit()

    def _on_stop_clicked(self, button):
        self.on_stop()

    def set_running_state(self, is_running: bool):
        """Switch between Run and Stop buttons."""
        self.btn_run.set_visible(not is_running)
        self.btn_stop.set_visible(is_running)
        self.text_view.set_editable(not is_running)

    def clear(self):
        self.buffer.set_text("")

    def set_text(self, text: str):
        self.buffer.set_text(text)

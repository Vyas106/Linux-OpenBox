#!/usr/bin/env python3
"""
desktop_input_box.py - Sleek AI Desktop Input & Companion Widget for Openbox Linux
Positioned directly on top of the Bottom-Left Conky Greeting Box with matching width & aesthetic.
Features:
 - Pure monochrome dark aesthetic matching Conky Greeting
 - Dynamic 4-5 rows expandable multi-line input box
 - In-box conversation replies with real-time Ollama streaming
 - 4 Bottom Action Buttons: [Model], [Level: Short/Med/Exp], [Mode: Task/Knowledge/Code], [Send]
 - Auto-snapping geometry docking right above ConkyGreeting window
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import threading
import subprocess
from datetime import datetime
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

# Code syntax highlighting keywords
KEYWORDS = {
    'import', 'from', 'as', 'def', 'class', 'return', 'if', 'elif', 'else',
    'for', 'while', 'in', 'try', 'except', 'finally', 'with', 'lambda',
    'yield', 'async', 'await', 'pass', 'break', 'continue', 'global',
    'const', 'let', 'var', 'function', 'export', 'default', 'new', 'this',
    'echo', 'sudo', 'cat', 'grep', 'pacman', 'git', 'export', 'source', 'bash',
    'sh', 'chmod', 'mkdir', 'rm', 'cp', 'mv', 'systemctl',
    'None', 'True', 'False', 'null', 'true', 'false', 'int', 'float', 'str', 'bool',
    'void', 'public', 'private', 'static', 'self'
}

# -----------------------------------------------------------------------------
# CSS STYLING (Monochrome Conky Aesthetic with Green Status Accents)
# -----------------------------------------------------------------------------
CSS_DATA = """
/* Reset all button defaults across GTK to prevent light-theme gradient leak */
button, button * {
    background-image: none;
    box-shadow: none;
    text-shadow: none;
    outline: none;
}

button {
    background-image: none;
    background-color: #121212;
    border: 1px solid #282828;
    border-radius: 5px;
    box-shadow: none;
    text-shadow: none;
    outline: none;
    color: #A0A0A0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    padding: 4px 8px;
    transition: all 120ms ease-in-out;
}

button:hover {
    background-color: #000000;
    background-image: none;
    color: #FFFFFF;
    border-color: #484848;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
}

button:active {
    background-color: #050505;
    background-image: none;
    color: #FFFFFF;
    border-color: #606060;
}

window.desktop-ai-window {
    background-color: transparent;
}

box.main-card {
    background-color: rgba(10, 10, 10, 0.95);
    border: 1px solid #262626;
    border-radius: 8px;
    padding: 10px 14px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.9);
}

/* Header */
label.header-title {
    color: #D4D4D4;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 11px;
    font-weight: bold;
}

label.status-badge {
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9px;
    font-weight: bold;
    color: #50FA7B;
}

label.status-badge.busy {
    color: #FFB86C;
}

label.status-badge.error {
    color: #FF5555;
}

separator.divider {
    background-color: #202020;
    min-height: 1px;
    margin-top: 6px;
    margin-bottom: 6px;
}

/* Response / Chat Area */
scrolledwindow.response-scroll {
    background-color: transparent;
    border: none;
}

textview.response-view {
    background-color: transparent;
    color: #D0D0D0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 10px;
}

textview.response-view text {
    background-color: transparent;
    color: #D0D0D0;
}

/* Input Area */
box.input-wrapper {
    background-color: #0E0E0E;
    border: 1px solid #262626;
    border-radius: 6px;
    padding: 6px 8px;
    transition: all 150ms ease;
}

box.input-wrapper:focus-within {
    border-color: #50FA7B;
    background-color: #050505;
    box-shadow: 0 0 8px rgba(80, 250, 123, 0.18);
}

textview.input-textview {
    background-color: transparent;
    color: #F8F8F2;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 10.5px;
}

textview.input-textview text {
    background-color: transparent;
    color: #F8F8F2;
}

/* Bottom Controls */
box.bottom-bar {
    margin-top: 8px;
}

button.control-btn {
    background-color: #141414;
    background-image: none;
    border: 1px solid #282828;
    border-radius: 5px;
    color: #A4A4A4;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9.5px;
    font-weight: 500;
    padding: 5px 10px;
    transition: all 120ms ease;
}

button.control-btn:hover {
    background-color: #000000;
    background-image: none;
    color: #FFFFFF;
    border-color: #505050;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
}

button.control-btn.active-btn {
    color: #50FA7B;
    border-color: #50FA7B;
    background-color: #0A140E;
}

button.send-btn {
    background-color: #102416;
    background-image: none;
    border: 1px solid #2A6E3B;
    border-radius: 5px;
    color: #50FA7B;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 10px;
    font-weight: bold;
    padding: 5px 13px;
    transition: all 120ms ease;
}

button.send-btn:hover {
    background-color: #000000;
    background-image: none;
    color: #FFFFFF;
    border-color: #50FA7B;
    box-shadow: 0 0 8px rgba(80, 250, 123, 0.35);
}

button.send-btn.stop-btn {
    background-color: #261010;
    background-image: none;
    border-color: #8C2C2C;
    color: #FF6666;
}

button.send-btn.stop-btn:hover {
    background-color: #000000;
    background-image: none;
    color: #FFFFFF;
    border-color: #FF5555;
    box-shadow: 0 0 8px rgba(255, 85, 85, 0.35);
}

/* Header Action Buttons (Copy & Clear) */
button.icon-tool-btn {
    background: transparent;
    background-color: transparent;
    background-image: none;
    border: 1px solid transparent;
    box-shadow: none;
    color: #707070;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 11px;
    padding: 2px 5px;
    border-radius: 4px;
    min-height: 18px;
    min-width: 20px;
    transition: all 120ms ease;
}

button.icon-tool-btn:hover {
    background-color: #000000;
    background-image: none;
    border-color: #333333;
    color: #FFFFFF;
}

/* Scrollbars */
scrollbar, scrollbar button, scrollbar trough {
    background-color: transparent;
    border: none;
}

scrollbar slider {
    min-width: 4px;
    min-height: 4px;
    border-radius: 2px;
    background-color: #2E2E2E;
}

scrollbar slider:hover {
    background-color: #4A4A4A;
}

/* Popup Menu */
menu, .menu {
    background-color: #0E0E0E;
    border: 1px solid #2A2A2A;
    border-radius: 6px;
    padding: 4px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.85);
}

menuitem, .menuitem {
    padding: 5px 10px;
    border-radius: 4px;
    color: #B0B0B0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9.5px;
}

menuitem:hover, .menuitem:hover {
    background-color: #000000;
    color: #FFFFFF;
    border: 1px solid #3A3A3A;
}

/* Tooltip */
tooltip {
    background-color: #0A0A0A;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 4px 8px;
    color: #E0E0E0;
}

tooltip * {
    background-color: transparent;
    color: #E0E0E0;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", monospace;
    font-size: 9.5px;
}
"""

LEVELS = ["Short", "Medium", "Expert"]
MODES = ["Task", "Knowledge", "Code"]


class DesktopInputBox(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Desktop AI Companion")
        self.set_wmclass("DesktopInputBox", "DesktopInputBox")
        
        # Geometry defaults (matches 470px Conky width)
        self.BOX_WIDTH = 470
        self.conky_geometry = None
        
        # State
        self.ollama_url = "http://localhost:11434"
        self.available_models = ["qwen2.5:3b"]
        self.selected_model = "qwen2.5:3b"
        self.selected_level = "Medium"
        self.selected_mode = "Task"
        self.is_generating = False
        self.stop_requested = False
        self.current_stream_thread = None
        self.user_prompt_text = ""
        self.raw_assistant_response = ""
        
        # Window attributes
        self.set_size_request(self.BOX_WIDTH, -1)
        self.set_resizable(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(False)
        self.stick()
        
        # Transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
            
        self.load_css()
        self.build_ui()
        
        # Key bindings
        self.connect("key-press-event", self.on_global_key_press)
        self.connect("realize", self.on_realize)
        self.connect("size-allocate", self.on_size_allocate)
        
        # Fetch installed models in background
        threading.Thread(target=self.fetch_ollama_models, daemon=True).start()

    def load_css(self):
        self.get_style_context().add_class("desktop-ai-window")
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_DATA.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def build_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.get_style_context().add_class("main-card")
        self.main_box.set_size_request(self.BOX_WIDTH, -1)
        
        # 1. Header Row
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.lbl_title = Gtk.Label()
        self.lbl_title.set_markup("<b>󰚩 AI COMPANION</b>")
        self.lbl_title.get_style_context().add_class("header-title")
        header.pack_start(self.lbl_title, False, False, 0)
        
        # Status Badge (ACTIVE / BUSY / ERROR)
        self.lbl_status = Gtk.Label(label="● ACTIVE")
        self.lbl_status.get_style_context().add_class("status-badge")
        header.pack_start(self.lbl_status, False, False, 4)
        
        # Header Right Tools
        header_tools = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        
        # Copy Response Button
        self.btn_copy = Gtk.Button(label="󰆏")
        self.btn_copy.get_style_context().add_class("icon-tool-btn")
        self.btn_copy.set_tooltip_text("Copy AI response")
        self.btn_copy.connect("clicked", self.on_copy_response)
        self.btn_copy.set_visible(False)
        header_tools.pack_start(self.btn_copy, False, False, 0)
        
        # Clear / Collapse Button
        self.btn_clear = Gtk.Button(label="󰅖")
        self.btn_clear.get_style_context().add_class("icon-tool-btn")
        self.btn_clear.set_tooltip_text("Clear response and input (Esc)")
        self.btn_clear.connect("clicked", self.on_clear_all)
        header_tools.pack_start(self.btn_clear, False, False, 0)
        
        header.pack_end(header_tools, False, False, 0)
        self.main_box.pack_start(header, False, False, 0)
        
        # Divider
        self.divider1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.divider1.get_style_context().add_class("divider")
        self.main_box.pack_start(self.divider1, False, False, 0)
        
        # 2. Response / Chat Area (Expandable on reply)
        self.response_scroll = Gtk.ScrolledWindow()
        self.response_scroll.get_style_context().add_class("response-scroll")
        self.response_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.response_scroll.set_propagate_natural_height(True)
        self.response_scroll.set_min_content_height(0)
        self.response_scroll.set_max_content_height(self.get_max_allowed_response_height())
        self.response_scroll.set_visible(False)
        
        self.response_view = Gtk.TextView()
        self.response_view.get_style_context().add_class("response-view")
        self.response_view.set_editable(False)
        self.response_view.set_cursor_visible(False)
        self.response_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.response_view.set_left_margin(4)
        self.response_view.set_right_margin(4)
        self.response_view.set_pixels_above_lines(2)
        self.response_view.set_pixels_below_lines(2)
        self.response_buffer = self.response_view.get_buffer()
        
        # Comprehensive Markdown & Code Syntax Tags
        self.tags = {
            'h1': self.response_buffer.create_tag("h1", weight=Pango.Weight.BOLD, foreground="#50FA7B", scale=1.14),
            'h2': self.response_buffer.create_tag("h2", weight=Pango.Weight.BOLD, foreground="#8BE9FD", scale=1.08),
            'h3': self.response_buffer.create_tag("h3", weight=Pango.Weight.BOLD, foreground="#F1FA8C", scale=1.03),
            'h4': self.response_buffer.create_tag("h4", weight=Pango.Weight.BOLD, foreground="#BD93F9"),
            'bold': self.response_buffer.create_tag("bold", weight=Pango.Weight.BOLD, foreground="#FFFFFF"),
            'italic': self.response_buffer.create_tag("italic", style=Pango.Style.ITALIC, foreground="#D0D0D0"),
            'inline_code': self.response_buffer.create_tag("inline_code", foreground="#50FA7B", background="#181818", font="JetBrainsMono Nerd Font 9.5"),
            'bullet': self.response_buffer.create_tag("bullet", foreground="#50FA7B", weight=Pango.Weight.BOLD),
            'quote': self.response_buffer.create_tag("quote", foreground="#8BE9FD", style=Pango.Style.ITALIC),
            'code_header': self.response_buffer.create_tag("code_header", foreground="#6272A4", font="JetBrainsMono Nerd Font 9"),
            'code_block': self.response_buffer.create_tag("code_block", foreground="#ECEFF4", font="JetBrainsMono Nerd Font 9.5"),
            'code_kw': self.response_buffer.create_tag("code_kw", foreground="#FF79C6", weight=Pango.Weight.BOLD, font="JetBrainsMono Nerd Font 9.5"),
            'code_str': self.response_buffer.create_tag("code_str", foreground="#F1FA8C", font="JetBrainsMono Nerd Font 9.5"),
            'code_com': self.response_buffer.create_tag("code_com", foreground="#6272A4", style=Pango.Style.ITALIC, font="JetBrainsMono Nerd Font 9.5"),
            'prompt': self.response_buffer.create_tag("prompt", foreground="#50FA7B", weight=Pango.Weight.BOLD),
            'ai_title': self.response_buffer.create_tag("ai_title", foreground="#8BE9FD", weight=Pango.Weight.BOLD),
            'meta': self.response_buffer.create_tag("meta", foreground="#707070", scale=0.85),
            'error': self.response_buffer.create_tag("error", foreground="#FF5555"),
        }
        
        self.response_scroll.add(self.response_view)
        self.main_box.pack_start(self.response_scroll, True, True, 0)
        
        self.divider2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.divider2.get_style_context().add_class("divider")
        self.divider2.set_visible(False)
        self.main_box.pack_start(self.divider2, False, False, 0)
        
        # 3. Dynamic Multi-Line Input Box (4-5 rows)
        self.input_wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.input_wrapper.get_style_context().add_class("input-wrapper")
        
        # Multi-line TextView
        self.input_scroll = Gtk.ScrolledWindow()
        self.input_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.input_scroll.set_min_content_height(32)
        self.input_scroll.set_max_content_height(96)  # ~4 to 5 lines
        self.input_scroll.set_hexpand(True)
        
        self.input_view = Gtk.TextView()
        self.input_view.get_style_context().add_class("input-textview")
        self.input_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.input_view.set_accepts_tab(False)
        self.input_buffer = self.input_view.get_buffer()
        self.input_buffer.connect("changed", self.on_input_changed)
        self.input_view.connect("key-press-event", self.on_input_key_press)
        
        # Placeholder simulation
        self.placeholder_text = "Ask AI, run task, or search... (Enter to send, Shift+Enter for newline)"
        self.is_placeholder = True
        self.set_placeholder()
        self.input_view.connect("focus-in-event", self.on_input_focus_in)
        self.input_view.connect("focus-out-event", self.on_input_focus_out)
        
        self.input_scroll.add(self.input_view)
        self.input_wrapper.pack_start(self.input_scroll, True, True, 0)
        
        self.main_box.pack_start(self.input_wrapper, False, False, 0)
        
        # 4. Bottom Controls Bar: 4 Buttons
        # [ Model ] [ Level: Short/Med/Exp ] [ Mode: Task/Know/Code ] [ Send ]
        self.bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.bottom_bar.get_style_context().add_class("bottom-bar")
        
        # Button 1: Model
        self.btn_model = Gtk.Button(label="󰚩 Model")
        self.btn_model.get_style_context().add_class("control-btn")
        self.btn_model.set_tooltip_text("Switch Ollama Model")
        self.btn_model.connect("clicked", self.on_model_clicked)
        self.bottom_bar.pack_start(self.btn_model, True, True, 0)
        
        # Button 2: Level [Short, Medium, Expert]
        self.btn_level = Gtk.Button(label=f"󰮔 {self.selected_level}")
        self.btn_level.get_style_context().add_class("control-btn")
        self.btn_level.set_tooltip_text("Toggle Response Depth: Short / Medium / Expert")
        self.btn_level.connect("clicked", self.on_level_clicked)
        self.bottom_bar.pack_start(self.btn_level, True, True, 0)
        
        # Button 3: Mode [Task, Knowledge, Code]
        self.btn_mode = Gtk.Button(label=f"󰒓 {self.selected_mode}")
        self.btn_mode.get_style_context().add_class("control-btn")
        self.btn_mode.set_tooltip_text("Toggle Mode: Task / Knowledge / Code")
        self.btn_mode.connect("clicked", self.on_mode_clicked)
        self.bottom_bar.pack_start(self.btn_mode, True, True, 0)
        
        # Button 4: Send
        self.btn_send = Gtk.Button(label="󰒭 Send")
        self.btn_send.get_style_context().add_class("send-btn")
        self.btn_send.set_tooltip_text("Execute Prompt / Command (Enter)")
        self.btn_send.connect("clicked", self.on_send_clicked)
        self.bottom_bar.pack_start(self.btn_send, False, False, 0)
        
        self.main_box.pack_start(self.bottom_bar, False, False, 0)
        
        self.add(self.main_box)

    # -------------------------------------------------------------------------
    # Placeholders & Input Handling
    # -------------------------------------------------------------------------
    def set_placeholder(self):
        if not self.input_buffer.get_text(self.input_buffer.get_start_iter(), self.input_buffer.get_end_iter(), True).strip():
            self.is_placeholder = True
            self.input_buffer.set_text(self.placeholder_text)
            self.input_view.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.5, 0.5, 0.5, 0.7))

    def on_input_focus_in(self, widget, event):
        if self.is_placeholder:
            self.is_placeholder = False
            self.input_buffer.set_text("")
            self.input_view.override_color(Gtk.StateFlags.NORMAL, None)
        return False

    def on_input_focus_out(self, widget, event):
        text = self.input_buffer.get_text(self.input_buffer.get_start_iter(), self.input_buffer.get_end_iter(), True).strip()
        if not text:
            self.set_placeholder()
        return False

    def on_input_changed(self, buffer):
        if self.is_placeholder:
            return
        # Calculate line count to dynamically adjust height up to 5 rows
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        lines = max(1, text.count("\n") + 1 + len(text) // 48)
        # Approximate line height: 18px
        target_height = min(96, max(32, lines * 18 + 12))
        self.input_scroll.set_min_content_height(target_height)

    def on_input_key_press(self, widget, event):
        # Enter without Shift triggers send
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                # Insert newline
                return False
            else:
                self.on_send_clicked(None)
                return True
        elif event.keyval == Gdk.KEY_Escape:
            self.on_clear_all(None)
            return True
        return False

    def on_global_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.on_clear_all(None)
            return True
        return False

    # -------------------------------------------------------------------------
    # Conky Docking Geometry Snapping
    # -------------------------------------------------------------------------
    def get_conky_geometry(self):
        try:
            gi.require_version("GdkX11", "3.0")
            from gi.repository import GdkX11
            out = subprocess.check_output(["xprop", "-root", "_NET_CLIENT_LIST"], stderr=subprocess.DEVNULL).decode()
            win_ids = [w.strip() for w in out.split("#")[1].split(",") if w.strip()]
            disp = Gdk.Display.get_default()
            for wid_str in win_ids:
                prop = subprocess.check_output(["xprop", "-id", wid_str, "WM_CLASS"], stderr=subprocess.DEVNULL).decode()
                if "ConkyGreeting" in prop:
                    wid = int(wid_str, 16)
                    xwin = GdkX11.X11Window.foreign_new_for_display(disp, wid)
                    if xwin:
                        _, ox, oy = xwin.get_origin()
                        _, _, w, h = xwin.get_geometry()
                        return ox, oy, w, h
        except Exception:
            pass
        return None

    def get_max_allowed_response_height(self):
        TOP_PANEL_MARGIN = 44  # Space for top Polybar panel
        screen = self.get_screen()
        sh = screen.get_height()
        geom = self.get_conky_geometry() or self.conky_geometry
        if geom:
            _, conky_y, _, _ = geom
        else:
            conky_y = sh - 175
            
        # Total available height between Conky greeting and the top panel
        available_height = max(180, (conky_y - 6) - TOP_PANEL_MARGIN)
        # Fixed UI overhead: header, dividers, input box, bottom controls (~160px)
        overhead = 160
        max_response_h = max(120, available_height - overhead)
        return max_response_h

    def calculate_response_needed_height(self):
        """Calculate required pixel height for the response TextView as text streams."""
        text = self.response_buffer.get_text(
            self.response_buffer.get_start_iter(),
            self.response_buffer.get_end_iter(),
            True
        )
        if not text.strip():
            return 0
            
        total_lines = 0
        for l in text.split("\n"):
            # ~48 chars per line in 440-470px width
            total_lines += max(1, (len(l) + 47) // 48)
            
        estimated_height = total_lines * 19 + 20
        
        try:
            end_iter = self.response_buffer.get_end_iter()
            rect = self.response_view.get_iter_location(end_iter)
            iter_height = rect.y + rect.height + 20
            return max(estimated_height, iter_height)
        except Exception:
            return estimated_height

    def adjust_response_height(self):
        """Dynamically resize response area as text grows, capping at top panel and scrolling thereafter."""
        if not self.response_scroll.get_visible():
            return
            
        max_allowed = self.get_max_allowed_response_height()
        needed = self.calculate_response_needed_height()
        
        # Height dynamically matches text content, clamped at max_allowed (touching top panel)
        target_height = min(needed, max_allowed)
        target_height = max(35, target_height)
        
        self.response_scroll.set_min_content_height(target_height)
        self.response_scroll.set_max_content_height(max_allowed)
        
        self.reposition_above_conky()
        
        # When text reaches top panel max height, auto-scroll to bottom smoothly
        if needed >= max_allowed:
            adj = self.response_scroll.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

    def reposition_above_conky(self):
        """Keep bottom edge of this widget docked directly above ConkyGreeting, dynamically expanding upwards up to top panel."""
        TOP_PANEL_MARGIN = 44  # Polybar panel margin
        geom = self.get_conky_geometry() or self.conky_geometry
        screen = self.get_screen()
        sh = screen.get_height()
        
        if geom:
            self.conky_geometry = geom
            conky_x, conky_y, conky_w, _ = geom
            self.BOX_WIDTH = conky_w
            target_bottom = conky_y - 6
            target_x = conky_x
        else:
            target_bottom = sh - 175
            target_x = 9
            
        # Update maximum allowable response scroll height
        max_resp_h = self.get_max_allowed_response_height()
        self.response_scroll.set_max_content_height(max_resp_h)
        
        # Calculate target Y based on current window height
        _, height = self.get_size()
        target_y = target_bottom - height
        
        # Limit upward expansion so it maxes out cleanly right below the top panel
        if target_y < TOP_PANEL_MARGIN:
            target_y = TOP_PANEL_MARGIN
            
        self.move(target_x, target_y)

    def on_size_allocate(self, widget, allocation):
        # Reposition to stay locked right above the greeting box when height changes
        GLib.idle_add(self.reposition_above_conky)

    def on_realize(self, widget):
        self.reposition_above_conky()
        GLib.timeout_add(1000, self._periodic_snap_check, 0)

    def _periodic_snap_check(self, count):
        self.reposition_above_conky()
        if count < 5:
            GLib.timeout_add(1000, self._periodic_snap_check, count + 1)
        return False

    # -------------------------------------------------------------------------
    # Button Actions: Model, Level, Mode, Send
    # -------------------------------------------------------------------------
    def fetch_ollama_models(self):
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", headers={"User-Agent": "DesktopAI"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    if models:
                        self.available_models = models
                        if self.selected_model not in models:
                            self.selected_model = models[0]
                        GLib.idle_add(self.update_model_button_label)
        except Exception:
            pass

    def update_model_button_label(self):
        short_name = self.selected_model.split(":")[0]
        if len(short_name) > 12:
            short_name = short_name[:10] + ".."
        self.btn_model.set_label(f"󰚩 {short_name}")
        self.btn_model.set_tooltip_text(f"Model: {self.selected_model} (Click to switch)")

    def on_model_clicked(self, widget):
        if not self.available_models:
            return
        # Open a popup menu with all available models
        menu = Gtk.Menu()
        for m in self.available_models:
            item = Gtk.MenuItem(label=f"󰚩  {m}")
            item.connect("activate", self._set_model, m)
            menu.append(item)
        menu.show_all()
        menu.popup_at_widget(widget, Gdk.Gravity.SOUTH, Gdk.Gravity.NORTH, None)

    def _set_model(self, widget, model_name):
        self.selected_model = model_name
        self.update_model_button_label()

    def on_level_clicked(self, widget):
        idx = (LEVELS.index(self.selected_level) + 1) % len(LEVELS)
        self.selected_level = LEVELS[idx]
        self.btn_level.set_label(f"󰮔 {self.selected_level}")
        self.btn_level.set_tooltip_text(f"Response Level: {self.selected_level}")

    def on_mode_clicked(self, widget):
        idx = (MODES.index(self.selected_mode) + 1) % len(MODES)
        self.selected_mode = MODES[idx]
        icon = "󰒓" if self.selected_mode == "Task" else ("󰈙" if self.selected_mode == "Knowledge" else "󰅩")
        self.btn_mode.set_label(f"{icon} {self.selected_mode}")
        self.btn_mode.set_tooltip_text(f"Agent Mode: {self.selected_mode}")

    # -------------------------------------------------------------------------
    # Markdown & Code Syntax Parsing Engine
    # -------------------------------------------------------------------------
    def parse_code_line(self, line):
        tokens = []
        pattern = re.compile(r'(#.*|//.*|\"[^\"]*\"|\'[^\']*\'|\b\w+\b|[^\s\w]+|\s+)')
        for m in pattern.finditer(line):
            tok = m.group(0)
            if tok.startswith('#') or tok.startswith('//'):
                tokens.append(('comment', tok))
            elif (tok.startswith('"') and tok.endswith('"')) or (tok.startswith("'") and tok.endswith("'")):
                tokens.append(('string', tok))
            elif tok in KEYWORDS:
                tokens.append(('keyword', tok))
            else:
                tokens.append(('normal', tok))
        return tokens

    def insert_inline_markdown(self, line, base_tag=None):
        pattern = re.compile(r'(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)')
        pos = 0
        for match in pattern.finditer(line):
            start, end = match.span()
            if start > pos:
                segment = line[pos:start]
                end_iter = self.response_buffer.get_end_iter()
                if base_tag:
                    self.response_buffer.insert_with_tags(end_iter, segment, base_tag)
                else:
                    self.response_buffer.insert(end_iter, segment)
            token = match.group(0)
            end_iter = self.response_buffer.get_end_iter()
            if token.startswith('**') and token.endswith('**'):
                self.response_buffer.insert_with_tags(end_iter, token[2:-2], self.tags['bold'])
            elif token.startswith('`') and token.endswith('`'):
                self.response_buffer.insert_with_tags(end_iter, f" {token[1:-1]} ", self.tags['inline_code'])
            elif token.startswith('*') and token.endswith('*'):
                self.response_buffer.insert_with_tags(end_iter, token[1:-1], self.tags['italic'])
            pos = end
        if pos < len(line):
            segment = line[pos:]
            end_iter = self.response_buffer.get_end_iter()
            if base_tag:
                self.response_buffer.insert_with_tags(end_iter, segment, base_tag)
            else:
                self.response_buffer.insert(end_iter, segment)

    def insert_markdown_text(self, markdown_text):
        lines = markdown_text.split('\n')
        in_code_block = False
        code_lang = 'CODE'
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Code block delimiter
            if stripped.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    lang_match = stripped[3:].strip()
                    code_lang = lang_match.upper() if lang_match else 'CODE'
                    icon = '󰌠' if 'PY' in code_lang else ('󰒓' if 'SH' in code_lang or 'BASH' in code_lang else '󰅩')
                    header_text = f"╭─ {icon} [ {code_lang} ] " + "─" * max(4, 30 - len(code_lang)) + "\n"
                    end_iter = self.response_buffer.get_end_iter()
                    self.response_buffer.insert_with_tags(end_iter, header_text, self.tags['code_header'])
                else:
                    in_code_block = False
                    footer_text = "╰" + "─" * 40 + "\n"
                    end_iter = self.response_buffer.get_end_iter()
                    self.response_buffer.insert_with_tags(end_iter, footer_text, self.tags['code_header'])
                continue
                
            # Inside Code Block
            if in_code_block:
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, "│ ", self.tags['code_header'])
                tokens = self.parse_code_line(line)
                for t_type, t_val in tokens:
                    end_iter = self.response_buffer.get_end_iter()
                    if t_type == 'keyword':
                        self.response_buffer.insert_with_tags(end_iter, t_val, self.tags['code_kw'])
                    elif t_type == 'string':
                        self.response_buffer.insert_with_tags(end_iter, t_val, self.tags['code_str'])
                    elif t_type == 'comment':
                        self.response_buffer.insert_with_tags(end_iter, t_val, self.tags['code_com'])
                    else:
                        self.response_buffer.insert_with_tags(end_iter, t_val, self.tags['code_block'])
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert(end_iter, "\n")
                continue
                
            # Headings
            if stripped.startswith('#### '):
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, f"▪ {stripped[5:].strip()}\n", self.tags['h4'])
                continue
            elif stripped.startswith('### '):
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, f"● {stripped[4:].strip()}\n", self.tags['h3'])
                continue
            elif stripped.startswith('## '):
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, f"▸ {stripped[3:].strip()}\n", self.tags['h2'])
                continue
            elif stripped.startswith('# '):
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, f"◆ {stripped[2:].strip()}\n", self.tags['h1'])
                continue
                
            # Horizontal Divider
            if stripped in ("---", "***", "___") or (len(stripped) >= 3 and set(stripped) <= {"-", "*", "_"}):
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, "─" * 40 + "\n", self.tags['meta'])
                continue
                
            # Blockquote
            if stripped.startswith('> '):
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, "┃ ", self.tags['code_header'])
                self.insert_inline_markdown(stripped[2:].strip() + "\n", base_tag=self.tags['quote'])
                continue
                
            # Bullet list
            if stripped.startswith(('- ', '* ', '+ ')):
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, "  • ", self.tags['bullet'])
                self.insert_inline_markdown(stripped[2:].strip() + "\n")
                continue
                
            # Numbered list
            num_match = re.match(r"^(\d+\.)\s+(.*)", stripped)
            if num_match:
                n_pref, n_body = num_match.groups()
                end_iter = self.response_buffer.get_end_iter()
                self.response_buffer.insert_with_tags(end_iter, f"  {n_pref} ", self.tags['bullet'])
                self.insert_inline_markdown(n_body + "\n")
                continue
                
            # Regular text line with inline formatting
            self.insert_inline_markdown(line + ("\n" if i < len(lines) - 1 or line else ""))
            
        if in_code_block:
            end_iter = self.response_buffer.get_end_iter()
            self.response_buffer.insert_with_tags(end_iter, "╰" + "─" * 40 + "\n", self.tags['code_header'])

    def render_full_conversation(self, meta_text=""):
        self.response_buffer.set_text("")
        end_iter = self.response_buffer.get_end_iter()
        
        # 1. User Prompt
        if self.user_prompt_text:
            self.response_buffer.insert_with_tags(
                end_iter,
                f"󰒓 YOU [{self.selected_mode.upper()} • {self.selected_level}]:\n",
                self.tags['prompt']
            )
            end_iter = self.response_buffer.get_end_iter()
            self.response_buffer.insert(end_iter, f"{self.user_prompt_text}\n\n")
            
        # 2. Assistant Header
        end_iter = self.response_buffer.get_end_iter()
        self.response_buffer.insert_with_tags(
            end_iter,
            f"󰚩 AI ({self.selected_model.split(':')[0]}):\n",
            self.tags['ai_title']
        )
        
        # 3. Formatted Markdown Output
        if self.raw_assistant_response:
            self.insert_markdown_text(self.raw_assistant_response)
            
        # 4. Completion Meta
        if meta_text:
            end_iter = self.response_buffer.get_end_iter()
            self.response_buffer.insert_with_tags(end_iter, f"\n{meta_text}\n", self.tags['meta'])
            
        self.adjust_response_height()

    def on_send_clicked(self, widget):
        if self.is_generating:
            # Stop button pressed
            self.stop_requested = True
            self.set_status("STOPPING", "busy")
            return
            
        if self.is_placeholder:
            return
            
        prompt = self.input_buffer.get_text(
            self.input_buffer.get_start_iter(),
            self.input_buffer.get_end_iter(),
            True
        ).strip()
        
        if not prompt:
            return
            
        # Reset input box
        self.input_buffer.set_text("")
        self.input_scroll.set_min_content_height(32)
        
        # Show response area and setup conversation view
        self.response_scroll.set_visible(True)
        self.divider2.set_visible(True)
        self.btn_copy.set_visible(True)
        
        # Store prompt and reset response buffer
        self.user_prompt_text = prompt
        self.raw_assistant_response = ""
        self.render_full_conversation()
        
        # Set busy UI state
        self.is_generating = True
        self.stop_requested = False
        self.btn_send.set_label("󰐊 Stop")
        self.btn_send.get_style_context().add_class("stop-btn")
        self.set_status("● GENERATING...", "busy")
        
        # Run streaming in background
        self.current_stream_thread = threading.Thread(
            target=self.run_generation_stream,
            args=(prompt, self.selected_model, self.selected_mode, self.selected_level),
            daemon=True
        )
        self.current_stream_thread.start()

    def set_status(self, text, style_class=""):
        self.lbl_status.set_text(text)
        self.lbl_status.get_style_context().remove_class("busy")
        self.lbl_status.get_style_context().remove_class("error")
        if style_class:
            self.lbl_status.get_style_context().add_class(style_class)

    def on_copy_response(self, widget):
        if self.raw_assistant_response:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(self.raw_assistant_response, -1)
            self.set_status("✓ COPIED", "")
            GLib.timeout_add(1500, lambda: self.set_status("● ACTIVE", ""))

    def on_clear_all(self, widget):
        if self.is_generating:
            self.stop_requested = True
        self.user_prompt_text = ""
        self.raw_assistant_response = ""
        self.response_buffer.set_text("")
        self.response_scroll.set_visible(False)
        self.divider2.set_visible(False)
        self.btn_copy.set_visible(False)
        self.input_buffer.set_text("")
        self.set_placeholder()
        self.input_scroll.set_min_content_height(32)
        self.set_status("● ACTIVE", "")
        self.resize(self.BOX_WIDTH, 1)
        GLib.idle_add(self.reposition_above_conky)

    # -------------------------------------------------------------------------
    # Ollama Streaming Generation Engine
    # -------------------------------------------------------------------------
    def run_generation_stream(self, prompt, model, mode, level):
        start_time = time.time()
        
        # Quick Shortcuts: Google Search or Web Open
        if prompt.startswith("g ") or prompt.startswith("google ") or prompt.startswith("web "):
            query = prompt.split(" ", 1)[1] if " " in prompt else ""
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
            subprocess.Popen(["xdg-open", url])
            GLib.idle_add(self.append_stream_chunk, f"Opening Google search for: '{query}'\n")
            GLib.idle_add(self.finish_generation_stream, 0.1, True)
            return
            
        elif prompt.startswith("http://") or prompt.startswith("https://"):
            subprocess.Popen(["xdg-open", prompt])
            GLib.idle_add(self.append_stream_chunk, f"Opening browser for URL: {prompt}\n")
            GLib.idle_add(self.finish_generation_stream, 0.1, True)
            return

        # System Prompt construction based on Mode & Level
        level_instructions = {
            "Short": "Provide a very brief, concise, and direct 1-3 sentence summary answer. Omit unnecessary fluff.",
            "Medium": "Provide a clear, balanced, and helpful answer formatted with clean markdown.",
            "Expert": "Provide a comprehensive, in-depth technical analysis, complete architectural breakdown, and fully runnable code blocks."
        }.get(level, "")

        mode_instructions = {
            "Task": "You are an autonomous Linux assistant. Provide actionable commands, package names, and terminal execution steps for Arch Linux.",
            "Knowledge": "You are an expert Q&A AI consultant. Explain concepts thoroughly with structured points and clear examples.",
            "Code": "You are a senior full-stack software engineer. Provide clean, robust, modern, production-grade code with error handling."
        }.get(mode, "")

        system_prompt = f"{mode_instructions}\nResponse Depth: {level_instructions}\nAlways be accurate and format cleanly."

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "options": {
                "temperature": 0.2 if mode in ("Code", "Task") else 0.5,
                "num_ctx": 4096
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.ollama_url}/api/chat",
                data=req_data,
                headers={"Content-Type": "application/json", "User-Agent": "DesktopAI"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    if self.stop_requested:
                        break
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            GLib.idle_add(self.append_stream_chunk, content)
                        if chunk.get("done", False):
                            break

            elapsed = time.time() - start_time
            GLib.idle_add(self.finish_generation_stream, elapsed, True)

        except urllib.error.URLError as e:
            err_msg = f"Cannot connect to Ollama ({self.ollama_url}). Make sure 'ollama serve' is active.\nDetail: {e}"
            GLib.idle_add(self.append_stream_chunk, f"\n[Error] {err_msg}")
            GLib.idle_add(self.finish_generation_stream, 0, False)
        except Exception as e:
            GLib.idle_add(self.append_stream_chunk, f"\n[Error] {str(e)}")
            GLib.idle_add(self.finish_generation_stream, 0, False)

    def append_stream_chunk(self, chunk):
        self.raw_assistant_response += chunk
        self.render_full_conversation()

    def finish_generation_stream(self, elapsed, success):
        self.is_generating = False
        self.stop_requested = False
        self.btn_send.set_label("󰒭 Send")
        self.btn_send.get_style_context().remove_class("stop-btn")
        
        if success:
            self.set_status("● ACTIVE", "")
            meta = f"✓ {self.selected_model.split(':')[0]} • {elapsed:.1f}s"
            self.render_full_conversation(meta_text=meta)
        else:
            self.set_status("● ERROR", "error")
            self.render_full_conversation()


def main():
    app = DesktopInputBox()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

"""CSS Stylesheet and Theme Provider for GTK4 Desktop Panel & Sidebar AI Widget."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk

DARK_CSS = """
/* Local AI Agent GTK4 Desktop Panel & Sidebar Widget */
window.main-window {
    background-color: #0f1017;
    color: #cdd6f4;
    border: 1px solid #282a36;
    border-radius: 12px;
}

/* Custom Desktop Widget Header */
.widget-header {
    background-color: #0b0c12;
    border-bottom: 1px solid #232533;
    padding: 10px 14px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

.widget-title {
    font-weight: 800;
    font-size: 13px;
    color: #ffffff;
    letter-spacing: 0.5px;
}

.subtitle-badge {
    font-size: 10px;
    background-color: #1e1e2e;
    color: #89b4fa;
    padding: 2px 7px;
    border-radius: 6px;
    font-weight: 600;
    border: 1px solid #313244;
}

.btn-header-action {
    background: transparent;
    color: #a6adc8;
    border: none;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 12px;
}

.btn-header-action:hover {
    background-color: #232533;
    color: #ffffff;
}

.btn-header-close {
    background: transparent;
    color: #f38ba8;
    border: none;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 12px;
    font-weight: bold;
}

.btn-header-close:hover {
    background-color: #f38ba8;
    color: #11111b;
}

/* Mode Switcher Bar */
.mode-bar {
    background-color: #14151f;
    border: 1px solid #232533;
    border-radius: 8px;
    padding: 3px;
    margin: 8px 12px 4px 12px;
}

.mode-btn {
    font-size: 11px;
    font-weight: 600;
    color: #9399b2;
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    transition: all 0.2s ease;
}

.mode-btn:hover {
    color: #ffffff;
    background-color: #1e202f;
}

.mode-btn-active {
    color: #0b0c12;
    background: linear-gradient(135deg, #89b4fa 0%, #74c7ec 100%);
    font-weight: bold;
    box-shadow: 0 2px 6px rgba(137, 180, 250, 0.3);
}

.project-bar {
    background-color: #14151f;
    border: 1px solid #2e3145;
    border-radius: 8px;
    padding: 5px 10px;
    margin: 4px 12px;
}

.project-dir-label {
    font-size: 11px;
    color: #89dceb;
    font-family: monospace;
}

.btn-small-browse {
    font-size: 10px;
    font-weight: bold;
    background-color: #252739;
    color: #cdd6f4;
    border-radius: 5px;
    padding: 2px 8px;
    border: 1px solid #363a4f;
}

.btn-small-browse:hover {
    background-color: #3b3f5c;
    color: #ffffff;
}

/* Status bar */
.status-badge {
    font-size: 10px;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 6px;
    text-transform: uppercase;
}

.status-idle {
    background-color: #1e202f;
    color: #a6adc8;
}

.status-thinking {
    background-color: #3e3321;
    color: #f9e2af;
}

.status-running {
    background-color: #1c362a;
    color: #a6e3a1;
}

.status-waiting {
    background-color: #3e262b;
    color: #f38ba8;
}

.status-completed {
    background-color: #1c362a;
    color: #a6e3a1;
}

.status-failed {
    background-color: #3e262b;
    color: #f38ba8;
}

/* Input container */
.input-container {
    background-color: #14151f;
    border: 1px solid #232533;
    border-radius: 10px;
    padding: 8px;
    margin: 6px 12px;
}

.input-container:focus-within {
    border-color: #89b4fa;
}

.task-textview {
    background-color: transparent;
    color: #cdd6f4;
    font-size: 13px;
    border: none;
    padding: 2px;
}

.task-textview text {
    background-color: transparent;
    color: #cdd6f4;
}

.btn-primary {
    background: linear-gradient(135deg, #89b4fa 0%, #74c7ec 100%);
    color: #0b0c12;
    font-weight: bold;
    font-size: 12px;
    border-radius: 6px;
    padding: 5px 14px;
    border: none;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #b4befe 0%, #89dceb 100%);
}

.btn-danger {
    background: #f38ba8;
    color: #0b0c12;
    font-weight: bold;
    font-size: 12px;
    border-radius: 6px;
    padding: 5px 14px;
    border: none;
}

.btn-danger:hover {
    background: #eba0ac;
}

.btn-flat {
    background: transparent;
    color: #a6adc8;
    font-size: 11px;
    border: none;
    padding: 2px 6px;
}

.btn-flat:hover {
    color: #ffffff;
}

/* Activity Cards */
.activity-card {
    background-color: #14151f;
    border: 1px solid #232533;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 3px 12px;
}

.knowledge-card {
    background-color: #14151f;
    border: 1px solid #2e3145;
    border-left: 3px solid #89b4fa;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 4px 12px;
}

.activity-card-title {
    font-weight: 600;
    font-size: 12px;
    color: #cdd6f4;
}

.activity-card-desc {
    font-size: 11px;
    color: #a6adc8;
    line-height: 1.4;
}

.knowledge-desc {
    font-size: 12px;
    color: #cdd6f4;
    line-height: 1.5;
}

.terminal-box {
    background-color: #07080c;
    border: 1px solid #1a1b26;
    border-radius: 6px;
    padding: 6px 8px;
    margin-top: 4px;
}

.terminal-textview {
    background-color: #07080c;
    color: #a6e3a1;
    font-family: monospace;
    font-size: 11px;
}

.terminal-textview text {
    background-color: #07080c;
    color: #a6e3a1;
}

.diff-view {
    background-color: #07080c;
    color: #cdd6f4;
    font-family: monospace;
    font-size: 11px;
}

.diff-view text {
    background-color: #07080c;
    color: #cdd6f4;
}

.permission-banner {
    background-color: #2b1d1f;
    border: 1px solid #f38ba8;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 6px 12px;
}
"""


def load_theme():
    """Load and apply the CSS theme across the application display."""
    provider = Gtk.CssProvider()
    provider.load_from_string(DARK_CSS)
    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

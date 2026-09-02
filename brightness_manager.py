#!/usr/bin/env python3
"""
Brightness Manager — Premium GTK4 popup
Arch Linux / Openbox / CachyOS
Uses brightnessctl for hardware backlight control.
"""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk, Gio

import subprocess
import sys

APP_ID = "com.cachyos.brightnessmanager"

# ─── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
* {
    font-family: "Inter", "Noto Sans", sans-serif;
}

window {
    background-color: #1a1a2e;
    border-radius: 16px;
}

.panel {
    background: linear-gradient(145deg, #1e1e3a 0%, #16213e 60%, #0f3460 100%);
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* ── Header ── */
.header-bar {
    background: linear-gradient(135deg, #f6a623 0%, #e8820c 50%, #c0550a 100%);
    padding: 18px 22px 14px 22px;
    border-radius: 16px 16px 0 0;
}
.header-icon {
    font-size: 32px;
    color: white;
}
.header-title {
    color: white;
    font-size: 20px;
    font-weight: 700;
}
.header-subtitle {
    color: rgba(255,255,255,0.75);
    font-size: 12px;
    font-weight: 400;
}

/* ── Percentage display ── */
.pct-display {
    background: rgba(246,166,35,0.12);
    border-radius: 14px;
    border: 1px solid rgba(246,166,35,0.25);
    padding: 14px 24px;
    margin: 16px 20px 4px 20px;
}
.pct-number {
    color: #f6a623;
    font-size: 48px;
    font-weight: 700;
}
.pct-symbol {
    color: rgba(246,166,35,0.6);
    font-size: 22px;
    font-weight: 500;
}
.pct-label {
    color: rgba(255,255,255,0.45);
    font-size: 11px;
    font-weight: 500;
}

/* ── Slider ── */
.slider-box {
    margin: 8px 20px 4px 20px;
}
scale trough {
    background: rgba(255,255,255,0.10);
    border-radius: 8px;
    min-height: 8px;
}
scale trough highlight {
    background: linear-gradient(to right, #e8820c, #f6a623, #ffd166);
    border-radius: 8px;
}
scale slider {
    background: white;
    border-radius: 50%;
    min-width: 22px;
    min-height: 22px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.45);
    border: 2px solid rgba(246,166,35,0.6);
    margin: -7px 0;
}
scale slider:hover {
    background: #fff8ec;
    border-color: #f6a623;
}

/* ── Preset buttons ── */
.preset-section {
    margin: 10px 20px 6px 20px;
}
.preset-label {
    color: rgba(255,255,255,0.35);
    font-size: 10px;
    font-weight: 600;
    margin-bottom: 6px;
}
.preset-btn {
    background: rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.75);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 6px 0;
    font-size: 12px;
    font-weight: 600;
    min-width: 54px;
}
.preset-btn:hover {
    background: rgba(246,166,35,0.18);
    border-color: rgba(246,166,35,0.4);
    color: #f6a623;
}
.preset-btn-active {
    background: rgba(246,166,35,0.25);
    border-color: #f6a623;
    color: #f6a623;
}

/* ── Step buttons ── */
.step-btn {
    background: rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.85);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 8px 20px;
    font-size: 18px;
    font-weight: 500;
    min-width: 52px;
}
.step-btn:hover {
    background: rgba(246,166,35,0.20);
    border-color: rgba(246,166,35,0.5);
    color: #f6a623;
}

/* ── Status bar ── */
.status-bar {
    background: rgba(246,166,35,0.08);
    border-top: 1px solid rgba(246,166,35,0.12);
    border-radius: 0 0 16px 16px;
    padding: 8px 20px;
    color: rgba(255,255,255,0.4);
    font-size: 11px;
}

separator {
    background: rgba(255,255,255,0.07);
    min-height: 1px;
    margin: 0 16px;
}
"""

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_brightness_pct():
    try:
        cur = int(subprocess.check_output(["brightnessctl", "get"], text=True).strip())
        mx  = int(subprocess.check_output(["brightnessctl", "max"], text=True).strip())
        if mx == 0:
            return 0
        return max(1, round((cur / mx) * 100))
    except Exception:
        return 50

def set_brightness_pct(pct):
    pct = max(1, min(100, int(pct)))
    subprocess.run(
        ["brightnessctl", "set", f"{pct}%"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def brightness_to_icon(pct):
    if pct <= 0:  return "🌑"
    if pct < 20:  return "🌘"
    if pct < 40:  return "🌗"
    if pct < 60:  return "🌖"
    if pct < 80:  return "🌕"
    return "☀️"

def brightness_to_desc(pct):
    if pct <= 5:  return "Screen is very dim"
    if pct < 25:  return "Low brightness"
    if pct < 50:  return "Moderate brightness"
    if pct < 75:  return "High brightness"
    if pct < 95:  return "Very bright"
    return "Maximum brightness"

# ─── Main Window ──────────────────────────────────────────────────────────────

PRESETS = [("10%", 10), ("25%", 25), ("50%", 50), ("75%", 75), ("100%", 100)]

class BrightnessWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Brightness")
        self.set_default_size(360, -1)
        self.set_resizable(False)

        self._updating = False
        self._pct = get_brightness_pct()

        # Root panel
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.add_css_class("panel")
        self.set_child(root)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hdr.add_css_class("header-bar")

        self.icon_lbl = Gtk.Label(label=brightness_to_icon(self._pct))
        self.icon_lbl.add_css_class("header-icon")
        hdr.append(self.icon_lbl)

        hdr_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hdr_text.set_hexpand(True)
        hdr_title = Gtk.Label(label="Brightness")
        hdr_title.add_css_class("header-title")
        hdr_title.set_xalign(0)
        hdr_text.append(hdr_title)

        self.sub_lbl = Gtk.Label(label=brightness_to_desc(self._pct))
        self.sub_lbl.add_css_class("header-subtitle")
        self.sub_lbl.set_xalign(0)
        hdr_text.append(self.sub_lbl)
        hdr.append(hdr_text)

        close_btn = Gtk.Button(label="✕")
        close_btn.add_css_class("flat")
        close_btn.connect("clicked", lambda _: self.close())
        close_btn.set_valign(Gtk.Align.START)
        hdr.append(close_btn)

        root.append(hdr)

        # ── Percentage display ───────────────────────────────────────────────
        pct_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        pct_box.add_css_class("pct-display")
        pct_box.set_halign(Gtk.Align.FILL)

        num_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        num_row.set_halign(Gtk.Align.CENTER)

        self.num_lbl = Gtk.Label(label=str(self._pct))
        self.num_lbl.add_css_class("pct-number")
        num_row.append(self.num_lbl)

        sym_lbl = Gtk.Label(label="%")
        sym_lbl.add_css_class("pct-symbol")
        sym_lbl.set_valign(Gtk.Align.END)
        sym_lbl.set_margin_bottom(10)
        num_row.append(sym_lbl)
        pct_box.append(num_row)

        desc_lbl = Gtk.Label(label="BACKLIGHT LEVEL")
        desc_lbl.add_css_class("pct-label")
        desc_lbl.set_halign(Gtk.Align.CENTER)
        pct_box.append(desc_lbl)

        root.append(pct_box)

        # ── Slider ──────────────────────────────────────────────────────────
        slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        slider_box.add_css_class("slider-box")

        Gtk.Label(label="🌑").set_valign(Gtk.Align.CENTER)
        dim = Gtk.Label(label="🌑")
        dim.set_valign(Gtk.Align.CENTER)
        slider_box.append(dim)

        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
        self.scale.set_draw_value(False)
        self.scale.set_hexpand(True)
        self.scale.set_value(self._pct)
        self.scale.connect("value-changed", self._on_slider)
        slider_box.append(self.scale)

        bright = Gtk.Label(label="☀️")
        bright.set_valign(Gtk.Align.CENTER)
        slider_box.append(bright)

        root.append(slider_box)

        # ── Step buttons ─────────────────────────────────────────────────────
        step_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        step_box.set_halign(Gtk.Align.CENTER)
        step_box.set_margin_top(2)
        step_box.set_margin_bottom(4)

        minus_btn = Gtk.Button(label="−")
        minus_btn.add_css_class("step-btn")
        minus_btn.connect("clicked", self._decrease)

        plus_btn = Gtk.Button(label="+")
        plus_btn.add_css_class("step-btn")
        plus_btn.connect("clicked", self._increase)

        step_box.append(minus_btn)
        step_box.append(plus_btn)
        root.append(step_box)

        # ── Separator ───────────────────────────────────────────────────────
        root.append(Gtk.Separator())

        # ── Presets ─────────────────────────────────────────────────────────
        preset_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        preset_box.add_css_class("preset-section")

        preset_title = Gtk.Label(label="QUICK PRESETS")
        preset_title.add_css_class("preset-label")
        preset_title.set_xalign(0)
        preset_box.append(preset_title)

        self._preset_btns = []
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_row.set_homogeneous(True)
        for label, val in PRESETS:
            btn = Gtk.Button(label=label)
            btn.add_css_class("preset-btn")
            btn.connect("clicked", self._on_preset, val)
            btn_row.append(btn)
            self._preset_btns.append((btn, val))
        preset_box.append(btn_row)
        root.append(preset_box)

        # ── Status bar ──────────────────────────────────────────────────────
        self.status_lbl = Gtk.Label(label="Device: intel_backlight  •  brightnessctl")
        self.status_lbl.add_css_class("status-bar")
        self.status_lbl.set_xalign(0)
        root.append(self.status_lbl)

        # Live polling
        self._update_ui(self._pct)
        GLib.timeout_add(2000, self._poll)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _update_ui(self, pct):
        self._updating = True
        self.scale.set_value(pct)
        self._updating = False

        self._pct = pct
        self.num_lbl.set_label(str(pct))
        self.icon_lbl.set_label(brightness_to_icon(pct))
        self.sub_lbl.set_label(brightness_to_desc(pct))

        for btn, val in self._preset_btns:
            if val == pct:
                btn.add_css_class("preset-btn-active")
            else:
                btn.remove_css_class("preset-btn-active")

    def _apply(self, pct):
        set_brightness_pct(pct)
        self._update_ui(pct)
        self.status_lbl.set_label(f"Set to {pct}%  •  intel_backlight")

    def _poll(self):
        actual = get_brightness_pct()
        if actual != self._pct:
            self._update_ui(actual)
        return True

    # ── Signal handlers ─────────────────────────────────────────────────────

    def _on_slider(self, slider):
        if self._updating:
            return
        self._apply(int(slider.get_value()))

    def _increase(self, _btn):
        self._apply(min(100, self._pct + 5))

    def _decrease(self, _btn):
        self._apply(max(1, self._pct - 5))

    def _on_preset(self, _btn, val):
        self._apply(val)


# ─── Application ──────────────────────────────────────────────────────────────

class BrightnessApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.win = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def do_activate(self):
        if self.win is None:
            self.win = BrightnessWindow(self)
        self.win.present()


if __name__ == "__main__":
    app = BrightnessApp()
    app.run(sys.argv)

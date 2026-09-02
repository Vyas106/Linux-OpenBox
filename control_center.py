#!/usr/bin/env python3
"""
Control Center / Tools Popup for Openbox & Polybar
Features:
- Volume slider (with mute toggle)
- Brightness slider
- 3x2 Grid: Hotspot, Bluetooth, Night Mode, Lock Screen, Kitty Terminal, Custom App slot (+ Add App)
- 100% Minimalist Pure Black & White Theme
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk, Gio

import subprocess
import threading
import json
import os
import sys

APP_ID = "com.cachyos.controlcenter"
CUSTOM_APP_CONFIG = os.path.expanduser("~/.config/control_center_custom.json")

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

# ─── System Controls ─────────────────────────────────────────────────────────

def get_volume():
    try:
        r = run_cmd("pactl get-sink-volume @DEFAULT_SINK@")
        import re
        m = re.search(r'(\d+)%', r.stdout)
        return int(m.group(1)) if m else 50
    except:
        return 50

def set_volume(val):
    run_cmd(f"pactl set-sink-volume @DEFAULT_SINK@ {int(val)}%")

def get_muted():
    r = run_cmd("pactl get-sink-mute @DEFAULT_SINK@")
    return "yes" in r.stdout.lower()

def toggle_mute():
    run_cmd("pactl set-sink-mute @DEFAULT_SINK@ toggle")

def get_brightness():
    try:
        r = run_cmd("brightnessctl -m")
        parts = r.stdout.strip().split(",")
        if len(parts) >= 4:
            pct_str = parts[3].replace("%", "")
            return int(pct_str)
        return 50
    except:
        return 50

def set_brightness(val):
    run_cmd(f"brightnessctl set {int(val)}%")

def get_hotspot_status():
    r = run_cmd("nmcli -t -f TYPE,STATE connection show --active 2>/dev/null")
    return "802-11-wireless:activated" in r.stdout or "wifi:activated" in r.stdout

def toggle_hotspot():
    run_cmd("/home/vishal/Useless/hotspot_toggle.sh")

def get_bluetooth_status():
    r = run_cmd("bluetoothctl show 2>/dev/null | grep 'Powered:'")
    return "yes" in r.stdout.lower()

def toggle_bluetooth():
    if get_bluetooth_status():
        run_cmd("bluetoothctl power off")
    else:
        run_cmd("bluetoothctl power on")

def get_installed_apps():
    """Scans .desktop files for user-friendly app selection"""
    apps = []
    dirs = [
        os.path.expanduser("~/.local/share/applications"),
        "/usr/share/applications"
    ]
    seen_names = set()
    for d in dirs:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".desktop"):
                fp = os.path.join(d, f)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as file:
                        content = file.read()
                    name, exec_cmd, icon, nodisplay = None, None, None, False
                    for line in content.splitlines():
                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1].strip()
                        elif line.startswith("Exec=") and not exec_cmd:
                            exec_cmd = line.split("=", 1)[1].strip().split("%")[0].strip()
                        elif line.startswith("Icon=") and not icon:
                            icon = line.split("=", 1)[1].strip()
                        elif line.startswith("NoDisplay=true"):
                            nodisplay = True
                    if name and exec_cmd and not nodisplay and name not in seen_names:
                        seen_names.add(name)
                        apps.append({"name": name, "exec": exec_cmd, "icon": icon or "application-x-executable"})
                except:
                    pass
    apps.sort(key=lambda x: x["name"].lower())
    return apps

def load_custom_app():
    if os.path.exists(CUSTOM_APP_CONFIG):
        try:
            with open(CUSTOM_APP_CONFIG, "r") as f:
                return json.load(f)
        except:
            pass
    return None

def save_custom_app(app_info):
    try:
        os.makedirs(os.path.dirname(CUSTOM_APP_CONFIG), exist_ok=True)
        with open(CUSTOM_APP_CONFIG, "w") as f:
            json.dump(app_info, f, indent=2)
    except:
        pass


# ─── Terminal / Minimal CSS ──────────────────────────────────────────────────
CSS = """
* {
    font-family: 'JetBrains Mono', 'MesloLGS Nerd Font', monospace;
}

window {
    background-color: #000000;
    color: #ffffff;
    border: 1px solid #333333;
}

button {
    all: unset;
    background-color: #141414;
    color: #ffffff;
    border: 1px solid #282828;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    text-align: center;
}

button:hover {
    background-color: #242424;
    border-color: #444444;
    color: #ffffff;
}

.cc-header {
    background-color: #0a0a0a;
    border-bottom: 1px solid #222222;
    padding: 12px 16px;
}

.cc-title {
    color: #ffffff;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

.slider-card {
    background-color: #080808;
    border: 1px solid #202020;
    padding: 10px 14px;
    margin: 6px 14px;
}

.slider-icon {
    font-size: 16px;
    color: #ffffff;
    margin-right: 10px;
}

.slider-pct {
    color: #aaaaaa;
    font-size: 12px;
    font-weight: bold;
    margin-left: 10px;
}

scale trough {
    background-color: #222222;
    min-height: 8px;
    border-radius: 4px;
}

scale highlight {
    background-color: #2563eb;
    border-radius: 4px;
}

scale slider {
    background-color: #ffffff;
    border: none;
    min-width: 16px;
    min-height: 16px;
    border-radius: 8px;
}

button.grid-btn,
.grid-btn {
    all: unset;
    background-color: #0d0d0d !important;
    color: #ffffff !important;
    border: 1px solid #242424 !important;
    border-radius: 8px;
    padding: 12px 8px;
    margin: 4px;
    text-align: center;
}

button.grid-btn:hover,
.grid-btn:hover {
    background-color: #1a1a1a !important;
    border-color: #3b82f6 !important;
    color: #ffffff !important;
}

button.grid-btn-active,
.grid-btn-active {
    background-color: #172554 !important;
    border: 1px solid #3b82f6 !important;
    color: #ffffff !important;
}

.tile-icon {
    font-size: 18px;
    margin-bottom: 4px;
    color: #ffffff;
}

.tile-title {
    font-size: 11px;
    font-weight: bold;
    color: #ffffff;
}

.tile-sub {
    font-size: 10px;
    color: #94a3b8;
}

.section-label {
    color: #60a5fa;
    font-size: 10px;
    font-weight: bold;
    margin: 8px 14px 2px 14px;
    letter-spacing: 0.5px;
}

.app-item {
    all: unset;
    padding: 8px 12px;
    border-bottom: 1px solid #181818;
    background-color: #050505;
    color: #ffffff;
}

.app-item:hover {
    background-color: #1a1a1a;
    color: #ffffff;
}
"""

# ─── App Chooser Dialog ──────────────────────────────────────────────────────
class AppChooserDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(transient_for=parent, modal=True)
        self.set_title("Select Application to Pin")
        self.set_default_size(380, 480)
        self.selected_app = None

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        hdr = Gtk.Label(label="<b>Select Application:</b>")
        hdr.set_use_markup(True)
        hdr.set_xalign(0)
        box.append(hdr)

        self.search = Gtk.Entry()
        self.search.set_placeholder_text("Search apps...")
        self.search.connect("changed", self.on_search_changed)
        box.append(self.search)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.app_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll.set_child(self.app_list_box)
        box.append(scroll)

        self.all_apps = get_installed_apps()
        self.render_apps(self.all_apps)

        self.set_child(box)

    def render_apps(self, apps):
        child = self.app_list_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.app_list_box.remove(child)
            child = nxt

        for app in apps:
            btn = Gtk.Button()
            btn.add_css_class("app-item")
            row = Gtk.Box(spacing=8)
            lbl = Gtk.Label(label=f"󰘔  {app['name']}")
            lbl.set_xalign(0)
            lbl.set_hexpand(True)
            row.append(lbl)
            btn.set_child(row)
            btn.connect("clicked", lambda _, a=app: self.on_select(a))
            self.app_list_box.append(btn)

    def on_search_changed(self, entry):
        q = entry.get_text().lower()
        filt = [a for a in self.all_apps if q in a["name"].lower()]
        self.render_apps(filt)

    def on_select(self, app):
        self.selected_app = app
        self.response(Gtk.ResponseType.OK)


# ─── Control Center Window ───────────────────────────────────────────────────
class ControlCenterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Quick Settings & Tools")
        self.set_default_size(380, 520)
        self.set_resizable(False)

        self.custom_app = load_custom_app()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(root)

        # ── Header ───────────────────────────────────────────────────────────
        hdr = Gtk.Box(spacing=8)
        hdr.add_css_class("cc-header")
        title = Gtk.Label(label="󰒓  CONTROL CENTER & QUICK TOOLS")
        title.add_css_class("cc-title")
        title.set_hexpand(True)
        title.set_xalign(0)
        hdr.append(title)
        root.append(hdr)

        # ── Sliders Section ──────────────────────────────────────────────────
        sl_lbl = Gtk.Label(label="DEVICE CONTROLS")
        sl_lbl.add_css_class("section-label")
        sl_lbl.set_xalign(0)
        root.append(sl_lbl)

        # Volume Slider Row
        vol_box = Gtk.Box(spacing=6)
        vol_box.add_css_class("slider-card")
        self.vol_icon_btn = Gtk.Button(label="󰕾" if not get_muted() else "󰝟")
        self.vol_icon_btn.add_css_class("slider-icon")
        self.vol_icon_btn.connect("clicked", self.on_mute_toggle)
        vol_box.append(self.vol_icon_btn)

        cur_vol = get_volume()
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_value(cur_vol)
        self.vol_scale.set_hexpand(True)
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        vol_box.append(self.vol_scale)

        self.vol_lbl = Gtk.Label(label=f"{cur_vol}%")
        self.vol_lbl.add_css_class("slider-pct")
        self.vol_lbl.set_width_chars(5)
        vol_box.append(self.vol_lbl)
        root.append(vol_box)

        # Brightness Slider Row
        br_box = Gtk.Box(spacing=6)
        br_box.add_css_class("slider-card")
        br_icon = Gtk.Label(label="󰃠")
        br_icon.add_css_class("slider-icon")
        br_box.append(br_icon)

        cur_br = get_brightness()
        self.br_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.br_scale.set_value(cur_br)
        self.br_scale.set_hexpand(True)
        self.br_scale.connect("value-changed", self.on_br_changed)
        br_box.append(self.br_scale)

        self.br_lbl = Gtk.Label(label=f"{cur_br}%")
        self.br_lbl.add_css_class("slider-pct")
        self.br_lbl.set_width_chars(5)
        br_box.append(self.br_lbl)
        root.append(br_box)

        # ── 3x2 Quick Tool Grid Section ──────────────────────────────────────
        grid_lbl = Gtk.Label(label="QUICK TOGGLES & TOOLS")
        grid_lbl.add_css_class("section-label")
        grid_lbl.set_xalign(0)
        root.append(grid_lbl)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.set_margin_start(10)
        grid.set_margin_end(10)
        grid.set_margin_top(4)
        grid.set_margin_bottom(10)

        # 1. Hotspot Button
        self.hotspot_btn = self._make_tile("󰤨", "Hotspot", "OFF")
        self.hotspot_btn.connect("clicked", self.on_hotspot_toggle)
        grid.attach(self.hotspot_btn, 0, 0, 1, 1)

        # 2. Bluetooth Button
        self.bt_btn = self._make_tile("󰂯", "Bluetooth", "OFF")
        self.bt_btn.connect("clicked", self.on_bt_toggle)
        grid.attach(self.bt_btn, 1, 0, 1, 1)

        # 3. Night Light / Eye Care
        self.night_btn = self._make_tile("󰖔", "Night Light", "OFF")
        self.night_btn.connect("clicked", self.on_night_toggle)
        grid.attach(self.night_btn, 2, 0, 1, 1)

        # 4. Lock Screen
        lock_btn = self._make_tile("󰌾", "Lock Screen", "Openbox")
        lock_btn.connect("clicked", lambda _: (subprocess.Popen(["/home/vishal/Useless/lock.sh"]), self.close()))
        grid.attach(lock_btn, 0, 1, 1, 1)

        # 5. Kitty Terminal
        term_btn = self._make_tile("", "Kitty", "Terminal")
        term_btn.connect("clicked", lambda _: (subprocess.Popen(["kitty"]), self.close()))
        grid.attach(term_btn, 1, 1, 1, 1)

        # 6. Custom App Slot
        self.custom_btn = Gtk.Button()
        self.custom_btn.add_css_class("grid-btn")
        self.custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.custom_btn.set_child(self.custom_box)
        self.custom_btn.connect("clicked", self.on_custom_app_click)
        grid.attach(self.custom_btn, 2, 1, 1, 1)

        self._update_custom_app_tile()
        root.append(grid)

        # Refresh state asynchronously
        self._refresh_states()

    def _make_tile(self, icon, title, sub):
        btn = Gtk.Button()
        btn.add_css_class("grid-btn")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_valign(Gtk.Align.CENTER)

        i_lbl = Gtk.Label(label=icon)
        i_lbl.add_css_class("tile-icon")
        box.append(i_lbl)

        t_lbl = Gtk.Label(label=title)
        t_lbl.add_css_class("tile-title")
        box.append(t_lbl)

        s_lbl = Gtk.Label(label=sub)
        s_lbl.add_css_class("tile-sub")
        box.append(s_lbl)

        btn.set_child(box)
        btn._sub_label = s_lbl
        btn._title_label = t_lbl
        return btn

    def _update_custom_app_tile(self):
        # Clear children
        child = self.custom_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.custom_box.remove(child)
            child = nxt

        if self.custom_app:
            name = self.custom_app.get("name", "Custom App")
            if len(name) > 10:
                name = name[:9] + ".."
            i_lbl = Gtk.Label(label="󰘔")
            i_lbl.add_css_class("tile-icon")
            t_lbl = Gtk.Label(label=name)
            t_lbl.add_css_class("tile-title")
            s_lbl = Gtk.Label(label="Run (R-Click +)")
            s_lbl.add_css_class("tile-sub")
            self.custom_box.append(i_lbl)
            self.custom_box.append(t_lbl)
            self.custom_box.append(s_lbl)
        else:
            i_lbl = Gtk.Label(label="󰐕")
            i_lbl.add_css_class("tile-icon")
            t_lbl = Gtk.Label(label="Add App")
            t_lbl.add_css_class("tile-title")
            s_lbl = Gtk.Label(label="Click to Pin")
            s_lbl.add_css_class("tile-sub")
            self.custom_box.append(i_lbl)
            self.custom_box.append(t_lbl)
            self.custom_box.append(s_lbl)

    def on_custom_app_click(self, _):
        if not self.custom_app:
            self._open_app_picker()
        else:
            cmd = self.custom_app.get("exec")
            if cmd:
                subprocess.Popen(cmd, shell=True)
                self.close()

    def _open_app_picker(self):
        dlg = AppChooserDialog(self)
        dlg.connect("response", self._on_app_picked)
        dlg.show()

    def _on_app_picked(self, dlg, resp):
        if resp == Gtk.ResponseType.OK and dlg.selected_app:
            self.custom_app = dlg.selected_app
            save_custom_app(self.custom_app)
            self._update_custom_app_tile()
        dlg.destroy()

    def on_vol_changed(self, scale):
        val = int(scale.get_value())
        self.vol_lbl.set_text(f"{val}%")
        set_volume(val)

    def on_mute_toggle(self, _):
        toggle_mute()
        muted = get_muted()
        self.vol_icon_btn.set_label("󰝟" if muted else "󰕾")

    def on_br_changed(self, scale):
        val = int(scale.get_value())
        self.br_lbl.set_text(f"{val}%")
        set_brightness(val)

    def on_hotspot_toggle(self, _):
        toggle_hotspot()
        self._refresh_states()

    def on_bt_toggle(self, _):
        toggle_bluetooth()
        self._refresh_states()

    def on_night_toggle(self, _):
        # Toggle redshift / night light
        if os.path.exists("/tmp/night_light_active"):
            run_cmd("redshift -x >/dev/null 2>&1; pkill -9 redshift 2>/dev/null; rm -f /tmp/night_light_active")
            self.night_btn._sub_label.set_text("OFF")
            self.night_btn.remove_css_class("grid-btn-active")
        else:
            run_cmd("redshift -O 4500K >/dev/null 2>&1 & touch /tmp/night_light_active")
            self.night_btn._sub_label.set_text("ON (4500K)")
            self.night_btn.add_css_class("grid-btn-active")

    def _refresh_states(self):
        def task():
            hs = get_hotspot_status()
            bt = get_bluetooth_status()
            nl = os.path.exists("/tmp/night_light_active")
            GLib.idle_add(self._apply_states, hs, bt, nl)
        threading.Thread(target=task, daemon=True).start()

    def _apply_states(self, hs, bt, nl):
        self.hotspot_btn._sub_label.set_text("ON" if hs else "OFF")
        if hs:
            self.hotspot_btn.add_css_class("grid-btn-active")
        else:
            self.hotspot_btn.remove_css_class("grid-btn-active")

        self.bt_btn._sub_label.set_text("ON" if bt else "OFF")
        if bt:
            self.bt_btn.add_css_class("grid-btn-active")
        else:
            self.bt_btn.remove_css_class("grid-btn-active")

        self.night_btn._sub_label.set_text("ON" if nl else "OFF")
        if nl:
            self.night_btn.add_css_class("grid-btn-active")
        else:
            self.night_btn.remove_css_class("grid-btn-active")


# ─── App Runner ──────────────────────────────────────────────────────────────
class ControlCenterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.win = None

    def do_activate(self):
        if self.win is None:
            self.win = ControlCenterWindow(self)
        self.win.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

if __name__ == "__main__":
    app = ControlCenterApp()
    app.run(sys.argv)

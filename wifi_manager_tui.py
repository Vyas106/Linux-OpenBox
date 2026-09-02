#!/usr/bin/env python3
"""
Terminal-Aesthetic Modern Wi-Fi Manager (GUI/TUI)
High-Contrast Dark Theme with Blue Action & Red Danger buttons for Openbox / CachyOS Linux
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk, Gio

import subprocess
import threading
import os
import sys
import re

APP_ID = "com.cachyos.wifimanager.tui"

def run_cmd(cmd, timeout=10):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        class Dummy:
            returncode = 1
            stdout = ""
            stderr = str(e)
        return Dummy()

def nmcli(*args):
    return run_cmd("nmcli " + " ".join(args))

def get_wifi_status():
    r = nmcli("radio wifi")
    return r.stdout.strip() == "enabled"

def get_wifi_devices():
    r = nmcli("-t -f DEVICE,TYPE dev")
    devs = []
    for line in r.stdout.strip().split("\n"):
        if ":wifi" in line:
            devs.append(line.split(":")[0])
    return devs or ["wlan0"]

def connect_to_wifi(ssid, password=None):
    ssid_clean = ssid.replace('"', '\\"')
    devs = get_wifi_devices()
    dev = devs[0] if devs else "wlan0"
    
    # Ensure device is managed & autoconnect enabled
    run_cmd(f"nmcli dev set {dev} managed yes 2>/dev/null; nmcli dev set {dev} autoconnect yes 2>/dev/null")
    
    saved = get_saved_connections()
    
    if password:
        pwd_clean = password.replace('"', '\\"')
        # If profile is already saved, update password and activate directly
        if ssid in saved:
            run_cmd(f'nmcli connection modify "{ssid_clean}" 802-11-wireless-security.key-mgmt wpa-psk 802-11-wireless-security.psk "{pwd_clean}" connection.interface-name "" 802-11-wireless.cloned-mac-address preserve')
            r = run_cmd(f'nmcli connection up "{ssid_clean}"')
            if r.returncode == 0:
                return r
        
        # Fresh connect via device wifi
        r = run_cmd(f'nmcli device wifi connect "{ssid_clean}" password "{pwd_clean}" ifname {dev}')
        if r.returncode == 0:
            return r
        r = run_cmd(f'nmcli device wifi connect "{ssid_clean}" password "{pwd_clean}"')
        return r
    else:
        # Saved or open network
        if ssid in saved:
            run_cmd(f'nmcli connection modify "{ssid_clean}" connection.interface-name "" 802-11-wireless.cloned-mac-address preserve 2>/dev/null')
            r = run_cmd(f'nmcli connection up "{ssid_clean}"')
            if r.returncode == 0:
                return r
        r = run_cmd(f'nmcli device wifi connect "{ssid_clean}" ifname {dev}')
        if r.returncode == 0:
            return r
        r = run_cmd(f'nmcli device wifi connect "{ssid_clean}"')
        return r

def get_active_connection():
    r = nmcli("-t -f ACTIVE,SSID,BSSID,DEVICE,CHAN,SIGNAL,SECURITY dev wifi")
    for line in r.stdout.strip().split("\n"):
        if line.startswith("yes:"):
            parts = line.split(":")
            if len(parts) >= 6:
                return {
                    "ssid": parts[1],
                    "bssid": parts[2],
                    "device": parts[3],
                    "channel": parts[4],
                    "signal": parts[5],
                    "security": parts[6] if len(parts) > 6 else ""
                }
    return None

def get_ip_address(device="wlan0"):
    r = run_cmd(f"ip -4 addr show {device} 2>/dev/null | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){{3}}'")
    ip = r.stdout.strip().split("\n")[0] if r.stdout.strip() else ""
    return ip

def get_saved_connections():
    r = nmcli("-t -f NAME,TYPE connection show")
    saved = set()
    for line in r.stdout.strip().split("\n"):
        if ":" in line:
            name, ctype = line.split(":", 1)
            if any(k in ctype for k in ("wireless", "wifi", "802-11-wireless")):
                saved.add(name)
    return saved

FORGOTTEN_FILE = os.path.expanduser("~/.config/polybar/forgotten_wifi.json")

def get_forgotten_networks():
    try:
        if os.path.exists(FORGOTTEN_FILE):
            with open(FORGOTTEN_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_forgotten_network(ssid, security=""):
    try:
        os.makedirs(os.path.dirname(FORGOTTEN_FILE), exist_ok=True)
        items = get_forgotten_networks()
        items = [x for x in items if x["ssid"] != ssid]
        items.insert(0, {
            "ssid": ssid,
            "security": security,
            "time": time.strftime("%Y-%m-%d %H:%M")
        })
        with open(FORGOTTEN_FILE, "w") as f:
            json.dump(items, f, indent=2)
    except Exception as e:
        print("Error saving forgotten wifi:", e)

def remove_forgotten_network(ssid):
    try:
        items = get_forgotten_networks()
        items = [x for x in items if x["ssid"] != ssid]
        with open(FORGOTTEN_FILE, "w") as f:
            json.dump(items, f, indent=2)
    except Exception:
        pass

def signal_bar(signal_str):
    try:
        s = int(signal_str)
        if s >= 80: return "[████]"
        if s >= 60: return "[███░]"
        if s >= 40: return "[██░░]"
        if s >= 20: return "[█░░░]"
        return "[░░░░]"
    except:
        return "[????]"

# ─── Rich High-Contrast CSS (Blue Primary, Red Danger, Black BG) ─────────────
CSS = """
* {
    font-family: 'JetBrains Mono', 'MesloLGS Nerd Font', monospace;
}

window {
    background-color: #000000;
    color: #ffffff;
    border: 1px solid #282828;
}

.term-header {
    background-color: #0a0a0a;
    border-bottom: 1px solid #222222;
    padding: 12px 16px;
}

.term-title {
    color: #ffffff;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

.term-prompt {
    color: #777777;
    font-size: 11px;
}

.status-box {
    background-color: #0c0c0c;
    border: 1px solid #222222;
    margin: 8px 12px;
    padding: 10px 14px;
}

.status-label {
    color: #dddddd;
    font-size: 12px;
}

button {
    all: unset;
    background-color: #141414;
    color: #ffffff;
    border: 1px solid #282828;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    text-align: center;
}

button:hover {
    background-color: #242424;
    border-color: #444444;
    color: #ffffff;
}

/* Blue Action Buttons (Scan, Connect, Manual) */
button.btn-blue,
.btn-blue {
    all: unset;
    background-color: #1a73e8 !important;
    color: #ffffff !important;
    border: 1px solid #1557b0 !important;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: bold;
    text-align: center;
}

button.btn-blue:hover,
.btn-blue:hover {
    background-color: #1557b0 !important;
    border-color: #0d47a1 !important;
    color: #ffffff !important;
}

button.btn-blue:active,
.btn-blue:active {
    background-color: #0d47a1 !important;
}

/* Red Danger Buttons (Forget, Disconnect) */
button.btn-red,
.btn-red {
    all: unset;
    background-color: #dc2626 !important;
    color: #ffffff !important;
    border: 1px solid #b91c1c !important;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: bold;
    text-align: center;
}

button.btn-red:hover,
.btn-red:hover {
    background-color: #b91c1c !important;
    border-color: #991b1b !important;
    color: #ffffff !important;
}

button.btn-red:active,
.btn-red:active {
    background-color: #991b1b !important;
}

/* Secondary / Dark Buttons */
button.btn-dark,
.btn-dark {
    all: unset;
    background-color: #1c1c1c !important;
    color: #ffffff !important;
    border: 1px solid #333333 !important;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    text-align: center;
}

button.btn-dark:hover,
.btn-dark:hover {
    background-color: #2a2a2a !important;
    border-color: #555555 !important;
    color: #ffffff !important;
}

/* Search Entry */
.search-entry {
    background-color: #0e0e0e;
    color: #ffffff;
    border: 1px solid #2c2c2c;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 12px;
}

.search-entry:focus {
    border-color: #1a73e8;
}

/* Network Row */
.net-row {
    background-color: #080808;
    border: 1px solid #1c1c1c;
    border-radius: 4px;
    padding: 10px 14px;
    margin: 3px 12px;
}

.net-row:hover {
    background-color: #141414;
    border-color: #333333;
}

.net-ssid {
    color: #ffffff;
    font-size: 13px;
    font-weight: bold;
}

.net-info {
    color: #888888;
    font-size: 11px;
}

.badge-connected {
    background-color: #052e16;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 3px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: bold;
}

.badge-saved {
    background-color: #172554;
    color: #60a5fa;
    border: 1px solid #1e40af;
    border-radius: 3px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: bold;
}

.section-hdr {
    color: #60a5fa;
    font-size: 10px;
    font-weight: bold;
    padding: 8px 14px 2px 14px;
    letter-spacing: 0.5px;
}
"""

# ─── Password Authentication Dialog ──────────────────────────────────────────
class PasswordDialog(Gtk.Dialog):
    def __init__(self, parent, ssid, security):
        super().__init__(transient_for=parent, modal=True)
        self.ssid = ssid
        self.set_title("Wi-Fi Authentication")
        self.set_default_size(380, -1)
        self.set_resizable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label(label=f"<b>[ AUTHENTICATION REQUIRED ]</b>\nNetwork: <span foreground='#60a5fa'><b>{ssid}</b></span>\nSecurity: {security}")
        lbl.set_use_markup(True)
        lbl.set_xalign(0)
        box.append(lbl)

        self.entry = Gtk.Entry()
        self.entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.entry.set_visibility(False)
        self.entry.set_placeholder_text("Enter Wi-Fi Password...")
        self.entry.add_css_class("search-entry")
        box.append(self.entry)

        show_cb = Gtk.CheckButton(label="Show password")
        show_cb.connect("toggled", lambda b: self.entry.set_visibility(b.get_active()))
        box.append(show_cb)

        btn_row = Gtk.Box(spacing=8)
        btn_row.set_halign(Gtk.Align.END)
        btn_row.set_margin_top(8)

        cancel = Gtk.Button(label="Cancel")
        cancel.add_css_class("btn-dark")
        cancel.connect("clicked", lambda _: self.response(Gtk.ResponseType.CANCEL))

        ok = Gtk.Button(label="Connect")
        ok.add_css_class("btn-blue")
        ok.connect("clicked", lambda _: self.response(Gtk.ResponseType.OK))

        btn_row.append(cancel)
        btn_row.append(ok)
        box.append(btn_row)

        self.set_child(box)

    def get_password(self):
        return self.entry.get_text()


# ─── Manual / Hidden Network Dialog ──────────────────────────────────────────
class ManualConnectDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(transient_for=parent, modal=True)
        self.set_title("Connect to Hidden / Manual Network")
        self.set_default_size(380, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label(label="<b>[ CONNECT TO MANUAL / HIDDEN NETWORK ]</b>")
        lbl.set_use_markup(True)
        lbl.set_xalign(0)
        box.append(lbl)

        self.ssid_entry = Gtk.Entry()
        self.ssid_entry.set_placeholder_text("Network Name (SSID)...")
        self.ssid_entry.add_css_class("search-entry")
        box.append(self.ssid_entry)

        self.pwd_entry = Gtk.Entry()
        self.pwd_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.pwd_entry.set_placeholder_text("Password (leave empty if open)...")
        self.pwd_entry.add_css_class("search-entry")
        box.append(self.pwd_entry)

        btn_row = Gtk.Box(spacing=8)
        btn_row.set_halign(Gtk.Align.END)
        btn_row.set_margin_top(8)

        cancel = Gtk.Button(label="Cancel")
        cancel.add_css_class("btn-dark")
        cancel.connect("clicked", lambda _: self.response(Gtk.ResponseType.CANCEL))

        ok = Gtk.Button(label="Connect")
        ok.add_css_class("btn-blue")
        ok.connect("clicked", lambda _: self.response(Gtk.ResponseType.OK))

        btn_row.append(cancel)
        btn_row.append(ok)
        box.append(btn_row)

        self.set_child(box)

    def get_details(self):
        return self.ssid_entry.get_text().strip(), self.pwd_entry.get_text()


# ─── Wi-Fi Row Widget ────────────────────────────────────────────────────────
# ─── Wi-Fi Row Widget ────────────────────────────────────────────────────────
class WifiRow(Gtk.Box):
    def __init__(self, net, parent_win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.net = net
        self.win = parent_win
        self.add_css_class("net-row")

        # ── Main Row ──────────────────────────────────────────
        main_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        # Signal meter
        bar_str = signal_bar(net["signal"])
        bar_lbl = Gtk.Label(label=bar_str)
        bar_lbl.set_width_chars(6)
        bar_lbl.set_xalign(0)
        main_row.append(bar_lbl)

        # SSID & Info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        ssid_lbl = Gtk.Label(label=net["ssid"])
        ssid_lbl.add_css_class("net-ssid")
        ssid_lbl.set_xalign(0)
        ssid_lbl.set_ellipsize(3)
        info_box.append(ssid_lbl)

        sec_str = net["security"] if net["security"] else "Open"
        detail_lbl = Gtk.Label(label=f"{sec_str}  •  {net['signal']}%")
        detail_lbl.add_css_class("net-info")
        detail_lbl.set_xalign(0)
        info_box.append(detail_lbl)
        main_row.append(info_box)

        # Actions
        act_box = Gtk.Box(spacing=6)
        act_box.set_valign(Gtk.Align.CENTER)

        if net["connected"]:
            badge = Gtk.Label(label="CONNECTED")
            badge.add_css_class("badge-connected")
            act_box.append(badge)

            disc_btn = Gtk.Button(label="Disconnect")
            disc_btn.add_css_class("btn-red")
            disc_btn.connect("clicked", self.on_disconnect)
            act_box.append(disc_btn)

            if net["saved"]:
                f_btn = Gtk.Button(label="Forget")
                f_btn.add_css_class("btn-dark")
                f_btn.connect("clicked", self.on_forget)
                act_box.append(f_btn)
        else:
            if net["saved"]:
                badge = Gtk.Label(label="SAVED")
                badge.add_css_class("badge-saved")
                act_box.append(badge)

            self.conn_btn = Gtk.Button(label="Connect")
            self.conn_btn.add_css_class("btn-blue")
            self.conn_btn.connect("clicked", self.on_toggle_auth_box)
            act_box.append(self.conn_btn)

            if net["saved"]:
                f_btn = Gtk.Button(label="Forget")
                f_btn.add_css_class("btn-red")
                f_btn.connect("clicked", self.on_forget)
                act_box.append(f_btn)

        main_row.append(act_box)
        self.append(main_row)

        # ── Inline Password Input Box (2-Row Layout) ──
        self.inline_auth = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.inline_auth.set_margin_top(8)
        self.inline_auth.set_margin_bottom(4)
        self.inline_auth.add_css_class("status-box")
        self.inline_auth.set_visible(False)

        # Row 1: Password Label + Wider Entry + Single Blue Connect Button
        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        auth_lbl = Gtk.Label(label="Password:")
        auth_lbl.add_css_class("status-label")
        row1.append(auth_lbl)

        self.pwd_entry = Gtk.Entry()
        self.pwd_entry.set_hexpand(True)
        self.pwd_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.pwd_entry.set_visibility(False)
        self.pwd_entry.set_placeholder_text("Enter Wi-Fi security password...")
        self.pwd_entry.add_css_class("search-entry")
        self.pwd_entry.connect("activate", self.on_submit_inline)
        row1.append(self.pwd_entry)

        sub_btn = Gtk.Button(label="Connect ➔")
        sub_btn.add_css_class("btn-blue")
        sub_btn.connect("clicked", self.on_submit_inline)
        row1.append(sub_btn)

        self.inline_auth.append(row1)

        # Row 2: Show Password Checkbox + Secondary Action Buttons
        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        show_pwd = Gtk.CheckButton(label="Show password")
        show_pwd.connect("toggled", lambda b: self.pwd_entry.set_visibility(b.get_active()))
        row2.append(show_pwd)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        row2.append(spacer)

        if net["saved"]:
            saved_btn = Gtk.Button(label="󰌆 Use Saved Key")
            saved_btn.add_css_class("btn-dark")
            saved_btn.connect("clicked", lambda _: self.on_connect_saved())
            row2.append(saved_btn)

        cancel_btn = Gtk.Button(label="✕ Cancel")
        cancel_btn.add_css_class("btn-dark")
        cancel_btn.connect("clicked", lambda _: self.inline_auth.set_visible(False))
        row2.append(cancel_btn)

        self.inline_auth.append(row2)

        self.append(self.inline_auth)

    def on_toggle_auth_box(self, _):
        sec = self.net.get("security", "")
        if sec and "open" in sec.lower():
            self._do_connect("")
            return
        is_vis = self.inline_auth.get_visible()
        self.inline_auth.set_visible(not is_vis)
        if not is_vis:
            self.pwd_entry.grab_focus()

    def on_submit_inline(self, _):
        pwd = self.pwd_entry.get_text()
        self.inline_auth.set_visible(False)
        self._do_connect(pwd)

    def _do_connect(self, pwd):
        ssid = self.net["ssid"]
        self.win.set_status(f">> Connecting to '{ssid}'...")
        def task():
            r = connect_to_wifi(ssid, pwd)
            GLib.idle_add(self._after_action, r, f"Connected to {ssid}")
        threading.Thread(target=task, daemon=True).start()

    def on_connect_saved(self):
        ssid = self.net["ssid"]
        self.inline_auth.set_visible(False)
        self.win.set_status(f">> Activating saved connection '{ssid}'...")
        def task():
            r = connect_to_wifi(ssid)
            GLib.idle_add(self._after_action, r, f"Connected to {ssid}")
        threading.Thread(target=task, daemon=True).start()

    def on_disconnect(self, _):
        self.win.set_status(">> Disconnecting...")
        def task():
            devs = get_wifi_devices()
            dev = devs[0] if devs else "wlan0"
            r = nmcli(f'device disconnect {dev}')
            GLib.idle_add(self._after_action, r, "Disconnected")
        threading.Thread(target=task, daemon=True).start()

    def on_forget(self, _):
        ssid = self.net["ssid"]
        self.win.set_status(f">> Moving '{ssid}' to Forgotten Recovery...")
        def task():
            save_forgotten_network(ssid, self.net.get("security", ""))
            r = nmcli(f'connection delete "{ssid}"')
            GLib.idle_add(self._after_action, r, f"Moved '{ssid}' to Recovery list")
        threading.Thread(target=task, daemon=True).start()

    def _after_action(self, r, success_msg):
        if r.returncode == 0:
            self.win.set_status(f">> SUCCESS: {success_msg}")
        else:
            err = r.stderr.strip().split("\n")[0] if r.stderr.strip() else r.stdout.strip()
            self.win.set_status(f">> ERROR: {err}")
        self.win.refresh_networks()
        return False


# ─── Forgotten / Recoverable Network Widget ──────────────────────────────────
class ForgottenRow(Gtk.Box):
    def __init__(self, item, parent_win):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.item = item
        self.win = parent_win
        self.add_css_class("net-row")

        icon_lbl = Gtk.Label(label="[ ⟲ ]")
        icon_lbl.set_width_chars(6)
        icon_lbl.set_xalign(0)
        self.append(icon_lbl)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        ssid_lbl = Gtk.Label(label=item["ssid"])
        ssid_lbl.add_css_class("net-ssid")
        ssid_lbl.set_xalign(0)
        info_box.append(ssid_lbl)

        time_str = item.get("time", "")
        time_lbl = Gtk.Label(label=f"Forgotten profile  •  {time_str}")
        time_lbl.add_css_class("net-info")
        time_lbl.set_xalign(0)
        info_box.append(time_lbl)
        self.append(info_box)

        act_box = Gtk.Box(spacing=6)
        act_box.set_valign(Gtk.Align.CENTER)

        rec_btn = Gtk.Button(label="⟲ Recover")
        rec_btn.add_css_class("btn-blue")
        rec_btn.connect("clicked", self.on_recover)
        act_box.append(rec_btn)

        del_btn = Gtk.Button(label="✕ Purge")
        del_btn.add_css_class("btn-dark")
        del_btn.connect("clicked", self.on_delete)
        act_box.append(del_btn)

        self.append(act_box)

    def on_recover(self, _):
        ssid = self.item["ssid"]
        self.win.set_status(f">> Recovering '{ssid}' to Saved Profiles...")
        def task():
            ssid_clean = ssid.replace('"', '\\"')
            r = run_cmd(f'nmcli connection add type wifi con-name "{ssid_clean}" ifname "" ssid "{ssid_clean}" 802-11-wireless.cloned-mac-address preserve 2>/dev/null')
            remove_forgotten_network(ssid)
            GLib.idle_add(self._after_recover, ssid)
        threading.Thread(target=task, daemon=True).start()

    def _after_recover(self, ssid):
        self.win.set_status(f">> SUCCESS: Recovered '{ssid}' to Saved Profiles")
        self.win.refresh_networks()

    def on_delete(self, _):
        remove_forgotten_network(self.item["ssid"])
        self.win.set_status(f">> Deleted recovery entry for '{self.item['ssid']}'")
        self.win.refresh_networks()


# ─── Main Window ──────────────────────────────────────────────────────────────
class WifiMainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Wi-Fi Control Center")
        self.set_default_size(500, 600)
        self.set_resizable(True)

        self._networks = []
        self._filter_text = ""
        self._scanning = False

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(root)

        # ── Header Bar ───────────────────────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        hdr.add_css_class("term-header")

        row1 = Gtk.Box(spacing=8)
        title = Gtk.Label(label="󰖩  WI-FI & NETWORK MANAGER")
        title.add_css_class("term-title")
        title.set_hexpand(True)
        title.set_xalign(0)
        row1.append(title)

        self.rescan_btn = Gtk.Button(label="⟳ Rescan")
        self.rescan_btn.add_css_class("btn-blue")
        self.rescan_btn.connect("clicked", lambda _: self.trigger_full_scan())
        row1.append(self.rescan_btn)

        self.fix_btn = Gtk.Button(label="🛠 Fix Driver")
        self.fix_btn.add_css_class("btn-dark")
        self.fix_btn.connect("clicked", lambda _: subprocess.Popen(["kitty", "-e", "/home/vishal/Useless/fix_wifi_mt7921.sh"]))
        row1.append(self.fix_btn)

        self.manual_btn = Gtk.Button(label="+ Manual")
        self.manual_btn.add_css_class("btn-dark")
        self.manual_btn.connect("clicked", self.on_manual_connect)
        row1.append(self.manual_btn)

        hdr.append(row1)

        prompt_lbl = Gtk.Label(label="vishal@cachyos:~$ nmcli dev wifi")
        prompt_lbl.add_css_class("term-prompt")
        prompt_lbl.set_xalign(0)
        hdr.append(prompt_lbl)
        root.append(hdr)

        # ── Status Panel ─────────────────────────────────────────────────────
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.add_css_class("status-box")

        row_top = Gtk.Box(spacing=10)
        self.radio_switch = Gtk.Switch()
        self.radio_switch.set_active(get_wifi_status())
        self.radio_switch.connect("state-set", self.on_toggle_radio)

        sw_lbl = Gtk.Label(label="Wi-Fi Radio Power:")
        sw_lbl.add_css_class("status-label")
        row_top.append(sw_lbl)
        row_top.append(self.radio_switch)

        status_box.append(row_top)

        self.conn_info_lbl = Gtk.Label(label="Status: Checking...")
        self.conn_info_lbl.add_css_class("status-label")
        self.conn_info_lbl.set_xalign(0)
        status_box.append(self.conn_info_lbl)

        root.append(status_box)

        # ── Search / Filter Bar ──────────────────────────────────────────────
        search_box = Gtk.Box(spacing=8)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(4)

        search_lbl = Gtk.Label(label="Filter:")
        search_lbl.add_css_class("status-label")
        search_box.append(search_lbl)

        self.search_entry = Gtk.Entry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text("Search SSID / hotspot name...")
        self.search_entry.add_css_class("search-entry")
        self.search_entry.connect("changed", self.on_filter_changed)
        search_box.append(self.search_entry)
        root.append(search_box)

        # ── Network List (Scrollable) ────────────────────────────────────────
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_margin_top(6)

        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll.set_child(self.list_box)
        root.append(scroll)

        # ── Bottom Command Output / Status Line ──────────────────────────────
        self.cmd_status_lbl = Gtk.Label(label=">> Ready.")
        self.cmd_status_lbl.add_css_class("status-box")
        self.cmd_status_lbl.set_xalign(0)
        root.append(self.cmd_status_lbl)

        self.refresh_networks()

    def set_status(self, text):
        self.cmd_status_lbl.set_text(text)

    def on_toggle_radio(self, switch, state):
        def task():
            if state:
                nmcli("radio wifi on")
                run_cmd("nmcli dev set wlan0 managed yes 2>/dev/null")
                GLib.idle_add(self.set_status, ">> Wi-Fi Radio Turned ON")
                self.trigger_full_scan()
            else:
                nmcli("radio wifi off")
                GLib.idle_add(self.set_status, ">> Wi-Fi Radio Turned OFF")
                GLib.idle_add(self._render_disabled)
        threading.Thread(target=task, daemon=True).start()

    def on_manual_connect(self, _):
        dlg = ManualConnectDialog(self)
        dlg.connect("response", self._on_manual_resp)
        dlg.show()

    def _on_manual_resp(self, dlg, resp):
        if resp == Gtk.ResponseType.OK:
            ssid, pwd = dlg.get_details()
            dlg.destroy()
            if ssid:
                self.set_status(f">> Connecting manually to '{ssid}'...")
                def task():
                    r = connect_to_wifi(ssid, pwd)
                    GLib.idle_add(self._after_manual, r, ssid)
                threading.Thread(target=task, daemon=True).start()
        else:
            dlg.destroy()

    def _after_manual(self, r, ssid):
        if r.returncode == 0:
            self.set_status(f">> SUCCESS: Connected to {ssid}")
        else:
            self.set_status(f">> FAILED: {r.stderr.strip() or r.stdout.strip()}")
        self.refresh_networks()
        return False

    def on_filter_changed(self, entry):
        self._filter_text = entry.get_text().lower()
        self._render_list()

    def _clear_list(self):
        child = self.list_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.list_box.remove(child)
            child = nxt

    def _render_disabled(self):
        self._clear_list()
        self.conn_info_lbl.set_text("Status: Wi-Fi is disabled (Radio Off)")
        lbl = Gtk.Label(label="[ Wi-Fi Radio is turned OFF. Toggle switch above to enable. ]")
        lbl.add_css_class("status-label")
        lbl.set_margin_top(40)
        self.list_box.append(lbl)

    def trigger_full_scan(self):
        self.set_status(">> Triggering active Wi-Fi rescan...")
        def scan():
            run_cmd("nmcli dev set wlan0 managed yes 2>/dev/null; nmcli device wifi rescan 2>/dev/null")
            GLib.idle_add(self.refresh_networks)
        threading.Thread(target=scan, daemon=True).start()

    def refresh_networks(self):
        if self._scanning:
            return
        self._scanning = True

        def task():
            enabled = get_wifi_status()
            if not enabled:
                GLib.idle_add(self.radio_switch.set_active, False)
                GLib.idle_add(self._render_disabled)
                self._scanning = False
                return

            active = get_active_connection()
            saved = get_saved_connections()
            r = nmcli("-t -f SSID,SIGNAL,SECURITY dev wifi list")

            nets = []
            seen = set()
            active_ssid = active["ssid"] if active else None

            for line in r.stdout.strip().split("\n"):
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                ssid = ":".join(parts[:-2]).strip()
                if not ssid or ssid == "--" or ssid in seen:
                    continue
                seen.add(ssid)
                signal = parts[-2] if len(parts) >= 2 else "0"
                security = parts[-1] if len(parts) >= 1 else ""

                nets.append({
                    "ssid": ssid,
                    "signal": signal,
                    "security": security,
                    "saved": (ssid in saved),
                    "connected": (ssid == active_ssid)
                })

            # Also ensure saved networks not currently in air scan still appear in saved list
            for s in saved:
                if s not in seen:
                    nets.append({
                        "ssid": s,
                        "signal": "0",
                        "security": "Saved",
                        "saved": True,
                        "connected": False
                    })
                    seen.add(s)

            nets.sort(key=lambda x: (-x["connected"], -x["saved"], -int(x["signal"]) if x["signal"].isdigit() else 0))

            dev = active["device"] if active else "wlan0"
            ip = get_ip_address(dev)

            GLib.idle_add(self._update_ui, nets, active, ip)
            self._scanning = False

        threading.Thread(target=task, daemon=True).start()

    def _update_ui(self, nets, active, ip):
        self._networks = nets
        if active:
            ip_str = f" • IP: {ip}" if ip else ""
            self.conn_info_lbl.set_markup(
                f"Connected: <span foreground='#4ade80'><b>{active['ssid']}</b></span> "
                f"({active['signal']}%) [Dev: {active['device']}{ip_str}]"
            )
        else:
            self.conn_info_lbl.set_text("Status: Disconnected (No AP active)")

        self.set_status(f">> {len(nets)} networks listed. (Click Rescan for fresh beacon scan)")
        self._render_list()

    def _render_list(self):
        self._clear_list()
        filt = [n for n in self._networks if self._filter_text in n["ssid"].lower()]

        if not filt:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.set_margin_top(40)
            lbl = Gtk.Label(label="[ No Wi-Fi networks found in cache ]\nClick 'Rescan' to scan for nearby phones / routers.")
            lbl.add_css_class("status-label")
            lbl.set_justify(Gtk.Justification.CENTER)
            box.append(lbl)

            btn = Gtk.Button(label="⟳ Trigger Rescan Now")
            btn.add_css_class("btn-blue")
            btn.set_halign(Gtk.Align.CENTER)
            btn.connect("clicked", lambda _: self.trigger_full_scan())
            box.append(btn)
            self.list_box.append(box)
            return

        connected = [n for n in filt if n["connected"]]
        saved = [n for n in filt if n["saved"] and not n["connected"]]
        others = [n for n in filt if not n["saved"] and not n["connected"]]

        def add_sec(title, items):
            if items:
                hdr = Gtk.Label(label=f"── {title} ──────────────────────────────────────")
                hdr.add_css_class("section-hdr")
                hdr.set_xalign(0)
                self.list_box.append(hdr)
                for net in items:
                    self.list_box.append(WifiRow(net, self))

        add_sec("CONNECTED NETWORK", connected)
        add_sec("SAVED PROFILES", saved)
        add_sec("AVAILABLE ACCESS POINTS", others)

        # Forgotten / Recoverable Profiles
        forgotten = get_forgotten_networks()
        if self._filter_text:
            forgotten = [f for f in forgotten if self._filter_text in f["ssid"].lower()]

        if forgotten:
            hdr = Gtk.Label(label="── FORGOTTEN / RECOVERABLE PROFILES ──────────────")
            hdr.add_css_class("section-hdr")
            hdr.set_xalign(0)
            self.list_box.append(hdr)
            for item in forgotten:
                self.list_box.append(ForgottenRow(item, self))


# ─── Application Main ─────────────────────────────────────────────────────────
class WifiApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.win = None

    def do_activate(self):
        if self.win is None:
            self.win = WifiMainWindow(self)
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
    app = WifiApp()
    app.run(sys.argv)

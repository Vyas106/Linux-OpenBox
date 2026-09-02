#!/usr/bin/env python3
"""
Dynamic Pipe Menu Generator for Openbox & Labwc
- Automatically parses system and user XDG .desktop files
- Dynamically moves Last Opened / Most Recent apps to the top of Quick Launch
- Categorizes apps into cleanly organized submenus with counts
- Prepend crisp Nerd Font glyphs
- Session & Power options
- 100% XML Schema Compliant via ElementTree
"""

import os
import sys
import json
import xml.etree.ElementTree as ET

LAUNCHER_SCRIPT = "/home/vishal/Useless/menu/launch_app.py"
RECENTS_FILE = os.path.expanduser("~/.cache/openbox_menu_recents.json")

# Category definitions with icons and matching keywords
CATEGORIES = {
    "Development": {
        "icon": "󰅩",
        "label": "Development",
        "keywords": ["development", "ide", "editor", "programming", "code", "debugger"],
        "items": []
    },
    "Internet": {
        "icon": "󰈹",
        "label": "Internet & Web",
        "keywords": ["network", "webbrowser", "chat", "email", "feed", "transfer", "p2p"],
        "items": []
    },
    "Files": {
        "icon": "",
        "label": "File Management",
        "keywords": ["filemanager", "filetools", "archiving", "compression", "filesystem"],
        "items": []
    },
    "Office": {
        "icon": "󱞁",
        "label": "Office & Notes",
        "keywords": ["office", "texteditor", "wordprocessor", "notes", "viewer", "document"],
        "items": []
    },
    "Multimedia": {
        "icon": "󰕼",
        "label": "Media & Graphics",
        "keywords": ["audio", "video", "audiovideo", "graphics", "player", "recorder", "music", "photo"],
        "items": []
    },
    "System": {
        "icon": "󰒓",
        "label": "System & Tools",
        "keywords": ["system", "settings", "terminalemulator", "utility", "monitor", "package"],
        "items": []
    }
}

# Default quick launch tools to fallback or pad
DEFAULT_TOOLS = [
    {"name": "Kitty Terminal", "icon": "", "cmd": "kitty"},
    {"name": "Firefox Browser", "icon": "󰈹", "cmd": "firefox"},
    {"name": "Yazi File Manager", "icon": "", "cmd": "kitty -e yazi"},
    {"name": "Obsidian Notes", "icon": "󱞁", "cmd": "obsidian"},
    {"name": "Antigravity IDE", "icon": "󰨞", "cmd": "\"/home/vishal/Downloads/Antigravity IDE/antigravity-ide\""},
    {"name": "Control Center", "icon": "󰒓", "cmd": "python3 /home/vishal/Useless/control_center.py"},
    {"name": "Wi-Fi Manager", "icon": "󰤨", "cmd": "python3 /home/vishal/Useless/wifi_manager_tui.py"},
    {"name": "AI Assistant (Ollama)", "icon": "󰚩", "cmd": "kitty -e ollama run uncensored"}
]

def load_recents():
    if os.path.exists(RECENTS_FILE):
        try:
            with open(RECENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def scan_desktop_files():
    search_dirs = [
        os.path.expanduser("~/.local/share/applications"),
        "/usr/share/applications"
    ]
    seen_names = set()

    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for file in sorted(files):
                if not file.endswith(".desktop"):
                    continue
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    
                    name, exec_cmd, cats, nodisplay = None, None, "", False
                    for line in lines:
                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1].strip()
                        elif line.startswith("Exec=") and not exec_cmd:
                            raw_cmd = line.split("=", 1)[1].strip()
                            exec_cmd = raw_cmd.split("%")[0].strip()
                        elif line.startswith("Categories="):
                            cats = line.split("=", 1)[1].strip().lower()
                        elif line.startswith("NoDisplay=true"):
                            nodisplay = True

                    if not name or not exec_cmd or nodisplay or name in seen_names:
                        continue

                    seen_names.add(name)
                    assigned = False
                    for cat_key, cat_data in CATEGORIES.items():
                        if any(kw in cats for kw in cat_data["keywords"]):
                            cat_data["items"].append((name, exec_cmd))
                            assigned = True
                            break
                    if not assigned:
                        CATEGORIES["System"]["items"].append((name, exec_cmd))
                except Exception:
                    pass

def make_wrapped_cmd(name, icon, cmd):
    # Escape quotes for shell wrapper
    safe_name = name.replace('"', '\\"')
    safe_icon = icon.replace('"', '\\"')
    return f'{LAUNCHER_SCRIPT} "{safe_name}" "{safe_icon}" {cmd}'

def add_item(parent, label, command):
    item = ET.SubElement(parent, "item", label=label)
    action = ET.SubElement(item, "action", name="Execute")
    cmd = ET.SubElement(action, "command")
    cmd.text = command
    return item

def add_action_item(parent, label, action_name):
    item = ET.SubElement(parent, "item", label=label)
    ET.SubElement(item, "action", name=action_name)
    return item

def generate_menu_xml():
    scan_desktop_files()
    recents = load_recents()

    root = ET.Element("openbox_pipe_menu", xmlns="http://openbox.org/3.4/menu")

    # 1. DYNAMIC QUICK LAUNCH & RECENT APPS SECTION
    ET.SubElement(root, "separator", label="  RECENT & QUICK LAUNCH")

    shown_cmds = set()

    # A. Display Most Recently Opened Apps first
    if recents:
        for r in recents[:5]:
            r_name = r.get("name", "App")
            r_icon = r.get("icon", "󰄬")
            r_cmd = r.get("cmd", "")
            if r_cmd:
                shown_cmds.add(r_cmd)
                wrap_cmd = make_wrapped_cmd(r_name, r_icon, r_cmd)
                add_item(root, f"  {r_icon}  {r_name}", wrap_cmd)

    # B. Fill remainder of Quick Launch strip with default tools
    for tool in DEFAULT_TOOLS:
        if tool["cmd"] not in shown_cmds and len(shown_cmds) < 7:
            shown_cmds.add(tool["cmd"])
            wrap_cmd = make_wrapped_cmd(tool["name"], tool["icon"], tool["cmd"])
            add_item(root, f"  {tool['icon']}  {tool['name']}", wrap_cmd)

    # 2. Categorized Applications Section
    ET.SubElement(root, "separator", label="  APPLICATIONS")
    for key, cat in CATEGORIES.items():
        items = cat["items"]
        if not items:
            continue
        items.sort(key=lambda x: x[0].lower())
        cat_id = f"apps-{key.lower()}"
        cat_icon = cat["icon"]
        sub_menu = ET.SubElement(root, "menu", id=cat_id, label=f"  {cat_icon}  {cat['label']} ({len(items)})")
        for name, cmd in items:
            wrapped = make_wrapped_cmd(name, cat_icon, cmd)
            add_item(sub_menu, f"    {name}", wrapped)

    # 3. System & Power Controls
    ET.SubElement(root, "separator", label="  SYSTEM & POWER")
    add_item(root, "  󰌾  Lock Screen", "/home/vishal/Useless/lock.sh")
    add_action_item(root, "  󰑓  Reconfigure Openbox", "Reconfigure")
    add_item(root, "  󰜉  Restart System", "systemctl reboot")
    add_item(root, "  󰐥  Power Off", "systemctl poweroff")
    add_action_item(root, "  󰗼  Exit Openbox", "Exit")

    return ET.tostring(root, encoding="utf-8").decode("utf-8")

if __name__ == "__main__":
    print(generate_menu_xml())

#!/usr/bin/env python3
"""
Dynamic Pipe Menu Generator for Openbox & Labwc
- Automatically parses system and user XDG .desktop files
- Categorizes apps into cleanly organized submenus
- Prepend crisp Nerd Font glyphs
- Adds quick launch for workspace tools (Yazi, Obsidian, Antigravity IDE, Control Center, Wi-Fi Manager)
"""

import os
import sys
import xml.sax.saxutils as saxutils

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

def escape(text):
    return saxutils.escape(text or "")

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

def build_pipe_menu():
    scan_desktop_files()
    lines = ['<openbox_pipe_menu>']

    # 1. Quick Launch Section
    lines.append('  <separator label="  QUICK LAUNCH" />')
    lines.append('  <item label="    Kitty Terminal">')
    lines.append('    <action name="Execute"><command>kitty</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰈹  Firefox Browser">')
    lines.append('    <action name="Execute"><command>firefox</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="    Yazi File Manager">')
    lines.append('    <action name="Execute"><command>kitty -e yazi</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󱞁  Obsidian Notes">')
    lines.append('    <action name="Execute"><command>obsidian</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰨞  Antigravity IDE">')
    lines.append('    <action name="Execute"><command>&quot;/home/vishal/Downloads/Antigravity IDE/antigravity-ide&quot;</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰒓  Control Center">')
    lines.append('    <action name="Execute"><command>python3 /home/vishal/Useless/control_center.py</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰤨  Wi-Fi Manager">')
    lines.append('    <action name="Execute"><command>python3 /home/vishal/Useless/wifi_manager_tui.py</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰚩  AI Assistant (Ollama)">')
    lines.append('    <action name="Execute"><command>kitty -e ollama run uncensored</command></action>')
    lines.append('  </item>')

    # 2. Categorized Apps Section
    lines.append('  <separator label="  APPLICATIONS" />')
    for key, cat in CATEGORIES.items():
        items = cat["items"]
        if not items:
            continue
        items.sort(key=lambda x: x[0].lower())
        cat_id = f"apps-{key.lower()}"
        lines.append(f'  <menu id="{cat_id}" label="  {cat["icon"]}  {cat["label"]} ({len(items)})">')
        for name, cmd in items:
            lines.append(f'    <item label="    {escape(name)}">')
            lines.append(f'      <action name="Execute"><command>{escape(cmd)}</command></action>')
            lines.append('    </item>')
        lines.append('  </menu>')

    # 3. System Controls & Power
    lines.append('  <separator label="  SYSTEM &amp; POWER" />')
    lines.append('  <item label="  󰌾  Lock Screen">')
    lines.append('    <action name="Execute"><command>/home/vishal/Useless/lock.sh</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰑓  Reconfigure Openbox">')
    lines.append('    <action name="Reconfigure" />')
    lines.append('  </item>')
    lines.append('  <item label="  󰜉  Restart System">')
    lines.append('    <action name="Execute"><command>systemctl reboot</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰐥  Power Off">')
    lines.append('    <action name="Execute"><command>systemctl poweroff</command></action>')
    lines.append('  </item>')
    lines.append('  <item label="  󰗼  Exit Openbox">')
    lines.append('    <action name="Exit" />')
    lines.append('  </item>')

    lines.append('</openbox_pipe_menu>')
    return '\n'.join(lines)

if __name__ == "__main__":
    print(build_pipe_menu())

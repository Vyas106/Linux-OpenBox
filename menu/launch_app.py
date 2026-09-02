#!/usr/bin/env python3
"""
App launcher wrapper for Openbox / Labwc Menu
- Asynchronously spawns the application
- Tracks Most Recently Used (MRU) apps in ~/.cache/openbox_menu_recents.json
"""

import sys
import os
import json
import subprocess

RECENTS_FILE = os.path.expanduser("~/.cache/openbox_menu_recents.json")
MAX_RECENTS = 6

def record_and_launch():
    if len(sys.argv) < 2:
        return

    # If invoked with --clear
    if sys.argv[1] == "--clear":
        try:
            if os.path.exists(RECENTS_FILE):
                os.remove(RECENTS_FILE)
        except Exception:
            pass
        return

    if len(sys.argv) >= 4:
        name = sys.argv[1]
        icon = sys.argv[2]
        cmd = sys.argv[3]
    elif len(sys.argv) == 3:
        name = sys.argv[1]
        icon = "󰄬"
        cmd = sys.argv[2]
    else:
        name = "App"
        icon = "󰄬"
        cmd = sys.argv[1]

    # Save to recents
    try:
        os.makedirs(os.path.dirname(RECENTS_FILE), exist_ok=True)
        recents = []
        if os.path.exists(RECENTS_FILE):
            with open(RECENTS_FILE, "r", encoding="utf-8") as f:
                recents = json.load(f)
        
        # Filter out existing matching entries
        recents = [r for r in recents if r.get("cmd") != cmd and r.get("name") != name]
        
        # Prepend to the top of history
        recents.insert(0, {
            "name": name,
            "icon": icon,
            "cmd": cmd
        })
        
        recents = recents[:MAX_RECENTS]
        
        with open(RECENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(recents, f, indent=2)
    except Exception:
        pass

    # Launch application in background
    try:
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print(f"Error launching {cmd}: {e}", file=sys.stderr)

if __name__ == "__main__":
    record_and_launch()

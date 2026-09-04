#!/usr/bin/env bash
# Autostart / background launcher for Bottom-Left Desktop Input Box & AI Companion Widget

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Terminate existing instance if any
pkill -f "$SCRIPT_DIR/desktop_input_box.py" 2>/dev/null || true
sleep 0.3

# Launch in background with log capture
setsid python3 "$SCRIPT_DIR/desktop_input_box.py" > /tmp/desktop_input_box.log 2>&1 &

echo "Desktop Input Box widget launched successfully on top of bottom-left greeting box."

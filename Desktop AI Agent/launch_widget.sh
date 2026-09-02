#!/usr/bin/env bash
# Autostart / background launcher for Right-Side Desktop AI Agent Widget

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Terminate existing instance if any
pkill -f "$SCRIPT_DIR/main.py" 2>/dev/null || true
sleep 0.3

# Launch in background
nohup python3 "$SCRIPT_DIR/main.py" >/tmp/desktop_ai_agent.log 2>&1 &
disown

echo "Desktop AI Agent widget started on right side."

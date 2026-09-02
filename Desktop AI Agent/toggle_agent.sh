#!/usr/bin/env bash
# Robust toggle launcher for Desktop AI Agent widget
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

if pgrep -f "python.*$SCRIPT_DIR/main.py" >/dev/null; then
    pkill -f "python.*$SCRIPT_DIR/main.py" 2>/dev/null || true
else
    nohup python3 "$SCRIPT_DIR/main.py" "$@" >/tmp/desktop_ai_agent.log 2>&1 &
    disown
fi


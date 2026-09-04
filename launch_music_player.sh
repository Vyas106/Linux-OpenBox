#!/usr/bin/env bash
# Autostart / background launcher for JioSaavn Desktop Music Player Widget

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Terminate existing instance if any
pkill -f "$SCRIPT_DIR/desktop_music_player.py" 2>/dev/null || true
sleep 0.3

# Launch in background with log capture
setsid python3 "$SCRIPT_DIR/desktop_music_player.py" > /tmp/desktop_music_player.log 2>&1 &

echo "Desktop Music Player widget launched successfully between Left Input Box and Right Sidebar."

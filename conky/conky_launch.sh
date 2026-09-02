#!/usr/bin/env bash

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Sync conky configurations
mkdir -p "$HOME/.config/conky"
cp -rf /home/vishal/Useless/conky/* "$HOME/.config/conky/" 2>/dev/null
chmod +x "$HOME/.config/conky"/*.sh "$HOME/.config/conky"/*.py 2>/dev/null

# Terminate already running conky instances
killall -q conky 2>/dev/null
while pgrep -u $UID -x conky >/dev/null; do sleep 0.1; done

CONKY_CONF="$HOME/.config/conky/conky.conf"
if [ ! -f "$CONKY_CONF" ]; then
    CONKY_CONF="/home/vishal/Useless/conky/conky.conf"
fi

CONKY_GREETING_CONF="$HOME/.config/conky/conky_greeting.conf"
if [ ! -f "$CONKY_GREETING_CONF" ]; then
    CONKY_GREETING_CONF="/home/vishal/Useless/conky/conky_greeting.conf"
fi

# Launch Right-Sidebar Conky
nohup conky -c "$CONKY_CONF" >/dev/null 2>&1 &

# Launch Bottom-Left Greeting Box Conky
if [ -f "$CONKY_GREETING_CONF" ]; then
    nohup conky -c "$CONKY_GREETING_CONF" >/dev/null 2>&1 &
fi

echo "Conky instances (Right Sidebar & Bottom-Left Greeting) launched successfully."

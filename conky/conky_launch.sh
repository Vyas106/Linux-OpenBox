#!/usr/bin/env bash

# Terminate already running conky instances
killall -q conky 2>/dev/null

# Wait until processes are shut down
while pgrep -u $UID -x conky >/dev/null; do sleep 0.2; done

CONKY_CONF="$HOME/.config/conky/conky.conf"
if [ ! -f "$CONKY_CONF" ]; then
    CONKY_CONF="/home/vishal/Useless/conky/conky.conf"
fi

# Launch Conky in detached background mode
conky -c "$CONKY_CONF" >/dev/null 2>&1 &
disown

echo "Conky daemon started successfully."

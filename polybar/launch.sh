#!/usr/bin/env bash

# Terminate already running polybar instances
killall -q polybar 2>/dev/null

# Wait until the processes have been completely shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 0.1; done

CONFIG_PATH="$HOME/.config/polybar/config.ini"
if [ ! -f "$CONFIG_PATH" ]; then
    CONFIG_PATH="/home/vishal/Useless/polybar/config.ini"
fi

# Launch Polybar on primary monitor or all monitors detached
if type "xrandr" > /dev/null 2>&1; then
    for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
        MONITOR=$m polybar --reload main -c "$CONFIG_PATH" >/dev/null 2>&1 &
    done
else
    polybar --reload main -c "$CONFIG_PATH" >/dev/null 2>&1 &
fi

disown -a 2>/dev/null

echo "Polybar launched successfully."

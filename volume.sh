#!/usr/bin/env bash
mute=$(pactl get-sink-mute @DEFAULT_SINK@ 2>/dev/null | awk '{print $2}')
volume=$(pactl get-sink-volume @DEFAULT_SINK@ 2>/dev/null | grep -Po '[0-9]+(?=%)' | head -n1)

if [ "$mute" = "yes" ]; then
    echo "󰝟 Muted"
else
    if [ -z "$volume" ]; then
        echo "󰕾 N/A"
    else
        if [ "$volume" -eq 0 ]; then
            echo "󰕿 ${volume}%"
        elif [ "$volume" -lt 50 ]; then
            echo "󰖀 ${volume}%"
        else
            echo "󰕾 ${volume}%"
        fi
    fi
fi

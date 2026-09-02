#!/usr/bin/env bash

STATE_FILE="/tmp/polybar_time_mode"

# Toggle to next mode if called with "next"
if [ "$1" = "next" ]; then
    CURRENT=0
    if [ -f "$STATE_FILE" ]; then
        CURRENT=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
    fi
    NEXT=$(( (CURRENT + 1) % 3 ))
    echo "$NEXT" > "$STATE_FILE"
    exit 0
fi

# Read current mode
MODE=0
if [ -f "$STATE_FILE" ]; then
    MODE=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
fi

case "$MODE" in
    1)
        # State 1: Expanded Date
        echo " $(date '+%a, %d %b %Y')"
        ;;
    2)
        # State 2: 12-Hour Time with AM/PM
        echo " $(date '+%-I:%M %p')"
        ;;
    *)
        # State 0: 24-Hour Normal Time
        echo " $(date '+%H:%M')"
        ;;
esac

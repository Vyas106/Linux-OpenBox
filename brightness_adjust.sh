#!/usr/bin/env bash
current=$(xrandr --verbose 2>/dev/null | grep -m 1 -i brightness | awk '{print $2}')
if [ -z "$current" ]; then
    current=1.0
fi
step=0.1
if [ "$1" = "up" ]; then
    new=$(awk -v cur="$current" -v step="$step" 'BEGIN { new = cur + step; if (new > 1.0) new = 1.0; print new }')
else
    new=$(awk -v cur="$current" -v step="$step" 'BEGIN { new = cur - step; if (new < 0.1) new = 0.1; print new }')
fi
display=$(xrandr 2>/dev/null | grep " connected" | awk '{print $1}' | head -n1)
if [ -n "$display" ]; then
    xrandr --output "$display" --brightness "$new" >/dev/null 2>&1
fi

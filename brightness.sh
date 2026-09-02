#!/usr/bin/env bash
brightness=$(xrandr --verbose 2>/dev/null | grep -m 1 -i brightness | awk '{print $2}')
if [ -z "$brightness" ]; then
    echo "󰃠 N/A"
else
    pct=$(awk -v b="$brightness" 'BEGIN {print int(b*100)}')
    echo "󰃠 ${pct}%"
fi

#!/usr/bin/env bash

# Toggle behavior: if rofi calendar is open, close it
if pgrep -f "rofi.*calendar.rasi" > /dev/null; then
    pkill -f "rofi.*calendar.rasi"
    exit 0
fi

DATE_HEADER=$(date "+󰸗 %A, %d %B %Y  •  󰥔 %T")

CAL_OUTPUT=$(cal | sed 's/\x1b\[[0-9;]*m//g')

THEME_PATH="$HOME/.config/polybar/calendar.rasi"
if [ ! -f "$THEME_PATH" ]; then
    THEME_PATH="/home/vishal/Useless/polybar/calendar.rasi"
fi

echo "$CAL_OUTPUT" | rofi -dmenu \
    -theme "$THEME_PATH" \
    -mesg "$DATE_HEADER" \
    -p "Calendar"


#!/usr/bin/env bash

# Check Wi-Fi radio status
wifi_status=$(nmcli radio wifi 2>/dev/null)

if [ "$wifi_status" = "enabled" ]; then
    active_conn=$(nmcli -t -f ACTIVE,SSID,SIGNAL dev wifi 2>/dev/null | grep '^yes:' | head -n1)
    if [ -n "$active_conn" ]; then
        ssid=$(echo "$active_conn" | cut -d: -f2)
        signal=$(echo "$active_conn" | cut -d: -f3)
        # Truncate SSID if too long
        if [ ${#ssid} -gt 12 ]; then
            ssid="${ssid:0:10}.."
        fi
        echo "%{F#50fa7b}󰖩%{F-}  ${ssid}"
    else
        echo "%{F#888888}󰖩%{F-}  Disconnected"
    fi
else
    echo "%{F#666666}󰖪  Off%{F-}"
fi

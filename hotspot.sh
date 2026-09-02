#!/usr/bin/env bash
hotspot_conn=$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | grep ':802-11-wireless$' | cut -d: -f1 | head -n1)
if [ -z "$hotspot_conn" ]; then
    echo "󰏃 Off"
else
    hotspot_active=$(nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null | grep "^$hotspot_conn:")
    if [ -n "$hotspot_active" ]; then
        echo "󰏃 On"
    else
        echo "󰏃 Off"
    fi
fi

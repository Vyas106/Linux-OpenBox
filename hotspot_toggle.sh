#!/usr/bin/env bash
hotspot_conn=$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | grep ':802-11-wireless$' | cut -d: -f1 | head -n1)
if [ -z "$hotspot_conn" ]; then
    nmcli device wifi hotspot ssid "CachyOS-Hotspot" password "12345678" >/dev/null 2>&1
else
    hotspot_active=$(nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null | grep "^$hotspot_conn:")
    if [ -n "$hotspot_active" ]; then
        nmcli connection down "$hotspot_conn" >/dev/null 2>&1
    else
        nmcli connection up "$hotspot_conn" >/dev/null 2>&1
    fi
fi

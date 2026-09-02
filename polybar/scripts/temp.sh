#!/usr/bin/env bash

# Robust CPU temperature reader
get_temp() {
    # Try coretemp hwmon
    for h in /sys/class/hwmon/hwmon*; do
        if [ -f "$h/name" ] && [ "$(cat "$h/name" 2>/dev/null)" = "coretemp" ]; then
            if [ -f "$h/temp1_input" ]; then
                local raw
                raw=$(cat "$h/temp1_input" 2>/dev/null)
                if [ -n "$raw" ] && [ "$raw" -gt 0 ]; then
                    echo "$(( raw / 1000 ))"
                    return
                fi
            fi
        fi
    done

    # Try thermal zones
    for tz in /sys/class/thermal/thermal_zone*; do
        if [ -f "$tz/type" ]; then
            type=$(cat "$tz/type" 2>/dev/null)
            if [[ "$type" =~ (x86_pkg_temp|TCPU|acpitz|cpu-thermal|k10temp) ]]; then
                raw=$(cat "$tz/temp" 2>/dev/null)
                if [ -n "$raw" ] && [ "$raw" -gt 0 ]; then
                    echo "$(( raw / 1000 ))"
                    return
                fi
            fi
        fi
    done

    # Fallback to thermal_zone0
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        raw=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
        if [ -n "$raw" ]; then
            echo "$(( raw / 1000 ))"
            return
        fi
    fi

    echo "N/A"
}

TEMP=$(get_temp)

if [ "$TEMP" = "N/A" ]; then
    echo "󰔏 --°C"
else
    echo "󰔏 ${TEMP}°C"
fi

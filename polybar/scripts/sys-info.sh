#!/usr/bin/env bash

STATE_FILE="/tmp/polybar_sys_info_state"
CPU_CACHE="/tmp/polybar_cpu_cache"

# If toggle command is received
if [ "$1" = "toggle" ]; then
    if [ -f "$STATE_FILE" ] && [ "$(cat "$STATE_FILE" 2>/dev/null)" = "1" ]; then
        echo "0" > "$STATE_FILE"
    else
        echo "1" > "$STATE_FILE"
    fi
    exit 0
fi

# Check state (default 0: collapsed)
STATE=0
[ -f "$STATE_FILE" ] && STATE=$(cat "$STATE_FILE" 2>/dev/null)

if [ "$STATE" != "1" ]; then
    echo "󰍛  Info ▾"
    exit 0
fi

# Expanded state: compute live CPU, RAM, and Temperature


# 1. CPU Calculation
CPU_USAGE=0
if [ -r /proc/stat ]; then
    read -r _ c_user c_nice c_sys c_idle c_iowait c_irq c_softirq c_steal _ < /proc/stat
    c_total=$(( c_user + c_nice + c_sys + c_idle + c_iowait + c_irq + c_softirq + c_steal ))
    c_active=$(( c_user + c_nice + c_sys + c_irq + c_softirq + c_steal ))

    if [ -f "$CPU_CACHE" ]; then
        read -r p_total p_active < "$CPU_CACHE"
        total_diff=$(( c_total - p_total ))
        active_diff=$(( c_active - p_active ))
        if [ "$total_diff" -gt 0 ]; then
            CPU_USAGE=$(( active_diff * 100 / total_diff ))
            [ "$CPU_USAGE" -lt 0 ] && CPU_USAGE=0
            [ "$CPU_USAGE" -gt 100 ] && CPU_USAGE=100
        fi
    fi
    echo "$c_total $c_active" > "$CPU_CACHE"
fi

# 2. RAM Calculation
RAM_USAGE=0
if [ -r /proc/meminfo ]; then
    mem_total=$(grep -m1 '^MemTotal:' /proc/meminfo | awk '{print $2}')
    mem_avail=$(grep -m1 '^MemAvailable:' /proc/meminfo | awk '{print $2}')
    if [ -n "$mem_total" ] && [ -n "$mem_avail" ] && [ "$mem_total" -gt 0 ]; then
        mem_used=$(( mem_total - mem_avail ))
        RAM_USAGE=$(( mem_used * 100 / mem_total ))
    fi
fi

# 3. Temperature Calculation
get_temp() {
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
TEMP_STR="${TEMP}°C"
[ "$TEMP" = "N/A" ] && TEMP_STR="--°C"

# Output formatted expanded info with collapse indicator
echo "󰍛 Info ▴  ${CPU_USAGE}%  󰘚 ${RAM_USAGE}%  󰔏 ${TEMP_STR}"

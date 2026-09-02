#!/usr/bin/env bash

# Robust, Real-Time Network Speed Indicator for Polybar
# Measures live throughput across all active network interfaces (Wi-Fi, Ethernet, USB Tethering)

CACHE_FILE="/tmp/polybar_netspeed_cache"
NOW=$(date +%s%N)

# Extract total RX and TX bytes across all interfaces excluding loopback
read -r R2 T2 < <(awk '$1 ~ /:/ && $1 !~ /lo:/ {rx+=$2; tx+=$10} END {print (rx?rx:0), (tx?tx:0)}' /proc/net/dev)

format_speed() {
    local bytes=$1
    if [ "$bytes" -ge 10485760 ]; then # >= 10 MB/s (Ultra Fast: Cyan)
        awk "BEGIN {printf \"%%{F#00f0ff}%.1fM%%{F-}\", $bytes/1048576}"
    elif [ "$bytes" -ge 1048576 ]; then # >= 1 MB/s (Fast: Vibrant Green)
        awk "BEGIN {printf \"%%{F#50fa7b}%.1fM%%{F-}\", $bytes/1048576}"
    elif [ "$bytes" -ge 1024 ]; then # >= 1 KB/s (Normal: Light Grey)
        awk "BEGIN {printf \"%%{F#d4d4d4}%.0fK%%{F-}\", $bytes/1024}"
    else # < 1 KB/s (Idle / Low: Dim Grey)
        echo "%{F#777777}${bytes}B%{F-}"
    fi
}

if [ -f "$CACHE_FILE" ]; then
    read -r TIME_PREV R1 T1 < "$CACHE_FILE"
    TIME_DIFF=$(( (NOW - TIME_PREV) / 1000000 )) # milliseconds
    if [ "$TIME_DIFF" -gt 200 ] && [ "$TIME_DIFF" -lt 10000 ]; then
        RX_RATE=$(( (R2 - R1) * 1000 / TIME_DIFF ))
        TX_RATE=$(( (T2 - T1) * 1000 / TIME_DIFF ))
        [ "$RX_RATE" -lt 0 ] && RX_RATE=0
        [ "$TX_RATE" -lt 0 ] && TX_RATE=0

        DOWN=$(format_speed "$RX_RATE")
        UP=$(format_speed "$TX_RATE")
        echo " ${DOWN}   ${UP}"
    else
        echo " %{F#777777}0B%{F-}   %{F#777777}0B%{F-}"
    fi
else
    echo " %{F#777777}0B%{F-}   %{F#777777}0B%{F-}"
fi

echo "$NOW $R2 $T2" > "$CACHE_FILE"

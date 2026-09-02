#!/usr/bin/env bash

# Helper script to list active/recent applications for Conky
get_active_apps() {
    local apps=()
    local wids
    wids=$(xprop -root _NET_CLIENT_LIST 2>/dev/null | awk -F'#' '{print $2}' | tr ',' ' ')
    
    for wid in $wids; do
        [ -z "$wid" ] && continue
        local cname
        cname=$(xprop -id "$wid" WM_CLASS 2>/dev/null | awk -F'"' '{print $4}')
        [ -z "$cname" ] && continue
        
        # Filter out system desktop windows
        case "$cname" in
            Polybar|polybar|Conky|conky|tint2|Plank|plank|Desktop|desktop)
                continue
                ;;
        esac
        
        # Add icon based on application name
        local icon="󰣆"
        case "${cname,,}" in
            *firefox*|*chrome*|*brave*|*browser*)
                icon="󰈹" ;;
            *terminal*|*alacritty*|*kitty*|*urxvt*|*bash*)
                icon="" ;;
            *code*|*antigravity*|*nvim*|*vim*|*mousepad*)
                icon="󰨞" ;;
            *thunar*|*nautilus*|*pcmanfm*|*file*)
                icon="" ;;
            *discord*|*telegram*|*slack*)
                icon="󰭹" ;;
            *spotify*|*vlc*|*mpv*|*music*)
                icon="󰝚" ;;
            *btop*|*htop*)
                icon="" ;;
        esac
        
        # Avoid duplicates in list
        if [[ ! " ${apps[*]} " =~ " ${cname} " ]]; then
            apps+=("${icon}  ${cname}")
        fi
    done
    
    if [ ${#apps[@]} -eq 0 ]; then
        echo "No active user apps"
    else
        for app in "${apps[@]}"; do
            echo "$app"
        done | head -n 4
    fi
}

get_active_apps

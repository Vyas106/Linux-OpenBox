#!/usr/bin/env bash
# =============================================================================
# copyBord - Screenshot to Clipboard & File Utility
# Automatically captures screenshot, saves to file, and copies to Clipboard (Ctrl+C)
# =============================================================================

# Directory to store screenshots
SAVE_DIR="$HOME/Pictures/Screenshots"
mkdir -p "$SAVE_DIR"

# Generate timestamped filename
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
FILENAME="Screenshot_${TIMESTAMP}.png"
FILEPATH="${SAVE_DIR}/${FILENAME}"

MODE="${1:-select}"

copy_and_notify() {
    local img="$1"
    local title="$2"
    
    if [ -f "$img" ] && [ -s "$img" ]; then
        # Copy to X11 system clipboard (Ctrl+C / Ctrl+V buffer)
        xclip -selection clipboard -t image/png -i "$img"
        
        # Send desktop notification with thumbnail preview & quick actions
        if command -v dunstify &>/dev/null; then
            ACTION=$(dunstify -a "copyBord" \
                -i "$img" \
                -u normal \
                -t 5000 \
                --action="open,Open" \
                --action="folder,Open Folder" \
                "📋 Screenshot Copied to Clipboard" \
                "${title}\nSaved to ${FILENAME}")
            
            case "$ACTION" in
                "open")
                    xdg-open "$img" &
                    ;;
                "folder")
                    xdg-open "$SAVE_DIR" &
                    ;;
            esac
        elif command -v notify-send &>/dev/null; then
            notify-send -a "copyBord" -i "$img" "📋 Screenshot Copied to Clipboard" "${title}\nSaved to ${FILENAME}"
        fi
    fi
}

case "$MODE" in
    "select"|"region"|"area")
        # Freeze screen for clean area selection
        scrot -s -f -z -l style=solid,width=2,color="#7aa2f7" "$FILEPATH"
        copy_and_notify "$FILEPATH" "Selected region captured"
        ;;
        
    "full"|"screen")
        scrot -z "$FILEPATH"
        copy_and_notify "$FILEPATH" "Full screen captured"
        ;;
        
    "window"|"active")
        scrot -u -b -z "$FILEPATH"
        copy_and_notify "$FILEPATH" "Active window captured"
        ;;
        
    "delay"|"timer")
        DELAY="${2:-5}"
        scrot -d "$DELAY" -c -z "$FILEPATH"
        copy_and_notify "$FILEPATH" "${DELAY}s delayed screenshot captured"
        ;;
        
    "clip-only"|"copy")
        # Copy direct to clipboard without permanently saving
        TEMP_FILE=$(mktemp /tmp/screenshot_XXXXXX.png)
        scrot -s -f -z -l style=solid,width=2,color="#7aa2f7" "$TEMP_FILE"
        if [ -f "$TEMP_FILE" ] && [ -s "$TEMP_FILE" ]; then
            xclip -selection clipboard -t image/png -i "$TEMP_FILE"
            dunstify -a "copyBord" -i "$TEMP_FILE" -u normal -t 3000 "📋 Screenshot Copied to Clipboard" "Temporary selection copied (Ctrl+V ready)" 2>/dev/null
            rm -f "$TEMP_FILE"
        fi
        ;;
        
    *)
        echo "Usage: $0 [select|full|window|delay <sec>|clip-only]"
        exit 1
        ;;
esac

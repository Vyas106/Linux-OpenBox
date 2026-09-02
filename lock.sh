#!/usr/bin/env bash

# =============================================================================
# MODERN MINIMAL LOCKSCREEN SCRIPT
# Custom 4K Wallpaper + Minimalist Frosted Dark Card (Openbox / CachyOS Linux)
# Supports Super+L, laptop lid close, suspend, idle lock, and logind signals
# =============================================================================

# Ensure proper X11 display environment
export DISPLAY="${DISPLAY:-:0}"
if [ -z "$XAUTHORITY" ] && [ -f "$HOME/.Xauthority" ]; then
    export XAUTHORITY="$HOME/.Xauthority"
fi

# Prevent multiple lockscreen instances
if pgrep -u "$UID" -x i3lock >/dev/null 2>&1; then
    exit 0
fi

# Cache paths
LOCK_CACHE_DIR="$HOME/.cache"
LOCK_BG="$LOCK_CACHE_DIR/lockscreen_bg.png"
mkdir -p "$LOCK_CACHE_DIR"

# Generate modern lock canvas with user wallpaper & minimalist card
python3 - <<'EOF'
import os, sys, time, subprocess

# Wallpaper candidates in priority order
WALLPAPER_CANDIDATES = [
    os.path.expanduser("/home/vishal/Downloads/5819405-3840x2160-desktop-hd-pc-wallpaper_imgupscaler.ai_V1(Fast)_4K.jpg"),
    os.path.expanduser("~/Downloads/wallpaper.jpg"),
    os.path.expanduser("~/.config/wallpaper.jpg"),
    "/usr/share/backgrounds/default.png"
]

wallpaper_file = None
for wp in WALLPAPER_CANDIDATES:
    if os.path.exists(wp):
        wallpaper_file = wp
        break

# Get screen resolution
width, height = 1920, 1080
try:
    res = subprocess.check_output("xrandr --current 2>/dev/null | grep '\\*' | awk '{print $1}'", shell=True).decode().strip()
    if 'x' in res:
        parts = res.split()[0].split('x')
        width, height = int(parts[0]), int(parts[1])
except Exception:
    pass

output_path = os.path.expanduser('~/.cache/lockscreen_bg.png')
os.makedirs(os.path.dirname(output_path), exist_ok=True)

try:
    import gi
    gi.require_version('Gdk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import Gdk, GdkPixbuf
    import cairo

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # 1. Background (Wallpaper or Pure Black)
    if wallpaper_file:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(wallpaper_file, width, height, False)
            Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
            ctx.paint()

            # Elegant Dark Dimming Overlay (55% black for high contrast & readability)
            ctx.set_source_rgba(0, 0, 0, 0.55)
            ctx.paint()
        except Exception as e:
            # Fallback to pure black
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
    else:
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()

    # 2. Minimalist Center Card (Frosted Dark Glass)
    card_w, card_h = 440, 290
    card_x = (width - card_w) / 2
    card_y = (height - card_h) / 2

    # Card background: translucent dark glass
    ctx.set_source_rgba(0.04, 0.04, 0.04, 0.88)
    ctx.rectangle(card_x, card_y, card_w, card_h)
    ctx.fill()

    # White Border (1.5px)
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.9)
    ctx.set_line_width(1.5)
    ctx.rectangle(card_x, card_y, card_w, card_h)
    ctx.stroke()

    # Header Title
    ctx.select_font_face('JetBrainsMono Nerd Font', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(15)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    title = 'SYSTEM LOCKED'
    ext = ctx.text_extents(title)
    ctx.move_to(card_x + (card_w - ext.width) / 2, card_y + 48)
    ctx.show_text(title)

    # Digital Clock
    ctx.set_font_size(54)
    time_str = time.strftime('%H:%M')
    ext = ctx.text_extents(time_str)
    ctx.move_to(card_x + (card_w - ext.width) / 2, card_y + 124)
    ctx.show_text(time_str)

    # Date
    ctx.select_font_face('JetBrainsMono Nerd Font', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(13)
    ctx.set_source_rgb(0.8, 0.8, 0.8)
    date_str = time.strftime('%A, %d %B %Y')
    ext = ctx.text_extents(date_str)
    ctx.move_to(card_x + (card_w - ext.width) / 2, card_y + 165)
    ctx.show_text(date_str)

    # Subtle Divider Line
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.25)
    ctx.set_line_width(1.0)
    ctx.move_to(card_x + 35, card_y + 198)
    ctx.line_to(card_x + card_w - 35, card_y + 198)
    ctx.stroke()

    # Unlock Prompt
    ctx.set_font_size(12)
    ctx.set_source_rgb(0.95, 0.95, 0.95)
    prompt = 'ENTER PASSWORD TO UNLOCK'
    ext = ctx.text_extents(prompt)
    ctx.move_to(card_x + (card_w - ext.width) / 2, card_y + 242)
    ctx.show_text(prompt)

    surface.write_to_png(output_path)
except Exception as e:
    print(f"Lock screen generator fallback: {e}", file=sys.stderr)
EOF

# Launch i3lock with the generated wallpaper lockscreen
if [ -f "$LOCK_BG" ]; then
    i3lock -i "$LOCK_BG" -c 000000
else
    i3lock -c 000000
fi

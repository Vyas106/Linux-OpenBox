# 🚀 Minimalist Modern Openbox Setup (CachyOS / Arch Linux)

An ultra-lightweight, high-performance, and distraction-free desktop environment configuration built on **Openbox** and powered by **CachyOS (Arch Linux)**.

Designed with a **100% Pure Black & White Monochrome Aesthetic** (`#000000` background with crisp white typography and subtle borders). Built following the philosophy of **90% fast Shell scripts** for window management and keybindings, and **10% Python (GTK4)** for modern GUI control utilities.

---

## 📦 Modular Repositories

This setup is split into modular, standalone repositories for easy plug-and-play installation:

- ⚙️ [**Linux-OpenBox-Managers**](https://github.com/Vyas106/Linux-OpenBox-Managers) — Wi-Fi, Hotspot, Brightness, Volume, and Control Center GUI/TUI controllers.
- 📊 [**Linux-OpenBox-Panel**](https://github.com/Vyas106/Linux-OpenBox-Panel) — Minimalist Polybar setup and custom system widgets.
- 🖥️ [**Linux-OpenBox-Conky**](https://github.com/Vyas106/Linux-OpenBox-Conky) — Desktop sidebar system monitor HUD.
- 🔔 [**Linux-OpenBox-Dunst**](https://github.com/Vyas106/Linux-OpenBox-Dunst) — Monochrome Dunst notification daemon and smart lock screen suite.
- 🎯 [**Linux-OpenBox-Rofi**](https://github.com/Vyas106/Linux-OpenBox-Rofi) — App launcher theme and popup calendar HUD.
- 🪟 [**Linux-OpenBox-Core**](https://github.com/Vyas106/Linux-OpenBox-Core) — Core Openbox window manager configuration (`rc.xml`, `autostart`).

---

## 🌟 Features & Highlights

- 🖥️ **Pure Monochrome Aesthetic**: High-contrast, OLED-friendly, distraction-free pure black & white interface across all components.
- 📊 **Polybar Status Bar**:
  - Quick-launch pinned apps (Terminal, Browser, Files, VS Code, Ollama AI).
  - Dynamic workspace switcher & window actions (Minimize All, Close All).
  - Live system stats (CPU, RAM, Temp, Network speed).
  - Interactive popup calendar (`Rofi`-powered).
- 🎛️ **Modern GTK4 Control Center (`control_center.py`)**:
  - Volume & Brightness sliders with instant feedback.
  - Quick toggles for Hotspot, Bluetooth, Night Light, Lock Screen, and custom app slots.
- 📶 **Interactive Wi-Fi Manager (`wifi_manager_tui.py`)**:
  - Terminal-aesthetic GTK4 Wi-Fi interface.
  - Scan networks, connect, view saved profiles, forget networks, and generate QR codes for hotspot sharing.
- 🔒 **Smart Lock Screen & Daemon (`lock.sh` / `lock_daemon.py`)**:
  - Frosted minimalist lock screen with custom wallpaper rendering.
  - Background daemon reacting to laptop lid close, system suspend, idle timeouts, and `logind`/DBus lock events.
- 📋 **Conky Desktop Monitor**: Minimal system telemetry widget with CPU, RAM, Disk, and running process info.
- 🔔 **Dunst Notifications**: Clean monochrome notification styling matching the system theme.
- 🚀 **Rofi App Launcher**: Sleek, keyboard-driven application menu (`launcher.rasi`).

---

## ⌨️ Keybindings Cheat Sheet

All keybindings are configured in [`rc.xml`](file:///home/vishal/Useless/rc.xml).

### 🚀 Applications & Utilities
| Shortcut | Action |
| :--- | :--- |
| `Ctrl + Space` | Open Rofi Application Launcher |
| `Ctrl + Shift + W` | Launch GTK4 Wi-Fi Manager |
| `Super + B` | Launch Brightness Manager |
| `Super + O` | Launch Ollama AI in Kitty Terminal |
| `Super + L` / `Ctrl + Alt + L` | Lock Screen |
| `Super + D` | Toggle Show Desktop |

### 📸 Screenshots
| Shortcut | Action |
| :--- | :--- |
| `Super + Shift + S` | Select region screenshot (saved to `~/Pictures/Screenshots/`) |
| `PrintScreen` | Full-screen screenshot (saved to `~/Pictures/Screenshots/`) |

### 🔊 Media & Hardware Controls
| Shortcut | Action |
| :--- | :--- |
| `XF86AudioRaiseVolume` (Fn + F3) | Volume Up (+5%) |
| `XF86AudioLowerVolume` (Fn + F2) | Volume Down (-5%) |
| `XF86MonBrightnessUp` (Fn + F8) | Brightness Up (+10%) |
| `XF86MonBrightnessDown` (Fn + F7) | Brightness Down (-10%) |

### 🪟 Window & Workspace Navigation
| Shortcut | Action |
| :--- | :--- |
| `Alt + Tab` / `Alt + Shift + Tab` | Cycle forward / backward between windows |
| `Alt + F4` | Close active window |
| `Super + F1` .. `Super + F4` | Switch directly to Desktop 1, 2, 3, or 4 |
| `Ctrl + Alt + Arrow Keys` | Switch to adjacent desktop |
| `Shift + Alt + Arrow Keys` | Send active window to adjacent desktop |
| `Super + Shift + Arrow Keys` | Directional window focus cycle |

---

## 📁 Repository Structure

```
├── autostart                  # Openbox session autostart script
├── rc.xml                     # Core Openbox window manager & keybinding config
├── launcher.rasi              # Rofi application launcher theme
│
├── polybar/                   # Polybar configuration
│   ├── config.ini             # Polybar layout, colors, and modules
│   ├── launch.sh              # Multi-monitor Polybar launcher
│   ├── popup-calendar.sh      # Interactive calendar popup trigger
│   ├── calendar.rasi          # Calendar theme for Rofi
│   └── scripts/               # Status scripts (network speed, temp, sys-info, etc.)
│
├── conky/                     # Conky configuration
│   ├── conky.conf             # Minimal desktop widget telemetry
│   ├── conky_launch.sh        # Startup script for Conky
│   └── active_apps.sh         # Helper to parse active tasks
│
├── dunst/                     # Dunst notification daemon config
│   └── dunstrc                # Black & white minimalist notification theme
│
├── control_center.py          # Modern GTK4 Control Center popup
├── wifi_manager_tui.py        # Terminal-style GTK4 Wi-Fi Manager GUI
├── brightness_manager.py      # GUI Brightness Manager popup
├── lock_daemon.py             # Lock screen background daemon (lid/idle/suspend)
├── lock.sh                    # Lock screen renderer & invoker (i3lock)
│
├── hotspot.sh                 # Hotspot creation helper
├── hotspot_toggle.sh          # Quick toggle script for Wi-Fi hotspot
├── volume.sh                  # Volume adjustment helper with dunst notifications
├── brightness.sh              # Brightness adjustment helper
├── fix_wifi_mt7921.sh         # Driver patch script for MediaTek MT7921 Wi-Fi
├── Modelfile                  # Local Ollama AI model definition
└── Rule.txt                   # Design & architecture rules
```

---

## 📦 Dependencies & Prerequisites

To run this environment smoothly, install the required packages on Arch / CachyOS:

```bash
# Core Window Manager & Tools
sudo pacman -S openbox picom rofi polybar conky dunst feh scrot brightnessctl pulseaudio-utils

# Python & GTK4 Dependencies (for GUI utilities)
sudo pacman -S python python-gobject gtk4 libadwaita python-pillow python-cairo

# Fonts (Required for icons & status bar rendering)
sudo pacman -S ttf-jetbrains-mono-nerd ttf-nerd-fonts-symbols
```

---

## ⚙️ Installation & Usage

1. **Clone or navigate into the repository**:
   ```bash
   cd ~/Useless
   ```

2. **Make all scripts executable**:
   ```bash
   chmod +x autostart *.sh polybar/*.sh polybar/scripts/*.sh conky/*.sh
   ```

3. **Deploy configuration to `~/.config`**:
   The [`autostart`](file:///home/vishal/Useless/autostart) script automatically syncs configurations on login, or you can symlink/copy manually:
   ```bash
   mkdir -p ~/.config/openbox ~/.config/polybar ~/.config/conky ~/.config/rofi ~/.config/dunst
   cp rc.xml ~/.config/openbox/rc.xml
   cp autostart ~/.config/openbox/autostart
   cp -r polybar/* ~/.config/polybar/
   cp -r conky/* ~/.config/conky/
   cp launcher.rasi ~/.config/rofi/launcher.rasi
   cp dunst/dunstrc ~/.config/dunst/dunstrc
   ```

4. **Start Openbox**:
   Select **Openbox** from your display manager (SDDM, LightDM, Ly, etc.) or launch via `startx` with `exec openbox-session` in `~/.xinitrc`.

---

## 🎨 Design Philosophy

- **Background**: `#000000` (100% True Black)
- **Foreground / Text**: `#FFFFFF` / `#D4D4D4`
- **Borders & Dividers**: Subtle gray outlines (`#1C1C1C` / `#262626`)
- **Philosophy**: Minimal bloat, maximum keyboard productivity, sub-millisecond responsiveness.

# 📋 copyBord - Automatic Screenshot to Clipboard

**copyBord** ensures that whenever you capture a screenshot, it is **automatically copied to your system clipboard (Ctrl+C)** so you can immediately paste (`Ctrl+V`) into apps (Discord, Telegram, WhatsApp, Browser, Slack, GIMP, etc.) while also preserving a copy in `~/Pictures/Screenshots/`.

---

## ⌨️ Default Keybindings

| Keybinding | Action | Description |
|---|---|---|
| <kbd>Super</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> | **Select Area** | Freeze screen and drag a box to capture region -> auto-copied to Clipboard |
| <kbd>PrintScreen</kbd> | **Full Screen** | Capture whole screen -> auto-copied to Clipboard |
| <kbd>Alt</kbd> + <kbd>PrintScreen</kbd> | **Active Window** | Capture current focused window -> auto-copied to Clipboard |
| <kbd>Ctrl</kbd> + <kbd>PrintScreen</kbd> | **5s Timer Delay** | Capture screen after 5 seconds delay -> auto-copied to Clipboard |

---

## 🚀 Manual Usage

Run `screenshot.sh` with any of the following modes:

```bash
# Capture selected region (default)
/home/vishal/Useless/copyBord/screenshot.sh select

# Capture full screen
/home/vishal/Useless/copyBord/screenshot.sh full

# Capture active focused window
/home/vishal/Useless/copyBord/screenshot.sh window

# Delayed screenshot (5 seconds countdown)
/home/vishal/Useless/copyBord/screenshot.sh delay 5

# Capture region directly to clipboard without saving file
/home/vishal/Useless/copyBord/screenshot.sh clip-only
```

---

## ⚙️ Background Watcher Daemon

The `copybord_daemon.py` monitors `~/Pictures/Screenshots/`. If any external application or tool saves an image there, it will automatically load it into `xclip` clipboard!

```bash
python3 /home/vishal/Useless/copyBord/copybord_daemon.py &
```

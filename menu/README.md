# 📑 Linux-OpenBox-Menu

A modern, fast, and automated **Dynamic Pipe Menu Generator** and sleek **Dark UI Theme** for **Openbox** and **Labwc** on Linux / Arch / CachyOS.

---

## 📸 Overview & Features

- **🚀 100% Dynamic XDG Parsing**: Automatically discovers applications from `/usr/share/applications` and `~/.local/share/applications` in real time.
- **📁 Smart Auto-Categorization**: Intelligently organizes installed applications into categorized submenus with dynamic app counts:
  - 󰅩 **Development** (IDEs, text editors, dev tools)
  - 󰈹 **Internet & Web** (Browsers, clients, communication tools)
  -  **File Management** (Yazi, Dolphin, Thunar, archive managers)
  - 󱞁 **Office & Notes** (Obsidian, document viewers, office suites)
  - 󰕼 **Media & Graphics** (Audio, video players, graphics tools)
  - 󰒓 **System & Tools** (Terminals, monitors, system settings)
- **⚡ Quick Launch Strip**: Instant one-click access to essential daily tools (Kitty, Firefox, Yazi, Obsidian, Antigravity IDE, Control Center, Wi-Fi Manager, Ollama AI).
- **🎨 Sleek Onyx Modern Theme**: Pure minimalist black theme (`#0c0c0c` / `#080808`) with 1px border (`#222222`), subtle accent hover (`#1e3a8a`), and crisp `JetBrainsMono Nerd Font` typography.
- **🔒 Session & Power Controls**: Integrated Lock Screen, Openbox Reconfigure, Reboot, Power Off, and Exit actions.
- **🔄 Dual Compatibility**: Works out of the box with both **Openbox** (X11) and **Labwc** (Wayland).

---

## 🛠️ Repository Structure

```text
menu/
├── menu_generator.py   # Dynamic Python pipe menu generator
├── menu.xml            # Openbox / Labwc root menu definition
├── themerc             # Minimal dark UI theme for the menu
└── README.md           # Documentation and guide
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
Ensure Python 3 and Nerd Fonts are installed on your system:
```bash
sudo pacman -S python ttf-jetbrains-mono-nerd
```

### 2. Make Generator Executable
```bash
chmod +x /home/vishal/Useless/menu/menu_generator.py
```

### 3. Deploy to Openbox Config Directory
```bash
mkdir -p ~/.config/openbox ~/.themes/Onyx-Modern/openbox-3
cp menu.xml ~/.config/openbox/menu.xml
cp themerc ~/.themes/Onyx-Modern/openbox-3/themerc
```

### 4. Apply & Reload Openbox
Ensure your `~/.config/openbox/rc.xml` specifies `Onyx-Modern` as your active theme:
```xml
<theme>
  <name>Onyx-Modern</name>
  <font place="MenuItem">
    <name>JetBrainsMono Nerd Font</name>
    <size>10</size>
  </font>
  <font place="MenuHeader">
    <name>JetBrainsMono Nerd Font</name>
    <size>10</size>
    <weight>bold</weight>
  </font>
</theme>
```

Reload Openbox to apply changes live:
```bash
openbox --reconfigure
```

---

## 🖱️ Usage
- **Right-Click Desktop**: Opens the dynamic application and tools menu.
- **Middle-Click Desktop**: Access open windows or desktop switching.
- **Keybinding Trigger (Optional)**: Add `<keybind key="W-space"><action name="ShowMenu"><menu>root-menu</menu></action></keybind>` to `rc.xml` to trigger via keyboard.

---

## 📄 License
MIT License

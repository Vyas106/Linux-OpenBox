# Native Linux Desktop AI Agent (Qwen 2.5:3B)

A **native Linux desktop AI agent** built for **Arch Linux + Openbox**, powered locally by Ollama using `qwen2.5:3b`.

This application provides a single input interface to command your Linux system locally with live activity streaming, asynchronous PTY command execution, path sandboxing, and interactive safety approvals.

---

## 🌟 Key Features

* **True Native GTK4 Desktop UI**: Built with Python 3, GTK4 (`PyGObject`), and a modern dark theme designed for Openbox floating windows.
* **100% Local Execution**: Powered by Ollama (`http://localhost:11434`) and local Qwen 2.5:3B. No cloud keys, no telemetry.
* **Autonomous Multi-Step Tool Engine**:
  * `list_directory(path)`
  * `read_file(path, max_lines)`
  * `write_file(path, content)`
  * `edit_file(path, old_text, new_text)` (with unified diff viewer)
  * `create_directory(path)`
  * `delete_file(path)`
  * `move_file(source, destination)`
  * `search_files(path, pattern, search_content)`
  * `run_command(command)`
* **Live Streaming Output**: Commands execute asynchronously via PTY pipes with real-time stdout/stderr streaming into the GTK activity timeline without freezing the GUI.
* **Security & Sandboxing**:
  * Path validation preventing directory traversal outside `~/AIWorkspace`.
  * Command classifier detecting dangerous commands (`sudo`, `rm -rf`, `mkfs`, `dd`, `shutdown`, `systemctl`, `chmod`, `pacman -S`, etc.) and requiring interactive user approval (`Allow`, `Deny`, `Always Allow`).
* **Iterative Error Recovery**: Small model resilient tool-parsing and automatic error feedback loop for iterative bug fixing.
* **Keyboard Friendly**: Press **Enter** to submit task, **Shift+Enter** for new lines.

---

## 📋 Requirements

* **OS**: Arch Linux (or any Linux distribution with GTK4)
* **Window Manager**: Openbox (or any X11/Wayland desktop)
* **Python**: 3.10+
* **System Packages**:
  ```bash
  sudo pacman -S python python-pip python-gobject gtk4
  ```
* **Ollama**:
  ```bash
  # Start Ollama
  ollama serve

  # Pull Qwen 2.5:3B
  ollama pull qwen2.5:3b
  ```

---

## 🚀 Quick Start

### 1. Setup & Health Check
Run the automated setup script:
```bash
./setup.sh
```

### 2. Launch GUI Application
```bash
./run.sh
```

### 3. CLI Mode (Headless / Scripting)
You can also run tasks directly from your terminal:
```bash
python3 main.py --task "Create a python script math_test.py that computes 17 * 23, then execute it."
```

---

## ⌨️ Openbox Keybinding Setup

To launch or focus the AI agent with a shortcut (e.g., `Super + Space`), add the following to your `~/.config/openbox/rc.xml` inside the `<keyboard>` section:

```xml
<keybind key="W-space">
  <action name="Execute">
    <command>/home/vishal/Useless/Desktop AI Agent/run.sh</command>
  </action>
</keybind>
```

Then reconfigure Openbox:
```bash
openbox --reconfigure
```

---

## ⚙️ Configuration

Configuration is loaded from `~/.config/local-ai-agent/config.toml` (or `./config.toml`).

```toml
# Model settings
model = "qwen2.5:3b"
ollama_url = "http://localhost:11434"
temperature = 0.2
context_length = 8192

# Workspace sandbox
workspace = "~/AIWorkspace"

# Execution limits
max_tool_calls = 30

# UI Settings
window_width = 920
window_height = 740
dark_theme = true
require_confirmation = true
```

---

## 🧪 Running Tests

Run the complete automated unit test suite:
```bash
python3 -m unittest discover -s tests -v
```

---

## 📂 Project Structure

```text
Desktop AI Agent/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration manager (~/.config/local-ai-agent/config.toml)
│   ├── security.py            # Workspace sandbox & command permission classifier
│   ├── ollama_client.py       # Ollama API client & health check
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py        # Central tool registry & schema dispatcher
│   │   ├── filesystem.py      # File & directory operations
│   │   └── shell.py           # Async PTY subprocess execution & output streaming
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── prompts.py         # Tailored Qwen system prompts
│   │   ├── tool_parser.py     # Resilient tool parser
│   │   └── agent.py           # Multi-step autonomous agent loop
│   └── ui/
│       ├── __init__.py
│       ├── theme.py           # Modern dark CSS stylesheet for GTK4
│       ├── window.py          # Main GTK4 desktop window
│       ├── input_box.py       # Enter-to-run / Shift+Enter input box
│       ├── activity_view.py   # Live activity timeline & cards
│       ├── command_view.py    # Terminal-styled live output viewer
│       └── permission_dialog.py # Sensitive command approval banner
├── tests/
│   ├── test_security.py
│   ├── test_tools.py
│   ├── test_tool_parser.py
│   ├── test_shell.py
│   └── test_agent.py
├── local-ai-agent.desktop     # Desktop entry for Openbox menu / Rofi / dmenu
├── setup.sh                   # Setup and health check script
├── run.sh                     # Launch script
├── main.py                    # Application entrypoint
├── config.example.toml        # Sample configuration file
├── requirements.txt           # Python dependencies
└── system.md                  # Specifications & requirements
```

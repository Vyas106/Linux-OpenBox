# Build a Native Linux Desktop AI Agent for Arch Linux + Openbox

I want you to build a **native Linux desktop AI agent application** for my Arch Linux + Openbox desktop.

## VERY IMPORTANT

This must **NOT be a browser application**.

Do NOT build:

* React web UI
* Vite web UI
* Next.js
* FastAPI web interface
* browser-based dashboard
* localhost web application

I want a **real native Linux desktop window** that I can launch from Openbox.

The application should feel like a small desktop AI assistant: I open it, type one task into one input box, press Enter, and the local AI performs the task on my Linux computer while showing me exactly what it is doing.

---

# 1. Technology

Use:

* Python 3
* GTK4
* PyGObject (`gi`)
* Ollama
* Qwen2.5-Coder 3B running locally
* SQLite only if persistent task history is useful
* Linux subprocess/PTY for command execution
* asyncio/threads where necessary so the GTK interface never freezes

The default model should be:

```text
qwen2.5-coder:3b
```

Make the model configurable in a simple config file.

The application must communicate with the local Ollama server.

Default Ollama endpoint:

```text
http://localhost:11434
```

Do not require cloud APIs.

The application must work completely locally.

---

# 2. Main UI

Create a compact, modern GTK4 desktop window.

The main screen should look approximately like this:

┌────────────────────────────────────────────────────────────┐
│ Local AI Agent                                      − □ × │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  What do you want me to do?                                │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Type a task...                                       │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│                              [ Run ]                       │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ ACTIVITY                                                   │
│                                                            │
│ ● Understanding task...                                    │
│                                                            │
│ ✓ Inspecting workspace                                     │
│                                                            │
│ ▶ Running command                                          │
│   $ ls -la                                                 │
│                                                            │
│   total 32                                                 │
│   drwxr-xr-x ...                                           │
│                                                            │
│ ✓ Command completed                                        │
│                                                            │
│ ● Checking result...                                       │
│                                                            │
│ ✓ Task completed                                           │
└────────────────────────────────────────────────────────────┘

The exact visual design can be improved, but keep it simple and focused.

The primary interaction should be:

```text
open application
        ↓
type task
        ↓
press Enter
        ↓
AI works
        ↓
watch activity/output
        ↓
task completed
```

---

# 3. Single Input Box

The input box is the primary interface.

I should be able to type natural language such as:

```text
Create a Python project called test and run it.
```

or:

```text
Install neovim.
```

or:

```text
Find why my Python script is failing and fix it.
```

or:

```text
Create a folder called ~/test and put a hello.py file inside it.
```

or:

```text
Check my current directory and explain what files are important.
```

I should NOT need to manually select tools.

The AI decides what actions are required.

Pressing Enter should submit the task.

Shift+Enter should create a new line.

---

# 4. Agent System

Implement a real agent loop.

The flow should be:

```text
User task
   ↓
Qwen
   ↓
Qwen decides next action
   ↓
Tool call
   ↓
Tool executes
   ↓
Tool result returned to Qwen
   ↓
Qwen decides next action
   ↓
...
   ↓
Task completed
```

The agent must be able to perform multiple tool calls for one user request.

Example:

User:

```text
Create a Python project called hello and run it.
```

The agent might do:

```text
list_files()
create_directory()
write_file()
run_command()
inspect_output()
finish()
```

Do NOT simply ask Qwen for a final text answer.

Qwen must be able to actually operate the computer through tools.

---

# 5. Tools

Implement these initial tools:

```text
list_directory(path)

read_file(path)

write_file(path, content)

edit_file(path, old_text, new_text)

create_directory(path)

delete_file(path)

move_file(source, destination)

search_files(path, pattern)

run_command(command)
```

Each tool should return structured results to the agent.

For example:

```json
{
  "success": true,
  "exit_code": 0,
  "output": "..."
}
```

For errors:

```json
{
  "success": false,
  "exit_code": 1,
  "error": "..."
}
```

---

# 6. Linux Command Execution

This is extremely important.

Do NOT use a blocking subprocess call that freezes the GTK UI.

Commands must execute asynchronously.

Use:

```text
subprocess.Popen
```

or a PTY-based implementation.

I want command output to appear **live while the command is running**.

For example, if the AI runs:

```bash
sudo pacman -S docker
```

the UI should show:

```text
▶ Running command

$ sudo pacman -S docker

resolving dependencies...
looking for conflicting packages...
Packages (1) docker...

:: Proceed with installation? [Y/n]
```

The output should appear progressively, not only after the command finishes.

Capture:

* stdout
* stderr
* exit code
* process state

Display them in the activity panel.

---

# 7. Activity / Task Timeline

Below the input box, create a live activity panel.

The activity panel should show useful high-level actions.

Examples:

```text
● Understanding request
✓ Inspecting workspace
▶ Running command
✓ Command completed
● Reading file
▶ Editing file
✓ File updated
● Testing changes
✓ Tests passed
✓ Task completed
```

Each command should have an expandable output area.

Example:

```text
▶ Running command

$ python main.py

Hello World
Server started on port 8000

✓ Exit code: 0
```

Long output should be scrollable.

Do not flood the UI with unnecessary AI text.

Show concise status messages rather than exposing hidden chain-of-thought.

For example:

```text
● Inspecting project
```

instead of displaying private reasoning.

---

# 8. Command Approval / Safety

The AI will have access to my Linux machine, so implement a permission system.

Do NOT blindly execute dangerous commands.

Classify commands.

Safe commands can run automatically.

Potentially dangerous commands require confirmation.

Examples that should require confirmation:

```text
sudo ...
rm ...
rm -rf ...
mkfs ...
dd ...
shutdown ...
reboot ...
systemctl ...
chmod dangerous permissions
chown ...
package installation
network configuration
disk operations
```

When confirmation is required, display:

┌──────────────────────────────────────────────┐
│ ⚠ Permission required                       │
│                                              │
│ The AI wants to run:                         │
│                                              │
│ sudo pacman -S docker                        │
│                                              │
│ [ Allow ]              [ Deny ]              │
└──────────────────────────────────────────────┘

The task should pause until I choose.

Also allow a "Always allow for this task" option where appropriate.

Never hide dangerous commands from the user.

---

# 9. Workspace

Create a configurable workspace.

Default:

```text
~/AIWorkspace
```

The agent should preferably operate inside the workspace.

Implement path validation so the agent cannot accidentally escape the workspace through:

```text
../
```

or symbolic/path tricks.

Allow the user to configure trusted directories later.

For the first version, make the workspace clearly visible in the UI.

Example:

```text
Workspace: ~/AIWorkspace
```

---

# 10. File Operations

When the AI creates or modifies files, show it in the activity feed.

Example:

```text
▶ Creating file

~/AIWorkspace/hello/main.py

✓ File created
```

For edits:

```text
▶ Editing

src/main.py

+ print("Hello")
- print("hello")

[ View Diff ]
```

Implement a basic diff viewer if practical.

Do not silently overwrite important files without showing the user what happened.

---

# 11. Task State

The UI should clearly indicate whether the agent is:

```text
IDLE
THINKING
RUNNING
WAITING_FOR_PERMISSION
COMPLETED
FAILED
STOPPED
```

For example:

```text
● THINKING
```

```text
▶ RUNNING
```

```text
⚠ WAITING FOR PERMISSION
```

```text
✓ COMPLETED
```

```text
✗ FAILED
```

---

# 12. Stop Button

While the agent is working, show:

```text
[ Stop ]
```

Pressing Stop must:

* stop the current command/process where possible
* stop the agent loop
* return the application to IDLE
* not crash the application

---

# 13. Error Recovery

If a command fails:

```text
$ python main.py

Traceback...
```

the agent should receive the error and be able to decide whether to fix it.

For example:

```text
▶ Running command
✗ Command failed

● Analyzing error

▶ Editing main.py

✓ File updated

▶ Running command again

✓ Command completed
```

The agent should be capable of iterative debugging.

Set reasonable limits so it doesn't loop forever.

For example:

```text
maximum tool calls per task: 30
```

Make this configurable.

---

# 14. Ollama Integration

Create a clean Ollama client module.

Example architecture:

```text
app/
├── main.py
├── ui/
│   ├── window.py
│   ├── input_box.py
│   ├── activity_view.py
│   ├── command_view.py
│   └── permission_dialog.py
│
├── agent/
│   ├── agent.py
│   ├── prompts.py
│   └── tool_parser.py
│
├── tools/
│   ├── filesystem.py
│   ├── shell.py
│   └── registry.py
│
├── ollama_client.py
├── config.py
├── security.py
└── requirements.txt
```

Keep modules separated.

Do not put everything inside one giant Python file.

---

# 15. Model Prompt

Create a strong system prompt for Qwen.

The AI should understand:

```text
You are a local Linux computer agent.

Your job is to complete the user's requested task using the tools provided.

You may inspect files, create files, modify files, and execute Linux commands.

Do not claim that you performed an action unless the tool actually succeeded.

After each tool result, determine whether another action is necessary.

If a command fails, inspect the error and attempt to resolve it when appropriate.

Keep user-facing explanations concise.

Never reveal private chain-of-thought.

Use tools rather than merely describing what the user should do.
```

Adapt this to Qwen2.5-Coder 3B's capabilities.

---

# 16. Qwen Tool Calling

Implement robust tool-call parsing.

Qwen2.5-Coder 3B is a small local model, so assume that tool calls may occasionally be malformed.

The application should:

* validate tool names
* validate JSON arguments
* reject unknown tools
* validate required parameters
* return errors to the model
* retry malformed tool calls when reasonable
* prevent arbitrary Python execution generated by the model
* never execute tool names that aren't registered

Create a central tool registry:

```text
TOOL_REGISTRY
    list_directory
    read_file
    write_file
    edit_file
    create_directory
    delete_file
    move_file
    search_files
    run_command
```

---

# 17. Terminal / PTY

For commands requiring an interactive terminal, use a PTY.

The architecture should support:

```text
Agent
 ↓
run_command
 ↓
PTY
 ↓
live stdout/stderr
 ↓
GTK activity view
```

Eventually this should support commands such as:

```text
pacman
python
npm
git
ssh
```

where practical.

If a command requires interactive user input, the UI should make that obvious.

---

# 18. Openbox Integration

The application should be easy to launch from Openbox.

Create a desktop entry:

```text
~/.local/share/applications/local-ai-agent.desktop
```

Example:

```ini
[Desktop Entry]
Name=Local AI Agent
Comment=Local Linux AI Agent
Exec=/path/to/local-ai-agent
Terminal=false
Type=Application
Categories=Utility;
```

Also document how to add an Openbox keyboard shortcut such as:

```text
Super + Space
```

to launch/focus the application.

The application should support a compact floating-window style suitable for Openbox.

---

# 19. Configuration

Create a simple config file such as:

```text
~/.config/local-ai-agent/config.toml
```

Configuration should include:

```text
model = "qwen2.5-coder:3b"
ollama_url = "http://localhost:11434"
workspace = "~/AIWorkspace"
max_tool_calls = 30
window_width = 900
window_height = 700
```

Do not make configuration complicated.

---

# 20. No Cloud Dependency

Everything should work locally.

The normal flow is:

```text
GTK4
 ↓
Python
 ↓
Ollama
 ↓
Qwen2.5-Coder 3B
 ↓
Local Linux tools
```

No OpenAI API key.

No Anthropic API key.

No cloud service.

No browser.

---

# 21. Installation

Create an easy installation/setup script.

For Arch Linux, document dependencies such as:

```bash
sudo pacman -S python python-pip python-gobject gtk4 git
```

The README should explain:

1. Install Ollama.
2. Start Ollama.
3. Pull Qwen2.5-Coder 3B.
4. Create Python environment.
5. Install dependencies.
6. Start the application.
7. Install the `.desktop` file.
8. Configure Openbox shortcut.

Also include a health check:

```text
✓ GTK4
✓ Python
✓ Ollama
✓ Qwen model
✓ Workspace
```

If Ollama is unavailable, show a friendly error in the GUI.

---

# 22. First-run Experience

When the app starts, check:

```text
Is Ollama running?
Is qwen2.5-coder:3b installed?
Does the workspace exist?
Are required Python/GTK components available?
```

If everything works:

```text
✓ Local AI ready
```

If not:

```text
⚠ Ollama is not running.

Start Ollama and try again.
```

---

# 23. Design Requirements

The UI should be:

* dark
* compact
* clean
* keyboard-friendly
* responsive
* minimal
* native GTK
* suitable for a desktop assistant

Do not make it look like a website.

No unnecessary sidebar.

No dashboard.

No complicated navigation.

The primary screen is:

```text
INPUT
  ↓
ACTIVITY
  ↓
COMMAND OUTPUT
```

---

# 24. Important: Build a Working MVP First

Do NOT spend most of the time making the UI beautiful.

First make this exact workflow work:

```text
User types:

Create test.txt containing Hello World.
```

Then:

```text
Qwen
 ↓
write_file()
 ↓
Linux
 ↓
test.txt created
 ↓
GTK shows:

▶ Creating test.txt
✓ File created
✓ Task completed
```

Then test:

```text
Run:

echo Hello World
```

The UI must show:

```text
▶ Running command

$ echo Hello World

Hello World

✓ Exit code: 0
```

Then test a multi-step task:

```text
Create a folder called test,
create hello.py inside it,
and run hello.py.
```

The agent must perform multiple tools automatically.

---

# 25. Testing

Create tests for:

* tool parsing
* file path security
* workspace restrictions
* command execution
* malformed model output
* tool errors
* permission handling
* agent loop limits
* stopping commands
* Ollama connection failure

Do not allow a failed test to be silently ignored.

---

# 26. Final Deliverables

I want a complete runnable project.

Provide:

```text
source code
requirements.txt
README.md
setup.sh
run.sh
desktop entry
config example
tests
```

The project should run with something similar to:

```bash
./run.sh
```

Do not give me pseudocode.

Do not leave the core agent loop as TODO.

Do not leave command execution as TODO.

Do not leave GTK UI as TODO.

Build the working application.

---

# 27. Development Priority

Follow this order:

1. Ollama connection
2. Qwen agent loop
3. tool system
4. safe command execution
5. live command output
6. GTK input
7. GTK activity timeline
8. permission dialog
9. file operations
10. error recovery
11. configuration
12. Openbox integration
13. tests
14. polish

At every stage, keep the application runnable.

---

# MOST IMPORTANT USER EXPERIENCE

When I open the application, I want to feel like I have a local AI that can operate my Linux machine.

I should be able to say:

```text
"Install neovim and create a basic Python configuration."
```

and then watch:

```text
● Understanding request

▶ Checking system

$ pacman -Q neovim

✗ Not installed

⚠ Permission required

$ sudo pacman -S neovim

[ Allow ] [ Deny ]

▶ Installing

...live output...

✓ Installed

▶ Creating configuration

✓ File created

▶ Testing

✓ Configuration works

✓ Task completed
```

That **single input + autonomous tools + live activity + command output + permission approval** experience is the core product.

Build the application around this experience.

Before finishing, actually run the application and test the complete end-to-end flow with Ollama and the local Qwen model.

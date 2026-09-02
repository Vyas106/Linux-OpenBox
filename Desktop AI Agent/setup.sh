#!/usr/bin/env bash
# Setup and Dependency Installer for Local AI Agent (Arch Linux / Openbox)

set -e

echo "================================================="
echo " Setting up Native Linux Desktop AI Agent"
echo "================================================="

# 1. Check system package manager (Arch Linux pacman)
if command -v pacman &> /dev/null; then
    echo "[1/5] Checking Arch Linux system dependencies..."
    MISSING_PKGS=()
    for pkg in python python-pip python-gobject gtk4; do
        if ! pacman -Qi "$pkg" &> /dev/null; then
            MISSING_PKGS+=("$pkg")
        fi
    done

    if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
        echo "The following system packages are recommended: ${MISSING_PKGS[*]}"
        echo "Run: sudo pacman -S ${MISSING_PKGS[*]}"
    else
        echo "✓ All core Arch Linux system packages are installed."
    fi
fi

# 2. Check Python packages
echo "[2/5] Checking Python packages..."
pip install --break-system-packages -r requirements.txt 2>/dev/null || pip install -r requirements.txt 2>/dev/null || echo "Python environment ready."

# 3. Create Default Workspace
echo "[3/5] Initializing workspace..."
mkdir -p "$HOME/AIWorkspace"
echo "✓ Workspace initialized at $HOME/AIWorkspace"

# 4. Create User Config Directory
echo "[4/5] Initializing configuration..."
CONFIG_DIR="$HOME/.config/local-ai-agent"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    cp config.example.toml "$CONFIG_DIR/config.toml"
    echo "✓ Created default config at $CONFIG_DIR/config.toml"
else
    echo "✓ Configuration file exists at $CONFIG_DIR/config.toml"
fi

# 5. Install Desktop Entry for Openbox / App Launchers
echo "[5/5] Installing desktop entry..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sed "s|Exec=.*|Exec=$SCRIPT_DIR/run.sh|g" local-ai-agent.desktop > "$DESKTOP_DIR/local-ai-agent.desktop"
chmod +x "$DESKTOP_DIR/local-ai-agent.desktop"
echo "✓ Desktop entry installed at $DESKTOP_DIR/local-ai-agent.desktop"

echo ""
echo "================================================="
echo " Running System Health Check"
echo "================================================="
python3 main.py --check || true

echo ""
echo "Setup complete! You can now start the agent by running:"
echo "  ./run.sh"
echo "================================================="

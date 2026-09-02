#!/usr/bin/env bash
# Launcher script for Native Linux Desktop AI Agent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Launch Python GTK4 application
exec python3 main.py "$@"

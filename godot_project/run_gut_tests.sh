#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 1. Resolve Godot 4 binary location
GODOT_BIN=""

if [ -x "$PROJECT_DIR/bin/godot" ]; then
    GODOT_BIN="$PROJECT_DIR/bin/godot"
elif [ -x "$PROJECT_DIR/../bin/godot" ]; then
    GODOT_BIN="$PROJECT_DIR/../bin/godot"
elif command -v godot &>/dev/null; then
    GODOT_BIN="godot"
elif [ -x "/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64" ]; then
    GODOT_BIN="/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64"
else
    echo "ERROR: Godot 4 executable not found!"
    echo "Checked: $PROJECT_DIR/bin/godot, $PROJECT_DIR/../bin/godot, PATH, /home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64"
    exit 1
fi

echo "==> Using Godot binary: $GODOT_BIN"
echo "==> Project Directory: $PROJECT_DIR"

# 2. Run GUT Headless Runner
"$GODOT_BIN" --headless --path "$PROJECT_DIR" -s addons/gut/gut_cmdln.gd -gexit "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "==> All GUT tests passed successfully! (Exit code: 0)"
else
    echo "==> GUT tests FAILED! (Exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE

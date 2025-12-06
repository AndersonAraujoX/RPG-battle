#!/bin/bash
# Script to build the standalone executable for RPG Battle

# Ensure pyinstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
rm -rf build dist *.spec

# Build the executable
# --onefile: Create a single executable file
# --windowed: Do not show a console window (for GUI apps)
# --name: Name of the executable
# --add-data: Include assets and data folders (format: source:dest)
# Note: On Linux/Mac use ':', on Windows use ';' for add-data separator. Assuming Linux based on user OS.

echo "Building OsEsquecidos..."
pyinstaller --noconfirm --onefile --windowed --name "OsEsquecidos" \
    --add-data "assets:assets" \
    --add-data "dados:dados" \
    main.py

echo "Build complete! Executable is in dist/OsEsquecidos"

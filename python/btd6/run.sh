#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Find a working python command
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "ERROR: Python not found. Install Python 3.10+ from https://www.python.org"
    exit 1
fi

# Check version is 3.10+
VERSION=$($PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using $PY ($VERSION)"

# Install dependencies if needed
if ! $PY -c "import pygame" &>/dev/null; then
    echo "Installing dependencies..."
    $PY -m pip install --user -r requirements.txt
fi

echo "Launching Bloons TD 6..."
$PY main.py

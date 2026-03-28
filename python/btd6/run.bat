@echo off
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

python -c "import pygame" >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
)

echo Launching Bloons TD 6...
python main.py
pause

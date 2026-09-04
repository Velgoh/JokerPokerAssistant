@echo off
title Joker Poker Assistant
cd /d "%~dp0"

echo ================================================================
echo    Joker Poker - Video Poker & High-Low Assistant
echo ================================================================
echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3.8+ or open index.html directly in your browser.
    pause
    exit /b 1
)

echo Starting local server and opening your default browser...
echo (Press Ctrl+C in this window to stop the server)
echo.
python server.py
pause

@echo off
title SteamDealBot - Manual Poster
color 0A
echo.
echo ========================================
echo    🎮 SteamDealBot - Manual Poster 🎮
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "manual_poster.py" (
    echo ❌ Cannot find manual_poster.py
    echo Please make sure you're in the SteamDealBot folder
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo ✅ Project files found
echo.
echo Starting SteamDealBot...
echo.

REM Run the bot
python manual_poster.py

echo.
echo ========================================
echo Bot execution completed!
echo ========================================
echo.
echo Press any key to exit...
pause >nul

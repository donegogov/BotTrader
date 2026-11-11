@echo off
title BotTrader Install
echo ============================================
echo   BotTrader - instalacija (Windows)
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [GRESKA] Python ne e instaliran!
    echo.
    echo  1. Otvori https://www.python.org/downloads/
    echo  2. Simni "Download Python 3.12"
    echo  3. Pri instalacija STIKLIRAJ "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/2] Python e OK
echo [2/2] Instaliram paketi...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet requests telethon qrcode

echo.
echo ============================================
echo   Gotovo! Sega pokreni: 2-start-windows.bat
echo ============================================
pause

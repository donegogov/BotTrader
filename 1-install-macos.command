#!/bin/bash
cd "$(dirname "$0")"
echo "============================================"
echo "  BotTrader - instalacija (macOS)"
echo "============================================"
echo
if ! command -v python3 >/dev/null 2>&1; then
    echo "[GRESKA] Python3 ne e instaliran!"
    echo "Simni od: https://www.python.org/downloads/macos/"
    read -p "Pritisni ENTER za izlez..."
    exit 1
fi
echo "[1/2] Python3 e OK"
echo "[2/2] Instaliram paketi..."
python3 -m pip install --quiet --upgrade pip 2>/dev/null
python3 -m pip install --quiet --user requests telethon qrcode
echo
echo "============================================"
echo "  Gotovo! Sega pokreni: 2-start-macos.command"
echo "============================================"
read -p "Pritisni ENTER za izlez..."

#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "============================================"
echo "  BotTrader - instalacija (Linux)"
echo "============================================"
if ! command -v python3 >/dev/null 2>&1; then
    echo "[GRESKA] Instaliraj Python3:"
    echo "  sudo apt update && sudo apt install -y python3 python3-pip"
    exit 1
fi
echo "[1/2] Python3 e OK"
echo "[2/2] Instaliram paketi..."
python3 -m pip install --quiet --upgrade pip 2>/dev/null || true
python3 -m pip install --quiet --user requests || pip3 install --quiet requests
echo
echo "============================================"
echo "  Gotovo! Sega pokreni: ./2-start-linux.sh"
echo "============================================"

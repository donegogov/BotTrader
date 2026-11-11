#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f config.json ]; then
    echo "Prv pat - pokreni setup..."
    python3 bot_trader.py --setup
fi
python3 bot_trader.py
read -p "Pritisni ENTER za izlez..."

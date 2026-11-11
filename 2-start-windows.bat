@echo off
title BotTrader
cd /d "%~dp0"
if not exist config.json (
    echo Prv pat - pokreni setup...
    python bot_trader.py --setup
)
python bot_trader.py
pause

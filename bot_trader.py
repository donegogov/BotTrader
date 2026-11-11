#!/usr/bin/env python3
"""
================================================================================
  BotTrader — for PremTradingSig
================================================================================
  Follows signals from the Premium Trading Signals channel and trades them
  on YOUR OWN Bybit / Binance account.

  How it works
  ------------
  The channel is private, so it can't be read directly by a normal user.
  Instead, signals are published by the PremTradingSig relay server:

        https://<RELAY_HOST>/api/signals?since=<id>

  This program just polls that URL. It never touches the signal channel,
  never needs a Telegram token, and never uses anyone else's credentials.

  You only enter YOUR OWN exchange API keys (for live trading).

  Quick start
  -----------
      python bot_trader.py --setup     # first-time wizard
      python bot_trader.py             # run in paper mode (default)
      python bot_trader.py --status    # what is open right now

  Everything about positions lives in memory only — nothing is written to
  disk except config.json (created by --setup).
================================================================================
"""

import os
import sys
import json
import time
import argparse
import hashlib
import hmac
import shutil
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Dict, List

try:
    import requests
except ImportError:
    print("\n  Missing package: requests")
    print("  Install with:  pip install requests\n")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "relay_url": "https://signals.premtradingsig.com",
    "exchange": "bybit",              # bybit | binance
    "mode": "paper",                  # paper | live
    "leverage": 10,
    "coins": ["SOL", "BNB", "TRX"],   # any of the supported coins
    "max_positions": 4,
    "bybit_api_key": "",
    "bybit_api_secret": "",
    "binance_api_key": "",
    "binance_api_secret": "",
}

COIN_CHOICES = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "TRX",
                "LINK", "AVAX", "LTC", "BCH", "SUI", "NEAR", "DOT",
                "ARB", "OP", "TIA", "APT", "FIL", "INJ", "SEI"]


# ══════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════
def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    except Exception:
        return {}
    return {**DEFAULT_CONFIG, **cfg}


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def ask(question, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        v = input(f"{question}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return v or default


def setup_wizard():
    print("\n" + "=" * 64)
    print("  BotTrader — first-time setup")
    print("=" * 64)
    print("""
  This wizard will create config.json.
  Press ENTER to accept the default value shown in brackets.
""")

    cfg = dict(DEFAULT_CONFIG)

    print("\n[1/4] Relay address (provided by PremTradingSig)")
    url = ask("      Relay URL", cfg["relay_url"])
    cfg["relay_url"] = url.rstrip("/")

    print("\n[2/4] Exchange")
    print("      1) Bybit   2) Binance")
    ex = ask("      Choose (1/2)", "1")
    cfg["exchange"] = "binance" if ex.strip() == "2" else "bybit"

    print("\n[3/4] Coins to trade")
    print(f"      Supported: {', '.join(COIN_CHOICES)}")
    print("      Example: SOL,BNB,TRX")
    coins = ask("      Coins", ",".join(cfg["coins"]))
    cfg["coins"] = [c.strip().upper() for c in coins.split(",") if c.strip()]

    lev = ask("      Leverage (10 recommended)", str(cfg["leverage"]))
    try:
        cfg["leverage"] = int(lev)
    except ValueError:
        cfg["leverage"] = 10

    print("\n[4/4] Trading mode")
    print("      1) PAPER — simulate, no real money (recommended first)")
    print("      2) LIVE  — real money on your exchange account")
    m = ask("      Choose (1/2)", "1")
    cfg["mode"] = "live" if m.strip() == "2" else "paper"

    if cfg["mode"] == "live":
        print("\n  Enter your OWN API keys (keep them private!)")
        print("  Create them in the exchange dashboard: Read + Trade, no Withdraw.")
        if cfg["exchange"] == "bybit":
            cfg["bybit_api_key"] = ask("      Bybit API key")
            cfg["bybit_api_secret"] = ask("      Bybit API secret")
        else:
            cfg["binance_api_key"] = ask("      Binance API key")
            cfg["binance_api_secret"] = ask("      Binance API secret")

    save_config(cfg)
    print("\n  ✅ Saved to config.json")
    print("  Start trading with:  python bot_trader.py\n")


# ══════════════════════════════════════════════════════════════════════════
#  RELAY
# ══════════════════════════════════════════════════════════════════════════
def fetch_signals(relay_url: str, since_id: int) -> List[dict]:
    try:
        r = requests.get(f"{relay_url}/api/signals",
                         params={"since": since_id}, timeout=15)
        if r.status_code != 200:
            print(f"  [relay] HTTP {r.status_code}")
            return []
        data = r.json()
        return data.get("signals", [])
    except Exception as e:
        print(f"  [relay] error: {e}")
        return []


def check_relay(relay_url: str) -> bool:
    try:
        r = requests.get(f"{relay_url}/health", timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════
#  EXCHANGE (Bybit + Binance, minimal)
# ══════════════════════════════════════════════════════════════════════════
class BaseExchange:
    name = "base"

    def __init__(self, cfg):
        self.cfg = cfg
        self._instr = {}

    def instrument(self, symbol): raise NotImplementedError
    def price(self, symbol): raise NotImplementedError
    def set_leverage(self, symbol, lev): raise NotImplementedError
    def market_order(self, symbol, side, qty, sl, tp, lev): raise NotImplementedError
    def close(self, symbol, qty): raise NotImplementedError
    def balance(self): raise NotImplementedError
    def open_positions(self): raise NotImplementedError

    def size_for(self, symbol, price):
        inst = self.instrument(symbol)
        if not inst or not price:
            return 0.0
        step = inst["step"]
        qty = inst["min_qty"]
        if qty * price < inst["min_notional"]:
            qty = (inst["min_notional"] * 1.2) / price
            qty = round(qty / step) * step
        qty = max(qty, inst["min_qty"])
        if step >= 1:
            return int(round(qty))
        return round(qty, 8)


class BybitX(BaseExchange):
    name = "bybit"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.key = cfg.get("bybit_api_key", "")
        self.secret = cfg.get("bybit_api_secret", "")
        self.base = "https://api.bybit.com"

    def _sign(self, method, path, params):
        ts = str(int(time.time() * 1000))
        if method == "GET":
            q = urllib.parse.urlencode(sorted(params)); body = ""
        else:
            q = ""; body = json.dumps(params, separators=(",", ":"))
        payload = ts + self.key + "5000" + q + body
        sig = hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        h = {"X-BAPI-SIGN": sig, "X-BAPI-API-KEY": self.key,
             "X-BAPI-TIMESTAMP": ts, "X-BAPI-RECV-WINDOW": "5000",
             "Content-Type": "application/json"}
        url = self.base + path + (f"?{q}" if q else "")
        if method == "GET":
            return requests.get(url, headers=h, timeout=15).json()
        return requests.post(url, headers=h, data=body, timeout=15).json()

    def instrument(self, symbol):
        if symbol in self._instr:
            return self._instr[symbol]
        try:
            r = requests.get(self.base + "/v5/market/instruments-info",
                             params={"category": "linear", "symbol": symbol}, timeout=10)
            it = r.json()["result"]["list"][0]
            cfg = {"min_qty": float(it["lotSizeFilter"]["minOrderQty"]),
                   "step": float(it["lotSizeFilter"]["qtyStep"]),
                   "min_notional": float(it["lotSizeFilter"].get("minNotionalValue", 5) or 5)}
            self._instr[symbol] = cfg
            return cfg
        except Exception:
            return None

    def price(self, symbol):
        try:
            r = requests.get(self.base + "/v5/market/tickers",
                             params={"category": "linear", "symbol": symbol}, timeout=10)
            return float(r.json()["result"]["list"][0]["lastPrice"])
        except Exception:
            return None

    def set_leverage(self, symbol, lev):
        r = self._sign("POST", "/v5/position/set-leverage",
                       {"category": "linear", "symbol": symbol,
                        "buyLeverage": str(lev), "sellLeverage": str(lev)})
        return r.get("retCode") == 0

    def market_order(self, symbol, side, qty, sl, tp, lev):
        p = {"category": "linear", "symbol": symbol, "side": side,
             "orderType": "Market", "qty": str(qty), "leverage": str(lev)}
        if sl: p["stopLoss"] = str(round(sl, 8))
        if tp: p["takeProfit"] = str(round(tp, 8)); p["tpSlMode"] = "Full"
        r = self._sign("POST", "/v5/order/create", p)
        if r.get("retCode") != 0:
            return {"error": r.get("retMsg", r)}
        return {"id": r["result"].get("orderId")}

    def close(self, symbol, qty):
        pos = self.open_positions().get(symbol, {})
        side = "Sell" if pos.get("side") == "LONG" else "Buy"
        r = self._sign("POST", "/v5/order/create",
                       {"category": "linear", "symbol": symbol, "side": side,
                        "orderType": "Market", "qty": str(qty), "reduceOnly": True})
        if r.get("retCode") != 0:
            return {"error": r.get("retMsg", r)}
        return {"id": r["result"].get("orderId")}

    def balance(self):
        r = self._sign("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})
        if r.get("retCode") != 0:
            return None
        return float(r["result"]["list"][0].get("totalEquity", 0) or 0)

    def open_positions(self):
        out = {}
        r = self._sign("GET", "/v5/position/list", {"category": "linear", "settleCoin": "USDT"})
        if r.get("retCode") != 0:
            return out
        for p in r["result"]["list"]:
            size = float(p.get("size", 0) or 0)
            if size <= 0:
                continue
            out[p["symbol"]] = {"side": "LONG" if p.get("side") == "Buy" else "SHORT",
                                "size": size,
                                "entry": float(p.get("avgPrice", 0) or 0),
                                "mark": float(p.get("markPrice", 0) or 0),
                                "pnl": float(p.get("unrealisedPnl", 0) or 0)}
        return out


class BinanceX(BaseExchange):
    name = "binance"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.key = cfg.get("binance_api_key", "")
        self.secret = cfg.get("binance_api_secret", "")
        self.base = "https://fapi.binance.com"

    def _sign(self, method, path, params):
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        q = urllib.parse.urlencode(sorted(params.items()))
        sig = hmac.new(self.secret.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = self.base + path + "?" + q + "&signature=" + sig
        h = {"X-MBX-APIKEY": self.key}
        if method == "GET":
            return requests.get(url, headers=h, timeout=15).json()
        return requests.post(url, headers=h, timeout=15).json()

    def instrument(self, symbol):
        if symbol in self._instr:
            return self._instr[symbol]
        try:
            r = requests.get(self.base + "/fapi/v1/exchangeInfo", timeout=10)
            for s in r.json()["symbols"]:
                if s["symbol"] == symbol:
                    f = {x["filterType"]: x for x in s["filters"]}
                    cfg = {"min_qty": float(f["LOT_SIZE"]["minQty"]),
                           "step": float(f["LOT_SIZE"]["stepSize"]),
                           "min_notional": float((f.get("MIN_NOTIONAL") or {}).get("notional", 5.0))}
                    self._instr[symbol] = cfg
                    return cfg
        except Exception:
            return None
        return None

    def price(self, symbol):
        try:
            r = requests.get(self.base + "/fapi/v1/ticker/price",
                             params={"symbol": symbol}, timeout=10)
            return float(r.json()["price"])
        except Exception:
            return None

    def set_leverage(self, symbol, lev):
        r = self._sign("POST", "/fapi/v1/leverage", {"symbol": symbol, "leverage": lev})
        return "leverage" in r

    def market_order(self, symbol, side, qty, sl, tp, lev):
        r = self._sign("POST", "/fapi/v1/order",
                       {"symbol": symbol, "side": side, "type": "MARKET", "quantity": qty})
        if "orderId" not in r:
            return {"error": r}
        opp = "SELL" if side == "BUY" else "BUY"
        if sl:
            self._sign("POST", "/fapi/v1/order",
                       {"symbol": symbol, "side": opp, "type": "STOP_MARKET",
                        "stopPrice": round(sl, 8), "closePosition": "true"})
        if tp:
            self._sign("POST", "/fapi/v1/order",
                       {"symbol": symbol, "side": opp, "type": "TAKE_PROFIT_MARKET",
                        "stopPrice": round(tp, 8), "closePosition": "true"})
        return {"id": r["orderId"]}

    def close(self, symbol, qty):
        pos = self.open_positions().get(symbol, {})
        side = "SELL" if pos.get("side") == "LONG" else "BUY"
        r = self._sign("POST", "/fapi/v1/order",
                       {"symbol": symbol, "side": side, "type": "MARKET",
                        "quantity": qty, "reduceOnly": "true"})
        if "orderId" not in r:
            return {"error": r}
        return {"id": r["orderId"]}

    def balance(self):
        r = self._sign("GET", "/fapi/v2/account", {})
        return float(r.get("totalWalletBalance", 0)) if "totalWalletBalance" in r else None

    def open_positions(self):
        out = {}
        r = self._sign("GET", "/fapi/v2/positionRisk", {})
        if not isinstance(r, list):
            return out
        for p in r:
            size = abs(float(p.get("positionAmt", 0) or 0))
            if size <= 0:
                continue
            out[p["symbol"]] = {"side": "LONG" if float(p["positionAmt"]) > 0 else "SHORT",
                                "size": size,
                                "entry": float(p.get("entryPrice", 0) or 0),
                                "mark": float(p.get("markPrice", 0) or 0),
                                "pnl": float(p.get("unRealizedProfit", 0) or 0)}
        return out


def make_exchange(cfg):
    return BinanceX(cfg) if cfg["exchange"] == "binance" else BybitX(cfg)


# ══════════════════════════════════════════════════════════════════════════
#  TRADER (in-memory only)
# ══════════════════════════════════════════════════════════════════════════
class Trader:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ex = make_exchange(cfg)
        self.positions = {}          # in-memory: symbol -> dict
        self.last_signal_id = 0
        self.processed = set()
        self.started = datetime.now(timezone.utc)

    # ── display ────────────────────────────────────────────────────────
    def banner(self):
        c = self.cfg
        print("=" * 64)
        print(f"  BotTrader — {c['exchange'].upper()} — {c['mode'].upper()} — {c['leverage']}x")
        print("=" * 64)
        print(f"  Relay   : {c['relay_url']}")
        print(f"  Coins   : {', '.join(c['coins']) if c['coins'] else '(none)'}")
        print(f"  Max pos : {c['max_positions']}")
        if c["mode"] == "live":
            keys = c.get(f"{c['exchange']}_api_key", "")
            print(f"  API keys: {'set' if keys else 'MISSING'}")
        print("=" * 64)

    def status(self):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n  [{now}] ── status ──")
        if self.positions:
            for sym, p in self.positions.items():
                print(f"    {sym:9s} {p['side']:5s} {p['qty']} @ {p['entry']:.6f} "
                      f"SL {p['sl']:.6f} TP {p['tp']:.6f}")
        else:
            print("    (no open positions)")
        if self.cfg["mode"] == "live":
            bal = self.ex.balance()
            if bal is not None:
                print(f"    balance: ${bal:.2f}")
        print()

    # ── trading ────────────────────────────────────────────────────────
    def handle(self, sig):
        symbol = sig.get("symbol", "")
        coin = symbol.replace("USDT", "")
        if coin not in self.cfg["coins"]:
            return
        action = sig.get("signal", "")
        if "OPEN" in action:
            self.open(sig)
        elif "CLOSE" in action:
            self.close(sig)

    def open(self, sig):
        symbol = sig["symbol"]
        if symbol in self.positions:
            return
        if len(self.positions) >= self.cfg["max_positions"]:
            print(f"  [limit] max {self.cfg['max_positions']} positions")
            return
        price = float(sig["price"])
        sl_pct = float(sig["sl_pct"])
        tp_pct = float(sig["tp_pct"])
        lev = int(sig.get("leverage", self.cfg["leverage"]))
        is_long = "LONG" in sig["signal"]
        side = "Buy" if is_long else "Sell"
        sl = price * (1 - sl_pct) if is_long else price * (1 + sl_pct)
        tp = price * (1 + tp_pct) if is_long else price * (1 - tp_pct)
        qty = self.ex.size_for(symbol, price)
        if qty <= 0:
            print(f"  [{symbol}] cannot size")
            return

        if self.cfg["mode"] == "live":
            self.ex.set_leverage(symbol, lev)
            res = self.ex.market_order(symbol, side, qty, sl, tp, lev)
            if "error" in res:
                print(f"  ❌ {symbol} {side} rejected: {res['error']}")
                return
            print(f"  ✅ LIVE {symbol} {side} qty={qty} SL={sl:.6f} TP={tp:.6f}")
        else:
            print(f"  🚀 PAPER {symbol} {'LONG' if is_long else 'SHORT'} "
                  f"qty={qty} @ {price:.4f} SL={sl:.4f} TP={tp:.4f}")

        self.positions[symbol] = {"side": "LONG" if is_long else "SHORT",
                                  "qty": qty, "entry": price, "sl": sl, "tp": tp}

    def close(self, sig):
        symbol = sig["symbol"]
        if symbol not in self.positions:
            return
        pos = self.positions[symbol]
        if self.cfg["mode"] == "live":
            res = self.ex.close(symbol, pos["qty"])
            if "error" in res:
                print(f"  ❌ close {symbol}: {res['error']}")
                return
            print(f"  ✅ LIVE closed {symbol} ({sig['signal']})")
        else:
            print(f"  📉 PAPER closed {symbol} ({sig['signal']}) @ {sig.get('price')}")
        del self.positions[symbol]

    # ── loop ───────────────────────────────────────────────────────────
    def run(self):
        self.banner()
        if not check_relay(self.cfg["relay_url"]):
            print(f"\n  ⚠️  Relay not reachable: {self.cfg['relay_url']}")
            print("     Check your internet, or the relay is down.\n")
        if self.cfg["mode"] == "live":
            bal = self.ex.balance()
            print(f"  balance: ${bal:.2f}" if bal is not None
                  else "  ⚠️  cannot read balance — check API keys")
        print("\n  Listening for signals... (Ctrl+C to stop)\n")

        last_status = 0
        while True:
            try:
                signals = fetch_signals(self.cfg["relay_url"], self.last_signal_id)
                for s in signals:
                    sid = s.get("id", 0)
                    if sid in self.processed:
                        continue
                    self.processed.add(sid)
                    self.last_signal_id = max(self.last_signal_id, sid)
                    print(f"  [signal] {s.get('signal')} {s.get('symbol')} @ {s.get('price')}")
                    self.handle(s)
                if time.time() - last_status > 60:
                    self.status()
                    last_status = time.time()
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n  stopped")
                break
            except Exception as e:
                print(f"  [error] {e}")
                time.sleep(5)


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="BotTrader for PremTradingSig")
    ap.add_argument("--setup", action="store_true", help="first-time setup wizard")
    ap.add_argument("--status", action="store_true", help="show live status")
    args = ap.parse_args()

    if args.setup:
        setup_wizard()
        return

    cfg = load_config()
    if not cfg:
        print("\n  No config.json found.")
        print("  Run first:  python bot_trader.py --setup\n")
        sys.exit(1)

    t = Trader(cfg)

    if args.status:
        t.banner()
        t.status()
        if cfg["mode"] == "live":
            pos = t.ex.open_positions()
            print("  Exchange positions:")
            for sym, p in pos.items():
                print(f"    {sym:9s} {p['side']:5s} {p['size']} @ {p['entry']:.6f} "
                      f"PnL {p['pnl']:+.2f}")
            if not pos:
                print("    (none)")
        print()
        return

    if cfg["mode"] == "live" and not cfg.get(f"{cfg['exchange']}_api_key"):
        print("\n  LIVE mode needs API keys. Run --setup again.\n")
        sys.exit(1)

    t.run()


if __name__ == "__main__":
    main()

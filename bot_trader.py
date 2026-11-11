#!/usr/bin/env python3
"""
================================================================================
  BotTrader — for PremTradingSig
================================================================================
  Чита сигнали од Telegram каналот (преку ТВОЈОТ Telegram акаунт) и ги
  тргува на ТВОЈОТ Bybit / Binance акаунт.

  ЗОШТО TELEGRAM АКАУНТ?
  ----------------------
  Каналот е приватен (само членови можат да го читаат). Оваа програма се
  најавува со ТВОЈОТ телефонски број (како во Telegram апликацијата) и ги
  чита пораките како обичен член. Нема сервер, нема API, нема линкови —
  ништо не знае каде е ботот освен Telegram.

  ПРВО ПУШТАЊЕ:
      python bot_trader.py --login      # најава со телефон (еднаш)
      python bot_trader.py --setup      # поставки (коини, левериџ, режим)
      python bot_trader.py              # старт

  КОМАНДИ:
      --login    најава / проверка на Telegram сесија
      --setup    поставки (exchange, coins, leverage, paper/live)
      --status   што е отворено сега
      --logout   избриши ја Telegram сесијата
================================================================================
"""

import os
import sys
import json
import time
import asyncio
import argparse
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, List, Dict

try:
    import requests
except ImportError:
    print("\n  ❌ Недостасува пакет: requests")
    print("  Инсталирај:  pip install requests telethon\n")
    sys.exit(1)

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Chat
    from telethon.errors import (
        SessionPasswordNeededError,
        PhoneNumberInvalidError,
        PhoneNumberBannedError,
        PhoneCodeInvalidError,
        PhoneCodeExpiredError,
        FloodWaitError,
        ApiIdInvalidError,
    )
except ImportError:
    print("\n  ❌ Недостасува пакет: telethon")
    print("  Инсталирај:  pip install telethon\n")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SESSION_PATH = os.path.join(BASE_DIR, "telegram_session")

# Публични Telegram API credentials (исти за сите апарати, не се тајни)
TG_API_ID = 2040
TG_API_HASH = "b18441a1ff607e10a989891a5462e627"

DEFAULT_CONFIG = {
    "channel": "@premtradsignal",
    "tg_api_id": 0,
    "tg_api_hash": "",
    "exchange": "bybit",
    "mode": "paper",
    "leverage": 10,
    "coins": ["SOL", "BNB", "TRX"],
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


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def ask(q, default=""):
    s = f" [{default}]" if default else ""
    try:
        v = input(f"{q}{s}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return v or default


# ══════════════════════════════════════════════════════════════════════════
#  TELEGRAM LOGIN
# ══════════════════════════════════════════════════════════════════════════
def normalize_phone(raw: str) -> str:
    """Clean a phone number: remove spaces/dashes/brackets, one leading '+'."""
    s = (raw or "").strip()
    for ch in (" ", "-", "(", ")", ".", "/", "\t", "\u00a0", "\u2013", "\u2014"):
        s = s.replace(ch, "")
    if s.startswith("00"):
        s = "+" + s[2:]
    if s and not s.startswith("+"):
        s = "+" + s
    return s


def phone_looks_valid(p: str) -> bool:
    return p.startswith("+") and p[1:].isdigit() and 8 <= len(p[1:]) <= 15



def get_tg_creds():
    """API credentials — optional override from config.json (tg_api_id/tg_api_hash)."""
    try:
        cfg = load_config()
        return (int(cfg.get("tg_api_id") or TG_API_ID),
                str(cfg.get("tg_api_hash") or TG_API_HASH))
    except Exception:
        return TG_API_ID, TG_API_HASH


def render_qr(url: str):
    """Draw a scannable QR code in the terminal."""
    try:
        import qrcode
        q = qrcode.QRCode(border=2, box_size=1)
        q.add_data(url)
        q.make(fit=True)
        q.print_ascii(invert=True)
        return True
    except ImportError:
        print("\n  ⚠️  Недостасува пакетот 'qrcode'.")
        print("     Инсталирај:  pip install qrcode\n")
        print(f"  Или отвори го овој линк на телефон:\n  {url}\n")
        return False
    except Exception as e:
        print(f"  ⚠️ QR рендер: {e}")
        print(f"  Линк: {url}")
        return False


async def login_with_qr():
    """Login by scanning a QR with the Telegram app (no codes needed)."""
    api_id, api_hash = get_tg_creds()
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"  ✅ Веќе најавен како: {me.first_name or ''} (@{me.username or me.phone})")
        await client.disconnect()
        return True

    print("""
  📱 НАЈАВА СО QR КОД

  1. Отвори Telegram на телефон (со твојот број)
  2. Settings (Поставки) → Devices (Уреди)
  3. „Link Desktop Device" (Поврзи уред)
  4. Скенирај го QR кодот подолу 👇
""")

    deadline = time.time() + 240   # 4 минути
    qr = await client.qr_login()
    render_qr(qr.url)

    while time.time() < deadline:
        try:
            await qr.wait(timeout=25)
            # успешно скенирано
            try:
                me = await client.get_me()
                print(f"\n  ✅ Најавен како: {me.first_name or ''} (@{me.username or me.phone})")
            except Exception:
                print("\n  ✅ Најавен.")
            await client.disconnect()
            return True
        except asyncio.TimeoutError:
            # QR истече — нов
            print("\n  ⏳ QR истече, нов код...\n")
            try:
                qr = await client.qr_login()
                render_qr(qr.url)
            except Exception as e:
                print(f"  ❌ {e}")
                await client.disconnect()
                return False
        except SessionPasswordNeededError:
            print("\n  🔐 Имаш 2FA.")
            pwd = ask("  Твојата Telegram лозинка", "")
            try:
                await client.sign_in(password=pwd)
                print("\n  ✅ Најавен.")
                await client.disconnect()
                return True
            except Exception as e:
                print(f"  ❌ {e}")
                await client.disconnect()
                return False
        except Exception as e:
            print(f"\n  ❌ {type(e).__name__}: {e}")
            await client.disconnect()
            return False

    print("\n  ⏱ Времето истече. Пушти --login повторно.\n")
    await client.disconnect()
    return False


async def telegram_login():
    """Interactive login — QR (default) or phone + code."""
    print("\n" + "=" * 64)
    print("  Telegram најава")
    print("=" * 64)
    print("""
  Како сакаш да се најавиш?

    1) 📱 QR КОД  — скенираш со телефон (најлесно, без кодови)
    2) ☎️  ТЕЛЕФОН + КОД — ако QR не работи
""")
    choice = ask("  Избери (1/2)", "1").strip()

    if choice == "2":
        return await login_phone_code()
    return await login_with_qr()


async def login_phone_code():
    """Login with phone number + code."""
    print("""
  Ќе се најавиш со ТВОЈОТ телефонски број.

  Внеси го бројот СО државен код, на пример:
      +49 1512 3456789     (Germany — БЕЗ водечка 0!)
      +389 70 123 456      (Macedonia — БЕЗ водечка 0!)

  ✔ Празни места и цртички се дозволени — програмата ги брише.
  ✔ Мора да почнува со '+' .
""")

    phone = ""
    for _ in range(3):
        raw = ask("  Телефонски број", "")
        if not raw:
            print("  ❌ Откажано")
            return False
        phone = normalize_phone(raw)
        if phone_looks_valid(phone):
            break
        print(f"\n  ❌ „{raw}\" не е валиден број.")
        print("     Треба: + и 8-15 цифри. Пример: +4915123456789\n")
        phone = ""
    if not phone:
        return False

    print(f"\n  📱 Број: {phone}")
    print("     Ако е погрешен, притисни Ctrl+C сега и почни повторно.\n")

    api_id, api_hash = get_tg_creds()
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"  ✅ Веќе најавен како: {me.first_name or ''} (@{me.username or me.phone})")
        await client.disconnect()
        return True

    # ── Изпрати код ──
    sent = None
    for attempt in range(2):
        try:
            sent = await client.send_code_request(phone)
            print("  ✅ Кодот е пратен.")
            print("     Погледни ја Telegram апликацијата на ТОЈ телефон.")
            print("     Пораката е од „Telegram\" (не SMS).\n")
            break
        except PhoneNumberInvalidError:
            print(f"\n  ❌ Telegram: бројот „{phone}\" е невалиден.")
            print("     Провери го државниот код (пр. +49 за Германија).\n")
            await client.disconnect()
            return False
        except PhoneNumberBannedError:
            print("\n  ❌ Овој број е блокиран во Telegram.\n")
            await client.disconnect()
            return False
        except FloodWaitError as e:
            print(f"\n  ⏳ Премногу обиди. Почекај {e.seconds} секунди и пушти повторно.\n")
            await client.disconnect()
            return False
        except ApiIdInvalidError:
            print("\n  ❌ API конфигурацијата е невалидна (api_id/api_hash).\n")
            await client.disconnect()
            return False
        except Exception as e:
            print(f"\n  ❌ Грешка: {type(e).__name__}: {e}")
            if attempt == 0:
                again = ask("  Да пробам повторно? (d/n)", "d")
                if again.lower() not in ("d", "y", "да", ""):
                    await client.disconnect()
                    return False
                continue
            await client.disconnect()
            return False

    # ── Внеси код ──
    for attempt in range(3):
        code = ask("  Код од Telegram (5 цифри)", "").strip().replace(" ", "")
        if not code:
            print("  ❌ Откажано")
            await client.disconnect()
            return False
        try:
            await client.sign_in(phone=phone, code=code,
                                 phone_code_hash=sent.phone_code_hash if sent else None)
            break
        except SessionPasswordNeededError:
            print("\n  🔐 Имаш двофакторска заштита (2FA).")
            pwd = ask("  Твојата Telegram лозинка", "")
            if not pwd:
                await client.disconnect()
                return False
            try:
                await client.sign_in(password=pwd)
                break
            except Exception as e:
                print(f"\n  ❌ Погрешна лозинка: {e}\n")
                await client.disconnect()
                return False
        except PhoneCodeInvalidError:
            print(f"\n  ❌ Погрешен код. Обиди {attempt + 1}/3.\n")
            continue
        except PhoneCodeExpiredError:
            print("\n  ❌ Кодот истече. Пушти --login повторно.\n")
            await client.disconnect()
            return False
        except Exception as e:
            print(f"\n  ❌ {type(e).__name__}: {e}\n")
            continue
    else:
        await client.disconnect()
        return False

    try:
        me = await client.get_me()
        print(f"\n  ✅ Најавен како: {me.first_name or ''} (@{me.username or me.phone})")
    except Exception:
        print("\n  ✅ Најавен.")
    await client.disconnect()
    return True


async def telegram_logout():
    if not os.path.exists(SESSION_PATH + ".session"):
        print("  Нема активна сесија")
        return
    api_id, api_hash = get_tg_creds()
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    await client.connect()
    try:
        await client.log_out()
        print("  ✅ Одјавен. Сесијата е избришана.")
    except Exception as e:
        print(f"  ⚠️ {e}")
    await client.disconnect()
    try:
        os.remove(SESSION_PATH + ".session")
    except Exception:
        pass


def has_session() -> bool:
    return os.path.exists(SESSION_PATH + ".session")


# ══════════════════════════════════════════════════════════════════════════
#  SIGNAL PARSING
# ══════════════════════════════════════════════════════════════════════════
def parse_signal(text: str) -> Optional[dict]:
    if not text or "#signal" not in text:
        return None
    try:
        start = text.index("{", text.index("#signal"))
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        data = json.loads(text[start:end])
        if "signal" in data and "symbol" in data:
            return data
    except Exception:
        return None
    return None


# ══════════════════════════════════════════════════════════════════════════
#  EXCHANGES
# ══════════════════════════════════════════════════════════════════════════
class BaseExchange:
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
        return int(round(qty)) if step >= 1 else round(qty, 8)


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
            self._instr[symbol] = {
                "min_qty": float(it["lotSizeFilter"]["minOrderQty"]),
                "step": float(it["lotSizeFilter"]["qtyStep"]),
                "min_notional": float(it["lotSizeFilter"].get("minNotionalValue", 5) or 5)}
            return self._instr[symbol]
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
                    self._instr[symbol] = {
                        "min_qty": float(f["LOT_SIZE"]["minQty"]),
                        "step": float(f["LOT_SIZE"]["stepSize"]),
                        "min_notional": float((f.get("MIN_NOTIONAL") or {}).get("notional", 5.0))}
                    return self._instr[symbol]
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
        return float(r["totalWalletBalance"]) if "totalWalletBalance" in r else None

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
#  TRADER
# ══════════════════════════════════════════════════════════════════════════
class Trader:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ex = make_exchange(cfg)
        self.positions: Dict[str, dict] = {}
        self.seen: set = set()

    def banner(self):
        c = self.cfg
        print("=" * 64)
        print(f"  BotTrader — {c['exchange'].upper()} — {c['mode'].upper()} — {c['leverage']}x")
        print("=" * 64)
        print(f"  Канал    : {c['channel']}")
        print(f"  Коини    : {', '.join(c['coins']) if c['coins'] else '(нема)'}")
        print(f"  Max pos  : {c['max_positions']}")
        if c["mode"] == "live":
            k = c.get(f"{c['exchange']}_api_key", "")
            print(f"  API keys : {'✅ set' if k else '❌ MISSING'}")
        print("=" * 64)

    def show_status(self):
        t = datetime.now().strftime("%H:%M:%S")
        print(f"\n  [{t}] ── статус ──")
        if self.positions:
            for sym, p in self.positions.items():
                print(f"    {sym:9s} {p['side']:5s} {p['qty']} @ {p['entry']:.6f} "
                      f"SL {p['sl']:.6f} TP {p['tp']:.6f}")
        else:
            print("    (нема отворени позиции)")
        if self.cfg["mode"] == "live":
            b = self.ex.balance()
            if b is not None:
                print(f"    баланс: ${b:.2f}")
        print()

    def on_signal(self, sig: dict):
        symbol = sig.get("symbol", "")
        coin = symbol.replace("USDT", "")
        if coin not in self.cfg["coins"]:
            print(f"  [филтер] {symbol} не е во листата")
            return
        action = sig.get("signal", "")
        print(f"  [сигнал] {action} {symbol} @ {sig.get('price')}")
        if "OPEN" in action:
            self.open(sig)
        elif "CLOSE" in action:
            self.close(sig)

    def open(self, sig):
        symbol = sig["symbol"]
        if symbol in self.positions:
            return
        if len(self.positions) >= self.cfg["max_positions"]:
            print(f"  [лимит] макс {self.cfg['max_positions']} позиции")
            return
        price = float(sig["price"]); sl_pct = float(sig["sl_pct"]); tp_pct = float(sig["tp_pct"])
        lev = int(sig.get("leverage", self.cfg["leverage"]))
        is_long = "LONG" in sig["signal"]
        side = "Buy" if is_long else "Sell"
        sl = price * (1 - sl_pct) if is_long else price * (1 + sl_pct)
        tp = price * (1 + tp_pct) if is_long else price * (1 - tp_pct)
        qty = self.ex.size_for(symbol, price)
        if qty <= 0:
            print(f"  ❌ {symbol}: не можам да пресметам големина")
            return
        if self.cfg["mode"] == "live":
            self.ex.set_leverage(symbol, lev)
            res = self.ex.market_order(symbol, side, qty, sl, tp, lev)
            if "error" in res:
                print(f"  ❌ {symbol} {side} одбиено: {res['error']}")
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
        p = self.positions[symbol]
        if self.cfg["mode"] == "live":
            res = self.ex.close(symbol, p["qty"])
            if "error" in res:
                print(f"  ❌ затворање {symbol}: {res['error']}")
                return
            print(f"  ✅ LIVE затворено {symbol} ({sig['signal']})")
        else:
            print(f"  📉 PAPER затворено {symbol} ({sig['signal']}) @ {sig.get('price')}")
        del self.positions[symbol]


# ══════════════════════════════════════════════════════════════════════════
#  SETUP WIZARD
# ══════════════════════════════════════════════════════════════════════════
def setup_wizard():
    cfg = load_config() or dict(DEFAULT_CONFIG)
    print("\n" + "=" * 64)
    print("  BotTrader — поставки")
    print("=" * 64)
    print("  Притисни ENTER за да ја прифатиш вредноста во загради.\n")

    cfg["channel"] = ask("  Telegram канал", cfg["channel"])

    print("\n  Берза:  1) Bybit   2) Binance")
    ex = ask("  Избери (1/2)", "1" if cfg["exchange"] == "bybit" else "2")
    cfg["exchange"] = "binance" if ex.strip() == "2" else "bybit"

    print(f"\n  Достапни коини: {', '.join(COIN_CHOICES)}")
    print("  Пример: SOL,BNB,TRX")
    coins = ask("  Коини", ",".join(cfg["coins"]))
    cfg["coins"] = [c.strip().upper() for c in coins.split(",") if c.strip()]

    try:
        cfg["leverage"] = int(ask("  Левериџ (10 препорачано)", str(cfg["leverage"])))
    except ValueError:
        cfg["leverage"] = 10

    print("\n  Режим:")
    print("    1) PAPER — симулација (без пари) — препорачано прво")
    print("    2) LIVE  — реални пари")
    m = ask("  Избери (1/2)", "1" if cfg["mode"] == "paper" else "2")
    cfg["mode"] = "live" if m.strip() == "2" else "paper"

    if cfg["mode"] == "live":
        print("\n  Внеси ГИ ТВОИТЕ API клучеви (не ги споделувај со никого)")
        print("  Дозволи: Read + Trade, БЕЗ Withdraw")
        if cfg["exchange"] == "bybit":
            cfg["bybit_api_key"] = ask("  Bybit API key", cfg.get("bybit_api_key", ""))
            cfg["bybit_api_secret"] = ask("  Bybit API secret", cfg.get("bybit_api_secret", ""))
        else:
            cfg["binance_api_key"] = ask("  Binance API key", cfg.get("binance_api_key", ""))
            cfg["binance_api_secret"] = ask("  Binance API secret", cfg.get("binance_api_secret", ""))

    save_config(cfg)
    print("\n  ✅ Зачувано во config.json")
    print("  Старт:  python bot_trader.py\n")


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════
async def resolve_channel(client, channel: str):
    """Find the channel entity. Accepts @name, name, t.me/name or -100... id."""
    candidates = []
    ch = channel.strip()
    candidates.append(ch)
    if ch.startswith("https://t.me/"):
        candidates.append(ch.replace("https://t.me/", ""))
    if ch.startswith("t.me/"):
        candidates.append(ch.replace("t.me/", ""))
    if ch.startswith("@"):
        candidates.append(ch.lstrip("@"))
    else:
        candidates.append("@" + ch)

    for c in candidates:
        try:
            return await client.get_entity(c)
        except Exception:
            continue
    return None


async def run_trader(cfg):
    trader = Trader(cfg)
    trader.banner()

    api_id, api_hash = get_tg_creds()
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    await client.start()
    me = await client.get_me()
    print(f"  Најавен како: {me.first_name or ''} (@{me.username or me.phone})\n")

    # ── Membership check: only channel members can read signals ──
    entity = await resolve_channel(client, cfg["channel"])
    if entity is None:
        print(f"  ❌ Не можам да го најдам каналот: {cfg['channel']}")
        print("     Можни причини:")
        print("       1) Не си член на каналот — приклучи се прво")
        print("       2) Погрешно име — провери во config.json → \"channel\"")
        print("       3) Каналот е приватен и немаш пристап")
        await client.disconnect()
        return

    title = getattr(entity, "title", None) or str(entity.id)
    try:
        await client.get_messages(entity, limit=1)
        can_read = True
    except Exception as e:
        can_read = False
        print(f"  ⚠️  Не можам да читам пораки: {e}")

    if not can_read:
        print(f"  ❌ Немаш пристап до „{title}\".")
        print("     Само членови на каналот можат да читаат сигнали.")
        print("     Приклучи се на каналот, па пушти ме повторно.")
        await client.disconnect()
        return

    print(f"  ✅ Канал: „{title}\" — пристап потврден (член си)\n")

    if cfg["mode"] == "live":
        b = trader.ex.balance()
        print(f"  баланс: ${b:.2f}" if b is not None
              else "  ⚠️ не можам да го прочитам балансот (провери API клучеви)")

    @client.on(events.NewMessage(chats=entity))
    async def handler(event):
        text = event.message.message or ""
        sig = parse_signal(text)
        if sig:
            trader.on_signal(sig)
            trader.show_status()

    print(f"  👂 Слушам сигнали во „{title}\"... (Ctrl+C за стоп)\n")

    # periodic status
    async def heartbeat():
        while True:
            await asyncio.sleep(300)
            trader.show_status()

    asyncio.ensure_future(heartbeat())
    await client.run_until_disconnected()


def run_test_signal(cfg):
    """Offline paper test — feed a fake LONG_OPEN + CLOSE and show results."""
    t = Trader(cfg)
    t.banner()
    print("  🧪 ТЕСТ СИГНАЛ (не бара Telegram најава)\n")

    coin = cfg["coins"][0] if cfg["coins"] else "SOL"
    symbol = f"{coin}USDT"
    price = t.ex.price(symbol)
    if price is None:
        print(f"  ⚠️ не можам да прочитам цена за {symbol} — користам примерна 100.0")
        price = 100.0
    else:
        print(f"  цена {symbol}: {price}")

    open_sig = {"signal": "LONG_OPEN", "symbol": symbol, "price": price,
                "sl_pct": 0.05, "tp_pct": 0.10, "leverage": cfg["leverage"]}
    print("\n  ── 1) OPEN LONG ──")
    t.on_signal(open_sig)
    t.show_status()

    close_price = round(price * 0.97, 8)
    close_sig = {"signal": "LONG_CLOSE_SL", "symbol": symbol, "price": close_price,
                 "sl_pct": 0.05, "tp_pct": 0.10, "leverage": cfg["leverage"]}
    print(f"  ── 2) CLOSE LONG @ {close_price} (−3%) ──")
    t.on_signal(close_sig)
    t.show_status()

    print("  ✅ Тестот заврши. (`OPEN` + `CLOSE` горе = paper логиката работи)\n")
    print("  Следно за вистински сигнали:")
    print("     python bot_trader.py --login\n")


def main():
    ap = argparse.ArgumentParser(description="BotTrader for PremTradingSig")
    ap.add_argument("--login", action="store_true", help="најава со Telegram телефон")
    ap.add_argument("--logout", action="store_true", help="избриши Telegram сесија")
    ap.add_argument("--setup", action="store_true", help="поставки")
    ap.add_argument("--status", action="store_true", help="преглед на позиции")
    ap.add_argument("--test-signal", action="store_true", help="offline тест на paper логика")
    args = ap.parse_args()

    if args.logout:
        asyncio.run(telegram_logout())
        return

    if args.login:
        ok = asyncio.run(telegram_login())
        if ok:
            print("\n  Следно:  python bot_trader.py --setup\n")
        return

    if args.setup:
        setup_wizard()
        return

    cfg = load_config()
    if not cfg:
        print("\n  ❌ Нема config.json")
        print("  1) python bot_trader.py --login")
        print("  2) python bot_trader.py --setup\n")
        sys.exit(1)

    if args.status:
        t = Trader(cfg)
        t.banner()
        t.show_status()
        return

    if args.test_signal:
        run_test_signal(cfg)
        return

    if not has_session():
        print("\n  ❌ Нема Telegram сесија. Прво најави се:")
        print("     python bot_trader.py --login\n")
        sys.exit(1)

    if cfg["mode"] == "live" and not cfg.get(f"{cfg['exchange']}_api_key"):
        print("\n  ❌ LIVE режим бара API клучеви. Пушти --setup повторно.\n")
        sys.exit(1)

    try:
        asyncio.run(run_trader(cfg))
    except KeyboardInterrupt:
        print("\n  стоп")


if __name__ == "__main__":
    main()

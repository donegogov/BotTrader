# 🤖 BotTrader — for PremTradingSig

**Автоматски ги тргува сигналите од каналот PremTradingSig на твојот Bybit или Binance акаунт.**

Не ти треба никакво програмерско знаење. Само следи ги чекорите подолу.

---

## 📋 Што ти треба

| Што | Како |
|---|---|
| Компјутер | Windows, macOS или Linux |
| Интернет | ✅ |
| Bybit или Binance акаунт | (за реално тргување) |

**Не треба** ништо да плаќаш, нема скриени трошоци.

---

# 🪟 Windows — ЧЕКОР ПО ЧЕКОР

## Чекор 1: Симни Python

1. Отвори: **https://www.python.org/downloads/**
2. Кликни го големото **„Download Python 3.12"** копче
3. Кога ќе се симне, **кликни два пати** на фајлот
4. ⚠️ **ВАЖНО:** На првиот екран, **штиклирај го полето**:
   ```
   ☑ Add python.exe to PATH
   ```
   *(се наоѓа најдолу, мора да биде штиклирано!)*
5. Кликни **„Install Now"** и почекај 1-2 минути
6. Кликни **„Close"**

## Чекор 2: Провери дали Python работи

1. Кликни **Start** (кругот долу лево)
2. Напиши **`cmd`**
3. Кликни на **„Command Prompt"**
4. Ќе се отвори црн прозорец. Напиши и притисни ENTER:

```bash
python --version
```

Треба да видиш нешто како: `Python 3.12.4`

> ❌ Ако пишува „python is not recognized" — врати се на Чекор 1 и провери ја штиклираната опција. Потоа рестартирај компјутер.

## Чекор 3: Симни го BotTrader

1. Отвори: **https://github.com/PremTradingSig/BotTrader** *(линкот ќе го добиеш)*
2. Кликни го зелениот **„Code"** копче
3. Кликни **„Download ZIP"**
4. Отвори ја папката **Downloads** (Симнувања)
5. Кликни **десен клик** на `BotTrader-main.zip` → **„Extract All"**
6. Кликни **„Extract"**

## Чекор 4: Инсталирај потребниот пакет

1. Отвори ја извадената папка `BotTrader-main`
2. Кликни на адресната лента горе (каде пишува патеката)
3. Избриши сè и напиши **`cmd`**, притисни ENTER
4. Во црниот прозорец напиши:

```bash
pip install requests
```

*(почекај 10 секунди)*

## Чекор 5: Постави го ботот

Во истиот црн прозорец напиши:

```bash
python bot_trader.py --setup
```

Ќе те праша 4 прашања. **Само притискај ENTER** за да ги прифатиш препораките:

```
[1/4] Relay address (provided by PremTradingSig)
      Relay URL [https://signals.premtradingsig.com]:     ← ENTER

[2/4] Exchange
      1) Bybit   2) Binance
      Choose (1/2) [1]:                                    ← ENTER

[3/4] Coins to trade
      Supported: BTC, ETH, SOL, BNB, XRP, DOGE, ADA, TRX, ...
      Example: SOL,BNB,TRX
      Coins [SOL,BNB,TRX]:                                 ← ENTER

      Leverage (10 recommended) [10]:                      ← ENTER

[4/4] Trading mode
      1) PAPER — simulate, no real money (recommended first)
      2) LIVE  — real money on your exchange account
      Choose (1/2) [1]:                                    ← ENTER (за тест)
```

✅ **Готово!** Веднаш потоа ќе видиш:

```
========================================================================
  BotTrader — BYBIT — PAPER — 10x
========================================================================
  Relay   : https://signals.premtradingsig.com
  Coins   : SOL, BNB, TRX
  ...
  Listening for signals... (Ctrl+C to stop)
```

# 🍎 macOS — ЧЕКОР ПО ЧЕКОР

## Чекор 1: Провери дали Python го имаш

1. Кликни **⌘ + Space** (Spotlight)
2. Напиши **`Terminal`**, притисни ENTER
3. Во црниот прозорец напиши:

```bash
python3 --version
```

> ❌ Ако пишува „command not found" → оди на **https://www.python.org/downloads/macos/**, симни го и инсталирај го (клик-клик-инсталирај).

## Чекор 2: Симни го BotTrader

1. Отвори: **https://github.com/PremTradingSig/BotTrader**
2. Кликни **„Code"** → **„Download ZIP"**
3. Отвори ја папката **Downloads**
4. Кликни **два пати** на ZIP-от (сам ќе се отвори)

## Чекор 3: Отвори терминал во папката

1. Отвори **Terminal** (⌘ + Space → `Terminal`)
2. Напиши:

```bash
cd ~/Downloads/BotTrader-main
```

## Чекор 4: Инсталирај го пакетот

```bash
pip3 install requests
```

## Чекор 5: Постави го ботот

```bash
python3 bot_trader.py --setup
```

Притискај **ENTER** на сите прашања (прифаќа препорачани вредности).

✅ **Готово!** Ботот стартува во PAPER режим.

# 🐧 Linux — ЧЕКОР ПО ЧЕКОР

## Чекор 1: Отвори терминал

**Ubuntu/Debian:** `Ctrl + Alt + T`

## Чекор 2: Провери Python

```bash
python3 --version
```

> ❌ Ако не го има: `sudo apt update && sudo apt install python3 python3-pip`

## Чекор 3: Симни го

```bash
cd ~
git clone https://github.com/PremTradingSig/BotTrader.git
```

> ❌ Ако не работи (нема git): `sudo apt install git` прво

## Чекор 4: Инсталирај

```bash
cd BotTrader
pip3 install requests
```

## Чекор 5: Постави го

```bash
python3 bot_trader.py --setup
```

Притискај **ENTER** на сите прашања.

---

# ⚙️ КОМАНДИ (сите OS)

| Што сакаш | Windows | macOS | Linux |
|---|---|---|---|
| Прво поставување | `python bot_trader.py --setup` | `python3 bot_trader.py --setup` | `python3 bot_trader.py --setup` |
| Пушти го ботот | `python bot_trader.py` | `python3 bot_trader.py` | `python3 bot_trader.py` |
| Види статус | `python bot_trader.py --status` | `python3 bot_trader.py --status` | `python3 bot_trader.py --status` |
| Стоп | `Ctrl + C` | `Ctrl + C` | `Ctrl + C` |

---

# 🔑 Како да преминеш на РЕАЛНО тргување

Само кога ќе си сигурен (прво пробај 1-2 дена PAPER).

## 1. Направи API клуч на твојата берза

### Bybit
1. Оди на **bybit.com** → најави се
2. Кликни **профил** (горе десно) → **„API"** (или „API Management")
3. Кликни **„Create New Key"**
4. Тип: **„System-generated API Keys"**
5. Дозволи: **☑ Read-Write** *(ТРЕБА да биде*) / **☐ Withdraw** *(НЕ штиклирај!)*
6. Кликни **„Submit"**, внеси код од телефон
7. **Копирај ги** API Key и API Secret (Secret се покажува само еднаш!)

### Binance
1. **binance.com** → **профил** → **„API Management"**
2. Кликни **„Create API"** → **„System generated"**
3. Име: `BotTrader`
4. Кликни **„Edit restrictions"**:
   - **☑ Enable Futures** ← важно!
   - **☑ Enable Reading**
   - **☐ Enable Withdrawals** ← НЕ
5. Спаси → копирај Key и Secret

## 2. Премини на LIVE

```bash
python bot_trader.py --setup
```

- Кај **mode** избери **`2`** (LIVE)
- Внеси ги API key и secret

✅ Ќе почнеш да тргуваш реално.

---

# 🧠 Како работи (во 3 реда)

1. Каналот е приватен → сигналите ги сервира relay серверот на PremTradingSig
2. Ботот на секои 5 секунди проверува дали има нов сигнал
3. Ако има: праќа нарачка на твојот акаунт (со твоите пари, твојот акаунт)

**Твоите API клучеви НЕ се праќаат никаде** — остануваат само на твојот компјутер (во `config.json`).

---

# ❓ Најчести проблеми

| Проблем | Решение |
|---|---|
| „python is not recognized" (Windows) | Реинсталирај Python и штиклирај „Add to PATH" |
| „pip is not recognized" | Пробај `python -m pip install requests` |
| „No config.json found" | Прво пушти `--setup` |
| „Relay not reachable" | Провери интернет. Ако сè уште не работи, кажи на @PremTradingSig |
| „❌ ... rejected" во live | Провери API дозволи (треба Read-Write + Futures) |
| Ништо не се случува | Нормално — ботот чека сигнал. Сигналите доаѓаат ретко. |

---

# 📁 Што има во папката

| Фајл | Што е |
|---|---|
| `bot_trader.py` | Главната програма |
| `config.json` | Твоите поставки (се креира при --setup) |

Нема ништо друго да чепкаш.

---

# ⚠️ ВАЖНО

- **Прво PAPER** — барем 1-2 дена, за да видиш како работи.
- **API без Withdraw** — секогаш.
- **Leverage 10x** — не менувај (20x е опасно: SL 5% = 100% загуба).
- **Не ги споделувај API Secret** со никого.

Сè најдобро, и среќно тргување! 🚀

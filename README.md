# 🤖 BotTrader — for PremTradingSig

**Автоматски ги тргува сигналите од каналот PremTradingSig на твојот Bybit или Binance акаунт.**

Чита директно од **Telegram** — преку твојот сопствен Telegram акаунт.
Нема сервер, нема API, ништо не е изложено.

---

## 📋 Што ти треба

| Што | Како |
|---|---|
| Компјутер | Windows, macOS или Linux |
| Интернет | ✅ |
| **Telegram акаунт** | Го имаш веќе (телефон) |
| **Претплата на каналот** | Мора да си член на PremTradingSig |
| Bybit или Binance | (само за реално тргување) |

---

# 🪟 Windows — ЧЕКОР ПО ЧЕКОР

## Чекор 1: Симни Python

1. Отвори: **https://www.python.org/downloads/**
2. Кликни **„Download Python 3.12"**
3. Отвори го симнатиот фајл (двоен клик)
4. ⚠️ **ВАЖНО:** На првиот екран штиклирај:
   ```
   ☑ Add python.exe to PATH
   ```
5. Кликни **„Install Now"** и почекај
6. Кликни **„Close"**

## Чекор 2: Провери Python

1. **Start** → напиши `cmd` → ENTER
2. Напиши:

```bash
python --version
```

Треба да видиш `Python 3.12.x`

> ❌ Ако пишува „not recognized" — врати се на Чекор 1 (провери ја штиклираната опција) и рестартирај компјутер.

## Чекор 3: Симни BotTrader

1. Отвори: **https://github.com/PremTradingSig/BotTrader**
2. Зелено копче **„Code"** → **„Download ZIP"**
3. Отвори **Downloads**
4. Десен клик на ZIP → **„Extract All"** → **Extract**

## Чекор 4: Инсталирај

1. Отвори ја папката `BotTrader-main`
2. Кликни на адресната лента (каде е патеката)
3. Избриши сè, напиши `cmd`, ENTER
4. Напиши:

```bash
pip install requests telethon
```

*(почекај ~20 секунди)*

## Чекор 5: Најави се со Telegram

```bash
python bot_trader.py --login
```

Ќе те праша:
```
  Телефонски број (со +389...):
```
Напиши го **твојот број** со +389… и ENTER.

Во твојата **Telegram апликација** на телефон ќе ти дојде порака со код (не SMS).

```
  Код од Telegram: 
```
Напиши го кодот и ENTER.

✅ Ќе видиш: `✅ Најавен како: Твоe Име (@username)`

## Чекор 6: Постави го ботот

```bash
python bot_trader.py --setup
```

Притискај **ENTER** на сите прашања (прифаќа препорачани вредности):

```
  Telegram канал [@premtradsignal]:        ← ENTER
  Берза: 1) Bybit  2) Binance
  Избери (1/2) [1]:                        ← ENTER
  Коини [SOL,BNB,TRX]:                     ← ENTER
  Левериџ (10 препорачано) [10]:           ← ENTER
  Режим: 1) PAPER  2) LIVE
  Избери (1/2) [1]:                        ← ENTER (за тест)
```

## Чекор 7: Стартувај

```bash
python bot_trader.py
```

✅ Ќе видиш:

```
========================================================================
  BotTrader — BYBIT — PAPER — 10x
========================================================================
  Канал    : @premtradsignal
  Коини    : SOL, BNB, TRX
========================================================================
  👂 Слушам сигнали во @premtradsignal...
```

**Готово!** Ботот работи.

# 🍎 macOS — ЧЕКОР ПО ЧЕКОР

## Чекор 1: Провери Python

1. **⌘ + Space** → напиши `Terminal` → ENTER
2. Напиши:

```bash
python3 --version
```

> ❌ Ако „command not found" → https://www.python.org/downloads/macos/ → симни → инсталирај

## Чекор 2: Симни BotTrader

1. **https://github.com/PremTradingSig/BotTrader**
2. **„Code"** → **„Download ZIP"**
3. Отвори **Downloads** → двоен клик на ZIP

## Чекор 3: Инсталирај

```bash
cd ~/Downloads/BotTrader-main
pip3 install requests telethon
```

## Чекор 4: Најави се

```bash
python3 bot_trader.py --login
```

Внеси телефон (+389…) и код од Telegram.

## Чекор 5: Постави

```bash
python3 bot_trader.py --setup
```

ENTER на сите прашања.

## Чекор 6: Стартувај

```bash
python3 bot_trader.py
```

✅ Готово!

# 🐧 Linux — ЧЕКОР ПО ЧЕКОР

## Чекор 1: Терминал

`Ctrl + Alt + T`

## Чекор 2: Провери Python

```bash
python3 --version
```

> ❌ Ако го нема: `sudo apt update && sudo apt install -y python3 python3-pip`

## Чекор 3: Симни

```bash
cd ~
git clone https://github.com/PremTradingSig/BotTrader.git
cd BotTrader
```

> ❌ Ако нема git: `sudo apt install -y git`

## Чекор 4: Инсталирај

```bash
pip3 install requests telethon
```

## Чекор 5: Најави се

```bash
python3 bot_trader.py --login
```

## Чекор 6: Постави

```bash
python3 bot_trader.py --setup
```

## Чекор 7: Стартувај

```bash
python3 bot_trader.py
```

---

# ⚙️ КОМАНДИ (сите OS)

| Што сакаш | Windows | macOS | Linux |
|---|---|---|---|
| Најава со Telegram | `python bot_trader.py --login` | `python3 bot_trader.py --login` | `python3 bot_trader.py --login` |
| Поставки | `python bot_trader.py --setup` | `python3 bot_trader.py --setup` | `python3 bot_trader.py --setup` |
| Старт | `python bot_trader.py` | `python3 bot_trader.py` | `python3 bot_trader.py` |
| Статус | `python bot_trader.py --status` | `python3 bot_trader.py --status` | `python3 bot_trader.py --status` |
| Избриши сесија | `python bot_trader.py --logout` | `python3 bot_trader.py --logout` | `python3 bot_trader.py --logout` |
| Стоп | `Ctrl + C` | `Ctrl + C` | `Ctrl + C` |

---

# 🔑 Премин на РЕАЛНО тргување

Само откако ќе тестираш во PAPER 1-2 дена.

## 1. API клуч на твојата берза

### Bybit
1. **bybit.com** → најава → **профил** (горе десно) → **„API"**
2. **„Create New Key"** → **„System-generated API Keys"**
3. Дозволи:
   - ☑ **Read-Write** (мора)
   - ☐ **Withdraw** (НЕ стиклирај!)
4. **Submit** → внеси код од телефон
5. **Копирај** API Key + API Secret (Secret се покажува само еднаш)

### Binance
1. **binance.com** → **профил** → **„API Management"**
2. **„Create API"** → **„System generated"**
3. Име: `BotTrader` → **„Edit restrictions"**:
   - ☑ **Enable Futures** ← мора!
   - ☑ **Enable Reading**
   - ☐ **Enable Withdrawals** ← НЕ
4. Зачувај → копирај Key + Secret

## 2. Внеси ги во ботот

```bash
python3 bot_trader.py --setup
```

- Кај **Режим** избери **`2`** (LIVE)
- Внеси API key + secret

✅ Почињ тргување.

---

# 🧠 Како работи

1. Ботот се најавува **со твојот Telegram акаунт** (еднаш, се памти)
2. Слуша пораки во каналот **како обичен член** — преку Telegram, не API
3. Кога ќе дојде сигнал: праќа нарачка на **твојот** акаунт

**Твоите API клучеви остануваат само на твојот компјутер.**
**Никој не знае каде е ботот освен Telegram.**

---

# ❓ Најчести проблеми

| Проблем | Решение |
|---|---|
| „python is not recognized" | Реинсталирај Python, штиклирај „Add to PATH" |
| „pip is not recognized" | Пробај `python -m pip install requests telethon` |
| „Нема Telegram сесија" | Прво `--login` |
| „Cannot find the channel" | Провери дали си член на @premtradsignal |
| „Режим LIVE бара API клучеви" | Пушти `--setup` и избери 2, внеси клучеви |
| Ништо не се случува | Нормално — ботот чека сигнал. Сигналите доаѓаат ретко. |

---

# 📁 Што има во папката

| Фајл | Што е |
|---|---|
| `bot_trader.py` | Главната програма |
| `config.json` | Твоите поставки (креира се со `--setup`) |
| `telegram_session.session` | Најава на Telegram (креира се со `--login`) |

---

# ⚠️ ВАЖНО

- **Прво PAPER** — 1-2 дена пред реални пари.
- **API без Withdraw** — секогаш.
- **Leverage 10x** — 20x е опасно (SL 5% = цела марџа).
- **Не ширете API Secret** со никого.
- Ако сакаш да се одјавиш од ботот: `--logout` (брише сесијата).

Срекно тргување! 🚀

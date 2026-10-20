# Price Monitoring Bot Demo (Playwright + Telegram)

## Українською

Демонстраційний Python-бот для моніторингу цін, який показує типовий
pipeline price-tracking сервісу: скрейпінг динамічної сторінки,
порівняння з попереднім результатом і сповіщення в Telegram.

Бот:
- запускає headless Chromium через **Playwright** (сучасна альтернатива
  Selenium, працює через Chrome DevTools Protocol);
- відкриває тестовий сайт [books.toscrape.com](https://books.toscrape.com/)
  (офіційний сайт для тренування скрейперів із цінами й наявністю товару);
- перевіряє назву, ціну та наявність 12 товарів;
- зберігає результат у **CSV** (`output/prices.csv`), а попередній результат
  архівує окремо (`output/prices_previous.csv`);
- порівнює поточні дані з попереднім запуском і формує список змін (нова
  ціна, зміна наявності, новий товар);
- якщо зміни є — надсилає сповіщення в **Telegram** через Bot API; якщо
  токен бота не налаштовано, просто виводить те саме повідомлення в
  лог/консоль (демо-режим без токена);
- веде детальний лог кожного кроку і всіх помилок у `scraper.log`.

### Встановлення

```powershell
# створити й активувати віртуальне середовище (рекомендовано)
python -m venv venv
venv\Scripts\activate

# встановити залежності
pip install -r requirements.txt

# завантажити браузер Chromium для Playwright (один раз)
playwright install chromium
```

### Запуск

```powershell
python price_monitor.py
```

Після завершення:
- `output/prices.csv` — результат поточного запуску;
- `output/prices_previous.csv` — результат попереднього запуску (для
  порівняння при наступному старті);
- `scraper.log` — повний лог роботи.

Запустіть скрипт двічі підряд, щоб побачити різницю: перший запуск
позначить усі товари як "нові" (бо попередніх даних ще немає), другий —
покаже "змін не виявлено" (бо сторінка статична і ціни не змінились).

### Приклад результату (`output/prices.csv`)

| title | price | availability | checked_at |
|---|---|---|---|
| A Light in the Attic | £51.77 | In stock | 2026-10-20 05:22:51 UTC |
| Tipping the Velvet | £53.74 | In stock | 2026-10-20 05:22:51 UTC |
| Soumission | £50.10 | In stock | 2026-10-20 05:22:51 UTC |
| Sharp Objects | £47.82 | In stock | 2026-10-20 05:22:51 UTC |
| Sapiens: A Brief History of Humankind | £54.23 | In stock | 2026-10-20 05:22:51 UTC |
| The Requiem Red | £22.65 | In stock | 2026-10-20 05:22:51 UTC |

(повна версія — у `output/prices.csv`, 12 товарів)

### Telegram Alerts

Бот надсилає сповіщення через звичайний Telegram Bot API (`sendMessage`),
без додаткових бібліотек типу `python-telegram-bot`.

**Як підключити власного бота:**

1. Відкрийте Telegram і напишіть **@BotFather** → команда `/newbot`.
2. Дайте боту ім'я, отримайте **токен** (виглядає як `123456:ABC-DEF...`).
3. Напишіть своєму новому боту будь-яке повідомлення (щоб він "побачив" ваш чат).
4. Відкрийте в браузері:
   `https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates`
   і знайдіть у відповіді `"chat":{"id": ...}` — це ваш **chat_id**.
5. Скопіюйте `.env.example` у `.env` і заповніть:

   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=123456789
   ```

6. Запустіть `python price_monitor.py` — якщо будуть зміни, прийде
   повідомлення в Telegram. Без `.env` скрипт працює демонстраційно й
   просто показує, яке повідомлення було б відправлене.

### Структура проєкту

```
price_monitoring_bot_demo/
├── price_monitor.py      # основний скрипт
├── requirements.txt      # залежності
├── .env.example           # шаблон змінних середовища для Telegram
├── README.md
├── scraper.log            # лог останніх запусків (генерується)
└── output/
    ├── prices.csv             # поточний результат
    └── prices_previous.csv    # результат попереднього запуску
```

---

## English (simple)

A small demo Python bot for price monitoring, showing a typical
price-tracking pipeline: scraping a dynamic page, comparing it with the
previous result, and sending a Telegram notification.

The bot:
- launches a headless Chromium browser via **Playwright** (a modern
  alternative to Selenium, built on the Chrome DevTools Protocol);
- opens the test site [books.toscrape.com](https://books.toscrape.com/)
  (an official scraping-practice site with prices and stock status);
- checks the title, price and availability of 12 products;
- saves the result to **CSV** (`output/prices.csv`), and archives the
  previous result separately (`output/prices_previous.csv`);
- compares the current data with the previous run and builds a list of
  changes (price change, availability change, new product);
- if there are changes, sends a **Telegram** notification via the Bot API;
  if no bot token is configured, it simply logs/prints the same message
  instead (demo mode, no token required);
- logs every step and any errors to `scraper.log`.

### Install

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Run

```powershell
python price_monitor.py
```

Run it twice in a row to see the difference: the first run marks every
product as "new" (no previous data yet), the second shows "no changes"
(the demo site is static).

### Telegram Alerts

The bot uses the plain Telegram Bot API (`sendMessage`), no extra
libraries required.

**How to connect your own bot:**

1. In Telegram, message **@BotFather** → `/newbot`.
2. Name your bot and get a **token** (looks like `123456:ABC-DEF...`).
3. Send any message to your new bot (so it "sees" your chat).
4. Open in a browser:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   and find `"chat":{"id": ...}` in the response — that's your **chat_id**.
5. Copy `.env.example` to `.env` and fill in:

   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=123456789
   ```

6. Run `python price_monitor.py` — if there are changes, you'll get a
   Telegram message. Without `.env`, the script runs in demo mode and
   just shows what message would have been sent.

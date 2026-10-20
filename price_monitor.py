"""
Price Monitoring Bot Demo - автоматизація браузера з Playwright.

Відкриває https://books.toscrape.com/ (офіційний навчальний сайт для
скрейперів), перевіряє ціну та наявність набору товарів, порівнює з
результатом попереднього запуску і надсилає сповіщення в Telegram,
якщо щось змінилось.
"""

import csv
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://books.toscrape.com/"
PRODUCT_LIMIT = 12
NAV_TIMEOUT_MS = 15_000

OUTPUT_DIR = Path(__file__).parent / "output"
CURRENT_CSV = OUTPUT_DIR / "prices.csv"
PREVIOUS_CSV = OUTPUT_DIR / "prices_previous.csv"
LOG_PATH = Path(__file__).parent / "scraper.log"

PRODUCT_SELECTOR = "article.product_pod"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("price_monitor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stdout = sys.stdout
    if hasattr(stdout, "reconfigure"):
        try:
            stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    console_handler = logging.StreamHandler(stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


@dataclass
class Product:
    title: str
    price: str
    availability: str
    checked_at: str


def scrape_products(logger: logging.Logger) -> list[Product]:
    products: list[Product] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with sync_playwright() as pw:
        logger.info("Запуск headless Chromium через Playwright (CDP)...")
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(NAV_TIMEOUT_MS)

        try:
            logger.info("Відкриваю сторінку: %s", BASE_URL)
            page.goto(BASE_URL, wait_until="domcontentloaded")

            logger.info("Чекаю рендеринг списку товарів (%s)...", PRODUCT_SELECTOR)
            try:
                page.wait_for_selector(PRODUCT_SELECTOR, state="visible")
            except PlaywrightTimeoutError:
                logger.error("Список товарів не завантажився за %d мс.", NAV_TIMEOUT_MS)
                return products

            elements = page.query_selector_all(PRODUCT_SELECTOR)[:PRODUCT_LIMIT]
            logger.info("Знайдено %d товар(и) для перевірки (ліміт %d).", len(elements), PRODUCT_LIMIT)

            for element in elements:
                try:
                    title_el = element.query_selector("h3 a")
                    price_el = element.query_selector("p.price_color")
                    availability_el = element.query_selector("p.instock.availability")

                    title = title_el.get_attribute("title").strip() if title_el else ""
                    price = price_el.inner_text().strip() if price_el else ""
                    availability = availability_el.inner_text().strip() if availability_el else ""

                    if not title or not price:
                        logger.warning("Пропущено неповний запис (title=%r, price=%r)", title, price)
                        continue

                    products.append(Product(title=title, price=price, availability=availability, checked_at=now))
                except Exception as exc:
                    logger.error("Помилка при розборі товару: %s", exc)

        except Exception as exc:
            logger.exception("Неочікувана помилка під час перевірки цін: %s", exc)
        finally:
            browser.close()
            logger.info("Браузер закрито.")

    return products


def load_previous(logger: logging.Logger) -> dict[str, Product]:
    if not CURRENT_CSV.exists():
        logger.info("Попередніх даних не знайдено (%s) — це перший запуск.", CURRENT_CSV)
        return {}

    previous: dict[str, Product] = {}
    try:
        with open(CURRENT_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                previous[row["title"]] = Product(
                    title=row["title"],
                    price=row["price"],
                    availability=row["availability"],
                    checked_at=row["checked_at"],
                )
        logger.info("Завантажено %d запис(и) з попереднього запуску.", len(previous))
    except OSError as exc:
        logger.error("Не вдалося прочитати попередній CSV: %s", exc)

    return previous


def archive_previous(logger: logging.Logger) -> None:
    if not CURRENT_CSV.exists():
        return
    try:
        CURRENT_CSV.replace(PREVIOUS_CSV)
        logger.info("Поточний результат архівовано як %s.", PREVIOUS_CSV)
    except OSError as exc:
        logger.error("Не вдалося архівувати попередній результат: %s", exc)


def detect_changes(previous: dict[str, Product], current: list[Product], logger: logging.Logger) -> list[str]:
    changes: list[str] = []

    for product in current:
        prev = previous.get(product.title)
        if prev is None:
            changes.append(f"🆕 {product.title}: новий товар у списку ({product.price}, {product.availability})")
            continue
        if prev.price != product.price:
            changes.append(f"💰 {product.title}: ціна змінилась {prev.price} → {product.price}")
        if prev.availability != product.availability:
            changes.append(
                f"📦 {product.title}: наявність змінилась '{prev.availability}' → '{product.availability}'"
            )

    if changes:
        logger.info("Виявлено %d зміну(и) порівняно з попереднім запуском.", len(changes))
        for line in changes:
            logger.info("  %s", line)
    else:
        logger.info("Змін порівняно з попереднім запуском не виявлено.")

    return changes


def save_current(products: list[Product], logger: logging.Logger) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CURRENT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "price", "availability", "checked_at"])
            writer.writeheader()
            for p in products:
                writer.writerow(asdict(p))
        logger.info("Збережено поточний результат: %s (%d рядків)", CURRENT_CSV, len(products))
    except OSError as exc:
        logger.error("Не вдалося записати CSV-файл: %s", exc)


def send_telegram_alert(changes: list[str], logger: logging.Logger) -> None:
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    message = "📊 Price Monitor: виявлено зміни\n\n" + "\n".join(changes)

    if not bot_token or not chat_id:
        logger.info(
            "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID не задані — демонстраційний режим, "
            "повідомлення виводиться в лог замість реальної відправки:"
        )
        logger.info("---\n%s\n---", message)
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)
        response.raise_for_status()
        logger.info("Сповіщення успішно надіслано в Telegram.")
    except requests.RequestException as exc:
        logger.error("Не вдалося надіслати сповіщення в Telegram: %s", exc)


def main() -> int:
    logger = setup_logging()
    logger.info("=== Старт перевірки цін books.toscrape.com ===")

    previous = load_previous(logger)
    products = scrape_products(logger)

    if not products:
        logger.warning("Жодного товару не зібрано — перевірка завершена без результату.")
        logger.info("=== Завершено ===")
        return 1

    changes = detect_changes(previous, products, logger)

    archive_previous(logger)
    save_current(products, logger)

    if changes:
        send_telegram_alert(changes, logger)

    logger.info("=== Завершено ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

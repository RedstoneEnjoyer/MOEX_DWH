from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
from pathlib import Path

"""
Функция парсит данные по ссылке на актив MOEX в текущую минуту
и возвращает в формате словаря

Для парсинга используется javascript элемент, поэтому выбрана
библиотека playwright
"""
def fetch_and_send_json(browser, url):
    code = extract_code(url)
    try:
        # Инициализация и переход по странице
        logger.info(f"Fetching {url}")
        page = browser.new_page()
        # Ждём, если появится кнопка cookie
        page.goto(url, timeout=30000)
        # Куки
        if page.query_selector("a.btn2.btn2-primary"):
            page.click("a.btn2.btn2-primary")
            page.wait_for_timeout(1000)
        # Выбор поминутного графика
        page.click('li[data-interval="1"][data-duration="60"]')
        page.wait_for_timeout(3000)

        # Парсинг
        tooltip = page.query_selector('ul.tooltip')
        if not tooltip:
            logging.warning(f"{code}: Tooltip not found")
            page.close()
            return None

        date_text = tooltip.query_selector('.date')
        if not date_text:
            logging.warning(f"{code}: Date not found")
            page.close()
            return None

        date_info = date_text.inner_text().split(" ")
        data = {
            "code": code,
            "Date": date_info[0] if len(date_info) > 0 else None,
            "Time": date_info[1] if len(date_info) > 1 else None,
            "Open": None,
            "Max": None,
            "Min": None,
            "Close": None,
            "Volume": None
        }

        for param in ["Open", "Max", "Min", "Close"]:
            value_span = tooltip.query_selector(f'li span:has-text("{param}")')
            if value_span:
                value = value_span.inner_text().split()[-1].replace(",", ".")
                try:
                    data[param] = float(value)
                except ValueError:
                    data[param] = None

        volume_span = tooltip.query_selector('li span:has-text("Объем")')
        if volume_span:
            volume_txt = volume_span.inner_text().split(":")[-1].split("\xa0₽")[0].replace(" ", "").replace(",", ".")
            try:
                data["Volume"] = float(volume_txt)
            except ValueError:
                data["Volume"] = None

        page.close()
        return data
    except PlaywrightTimeoutError as e:
        logging.error(f"{code}: Playwright timeout: {e}")
    except Exception as e:
        logging.exception(f"{code}: Failed to fetch data.")
    return None

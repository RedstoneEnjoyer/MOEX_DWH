import asyncio
import logging

"""
Функция парсит данные по ссылке на актив MOEX в текущую минуту
и возвращает в формате словаря

Для парсинга используется javascript элемент, поэтому выбрана
библиотека playwright
"""


async def fetch_data(browser, ticker):
    url = f"https://www.moex.com/ru/issue.aspx?board=TQBR&code={ticker}"
    try:
        logging.info(f"Fetching {url}")
        page = await browser.new_page()
        await page.goto(url, timeout=30000)

        # Куки
        if await page.query_selector("a.btn2.btn2-primary"):
            await page.click("a.btn2.btn2-primary")
            await page.wait_for_timeout(1000)

        # Выбор поминутного графика
        await page.click('li[data-interval="1"][data-duration="60"]')
        await page.wait_for_timeout(3000)

        tooltip = await page.query_selector("ul.tooltip")
        if not tooltip:
            logging.warning(f"{ticker}: Tooltip not found")
            await page.close()
            return None

        date_text = await tooltip.query_selector(".date")
        if not date_text:
            logging.warning(f"{ticker}: Date not found")
            await page.close()
            return None

        date_info = (await date_text.inner_text()).split(" ")
        data = {
            "code": ticker,
            "Date": date_info[0] if len(date_info) > 0 else None,
            "Time": date_info[1] if len(date_info) > 1 else None,
            "Open": None,
            "Max": None,
            "Min": None,
            "Close": None,
            "Volume": None,
        }

        # Словарь для перевода подписей значений
        param_map = {
            "Открытие": "Open",
            "Макс.": "Max",
            "Мин.": "Min",
            "Закрытие": "Close",
        }

        for ru_param, en_param in param_map.items():
            value_span = await tooltip.query_selector(f'li span:has-text("{ru_param}")')
            if value_span:
                value = (
                    (await value_span.inner_text()).split()[-1].replace(",", ".")
                )  # ← И здесь

                try:
                    data[en_param] = float(value)
                except ValueError:
                    data[en_param] = None

        volume_span = await tooltip.query_selector('li span:has-text("Объём")')
        if volume_span:
            volume_txt = (
                (await volume_span.inner_text())
                .split(":")[-1]
                .split("\xa0₽")[0]
                .replace(" ", "")
                .replace(",", ".")
            )
            try:
                data["Volume"] = float(volume_txt)
            except ValueError:
                data["Volume"] = None

        await page.close()
        return data
    except PlaywrightTimeoutError as e:
        logging.error(f"{ticker}: Playwright timeout: {e}")
    except Exception as e:
        logging.exception(f"{ticker}: Failed to fetch data.")
    return None

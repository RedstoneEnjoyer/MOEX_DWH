import asyncio
import json
import logging
from asyncio import Semaphore
from parser import fetch_data
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

STORAGE_PATH = Path(__file__).parent.parent / "storage"

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(Path("logs") / "parser.log"), encoding='utf-8'),
        logging.StreamHandler()
    ],
)

"""
Фунция загружет полученные данные во временное хранилище (JSONL)
"""


def save_data(stock_data):
    for stock in stock_data:
        ticker = stock["code"]
        filename = STORAGE_PATH / "tmp" / f"{ticker}.jsonl"

        try:
            with open(filename, "a", encoding="utf-8") as f:  # 'a' для дописывания
                f.write(json.dumps(stock, ensure_ascii=False) + "\n")
            print(f"Данные для {ticker} успешно сохранены в {filename}")
        except Exception as e:
            print(f"Ошибка при сохранении данных для {ticker}: {str(e)}")


# await json.dump(stock, f, ensure_ascii= False, indent=4)

"""
Основная асинхронная функция для парсинга
"""


async def pull_data():
    try:
        # Чтение списка тикеров
        with open(STORAGE_PATH / "tickers.txt", "r") as file:
            tickers = [line.strip() for line in file if line.strip()]

        if not tickers:
            logging.warning("Файл с тикерами пуст или не найден")
            return []

        logging.info(f"Начало обработки {len(tickers)} тикеров")

        # Ограничиваем количество одновременных запросов
        semaphore = Semaphore(5)  # Не более 5 параллельных запросов (чтобы не забанили)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)

            async def process_ticker(ticker):
                """Обработка одного тикера с учетом семафора."""
                async with semaphore:
                    try:
                        return await fetch_data(browser, ticker)
                    except Exception as e:
                        logging.error(f"Ошибка при обработке {ticker}: {str(e)}")
                        return None

            # Создаем и запускаем задачи
            tasks = [process_ticker(ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks)

            await browser.close()

        # Фильтруем результаты
        valid_results = [r for r in results if r is not None]
        logging.info(
            f"Успешно обработано {len(valid_results)} из {len(tickers)} тикеров"
        )

        # print(valid_results)

        save_data(valid_results)
        return valid_results

    except Exception as e:
        logging.exception(f"Ошибка в pull_data(): {str(e)}")
        return []


if __name__ == "__main__":
    try:
        results = asyncio.run(pull_data())
        print(f"Успешно получено данных: {len(results)}")
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")
    except Exception as e:
        logging.exception(f"Необработанная ошибка: {str(e)}")

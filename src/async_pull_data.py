import asyncio
import logging
from pathlib import Path
from asyncio import Semaphore
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from parser import fetch_data

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("parser.log"), logging.StreamHandler()],
)


async def main():
    """Основная асинхронная функция для выполнения парсинга."""
    try:
        # Чтение списка тикеров
        data_path = Path(__file__).parent.parent / "storage" / "tickers.txt"
        with open(data_path, "r") as file:
            tickers = [line.strip() for line in file if line.strip()]

        if not tickers:
            logging.warning("Файл с тикерами пуст или не найден")
            return []

        logging.info(f"Начало обработки {len(tickers)} тикеров")

        # Ограничиваем количество одновременных запросов
        semaphore = Semaphore(5)  # Не более 5 параллельных запросов

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)

            async def process_ticker(code):
                """Обработка одного тикера с учетом семафора."""
                async with semaphore:
                    try:
                        return await fetch_data(browser, code)
                    except Exception as e:
                        logging.error(f"Ошибка при обработке {code}: {str(e)}")
                        return None

            # Создаем и запускаем задачи
            tasks = [process_ticker(code) for code in tickers]
            results = await asyncio.gather(*tasks)

            await browser.close()

        # Фильтруем результаты
        valid_results = [r for r in results if r is not None]
        logging.info(
            f"Успешно обработано {len(valid_results)} из {len(tickers)} тикеров"
        )

        print(valid_results)
        return valid_results

    except Exception as e:
        logging.exception(f"Критическая ошибка в main(): {str(e)}")
        return []


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        print(f"Успешно получено данных: {len(results)}")
    except KeyboardInterrupt:
        logging.info("Парсинг прерван пользователем")
    except Exception as e:
        logging.exception(f"Необработанная ошибка: {str(e)}")

from pathlib import Path
from clickhouse_driver import Client
import json

"""
функция создает таблицу (если ее нет) по клиенту кликхауса + тикеру 
"""
def create_table(ch, ticker):
    ch.execute(f"""
    CREATE TABLE IF NOT EXISTS market_data.{ticker}
    (
        date Date,
        time DateTime,
        open Float32,
        high Float32,
        low Float32,
        close Float32,
        volume Float64
    )
    ENGINE = MergeTree()
    ORDER BY (date, time)
    """)


def load_jsonl_to_clickhouse(file_path, table_name):
    ch = Client(
        host='localhost',
        user='default',
        password='password',
        database='market_data'
    )
    
    with open(file_path, 'r') as f:
        # Читаем и преобразуем данные
        batch = []
        for line in f:
            data = json.loads(line)
            # Преобразуем поля под структуру таблицы
            batch.append({
                'date': data['Date'],
                'time': f"{data['Date']} {data['Time']}",
                'open': data['Open'],
                'high': data['Max'],
                'low': data['Min'],
                'close': data['Close'],
                'volume': data['Volume']
            })
            
            # Вставляем батчами по 1000 записей
            if len(batch) >= 1000:
                ch.execute(f"INSERT INTO {table_name} VALUES", batch)
                batch = []
        
        # Вставляем оставшиеся записи
        if batch:
            ch.execute(f"INSERT INTO {table_name} VALUES", batch)

load_jsonl_to_clickhouse('SBER.jsonl', 'SBER')

def process_all_files():
    ch = Client(host='localhost', user='default')
    
    for jsonl_file in Path('data').glob('*.jsonl'):
        ticker = jsonl_file.stem  # SBER.jsonl -> SBER
        create_table(ch, ticker)
        load_jsonl_to_clickhouse(jsonl_file, ticker)
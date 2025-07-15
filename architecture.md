## Локальная версия

### **Архитектура без облака**
```
Parser -> Local File System (json) -> Cron / Scheduler -> 
Python ETL Script -> Local ClickHouse -> dbt -> Grafana / BI tool
```

### **Технологический стек**
- **Parser**: Python скрипт с playwright
- **Буферизация**: Локальные JSON файлы в папках
- **Планировщик**: Cron или Python APScheduler
- **ETL**: Python скрипты с pandas
- **БД**: ClickHouse в Docker контейнере
- **Трансформации**: dbt Core
- **Мониторинг**: Grafana + Prometheus

### **Структура проекта**
```

```

### **Ключевые принципы для легкой миграции**

**1. Конфигурация через переменные окружения**
```python
# Вместо хардкода путей
DATA_PATH = os.getenv('DATA_PATH', '/local/data')
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
```

**2. Абстракция storage слоя**
```python
class StorageAdapter:
    def save_data(self, data, path):
        # Локально - в файл, в облаке - в S3
        pass
    
    def load_data(self, path):
        # Универсальный интерфейс
        pass
```

**3. Модульная архитектура**
- Каждый компонент ETL в отдельном модуле
- Четкие интерфейсы между компонентами
- Dependency injection для настроек

## Поэтапная миграция в облако

### **Этап 1: Контейнеризация (0% переписывания)**
```yaml
# docker-compose.yml
version: '3.8'
services:
  parser:
    build: ./parser
    volumes:
      - ./data:/app/data
  
  clickhouse:
    image: clickhouse/clickhouse-server
    
  etl:
    build: ./etl
    depends_on:
      - clickhouse
```

### **Этап 2: Замена файловой системы на S3 (5% переписывания)**
```python
# Просто меняем StorageAdapter
class S3StorageAdapter(StorageAdapter):
    def save_data(self, data, path):
        s3_client.put_object(Bucket=bucket, Key=path, Body=data)
```

### **Этап 3: Замена Cron на EventBridge (10% переписывания)**
- ETL скрипты остаются теми же
- Только меняется способ запуска
- Добавляем Lambda wrapper вокруг существующих функций

### **Этап 4: Контейнеры в ECS/Fargate (15% переписывания)**
- Docker образы остаются теми же
- Добавляем task definitions для ECS
- Настраиваем service discovery

### **Этап 5: Managed ClickHouse (0% переписывания)**
- Меняем только connection string
- Вся логика работы с БД остается той же

## Что НЕ потребует переписывания

### **dbt проект**
- SQL модели остаются идентичными
- Только меняется connection в profiles.yml
- Миграция с dbt Core на dbt Cloud - копирование файлов

### **Бизнес-логика**
- Алгоритмы очистки данных
- Расчет технических индикаторов  
- Правила валидации
- Тесты качества данных

### **Мониторинг**
- Grafana дашборды работают с любыми источниками
- Prometheus метрики легко адаптируются
- Алерты остаются теми же

## Практические советы для MVP

### **Используйте Docker Compose**
```yaml
# Сразу приучитесь к контейнерам
services:
  clickhouse:
    image: clickhouse/clickhouse-server
    ports:
      - "8123:8123"
    volumes:
      - ./clickhouse/data:/var/lib/clickhouse
```

### **Настройте логирование**
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Roadmap разработки

### **Неделя 1-2: Базовый MVP**
- Парсер + локальные файлы
- Простой ETL скрипт
- ClickHouse в Docker

### **Неделя 3-4: Улучшения**
- dbt трансформации
- Базовый мониторинг
- Обработка ошибок

### **Неделя 5-6: Подготовка к облаку**
- Контейнеризация
- Конфигурация через env vars
- Абстракция storage

### **Неделя 7-8: Миграция**
- S3 для данных
- Lambda для ETL
- Managed ClickHouse

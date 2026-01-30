# Config (config/)

Вся доменная конфигурация. Код не содержит захардкоженных значений — всё из конфига.

## Модули

### models.py
Конфигурация LLM-моделей. Pricing (USD за 1M токенов), context window, max output. Функция `calculate_cost()` считает стоимость запроса.

Текущие модели: `gemini-3-flash`, `gemini-2.5-flash-lite` (дефолт).

### market/instruments.py
Конфигурация торговых инструментов. Сейчас один — NQ (Nasdaq 100 E-mini).

Что содержит:
- Название, биржа, tick size
- Диапазон данных (2008-01-02 — 2026-01-07)
- Торговые сессии с временами (ETH, RTH, OVERNIGHT, ASIAN, EUROPEAN и т.д.)
- Дефолтная сессия

Функции: `get_instrument()`, `get_session_times()`, `list_sessions()`, `get_trading_day_options()`.

### market/holidays.py
Праздники американского рынка. Рассчитывает: New Year's, MLK Day, Presidents' Day, Good Friday, Memorial Day, Independence Day, Labor Day, Thanksgiving, Christmas.

Функции: `get_day_type()` (regular/early_close/closed), `is_trading_day()`, `get_close_time()`.

### market/events.py
Реестр макроэкономических событий: FOMC, NFP, CPI, PPI, GDP, PCE, Retail Sales, Jobless Claims. У каждого — категория, импакт, расписание, типичное время.

## Принцип

Промпт строится из конфига:
```python
# Плохо — захардкожено
PROMPT = """Sessions: RTH (09:30-16:00), ETH..."""

# Хорошо — из конфига
config = get_instrument("NQ")
sessions = config["sessions"]
prompt = f"""Sessions: {sessions}..."""
```

Добавить новый инструмент = добавить запись в INSTRUMENTS + файл данных в data/.

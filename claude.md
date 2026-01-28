# Barb Development Guidelines

## Главный принцип

**Объясни, потом код** — Перед написанием кода объясни что и зачем делаем.

## Архитектура

```
config/           # Конфигурация
├── models.py     # LLM модели и pricing
└── market/       # Доменная конфигурация
    ├── instruments.py  # Инструменты, сессии
    ├── holidays.py     # Праздники
    └── events.py       # События

api/agent/        # Агент Barb
```

## Правило №1: Динамический контекст

Агент должен получать доменную информацию из config/, не хардкод в промптах.

```python
# Плохо — хардкод
PROMPT = """Сессии: RTH (09:30-16:00), ETH..."""

# Хорошо — из конфига
def build_prompt(instrument: str) -> str:
    config = get_instrument(instrument)
    sessions = config["sessions"]
    return f"""Сессии: {sessions}..."""
```

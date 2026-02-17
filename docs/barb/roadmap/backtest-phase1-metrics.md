# Backtest Phase 1: Metrics + AI Commentary + Commission

v1 — движок. v2 — минутное разрешение exit'ов. Оба реализованы.

Phase 1 — метрики, AI-комментарий и комиссия. Цель: Claude превращается из "повторителя цифр" в скептичного трейдинг-советника.

## Проблема

Claude после бэктеста видит **2 строки, 8 чисел**:

```
Backtest: 90 trades | Win Rate 52.2% | PF 1.48 | Total +2555.0 pts | Max DD 1675.7 pts
Avg win: +171.2 | Avg loss: -124.6 | Avg bars: 1.1 | Consec W/L: 5/6
```

Он не видит отдельные сделки, не знает что 60% прибыли — три сделки в ковид, не видит что стратегия перестала работать в 2023. Он может только сказать "PF 1.48, неплохо, max drawdown 1675 пунктов, учтите риски". Это уровень Excel.

Без комиссий. Ни одна сделка не учитывает стоимость входа/выхода — трейдер с опытом видит это сразу.

## Что делаем

### 1. Новые метрики в BacktestMetrics

Добавляем 3 поля в `barb/backtest/metrics.py`:

| Метрика | Формула | Зачем |
|---------|---------|-------|
| `recovery_factor` | total_pnl / max_drawdown | Прибыль на единицу боли. Самый интуитивный ratio для discretionary трейдера |
| `gross_profit` | сумма прибыльных сделок | Claude видит структуру P&L, не только ratio |
| `gross_loss` | сумма убыточных (отрицательное) | Вместе с gross_profit показывает откуда берётся profit factor |

Почему НЕ Sharpe/Sortino/Calmar: эти ratios требуют annualization и процентных returns. У нас P&L в пунктах инструмента. Sharpe = 1.5 на NQ (пункт = $20) и Sharpe = 1.5 на ES (пункт = $50) — разные вещи. Добавим когда будут dollar-based returns.

`gross_profit` и `gross_loss` уже вычисляются в `calculate_metrics()` (строки 65-66), просто не экспортируются. Экспозиция — тривиальная.

### 2. Расширенный model_response для Claude

Сейчас `_format_summary()` в `assistant/tools/backtest.py` принимает `BacktestMetrics`. Меняем на `BacktestResult` — получаем доступ к списку сделок.

Новый формат — **5 строк** вместо 2:

```
Backtest: 90 trades | Win Rate 52.2% | PF 1.48 | Total +2555.0 pts | Max DD 1675.7 pts
Avg win: +171.2 | Avg loss: -124.6 | Avg bars: 1.1 | Recovery: 1.52
By year: 2020 +1200.5 (25) | 2021 +408.2 (22) | 2022 -102.0 (18) | 2023 +893.1 (16) | 2024 +155.2 (9)
Exits: stop 43 (-1800.5) | take_profit 38 (+4200.0) | timeout 9 (+155.5)
Top 3 trades: +1850.0 pts (72.4% of total PnL)
```

Каждая строка — материал для конкретного вывода Claude:

| Строка | Что Claude видит | Какой вывод может сделать |
|--------|-----------------|--------------------------|
| Line 1 | Headline metrics + Recovery | Общая оценка стратегии |
| Line 2 | Avg win/loss, bars held | Соотношение risk/reward, скорость |
| Line 3 | Годовая разбивка | "Работает 2020-2022, ломается в 2023" |
| Line 4 | P&L по типу выхода | "80% прибыли от TP, стопы съедают 40%" |
| Line 5 | Концентрация в топ-3 | "72% прибыли — 3 сделки, без них PF = 0.9" |

Строки 3-5 вычисляются из `result.trades` прямо в функции. Не хранятся в BacktestMetrics — это аналитика для Claude, не персистентные метрики.

### 3. Правило #9 в промпте

Текущее правило:
```
9. Strategy testing → call run_backtest. Always include stop_loss (suggest 1-2% if user didn't specify).
   After results: comment on win rate, profit factor, and max drawdown.
   If 0 trades — explain why condition may be too restrictive.
```

"Comment on win rate, profit factor, and max drawdown" = "повтори цифры". Меняем на:

```
9. Strategy testing → call run_backtest. Always include stop_loss (suggest 1-2% if user didn't specify).
   After results — analyze strategy QUALITY, don't just repeat numbers:
   a) Yearly stability: consistent across years, or depends on one period?
   b) Exit analysis: which exit type drives profits? Are stops destroying gains?
   c) Concentration: if top 3 trades dominate total PnL — flag fragility.
   d) Trade count: below 30 trades = insufficient data, warn explicitly.
   e) Suggest one specific variation (tighter stop, trend filter, session filter).
   f) If PF > 2.0 or win rate > 70% — express skepticism, suggest stress testing.
   If 0 trades — explain why condition may be too restrictive and suggest relaxing it.
```

Это позиционирование: Barb — единственный инструмент который пытается СЛОМАТЬ твою стратегию перед тем как ты поставишь на неё деньги.

### 4. Commission

В `barb/backtest/strategy.py`:
```python
commission: float = 0.0  # points per round-trip
```

В `barb/backtest/engine.py` → `_build_trade()`:
```python
pnl -= strategy.commission
```

В `assistant/tools/backtest.py` → BACKTEST_TOOL schema:
```python
"commission": {
    "type": "number",
    "description": "Commission in points per round-trip, default 0",
}
```

1 строка в strategy, 1 строка в engine, 5 строк в tool schema. Комиссия в пунктах (те же единицы что slippage и P&L). Конвертация из долларов — ответственность пользователя/Claude. Claude может предложить значение из config инструмента.

Типичные значения:
- NQ: ~0.225 pts ($4.50 RT / $20 per point)
- ES: ~0.09 pts ($4.50 RT / $50 per point)
- CL: ~0.45 pts ($4.50 RT / $10 per point)

## Изменения в файлах

```
barb/backtest/strategy.py          — commission field (1 строка)
barb/backtest/engine.py            — commission в _build_trade (1 строка)
barb/backtest/metrics.py           — recovery_factor, gross_profit, gross_loss (~10 строк)
assistant/tools/backtest.py        — richer _format_summary + commission в schema (~40 строк)
assistant/prompt/system.py         — rewrite rule #9 (~8 строк)
tests/test_backtest.py             — ~10 новых тестов
docs/barb/backtest.md              — обновить документацию
```

## Тесты

- `test_recovery_factor` — корректное вычисление
- `test_gross_profit_loss` — экспозиция в metrics
- `test_recovery_factor_zero_trades` — edge case
- `test_recovery_factor_no_drawdown` — inf case
- `test_commission_basic` — комиссия уменьшает P&L
- `test_commission_default_zero` — backward compatible
- `test_commission_with_slippage` — оба применяются корректно
- `test_format_summary_yearly` — годовая разбивка присутствует
- `test_format_summary_exit_types` — разбивка по типам выхода
- `test_format_summary_top_trades` — метрика концентрации

## Что НЕ входит в Phase 1

| Что | Почему потом |
|-----|-------------|
| MAE/MFE per trade | Требует изменений engine — трекинг running min/max при открытой позиции |
| Sharpe/Sortino/Calmar | Нужна annualization + процентные returns, не point-based P&L |
| Frontend визуализации | Equity curve overlay, monthly table, charts — отдельная фаза |
| Monte Carlo / walk-forward | Phase 3 — валидация |
| fill_mode / slippage_atr | Phase 4 — engine improvements |

## Ожидаемый эффект

До Phase 1:
```
Claude: "Стратегия показала 90 сделок с win rate 52.2% и profit factor 1.48.
Max drawdown 1675 пунктов — учитывайте этот риск."
```

После Phase 1:
```
Claude: "90 сделок с PF 1.48, но есть нюансы. По годам: стратегия стабильно
прибыльна 2020-2023, но 2024 показывает только +155 pts на 9 сделок — возможно
edge ослабевает. 72% общей прибыли — 3 лучшие сделки, без них PF падает ниже 1.0.
Стопы съедают 1800 pts (43 сделки), а тейк-профиты приносят 4200 pts (38 сделок) —
соотношение нормальное. Попробуйте добавить фильтр по тренду — лонги только когда
цена выше SMA(200) — это может отсечь убыточные входы в нисходящем тренде."
```

Трейдер: "нихуя себе, он реально разобрался в моей стратегии."

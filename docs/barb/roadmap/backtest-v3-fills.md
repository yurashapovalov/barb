# Backtest v3: Realistic Fills

v1 — движок (engine, strategy, metrics). v2 — минутное разрешение exit'ов. Оба реализованы.

v3 — реалистичные fills. Текущий движок систематически завышает результаты. Трейдер с опытом увидит это сразу.

## Проблема

| Что сейчас | Что в реальности | Влияние |
|------------|-----------------|---------|
| Stop fill = stop_price | Stop-market заполняется по рыночной цене после trigger | Занижает убытки |
| TP fill = tp_price | Лимитка может не исполниться при касании | Завышает прибыль |
| Entry fill = open ± fixed slippage | На открытии спред шире, зависит от волатильности | Занижает entry cost |
| Slippage фиксированный | Зависит от времени, волатильности, ликвидности | Не отражает реальность |
| Комиссия = 0 | $4.50 RT на NQ, $2.50 на ES | Завышает чистую прибыль |

>90% академических стратегий не работают при реальном исполнении. Главная причина — идеализированные fills.

PF 1.48 в бэктесте может быть 1.1-1.2 в живой торговле.

## Исследование: как делают другие

### QuantConnect — Future Fill Model

Stop-market fill формула: `fill = max(stop_price, close_of_trigger_bar) + slippage`

Самый пессимистичный подход — fill по close бара где сработал стоп, не по stop_price. Rationale: на bar-level данных нельзя знать точный момент fill, поэтому worst-case. Для equities другая формула: `max(open, stop) + slippage` — учитывает overnight gap.

Источник: https://www.quantconnect.com/forum/discussion/19752/high-slippage-with-future-fill-model/

### NautilusTrader

Gap через стоп → fill по open (рыночная цена после gap). Поддерживает L2/L3 order book для точных fills на tick data.

Источник: https://nautilustrader.io/docs/nightly/concepts/backtesting/

### Backtrader

`slippage_perc` (процентный) и `slippage_fixed` (фиксированный). Stop fill по next bar open если gap. Commission presets по бирже.

Источник: https://www.backtrader.com/docu/slippage/slippage/

### VectorBT

Упрощённый: fill мгновенный как market order. С v1.2.0 tick-level resolution и slippage models. Vectorized подход — быстро, но менее реалистично для order management.

### Академический подход

**Square root market impact model**: `Impact = σ × √(Q/V)` — slippage растёт как корень от объёма ордера относительно дневного объёма. Для 1 контракта не актуально, но стандарт в институциональном трейдинге.

**Triple Barrier Method** (Marcos López de Prado, "Advances in Financial Machine Learning"): три барьера — stop loss, take profit, time exit. Наша модель уже реализует это.

**Walk-Forward Efficiency Ratio**: avg test Sharpe / avg training Sharpe. >0.5 хорошо, 0.3-0.5 приемлемо, <0.3 переоптимизация.

Источники:
- https://arxiv.org/html/2512.12924v1
- https://www.hyper-quant.tech/research/realistic-backtesting-methodology
- https://www.interactivebrokers.com/campus/ibkr-quant-news/slippage-in-model-backtesting/

## Наше преимущество

У нас есть **минутные данные**. QuantConnect вынужден брать close дневного бара для worst-case потому что у них bar-level resolution. Мы можем:

- Взять open следующей минутки после trigger — это имитация stop-market order
- Или взять worst price минутного бара — pessimistic
- Или оставить stop_price — optimistic (текущее поведение)

Это точнее любого дневного движка.

## Решения (по приоритету)

### 1. Fill mode — realistic stop fills

Самый большой эффект на честность результатов.

Сейчас в `_find_exit_in_minutes()`:
```python
if is_long and bar["low"] <= stop_price:
    return stop_price, "stop"  # ← идеализированный fill
```

v3 — три режима:

| Mode | Stop fill (long) | Stop fill (short) | Модель |
|------|-----------------|-------------------|--------|
| `optimistic` | stop_price | stop_price | Текущее поведение. Retail backtestеры |
| `realistic` | open следующей минутки | open следующей минутки | NautilusTrader подход |
| `pessimistic` | bar low | bar high | QuantConnect futures подход |

```python
# _find_exit_in_minutes — v3
for i, (_, bar) in enumerate(minutes.iterrows()):
    if stop_price is not None and is_long and bar["low"] <= stop_price:
        if fill_mode == "optimistic":
            return stop_price, "stop"
        elif fill_mode == "pessimistic":
            return bar["low"], "stop"
        else:  # realistic
            # Open следующей минутки = цена исполнения stop-market
            if i + 1 < len(minutes):
                return minutes.iloc[i + 1]["open"], "stop"
            return bar["close"], "stop"  # последняя минутка → close
```

**realistic** логика: стоп сработал на этом баре → ордер исполняется по следующей доступной цене → open следующей минутки. Это ближе всего к реальному stop-market order.

Для `_check_exit_levels()` (daily fallback без минуток):

| Mode | Stop fill (long) |
|------|-----------------|
| `optimistic` | stop_price |
| `realistic` | bar open (если gap through) или stop_price |
| `pessimistic` | bar low |

```python
# daily fallback
if is_long and bar["low"] <= stop_price:
    if fill_mode == "optimistic":
        return stop_price, "stop"
    elif fill_mode == "pessimistic":
        return bar["low"], "stop"
    else:  # realistic
        return max(stop_price, bar["open"]), "stop"  # QuantConnect equity formula
```

**TP fills** — аналогично но в обратную сторону:

| Mode | TP fill (long) |
|------|---------------|
| `optimistic` | tp_price |
| `realistic` | tp_price (лимитка исполняется по заявленной цене) |
| `pessimistic` | tp_price (лимитка не может исполниться хуже) |

TP fill не меняется — лимитный ордер гарантирует цену. Но можно добавить `tp_must_exceed` (п.3).

Default: `realistic`.

### 2. Commission

Тривиально, но необходимо для честного P&L.

```python
@dataclass
class Strategy:
    ...
    commission: float = 0.0  # points per round-trip
```

В `_build_trade()`:
```python
pnl = exit_price - entry_price  # (для long)
pnl -= strategy.commission      # вычитаем комиссию
```

Типичные значения (в пунктах инструмента):
- NQ: ~0.225 pts ($4.50 / $20 per point)
- ES: ~0.10 pts ($2.50 / $50 per point * 2 sides... упрощаем до RT)

Claude может предложить commission на основе инструмента из config.

### 3. TP must exceed

Лимитка на TP может не исполниться при точном касании. Простой параметр:

```python
@dataclass
class Strategy:
    ...
    tp_must_exceed: bool = False  # TP requires price > level, not >=
```

Текущий код: `bar["high"] >= tp_price` → `take_profit`
С `tp_must_exceed=True`: `bar["high"] > tp_price` → `take_profit`

Маленькое изменение, но честное — в реальности цена должна пройти уровень, а не просто коснуться.

### 4. ATR-based slippage

Фиксированный slippage не учитывает что NQ в 2008 (ATR 80) и NQ в 2024 (ATR 300) — разные инструменты. 0.5 пункта slippage на цене 1700 и на цене 22000 — это разный процент.

```python
@dataclass
class Strategy:
    ...
    slippage_atr: float | None = None  # slippage as fraction of ATR(14)
```

Если `slippage_atr` задан — вычисляем slippage при входе:
```python
if strategy.slippage_atr is not None:
    atr_value = evaluate("atr(close, 14)", daily.iloc[:i+1], FUNCTIONS)
    slippage = float(atr_value.iloc[-1]) * strategy.slippage_atr
else:
    slippage = strategy.slippage
```

Пример: `slippage_atr: 0.05` = 5% от ATR(14). При ATR=300 → slippage=15 pts. При ATR=80 → slippage=4 pts. Адаптивно.

## Что НЕ делаем

| Идея | Почему нет |
|------|-----------|
| Position sizing / compounding | Другой уровень сложности. 1 контракт достаточен для оценки edge |
| Multi-instrument | Отдельный проект (screener) |
| Tick-level simulation | Нет tick data. Минутки достаточно для swing strategies |
| Monte Carlo / walk-forward | Полезно, но нишевое. Усложняет UX без явной пользы для целевой аудитории |
| Trailing stop | Требует bar-by-bar state tracking. Можно добавить позже как exit type |
| Order book simulation | Нет L2 data. Square root impact model не нужен для 1 контракта |
| Variable fill rate на TP | Слишком сложно моделировать. tp_must_exceed достаточно |

## Изменения в Strategy

```python
@dataclass
class Strategy:
    entry: str
    direction: str
    exit_target: str | None = None
    stop_loss: float | str | None = None
    take_profit: float | str | None = None
    exit_bars: int | None = None
    slippage: float = 0.0
    # v3: realistic fills
    fill_mode: str = "realistic"       # "optimistic" | "realistic" | "pessimistic"
    commission: float = 0.0            # points per round-trip
    tp_must_exceed: bool = False       # TP requires price > level, not >=
    slippage_atr: float | None = None  # slippage as fraction of ATR(14), overrides slippage
```

Backward compatible — все новые поля имеют defaults, совпадающие с текущим поведением (кроме fill_mode: "realistic" vs текущий implicit "optimistic"). Это сознательное решение — новый default должен быть честнее.

## Изменения в файлах

```
barb/backtest/strategy.py   — новые поля в Strategy
barb/backtest/engine.py     — fill_mode в _find_exit_in_minutes, _check_exit_levels
                             — commission в _build_trade
                             — tp_must_exceed в проверках TP
                             — slippage_atr в _simulate (вычисление при entry)
assistant/tools/backtest.py — новые поля в BACKTEST_TOOL schema
                             — описание fill_mode в tool description
tests/test_backtest.py      — тесты для каждого fill_mode
                             — тесты для commission
                             — тесты для tp_must_exceed
```

## Порядок реализации

```
Step 1: fill_mode в engine        — самый большой эффект, ~50 строк
Step 2: commission в _build_trade  — тривиально, ~5 строк
Step 3: tp_must_exceed             — одна строка в условии, ~3 строки
Step 4: slippage_atr               — evaluate ATR при entry, ~15 строк
Step 5: BACKTEST_TOOL schema       — новые поля, описания
Step 6: тесты                      — ~20 новых тестов
Step 7: e2e прогон                 — сравнение optimistic vs realistic vs pessimistic
```

## Ожидаемый эффект

На примере стратегии "3 дня падения + верх диапазона" (90 trades, PF 1.48, +2555 pts):

| Mode | Ожидаемый PF | Почему |
|------|-------------|--------|
| optimistic (текущий) | 1.48 | Идеализированные fills |
| realistic | ~1.25-1.35 | Стопы хуже, entry дороже |
| pessimistic | ~1.05-1.15 | Worst case на каждом fill |

Если стратегия прибыльна в pessimistic режиме — она реально работает.

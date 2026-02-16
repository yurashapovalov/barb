# Backtest Integration: Phase 2 + 3

Phase 1 (движок) готов: `barb/backtest/` — Strategy, engine, metrics, 28 тестов.
Задача — подключить движок к чату, чтобы пользователь описал стратегию → получил результат.

## Как работает run_query сейчас (паттерн для копирования)

```
1. assistant/tools/__init__.py  — BARB_TOOL schema + run_query() wrapper
2. assistant/chat.py            — tools=[BARB_TOOL], dispatch в цикле tool_uses
3. assistant/prompt/system.py   — behavior rules в system prompt
4. SSE: tool_start → data_block → tool_end → done
5. Frontend: onToolStart → loading block → onDataBlock → replace with data
```

chat.py сейчас предполагает единственный tool — `run_query`. Цикл `for tu in tool_uses` не проверяет `tu["name"]`, всё идёт в run_query. Нужно: dispatch по имени для двух инструментов.

## Phase 2: Backend

### 2.1 Tool definition: `assistant/tools/backtest.py` (новый файл)

```python
BACKTEST_TOOL = {
    "name": "run_backtest",
    "description": """...""",
    "input_schema": {
        "type": "object",
        "properties": {
            "strategy": {
                "type": "object",
                "properties": {
                    "entry": {"type": "string"},
                    "direction": {"type": "string", "enum": ["long", "short"]},
                    "exit_target": {"type": "string"},
                    "stop_loss": {},          # number or string "2%"
                    "take_profit": {},         # number or string "3%"
                    "exit_bars": {"type": "integer"},
                    "slippage": {"type": "number"},
                },
                "required": ["entry", "direction"],
            },
            "session": {"type": "string", "enum": ["RTH", "ETH"]},
            "period": {"type": "string"},
            "title": {"type": "string"},
        },
        "required": ["strategy", "title"],
    },
}
```

Tool description — короткая, с примерами:
- Что такое backtest (1 предложение)
- entry: expression, same syntax as run_query map
- direction: long/short
- stop_loss/take_profit: points or "N%"
- exit_target: expression evaluated once at entry
- exit_bars: max holding period
- 2-3 примера стратегий

Wrapper function:

```python
def run_backtest_tool(input_data: dict, df_minute: pd.DataFrame, sessions: dict) -> dict:
    """Execute backtest and return structured result.

    Returns:
        model_response: compact summary for Claude
        backtest: full data for UI (metrics, trades, equity_curve, strategy)
    """
    strategy = Strategy(
        entry=input_data["strategy"]["entry"],
        direction=input_data["strategy"]["direction"],
        ...
    )
    result = run_backtest(df_minute, strategy, sessions, ...)

    # CRITICAL: convert datetime.date → ISO string for JSON serialization.
    # Trade.entry_date/exit_date are datetime.date objects from engine.
    # Both SSE (json.dumps in api/main.py) and DB (JSONB) need strings.
    trades = [
        {
            "entry_date": str(t.entry_date),
            "exit_date": str(t.exit_date),
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "direction": t.direction,
            "pnl": t.pnl,
            "exit_reason": t.exit_reason,
            "bars_held": t.bars_held,
        }
        for t in result.trades
    ]

    return {
        "model_response": _format_backtest_summary(result.metrics),
        "backtest": {
            "type": "backtest",
            "metrics": asdict(result.metrics),
            "trades": trades,
            "equity_curve": result.equity_curve,
            "strategy": asdict(strategy),
        },
    }
```

model_response — компактный summary для Claude:
```
Backtest: 53 trades | Win Rate 49.1% | PF 1.32 | Total +1087 pts | Max DD -1676 pts
Avg win: +171 | Avg loss: -125 | Avg bars: 1.1 | Consec W/L: 5/6
```

Если 0 сделок:
```
Backtest: 0 trades — entry condition never triggered in this period.
```

### 2.2 Tool dispatch: `assistant/chat.py`

Текущий код предполагает единственный tool. Изменения:

```python
# imports
from assistant.tools.backtest import BACKTEST_TOOL, run_backtest_tool

# tools list (в stream() вызове)
tools=[BARB_TOOL, BACKTEST_TOOL],

# dispatch по tu["name"] в цикле for tu in tool_uses
```

Backtest dispatch:
- Всегда `df_minute` — движок сам ресемплит в daily через `barb.interpreter.resample()`
- tool_start event: `{"tool_name": "run_backtest", "input": {...}}`
- Выполнение: `run_backtest_tool(tu["input"], self.df_minute, self.sessions)`
- data_block event: бэктест-данные с `type: "backtest"`
- tool_end event: стандартный `{"tool_name": "run_backtest", "duration_ms": ..., "error": ...}`
- model_response → tool_results для следующего раунда Claude

Error handling — тот же паттерн что и run_query:
```python
try:
    result = run_backtest_tool(...)
except Exception as exc:
    call_error = str(exc)
    model_response = f"Error: {call_error}"
```

Рефакторинг: вынести общую логику tool dispatch (tool_start/tool_end events, error handling, tool_call_log) в хелпер, чтобы не дублировать 100 строк для каждого тула.

### 2.3 Data block format

Backend отправляет через SSE event `data_block`:

```json
{
    "type": "backtest",
    "title": "RSI Mean Reversion",
    "strategy": {
        "entry": "rsi(close, 14) < 30",
        "direction": "long",
        "stop_loss": "2%",
        "take_profit": "3%",
        "exit_bars": 5
    },
    "metrics": {
        "total_trades": 53,
        "winning_trades": 26,
        "losing_trades": 27,
        "win_rate": 49.06,
        "profit_factor": 1.32,
        "avg_win": 171.16,
        "avg_loss": -124.58,
        "max_drawdown": 1675.66,
        "total_pnl": 1086.67,
        "expectancy": 20.5,
        "avg_bars_held": 1.09,
        "max_consecutive_wins": 5,
        "max_consecutive_losses": 6
    },
    "trades": [
        {
            "entry_date": "2008-01-22",
            "entry_price": 1750.5,
            "exit_date": "2008-01-22",
            "exit_price": 1803.0,
            "direction": "long",
            "pnl": 52.5,
            "exit_reason": "take_profit",
            "bars_held": 0
        }
    ],
    "equity_curve": [52.5, 17.8, ...]
}
```

Дискриминация query vs backtest: поле `type`. У query блоков `type` нет (undefined), у backtest `type === "backtest"`. Frontend проверяет: `"type" in block && block.type === "backtest"`.

### 2.4 Хранение в DB

Бэктест-блоки хранятся в том же массиве `message.data` (JSONB[]) рядом с query блоками. Тип определяется по полю `type`. Не нужна миграция — JSONB принимает любую структуру. При загрузке из DB frontend различает по `type`.

Даты в trades уже строки (ISO format) — сериализация без проблем. SSE: `json.dumps(data, default=str)` в api/main.py тоже обработает. `_build_messages` в chat.py работает: `tool_name: "run_backtest"` сохраняется в tool_calls, input сериализуется как JSON. `_compact_output` возвращает "done" для всех tool calls — backtest не исключение.

### 2.5 System prompt: `assistant/prompt/system.py`

Добавить правило в `<behavior>`:
```
9. Strategy testing → call run_backtest. Always include stop_loss (suggest 1-2% if user didn't specify). Suggest slippage for realistic results. After results: comment on win rate, profit factor, and drawdown. If 0 trades — explain why the condition may be too restrictive.
```

## Phase 3: Frontend

### 3.1 Types: `front/src/types/index.ts`

Добавить BacktestBlock interface. Использовать discriminated union с DataBlock:

```typescript
export interface BacktestMetrics {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    profit_factor: number;
    avg_win: number;
    avg_loss: number;
    max_drawdown: number;
    total_pnl: number;
    expectancy: number;
    avg_bars_held: number;
    max_consecutive_wins: number;
    max_consecutive_losses: number;
}

export interface BacktestTrade {
    entry_date: string;
    entry_price: number;
    exit_date: string;
    exit_price: number;
    direction: "long" | "short";
    pnl: number;
    exit_reason: string;
    bars_held: number;
}

export interface BacktestBlock {
    type: "backtest";
    title: string;
    strategy: Record<string, unknown>;
    metrics: BacktestMetrics;
    trades: BacktestTrade[];
    equity_curve: number[];
    status?: "loading" | "success" | "error";
    error?: string;
}

// Union type for all block kinds
export type AnyBlock = DataBlock | BacktestBlock;

// Type guard
export function isBacktestBlock(block: AnyBlock): block is BacktestBlock {
    return "type" in block && block.type === "backtest";
}
```

Обновить ссылки на DataBlock → AnyBlock:
- `Message.data: AnyBlock[] | null`
- `SSEDoneEvent.data: AnyBlock[]`
- `ChatPanelProps.selectedData: AnyBlock | null`
- `parseContent` → `ContentSegment.block: AnyBlock`

### 3.2 Backtest Card: `front/src/components/ai/backtest-card.tsx` (новый файл)

В сообщении — компактная карточка с ключевыми метриками:

```
┌──────────────────────────────────────┐
│ ▶ RSI Mean Reversion                 │
│   53 trades · 49.1% WR · PF 1.32    │
│   +1087 pts · DD -1676               │
└──────────────────────────────────────┘
```

Loading state: spinner + "Backtesting...". Error state: red icon + error message.
Клик → `onSelectData(block)` — тот же callback что и DataCard.

### 3.3 Backtest Panel: `front/src/components/panels/backtest-panel.tsx` (новый файл)

Правая панель с тремя секциями:

**1. Metrics Grid** — 2x6 grid:
```
Trades       53          Win Rate    49.1%
Winners      26          Losers      27
Profit Factor 1.32       Expectancy  +20.5
Total P&L    +1087       Max DD      -1676
Avg Win      +171        Avg Loss    -125
Avg Bars     1.1         Consec W/L  5/6
```

**2. Equity Curve** — area chart (Recharts, уже есть через shadcn):
- X: trade number (1, 2, 3, ...)
- Y: cumulative P&L
- Зелёная область выше 0, красная ниже 0

**3. Trades Table** — reuse Table/TableHeader/TableBody из data-panel:
| Entry | Exit | Dir | Entry Price | Exit Price | P&L | Reason | Bars |

### 3.4 Message rendering: `front/src/components/panels/chat-panel.tsx`

Сейчас (line 56-61): `parseContent(msg)` → `seg.type === "data"` → `<DataCard>`.
Нужно: проверить тип блока и рендерить BacktestCard или DataCard:

```tsx
seg.type === "data" ? (
    isBacktestBlock(seg.block)
        ? <BacktestCard data={seg.block} ... />
        : <DataCard data={seg.block} ... />
) : ...
```

Также обновить `parseContent` в `front/src/lib/parse-content.ts` — тип `ContentSegment.block` меняется на `AnyBlock`.

### 3.5 Panel routing: `front/src/pages/chat/chat-page.tsx`

Сейчас (line 43): `<DataPanel data={selectedData} onClose={onCloseData} />`.
Нужно: если `isBacktestBlock(selectedData)` → `<BacktestPanel>`, иначе `<DataPanel>`.

```tsx
{selectedData && (
    <>
        <ResizeHandle ... />
        <div ...>
            {isBacktestBlock(selectedData)
                ? <BacktestPanel data={selectedData} onClose={onCloseData} />
                : <DataPanel data={selectedData} onClose={onCloseData} />
            }
        </div>
    </>
)}
```

### 3.6 Loading state: `front/src/hooks/use-chat.ts`

Тот же паттерн что и query:
1. `onToolStart` → создаёт loading block. Для backtest tool: `{ type: "backtest", status: "loading" } as BacktestBlock`
2. `onDataBlock` → заменяет loading block на реальные данные + `status: "success"`
3. `onToolEnd` с ошибкой → `status: "error"`, `error: event.error`

Нужно: в `onToolStart` проверять `event.tool_name` чтобы создать правильный loading block:
```typescript
onToolStart(event) {
    const loadingBlock = event.tool_name === "run_backtest"
        ? { type: "backtest" as const, status: "loading" as const, ... }
        : { query: {}, result: null, status: "loading" as const, ... };
}
```

## Порядок реализации

```
Step 1: assistant/tools/backtest.py     — tool schema + wrapper + date serialization
Step 2: assistant/chat.py              — refactor dispatch + add backtest branch
Step 3: assistant/prompt/system.py     — behavior rule #9
Step 4: тест через Python              — вызвать run_backtest_tool() напрямую
Step 5: front/src/types/index.ts       — BacktestBlock, AnyBlock, isBacktestBlock
Step 6: front/src/components/ai/backtest-card.tsx — card component
Step 7: front/src/components/panels/backtest-panel.tsx — panel component
Step 8: front/src/components/panels/chat-panel.tsx — conditional rendering
Step 9: front/src/pages/chat/chat-page.tsx — panel routing
Step 10: front/src/hooks/use-chat.ts    — loading block by tool name
Step 11: front/src/lib/parse-content.ts — AnyBlock type
```

Steps 1-4 = Phase 2 (backend). Steps 5-11 = Phase 3 (frontend).

## Файлы

### Новые
- `assistant/tools/backtest.py` — tool definition + wrapper

- `front/src/components/ai/backtest-card.tsx` — card in message
- `front/src/components/panels/backtest-panel.tsx` — right panel

### Изменяемые
- `assistant/chat.py` — import + tools list + dispatch refactor
- `assistant/prompt/system.py` — behavior rule #9

- `front/src/types/index.ts` — BacktestBlock, AnyBlock union, isBacktestBlock guard
- `front/src/lib/parse-content.ts` — AnyBlock type in ContentSegment
- `front/src/components/panels/chat-panel.tsx` — BacktestCard vs DataCard rendering
- `front/src/pages/chat/chat-page.tsx` — BacktestPanel vs DataPanel routing
- `front/src/hooks/use-chat.ts` — loading block by tool_name

### Не меняются
- `barb/backtest/*` — движок готов, Phase 1 done
- `api/main.py` — SSE streaming generic, `json.dumps(data, default=str)` обработает
- `front/src/lib/api.ts` — SSE parsing generic, data_block event тот же

## Верификация

1. `.venv/bin/pytest tests/` — все тесты проходят
2. Python: `run_backtest_tool({"strategy": {"entry": "rsi(close,14)<30", "direction": "long", "stop_loss": "2%"}, "title": "Test"}, df, sessions)` → проверить model_response строка, backtest dict с ISO date строками, metrics числа
3. JSON roundtrip: `json.dumps(result["backtest"])` не падает (нет datetime.date)
4. API: `curl -X POST /api/chat/stream` → SSE events: tool_start, data_block (type=backtest), tool_end
5. Browser: отправить "протестируй RSI < 30 long" → backtest card в чате → клик → panel с метриками + equity curve + trades table
6. Reload: backtest card рендерится из DB (message.data содержит блок с type=backtest)
7. History: начать новый разговор → tool_calls из предыдущего корректно восстанавливаются в _build_messages

# Understand Tool

## Problem

The LLM silently substitutes a different question when it can't answer what the user asked. User gets wrong data without knowing it. The model doesn't know the engine's limitations because they're not in its context.

Adding capabilities/limitations to the system prompt would bloat it. Every new feature = more lines in the prompt.

## Solution

New tool `understand_question` that the model calls before executing queries.

```
User question
    |
    v
Model calls understand_question(question="...")
    |
    v
Tool returns: capabilities, limitations, guidance
    |
    v
Model explains what it understood and what it will compute
(or honestly says it can't and offers alternatives)
    |
    v
User confirms or corrects
    |
    v
Model calls execute_query → data + commentary
```

## Why a tool

- **Prompt stays small** — one line ("call understand_question first") instead of 20-line capabilities section
- **Scalable** — new features/limitations = update tool response, not prompt
- **Loggable** — tool calls are already traced in e2e tests
- **Same architecture** — fits existing tool-calling loop, no new phases or endpoints

## How it works

### Tool declaration

```python
UNDERSTAND_QUESTION_DECLARATION = {
    "name": "understand_question",
    "description": (
        "Analyze a user question before executing queries. "
        "Returns engine capabilities and limitations. "
        "Call this before execute_query to understand what is possible."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user's question to analyze",
            },
        },
        "required": ["question"],
    },
}
```

### Tool response

Returns a static context about what the engine can and cannot do:

```python
def _understand_question(args: dict) -> str:
    return json.dumps({
        "capabilities": {
            "single_timeframe": "1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly",
            "sessions": "RTH, ETH, OVERNIGHT, ASIAN, EUROPEAN, MORNING, AFTERNOON",
            "computed_columns": "arithmetic, comparisons, if(), lag (prev/next), rolling windows, cumulative, patterns",
            "filtering": "boolean expressions on any column",
            "grouping": "by any column (weekday, month, year, etc.)",
            "aggregation": "mean, sum, count, min, max, std, median, percentile, correlation, last",
            "time_functions": "dayofweek, dayname, hour, month, monthname, year, quarter, date",
        },
        "limitations": [
            "Cross-timeframe queries not supported (e.g. comparing daily values with weekly aggregates in one query)",
            "No subqueries or nested queries",
            "No JOINs or multiple data sources",
            "No loops or arbitrary code",
            "Single pipeline: session → period → timeframe → map → where → group_by → select → sort → limit",
        ],
        "instructions": (
            "Explain to the user what you understood and what you will compute. "
            "If the question requires unsupported capabilities, say so honestly "
            "and suggest 1-2 closest alternatives. "
            "Never silently substitute a different question."
        ),
    })
```

### Prompt change

One line added to `<instructions>`:

```
1. On the first analytical question, call get_query_reference to learn the query format.
2. Call understand_question with the user's question to check capabilities.
3. Explain to the user what you understood and what you will compute. Wait for confirmation.
...
```

Remove the 4-line `<constraints>` block about honest refusal — that's now in the tool response.

### Flow examples

**Normal question:**
```
User: "Какой средний дневной диапазон NQ?"

Model → calls understand_question(question="Какой средний дневной диапазон NQ?")
Tool → {capabilities: {...}, limitations: [...], instructions: "..."}
Model → "Посчитаю средний диапазон (high - low) по всем RTH данным."
User → "Ок"
Model → calls execute_query → data + commentary
```

**Unsupported question:**
```
User: "Распредели дни недели по частоте хай лоу недели"

Model → calls understand_question(question="...")
Tool → {capabilities: {...}, limitations: ["Cross-timeframe queries not supported..."], ...}
Model → "Этот вопрос требует сравнения дневных данных с недельными —
         кросс-таймфрейм join, который пока не поддерживается. Могу:
         - Количество дней где high > prev(high) по дням недели
         - Средний диапазон по дням недели
         Какой вариант?"
User → "Первый"
Model → calls execute_query → data + commentary
```

**Knowledge question:**
```
User: "What is NR7?"

Model → calls understand_question(question="What is NR7?")
Tool → {capabilities: {...}, ...}
Model → "NR7 — day with the narrowest range of the last 7..."
(no execute_query needed)
```

## Implementation

### Files

| File | Action | What |
|------|--------|------|
| `assistant/tools.py` | MODIFY | Add `understand_question` declaration + handler |
| `assistant/prompt.py` | MODIFY | Add instruction to call understand_question first, remove honesty constraint |
| `scripts/e2e.py` | MODIFY | Update checks to expect understand_question calls |
| `tests/test_tools.py` | MODIFY | Add tests for new tool |

Files unchanged: `assistant/chat.py`, `api/main.py`, `barb/interpreter.py`

### Changes detail

**`assistant/tools.py`:**
- Add `UNDERSTAND_QUESTION_DECLARATION` to `TOOL_DECLARATIONS`
- Add `_understand_question()` handler in `run_tool()`
- Capabilities/limitations as structured JSON

**`assistant/prompt.py`:**
- Instruction 2: "Call understand_question with the user's question to check capabilities before executing."
- Instruction 3: "Explain what you understood and what you will compute. Wait for the user to confirm."
- Remove from constraints: the 4-line honesty block (now in tool response)

**`scripts/e2e.py`:**
- Add `understand_question` to `expect_tools` for analytical scenarios
- Add scenario for honest refusal (cross-timeframe question)

**`tests/test_tools.py`:**
- Test understand_question returns capabilities and limitations
- Test it's in TOOL_DECLARATIONS

## Verification

```
python -m pytest tests/
python scripts/e2e.py --scenario 7
```

Scenario 7 (weekday high/low) should show:
1. Model calls understand_question
2. Model explains it can't do cross-timeframe join
3. Model suggests alternatives

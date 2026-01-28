"""Prompts for Barb trading analyst agent."""

from config.market import get_instrument, list_sessions, get_session_times


def build_system_prompt(instrument: str) -> str:
    """Build system prompt with domain context."""
    config = get_instrument(instrument)
    if not config:
        return f"Unknown instrument: {instrument}"

    # Format sessions
    sessions = []
    for name in list_sessions(instrument):
        times = get_session_times(instrument, name)
        if times:
            sessions.append(f"  {name}: {times[0]}-{times[1]}")
    sessions_text = "\n".join(sessions)

    return f"""<role>
You are Barb, a trading data analyst. You write Polars code to answer questions about market data.
</role>

<instrument>
Name: {config['name']}
Symbol: {instrument}
Exchange: {config['exchange']}
Timezone: {config['data_timezone']}
Tick size: {config['tick_size']}
</instrument>

<data>
Variable `df` is a Polars LazyFrame with 1-minute bars.

Columns:
- instrument: str (symbol)
- timestamp: datetime
- open, high, low, close: float (prices)
- volume: int

Sessions ({config['data_timezone']}):
{sessions_text}
</data>

<rules>
1. Use Polars API (not pandas)
2. Data is in `df` as LazyFrame
3. Assign result to variable `result`
4. Call `.collect()` at the end
</rules>

<example>
Question: What was the highest price last week?

```python
import polars as pl
from datetime import datetime, timedelta

last_week = datetime.now() - timedelta(days=7)
result = (
    df
    .filter(pl.col("timestamp") > last_week)
    .select(pl.col("high").max())
    .collect()
)
```
</example>"""


def build_code_prompt(question: str) -> str:
    """Build prompt for code generation."""
    return f"""<task>
Write Polars code to answer this question.
Assign the result to `result` variable.
Return only code in ```python``` block.
</task>

<question>
{question}
</question>"""


def build_explanation_prompt(question: str, code: str, data: str) -> str:
    """Build prompt for explaining results."""
    return f"""<context>
Question: {question}

Code executed:
```python
{code}
```

Result:
{data}
</context>

<task>
Explain the results concisely in Russian. Use specific numbers from the data.
</task>"""

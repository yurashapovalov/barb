"""Single Barb Script tool for Anthropic Claude."""

from assistant.tools.reference import build_function_reference
from barb.interpreter import execute
from barb.ops import BarbError

_EXPRESSIONS_MD = build_function_reference()

# Anthropic tool definition
BARB_TOOL = {
    "name": "run_query",
    "description": f"""Execute a Barb Script query against market data.

Query is a flat JSON object with these fields (all optional):
- session: trading session name (RTH, ETH). Omit for settlement data. Use with any timeframe including daily.
- from: "1m", "5m", "15m", "30m", "1h", "daily", "weekly" — timeframe (default: "1m")
- period: "2024", "2024-03", "2024-01:2024-06", "2023:", "last_year", "last_50" — date filter. last_N = last N trading days.
- map: {{"col_name": "expression"}} — compute derived columns
- where: "expression" — filter rows (boolean expression)
- group_by: "column" or ["col1", "col2"] — group rows (must be column name, not expression)
- select: "mean(col)" or ["sum(x)", "count()"] — aggregate functions
- sort: "column desc" or "column asc" — sort results (use column NAME from map, not expression)
- limit: number — max rows to return

Execution order is FIXED: session → period → from → map → where → group_by → select → sort → limit

IMPORTANT:
- group_by requires a COLUMN NAME, not an expression. Create column in map first.
- select with group_by supports: count(), sum(col), mean(col), min(col), max(col), std(col), median(col), pct(condition).
- select without group_by: any expression including last(col), percentile(col, p), correlation(col1, col2).
- pct(condition) returns fraction (0.0-1.0): pct(gap_pct() > 0) → 0.58.
- hour() and minute() return 0 on daily/weekly/monthly data (no time component). Use intraday timeframe (1m, 5m, 1h) for time-of-day analysis.

Multi-step queries — use "steps" instead of flat fields when filtering must happen before computation:
  {{"steps": [
    {{"from": "daily", "map": {{"rsi": "rsi(close,14)"}}, "where": "rsi < 30"}},
    {{"map": {{"ret": "change_pct(close,5)"}}, "select": "mean(ret)"}}
  ]}}
Step 1 sets scope (session/period/from) + map/where/group_by/select. Steps 2+: map/where/group_by/select on previous output.
Last step also has sort/limit. "columns" goes at query level (outside steps).
Each step's group_by output becomes the input for the next step — use this for nested aggregation:
  count per (date, hour) → then count per hour = "how many sessions per hour" (not bars).
Don't use steps for simple queries — flat fields work fine.

Output format:
- Use "columns" to control which columns appear in the result table. Order in array = order in output.
- Available: date, time (intraday only), open, high, low, close, volume, + any key from map.
- Always include date (and time for intraday). Only include OHLCV when relevant.
- Order: date/time first, then answer columns (from map), then supporting context (close, volume).
- Omit columns for scalar/grouped results (they manage their own output).
- Name map columns in user's language, short and clear.

<patterns>
Common multi-function patterns:
  MACD cross      → crossover(macd(close,12,26), macd_signal(close,12,26,9))
  breakout up     → close > rolling_max(high, 20)
  breakdown       → close < rolling_min(low, 20)
  NFP days        → dayofweek() == 4 and day_of_month() <= 7
  OPEX            → 3rd Friday: dayofweek() == 4 and day_of_month() >= 15 and day_of_month() <= 21
  opening range   → first 30-60 min of RTH session
  closing range   → last 60 min of RTH session
  when session high set → where: high == session_high(), group_by: date, select: max(hr) → then group_by: max_hr, select: count()
  move from session low → session_close() - session_low()
  find days matching criteria (intraday) → filter minute bars with where, then group_by date to get one row per day
</patterns>

<examples>
Example 1 — filter (date + close for context):
User: Show me days when the market dropped 2.5%+ in 2024
→ run_query(query={{"from":"daily","period":"2024",
  "map":{{"chg":"change_pct(close,1)"}}, "where":"chg <= -2.5",
  "columns":["date","close","chg"]}},
  title="Days down >2.5%")

Example 2 — indicator (date + indicator only):
User: When was the market oversold?
→ run_query(query={{"from":"daily",
  "map":{{"rsi":"rsi(close,14)"}}, "where":"rsi < 30",
  "columns":["date","rsi"]}},
  title="Oversold days")

Example 3 — raw data (OHLCV when relevant):
User: Show me last week's data
→ run_query(query={{"from":"daily","period":"last_week",
  "map":{{"chg":"change_pct(close,1)"}},
  "columns":["date","open","high","low","close","volume","chg"]}},
  title="Last week")

Example 4 — helper column hidden:
User: Golden cross dates in 2024?
→ run_query(query={{"from":"daily","period":"2024",
  "map":{{"sma50":"sma(close,50)","sma200":"sma(close,200)",
  "cross":"crossover(sma(close,50),sma(close,200))"}},
  "where":"cross",
  "columns":["date","close","sma50","sma200"]}},
  title="Golden crosses")

Example 5 — group_by (no columns needed):
User: Average range by day of week for 2024?
→ run_query(query={{"from":"daily","period":"2024",
  "map":{{"r":"range()","dow":"dayofweek()"}}, "group_by":"dow", "select":"mean(r)"}},
  title="Range by day")

Example 6 — steps (one hour per session, not all bars that touched the high):
User: At what hour does the session high typically occur?
→ run_query(query={{"steps":[
  {{"session":"ETH","from":"1m","period":"last_50",
    "map":{{"hr":"hour()","is_high":"high == session_high()"}},"where":"is_high"}},
  {{"map":{{"dt":"date()"}},"group_by":"dt","select":"max(hr)"}},
  {{"group_by":"max_hr","select":"count()","sort":"count desc"}}
  ]}},
  title="Session high by hour")

Example 7 — steps (breakdown of filtered data):
User: RSI below 40 — which months?
→ run_query(query={{"steps":[
  {{"from":"daily","period":"2024","map":{{"rsi":"rsi(close,14)"}},"where":"rsi < 40"}},
  {{"map":{{"mo":"month()"}},"group_by":"mo","select":"count()"}}
  ]}},
  title="Oversold by month")

Example 8 — time range spanning two hours:
User: On which days did the session low occur between 9:45 and 10:15?
→ run_query(query={{"session":"ETH","from":"1m","period":"last_50",
  "map":{{"hr":"hour()","min":"minute()","is_low":"low == session_low()",
  "time_ok":"(hr == 9 and min >= 45) or (hr == 10 and min <= 15)"}},
  "where":"is_low and time_ok",
  "columns":["date","time"]}},
  title="Session low 9:45-10:15")

Example 9 — bucketing into 10-minute intervals:
User: Group session highs/lows by 10-minute intervals
→ run_query(query={{"steps":[
  {{"session":"ETH","from":"1m","period":"last_22",
    "map":{{"hr":"hour()","min":"minute()","is_high":"high == session_high()","is_low":"low == session_low()"}},
    "where":"is_high or is_low"}},
  {{"map":{{"dt":"date()","type":"if(is_high, 'high', 'low')","interval":"hr * 100 + (min // 10) * 10"}},
    "group_by":["dt","interval","type"],"select":"count()"}},
  {{"group_by":["interval","type"],"select":"count()","sort":"count desc"}}
  ]}},
  title="High/low by 10-min interval")

Example 10 — find specific days from intraday data (filter → group by date):
User: Which days in 2024 had price within 1% of the weekly open during the first hour?
→ run_query(query={{"steps":[
  {{"session":"ETH","from":"1m","period":"2024",
    "map":{{"wk_open":"valuewhen(dayofweek() == 6 and hour() == 18, open, 0)",
    "diff_pct":"abs(close - wk_open) / wk_open * 100","hr":"hour()"}},
    "where":"hr < 19 and diff_pct <= 1"}},
  {{"map":{{"dt":"date()"}},"group_by":"dt","select":["count()","min(diff_pct)"],"sort":"min_diff_pct asc"}}
  ]}},
  title="Days near weekly open, first hour")
</examples>

<data-protocol>
Tool results are SUMMARIES — you don't see the full table:
- Table: row count, column stats (min/max/mean), first/last row only.
- Scalar: the computed value.
- Grouped: group count, min/max group row. All groups shown to user in UI.
The user sees the complete table directly. If you need dates, values, or breakdowns — run another query.
Never hardcode values you haven't received (e.g. date() in [...] with guessed dates).
</data-protocol>

<commentary-examples>
How to comment on results — cite ONLY what's in the summary:

<example>
Summary: "Result: 27 groups by hr  min: hr=(7, 'high'), count=1  max: hr=(9, 'high'), count=8"
Good: "9am leads with 8 session highs, 7am had just 1."
Bad: "Lows are scattered throughout the day" — both min/max show type='high', you can't see lows distribution from this summary.
</example>

<example>
Summary: "Result: 44 rows  first: date=2024-01-29  last: date=2024-11-15"
Good: "44 instances between January and November 2024."
Bad: "This occurred on Jan 29, Feb 3, Feb 10..." — you only see first and last row, not the ones in between.
</example>

<example>
Summary: "Result: 0 rows"
Good: "No session highs occurred in that time window."
Bad: Any fabricated dates, counts, or values.
</example>

<example>
Summary: "Result: 21 (from 252 rows)"
Good: "21 trading days out of 252."
</example>

<example>
Summary: "Result: 27 groups by hr  max: hr=18, count=7"
Good: "Час 18 лидирует с 7 минимумами сессии."
Bad: "В 18:00 зафиксировано 7 минимумов" — hr=18 is the whole hour (18:00-18:59), not a specific minute.
</example>
</commentary-examples>

<query-rules>
- Percentage questions → use pct(condition) in select. One query, not two.
- Without period → ALL data. Don't add a default period. Keep period from conversation context.
- Without session → settlement data. With session (RTH/ETH) → session-specific. Works on any timeframe.
- User asks "which days/dates" from intraday data → use steps: filter in step 1, group_by date in step 2. One query, not two.
</query-rules>

{_EXPRESSIONS_MD}
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "description": "Barb Script query object",
                "properties": {
                    "session": {"type": "string"},
                    "from": {"type": "string"},
                    "period": {"type": "string"},
                    "map": {"type": "object"},
                    "where": {"type": "string"},
                    "group_by": {},
                    "select": {},
                    "sort": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1},
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to show in result. Order matters.",
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "session": {"type": "string"},
                                "from": {"type": "string"},
                                "period": {"type": "string"},
                                "map": {"type": "object"},
                                "where": {"type": "string"},
                                "group_by": {},
                                "select": {},
                                "sort": {"type": "string"},
                                "limit": {"type": "integer", "minimum": 1},
                            },
                        },
                        "description": "Multi-step query. Use instead of flat fields.",
                    },
                },
            },
            "title": {
                "type": "string",
                "description": "Short descriptive title for this data (shown to user)",
            },
        },
        "required": ["query", "title"],
    },
}


def run_query(query: dict, df, sessions: dict) -> dict:
    """Execute Barb Script query and return structured result.

    Returns dict with:
        - model_response: str - compact summary for model
        - table: list | None - full data for UI
        - source_rows: list | None - evidence for aggregations
        - chart: dict | None - chart hints (category, value columns)
    """
    try:
        result = execute(query, df, sessions)
        summary = result.get("summary", {})

        return {
            "model_response": _format_summary_for_model(summary),
            "table": result.get("table"),
            "source_rows": result.get("source_rows"),
            "source_row_count": result.get("source_row_count"),
            "chart": result.get("chart"),
        }

    except BarbError as e:
        return {"model_response": f"Error: {e}", "table": None, "source_rows": None, "chart": None}
    except Exception as e:
        msg = f"Error: {type(e).__name__}: {e}"
        return {"model_response": msg, "table": None, "source_rows": None, "chart": None}


def _format_summary_for_model(summary: dict) -> str:
    """Format summary into compact string for model."""
    stype = summary.get("type", "unknown")

    if stype == "scalar":
        value = summary.get("value")
        rows_scanned = summary.get("rows_scanned")
        if rows_scanned:
            return f"Result: {value} (from {rows_scanned} rows)"
        return f"Result: {value}"

    if stype == "dict":
        values = summary.get("values", {})
        parts = [f"{k}={v}" for k, v in values.items()]
        return f"Result: {', '.join(parts)}"

    if stype == "table":
        lines = [f"Result: {summary.get('rows', 0)} rows"]

        # Stats
        if summary.get("stats"):
            for col, st in summary["stats"].items():
                if st.get("min") is not None:
                    mean_str = f", mean={st['mean']:.2f}" if st.get("mean") is not None else ""
                    lines.append(f"  {col}: min={st['min']}, max={st['max']}{mean_str}")

        # First/last
        if summary.get("first"):
            first_str = ", ".join(f"{k}={v}" for k, v in summary["first"].items())
            lines.append(f"  first: {first_str}")
        if summary.get("last"):
            last_str = ", ".join(f"{k}={v}" for k, v in summary["last"].items())
            lines.append(f"  last: {last_str}")

        return "\n".join(lines)

    if stype == "grouped":
        lines = [f"Result: {summary.get('rows', 0)} groups by {summary.get('by', '?')}"]

        # Min/max rows
        if summary.get("min_row"):
            min_parts = ", ".join(f"{k}={v}" for k, v in summary["min_row"].items())
            lines.append(f"  min: {min_parts}")
        if summary.get("max_row"):
            max_parts = ", ".join(f"{k}={v}" for k, v in summary["max_row"].items())
            lines.append(f"  max: {max_parts}")

        return "\n".join(lines)

    return f"Result: {summary}"

# Barb

Conversational trading analytics. User asks a question about the market in any language → Claude generates a Barb Script JSON query → engine executes it against historical data (parquet) → user gets answer with charts and tables.

## Project structure

```
barb/
  interpreter.py    — 9-step query pipeline (CORE, change carefully)
  expressions.py    — AST expression parser (CORE, change carefully)
  functions.py      — ~41 functions, will grow to 107 (changes most often)
  data.py           — parquet data loading (lru_cache — loads once per instrument)
  validation.py     — input validation

assistant/
  chat.py           — LLM chat loop, SSE streaming, prompt caching (MODEL hardcoded here)
  context.py        — sliding window + summarization for long conversations
  prompt.py         — system prompt builder from instrument config (97 lines, will be refactored)
  tools/
    __init__.py     — run_query tool definition + result formatting
    reference/
      expressions.md — expression syntax docs (embedded in tool description)

config/
  models.py         — config data models
  market/
    instruments.py  — instrument configs (NQ, etc.)
    holidays.py     — holiday calendar
    events.py       — market events

api/
  main.py           — FastAPI app, endpoints, SSE streaming
  auth.py           — Supabase JWT validation
  config.py         — settings from .env (pydantic-settings)
  db.py             — Supabase client (service role)
  errors.py         — structured error responses
  request_id.py     — request ID middleware + logging filter
front/          — React/TypeScript UI (Vercel)
scripts/        — data download, maintenance
tests/          — pytest (mirrors barb/ structure)
docs/barb/      — architecture documentation
supabase/       — database migrations, RLS policies
```

## How it works

1. User sends a question (any language)
2. `assistant/prompt.py` builds system prompt from `config/market/instruments.py`
3. `assistant/chat.py` sends to Claude (Sonnet 4.5) with prompt caching, streams SSE events
4. Claude generates a run_query tool call with a JSON query
5. `assistant/tools/__init__.py` executes the tool, `reference/expressions.md` is embedded in tool description
6. `barb/data.py` loads parquet data
7. `barb/interpreter.py` executes 9-step pipeline: session → period → from → map → where → group_by → select → sort → limit
8. `barb/expressions.py` parses expressions, `barb/functions.py` provides functions
9. Result streams back: summary for model + table/chart for UI
10. If model needs more data, it calls run_query again (up to 5 rounds)

## Commands

```bash
# Dev
docker compose up              # backend + hot reload
cd front && npm run dev        # frontend

# Test
pytest                         # all tests
pytest tests/test_interpreter.py -v  # specific
ruff check .                   # lint

# Deploy (automated via GitHub Actions on push to main)
# Manual: ssh to Hetzner → git pull → docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

## Documentation

**`docs/`** — describes the current system as-is. May be slightly outdated but useful for understanding existing code:
overview, api, query-engine, assistant, config, frontend, infrastructure, charts, result-format, column-ordering.

**`docs/barb/`** — target architecture for refactoring. This is where we're heading:
- `functions-architecture.md` — 107 functions, TradingView matching, SIGNATURES pattern, test strategy
- `prompt-architecture.md` — 6-layer prompt system, auto-generation from code, annotations
- `backtest.md` — strategy engine, entry/exit logic, metrics
- `screener-compare.md` — multi-instrument screening, compare, daily cache

**When refactoring:** follow `docs/barb/`. When understanding existing code: check `docs/`.

If a task touches barb/functions.py → read docs/barb/functions-architecture.md first.
If a task touches assistant/prompt.py → read docs/barb/prompt-architecture.md first.
If unsure → read the relevant doc. It's faster than guessing wrong.

## How to work

**Think before coding.** Before writing code, explain your approach. What files will change? What's the plan? If the plan is wrong, better to catch it before 200 lines of code.

**Challenge my decisions.** If I ask you to do something that contradicts architecture docs, existing patterns, or common sense — say so. Explain why. Don't just do what I say. You are a staff engineer, not a code monkey.

**Understand context first.** Before changing a file, read it. Before changing a function, find where it's called. Before adding a feature, check if something similar exists. `grep -r` is your friend.

**One thing at a time.** Don't refactor + add features + fix bugs in one pass. Separate concerns. Small commits that do one thing. If you notice something unrelated that needs fixing — note it, don't fix it. Finish the current task first.

**Don't break what works.** Run tests after changes. If tests fail, fix before moving on. If there are no tests for what you changed — write them.

## Tests

Test file mirrors source: `barb/functions/oscillators.py` → `tests/test_oscillators.py`. New functions must have tests. Indicator functions must have TradingView match tests — compare output against real values from TradingView on known data.

```bash
pytest tests/test_functions.py::test_rsi -v    # run single test
pytest tests/ -k "rsi" -v                      # run by keyword
```

## Git

Commit after each logical change, not at the end. Message format: `add rsi function with wilder smoothing` — lowercase, no prefix, says what was done. Don't bundle unrelated changes in one commit.

## Code Philosophy

Write boring code. The goal is not to impress — it's to be understood.

**Obviousness** — Read the code, immediately understand what it does. No mental stack of 5 abstraction layers.

**Deletability** — Any piece can be ripped out and replaced without breaking the rest. Minimal coupling between parts.

**No speculative code** — Don't write what "might be needed". YAGNI. When it's needed — we'll write it then.

**Explicit over implicit** — No magic. If something happens, it's visible in the code, not hidden in a base class.

**Small modules** — Each file does one thing. Open — understand — close.

## What We Don't Do

- AbstractExpressionVisitorFactory
- Plugin registries
- Middleware pipelines
- Dependency injection
- Premature abstractions: three similar lines are better than a premature helper
- Feature flags or backwards-compatibility shims
- Docstrings on obvious functions
- Comments that repeat what the code says

## What We Do

- Functions with clear names that say what they do
- Plain dicts and dataclasses, not class hierarchies
- Tests as documentation — a test shows what the function does better than any comment
- Comments only when WHY is not obvious from the code
- Type hints on public interfaces
- Early returns over nested ifs

## Comments

```python
# Bad — repeats the code
x = price * quantity  # multiply price by quantity

# Bad — obvious function doesn't need a docstring
def get_session(name: str) -> tuple:
    """Get session by name."""  # we can see that
    return sessions[name]

# Good — explains WHY
# Wrap-around sessions (18:00-09:30) span midnight.
# Filter: time >= start OR time < end (not AND).
if start > end:
    mask = (df.index.time >= start) | (df.index.time < end)

# Good — domain knowledge that's not obvious from code
# Wilder's smoothing is equivalent to EMA with period 2n-1
ema_period = 2 * n - 1
```

## Code Quality Checklist

Every commit must pass these checks. No exceptions, no "fix later".

**Validation** — Validate all inputs at system boundaries. Guard edge cases (empty DataFrame, missing keys, unknown enum values). Don't trust external data — LLM responses, user input, API payloads.

**Logging** — Always lazy formatting: `log.info("msg: %s", val)`, never `log.info(f"msg: {val}")`. F-strings evaluate even when the log level is disabled.

**Error handling** — Wrap external calls (LLM API, file I/O) in try/except. Return meaningful errors with context (what failed, which step, what expression). Never swallow exceptions silently.

**Infrastructure** — Dockerfile must copy all source packages. Dependencies in pyproject.toml must match actual imports. CI must run lint + tests before deploy. Verify the build works before pushing.

**Types** — Use correct type hints (`Callable` from collections.abc, not `callable`). Type API response models with Pydantic. Scope test fixtures appropriately (session-scoped for static data).

**No dead code** — No unreachable branches, no unused imports, no stale fields. If it's not executed, delete it.

## Key principle: TradingView matching

Every indicator must match TradingView exactly. RSI(14) on NQ in Barb must equal RSI(14) on NQ in TradingView. Divergence > 0.1 on 100+ bars = bug. This is non-negotiable. See functions-architecture.md for details on Wilder's smoothing, Bollinger ddof=0, and other gotchas.

## Rule: Dynamic Context

The agent gets domain information from config/, not hardcoded in prompts.

```python
# Bad — hardcoded
PROMPT = """Sessions: RTH (09:30-16:00), ETH..."""

# Good — from config
def build_prompt(instrument: str) -> str:
    config = get_instrument(instrument)
    sessions = config["sessions"]
    return f"""Sessions: {sessions}..."""
```
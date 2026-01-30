# Barb Development Guidelines

## Architecture

Документация по архитектуре проекта: [docs/architecture/](docs/architecture/)

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

# Code Review Fixes

Staff-level review, 2026-01-29. Organized by priority.

## P0 — Broken

### 1. Dockerfile missing `barb/` and `assistant/`

**File:** `Dockerfile`
**Problem:** Only copies `config/`, `api/`, `scripts/`. Missing `barb/` and `assistant/` — container can't import core modules.
Also: `pip install .` runs before source code is copied (only pyproject.toml present).

**Fix:** Restructure Dockerfile:
```dockerfile
COPY pyproject.toml .
RUN pip install --no-cache-dir --only-deps .
COPY . .
```
Or explicit COPY for each package directory after deps install.

### 2. `pandas` missing from dependencies, phantom deps present

**File:** `pyproject.toml`
**Problem:** `polars` listed but unused (everything is pandas). `pandas` not listed but used everywhere. `supabase` kept — needed for next phase (frontend/chat logging).

**Fix:** Remove `polars`. Add `pandas>=2.0.0`. Keep `supabase`.

### 3. `_filter_period` crashes on invalid strings

**File:** `barb/interpreter.py:185-206`
**Problem:** `df.loc[period]` throws `KeyError` on invalid period strings like `"all"`, `"everything"`, `"last_3_months"`. Error becomes unhelpful `"Internal error: 'all'"`.

**Fix:** Validate period format with regex before `.loc[]`. Valid formats:
- Year: `"2024"` (4 digits)
- Month: `"2024-03"` (YYYY-MM)
- Range: `"2024-01-01:2024-06-30"` (already handled)
- Relative: `"last_year"`, `"last_month"`, `"last_week"` (already handled)

Anything else → `QueryError` with valid formats list.

### 4. `response.text` crashes when no candidates

**File:** `assistant/chat.py:100`
**Problem:** If Gemini returns empty candidates (rate limit, safety filter, blocked), `response.text` throws `ValueError`. The tool loop `break`s and falls through.

**Fix:** Check `response.candidates` before accessing `.text`. Return empty answer with warning if no candidates.

### 5. Duplicate `import re` in interpreter

**File:** `barb/interpreter.py:7` and `:347`
**Problem:** `re` imported at module level and again inside `_aggregate_col_name()`.

**Fix:** Remove local import at line 347.

---

## P1 — Design

### 6. Assistant created per request

**File:** `api/main.py:78-83`
**Problem:** Every HTTP request creates a new `genai.Client`. Wasteful — client is stateless and reusable.

**Fix:** Cache `Assistant` per instrument at module level or use FastAPI dependency injection with `lru_cache`.

### 7. Cost calculation uses hardcoded model

**File:** `assistant/chat.py:104-108`
**Problem:** `calculate_cost(model=DEFAULT_MODEL)` ignores `self.model_config`. If model changes, cost is wrong.

**Fix:** Use `self.model_config` name or id for cost calculation.

### 8. `_sort` silently ignores unknown columns

**File:** `barb/interpreter.py:362-364`
**Problem:** Every other pipeline step raises `QueryError` for invalid columns. `_sort` returns unsorted data without error.

**Fix:** Raise `QueryError` with available columns, same pattern as group_by/select.

### 9. `"join"` in valid fields but unimplemented

**File:** `barb/interpreter.py:40`
**Problem:** Query passes validation but join does nothing. Silent wrong results.

**Fix:** Remove `"join"` from `_VALID_FIELDS`. Re-add when implemented.

### 10. Production runs with `--reload` and `ENV=development`

**File:** `docker-compose.yml`
**Problem:** CI/CD uses `docker compose up -d --build` with development settings.

**Fix:** Add `docker-compose.prod.yml` override:
```yaml
services:
  api:
    environment:
      - ENV=production
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```
Deploy: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

---

## P2 — Code Quality

### 11. Reverse alias dict rebuilt per AST node

**File:** `barb/expressions.py:155`
**Problem:** `reverse_aliases = {v: k for k, v in _KEYWORD_ALIASES.items()}` inside `_eval_node()` — called recursively for every node in expression.

**Fix:** Module-level constant `_REVERSE_ALIASES`.

### 12. `sessions` fixture duplicates instrument config

**File:** `tests/conftest.py:21-33`
**Problem:** Session times hardcoded in fixture. Drifts if `instruments.py` changes.

**Fix:** `return get_instrument("NQ")["sessions"]`

### 13. `_eval_aggregate` limited to single-arg functions

**File:** `barb/interpreter.py:316`
**Problem:** Regex `(\w+)\((\w+)\)` doesn't match `percentile(col, 0.5)` in group_by context.

**Fix:** Either extend regex to handle multi-arg, or document limitation in query reference and understand_question response.

### 14. Untyped API response models

**File:** `api/main.py:54-55`
**Problem:** `data: list` and `cost: dict` — no schema for API consumers.

**Fix:** Define `CostResponse` and `DataBlock` Pydantic models.

### 15. Wildcard import

**File:** `config/__init__.py:9`
**Problem:** `from config.market import *`

**Fix:** Explicit imports or remove the re-export entirely (consumers already import from submodules).

### 16. Dead code in `config/market/`

~200 lines of unused functions across `instruments.py`, `holidays.py`, `events.py`. Built for future features.

**Fix:** Keep for now — these are config/calendar utilities we'll need when events integration lands. No action.

### 17. `asyncio_mode` warning

**File:** `pyproject.toml:34`
**Problem:** `asyncio_mode = "auto"` with no async tests. Warning on every pytest run.

**Fix:** Remove the line.

### 18. Unused `data_dir` config field

**File:** `api/config.py:9`
**Problem:** `data_dir: str = "/app/data"` — never read by any code.

**Fix:** Remove field.

---

## Execution Order

1. **P0 first:** Dockerfile + deps + period validation + response safety + dupe import
2. **P1 second:** Assistant caching, cost model, sort validation, remove join, prod compose
3. **P2 last:** Cleanup pass

Each group = one commit.

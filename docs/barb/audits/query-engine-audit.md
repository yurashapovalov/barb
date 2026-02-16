# Audit: query-engine.md

**Date**: 2026-02-16
**Claims checked**: 62
**Correct**: 62 | **Wrong**: 0 | **Outdated**: 0 | **Unverifiable**: 0

## Issues

No issues found. All claims match the current codebase.

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Query is a flat JSON, each field is a pipeline step | CORRECT | `barb/interpreter.py`:60-71 — `_VALID_FIELDS` defines the flat set of allowed fields |
| 2 | Execution order is fixed: session -> period -> from -> map -> where -> group_by -> select -> sort -> limit | CORRECT | `barb/interpreter.py`:112-162 — steps executed in this exact order |
| 3 | Step 1: session filters by trading session (RTH, ETH) | CORRECT | `barb/interpreter.py`:113-120 — `filter_session()` |
| 4 | Step 2: period filters by date range (YYYY, YYYY-MM, YYYY-MM-DD, start:end, last_year, last_month, last_week) | CORRECT | `barb/interpreter.py`:241-294 — `_RELATIVE_PERIODS`, `_PERIOD_RE`, `filter_period()` |
| 5 | Step 3: from resamples timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly) | CORRECT | `barb/interpreter.py`:17-30 — `TIMEFRAMES` contains all 12 values |
| 6 | Step 4: map computes derived columns {"name": "expression"} | CORRECT | `barb/interpreter.py`:317-337 — `compute_map()` |
| 7 | Step 5: where filters rows by condition expression | CORRECT | `barb/interpreter.py`:340-359 — `filter_where()` |
| 8 | Step 6: group_by groups by column from map | CORRECT | `barb/interpreter.py`:362-387 — `_group_aggregate()` |
| 9 | Step 7: select aggregates ("count()", "mean(col)", ["sum(x)", "max(y)"]) | CORRECT | `barb/interpreter.py`:390-418 — `_aggregate()` handles string, list |
| 10 | Step 8: sort by "column desc" or "column asc" | CORRECT | `barb/interpreter.py`:471-490 — `sort_df()` |
| 11 | Step 9: limit restricts row count | CORRECT | `barb/interpreter.py`:161-162 — `result_df.head(query["limit"])` |
| 12 | Result contains summary, table, source_rows, source_row_count, metadata, query, chart | CORRECT | `barb/interpreter.py`:641-649, 658-665, 676-683 — all three response branches |
| 13 | `execute(query, df, sessions)` is the function signature | CORRECT | `barb/interpreter.py`:90 — `def execute(query: dict, df: pd.DataFrame, sessions: dict) -> dict:` |
| 14 | summary type "table": {type, rows, columns, stats:{col:{min,max,mean}}, first:{date,..}, last:{date,..}} | CORRECT | `barb/interpreter.py`:695-729 — `_build_summary_for_table()` builds exactly this structure |
| 15 | summary type "grouped": table + {by, min_row, max_row} | CORRECT | `barb/interpreter.py`:701-703, 732-740 — adds `by`, `min_row`, `max_row` for grouped |
| 16 | summary type "scalar": {type: "scalar", value, rows_scanned} | CORRECT | `barb/interpreter.py`:671-674 |
| 17 | summary type "dict": {type: "dict", values, rows_scanned} | CORRECT | `barb/interpreter.py`:653-656 |
| 18 | metadata contains rows, session, from, warnings | CORRECT | `barb/interpreter.py`:590-595 |
| 19 | chart contains {category, value}, only for grouped DataFrame results | CORRECT | `barb/interpreter.py`:631-639 — chart set only when `is_grouped`, contains `category` and `value` |
| 20 | chart key absent in scalar/dict responses | CORRECT | `barb/interpreter.py`:658-665, 676-683 — no `chart` key in those dicts |
| 21 | table is JSON-serialized rows for UI (or None for scalars/dict) | CORRECT | `barb/interpreter.py`:618, 660, 678 |
| 22 | source_rows are pre-aggregation rows (for transparency) | CORRECT | `barb/interpreter.py`:605-613 — only populated when `has_aggregation` |
| 23 | Validates unknown fields | CORRECT | `barb/interpreter.py`:184-190 — checks `set(query.keys()) - _VALID_FIELDS` |
| 24 | Validates invalid timeframes | CORRECT | `barb/interpreter.py`:192-198 |
| 25 | Validates invalid limit | CORRECT | `barb/interpreter.py`:200-205 |
| 26 | Validates incorrect map (must be dict) | CORRECT | `barb/interpreter.py`:207-213 |
| 27 | validation.py does pre-validation without DataFrame, pure AST analysis | CORRECT | `barb/validation.py`:1-6 docstring, no DataFrame required |
| 28 | validation.py checks syntax of all expressions (map, where, select) | CORRECT | `barb/validation.py`:48-71 — checks map, where, select |
| 29 | validation.py checks unknown functions | CORRECT | `barb/validation.py`:135 — `func_name not in _KNOWN_FUNCTIONS` |
| 30 | validation.py checks unsupported operators and method calls (a.upper() forbidden) | CORRECT | `barb/validation.py`:144-149 — rejects non-Name function calls (methods) |
| 31 | validation.py checks = instead of == (common LLM mistake) | CORRECT | `barb/validation.py`:30, 105-112 — `_LONE_EQUALS_RE` |
| 32 | validation.py checks functions in group_by (LLM mistake) | CORRECT | `barb/validation.py`:74-96 — detects `(` in group_by |
| 33 | validation.py checks aggregate format in group_by context (must be func(col) or count()) | CORRECT | `barb/validation.py`:221-248 — `_check_group_select()` |
| 34 | ValidationError(errors: list[dict]) collects all errors at once | CORRECT | `barb/validation.py`:20-26 — `__init__(self, errors: list[dict])` |
| 35 | expressions.py is safe — no eval/exec, builds AST via ast.parse() | CORRECT | `barb/expressions.py`:102 — `ast.parse(parsed_expr, mode="eval")`, no eval/exec anywhere |
| 36 | expressions.py evaluates recursively on DataFrame | CORRECT | `barb/expressions.py`:109 — `_eval_node` is recursive |
| 37 | Supports arithmetic: +, -, *, / | CORRECT | `barb/expressions.py`:67-72 — `_BINARY_OPS`: Add, Sub, Mult, Div |
| 38 | Supports comparisons: >, <, >=, <=, ==, != | CORRECT | `barb/expressions.py`:74-81 — `_COMPARE_OPS`: Gt, Lt, GtE, LtE, Eq, NotEq |
| 39 | Supports boolean logic: and, or, not | CORRECT | `barb/expressions.py`:181-193 (And, Or), 139-144 (Not via UnaryOp) |
| 40 | Supports membership: in [1, 2, 3], not in [4, 5] | CORRECT | `barb/expressions.py`:153-167 — ast.In, ast.NotIn |
| 41 | Supports functions: prev(), rolling_mean(), dayofweek() etc | CORRECT | `barb/expressions.py`:196-218 — ast.Call handling |
| 42 | Auto-converts dates: date() >= '2024-03-15' | CORRECT | `barb/expressions.py`:16-46 — `_is_date_series`, `_parse_date_string`, `_coerce_for_date_comparison` |
| 43 | functions/ is a package with 12 modules | CORRECT | 12 public modules: core, lag, window, cumulative, pattern, aggregate, time, convenience, oscillators, volatility, trend, volume |
| 44 | 106 functions total | CORRECT | 6+2+12+3+8+10+10+19+8+14+9+5 = 106 |
| 45 | Each module exports *_FUNCTIONS, *_SIGNATURES, *_DESCRIPTIONS | CORRECT | All 12 modules export these three dicts |
| 46 | __init__.py combines into FUNCTIONS, SIGNATURES, DESCRIPTIONS | CORRECT | `barb/functions/__init__.py`:53-96 |
| 47 | core (6): abs, log, sqrt, sign, round, if | CORRECT | `barb/functions/core.py`:14-21 — CORE_FUNCTIONS has these 6 |
| 48 | lag (2): prev, next | CORRECT | `barb/functions/lag.py`:3-6 — LAG_FUNCTIONS has these 2 |
| 49 | window (12): sma, ema, wma, hma, rma, vwma, rolling_mean, rolling_sum, rolling_max, rolling_min, rolling_std, rolling_count | CORRECT | `barb/functions/window.py`:52-65 — WINDOW_FUNCTIONS has these 12 |
| 50 | cumulative (3): cumsum, cummax, cummin | CORRECT | `barb/functions/cumulative.py`:3-7 — CUMULATIVE_FUNCTIONS has these 3 |
| 51 | pattern (8): streak, bars_since, rank, rising, falling, valuewhen, pivothigh, pivotlow | CORRECT | `barb/functions/pattern.py`:99-108 — PATTERN_FUNCTIONS has these 8 |
| 52 | aggregate (10): mean, sum, count, max, min, std, median, percentile, correlation, last | CORRECT | `barb/functions/aggregate.py`:5-16 — AGGREGATE_FUNCTIONS has these 10 |
| 53 | time (10): dayofweek, dayname, hour, minute, month, year, date, monthname, day, quarter | CORRECT | `barb/functions/time.py`:5-16 — TIME_FUNCTIONS has these 10 |
| 54 | convenience (19): change, change_pct, gap, gap_pct, range, range_pct, body, body_pct, upper_wick, lower_wick, midpoint, typical_price, green, red, doji, inside_bar, outside_bar, crossover, crossunder | CORRECT | `barb/functions/convenience.py`:100-123 — CONVENIENCE_FUNCTIONS has these 19 |
| 55 | oscillators (8): rsi, stoch_k, stoch_d, cci, williams_r, mfi, momentum, roc | CORRECT | `barb/functions/oscillators.py`:85-94 — OSCILLATOR_FUNCTIONS has these 8 |
| 56 | volatility (14): tr, atr, natr, bbands_upper, bbands_middle, bbands_lower, bbands_width, bbands_pctb, donchian_upper, donchian_lower, kc_upper, kc_middle, kc_lower, kc_width | CORRECT | `barb/functions/volatility.py`:114-129 — VOLATILITY_FUNCTIONS has these 14 |
| 57 | trend (9): macd, macd_signal, macd_hist, adx, plus_di, minus_di, sar, supertrend, supertrend_dir | CORRECT | `barb/functions/trend.py`:219-229 — TREND_FUNCTIONS has these 9 |
| 58 | volume (5): obv, ad_line, vwap_day, volume_sma, volume_ratio | CORRECT | `barb/functions/volume.py`:53-59 — VOLUME_FUNCTIONS has these 5 |
| 59 | data.py: load_data(instrument, timeframe="1d", asset_type="futures") | CORRECT | `barb/data.py`:12 — exact signature match |
| 60 | data.py: two datasets data/1d/futures/{symbol}.parquet and data/1m/futures/{symbol}.parquet | CORRECT | `barb/data.py`:20 — path built from timeframe/asset_type/symbol |
| 61 | data.py: cached via @lru_cache | CORRECT | `barb/data.py`:11 — `@lru_cache` decorator |
| 62 | data.py: returns DataFrame with DatetimeIndex and columns [open, high, low, close, volume] | CORRECT | `barb/data.py`:26-27 — sets index from timestamp, selects OHLCV columns |

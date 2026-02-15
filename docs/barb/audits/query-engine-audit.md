# Audit: docs/barb/query-engine.md

**Auditor:** Independent code audit (Claude Opus 4.6)
**Date:** 2026-02-15
**Document:** `docs/barb/query-engine.md` (105 lines)
**Sources verified:** `barb/interpreter.py`, `barb/validation.py`, `barb/expressions.py`, `barb/functions/__init__.py`, `barb/functions/*.py` (all 12 modules), `barb/data.py`

---

## Section: Pipeline (lines 9-23)

| # | Claim | Verdict | Notes |
|---|-------|---------|-------|
| 1 | 9-step pipeline: session, period, from, map, where, group_by, select, sort, limit | ACCURATE | interpreter.py lines 112-162, exact order matches |
| 2 | Fixed execution order regardless of JSON key order | ACCURATE | interpreter.py processes steps sequentially by name, not by dict iteration |
| 3 | Timeframes: 1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly | ACCURATE | TIMEFRAMES set, interpreter.py lines 17-30 |
| 4 | Period formats: YYYY, YYYY-MM, YYYY-MM-DD, start:end, last_year, last_month, last_week | ACCURATE | filter_period() lines 241-294, _PERIOD_RE and _RELATIVE_PERIODS match |
| 5 | Map: `{"name": "expression"}` | ACCURATE | compute_map() line 317-337 |
| 6 | Where: expression filter | ACCURATE | filter_where() line 340-359 |
| 7 | Group_by: by column from map | ACCURATE | _group_aggregate() line 362-387 |
| 8 | Select: `"count()"`, `"mean(col)"`, `["sum(x)", "max(y)"]` | ACCURATE | _normalize_select() line 172-176, _aggregate() line 390-418 |
| 9 | Sort: `"column desc"` or `"column asc"` | ACCURATE | sort_df() line 471-490, default ascending |
| 10 | Limit: row count | ACCURATE | interpreter.py line 161-162, df.head(limit) |

---

## Section: interpreter.py (lines 27-43)

| # | Claim | Verdict | Notes |
|---|-------|---------|-------|
| 11 | `execute(query, df, sessions)` signature | ACCURATE | line 90 |
| 12 | Returns dict with: summary, table, source_rows, source_row_count, metadata, query, chart | ACCURATE | _build_response() lines 641-683. Note: chart key is only present for DataFrame results, absent for scalar/dict as documented |
| 13 | `table` is JSON-serialized rows or None for scalars/dict | ACCURATE | DataFrame: line 618 (serialized records), dict/scalar: lines 661/678 (None) |
| 14 | `source_rows` for transparency | ACCURATE | lines 604-613, only populated when has_aggregation=True |
| 15 | `source_row_count` | ACCURATE | lines 606, 611 |
| 16 | `metadata` contains rows, session, from, warnings | ACCURATE | lines 590-595, exact four keys |
| 17 | `chart` = `{category, value}` only for grouped DataFrame; absent for scalar/dict | ACCURATE | lines 631-639 (grouped chart), lines 658-665/676-683 (no chart key for dict/scalar) |
| 18 | Summary type "table": `{type, rows, columns, stats:{col:{min,max,mean}}, first:{date,..}, last:{date,..}}` | ACCURATE | _build_summary_for_table() lines 695-729 |
| 19 | Summary type "grouped": table fields + `{by, min_row, max_row}` | ACCURATE | lines 701-703, 732-740 |
| 20 | Summary type "scalar": `{type: "scalar", value, rows_scanned}` | ACCURATE | lines 671-675 |
| 21 | Summary type "dict": `{type: "dict", values, rows_scanned}` | ACCURATE | lines 653-657 |
| 22 | Validates: unknown fields, invalid timeframes, invalid limit, invalid map | ACCURATE | _validate() lines 182-212, all four checks present |

---

## Section: validation.py (lines 45-54)

| # | Claim | Verdict | Notes |
|---|-------|---------|-------|
| 23 | Pre-validation without DataFrame, pure AST analysis | ACCURATE | No df parameter in validate_expressions() |
| 24 | Checks syntax of all expressions (map, where, select) | ACCURATE | lines 47-71 check map, where, select |
| 25 | Unknown functions check | ACCURATE | _walk_ast() lines 131-143 |
| 26 | Unsupported operators and method calls (`a.upper()` forbidden) | ACCURATE | Operators: lines 154-174; methods: lines 144-149 |
| 27 | `=` vs `==` detection | ACCURATE | _LONE_EQUALS_RE line 30, check at lines 104-112 |
| 28 | Functions in group_by detection | ACCURATE | lines 73-96 |
| 29 | Aggregate format validation in group_by context | ACCURATE | _check_group_select() lines 221-248 |
| 30 | Collects all errors at once: `ValidationError(errors: list[dict])` | ACCURATE | ValidationError class lines 20-26, errors list at line 45 |

---

## Section: expressions.py (lines 56-63)

| # | Claim | Verdict | Notes |
|---|-------|---------|-------|
| 31 | Safe parser -- no eval/exec, builds AST via ast.parse(), recursive evaluation | ACCURATE | evaluate() line 84-106, _eval_node() recursive |
| 32 | Arithmetic: +, -, *, / | ACCURATE | _BINARY_OPS lines 67-72: Add, Sub, Mult, Div |
| 33 | Comparisons: >, <, >=, <=, ==, != | ACCURATE | _COMPARE_OPS lines 74-81: Gt, Lt, GtE, LtE, Eq, NotEq |
| 34 | Boolean logic: and, or, not | ACCURATE | BoolOp handling lines 181-193, UnaryOp Not lines 139-145 |
| 35 | Membership: `in [1,2,3]`, `not in [4,5]` | ACCURATE | ast.In lines 153-161, ast.NotIn lines 162-167 |
| 36 | Function calls: `prev()`, `rolling_mean()`, `dayofweek()`, etc. | ACCURATE | Call handling lines 196-218 |
| 37 | Auto date conversion: `date() >= '2024-03-15'` | ACCURATE | _coerce_for_date_comparison() lines 36-46, called at line 174 |

---

## Section: functions/ package (lines 65-80)

| # | Claim | Verdict | Notes |
|---|-------|---------|-------|
| 38 | 106 functions in 12 modules | ACCURATE | Counted: 6+2+12+3+8+10+10+19+8+14+9+5 = 106. Modules: core, lag, window, cumulative, pattern, aggregate, time, convenience, oscillators, volatility, trend, volume = 12 (excluding `_smoothing.py` internal helper and `__init__.py`) |
| 39 | Each module exports `*_FUNCTIONS`, `*_SIGNATURES`, `*_DESCRIPTIONS` | ACCURATE | Verified in all 12 modules |
| 40 | `__init__.py` combines into `FUNCTIONS`, `SIGNATURES`, `DESCRIPTIONS` | ACCURATE | lines 53-96, plus `AGGREGATE_FUNCS` at line 98 |
| 41 | **core** (6): abs, log, sqrt, sign, round, if | ACCURATE | core.py CORE_FUNCTIONS has exactly these 6 |
| 42 | **lag** (2): prev, next | ACCURATE | lag.py LAG_FUNCTIONS has exactly these 2 |
| 43 | **window** (12): sma, ema, wma, hma, rma, vwma, rolling_mean, rolling_sum, rolling_max, rolling_min, rolling_std, rolling_count | ACCURATE | window.py WINDOW_FUNCTIONS has exactly these 12 |
| 44 | **cumulative** (3): cumsum, cummax, cummin | ACCURATE | cumulative.py has exactly these 3 |
| 45 | **pattern** (8): streak, bars_since, rank, rising, falling, valuewhen, pivothigh, pivotlow | ACCURATE | pattern.py PATTERN_FUNCTIONS has exactly these 8 |
| 46 | **aggregate** (10): mean, sum, count, max, min, std, median, percentile, correlation, last | ACCURATE | aggregate.py AGGREGATE_FUNCTIONS has exactly these 10 |
| 47 | **time** (10): dayofweek, dayname, hour, minute, month, year, date, monthname, day, quarter | ACCURATE | time.py TIME_FUNCTIONS has exactly these 10 |
| 48 | **convenience** (19): change, change_pct, gap, gap_pct, range, range_pct, body, body_pct, upper_wick, lower_wick, midpoint, typical_price, green, red, doji, inside_bar, outside_bar, crossover, crossunder | ACCURATE | convenience.py CONVENIENCE_FUNCTIONS has exactly these 19 |
| 49 | **oscillators** (8): rsi, stoch_k, stoch_d, cci, williams_r, mfi, momentum, roc | ACCURATE | oscillators.py OSCILLATOR_FUNCTIONS has exactly these 8 |
| 50 | **volatility** (14): tr, atr, natr, bbands_upper, bbands_middle, bbands_lower, bbands_width, bbands_pctb, donchian_upper, donchian_lower, kc_upper, kc_middle, kc_lower, kc_width | ACCURATE | volatility.py VOLATILITY_FUNCTIONS has exactly these 14 |
| 51 | **trend** (9): macd, macd_signal, macd_hist, adx, plus_di, minus_di, sar, supertrend, supertrend_dir | ACCURATE | trend.py TREND_FUNCTIONS has exactly these 9 |
| 52 | **volume** (5): obv, ad_line, vwap_day, volume_sma, volume_ratio | ACCURATE | volume.py VOLUME_FUNCTIONS has exactly these 5 |

---

## Section: data.py (lines 82-83)

| # | Claim | Verdict | Notes |
|---|-------|---------|-------|
| 53 | Signature: `load_data(instrument, timeframe="1d", asset_type="futures")` | ACCURATE | data.py line 12 |
| 54 | Path: `data/1d/futures/{symbol}.parquet` and `data/1m/futures/{symbol}.parquet` | ACCURATE | data.py line 20: `DATA_DIR / timeframe / asset_type / f"{instrument.upper()}.parquet"` |
| 55 | Cached via `@lru_cache` | ACCURATE | data.py line 11 |
| 56 | Returns DataFrame with DatetimeIndex and columns [open, high, low, close, volume] | ACCURATE | data.py lines 25-28: sets index on "timestamp", selects OHLCV columns |

---

## Section: Example (lines 85-104)

| # | Claim | Verdict | Notes |
|---|-------|---------|-------|
| 57 | Query structure matches pipeline steps | ACCURATE | session, period, from, map, where, sort -- all valid fields |
| 58 | `stats.min` (-3.6423) equals `first.change_pct` (-3.6423) when sorted asc | ACCURATE | Internally consistent: sorted ascending means first row = minimum value |
| 59 | `stats.max` (-2.6643) equals `last.change_pct` (-2.6643) when sorted asc | ACCURATE | Internally consistent: last row = maximum value in ascending sort |
| 60 | `source_rows: null` because no aggregation (no select) | ACCURATE | _build_response() lines 604-607: has_aggregation checks `query.get("select") is not None` |
| 61 | `chart: null` because no group_by | ACCURATE | _build_response() lines 631-639: chart=None when not grouped |

---

## Special attention items

### Are ALL summary fields documented for each type?

- **table**: type, rows, columns, stats, first, last -- all documented. Note: stats is only included when there are numeric summary_columns (line 714), and first/last are only included when table is non-empty and rows have relevant columns (lines 718-729). These conditional inclusions are not explicitly mentioned, but the doc's format implies they are always present. **Minor omission** -- stats can be absent if no map columns or sort column exists.

- **grouped**: type, rows, columns, by, stats, first, last, min_row, max_row -- all documented. Same conditional note as above for stats. **ACCURATE** overall.

- **scalar**: type, value, rows_scanned -- all three fields documented. **ACCURATE**.

- **dict**: type, values, rows_scanned -- all three fields documented. **ACCURATE**.

### Is the chart key correctly described?

Yes. The doc states `{category, value}` for grouped DataFrame results and says the key is absent for scalar/dict responses. This matches the source: chart key is only emitted in the DataFrame branch of `_build_response()` (line 648), and is set to `None` for non-grouped DataFrames. For scalar/dict, the chart key is not in the returned dict at all (lines 658-665 and 676-683).

### Is the period format description complete?

Nearly complete. The doc says: "YYYY, YYYY-MM, YYYY-MM-DD, start:end where each part is any format, last_year, last_month, last_week". The source also supports:
- Open-ended ranges: `"2023:"` (start only) and `":2024"` (end only) -- not explicitly mentioned in the doc but arguably covered by "start:end" with an empty part.

**Minor omission**: open-ended ranges could be explicitly documented.

---

## Summary

| Category | Claims | Accurate | Wrong |
|----------|--------|----------|-------|
| Pipeline | 10 | 10 | 0 |
| interpreter.py | 12 | 12 | 0 |
| validation.py | 8 | 8 | 0 |
| expressions.py | 7 | 7 | 0 |
| functions/ | 15 | 15 | 0 |
| data.py | 4 | 4 | 0 |
| Example | 5 | 5 | 0 |
| **Total** | **61** | **61** | **0** |

### Minor omissions (not errors):

1. **Conditional summary fields**: `stats`, `first`, `last` in table/grouped summaries are only included when certain conditions are met (numeric columns exist, table is non-empty). The doc implies they are always present.

2. **Open-ended period ranges**: `"2023:"` and `":2024"` are supported but not explicitly documented. Arguably covered by "start:end" phrasing.

3. **`columns` in summary**: The `columns` field in table/grouped summary uses `df.columns` from the original result DataFrame, which may not include the `date`/`time` columns that appear in the serialized `table` output (added by `_prepare_for_output`). This subtle difference is not mentioned.

---

## Final Accuracy Score

**61/61 factual claims verified as ACCURATE (100%)**

Three minor omissions noted (conditional field presence, open-ended ranges, columns source) -- none of these constitute errors in the existing text; they are details the doc does not cover but does not misstate.

**Verdict: The document is fully accurate against the current source code.**

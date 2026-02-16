# Audit: functions-architecture.md

**Date**: 2026-02-16
**Claims checked**: 62
**Correct**: 62 | **Wrong**: 0 | **Outdated**: 0 | **Unverifiable**: 0

## Issues

No issues found. All claims verified against the codebase.

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Package `barb/functions/` — 106 functions in 12 modules | CORRECT | `len(FUNCTIONS)` = 106; 12 module .py files (excluding `__init__.py` and `_smoothing.py`) |
| 2 | `__init__.py` exports FUNCTIONS, SIGNATURES, DESCRIPTIONS, AGGREGATE_FUNCS | CORRECT | `barb/functions/__init__.py:98` — `__all__ = ["FUNCTIONS", "AGGREGATE_FUNCS", "SIGNATURES", "DESCRIPTIONS"]` |
| 3 | `_smoothing.py` contains `wilder_smooth()` | CORRECT | `barb/functions/_smoothing.py:11` — `def wilder_smooth(series, n)` |
| 4 | `core.py` has 6 functions: abs, log, sqrt, sign, round, if | CORRECT | `barb/functions/core.py:14-21` — `CORE_FUNCTIONS` has exactly 6 keys |
| 5 | `lag.py` has 2 functions: prev, next | CORRECT | `barb/functions/lag.py:3-6` — `LAG_FUNCTIONS` has exactly 2 keys |
| 6 | `window.py` has 12 functions: rolling_*, ema, sma, wma, hma, vwma, rma | CORRECT | `barb/functions/window.py:52-65` — `WINDOW_FUNCTIONS` has 12 keys |
| 7 | `cumulative.py` has 3 functions: cumsum, cummax, cummin | CORRECT | `barb/functions/cumulative.py:3-7` — `CUMULATIVE_FUNCTIONS` has 3 keys |
| 8 | `pattern.py` has 8 functions: streak, bars_since, rank, rising, falling, valuewhen, pivothigh, pivotlow | CORRECT | `barb/functions/pattern.py:99-108` — `PATTERN_FUNCTIONS` has 8 keys |
| 9 | `aggregate.py` has 10 functions: mean, sum, max, min, std, median, count, percentile, correlation, last | CORRECT | `barb/functions/aggregate.py:5-16` — `AGGREGATE_FUNCTIONS` has 10 keys |
| 10 | `time.py` has 10 functions: dayofweek, dayname, hour, minute, month, monthname, year, date, day, quarter | CORRECT | `barb/functions/time.py:5-16` — `TIME_FUNCTIONS` has 10 keys |
| 11 | `convenience.py` has 19 functions: gap, change_pct, body, crossover, inside_bar, ... | CORRECT | `barb/functions/convenience.py:100-123` — `CONVENIENCE_FUNCTIONS` has 19 keys |
| 12 | `oscillators.py` has 8 functions: rsi, stoch_k, stoch_d, cci, williams_r, mfi, roc, momentum | CORRECT | `barb/functions/oscillators.py:85-94` — `OSCILLATOR_FUNCTIONS` has 8 keys |
| 13 | `trend.py` has 9 functions: macd, macd_signal, macd_hist, adx, plus_di, minus_di, supertrend, supertrend_dir, sar | CORRECT | `barb/functions/trend.py:219-229` — `TREND_FUNCTIONS` has 9 keys |
| 14 | `volatility.py` has 14 functions: tr, atr, natr, bbands_*, kc_*, donchian_* | CORRECT | `barb/functions/volatility.py:114-129` — `VOLATILITY_FUNCTIONS` has 14 keys |
| 15 | `volume.py` has 5 functions: obv, vwap_day, ad_line, volume_ratio, volume_sma | CORRECT | `barb/functions/volume.py:53-59` — `VOLUME_FUNCTIONS` has 5 keys |
| 16 | Function contract: `(df, *args) -> pd.Series \| scalar` | CORRECT | All functions take df as first arg and return Series or scalar values |
| 17 | Functions access OHLCV from df directly (`df["high"]`, `df["close"]`) | CORRECT | e.g. `barb/functions/oscillators.py:31` — `df["low"].rolling(n).min()` |
| 18 | Each module exports `*_FUNCTIONS`, `*_SIGNATURES`, `*_DESCRIPTIONS` | CORRECT | All 12 modules follow this pattern consistently |
| 19 | `__init__.py` merges dicts with `**` unpacking | CORRECT | `barb/functions/__init__.py:53-66` — `FUNCTIONS = {**CORE_FUNCTIONS, **LAG_FUNCTIONS, ...}` |
| 20 | SIGNATURES and DESCRIPTIONS used in `assistant/tools/reference.py` | CORRECT | `assistant/tools/reference.py:7` — `from barb.functions import DESCRIPTIONS, SIGNATURES` |
| 21 | AGGREGATE_FUNCS has 6 functions for group_by: mean, sum, max, min, std, median | CORRECT | `barb/functions/aggregate.py:20-27` — exactly 6 keys |
| 22 | RSI: `(df, col, n=14)` — explicit column | CORRECT | `barb/functions/oscillators.py:6` — `def _rsi(df, col, n=14)` |
| 23 | EMA: `(df, col, n)` — explicit column | CORRECT | `barb/functions/window.py:59` — `lambda df, col, n: col.ewm(...)` |
| 24 | ATR: `(df, n=14)` — implicit, always H/L/C | CORRECT | `barb/functions/volatility.py:17` — `def _atr(df, n=14)`, uses `_tr(df)` internally |
| 25 | gap: `(df)` — implicit, always O/C | CORRECT | `barb/functions/convenience.py:12-13` — `def _gap(df): return df["open"] - df["close"].shift(1)` |
| 26 | stoch_k: `(df, n=14)` — implicit, always H/L/C | CORRECT | `barb/functions/oscillators.py:25` — `def _stoch_k(df, n=14)` |
| 27 | `trend.py` imports `_atr, _tr` from volatility | CORRECT | `barb/functions/trend.py:7` — `from barb.functions.volatility import _atr, _tr` |
| 28 | `window.py`, `oscillators.py`, `volatility.py`, `trend.py` import wilder_smooth from `_smoothing` | CORRECT | grep shows all four import `wilder_smooth` from `barb.functions._smoothing` |
| 29 | Only public names in FUNCTIONS dict; `_rsi`, `_atr`, `_tr` are private | CORRECT | FUNCTIONS dict keys are all without underscore prefix |
| 30 | Wilder's/RMA: α=1/n, SMA seed, used by RSI, ATR, ADX, +DI, -DI | CORRECT | `_smoothing.py:37` — `alpha = 1.0 / n`; RSI/ATR use wilder_smooth; ADX uses it 3 times |
| 31 | Standard EMA: α=2/(n+1), `ewm(span=n, adjust=False)`, used by MACD, Keltner | CORRECT | `trend.py:14` — MACD uses `ewm(span=..., adjust=False)`; `volatility.py:79` — KC uses same |
| 32 | SMA: `rolling(n).mean()`, used by Bollinger, Stochastic %D | CORRECT | `volatility.py:36` — bbands uses `rolling(n).mean()`; `oscillators.py:38` — stoch_d uses `rolling().mean()` |
| 33 | `adjust=False` always used with EMA | CORRECT | All 9 `ewm()` calls across codebase use `adjust=False` |
| 34 | wilder_smooth: first value = SMA of first n non-NaN points | CORRECT | `_smoothing.py:34` — `result[seed_idx] = np.mean(non_nan)` where `non_nan` has exactly n elements |
| 35 | wilder_smooth: recursive `rma[t] = (1/n) * val[t] + (1 - 1/n) * rma[t-1]` | CORRECT | `_smoothing.py:38-42` — exact formula match |
| 36 | Bollinger Bands uses `ddof=0` (population std) | CORRECT | `barb/functions/volatility.py:38,51,59,68` — all use `.std(ddof=0)` |
| 37 | CCI uses mean deviation, not std | CORRECT | `barb/functions/oscillators.py:50` — `lambda x: abs(x - x.mean()).mean()` |
| 38 | Keltner: `kc_upper(n=20, atr_n=10, mult=1.5)` — two different periods | CORRECT | `barb/functions/volatility.py:77` — `def _kc_upper(df, n=20, atr_n=10, mult=1.5)` |
| 39 | MFI uses `rolling(n).sum()`, not exponential smoothing | CORRECT | `barb/functions/oscillators.py:68-69` — `.rolling(n).sum()` for both pos and neg flow |
| 40 | Stochastic %K default = 14 (TV), not 5 (ta-lib) | CORRECT | `barb/functions/oscillators.py:25` — `def _stoch_k(df, n=14)` |
| 41 | CCI default = 20 (TV), not 14 (ta-lib) | CORRECT | `barb/functions/oscillators.py:41` — `def _cci(df, n=20)` |
| 42 | Keltner mult default = 1.5 | CORRECT | `barb/functions/volatility.py:77` — `mult=1.5` |
| 43 | Test structure: `tests/functions/` with conftest.py and test files per module | CORRECT | All 15 test files exist in `tests/functions/` |
| 44 | conftest.py has shared `df` fixture: 10-bar OHLCV DataFrame with DatetimeIndex | CORRECT | `tests/functions/conftest.py:7-17` — 10 rows, OHLCV columns, DatetimeIndex |
| 45 | Fixture dates start at `2024-01-02`, periods=10, freq="D" | CORRECT | `tests/functions/conftest.py:10` — exact match |
| 46 | Fixture OHLCV values match doc | CORRECT | `tests/functions/conftest.py:12-16` — values identical to doc |
| 47 | Fixture is function-scoped | CORRECT | No explicit scope parameter = pytest default `function` scope |
| 48 | test_registry.py checks: functions without signatures, orphan signatures, orphan descriptions | CORRECT | `tests/functions/test_registry.py:7-21` — four tests cover these checks |
| 49 | test_registry.py checks: each signature starts with `func_name(` | CORRECT | `tests/functions/test_registry.py:31-36` — `sig.startswith(name + "(")` |
| 50 | test_registry.py checks: `len(FUNCTIONS) == len(SIGNATURES) == len(DESCRIPTIONS)` | CORRECT | `tests/functions/test_registry.py:38-40` — two assertions cover this |
| 51 | test_tv_match.py uses real NQ daily data with `load_data("NQ", "1d")`, module-scoped | CORRECT | `tests/functions/test_tv_match.py:24-30` — `scope="module"`, `load_data("NQ", "1d")` |
| 52 | test_tv_match.py uses CSV reference data from `tests/functions/reference_data/nq_oscillators_tv.csv` | CORRECT | `tests/functions/test_tv_match.py:21` — `REF_PATH = "tests/functions/reference_data/nq_oscillators_tv.csv"` |
| 53 | Reference CSV has 3 dates x OHLCV + RSI/ATR/CCI/StochK/WilliamsR/MFI | CORRECT | CSV has 3 data rows with columns: date,open,high,low,close,rsi_14,atr_14,cci_20,stoch_k_14,williams_r_14,mfi_14 |
| 54 | `_assert_close` uses relative OR absolute tolerance | CORRECT | `tests/functions/test_tv_match.py:51-60` — checks abs_tol first, then rel_tol |
| 55 | RSI test tolerance: `rel_tol=0.01, abs_tol=0.5` | CORRECT | `tests/functions/test_tv_match.py:70` — exact values match |
| 56 | test_tv_match.py has TestRSIMatch class | CORRECT | `tests/functions/test_tv_match.py:63` — `class TestRSIMatch:` |
| 57 | `DISPLAY_GROUPS` exists in `assistant/tools/reference.py` | CORRECT | `assistant/tools/reference.py:11` — `DISPLAY_GROUPS = [...]` |
| 58 | reference.py has explicit list of functions per group | CORRECT | `assistant/tools/reference.py:11-162` — all 106 functions listed by name in groups |
| 59 | Functions not in DISPLAY_GROUPS won't appear in Claude's prompt | CORRECT | `assistant/tools/reference.py:189-199` — only names from DISPLAY_GROUPS are rendered |
| 60 | Step 6 of adding new function: add to DISPLAY_GROUPS in reference.py | CORRECT | This is the documented process; reference.py has explicit name lists |
| 61 | Files section lists correct paths | CORRECT | All listed paths exist and serve described purposes |
| 62 | Dates in reference CSV chosen away from contract rolls | CORRECT | `tests/functions/test_tv_match.py:7` — docstring states "chosen away from contract rolls"; dates are 2025-12-05, 2026-01-15, 2026-02-05 (mid-quarter) |

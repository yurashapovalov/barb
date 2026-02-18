# Audit: research.md

Date: 2026-02-18

## Claims

### Claim 1
- **Doc**: line 5: "Every major platform — TradingView, ta-lib, and pandas-ta — uses Wilder's smoothing (α = 1/n) for RSI, ATR, and ADX, and standard EMA (α = 2/(n+1)) for MACD."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about external platforms (TradingView, ta-lib, pandas-ta), cannot verify from codebase alone

### Claim 2
- **Doc**: line 14: "RMA[t] = (1/n) × value[t] + (1 - 1/n) × RMA[t-1]"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/_smoothing.py:42` — `result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]` where `alpha = 1.0 / n` (line 37)

### Claim 3
- **Doc**: line 17: "TradingView implements this as `ta.rma()`, which seeds the first value with an SMA of the first *n* data points, then switches to the recursive formula."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about TradingView's internal implementation, cannot verify from codebase alone; the Barb implementation does match this description (see Claim 4)

### Claim 4
- **Doc**: line 17: "seeds the first value with an SMA of the first *n* data points"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/_smoothing.py:34` — `result[seed_idx] = np.mean(non_nan)` where `non_nan` is the list of the first `n` non-NaN values collected in the loop at lines 22–29

### Claim 5
- **Doc**: line 19: "The correct pandas equivalent is **`ewm(alpha=1/n, adjust=False).mean()`** or equivalently `ewm(com=n-1, adjust=False).mean()`."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/_smoothing.py:1-5` — module docstring explicitly states "NOT the same as pandas ewm(alpha=1/n, adjust=False)" because of the SMA seed difference; the mathematical equivalence of alpha=1/n and com=n-1 is a standard pandas identity, consistent with Claim 6 below

### Claim 6
- **Doc**: line 19: "This causes divergence in early bars that converges after roughly **100 bars** to within 0.01. To get an exact match, you need custom code that computes the SMA of the first *n* values as the seed, then applies the recursive formula from there."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/_smoothing.py:1-4` — "NOT the same as pandas ewm(alpha=1/n, adjust=False). The SMA seed is what makes TradingView values match." Barb implements the custom SMA-seed approach; `/Users/yura/Development/barb/docs/barb/functions-architecture.md:99` — "Наивный ewm(alpha=1/n) расходится с TradingView в первых ~100 барах."

### Claim 7
- **Doc**: line 21: "For standard EMA (used in MACD, Keltner Channels), the pandas equivalent is **`ewm(span=n, adjust=False).mean()`**, which gives α = 2/(n+1). The `adjust=False` is critical."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:14` — `fast_ema = col.ewm(span=int(fast), adjust=False).mean()`; `/Users/yura/Development/barb/barb/functions/volatility.py:79` — `ema = df["close"].ewm(span=int(n), adjust=False).mean()`

### Claim 8
- **Doc**: line 25: "Wilder's / RMA | 1/n | `ewm(com=n-1, adjust=False)` | RSI, ATR, ADX"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:13` — RSI calls `wilder_smooth(gain, n)`; `/Users/yura/Development/barb/barb/functions/volatility.py:22` — ATR calls `wilder_smooth(_tr(df), int(n))`; `/Users/yura/Development/barb/barb/functions/trend.py:56-58` — ADX calls `wilder_smooth` for DM and TR smoothing

### Claim 9
- **Doc**: line 26: "Standard EMA | 2/(n+1) | `ewm(span=n, adjust=False)` | MACD, Keltner"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:14-15` — MACD uses `ewm(span=int(fast), adjust=False)` and `ewm(span=int(slow), adjust=False)`; `/Users/yura/Development/barb/barb/functions/volatility.py:79` — Keltner uses `ewm(span=int(n), adjust=False)`

### Claim 10
- **Doc**: line 27: "SMA | N/A | `rolling(n).mean()` | Bollinger, Stochastic %D"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:36` — `sma = col.rolling(n).mean()` in Bollinger; `/Users/yura/Development/barb/barb/functions/oscillators.py:38` — `_stoch_d` returns `_stoch_k(df, n).rolling(int(smooth)).mean()`

### Claim 11
- **Doc**: line 39: "Smooth both using **Wilder's smoothing** (not SMA, not standard EMA): `avg_gain = RMA(gains, 14)`, `avg_loss = RMA(losses, 14)`"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:13-14` — `avg_gain = wilder_smooth(gain, n)` and `avg_loss = wilder_smooth(loss, n)`

### Claim 12
- **Doc**: line 41: "`RSI = 100 - 100/(1 + RS)`, equivalently `RSI = 100 × avg_gain / (avg_gain + avg_loss)`"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:17` — `rsi = 100 - 100 / (1 + rs)` where `rs = avg_gain / avg_loss`

### Claim 13
- **Doc**: line 43: "Handle the edge case where all changes are gains (loss = 0): RS → ∞, RSI should be **100**."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:19-20` — `# Edge case: all gains (avg_loss = 0) → RSI = 100` followed by `rsi = rsi.where(avg_loss != 0, 100.0)`

### Claim 14
- **Doc**: line 45: "### MACD — Defaults: fast=12, slow=26, signal=9"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:12` — `def _macd(df, col, fast=12, slow=26)`; `/Users/yura/Development/barb/barb/functions/trend.py:19` — `def _macd_signal(df, col, fast=12, slow=26, sig=9)`

### Claim 15
- **Doc**: line 48-50: "MACD Line = EMA(close, 12) - EMA(close, 26) / Signal Line = EMA(MACD_Line, 9) / Histogram = MACD Line - Signal Line"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:14-16` — `fast_ema = col.ewm(span=int(fast), adjust=False).mean()`, `slow_ema = col.ewm(span=int(slow), adjust=False).mean()`, `return fast_ema - slow_ema`; `/Users/yura/Development/barb/barb/functions/trend.py:22` — signal is `macd_line.ewm(span=int(sig), adjust=False).mean()`; `/Users/yura/Development/barb/barb/functions/trend.py:29` — histogram is `macd_line - signal`

### Claim 16
- **Doc**: line 53: "All three platforms use **standard span-based EMA** (α = 2/(n+1)), not Wilder's smoothing."
- **Verdict**: UNVERIFIABLE
- **Evidence**: the Barb implementation uses standard EMA correctly (see Claim 15), but whether ta-lib and pandas-ta do the same cannot be verified from codebase alone

### Claim 17
- **Doc**: line 62-63: "**The critical platform difference**: ta-lib defaults to `fastk_period=5`, while TradingView and pandas-ta default to **14**."
- **Verdict**: ACCURATE (for TradingView/Barb side)
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:25-28` — `def _stoch_k(df, n=14)` with comment "Default n=14 matches TradingView (NOT ta-lib which defaults to 5)"; the ta-lib side is UNVERIFIABLE from codebase

### Claim 18
- **Doc**: line 63: "All platforms use SMA for smoothing by default."
- **Verdict**: ACCURATE (for Barb)
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:38` — `_stoch_d` uses `_stoch_k(df, n).rolling(int(smooth)).mean()` (SMA)

### Claim 19
- **Doc**: line 65-70: "### Williams %R — Default period: 14" with formula `%R = ((Highest_High - Close) / (Highest_High - Lowest_Low)) × -100`
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:54-59` — `def _williams_r(df, n=14)` with `return (highest - df["close"]) / (highest - lowest) * -100`

### Claim 20
- **Doc**: line 71: "This is mathematically the **inverse of fast %K**: `%R = Fast%K - 100`."
- **Verdict**: ACCURATE
- **Evidence**: mathematically derived from the formulas in Claims 17 and 19 — both use the same highest/lowest range; `%K = (Close - Lowest) / (Highest - Lowest) * 100` and `%R = (Highest - Close) / (Highest - Lowest) * -100 = %K - 100`. The implementations in `/Users/yura/Development/barb/barb/functions/oscillators.py:31-33` and `54-59` confirm this relationship.

### Claim 21
- **Doc**: line 75-82: "MFI uses simple rolling sums, not exponential smoothing"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:68-69` — `pos_flow = rmf.where(direction > 0, 0.0).rolling(n).sum()` and `neg_flow = rmf.where(direction < 0, 0.0).rolling(n).sum()` — these are simple rolling sums, not EWM

### Claim 22
- **Doc**: line 79: "Direction: if `TP[t] > TP[t-1]`, flow is positive; if less, negative; if equal, zero"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:67-69` — `direction = tp.diff()`, then `pos_flow = rmf.where(direction > 0, 0.0)` and `neg_flow = rmf.where(direction < 0, 0.0)` — equal (diff == 0) is treated as neither positive nor negative (zero contribution to both flows)

### Claim 23
- **Doc**: line 81: "`MFI = 100 - 100/(1 + Positive_Sum/Negative_Sum)`"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:70` — `return 100 - 100 / (1 + pos_flow / neg_flow)`

### Claim 24
- **Doc**: line 91: "ATR applies **Wilder's smoothing** to TR, not SMA."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:21-22` — `def _atr(df, n=14)` calls `return wilder_smooth(_tr(df), int(n))`

### Claim 25
- **Doc**: line 91: "the first ATR value is seeded with an SMA of the first *n* True Range values"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/_smoothing.py:34` — `result[seed_idx] = np.mean(non_nan)` — SMA of first n non-NaN values used as seed for all wilder_smooth calls including ATR

### Claim 26
- **Doc**: line 93: "### Bollinger Bands — Defaults: period=20, multiplier=2"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:33` — `def _bbands_upper(df, col, n=20, mult=2.0)`

### Claim 27
- **Doc**: line 101: "All three platforms use **population standard deviation (ddof=0)**, dividing by N rather than N-1."
- **Verdict**: ACCURATE (for Barb)
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:38` — `std = col.rolling(n).std(ddof=0)` with comment `# ddof=0: population std, matches TradingView`

### Claim 28
- **Doc**: line 101: "In pandas, you must use `rolling(20).std(ddof=0)` — the default `ddof=1` (sample std dev) will produce slightly wider bands."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:38` — code uses `col.rolling(n).std(ddof=0)`, confirming this is a deliberate choice to avoid pandas default `ddof=1`

### Claim 29
- **Doc**: line 103: "### Keltner Channels — Defaults: EMA=20, ATR=10, multiplier=1.5"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:77` — `def _kc_upper(df, n=20, atr_n=10, mult=1.5)`

### Claim 30
- **Doc**: line 106-108: "Middle = EMA(close, 20) / Upper = Middle + 1.5 × ATR(10) / Lower = Middle - 1.5 × ATR(10)"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:79-80` — `ema = df["close"].ewm(span=int(n), adjust=False).mean()` and `return ema + float(mult) * _atr(df, int(atr_n))`; `/Users/yura/Development/barb/barb/functions/volatility.py:89-91` — lower uses `ema - float(mult) * _atr(df, int(atr_n))`

### Claim 31
- **Doc**: line 111: "The center line is an **EMA** (not SMA — this distinguishes Keltner from Bollinger)."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volatility.py:83-85` — `def _kc_middle(df, n=20)` returns `df["close"].ewm(span=int(n), adjust=False).mean()` (EMA); Bollinger middle uses `col.rolling(int(n)).mean()` (SMA) at line 43-44

### Claim 32
- **Doc**: line 113: "### SuperTrend — Defaults: ATR period=10, multiplier=3"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:136` — `def _supertrend(df, n=10, mult=3.0)`

### Claim 33
- **Doc**: line 117: "**Basic bands**: `Upper = hl2 + 3 × ATR(10)`, `Lower = hl2 - 3 × ATR(10)` where `hl2 = (High + Low) / 2`."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:98` — `hl2 = ((df["high"] + df["low"]) / 2).values`; lines 102-103 — `upper = (hl2 + mult * atr_vals).copy()` and `lower = (hl2 - mult * atr_vals).copy()`

### Claim 34
- **Doc**: lines 121-124: "Band clamping" — `finalUpper = basicUpper < prevUpper OR prevClose > prevUpper ? basicUpper : prevUpper` and `finalLower = basicLower > prevLower OR prevClose < prevLower ? basicLower : prevLower`
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:113-118` — `if not (lower[i] > lower[i - 1] or close[i - 1] < lower[i - 1]): lower[i] = lower[i - 1]` and `if not (upper[i] < upper[i - 1] or close[i - 1] > upper[i - 1]): upper[i] = upper[i - 1]`

### Claim 35
- **Doc**: line 126: "ta-lib has **no built-in SuperTrend** — it must be implemented manually."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about ta-lib's feature set, cannot verify from codebase alone

### Claim 36
- **Doc**: line 126: "TradingView defaults to period=10, multiplier=3"
- **Verdict**: ACCURATE (Barb matches these defaults)
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:136` — `def _supertrend(df, n=10, mult=3.0)` — Barb uses these as defaults, consistent with the doc's statement that TradingView uses them

### Claim 37
- **Doc**: line 126: "pandas-ta defaults to period=**7**, multiplier=3"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about pandas-ta's default parameters, cannot verify from codebase alone

### Claim 38
- **Doc**: line 132-138: "### CCI — Constant: 0.015" with formula and "Lambert chose **0.015** so that ~70–80% of CCI values fall within ±100"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:51` — `return (tp - sma_tp) / (0.015 * mean_dev)` confirms the constant; the ~70-80% interpretation is UNVERIFIABLE from code alone

### Claim 39
- **Doc**: line 140: "**TradingView defaults to period 20** (matching Lambert's original), while **ta-lib and pandas-ta default to 14**."
- **Verdict**: ACCURATE (for TradingView/Barb side; ta-lib side UNVERIFIABLE)
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:41` — `def _cci(df, n=20)` with comment "Default n=20 matches TradingView (NOT ta-lib which defaults to 14)"

### Claim 40
- **Doc**: line 140: "CCI uses **mean absolute deviation**, not standard deviation."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:50` — `mean_dev = tp.rolling(n).apply(lambda x: abs(x - x.mean()).mean(), raw=True)` — this is mean absolute deviation

### Claim 41
- **Doc**: line 148: "If UpMove > DownMove and UpMove > 0, then +DM = UpMove, else +DM = 0. If DownMove > UpMove and DownMove > 0, then -DM = DownMove, else -DM = 0."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:50-53` — `plus_mask = (up_move > down_move) & (up_move > 0)` and `minus_mask = (down_move > up_move) & (down_move > 0)` then DM set to move values at those masks, 0 otherwise

### Claim 42
- **Doc**: line 148: "The first smoothed value is the SMA (mean) of the first 14 values; subsequent values use `Smoothed[t] = Smoothed[t-1] × 13/14 + Current / 14`."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:56-58` — ADX calls `wilder_smooth` for TR, +DM, -DM; `/Users/yura/Development/barb/barb/functions/_smoothing.py:34,37,42` — seed is `np.mean(non_nan)` (SMA), then `result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]` where `alpha = 1/n`, equivalent to `1/14 * current + 13/14 * prev`

### Claim 43
- **Doc**: line 154: "**Step 5 — ADX**: The first ADX is an SMA of the first 14 DX values. Subsequent values use Wilder's smoothing: `ADX[t] = (ADX[t-1] × 13 + DX[t]) / 14`."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:63-64` — `dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100` then `adx = wilder_smooth(dx, n)`, which applies SMA seed then recursive formula

### Claim 44
- **Doc**: line 156: "The total lookback for ADX(14) is **27 bars** (2N - 1)."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:39` — comment "Total warmup = 2n - 1 bars." For n=14, 2×14-1 = 27

### Claim 45
- **Doc**: lines 163-169: "### OBV (On Balance Volume) — No parameters" with the if/else accumulation formula
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volume.py:8-11` — `direction = np.sign(df["close"].diff())` implements the three-way direction (positive, negative, zero); result is `(df["volume"] * direction).cumsum()`

### Claim 46
- **Doc**: line 170: "The only edge case: pandas-ta's native implementation treats the first bar as positive (adds volume), while ta-lib initializes OBV at 0."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about pandas-ta and ta-lib internal behavior, cannot verify from codebase alone; Barb's own OBV at `/Users/yura/Development/barb/barb/functions/volume.py:10` sets `direction.iloc[0] = 0` (no volume added on first bar, matching ta-lib's approach)

### Claim 47
- **Doc**: line 174-178: "VWAP = Cumulative(TP × Volume) / Cumulative(Volume)" with reset at session boundary
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volume.py:14-27` — computes `tp = (high + low + close) / 3`, `tpv = tp * df["volume"]`, then `cum_tpv / cum_vol` with daily groupby reset

### Claim 48
- **Doc**: line 178: "**ta-lib does not include VWAP** — this must be implemented manually."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about ta-lib's feature set, cannot verify from codebase alone

### Claim 49
- **Doc**: line 178: "TradingView supports anchoring to session, week, month, quarter, year, earnings, and dividends."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about TradingView's feature set, cannot verify from codebase alone

### Claim 50
- **Doc**: line 178: "On daily charts with session anchoring, VWAP equals each bar's typical price (useless) — use week/month anchors instead."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volume.py:17-19` — comment "On daily data, VWAP = typical price (trivially)." confirms this observation; the `vwap_day` function resets per calendar day, making each daily bar its own VWAP window

### Claim 51
- **Doc**: lines 183-185: "CLV = ((Close - Low) - (High - Close)) / (High - Low)" and "A/D[t] = A/D[t-1] + CLV × Volume"
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volume.py:36-39` — `clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / high_low` then `return (clv * df["volume"]).cumsum()`

### Claim 52
- **Doc**: line 188: "When **High == Low** (zero-range bar), all platforms set CLV = 0, effectively skipping that bar."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/volume.py:37-38` — when `high_low = 0`, the division produces `NaN`, then `clv = clv.fillna(0)` sets it to 0

### Claim 53
- **Doc**: lines 196-202: "**Not yet implemented** — Oscillators: `ta.cmo()`, `ta.tsi()`, `ta.cog()`. Moving averages: `ta.alma()`, `ta.swma()`. Volume: `ta.pvt`, `ta.nvi`/`ta.pvi`, `ta.iii`. Other: `ta.linreg()`, Ichimoku Cloud, Fibonacci retracement levels."
- **Verdict**: ACCURATE
- **Evidence**: none of `cmo`, `tsi`, `cog`, `alma`, `swma`, `pvt`, `nvi`, `pvi`, `iii`, `linreg`, `ichimoku`, or `fibonacci` appear in `/Users/yura/Development/barb/barb/functions/__init__.py`; the grep across all function modules returned no matches for these names

### Claim 54
- **Doc**: line 212: "With insufficient history, ta-lib's warmup phase produces values that diverge by up to **10 points** for indicators like Stochastic and 2–3 points for RSI."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about ta-lib's runtime behavior with specific data inputs, cannot verify from codebase alone

### Claim 55
- **Doc**: line 214: "CCI defaults to 20 in TradingView but **14** in ta-lib. Stochastic %K defaults to 14 in TradingView but **5** in ta-lib."
- **Verdict**: ACCURATE (for TradingView/Barb side; ta-lib side UNVERIFIABLE)
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:41` — `def _cci(df, n=20)` comment "Default n=20 matches TradingView (NOT ta-lib which defaults to 14)"; `/Users/yura/Development/barb/barb/functions/oscillators.py:25-28` — `def _stoch_k(df, n=14)` comment "Default n=14 matches TradingView (NOT ta-lib which defaults to 5)"

### Claim 56
- **Doc**: line 222: "**The `adjust` parameter is the single biggest source of bugs.** Pandas defaults to `adjust=True`, which uses a bias-corrected weighted average. Every trading platform uses the equivalent of `adjust=False`."
- **Verdict**: ACCURATE
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:14,15,22,28` — all EWM calls in Barb use `adjust=False`; `/Users/yura/Development/barb/barb/functions/volatility.py:79,85,90,96` — same pattern throughout; `/Users/yura/Development/barb/docs/barb/functions-architecture.md:95` — "adjust=False всегда. Pandas дефолт adjust=True не совпадает ни с одной торговой платформой."

### Claim 57
- **Doc**: line 224: "`span=14` gives α = 2/15 ≈ 0.133 (standard EMA). `com=13` gives α = 1/14 ≈ 0.071 (Wilder's smoothing). `com=14` gives α = 1/15 ≈ 0.067 (wrong for both)."
- **Verdict**: ACCURATE
- **Evidence**: these are standard pandas EWM parameter relationships; the Barb codebase consistently uses `span=n` for standard EMA and documents `com=n-1` as the Wilder's equivalent; `/Users/yura/Development/barb/barb/functions/_smoothing.py` implements Wilder's via custom code rather than pandas EWM to get exact SMA seeding

### Claim 58
- **Doc**: line 226: "**NaN handling**: Set `min_periods` explicitly on every `ewm()` call."
- **Verdict**: WRONG
- **Evidence**: `/Users/yura/Development/barb/barb/functions/trend.py:14,15,22,28`, `/Users/yura/Development/barb/barb/functions/volatility.py:79,85,90,96`, `/Users/yura/Development/barb/barb/functions/window.py:59` — no `min_periods` is set on any `ewm()` call in the codebase; the doc recommends this practice but it is not followed in the implementation
- **Fix**: either update the doc to remove this recommendation, or note that Barb's EWM calls do not set `min_periods` (relying on the SMA-seeded wilder_smooth for Wilder indicators, and tolerating early EMA values for standard EMA indicators)

### Claim 59
- **Doc**: line 228: "`rolling().apply(lambda)` is extremely slow (~2 seconds per 5,000 rows). ta-lib's C implementation is approximately **100× faster** than pure Python."
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about runtime performance benchmarks, cannot verify from codebase alone; note that Barb does use `rolling().apply(lambda)` in several places (e.g., `/Users/yura/Development/barb/barb/functions/oscillators.py:50` for CCI mean deviation, `/Users/yura/Development/barb/barb/functions/window.py:12` for WMA)

### Claim 60
- **Doc**: line 236: "1. **Smoothing**: Wilder's (α=1/n, SMA seed) for RSI/ATR/ADX, standard EMA (α=2/(n+1)) for MACD/Keltner, SMA for Bollinger"
- **Verdict**: ACCURATE
- **Evidence**: RSI: `/Users/yura/Development/barb/barb/functions/oscillators.py:13-14`; ATR: `/Users/yura/Development/barb/barb/functions/volatility.py:22`; ADX: `/Users/yura/Development/barb/barb/functions/trend.py:56-64`; MACD: `/Users/yura/Development/barb/barb/functions/trend.py:14-15`; Keltner: `/Users/yura/Development/barb/barb/functions/volatility.py:79`; Bollinger: `/Users/yura/Development/barb/barb/functions/volatility.py:36`

### Claim 61
- **Doc**: line 238: "3. **Pandas**: always `adjust=False`, `ddof=0` for Bollinger, `com=n-1` for Wilder's"
- **Verdict**: ACCURATE
- **Evidence**: `adjust=False`: all `ewm()` calls in the codebase (see Claim 56); `ddof=0`: `/Users/yura/Development/barb/barb/functions/volatility.py:38,51,59,68`; the `com=n-1` form is the documented pandas equivalent for Wilder's, though Barb uses the custom `wilder_smooth` function instead of `ewm(com=n-1)`

### Claim 62
- **Doc**: line 239: "4. **Defaults**: specify explicitly — ta-lib and TradingView disagree on CCI (14 vs 20) and Stochastic %K (5 vs 14)"
- **Verdict**: ACCURATE (for Barb's choices)
- **Evidence**: `/Users/yura/Development/barb/barb/functions/oscillators.py:41` — `_cci` defaults to `n=20`; `/Users/yura/Development/barb/barb/functions/oscillators.py:25` — `_stoch_k` defaults to `n=14`; both match TradingView, not ta-lib

---

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 43 |
| OUTDATED | 0 |
| WRONG | 1 |
| MISSING | 0 |
| UNVERIFIABLE | 18 |
| **Total** | **62** |
| **Accuracy** | **69%** |

Accuracy = ACCURATE / Total × 100 = 43 / 62 × 100 ≈ 69%

Note: The UNVERIFIABLE claims are all about external systems (TradingView, ta-lib, pandas-ta behavior and defaults). They are not wrong — the Barb implementation code validates the choices made on the basis of those claims. If only verifiable claims are counted (ACCURATE + WRONG), the accuracy rate is 43/44 = 98%.

The single WRONG claim (Claim 58) is an actionable recommendation in the doc (`min_periods` on every `ewm()` call) that is not followed anywhere in the actual implementation.

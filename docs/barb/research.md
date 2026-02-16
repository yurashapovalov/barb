# Research: Canonical Indicator Implementations

> Pre-implementation research. See `functions-architecture.md` for current Barb implementation details.

**Every major platform — TradingView, ta-lib, and pandas-ta — uses Wilder's smoothing (α = 1/n) for RSI, ATR, and ADX, and standard EMA (α = 2/(n+1)) for MACD.** The differences that trip up developers are not in the core formulas but in initialization seeding, default parameter values, and pandas's `adjust=True` default. This report covers all 14 requested indicators with exact formulas, verified default parameters, known cross-platform discrepancies, and the precise pandas equivalents needed to replicate each one.

---

## Wilder's smoothing is the foundation — and the #1 source of bugs

Three of the most important indicators (RSI, ATR, ADX) depend on Wilder's smoothing, also called RMA or SMMA. The exact recursive formula is:

```
RMA[t] = (1/n) × value[t] + (1 - 1/n) × RMA[t-1]
```

This is an EMA with **α = 1/n**, which is slower than a standard EMA where α = 2/(n+1). A 14-period Wilder's smoothing is roughly equivalent to a **27-period standard EMA** in responsiveness. TradingView implements this as `ta.rma()`, which seeds the first value with an SMA of the first *n* data points, then switches to the recursive formula.

The correct pandas equivalent is **`ewm(alpha=1/n, adjust=False).mean()`** or equivalently `ewm(com=n-1, adjust=False).mean()`. However, there is a subtle initialization difference: pandas EWM starts exponential weighting from the first data point, while Wilder's original method and TradingView/ta-lib seed with an SMA. This causes divergence in early bars that converges after roughly **100 bars** to within 0.01. To get an exact match, you need custom code that computes the SMA of the first *n* values as the seed, then applies the recursive formula from there.

For standard EMA (used in MACD, Keltner Channels), the pandas equivalent is **`ewm(span=n, adjust=False).mean()`**, which gives α = 2/(n+1). The `adjust=False` is critical — pandas defaults to `adjust=True`, which uses a bias-corrected weighted average that does **not** match any trading platform.

| Smoothing type | Alpha | Pandas equivalent | Used by |
|---|---|---|---|
| Wilder's / RMA | 1/n | `ewm(com=n-1, adjust=False)` | RSI, ATR, ADX |
| Standard EMA | 2/(n+1) | `ewm(span=n, adjust=False)` | MACD, Keltner |
| SMA | N/A | `rolling(n).mean()` | Bollinger, Stochastic %D |

---

## RSI, MACD, and the momentum indicators

### RSI (Relative Strength Index) — Default period: 14

The step-by-step formula that all three platforms implement:

1. Price change: `Δ = close[t] - close[t-1]`
2. Separate: `gain = max(Δ, 0)`, `loss = max(-Δ, 0)`
3. Smooth both using **Wilder's smoothing** (not SMA, not standard EMA): `avg_gain = RMA(gains, 14)`, `avg_loss = RMA(losses, 14)`
4. `RS = avg_gain / avg_loss`
5. `RSI = 100 - 100/(1 + RS)`, equivalently `RSI = 100 × avg_gain / (avg_gain + avg_loss)`

TradingView's `ta.rsi()` calls `ta.rma()` internally. ta-lib's `RSI()` also uses Wilder's smoothing — and critically, **ta-lib's RSI has no `matype` parameter**; it always uses Wilder's method. The most common pandas mistake is using `rolling(14).mean()` for the averages, which produces an SMA-based RSI that diverges significantly from both platforms. Handle the edge case where all changes are gains (loss = 0): RS → ∞, RSI should be **100**.

### MACD — Defaults: fast=12, slow=26, signal=9

```
MACD Line  = EMA(close, 12) - EMA(close, 26)
Signal Line = EMA(MACD_Line, 9)
Histogram   = MACD Line - Signal Line
```

All three platforms use **standard span-based EMA** (α = 2/(n+1)), not Wilder's smoothing. There are no meaningful cross-platform differences for MACD. In pandas: `ewm(span=n, adjust=False).mean()` for all three components. ta-lib also offers `MACDEXT` which allows configurable MA types per component.

### Stochastic Oscillator — Defaults vary by platform

The raw (fast) %K formula:

```
Fast %K = (Close - Lowest_Low(K)) / (Highest_High(K) - Lowest_Low(K)) × 100
```

The fast stochastic displays this raw %K plus an SMA-smoothed %D. The slow stochastic first smooths %K with an SMA (producing Slow %K), then smooths that again for Slow %D. **The critical platform difference**: ta-lib defaults to `fastk_period=5`, while TradingView and pandas-ta default to **14**. All platforms use SMA for smoothing by default. In TradingView, `ta.stoch()` returns only the raw %K — you must smooth it manually with `ta.sma()`.

### Williams %R — Default period: 14

```
%R = ((Highest_High - Close) / (Highest_High - Lowest_Low)) × -100
```

This is mathematically the **inverse of fast %K**: `%R = Fast%K - 100`. The range is -100 (oversold) to 0 (overbought). No meaningful platform differences.

### MFI (Money Flow Index) — Default period: 14

MFI is often described as "RSI applied to volume-weighted price," but this is misleading. The critical difference is that **MFI uses simple rolling sums, not exponential smoothing**:

1. Typical Price: `TP = (H + L + C) / 3`
2. Raw Money Flow: `RMF = TP × Volume`
3. Direction: if `TP[t] > TP[t-1]`, flow is positive; if less, negative; if equal, zero
4. Sum positive and negative flows over the period (simple rolling sum, **not** Wilder's smoothing)
5. `MFI = 100 - 100/(1 + Positive_Sum/Negative_Sum)`

RSI has infinite memory via exponential smoothing; MFI has a fixed lookback window. All platforms agree on this implementation.

---

## ATR, Bollinger Bands, and the volatility indicators

### ATR (Average True Range) — Default period: 14

True Range: `TR = max(High - Low, |High - Prev_Close|, |Low - Prev_Close|)`. ATR applies **Wilder's smoothing** to TR, not SMA. All three platforms agree: the first ATR value is seeded with an SMA of the first *n* True Range values, then the recursive RMA formula takes over. ta-lib's C source code explicitly confirms the Wilder's approach. pandas-ta defaults to RMA but allows switching via the `mamode` parameter.

### Bollinger Bands — Defaults: period=20, multiplier=2

```
Middle = SMA(close, 20)
Upper  = Middle + 2 × σ
Lower  = Middle - 2 × σ
```

All three platforms use **population standard deviation (ddof=0)**, dividing by N rather than N-1. This is consistent with Bollinger's original formulation. In pandas, you must use `rolling(20).std(ddof=0)` — the default `ddof=1` (sample std dev) will produce slightly wider bands. TradingView's `ta.stdev()` has a `biased` parameter defaulting to `true` (population). ta-lib also uses ddof=0.

### Keltner Channels — Defaults: EMA=20, ATR=10, multiplier=1.5

```
Middle = EMA(close, 20)
Upper  = Middle + 1.5 × ATR(10)
Lower  = Middle - 1.5 × ATR(10)
```

The center line is an **EMA** (not SMA — this distinguishes Keltner from Bollinger). The EMA period and ATR period are **separate parameters**. ATR uses Wilder's smoothing. Keltner bands are generally smoother than Bollinger Bands because ATR-based width changes more gradually than standard-deviation-based width. TradingView defaults to mult=1.5 (Barb follows this).

### SuperTrend — Defaults: ATR period=10, multiplier=3

The algorithm has three key components:

**Basic bands**: `Upper = hl2 + 3 × ATR(10)`, `Lower = hl2 - 3 × ATR(10)` where `hl2 = (High + Low) / 2`.

**Band clamping** (the critical part): The upper band can only move down (tighten) unless price has broken above it. The lower band can only move up unless price has broken below it. This creates a ratchet effect:

```
finalUpper = basicUpper < prevUpper OR prevClose > prevUpper ? basicUpper : prevUpper
finalLower = basicLower > prevLower OR prevClose < prevLower ? basicLower : prevLower
```

**Flip logic**: In a downtrend, SuperTrend = upper band; if close breaks above the upper band, it flips to uptrend and SuperTrend = lower band. The reverse triggers a downtrend flip. ta-lib has **no built-in SuperTrend** — it must be implemented manually. TradingView defaults to period=10, multiplier=3; pandas-ta defaults to period=**7**, multiplier=3.

---

## CCI, ADX, and the complex indicators

### CCI (Commodity Channel Index) — Constant: 0.015

```
TP = (H + L + C) / 3
CCI = (TP - SMA(TP, n)) / (0.015 × Mean_Deviation)
Mean_Deviation = (1/n) × Σ|TP_i - SMA(TP, n)|
```

CCI uses **mean absolute deviation**, not standard deviation. Lambert chose **0.015** so that ~70–80% of CCI values fall within ±100, corresponding to roughly ±1.33 standard deviations. A significant platform discrepancy: **TradingView defaults to period 20** (matching Lambert's original), while **ta-lib and pandas-ta default to 14**. Always specify the period explicitly.

### ADX / +DI / -DI — Default period: 14

This is the most complex indicator. The complete algorithm:

**Step 1 — Directional Movement**: `UpMove = High[t] - High[t-1]`, `DownMove = Low[t-1] - Low[t]`. If UpMove > DownMove and UpMove > 0, then +DM = UpMove, else +DM = 0. If DownMove > UpMove and DownMove > 0, then -DM = DownMove, else -DM = 0. Only one can be positive per bar; if equal, both are zero.

**Step 2 — Smooth +DM, -DM, and TR** using Wilder's smoothing over 14 periods. The first smoothed value is the SMA (mean) of the first 14 values; subsequent values use `Smoothed[t] = Smoothed[t-1] × 13/14 + Current / 14`.

**Step 3 — Directional Indicators**: `+DI = (Smoothed +DM / Smoothed TR) × 100`, `-DI = (Smoothed -DM / Smoothed TR) × 100`.

**Step 4 — DX**: `DX = |+DI - -DI| / (+DI + -DI) × 100`.

**Step 5 — ADX**: The first ADX is an SMA of the first 14 DX values. Subsequent values use Wilder's smoothing: `ADX[t] = (ADX[t-1] × 13 + DX[t]) / 14`.

The total lookback for ADX(14) is **27 bars** (2N - 1). TradingView's `ta.dmi()` allows separate DI and ADX smoothing lengths; ta-lib's `ADX()` uses a single `timeperiod` for both. Minor numerical differences between platforms arise from initialization, converging after ~100 bars.

---

## Volume and price-based indicators

### OBV (On Balance Volume) — No parameters

```
If Close > Prev_Close: OBV += Volume
If Close < Prev_Close: OBV -= Volume
If Close == Prev_Close: OBV unchanged
```

Purely cumulative with no configurable period. All platforms agree. The only edge case: pandas-ta's native implementation treats the first bar as positive (adds volume), while ta-lib initializes OBV at 0. Since only the shape matters, not absolute values, this is inconsequential.

### VWAP — Resets per anchor period

```
VWAP = Cumulative(TP × Volume) / Cumulative(Volume)
```

where `TP = (H + L + C) / 3` and cumulative sums reset at each session boundary. **ta-lib does not include VWAP** — this must be implemented manually. TradingView supports anchoring to session, week, month, quarter, year, earnings, and dividends. pandas-ta requires a DatetimeIndex and uses pandas offset aliases for anchoring. On daily charts with session anchoring, VWAP equals each bar's typical price (useless) — use week/month anchors instead.

### Accumulation/Distribution Line — No parameters

```
CLV = ((Close - Low) - (High - Close)) / (High - Low)
    = (2 × Close - Low - High) / (High - Low)
A/D[t] = A/D[t-1] + CLV × Volume
```

CLV ranges from -1 (close at low) to +1 (close at high). When **High == Low** (zero-range bar), all platforms set CLV = 0, effectively skipping that bar. Unlike OBV which assigns all volume as positive or negative, the A/D line weights volume proportionally by close position within the bar's range.

---

## Not yet implemented

Most functions from the original research list are now in `barb/functions/`. Remaining candidates:

**Oscillators**: `ta.cmo()` (Chande Momentum Oscillator), `ta.tsi()` (True Strength Index), `ta.cog()` (Center of Gravity).

**Moving averages**: `ta.alma()` (Arnaud Legoux), `ta.swma()`.

**Volume**: `ta.pvt` (Price Volume Trend), `ta.nvi`/`ta.pvi` (Negative/Positive Volume Index), `ta.iii` (Intraday Intensity Index).

**Other**: `ta.linreg()` (linear regression), Ichimoku Cloud, Fibonacci retracement levels.

---

## Cross-platform discrepancies and pandas gotchas

### Known TradingView vs ta-lib differences

The root causes of discrepancy are consistent across all indicators:

- **Initialization seeding**: TradingView calculates from bar 0 of its full chart history; ta-lib works only with the data you provide. With insufficient history, ta-lib's warmup phase produces values that diverge by up to **10 points** for indicators like Stochastic and 2–3 points for RSI.
- **EMA seeding**: Both platforms seed the first EMA with an SMA, but TradingView may have access to more pre-chart bars for this seed.
- **CCI and Stochastic defaults**: CCI defaults to 20 in TradingView but **14** in ta-lib. Stochastic %K defaults to 14 in TradingView but **5** in ta-lib. These produce completely different signals if you rely on defaults.
- **SuperTrend and VWAP**: ta-lib lacks both entirely.
- **ADX rounding**: ta-lib originally followed Wilder's manual rounding from his book but later removed it for computer precision.

The `tradingview-ta-lib` Python library (github.com/akumidv/tradingview-ta-lib) was created specifically to replicate TradingView's exact calculations in Python.

### Critical pandas implementation pitfalls

**The `adjust` parameter is the single biggest source of bugs.** Pandas defaults to `adjust=True`, which uses a bias-corrected weighted average. Every trading platform uses the equivalent of `adjust=False` (pure recursive formula). Always specify `adjust=False`.

**The `ewm()` parameter confusion** catches even experienced developers. `span=14` gives α = 2/15 ≈ 0.133 (standard EMA). `com=13` gives α = 1/14 ≈ 0.071 (Wilder's smoothing). `com=14` gives α = 1/15 ≈ 0.067 (wrong for both). For Wilder's smoothing with period *n*, use `com=n-1` or `alpha=1/n`. For standard EMA with period *n*, use `span=n`.

**NaN handling**: Set `min_periods` explicitly on every `ewm()` call. Without it, a "14-period EMA" computed from a single data point silently produces a value. Use `ewm(span=14, adjust=False, min_periods=14)`. For data with gaps, note that `ignore_na=False` (default) counts NaN positions in the decay weighting.

**Performance**: `rolling().apply(lambda)` is extremely slow (~2 seconds per 5,000 rows). Use vectorized operations wherever possible. ta-lib's C implementation is approximately **100× faster** than pure Python for indicators like RSI on large datasets. For a production library, compute in numpy and wrap in pandas at the output stage.

**Look-ahead bias**: Always `shift(1)` indicator values before using them as trading signals. This is the error that invalidates entire backtesting pipelines.

---

## Key takeaways

1. **Smoothing**: Wilder's (α=1/n, SMA seed) for RSI/ATR/ADX, standard EMA (α=2/(n+1)) for MACD/Keltner, SMA for Bollinger
2. **Initialization**: SMA seed then recursive — `ewm(alpha=1/n)` without seed diverges in first ~100 bars
3. **Pandas**: always `adjust=False`, `ddof=0` for Bollinger, `com=n-1` for Wilder's
4. **Defaults**: specify explicitly — ta-lib and TradingView disagree on CCI (14 vs 20) and Stochastic %K (5 vs 14)
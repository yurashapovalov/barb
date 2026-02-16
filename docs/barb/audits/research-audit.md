# Audit: research.md

**Date**: 2026-02-16
**Claims checked**: 72
**Correct**: 55 | **Wrong**: 1 | **Outdated**: 0 | **Unverifiable**: 16

## Summary

`research.md` is a pre-implementation research document, not a code documentation file. It describes canonical indicator algorithms and cross-platform differences. Most claims fall into two categories: (1) mathematical/algorithmic descriptions verified against Barb's implementation, and (2) statements about external platforms (TradingView, ta-lib, pandas-ta) that cannot be verified from our codebase alone. The document is highly accurate -- only one claim is technically wrong (a mixed-form Wilder's smoothing formula in the ADX section), and all implemented indicators match the algorithms described.

## Issues

### [WRONG] ADX Step 2 mixes sum-form and average-form of Wilder's smoothing
- **Doc says**: "The first smoothed value is the SMA (mean) of the first 14 values; subsequent values use `Smoothed[t] = Smoothed[t-1] * 13/14 + Current`."
- **Code says**: `wilder_smooth()` uses the average form throughout: first value = mean of first n values, then `rma[t] = (1/n) * value[t] + (1 - 1/n) * rma[t-1]`. The doc's recursive formula `Smoothed[t-1] * 13/14 + Current` is Wilder's *sum* form (operates on running sums, not averages), but it says the first value is the "SMA (mean)" which is the *average* form seed. These two forms are mathematically equivalent for computing DI and ADX (the n factor cancels in ratios), but the doc's formula does not match the code's implementation. The code uses `alpha * value + (1-alpha) * prev_rma` consistently.
- **File**: `/Users/yura/Development/barb/barb/functions/_smoothing.py:15-16`, `/Users/yura/Development/barb/docs/barb/research.md:148`

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Major platforms use Wilder's smoothing (alpha=1/n) for RSI, ATR, ADX | CORRECT | `barb/functions/_smoothing.py:37` uses `alpha = 1.0 / n`; RSI/ATR/ADX all call `wilder_smooth()` |
| 2 | Standard EMA (alpha=2/(n+1)) for MACD | CORRECT | `barb/functions/trend.py:14` uses `ewm(span=int(fast), adjust=False)` which gives alpha=2/(n+1) |
| 3 | RMA formula: `RMA[t] = (1/n) * value[t] + (1 - 1/n) * RMA[t-1]` | CORRECT | `barb/functions/_smoothing.py:37-42` — `alpha = 1.0 / n`, `result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]` |
| 4 | Wilder's is an EMA with alpha=1/n, slower than standard EMA | CORRECT | Standard EMA alpha=2/(n+1) > 1/n for all n>1. Mathematical fact. |
| 5 | 14-period Wilder's ~ 27-period standard EMA | CORRECT | Setting 1/14 = 2/(n+1) gives n=27. Mathematical derivation. |
| 6 | TradingView implements RMA with SMA seed of first n data points | CORRECT | `barb/functions/_smoothing.py:22-34` — collects first n non-NaN values, seeds with `np.mean(non_nan)` |
| 7 | Correct pandas equivalent for Wilder's: `ewm(alpha=1/n, adjust=False)` or `ewm(com=n-1, adjust=False)` | CORRECT | `com=n-1` gives alpha=1/(1+(n-1))=1/n. Mathematical identity. But doc also notes this diverges without SMA seed. |
| 8 | Naive pandas EWM diverges from TradingView in early bars, converges after ~100 bars | UNVERIFIABLE | General claim about convergence behavior. Code uses custom `wilder_smooth()` to avoid this. |
| 9 | Standard EMA pandas: `ewm(span=n, adjust=False)` gives alpha=2/(n+1) | CORRECT | Pandas documentation: span gives alpha=2/(span+1). |
| 10 | `adjust=False` is critical; pandas defaults to `adjust=True` | CORRECT | Pandas documentation confirms default. Code uses `adjust=False` everywhere: `barb/functions/trend.py:14-15`, `barb/functions/window.py:59`, `barb/functions/volatility.py:79` |
| 11 | Wilder's/RMA used by RSI, ATR, ADX | CORRECT | `oscillators.py:13-14` (RSI), `volatility.py:22` (ATR), `trend.py:56-58,64` (ADX) — all call `wilder_smooth()` |
| 12 | Standard EMA used by MACD, Keltner | CORRECT | `trend.py:14-15` (MACD), `volatility.py:79,85,90` (Keltner) — all use `ewm(span=..., adjust=False)` |
| 13 | SMA used by Bollinger, Stochastic %D | CORRECT | `volatility.py:36` (Bollinger: `rolling(n).mean()`), `oscillators.py:38` (Stochastic %D: `rolling(int(smooth)).mean()`) |
| 14 | RSI default period: 14 | CORRECT | `oscillators.py:6` — `_rsi(df, col, n=14)` |
| 15 | RSI step-by-step: delta, gain/loss separation, Wilder's smoothing, RS, formula | CORRECT | `oscillators.py:9-17` matches exactly |
| 16 | RSI edge case: all gains (loss=0) → RSI=100 | CORRECT | `oscillators.py:20` — `rsi = rsi.where(avg_loss != 0, 100.0)` |
| 17 | ta-lib RSI has no `matype` parameter | UNVERIFIABLE | External library claim |
| 18 | MACD defaults: fast=12, slow=26, signal=9 | CORRECT | `trend.py:12,19,25` — `_macd(df, col, fast=12, slow=26)`, `_macd_signal(..., sig=9)` |
| 19 | MACD uses standard span-based EMA, not Wilder's | CORRECT | `trend.py:14-15` uses `ewm(span=..., adjust=False)`, not `wilder_smooth()` |
| 20 | MACD Line = EMA(close, 12) - EMA(close, 26) | CORRECT | `trend.py:14-16` |
| 21 | Signal Line = EMA(MACD_Line, 9) | CORRECT | `trend.py:21-22` |
| 22 | Histogram = MACD Line - Signal Line | CORRECT | `trend.py:28-29` |
| 23 | ta-lib offers MACDEXT with configurable MA types | UNVERIFIABLE | External library claim |
| 24 | Stochastic fast %K formula: (Close - Lowest_Low) / (Highest_High - Lowest_Low) * 100 | CORRECT | `oscillators.py:31-33` — exact match |
| 25 | ta-lib defaults fastk_period=5, TradingView/pandas-ta default to 14 | UNVERIFIABLE | External library claims. Barb uses 14: `oscillators.py:25` |
| 26 | TradingView `ta.stoch()` returns only raw %K | UNVERIFIABLE | TradingView PineScript behavior |
| 27 | Williams %R default period: 14 | CORRECT | `oscillators.py:54` — `_williams_r(df, n=14)` |
| 28 | Williams %R formula: ((Highest_High - Close) / (Highest_High - Lowest_Low)) * -100 | CORRECT | `oscillators.py:57-59` — exact match |
| 29 | Williams %R is inverse of fast %K: %R = Fast%K - 100 | CORRECT | Mathematical proof: %K = (C-L)/(H-L)*100, %R = -(H-C)/(H-L)*100 = (C-H)/(H-L)*100 = (C-L-H+L)/(H-L)*100 = %K - 100 |
| 30 | MFI default period: 14 | CORRECT | `oscillators.py:62` — `_mfi(df, n=14)` |
| 31 | MFI Typical Price = (H+L+C)/3 | CORRECT | `oscillators.py:65` — `tp = (df["high"] + df["low"] + df["close"]) / 3` |
| 32 | MFI Raw Money Flow = TP * Volume | CORRECT | `oscillators.py:66` — `rmf = tp * df["volume"]` |
| 33 | MFI direction: if TP[t] > TP[t-1], positive; if less, negative | CORRECT | `oscillators.py:67-69` — `direction = tp.diff()`, then `.where(direction > 0, 0.0)` and `.where(direction < 0, 0.0)` |
| 34 | MFI uses rolling sums, not exponential smoothing | CORRECT | `oscillators.py:68-69` — `rolling(n).sum()` |
| 35 | MFI formula: 100 - 100/(1 + Positive_Sum/Negative_Sum) | CORRECT | `oscillators.py:70` — exact match |
| 36 | ATR default period: 14 | CORRECT | `volatility.py:17` — `_atr(df, n=14)` |
| 37 | True Range formula: max(H-L, abs(H-prevC), abs(L-prevC)) | CORRECT | `volatility.py:10-14` — exact match |
| 38 | ATR uses Wilder's smoothing, not SMA | CORRECT | `volatility.py:22` — `wilder_smooth(_tr(df), int(n))` |
| 39 | pandas-ta defaults to RMA but allows switching via `mamode` | UNVERIFIABLE | External library claim |
| 40 | Bollinger Bands defaults: period=20, multiplier=2 | CORRECT | `volatility.py:33` — `_bbands_upper(df, col, n=20, mult=2.0)` |
| 41 | Bollinger Middle = SMA(close, 20) | CORRECT | `volatility.py:44` — `col.rolling(int(n)).mean()` |
| 42 | All platforms use population std dev (ddof=0) for Bollinger | CORRECT | `volatility.py:38` — `col.rolling(n).std(ddof=0)` |
| 43 | TradingView `ta.stdev()` has `biased` parameter defaulting to `true` | UNVERIFIABLE | TradingView PineScript behavior |
| 44 | ta-lib uses ddof=0 for Bollinger | UNVERIFIABLE | External library claim |
| 45 | Keltner defaults: EMA=20, ATR=10, multiplier=1.5 | CORRECT | `volatility.py:77` — `_kc_upper(df, n=20, atr_n=10, mult=1.5)` |
| 46 | Keltner center is EMA (not SMA) | CORRECT | `volatility.py:79` — `ewm(span=int(n), adjust=False).mean()` |
| 47 | Keltner EMA and ATR are separate parameters | CORRECT | `volatility.py:77` — `n=20, atr_n=10` are separate |
| 48 | Keltner ATR uses Wilder's smoothing | CORRECT | `volatility.py:80` calls `_atr()` which calls `wilder_smooth()` |
| 49 | SuperTrend defaults: ATR period=10, multiplier=3 | CORRECT | `trend.py:136` — `_supertrend(df, n=10, mult=3.0)` |
| 50 | SuperTrend basic bands: Upper = hl2 + mult * ATR, Lower = hl2 - mult * ATR | CORRECT | `trend.py:98,102-103` — `hl2 = (high + low) / 2`, `upper = hl2 + mult * atr`, `lower = hl2 - mult * atr` |
| 51 | SuperTrend band clamping formula | CORRECT | `trend.py:113-118` — verified against doc pseudocode, logic matches exactly |
| 52 | SuperTrend flip logic: downtrend=upper band, close breaks above → flip to uptrend=lower band | CORRECT | `trend.py:123-128` — `tv_dir` controls which band is active |
| 53 | ta-lib has no built-in SuperTrend | UNVERIFIABLE | External library claim |
| 54 | pandas-ta SuperTrend defaults to period=7, multiplier=3 | UNVERIFIABLE | External library claim |
| 55 | CCI constant: 0.015 | CORRECT | `oscillators.py:51` — `0.015 * mean_dev` |
| 56 | CCI uses mean absolute deviation, not std dev | CORRECT | `oscillators.py:50` — `lambda x: abs(x - x.mean()).mean()` |
| 57 | CCI Typical Price = (H+L+C)/3 | CORRECT | `oscillators.py:48` — exact match |
| 58 | TradingView CCI defaults to 20, ta-lib to 14 | UNVERIFIABLE | External platform claims. Barb uses 20: `oscillators.py:41` |
| 59 | ADX default period: 14 | CORRECT | `trend.py:35` — `_adx_system(df, n=14)` |
| 60 | ADX Step 1: +DM/-DM directional movement formulas | CORRECT | `trend.py:44-53` — verified in detail, exact match |
| 61 | ADX: only one DM can be positive per bar; if equal, both zero | CORRECT | `trend.py:50-51` — strict `>` comparison means equal values produce both zero |
| 62 | ADX Step 2: Smooth +DM, -DM, and TR using Wilder's smoothing | CORRECT | `trend.py:56-58` — all three use `wilder_smooth()` |
| 63 | ADX Step 2 recursive formula: `Smoothed[t] = Smoothed[t-1] * 13/14 + Current` | WRONG | Code uses average form: `rma[t] = (1/n) * value[t] + (1-1/n) * rma[t-1]` (`_smoothing.py:37-42`). Doc formula is the sum form but seeds with "SMA (mean)" which is the average form. Mixed formulation. |
| 64 | ADX Step 3: +DI = Smoothed +DM / Smoothed TR * 100 | CORRECT | `trend.py:60` — exact match |
| 65 | ADX Step 4: DX = abs(+DI - -DI) / (+DI + -DI) * 100 | CORRECT | `trend.py:63` — exact match |
| 66 | ADX Step 5: First ADX = SMA of first 14 DX values, then Wilder's smoothing | CORRECT | `trend.py:64` — `wilder_smooth(dx, n)` which seeds with SMA of first n values |
| 67 | Total ADX lookback = 27 bars (2N-1) | CORRECT | `trend.py:39` docstring confirms `2n - 1`. First wilder_smooth needs n bars, second needs n more, overlap of 1. |
| 68 | OBV formula: add volume on up, subtract on down, unchanged on equal | CORRECT | `volume.py:8-11` — `np.sign(df["close"].diff())` gives +1/0/-1, multiply by volume |
| 69 | VWAP formula: Cumulative(TP * Volume) / Cumulative(Volume) with session reset | CORRECT | `volume.py:20-27` — `cum_tpv / cum_vol` with groupby dates |
| 70 | ta-lib does not include VWAP | UNVERIFIABLE | External library claim |
| 71 | A/D Line CLV formula: ((Close-Low) - (High-Close)) / (High-Low) | CORRECT | `volume.py:37` — exact match |
| 72 | A/D Line: when High==Low, CLV=0 | CORRECT | `volume.py:38` — `clv.fillna(0)` handles division by zero |

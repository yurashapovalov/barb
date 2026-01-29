# Barb Script — Standard Indicator Library

Built-in indicators assembled from DSL primitives. The LLM writes `rsi(close, 14)` in a query — the interpreter expands it into steps and computes the result.

These are NOT new language features. Each indicator is a recipe of existing building blocks: `ema`, `rolling_mean`, `rolling_max`, `rolling_min`, `rolling_std`, `prev`, `if`, `abs`, `cumsum`, arithmetic.

---

## Trend Indicators

### SMA — Simple Moving Average

Already a primitive: `rolling_mean(col, n)`

```
sma(close, 20) = rolling_mean(close, 20)
```

### EMA — Exponential Moving Average

Already a primitive: `ema(col, n)`

```
ema(close, 20) = ema(close, 20)
```

### MACD — Moving Average Convergence Divergence

Measures trend direction and momentum using two EMAs.

```
macd(col, fast, slow, signal)
  Default: macd(close, 12, 26, 9)
```

Expands to:
```
macd_line   = ema(close, 12) - ema(close, 26)
signal_line = ema(macd_line, 9)
histogram   = macd_line - signal_line
```

Returns three columns: `macd_line`, `signal_line`, `histogram`.

Usage: MACD line crossing above signal = bullish. Histogram growing = momentum increasing. Divergence between MACD and price = potential reversal.

### ADX — Average Directional Index

Measures trend strength (0-100). Does NOT show direction.

```
adx(n)
  Default: adx(14)
```

Expands to:
```
up_move    = high - prev(high)
down_move  = prev(low) - low
plus_dm    = if(up_move > down_move and up_move > 0, up_move, 0)
minus_dm   = if(down_move > up_move and down_move > 0, down_move, 0)
atr_n      = ema(true_range, n)
plus_di    = 100 * ema(plus_dm, n) / atr_n
minus_di   = 100 * ema(minus_dm, n) / atr_n
dx         = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
adx        = ema(dx, n)
```

Returns: `adx` value (0-100). Also available: `plus_di`, `minus_di`.

Usage: ADX > 25 = trending. ADX < 20 = ranging. Does not tell direction — use plus_di/minus_di for that.

### Parabolic SAR

Trailing stop/reversal indicator. Dots above price = downtrend, below = uptrend.

```
psar(af_start, af_step, af_max)
  Default: psar(0.02, 0.02, 0.2)
```

This indicator has iterative state (acceleration factor changes over time). Cannot be expressed as a simple formula from primitives — requires dedicated implementation in the interpreter.

---

## Momentum / Oscillators

### RSI — Relative Strength Index

Momentum oscillator (0-100). Overbought > 70, oversold < 30.

```
rsi(col, n)
  Default: rsi(close, 14)
```

Expands to:
```
change   = close - prev(close)
gain     = if(change > 0, change, 0)
loss     = if(change < 0, abs(change), 0)
avg_gain = ema(gain, n)
avg_loss = ema(loss, n)
rs       = avg_gain / avg_loss
rsi      = 100 - 100 / (1 + rs)
```

Usage: RSI < 30 = oversold (potential buy). RSI > 70 = overbought (potential sell). Divergence between RSI and price = reversal signal.

### Stochastic Oscillator

Compares closing price to price range over N bars. Fast %K/%D and Slow %K/%D.

```
stochastic(k_period, d_period, slowing)
  Default: stochastic(14, 3, 3)
```

Expands to:
```
lowest_k   = rolling_min(low, k_period)
highest_k  = rolling_max(high, k_period)
fast_k     = (close - lowest_k) / (highest_k - lowest_k) * 100
fast_d     = rolling_mean(fast_k, d_period)
slow_k     = fast_d
slow_d     = rolling_mean(slow_k, slowing)
```

Returns: `fast_k`, `fast_d`, `slow_k`, `slow_d`.

Usage: %K crossing above %D = buy signal. Above 80 = overbought. Below 20 = oversold.

### CCI — Commodity Channel Index

Measures deviation from statistical mean. Unbounded but typically -100 to +100.

```
cci(n)
  Default: cci(20)
```

Expands to:
```
typical    = (high + low + close) / 3
sma_tp     = rolling_mean(typical, n)
mean_dev   = rolling_mean(abs(typical - sma_tp), n)
cci        = (typical - sma_tp) / (0.015 * mean_dev)
```

Usage: CCI > 100 = overbought / strong uptrend. CCI < -100 = oversold / strong downtrend.

### MFI — Money Flow Index

Volume-weighted RSI. Uses both price and volume.

```
mfi(n)
  Default: mfi(14)
```

Expands to:
```
typical      = (high + low + close) / 3
money_flow   = typical * volume
positive_mf  = if(typical > prev(typical), money_flow, 0)
negative_mf  = if(typical < prev(typical), money_flow, 0)
mf_ratio     = rolling_sum(positive_mf, n) / rolling_sum(negative_mf, n)
mfi          = 100 - 100 / (1 + mf_ratio)
```

Usage: MFI > 80 = overbought. MFI < 20 = oversold. Divergence with price = reversal signal.

---

## Volatility Indicators

### ATR — Average True Range

Already available as a recipe from primitives:

```
atr(n)
  Default: atr(14)
```

Expands to:
```
true_range = max(high - low, abs(high - prev(close)), abs(low - prev(close)))
atr        = rolling_mean(true_range, n)
```

Note: some implementations use EMA instead of SMA. We use SMA (Wilder's original used a smoothing that is equivalent to EMA with period 2n-1).

### Bollinger Bands

Volatility envelope around SMA. Price touching bands = potential reversal or breakout.

```
bollinger(col, n, num_std)
  Default: bollinger(close, 20, 2)
```

Expands to:
```
middle = rolling_mean(close, n)
std_n  = rolling_std(close, n)
upper  = middle + num_std * std_n
lower  = middle - num_std * std_n
```

Returns: `upper`, `middle`, `lower`.

Usage: Price touching upper band = potential overbought. Squeeze (bands narrow) = low volatility, breakout coming. Bandwidth = (upper - lower) / middle.

### Keltner Channels

Like Bollinger but uses ATR instead of standard deviation. Smoother.

```
keltner(n, atr_n, multiplier)
  Default: keltner(20, 10, 1.5)
```

Expands to:
```
middle = ema(close, n)
atr_val = atr(atr_n)
upper  = middle + multiplier * atr_val
lower  = middle - multiplier * atr_val
```

Returns: `upper`, `middle`, `lower`.

Usage: Similar to Bollinger. Bollinger inside Keltner = "squeeze" (TTM Squeeze indicator).

### Donchian Channels

Highest high and lowest low over N bars. Already available from primitives:

```
donchian(n)
  Default: donchian(20)
```

Expands to:
```
upper  = rolling_max(high, n)
lower  = rolling_min(low, n)
middle = (upper + lower) / 2
```

Usage: Breakout above upper = buy signal (Turtle Trading). Channel width shows volatility.

---

## Volume Indicators

### OBV — On-Balance Volume

Cumulative volume weighted by price direction. Rising OBV = accumulation, falling = distribution.

```
obv()
```

Expands to:
```
direction  = if(close > prev(close), 1, if(close < prev(close), -1, 0))
obv        = cumsum(direction * volume)
```

Usage: OBV diverging from price = potential reversal. OBV confirming price = trend is strong.

### VWAP — Volume-Weighted Average Price

Average price weighted by volume. Intraday benchmark.

```
vwap()
```

Expands to:
```
typical    = (high + low + close) / 3
cum_tp_vol = cumsum(typical * volume)
cum_vol    = cumsum(volume)
vwap       = cum_tp_vol / cum_vol
```

Note: Traditional VWAP resets daily. This is a running VWAP — does not reset. Daily reset requires session-aware implementation.

---

## Summary

| Indicator | Function | Category | Complexity |
|-----------|----------|----------|------------|
| SMA | `rolling_mean(col, n)` | Trend | Primitive |
| EMA | `ema(col, n)` | Trend | Primitive |
| MACD | `macd(close, 12, 26, 9)` | Trend | 3 steps |
| ADX | `adx(14)` | Trend | 8 steps |
| Parabolic SAR | `psar(0.02, 0.02, 0.2)` | Trend | Dedicated impl |
| RSI | `rsi(close, 14)` | Momentum | 6 steps |
| Stochastic | `stochastic(14, 3, 3)` | Momentum | 4 steps |
| CCI | `cci(20)` | Momentum | 3 steps |
| MFI | `mfi(14)` | Volume/Momentum | 5 steps |
| ATR | `atr(14)` | Volatility | 2 steps |
| Bollinger | `bollinger(close, 20, 2)` | Volatility | 3 steps |
| Keltner | `keltner(20, 10, 1.5)` | Volatility | 3 steps |
| Donchian | `donchian(20)` | Volatility | 2 steps |
| OBV | `obv()` | Volume | 2 steps |
| VWAP | `vwap()` | Volume | 3 steps |

15 indicators. All except Parabolic SAR build from existing primitives.

---

## Adding New Indicators

To add a new indicator:
1. Write the recipe as a sequence of steps using existing primitives
2. Add it to this library with name, default parameters, expansion, and usage
3. The interpreter automatically supports it — no DSL changes needed

If the indicator requires logic that cannot be expressed with current primitives (like Parabolic SAR's iterative state), it needs dedicated implementation in the interpreter.

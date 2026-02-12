# Expression Reference

## Base columns

open, high, low, close, volume — plus any columns created in `map`.

## Operators

Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`
Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
Boolean: `and`, `or`, `not`
Membership: `dayofweek() in [0, 1, 4]`

## Functions

Scalar: abs(x), log(x), sqrt(x), sign(x), round(x, n=0), if(cond, then, else)

Lag: prev(col, n=1), next(col, n=1)

Moving Averages: sma(col, n), ema(col, n), wma(col, n), hma(col, n), vwma(n=20), rma(col, n)

Window: rolling_mean(col, n), rolling_sum(col, n), rolling_max(col, n), rolling_min(col, n), rolling_std(col, n), rolling_count(cond, n)

Cumulative: cummax(col), cummin(col), cumsum(col)

Pattern: streak(cond), bars_since(cond), rank(col), rising(col, n=1), falling(col, n=1), valuewhen(cond, col, n=0), pivothigh(n_left=5, n_right=5), pivotlow(n_left=5, n_right=5)

Aggregate (for select/group_by): mean(col), sum(col), max(col), min(col), std(col), median(col), count(), percentile(col, p), correlation(col1, col2), last(col)

Time: dayofweek(), dayname(), hour(), minute(), month(), monthname(), year(), date(), day(), quarter()

Price: gap(), gap_pct(), change(col, n=1), change_pct(col, n=1), range(), range_pct(), midpoint(), typical_price()

Candle: body(), body_pct(), upper_wick(), lower_wick(), green(), red(), doji(threshold=0.1), inside_bar(), outside_bar()

Signal: crossover(a, b), crossunder(a, b)

Oscillators: rsi(col, n=14), stoch_k(n=14), stoch_d(n=14, smooth=3), cci(n=20), williams_r(n=14), mfi(n=14), roc(col, n=1), momentum(col, n=10)

Trend: macd(col, fast=12, slow=26), macd_signal(col, fast=12, slow=26, sig=9), macd_hist(col, fast=12, slow=26, sig=9), adx(n=14), plus_di(n=14), minus_di(n=14), supertrend(n=10, mult=3.0), supertrend_dir(n=10, mult=3.0), sar(accel=0.02, max_accel=0.2)

Volatility: tr(), atr(n=14), natr(n=14), bbands_upper(col, n=20, mult=2.0), bbands_middle(col, n=20), bbands_lower(col, n=20, mult=2.0), bbands_width(col, n=20, mult=2.0), bbands_pctb(col, n=20, mult=2.0), kc_upper(n=20, atr_n=10, mult=1.5), kc_middle(n=20), kc_lower(n=20, atr_n=10, mult=1.5), kc_width(n=20, atr_n=10, mult=1.5), donchian_upper(n=20), donchian_lower(n=20)

Volume: obv(), vwap_day(), ad_line(), volume_ratio(n=20), volume_sma(n=20)

## Notes

- Functions like atr(), gap(), stoch_k() use OHLCV from the DataFrame directly — no need to pass columns.
- Functions like rsi(col, n), ema(col, n) take an explicit column — can be applied to any series.
- prev(close) returns NaN for the first row. NaN rows are excluded from filters automatically.
- dayofweek() returns 0=Monday, 1=Tuesday, ..., 4=Friday.
- crossover(a, b) is true on the bar where a crosses above b.

# Barb Script — Catalog

Everything that can be computed from OHLCV data. Derived from the data itself, not from any specific set of questions.

---

## 1. Bar Metrics

Measurements from a single OHLCV bar. Each bar has timestamp, open, high, low, close, volume.

### 1.1 Price Metrics

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `range` | `high - low` | float | Full price range of the bar. How much price moved in total. |
| `body` | `abs(close - open)` | float | Candle body size. How much of the move was directional. |
| `upper_wick` | `high - max(open, close)` | float | Upper shadow. Price went up but was rejected. |
| `lower_wick` | `min(open, close) - low` | float | Lower shadow. Price went down but was rejected. |
| `midpoint` | `(high + low) / 2` | float | Middle of the bar's range. |
| `typical_price` | `(high + low + close) / 3` | float | Weighted center of the bar. Used in some indicators. |
| `body_pct` | `body / range` | float | Body as percentage of range. 1.0 = no wicks, 0.0 = doji. |

### 1.2 Direction

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `direction` | `sign(close - open)` | int | +1 = bullish (close > open), -1 = bearish, 0 = unchanged |
| `is_bullish` | `close > open` | bool | Bar closed higher than it opened. |
| `is_bearish` | `close < open` | bool | Bar closed lower than it opened. |

### 1.3 Volume

Volume is already a base column. No derived metrics from volume alone — it becomes useful in aggregation (mean, sum) and in combination with other metrics (e.g., high volume + big range = strong move).

---

## 2. Inter-bar Metrics

Measurements that compare the current bar to the previous bar. All require `prev()` — access to the prior bar's values.

### 2.1 Price Change

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `change` | `close - prev(close)` | float | How much price moved since last bar's close. Signed — positive = up. |
| `pct_change` | `change / prev(close)` | float | Percentage price change. 0.01 = 1% up. |
| `gap` | `open - prev(close)` | float | Gap between this bar's open and last bar's close. Positive = gap up. |
| `gap_pct` | `gap / prev(close)` | float | Gap as percentage of previous close. |
| `true_range` | `max(high - low, abs(high - prev(close)), abs(low - prev(close)))` | float | True Range — accounts for gaps. Used in ATR calculation. Always >= range. |

### 2.2 Structural Comparisons

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `higher_high` | `high > prev(high)` | bool | This bar's high is above the previous bar's high. |
| `lower_low` | `low < prev(low)` | bool | This bar's low is below the previous bar's low. |
| `higher_low` | `low > prev(low)` | bool | This bar's low is higher. Sign of strength. |
| `lower_high` | `high < prev(high)` | bool | This bar's high is lower. Sign of weakness. |

### 2.3 Gap Details

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `gap_up` | `open > prev(high)` | bool | True gap up — open is above previous high. No overlap. |
| `gap_down` | `open < prev(low)` | bool | True gap down — open is below previous low. |
| `gap_exists` | `gap != 0` | bool | Any gap (open != prev close). Includes partial gaps. |
| `gap_filled` | `if(gap > 0, low <= prev(close), high >= prev(close))` | bool | Price returned to previous close during the bar. Gap was "filled". |

---

## 3. Named Patterns

Boolean conditions that describe well-known trading patterns. These are combinations of the metrics above.

### 3.1 Single-bar Patterns (relative to previous bar)

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `inside_bar` | `high < prev(high) and low > prev(low)` | bool | Bar is entirely within previous bar's range. Contraction. Indecision. |
| `outside_bar` | `high > prev(high) and low < prev(low)` | bool | Bar engulfs previous bar's range. Expansion. Strong move or reversal. |
| `up_day` | `close > prev(close)` | bool | Closed higher than previous close. |
| `down_day` | `close < prev(close)` | bool | Closed lower than previous close. |

### 3.2 Candle Shape Patterns

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `doji` | `body_pct < 0.1` | bool | Very small body relative to range. Indecision. Threshold: body < 10% of range. |
| `strong_body` | `body_pct > 0.7` | bool | Large body relative to range. Directional conviction. Little rejection (small wicks). |
| `hammer` | `lower_wick > body * 2 and upper_wick < body` | bool | Long lower wick, small upper wick. Bullish reversal signal at bottoms. |
| `shooting_star` | `upper_wick > body * 2 and lower_wick < body` | bool | Long upper wick, small lower wick. Bearish reversal signal at tops. |

Note: `doji`, `hammer`, `shooting_star` thresholds are approximate. These are not exact definitions — different sources use different thresholds. The ratios above (0.1, 0.7, 2x) are reasonable defaults.

### 3.3 Multi-bar Patterns

| Name | Formula | Type | What it means |
|------|---------|------|---------------|
| `engulfing_bull` | `is_bullish and is_bearish[-1] and close > prev(open) and open < prev(close)` | bool | Current bullish body fully covers previous bearish body. Reversal signal. |
| `engulfing_bear` | `is_bearish and is_bullish[-1] and close < prev(open) and open > prev(close)` | bool | Current bearish body fully covers previous bullish body. |
| `two_up` | `up_day and up_day[-1]` | bool | Two consecutive up days. |
| `two_down` | `down_day and down_day[-1]` | bool | Two consecutive down days. |
| `three_up` | `up_day and up_day[-1] and up_day[-2]` | bool | Three consecutive up days. Momentum. |
| `three_down` | `down_day and down_day[-1] and down_day[-2]` | bool | Three consecutive down days. |

Note: `[-1]` notation means "previous bar's value of this metric". In practice this is `prev(up_day)`, and `[-2]` is `prev(up_day, 2)`.

---

## 4. Rolling Window Metrics

Computed over a sliding window of `n` bars. The window includes the current bar and the `n-1` previous bars.

### 4.1 Price Windows

| Name | Parameters | Formula | What it means |
|------|------------|---------|---------------|
| `sma` | col, n | `rolling_mean(close, n)` | Simple Moving Average. Smoothed price trend. |
| `highest` | col, n | `rolling_max(high, n)` | Highest high over n bars. Resistance reference. |
| `lowest` | col, n | `rolling_min(low, n)` | Lowest low over n bars. Support reference. |
| `volatility` | col, n | `rolling_std(close, n)` | Price volatility over n bars. |
| `atr` | n | `rolling_mean(true_range, n)` | Average True Range. Standard volatility measure. |
| `avg_volume` | n | `rolling_mean(volume, n)` | Average volume over n bars. Baseline for volume comparison. |
| `avg_range` | n | `rolling_mean(range, n)` | Average range over n bars. Baseline for range comparison. |

### 4.2 Window-based Conditions

| Name | Parameters | Formula | What it means |
|------|------------|---------|---------------|
| `is_nr` | n | `range == rolling_min(range, n)` | Narrowest Range of n bars. NR7 = `is_nr(7)`. Compression before expansion. |
| `is_wr` | n | `range == rolling_max(range, n)` | Widest Range of n bars. Expansion / breakout. |
| `above_sma` | n | `close > rolling_mean(close, n)` | Price above its moving average. Bullish bias. |
| `below_sma` | n | `close < rolling_mean(close, n)` | Price below its moving average. Bearish bias. |
| `high_volume` | n | `volume > rolling_mean(volume, n) * 1.5` | Volume 50%+ above average. Unusual activity. |
| `low_volume` | n | `volume < rolling_mean(volume, n) * 0.5` | Volume 50%+ below average. Quiet market. |
| `sma_cross_up` | fast, slow | `rolling_mean(close, fast) > rolling_mean(close, slow) and prev(rolling_mean(close, fast)) <= prev(rolling_mean(close, slow))` | Fast SMA crosses above slow SMA. Golden cross. |
| `sma_cross_down` | fast, slow | `rolling_mean(close, fast) < rolling_mean(close, slow) and prev(rolling_mean(close, fast)) >= prev(rolling_mean(close, slow))` | Fast SMA crosses below slow SMA. Death cross. |

### 4.3 EMA (Exponential Moving Average)

| Name | Parameters | Formula | What it means |
|------|------------|---------|---------------|
| `ema` | col, n | `ema(close, n)` | Exponential Moving Average. More weight on recent bars than SMA. Standard in trading. |
| `ema_cross_up` | fast, slow | `ema(close, fast) > ema(close, slow) and prev(ema(close, fast)) <= prev(ema(close, slow))` | Fast EMA crosses above slow. Trend change signal. |
| `ema_cross_down` | fast, slow | `ema(close, fast) < ema(close, slow) and prev(ema(close, fast)) >= prev(ema(close, slow))` | Fast EMA crosses below slow. |

Common EMA periods: 9, 12, 21, 26, 50, 200.

### 4.4 Cumulative Functions

Expanding window — from the start of the dataset to the current bar. No window size parameter.

| Name | Formula | What it means |
|------|---------|---------------|
| `cummax` | `cummax(high)` | All-time high up to this bar. |
| `cummin` | `cummin(low)` | All-time low up to this bar. |
| `drawdown` | `close / cummax(close) - 1` | How far price has fallen from peak. Always <= 0. |
| `runup` | `close / cummin(close) - 1` | How far price has risen from bottom. Always >= 0. |

### 4.5 Pattern Functions

Functions for detecting sequences and relative positioning.

| Name | Formula | What it means |
|------|---------|---------------|
| `streak(cond)` | `streak(close > prev(close))` | How many bars in a row the condition is true. Resets to 0 when false. "3 up days in a row" = streak of 3. |
| `bars_since(cond)` | `bars_since(is_nr7)` | How many bars ago the condition was last true. "10 days since last NR7." |
| `rolling_count(cond, n)` | `rolling_count(up_day, 10)` | How many times condition was true in last n bars. "7 of last 10 days were up." |
| `rank(col)` | `rank(range)` | Percentile rank within the full column. 0.95 = in the top 5%. "Today's range is unusually large." |

### 4.6 Common Window Sizes

| Size | Usage |
|------|-------|
| 5 | Trading week (5 days) |
| 7 | Calendar week |
| 10 | Two trading weeks |
| 14 | Standard for ATR, RSI |
| 20 | Trading month, standard SMA |
| 50 | Medium-term trend |
| 100 | Long-term trend |
| 200 | Major trend, institutional benchmark |

---

## 5. Time Dimensions

Properties extracted from the bar's timestamp. Used for grouping and filtering.

| Name | Type | Range | What it means |
|------|------|-------|---------------|
| `dayofweek` | int | 0-6 | Day of the week. 0=Monday, 4=Friday, 5-6=weekend. |
| `hour` | int | 0-23 | Hour of the day. |
| `day` | int | 1-31 | Day of the month. |
| `week` | int | 1-53 | ISO week number. |
| `month` | int | 1-12 | Month of the year. |
| `quarter` | int | 1-4 | Quarter. Q1=Jan-Mar, Q4=Oct-Dec. |
| `year` | int | 2008+ | Year. |
| `date` | date | — | Calendar date (no time). For joins and daily grouping. |

### Typical Groupings

| Dimension | Analysis type |
|-----------|---------------|
| `dayofweek` | "Monday vs Friday volume", "most volatile day" |
| `hour` | "hourly volume profile", "most active hour" |
| `month` | "seasonal patterns", "which month is most volatile" |
| `quarter` | "quarterly trends" |
| `year` | "year-over-year comparison" |
| `[year, month]` | "monthly breakdown per year" |
| `[year, quarter]` | "quarterly breakdown per year" |

---

## 6. Session Metrics

Sessions define time-of-day windows. Session filtering produces different daily bars depending on which session's minutes are included.

### 6.1 Session Types

Sessions are instrument-specific. For NQ:

| Session | Time (ET) | What it is |
|---------|-----------|------------|
| RTH | 09:30—17:00 | Regular Trading Hours. Most volume and liquidity. |
| ETH | 18:00—17:00 | Extended Trading Hours. Full trading day (wraps midnight). |
| OVERNIGHT | 18:00—09:30 | Overnight session. Asian + European. Lower volume. |
| ASIAN | 18:00—03:00 | Asian markets overlap. |
| EUROPEAN | 03:00—09:30 | European markets overlap. |
| MORNING | 09:30—12:30 | First half of RTH. |
| AFTERNOON | 12:30—17:00 | Second half of RTH. |
| RTH_OPEN | 09:30—10:30 | First hour. Most volatile period. Opening rotation. |
| RTH_CLOSE | 16:00—17:00 | Last hour. MOC orders, final positioning. |

### 6.2 Session-derived Metrics

When we have session-filtered data, the standard bar metrics (range, volume, etc.) become session-specific:

| Concept | How to compute | What it means |
|---------|---------------|---------------|
| RTH range | session=RTH, from=daily, range | How much price moved during regular hours. |
| Overnight range | session=OVERNIGHT, from=daily, range | How much price moved overnight. |
| Opening range | session=RTH_OPEN, from=daily, range | First hour range. Sets the tone for the day. |
| Initial Balance (IB) | session=RTH_OPEN, from=daily, high/low | High and low of first hour. Key Market Profile level. |

Note: these aren't separate metrics — they're the same `range` metric computed on session-filtered data. The session determines WHICH minutes go into the daily bar.

### 6.3 Cross-session Analysis

Comparing metrics across sessions requires running separate queries:
- Query 1: `session=RTH, from=daily, select=mean(range)` → RTH average range
- Query 2: `session=OVERNIGHT, from=daily, select=mean(range)` → overnight average range

Correlation between sessions (e.g., "does a big overnight move predict a big RTH move?") requires a more complex setup — either two queries with manual comparison, or a dedicated cross-session mechanism (see Open Questions).

---

## 7. Price Levels

Reference prices from previous periods. Used for "did price touch X?" or "how far from X?" analysis.

### 7.1 Previous Bar Levels

| Name | Formula | What it means |
|------|---------|---------------|
| `prev_close` | `prev(close)` | Yesterday's close. Most common reference level. |
| `prev_high` | `prev(high)` | Yesterday's high. Resistance. |
| `prev_low` | `prev(low)` | Yesterday's low. Support. |
| `prev_open` | `prev(open)` | Yesterday's open. |
| `prev_midpoint` | `prev(midpoint)` | Yesterday's midpoint. |
| `prev_range` | `prev(range)` | Yesterday's range. For range comparison. |

### 7.2 Level Tests

"Did today's bar touch/break a level?"

| Name | Formula | What it means |
|------|---------|---------------|
| `touched_prev_close` | `low <= prev(close) and high >= prev(close)` | Price crossed previous close during the bar. |
| `touched_prev_high` | `high >= prev(high)` | Price reached or exceeded previous high. |
| `touched_prev_low` | `low <= prev(low)` | Price reached or fell below previous low. |
| `broke_prev_high` | `close > prev(high)` | Closed above previous high. Stronger than just touching. |
| `broke_prev_low` | `close < prev(low)` | Closed below previous low. |

### 7.3 Distance from Levels

| Name | Formula | What it means |
|------|---------|---------------|
| `dist_from_high` | `highest(high, n) - close` | How far current price is from n-bar high. In points. |
| `dist_from_low` | `close - lowest(low, n)` | How far current price is from n-bar low. |
| `dist_from_high_pct` | `dist_from_high / close` | Same in percentage. |
| `dist_from_low_pct` | `dist_from_low / close` | Same in percentage. |

---

## 8. External Data

Data from outside the OHLCV series. Attached via JOIN.

### 8.1 Market Events

Regular, schedulable events that affect trading.

| Event | ID | Category | Impact | Schedule |
|-------|----|----------|--------|----------|
| FOMC Rate Decision | `fomc` | macro | high | ~8x/year |
| Non-Farm Payrolls | `nfp` | macro | high | 1st Friday |
| CPI | `cpi` | macro | high | monthly |
| PPI | `ppi` | macro | medium | monthly |
| GDP | `gdp` | macro | medium | quarterly |
| PCE | `pce` | macro | high | monthly |
| Retail Sales | `retail_sales` | macro | medium | monthly |
| Jobless Claims | `jobless_claims` | macro | low | weekly (Thu) |
| ISM Manufacturing | `ism_manufacturing` | macro | medium | 1st biz day |
| ISM Services | `ism_services` | macro | medium | 3rd biz day |
| Consumer Confidence | `consumer_confidence` | macro | medium | monthly |
| Michigan Sentiment | `michigan_sentiment` | macro | medium | monthly |
| Options Expiration | `opex` | options | medium | 3rd Friday |
| Quad Witching | `quad_witching` | options | high | 3rd Fri of Mar/Jun/Sep/Dec |
| VIX Expiration | `vix_expiration` | options | medium | Wed before 3rd Fri |

Event data columns available after JOIN:
- `event_id` — identifier (e.g., `"fomc"`)
- `event_name` — human name (e.g., `"FOMC Rate Decision"`)
- `event_category` — `"macro"` or `"options"`
- `event_impact` — `"high"`, `"medium"`, `"low"`
- `event_time` — time of release (e.g., `"14:00"`) or null

### 8.2 Holidays

Days when the market is closed or closes early.

| Type | Examples | Effect |
|------|----------|--------|
| Full close | Christmas, Thanksgiving, New Year | No trading data for this date. |
| Early close | Christmas Eve, Black Friday | Shortened session. close time from config (e.g., 13:15). |

Holiday data columns after JOIN:
- `holiday_name` — e.g., `"Christmas"`, `"Thanksgiving"`
- `day_type` — `"closed"` or `"early_close"`
- `close_time` — e.g., `"13:15"` for early close, null for full close

### 8.3 Typical Event Analysis

| Question type | How to express |
|---------------|----------------|
| "Range on FOMC days" | join events, filter event_id=fomc, metric=range |
| "Volume on OPEX" | join events, filter event_id=opex, metric=volume |
| "Range by event type" | join events, group by event_id, metric=range |
| "High impact days vs normal" | join events, filter event_impact=high, compare with no-join query |
| "Does NQ move more before or after NFP?" | Requires session-level analysis on NFP days. Two queries: morning session + afternoon session with join. |

---

## 9. Aggregations

How to summarize data. Applied to the final result.

### 9.1 Statistical Aggregations

| Name | What it does | Return type | Typical use |
|------|-------------|-------------|-------------|
| `mean` | Arithmetic average | float | Average range, average volume |
| `median` | Middle value | float | Typical value, less sensitive to outliers |
| `sum` | Total | float | Total volume |
| `count` | Number of rows | int | "How many inside days?" |
| `min` | Smallest value | float | Minimum range |
| `max` | Largest value | float | Maximum range, all-time high |
| `std` | Standard deviation | float | Volatility of a metric |
| `percentile(p)` | p-th percentile | float | "What is the 95th percentile range?" |

### 9.2 Relationship Aggregations

| Name | What it does | Return type | Typical use |
|------|-------------|-------------|-------------|
| `correlation` | Pearson correlation between two columns | float | "Is overnight range correlated with RTH range?" |

### 9.3 Percentage / Ratio Calculations

A common pattern: "what percentage of days are X?"

This is expressed as: filter to all relevant days, add a boolean column for condition X, then `mean(condition)`. The mean of a boolean column (0/1) gives the proportion.

| Question | Expression |
|----------|------------|
| "What % of days are inside days?" | map: is_inside, select: mean(is_inside) |
| "What % of gaps fill?" | map: gap, gap_filled; where: gap != 0; select: mean(gap_filled) |
| "What % of days close above open?" | map: is_bullish, select: mean(is_bullish) |

### 9.4 Grouped Aggregations

Add `group_by` to get breakdown by dimension:

| Question | group_by | select |
|----------|----------|--------|
| "Average volume by weekday" | dayofweek | mean(volume) |
| "Average range by month" | month | mean(range) |
| "Inside day frequency by year" | year | mean(is_inside) |
| "Range by event type" | event_id | mean(range) |

---

## 10. "What Happens After X" Analysis

A common pattern: identify a condition, then look at what the NEXT bar does. This requires `next()` to access the following bar's values.

### 10.1 Pattern

1. Define the condition (e.g., NR7, inside day, FOMC)
2. Compute the next bar's metric (e.g., `next(range)`, `next(direction)`)
3. Filter to condition
4. Aggregate the next-bar metric

### 10.2 Examples

| Question | Condition | Next-bar metric | Aggregation |
|----------|-----------|-----------------|-------------|
| "Average range after NR7" | is_nr(7) | next(range) | mean |
| "Direction after inside day" | inside_bar | next(direction) | mean |
| "Range after gap up" | gap > 0 | next(range) | mean |
| "Does FOMC day predict next day?" | event_id=fomc | next(range), next(direction) | mean |
| "What happens after 3 down days?" | three_down | next(direction) | mean |
| "Range expansion after NR7" | is_nr(7) | next(range) / range | mean |

### 10.3 Multiple Look-ahead

For "what happens in the next N days", use `next(col, n)`:

| Look-ahead | Expression |
|-----------|------------|
| Next day | `next(range)` or `next(range, 1)` |
| 2 days later | `next(range, 2)` |
| 3 days later | `next(range, 3)` |

Note: `next()` on the last row(s) produces NaN, which is excluded from aggregation.

---

## 11. Complete Metric Reference

All metrics in one place, sorted by category.

### Bar Properties (from single bar)

| ID | Name | Formula | Type |
|----|------|---------|------|
| `range` | Range | `high - low` | float |
| `body` | Body | `abs(close - open)` | float |
| `upper_wick` | Upper Wick | `high - max(open, close)` | float |
| `lower_wick` | Lower Wick | `min(open, close) - low` | float |
| `midpoint` | Midpoint | `(high + low) / 2` | float |
| `typical_price` | Typical Price | `(high + low + close) / 3` | float |
| `body_pct` | Body Percentage | `body / range` | float |
| `direction` | Direction | `sign(close - open)` | int |
| `is_bullish` | Bullish | `close > open` | bool |
| `is_bearish` | Bearish | `close < open` | bool |

### Inter-bar (require prev)

| ID | Name | Formula | Type |
|----|------|---------|------|
| `change` | Price Change | `close - prev(close)` | float |
| `pct_change` | Pct Change | `change / prev(close)` | float |
| `gap` | Gap | `open - prev(close)` | float |
| `gap_pct` | Gap Pct | `gap / prev(close)` | float |
| `true_range` | True Range | `max(range, abs(high - prev(close)), abs(low - prev(close)))` | float |
| `higher_high` | Higher High | `high > prev(high)` | bool |
| `lower_low` | Lower Low | `low < prev(low)` | bool |
| `higher_low` | Higher Low | `low > prev(low)` | bool |
| `lower_high` | Lower High | `high < prev(high)` | bool |
| `gap_up` | True Gap Up | `open > prev(high)` | bool |
| `gap_down` | True Gap Down | `open < prev(low)` | bool |
| `gap_exists` | Gap Exists | `gap != 0` | bool |
| `gap_filled` | Gap Filled | `if(gap > 0, low <= prev(close), high >= prev(close))` | bool |
| `up_day` | Up Day | `close > prev(close)` | bool |
| `down_day` | Down Day | `close < prev(close)` | bool |

### Patterns (named conditions)

| ID | Name | Formula | Type |
|----|------|---------|------|
| `inside_bar` | Inside Bar | `high < prev(high) and low > prev(low)` | bool |
| `outside_bar` | Outside Bar | `high > prev(high) and low < prev(low)` | bool |
| `doji` | Doji | `body_pct < 0.1` | bool |
| `strong_body` | Strong Body | `body_pct > 0.7` | bool |
| `hammer` | Hammer | `lower_wick > body * 2 and upper_wick < body` | bool |
| `shooting_star` | Shooting Star | `upper_wick > body * 2 and lower_wick < body` | bool |
| `engulfing_bull` | Bullish Engulfing | `is_bullish and prev(is_bearish) and close > prev(open) and open < prev(close)` | bool |
| `engulfing_bear` | Bearish Engulfing | `is_bearish and prev(is_bullish) and close < prev(open) and open > prev(close)` | bool |
| `two_up` | Two Up Days | `up_day and prev(up_day)` | bool |
| `two_down` | Two Down Days | `down_day and prev(down_day)` | bool |
| `three_up` | Three Up Days | `up_day and prev(up_day) and prev(up_day, 2)` | bool |
| `three_down` | Three Down Days | `down_day and prev(down_day) and prev(down_day, 2)` | bool |

### Rolling Window (parametric)

| ID | Parameters | Formula | Type |
|----|------------|---------|------|
| `sma` | col, n | `rolling_mean(col, n)` | float |
| `highest` | col, n | `rolling_max(col, n)` | float |
| `lowest` | col, n | `rolling_min(col, n)` | float |
| `atr` | n | `rolling_mean(true_range, n)` | float |
| `avg_volume` | n | `rolling_mean(volume, n)` | float |
| `avg_range` | n | `rolling_mean(range, n)` | float |
| `volatility` | col, n | `rolling_std(col, n)` | float |
| `is_nr` | n | `range == rolling_min(range, n)` | bool |
| `is_wr` | n | `range == rolling_max(range, n)` | bool |
| `above_sma` | n | `close > rolling_mean(close, n)` | bool |
| `below_sma` | n | `close < rolling_mean(close, n)` | bool |
| `high_volume` | n | `volume > rolling_mean(volume, n) * 1.5` | bool |
| `low_volume` | n | `volume < rolling_mean(volume, n) * 0.5` | bool |

### Time Dimensions

| ID | Type | Range |
|----|------|-------|
| `dayofweek` | int | 0-6 |
| `hour` | int | 0-23 |
| `day` | int | 1-31 |
| `week` | int | 1-53 |
| `month` | int | 1-12 |
| `quarter` | int | 1-4 |
| `year` | int | 2008+ |

---

## 12. Open Questions

Things this catalog does not yet cover:

### 12.1 Cross-session Metrics

"Correlation between overnight range and RTH range" requires data from two different sessions for the same day. Current design runs one session per query. Options:
- Two separate queries + manual comparison
- A dedicated `compare_sessions` mechanism
- Allow session-specific columns (e.g., `rth_range`, `overnight_range`) within one query

### 12.2 Streak Counting

"How many consecutive up days on average?" requires counting streaks — not just detecting "3 up days" but counting arbitrary-length sequences. This is hard to express with current primitives. Options:
- Add a `streak(condition)` function that returns the length of the current streak
- Handle via cumulative sum tricks (possible but complex)
- Exclude from v1

### 12.3 Relative Rankings

"Is today's range in the top 10% historically?" requires ranking within the full dataset. Options:
- Add `rank(col)` or `pct_rank(col)` function
- Use `percentile()` in aggregation only

### 12.4 Intraday Levels within Daily Context

"Did RTH break the IB high?" requires both IB (first 30 min) and full RTH data in the same query. The current session model gives one or the other.

### 12.5 Custom Thresholds for Patterns

`doji` uses `body_pct < 0.1`. Different traders might want 0.05 or 0.15. Options:
- Parameterize: `doji(threshold)`
- Keep fixed defaults with documentation
- Allow override via config

### 12.6 ATR-relative Measurements

Traders often measure things in ATR units: "range > 2 ATR". This requires ATR as a reference metric and then comparing other values to it. Currently possible via map (`atr_14: atr(14)`, `range_vs_atr: range / atr_14`) but verbose.

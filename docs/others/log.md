Run pytest --tb=short -q
........................................................................ [ 13%]
........................................................................ [ 26%]
...............EEEEEEEEEEEEEEEEEEE.EEEEEEEEEEEEEEEE.EEEEEEEEEEEEEEEEEEEE [ 39%]
EEEEEEEEEE..E..E..E.EE.................................................. [ 52%]
........................................................................ [ 65%]
........................................................................ [ 78%]
.........................EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE..... [ 92%]
...........................................                              [100%]
==================================== ERRORS ====================================
____________________ ERROR at setup of TestMACD.test_length ____________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
______________ ERROR at setup of TestMACD.test_uses_standard_ema _______________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________ ERROR at setup of TestMACD.test_signal_is_ema_of_macd _____________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________ ERROR at setup of TestMACD.test_hist_is_macd_minus_signal ___________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
________________ ERROR at setup of TestMACD.test_custom_periods ________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________________ ERROR at setup of TestADX.test_adx_range ___________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________________ ERROR at setup of TestADX.test_di_range ____________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________________ ERROR at setup of TestADX.test_warmup_nans __________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_____________ ERROR at setup of TestADX.test_uses_wilder_smoothing _____________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestSuperTrend.test_length _________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_______________ ERROR at setup of TestSuperTrend.test_nan_warmup _______________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________ ERROR at setup of TestSuperTrend.test_direction_values ____________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________ ERROR at setup of TestSuperTrend.test_value_near_price ____________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________ ERROR at setup of TestSuperTrend.test_uptrend_below_price ___________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________________ ERROR at setup of TestSAR.test_length _____________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________________ ERROR at setup of TestSAR.test_not_all_nan __________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________________ ERROR at setup of TestSAR.test_positive ____________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________________ ERROR at setup of TestSAR.test_near_price ___________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestSAR.test_custom_params _________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________________ ERROR at setup of TestTVMatch.test_macd ____________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
________________ ERROR at setup of TestTVMatch.test_macd_signal ________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestTVMatch.test_macd_hist _________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________________ ERROR at setup of TestTVMatch.test_plus_di __________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestTVMatch.test_minus_di __________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________________ ERROR at setup of TestTVMatch.test_adx ____________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
________________ ERROR at setup of TestTVMatch.test_supertrend _________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
______________ ERROR at setup of TestTVMatch.test_supertrend_dir _______________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________________ ERROR at setup of TestTVMatch.test_sar ____________________
tests/functions/test_trend.py:24: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________ ERROR at setup of TestRSIMatch.test_rsi_matches_tradingview __________
tests/functions/test_tv_match.py:27: in daily_df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
______ ERROR at setup of TestStochKMatch.test_stoch_k_matches_tradingview ______
tests/functions/test_tv_match.py:27: in daily_df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________ ERROR at setup of TestCCIMatch.test_cci_matches_tradingview __________
tests/functions/test_tv_match.py:27: in daily_df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___ ERROR at setup of TestWilliamsRMatch.test_williams_r_matches_tradingview ___
tests/functions/test_tv_match.py:27: in daily_df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________ ERROR at setup of TestMFIMatch.test_mfi_matches_tradingview __________
tests/functions/test_tv_match.py:27: in daily_df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_____________________ ERROR at setup of TestTR.test_basic ______________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________ ERROR at setup of TestTR.test_first_bar_is_high_minus_low ___________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________________ ERROR at setup of TestATR.test_length _____________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________________ ERROR at setup of TestATR.test_positive ____________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________________ ERROR at setup of TestATR.test_nan_first_n __________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_____________ ERROR at setup of TestATR.test_uses_wilder_smoothing _____________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
________________ ERROR at setup of TestNATR.test_is_percentage _________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___ ERROR at setup of TestBollingerBands.test_upper_above_middle_above_lower ___
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________ ERROR at setup of TestBollingerBands.test_middle_is_sma ____________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_____________ ERROR at setup of TestBollingerBands.test_ddof_zero ______________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_______________ ERROR at setup of TestBollingerBands.test_width ________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_____________ ERROR at setup of TestBollingerBands.test_pctb_range _____________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________ ERROR at setup of TestBollingerBands.test_custom_mult _____________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________ ERROR at setup of TestKeltnerChannel.test_upper_above_lower __________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________ ERROR at setup of TestKeltnerChannel.test_middle_is_ema ____________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________ ERROR at setup of TestKeltnerChannel.test_width_positive ___________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
______________ ERROR at setup of TestKeltnerChannel.test_uses_atr ______________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________________ ERROR at setup of TestTVMatch.test_tr _____________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________________ ERROR at setup of TestTVMatch.test_atr ____________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________________ ERROR at setup of TestTVMatch.test_natr ____________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_______________ ERROR at setup of TestTVMatch.test_bbands_middle _______________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_______________ ERROR at setup of TestTVMatch.test_bbands_upper ________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_______________ ERROR at setup of TestTVMatch.test_bbands_lower ________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
________________ ERROR at setup of TestTVMatch.test_bbands_pctb ________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestTVMatch.test_kc_middle _________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestTVMatch.test_kc_upper __________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestTVMatch.test_kc_lower __________________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_______ ERROR at setup of TestDonchianChannel.test_upper_is_highest_high _______
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
________ ERROR at setup of TestDonchianChannel.test_lower_is_lowest_low ________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________ ERROR at setup of TestDonchianChannel.test_upper_above_lower _________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________ ERROR at setup of TestDonchianChannel.test_nan_warmup _____________
tests/functions/test_volatility.py:29: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
____________________ ERROR at setup of TestOBV.test_length _____________________
tests/functions/test_volume.py:13: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
__________________ ERROR at setup of TestVWAPDay.test_length ___________________
tests/functions/test_volume.py:13: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
___________________ ERROR at setup of TestADLine.test_length ___________________
tests/functions/test_volume.py:13: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
________________ ERROR at setup of TestVolumeRatio.test_formula ________________
tests/functions/test_volume.py:13: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_________________ ERROR at setup of TestVolumeSMA.test_formula _________________
tests/functions/test_volume.py:13: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_______________ ERROR at setup of TestVolumeSMA.test_nan_warmup ________________
tests/functions/test_volume.py:13: in df
    return load_data("NQ", "1d")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
_____________ ERROR at setup of TestValidation.test_unknown_field ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
___________ ERROR at setup of TestValidation.test_invalid_timeframe ____________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestValidation.test_invalid_limit ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
______________ ERROR at setup of TestValidation.test_empty_query _______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_ ERROR at setup of TestValidation.test_expression_errors_caught_before_execution _
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________________ ERROR at setup of TestSession.test_rth_filter _________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
__________ ERROR at setup of TestSession.test_unknown_session_warning __________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
______________ ERROR at setup of TestResample.test_daily_resample ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestResample.test_weekly_resample ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________________ ERROR at setup of TestMap.test_range _____________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_________________ ERROR at setup of TestMap.test_map_ordering __________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestWhere.test_filter_bullish_days _____________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_________________ ERROR at setup of TestWhere.test_inside_day __________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_______ ERROR at setup of TestNormalization.test_comma_separated_select ________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_______ ERROR at setup of TestNormalization.test_single_select_unchanged _______
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestGroupBy.test_volume_by_weekday _____________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
__________ ERROR at setup of TestGroupBy.test_group_by_missing_column __________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
___________ ERROR at setup of TestGroupBy.test_select_missing_column ___________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestGroupBy.test_group_with_count ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________________ ERROR at setup of TestSortLimit.test_sort_desc ________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
__________________ ERROR at setup of TestSortLimit.test_limit __________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
___________ ERROR at setup of TestSortLimit.test_sort_unknown_column ___________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
___________ ERROR at setup of TestSortLimit.test_join_field_rejected ___________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________________ ERROR at setup of TestPeriod.test_year_filter _________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________________ ERROR at setup of TestPeriod.test_month_filter ________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_______________ ERROR at setup of TestPeriod.test_open_end_range _______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________________ ERROR at setup of TestPeriod.test_month_range _________________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
___________ ERROR at setup of TestPeriod.test_invalid_period_string ____________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
____________ ERROR at setup of TestPeriod.test_invalid_period_range ____________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_________ ERROR at setup of TestPeriod.test_relative_period_last_month _________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestResponse.test_scalar_response ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
______________ ERROR at setup of TestResponse.test_table_response ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestResponse.test_metadata_fields ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
______________ ERROR at setup of TestResponse.test_error_response ______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_________ ERROR at setup of TestSpecExamples.test_average_daily_range __________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_____________ ERROR at setup of TestSpecExamples.test_gap_analysis _____________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
______________ ERROR at setup of TestSpecExamples.test_nr7_count _______________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
_________ ERROR at setup of TestSourceRows.test_scalar_has_source_rows _________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
__________ ERROR at setup of TestSourceRows.test_mean_has_source_rows __________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________ ERROR at setup of TestSourceRows.test_group_by_has_source_rows ________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________ ERROR at setup of TestSourceRows.test_no_select_returns_table _________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
________ ERROR at setup of TestSourceRows.test_source_rows_have_columns ________
tests/conftest.py:50: in nq_minute
    return load_data("NQ", "1m")
           ^^^^^^^^^^^^^^^^^^^^^
barb/data.py:22: in load_data
    raise FileNotFoundError(f"Data file not found: {path}")
E   FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
=========================== short test summary info ============================
ERROR tests/functions/test_trend.py::TestMACD::test_length - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestMACD::test_uses_standard_ema - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestMACD::test_signal_is_ema_of_macd - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestMACD::test_hist_is_macd_minus_signal - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestMACD::test_custom_periods - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestADX::test_adx_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestADX::test_di_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestADX::test_warmup_nans - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestADX::test_uses_wilder_smoothing - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSuperTrend::test_length - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSuperTrend::test_nan_warmup - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSuperTrend::test_direction_values - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSuperTrend::test_value_near_price - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSuperTrend::test_uptrend_below_price - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSAR::test_length - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSAR::test_not_all_nan - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSAR::test_positive - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSAR::test_near_price - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestSAR::test_custom_params - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_macd - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_macd_signal - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_macd_hist - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_plus_di - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_minus_di - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_adx - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_supertrend - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_supertrend_dir - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_trend.py::TestTVMatch::test_sar - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_tv_match.py::TestRSIMatch::test_rsi_matches_tradingview - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_tv_match.py::TestStochKMatch::test_stoch_k_matches_tradingview - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_tv_match.py::TestCCIMatch::test_cci_matches_tradingview - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_tv_match.py::TestWilliamsRMatch::test_williams_r_matches_tradingview - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_tv_match.py::TestMFIMatch::test_mfi_matches_tradingview - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTR::test_basic - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTR::test_first_bar_is_high_minus_low - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestATR::test_length - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestATR::test_positive - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestATR::test_nan_first_n - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestATR::test_uses_wilder_smoothing - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestNATR::test_is_percentage - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestBollingerBands::test_upper_above_middle_above_lower - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestBollingerBands::test_middle_is_sma - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestBollingerBands::test_ddof_zero - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestBollingerBands::test_width - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestBollingerBands::test_pctb_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestBollingerBands::test_custom_mult - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestKeltnerChannel::test_upper_above_lower - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestKeltnerChannel::test_middle_is_ema - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestKeltnerChannel::test_width_positive - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestKeltnerChannel::test_uses_atr - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_tr - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_atr - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_natr - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_bbands_middle - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_bbands_upper - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_bbands_lower - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_bbands_pctb - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_kc_middle - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_kc_upper - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestTVMatch::test_kc_lower - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestDonchianChannel::test_upper_is_highest_high - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestDonchianChannel::test_lower_is_lowest_low - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestDonchianChannel::test_upper_above_lower - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volatility.py::TestDonchianChannel::test_nan_warmup - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volume.py::TestOBV::test_length - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volume.py::TestVWAPDay::test_length - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volume.py::TestADLine::test_length - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volume.py::TestVolumeRatio::test_formula - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volume.py::TestVolumeSMA::test_formula - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/functions/test_volume.py::TestVolumeSMA::test_nan_warmup - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1d/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestValidation::test_unknown_field - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestValidation::test_invalid_timeframe - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestValidation::test_invalid_limit - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestValidation::test_empty_query - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestValidation::test_expression_errors_caught_before_execution - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSession::test_rth_filter - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSession::test_unknown_session_warning - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestResample::test_daily_resample - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestResample::test_weekly_resample - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestMap::test_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestMap::test_map_ordering - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestWhere::test_filter_bullish_days - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestWhere::test_inside_day - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestNormalization::test_comma_separated_select - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestNormalization::test_single_select_unchanged - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestGroupBy::test_volume_by_weekday - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestGroupBy::test_group_by_missing_column - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestGroupBy::test_select_missing_column - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestGroupBy::test_group_with_count - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSortLimit::test_sort_desc - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSortLimit::test_limit - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSortLimit::test_sort_unknown_column - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSortLimit::test_join_field_rejected - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestPeriod::test_year_filter - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestPeriod::test_month_filter - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestPeriod::test_open_end_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestPeriod::test_month_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestPeriod::test_invalid_period_string - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestPeriod::test_invalid_period_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestPeriod::test_relative_period_last_month - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestResponse::test_scalar_response - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestResponse::test_table_response - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestResponse::test_metadata_fields - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestResponse::test_error_response - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSpecExamples::test_average_daily_range - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSpecExamples::test_gap_analysis - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSpecExamples::test_nr7_count - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSourceRows::test_scalar_has_source_rows - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSourceRows::test_mean_has_source_rows - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSourceRows::test_group_by_has_source_rows - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSourceRows::test_no_select_returns_table - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
ERROR tests/test_interpreter.py::TestSourceRows::test_source_rows_have_columns - FileNotFoundError: Data file not found: /home/runner/work/barb/barb/data/1m/futures/NQ.parquet
435 passed, 112 errors in 3.36s
Error: Process completed with exit code 1.
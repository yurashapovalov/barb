"""Tests for session-aware functions."""

import pandas as pd
import pytest

from barb.functions.session import (
    _session_close,
    _session_high,
    _session_id,
    _session_low,
    _session_open,
)


@pytest.fixture
def two_sessions():
    """Two RTH sessions of hourly data with an overnight gap."""
    index = pd.DatetimeIndex(
        [
            # Session 1
            "2024-01-10 09:00",
            "2024-01-10 10:00",
            "2024-01-10 11:00",
            "2024-01-10 12:00",
            "2024-01-10 13:00",
            "2024-01-10 14:00",
            "2024-01-10 15:00",
            # Session 2 — overnight gap
            "2024-01-11 09:00",
            "2024-01-11 10:00",
            "2024-01-11 11:00",
            "2024-01-11 12:00",
            "2024-01-11 13:00",
            "2024-01-11 14:00",
            "2024-01-11 15:00",
        ]
    )
    return pd.DataFrame(
        {
            "open": [100, 102, 105, 103, 104, 106, 107, 110, 112, 108, 109, 111, 113, 114],
            "high": [103, 106, 108, 105, 107, 109, 108, 113, 115, 112, 111, 114, 116, 115],
            "low": [99, 101, 104, 102, 103, 105, 106, 109, 111, 107, 108, 110, 112, 113],
            "close": [102, 105, 103, 104, 106, 107, 106, 112, 108, 109, 111, 113, 114, 114],
            "volume": [100] * 14,
        },
        index=index,
    )


class TestSessionId:
    def test_two_sessions_detected(self, two_sessions):
        sid = _session_id(two_sessions)
        # First session = 0, second session = 1
        assert sid.iloc[0] == 0
        assert sid.iloc[6] == 0  # last bar of session 1
        assert sid.iloc[7] == 1  # first bar of session 2
        assert sid.iloc[13] == 1

    def test_single_session(self, two_sessions):
        """Single session has all same IDs."""
        session1 = two_sessions.iloc[:7]
        sid = _session_id(session1)
        assert sid.nunique() == 1


class TestSessionHigh:
    def test_session_high_per_session(self, two_sessions):
        sh = _session_high(two_sessions)
        # Session 1: max high = 109 (at 14:00)
        assert sh.iloc[0] == 109
        assert sh.iloc[6] == 109
        # Session 2: max high = 116 (at 13:00)
        assert sh.iloc[7] == 116
        assert sh.iloc[13] == 116

    def test_session_high_does_not_cross_boundary(self, two_sessions):
        """Session 2 high (116) must not appear in session 1."""
        sh = _session_high(two_sessions)
        for i in range(7):  # session 1 bars
            assert sh.iloc[i] == 109, f"Bar {i} should see session 1 high"

    def test_find_bar_with_session_high(self, two_sessions):
        """high == session_high() finds the exact bar."""
        sh = _session_high(two_sessions)
        is_high = two_sessions["high"] == sh
        # Session 1: high=109 at index 5 (14:00)
        assert is_high.iloc[5]
        # Session 2: high=116 at index 12 (13:00)
        assert is_high.iloc[12]


class TestSessionLow:
    def test_session_low_per_session(self, two_sessions):
        sl = _session_low(two_sessions)
        # Session 1: min low = 99 (at 09:00)
        assert sl.iloc[0] == 99
        assert sl.iloc[6] == 99
        # Session 2: min low = 107 (at 11:00)
        assert sl.iloc[7] == 107
        assert sl.iloc[13] == 107

    def test_session_low_does_not_cross_boundary(self, two_sessions):
        """Session 1 low (99) must not appear in session 2."""
        sl = _session_low(two_sessions)
        for i in range(7, 14):  # session 2 bars
            assert sl.iloc[i] == 107, f"Bar {i} should see session 2 low"


class TestSessionOpenClose:
    def test_session_open(self, two_sessions):
        so = _session_open(two_sessions)
        # Session 1: first open = 100
        assert so.iloc[0] == 100
        assert so.iloc[6] == 100
        # Session 2: first open = 110
        assert so.iloc[7] == 110
        assert so.iloc[13] == 110

    def test_session_close(self, two_sessions):
        sc = _session_close(two_sessions)
        # Session 1: last close = 106
        assert sc.iloc[0] == 106
        assert sc.iloc[6] == 106
        # Session 2: last close = 114
        assert sc.iloc[7] == 114
        assert sc.iloc[13] == 114


class TestETHSessionBoundaries:
    """ETH sessions span midnight: 18:00 → 17:00 next day.

    CME halt is only 60 min (17:00-18:00), so gap detection (>90 min)
    merges consecutive days. __session_id from config fixes this.
    """

    @pytest.fixture
    def two_eth_sessions(self):
        """Two ETH sessions with 60-min halt between them.

        Session 1: Mon 18:00 → Tue 16:00
        Session 2: Tue 18:00 → Wed 16:00
        """
        from barb.ops import add_session_id

        index = pd.DatetimeIndex(
            [
                # Session 1 (Monday evening → Tuesday afternoon)
                "2024-01-08 18:00",
                "2024-01-08 21:00",
                "2024-01-09 03:00",
                "2024-01-09 09:00",
                "2024-01-09 12:00",
                "2024-01-09 16:00",
                # 60-min halt: 17:00-18:00 — NOT detected by 90-min gap
                # Session 2 (Tuesday evening → Wednesday afternoon)
                "2024-01-09 18:00",
                "2024-01-09 21:00",
                "2024-01-10 03:00",
                "2024-01-10 09:00",
                "2024-01-10 12:00",
                "2024-01-10 16:00",
            ]
        )
        df = pd.DataFrame(
            {
                "open": [100, 102, 104, 106, 108, 110, 200, 202, 204, 206, 208, 210],
                "high": [105, 107, 109, 111, 113, 115, 205, 207, 209, 211, 213, 215],
                "low": [98, 100, 102, 104, 106, 108, 198, 200, 202, 204, 206, 208],
                "close": [102, 104, 106, 108, 110, 112, 202, 204, 206, 208, 210, 212],
                "volume": [100] * 12,
            },
            index=index,
        )
        return add_session_id(df, ("18:00", "17:00"))

    def test_gap_detection_fails_for_eth(self):
        """Without __session_id, 60-min halt is not detected."""
        index = pd.DatetimeIndex(
            [
                # Session 1: last hour before halt
                "2024-01-09 16:00",
                "2024-01-09 16:30",
                # 60-min halt: 17:00-18:00 — gap = 60 min < 90 min threshold
                # Session 2: first hour after halt
                "2024-01-09 18:00",
                "2024-01-09 18:30",
            ]
        )
        df = pd.DataFrame(
            {
                "open": [100, 110, 200, 210],
                "high": [115, 115, 215, 215],
                "low": [98, 108, 198, 208],
                "close": [112, 112, 212, 212],
                "volume": [100] * 4,
            },
            index=index,
        )
        # Gap detection merges both days into one session — wrong!
        sid = _session_id(df)
        assert sid.nunique() == 1  # bug: should be 2

    def test_session_id_from_config_separates_eth(self, two_eth_sessions):
        """With __session_id from config, ETH sessions are correctly separated."""
        sid = _session_id(two_eth_sessions)
        assert sid.nunique() == 2
        # Session 1: bars 0-5, Session 2: bars 6-11
        assert sid.iloc[0] == sid.iloc[5]  # same session
        assert sid.iloc[0] != sid.iloc[6]  # different sessions

    def test_session_high_with_eth(self, two_eth_sessions):
        sh = _session_high(two_eth_sessions)
        # Session 1: max high = 115 (at 16:00)
        assert sh.iloc[0] == 115
        assert sh.iloc[5] == 115
        # Session 2: max high = 215 (at 16:00)
        assert sh.iloc[6] == 215
        assert sh.iloc[11] == 215
        # Session 2 high must NOT leak into session 1
        assert sh.iloc[5] != 215

    def test_session_low_with_eth(self, two_eth_sessions):
        sl = _session_low(two_eth_sessions)
        # Session 1: min low = 98
        assert sl.iloc[0] == 98
        assert sl.iloc[5] == 98
        # Session 2: min low = 198
        assert sl.iloc[6] == 198
        assert sl.iloc[11] == 198

    def test_session_open_close_with_eth(self, two_eth_sessions):
        so = _session_open(two_eth_sessions)
        sc = _session_close(two_eth_sessions)
        # Session 1: open=100 (Mon 18:00), close=112 (Tue 16:00)
        assert so.iloc[0] == 100
        assert sc.iloc[5] == 112
        # Session 2: open=200 (Tue 18:00), close=212 (Wed 16:00)
        assert so.iloc[6] == 200
        assert sc.iloc[11] == 212

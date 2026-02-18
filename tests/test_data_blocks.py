"""Tests for data block format — typed blocks for frontend rendering."""

from datetime import date

from assistant.chat import _build_query_card
from assistant.tools.backtest import _build_backtest_card
from barb.backtest.metrics import BacktestResult, Trade, build_equity_curve, calculate_metrics


def _make_trades():
    """3 trades: win, loss, win."""
    return [
        Trade(
            date(2024, 1, 15), 18000.0, date(2024, 1, 16), 18100.0, "long", 100.0, "take_profit", 1
        ),
        Trade(date(2024, 1, 22), 18200.0, date(2024, 1, 23), 18150.0, "long", -50.0, "stop", 1),
        Trade(date(2024, 2, 5), 18100.0, date(2024, 2, 7), 18180.0, "long", 80.0, "timeout", 2),
    ]


def _make_result(trades=None):
    trades = _make_trades() if trades is None else trades
    metrics = calculate_metrics(trades)
    equity_curve = build_equity_curve(trades)
    return BacktestResult(trades=trades, metrics=metrics, equity_curve=equity_curve)


class TestBuildQueryCard:
    """_build_query_card converts run_query result into typed DataCard."""

    def test_returns_none_when_no_data(self):
        result = {"model_response": "Result: 42", "table": None, "source_rows": None, "chart": None}
        card = _build_query_card(result, "Test")
        assert card is None

    def test_table_block_from_table_data(self):
        result = {
            "model_response": "Result: 2 rows",
            "table": [
                {"date": "2024-01-15", "close": 18450},
                {"date": "2024-01-16", "close": 18500},
            ],
            "source_rows": None,
            "chart": None,
        }
        card = _build_query_card(result, "Price data")
        assert card["title"] == "Price data"
        assert len(card["blocks"]) == 1
        assert card["blocks"][0]["type"] == "table"
        assert card["blocks"][0]["columns"] == ["date", "close"]
        assert len(card["blocks"][0]["rows"]) == 2

    def test_table_block_from_source_rows(self):
        """When table is None, source_rows become the table."""
        result = {
            "model_response": "Result: 5",
            "table": None,
            "source_rows": [
                {"date": "2024-01-15", "close": 18450},
            ],
            "chart": None,
        }
        card = _build_query_card(result, "Count query")
        assert len(card["blocks"]) == 1
        assert card["blocks"][0]["type"] == "table"
        assert len(card["blocks"][0]["rows"]) == 1

    def test_bar_chart_block_when_chart_hint(self):
        """Grouped results with chart hint → bar-chart + table."""
        rows = [
            {"dow": "Mon", "mean_r": 150.3},
            {"dow": "Tue", "mean_r": 142.1},
        ]
        result = {
            "model_response": "Result: 2 groups",
            "table": rows,
            "source_rows": None,
            "chart": {"category": "dow", "value": "mean_r"},
        }
        card = _build_query_card(result, "Range by day")
        assert len(card["blocks"]) == 2
        # First block: bar-chart
        assert card["blocks"][0]["type"] == "bar-chart"
        assert card["blocks"][0]["category_key"] == "dow"
        assert card["blocks"][0]["value_key"] == "mean_r"
        assert card["blocks"][0]["rows"] == rows
        # Second block: table
        assert card["blocks"][1]["type"] == "table"
        assert card["blocks"][1]["rows"] == rows

    def test_columns_from_first_row_keys(self):
        result = {
            "model_response": "Result: 1 row",
            "table": [{"date": "2024-01-15", "close": 18450, "rsi": 28.5}],
            "source_rows": None,
            "chart": None,
        }
        card = _build_query_card(result, "RSI data")
        assert card["blocks"][0]["columns"] == ["date", "close", "rsi"]

    def test_empty_table(self):
        """Empty list → no card (nothing to render)."""
        result = {
            "model_response": "Result: 0 rows",
            "table": [],
            "source_rows": None,
            "chart": None,
        }
        card = _build_query_card(result, "Empty")
        assert card is None


class TestBuildBacktestCard:
    """_build_backtest_card converts BacktestResult into typed DataCard."""

    def test_four_blocks(self):
        """Standard result → 4 blocks: metrics-grid, area-chart, horizontal-bar, table."""
        card = _build_backtest_card(_make_result(), "RSI Strategy")
        assert card["title"] == "RSI Strategy · 3 trades"
        assert len(card["blocks"]) == 4
        types = [b["type"] for b in card["blocks"]]
        assert types == ["metrics-grid", "area-chart", "horizontal-bar", "table"]

    def test_metrics_grid_values(self):
        card = _build_backtest_card(_make_result(), "Test")
        grid = card["blocks"][0]
        assert grid["type"] == "metrics-grid"
        labels = [item["label"] for item in grid["items"]]
        assert "Trades" in labels
        assert "Win Rate" in labels
        assert "PF" in labels
        assert "Total P&L" in labels
        # Find trades item
        trades_item = next(i for i in grid["items"] if i["label"] == "Trades")
        assert trades_item["value"] == "3"
        # P&L is positive → green
        pnl_item = next(i for i in grid["items"] if i["label"] == "Total P&L")
        assert pnl_item["color"] == "green"

    def test_area_chart_equity_and_drawdown(self):
        card = _build_backtest_card(_make_result(), "Test")
        chart = card["blocks"][1]
        assert chart["type"] == "area-chart"
        assert chart["x_key"] == "date"
        assert len(chart["series"]) == 2
        assert len(chart["data"]) == 3
        # First trade: +100 → equity=100, drawdown=0
        assert chart["data"][0]["equity"] == 100.0
        assert chart["data"][0]["drawdown"] == 0.0
        assert chart["data"][0]["date"] == "2024-01-16"
        # Second trade: -50 → equity=50, drawdown=-50
        assert chart["data"][1]["equity"] == 50.0
        assert chart["data"][1]["drawdown"] == -50.0
        # Third trade: +80 → equity=130, drawdown=0 (new peak)
        assert chart["data"][2]["equity"] == 130.0
        assert chart["data"][2]["drawdown"] == 0.0

    def test_horizontal_bar_exits(self):
        card = _build_backtest_card(_make_result(), "Test")
        hbar = card["blocks"][2]
        assert hbar["type"] == "horizontal-bar"
        # 3 exit types: take_profit (+100), timeout (+80), stop (-50)
        assert len(hbar["items"]) == 3
        # Sorted by pnl descending
        assert hbar["items"][0]["label"] == "Take Profit"
        assert hbar["items"][0]["value"] == 100.0
        assert "W:1 L:0" in hbar["items"][0]["detail"]
        assert hbar["items"][-1]["label"] == "Stop"
        assert hbar["items"][-1]["value"] == -50.0

    def test_table_trades(self):
        card = _build_backtest_card(_make_result(), "Test")
        table = card["blocks"][3]
        assert table["type"] == "table"
        assert len(table["rows"]) == 3
        assert table["columns"][0] == "entry_date"
        assert table["rows"][0]["entry_date"] == "2024-01-15"
        assert table["rows"][0]["pnl"] == 100.0
        assert table["rows"][0]["exit_reason"] == "take_profit"

    def test_zero_trades(self):
        """Zero trades → single metrics-grid block with Trades=0."""
        result = _make_result(trades=[])
        card = _build_backtest_card(result, "Empty")
        assert card["title"] == "Empty"
        assert len(card["blocks"]) == 1
        assert card["blocks"][0]["type"] == "metrics-grid"
        assert card["blocks"][0]["items"][0]["value"] == "0"

    def test_negative_pnl_color(self):
        """Losing strategy → P&L colored red."""
        trades = [
            Trade(
                date(2024, 1, 15), 18000.0, date(2024, 1, 16), 17900.0, "long", -100.0, "stop", 1
            ),
        ]
        card = _build_backtest_card(_make_result(trades), "Losing")
        pnl_item = next(i for i in card["blocks"][0]["items"] if i["label"] == "Total P&L")
        assert pnl_item["color"] == "red"

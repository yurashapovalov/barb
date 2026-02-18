"""Tests for data block format — typed blocks for frontend rendering."""

from assistant.chat import _build_query_card


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

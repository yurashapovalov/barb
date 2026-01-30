"""Tests for api/main.py — endpoints and helpers."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import _parse_tool_output, app

# --- _parse_tool_output (pure function) ---


class TestParseToolOutput:
    def test_none(self):
        assert _parse_tool_output(None) is None

    def test_dict_passthrough(self):
        d = {"key": "value"}
        assert _parse_tool_output(d) == d

    def test_list_passthrough(self):
        lst = [1, 2, 3]
        assert _parse_tool_output(lst) == lst

    def test_json_string(self):
        result = _parse_tool_output('{"rows": 5, "data": [1, 2]}')
        assert result == {"rows": 5, "data": [1, 2]}

    def test_json_array_string(self):
        result = _parse_tool_output('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_non_json_string(self):
        result = _parse_tool_output("just plain text")
        assert result == {"raw": "just plain text"}

    def test_number(self):
        result = _parse_tool_output(42)
        assert result == {"raw": "42"}


# --- API Endpoints (with mocked DB and auth) ---

MOCK_USER = {"sub": "user-abc-123", "aud": "authenticated"}


def _mock_user_override():
    return MOCK_USER


@pytest.fixture
def client():
    """TestClient with mocked auth."""
    from api.auth import get_current_user

    app.dependency_overrides[get_current_user] = _mock_user_override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mock_table_chain(data):
    """Create a mock that supports fluent .table().select().eq().execute() chains."""
    mock = MagicMock()
    result = MagicMock()
    result.data = data
    # Every method call returns the same mock (fluent API), execute() returns result
    mock.insert.return_value = mock
    mock.select.return_value = mock
    mock.eq.return_value = mock
    mock.order.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.execute.return_value = result
    return mock


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestCreateConversation:
    def test_success(self, client):
        row = {
            "id": "conv-1",
            "title": "New conversation",
            "instrument": "NQ",
            "usage": {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0,
                      "cached_tokens": 0, "input_cost": 0, "output_cost": 0,
                      "thinking_cost": 0, "total_cost": 0, "message_count": 0},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([row])

        with patch("api.main.get_db", return_value=mock_db):
            r = client.post("/api/conversations", json={"instrument": "NQ"})

        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "conv-1"
        assert data["title"] == "New conversation"
        assert data["instrument"] == "NQ"

    def test_unknown_instrument(self, client):
        r = client.post("/api/conversations", json={"instrument": "UNKNOWN"})
        assert r.status_code == 400


class TestListConversations:
    def test_success(self, client):
        rows = [
            {
                "id": "conv-1",
                "title": "First chat",
                "instrument": "NQ",
                "usage": {"input_tokens": 100, "output_tokens": 50, "thinking_tokens": 0,
                          "cached_tokens": 0, "input_cost": 0, "output_cost": 0,
                          "thinking_cost": 0, "total_cost": 0, "message_count": 1},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ]
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain(rows)

        with patch("api.main.get_db", return_value=mock_db):
            r = client.get("/api/conversations")

        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == "conv-1"

    def test_empty(self, client):
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([])

        with patch("api.main.get_db", return_value=mock_db):
            r = client.get("/api/conversations")

        assert r.status_code == 200
        assert r.json() == []


class TestDeleteConversation:
    def test_success(self, client):
        mock_db = MagicMock()
        check_chain = _mock_table_chain([{"id": "conv-1"}])
        delete_chain = _mock_table_chain([])

        call_count = 0

        def table_side_effect(name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return check_chain  # ownership check
            return delete_chain  # delete

        mock_db.table.side_effect = table_side_effect

        with patch("api.main.get_db", return_value=mock_db):
            r = client.delete("/api/conversations/conv-1")

        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_not_found(self, client):
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([])  # empty = not found

        with patch("api.main.get_db", return_value=mock_db):
            r = client.delete("/api/conversations/nonexistent")

        assert r.status_code == 404


class TestChat:
    def _make_conversation(self):
        return {
            "id": "conv-1",
            "user_id": MOCK_USER["sub"],
            "title": "New conversation",
            "instrument": "NQ",
            "usage": {
                "input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0,
                "cached_tokens": 0, "input_cost": 0, "output_cost": 0,
                "thinking_cost": 0, "total_cost": 0, "message_count": 0,
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

    def _make_assistant_result(self):
        return {
            "answer": "The average range is 150 points.",
            "data": [{"query": {"select": "range"}, "result": 150, "rows": 1,
                       "session": "RTH", "timeframe": None}],
            "usage": {
                "input_tokens": 500, "output_tokens": 200, "thinking_tokens": 0,
                "cached_tokens": 100, "input_cost": 0.0001, "output_cost": 0.0002,
                "thinking_cost": 0.0, "total_cost": 0.0003,
            },
            "tool_calls": [
                {"tool_name": "execute_query", "input": {"query": {"select": "range"}},
                 "output": json.dumps({"result": 150}), "error": None, "duration_ms": 45},
            ],
        }

    def test_success(self, client):
        conversation = self._make_conversation()
        assistant_result = self._make_assistant_result()

        # Mock DB: returns conversation, then messages, then handles writes
        mock_db = MagicMock()
        call_count = 0

        def table_side_effect(name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Load conversation
                return _mock_table_chain([conversation])
            elif call_count == 2:
                # Load messages (empty history)
                return _mock_table_chain([])
            elif call_count == 3:
                # Write user message
                return _mock_table_chain([{"id": "msg-user-1"}])
            elif call_count == 4:
                # Write model message
                return _mock_table_chain([{"id": "msg-model-1"}])
            elif call_count == 5:
                # Write tool calls
                return _mock_table_chain([])
            else:
                # Update conversation
                return _mock_table_chain([])

        mock_db.table.side_effect = table_side_effect

        mock_assistant = MagicMock()
        mock_assistant.chat.return_value = assistant_result

        with (
            patch("api.main.get_db", return_value=mock_db),
            patch("api.main._get_assistant", return_value=mock_assistant),
        ):
            r = client.post("/api/chat", json={
                "conversation_id": "conv-1",
                "message": "What is the average daily range?",
            })

        assert r.status_code == 200
        data = r.json()
        assert data["answer"] == "The average range is 150 points."
        assert data["message_id"] == "msg-model-1"
        assert data["conversation_id"] == "conv-1"
        assert data["persisted"] is True
        assert len(data["tool_calls"]) == 1

    def test_conversation_not_found(self, client):
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([])

        with patch("api.main.get_db", return_value=mock_db):
            r = client.post("/api/chat", json={
                "conversation_id": "nonexistent",
                "message": "hello",
            })

        assert r.status_code == 404

    def test_missing_message(self, client):
        r = client.post("/api/chat", json={"conversation_id": "conv-1"})
        assert r.status_code == 422  # validation error

    def test_missing_conversation_id(self, client):
        r = client.post("/api/chat", json={"message": "hello"})
        assert r.status_code == 422

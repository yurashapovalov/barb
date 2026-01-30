"""Tests for backend foundation: Request ID, Health Check, Structured Errors."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

MOCK_USER = {"sub": "user-abc-123", "aud": "authenticated"}


def _mock_user_override():
    return MOCK_USER


@pytest.fixture
def client():
    from api.auth import get_current_user

    app.dependency_overrides[get_current_user] = _mock_user_override
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _mock_table_chain(data):
    mock = MagicMock()
    result = MagicMock()
    result.data = data
    mock.insert.return_value = mock
    mock.select.return_value = mock
    mock.eq.return_value = mock
    mock.order.return_value = mock
    mock.limit.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.execute.return_value = result
    return mock


# --- Request ID ---


class TestRequestId:
    def test_response_contains_request_id(self, client):
        r = client.get("/health")
        assert "x-request-id" in r.headers
        assert len(r.headers["x-request-id"]) > 0

    def test_client_provided_request_id(self, client):
        r = client.get("/health", headers={"X-Request-Id": "custom-123"})
        assert r.headers["x-request-id"] == "custom-123"

    def test_generated_request_id_is_uuid(self, client):
        import uuid

        r = client.get("/health")
        rid = r.headers["x-request-id"]
        # Should be a valid UUID
        uuid.UUID(rid)


# --- Structured Errors ---


class TestStructuredErrors:
    def test_404_format(self, client):
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([])

        with patch("api.main.get_db", return_value=mock_db):
            r = client.delete("/api/conversations/nonexistent")

        assert r.status_code == 404
        data = r.json()
        assert data["error"] == "Conversation not found"
        assert data["code"] == "NOT_FOUND"
        assert "request_id" in data

    def test_422_format(self, client):
        r = client.post("/api/chat", json={"conversation_id": "conv-1"})
        assert r.status_code == 422
        data = r.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "request_id" in data

    def test_400_format(self, client):
        r = client.post("/api/conversations", json={"instrument": "UNKNOWN"})
        assert r.status_code == 400
        data = r.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "request_id" in data

    def test_error_includes_client_request_id(self, client):
        r = client.post(
            "/api/chat",
            json={"conversation_id": "conv-1"},
            headers={"X-Request-Id": "trace-abc"},
        )
        data = r.json()
        assert data["request_id"] == "trace-abc"


# --- Health Check ---


class TestHealthCheck:
    def test_all_ok(self, client):
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([])

        mock_settings = MagicMock()
        mock_settings.gemini_api_key = "test-key"

        with (
            patch("api.main.get_db", return_value=mock_db),
            patch("api.main.get_settings", return_value=mock_settings),
            patch("api.main.DATA_DIR") as mock_dir,
        ):
            mock_dir.__truediv__ = lambda self, key: MagicMock(exists=lambda: True)
            r = client.get("/health")

        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["checks"]["supabase"] == "ok"
        assert data["checks"]["gemini"] == "ok"
        assert data["checks"]["data"] == "ok"

    def test_supabase_fail(self, client):
        mock_db = MagicMock()
        mock_db.table.side_effect = Exception("connection refused")

        mock_settings = MagicMock()
        mock_settings.gemini_api_key = "test-key"

        with (
            patch("api.main.get_db", return_value=mock_db),
            patch("api.main.get_settings", return_value=mock_settings),
            patch("api.main.DATA_DIR") as mock_dir,
        ):
            mock_dir.__truediv__ = lambda self, key: MagicMock(exists=lambda: True)
            r = client.get("/health")

        assert r.status_code == 503
        data = r.json()
        assert data["status"] == "fail"
        assert data["checks"]["supabase"] == "fail"
        assert data["checks"]["gemini"] == "ok"

    def test_gemini_key_missing(self, client):
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([])

        mock_settings = MagicMock()
        mock_settings.gemini_api_key = ""

        with (
            patch("api.main.get_db", return_value=mock_db),
            patch("api.main.get_settings", return_value=mock_settings),
            patch("api.main.DATA_DIR") as mock_dir,
        ):
            mock_dir.__truediv__ = lambda self, key: MagicMock(exists=lambda: True)
            r = client.get("/health")

        assert r.status_code == 503
        data = r.json()
        assert data["checks"]["gemini"] == "fail"

    def test_data_file_missing(self, client):
        mock_db = MagicMock()
        mock_db.table.return_value = _mock_table_chain([])

        mock_settings = MagicMock()
        mock_settings.gemini_api_key = "test-key"

        with (
            patch("api.main.get_db", return_value=mock_db),
            patch("api.main.get_settings", return_value=mock_settings),
            patch("api.main.DATA_DIR") as mock_dir,
        ):
            mock_dir.__truediv__ = lambda self, key: MagicMock(exists=lambda: False)
            r = client.get("/health")

        assert r.status_code == 503
        data = r.json()
        assert data["checks"]["data"] == "fail"

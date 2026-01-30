"""Tests for api/auth.py — JWT validation."""

import time
from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException

from api.auth import get_current_user

TEST_SECRET = "test-jwt-secret-for-unit-tests"


def _make_request(token: str | None = None):
    """Create a mock Request with Authorization header."""

    class MockRequest:
        def __init__(self, headers):
            self._headers = headers

        @property
        def headers(self):
            return self._headers

    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return MockRequest(headers)


def _make_token(payload: dict, secret: str = TEST_SECRET) -> str:
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(autouse=True)
def _mock_settings():
    """Mock get_settings to return test secret."""

    class FakeSettings:
        supabase_jwt_secret = TEST_SECRET

    with patch("api.auth.get_settings", return_value=FakeSettings()):
        yield


class TestGetCurrentUser:
    def test_valid_token(self):
        token = _make_token({"sub": "user-123", "aud": "authenticated"})
        user = get_current_user(_make_request(token))
        assert user["sub"] == "user-123"

    def test_missing_header(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request())
        assert exc_info.value.status_code == 401
        assert "Missing" in exc_info.value.detail

    def test_no_bearer_prefix(self):
        request = _make_request()
        request._headers["Authorization"] = "Basic abc123"
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)
        assert exc_info.value.status_code == 401

    def test_expired_token(self):
        token = _make_token({
            "sub": "user-123",
            "aud": "authenticated",
            "exp": int(time.time()) - 3600,  # expired 1h ago
        })
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request(token))
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request("not-a-valid-jwt"))
        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail

    def test_wrong_secret(self):
        token = _make_token(
            {"sub": "user-123", "aud": "authenticated"},
            secret="wrong-secret",
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request(token))
        assert exc_info.value.status_code == 401

    def test_wrong_audience(self):
        token = _make_token({"sub": "user-123", "aud": "wrong-audience"})
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request(token))
        assert exc_info.value.status_code == 401

"""Tests for api/auth.py — JWT validation."""

import time
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

import api.auth
from api.auth import get_current_user

# Generate a test ES256 key pair
_private_key = ec.generate_private_key(ec.SECP256R1())
_public_key = _private_key.public_key()


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


def _make_token(payload: dict, key=_private_key) -> str:
    return jwt.encode(payload, key, algorithm="ES256")


@pytest.fixture(autouse=True)
def _mock_jwks():
    """Mock JWKS client to return our test public key."""
    # Reset cached client between tests
    api.auth._jwks_client = None

    mock_signing_key = MagicMock()
    mock_signing_key.key = _public_key

    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.return_value = mock_signing_key

    with patch("api.auth._get_jwks_client", return_value=mock_client):
        yield mock_client


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

    def test_invalid_token(self, _mock_jwks):
        # JWKS client raises when token is garbage
        _mock_jwks.get_signing_key_from_jwt.side_effect = jwt.InvalidTokenError
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request("not-a-valid-jwt"))
        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail

    def test_wrong_key(self):
        wrong_key = ec.generate_private_key(ec.SECP256R1())
        token = _make_token(
            {"sub": "user-123", "aud": "authenticated"},
            key=wrong_key,
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request(token))
        assert exc_info.value.status_code == 401

    def test_wrong_audience(self):
        token = _make_token({"sub": "user-123", "aud": "wrong-audience"})
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_make_request(token))
        assert exc_info.value.status_code == 401

"""Supabase JWT validation."""

import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient

from api.config import get_settings

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = f"{get_settings().supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(url, cache_keys=True)
    return _jwks_client


def get_current_user(request: Request) -> dict:
    """Validate Supabase JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization token")

    token = auth[7:]
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    except (jwt.PyJWKClientError, jwt.InvalidTokenError):
        raise HTTPException(401, "Invalid token")

    try:
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

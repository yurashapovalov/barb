"""Supabase JWT validation."""

import jwt
from fastapi import HTTPException, Request

from api.config import get_settings


def get_current_user(request: Request) -> dict:
    """Validate Supabase JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization token")

    token = auth[7:]
    try:
        return jwt.decode(
            token,
            get_settings().supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

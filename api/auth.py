"""Optional API key authentication for IVSURF routes."""

from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status


def configured_api_key() -> str | None:
    """Return the configured API key, or None when auth is disabled."""
    key = os.environ.get("IVSURF_API_KEY", "").strip()
    return key or None


def auth_enabled() -> bool:
    return configured_api_key() is not None


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """
    Enforce X-API-Key header when IVSURF_API_KEY is set.

    When IVSURF_API_KEY is unset, all routes remain open (local dev default).
    """
    expected = configured_api_key()
    if expected is None:
        return

    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

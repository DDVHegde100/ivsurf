"""Tests for API authentication helpers."""

import pytest

from api.auth import auth_enabled, configured_api_key, require_api_key
from fastapi import HTTPException


class TestAPIAuth:
    def test_auth_disabled_without_env(self, monkeypatch):
        monkeypatch.delenv("IVSURF_API_KEY", raising=False)
        assert configured_api_key() is None
        assert auth_enabled() is False
        require_api_key(None)

    def test_auth_enabled_with_env(self, monkeypatch):
        monkeypatch.setenv("IVSURF_API_KEY", "secret")
        assert configured_api_key() == "secret"
        assert auth_enabled() is True

    def test_require_api_key_accepts_valid_header(self, monkeypatch):
        monkeypatch.setenv("IVSURF_API_KEY", "secret")
        require_api_key("secret")

    def test_require_api_key_rejects_missing(self, monkeypatch):
        monkeypatch.setenv("IVSURF_API_KEY", "secret")
        with pytest.raises(HTTPException) as exc:
            require_api_key(None)
        assert exc.value.status_code == 401

    def test_require_api_key_rejects_invalid(self, monkeypatch):
        monkeypatch.setenv("IVSURF_API_KEY", "secret")
        with pytest.raises(HTTPException):
            require_api_key("other")

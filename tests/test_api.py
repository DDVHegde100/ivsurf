"""Tests for FastAPI backend."""

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authed_client(monkeypatch):
    monkeypatch.setenv("IVSURF_API_KEY", "test-secret-key")
    return TestClient(app)


class TestAPI:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["auth"] == "disabled"

    def test_health_reports_auth_required(self, authed_client):
        resp = authed_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["auth"] == "required"

    def test_scan_empty_result(self, client):
        resp = client.post("/scan", json={"tickers": ["INVALIDTICKERXYZ"], "min_score": 99})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0

    def test_scan_with_universe_preset(self, client):
        resp = client.post("/scan", json={"universe": "opening", "min_score": 99})
        assert resp.status_code == 200
        body = resp.json()
        assert body["universe"] == "opening"
        assert body["ticker_count"] > 0

    def test_list_universes(self, client):
        resp = client.get("/universes")
        assert resp.status_code == 200
        body = resp.json()
        assert "core" in body["presets"]

    def test_get_preset_universe(self, client):
        resp = client.get("/universes/presets/tech_mega")
        assert resp.status_code == 200
        assert "NVDA" in resp.json()["tickers"]

    def test_signals_history_empty(self, client, tmp_path, monkeypatch):
        monkeypatch.setenv("IVSURF_DB_PATH", str(tmp_path / "test.db"))
        resp = client.get("/signals/history")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_protected_routes_reject_missing_key(self, authed_client, tmp_path, monkeypatch):
        monkeypatch.setenv("IVSURF_DB_PATH", str(tmp_path / "test.db"))
        resp = authed_client.get("/signals/history")
        assert resp.status_code == 401

    def test_protected_routes_accept_valid_key(self, authed_client, tmp_path, monkeypatch):
        monkeypatch.setenv("IVSURF_DB_PATH", str(tmp_path / "test.db"))
        resp = authed_client.get("/signals/history", headers={"X-API-Key": "test-secret-key"})
        assert resp.status_code == 200

    def test_protected_routes_reject_invalid_key(self, authed_client):
        resp = authed_client.post(
            "/scan",
            json={"tickers": ["AAPL"], "min_score": 99},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

"""Tests for FastAPI backend."""

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestAPI:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_scan_empty_result(self, client):
        resp = client.post("/scan", json={"tickers": ["INVALIDTICKERXYZ"], "min_score": 99})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0

    def test_signals_history_empty(self, client, tmp_path, monkeypatch):
        monkeypatch.setenv("IVSURF_DB_PATH", str(tmp_path / "test.db"))
        resp = client.get("/signals/history")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

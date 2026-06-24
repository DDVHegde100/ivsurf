"""Tests for storage backend factory and PostgreSQL adapter."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from engine.data.backends.factory import create_backend
from engine.data.backends.postgres import PostgresBackend
from engine.data.backends.sqlite import SQLiteBackend
from engine.data.storage import DataStore


class TestStorageFactory:
    def test_defaults_to_sqlite(self, tmp_path, monkeypatch):
        monkeypatch.delenv("IVSURF_DATABASE_URL", raising=False)
        backend = create_backend(db_path=tmp_path / "local.db")
        assert isinstance(backend, SQLiteBackend)

    def test_uses_postgres_when_url_set(self, monkeypatch):
        monkeypatch.setenv("IVSURF_DATABASE_URL", "postgresql://user:pass@localhost/ivsurf")
        backend = create_backend()
        assert isinstance(backend, PostgresBackend)

    def test_datastore_reports_dialect(self, tmp_path, monkeypatch):
        monkeypatch.delenv("IVSURF_DATABASE_URL", raising=False)
        store = DataStore(db_path=tmp_path / "test.db")
        assert store.dialect == "sqlite"


class TestPostgresBackend:
    def test_init_schema_executes_statements(self):
        backend = PostgresBackend("postgresql://localhost/ivsurf")
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(backend, "_connect", return_value=mock_conn):
            backend.init_schema()

        assert mock_cursor.execute.call_count >= 3

    def test_log_signal_returns_id(self):
        backend = PostgresBackend("postgresql://localhost/ivsurf")
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 42}
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(backend, "_connect", return_value=mock_conn):
            signal_id = backend.log_signal("AAPL", "opening_scan", 70.0, {"gap_pct": 1.0})

        assert signal_id == 42

    def test_missing_psycopg_raises_clear_error(self):
        backend = PostgresBackend("postgresql://localhost/ivsurf")
        with patch.dict("sys.modules", {"psycopg": None}):
            with pytest.raises(RuntimeError, match="psycopg"):
                backend._connect()

    def test_save_bars_empty_returns_zero(self):
        backend = PostgresBackend("postgresql://localhost/ivsurf")
        assert backend.save_bars("AAPL", pd.DataFrame()) == 0

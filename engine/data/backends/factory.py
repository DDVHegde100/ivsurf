"""Select SQLite or PostgreSQL storage backend from environment."""

from __future__ import annotations

import os
from pathlib import Path

from engine.data.backends.sqlite import SQLiteBackend

_DEFAULT_DB = Path("data/ivsurf.db")


def create_backend(
    db_path: str | Path | None = None,
    database_url: str | None = None,
):
    """Return a storage backend. Postgres used when IVSURF_DATABASE_URL is set."""
    url = (database_url or os.environ.get("IVSURF_DATABASE_URL", "")).strip()
    if url:
        from engine.data.backends.postgres import PostgresBackend

        return PostgresBackend(url)

    path = Path(db_path or os.environ.get("IVSURF_DB_PATH", _DEFAULT_DB))
    return SQLiteBackend(path)

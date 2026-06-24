"""SQLite and PostgreSQL persistence for bars, signals, and outcomes."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from engine.data.backends.factory import create_backend

_DEFAULT_DB = Path("data/ivsurf.db")


class DataStore:
    """Persist intraday bars and signal history locally or on PostgreSQL."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        database_url: str | None = None,
        backend=None,
    ):
        self._backend = backend or create_backend(db_path=db_path, database_url=database_url)
        self.data_dir = Path(os.environ.get("IVSURF_DATA_DIR", "data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if getattr(self._backend, "db_path", None) is None:
            self.db_path = self.data_dir / "ivsurf.db"
        else:
            self.db_path = self._backend.db_path
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._backend.init_schema()

    @property
    def dialect(self) -> str:
        return self._backend.dialect

    def _connect(self):
        """Legacy access for callers that need a raw connection."""
        return self._backend.connect()

    def save_bars(
        self,
        ticker: str,
        df: pd.DataFrame,
        timeframe: str = "1Min",
        source: str = "yfinance",
    ) -> int:
        """Upsert OHLCV bars. Returns number of rows written."""
        return self._backend.save_bars(ticker, df, timeframe=timeframe, source=source)

    def load_bars(
        self,
        ticker: str,
        timeframe: str = "1Min",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """Load bars into a DataFrame."""
        return self._backend.load_bars(ticker, timeframe=timeframe, start=start, end=end)

    def save_bars_parquet(self, ticker: str, df: pd.DataFrame, timeframe: str = "1Min") -> Path:
        """Write bars to Parquet for bulk historical storage."""
        out_dir = self.data_dir / "parquet" / ticker.upper()
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{timeframe}.parquet"
        df.to_parquet(path)
        return path

    def log_signal(
        self,
        ticker: str,
        signal_type: str,
        score: float | None,
        payload: dict[str, Any],
    ) -> int:
        """Record a generated signal. Returns signal id."""
        return self._backend.log_signal(ticker, signal_type, score, payload)

    def log_outcome(
        self,
        signal_id: int,
        horizon: str,
        realized_return: float,
        label: str | None = None,
    ) -> None:
        """Record realized outcome for a signal."""
        self._backend.log_outcome(signal_id, horizon, realized_return, label)

    def fetch_signals_with_outcomes(
        self,
        limit: int = 500,
        signal_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return signals joined with optional outcome rows, newest first."""
        return self._backend.fetch_signals_with_outcomes(limit=limit, signal_type=signal_type)

    def fetch_labeled_signals(
        self,
        horizon: str = "1h",
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        """Return signals with realized outcomes for ML training."""
        return self._backend.fetch_labeled_signals(horizon=horizon, limit=limit)

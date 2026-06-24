"""SQLite and Parquet persistence for bars, signals, and outcomes."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

_DEFAULT_DB = Path("data/ivsurf.db")
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class DataStore:
    """Persist intraday bars and signal history locally."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or os.environ.get("IVSURF_DB_PATH", _DEFAULT_DB))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        schema = _SCHEMA_PATH.read_text()
        with self._connect() as conn:
            conn.executescript(schema)

    def save_bars(
        self,
        ticker: str,
        df: pd.DataFrame,
        timeframe: str = "1Min",
        source: str = "yfinance",
    ) -> int:
        """Upsert OHLCV bars. Returns number of rows written."""
        if df.empty:
            return 0

        records = []
        for ts, row in df.iterrows():
            records.append(
                (
                    ticker.upper(),
                    timeframe,
                    pd.Timestamp(ts).isoformat(),
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    float(row["Volume"]),
                    source,
                )
            )

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO bars (ticker, timeframe, timestamp, open, high, low, close, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, timeframe, timestamp) DO UPDATE SET
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, volume=excluded.volume, source=excluded.source
                """,
                records,
            )
        return len(records)

    def load_bars(
        self,
        ticker: str,
        timeframe: str = "1Min",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """Load bars from SQLite into a DataFrame."""
        query = "SELECT timestamp, open, high, low, close, volume FROM bars WHERE ticker = ? AND timeframe = ?"
        params: list[Any] = [ticker.upper(), timeframe]

        if start:
            query += " AND timestamp >= ?"
            params.append(start)
        if end:
            query += " AND timestamp <= ?"
            params.append(end)

        query += " ORDER BY timestamp"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        if not rows:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

        df = pd.DataFrame(
            [
                {
                    "Open": r["open"],
                    "High": r["high"],
                    "Low": r["low"],
                    "Close": r["close"],
                    "Volume": r["volume"],
                }
                for r in rows
            ],
            index=pd.to_datetime([r["timestamp"] for r in rows]),
        )
        return df

    def save_bars_parquet(self, ticker: str, df: pd.DataFrame, timeframe: str = "1Min") -> Path:
        """Write bars to Parquet for bulk historical storage."""
        out_dir = self.db_path.parent / "parquet" / ticker.upper()
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
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO signals (ticker, signal_type, score, payload)
                VALUES (?, ?, ?, ?)
                """,
                (ticker.upper(), signal_type, score, json.dumps(payload)),
            )
            return int(cur.lastrowid)

    def log_outcome(
        self,
        signal_id: int,
        horizon: str,
        realized_return: float,
        label: str | None = None,
    ) -> None:
        """Record realized outcome for a signal."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO outcomes (signal_id, horizon, realized_return, label)
                VALUES (?, ?, ?, ?)
                """,
                (signal_id, horizon, realized_return, label),
            )

    def fetch_signals_with_outcomes(
        self,
        limit: int = 500,
        signal_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return signals joined with optional outcome rows, newest first."""
        query = """
            SELECT s.id, s.ticker, s.signal_type, s.score, s.payload, s.created_at,
                   o.horizon, o.realized_return, o.label AS outcome_label
            FROM signals s
            LEFT JOIN outcomes o ON o.signal_id = s.id
        """
        params: list[Any] = []
        if signal_type:
            query += " WHERE s.signal_type = ?"
            params.append(signal_type)
        query += " ORDER BY s.created_at DESC, s.id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

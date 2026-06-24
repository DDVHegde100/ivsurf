"""PostgreSQL storage backend for multi-instance deployments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

_SCHEMA_PATH = Path(__file__).parent.parent / "schema_postgres.sql"


class PostgresBackend:
    """Shared PostgreSQL persistence via psycopg."""

    dialect = "postgres"

    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL backend requires psycopg. Install with: pip install 'psycopg[binary]'"
            ) from exc

        return psycopg.connect(self.database_url, row_factory=dict_row)

    def connect(self):
        """Context-managed connection compatible with legacy callers."""
        return self._connect()

    def init_schema(self) -> None:
        schema = _SCHEMA_PATH.read_text()
        statements = [stmt.strip() for stmt in schema.split(";") if stmt.strip()]
        with self._connect() as conn:
            with conn.cursor() as cur:
                for stmt in statements:
                    cur.execute(stmt)
            conn.commit()

    def save_bars(
        self,
        ticker: str,
        df: pd.DataFrame,
        timeframe: str = "1Min",
        source: str = "yfinance",
    ) -> int:
        if df.empty:
            return 0

        records = [
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
            for ts, row in df.iterrows()
        ]

        sql = """
            INSERT INTO bars (ticker, timeframe, timestamp, open, high, low, close, volume, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, timeframe, timestamp) DO UPDATE SET
                open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                close=EXCLUDED.close, volume=EXCLUDED.volume, source=EXCLUDED.source
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, records)
            conn.commit()
        return len(records)

    def load_bars(
        self,
        ticker: str,
        timeframe: str = "1Min",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        query = (
            "SELECT timestamp, open, high, low, close, volume "
            "FROM bars WHERE ticker = %s AND timeframe = %s"
        )
        params: list[Any] = [ticker.upper(), timeframe]

        if start:
            query += " AND timestamp >= %s"
            params.append(start)
        if end:
            query += " AND timestamp <= %s"
            params.append(end)

        query += " ORDER BY timestamp"

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        if not rows:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

        return pd.DataFrame(
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
            index=pd.to_datetime([str(r["timestamp"]) for r in rows]),
        )

    def log_signal(
        self,
        ticker: str,
        signal_type: str,
        score: float | None,
        payload: dict[str, Any],
    ) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO signals (ticker, signal_type, score, payload)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (ticker.upper(), signal_type, score, json.dumps(payload)),
                )
                row = cur.fetchone()
            conn.commit()
        return int(row["id"])

    def log_outcome(
        self,
        signal_id: int,
        horizon: str,
        realized_return: float,
        label: str | None = None,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO outcomes (signal_id, horizon, realized_return, label)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (signal_id, horizon, realized_return, label),
                )
            conn.commit()

    def fetch_signals_with_outcomes(
        self,
        limit: int = 500,
        signal_type: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT s.id, s.ticker, s.signal_type, s.score, s.payload, s.created_at,
                   o.horizon, o.realized_return, o.label AS outcome_label
            FROM signals s
            LEFT JOIN outcomes o ON o.signal_id = s.id
        """
        params: list[Any] = []
        if signal_type:
            query += " WHERE s.signal_type = %s"
            params.append(signal_type)
        query += " ORDER BY s.created_at DESC, s.id DESC LIMIT %s"
        params.append(limit)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [dict(row) for row in rows]

    def fetch_labeled_signals(
        self,
        horizon: str = "1h",
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT s.id, s.ticker, s.signal_type, s.score, s.payload, s.created_at,
                   o.horizon, o.realized_return, o.label AS outcome_label
            FROM signals s
            INNER JOIN outcomes o ON o.signal_id = s.id
            WHERE o.horizon = %s AND o.realized_return IS NOT NULL
            ORDER BY s.created_at ASC
            LIMIT %s
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (horizon, limit))
                rows = cur.fetchall()
        return [dict(row) for row in rows]

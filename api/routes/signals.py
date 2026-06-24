"""Signal history endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter

from engine.data.storage import DataStore

router = APIRouter()


@router.get("/history")
def signal_history(limit: int = 50):
    """Return recent logged signals from local SQLite store."""
    store = DataStore()
    with store._connect() as conn:
        rows = conn.execute(
            """
            SELECT id, ticker, signal_type, score, payload, created_at
            FROM signals
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        payload = json.loads(row["payload"]) if row["payload"] else {}
        results.append(
            {
                "id": row["id"],
                "ticker": row["ticker"],
                "signal_type": row["signal_type"],
                "score": row["score"],
                "payload": payload,
                "created_at": row["created_at"],
            }
        )

    return {"count": len(results), "signals": results}

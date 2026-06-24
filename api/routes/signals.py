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
    rows = store.fetch_signals_with_outcomes(limit=limit)

    results = []
    seen: set[int] = set()
    for row in rows:
        signal_id = row["id"]
        if signal_id in seen:
            continue
        seen.add(signal_id)
        payload = row.get("payload")
        if isinstance(payload, str):
            payload = json.loads(payload) if payload else {}
        results.append(
            {
                "id": signal_id,
                "ticker": row["ticker"],
                "signal_type": row["signal_type"],
                "score": row["score"],
                "payload": payload or {},
                "created_at": str(row["created_at"]),
            }
        )

    return {"count": len(results), "signals": results, "dialect": store.dialect}

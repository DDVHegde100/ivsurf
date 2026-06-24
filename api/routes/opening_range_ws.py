"""WebSocket feed for live opening range updates."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from api.auth import verify_ws_api_key
from engine.feed.opening_range import MAX_TICKERS, OpeningRangeFeed

router = APIRouter()
ET = ZoneInfo("America/New_York")

DEFAULT_INTERVAL_SEC = float(os.environ.get("IVSURF_OR_FEED_INTERVAL_SEC", "30"))
MIN_INTERVAL_SEC = 5.0
MAX_INTERVAL_SEC = 300.0


def _clamp_interval(value: float | None) -> float:
    interval = DEFAULT_INTERVAL_SEC if value is None else float(value)
    return max(MIN_INTERVAL_SEC, min(MAX_INTERVAL_SEC, interval))


def _normalize_tickers(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    tickers: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            tickers.append(item.strip().upper())
    return tickers[:MAX_TICKERS]


async def _send_update(websocket: WebSocket, feed: OpeningRangeFeed, tickers: list[str]) -> None:
    snapshots = await asyncio.to_thread(feed.snapshots, tickers)
    await websocket.send_json(
        {
            "type": "update",
            "count": len(snapshots),
            "snapshots": snapshots,
            "timestamp": datetime.now(tz=ET).isoformat(),
        }
    )


@router.websocket("/opening-range")
async def opening_range_ws(
    websocket: WebSocket,
    api_key: str | None = Query(default=None),
):
    """
    Stream opening-range snapshots for subscribed tickers.

    Connect, then send:
    {"action": "subscribe", "tickers": ["AAPL", "NVDA"], "interval_sec": 30}

    When IVSURF_API_KEY is set, pass ?api_key=... on the connection URL.
    """
    await websocket.accept()

    try:
        verify_ws_api_key(api_key)
    except PermissionError as exc:
        await websocket.close(code=1008, reason=str(exc))
        return

    feed = OpeningRangeFeed()
    tickers: list[str] = []
    interval_sec = DEFAULT_INTERVAL_SEC

    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=interval_sec)
            except asyncio.TimeoutError:
                if tickers:
                    await _send_update(websocket, feed, tickers)
                continue

            action = str(message.get("action", "")).lower()

            if action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now(tz=ET).isoformat()})
                continue

            if action == "unsubscribe":
                tickers = []
                await websocket.send_json({"type": "unsubscribed"})
                continue

            if action != "subscribe":
                await websocket.send_json({"type": "error", "message": "Expected action 'subscribe'"})
                continue

            tickers = _normalize_tickers(message.get("tickers"))
            if not tickers:
                await websocket.send_json({"type": "error", "message": "Provide at least one ticker"})
                continue

            interval_sec = _clamp_interval(message.get("interval_sec"))
            await websocket.send_json(
                {
                    "type": "subscribed",
                    "tickers": tickers,
                    "interval_sec": interval_sec,
                }
            )
            await _send_update(websocket, feed, tickers)

    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
        await websocket.close(code=1011)

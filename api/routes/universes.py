"""Universe and watchlist endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.data.universe import (
    delete_user_watchlist,
    get_preset,
    get_user_watchlist,
    list_universes,
    resolve_universe,
    save_user_watchlist,
)

router = APIRouter()


class WatchlistRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)
    tickers: list[str] = Field(..., min_length=1, max_length=50)


@router.get("")
def list_available_universes():
    """List built-in presets and saved user watchlists."""
    return list_universes()


@router.get("/presets/{name}")
def get_preset_universe(name: str):
    try:
        tickers = get_preset(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"name": name, "count": len(tickers), "tickers": tickers}


@router.get("/resolve/{source}")
def resolve_universe_endpoint(source: str):
    try:
        tickers = resolve_universe(source)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"source": source, "count": len(tickers), "tickers": tickers}


@router.post("/watchlists")
def create_watchlist(request: WatchlistRequest):
    tickers = save_user_watchlist(request.name, request.tickers)
    key = request.name.strip().lower().replace(" ", "_")
    return {"name": key, "count": len(tickers), "tickers": tickers}


@router.get("/watchlists/{name}")
def read_watchlist(name: str):
    try:
        tickers = get_user_watchlist(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"name": name, "count": len(tickers), "tickers": tickers}


@router.delete("/watchlists/{name}")
def remove_watchlist(name: str):
    if not delete_user_watchlist(name):
        raise HTTPException(status_code=404, detail=f"Unknown user watchlist: {name}")
    return {"deleted": name}

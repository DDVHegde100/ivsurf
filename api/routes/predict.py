"""Single-ticker prediction endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engine.signals.opening_scanner import scan_ticker
from engine.signals.regime_filter import RegimeFilter

router = APIRouter()


@router.get("/{ticker}")
def predict_ticker(ticker: str, use_regime_filter: bool = True):
    """Score a single ticker for opening volatility opportunity."""
    regime_filter = RegimeFilter() if use_regime_filter else None
    result = scan_ticker(ticker.upper(), regime_filter=regime_filter)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data available for {ticker.upper()}")
    return result

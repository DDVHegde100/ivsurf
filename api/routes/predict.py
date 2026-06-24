"""Single-ticker prediction endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException

from engine.signals.ml_ranker import load_ranker_if_available
from engine.signals.opening_options import recommend_from_scan_row
from engine.signals.opening_scanner import scan_ticker
from engine.signals.regime_filter import RegimeFilter

router = APIRouter()


@router.get("/{ticker}")
def predict_ticker(
    ticker: str,
    use_regime_filter: bool = True,
    use_ml_rank: bool = True,
    include_options_play: bool = True,
):
    """Score a single ticker for opening volatility opportunity."""
    regime_filter = RegimeFilter() if use_regime_filter else None
    result = scan_ticker(ticker.upper(), regime_filter=regime_filter)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data available for {ticker.upper()}")

    if use_ml_rank:
        ranker = load_ranker_if_available()
        if ranker is not None:
            ranked = ranker.rank(pd.DataFrame([result]))
            result = ranked.iloc[0].to_dict()

    if include_options_play:
        result["options_play"] = recommend_from_scan_row(result)

    return result

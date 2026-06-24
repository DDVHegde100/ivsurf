"""Opening scanner endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from engine.data.universe import resolve_universe
from engine.signals.opening_scanner import scan_ticker, scan_universe
from engine.signals.regime_filter import RegimeFilter

router = APIRouter()


class ScanRequest(BaseModel):
    tickers: list[str] | None = Field(None, max_length=50)
    universe: str | None = Field(None, description="Preset or user watchlist name, e.g. core or user:my_list")
    min_score: float = Field(20.0, ge=0, le=100)
    use_regime_filter: bool = True


@router.post("")
def run_scan(request: ScanRequest):
    """Scan tickers for opening volatility opportunities."""
    if request.tickers:
        symbols = request.tickers
    elif request.universe:
        symbols = resolve_universe(request.universe)
    else:
        symbols = resolve_universe("core")

    regime_filter = None
    if request.use_regime_filter:
        regime_filter = RegimeFilter()

    df = scan_universe(
        symbols,
        regime_filter=regime_filter,
        min_score=request.min_score,
    )
    return {
        "universe": request.universe or ("custom" if request.tickers else "core"),
        "ticker_count": len(symbols),
        "count": len(df),
        "results": df.to_dict(orient="records") if not df.empty else [],
    }

"""Opening scanner endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from engine.signals.opening_scanner import scan_ticker, scan_universe
from engine.signals.regime_filter import RegimeFilter

router = APIRouter()


class ScanRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, max_length=50)
    min_score: float = Field(20.0, ge=0, le=100)
    use_regime_filter: bool = True


@router.post("")
def run_scan(request: ScanRequest):
    """Scan tickers for opening volatility opportunities."""
    regime_filter = None
    if request.use_regime_filter:
        regime_filter = RegimeFilter()

    df = scan_universe(
        request.tickers,
        regime_filter=regime_filter,
        min_score=request.min_score,
    )
    return {
        "count": len(df),
        "results": df.to_dict(orient="records") if not df.empty else [],
    }

"""Pre-market opening volatility scan job."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from engine.data.sessions import ET, is_trading_day
from engine.data.storage import DataStore
from engine.signals.opening_scanner import scan_universe
from engine.signals.regime_filter import RegimeFilter

DEFAULT_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "AMD",
    "NFLX", "COIN", "PLTR", "SOFI", "RIVN", "LCID", "GME", "AMC",
    "SPY", "QQQ", "IWM", "BA", "JPM", "XOM", "DIS", "INTC",
]


def run_premarket_scan(
    tickers: list[str] | None = None,
    *,
    min_score: float = 20.0,
    use_regime_filter: bool = True,
    persist: bool = True,
    top_n: int = 20,
    skip_non_trading_days: bool = True,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """
    Scan the universe for opening volatility opportunities and persist top hits.

    Returns a summary dict with results, signal ids, and scan metadata.
    """
    now = as_of or datetime.now(tz=ET)
    if skip_non_trading_days and not is_trading_day(now.date()):
        return {
            "skipped": True,
            "reason": "non_trading_day",
            "scanned_at": now.isoformat(),
            "count": 0,
            "results": [],
            "signal_ids": [],
        }

    universe = [t.strip().upper() for t in (tickers or DEFAULT_UNIVERSE) if t.strip()]
    regime_filter = RegimeFilter() if use_regime_filter else None
    df = scan_universe(universe, regime_filter=regime_filter, min_score=min_score)

    results = df.to_dict(orient="records") if not df.empty else []
    signal_ids: list[int] = []

    if persist and results:
        store = DataStore()
        for row in results[:top_n]:
            signal_ids.append(
                store.log_signal(
                    row["ticker"],
                    "premarket_scan",
                    row.get("opening_score"),
                    row,
                )
            )

    return {
        "skipped": False,
        "scanned_at": now.isoformat(),
        "ticker_count": len(universe),
        "count": len(results),
        "results": results,
        "signal_ids": signal_ids,
    }


def write_scan_report(summary: dict[str, Any], path: str | Path) -> Path:
    """Write scan summary JSON for CI artifacts or cron logs."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, default=str))
    return out

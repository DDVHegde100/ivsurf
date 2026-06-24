#!/usr/bin/env python3
"""CLI entry point for scheduled pre-market opening scans."""

from __future__ import annotations

import argparse
import json
import sys

from engine.jobs.premarket_scan import DEFAULT_UNIVERSE, run_premarket_scan, write_scan_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run IVSURF pre-market opening scan")
    parser.add_argument(
        "--tickers",
        help="Comma-separated tickers (default: built-in universe)",
    )
    parser.add_argument("--min-score", type=float, default=20.0, help="Minimum opening score")
    parser.add_argument("--top-n", type=int, default=20, help="Max signals to persist")
    parser.add_argument("--no-regime", action="store_true", help="Disable regime filter")
    parser.add_argument("--no-persist", action="store_true", help="Skip SQLite persistence")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even on weekends (ignore trading-day check)",
    )
    parser.add_argument(
        "--output",
        default="data/premarket_scan.json",
        help="Path for JSON report (default: data/premarket_scan.json)",
    )
    args = parser.parse_args(argv)

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    elif not args.tickers:
        tickers = DEFAULT_UNIVERSE

    summary = run_premarket_scan(
        tickers,
        min_score=args.min_score,
        use_regime_filter=not args.no_regime,
        persist=not args.no_persist,
        top_n=args.top_n,
        skip_non_trading_days=not args.force,
    )

    write_scan_report(summary, args.output)

    if summary.get("skipped"):
        print(json.dumps(summary, indent=2))
        return 0

    print(
        f"Pre-market scan complete: {summary['count']} hits from "
        f"{summary['ticker_count']} tickers → {args.output}"
    )
    if summary["count"] == 0:
        return 0

    top = summary["results"][0]
    print(
        f"Top: {top['ticker']} score={top.get('opening_score', 0):.0f} "
        f"gap={top.get('gap_pct', 0):+.2f}%"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

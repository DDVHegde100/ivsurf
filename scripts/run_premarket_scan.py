#!/usr/bin/env python3
"""CLI entry point for scheduled pre-market opening scans."""

from __future__ import annotations

import argparse
import json
import sys

from engine.alerts.webhooks import dispatch_scan_alerts
from engine.data.universe import DEFAULT_UNIVERSE, resolve_universe
from engine.jobs.premarket_scan import run_premarket_scan, write_scan_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run IVSURF pre-market opening scan")
    parser.add_argument(
        "--tickers",
        help="Comma-separated tickers (overrides --universe)",
    )
    parser.add_argument(
        "--universe",
        default="core",
        help="Preset or user watchlist name (default: core)",
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
    parser.add_argument(
        "--alert",
        action="store_true",
        help="Send Slack/Discord webhook alert for hits above alert threshold",
    )
    parser.add_argument(
        "--alert-threshold",
        type=float,
        default=None,
        help="Minimum score for webhook alert (default: IVSURF_ALERT_MIN_SCORE or 50)",
    )
    parser.add_argument(
        "--alert-dry-run",
        action="store_true",
        help="Build alert payloads without POSTing to webhooks",
    )
    args = parser.parse_args(argv)

    tickers = None
    universe = args.universe
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        universe = None
    elif not args.tickers:
        tickers = None

    summary = run_premarket_scan(
        tickers,
        universe=universe,
        min_score=args.min_score,
        use_regime_filter=not args.no_regime,
        persist=not args.no_persist,
        top_n=args.top_n,
        skip_non_trading_days=not args.force,
    )

    write_scan_report(summary, args.output)

    if args.alert and not summary.get("skipped"):
        alert_result = dispatch_scan_alerts(
            summary,
            min_alert_score=args.alert_threshold,
            dry_run=args.alert_dry_run,
        )
        print(json.dumps({"alerts": alert_result}, indent=2, default=str))

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

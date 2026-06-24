#!/usr/bin/env python3
"""Train the opening ML ranker from accumulated signal outcomes."""

from __future__ import annotations

import argparse
import json
import sys

from engine.ml.train import train_ranker_from_store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train IVSURF opening ML ranker from stored outcomes")
    parser.add_argument("--horizon", default="1h", choices=["1h", "1d", "3d"])
    parser.add_argument("--min-samples", type=int, default=30)
    parser.add_argument("--output", help="Model output path (default: data/models/opening_ranker.joblib)")
    parser.add_argument("--no-xgboost", action="store_true", help="Use sklearn GBM instead of XGBoost")
    parser.add_argument("--no-walk-forward", action="store_true")
    args = parser.parse_args(argv)

    summary = train_ranker_from_store(
        horizon=args.horizon,
        min_samples=args.min_samples,
        model_path=args.output,
        use_xgboost=not args.no_xgboost,
        walk_forward=not args.no_walk_forward,
    )

    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary.get("trained") else 1


if __name__ == "__main__":
    sys.exit(main())

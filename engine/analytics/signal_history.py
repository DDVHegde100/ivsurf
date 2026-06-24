"""Signal history parsing and equity curve analytics."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


def _payload_field(payload: str | dict | None, key: str) -> Any:
    if not payload:
        return None
    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
        return data.get(key)
    except Exception:
        return None


def parse_signal_history(rows: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split joined storage rows into unique signals and outcome rows."""
    if not rows:
        empty_signals = pd.DataFrame(
            columns=["id", "ticker", "signal_type", "score", "created_at", "gap_pct", "direction"]
        )
        empty_outcomes = pd.DataFrame(
            columns=["signal_id", "horizon", "realized_return", "outcome_label"]
        )
        return empty_signals, empty_outcomes

    signals_df = pd.DataFrame(
        [
            {
                "id": r["id"],
                "ticker": r["ticker"],
                "signal_type": r["signal_type"],
                "score": r["score"],
                "created_at": r["created_at"],
                "gap_pct": _payload_field(r.get("payload"), "gap_pct"),
                "direction": _payload_field(r.get("payload"), "direction"),
            }
            for r in rows
        ]
    ).drop_duplicates(subset=["id"])

    outcomes_df = pd.DataFrame(
        [
            {
                "signal_id": r["id"],
                "horizon": r["horizon"],
                "realized_return": r["realized_return"],
                "outcome_label": r.get("outcome_label"),
            }
            for r in rows
            if r.get("horizon") is not None and r.get("realized_return") is not None
        ]
    )

    return signals_df, outcomes_df


def directional_return(realized_return: float, direction: str | None) -> float:
    """Map underlying return to PnL for long (up) or short (down) signals."""
    if direction == "down":
        return -realized_return
    return realized_return


def build_equity_curve(
    outcomes_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    *,
    horizon: str = "1d",
    initial_equity: float = 10_000.0,
    notional_per_trade: float = 500.0,
) -> pd.DataFrame:
    """
    Build a cumulative equity curve from labeled outcomes at a given horizon.

    Assumes fixed notional per signal, direction-aware long/short PnL, and
    chronological compounding on the running equity balance.
    """
    if outcomes_df.empty or signals_df.empty:
        return pd.DataFrame(
            columns=[
                "created_at",
                "ticker",
                "trade_return",
                "trade_pnl",
                "equity",
                "cumulative_return",
            ]
        )

    horizon_outcomes = outcomes_df[outcomes_df["horizon"] == horizon].copy()
    if horizon_outcomes.empty:
        return pd.DataFrame(
            columns=[
                "created_at",
                "ticker",
                "trade_return",
                "trade_pnl",
                "equity",
                "cumulative_return",
            ]
        )

    meta = signals_df[["id", "ticker", "created_at", "direction"]]
    merged = horizon_outcomes.merge(meta, left_on="signal_id", right_on="id").sort_values("created_at")

    equity = initial_equity
    records: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        trade_return = directional_return(float(row["realized_return"]), row.get("direction"))
        trade_pnl = notional_per_trade * trade_return
        equity += trade_pnl
        records.append(
            {
                "created_at": row["created_at"],
                "ticker": row["ticker"],
                "trade_return": trade_return,
                "trade_pnl": trade_pnl,
                "equity": equity,
                "cumulative_return": (equity / initial_equity) - 1,
            }
        )

    return pd.DataFrame(records)


def compute_hit_rates(
    outcomes_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    *,
    horizon: str = "1d",
) -> dict[str, float | int]:
    """Win rate and average directional return for a horizon."""
    if outcomes_df.empty or signals_df.empty:
        return {"trades": 0, "win_rate": 0.0, "avg_return": 0.0, "total_pnl_pct": 0.0}

    horizon_outcomes = outcomes_df[outcomes_df["horizon"] == horizon]
    meta = signals_df[["id", "direction"]]
    merged = horizon_outcomes.merge(meta, left_on="signal_id", right_on="id")
    if merged.empty:
        return {"trades": 0, "win_rate": 0.0, "avg_return": 0.0, "total_pnl_pct": 0.0}

    trade_returns = merged.apply(
        lambda r: directional_return(float(r["realized_return"]), r.get("direction")),
        axis=1,
    )
    wins = (trade_returns > 0).sum()
    trades = len(trade_returns)

    return {
        "trades": trades,
        "win_rate": float(wins / trades) if trades else 0.0,
        "avg_return": float(trade_returns.mean()),
        "total_pnl_pct": float(trade_returns.sum()),
    }

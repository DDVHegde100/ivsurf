"""Options-aware opening volatility play recommendations."""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd

from core.black_scholes import black_scholes_price

PlayType = Literal["straddle", "strangle", "none"]

STRADDLE_OR_THRESHOLD = 1.5
STRANGLE_OR_MIN = 1.0
DEFAULT_EXPIRY_DAYS = 7
DEFAULT_RISK_FREE_RATE = 0.05
STRANGLE_WING_PCT = 0.02


def _round_strike(price: float, step: float = 1.0) -> float:
    return round(price / step) * step


def _time_to_expiry_years(expiry_days: int) -> float:
    return max(expiry_days, 1) / 365.25


def price_straddle(
    spot: float,
    strike: float,
    volatility: float,
    *,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
) -> float:
    """ATM straddle debit using Black-Scholes."""
    t = _time_to_expiry_years(expiry_days)
    call = float(black_scholes_price(spot, strike, t, risk_free_rate, volatility, "call"))
    put = float(black_scholes_price(spot, strike, t, risk_free_rate, volatility, "put"))
    return call + put


def price_strangle(
    spot: float,
    call_strike: float,
    put_strike: float,
    volatility: float,
    *,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
) -> float:
    """OTM strangle debit using Black-Scholes."""
    t = _time_to_expiry_years(expiry_days)
    call = float(black_scholes_price(spot, call_strike, t, risk_free_rate, volatility, "call"))
    put = float(black_scholes_price(spot, put_strike, t, risk_free_rate, volatility, "put"))
    return call + put


def breakeven_moves(
    spot: float,
    debit: float,
    call_strike: float,
    put_strike: float,
    play_type: PlayType,
) -> tuple[float, float]:
    """Return (upside breakeven %, downside breakeven %) from spot."""
    if spot <= 0 or play_type == "none":
        return 0.0, 0.0

    if play_type == "straddle":
        up = ((call_strike + debit) / spot - 1) * 100
        down = (1 - (put_strike - debit) / spot) * 100
        return float(up), float(down)

    up = ((call_strike + debit) / spot - 1) * 100
    down = (1 - (put_strike - debit) / spot) * 100
    return float(up), float(down)


def recommend_options_play(
    *,
    spot: float,
    volatility: float,
    or_15m_range_pct: float,
    gap_pct: float = 0.0,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    use_market_quotes: bool = False,
    ticker: str | None = None,
) -> dict[str, Any]:
    """
    Recommend a straddle or strangle when opening range expansion is elevated.

    Straddle: high OR + small gap (direction uncertain, expect continuation).
    Strangle: moderate OR (cheaper vol expression with OTM wings).
    """
    vol = max(float(volatility), 0.05)
    or_range = float(or_15m_range_pct)
    gap = abs(float(gap_pct))

    base = {
        "play_type": "none",
        "spot": spot,
        "call_strike": None,
        "put_strike": None,
        "expiry_days": expiry_days,
        "estimated_debit": None,
        "market_debit": None,
        "breakeven_up_pct": None,
        "breakeven_down_pct": None,
        "or_15m_range_pct": or_range,
        "pricing_source": "black_scholes",
        "rationale": "Opening range too narrow for a volatility play.",
    }

    if or_range < STRANGLE_OR_MIN:
        return base

    if or_range >= STRADDLE_OR_THRESHOLD and gap < 1.0:
        strike = _round_strike(spot)
        debit = price_straddle(spot, strike, vol, expiry_days=expiry_days, risk_free_rate=risk_free_rate)
        up, down = breakeven_moves(spot, debit, strike, strike, "straddle")
        play: dict[str, Any] = {
            **base,
            "play_type": "straddle",
            "call_strike": strike,
            "put_strike": strike,
            "estimated_debit": round(debit, 2),
            "breakeven_up_pct": round(up, 2),
            "breakeven_down_pct": round(down, 2),
            "rationale": (
                f"15m OR {or_range:.1f}% with small gap — ATM straddle for continued expansion."
            ),
        }
    else:
        call_strike = _round_strike(spot * (1 + STRANGLE_WING_PCT))
        put_strike = _round_strike(spot * (1 - STRANGLE_WING_PCT))
        debit = price_strangle(
            spot, call_strike, put_strike, vol, expiry_days=expiry_days, risk_free_rate=risk_free_rate
        )
        up, down = breakeven_moves(spot, debit, call_strike, put_strike, "strangle")
        play = {
            **base,
            "play_type": "strangle",
            "call_strike": call_strike,
            "put_strike": put_strike,
            "estimated_debit": round(debit, 2),
            "breakeven_up_pct": round(up, 2),
            "breakeven_down_pct": round(down, 2),
            "rationale": (
                f"15m OR {or_range:.1f}% — OTM strangle ({STRANGLE_WING_PCT:.0%} wings) for vol expansion."
            ),
        }

    if use_market_quotes and ticker:
        market = _lookup_market_debit(ticker, play["call_strike"], play["put_strike"], expiry_days)
        if market is not None:
            play["market_debit"] = market["debit"]
            play["expiry"] = market.get("expiration")
            play["pricing_source"] = "market"

    return play


def recommend_from_scan_row(row: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Build an options play recommendation from an opening scanner result row."""
    return recommend_options_play(
        spot=float(row.get("price", 0)),
        volatility=float(row.get("volatility", 0.25)),
        or_15m_range_pct=float(row.get("or_15m_range_pct", 0)),
        gap_pct=float(row.get("gap_pct", 0)),
        ticker=str(row.get("ticker", "")),
        **kwargs,
    )


def enrich_scan_with_options(
    df: pd.DataFrame,
    *,
    min_or_pct: float = STRANGLE_OR_MIN,
    use_market_quotes: bool = False,
) -> pd.DataFrame:
    """Add options play columns for tickers with sufficient opening range."""
    if df.empty:
        return df

    plays: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        or_range = float(row.get("or_15m_range_pct", 0))
        if or_range < min_or_pct:
            plays.append({"options_play_type": "none"})
            continue
        play = recommend_from_scan_row(row.to_dict(), use_market_quotes=use_market_quotes)
        plays.append(
            {
                "options_play_type": play["play_type"],
                "options_call_strike": play.get("call_strike"),
                "options_put_strike": play.get("put_strike"),
                "options_est_debit": play.get("estimated_debit"),
                "options_breakeven_up_pct": play.get("breakeven_up_pct"),
                "options_breakeven_down_pct": play.get("breakeven_down_pct"),
                "options_rationale": play.get("rationale"),
            }
        )

    return pd.concat([df.reset_index(drop=True), pd.DataFrame(plays)], axis=1)


def _lookup_market_debit(
    ticker: str,
    call_strike: float,
    put_strike: float,
    expiry_days: int,
) -> dict[str, Any] | None:
    """Try to price the play from Yahoo Finance option mids."""
    try:
        from engine.data.fetcher import OptionsDataFetcher

        chain = OptionsDataFetcher().get_options_chain(ticker, max_expiries=4)
        if chain.empty:
            return None

        target = chain[
            (chain["daysToExpiry"] >= max(1, expiry_days - 3))
            & (chain["daysToExpiry"] <= expiry_days + 7)
        ]
        if target.empty:
            target = chain

        expiry = target["expiration"].iloc[0]
        slice_df = target[target["expiration"] == expiry]

        call_row = slice_df[
            (slice_df["optionType"] == "call") & (slice_df["strike"] == call_strike)
        ]
        put_row = slice_df[(slice_df["optionType"] == "put") & (slice_df["strike"] == put_strike)]

        if call_row.empty or put_row.empty:
            # nearest strike fallback
            calls = slice_df[slice_df["optionType"] == "call"].copy()
            puts = slice_df[slice_df["optionType"] == "put"].copy()
            if calls.empty or puts.empty:
                return None
            calls["dist"] = (calls["strike"] - call_strike).abs()
            puts["dist"] = (puts["strike"] - put_strike).abs()
            call_row = calls.nsmallest(1, "dist")
            put_row = puts.nsmallest(1, "dist")

        debit = float(call_row["midPrice"].iloc[0] + put_row["midPrice"].iloc[0])
        return {"debit": round(debit, 2), "expiration": str(expiry)}
    except Exception:
        return None

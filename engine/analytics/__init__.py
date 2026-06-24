"""Performance analytics for logged signals."""

from engine.analytics.signal_history import (
    build_equity_curve,
    compute_hit_rates,
    parse_signal_history,
)

__all__ = ["build_equity_curve", "compute_hit_rates", "parse_signal_history"]

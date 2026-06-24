"""Strategy backtesting, labeling, and walk-forward validation."""

from engine.backtest.labeling import (
    build_labeled_dataset,
    compute_horizon_return,
    label_return,
    label_signal_outcomes,
)
from engine.backtest.walk_forward import walk_forward_evaluate, walk_forward_splits
from portfolio.regime_backtesting import RegimeAwareBacktester

__all__ = [
    "RegimeAwareBacktester",
    "build_labeled_dataset",
    "compute_horizon_return",
    "label_return",
    "label_signal_outcomes",
    "walk_forward_evaluate",
    "walk_forward_splits",
]

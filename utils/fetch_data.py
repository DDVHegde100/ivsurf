"""Backwards-compatible re-exports — use engine.data.fetcher directly."""

from engine.data.fetcher import (
    OptionsDataFetcher,
    get_options_chain,
    get_single_option_quote,
    get_stock_price,
)

__all__ = [
    "OptionsDataFetcher",
    "get_options_chain",
    "get_single_option_quote",
    "get_stock_price",
]

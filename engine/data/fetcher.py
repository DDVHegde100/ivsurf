"""
Enhanced options data fetcher with comprehensive Yahoo Finance integration.
"""

from __future__ import annotations

import warnings
from datetime import timedelta
from typing import Dict, Tuple

import pandas as pd
import yfinance as yf

from engine.data.cache import TTLCache


class OptionsDataFetcher:
    """Enhanced options data fetcher with caching and error handling."""

    def __init__(self, cache_duration_minutes: int = 5):
        self._cache = TTLCache[pd.DataFrame](timedelta(minutes=cache_duration_minutes))

    def get_stock_info(self, ticker: str) -> Dict:
        """Get basic stock information."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="5d")

            if hist.empty:
                raise ValueError(f"No price data found for {ticker}")

            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current_price

            return {
                "symbol": ticker.upper(),
                "current_price": float(current_price),
                "previous_close": float(prev_close),
                "change": float(current_price - prev_close),
                "change_percent": float((current_price - prev_close) / prev_close * 100),
                "volume": int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0,
                "company_name": info.get("longName", ticker.upper()),
                "sector": info.get("sector", "Unknown"),
                "beta": info.get("beta", None),
                "market_cap": info.get("marketCap", None),
            }

        except Exception as e:
            raise ValueError(f"Failed to fetch stock info for {ticker}: {str(e)}") from e

    def get_options_chain(self, ticker: str, max_expiries: int = 6) -> pd.DataFrame:
        """Fetch options chain data with comprehensive information."""
        cache_key = f"{ticker}_options"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached.copy()

        try:
            stock = yf.Ticker(ticker)
            expiration_dates = stock.options
            if not expiration_dates:
                raise ValueError(f"No options data available for {ticker}")

            expiration_dates = expiration_dates[:max_expiries]
            options_data = []

            for exp_date in expiration_dates:
                try:
                    opt_chain = stock.option_chain(exp_date)

                    calls = opt_chain.calls.copy()
                    calls["optionType"] = "call"
                    calls["expiration"] = exp_date
                    calls["daysToExpiry"] = (pd.to_datetime(exp_date) - pd.Timestamp.today()).days
                    calls["timeToExpiry"] = calls["daysToExpiry"] / 365.25

                    puts = opt_chain.puts.copy()
                    puts["optionType"] = "put"
                    puts["expiration"] = exp_date
                    puts["daysToExpiry"] = (pd.to_datetime(exp_date) - pd.Timestamp.today()).days
                    puts["timeToExpiry"] = puts["daysToExpiry"] / 365.25

                    combined = pd.concat([calls, puts], ignore_index=True)
                    combined["midPrice"] = (combined["bid"] + combined["ask"]) / 2
                    combined["bidAskSpread"] = combined["ask"] - combined["bid"]
                    combined["bidAskSpreadPct"] = combined["bidAskSpread"] / combined["midPrice"] * 100

                    combined = combined[
                        (combined["bid"] > 0)
                        & (combined["ask"] > 0)
                        & (combined["volume"].notna())
                        & (combined["timeToExpiry"] > 0)
                    ].copy()

                    if not combined.empty:
                        options_data.append(combined)

                except Exception as e:
                    warnings.warn(f"Failed to fetch options for expiry {exp_date}: {str(e)}")
                    continue

            if not options_data:
                raise ValueError(f"No valid options data found for {ticker}")

            final_df = pd.concat(options_data, ignore_index=True)
            final_df = final_df.sort_values(["expiration", "strike"]).reset_index(drop=True)
            self._cache.set(cache_key, final_df.copy())
            return final_df

        except Exception as e:
            raise ValueError(f"Failed to fetch options chain for {ticker}: {str(e)}") from e

    def get_option_by_criteria(
        self,
        ticker: str,
        option_type: str,
        strike_range: Tuple[float, float] | None = None,
        days_to_expiry_range: Tuple[int, int] | None = None,
        min_volume: int = 10,
    ) -> pd.DataFrame:
        """Get options filtered by specific criteria."""
        df = self.get_options_chain(ticker)
        df = df[df["optionType"] == option_type].copy()

        if strike_range:
            df = df[(df["strike"] >= strike_range[0]) & (df["strike"] <= strike_range[1])]

        if days_to_expiry_range:
            df = df[
                (df["daysToExpiry"] >= days_to_expiry_range[0])
                & (df["daysToExpiry"] <= days_to_expiry_range[1])
            ]

        if min_volume:
            df = df[df["volume"] >= min_volume]

        return df.reset_index(drop=True)


_fetcher = OptionsDataFetcher()


def get_options_chain(ticker: str, max_expiries: int = 3) -> pd.DataFrame:
    """Simplified interface for backwards compatibility."""
    return _fetcher.get_options_chain(ticker, max_expiries)


def get_stock_price(ticker: str) -> float:
    """Get current stock price."""
    info = _fetcher.get_stock_info(ticker)
    return info["current_price"]


def get_single_option_quote(ticker: str, strike: float, expiry: str, option_type: str) -> Dict:
    """Get quote for a specific option contract."""
    try:
        options_df = get_options_chain(ticker, max_expiries=10)
        match = options_df[
            (options_df["strike"] == strike)
            & (options_df["expiration"] == expiry)
            & (options_df["optionType"] == option_type)
        ]

        if match.empty:
            raise ValueError(f"Option not found: {ticker} {strike} {expiry} {option_type}")

        option_data = match.iloc[0]
        return {
            "symbol": ticker,
            "strike": float(option_data["strike"]),
            "expiry": option_data["expiration"],
            "option_type": option_data["optionType"],
            "last_price": float(option_data["lastPrice"]),
            "bid": float(option_data["bid"]),
            "ask": float(option_data["ask"]),
            "mid_price": float(option_data["midPrice"]),
            "volume": int(option_data["volume"]),
            "open_interest": int(option_data["openInterest"]),
            "implied_volatility": float(option_data.get("impliedVolatility", 0)),
            "days_to_expiry": int(option_data["daysToExpiry"]),
            "time_to_expiry": float(option_data["timeToExpiry"]),
        }

    except Exception as e:
        raise ValueError(f"Failed to get option quote: {str(e)}") from e

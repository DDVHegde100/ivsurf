"""Alpaca paper-trading adapter for opening scanner signals.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY. Uses ALPACA_BASE_URL
(defaults to paper-api.alpaca.markets). Set dry_run=True to log orders
without submitting them. Pre-trade guardrails apply via TradingGuardrails.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Literal

from engine.execution.guardrails import TradingGuardrails

OrderSide = Literal["buy", "sell"]


class AlpacaPaperTrader:
    """Submit market orders to Alpaca paper (or live) accounts."""

    def __init__(
        self,
        dry_run: bool = False,
        guardrails: TradingGuardrails | None = None,
    ):
        self._api_key = os.environ.get("ALPACA_API_KEY", "").strip()
        self._secret_key = os.environ.get("ALPACA_SECRET_KEY", "").strip()
        self._base_url = os.environ.get(
            "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
        ).rstrip("/")
        self._dry_run = dry_run
        self._guardrails = guardrails if guardrails is not None else TradingGuardrails.from_env()

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._secret_key)

    @property
    def guardrails(self) -> TradingGuardrails:
        return self._guardrails

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.configured and not self._dry_run:
            raise RuntimeError("Alpaca credentials not configured")

        url = f"{self._base_url}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "APCA-API-KEY-ID": self._api_key or "dry-run",
                "APCA-API-SECRET-KEY": self._secret_key or "dry-run",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()
            raise RuntimeError(f"Alpaca API error {exc.code}: {detail}") from exc

    def get_account(self) -> dict[str, Any]:
        """Return Alpaca account summary (buying power, equity, etc.)."""
        if self._dry_run:
            return {
                "status": "dry_run",
                "buying_power": "100000",
                "equity": "100000",
                "last_equity": "100000",
            }
        return self._request("GET", "/v2/account")

    def get_positions(self) -> list[dict[str, Any]]:
        """Return open positions."""
        if self._dry_run:
            return []
        payload = self._request("GET", "/v2/positions")
        return payload if isinstance(payload, list) else []

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Submit a day market order."""
        if qty < 1:
            raise ValueError("qty must be at least 1")

        order = {
            "symbol": symbol.upper(),
            "qty": str(qty),
            "side": side,
            "type": "market",
            "time_in_force": time_in_force,
        }

        if self._dry_run:
            return {"id": "dry-run", "status": "accepted", **order}

        return self._request("POST", "/v2/orders", order)

    def execute_signal(
        self,
        signal: dict[str, Any],
        *,
        notional_usd: float = 500.0,
        min_score: float = 50.0,
        orders_placed_today: int = 0,
    ) -> dict[str, Any] | None:
        """
        Convert an opening scanner row into a market order.

        Buys on upward gaps, sells (short) on downward gaps when score clears
        the threshold. Returns the Alpaca order payload, a blocked status dict,
        or None if skipped.
        """
        score = float(signal.get("opening_score", 0))
        if score < min_score:
            return None

        price = float(signal.get("price", 0))
        if price <= 0:
            return None

        qty = int(notional_usd / price)
        if qty < 1:
            return None

        direction = signal.get("direction", "up")
        side: OrderSide = "buy" if direction == "up" else "sell"
        ticker = str(signal.get("ticker", "")).upper()
        if not ticker:
            return None

        check = self._guardrails.evaluate(
            account=self.get_account(),
            positions=self.get_positions(),
            symbol=ticker,
            notional_usd=notional_usd,
            orders_placed_today=orders_placed_today,
        )
        if not check.allowed:
            return {
                "id": None,
                "status": "blocked",
                "symbol": ticker,
                "side": side,
                "qty": str(qty),
                "reason": check.reason,
            }

        return self.submit_market_order(ticker, qty, side)

    def execute_top_signals(
        self,
        signals: list[dict[str, Any]],
        *,
        max_orders: int = 3,
        notional_usd: float = 500.0,
        min_score: float = 50.0,
        orders_placed_today: int = 0,
    ) -> list[dict[str, Any]]:
        """Execute up to max_orders from a ranked scan result list."""
        results: list[dict[str, Any]] = []
        accepted = 0
        attempted = orders_placed_today

        for signal in signals:
            if accepted >= max_orders:
                break

            order = self.execute_signal(
                signal,
                notional_usd=notional_usd,
                min_score=min_score,
                orders_placed_today=attempted,
            )
            if order is None:
                continue

            results.append({"signal": signal, "order": order})
            attempted += 1
            if order.get("status") == "accepted":
                accepted += 1

        return results

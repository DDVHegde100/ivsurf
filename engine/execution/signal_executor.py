"""Signal execution with guardrails over a broker adapter."""

from __future__ import annotations

from typing import Any

from engine.execution.base import BrokerAdapter, OrderSide
from engine.execution.guardrails import TradingGuardrails


class SignalExecutor:
    """Convert opening scanner signals into broker market orders."""

    def __init__(
        self,
        broker: BrokerAdapter,
        guardrails: TradingGuardrails | None = None,
    ):
        self._broker = broker
        self._guardrails = guardrails if guardrails is not None else TradingGuardrails.from_env()

    @property
    def broker(self) -> BrokerAdapter:
        return self._broker

    @property
    def guardrails(self) -> TradingGuardrails:
        return self._guardrails

    def get_account(self) -> dict[str, Any]:
        return self._broker.get_account()

    def get_positions(self) -> list[dict[str, Any]]:
        return self._broker.get_positions()

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        return self._broker.submit_market_order(symbol, qty, side, time_in_force=time_in_force)

    def execute_signal(
        self,
        signal: dict[str, Any],
        *,
        notional_usd: float = 500.0,
        min_score: float = 50.0,
        orders_placed_today: int = 0,
    ) -> dict[str, Any] | None:
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
                "broker": self._broker.name,
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

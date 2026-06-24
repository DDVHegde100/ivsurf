"""Alpaca paper-trading adapter for opening scanner signals.

Backward-compatible facade over the broker abstraction. Prefer
``create_executor()`` for new code.
"""

from __future__ import annotations

from typing import Any

from engine.execution.base import OrderSide
from engine.execution.brokers.alpaca import AlpacaBroker
from engine.execution.factory import create_executor


class AlpacaPaperTrader:
    """Submit market orders via Alpaca with guardrails."""

    def __init__(
        self,
        dry_run: bool = False,
        guardrails: TradingGuardrails | None = None,
        executor: SignalExecutor | None = None,
    ):
        self._executor = executor or create_executor("alpaca", dry_run=dry_run, guardrails=guardrails)

    @property
    def configured(self) -> bool:
        return self._executor.broker.configured

    @property
    def guardrails(self) -> TradingGuardrails:
        return self._executor.guardrails

    @property
    def broker_name(self) -> str:
        return self._executor.broker.name

    def get_account(self) -> dict[str, Any]:
        return self._executor.get_account()

    def get_positions(self) -> list[dict[str, Any]]:
        return self._executor.get_positions()

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        return self._executor.submit_market_order(symbol, qty, side, time_in_force=time_in_force)

    def execute_signal(
        self,
        signal: dict[str, Any],
        *,
        notional_usd: float = 500.0,
        min_score: float = 50.0,
        orders_placed_today: int = 0,
    ) -> dict[str, Any] | None:
        return self._executor.execute_signal(
            signal,
            notional_usd=notional_usd,
            min_score=min_score,
            orders_placed_today=orders_placed_today,
        )

    def execute_top_signals(
        self,
        signals: list[dict[str, Any]],
        *,
        max_orders: int = 3,
        notional_usd: float = 500.0,
        min_score: float = 50.0,
        orders_placed_today: int = 0,
    ) -> list[dict[str, Any]]:
        return self._executor.execute_top_signals(
            signals,
            max_orders=max_orders,
            notional_usd=notional_usd,
            min_score=min_score,
            orders_placed_today=orders_placed_today,
        )

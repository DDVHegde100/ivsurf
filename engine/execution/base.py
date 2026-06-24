"""Broker adapter interfaces."""

from __future__ import annotations

from typing import Any, Literal, Protocol

OrderSide = Literal["buy", "sell"]


class BrokerAdapter(Protocol):
    """Minimal broker interface for equities order execution."""

    @property
    def name(self) -> str: ...

    @property
    def configured(self) -> bool: ...

    def get_account(self) -> dict[str, Any]: ...

    def get_positions(self) -> list[dict[str, Any]]: ...

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        time_in_force: str = "day",
    ) -> dict[str, Any]: ...

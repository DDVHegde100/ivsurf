"""Simulated broker for dry-run and local testing."""

from __future__ import annotations

from typing import Any

from engine.execution.base import OrderSide


class SimulatedBroker:
    """In-memory broker that accepts orders without external API calls."""

    name = "simulated"

    def __init__(
        self,
        *,
        buying_power: float = 100_000.0,
        equity: float = 100_000.0,
        last_equity: float = 100_000.0,
    ):
        self._buying_power = buying_power
        self._equity = equity
        self._last_equity = last_equity
        self._positions: dict[str, dict[str, Any]] = {}
        self._order_count = 0

    @property
    def configured(self) -> bool:
        return True

    def get_account(self) -> dict[str, Any]:
        return {
            "status": "simulated",
            "buying_power": str(self._buying_power),
            "equity": str(self._equity),
            "last_equity": str(self._last_equity),
        }

    def get_positions(self) -> list[dict[str, Any]]:
        return list(self._positions.values())

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        if qty < 1:
            raise ValueError("qty must be at least 1")

        self._order_count += 1
        sym = symbol.upper()
        if side == "buy":
            self._positions[sym] = {"symbol": sym, "qty": str(qty), "side": "long"}
        elif sym in self._positions:
            del self._positions[sym]

        return {
            "id": f"sim-{self._order_count}",
            "status": "accepted",
            "symbol": sym,
            "qty": str(qty),
            "side": side,
            "type": "market",
            "time_in_force": time_in_force,
            "broker": self.name,
        }

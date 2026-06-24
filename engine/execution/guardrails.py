"""Trading guardrails for paper and live order execution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GuardrailCheck:
    allowed: bool
    reason: str | None = None


@dataclass
class TradingGuardrails:
    """Pre-trade risk checks before submitting orders."""

    enabled: bool = True
    max_daily_loss_pct: float = 2.0
    max_open_positions: int = 5
    max_orders_per_day: int = 10
    max_notional_per_trade: float = 1000.0
    one_position_per_symbol: bool = True

    @classmethod
    def from_env(cls) -> TradingGuardrails:
        enabled = os.environ.get("IVSURF_GUARDRAILS_ENABLED", "true").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        return cls(
            enabled=enabled,
            max_daily_loss_pct=float(os.environ.get("IVSURF_MAX_DAILY_LOSS_PCT", "2")),
            max_open_positions=int(os.environ.get("IVSURF_MAX_OPEN_POSITIONS", "5")),
            max_orders_per_day=int(os.environ.get("IVSURF_MAX_ORDERS_PER_DAY", "10")),
            max_notional_per_trade=float(os.environ.get("IVSURF_MAX_NOTIONAL_PER_TRADE", "1000")),
            one_position_per_symbol=os.environ.get("IVSURF_ONE_POSITION_PER_SYMBOL", "true").strip().lower()
            in {"1", "true", "yes"},
        )

    def daily_pnl_pct(self, account: dict[str, Any]) -> float | None:
        try:
            equity = float(account.get("equity", 0))
            last_equity = float(account.get("last_equity", equity))
        except (TypeError, ValueError):
            return None
        if last_equity <= 0:
            return None
        return (equity - last_equity) / last_equity * 100

    def evaluate(
        self,
        *,
        account: dict[str, Any],
        positions: list[dict[str, Any]],
        symbol: str,
        notional_usd: float,
        orders_placed_today: int = 0,
    ) -> GuardrailCheck:
        if not self.enabled:
            return GuardrailCheck(True)

        daily_pnl = self.daily_pnl_pct(account)
        if daily_pnl is not None and daily_pnl <= -abs(self.max_daily_loss_pct):
            return GuardrailCheck(
                False,
                f"Daily loss limit reached ({daily_pnl:.2f}% / -{self.max_daily_loss_pct:.2f}%)",
            )

        if len(positions) >= self.max_open_positions:
            return GuardrailCheck(
                False,
                f"Max open positions reached ({len(positions)}/{self.max_open_positions})",
            )

        if orders_placed_today >= self.max_orders_per_day:
            return GuardrailCheck(
                False,
                f"Max orders per day reached ({orders_placed_today}/{self.max_orders_per_day})",
            )

        if notional_usd > self.max_notional_per_trade:
            return GuardrailCheck(
                False,
                f"Notional ${notional_usd:.0f} exceeds limit ${self.max_notional_per_trade:.0f}",
            )

        if self.one_position_per_symbol:
            held = {str(p.get("symbol", "")).upper() for p in positions}
            sym = symbol.upper()
            if sym in held:
                return GuardrailCheck(False, f"Already holding an open position in {sym}")

        return GuardrailCheck(True)

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "max_open_positions": self.max_open_positions,
            "max_orders_per_day": self.max_orders_per_day,
            "max_notional_per_trade": self.max_notional_per_trade,
            "one_position_per_symbol": self.one_position_per_symbol,
        }

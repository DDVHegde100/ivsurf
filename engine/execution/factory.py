"""Broker factory helpers."""

from __future__ import annotations

import os

from engine.execution.base import BrokerAdapter
from engine.execution.brokers.alpaca import AlpacaBroker
from engine.execution.brokers.simulated import SimulatedBroker
from engine.execution.guardrails import TradingGuardrails
from engine.execution.signal_executor import SignalExecutor

_SUPPORTED = {"alpaca", "simulated"}


def create_broker(
    broker_name: str | None = None,
    *,
    dry_run: bool = False,
) -> BrokerAdapter:
    """Instantiate a broker adapter from IVSURF_BROKER or explicit name."""
    name = (broker_name or os.environ.get("IVSURF_BROKER", "alpaca")).strip().lower()

    if name == "simulated":
        return SimulatedBroker()
    if name == "alpaca":
        return AlpacaBroker(dry_run=dry_run)

    raise ValueError(f"Unsupported broker '{name}'. Supported: {sorted(_SUPPORTED)}")


def create_executor(
    broker_name: str | None = None,
    *,
    dry_run: bool = False,
    guardrails: TradingGuardrails | None = None,
) -> SignalExecutor:
    """Create a signal executor wired to the selected broker."""
    if dry_run and (broker_name or os.environ.get("IVSURF_BROKER", "alpaca")).lower() != "alpaca":
        broker = SimulatedBroker()
    else:
        broker = create_broker(broker_name, dry_run=dry_run)
    return SignalExecutor(broker, guardrails=guardrails)


def list_brokers() -> list[str]:
    return sorted(_SUPPORTED)

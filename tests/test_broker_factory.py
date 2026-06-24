"""Tests for broker abstraction."""

import pytest

from engine.execution.brokers.alpaca import AlpacaBroker
from engine.execution.brokers.simulated import SimulatedBroker
from engine.execution.factory import create_broker, create_executor, list_brokers
from engine.execution.guardrails import TradingGuardrails


class TestBrokerFactory:
    def test_list_brokers(self):
        assert "alpaca" in list_brokers()
        assert "simulated" in list_brokers()

    def test_create_simulated_broker(self):
        broker = create_broker("simulated")
        assert broker.name == "simulated"
        assert broker.configured is True

    def test_create_alpaca_broker(self, monkeypatch):
        monkeypatch.setenv("ALPACA_API_KEY", "key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
        broker = create_broker("alpaca")
        assert broker.name == "alpaca"
        assert broker.configured is True

    def test_unknown_broker_raises(self):
        with pytest.raises(ValueError, match="Unsupported broker"):
            create_broker("unknown_broker")


class TestSimulatedBroker:
    def test_submit_and_track_position(self):
        broker = SimulatedBroker()
        order = broker.submit_market_order("AAPL", 10, "buy")
        assert order["status"] == "accepted"
        assert order["broker"] == "simulated"
        assert len(broker.get_positions()) == 1

    def test_executor_with_simulated_broker(self):
        executor = create_executor("simulated")
        result = executor.execute_signal(
            {"ticker": "NVDA", "opening_score": 80, "price": 100, "direction": "up"},
            min_score=50,
        )
        assert result is not None
        assert result["status"] == "accepted"
        assert result["broker"] == "simulated"


class TestAlpacaBrokerDryRun:
    def test_dry_run_does_not_require_credentials(self, monkeypatch):
        monkeypatch.delenv("ALPACA_API_KEY", raising=False)
        monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
        broker = AlpacaBroker(dry_run=True)
        assert broker.configured is False
        order = broker.submit_market_order("AAPL", 1, "buy")
        assert order["status"] == "accepted"

    def test_live_requires_credentials(self, monkeypatch):
        monkeypatch.delenv("ALPACA_API_KEY", raising=False)
        monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
        broker = AlpacaBroker(dry_run=False)
        with pytest.raises(RuntimeError, match="credentials"):
            broker.get_account()

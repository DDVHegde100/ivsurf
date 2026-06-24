"""Tests for Alpaca paper trading adapter."""

import pytest

from engine.execution.guardrails import TradingGuardrails
from engine.execution.paper_trader import AlpacaPaperTrader
from engine.execution.brokers.simulated import SimulatedBroker
from engine.execution.signal_executor import SignalExecutor


class TestAlpacaPaperTrader:
    def test_dry_run_submit_order(self):
        trader = AlpacaPaperTrader(dry_run=True)
        order = trader.submit_market_order("AAPL", 10, "buy")
        assert order["status"] == "accepted"
        assert order["symbol"] == "AAPL"
        assert order["qty"] == "10"

    def test_execute_signal_skips_low_score(self):
        trader = AlpacaPaperTrader(dry_run=True)
        result = trader.execute_signal(
            {"ticker": "AAPL", "opening_score": 30, "price": 150, "direction": "up"},
            min_score=50,
        )
        assert result is None

    def test_execute_signal_places_order(self):
        trader = AlpacaPaperTrader(dry_run=True)
        result = trader.execute_signal(
            {"ticker": "AAPL", "opening_score": 75, "price": 100, "direction": "up"},
            notional_usd=500,
            min_score=50,
        )
        assert result is not None
        assert result["side"] == "buy"
        assert int(result["qty"]) == 5

    def test_execute_signal_sells_on_down_gap(self):
        trader = AlpacaPaperTrader(dry_run=True)
        result = trader.execute_signal(
            {"ticker": "TSLA", "opening_score": 60, "price": 200, "direction": "down"},
        )
        assert result is not None
        assert result["side"] == "sell"

    def test_execute_top_signals_respects_max_orders(self):
        trader = AlpacaPaperTrader(dry_run=True)
        signals = [
            {"ticker": "AAPL", "opening_score": 80, "price": 100, "direction": "up"},
            {"ticker": "MSFT", "opening_score": 70, "price": 100, "direction": "up"},
            {"ticker": "NVDA", "opening_score": 65, "price": 100, "direction": "up"},
            {"ticker": "AMD", "opening_score": 55, "price": 100, "direction": "up"},
        ]
        placed = trader.execute_top_signals(signals, max_orders=2)
        accepted = [p for p in placed if p["order"]["status"] == "accepted"]
        assert len(accepted) == 2

    def test_execute_signal_blocked_by_guardrails(self):
        guardrails = TradingGuardrails(
            enabled=True,
            max_daily_loss_pct=2.0,
            max_open_positions=5,
            max_orders_per_day=10,
            max_notional_per_trade=1000.0,
        )
        broker = SimulatedBroker(equity=97_000, last_equity=100_000)
        executor = SignalExecutor(broker, guardrails=guardrails)
        trader = AlpacaPaperTrader(executor=executor)

        result = trader.execute_signal(
            {"ticker": "AAPL", "opening_score": 80, "price": 100, "direction": "up"},
        )
        assert result is not None
        assert result["status"] == "blocked"
        assert "Daily loss limit" in result["reason"]

    def test_not_configured_raises_without_dry_run(self, monkeypatch):
        monkeypatch.delenv("ALPACA_API_KEY", raising=False)
        monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
        trader = AlpacaPaperTrader(dry_run=False)
        with pytest.raises(RuntimeError, match="credentials"):
            trader.get_account()

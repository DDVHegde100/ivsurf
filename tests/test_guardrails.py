"""Tests for trading guardrails."""

import pytest

from engine.execution.guardrails import TradingGuardrails


class TestTradingGuardrails:
    def _guardrails(self) -> TradingGuardrails:
        return TradingGuardrails(
            enabled=True,
            max_daily_loss_pct=2.0,
            max_open_positions=3,
            max_orders_per_day=5,
            max_notional_per_trade=1000.0,
            one_position_per_symbol=True,
        )

    def test_allows_when_within_limits(self):
        g = self._guardrails()
        check = g.evaluate(
            account={"equity": "100000", "last_equity": "100000"},
            positions=[{"symbol": "MSFT"}],
            symbol="AAPL",
            notional_usd=500,
            orders_placed_today=1,
        )
        assert check.allowed is True

    def test_blocks_daily_loss_limit(self):
        g = self._guardrails()
        check = g.evaluate(
            account={"equity": "97000", "last_equity": "100000"},
            positions=[],
            symbol="AAPL",
            notional_usd=500,
        )
        assert check.allowed is False
        assert "Daily loss limit" in (check.reason or "")

    def test_blocks_max_positions(self):
        g = self._guardrails()
        positions = [{"symbol": "A"}, {"symbol": "B"}, {"symbol": "C"}]
        check = g.evaluate(
            account={"equity": "100000", "last_equity": "100000"},
            positions=positions,
            symbol="NVDA",
            notional_usd=500,
        )
        assert check.allowed is False

    def test_blocks_duplicate_symbol(self):
        g = self._guardrails()
        check = g.evaluate(
            account={"equity": "100000", "last_equity": "100000"},
            positions=[{"symbol": "AAPL"}],
            symbol="AAPL",
            notional_usd=500,
        )
        assert check.allowed is False
        assert "Already holding" in (check.reason or "")

    def test_blocks_notional_limit(self):
        g = self._guardrails()
        check = g.evaluate(
            account={"equity": "100000", "last_equity": "100000"},
            positions=[],
            symbol="AAPL",
            notional_usd=1500,
        )
        assert check.allowed is False

    def test_disabled_guardrails_always_allow(self):
        g = TradingGuardrails(enabled=False)
        check = g.evaluate(
            account={"equity": "90000", "last_equity": "100000"},
            positions=[{"symbol": "A"}] * 10,
            symbol="AAPL",
            notional_usd=5000,
            orders_placed_today=99,
        )
        assert check.allowed is True

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("IVSURF_MAX_DAILY_LOSS_PCT", "3")
        monkeypatch.setenv("IVSURF_MAX_OPEN_POSITIONS", "7")
        g = TradingGuardrails.from_env()
        assert g.max_daily_loss_pct == 3
        assert g.max_open_positions == 7

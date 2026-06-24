"""Tests for watchlist and sector universe management."""

import pytest

from engine.data.universe import (
    DEFAULT_UNIVERSE,
    delete_user_watchlist,
    get_preset,
    list_presets,
    parse_ticker_list,
    resolve_universe,
    save_user_watchlist,
)


class TestUniverse:
    def test_list_presets(self):
        presets = list_presets()
        assert "core" in presets
        assert "tech_mega" in presets

    def test_get_preset_core(self):
        tickers = get_preset("core")
        assert "AAPL" in tickers
        assert len(tickers) >= 10

    def test_default_universe_matches_core(self):
        assert DEFAULT_UNIVERSE == get_preset("core")

    def test_parse_ticker_list(self):
        assert parse_ticker_list("aapl, msft , NVDA") == ["AAPL", "MSFT", "NVDA"]

    def test_resolve_preset(self):
        assert resolve_universe("semis") == get_preset("semis")

    def test_resolve_user_watchlist(self, tmp_path, monkeypatch):
        monkeypatch.setenv("IVSURF_WATCHLIST_PATH", str(tmp_path / "watchlists.json"))
        save_user_watchlist("momentum", ["TSLA", "NVDA"])
        assert resolve_universe("user:momentum") == ["TSLA", "NVDA"]
        assert resolve_universe("@momentum") == ["TSLA", "NVDA"]

    def test_save_and_delete_watchlist(self, tmp_path, monkeypatch):
        monkeypatch.setenv("IVSURF_WATCHLIST_PATH", str(tmp_path / "watchlists.json"))
        saved = save_user_watchlist("test_list", ["AAPL", "MSFT"])
        assert saved == ["AAPL", "MSFT"]
        assert delete_user_watchlist("test_list") is True
        assert delete_user_watchlist("missing") is False

    def test_resolve_raw_tickers(self):
        tickers = resolve_universe("AAPL, MSFT")
        assert tickers == ["AAPL", "MSFT"]

    def test_unknown_preset_raises(self):
        with pytest.raises(ValueError):
            resolve_universe("not_a_real_preset_xyz")

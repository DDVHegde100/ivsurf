"""Tests for NYSE holiday calendar."""

from datetime import date

from engine.data.holidays import is_market_holiday, nyse_holidays
from engine.data.sessions import is_trading_day


class TestNYSEHolidays:
    def test_christmas_2025(self):
        holidays = nyse_holidays(2025)
        assert date(2025, 12, 25) in holidays

    def test_good_friday_2025(self):
        assert date(2025, 4, 18) in nyse_holidays(2025)

    def test_independence_day_observed_on_friday_when_july_4_is_saturday(self):
        # July 4, 2026 is Saturday -> observed Friday July 3
        holidays = nyse_holidays(2026)
        assert date(2026, 7, 3) in holidays

    def test_regular_weekday_not_holiday(self):
        assert not is_market_holiday(date(2025, 6, 2))

    def test_is_trading_day_skips_holidays(self):
        assert is_trading_day(date(2025, 12, 25)) is False
        assert is_trading_day(date(2025, 6, 2)) is True
        assert is_trading_day(date(2025, 6, 1)) is False  # Sunday

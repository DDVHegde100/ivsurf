"""NYSE market holiday calendar (no external dependency)."""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


def _easter_sunday(year: int) -> date:
    """Gregorian Easter Sunday (Anonymous algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth weekday (0=Mon) of a month."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last weekday (0=Mon) of a month."""
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last = next_month - timedelta(days=1)
    offset = (last.weekday() - weekday) % 7
    return last - timedelta(days=offset)


def _observe(holiday: date) -> date:
    """NYSE observed-date rules when a holiday falls on a weekend."""
    if holiday.weekday() == 5:  # Saturday
        return holiday - timedelta(days=1)
    if holiday.weekday() == 6:  # Sunday
        return holiday + timedelta(days=1)
    return holiday


def nyse_holidays(year: int) -> frozenset[date]:
    """Return observed NYSE closed dates for a calendar year."""
    holidays: set[date] = set()

    holidays.add(_observe(date(year, 1, 1)))
    holidays.add(_nth_weekday(year, 1, 0, 3))  # MLK
    holidays.add(_nth_weekday(year, 2, 0, 3))  # Presidents Day
    holidays.add(_easter_sunday(year) - timedelta(days=2))  # Good Friday
    holidays.add(_last_weekday(year, 5, 0))  # Memorial Day
    holidays.add(_observe(date(year, 6, 19)))  # Juneteenth
    holidays.add(_observe(date(year, 7, 4)))  # Independence Day
    holidays.add(_nth_weekday(year, 9, 0, 1))  # Labor Day
    holidays.add(_nth_weekday(year, 11, 3, 4))  # Thanksgiving
    holidays.add(_observe(date(year, 12, 25)))  # Christmas

    return frozenset(holidays)


@lru_cache(maxsize=8)
def _holiday_years_cached(start_year: int, end_year: int) -> frozenset[date]:
    out: set[date] = set()
    for year in range(start_year, end_year + 1):
        out.update(nyse_holidays(year))
    return frozenset(out)


def is_market_holiday(d: date) -> bool:
    """True when NYSE is closed for a scheduled holiday."""
    holidays = _holiday_years_cached(d.year - 1, d.year + 1)
    return d in holidays

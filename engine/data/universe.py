"""Watchlist and sector universe management."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_BUILTIN_PATH = Path(__file__).parent / "universes.json"
_DEFAULT_USER_PATH = Path("data/watchlists.json")
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


def _user_watchlist_path() -> Path:
    return Path(os.environ.get("IVSURF_WATCHLIST_PATH", _DEFAULT_USER_PATH))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _normalize_tickers(tickers: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in tickers:
        symbol = raw.strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        out.append(symbol)
    return out


def list_presets() -> dict[str, str]:
    """Return built-in preset names mapped to descriptions."""
    data = _load_json(_BUILTIN_PATH)
    presets = data.get("presets", {})
    return {name: meta.get("description", name) for name, meta in presets.items()}


def list_user_watchlists() -> dict[str, int]:
    """Return user watchlist names mapped to ticker counts."""
    data = _load_json(_user_watchlist_path())
    watchlists = data.get("watchlists", {})
    return {name: len(tickers) for name, tickers in watchlists.items()}


def list_universes() -> dict[str, Any]:
    """Return all available preset and user universe names."""
    return {
        "presets": list_presets(),
        "user_watchlists": list_user_watchlists(),
    }


def get_preset(name: str) -> list[str]:
    """Load tickers for a built-in preset universe."""
    data = _load_json(_BUILTIN_PATH)
    preset = data.get("presets", {}).get(name)
    if preset is None:
        raise KeyError(f"Unknown preset universe: {name}")
    return _normalize_tickers(preset.get("tickers", []))


def get_user_watchlist(name: str) -> list[str]:
    """Load tickers from a saved user watchlist."""
    data = _load_json(_user_watchlist_path())
    watchlists = data.get("watchlists", {})
    if name not in watchlists:
        raise KeyError(f"Unknown user watchlist: {name}")
    return _normalize_tickers(watchlists[name])


def save_user_watchlist(name: str, tickers: list[str]) -> list[str]:
    """Create or update a user watchlist."""
    key = name.strip().lower().replace(" ", "_")
    if not key:
        raise ValueError("Watchlist name is required")

    normalized = _normalize_tickers(tickers)
    if not normalized:
        raise ValueError("Watchlist must contain at least one ticker")

    path = _user_watchlist_path()
    data = _load_json(path)
    watchlists = data.setdefault("watchlists", {})
    watchlists[key] = normalized
    _save_json(path, data)
    return normalized


def delete_user_watchlist(name: str) -> bool:
    """Delete a user watchlist. Returns True if it existed."""
    path = _user_watchlist_path()
    data = _load_json(path)
    watchlists = data.get("watchlists", {})
    if name not in watchlists:
        return False
    del watchlists[name]
    _save_json(path, data)
    return True


def parse_ticker_list(raw: str) -> list[str]:
    """Parse a comma/space-separated ticker string."""
    parts = re.split(r"[\s,]+", raw.strip())
    return _normalize_tickers([p for p in parts if p])


def resolve_universe(source: str) -> list[str]:
    """
    Resolve a universe source to tickers.

    Supported forms:
    - preset name, e.g. ``core``, ``tech_mega``
    - user watchlist, e.g. ``user:my_list`` or ``@my_list``
    - raw ticker list, e.g. ``AAPL, MSFT, NVDA``
    """
    source = source.strip()
    if not source:
        return get_preset(DEFAULT_PRESET)

    if source.startswith("user:"):
        return get_user_watchlist(source[5:])
    if source.startswith("@"):
        return get_user_watchlist(source[1:])

    if "," in source or " " in source:
        tickers = parse_ticker_list(source)
        if tickers and all(_TICKER_RE.match(t) for t in tickers):
            return tickers

    try:
        return get_preset(source)
    except KeyError:
        pass

    try:
        return get_user_watchlist(source)
    except KeyError:
        pass

    tickers = parse_ticker_list(source)
    if tickers and all(_TICKER_RE.match(t) for t in tickers):
        return tickers

    raise ValueError(f"Could not resolve universe source: {source}")


DEFAULT_PRESET = "core"
DEFAULT_UNIVERSE = get_preset(DEFAULT_PRESET)

"""TTL cache for market data responses."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Simple time-to-live in-memory cache."""

    def __init__(self, ttl: timedelta):
        self.ttl = ttl
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if datetime.now() - entry["timestamp"] >= self.ttl:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: T) -> None:
        self._store[key] = {"value": value, "timestamp": datetime.now()}

    def clear(self) -> None:
        self._store.clear()


class MarketDataCache:
    """Shared cache for ticker scan results and options chains."""

    def __init__(self, ttl_minutes: int = 5):
        self._cache = TTLCache[Any](timedelta(minutes=ttl_minutes))

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache.set(key, value)

    def clear(self) -> None:
        self._cache.clear()

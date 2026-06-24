"""Alpaca Markets broker adapter."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from engine.execution.base import OrderSide


class AlpacaBroker:
    """Submit orders via Alpaca REST API."""

    name = "alpaca"

    def __init__(self, *, dry_run: bool = False):
        self._api_key = os.environ.get("ALPACA_API_KEY", "").strip()
        self._secret_key = os.environ.get("ALPACA_SECRET_KEY", "").strip()
        self._base_url = os.environ.get(
            "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
        ).rstrip("/")
        self._dry_run = dry_run

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._secret_key)

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.configured and not self._dry_run:
            raise RuntimeError("Alpaca credentials not configured")

        url = f"{self._base_url}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "APCA-API-KEY-ID": self._api_key or "dry-run",
                "APCA-API-SECRET-KEY": self._secret_key or "dry-run",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()
            raise RuntimeError(f"Alpaca API error {exc.code}: {detail}") from exc

    def get_account(self) -> dict[str, Any]:
        if self._dry_run:
            return {
                "status": "dry_run",
                "buying_power": "100000",
                "equity": "100000",
                "last_equity": "100000",
            }
        payload = self._request("GET", "/v2/account")
        payload["broker"] = self.name
        return payload

    def get_positions(self) -> list[dict[str, Any]]:
        if self._dry_run:
            return []
        payload = self._request("GET", "/v2/positions")
        return payload if isinstance(payload, list) else []

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: OrderSide,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        if qty < 1:
            raise ValueError("qty must be at least 1")

        order = {
            "symbol": symbol.upper(),
            "qty": str(qty),
            "side": side,
            "type": "market",
            "time_in_force": time_in_force,
        }

        if self._dry_run:
            return {"id": "dry-run", "status": "accepted", "broker": self.name, **order}

        result = self._request("POST", "/v2/orders", order)
        result["broker"] = self.name
        return result

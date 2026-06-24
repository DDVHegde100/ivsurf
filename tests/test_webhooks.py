"""Tests for Slack/Discord webhook alerts."""

import json
from unittest.mock import MagicMock, patch

import pytest

from engine.alerts.webhooks import (
    dispatch_scan_alerts,
    format_scan_alert,
    send_discord,
    send_slack,
)


class TestWebhooks:
    def test_format_scan_alert_filters_by_score(self):
        summary = {
            "results": [
                {"ticker": "AAPL", "opening_score": 70, "gap_pct": 2.0, "direction": "up"},
                {"ticker": "MSFT", "opening_score": 30, "gap_pct": 0.5, "direction": "up"},
            ]
        }
        alert = format_scan_alert(summary, min_alert_score=50)
        assert alert["eligible"] is True
        assert len(alert["hits"]) == 1
        assert "AAPL" in alert["text"]

    def test_format_scan_alert_no_hits(self):
        summary = {"results": [{"ticker": "X", "opening_score": 10}]}
        alert = format_scan_alert(summary, min_alert_score=50)
        assert alert["eligible"] is False

    def test_send_slack_dry_run(self):
        result = send_slack("https://hooks.slack.com/test", "hello", dry_run=True)
        assert result["status"] == "dry_run"
        assert result["payload"]["text"] == "hello"

    def test_send_discord_dry_run(self):
        result = send_discord("https://discord.com/api/webhooks/x", "hello", dry_run=True)
        assert result["status"] == "dry_run"

    @patch("engine.alerts.webhooks.urllib.request.urlopen")
    def test_send_slack_live(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"ok"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = send_slack("https://hooks.slack.com/test", "alert")
        assert result["status"] == 200
        mock_urlopen.assert_called_once()

    def test_dispatch_no_webhooks(self, monkeypatch):
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
        summary = {"results": [{"ticker": "AAPL", "opening_score": 80, "gap_pct": 1, "direction": "up"}]}
        result = dispatch_scan_alerts(summary)
        assert result["skipped"] is True
        assert result["reason"] == "no_webhooks_configured"

    def test_dispatch_sends_when_configured(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
        monkeypatch.setenv("IVSURF_ALERT_MIN_SCORE", "50")
        summary = {
            "scanned_at": "2025-06-01T08:00:00",
            "results": [{"ticker": "NVDA", "opening_score": 75, "gap_pct": 3, "direction": "up"}],
        }
        result = dispatch_scan_alerts(summary, dry_run=True)
        assert result["skipped"] is False
        assert len(result["sent"]) == 1
        assert result["hit_count"] == 1

    def test_dispatch_skips_low_scores(self, monkeypatch):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/x")
        summary = {"results": [{"ticker": "X", "opening_score": 20, "gap_pct": 0.1, "direction": "up"}]}
        result = dispatch_scan_alerts(summary, min_alert_score=50, dry_run=True)
        assert result["reason"] == "no_eligible_hits"

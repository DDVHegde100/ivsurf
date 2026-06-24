"""Outbound alert notifications."""

from engine.alerts.webhooks import dispatch_scan_alerts, format_scan_alert

__all__ = ["dispatch_scan_alerts", "format_scan_alert"]

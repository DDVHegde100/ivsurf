"""Slack and Discord webhook alerts for opening scanner hits."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _filter_results(results: list[dict[str, Any]], min_score: float) -> list[dict[str, Any]]:
    return [
        r
        for r in results
        if float(r.get("opening_score", 0)) >= min_score
    ]


def format_scan_alert(
    summary: dict[str, Any],
    *,
    min_alert_score: float = 50.0,
    max_lines: int = 5,
) -> dict[str, Any]:
    """Build alert text and embed payload from a scan summary."""
    if summary.get("skipped"):
        return {
            "eligible": False,
            "text": f"IVSURF scan skipped: {summary.get('reason', 'unknown')}",
            "hits": [],
        }

    hits = _filter_results(summary.get("results", []), min_alert_score)
    if not hits:
        return {
            "eligible": False,
            "text": f"No opening scanner hits at or above score {min_alert_score:.0f}.",
            "hits": [],
        }

    lines = [
        f"*{row['ticker']}* — score {row.get('opening_score', 0):.0f}, "
        f"gap {row.get('gap_pct', 0):+.2f}%, dir {row.get('direction', '?')}"
        for row in hits[:max_lines]
    ]
    header = f"IVSURF opening scan: {len(hits)} hit(s) ≥ {min_alert_score:.0f}"
    text = header + "\n" + "\n".join(lines)
    if len(hits) > max_lines:
        text += f"\n…and {len(hits) - max_lines} more"

    embed = {
        "title": "Opening Volatility Scanner",
        "description": "\n".join(lines),
        "color": 5814783,
        "fields": [
            {"name": "Threshold", "value": f"{min_alert_score:.0f}", "inline": True},
            {"name": "Hits", "value": str(len(hits)), "inline": True},
            {"name": "Scanned", "value": str(summary.get("scanned_at", "—")), "inline": False},
        ],
    }

    return {"eligible": True, "text": text, "hits": hits, "embed": embed}


def send_slack(webhook_url: str, text: str, *, dry_run: bool = False) -> dict[str, Any]:
    """Post a plain-text message to a Slack incoming webhook."""
    payload = {"text": text}
    return _post_json(webhook_url, payload, provider="slack", dry_run=dry_run)


def send_discord(
    webhook_url: str,
    text: str,
    *,
    embed: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Post a message (and optional embed) to a Discord webhook."""
    payload: dict[str, Any] = {"content": text[:2000]}
    if embed is not None:
        payload["embeds"] = [embed]
    return _post_json(webhook_url, payload, provider="discord", dry_run=dry_run)


def _post_json(
    webhook_url: str,
    payload: dict[str, Any],
    *,
    provider: str,
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        return {"provider": provider, "status": "dry_run", "payload": payload}

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            return {"provider": provider, "status": resp.status, "body": body}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{provider} webhook error {exc.code}: {detail}") from exc


def dispatch_scan_alerts(
    summary: dict[str, Any],
    *,
    min_alert_score: float | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Send scan alerts to configured Slack/Discord webhooks.

    Uses SLACK_WEBHOOK_URL and DISCORD_WEBHOOK_URL env vars when set.
    Alert threshold defaults to IVSURF_ALERT_MIN_SCORE or 50.
    """
    threshold = float(
        min_alert_score
        if min_alert_score is not None
        else os.environ.get("IVSURF_ALERT_MIN_SCORE", "50")
    )
    alert = format_scan_alert(summary, min_alert_score=threshold)

    slack_url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    if not slack_url and not discord_url:
        return {
            "sent": [],
            "skipped": True,
            "reason": "no_webhooks_configured",
            "eligible": alert["eligible"],
        }

    if not alert["eligible"]:
        return {
            "sent": [],
            "skipped": True,
            "reason": "no_eligible_hits",
            "eligible": False,
            "threshold": threshold,
        }

    sent: list[dict[str, Any]] = []
    if slack_url:
        sent.append(send_slack(slack_url, alert["text"], dry_run=dry_run))
    if discord_url:
        sent.append(
            send_discord(
                discord_url,
                alert["text"].split("\n", 1)[0],
                embed=alert.get("embed"),
                dry_run=dry_run,
            )
        )

    return {
        "sent": sent,
        "skipped": False,
        "eligible": True,
        "threshold": threshold,
        "hit_count": len(alert["hits"]),
    }

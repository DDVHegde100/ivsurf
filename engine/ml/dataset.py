"""Build labeled training datasets from stored signals."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from engine.signals.ml_ranker import DEFAULT_FEATURES

_POSITIVE_LABEL = "big_mover_up"
_RETURN_THRESHOLD = 0.03


def build_training_dataset(
    labeled_rows: list[dict[str, Any]],
    *,
    return_threshold: float = _RETURN_THRESHOLD,
) -> pd.DataFrame:
    """
    Flatten signal payloads and outcome labels into a training DataFrame.

    Positive class (`label_big_mover_up`) uses the stored outcome label when
    available, otherwise falls back to realized_return >= return_threshold.
    """
    records: list[dict[str, Any]] = []
    for row in labeled_rows:
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        payload = payload or {}

        record: dict[str, Any] = {col: payload.get(col) for col in DEFAULT_FEATURES}
        record["signal_id"] = row.get("id")
        record["ticker"] = row.get("ticker")
        record["created_at"] = row.get("created_at")

        outcome_label = row.get("outcome_label")
        realized_return = row.get("realized_return")
        if outcome_label == _POSITIVE_LABEL:
            record["label_big_mover_up"] = 1
        elif outcome_label in ("big_mover_down", "flat"):
            record["label_big_mover_up"] = 0
        elif realized_return is not None:
            record["label_big_mover_up"] = 1 if float(realized_return) >= return_threshold else 0
        else:
            continue

        records.append(record)

    if not records:
        return pd.DataFrame(columns=[*DEFAULT_FEATURES, "label_big_mover_up"])

    return pd.DataFrame(records)

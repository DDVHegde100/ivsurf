"""3D training history visualization for ML models."""

from __future__ import annotations

import numpy as np


def synthetic_training_history(epochs: int = 40, seed: int = 42) -> dict[str, np.ndarray]:
    """Simulate train/val loss and MAE curves for 3D epoch plots."""
    rng = np.random.default_rng(seed)
    ep = np.arange(1, epochs + 1)
    train_loss = 1.0 * np.exp(-ep / 12) + 0.05 + rng.normal(0, 0.01, epochs)
    val_loss = train_loss * (1 + 0.15 * np.sin(ep / 4)) + 0.08 + rng.normal(0, 0.015, epochs)
    train_mae = 0.5 * np.exp(-ep / 15) + 0.02 + rng.normal(0, 0.005, epochs)
    val_mae = train_mae * 1.1 + 0.03
    return {
        "epoch": ep,
        "train_loss": np.clip(train_loss, 0.01, None),
        "val_loss": np.clip(val_loss, 0.01, None),
        "train_mae": train_mae,
        "val_mae": val_mae,
    }


def training_history_to_3d_grid(history: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Map epoch × metric × value into a surface grid."""
    metrics = np.array([0, 1, 2, 3])  # train_loss, val_loss, train_mae, val_mae
    ep = history["epoch"]
    values = np.vstack([
        history["train_loss"],
        history["val_loss"],
        history["train_mae"],
        history["val_mae"],
    ])
    eg, mg = np.meshgrid(ep, metrics, indexing="ij")
    zg = values.T
    return eg, mg, zg

"""3D ML feature-space projections."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "gap_pct",
    "premarket_volume_ratio",
    "or_15m_range_pct",
    "relative_volume_open",
    "volatility",
    "opening_score",
]


def feature_matrix_from_scan(results: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str]]:
    """Extract numeric feature matrix from scan results."""
    available = [c for c in FEATURE_COLUMNS if c in results.columns]
    if not available:
        raise ValueError("Scan results missing feature columns for PCA")
    matrix = results[available].astype(float).fillna(0.0).values
    tickers = results["ticker"].astype(str).tolist() if "ticker" in results.columns else [f"T{i}" for i in range(len(results))]
    return matrix, tickers, available


def pca_to_3d(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Standardize and project features to 3D via PCA."""
    scaled = StandardScaler().fit_transform(matrix)
    n_components = min(3, scaled.shape[1], scaled.shape[0])
    pca = PCA(n_components=n_components, random_state=42)
    coords = pca.fit_transform(scaled)
    if coords.shape[1] < 3:
        pad = np.zeros((coords.shape[0], 3 - coords.shape[1]))
        coords = np.hstack([coords, pad])
    labels = [f"PC{i+1}" for i in range(3)]
    return coords, pca.explained_variance_ratio_, labels


def scan_results_to_feature_space(results: pd.DataFrame) -> dict[str, Any]:
    """Full PCA bundle for visualization."""
    matrix, tickers, columns = feature_matrix_from_scan(results)
    coords, variance, pc_labels = pca_to_3d(matrix)
    scores = results["opening_score"].astype(float).tolist() if "opening_score" in results.columns else [0.0] * len(tickers)
    return {
        "coords": coords,
        "tickers": tickers,
        "scores": scores,
        "columns": columns,
        "explained_variance": variance.tolist(),
        "pc_labels": pc_labels,
    }

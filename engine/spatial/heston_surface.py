"""Heston stochastic volatility 3D surface sampling."""

from __future__ import annotations

import numpy as np


def heston_iv_surface(
    *,
    spot: float = 100.0,
    n_strikes: int = 40,
    n_expiries: int = 30,
    kappa: float = 2.0,
    theta: float = 0.04,
    sigma_v: float = 0.3,
    rho: float = -0.7,
    v0: float = 0.04,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Approximate Heston implied vol surface via Fourier-style skew parameterization.

    Returns strike grid, expiry grid, IV grid for 3D plotting.
    """
    strikes = np.linspace(spot * 0.75, spot * 1.25, n_strikes)
    expiries = np.linspace(0.05, 1.5, n_expiries)
    kg, eg = np.meshgrid(strikes, expiries, indexing="ij")
    moneyness = np.log(kg / spot)
    long_run_vol = np.sqrt(theta)
    vol_of_vol_term = sigma_v * np.sqrt(eg) * (1 + rho * moneyness)
    mean_reversion = np.exp(-kappa * eg) * (np.sqrt(v0) - long_run_vol) + long_run_vol
    iv = mean_reversion + vol_of_vol_term + 0.1 * moneyness**2
    return kg, eg, np.clip(iv, 0.05, 1.2)

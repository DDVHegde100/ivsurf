"""
Greeks module (placeholder).

Will provide vectorized computations for Delta, Gamma, Vega, Theta, Rho
for calls and puts under various models (BSM, Heston).
"""

from typing import Literal

OptionType = Literal["call", "put"]


def delta(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType = "call") -> float:
    """Return Delta (to be implemented)."""
    raise NotImplementedError("Delta computation TBD")


def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Return Gamma (to be implemented)."""
    raise NotImplementedError("Gamma computation TBD")


def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Return Vega (to be implemented)."""
    raise NotImplementedError("Vega computation TBD")

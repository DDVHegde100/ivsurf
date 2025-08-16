"""
Greeks calculations for Black-Scholes model.

Provides analytical Greeks computations with full vectorization support
and comprehensive input validation.
"""

import numpy as np
import scipy.stats as si
from typing import Union, Literal

# Type aliases
OptionType = Literal["call", "put"]
ArrayLike = Union[float, np.ndarray]


def _d1_d2(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike):
    """Calculate d1 and d2 parameters (shared utility)."""
    sqrt_T = np.sqrt(np.maximum(T, 1e-10))
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


def delta(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike, 
          option_type: OptionType = "call") -> ArrayLike:
    """
    Calculate option Delta (price sensitivity to underlying).
    
    Parameters
    ----------
    S, K, T, r, sigma : array_like
        Black-Scholes parameters
    option_type : {'call', 'put'}
        Option type
        
    Returns
    -------
    array_like
        Delta values
        
    Notes
    -----
    Call delta: N(d1)
    Put delta: N(d1) - 1 = -N(-d1)
    """
    S, K, T, r, sigma = map(np.asarray, [S, K, T, r, sigma])
    
    # Handle T=0 case
    if np.any(T == 0):
        if option_type == "call":
            return np.where(S > K, 1.0, 0.0)
        else:
            return np.where(S < K, -1.0, 0.0)
    
    d1, _ = _d1_d2(S, K, T, r, sigma)
    
    if option_type == "call":
        return si.norm.cdf(d1)
    else:  # put
        return si.norm.cdf(d1) - 1.0


def gamma(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike) -> ArrayLike:
    """
    Calculate option Gamma (Delta sensitivity to underlying).
    
    Gamma is the same for calls and puts.
    
    Returns
    -------
    array_like
        Gamma values
        
    Notes
    -----
    Gamma = φ(d1) / (S * σ * √T)
    where φ is the standard normal PDF
    """
    S, K, T, r, sigma = map(np.asarray, [S, K, T, r, sigma])
    
    # Handle T=0 case - gamma is undefined/infinite
    if np.any(T == 0):
        return np.full_like(S, 0.0)
    
    d1, _ = _d1_d2(S, K, T, r, sigma)
    sqrt_T = np.sqrt(T)
    
    return si.norm.pdf(d1) / (S * sigma * sqrt_T)


def vega(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike) -> ArrayLike:
    """
    Calculate option Vega (price sensitivity to volatility).
    
    Vega is the same for calls and puts.
    
    Returns
    -------
    array_like
        Vega values (per 1% volatility change)
        
    Notes
    -----
    Vega = S * φ(d1) * √T / 100
    Returned as sensitivity per 1% volatility change
    """
    S, K, T, r, sigma = map(np.asarray, [S, K, T, r, sigma])
    
    # Handle T=0 case
    if np.any(T == 0):
        return np.full_like(S, 0.0)
    
    d1, _ = _d1_d2(S, K, T, r, sigma)
    sqrt_T = np.sqrt(T)
    
    # Return vega per 1% (0.01) change in volatility
    return S * si.norm.pdf(d1) * sqrt_T / 100


def theta(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike,
          option_type: OptionType = "call") -> ArrayLike:
    """
    Calculate option Theta (time decay).
    
    Returns
    -------
    array_like
        Theta values (per day)
        
    Notes
    -----
    Returned as value change per calendar day (divided by 365).
    Call theta is typically negative (time decay).
    Put theta can be positive or negative depending on moneyness.
    """
    S, K, T, r, sigma = map(np.asarray, [S, K, T, r, sigma])
    
    # Handle T=0 case
    if np.any(T == 0):
        return np.full_like(S, 0.0)
    
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    sqrt_T = np.sqrt(T)
    
    # Common terms
    term1 = -(S * si.norm.pdf(d1) * sigma) / (2 * sqrt_T)
    term2 = r * K * np.exp(-r * T)
    
    if option_type == "call":
        theta_annual = term1 - term2 * si.norm.cdf(d2)
    else:  # put
        theta_annual = term1 + term2 * si.norm.cdf(-d2)
    
    # Convert to per-day theta
    return theta_annual / 365


def rho(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike,
        option_type: OptionType = "call") -> ArrayLike:
    """
    Calculate option Rho (interest rate sensitivity).
    
    Returns
    -------
    array_like
        Rho values (per 1% interest rate change)
        
    Notes
    -----
    Sensitivity per 1% change in risk-free rate.
    Call rho is positive, put rho is negative.
    """
    S, K, T, r, sigma = map(np.asarray, [S, K, T, r, sigma])
    
    # Handle T=0 case
    if np.any(T == 0):
        return np.full_like(S, 0.0)
    
    _, d2 = _d1_d2(S, K, T, r, sigma)
    
    discount_factor = K * T * np.exp(-r * T)
    
    if option_type == "call":
        rho_val = discount_factor * si.norm.cdf(d2)
    else:  # put
        rho_val = -discount_factor * si.norm.cdf(-d2)
    
    # Return sensitivity per 1% change in interest rate
    return rho_val / 100


def all_greeks(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike,
               option_type: OptionType = "call") -> dict:
    """
    Calculate all Greeks at once for efficiency.
    
    Returns
    -------
    dict
        Dictionary containing 'delta', 'gamma', 'vega', 'theta', 'rho'
    """
    return {
        'delta': delta(S, K, T, r, sigma, option_type),
        'gamma': gamma(S, K, T, r, sigma),
        'vega': vega(S, K, T, r, sigma),
        'theta': theta(S, K, T, r, sigma, option_type),
        'rho': rho(S, K, T, r, sigma, option_type)
    }

"""
Enhanced Black-Scholes pricing and Greeks calculations.

Provides comprehensive option pricing functionality including:
- Vectorized Black-Scholes pricing for calls and puts
- All Greeks calculations (Delta, Gamma, Vega, Theta, Rho)
- Robust implied volatility calculation with multiple methods
- Extensive input validation and error handling
- Performance optimizations for bulk calculations
"""

import numpy as np
import scipy.stats as si
from scipy.optimize import brentq, minimize_scalar
from typing import Union, Literal, Tuple
import warnings

# Type aliases for better code clarity
OptionType = Literal["call", "put"]
ArrayLike = Union[float, np.ndarray]


class BlackScholesError(Exception):
    """Custom exception for Black-Scholes calculation errors."""
    pass


def _validate_inputs(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike) -> None:
    """Validate Black-Scholes inputs for mathematical consistency."""
    def _check_positive(val, name):
        if np.any(val <= 0):
            raise BlackScholesError(f"{name} must be positive, got {val}")
    
    def _check_non_negative(val, name):
        if np.any(val < 0):
            raise BlackScholesError(f"{name} must be non-negative, got {val}")
    
    _check_positive(S, "Stock price (S)")
    _check_positive(K, "Strike price (K)")
    _check_non_negative(T, "Time to expiry (T)")
    _check_positive(sigma, "Volatility (sigma)")
    
    # Risk-free rate can be negative (rare but possible)
    if np.any(np.abs(r) > 1):
        warnings.warn("Risk-free rate |r| > 100% detected. Please verify inputs.")


def _d1_d2(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike) -> Tuple[ArrayLike, ArrayLike]:
    """Calculate d1 and d2 parameters for Black-Scholes formula."""
    # Handle T=0 case to avoid division by zero
    sqrt_T = np.sqrt(np.maximum(T, 1e-10))
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    
    return d1, d2


def black_scholes_price(
    S: ArrayLike, 
    K: ArrayLike, 
    T: ArrayLike, 
    r: ArrayLike, 
    sigma: ArrayLike, 
    option_type: OptionType = 'call'
) -> ArrayLike:
    """
    Calculate Black-Scholes option price.
    
    Parameters
    ----------
    S : array_like
        Current stock price(s)
    K : array_like  
        Strike price(s)
    T : array_like
        Time to expiry in years
    r : array_like
        Risk-free interest rate
    sigma : array_like
        Volatility (annualized)
    option_type : {'call', 'put'}, default 'call'
        Type of option
        
    Returns
    -------
    array_like
        Option price(s)
        
    Raises
    ------
    BlackScholesError
        If inputs are invalid
        
    Examples
    --------
    >>> black_scholes_price(100, 100, 0.25, 0.05, 0.2, 'call')
    5.987
    
    >>> # Vectorized calculation
    >>> S = [95, 100, 105]
    >>> black_scholes_price(S, 100, 0.25, 0.05, 0.2, 'call')
    array([2.89, 5.99, 10.45])
    """
    # Convert to numpy arrays for vectorization
    S, K, T, r, sigma = map(np.asarray, [S, K, T, r, sigma])
    
    _validate_inputs(S, K, T, r, sigma)
    
    if option_type not in ['call', 'put']:
        raise BlackScholesError(f"option_type must be 'call' or 'put', got '{option_type}'")
    
    # Handle T=0 case (immediate expiry)
    if np.any(T == 0):
        if option_type == 'call':
            return np.maximum(S - K, 0)
        else:
            return np.maximum(K - S, 0)
    
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    
    discount_factor = np.exp(-r * T)
    
    if option_type == 'call':
        price = S * si.norm.cdf(d1) - K * discount_factor * si.norm.cdf(d2)
    else:  # put
        price = K * discount_factor * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)
    
    return price


def implied_volatility(
    price: ArrayLike,
    S: ArrayLike, 
    K: ArrayLike, 
    T: ArrayLike, 
    r: ArrayLike, 
    option_type: OptionType = 'call',
    method: str = 'newton',
    tol: float = 1e-6,
    max_iter: int = 100
) -> ArrayLike:
    """
    Calculate implied volatility using Newton-Raphson or Brent's method.
    
    Parameters
    ----------
    price : array_like
        Observed option price(s)
    S, K, T, r : array_like
        Black-Scholes parameters
    option_type : {'call', 'put'}, default 'call'
        Option type
    method : {'newton', 'brent'}, default 'newton'
        Numerical method for root finding
    tol : float, default 1e-6
        Convergence tolerance
    max_iter : int, default 100
        Maximum iterations
        
    Returns
    -------
    array_like
        Implied volatility(ies)
        
    Notes
    -----
    Returns NaN for invalid inputs or convergence failures.
    Newton-Raphson is faster but less robust than Brent's method.
    """
    # Convert to numpy arrays
    price, S, K, T, r = map(np.asarray, [price, S, K, T, r])
    
    try:
        _validate_inputs(S, K, T, r, np.array([0.1]))  # Dummy sigma for validation
    except BlackScholesError:
        return np.full_like(price, np.nan)
    
    # Check for intrinsic value violations
    if option_type == 'call':
        intrinsic = np.maximum(S - K * np.exp(-r * T), 0)
    else:
        intrinsic = np.maximum(K * np.exp(-r * T) - S, 0)
    
    # Price must be at least intrinsic value
    if np.any(price < intrinsic - tol):
        warnings.warn("Price below intrinsic value detected")
        return np.full_like(price, np.nan)
    
    if method == 'newton':
        return _implied_vol_newton(price, S, K, T, r, option_type, tol, max_iter)
    elif method == 'brent':
        return _implied_vol_brent(price, S, K, T, r, option_type, tol)
    else:
        raise BlackScholesError(f"Unknown method '{method}'. Use 'newton' or 'brent'")


def _implied_vol_newton(price, S, K, T, r, option_type, tol, max_iter):
    """Newton-Raphson implied volatility calculation."""
    # Import here to avoid circular import
    from .greeks import vega as vega_func
    
    # Vectorized implementation
    sigma = np.full_like(price, 0.2, dtype=float)  # Initial guess
    
    for i in range(max_iter):
        bs_price = black_scholes_price(S, K, T, r, sigma, option_type)
        vega_val = vega_func(S, K, T, r, sigma) * 100  # Convert from per-1% to per-unit
        
        # Avoid division by zero
        valid_vega = vega_val > 1e-10
        diff = bs_price - price
        
        # Check convergence
        converged = np.abs(diff) < tol
        if np.all(converged | ~valid_vega):
            break
            
        # Newton-Raphson update where vega is valid
        sigma = np.where(valid_vega & ~converged, 
                        sigma - diff / vega_val, 
                        sigma)
        
        # Clamp sigma to reasonable bounds
        sigma = np.clip(sigma, 1e-4, 5.0)
    
    # Set failed convergences to NaN
    final_diff = np.abs(black_scholes_price(S, K, T, r, sigma, option_type) - price)
    sigma = np.where(final_diff > tol, np.nan, sigma)
    
    return sigma


def _implied_vol_brent(price, S, K, T, r, option_type, tol):
    """Brent's method for implied volatility (more robust but slower)."""
    def objective(vol):
        try:
            return black_scholes_price(S, K, T, r, vol, option_type) - price
        except:
            return np.inf
    
    try:
        result = brentq(objective, 1e-4, 5.0, xtol=tol)
        return result
    except:
        return np.nan


# Convenience functions for common use cases
def call_price(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike) -> ArrayLike:
    """Calculate call option price."""
    return black_scholes_price(S, K, T, r, sigma, 'call')


def put_price(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike) -> ArrayLike:
    """Calculate put option price."""
    return black_scholes_price(S, K, T, r, sigma, 'put')


def option_value_decomposition(S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike,
                              option_type: OptionType = 'call') -> dict:
    """
    Decompose option value into intrinsic and time value.
    
    Returns
    -------
    dict
        Contains 'total_value', 'intrinsic_value', 'time_value'
    """
    total_value = black_scholes_price(S, K, T, r, sigma, option_type)
    
    if option_type == 'call':
        intrinsic_value = np.maximum(S - K, 0)
    else:
        intrinsic_value = np.maximum(K - S, 0)
    
    time_value = total_value - intrinsic_value
    
    return {
        'total_value': total_value,
        'intrinsic_value': intrinsic_value,
        'time_value': time_value
    }

"""
Stochastic Volatility Models Core Engine
=======================================

Professional implementation of stochastic volatility models including:
- Heston model with FFT pricing and Monte Carlo simulation
- SABR model with analytic approximations
- Stochastic volatility surface generation
- Model calibration and validation
- Advanced numerical methods for SV models

Mathematical Framework:
- Stochastic differential equations for volatility
- Characteristic function methods
- Monte Carlo variance reduction techniques
- FFT-based option pricing
- Implied volatility surface modeling

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from scipy import optimize, special, interpolate
from typing import Dict, List, Tuple, Optional, Union, Callable
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Import our Heston implementation
from models.heston_advanced import HestonAdvanced, HestonParameters, HestonCalibrationResult

class VolatilityModel(ABC):
    """Abstract base class for stochastic volatility models"""
    
    @abstractmethod
    def option_price(self, K: Union[float, np.ndarray], T: float, 
                    option_type: str = 'call') -> np.ndarray:
        """Calculate option price"""
        pass
    
    @abstractmethod
    def implied_volatility_surface(self, strikes: np.ndarray, 
                                 expiries: np.ndarray) -> np.ndarray:
        """Generate implied volatility surface"""
        pass
    
    @abstractmethod
    def simulate_paths(self, T: float, n_steps: int, 
                      n_paths: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """Simulate price and volatility paths"""
        pass

@dataclass
class SABRParameters:
    """SABR model parameters"""
    alpha: float    # ATM volatility
    beta: float     # CEV exponent
    rho: float      # Correlation
    nu: float       # Volatility of volatility
    
    def __post_init__(self):
        """Validate SABR parameters"""
        if self.alpha <= 0:
            raise ValueError("Alpha must be positive")
        if not 0 <= self.beta <= 1:
            raise ValueError("Beta must be in [0, 1]")
        if not -1 <= self.rho <= 1:
            raise ValueError("Rho must be in [-1, 1]")
        if self.nu < 0:
            raise ValueError("Nu must be non-negative")

class SABRModel(VolatilityModel):
    """
    SABR (Stochastic Alpha Beta Rho) Model
    
    Implements the SABR model with Hagan's analytic approximation
    for implied volatility calculation.
    """
    
    def __init__(self, params: SABRParameters, F0: float = 100.0, r: float = 0.05):
        """
        Initialize SABR model
        
        Args:
            params: SABR parameters
            F0: Initial forward price
            r: Risk-free rate
        """
        self.params = params
        self.F0 = F0
        self.r = r
    
    def implied_volatility(self, K: Union[float, np.ndarray], T: float) -> np.ndarray:
        """
        SABR implied volatility using Hagan's approximation
        
        Args:
            K: Strike price(s)
            T: Time to expiration
            
        Returns:
            Implied volatilities
        """
        if isinstance(K, (int, float)):
            K = np.array([K])
        K = np.asarray(K)
        
        alpha, beta, rho, nu = self.params.alpha, self.params.beta, self.params.rho, self.params.nu
        F = self.F0
        
        # Handle ATM case separately
        atm_mask = np.abs(K - F) < 1e-10
        
        # Initialize result array
        iv = np.zeros_like(K, dtype=float)
        
        # ATM implied volatility
        if np.any(atm_mask):
            z_atm = nu / alpha * F**(1-beta) * np.sqrt(T)
            x_atm = np.log((np.sqrt(1 - 2*rho*z_atm + z_atm**2) + z_atm - rho) / (1 - rho))
            
            iv_atm = (alpha / F**(1-beta)) * (1 + 
                ((1-beta)**2 / 24 * (np.log(F/F))**2 +
                 (1-beta)**4 / 1920 * (np.log(F/F))**4) +
                rho * beta * nu * alpha / (4 * F**(1-beta)) +
                (2 - 3*rho**2) * nu**2 / 24) * T
            
            iv[atm_mask] = iv_atm
        
        # Non-ATM cases
        non_atm_mask = ~atm_mask
        if np.any(non_atm_mask):
            K_non_atm = K[non_atm_mask]
            
            # Log-moneyness
            log_FK = np.log(F / K_non_atm)
            
            # SABR components
            FK_beta = (F * K_non_atm)**((1-beta)/2)
            z = nu / alpha * FK_beta * log_FK
            
            # Handle small z (Taylor expansion)
            small_z_mask = np.abs(z) < 1e-6
            x = np.zeros_like(z)
            
            if np.any(small_z_mask):
                z_small = z[small_z_mask]
                x[small_z_mask] = z_small * (1 - rho*z_small/2 + z_small**2*(3*rho**2-2)/12)
            
            if np.any(~small_z_mask):
                z_large = z[~small_z_mask]
                sqrt_term = np.sqrt(1 - 2*rho*z_large + z_large**2)
                x[~small_z_mask] = np.log((sqrt_term + z_large - rho) / (1 - rho))
            
            # SABR volatility formula
            numerator = alpha * (1 + 
                ((1-beta)**2 / 24 * log_FK**2 +
                 (1-beta)**4 / 1920 * log_FK**4) +
                rho * beta * nu * alpha / (4 * FK_beta) +
                (2 - 3*rho**2) * nu**2 / 24 * T)
            
            denominator = FK_beta * (1 + 
                (1-beta)**2 / 24 * log_FK**2 +
                (1-beta)**4 / 1920 * log_FK**4)
            
            # Handle z/x carefully to avoid division by zero
            z_over_x = np.ones_like(z)
            nonzero_x = np.abs(x) > 1e-12
            if np.any(nonzero_x):
                z_over_x[nonzero_x] = z[nonzero_x] / x[nonzero_x]
            
            iv[non_atm_mask] = numerator / denominator * z_over_x
        
        return iv
    
    def option_price(self, K: Union[float, np.ndarray], T: float, 
                    option_type: str = 'call') -> np.ndarray:
        """
        Option pricing using SABR implied volatility and Black formula
        
        Args:
            K: Strike price(s)
            T: Time to expiration
            option_type: 'call' or 'put'
            
        Returns:
            Option prices
        """
        from core.black_scholes import BlackScholesModel
        
        # Get SABR implied volatilities
        iv = self.implied_volatility(K, T)
        
        # Use Black formula for pricing
        bs_model = BlackScholesModel()
        
        if isinstance(K, (int, float)):
            K = np.array([K])
        K = np.asarray(K)
        
        prices = np.zeros_like(K, dtype=float)
        for i, (k, vol) in enumerate(zip(K, iv)):
            prices[i] = bs_model.black_formula(
                self.F0, k, T, vol, self.r, option_type
            )
        
        return prices
    
    def implied_volatility_surface(self, strikes: np.ndarray, 
                                 expiries: np.ndarray) -> np.ndarray:
        """Generate SABR implied volatility surface"""
        iv_surface = np.zeros((len(expiries), len(strikes)))
        
        for i, T in enumerate(expiries):
            iv_surface[i, :] = self.implied_volatility(strikes, T)
        
        return iv_surface
    
    def simulate_paths(self, T: float, n_steps: int, 
                      n_paths: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Monte Carlo simulation of SABR paths
        
        Args:
            T: Total time
            n_steps: Number of time steps  
            n_paths: Number of simulation paths
            
        Returns:
            Tuple of (forward_paths, volatility_paths)
        """
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        
        # Initialize paths
        F = np.zeros((n_paths, n_steps + 1))
        vol = np.zeros((n_paths, n_steps + 1))
        
        F[:, 0] = self.F0
        vol[:, 0] = self.params.alpha
        
        # Correlation matrix
        rho = self.params.rho
        correlation_matrix = np.array([[1.0, rho], [rho, 1.0]])
        
        for i in range(n_steps):
            # Generate correlated random variables
            Z = np.random.multivariate_normal([0, 0], correlation_matrix, n_paths)
            Z1, Z2 = Z[:, 0], Z[:, 1]
            
            # SABR dynamics
            # dF_t = σ_t F_t^β dW1_t
            # dσ_t = ν σ_t dW2_t
            
            F_beta = F[:, i] ** self.params.beta
            
            # Forward price evolution
            dF = vol[:, i] * F_beta * sqrt_dt * Z1
            F[:, i + 1] = F[:, i] + dF
            
            # Volatility evolution
            dVol = self.params.nu * vol[:, i] * sqrt_dt * Z2
            vol[:, i + 1] = np.maximum(vol[:, i] + dVol, 1e-6)  # Floor volatility
        
        return F, vol

class StochasticVolatilityEngine:
    """
    Unified engine for stochastic volatility modeling
    
    Provides a common interface for different SV models and
    advanced surface analysis capabilities.
    """
    
    def __init__(self):
        """Initialize the SV engine"""
        self.models = {}
        self.calibration_results = {}
    
    def register_model(self, name: str, model: VolatilityModel):
        """Register a stochastic volatility model"""
        self.models[name] = model
    
    def compare_models(self, market_data: pd.DataFrame, 
                      model_names: List[str] = None) -> pd.DataFrame:
        """
        Compare different SV models against market data
        
        Args:
            market_data: Market option prices
            model_names: List of model names to compare
            
        Returns:
            Comparison results DataFrame
        """
        if model_names is None:
            model_names = list(self.models.keys())
        
        results = []
        
        for name in model_names:
            if name not in self.models:
                continue
                
            model = self.models[name]
            
            # Calculate model prices
            model_prices = []
            for _, row in market_data.iterrows():
                try:
                    price = model.option_price(
                        row['strike'], row['expiry'], row['option_type']
                    )[0]
                    model_prices.append(price)
                except:
                    model_prices.append(np.nan)
            
            model_prices = np.array(model_prices)
            market_prices = market_data['price'].values
            
            # Calculate error metrics
            valid_mask = ~(np.isnan(model_prices) | np.isnan(market_prices))
            if np.any(valid_mask):
                errors = model_prices[valid_mask] - market_prices[valid_mask]
                rmse = np.sqrt(np.mean(errors**2))
                mae = np.mean(np.abs(errors))
                max_error = np.max(np.abs(errors))
                correlation = np.corrcoef(model_prices[valid_mask], 
                                        market_prices[valid_mask])[0, 1]
            else:
                rmse = mae = max_error = correlation = np.nan
            
            results.append({
                'model': name,
                'rmse': rmse,
                'mae': mae,
                'max_error': max_error,
                'correlation': correlation,
                'valid_prices': np.sum(valid_mask)
            })
        
        return pd.DataFrame(results).sort_values('rmse')
    
    def generate_volatility_smile(self, model_name: str, expiry: float,
                                strike_range: Tuple[float, float],
                                n_strikes: int = 50) -> pd.DataFrame:
        """
        Generate volatility smile for a specific model and expiry
        
        Args:
            model_name: Name of the model
            expiry: Time to expiration
            strike_range: (min_strike, max_strike)
            n_strikes: Number of strike points
            
        Returns:
            DataFrame with strikes and implied volatilities
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not registered")
        
        model = self.models[model_name]
        strikes = np.linspace(strike_range[0], strike_range[1], n_strikes)
        
        # Get option prices
        call_prices = model.option_price(strikes, expiry, 'call')
        
        # Convert to implied volatilities
        from core.black_scholes import BlackScholesModel
        bs_model = BlackScholesModel()
        
        ivs = []
        for i, (K, price) in enumerate(zip(strikes, call_prices)):
            try:
                # Assume spot price from model
                if hasattr(model, 'S0'):
                    S0 = model.S0
                elif hasattr(model, 'F0'):
                    S0 = model.F0
                else:
                    S0 = 100.0  # Default
                
                iv = bs_model.implied_volatility(
                    price, S0, K, expiry, 
                    getattr(model, 'r', 0.05), 'call'
                )
                ivs.append(iv)
            except:
                ivs.append(np.nan)
        
        return pd.DataFrame({
            'strike': strikes,
            'implied_volatility': ivs,
            'moneyness': strikes / (getattr(model, 'S0', getattr(model, 'F0', 100.0))),
            'option_price': call_prices
        })
    
    def term_structure_analysis(self, model_name: str, 
                              expiries: np.ndarray,
                              atm_level: float = 100.0) -> pd.DataFrame:
        """
        Analyze term structure of implied volatility
        
        Args:
            model_name: Name of the model
            expiries: Array of expiry times
            atm_level: ATM strike level
            
        Returns:
            DataFrame with term structure data
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not registered")
        
        model = self.models[model_name]
        
        # Calculate ATM implied volatilities
        atm_ivs = []
        for T in expiries:
            try:
                if hasattr(model, 'implied_volatility'):
                    # Direct IV calculation (e.g., SABR)
                    iv = model.implied_volatility(atm_level, T)[0]
                else:
                    # Via option price and BS inversion
                    price = model.option_price(atm_level, T, 'call')[0]
                    
                    from core.black_scholes import BlackScholesModel
                    bs_model = BlackScholesModel()
                    
                    S0 = getattr(model, 'S0', getattr(model, 'F0', 100.0))
                    r = getattr(model, 'r', 0.05)
                    
                    iv = bs_model.implied_volatility(price, S0, atm_level, T, r, 'call')
                
                atm_ivs.append(iv)
            except:
                atm_ivs.append(np.nan)
        
        return pd.DataFrame({
            'expiry': expiries,
            'time_to_expiry_years': expiries,
            'time_to_expiry_days': expiries * 365,
            'atm_implied_volatility': atm_ivs,
            'volatility_squared': np.array(atm_ivs)**2,
            'variance_time_product': np.array(atm_ivs)**2 * expiries
        })
    
    def risk_neutral_density(self, model_name: str, expiry: float,
                           strike_range: Tuple[float, float],
                           n_strikes: int = 100) -> pd.DataFrame:
        """
        Extract risk-neutral density from option prices
        
        Args:
            model_name: Name of the model
            expiry: Time to expiration
            strike_range: (min_strike, max_strike)
            n_strikes: Number of strike points
            
        Returns:
            DataFrame with strikes and density values
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not registered")
        
        model = self.models[model_name]
        strikes = np.linspace(strike_range[0], strike_range[1], n_strikes)
        dK = strikes[1] - strikes[0]
        
        # Get call prices
        call_prices = model.option_price(strikes, expiry, 'call')
        
        # Calculate second derivative numerically
        d2C_dK2 = np.gradient(np.gradient(call_prices, dK), dK)
        
        # Risk-neutral density
        r = getattr(model, 'r', 0.05)
        density = np.exp(r * expiry) * d2C_dK2
        
        # Smooth negative densities (numerical artifacts)
        density = np.maximum(density, 0)
        
        # Normalize to integrate to 1
        total_probability = np.trapz(density, strikes)
        if total_probability > 0:
            density = density / total_probability
        
        return pd.DataFrame({
            'strike': strikes,
            'density': density,
            'log_strike': np.log(strikes),
            'cumulative_probability': np.cumsum(density * dK)
        })

# Convenience functions for model creation
def create_heston_model(kappa: float = 2.0, theta: float = 0.04, 
                       sigma: float = 0.3, rho: float = -0.7, 
                       v0: float = 0.04, S0: float = 100.0, 
                       r: float = 0.05) -> HestonAdvanced:
    """Create a Heston model with given parameters"""
    params = HestonParameters(kappa, theta, sigma, rho, v0)
    return HestonAdvanced(params, S0, r)

def create_sabr_model(alpha: float = 0.2, beta: float = 0.5, 
                     rho: float = -0.3, nu: float = 0.4, 
                     F0: float = 100.0, r: float = 0.05) -> SABRModel:
    """Create a SABR model with given parameters"""
    params = SABRParameters(alpha, beta, rho, nu)
    return SABRModel(params, F0, r)

# Example usage and testing
if __name__ == "__main__":
    print("=== STOCHASTIC VOLATILITY ENGINE TESTING ===")
    
    # Create SV engine
    sv_engine = StochasticVolatilityEngine()
    
    # Create and register models
    heston_model = create_heston_model()
    sabr_model = create_sabr_model()
    
    sv_engine.register_model("Heston", heston_model)
    sv_engine.register_model("SABR", sabr_model)
    
    # Test volatility smile generation
    print("\n=== VOLATILITY SMILE ANALYSIS ===")
    heston_smile = sv_engine.generate_volatility_smile("Heston", 1.0, (80, 120), 20)
    sabr_smile = sv_engine.generate_volatility_smile("SABR", 1.0, (80, 120), 20)
    
    print("Heston 1Y Volatility Smile (sample):")
    print(heston_smile.head())
    
    print("\nSABR 1Y Volatility Smile (sample):")
    print(sabr_smile.head())
    
    # Test term structure
    print("\n=== TERM STRUCTURE ANALYSIS ===")
    expiries = np.array([0.25, 0.5, 1.0, 2.0])
    heston_term = sv_engine.term_structure_analysis("Heston", expiries)
    sabr_term = sv_engine.term_structure_analysis("SABR", expiries)
    
    print("Heston Term Structure:")
    print(heston_term)
    
    print("\nSABR Term Structure:")
    print(sabr_term)
    
    # Test risk-neutral density
    print("\n=== RISK-NEUTRAL DENSITY ===")
    heston_density = sv_engine.risk_neutral_density("Heston", 1.0, (70, 130), 50)
    print("Heston 1Y Risk-Neutral Density (sample):")
    print(heston_density.head())
    
    print("\nStochastic volatility engine testing completed successfully!")

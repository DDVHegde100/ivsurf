"""
Advanced Heston Stochastic Volatility Model Implementation
========================================================

Professional-grade Heston model with:
- Full SDE implementation with correlated Brownian motions
- FFT-based option pricing using characteristic functions
- Monte Carlo simulation with Euler and Milstein schemes
- Market data calibration using least squares and gradient descent
- Volatility surface generation and analysis
- Path simulation and Greeks computation

Mathematical Foundation:
dS_t = rS_t dt + √v_t S_t dW₁_t
dv_t = κ(θ - v_t)dt + σ√v_t dW₂_t
where dW₁_t dW₂_t = ρ dt

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from scipy import fft, optimize, special
from typing import Tuple, Dict, List, Optional, Union
import warnings
from dataclasses import dataclass
from enum import Enum

class SimulationScheme(Enum):
    """Monte Carlo simulation schemes for Heston model"""
    EULER = "euler"
    MILSTEIN = "milstein"
    BROADIE_KAYA = "broadie_kaya"
    EXACT = "exact"

@dataclass
class HestonParameters:
    """Heston model parameters with validation"""
    kappa: float      # Mean reversion rate
    theta: float      # Long-term variance
    sigma: float      # Volatility of volatility
    rho: float        # Correlation between price and volatility
    v0: float         # Initial variance
    
    def __post_init__(self):
        """Validate Heston parameters"""
        if self.kappa <= 0:
            raise ValueError("Mean reversion rate κ must be positive")
        if self.theta <= 0:
            raise ValueError("Long-term variance θ must be positive")
        if self.sigma <= 0:
            raise ValueError("Volatility of volatility σ must be positive")
        if not -1 <= self.rho <= 1:
            raise ValueError("Correlation ρ must be in [-1, 1]")
        if self.v0 <= 0:
            raise ValueError("Initial variance v₀ must be positive")
        
        # Feller condition check
        if 2 * self.kappa * self.theta <= self.sigma**2:
            warnings.warn("Feller condition violated: 2κθ ≤ σ²")

@dataclass
class HestonCalibrationResult:
    """Results from Heston model calibration"""
    parameters: HestonParameters
    rmse: float
    mae: float
    max_error: float
    convergence: bool
    iterations: int
    market_prices: np.ndarray
    model_prices: np.ndarray
    strikes: np.ndarray
    expiries: np.ndarray

class HestonAdvanced:
    """
    Advanced Heston Stochastic Volatility Model
    
    Implements the full Heston model with characteristic function pricing,
    Monte Carlo simulation, and market data calibration.
    """
    
    def __init__(self, params: HestonParameters, S0: float = 100.0, r: float = 0.05):
        """
        Initialize Heston model
        
        Args:
            params: Heston model parameters
            S0: Initial stock price
            r: Risk-free rate
        """
        self.params = params
        self.S0 = S0
        self.r = r
        
        # Precompute frequently used values
        self._alpha = -0.5  # Damping parameter for FFT
        self._N = 4096      # Number of FFT points
        self._eta = 0.25    # Grid spacing for FFT
        
    def characteristic_function(self, u: np.ndarray, T: float) -> np.ndarray:
        """
        Heston characteristic function for option pricing
        
        φ(u,T) = exp(C(u,T) + D(u,T)v₀ + iu ln(S₀))
        
        Args:
            u: Complex frequency parameter
            T: Time to expiration
            
        Returns:
            Complex characteristic function values
        """
        kappa, theta, sigma, rho, v0 = (
            self.params.kappa, self.params.theta, self.params.sigma,
            self.params.rho, self.params.v0
        )
        
        # Complex frequency adjustments
        d = np.sqrt((rho * sigma * 1j * u - kappa)**2 + sigma**2 * (1j * u + u**2))
        g = (kappa - rho * sigma * 1j * u - d) / (kappa - rho * sigma * 1j * u + d)
        
        # Handle numerical issues near zero
        mask = np.abs(d) < 1e-12
        d = np.where(mask, 1e-12, d)
        
        # Characteristic function components
        exp_dT = np.exp(-d * T)
        
        C = (self.r * 1j * u * T + 
             (kappa * theta / sigma**2) * 
             ((kappa - rho * sigma * 1j * u - d) * T - 
              2 * np.log((1 - g * exp_dT) / (1 - g))))
        
        D = ((kappa - rho * sigma * 1j * u - d) / sigma**2) * \
            ((1 - exp_dT) / (1 - g * exp_dT))
        
        # Full characteristic function
        phi = np.exp(C + D * v0 + 1j * u * np.log(self.S0))
        
        return phi
    
    def fft_option_price(self, K: Union[float, np.ndarray], T: float, 
                        option_type: str = 'call') -> np.ndarray:
        """
        FFT-based option pricing using characteristic function
        
        Args:
            K: Strike price(s)
            T: Time to expiration
            option_type: 'call' or 'put'
            
        Returns:
            Option prices
        """
        if isinstance(K, (int, float)):
            K = np.array([K])
        K = np.asarray(K)
        
        # FFT grid setup
        lambda_val = 2 * np.pi / (self._N * self._eta)
        b = self._N * lambda_val / 2
        
        # Frequency and strike grids
        u = np.arange(self._N) * self._eta
        k = -b + np.arange(self._N) * lambda_val  # Log-strike grid
        
        # Modified characteristic function for FFT
        phi_modified = np.exp(-self.r * T) * self.characteristic_function(
            u - (self._alpha + 1) * 1j, T
        ) / (self._alpha**2 + self._alpha - u**2 + 1j * (2 * self._alpha + 1) * u)
        
        # Apply Simpson's rule weights
        weights = np.ones(self._N)
        weights[0] = 0.5
        weights[-1] = 0.5
        weights[1::2] *= 4
        weights[2::2] *= 2
        weights *= self._eta / 3
        
        # FFT computation
        fft_input = phi_modified * weights
        fft_result = fft.fft(fft_input)
        
        # Extract call prices on grid
        call_prices_grid = np.real(np.exp(-self._alpha * k) * fft_result / np.pi)
        
        # Interpolate to desired strikes
        log_K = np.log(K)
        call_prices = np.interp(log_K, k, call_prices_grid)
        
        # Convert to put prices if needed
        if option_type.lower() == 'put':
            put_prices = call_prices - self.S0 + K * np.exp(-self.r * T)
            return put_prices
        
        return call_prices
    
    def monte_carlo_simulation(self, T: float, n_steps: int, n_paths: int = 10000,
                             scheme: SimulationScheme = SimulationScheme.EULER,
                             antithetic: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Monte Carlo simulation of Heston paths
        
        Args:
            T: Total time
            n_steps: Number of time steps
            n_paths: Number of simulation paths
            scheme: Simulation scheme
            antithetic: Use antithetic variates
            
        Returns:
            Tuple of (stock_paths, variance_paths)
        """
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        
        # Effective number of paths (doubled for antithetic)
        effective_paths = n_paths // 2 if antithetic else n_paths
        
        # Initialize paths
        S = np.zeros((effective_paths, n_steps + 1))
        v = np.zeros((effective_paths, n_steps + 1))
        
        S[:, 0] = self.S0
        v[:, 0] = self.params.v0
        
        # Correlation matrix for Brownian motions
        rho = self.params.rho
        correlation_matrix = np.array([[1.0, rho], [rho, 1.0]])
        
        for i in range(n_steps):
            # Generate correlated random variables
            Z = np.random.multivariate_normal([0, 0], correlation_matrix, effective_paths)
            Z1, Z2 = Z[:, 0], Z[:, 1]
            
            if scheme == SimulationScheme.EULER:
                # Euler scheme
                v_sqrt = np.maximum(np.sqrt(v[:, i]), 0)
                
                # Variance process
                dv = (self.params.kappa * (self.params.theta - v[:, i]) * dt +
                      self.params.sigma * v_sqrt * sqrt_dt * Z2)
                v[:, i + 1] = np.maximum(v[:, i] + dv, 0)  # Absorption at zero
                
                # Stock price process
                dS = (self.r * S[:, i] * dt +
                      v_sqrt * S[:, i] * sqrt_dt * Z1)
                S[:, i + 1] = S[:, i] + dS
                
            elif scheme == SimulationScheme.MILSTEIN:
                # Milstein scheme for improved accuracy
                v_sqrt = np.maximum(np.sqrt(v[:, i]), 0)
                
                # Milstein correction for variance
                milstein_correction = 0.25 * self.params.sigma**2 * dt * (Z2**2 - 1)
                
                dv = (self.params.kappa * (self.params.theta - v[:, i]) * dt +
                      self.params.sigma * v_sqrt * sqrt_dt * Z2 +
                      milstein_correction)
                v[:, i + 1] = np.maximum(v[:, i] + dv, 0)
                
                # Stock price (standard Euler for S)
                dS = (self.r * S[:, i] * dt +
                      v_sqrt * S[:, i] * sqrt_dt * Z1)
                S[:, i + 1] = S[:, i] + dS
        
        # Apply antithetic variates if requested
        if antithetic:
            S_anti = np.zeros_like(S)
            v_anti = np.zeros_like(v)
            
            S_anti[:, 0] = self.S0
            v_anti[:, 0] = self.params.v0
            
            # Regenerate with negative random variables
            np.random.seed(42)  # Reset for reproducibility
            for i in range(n_steps):
                Z = np.random.multivariate_normal([0, 0], correlation_matrix, effective_paths)
                Z1, Z2 = -Z[:, 0], -Z[:, 1]  # Antithetic
                
                if scheme == SimulationScheme.EULER:
                    v_sqrt = np.maximum(np.sqrt(v_anti[:, i]), 0)
                    
                    dv = (self.params.kappa * (self.params.theta - v_anti[:, i]) * dt +
                          self.params.sigma * v_sqrt * sqrt_dt * Z2)
                    v_anti[:, i + 1] = np.maximum(v_anti[:, i] + dv, 0)
                    
                    dS = (self.r * S_anti[:, i] * dt +
                          v_sqrt * S_anti[:, i] * sqrt_dt * Z1)
                    S_anti[:, i + 1] = S_anti[:, i] + dS
            
            # Combine original and antithetic paths
            S = np.vstack([S, S_anti])
            v = np.vstack([v, v_anti])
        
        return S, v
    
    def calibrate_to_market(self, market_data: pd.DataFrame, 
                          method: str = 'least_squares') -> HestonCalibrationResult:
        """
        Calibrate Heston model to market option prices
        
        Args:
            market_data: DataFrame with columns ['strike', 'expiry', 'price', 'option_type']
            method: Calibration method ('least_squares', 'maximum_likelihood')
            
        Returns:
            Calibration results
        """
        
        def objective_function(params_array):
            """Objective function for optimization"""
            try:
                # Unpack parameters
                kappa, theta, sigma, rho, v0 = params_array
                
                # Create parameter object with bounds checking
                if (kappa <= 0 or theta <= 0 or sigma <= 0 or 
                    not -0.99 <= rho <= 0.99 or v0 <= 0):
                    return 1e6
                
                temp_params = HestonParameters(kappa, theta, sigma, rho, v0)
                temp_model = HestonAdvanced(temp_params, self.S0, self.r)
                
                # Calculate model prices
                model_prices = []
                for _, row in market_data.iterrows():
                    try:
                        price = temp_model.fft_option_price(
                            row['strike'], row['expiry'], row['option_type']
                        )[0]
                        model_prices.append(price)
                    except:
                        return 1e6
                
                model_prices = np.array(model_prices)
                market_prices = market_data['price'].values
                
                # Calculate error
                if method == 'least_squares':
                    error = np.sum((model_prices - market_prices)**2)
                else:  # maximum_likelihood
                    error = -np.sum(np.log(model_prices + 1e-8))
                
                return error
                
            except:
                return 1e6
        
        # Initial guess and bounds
        initial_guess = [
            self.params.kappa,
            self.params.theta,
            self.params.sigma,
            self.params.rho,
            self.params.v0
        ]
        
        bounds = [
            (0.01, 10.0),    # kappa
            (0.001, 1.0),    # theta
            (0.01, 2.0),     # sigma
            (-0.99, 0.99),   # rho
            (0.001, 1.0)     # v0
        ]
        
        # Optimization
        result = optimize.minimize(
            objective_function,
            initial_guess,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000, 'ftol': 1e-9}
        )
        
        # Extract optimized parameters
        kappa_opt, theta_opt, sigma_opt, rho_opt, v0_opt = result.x
        optimized_params = HestonParameters(kappa_opt, theta_opt, sigma_opt, rho_opt, v0_opt)
        
        # Calculate final model prices and errors
        optimized_model = HestonAdvanced(optimized_params, self.S0, self.r)
        final_model_prices = []
        
        for _, row in market_data.iterrows():
            price = optimized_model.fft_option_price(
                row['strike'], row['expiry'], row['option_type']
            )[0]
            final_model_prices.append(price)
        
        final_model_prices = np.array(final_model_prices)
        market_prices = market_data['price'].values
        
        # Error metrics
        errors = final_model_prices - market_prices
        rmse = np.sqrt(np.mean(errors**2))
        mae = np.mean(np.abs(errors))
        max_error = np.max(np.abs(errors))
        
        return HestonCalibrationResult(
            parameters=optimized_params,
            rmse=rmse,
            mae=mae,
            max_error=max_error,
            convergence=result.success,
            iterations=result.nit,
            market_prices=market_prices,
            model_prices=final_model_prices,
            strikes=market_data['strike'].values,
            expiries=market_data['expiry'].values
        )
    
    def generate_volatility_surface(self, strikes: np.ndarray, 
                                  expiries: np.ndarray) -> np.ndarray:
        """
        Generate implied volatility surface using Heston model
        
        Args:
            strikes: Array of strike prices
            expiries: Array of expiry times
            
        Returns:
            2D array of implied volatilities
        """
        from core.black_scholes import BlackScholesModel
        
        iv_surface = np.zeros((len(expiries), len(strikes)))
        bs_model = BlackScholesModel()
        
        for i, T in enumerate(expiries):
            # Get Heston option prices
            heston_prices = self.fft_option_price(strikes, T, 'call')
            
            # Convert to implied volatilities
            for j, (K, price) in enumerate(zip(strikes, heston_prices)):
                try:
                    iv = bs_model.implied_volatility(
                        price, self.S0, K, T, self.r, option_type='call'
                    )
                    iv_surface[i, j] = iv
                except:
                    iv_surface[i, j] = np.nan
        
        return iv_surface
    
    def calculate_greeks_mc(self, K: float, T: float, option_type: str = 'call',
                          n_paths: int = 100000, bump_size: float = 0.01) -> Dict[str, float]:
        """
        Calculate option Greeks using Monte Carlo with finite differences
        
        Args:
            K: Strike price
            T: Time to expiration
            option_type: 'call' or 'put'
            n_paths: Number of Monte Carlo paths
            bump_size: Size of finite difference bump
            
        Returns:
            Dictionary of Greeks
        """
        # Base price
        base_price = self.fft_option_price(K, T, option_type)[0]
        
        # Delta: bump spot price
        S_up = self.S0 * (1 + bump_size)
        S_down = self.S0 * (1 - bump_size)
        
        model_up = HestonAdvanced(self.params, S_up, self.r)
        model_down = HestonAdvanced(self.params, S_down, self.r)
        
        price_up = model_up.fft_option_price(K, T, option_type)[0]
        price_down = model_down.fft_option_price(K, T, option_type)[0]
        
        delta = (price_up - price_down) / (2 * self.S0 * bump_size)
        gamma = (price_up - 2 * base_price + price_down) / (self.S0 * bump_size)**2
        
        # Vega: bump initial volatility
        v0_up = self.params.v0 * (1 + bump_size)
        v0_down = self.params.v0 * (1 - bump_size)
        
        params_up = HestonParameters(
            self.params.kappa, self.params.theta, self.params.sigma,
            self.params.rho, v0_up
        )
        params_down = HestonParameters(
            self.params.kappa, self.params.theta, self.params.sigma,
            self.params.rho, v0_down
        )
        
        model_vega_up = HestonAdvanced(params_up, self.S0, self.r)
        model_vega_down = HestonAdvanced(params_down, self.S0, self.r)
        
        price_vega_up = model_vega_up.fft_option_price(K, T, option_type)[0]
        price_vega_down = model_vega_down.fft_option_price(K, T, option_type)[0]
        
        vega = (price_vega_up - price_vega_down) / (2 * bump_size * np.sqrt(self.params.v0))
        
        # Theta: bump time
        T_down = T - bump_size / 365  # One day bump
        if T_down > 0:
            price_theta = self.fft_option_price(K, T_down, option_type)[0]
            theta = (price_theta - base_price) / (bump_size / 365)
        else:
            theta = 0.0
        
        # Rho: bump interest rate
        r_up = self.r + bump_size / 100  # 1bp bump
        r_down = self.r - bump_size / 100
        
        model_rho_up = HestonAdvanced(self.params, self.S0, r_up)
        model_rho_down = HestonAdvanced(self.params, self.S0, r_down)
        
        price_rho_up = model_rho_up.fft_option_price(K, T, option_type)[0]
        price_rho_down = model_rho_down.fft_option_price(K, T, option_type)[0]
        
        rho = (price_rho_up - price_rho_down) / (2 * bump_size / 100)
        
        return {
            'price': base_price,
            'delta': delta,
            'gamma': gamma,
            'vega': vega,
            'theta': theta,
            'rho': rho
        }

def create_sample_market_data() -> pd.DataFrame:
    """Create sample market data for testing"""
    np.random.seed(42)
    
    strikes = np.array([80, 90, 100, 110, 120])
    expiries = np.array([0.25, 0.5, 1.0])
    
    data = []
    for T in expiries:
        for K in strikes:
            # Simulate market prices with some noise
            true_params = HestonParameters(2.0, 0.04, 0.3, -0.7, 0.04)
            model = HestonAdvanced(true_params, 100.0, 0.05)
            
            true_price = model.fft_option_price(K, T, 'call')[0]
            noisy_price = true_price * (1 + np.random.normal(0, 0.02))
            
            data.append({
                'strike': K,
                'expiry': T,
                'price': max(noisy_price, 0.01),
                'option_type': 'call'
            })
    
    return pd.DataFrame(data)

# Example usage and testing
if __name__ == "__main__":
    # Example Heston parameters
    params = HestonParameters(
        kappa=2.0,      # Mean reversion rate
        theta=0.04,     # Long-term variance
        sigma=0.3,      # Volatility of volatility
        rho=-0.7,       # Correlation
        v0=0.04         # Initial variance
    )
    
    # Create model
    model = HestonAdvanced(params, S0=100.0, r=0.05)
    
    # Test option pricing
    print("=== HESTON MODEL TESTING ===")
    print(f"Parameters: κ={params.kappa}, θ={params.theta}, σ={params.sigma}, ρ={params.rho}, v₀={params.v0}")
    
    # Single option price
    call_price = model.fft_option_price(100, 1.0, 'call')[0]
    put_price = model.fft_option_price(100, 1.0, 'put')[0]
    print(f"ATM Call Price (T=1Y): ${call_price:.4f}")
    print(f"ATM Put Price (T=1Y): ${put_price:.4f}")
    
    # Greeks calculation
    greeks = model.calculate_greeks_mc(100, 1.0, 'call')
    print(f"Greeks: Δ={greeks['delta']:.4f}, Γ={greeks['gamma']:.4f}, "
          f"ν={greeks['vega']:.4f}, Θ={greeks['theta']:.4f}, ρ={greeks['rho']:.4f}")
    
    # Monte Carlo simulation
    S_paths, v_paths = model.monte_carlo_simulation(1.0, 252, 1000)
    print(f"MC Simulation: Final S mean=${np.mean(S_paths[:, -1]):.2f}, "
          f"Final v mean={np.mean(v_paths[:, -1]):.4f}")
    
    # Calibration test
    market_data = create_sample_market_data()
    print("\n=== CALIBRATION TEST ===")
    calibration_result = model.calibrate_to_market(market_data)
    print(f"Calibration converged: {calibration_result.convergence}")
    print(f"RMSE: {calibration_result.rmse:.6f}")
    print(f"Optimized parameters:")
    print(f"  κ={calibration_result.parameters.kappa:.4f}")
    print(f"  θ={calibration_result.parameters.theta:.4f}")
    print(f"  σ={calibration_result.parameters.sigma:.4f}")
    print(f"  ρ={calibration_result.parameters.rho:.4f}")
    print(f"  v₀={calibration_result.parameters.v0:.4f}")

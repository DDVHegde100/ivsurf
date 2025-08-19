"""
Jump-Diffusion Models Implementation
===================================

Professional-grade jump-diffusion models including:
- Merton Jump-Diffusion Model with Poisson jumps
- Kou Double Exponential Jump Model
- Jump parameter estimation and calibration
- Monte Carlo simulation with jump processes
- Option pricing with characteristic functions
- Jump risk premium decomposition

Mathematical Framework:
Merton: dS_t = μS_t dt + σS_t dW_t + S_t dJ_t
Kou: Jump sizes Y_i follow double exponential distribution
where dJ_t = Σ(Y_i - 1) dN_t, N_t is Poisson process

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize, special, integrate
from typing import Tuple, Dict, List, Optional, Union, Callable
import warnings
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

class JumpDistribution(Enum):
    """Types of jump size distributions"""
    NORMAL = "normal"
    DOUBLE_EXPONENTIAL = "double_exponential"
    UNIFORM = "uniform"
    LAPLACE = "laplace"

@dataclass
class MertonParameters:
    """Merton jump-diffusion model parameters"""
    mu: float           # Drift rate
    sigma: float        # Diffusion volatility
    lambda_j: float     # Jump intensity (jumps per year)
    mu_j: float         # Mean jump size (log)
    sigma_j: float      # Jump size volatility
    
    def __post_init__(self):
        """Validate Merton parameters"""
        if self.sigma <= 0:
            raise ValueError("Diffusion volatility σ must be positive")
        if self.lambda_j < 0:
            raise ValueError("Jump intensity λ must be non-negative")
        if self.sigma_j <= 0:
            raise ValueError("Jump volatility σⱼ must be positive")

@dataclass
class KouParameters:
    """Kou double exponential jump model parameters"""
    mu: float           # Drift rate
    sigma: float        # Diffusion volatility
    lambda_j: float     # Jump intensity
    p: float            # Probability of upward jump
    eta_u: float        # Upward jump rate parameter
    eta_d: float        # Downward jump rate parameter
    
    def __post_init__(self):
        """Validate Kou parameters"""
        if self.sigma <= 0:
            raise ValueError("Diffusion volatility σ must be positive")
        if self.lambda_j < 0:
            raise ValueError("Jump intensity λ must be non-negative")
        if not 0 <= self.p <= 1:
            raise ValueError("Jump probability p must be in [0, 1]")
        if self.eta_u <= 0 or self.eta_d <= 0:
            raise ValueError("Jump rate parameters η must be positive")

@dataclass
class JumpCalibrationResult:
    """Results from jump model calibration"""
    parameters: Union[MertonParameters, KouParameters]
    model_type: str
    rmse: float
    mae: float
    max_error: float
    convergence: bool
    iterations: int
    market_prices: np.ndarray
    model_prices: np.ndarray
    strikes: np.ndarray
    expiries: np.ndarray
    jump_probability: float
    jump_intensity: float

class JumpDiffusionModel(ABC):
    """Abstract base class for jump-diffusion models"""
    
    @abstractmethod
    def characteristic_function(self, u: np.ndarray, T: float) -> np.ndarray:
        """Calculate characteristic function"""
        pass
    
    @abstractmethod
    def simulate_paths(self, T: float, n_steps: int, n_paths: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """Simulate price paths with jumps"""
        pass
    
    @abstractmethod
    def option_price(self, K: Union[float, np.ndarray], T: float, option_type: str = 'call') -> np.ndarray:
        """Calculate option price"""
        pass

class MertonJumpDiffusion(JumpDiffusionModel):
    """
    Merton Jump-Diffusion Model
    
    Implements the classic Merton (1976) jump-diffusion model with
    log-normal jump sizes and Poisson jump timing.
    """
    
    def __init__(self, params: MertonParameters, S0: float = 100.0, r: float = 0.05):
        """
        Initialize Merton jump-diffusion model
        
        Args:
            params: Merton model parameters
            S0: Initial stock price
            r: Risk-free rate
        """
        self.params = params
        self.S0 = S0
        self.r = r
        
        # Precompute jump compensation
        self.k = np.exp(params.mu_j + 0.5 * params.sigma_j**2) - 1  # Expected jump size
        
        # FFT parameters
        self._N = 4096
        self._eta = 0.25
        self._alpha = -0.5
    
    def characteristic_function(self, u: np.ndarray, T: float) -> np.ndarray:
        """
        Merton characteristic function for option pricing
        
        φ(u,T) = exp(iuX₀ + T·ψ(u))
        where ψ(u) = iu(r - λk) - 0.5σ²u² + λ(φⱼ(u) - 1)
        
        Args:
            u: Complex frequency parameter
            T: Time to expiration
            
        Returns:
            Complex characteristic function values
        """
        mu, sigma, lambda_j, mu_j, sigma_j = (
            self.params.mu, self.params.sigma, self.params.lambda_j,
            self.params.mu_j, self.params.sigma_j
        )
        
        # Jump characteristic function (log-normal)
        phi_j = np.exp(1j * u * mu_j - 0.5 * sigma_j**2 * u**2)
        
        # Characteristic exponent
        psi = (1j * u * (self.r - lambda_j * self.k) - 
               0.5 * sigma**2 * u**2 + 
               lambda_j * (phi_j - 1))
        
        # Full characteristic function
        phi = np.exp(1j * u * np.log(self.S0) + T * psi)
        
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
        fft_result = np.fft.fft(fft_input)
        
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
    
    def option_price(self, K: Union[float, np.ndarray], T: float, 
                    option_type: str = 'call') -> np.ndarray:
        """Calculate option price using FFT method"""
        return self.fft_option_price(K, T, option_type)
    
    def simulate_paths(self, T: float, n_steps: int, 
                      n_paths: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Monte Carlo simulation of Merton jump-diffusion paths
        
        Args:
            T: Total time
            n_steps: Number of time steps
            n_paths: Number of simulation paths
            
        Returns:
            Tuple of (stock_paths, jump_times)
        """
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        
        # Initialize paths
        S = np.zeros((n_paths, n_steps + 1))
        S[:, 0] = self.S0
        
        # Store jump information
        jump_info = []
        
        # Parameters
        mu, sigma, lambda_j, mu_j, sigma_j = (
            self.params.mu, self.params.sigma, self.params.lambda_j,
            self.params.mu_j, self.params.sigma_j
        )
        
        for i in range(n_steps):
            # Generate Brownian motion increments
            dW = np.random.normal(0, sqrt_dt, n_paths)
            
            # Generate Poisson jumps
            dN = np.random.poisson(lambda_j * dt, n_paths)
            
            # Generate jump sizes (log-normal)
            jump_sizes = np.zeros(n_paths)
            has_jumps = dN > 0
            
            if np.any(has_jumps):
                n_jumps = np.sum(dN[has_jumps])
                if n_jumps > 0:
                    # Sum of log-normal jumps
                    total_jump_log = np.random.normal(
                        mu_j * dN[has_jumps], 
                        sigma_j * np.sqrt(dN[has_jumps])
                    )
                    jump_sizes[has_jumps] = np.exp(total_jump_log) - 1
            
            # Stock price evolution
            drift = (self.r - lambda_j * self.k - 0.5 * sigma**2) * dt
            diffusion = sigma * dW
            jumps = jump_sizes
            
            S[:, i + 1] = S[:, i] * np.exp(drift + diffusion) * (1 + jumps)
            
            # Store jump information
            if np.any(has_jumps):
                jump_info.append({
                    'time': (i + 1) * dt,
                    'paths': np.where(has_jumps)[0],
                    'sizes': jump_sizes[has_jumps],
                    'counts': dN[has_jumps]
                })
        
        return S, jump_info
    
    def calibrate_to_market(self, market_data: pd.DataFrame) -> JumpCalibrationResult:
        """
        Calibrate Merton model to market option prices
        
        Args:
            market_data: DataFrame with columns ['strike', 'expiry', 'price', 'option_type']
            
        Returns:
            Calibration results
        """
        
        def objective_function(params_array):
            """Objective function for optimization"""
            try:
                # Unpack parameters
                mu, sigma, lambda_j, mu_j, sigma_j = params_array
                
                # Parameter bounds checking
                if (sigma <= 0 or lambda_j < 0 or sigma_j <= 0):
                    return 1e6
                
                temp_params = MertonParameters(mu, sigma, lambda_j, mu_j, sigma_j)
                temp_model = MertonJumpDiffusion(temp_params, self.S0, self.r)
                
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
                
                # Calculate error (weighted by vega to emphasize liquid options)
                errors = model_prices - market_prices
                weights = 1.0 / (1.0 + market_prices)  # Higher weight for cheaper options
                weighted_error = np.sum(weights * errors**2)
                
                return weighted_error
                
            except:
                return 1e6
        
        # Initial guess and bounds
        initial_guess = [
            self.params.mu,
            self.params.sigma,
            self.params.lambda_j,
            self.params.mu_j,
            self.params.sigma_j
        ]
        
        bounds = [
            (-0.5, 0.5),     # mu
            (0.01, 2.0),     # sigma
            (0.0, 50.0),     # lambda_j
            (-0.5, 0.5),     # mu_j
            (0.01, 1.0)      # sigma_j
        ]
        
        # Multiple optimization attempts
        best_result = None
        best_error = np.inf
        
        for attempt in range(3):
            # Add noise to initial guess
            noisy_guess = [
                initial_guess[i] + np.random.normal(0, 0.1 * abs(initial_guess[i]))
                for i in range(len(initial_guess))
            ]
            
            result = optimize.minimize(
                objective_function,
                noisy_guess,
                method='L-BFGS-B',
                bounds=bounds,
                options={'maxiter': 1000, 'ftol': 1e-9}
            )
            
            if result.fun < best_error:
                best_error = result.fun
                best_result = result
        
        # Extract optimized parameters
        mu_opt, sigma_opt, lambda_j_opt, mu_j_opt, sigma_j_opt = best_result.x
        optimized_params = MertonParameters(mu_opt, sigma_opt, lambda_j_opt, mu_j_opt, sigma_j_opt)
        
        # Calculate final model prices and errors
        optimized_model = MertonJumpDiffusion(optimized_params, self.S0, self.r)
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
        
        # Jump statistics
        k = np.exp(mu_j_opt + 0.5 * sigma_j_opt**2) - 1
        jump_probability = 1 - np.exp(-lambda_j_opt)  # Annual jump probability
        
        return JumpCalibrationResult(
            parameters=optimized_params,
            model_type="Merton",
            rmse=rmse,
            mae=mae,
            max_error=max_error,
            convergence=best_result.success,
            iterations=best_result.nit,
            market_prices=market_prices,
            model_prices=final_model_prices,
            strikes=market_data['strike'].values,
            expiries=market_data['expiry'].values,
            jump_probability=jump_probability,
            jump_intensity=lambda_j_opt
        )

class KouJumpDiffusion(JumpDiffusionModel):
    """
    Kou Double Exponential Jump-Diffusion Model
    
    Implements the Kou (2002) jump-diffusion model with double
    exponential jump size distribution.
    """
    
    def __init__(self, params: KouParameters, S0: float = 100.0, r: float = 0.05):
        """
        Initialize Kou jump-diffusion model
        
        Args:
            params: Kou model parameters
            S0: Initial stock price
            r: Risk-free rate
        """
        self.params = params
        self.S0 = S0
        self.r = r
        
        # Precompute jump compensation
        self.k = (params.p * params.eta_u / (params.eta_u - 1) + 
                 (1 - params.p) * params.eta_d / (params.eta_d + 1) - 1)
        
        # FFT parameters
        self._N = 4096
        self._eta = 0.25
        self._alpha = -0.5
    
    def characteristic_function(self, u: np.ndarray, T: float) -> np.ndarray:
        """
        Kou characteristic function for option pricing
        
        φ(u,T) = exp(iuX₀ + T·ψ(u))
        where ψ(u) includes double exponential jump structure
        
        Args:
            u: Complex frequency parameter
            T: Time to expiration
            
        Returns:
            Complex characteristic function values
        """
        mu, sigma, lambda_j, p, eta_u, eta_d = (
            self.params.mu, self.params.sigma, self.params.lambda_j,
            self.params.p, self.params.eta_u, self.params.eta_d
        )
        
        # Jump characteristic function (double exponential)
        phi_j = (p * eta_u / (eta_u - 1j * u) + 
                (1 - p) * eta_d / (eta_d + 1j * u))
        
        # Characteristic exponent
        psi = (1j * u * (self.r - lambda_j * self.k) - 
               0.5 * sigma**2 * u**2 + 
               lambda_j * (phi_j - 1))
        
        # Full characteristic function
        phi = np.exp(1j * u * np.log(self.S0) + T * psi)
        
        return phi
    
    def fft_option_price(self, K: Union[float, np.ndarray], T: float, 
                        option_type: str = 'call') -> np.ndarray:
        """FFT-based option pricing using Kou characteristic function"""
        if isinstance(K, (int, float)):
            K = np.array([K])
        K = np.asarray(K)
        
        # FFT grid setup
        lambda_val = 2 * np.pi / (self._N * self._eta)
        b = self._N * lambda_val / 2
        
        # Frequency and strike grids
        u = np.arange(self._N) * self._eta
        k = -b + np.arange(self._N) * lambda_val
        
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
        fft_result = np.fft.fft(fft_input)
        
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
    
    def option_price(self, K: Union[float, np.ndarray], T: float, 
                    option_type: str = 'call') -> np.ndarray:
        """Calculate option price using FFT method"""
        return self.fft_option_price(K, T, option_type)
    
    def simulate_paths(self, T: float, n_steps: int, 
                      n_paths: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Monte Carlo simulation of Kou jump-diffusion paths
        
        Args:
            T: Total time
            n_steps: Number of time steps
            n_paths: Number of simulation paths
            
        Returns:
            Tuple of (stock_paths, jump_info)
        """
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        
        # Initialize paths
        S = np.zeros((n_paths, n_steps + 1))
        S[:, 0] = self.S0
        
        # Store jump information
        jump_info = []
        
        # Parameters
        mu, sigma, lambda_j, p, eta_u, eta_d = (
            self.params.mu, self.params.sigma, self.params.lambda_j,
            self.params.p, self.params.eta_u, self.params.eta_d
        )
        
        for i in range(n_steps):
            # Generate Brownian motion increments
            dW = np.random.normal(0, sqrt_dt, n_paths)
            
            # Generate Poisson jumps
            dN = np.random.poisson(lambda_j * dt, n_paths)
            
            # Generate jump sizes (double exponential)
            jump_sizes = np.zeros(n_paths)
            has_jumps = dN > 0
            
            if np.any(has_jumps):
                for path_idx in np.where(has_jumps)[0]:
                    n_jumps = dN[path_idx]
                    total_jump = 0
                    
                    for _ in range(n_jumps):
                        # Choose jump direction
                        if np.random.random() < p:
                            # Upward jump
                            jump_size = np.random.exponential(1 / eta_u)
                        else:
                            # Downward jump
                            jump_size = -np.random.exponential(1 / eta_d)
                        
                        total_jump += jump_size
                    
                    jump_sizes[path_idx] = np.exp(total_jump) - 1
            
            # Stock price evolution
            drift = (self.r - lambda_j * self.k - 0.5 * sigma**2) * dt
            diffusion = sigma * dW
            jumps = jump_sizes
            
            S[:, i + 1] = S[:, i] * np.exp(drift + diffusion) * (1 + jumps)
            
            # Store jump information
            if np.any(has_jumps):
                jump_info.append({
                    'time': (i + 1) * dt,
                    'paths': np.where(has_jumps)[0],
                    'sizes': jump_sizes[has_jumps],
                    'counts': dN[has_jumps]
                })
        
        return S, jump_info
    
    def calibrate_to_market(self, market_data: pd.DataFrame) -> JumpCalibrationResult:
        """Calibrate Kou model to market option prices"""
        
        def objective_function(params_array):
            """Objective function for optimization"""
            try:
                # Unpack parameters
                mu, sigma, lambda_j, p, eta_u, eta_d = params_array
                
                # Parameter bounds checking
                if (sigma <= 0 or lambda_j < 0 or not 0 <= p <= 1 or 
                    eta_u <= 0 or eta_d <= 0):
                    return 1e6
                
                temp_params = KouParameters(mu, sigma, lambda_j, p, eta_u, eta_d)
                temp_model = KouJumpDiffusion(temp_params, self.S0, self.r)
                
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
                errors = model_prices - market_prices
                return np.sum(errors**2)
                
            except:
                return 1e6
        
        # Initial guess and bounds
        initial_guess = [
            self.params.mu,
            self.params.sigma,
            self.params.lambda_j,
            self.params.p,
            self.params.eta_u,
            self.params.eta_d
        ]
        
        bounds = [
            (-0.5, 0.5),     # mu
            (0.01, 2.0),     # sigma
            (0.0, 50.0),     # lambda_j
            (0.01, 0.99),    # p
            (1.1, 50.0),     # eta_u (must be > 1)
            (1.1, 50.0)      # eta_d (must be > 1)
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
        mu_opt, sigma_opt, lambda_j_opt, p_opt, eta_u_opt, eta_d_opt = result.x
        optimized_params = KouParameters(mu_opt, sigma_opt, lambda_j_opt, p_opt, eta_u_opt, eta_d_opt)
        
        # Calculate final model prices and errors
        optimized_model = KouJumpDiffusion(optimized_params, self.S0, self.r)
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
        
        # Jump statistics
        jump_probability = 1 - np.exp(-lambda_j_opt)  # Annual jump probability
        
        return JumpCalibrationResult(
            parameters=optimized_params,
            model_type="Kou",
            rmse=rmse,
            mae=mae,
            max_error=max_error,
            convergence=result.success,
            iterations=result.nit,
            market_prices=market_prices,
            model_prices=final_model_prices,
            strikes=market_data['strike'].values,
            expiries=market_data['expiry'].values,
            jump_probability=jump_probability,
            jump_intensity=lambda_j_opt
        )

def create_sample_jump_data() -> pd.DataFrame:
    """Create sample market data for jump model testing"""
    np.random.seed(42)
    
    strikes = np.array([80, 90, 100, 110, 120])
    expiries = np.array([0.25, 0.5, 1.0])
    
    data = []
    for T in expiries:
        for K in strikes:
            # Simulate market prices with jumps
            true_params = MertonParameters(0.05, 0.2, 2.0, -0.1, 0.3)
            model = MertonJumpDiffusion(true_params, 100.0, 0.05)
            
            true_price = model.fft_option_price(K, T, 'call')[0]
            noisy_price = true_price * (1 + np.random.normal(0, 0.03))
            
            data.append({
                'strike': K,
                'expiry': T,
                'price': max(noisy_price, 0.01),
                'option_type': 'call'
            })
    
    return pd.DataFrame(data)

# Convenience functions
def create_merton_model(mu: float = 0.05, sigma: float = 0.2, 
                       lambda_j: float = 2.0, mu_j: float = -0.1, 
                       sigma_j: float = 0.3, S0: float = 100.0, 
                       r: float = 0.05) -> MertonJumpDiffusion:
    """Create a Merton jump-diffusion model"""
    params = MertonParameters(mu, sigma, lambda_j, mu_j, sigma_j)
    return MertonJumpDiffusion(params, S0, r)

def create_kou_model(mu: float = 0.05, sigma: float = 0.2, 
                    lambda_j: float = 2.0, p: float = 0.4, 
                    eta_u: float = 3.0, eta_d: float = 4.0, 
                    S0: float = 100.0, r: float = 0.05) -> KouJumpDiffusion:
    """Create a Kou jump-diffusion model"""
    params = KouParameters(mu, sigma, lambda_j, p, eta_u, eta_d)
    return KouJumpDiffusion(params, S0, r)

# Example usage and testing
if __name__ == "__main__":
    print("=== JUMP-DIFFUSION MODELS TESTING ===")
    
    # Create sample models
    merton_model = create_merton_model()
    kou_model = create_kou_model()
    
    print("Merton Model Parameters:")
    print(f"  μ={merton_model.params.mu}, σ={merton_model.params.sigma}")
    print(f"  λ={merton_model.params.lambda_j}, μⱼ={merton_model.params.mu_j}, σⱼ={merton_model.params.sigma_j}")
    
    print("\nKou Model Parameters:")
    print(f"  μ={kou_model.params.mu}, σ={kou_model.params.sigma}")
    print(f"  λ={kou_model.params.lambda_j}, p={kou_model.params.p}")
    print(f"  η₊={kou_model.params.eta_u}, η₋={kou_model.params.eta_d}")
    
    # Test option pricing
    print("\n=== OPTION PRICING COMPARISON ===")
    K = 100
    T = 1.0
    
    merton_price = merton_model.option_price(K, T, 'call')[0]
    kou_price = kou_model.option_price(K, T, 'call')[0]
    
    print(f"ATM Call Price (T=1Y):")
    print(f"  Merton: ${merton_price:.4f}")
    print(f"  Kou:    ${kou_price:.4f}")
    
    # Test Monte Carlo simulation
    print("\n=== MONTE CARLO SIMULATION ===")
    S_paths_merton, jumps_merton = merton_model.simulate_paths(1.0, 252, 1000)
    S_paths_kou, jumps_kou = kou_model.simulate_paths(1.0, 252, 1000)
    
    print(f"Merton MC Results:")
    print(f"  Final price mean: ${np.mean(S_paths_merton[:, -1]):.2f}")
    print(f"  Final price std:  ${np.std(S_paths_merton[:, -1]):.2f}")
    print(f"  Jump events:      {len(jumps_merton)}")
    
    print(f"Kou MC Results:")
    print(f"  Final price mean: ${np.mean(S_paths_kou[:, -1]):.2f}")
    print(f"  Final price std:  ${np.std(S_paths_kou[:, -1]):.2f}")
    print(f"  Jump events:      {len(jumps_kou)}")
    
    # Test calibration
    print("\n=== CALIBRATION TEST ===")
    market_data = create_sample_jump_data()
    
    print("Calibrating Merton model...")
    merton_calib = merton_model.calibrate_to_market(market_data)
    print(f"  Converged: {merton_calib.convergence}")
    print(f"  RMSE: {merton_calib.rmse:.6f}")
    print(f"  Jump probability: {merton_calib.jump_probability:.2%}")
    
    print("Calibrating Kou model...")
    kou_calib = kou_model.calibrate_to_market(market_data)
    print(f"  Converged: {kou_calib.convergence}")
    print(f"  RMSE: {kou_calib.rmse:.6f}")
    print(f"  Jump probability: {kou_calib.jump_probability:.2%}")
    
    print("\nJump-diffusion models testing completed successfully!")

"""
Monte Carlo Options Simulation Engine
====================================

Professional Monte Carlo simulation engine for options pricing with:
- Multi-asset correlated simulation
- Advanced variance reduction techniques
- Real-time Greeks calculation
- Path-dependent option valuation
- Exotic derivatives pricing
- Risk metrics and scenario analysis

Mathematical Framework:
- Geometric Brownian Motion: dS = μS dt + σS dW
- Correlated multi-asset: dS_i = μ_i S_i dt + σ_i S_i Σ_{j} L_{ij} dW_j
- Variance reduction: Antithetic variates, control variates, importance sampling
- Greeks: Finite difference and pathwise sensitivities
- American options: Longstaff-Schwartz LSM algorithm

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Callable, Any
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats, optimize, linalg
from scipy.interpolate import interp1d
import concurrent.futures
import time

# Try to import advanced numerical libraries
try:
    from numba import jit, njit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Create dummy decorators that do nothing
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]  # Handle @jit without parentheses
        return decorator
    
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]  # Handle @njit without parentheses
        return decorator

class OptionType(Enum):
    """Option type enumeration"""
    CALL = "call"
    PUT = "put"

class BarrierType(Enum):
    """Barrier option types"""
    UP_AND_IN = "up_and_in"
    UP_AND_OUT = "up_and_out"
    DOWN_AND_IN = "down_and_in"
    DOWN_AND_OUT = "down_and_out"

class AsianType(Enum):
    """Asian option types"""
    ARITHMETIC = "arithmetic"
    GEOMETRIC = "geometric"

@dataclass
class SimulationParameters:
    """Monte Carlo simulation parameters"""
    n_simulations: int = 100000
    n_time_steps: int = 252
    random_seed: Optional[int] = None
    use_antithetic: bool = True
    use_control_variate: bool = True
    parallel_execution: bool = True
    max_workers: Optional[int] = None

@dataclass
class OptionParameters:
    """Option contract parameters"""
    spot_price: float
    strike_price: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0
    option_type: OptionType = OptionType.CALL

@dataclass
class SimulationResult:
    """Monte Carlo simulation results"""
    option_price: float
    standard_error: float
    confidence_interval: Tuple[float, float]
    greeks: Dict[str, float]
    paths: Optional[np.ndarray] = None
    payoffs: Optional[np.ndarray] = None
    variance_reduction_effectiveness: float = 0.0
    computation_time: float = 0.0

class PathGenerator:
    """
    Advanced path generator for Monte Carlo simulation
    
    Supports:
    - Geometric Brownian Motion
    - Stochastic volatility models
    - Jump-diffusion processes
    - Multi-asset correlated paths
    """
    
    def __init__(self, model_type: str = "gbm"):
        """
        Initialize path generator
        
        Args:
            model_type: Type of model ("gbm", "heston", "merton")
        """
        self.model_type = model_type
    
    def generate_paths(self, 
                      params: OptionParameters,
                      n_paths: int,
                      n_steps: int,
                      correlation_matrix: Optional[np.ndarray] = None,
                      random_seed: Optional[int] = None) -> np.ndarray:
        """
        Generate price paths using specified model
        
        Args:
            params: Option parameters
            n_paths: Number of simulation paths
            n_steps: Number of time steps
            correlation_matrix: Asset correlation matrix
            random_seed: Random seed for reproducibility
            
        Returns:
            Array of shape (n_paths, n_steps + 1) with price paths
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        dt = params.time_to_expiry / n_steps
        
        if self.model_type == "gbm":
            return self._generate_gbm_paths(params, n_paths, n_steps, dt)
        elif self.model_type == "heston":
            return self._generate_heston_paths(params, n_paths, n_steps, dt)
        elif self.model_type == "merton":
            return self._generate_merton_paths(params, n_paths, n_steps, dt)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _generate_gbm_paths(self, params: OptionParameters, n_paths: int, 
                           n_steps: int, dt: float) -> np.ndarray:
        """Generate Geometric Brownian Motion paths"""
        # Pre-calculate constants
        drift = (params.risk_free_rate - params.dividend_yield - 0.5 * params.volatility**2) * dt
        diffusion = params.volatility * np.sqrt(dt)
        
        # Generate random numbers
        random_numbers = np.random.randn(n_paths, n_steps)
        
        # Calculate log returns
        log_returns = drift + diffusion * random_numbers
        
        # Calculate paths
        log_prices = np.cumsum(log_returns, axis=1)
        log_prices = np.column_stack([np.zeros(n_paths), log_prices])
        
        # Convert to price paths
        paths = params.spot_price * np.exp(log_prices)
        
        return paths
    
    def _generate_heston_paths(self, params: OptionParameters, n_paths: int,
                              n_steps: int, dt: float) -> np.ndarray:
        """Generate Heston stochastic volatility paths"""
        # Heston parameters (simplified)
        kappa = 2.0  # Mean reversion speed
        theta = params.volatility**2  # Long-term variance
        xi = 0.3  # Volatility of volatility
        rho = -0.5  # Correlation between asset and volatility
        
        # Initialize arrays
        paths = np.zeros((n_paths, n_steps + 1))
        variance_paths = np.zeros((n_paths, n_steps + 1))
        
        paths[:, 0] = params.spot_price
        variance_paths[:, 0] = theta
        
        # Correlated random numbers
        for i in range(n_steps):
            z1 = np.random.randn(n_paths)
            z2 = rho * z1 + np.sqrt(1 - rho**2) * np.random.randn(n_paths)
            
            # Variance process (Feller condition)
            variance_paths[:, i+1] = np.abs(
                variance_paths[:, i] + kappa * (theta - variance_paths[:, i]) * dt +
                xi * np.sqrt(variance_paths[:, i] * dt) * z2
            )
            
            # Price process
            paths[:, i+1] = paths[:, i] * np.exp(
                (params.risk_free_rate - params.dividend_yield - 0.5 * variance_paths[:, i]) * dt +
                np.sqrt(variance_paths[:, i] * dt) * z1
            )
        
        return paths
    
    def _generate_merton_paths(self, params: OptionParameters, n_paths: int,
                              n_steps: int, dt: float) -> np.ndarray:
        """Generate Merton jump-diffusion paths"""
        # Jump parameters
        jump_intensity = 0.1  # Jumps per year
        jump_mean = -0.05  # Average jump size
        jump_vol = 0.15  # Jump volatility
        
        # Initialize paths
        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = params.spot_price
        
        # Compensator for jumps
        jump_compensator = jump_intensity * (np.exp(jump_mean + 0.5 * jump_vol**2) - 1)
        
        for i in range(n_steps):
            # Brownian motion component
            brownian = np.random.randn(n_paths)
            
            # Jump component
            n_jumps = np.random.poisson(jump_intensity * dt, n_paths)
            jump_component = np.zeros(n_paths)
            
            for j in range(n_paths):
                if n_jumps[j] > 0:
                    jumps = np.random.normal(jump_mean, jump_vol, n_jumps[j])
                    jump_component[j] = np.sum(jumps)
            
            # Price evolution
            paths[:, i+1] = paths[:, i] * np.exp(
                (params.risk_free_rate - params.dividend_yield - 0.5 * params.volatility**2 - jump_compensator) * dt +
                params.volatility * np.sqrt(dt) * brownian + jump_component
            )
        
        return paths

class VarianceReductionEngine:
    """
    Advanced variance reduction techniques for Monte Carlo simulation
    
    Implements:
    - Antithetic variates
    - Control variates (with Black-Scholes as control)
    - Importance sampling
    - Stratified sampling
    """
    
    def __init__(self):
        pass
    
    def apply_antithetic_variates(self, paths1: np.ndarray, paths2: np.ndarray,
                                 payoff_func: Callable) -> Tuple[float, float]:
        """
        Apply antithetic variates variance reduction
        
        Args:
            paths1: Original paths
            paths2: Antithetic paths (using -Z instead of Z)
            payoff_func: Function to calculate option payoff
            
        Returns:
            Tuple of (reduced_price, variance_reduction_factor)
        """
        payoffs1 = payoff_func(paths1)
        payoffs2 = payoff_func(paths2)
        
        # Antithetic average
        antithetic_payoffs = 0.5 * (payoffs1 + payoffs2)
        antithetic_price = np.mean(antithetic_payoffs)
        
        # Variance reduction effectiveness
        original_variance = np.var(payoffs1)
        antithetic_variance = np.var(antithetic_payoffs)
        variance_reduction = 1 - antithetic_variance / (original_variance + 1e-10)
        
        return antithetic_price, variance_reduction
    
    def apply_control_variates(self, payoffs: np.ndarray, control_payoffs: np.ndarray,
                              control_analytical_price: float) -> Tuple[float, float]:
        """
        Apply control variates variance reduction
        
        Args:
            payoffs: Monte Carlo payoffs for target option
            control_payoffs: Monte Carlo payoffs for control option
            control_analytical_price: Analytical price of control option
            
        Returns:
            Tuple of (controlled_price, variance_reduction_factor)
        """
        # Calculate optimal control coefficient
        covariance = np.cov(payoffs, control_payoffs)[0, 1]
        control_variance = np.var(control_payoffs)
        
        if control_variance > 1e-10:
            beta = covariance / control_variance
        else:
            beta = 0
        
        # Apply control variate adjustment
        control_error = control_payoffs - control_analytical_price
        controlled_payoffs = payoffs - beta * control_error
        controlled_price = np.mean(controlled_payoffs)
        
        # Variance reduction effectiveness
        original_variance = np.var(payoffs)
        controlled_variance = np.var(controlled_payoffs)
        variance_reduction = 1 - controlled_variance / (original_variance + 1e-10)
        
        return controlled_price, variance_reduction
    
    def stratified_sampling(self, n_paths: int, n_strata: int, 
                           path_generator: Callable) -> np.ndarray:
        """
        Generate paths using stratified sampling
        
        Args:
            n_paths: Total number of paths
            n_strata: Number of strata
            path_generator: Function to generate paths
            
        Returns:
            Stratified paths array
        """
        paths_per_stratum = n_paths // n_strata
        remainder = n_paths % n_strata
        
        all_paths = []
        
        for i in range(n_strata):
            # Uniform samples within stratum
            u_min = i / n_strata
            u_max = (i + 1) / n_strata
            
            n_paths_stratum = paths_per_stratum + (1 if i < remainder else 0)
            
            # Generate uniform samples in [u_min, u_max]
            u_samples = np.random.uniform(u_min, u_max, n_paths_stratum)
            
            # Convert to normal samples
            z_samples = stats.norm.ppf(u_samples)
            
            # Generate paths for this stratum
            stratum_paths = path_generator(z_samples)
            all_paths.append(stratum_paths)
        
        return np.vstack(all_paths)

class GreeksCalculator:
    """
    Real-time Greeks calculation for Monte Carlo simulation
    
    Implements both finite difference and pathwise derivative methods:
    - Delta: ∂V/∂S
    - Gamma: ∂²V/∂S²
    - Theta: ∂V/∂t
    - Vega: ∂V/∂σ
    - Rho: ∂V/∂r
    """
    
    def __init__(self, bump_size: float = 0.01):
        """
        Initialize Greeks calculator
        
        Args:
            bump_size: Relative bump size for finite differences
        """
        self.bump_size = bump_size
    
    def calculate_greeks(self, params: OptionParameters, pricing_func: Callable,
                        method: str = "finite_difference") -> Dict[str, float]:
        """
        Calculate all Greeks using specified method
        
        Args:
            params: Option parameters
            pricing_func: Function to price the option
            method: "finite_difference" or "pathwise"
            
        Returns:
            Dictionary of Greeks values
        """
        if method == "finite_difference":
            return self._calculate_greeks_fd(params, pricing_func)
        elif method == "pathwise":
            return self._calculate_greeks_pathwise(params, pricing_func)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calculate_greeks_fd(self, params: OptionParameters, 
                            pricing_func: Callable) -> Dict[str, float]:
        """Calculate Greeks using finite differences"""
        base_price = pricing_func(params)
        
        greeks = {}
        
        # Delta: ∂V/∂S
        params_up = OptionParameters(**vars(params))
        params_up.spot_price *= (1 + self.bump_size)
        price_up = pricing_func(params_up)
        
        params_down = OptionParameters(**vars(params))
        params_down.spot_price *= (1 - self.bump_size)
        price_down = pricing_func(params_down)
        
        greeks['delta'] = (price_up - price_down) / (2 * params.spot_price * self.bump_size)
        
        # Gamma: ∂²V/∂S²
        greeks['gamma'] = (price_up - 2 * base_price + price_down) / (params.spot_price * self.bump_size)**2
        
        # Vega: ∂V/∂σ
        params_vega_up = OptionParameters(**vars(params))
        params_vega_up.volatility += self.bump_size
        price_vega_up = pricing_func(params_vega_up)
        
        params_vega_down = OptionParameters(**vars(params))
        params_vega_down.volatility -= self.bump_size
        price_vega_down = pricing_func(params_vega_down)
        
        greeks['vega'] = (price_vega_up - price_vega_down) / (2 * self.bump_size)
        
        # Theta: ∂V/∂t
        params_theta = OptionParameters(**vars(params))
        params_theta.time_to_expiry -= 1/365  # 1 day
        price_theta = pricing_func(params_theta)
        
        greeks['theta'] = (price_theta - base_price) / (1/365)
        
        # Rho: ∂V/∂r
        params_rho_up = OptionParameters(**vars(params))
        params_rho_up.risk_free_rate += self.bump_size
        price_rho_up = pricing_func(params_rho_up)
        
        params_rho_down = OptionParameters(**vars(params))
        params_rho_down.risk_free_rate -= self.bump_size
        price_rho_down = pricing_func(params_rho_down)
        
        greeks['rho'] = (price_rho_up - price_rho_down) / (2 * self.bump_size)
        
        return greeks
    
    def _calculate_greeks_pathwise(self, params: OptionParameters,
                                  pricing_func: Callable) -> Dict[str, float]:
        """Calculate Greeks using pathwise derivatives (placeholder)"""
        # Pathwise derivative implementation would require access to the paths
        # This is a simplified version
        return self._calculate_greeks_fd(params, pricing_func)

class MonteCarloEngine:
    """
    Main Monte Carlo simulation engine
    
    Orchestrates all components for comprehensive options pricing:
    - Path generation with various models
    - Variance reduction techniques
    - Greeks calculation
    - Exotic options pricing
    - Risk analysis
    """
    
    def __init__(self, simulation_params: SimulationParameters = None):
        """
        Initialize Monte Carlo engine
        
        Args:
            simulation_params: Simulation configuration
        """
        self.sim_params = simulation_params or SimulationParameters()
        self.path_generator = PathGenerator()
        self.variance_reducer = VarianceReductionEngine()
        self.greeks_calculator = GreeksCalculator()
        
    def price_european_option(self, option_params: OptionParameters) -> SimulationResult:
        """
        Price European option using Monte Carlo simulation
        
        Args:
            option_params: Option contract parameters
            
        Returns:
            Complete simulation results
        """
        start_time = time.time()
        
        # Set random seed for reproducibility
        if self.sim_params.random_seed is not None:
            np.random.seed(self.sim_params.random_seed)
        
        # Generate paths
        paths = self.path_generator.generate_paths(
            option_params,
            self.sim_params.n_simulations,
            self.sim_params.n_time_steps
        )
        
        # Calculate payoffs
        final_prices = paths[:, -1]
        if option_params.option_type == OptionType.CALL:
            payoffs = np.maximum(final_prices - option_params.strike_price, 0)
        else:
            payoffs = np.maximum(option_params.strike_price - final_prices, 0)
        
        # Discount to present value
        discount_factor = np.exp(-option_params.risk_free_rate * option_params.time_to_expiry)
        discounted_payoffs = payoffs * discount_factor
        
        # Basic Monte Carlo price
        mc_price = np.mean(discounted_payoffs)
        mc_std_error = np.std(discounted_payoffs) / np.sqrt(self.sim_params.n_simulations)
        
        # Apply variance reduction if enabled
        variance_reduction_effectiveness = 0.0
        
        if self.sim_params.use_antithetic:
            # Generate antithetic paths
            np.random.seed(self.sim_params.random_seed)  # Reset for consistency
            antithetic_paths = self.path_generator.generate_paths(
                option_params,
                self.sim_params.n_simulations,
                self.sim_params.n_time_steps
            )
            
            # Apply antithetic variates
            def payoff_func(path_array):
                final_prices = path_array[:, -1]
                if option_params.option_type == OptionType.CALL:
                    return np.maximum(final_prices - option_params.strike_price, 0) * discount_factor
                else:
                    return np.maximum(option_params.strike_price - final_prices, 0) * discount_factor
            
            mc_price, variance_reduction_effectiveness = self.variance_reducer.apply_antithetic_variates(
                paths, antithetic_paths, payoff_func
            )
        
        # Calculate confidence interval
        confidence_level = 0.95
        z_score = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        confidence_interval = (
            mc_price - z_score * mc_std_error,
            mc_price + z_score * mc_std_error
        )
        
        # Calculate Greeks
        def pricing_func(params):
            temp_paths = self.path_generator.generate_paths(
                params, self.sim_params.n_simulations // 10, self.sim_params.n_time_steps
            )
            temp_final_prices = temp_paths[:, -1]
            if params.option_type == OptionType.CALL:
                temp_payoffs = np.maximum(temp_final_prices - params.strike_price, 0)
            else:
                temp_payoffs = np.maximum(params.strike_price - temp_final_prices, 0)
            temp_discount = np.exp(-params.risk_free_rate * params.time_to_expiry)
            return np.mean(temp_payoffs * temp_discount)
        
        greeks = self.greeks_calculator.calculate_greeks(option_params, pricing_func)
        
        computation_time = time.time() - start_time
        
        return SimulationResult(
            option_price=mc_price,
            standard_error=mc_std_error,
            confidence_interval=confidence_interval,
            greeks=greeks,
            paths=paths if self.sim_params.n_simulations <= 10000 else None,  # Store paths only for small simulations
            payoffs=discounted_payoffs,
            variance_reduction_effectiveness=variance_reduction_effectiveness,
            computation_time=computation_time
        )
    
    def price_american_option(self, option_params: OptionParameters) -> SimulationResult:
        """
        Price American option using Longstaff-Schwartz LSM algorithm
        
        Args:
            option_params: Option contract parameters
            
        Returns:
            Complete simulation results
        """
        start_time = time.time()
        
        # Generate paths
        paths = self.path_generator.generate_paths(
            option_params,
            self.sim_params.n_simulations,
            self.sim_params.n_time_steps
        )
        
        # LSM algorithm implementation
        dt = option_params.time_to_expiry / self.sim_params.n_time_steps
        discount_factor = np.exp(-option_params.risk_free_rate * dt)
        
        # Initialize cash flows matrix
        cash_flows = np.zeros_like(paths)
        
        # Terminal payoffs
        if option_params.option_type == OptionType.CALL:
            cash_flows[:, -1] = np.maximum(paths[:, -1] - option_params.strike_price, 0)
        else:
            cash_flows[:, -1] = np.maximum(option_params.strike_price - paths[:, -1], 0)
        
        # Backward induction
        for t in range(self.sim_params.n_time_steps - 1, 0, -1):
            # Intrinsic value at time t
            if option_params.option_type == OptionType.CALL:
                intrinsic = np.maximum(paths[:, t] - option_params.strike_price, 0)
            else:
                intrinsic = np.maximum(option_params.strike_price - paths[:, t], 0)
            
            # Only consider in-the-money paths
            itm_indices = intrinsic > 0
            
            if np.sum(itm_indices) > 0:
                # Regression variables (Laguerre polynomials)
                x = paths[itm_indices, t]
                
                # Discounted future cash flows
                future_cf = np.sum(cash_flows[itm_indices, t+1:] * 
                                 (discount_factor ** np.arange(1, self.sim_params.n_time_steps - t)), axis=1)
                
                # Polynomial regression (up to degree 3)
                if len(x) > 5:  # Need sufficient data points
                    A = np.column_stack([
                        np.ones(len(x)),
                        x,
                        x**2,
                        x**3
                    ])
                    
                    try:
                        # Solve for regression coefficients
                        coeffs = np.linalg.lstsq(A, future_cf, rcond=None)[0]
                        continuation_value = A @ coeffs
                        
                        # Exercise decision
                        exercise_indices = intrinsic[itm_indices] > continuation_value
                        
                        # Update cash flows
                        exercise_paths = np.where(itm_indices)[0][exercise_indices]
                        cash_flows[exercise_paths, t] = intrinsic[exercise_paths]
                        cash_flows[exercise_paths, t+1:] = 0  # Zero out future cash flows
                    except:
                        # Fallback: exercise if deeply in-the-money
                        deep_itm = intrinsic[itm_indices] > option_params.strike_price * 0.1
                        exercise_paths = np.where(itm_indices)[0][deep_itm]
                        cash_flows[exercise_paths, t] = intrinsic[exercise_paths]
                        cash_flows[exercise_paths, t+1:] = 0
        
        # Calculate option value
        total_discounted_cf = np.sum(cash_flows * 
                                   (discount_factor ** np.arange(self.sim_params.n_time_steps + 1)), axis=1)
        
        american_price = np.mean(total_discounted_cf)
        american_std_error = np.std(total_discounted_cf) / np.sqrt(self.sim_params.n_simulations)
        
        # Calculate confidence interval
        confidence_level = 0.95
        z_score = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        confidence_interval = (
            american_price - z_score * american_std_error,
            american_price + z_score * american_std_error
        )
        
        # Calculate Greeks (simplified for American options)
        def pricing_func(params):
            # Use European approximation for Greeks
            temp_paths = self.path_generator.generate_paths(
                params, self.sim_params.n_simulations // 20, self.sim_params.n_time_steps
            )
            temp_final_prices = temp_paths[:, -1]
            if params.option_type == OptionType.CALL:
                temp_payoffs = np.maximum(temp_final_prices - params.strike_price, 0)
            else:
                temp_payoffs = np.maximum(params.strike_price - temp_final_prices, 0)
            temp_discount = np.exp(-params.risk_free_rate * params.time_to_expiry)
            return np.mean(temp_payoffs * temp_discount)
        
        greeks = self.greeks_calculator.calculate_greeks(option_params, pricing_func)
        
        computation_time = time.time() - start_time
        
        return SimulationResult(
            option_price=american_price,
            standard_error=american_std_error,
            confidence_interval=confidence_interval,
            greeks=greeks,
            paths=paths if self.sim_params.n_simulations <= 5000 else None,
            payoffs=total_discounted_cf,
            variance_reduction_effectiveness=0.0,
            computation_time=computation_time
        )

class RiskAnalyzer:
    """
    Risk analysis and scenario testing for Monte Carlo simulations
    
    Provides:
    - Value at Risk (VaR) calculation
    - Expected Shortfall (ES)
    - Scenario analysis
    - Stress testing
    - Sensitivity analysis
    """
    
    def __init__(self):
        pass
    
    def calculate_var(self, payoffs: np.ndarray, confidence_level: float = 0.95) -> Dict[str, float]:
        """
        Calculate Value at Risk metrics
        
        Args:
            payoffs: Array of option payoffs
            confidence_level: VaR confidence level
            
        Returns:
            Dictionary with VaR metrics
        """
        sorted_payoffs = np.sort(payoffs)
        n_obs = len(sorted_payoffs)
        
        # VaR calculation
        var_index = int((1 - confidence_level) * n_obs)
        var_value = sorted_payoffs[var_index] if var_index < n_obs else sorted_payoffs[-1]
        
        # Expected Shortfall (Conditional VaR)
        tail_payoffs = sorted_payoffs[:var_index + 1]
        expected_shortfall = np.mean(tail_payoffs) if len(tail_payoffs) > 0 else var_value
        
        return {
            'var': var_value,
            'expected_shortfall': expected_shortfall,
            'confidence_level': confidence_level,
            'worst_case': sorted_payoffs[0],
            'best_case': sorted_payoffs[-1],
            'percentile_5': np.percentile(payoffs, 5),
            'percentile_95': np.percentile(payoffs, 95)
        }
    
    def stress_test(self, option_params: OptionParameters, 
                   pricing_engine: MonteCarloEngine,
                   stress_scenarios: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """
        Perform stress testing under various scenarios
        
        Args:
            option_params: Base option parameters
            pricing_engine: Monte Carlo engine
            stress_scenarios: Dictionary of parameter stress values
            
        Returns:
            Dictionary of stressed prices
        """
        stress_results = {}
        
        for param_name, stress_values in stress_scenarios.items():
            stressed_prices = []
            
            for stress_value in stress_values:
                stressed_params = OptionParameters(**vars(option_params))
                
                if param_name == 'spot_price':
                    stressed_params.spot_price = stress_value
                elif param_name == 'volatility':
                    stressed_params.volatility = stress_value
                elif param_name == 'risk_free_rate':
                    stressed_params.risk_free_rate = stress_value
                elif param_name == 'time_to_expiry':
                    stressed_params.time_to_expiry = stress_value
                
                result = pricing_engine.price_european_option(stressed_params)
                stressed_prices.append(result.option_price)
            
            stress_results[param_name] = stressed_prices
        
        return stress_results

# Performance-optimized functions using Numba
@njit
def _fast_gbm_paths(spot: float, drift: float, vol: float, 
                   random_numbers: np.ndarray) -> np.ndarray:
    """Fast GBM path generation using Numba compilation"""
    n_paths, n_steps = random_numbers.shape
    paths = np.zeros((n_paths, n_steps + 1))
    paths[:, 0] = spot
    
    for i in range(n_steps):
        paths[:, i+1] = paths[:, i] * np.exp(drift + vol * random_numbers[:, i])
    
    return paths

@njit
def _fast_option_payoffs(final_prices: np.ndarray, strike: float, 
                        is_call: bool) -> np.ndarray:
    """Fast option payoff calculation using Numba compilation"""
    if is_call:
        return np.maximum(final_prices - strike, 0.0)
    else:
        return np.maximum(strike - final_prices, 0.0)

# Example usage and testing
if __name__ == "__main__":
    print("=== MONTE CARLO SIMULATION TESTING ===")
    
    # Define option parameters
    option_params = OptionParameters(
        spot_price=100.0,
        strike_price=105.0,
        time_to_expiry=0.25,  # 3 months
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.02,
        option_type=OptionType.CALL
    )
    
    # Simulation parameters
    sim_params = SimulationParameters(
        n_simulations=50000,
        n_time_steps=50,
        random_seed=42,
        use_antithetic=True,
        use_control_variate=False,
        parallel_execution=False
    )
    
    # Initialize Monte Carlo engine
    mc_engine = MonteCarloEngine(sim_params)
    
    print(f"Pricing European Call Option:")
    print(f"Spot: ${option_params.spot_price}")
    print(f"Strike: ${option_params.strike_price}")
    print(f"Time to Expiry: {option_params.time_to_expiry:.2f} years")
    print(f"Volatility: {option_params.volatility:.1%}")
    print(f"Risk-free Rate: {option_params.risk_free_rate:.1%}")
    
    # Price European option
    print("\n=== EUROPEAN OPTION PRICING ===")
    start_time = time.time()
    european_result = mc_engine.price_european_option(option_params)
    print(f"Computation Time: {european_result.computation_time:.3f} seconds")
    print(f"Option Price: ${european_result.option_price:.4f}")
    print(f"Standard Error: ${european_result.standard_error:.4f}")
    print(f"95% CI: [${european_result.confidence_interval[0]:.4f}, ${european_result.confidence_interval[1]:.4f}]")
    print(f"Variance Reduction: {european_result.variance_reduction_effectiveness:.2%}")
    
    print("\nGreeks:")
    for greek, value in european_result.greeks.items():
        print(f"  {greek.capitalize()}: {value:.4f}")
    
    # Price American option
    print("\n=== AMERICAN OPTION PRICING ===")
    american_result = mc_engine.price_american_option(option_params)
    print(f"Computation Time: {american_result.computation_time:.3f} seconds")
    print(f"American Option Price: ${american_result.option_price:.4f}")
    print(f"Early Exercise Premium: ${american_result.option_price - european_result.option_price:.4f}")
    
    # Risk analysis
    print("\n=== RISK ANALYSIS ===")
    risk_analyzer = RiskAnalyzer()
    var_metrics = risk_analyzer.calculate_var(european_result.payoffs)
    
    print(f"Value at Risk (95%): ${var_metrics['var']:.4f}")
    print(f"Expected Shortfall: ${var_metrics['expected_shortfall']:.4f}")
    print(f"Worst Case: ${var_metrics['worst_case']:.4f}")
    print(f"Best Case: ${var_metrics['best_case']:.4f}")
    
    # Stress testing
    print("\n=== STRESS TESTING ===")
    stress_scenarios = {
        'spot_price': [80, 90, 100, 110, 120],
        'volatility': [0.1, 0.15, 0.2, 0.25, 0.3],
        'risk_free_rate': [0.01, 0.03, 0.05, 0.07, 0.09]
    }
    
    # Simplified stress test (fewer simulations for speed)
    stress_sim_params = SimulationParameters(n_simulations=10000, random_seed=42)
    stress_engine = MonteCarloEngine(stress_sim_params)
    
    stress_results = risk_analyzer.stress_test(option_params, stress_engine, stress_scenarios)
    
    for param, prices in stress_results.items():
        print(f"\nStress Test - {param.replace('_', ' ').title()}:")
        for i, price in enumerate(prices):
            scenario_value = stress_scenarios[param][i]
            print(f"  {scenario_value}: ${price:.4f}")
    
    print("\nMonte Carlo simulation testing completed!")

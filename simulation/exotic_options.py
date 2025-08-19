"""
Exotic Options Pricing Module
============================

Advanced exotic options pricing using Monte Carlo simulation:
- Barrier options (knock-in/knock-out)
- Asian options (arithmetic/geometric average)
- Lookback options (floating/fixed strike)
- Rainbow options (multi-asset)
- Digital/Binary options
- Bermuda/American options with early exercise

Mathematical Framework:
- Path-dependent payoff calculations
- Barrier monitoring with continuous/discrete observation
- Average price calculations with control variates
- Multi-asset correlation handling with Cholesky decomposition
- Early exercise boundary optimization

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Callable, Any
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats, optimize

from .monte_carlo import (
    OptionType, BarrierType, AsianType, 
    OptionParameters, SimulationResult,
    PathGenerator, VarianceReductionEngine
)

@dataclass
class BarrierOptionParameters(OptionParameters):
    """Barrier option specific parameters"""
    barrier_level: float
    barrier_type: BarrierType
    rebate: float = 0.0
    observation_frequency: str = "continuous"  # "continuous" or "discrete"

@dataclass
class AsianOptionParameters(OptionParameters):
    """Asian option specific parameters"""
    asian_type: AsianType
    averaging_start: float = 0.0  # Time when averaging starts (fraction of total time)
    averaging_frequency: str = "daily"  # "daily", "weekly", "monthly"

@dataclass
class LookbackOptionParameters(OptionParameters):
    """Lookback option specific parameters"""
    lookback_type: str = "floating"  # "floating" or "fixed"
    lookback_start: float = 0.0  # Time when lookback starts

@dataclass
class RainbowOptionParameters:
    """Rainbow (multi-asset) option parameters"""
    spot_prices: List[float]
    strike_price: float
    time_to_expiry: float
    risk_free_rate: float
    volatilities: List[float]
    correlation_matrix: np.ndarray
    dividend_yields: List[float]
    option_type: OptionType
    rainbow_type: str = "best_of"  # "best_of", "worst_of", "basket"
    weights: Optional[List[float]] = None

class BarrierOption:
    """
    Barrier Options Pricing Engine
    
    Supports all barrier types:
    - Up-and-In/Out: Activated/Deactivated when price goes above barrier
    - Down-and-In/Out: Activated/Deactivated when price goes below barrier
    """
    
    def __init__(self):
        self.path_generator = PathGenerator()
    
    def price(self, params: BarrierOptionParameters, n_simulations: int = 100000,
              n_time_steps: int = 252) -> SimulationResult:
        """
        Price barrier option using Monte Carlo simulation
        
        Args:
            params: Barrier option parameters
            n_simulations: Number of Monte Carlo paths
            n_time_steps: Number of time steps per path
            
        Returns:
            Simulation results with barrier option price
        """
        # Generate price paths
        paths = self.path_generator.generate_paths(
            params, n_simulations, n_time_steps
        )
        
        # Check barrier conditions
        barrier_hit = self._check_barrier_conditions(paths, params)
        
        # Calculate payoffs based on barrier conditions
        final_prices = paths[:, -1]
        
        # Standard European payoff
        if params.option_type == OptionType.CALL:
            european_payoff = np.maximum(final_prices - params.strike_price, 0)
        else:
            european_payoff = np.maximum(params.strike_price - final_prices, 0)
        
        # Apply barrier conditions
        if params.barrier_type == BarrierType.UP_AND_OUT:
            # Option becomes worthless if barrier is hit
            payoffs = np.where(barrier_hit, params.rebate, european_payoff)
        elif params.barrier_type == BarrierType.UP_AND_IN:
            # Option only exists if barrier is hit
            payoffs = np.where(barrier_hit, european_payoff, params.rebate)
        elif params.barrier_type == BarrierType.DOWN_AND_OUT:
            # Option becomes worthless if barrier is hit
            payoffs = np.where(barrier_hit, params.rebate, european_payoff)
        elif params.barrier_type == BarrierType.DOWN_AND_IN:
            # Option only exists if barrier is hit
            payoffs = np.where(barrier_hit, european_payoff, params.rebate)
        else:
            payoffs = european_payoff
        
        # Discount to present value
        discount_factor = np.exp(-params.risk_free_rate * params.time_to_expiry)
        discounted_payoffs = payoffs * discount_factor
        
        # Calculate statistics
        option_price = np.mean(discounted_payoffs)
        standard_error = np.std(discounted_payoffs) / np.sqrt(n_simulations)
        
        # Confidence interval
        z_score = stats.norm.ppf(0.975)  # 95% confidence
        confidence_interval = (
            option_price - z_score * standard_error,
            option_price + z_score * standard_error
        )
        
        return SimulationResult(
            option_price=option_price,
            standard_error=standard_error,
            confidence_interval=confidence_interval,
            greeks={},  # Greeks calculation can be added
            paths=paths if n_simulations <= 10000 else None,
            payoffs=discounted_payoffs,
            variance_reduction_effectiveness=0.0,
            computation_time=0.0
        )
    
    def _check_barrier_conditions(self, paths: np.ndarray, 
                                 params: BarrierOptionParameters) -> np.ndarray:
        """Check which paths hit the barrier"""
        if params.barrier_type in [BarrierType.UP_AND_IN, BarrierType.UP_AND_OUT]:
            # Check if any price in path exceeds barrier
            return np.any(paths >= params.barrier_level, axis=1)
        else:  # DOWN_AND_IN or DOWN_AND_OUT
            # Check if any price in path goes below barrier
            return np.any(paths <= params.barrier_level, axis=1)

class AsianOption:
    """
    Asian Options Pricing Engine
    
    Supports:
    - Arithmetic average options
    - Geometric average options
    - Flexible averaging periods
    """
    
    def __init__(self):
        self.path_generator = PathGenerator()
        self.variance_reducer = VarianceReductionEngine()
    
    def price(self, params: AsianOptionParameters, n_simulations: int = 100000,
              n_time_steps: int = 252) -> SimulationResult:
        """
        Price Asian option using Monte Carlo simulation
        
        Args:
            params: Asian option parameters
            n_simulations: Number of Monte Carlo paths
            n_time_steps: Number of time steps per path
            
        Returns:
            Simulation results with Asian option price
        """
        # Generate price paths
        paths = self.path_generator.generate_paths(
            params, n_simulations, n_time_steps
        )
        
        # Determine averaging period
        start_step = int(params.averaging_start * n_time_steps)
        averaging_paths = paths[:, start_step:]
        
        # Calculate average prices
        if params.asian_type == AsianType.ARITHMETIC:
            average_prices = np.mean(averaging_paths, axis=1)
        else:  # GEOMETRIC
            # Geometric mean = exp(mean(log(prices)))
            log_prices = np.log(averaging_paths)
            average_prices = np.exp(np.mean(log_prices, axis=1))
        
        # Calculate payoffs using average price
        if params.option_type == OptionType.CALL:
            payoffs = np.maximum(average_prices - params.strike_price, 0)
        else:
            payoffs = np.maximum(params.strike_price - average_prices, 0)
        
        # Discount to present value
        discount_factor = np.exp(-params.risk_free_rate * params.time_to_expiry)
        discounted_payoffs = payoffs * discount_factor
        
        # For geometric Asian options, we can use control variate technique
        variance_reduction_effectiveness = 0.0
        option_price = np.mean(discounted_payoffs)
        
        if params.asian_type == AsianType.GEOMETRIC:
            # Geometric Asian has analytical solution - use as control variate
            analytical_geometric = self._analytical_geometric_asian(params)
            
            # Calculate geometric payoffs from MC
            geometric_payoffs = []
            for path in averaging_paths:
                geom_avg = np.exp(np.mean(np.log(path)))
                if params.option_type == OptionType.CALL:
                    geom_payoff = max(geom_avg - params.strike_price, 0)
                else:
                    geom_payoff = max(params.strike_price - geom_avg, 0)
                geometric_payoffs.append(geom_payoff * discount_factor)
            
            geometric_payoffs = np.array(geometric_payoffs)
            
            # Apply control variate
            option_price, variance_reduction_effectiveness = self.variance_reducer.apply_control_variates(
                discounted_payoffs, geometric_payoffs, analytical_geometric
            )
        
        # Calculate statistics
        standard_error = np.std(discounted_payoffs) / np.sqrt(n_simulations)
        
        # Confidence interval
        z_score = stats.norm.ppf(0.975)
        confidence_interval = (
            option_price - z_score * standard_error,
            option_price + z_score * standard_error
        )
        
        return SimulationResult(
            option_price=option_price,
            standard_error=standard_error,
            confidence_interval=confidence_interval,
            greeks={},
            paths=paths if n_simulations <= 10000 else None,
            payoffs=discounted_payoffs,
            variance_reduction_effectiveness=variance_reduction_effectiveness,
            computation_time=0.0
        )
    
    def _analytical_geometric_asian(self, params: AsianOptionParameters) -> float:
        """Analytical solution for geometric Asian option"""
        # Adjusted parameters for geometric Asian
        T = params.time_to_expiry
        adjusted_vol = params.volatility / np.sqrt(3)
        adjusted_rate = (params.risk_free_rate - params.dividend_yield + 
                        params.volatility**2 / 6)
        
        # Use Black-Scholes formula with adjusted parameters
        d1 = (np.log(params.spot_price / params.strike_price) + 
              (adjusted_rate + 0.5 * adjusted_vol**2) * T) / (adjusted_vol * np.sqrt(T))
        d2 = d1 - adjusted_vol * np.sqrt(T)
        
        if params.option_type == OptionType.CALL:
            price = (params.spot_price * np.exp(-params.dividend_yield * T) * stats.norm.cdf(d1) -
                    params.strike_price * np.exp(-params.risk_free_rate * T) * stats.norm.cdf(d2))
        else:
            price = (params.strike_price * np.exp(-params.risk_free_rate * T) * stats.norm.cdf(-d2) -
                    params.spot_price * np.exp(-params.dividend_yield * T) * stats.norm.cdf(-d1))
        
        return price

class LookbackOption:
    """
    Lookback Options Pricing Engine
    
    Supports:
    - Floating strike lookback options
    - Fixed strike lookback options
    """
    
    def __init__(self):
        self.path_generator = PathGenerator()
    
    def price(self, params: LookbackOptionParameters, n_simulations: int = 100000,
              n_time_steps: int = 252) -> SimulationResult:
        """
        Price lookback option using Monte Carlo simulation
        
        Args:
            params: Lookback option parameters
            n_simulations: Number of Monte Carlo paths
            n_time_steps: Number of time steps per path
            
        Returns:
            Simulation results with lookback option price
        """
        # Generate price paths
        paths = self.path_generator.generate_paths(
            params, n_simulations, n_time_steps
        )
        
        # Determine lookback period
        start_step = int(params.lookback_start * n_time_steps)
        lookback_paths = paths[:, start_step:]
        
        # Calculate extreme values
        if params.lookback_type == "floating":
            if params.option_type == OptionType.CALL:
                # Call pays S_T - min(S_t)
                min_prices = np.min(lookback_paths, axis=1)
                payoffs = np.maximum(paths[:, -1] - min_prices, 0)
            else:
                # Put pays max(S_t) - S_T
                max_prices = np.max(lookback_paths, axis=1)
                payoffs = np.maximum(max_prices - paths[:, -1], 0)
        else:  # fixed strike
            if params.option_type == OptionType.CALL:
                # Call pays max(max(S_t) - K, 0)
                max_prices = np.max(lookback_paths, axis=1)
                payoffs = np.maximum(max_prices - params.strike_price, 0)
            else:
                # Put pays max(K - min(S_t), 0)
                min_prices = np.min(lookback_paths, axis=1)
                payoffs = np.maximum(params.strike_price - min_prices, 0)
        
        # Discount to present value
        discount_factor = np.exp(-params.risk_free_rate * params.time_to_expiry)
        discounted_payoffs = payoffs * discount_factor
        
        # Calculate statistics
        option_price = np.mean(discounted_payoffs)
        standard_error = np.std(discounted_payoffs) / np.sqrt(n_simulations)
        
        # Confidence interval
        z_score = stats.norm.ppf(0.975)
        confidence_interval = (
            option_price - z_score * standard_error,
            option_price + z_score * standard_error
        )
        
        return SimulationResult(
            option_price=option_price,
            standard_error=standard_error,
            confidence_interval=confidence_interval,
            greeks={},
            paths=paths if n_simulations <= 10000 else None,
            payoffs=discounted_payoffs,
            variance_reduction_effectiveness=0.0,
            computation_time=0.0
        )

class RainbowOption:
    """
    Rainbow (Multi-Asset) Options Pricing Engine
    
    Supports:
    - Best-of options (max of multiple assets)
    - Worst-of options (min of multiple assets)
    - Basket options (weighted sum of assets)
    """
    
    def __init__(self):
        pass
    
    def price(self, params: RainbowOptionParameters, n_simulations: int = 100000,
              n_time_steps: int = 252) -> SimulationResult:
        """
        Price rainbow option using Monte Carlo simulation
        
        Args:
            params: Rainbow option parameters
            n_simulations: Number of Monte Carlo paths
            n_time_steps: Number of time steps per path
            
        Returns:
            Simulation results with rainbow option price
        """
        n_assets = len(params.spot_prices)
        dt = params.time_to_expiry / n_time_steps
        
        # Generate correlated random numbers
        random_numbers = np.random.randn(n_simulations, n_time_steps, n_assets)
        
        # Apply correlation using Cholesky decomposition
        try:
            L = np.linalg.cholesky(params.correlation_matrix)
            correlated_randoms = np.zeros_like(random_numbers)
            for i in range(n_simulations):
                for j in range(n_time_steps):
                    correlated_randoms[i, j, :] = L @ random_numbers[i, j, :]
        except np.linalg.LinAlgError:
            # If correlation matrix is not positive definite, use original randoms
            correlated_randoms = random_numbers
        
        # Generate paths for each asset
        all_paths = np.zeros((n_simulations, n_time_steps + 1, n_assets))
        
        for asset_idx in range(n_assets):
            all_paths[:, 0, asset_idx] = params.spot_prices[asset_idx]
            
            # GBM parameters for this asset
            mu = params.risk_free_rate - params.dividend_yields[asset_idx]
            sigma = params.volatilities[asset_idx]
            
            # Generate paths
            for t in range(n_time_steps):
                log_return = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * correlated_randoms[:, t, asset_idx]
                all_paths[:, t+1, asset_idx] = all_paths[:, t, asset_idx] * np.exp(log_return)
        
        # Calculate rainbow payoffs
        final_prices = all_paths[:, -1, :]
        
        if params.rainbow_type == "best_of":
            underlying_values = np.max(final_prices, axis=1)
        elif params.rainbow_type == "worst_of":
            underlying_values = np.min(final_prices, axis=1)
        elif params.rainbow_type == "basket":
            if params.weights is None:
                # Equal weights
                weights = np.ones(n_assets) / n_assets
            else:
                weights = np.array(params.weights)
            underlying_values = np.sum(final_prices * weights, axis=1)
        else:
            raise ValueError(f"Unknown rainbow type: {params.rainbow_type}")
        
        # Calculate option payoffs
        if params.option_type == OptionType.CALL:
            payoffs = np.maximum(underlying_values - params.strike_price, 0)
        else:
            payoffs = np.maximum(params.strike_price - underlying_values, 0)
        
        # Discount to present value
        discount_factor = np.exp(-params.risk_free_rate * params.time_to_expiry)
        discounted_payoffs = payoffs * discount_factor
        
        # Calculate statistics
        option_price = np.mean(discounted_payoffs)
        standard_error = np.std(discounted_payoffs) / np.sqrt(n_simulations)
        
        # Confidence interval
        z_score = stats.norm.ppf(0.975)
        confidence_interval = (
            option_price - z_score * standard_error,
            option_price + z_score * standard_error
        )
        
        return SimulationResult(
            option_price=option_price,
            standard_error=standard_error,
            confidence_interval=confidence_interval,
            greeks={},
            paths=all_paths if n_simulations <= 5000 else None,
            payoffs=discounted_payoffs,
            variance_reduction_effectiveness=0.0,
            computation_time=0.0
        )

class DigitalOption:
    """
    Digital/Binary Options Pricing Engine
    
    Options that pay a fixed amount if condition is met:
    - Cash-or-nothing options
    - Asset-or-nothing options
    """
    
    def __init__(self):
        self.path_generator = PathGenerator()
    
    def price(self, params: OptionParameters, payout_amount: float = 1.0,
              n_simulations: int = 100000, n_time_steps: int = 252) -> SimulationResult:
        """
        Price digital option using Monte Carlo simulation
        
        Args:
            params: Option parameters
            payout_amount: Fixed payout amount
            n_simulations: Number of Monte Carlo paths
            n_time_steps: Number of time steps per path
            
        Returns:
            Simulation results with digital option price
        """
        # Generate price paths
        paths = self.path_generator.generate_paths(
            params, n_simulations, n_time_steps
        )
        
        final_prices = paths[:, -1]
        
        # Digital payoff: fixed amount if condition is met
        if params.option_type == OptionType.CALL:
            # Pays payout_amount if S_T > K
            payoffs = np.where(final_prices > params.strike_price, payout_amount, 0.0)
        else:
            # Pays payout_amount if S_T < K
            payoffs = np.where(final_prices < params.strike_price, payout_amount, 0.0)
        
        # Discount to present value
        discount_factor = np.exp(-params.risk_free_rate * params.time_to_expiry)
        discounted_payoffs = payoffs * discount_factor
        
        # Calculate statistics
        option_price = np.mean(discounted_payoffs)
        standard_error = np.std(discounted_payoffs) / np.sqrt(n_simulations)
        
        # Confidence interval
        z_score = stats.norm.ppf(0.975)
        confidence_interval = (
            option_price - z_score * standard_error,
            option_price + z_score * standard_error
        )
        
        return SimulationResult(
            option_price=option_price,
            standard_error=standard_error,
            confidence_interval=confidence_interval,
            greeks={},
            paths=paths if n_simulations <= 10000 else None,
            payoffs=discounted_payoffs,
            variance_reduction_effectiveness=0.0,
            computation_time=0.0
        )

class AmericanOption:
    """
    American Options with Early Exercise
    
    Uses Longstaff-Schwartz Least Squares Monte Carlo algorithm
    """
    
    def __init__(self):
        self.path_generator = PathGenerator()
    
    def price(self, params: OptionParameters, n_simulations: int = 50000,
              n_time_steps: int = 100) -> SimulationResult:
        """
        Price American option using LSM algorithm
        
        Args:
            params: Option parameters
            n_simulations: Number of Monte Carlo paths
            n_time_steps: Number of time steps per path
            
        Returns:
            Simulation results with American option price
        """
        # Generate price paths
        paths = self.path_generator.generate_paths(
            params, n_simulations, n_time_steps
        )
        
        dt = params.time_to_expiry / n_time_steps
        discount_factor = np.exp(-params.risk_free_rate * dt)
        
        # Initialize cash flows matrix
        cash_flows = np.zeros_like(paths)
        
        # Terminal condition
        if params.option_type == OptionType.CALL:
            cash_flows[:, -1] = np.maximum(paths[:, -1] - params.strike_price, 0)
        else:
            cash_flows[:, -1] = np.maximum(params.strike_price - paths[:, -1], 0)
        
        # Backward induction using LSM
        for t in range(n_time_steps - 1, 0, -1):
            # Intrinsic value
            if params.option_type == OptionType.CALL:
                intrinsic = np.maximum(paths[:, t] - params.strike_price, 0)
            else:
                intrinsic = np.maximum(params.strike_price - paths[:, t], 0)
            
            # Only consider in-the-money paths
            itm_mask = intrinsic > 0
            
            if np.sum(itm_mask) > 10:  # Need sufficient data for regression
                x = paths[itm_mask, t]
                
                # Discounted continuation value
                continuation_cf = np.sum(
                    cash_flows[itm_mask, t+1:] * 
                    (discount_factor ** np.arange(1, n_time_steps - t)), 
                    axis=1
                )
                
                # Polynomial regression (Laguerre polynomials approximation)
                try:
                    # Use simple polynomial basis
                    X = np.column_stack([
                        np.ones(len(x)),
                        x,
                        x**2,
                        x**3
                    ])
                    
                    # Solve regression
                    coeffs = np.linalg.lstsq(X, continuation_cf, rcond=None)[0]
                    continuation_value = X @ coeffs
                    
                    # Exercise decision
                    exercise_mask = intrinsic[itm_mask] > continuation_value
                    
                    # Update cash flows for early exercise
                    itm_indices = np.where(itm_mask)[0]
                    exercise_indices = itm_indices[exercise_mask]
                    
                    cash_flows[exercise_indices, t] = intrinsic[exercise_indices]
                    cash_flows[exercise_indices, t+1:] = 0
                    
                except np.linalg.LinAlgError:
                    # Fallback: exercise if deeply ITM
                    deep_itm = intrinsic[itm_mask] > params.strike_price * 0.1
                    itm_indices = np.where(itm_mask)[0]
                    exercise_indices = itm_indices[deep_itm]
                    
                    cash_flows[exercise_indices, t] = intrinsic[exercise_indices]
                    cash_flows[exercise_indices, t+1:] = 0
        
        # Calculate option values
        total_cf = np.sum(
            cash_flows * (discount_factor ** np.arange(n_time_steps + 1)), 
            axis=1
        )
        
        option_price = np.mean(total_cf)
        standard_error = np.std(total_cf) / np.sqrt(n_simulations)
        
        # Confidence interval
        z_score = stats.norm.ppf(0.975)
        confidence_interval = (
            option_price - z_score * standard_error,
            option_price + z_score * standard_error
        )
        
        return SimulationResult(
            option_price=option_price,
            standard_error=standard_error,
            confidence_interval=confidence_interval,
            greeks={},
            paths=paths if n_simulations <= 5000 else None,
            payoffs=total_cf,
            variance_reduction_effectiveness=0.0,
            computation_time=0.0
        )

# Example usage and testing
if __name__ == "__main__":
    print("=== EXOTIC OPTIONS TESTING ===")
    
    # Base parameters
    base_params = OptionParameters(
        spot_price=100.0,
        strike_price=105.0,
        time_to_expiry=0.25,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.02,
        option_type=OptionType.CALL
    )
    
    print(f"Base Parameters:")
    print(f"Spot: ${base_params.spot_price}")
    print(f"Strike: ${base_params.strike_price}")
    print(f"Time to Expiry: {base_params.time_to_expiry:.2f} years")
    print(f"Volatility: {base_params.volatility:.1%}")
    
    # Test Barrier Option
    print("\n=== BARRIER OPTION ===")
    barrier_params = BarrierOptionParameters(
        **vars(base_params),
        barrier_level=110.0,
        barrier_type=BarrierType.UP_AND_OUT,
        rebate=2.0
    )
    
    barrier_engine = BarrierOption()
    barrier_result = barrier_engine.price(barrier_params, n_simulations=50000)
    print(f"Up-and-Out Barrier Option (Barrier=${barrier_params.barrier_level}): ${barrier_result.option_price:.4f}")
    
    # Test Asian Option
    print("\n=== ASIAN OPTION ===")
    asian_params = AsianOptionParameters(
        **vars(base_params),
        asian_type=AsianType.ARITHMETIC,
        averaging_start=0.0
    )
    
    asian_engine = AsianOption()
    asian_result = asian_engine.price(asian_params, n_simulations=50000)
    print(f"Arithmetic Asian Option: ${asian_result.option_price:.4f}")
    print(f"Variance Reduction: {asian_result.variance_reduction_effectiveness:.2%}")
    
    # Test Lookback Option
    print("\n=== LOOKBACK OPTION ===")
    lookback_params = LookbackOptionParameters(
        **vars(base_params),
        lookback_type="floating",
        lookback_start=0.0
    )
    
    lookback_engine = LookbackOption()
    lookback_result = lookback_engine.price(lookback_params, n_simulations=50000)
    print(f"Floating Strike Lookback Call: ${lookback_result.option_price:.4f}")
    
    # Test Rainbow Option
    print("\n=== RAINBOW OPTION ===")
    correlation_matrix = np.array([[1.0, 0.3], [0.3, 1.0]])
    
    rainbow_params = RainbowOptionParameters(
        spot_prices=[100.0, 95.0],
        strike_price=105.0,
        time_to_expiry=0.25,
        risk_free_rate=0.05,
        volatilities=[0.20, 0.25],
        correlation_matrix=correlation_matrix,
        dividend_yields=[0.02, 0.01],
        option_type=OptionType.CALL,
        rainbow_type="best_of"
    )
    
    rainbow_engine = RainbowOption()
    rainbow_result = rainbow_engine.price(rainbow_params, n_simulations=50000)
    print(f"Best-of Two Assets Rainbow Call: ${rainbow_result.option_price:.4f}")
    
    # Test Digital Option
    print("\n=== DIGITAL OPTION ===")
    digital_engine = DigitalOption()
    digital_result = digital_engine.price(base_params, payout_amount=10.0, n_simulations=50000)
    print(f"Digital Call Option (Payout=$10): ${digital_result.option_price:.4f}")
    
    # Test American Option
    print("\n=== AMERICAN OPTION ===")
    american_engine = AmericanOption()
    american_result = american_engine.price(base_params, n_simulations=30000)
    print(f"American Call Option: ${american_result.option_price:.4f}")
    
    print("\nExotic options testing completed!")

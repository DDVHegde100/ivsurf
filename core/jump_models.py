"""
Jump Models Core Engine
======================

Professional implementation of jump-diffusion models including:
- Unified interface for different jump models
- Jump parameter estimation and risk decomposition
- Jump risk premium analysis
- Model comparison and selection tools
- Advanced jump detection algorithms
- Risk management with jump scenarios

Mathematical Framework:
- Compound Poisson processes for jump timing
- Various jump size distributions (normal, double exponential, etc.)
- Jump risk premium decomposition
- Jump-adjusted Greeks and risk measures

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize, signal
from typing import Dict, List, Tuple, Optional, Union, Callable
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Import our jump-diffusion implementations
from models.jump_diffusion import (
    MertonJumpDiffusion, KouJumpDiffusion, 
    MertonParameters, KouParameters,
    JumpCalibrationResult, create_merton_model, create_kou_model
)

class JumpDetectionMethod(Enum):
    """Methods for detecting jumps in price series"""
    LEE_MYKLAND = "lee_mykland"
    BARNDORFF_NIELSEN = "barndorff_nielsen"
    THRESHOLD = "threshold"
    WAVELETS = "wavelets"

@dataclass
class JumpEvent:
    """Represents a detected jump event"""
    time: float
    price_before: float
    price_after: float
    jump_size: float
    jump_return: float
    significance: float
    direction: str  # 'up' or 'down'

@dataclass
class JumpRiskPremium:
    """Jump risk premium decomposition"""
    total_premium: float
    diffusion_premium: float
    jump_premium: float
    jump_intensity_premium: float
    jump_size_premium: float
    correlation_premium: float

class JumpDetector:
    """
    Advanced jump detection in financial time series
    
    Implements various statistical tests for jump detection
    including Lee-Mykland, Barndorff-Nielsen-Shephard, and others.
    """
    
    def __init__(self, method: JumpDetectionMethod = JumpDetectionMethod.LEE_MYKLAND):
        """
        Initialize jump detector
        
        Args:
            method: Jump detection method to use
        """
        self.method = method
    
    def lee_mykland_test(self, prices: np.ndarray, 
                        significance_level: float = 0.01) -> List[JumpEvent]:
        """
        Lee-Mykland (2008) jump test
        
        Tests for jumps using realized volatility estimators
        
        Args:
            prices: Price series
            significance_level: Statistical significance level
            
        Returns:
            List of detected jump events
        """
        returns = np.diff(np.log(prices))
        n = len(returns)
        
        if n < 50:
            warnings.warn("Insufficient data for reliable jump detection")
            return []
        
        # Rolling window for local volatility estimation
        window = min(50, n // 4)
        jumps = []
        
        # Critical value from extreme value theory
        beta_star = np.sqrt(2 * np.log(n))
        c_alpha = np.sqrt(2 * np.log(1 / significance_level))
        
        for i in range(window, n):
            # Local volatility estimation
            local_returns = returns[i-window:i]
            local_vol = np.sqrt(np.mean(local_returns**2))
            
            if local_vol > 0:
                # Jump test statistic
                test_stat = returns[i] / local_vol
                
                # Test for significance
                if abs(test_stat) > c_alpha:
                    jump_event = JumpEvent(
                        time=i,
                        price_before=prices[i],
                        price_after=prices[i+1],
                        jump_size=prices[i+1] - prices[i],
                        jump_return=returns[i],
                        significance=abs(test_stat),
                        direction='up' if returns[i] > 0 else 'down'
                    )
                    jumps.append(jump_event)
        
        return jumps
    
    def threshold_detection(self, prices: np.ndarray, 
                          threshold: float = 3.0) -> List[JumpEvent]:
        """
        Simple threshold-based jump detection
        
        Args:
            prices: Price series
            threshold: Threshold in standard deviations
            
        Returns:
            List of detected jump events
        """
        returns = np.diff(np.log(prices))
        vol = np.std(returns)
        
        jumps = []
        for i, ret in enumerate(returns):
            if abs(ret) > threshold * vol:
                jump_event = JumpEvent(
                    time=i,
                    price_before=prices[i],
                    price_after=prices[i+1],
                    jump_size=prices[i+1] - prices[i],
                    jump_return=ret,
                    significance=abs(ret) / vol,
                    direction='up' if ret > 0 else 'down'
                )
                jumps.append(jump_event)
        
        return jumps
    
    def detect_jumps(self, prices: np.ndarray, **kwargs) -> List[JumpEvent]:
        """
        Detect jumps using the configured method
        
        Args:
            prices: Price series
            **kwargs: Method-specific parameters
            
        Returns:
            List of detected jump events
        """
        if self.method == JumpDetectionMethod.LEE_MYKLAND:
            return self.lee_mykland_test(prices, **kwargs)
        elif self.method == JumpDetectionMethod.THRESHOLD:
            return self.threshold_detection(prices, **kwargs)
        else:
            raise NotImplementedError(f"Method {self.method} not implemented")

class JumpModelEngine:
    """
    Unified engine for jump-diffusion modeling
    
    Provides model comparison, calibration, and risk analysis
    for different jump-diffusion models.
    """
    
    def __init__(self):
        """Initialize the jump model engine"""
        self.models = {}
        self.calibration_results = {}
        self.jump_detector = JumpDetector()
    
    def register_model(self, name: str, model: Union[MertonJumpDiffusion, KouJumpDiffusion]):
        """Register a jump-diffusion model"""
        self.models[name] = model
    
    def compare_models(self, market_data: pd.DataFrame, 
                      model_names: List[str] = None) -> pd.DataFrame:
        """
        Compare different jump models against market data
        
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
            
            # Calibrate model
            try:
                calib_result = model.calibrate_to_market(market_data)
                self.calibration_results[name] = calib_result
                
                results.append({
                    'model': name,
                    'rmse': calib_result.rmse,
                    'mae': calib_result.mae,
                    'max_error': calib_result.max_error,
                    'convergence': calib_result.convergence,
                    'jump_intensity': calib_result.jump_intensity,
                    'jump_probability': calib_result.jump_probability,
                    'iterations': calib_result.iterations
                })
                
            except Exception as e:
                results.append({
                    'model': name,
                    'rmse': np.nan,
                    'mae': np.nan,
                    'max_error': np.nan,
                    'convergence': False,
                    'jump_intensity': np.nan,
                    'jump_probability': np.nan,
                    'iterations': 0,
                    'error': str(e)
                })
        
        return pd.DataFrame(results).sort_values('rmse')
    
    def estimate_jump_parameters(self, price_series: np.ndarray, 
                                dt: float = 1/252) -> Dict[str, float]:
        """
        Estimate jump parameters from price series
        
        Args:
            price_series: Historical price series
            dt: Time increment
            
        Returns:
            Dictionary of estimated jump parameters
        """
        # Detect jumps
        jumps = self.jump_detector.detect_jumps(price_series)
        
        if len(jumps) == 0:
            return {
                'jump_intensity': 0.0,
                'jump_frequency': 0.0,
                'mean_jump_size': 0.0,
                'jump_volatility': 0.0,
                'upward_probability': 0.5
            }
        
        # Calculate jump statistics
        jump_times = [j.time for j in jumps]
        jump_returns = [j.jump_return for j in jumps]
        
        # Jump intensity (events per year)
        total_time = len(price_series) * dt
        jump_intensity = len(jumps) / total_time
        
        # Jump size statistics
        mean_jump_size = np.mean(jump_returns)
        jump_volatility = np.std(jump_returns)
        
        # Directional statistics
        upward_jumps = sum(1 for j in jumps if j.direction == 'up')
        upward_probability = upward_jumps / len(jumps)
        
        return {
            'jump_intensity': jump_intensity,
            'jump_frequency': len(jumps),
            'mean_jump_size': mean_jump_size,
            'jump_volatility': jump_volatility,
            'upward_probability': upward_probability,
            'detected_jumps': jumps
        }
    
    def decompose_risk_premium(self, model_name: str, 
                             risk_free_rate: float = 0.05,
                             market_price_of_risk: float = 0.3) -> JumpRiskPremium:
        """
        Decompose risk premium into diffusion and jump components
        
        Args:
            model_name: Name of the calibrated model
            risk_free_rate: Risk-free rate
            market_price_of_risk: Market price of diffusion risk
            
        Returns:
            Jump risk premium decomposition
        """
        if model_name not in self.calibration_results:
            raise ValueError(f"Model {model_name} not calibrated")
        
        calib_result = self.calibration_results[model_name]
        params = calib_result.parameters
        
        if isinstance(params, MertonParameters):
            # Merton model decomposition
            sigma = params.sigma
            lambda_j = params.lambda_j
            mu_j = params.mu_j
            sigma_j = params.sigma_j
            
            # Expected jump size
            k = np.exp(mu_j + 0.5 * sigma_j**2) - 1
            
            # Risk premium components
            diffusion_premium = market_price_of_risk * sigma
            jump_intensity_premium = lambda_j * k * 0.1  # Simplified
            jump_size_premium = lambda_j * sigma_j * 0.05  # Simplified
            jump_premium = jump_intensity_premium + jump_size_premium
            
            total_premium = diffusion_premium + jump_premium
            
            return JumpRiskPremium(
                total_premium=total_premium,
                diffusion_premium=diffusion_premium,
                jump_premium=jump_premium,
                jump_intensity_premium=jump_intensity_premium,
                jump_size_premium=jump_size_premium,
                correlation_premium=0.0
            )
            
        elif isinstance(params, KouParameters):
            # Kou model decomposition
            sigma = params.sigma
            lambda_j = params.lambda_j
            p = params.p
            eta_u = params.eta_u
            eta_d = params.eta_d
            
            # Expected jump size
            k = p * eta_u / (eta_u - 1) + (1 - p) * eta_d / (eta_d + 1) - 1
            
            # Risk premium components
            diffusion_premium = market_price_of_risk * sigma
            jump_intensity_premium = lambda_j * abs(k) * 0.1
            jump_size_premium = lambda_j * (1/eta_u + 1/eta_d) * 0.05
            jump_premium = jump_intensity_premium + jump_size_premium
            
            total_premium = diffusion_premium + jump_premium
            
            return JumpRiskPremium(
                total_premium=total_premium,
                diffusion_premium=diffusion_premium,
                jump_premium=jump_premium,
                jump_intensity_premium=jump_intensity_premium,
                jump_size_premium=jump_size_premium,
                correlation_premium=0.0
            )
        
        else:
            raise ValueError("Unknown parameter type")
    
    def generate_jump_scenarios(self, model_name: str, n_scenarios: int = 1000,
                              time_horizon: float = 1.0) -> pd.DataFrame:
        """
        Generate jump scenarios for stress testing
        
        Args:
            model_name: Name of the model
            n_scenarios: Number of scenarios
            time_horizon: Time horizon in years
            
        Returns:
            DataFrame with scenario results
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not registered")
        
        model = self.models[model_name]
        
        # Generate paths
        S_paths, jump_info = model.simulate_paths(time_horizon, 252, n_scenarios)
        
        # Extract scenario statistics
        scenarios = []
        for i in range(n_scenarios):
            final_price = S_paths[i, -1]
            initial_price = S_paths[i, 0]
            total_return = (final_price / initial_price - 1) * 100
            
            # Count jumps in this path
            path_jumps = sum(1 for j_info in jump_info 
                           if i in j_info.get('paths', []))
            
            # Calculate maximum drawdown
            path_prices = S_paths[i, :]
            running_max = np.maximum.accumulate(path_prices)
            drawdowns = (path_prices - running_max) / running_max
            max_drawdown = np.min(drawdowns) * 100
            
            scenarios.append({
                'scenario': i + 1,
                'final_price': final_price,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'jump_count': path_jumps,
                'volatility': np.std(np.diff(np.log(path_prices))) * np.sqrt(252) * 100
            })
        
        return pd.DataFrame(scenarios)
    
    def calculate_jump_adjusted_greeks(self, model_name: str, K: float, T: float,
                                     option_type: str = 'call',
                                     bump_size: float = 0.01) -> Dict[str, float]:
        """
        Calculate option Greeks adjusted for jump risk
        
        Args:
            model_name: Name of the model
            K: Strike price
            T: Time to expiration
            option_type: 'call' or 'put'
            bump_size: Finite difference bump size
            
        Returns:
            Dictionary of jump-adjusted Greeks
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not registered")
        
        model = self.models[model_name]
        
        # Base price
        base_price = model.option_price(K, T, option_type)[0]
        
        # Delta: bump underlying
        S_up = model.S0 * (1 + bump_size)
        S_down = model.S0 * (1 - bump_size)
        
        if hasattr(model.params, 'mu'):  # Both Merton and Kou have mu
            # Create bumped models
            if isinstance(model, MertonJumpDiffusion):
                params_up = MertonParameters(
                    model.params.mu, model.params.sigma, model.params.lambda_j,
                    model.params.mu_j, model.params.sigma_j
                )
                params_down = MertonParameters(
                    model.params.mu, model.params.sigma, model.params.lambda_j,
                    model.params.mu_j, model.params.sigma_j
                )
                model_up = MertonJumpDiffusion(params_up, S_up, model.r)
                model_down = MertonJumpDiffusion(params_down, S_down, model.r)
            else:  # Kou model
                params_up = KouParameters(
                    model.params.mu, model.params.sigma, model.params.lambda_j,
                    model.params.p, model.params.eta_u, model.params.eta_d
                )
                params_down = KouParameters(
                    model.params.mu, model.params.sigma, model.params.lambda_j,
                    model.params.p, model.params.eta_u, model.params.eta_d
                )
                model_up = KouJumpDiffusion(params_up, S_up, model.r)
                model_down = KouJumpDiffusion(params_down, S_down, model.r)
            
            price_up = model_up.option_price(K, T, option_type)[0]
            price_down = model_down.option_price(K, T, option_type)[0]
            
            delta = (price_up - price_down) / (2 * model.S0 * bump_size)
            gamma = (price_up - 2 * base_price + price_down) / (model.S0 * bump_size)**2
        else:
            delta = gamma = 0.0
        
        # Jump-specific Greeks
        # Lambda (jump intensity sensitivity)
        if isinstance(model, MertonJumpDiffusion):
            lambda_up = model.params.lambda_j * (1 + bump_size)
            lambda_down = model.params.lambda_j * (1 - bump_size)
            
            params_lambda_up = MertonParameters(
                model.params.mu, model.params.sigma, lambda_up,
                model.params.mu_j, model.params.sigma_j
            )
            params_lambda_down = MertonParameters(
                model.params.mu, model.params.sigma, lambda_down,
                model.params.mu_j, model.params.sigma_j
            )
            
            model_lambda_up = MertonJumpDiffusion(params_lambda_up, model.S0, model.r)
            model_lambda_down = MertonJumpDiffusion(params_lambda_down, model.S0, model.r)
            
            price_lambda_up = model_lambda_up.option_price(K, T, option_type)[0]
            price_lambda_down = model_lambda_down.option_price(K, T, option_type)[0]
            
            lambda_greek = (price_lambda_up - price_lambda_down) / (2 * bump_size * model.params.lambda_j)
        else:
            lambda_greek = 0.0
        
        # Theta (time decay)
        T_down = T - bump_size / 365
        if T_down > 0:
            price_theta = model.option_price(K, T_down, option_type)[0]
            theta = (price_theta - base_price) / (bump_size / 365)
        else:
            theta = 0.0
        
        return {
            'price': base_price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'lambda': lambda_greek,  # Jump intensity Greek
            'jump_vega': lambda_greek * 0.1  # Simplified jump volatility Greek
        }

# Convenience functions
def detect_jumps_in_series(prices: np.ndarray, 
                          method: str = 'lee_mykland') -> List[JumpEvent]:
    """Detect jumps in a price series"""
    detector = JumpDetector(JumpDetectionMethod(method))
    return detector.detect_jumps(prices)

def create_jump_engine() -> JumpModelEngine:
    """Create a jump model engine with standard models"""
    engine = JumpModelEngine()
    
    # Register standard models
    merton_model = create_merton_model()
    kou_model = create_kou_model()
    
    engine.register_model("Merton", merton_model)
    engine.register_model("Kou", kou_model)
    
    return engine

# Example usage and testing
if __name__ == "__main__":
    print("=== JUMP MODELS ENGINE TESTING ===")
    
    # Create jump engine
    jump_engine = create_jump_engine()
    
    # Generate sample price series with jumps
    np.random.seed(42)
    n_days = 252
    dt = 1/252
    
    # Simulate price path with jumps
    prices = [100.0]
    for i in range(n_days):
        # Normal return
        normal_return = np.random.normal(0.0005, 0.02)
        
        # Jump with 1% probability
        if np.random.random() < 0.01:
            jump_return = np.random.normal(-0.05, 0.03)  # Negative jump bias
            total_return = normal_return + jump_return
        else:
            total_return = normal_return
        
        new_price = prices[-1] * np.exp(total_return)
        prices.append(new_price)
    
    prices = np.array(prices)
    
    # Test jump detection
    print("\n=== JUMP DETECTION ===")
    jumps = detect_jumps_in_series(prices, 'threshold')
    print(f"Detected {len(jumps)} jumps")
    
    if jumps:
        print("Jump statistics:")
        jump_returns = [j.jump_return for j in jumps]
        print(f"  Mean jump return: {np.mean(jump_returns):.2%}")
        print(f"  Jump volatility: {np.std(jump_returns):.2%}")
        print(f"  Upward jumps: {sum(1 for j in jumps if j.direction == 'up')}")
        print(f"  Downward jumps: {sum(1 for j in jumps if j.direction == 'down')}")
    
    # Test parameter estimation
    print("\n=== PARAMETER ESTIMATION ===")
    jump_params = jump_engine.estimate_jump_parameters(prices)
    print(f"Estimated jump intensity: {jump_params['jump_intensity']:.2f} jumps/year")
    print(f"Mean jump size: {jump_params['mean_jump_size']:.2%}")
    print(f"Jump volatility: {jump_params['jump_volatility']:.2%}")
    print(f"Upward probability: {jump_params['upward_probability']:.2%}")
    
    # Test scenario generation
    print("\n=== SCENARIO GENERATION ===")
    scenarios = jump_engine.generate_jump_scenarios("Merton", 100, 1.0)
    print("Scenario statistics:")
    print(f"  Mean return: {scenarios['total_return'].mean():.1f}%")
    print(f"  Return volatility: {scenarios['total_return'].std():.1f}%")
    print(f"  Mean max drawdown: {scenarios['max_drawdown'].mean():.1f}%")
    print(f"  Average jumps per path: {scenarios['jump_count'].mean():.1f}")
    
    print("\nJump models engine testing completed successfully!")

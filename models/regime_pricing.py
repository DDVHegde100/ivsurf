"""
Regime-Dependent Option Pricing Models
====================================

Advanced option pricing with regime-switching volatility:
- Regime-dependent Black-Scholes pricing
- Markov-switching volatility models
- Regime-aware Greeks calculations
- Dynamic hedging strategies
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq, minimize
from scipy.special import erf
import warnings

warnings.filterwarnings('ignore')

class RegimeDependentPricer:
    """
    Option pricing with regime-switching volatility models
    """
    
    def __init__(self, n_regimes=2):
        self.n_regimes = n_regimes
        self.regime_parameters = {}
        self.transition_matrix = None
        self.current_regime_probs = None
        
    def calibrate_regime_model(self, returns, option_data=None):
        """
        Calibrate regime-switching model parameters
        
        Args:
            returns: Historical return series
            option_data: Optional market option prices for calibration
            
        Returns:
            dict: Calibration results
        """
        
        try:
            # Estimate regime parameters from returns
            regime_params = self._estimate_regime_parameters(returns)
            
            if regime_params['success']:
                self.regime_parameters = regime_params['parameters']
                self.transition_matrix = regime_params['transition_matrix']
                self.current_regime_probs = regime_params['current_probabilities']
                
                # If option data provided, refine calibration
                if option_data is not None:
                    refined_params = self._refine_with_option_data(option_data)
                    if refined_params['success']:
                        self.regime_parameters.update(refined_params['parameters'])
                
                return {
                    'success': True,
                    'regime_parameters': self.regime_parameters,
                    'transition_matrix': self.transition_matrix,
                    'current_regime_probs': self.current_regime_probs,
                    'calibration_quality': self._assess_calibration_quality(returns)
                }
            else:
                return {'success': False, 'error': regime_params.get('error', 'Unknown error')}
                
        except Exception as e:
            return {'success': False, 'error': f'Calibration failed: {str(e)}'}
    
    def price_option_regime_dependent(self, S, K, T, r, option_type='call', 
                                    regime_weights=None):
        """
        Price option using regime-dependent model
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            option_type: 'call' or 'put'
            regime_weights: Custom regime probabilities (optional)
            
        Returns:
            dict: Pricing results
        """
        
        if not self.regime_parameters:
            return {'error': 'Model not calibrated'}
        
        try:
            # Use current regime probabilities or provided weights
            weights = regime_weights if regime_weights is not None else self.current_regime_probs
            
            if weights is None:
                weights = [1.0 / self.n_regimes] * self.n_regimes
            
            # Price option in each regime
            regime_prices = []
            regime_details = {}
            
            for i in range(self.n_regimes):
                regime_vol = self.regime_parameters[f'regime_{i}']['volatility']
                regime_price = self._black_scholes_price(S, K, T, r, regime_vol, option_type)
                regime_prices.append(regime_price)
                
                regime_details[f'regime_{i}'] = {
                    'price': regime_price,
                    'volatility': regime_vol,
                    'weight': weights[i]
                }
            
            # Weighted average price
            final_price = np.sum([price * weight for price, weight in zip(regime_prices, weights)])
            
            # Calculate regime-dependent Greeks
            greeks = self._calculate_regime_greeks(S, K, T, r, option_type, weights)
            
            return {
                'price': final_price,
                'regime_prices': regime_prices,
                'regime_weights': weights,
                'regime_details': regime_details,
                'greeks': greeks,
                'pricing_method': 'regime_dependent'
            }
            
        except Exception as e:
            return {'error': f'Pricing failed: {str(e)}'}
    
    def calculate_regime_hedging_strategy(self, S, K, T, r, option_type='call',
                                        hedge_frequency='daily'):
        """
        Calculate dynamic hedging strategy accounting for regime switches
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            option_type: 'call' or 'put'
            hedge_frequency: Hedging frequency
            
        Returns:
            dict: Hedging strategy details
        """
        
        if not self.regime_parameters:
            return {'error': 'Model not calibrated'}
        
        try:
            # Calculate hedging parameters for each regime
            hedge_ratios = {}
            regime_deltas = {}
            
            for i in range(self.n_regimes):
                regime_vol = self.regime_parameters[f'regime_{i}']['volatility']
                
                # Calculate delta in this regime
                delta = self._calculate_delta(S, K, T, r, regime_vol, option_type)
                regime_deltas[f'regime_{i}'] = delta
                
                # Hedging strategy adjustments for regime
                regime_adjustment = self._calculate_regime_hedge_adjustment(i, T)
                hedge_ratios[f'regime_{i}'] = delta * regime_adjustment
            
            # Overall hedge ratio (weighted by regime probabilities)
            weights = self.current_regime_probs or [1.0 / self.n_regimes] * self.n_regimes
            overall_hedge_ratio = np.sum([hedge_ratios[f'regime_{i}'] * weights[i] 
                                        for i in range(self.n_regimes)])
            
            # Regime transition adjustments
            transition_adjustments = self._calculate_transition_adjustments(S, K, T, r, option_type)
            
            return {
                'overall_hedge_ratio': overall_hedge_ratio,
                'regime_hedge_ratios': hedge_ratios,
                'regime_deltas': regime_deltas,
                'regime_weights': weights,
                'transition_adjustments': transition_adjustments,
                'hedge_frequency': hedge_frequency,
                'rebalancing_triggers': self._get_rebalancing_triggers()
            }
            
        except Exception as e:
            return {'error': f'Hedging calculation failed: {str(e)}'}
    
    def scenario_analysis(self, S, K, T, r, option_type='call', 
                         scenario_parameters=None):
        """
        Perform scenario analysis under different regime assumptions
        
        Args:
            S: Current stock price
            K: Strike price  
            T: Time to expiration
            r: Risk-free rate
            option_type: 'call' or 'put'
            scenario_parameters: Custom scenario parameters
            
        Returns:
            dict: Scenario analysis results
        """
        
        if not self.regime_parameters:
            return {'error': 'Model not calibrated'}
        
        try:
            scenarios = {}
            
            # Base case (current regime probabilities)
            base_result = self.price_option_regime_dependent(S, K, T, r, option_type)
            scenarios['base_case'] = base_result
            
            # Pure regime scenarios
            for i in range(self.n_regimes):
                pure_weights = [0.0] * self.n_regimes
                pure_weights[i] = 1.0
                
                pure_result = self.price_option_regime_dependent(
                    S, K, T, r, option_type, pure_weights
                )
                scenarios[f'pure_regime_{i}'] = pure_result
            
            # Stress scenarios
            stress_scenarios = self._generate_stress_scenarios()
            
            for scenario_name, scenario_weights in stress_scenarios.items():
                stress_result = self.price_option_regime_dependent(
                    S, K, T, r, option_type, scenario_weights
                )
                scenarios[f'stress_{scenario_name}'] = stress_result
            
            # Sensitivity analysis
            sensitivity_results = self._regime_sensitivity_analysis(S, K, T, r, option_type)
            
            return {
                'scenarios': scenarios,
                'sensitivity_analysis': sensitivity_results,
                'price_range': {
                    'min': min([s.get('price', 0) for s in scenarios.values() if 'price' in s]),
                    'max': max([s.get('price', 0) for s in scenarios.values() if 'price' in s])
                }
            }
            
        except Exception as e:
            return {'error': f'Scenario analysis failed: {str(e)}'}
    
    def _estimate_regime_parameters(self, returns):
        """Estimate regime parameters using EM algorithm (simplified)"""
        
        try:
            # Simple 2-regime estimation
            returns_clean = returns.dropna()
            
            if len(returns_clean) < 50:
                return {'success': False, 'error': 'Insufficient data'}
            
            # Initialize parameters
            volatilities = []
            means = []
            
            # Split data into high and low volatility periods for initial estimates
            rolling_vol = returns_clean.rolling(window=20).std()
            vol_median = rolling_vol.median()
            
            high_vol_mask = rolling_vol > vol_median
            low_vol_periods = returns_clean[~high_vol_mask].dropna()
            high_vol_periods = returns_clean[high_vol_mask].dropna()
            
            if len(low_vol_periods) > 10 and len(high_vol_periods) > 10:
                # Low volatility regime (Regime 0)
                vol_low = low_vol_periods.std() * np.sqrt(252)  # Annualized
                mean_low = low_vol_periods.mean() * 252  # Annualized
                
                # High volatility regime (Regime 1)
                vol_high = high_vol_periods.std() * np.sqrt(252)  # Annualized
                mean_high = high_vol_periods.mean() * 252  # Annualized
                
                volatilities = [vol_low, vol_high]
                means = [mean_low, mean_high]
            else:
                # Fallback: use overall statistics with adjustments
                overall_vol = returns_clean.std() * np.sqrt(252)
                overall_mean = returns_clean.mean() * 252
                
                volatilities = [overall_vol * 0.7, overall_vol * 1.3]
                means = [overall_mean, overall_mean]
            
            # Simple transition matrix estimation
            transition_matrix = self._estimate_transition_matrix(returns_clean, vol_median)
            
            # Current regime probabilities (simplified)
            recent_vol = returns_clean.tail(20).std() * np.sqrt(252)
            if recent_vol > (volatilities[0] + volatilities[1]) / 2:
                current_probs = [0.3, 0.7]  # More likely in high vol regime
            else:
                current_probs = [0.7, 0.3]  # More likely in low vol regime
            
            regime_params = {}
            for i in range(self.n_regimes):
                regime_params[f'regime_{i}'] = {
                    'volatility': volatilities[i],
                    'mean_return': means[i],
                    'persistence': transition_matrix[i][i] if transition_matrix is not None else 0.9
                }
            
            return {
                'success': True,
                'parameters': regime_params,
                'transition_matrix': transition_matrix,
                'current_probabilities': current_probs
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _estimate_transition_matrix(self, returns, vol_threshold):
        """Estimate regime transition matrix"""
        
        try:
            rolling_vol = returns.rolling(window=10).std()
            regimes = (rolling_vol > vol_threshold).astype(int)
            
            # Count transitions
            transition_counts = np.zeros((2, 2))
            
            for i in range(len(regimes) - 1):
                if not np.isnan(regimes.iloc[i]) and not np.isnan(regimes.iloc[i+1]):
                    current = int(regimes.iloc[i])
                    next_regime = int(regimes.iloc[i+1])
                    transition_counts[current][next_regime] += 1
            
            # Convert to probabilities
            transition_matrix = np.zeros((2, 2))
            for i in range(2):
                row_sum = transition_counts[i].sum()
                if row_sum > 0:
                    transition_matrix[i] = transition_counts[i] / row_sum
                else:
                    transition_matrix[i] = [0.5, 0.5]  # Default
            
            return transition_matrix.tolist()
            
        except Exception:
            return [[0.9, 0.1], [0.1, 0.9]]  # Default fallback
    
    def _refine_with_option_data(self, option_data):
        """Refine parameters using market option prices"""
        
        # Simplified refinement - in practice would use more sophisticated calibration
        try:
            # Placeholder for option-based calibration
            return {
                'success': True,
                'parameters': {}  # Would contain refined parameters
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _assess_calibration_quality(self, returns):
        """Assess quality of regime model calibration"""
        
        try:
            # Simple quality metrics
            quality_metrics = {
                'data_length': len(returns),
                'regime_separation': 0.0,
                'likelihood_improvement': 0.0
            }
            
            # Calculate regime separation
            if self.regime_parameters:
                vols = [self.regime_parameters[f'regime_{i}']['volatility'] 
                       for i in range(self.n_regimes)]
                quality_metrics['regime_separation'] = max(vols) / min(vols) - 1
            
            return quality_metrics
            
        except Exception:
            return {'error': 'Quality assessment failed'}
    
    def _black_scholes_price(self, S, K, T, r, sigma, option_type='call'):
        """Standard Black-Scholes pricing"""
        
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0.0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
        
        return max(price, 0.0)
    
    def _calculate_delta(self, S, K, T, r, sigma, option_type='call'):
        """Calculate delta"""
        
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0.0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type.lower() == 'call':
            return stats.norm.cdf(d1)
        else:  # put
            return stats.norm.cdf(d1) - 1
    
    def _calculate_regime_greeks(self, S, K, T, r, option_type, weights):
        """Calculate regime-weighted Greeks"""
        
        try:
            greeks = {
                'delta': 0.0,
                'gamma': 0.0,
                'vega': 0.0,
                'theta': 0.0
            }
            
            for i in range(self.n_regimes):
                regime_vol = self.regime_parameters[f'regime_{i}']['volatility']
                weight = weights[i]
                
                # Calculate Greeks for this regime
                regime_greeks = self._calculate_single_regime_greeks(
                    S, K, T, r, regime_vol, option_type
                )
                
                # Add weighted contribution
                for greek in greeks:
                    greeks[greek] += regime_greeks[greek] * weight
            
            return greeks
            
        except Exception as e:
            return {'error': f'Greeks calculation failed: {str(e)}'}
    
    def _calculate_single_regime_greeks(self, S, K, T, r, sigma, option_type):
        """Calculate Greeks for single regime"""
        
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return {'delta': 0.0, 'gamma': 0.0, 'vega': 0.0, 'theta': 0.0}
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        if option_type.lower() == 'call':
            delta = stats.norm.cdf(d1)
        else:
            delta = stats.norm.cdf(d1) - 1
        
        # Gamma
        gamma = stats.norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Vega (per 1% volatility change)
        vega = S * stats.norm.pdf(d1) * np.sqrt(T) / 100
        
        # Theta (per day)
        if option_type.lower() == 'call':
            theta = (-(S * stats.norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - 
                    r * K * np.exp(-r * T) * stats.norm.cdf(d2)) / 365
        else:
            theta = (-(S * stats.norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) + 
                    r * K * np.exp(-r * T) * stats.norm.cdf(-d2)) / 365
        
        return {
            'delta': delta,
            'gamma': gamma, 
            'vega': vega,
            'theta': theta
        }
    
    def _calculate_regime_hedge_adjustment(self, regime_index, T):
        """Calculate hedging adjustment for specific regime"""
        
        try:
            # Regime-specific adjustments based on volatility and persistence
            regime_params = self.regime_parameters[f'regime_{regime_index}']
            persistence = regime_params.get('persistence', 0.9)
            
            # Higher persistence requires smaller adjustments
            # Shorter time to expiration requires larger adjustments
            time_adjustment = min(1.0, 1.0 / max(T, 0.01))
            persistence_adjustment = 1.0 + (1.0 - persistence) * 0.5
            
            return time_adjustment * persistence_adjustment
            
        except Exception:
            return 1.0  # Default no adjustment
    
    def _calculate_transition_adjustments(self, S, K, T, r, option_type):
        """Calculate adjustments needed for regime transitions"""
        
        try:
            adjustments = {}
            
            if self.transition_matrix is None:
                return adjustments
            
            # Calculate expected transition impacts
            for i in range(self.n_regimes):
                for j in range(self.n_regimes):
                    if i != j:  # Transition from regime i to j
                        transition_prob = self.transition_matrix[i][j]
                        
                        if transition_prob > 0.01:  # Significant probability
                            # Calculate price difference between regimes
                            vol_i = self.regime_parameters[f'regime_{i}']['volatility']
                            vol_j = self.regime_parameters[f'regime_{j}']['volatility']
                            
                            price_i = self._black_scholes_price(S, K, T, r, vol_i, option_type)
                            price_j = self._black_scholes_price(S, K, T, r, vol_j, option_type)
                            
                            price_impact = price_j - price_i
                            
                            adjustments[f'transition_{i}_to_{j}'] = {
                                'probability': transition_prob,
                                'price_impact': price_impact,
                                'hedge_adjustment': price_impact * transition_prob
                            }
            
            return adjustments
            
        except Exception as e:
            return {'error': f'Transition calculation failed: {str(e)}'}
    
    def _get_rebalancing_triggers(self):
        """Define rebalancing triggers for regime-aware hedging"""
        
        return {
            'regime_probability_change': 0.1,  # Rebalance if regime prob changes by 10%
            'volatility_change': 0.05,  # Rebalance if realized vol changes by 5%
            'time_decay': 1,  # Rebalance daily
            'delta_tolerance': 0.05  # Rebalance if delta changes by 5%
        }
    
    def _generate_stress_scenarios(self):
        """Generate stress test scenarios"""
        
        scenarios = {}
        
        # High volatility stress
        scenarios['high_vol_stress'] = [0.1, 0.9]  # 90% probability of high vol regime
        
        # Low volatility stress  
        scenarios['low_vol_stress'] = [0.9, 0.1]   # 90% probability of low vol regime
        
        # Regime uncertainty
        scenarios['regime_uncertainty'] = [0.5, 0.5]  # Maximum uncertainty
        
        return scenarios
    
    def _regime_sensitivity_analysis(self, S, K, T, r, option_type):
        """Perform sensitivity analysis on regime parameters"""
        
        try:
            sensitivity_results = {}
            
            # Base case price
            base_price = self.price_option_regime_dependent(S, K, T, r, option_type)['price']
            
            # Volatility sensitivity
            vol_changes = [-0.05, -0.02, 0.02, 0.05]  # +/- 5%, 2%
            
            for vol_change in vol_changes:
                # Modify regime volatilities
                original_params = self.regime_parameters.copy()
                
                for i in range(self.n_regimes):
                    self.regime_parameters[f'regime_{i}']['volatility'] *= (1 + vol_change)
                
                # Calculate new price
                new_price = self.price_option_regime_dependent(S, K, T, r, option_type)['price']
                
                sensitivity_results[f'vol_change_{vol_change:.0%}'] = {
                    'price': new_price,
                    'price_change': new_price - base_price,
                    'sensitivity': (new_price - base_price) / (base_price * vol_change) if vol_change != 0 else 0
                }
                
                # Restore original parameters
                self.regime_parameters = original_params
            
            return sensitivity_results
            
        except Exception as e:
            return {'error': f'Sensitivity analysis failed: {str(e)}'}

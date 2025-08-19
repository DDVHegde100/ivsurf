"""
Value at Risk (VaR) Analysis Module
Advanced risk metrics including Historical, Parametric, and Monte Carlo VaR
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class VaRAnalyzer:
    """
    Comprehensive Value at Risk analyzer with multiple methodologies
    """
    
    def __init__(self, confidence_levels=[0.95, 0.99]):
        """
        Initialize VaR analyzer
        
        Args:
            confidence_levels: List of confidence levels for VaR calculation
        """
        self.confidence_levels = confidence_levels
        self.returns_data = None
        self.portfolio_value = None
        
    def load_data(self, returns, portfolio_value=1000000):
        """
        Load returns data for VaR analysis
        
        Args:
            returns: pandas Series or numpy array of returns
            portfolio_value: Portfolio value for absolute VaR calculation
        """
        if isinstance(returns, pd.Series):
            self.returns_data = returns.dropna()
        else:
            self.returns_data = pd.Series(returns).dropna()
        
        self.portfolio_value = portfolio_value
        
    def historical_var(self, confidence_level=0.95, window=252):
        """
        Calculate Historical Value at Risk
        
        Args:
            confidence_level: Confidence level (0.95 = 95%)
            window: Rolling window size for calculation
            
        Returns:
            dict: Historical VaR metrics
        """
        if self.returns_data is None:
            raise ValueError("Must load data first using load_data()")
            
        # Use most recent window of data
        recent_returns = self.returns_data.tail(window)
        
        # Calculate percentiles
        alpha = 1 - confidence_level
        var_percentile = np.percentile(recent_returns, alpha * 100)
        
        # Calculate Expected Shortfall (CVaR)
        tail_returns = recent_returns[recent_returns <= var_percentile]
        expected_shortfall = tail_returns.mean() if len(tail_returns) > 0 else var_percentile
        
        # Convert to absolute values
        var_absolute = abs(var_percentile * self.portfolio_value)
        es_absolute = abs(expected_shortfall * self.portfolio_value)
        
        return {
            'method': 'Historical',
            'confidence_level': confidence_level,
            'var_relative': var_percentile,
            'var_absolute': var_absolute,
            'expected_shortfall_relative': expected_shortfall,
            'expected_shortfall_absolute': es_absolute,
            'observations': len(recent_returns),
            'window_days': window
        }
    
    def parametric_var(self, confidence_level=0.95, distribution='normal'):
        """
        Calculate Parametric Value at Risk
        
        Args:
            confidence_level: Confidence level
            distribution: 'normal' or 't' for Student-t distribution
            
        Returns:
            dict: Parametric VaR metrics
        """
        if self.returns_data is None:
            raise ValueError("Must load data first using load_data()")
            
        # Calculate return statistics
        mu = self.returns_data.mean()
        sigma = self.returns_data.std()
        
        alpha = 1 - confidence_level
        
        if distribution == 'normal':
            # Normal distribution VaR
            z_score = stats.norm.ppf(alpha)
            var_relative = mu + z_score * sigma
            
        elif distribution == 't':
            # Student-t distribution for fat tails
            # Estimate degrees of freedom
            try:
                # Fit t-distribution
                df, loc, scale = stats.t.fit(self.returns_data)
                t_score = stats.t.ppf(alpha, df)
                var_relative = loc + t_score * scale
            except:
                # Fallback to normal if fitting fails
                z_score = stats.norm.ppf(alpha)
                var_relative = mu + z_score * sigma
        else:
            raise ValueError("Distribution must be 'normal' or 't'")
            
        # Calculate Expected Shortfall analytically
        if distribution == 'normal':
            # ES for normal distribution
            expected_shortfall = mu - sigma * stats.norm.pdf(stats.norm.ppf(alpha)) / alpha
        else:
            # ES for t-distribution (approximate)
            expected_shortfall = var_relative * 1.2  # Conservative approximation
            
        # Convert to absolute values
        var_absolute = abs(var_relative * self.portfolio_value)
        es_absolute = abs(expected_shortfall * self.portfolio_value)
        
        return {
            'method': f'Parametric ({distribution})',
            'confidence_level': confidence_level,
            'var_relative': var_relative,
            'var_absolute': var_absolute,
            'expected_shortfall_relative': expected_shortfall,
            'expected_shortfall_absolute': es_absolute,
            'mean_return': mu,
            'volatility': sigma,
            'distribution': distribution
        }
    
    def monte_carlo_var(self, confidence_level=0.95, simulations=10000, time_horizon=1):
        """
        Calculate Monte Carlo Value at Risk
        
        Args:
            confidence_level: Confidence level
            simulations: Number of Monte Carlo simulations
            time_horizon: Time horizon in days
            
        Returns:
            dict: Monte Carlo VaR metrics
        """
        if self.returns_data is None:
            raise ValueError("Must load data first using load_data()")
            
        # Calculate parameters
        mu = self.returns_data.mean()
        sigma = self.returns_data.std()
        
        # Generate random scenarios
        np.random.seed(42)  # For reproducibility
        
        # Simulate returns using geometric Brownian motion
        dt = time_horizon / 252  # Convert days to years
        random_shocks = np.random.normal(0, 1, simulations)
        
        # Calculate simulated returns
        simulated_returns = mu * dt + sigma * np.sqrt(dt) * random_shocks
        
        # Calculate VaR and ES
        alpha = 1 - confidence_level
        var_percentile = np.percentile(simulated_returns, alpha * 100)
        
        tail_returns = simulated_returns[simulated_returns <= var_percentile]
        expected_shortfall = tail_returns.mean() if len(tail_returns) > 0 else var_percentile
        
        # Convert to absolute values
        var_absolute = abs(var_percentile * self.portfolio_value)
        es_absolute = abs(expected_shortfall * self.portfolio_value)
        
        return {
            'method': 'Monte Carlo',
            'confidence_level': confidence_level,
            'var_relative': var_percentile,
            'var_absolute': var_absolute,
            'expected_shortfall_relative': expected_shortfall,
            'expected_shortfall_absolute': es_absolute,
            'simulations': simulations,
            'time_horizon_days': time_horizon,
            'simulated_returns': simulated_returns
        }
    
    def kupiec_backtest(self, var_estimates, actual_returns, confidence_level=0.95):
        """
        Perform Kupiec backtest for VaR model validation
        
        Args:
            var_estimates: Series of VaR estimates
            actual_returns: Series of actual returns
            confidence_level: VaR confidence level
            
        Returns:
            dict: Backtest results
        """
        # Count violations (actual losses > VaR estimates)
        violations = (actual_returns < var_estimates).sum()
        total_observations = len(actual_returns)
        
        # Expected violation rate
        expected_violations = (1 - confidence_level) * total_observations
        actual_violation_rate = violations / total_observations
        expected_violation_rate = 1 - confidence_level
        
        # Kupiec test statistic
        if violations == 0:
            lr_statistic = 0
        else:
            lr_statistic = -2 * np.log(
                ((expected_violation_rate ** violations) * 
                 ((1 - expected_violation_rate) ** (total_observations - violations))) /
                ((actual_violation_rate ** violations) * 
                 ((1 - actual_violation_rate) ** (total_observations - violations)))
            )
        
        # Critical value (chi-square with 1 df at 95% confidence)
        critical_value = stats.chi2.ppf(0.95, 1)
        p_value = 1 - stats.chi2.cdf(lr_statistic, 1)
        
        return {
            'violations': violations,
            'total_observations': total_observations,
            'violation_rate': actual_violation_rate,
            'expected_violation_rate': expected_violation_rate,
            'lr_statistic': lr_statistic,
            'critical_value': critical_value,
            'p_value': p_value,
            'model_adequate': lr_statistic < critical_value,
            'confidence_level': confidence_level
        }
    
    def comprehensive_var_analysis(self, confidence_levels=None):
        """
        Perform comprehensive VaR analysis using all methods
        
        Returns:
            dict: Complete VaR analysis results
        """
        if confidence_levels is None:
            confidence_levels = self.confidence_levels
            
        results = {}
        
        for cl in confidence_levels:
            results[f'VaR_{cl*100:.0f}'] = {
                'historical': self.historical_var(cl),
                'parametric_normal': self.parametric_var(cl, 'normal'),
                'parametric_t': self.parametric_var(cl, 't'),
                'monte_carlo': self.monte_carlo_var(cl)
            }
        
        return results
    
    def risk_metrics_summary(self):
        """
        Calculate comprehensive risk metrics summary
        
        Returns:
            dict: Risk metrics summary
        """
        if self.returns_data is None:
            raise ValueError("Must load data first using load_data()")
            
        returns = self.returns_data
        
        # Basic statistics
        mean_return = returns.mean()
        volatility = returns.std()
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        # Risk metrics
        max_drawdown = self._calculate_max_drawdown(returns)
        sharpe_ratio = mean_return / volatility * np.sqrt(252) if volatility > 0 else 0
        
        # Downside metrics
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = mean_return / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
        
        return {
            'mean_return_daily': mean_return,
            'mean_return_annual': mean_return * 252,
            'volatility_daily': volatility,
            'volatility_annual': volatility * np.sqrt(252),
            'skewness': skewness,
            'kurtosis': kurtosis,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'downside_deviation': downside_deviation,
            'observations': len(returns)
        }
    
    def _calculate_max_drawdown(self, returns):
        """Calculate maximum drawdown from returns series"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

"""
Stress Testing Module
Scenario analysis and stress testing for risk management
"""

import numpy as np
import pandas as pd
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class StressTester:
    """
    Advanced stress testing and scenario analysis
    """
    
    def __init__(self):
        """Initialize stress tester"""
        self.scenarios = {}
        self.portfolio_data = None
        
    def load_portfolio_data(self, returns, weights=None):
        """
        Load portfolio data for stress testing
        
        Args:
            returns: DataFrame of asset returns or Series for single asset
            weights: Portfolio weights (None for equal weight or single asset)
        """
        if isinstance(returns, pd.Series):
            self.portfolio_data = returns
        else:
            if weights is None:
                weights = np.ones(len(returns.columns)) / len(returns.columns)
            
            # Calculate portfolio returns
            self.portfolio_data = (returns * weights).sum(axis=1)
    
    def define_stress_scenarios(self):
        """
        Define standard stress test scenarios
        
        Returns:
            dict: Predefined stress scenarios
        """
        scenarios = {
            'market_crash': {
                'description': '2008-style market crash scenario',
                'equity_shock': -0.30,  # 30% equity drop
                'volatility_shock': 2.0,  # Volatility doubles
                'correlation_shock': 0.8,  # High correlation
                'duration_days': 5
            },
            'black_monday': {
                'description': '1987 Black Monday scenario',
                'equity_shock': -0.22,  # 22% single day drop
                'volatility_shock': 3.0,  # Triple volatility
                'correlation_shock': 0.9,  # Very high correlation
                'duration_days': 1
            },
            'covid_crash': {
                'description': 'COVID-19 market crash scenario',
                'equity_shock': -0.35,  # 35% drop over period
                'volatility_shock': 2.5,  # 2.5x volatility
                'correlation_shock': 0.85,  # High correlation
                'duration_days': 20
            },
            'interest_rate_shock': {
                'description': 'Sudden interest rate spike',
                'equity_shock': -0.15,  # 15% equity drop
                'volatility_shock': 1.5,  # 50% volatility increase
                'correlation_shock': 0.6,  # Moderate correlation
                'duration_days': 10
            },
            'flash_crash': {
                'description': 'Flash crash scenario',
                'equity_shock': -0.10,  # 10% instant drop
                'volatility_shock': 5.0,  # 5x volatility spike
                'correlation_shock': 0.95,  # Near perfect correlation
                'duration_days': 1
            }
        }
        
        self.scenarios = scenarios
        return scenarios
    
    def monte_carlo_stress_test(self, scenario_name, simulations=10000, portfolio_value=1000000):
        """
        Perform Monte Carlo stress testing for specific scenario
        
        Args:
            scenario_name: Name of predefined scenario
            simulations: Number of Monte Carlo simulations
            portfolio_value: Portfolio value for absolute P&L calculation
            
        Returns:
            dict: Stress test results
        """
        if self.portfolio_data is None:
            raise ValueError("Must load portfolio data first")
            
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not defined")
            
        scenario = self.scenarios[scenario_name]
        
        # Portfolio statistics
        mu = self.portfolio_data.mean()
        sigma = self.portfolio_data.std()
        
        # Scenario parameters
        equity_shock = scenario['equity_shock']
        vol_multiplier = scenario['volatility_shock']
        duration = scenario['duration_days']
        
        # Monte Carlo simulation
        np.random.seed(42)
        
        stressed_returns = []
        for _ in range(simulations):
            # Generate stressed return path
            daily_returns = []
            
            for day in range(duration):
                # Base random shock
                random_shock = np.random.normal(0, 1)
                
                # Apply stress scenario
                stressed_vol = sigma * vol_multiplier
                
                # Distribute total shock over duration
                daily_shock = equity_shock / duration
                
                # Calculate stressed return
                stressed_return = mu + daily_shock + stressed_vol * random_shock
                daily_returns.append(stressed_return)
            
            # Calculate cumulative return
            cumulative_return = np.prod([1 + r for r in daily_returns]) - 1
            stressed_returns.append(cumulative_return)
        
        stressed_returns = np.array(stressed_returns)
        
        # Calculate stress test metrics
        mean_loss = np.mean(stressed_returns)
        worst_case = np.min(stressed_returns)
        percentile_5 = np.percentile(stressed_returns, 5)
        percentile_1 = np.percentile(stressed_returns, 1)
        
        # Convert to absolute values
        mean_loss_abs = mean_loss * portfolio_value
        worst_case_abs = worst_case * portfolio_value
        percentile_5_abs = percentile_5 * portfolio_value
        percentile_1_abs = percentile_1 * portfolio_value
        
        return {
            'scenario': scenario_name,
            'description': scenario['description'],
            'simulations': simulations,
            'duration_days': duration,
            'results': {
                'mean_return': mean_loss,
                'worst_case_return': worst_case,
                'percentile_5': percentile_5,
                'percentile_1': percentile_1,
                'mean_pnl': mean_loss_abs,
                'worst_case_pnl': worst_case_abs,
                'percentile_5_pnl': percentile_5_abs,
                'percentile_1_pnl': percentile_1_abs
            },
            'scenario_parameters': scenario,
            'all_returns': stressed_returns
        }
    
    def historical_scenario_analysis(self, historical_periods=None):
        """
        Analyze portfolio performance during historical stress periods
        
        Args:
            historical_periods: Dict of {name: (start_date, end_date)} for analysis
            
        Returns:
            dict: Historical scenario analysis results
        """
        if self.portfolio_data is None:
            raise ValueError("Must load portfolio data first")
            
        if historical_periods is None:
            # Default historical stress periods
            historical_periods = {
                'dot_com_crash': ('2000-03-01', '2002-10-01'),
                'financial_crisis': ('2007-10-01', '2009-03-01'),
                'covid_crash': ('2020-02-20', '2020-04-01'),
                'recent_volatility': ('2022-01-01', '2022-06-01')
            }
        
        results = {}
        
        for period_name, (start_date, end_date) in historical_periods.items():
            try:
                # Filter data for the period
                if isinstance(self.portfolio_data.index, pd.DatetimeIndex):
                    period_data = self.portfolio_data.loc[start_date:end_date]
                else:
                    # If no date index, skip historical analysis
                    continue
                    
                if len(period_data) == 0:
                    continue
                
                # Calculate period statistics
                total_return = (1 + period_data).prod() - 1
                volatility = period_data.std() * np.sqrt(252)
                max_drawdown = self._calculate_max_drawdown(period_data)
                worst_day = period_data.min()
                best_day = period_data.max()
                negative_days = (period_data < 0).sum()
                total_days = len(period_data)
                
                results[period_name] = {
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_return': total_return,
                    'annualized_volatility': volatility,
                    'max_drawdown': max_drawdown,
                    'worst_day': worst_day,
                    'best_day': best_day,
                    'negative_days': negative_days,
                    'total_days': total_days,
                    'negative_day_ratio': negative_days / total_days
                }
                
            except Exception as e:
                results[period_name] = {'error': str(e)}
        
        return results
    
    def sensitivity_analysis(self, factor_shocks=None):
        """
        Perform sensitivity analysis to various market factors
        
        Args:
            factor_shocks: Dict of factor shock scenarios
            
        Returns:
            dict: Sensitivity analysis results
        """
        if factor_shocks is None:
            factor_shocks = {
                'volatility': [-0.5, -0.25, 0, 0.25, 0.5, 1.0, 2.0],
                'correlation': [0.1, 0.3, 0.5, 0.7, 0.9],
                'market_level': [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]
            }
        
        base_return = self.portfolio_data.mean()
        base_vol = self.portfolio_data.std()
        
        sensitivity_results = {}
        
        for factor, shock_levels in factor_shocks.items():
            factor_results = []
            
            for shock in shock_levels:
                if factor == 'volatility':
                    # Volatility shock
                    new_vol = base_vol * (1 + shock)
                    simulated_returns = np.random.normal(base_return, new_vol, 1000)
                    
                elif factor == 'market_level':
                    # Market level shock
                    simulated_returns = np.random.normal(base_return + shock, base_vol, 1000)
                    
                elif factor == 'correlation':
                    # Correlation shock (simplified)
                    correlation_factor = shock
                    adjusted_vol = base_vol * np.sqrt(correlation_factor)
                    simulated_returns = np.random.normal(base_return, adjusted_vol, 1000)
                
                # Calculate metrics for this shock level
                mean_return = np.mean(simulated_returns)
                var_95 = np.percentile(simulated_returns, 5)
                var_99 = np.percentile(simulated_returns, 1)
                
                factor_results.append({
                    'shock_level': shock,
                    'mean_return': mean_return,
                    'var_95': var_95,
                    'var_99': var_99
                })
            
            sensitivity_results[factor] = factor_results
        
        return sensitivity_results
    
    def comprehensive_stress_test(self, portfolio_value=1000000):
        """
        Run comprehensive stress testing suite
        
        Returns:
            dict: Complete stress test results
        """
        # Define scenarios
        self.define_stress_scenarios()
        
        results = {
            'portfolio_value': portfolio_value,
            'monte_carlo_scenarios': {},
            'historical_analysis': {},
            'sensitivity_analysis': {}
        }
        
        # Run Monte Carlo stress tests for all scenarios
        for scenario_name in self.scenarios.keys():
            try:
                results['monte_carlo_scenarios'][scenario_name] = self.monte_carlo_stress_test(
                    scenario_name, simulations=5000, portfolio_value=portfolio_value
                )
            except Exception as e:
                results['monte_carlo_scenarios'][scenario_name] = {'error': str(e)}
        
        # Run historical analysis
        try:
            results['historical_analysis'] = self.historical_scenario_analysis()
        except Exception as e:
            results['historical_analysis'] = {'error': str(e)}
        
        # Run sensitivity analysis
        try:
            results['sensitivity_analysis'] = self.sensitivity_analysis()
        except Exception as e:
            results['sensitivity_analysis'] = {'error': str(e)}
        
        return results
    
    def _calculate_max_drawdown(self, returns):
        """Calculate maximum drawdown from returns series"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def risk_attribution(self, factor_loadings=None):
        """
        Perform risk attribution analysis
        
        Args:
            factor_loadings: Dict of factor loadings for attribution
            
        Returns:
            dict: Risk attribution results
        """
        if factor_loadings is None:
            # Default factor loadings (example)
            factor_loadings = {
                'market_beta': 1.0,
                'size_factor': 0.0,
                'value_factor': 0.0,
                'momentum_factor': 0.0
            }
        
        portfolio_var = self.portfolio_data.var()
        
        # Simplified risk attribution
        attribution = {}
        total_attribution = 0
        
        for factor, loading in factor_loadings.items():
            # Simplified calculation - in practice would use factor covariance matrix
            factor_contribution = (loading ** 2) * portfolio_var * (1 / len(factor_loadings))
            attribution[factor] = {
                'loading': loading,
                'risk_contribution': factor_contribution,
                'risk_contribution_pct': factor_contribution / portfolio_var * 100
            }
            total_attribution += factor_contribution
        
        # Residual risk
        residual_risk = portfolio_var - total_attribution
        attribution['residual'] = {
            'loading': 1.0,
            'risk_contribution': residual_risk,
            'risk_contribution_pct': residual_risk / portfolio_var * 100
        }
        
        return {
            'total_portfolio_variance': portfolio_var,
            'total_portfolio_volatility': np.sqrt(portfolio_var),
            'factor_attribution': attribution
        }

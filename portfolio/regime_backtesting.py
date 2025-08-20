"""
Advanced Backtesting & Portfolio Integration
==========================================

Comprehensive backtesting framework for regime-aware strategies:
- Multi-regime portfolio optimization
- Risk-adjusted performance attribution
- Dynamic hedging backtests
- Stress testing integration
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

class RegimeAwareBacktester:
    """
    Advanced backtesting engine for regime-aware strategies
    """
    
    def __init__(self):
        self.backtest_results = {}
        self.portfolio_history = None
        self.performance_metrics = {}
        
    def backtest_regime_strategy(self, price_data, regime_model, strategy_config, 
                                start_date=None, end_date=None):
        """
        Backtest regime-aware trading strategy
        
        Args:
            price_data: Dictionary of ticker -> price series
            regime_model: Fitted regime switching model
            strategy_config: Strategy configuration parameters
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            dict: Comprehensive backtest results
        """
        
        try:
            # Align and prepare data
            aligned_data = self._align_price_data(price_data, start_date, end_date)
            
            if aligned_data.empty or len(aligned_data) < 50:
                return {'error': 'Insufficient data for backtesting'}
            
            # Calculate returns
            returns_data = aligned_data.pct_change().dropna()
            
            # Initialize portfolio
            portfolio_value = strategy_config.get('initial_capital', 100000)
            portfolio_history = []
            position_history = []
            regime_history = []
            
            # Strategy parameters
            rebalance_frequency = strategy_config.get('rebalance_frequency', 'weekly')
            risk_target = strategy_config.get('risk_target', 0.15)  # 15% annual volatility
            regime_confidence_threshold = strategy_config.get('regime_confidence', 0.7)
            
            # Backtesting loop
            for i in range(len(returns_data)):
                current_date = returns_data.index[i]
                current_returns = returns_data.iloc[i]
                
                # Detect current regime probabilities
                lookback_window = min(i + 1, 252)  # 1 year lookback
                historical_returns = returns_data.iloc[max(0, i-lookback_window):i+1]
                
                regime_probs = self._estimate_regime_probabilities(
                    historical_returns, regime_model
                )
                
                # Make portfolio allocation decision
                if self._should_rebalance(i, rebalance_frequency, current_date):
                    portfolio_weights = self._calculate_regime_weights(
                        regime_probs, strategy_config, historical_returns
                    )
                else:
                    # Use previous weights if not rebalancing
                    portfolio_weights = position_history[-1]['weights'] if position_history else {}
                
                # Calculate portfolio return
                portfolio_return = 0
                for ticker, weight in portfolio_weights.items():
                    if ticker in current_returns.index:
                        portfolio_return += weight * current_returns[ticker]
                
                # Update portfolio value
                portfolio_value *= (1 + portfolio_return)
                
                # Record history
                portfolio_history.append({
                    'date': current_date,
                    'portfolio_value': portfolio_value,
                    'portfolio_return': portfolio_return,
                    'benchmark_return': current_returns.mean() if not current_returns.empty else 0
                })
                
                position_history.append({
                    'date': current_date,
                    'weights': portfolio_weights.copy()
                })
                
                regime_history.append({
                    'date': current_date,
                    'regime_probabilities': regime_probs.copy()
                })
            
            # Calculate performance metrics
            portfolio_df = pd.DataFrame(portfolio_history)
            performance_metrics = self._calculate_performance_metrics(
                portfolio_df, aligned_data, strategy_config
            )
            
            # Regime analysis
            regime_analysis = self._analyze_regime_performance(
                portfolio_df, regime_history
            )
            
            # Risk attribution
            risk_attribution = self._calculate_risk_attribution(
                portfolio_df, position_history, returns_data
            )
            
            self.backtest_results = {
                'portfolio_history': portfolio_df,
                'position_history': position_history,
                'regime_history': regime_history,
                'performance_metrics': performance_metrics,
                'regime_analysis': regime_analysis,
                'risk_attribution': risk_attribution,
                'success': True
            }
            
            return self.backtest_results
            
        except Exception as e:
            return {'error': f'Backtesting failed: {str(e)}'}
    
    def stress_test_portfolio(self, portfolio_weights, price_data, stress_scenarios):
        """
        Perform stress testing on portfolio
        
        Args:
            portfolio_weights: Current portfolio weights
            price_data: Historical price data
            stress_scenarios: Dictionary of stress scenarios
            
        Returns:
            dict: Stress test results
        """
        
        try:
            stress_results = {}
            
            # Calculate base portfolio returns
            returns_data = self._align_price_data(price_data).pct_change().dropna()
            
            for scenario_name, scenario_params in stress_scenarios.items():
                scenario_results = self._simulate_stress_scenario(
                    portfolio_weights, returns_data, scenario_params
                )
                stress_results[scenario_name] = scenario_results
            
            # Calculate maximum drawdown scenarios
            stress_results['max_drawdown_analysis'] = self._analyze_max_drawdown_scenarios(
                portfolio_weights, returns_data
            )
            
            # Regime-specific stress tests
            stress_results['regime_stress_tests'] = self._regime_specific_stress_tests(
                portfolio_weights, returns_data
            )
            
            return {
                'stress_test_results': stress_results,
                'overall_risk_assessment': self._assess_overall_risk(stress_results),
                'recommendations': self._generate_risk_recommendations(stress_results)
            }
            
        except Exception as e:
            return {'error': f'Stress testing failed: {str(e)}'}
    
    def optimize_regime_portfolio(self, expected_returns, covariance_matrix, 
                                 regime_probabilities, constraints=None):
        """
        Optimize portfolio considering regime probabilities
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix of returns
            regime_probabilities: Current regime probabilities
            constraints: Portfolio constraints
            
        Returns:
            dict: Optimization results
        """
        
        try:
            n_assets = len(expected_returns)
            
            # Default constraints
            if constraints is None:
                constraints = {
                    'sum_to_one': True,
                    'long_only': True,
                    'max_weight': 0.4
                }
            
            # Regime-adjusted expected returns and covariance
            regime_adjusted_returns = self._adjust_returns_for_regime(
                expected_returns, regime_probabilities
            )
            
            regime_adjusted_cov = self._adjust_covariance_for_regime(
                covariance_matrix, regime_probabilities
            )
            
            # Optimization objective (maximize Sharpe ratio)
            def objective(weights):
                portfolio_return = np.dot(weights, regime_adjusted_returns)
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(regime_adjusted_cov, weights)))
                
                # Add penalty for extreme concentrations
                concentration_penalty = 10 * np.sum(weights ** 4)  # Penalize concentration
                
                return -(portfolio_return / (portfolio_vol + 1e-8)) + concentration_penalty
            
            # Constraints
            constraint_list = []
            
            # Weights sum to 1
            if constraints.get('sum_to_one', True):
                constraint_list.append({
                    'type': 'eq',
                    'fun': lambda x: np.sum(x) - 1.0
                })
            
            # Long only
            if constraints.get('long_only', True):
                bounds = [(0, constraints.get('max_weight', 1.0)) for _ in range(n_assets)]
            else:
                bounds = [(-1, 1) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            initial_weights = np.ones(n_assets) / n_assets
            
            # Optimize
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraint_list,
                options={'maxiter': 1000}
            )
            
            if result.success:
                optimal_weights = result.x
                
                # Calculate portfolio metrics
                portfolio_return = np.dot(optimal_weights, regime_adjusted_returns)
                portfolio_vol = np.sqrt(
                    np.dot(optimal_weights.T, np.dot(regime_adjusted_cov, optimal_weights))
                )
                sharpe_ratio = portfolio_return / portfolio_vol
                
                return {
                    'success': True,
                    'optimal_weights': optimal_weights.tolist(),
                    'expected_return': float(portfolio_return),
                    'expected_volatility': float(portfolio_vol),
                    'sharpe_ratio': float(sharpe_ratio),
                    'regime_probabilities_used': regime_probabilities
                }
            else:
                return {
                    'success': False,
                    'error': 'Optimization failed to converge'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Portfolio optimization failed: {str(e)}'}
    
    def _align_price_data(self, price_data, start_date=None, end_date=None):
        """Align price data across assets"""
        
        try:
            df = pd.DataFrame(price_data)
            
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            return df.dropna()
            
        except Exception:
            return pd.DataFrame()
    
    def _estimate_regime_probabilities(self, returns_data, regime_model):
        """Estimate current regime probabilities"""
        
        # Simplified regime probability estimation
        try:
            if len(returns_data) == 0:
                return [0.5, 0.5]  # Default equal probabilities
            
            # Calculate recent volatility
            recent_vol = returns_data.iloc[-min(20, len(returns_data)):].std()
            overall_vol = returns_data.std()
            
            # Simple heuristic: higher recent volatility -> higher probability of high-vol regime
            if recent_vol > overall_vol * 1.2:
                return [0.3, 0.7]  # High volatility regime more likely
            elif recent_vol < overall_vol * 0.8:
                return [0.7, 0.3]  # Low volatility regime more likely
            else:
                return [0.5, 0.5]  # Neutral
                
        except Exception:
            return [0.5, 0.5]
    
    def _should_rebalance(self, current_index, frequency, current_date):
        """Determine if portfolio should be rebalanced"""
        
        if frequency == 'daily':
            return True
        elif frequency == 'weekly':
            return current_date.weekday() == 0  # Monday
        elif frequency == 'monthly':
            return current_date.day == 1
        else:
            return current_index % 5 == 0  # Default: every 5 days
    
    def _calculate_regime_weights(self, regime_probs, strategy_config, historical_returns):
        """Calculate portfolio weights based on regime probabilities"""
        
        try:
            assets = historical_returns.columns
            n_assets = len(assets)
            
            if n_assets == 0:
                return {}
            
            # Base equal weights
            base_weights = np.ones(n_assets) / n_assets
            
            # Regime-based adjustments
            high_vol_regime_prob = regime_probs[1] if len(regime_probs) > 1 else 0.5
            
            # In high volatility regimes, reduce risk exposure
            risk_adjustment = 1.0 - (high_vol_regime_prob * 0.3)  # Reduce by up to 30%
            
            # Apply momentum/trend following based on recent performance
            if len(historical_returns) > 10:
                recent_returns = historical_returns.iloc[-10:].mean()
                momentum_scores = (recent_returns - recent_returns.mean()) / recent_returns.std()
                momentum_scores = momentum_scores.fillna(0)
                
                # Adjust weights based on momentum (with regime consideration)
                momentum_adjustment = 1 + momentum_scores * 0.2 * (1 - high_vol_regime_prob)
                momentum_adjustment = np.clip(momentum_adjustment, 0.5, 1.5)
                
                adjusted_weights = base_weights * momentum_adjustment * risk_adjustment
                adjusted_weights = adjusted_weights / adjusted_weights.sum()  # Normalize
            else:
                adjusted_weights = base_weights * risk_adjustment
            
            # Convert to dictionary
            weight_dict = {}
            for i, asset in enumerate(assets):
                weight_dict[asset] = float(adjusted_weights[i])
            
            return weight_dict
            
        except Exception:
            # Fallback to equal weights
            assets = historical_returns.columns
            return {asset: 1.0 / len(assets) for asset in assets}
    
    def _calculate_performance_metrics(self, portfolio_df, price_data, strategy_config):
        """Calculate comprehensive performance metrics"""
        
        try:
            portfolio_returns = portfolio_df['portfolio_return']
            benchmark_returns = portfolio_df['benchmark_return']
            
            # Basic metrics
            total_return = (portfolio_df['portfolio_value'].iloc[-1] / 
                          portfolio_df['portfolio_value'].iloc[0]) - 1
            
            annual_return = (1 + total_return) ** (252 / len(portfolio_df)) - 1
            annual_volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
            
            # Maximum drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdowns.min()
            
            # Calmar ratio
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
            
            # Information ratio vs benchmark
            excess_returns = portfolio_returns - benchmark_returns
            tracking_error = excess_returns.std() * np.sqrt(252)
            information_ratio = (excess_returns.mean() * 252) / tracking_error if tracking_error > 0 else 0
            
            # Win rate
            win_rate = (portfolio_returns > 0).mean()
            
            # Risk-adjusted metrics
            sortino_ratio = self._calculate_sortino_ratio(portfolio_returns)
            var_95 = np.percentile(portfolio_returns, 5)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            
            return {
                'total_return': float(total_return),
                'annual_return': float(annual_return),
                'annual_volatility': float(annual_volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'calmar_ratio': float(calmar_ratio),
                'information_ratio': float(information_ratio),
                'win_rate': float(win_rate),
                'sortino_ratio': float(sortino_ratio),
                'var_95': float(var_95),
                'cvar_95': float(cvar_95),
                'tracking_error': float(tracking_error)
            }
            
        except Exception as e:
            return {'error': f'Performance calculation failed: {str(e)}'}
    
    def _calculate_sortino_ratio(self, returns):
        """Calculate Sortino ratio"""
        
        try:
            downside_returns = returns[returns < 0]
            if len(downside_returns) == 0:
                return 0
            
            downside_deviation = downside_returns.std() * np.sqrt(252)
            annual_return = returns.mean() * 252
            
            return annual_return / downside_deviation if downside_deviation > 0 else 0
            
        except Exception:
            return 0
    
    def _analyze_regime_performance(self, portfolio_df, regime_history):
        """Analyze performance by regime"""
        
        try:
            regime_analysis = {}
            
            for i, regime_data in enumerate(regime_history):
                regime_probs = regime_data['regime_probabilities']
                
                # Classify dominant regime
                if len(regime_probs) >= 2:
                    dominant_regime = 0 if regime_probs[0] > regime_probs[1] else 1
                else:
                    dominant_regime = 0
                
                # Get corresponding portfolio return
                if i < len(portfolio_df):
                    portfolio_return = portfolio_df.iloc[i]['portfolio_return']
                    
                    regime_key = f'regime_{dominant_regime}'
                    if regime_key not in regime_analysis:
                        regime_analysis[regime_key] = {
                            'returns': [],
                            'count': 0
                        }
                    
                    regime_analysis[regime_key]['returns'].append(portfolio_return)
                    regime_analysis[regime_key]['count'] += 1
            
            # Calculate regime-specific metrics
            for regime_key, data in regime_analysis.items():
                returns = np.array(data['returns'])
                
                if len(returns) > 0:
                    regime_analysis[regime_key].update({
                        'avg_return': float(returns.mean()),
                        'volatility': float(returns.std()),
                        'sharpe': float(returns.mean() / returns.std()) if returns.std() > 0 else 0,
                        'frequency': float(len(returns) / len(portfolio_df))
                    })
            
            return regime_analysis
            
        except Exception as e:
            return {'error': f'Regime analysis failed: {str(e)}'}
    
    def _calculate_risk_attribution(self, portfolio_df, position_history, returns_data):
        """Calculate risk attribution analysis"""
        
        try:
            risk_attribution = {
                'asset_contributions': {},
                'concentration_risk': {},
                'regime_risk': {}
            }
            
            # Asset contribution to portfolio volatility
            if position_history and not returns_data.empty:
                # Get average weights over the period
                avg_weights = {}
                for position in position_history:
                    for asset, weight in position['weights'].items():
                        if asset not in avg_weights:
                            avg_weights[asset] = []
                        avg_weights[asset].append(weight)
                
                for asset, weights in avg_weights.items():
                    avg_weight = np.mean(weights)
                    
                    if asset in returns_data.columns:
                        asset_vol = returns_data[asset].std()
                        asset_contribution = avg_weight * asset_vol
                        
                        risk_attribution['asset_contributions'][asset] = {
                            'average_weight': float(avg_weight),
                            'volatility_contribution': float(asset_contribution),
                            'individual_volatility': float(asset_vol)
                        }
                
                # Concentration risk metrics
                max_weights = []
                for position in position_history:
                    if position['weights']:
                        max_weight = max(position['weights'].values())
                        max_weights.append(max_weight)
                
                if max_weights:
                    risk_attribution['concentration_risk'] = {
                        'avg_max_weight': float(np.mean(max_weights)),
                        'max_concentration': float(np.max(max_weights)),
                        'concentration_volatility': float(np.std(max_weights))
                    }
            
            return risk_attribution
            
        except Exception as e:
            return {'error': f'Risk attribution failed: {str(e)}'}
    
    def _simulate_stress_scenario(self, portfolio_weights, returns_data, scenario_params):
        """Simulate stress scenario"""
        
        try:
            scenario_type = scenario_params.get('type', 'shock')
            magnitude = scenario_params.get('magnitude', 0.1)
            
            if scenario_type == 'market_crash':
                # Simulate market crash (all assets down)
                stress_returns = {}
                for asset in portfolio_weights.keys():
                    if asset in returns_data.columns:
                        stress_returns[asset] = -magnitude  # Negative return
                
            elif scenario_type == 'volatility_spike':
                # Simulate volatility spike
                stress_returns = {}
                for asset in portfolio_weights.keys():
                    if asset in returns_data.columns:
                        # Random shock with higher volatility
                        normal_vol = returns_data[asset].std()
                        stress_vol = normal_vol * (1 + magnitude)
                        stress_returns[asset] = np.random.normal(0, stress_vol)
            
            else:  # Default shock
                stress_returns = {asset: -magnitude/2 for asset in portfolio_weights.keys()}
            
            # Calculate portfolio impact
            portfolio_impact = sum(
                portfolio_weights.get(asset, 0) * stress_returns.get(asset, 0)
                for asset in set(portfolio_weights.keys()) | set(stress_returns.keys())
            )
            
            return {
                'scenario_type': scenario_type,
                'portfolio_impact': float(portfolio_impact),
                'individual_impacts': stress_returns
            }
            
        except Exception as e:
            return {'error': f'Stress scenario simulation failed: {str(e)}'}
    
    def _analyze_max_drawdown_scenarios(self, portfolio_weights, returns_data):
        """Analyze maximum drawdown scenarios"""
        
        try:
            # Historical simulation approach
            scenarios = []
            
            for start_idx in range(len(returns_data) - 21):  # 21-day scenarios
                scenario_returns = returns_data.iloc[start_idx:start_idx + 21]
                
                # Calculate portfolio returns for this scenario
                portfolio_scenario_returns = []
                for _, day_returns in scenario_returns.iterrows():
                    portfolio_return = sum(
                        portfolio_weights.get(asset, 0) * day_returns.get(asset, 0)
                        for asset in portfolio_weights.keys()
                    )
                    portfolio_scenario_returns.append(portfolio_return)
                
                # Calculate drawdown for this scenario
                cumulative = (np.array(portfolio_scenario_returns) + 1).cumprod()
                rolling_max = np.maximum.accumulate(cumulative)
                drawdowns = (cumulative - rolling_max) / rolling_max
                max_dd = np.min(drawdowns)
                
                scenarios.append({
                    'start_date': scenario_returns.index[0],
                    'max_drawdown': float(max_dd),
                    'duration': len(scenario_returns)
                })
            
            # Find worst scenarios
            scenarios.sort(key=lambda x: x['max_drawdown'])
            worst_scenarios = scenarios[:5]  # Top 5 worst
            
            return {
                'worst_scenarios': worst_scenarios,
                'avg_max_drawdown': float(np.mean([s['max_drawdown'] for s in scenarios])),
                'percentile_95_drawdown': float(np.percentile([s['max_drawdown'] for s in scenarios], 5))
            }
            
        except Exception as e:
            return {'error': f'Max drawdown analysis failed: {str(e)}'}
    
    def _regime_specific_stress_tests(self, portfolio_weights, returns_data):
        """Perform regime-specific stress tests"""
        
        try:
            # Split data into high and low volatility periods
            rolling_vol = returns_data.rolling(window=20).std().mean(axis=1)
            vol_threshold = rolling_vol.median()
            
            high_vol_periods = returns_data[rolling_vol > vol_threshold]
            low_vol_periods = returns_data[rolling_vol <= vol_threshold]
            
            results = {}
            
            for regime_name, regime_data in [('high_volatility', high_vol_periods), 
                                           ('low_volatility', low_vol_periods)]:
                if not regime_data.empty:
                    # Calculate portfolio performance in this regime
                    regime_portfolio_returns = []
                    
                    for _, day_returns in regime_data.iterrows():
                        portfolio_return = sum(
                            portfolio_weights.get(asset, 0) * day_returns.get(asset, 0)
                            for asset in portfolio_weights.keys()
                        )
                        regime_portfolio_returns.append(portfolio_return)
                    
                    regime_returns = np.array(regime_portfolio_returns)
                    
                    results[regime_name] = {
                        'mean_return': float(regime_returns.mean()),
                        'volatility': float(regime_returns.std()),
                        'var_95': float(np.percentile(regime_returns, 5)),
                        'worst_day': float(regime_returns.min()),
                        'best_day': float(regime_returns.max()),
                        'sample_size': len(regime_returns)
                    }
            
            return results
            
        except Exception as e:
            return {'error': f'Regime stress tests failed: {str(e)}'}
    
    def _assess_overall_risk(self, stress_results):
        """Assess overall portfolio risk"""
        
        try:
            risk_score = 0
            risk_factors = []
            
            # Check stress test results
            for scenario_name, results in stress_results.get('stress_test_results', {}).items():
                if isinstance(results, dict) and 'portfolio_impact' in results:
                    impact = abs(results['portfolio_impact'])
                    if impact > 0.1:  # 10% loss
                        risk_score += 2
                        risk_factors.append(f"High loss in {scenario_name}: {impact:.1%}")
                    elif impact > 0.05:  # 5% loss
                        risk_score += 1
                        risk_factors.append(f"Moderate loss in {scenario_name}: {impact:.1%}")
            
            # Check regime-specific risks
            regime_tests = stress_results.get('regime_stress_tests', {})
            for regime, metrics in regime_tests.items():
                if isinstance(metrics, dict):
                    var_95 = metrics.get('var_95', 0)
                    if var_95 < -0.05:  # 5% daily VaR
                        risk_score += 1
                        risk_factors.append(f"High VaR in {regime} regime: {var_95:.1%}")
            
            # Overall risk assessment
            if risk_score >= 5:
                risk_level = "HIGH"
            elif risk_score >= 3:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors
            }
            
        except Exception as e:
            return {'error': f'Risk assessment failed: {str(e)}'}
    
    def _generate_risk_recommendations(self, stress_results):
        """Generate risk management recommendations"""
        
        recommendations = []
        
        try:
            # Check for concentration risk
            overall_risk = stress_results.get('overall_risk_assessment', {})
            risk_level = overall_risk.get('risk_level', 'UNKNOWN')
            
            if risk_level == 'HIGH':
                recommendations.append("Consider reducing portfolio risk through diversification")
                recommendations.append("Implement dynamic hedging strategies")
                recommendations.append("Reduce position sizes in volatile periods")
            
            elif risk_level == 'MODERATE':
                recommendations.append("Monitor regime changes closely")
                recommendations.append("Consider partial hedging during high volatility periods")
            
            # Regime-specific recommendations
            regime_tests = stress_results.get('regime_stress_tests', {})
            
            if 'high_volatility' in regime_tests:
                hv_metrics = regime_tests['high_volatility']
                if isinstance(hv_metrics, dict):
                    var_95 = hv_metrics.get('var_95', 0)
                    if var_95 < -0.03:
                        recommendations.append("Implement volatility-based position sizing")
            
            if not recommendations:
                recommendations.append("Current risk profile appears acceptable")
                recommendations.append("Continue monitoring market regimes")
            
            return recommendations
            
        except Exception:
            return ["Unable to generate recommendations due to data limitations"]
    
    def _adjust_returns_for_regime(self, expected_returns, regime_probabilities):
        """Adjust expected returns based on regime probabilities"""
        
        try:
            # Simple adjustment: reduce expected returns in high volatility regimes
            if len(regime_probabilities) >= 2:
                high_vol_prob = regime_probabilities[1]
                adjustment_factor = 1.0 - (high_vol_prob * 0.2)  # Up to 20% reduction
                return expected_returns * adjustment_factor
            
            return expected_returns
            
        except Exception:
            return expected_returns
    
    def _adjust_covariance_for_regime(self, covariance_matrix, regime_probabilities):
        """Adjust covariance matrix based on regime probabilities"""
        
        try:
            # Simple adjustment: increase volatilities in high volatility regimes
            if len(regime_probabilities) >= 2:
                high_vol_prob = regime_probabilities[1]
                vol_multiplier = 1.0 + (high_vol_prob * 0.5)  # Up to 50% increase
                return covariance_matrix * (vol_multiplier ** 2)
            
            return covariance_matrix
            
        except Exception:
            return covariance_matrix

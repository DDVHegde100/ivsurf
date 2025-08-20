"""
Advanced UI Enhancements for IVSURF Terminal
===========================================

Sophisticated visualization components for regime analysis:
- 3D regime probability surfaces
- Dynamic correlation heatmaps
- Interactive stress testing dashboards
- Real-time risk monitoring panels
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

class AdvancedVisualizationEngine:
    """
    Advanced visualization engine for regime analysis and risk management
    """
    
    def __init__(self):
        self.color_schemes = {
            'regime': ['#00ff00', '#ff6600', '#ff0000'],  # Green, Orange, Red
            'risk': ['#0066ff', '#ffff00', '#ff0000'],    # Blue, Yellow, Red
            'performance': ['#00ffff', '#ffffff', '#ff00ff']  # Cyan, White, Magenta
        }
    
    def create_regime_probability_surface(self, regime_data, dates, ticker):
        """
        Create 3D surface plot of regime probabilities over time
        
        Args:
            regime_data: Dictionary containing regime analysis results
            dates: Time series dates
            ticker: Stock ticker
            
        Returns:
            plotly.graph_objects.Figure: 3D surface plot
        """
        
        try:
            regime_probs = regime_data.get('regime_probabilities')
            
            if not regime_probs or len(regime_probs) == 0:
                return self._create_error_plot("No regime probability data available")
            
            # Convert to numpy array
            probs_array = np.array(regime_probs)
            
            if probs_array.ndim == 1:
                # Single regime probabilities
                probs_array = probs_array.reshape(-1, 1)
            
            n_time_points = len(dates)
            n_regimes = probs_array.shape[1]
            
            # Create 3D surface
            fig = go.Figure()
            
            # Time axis
            x_time = list(range(len(dates)))
            
            for regime_idx in range(n_regimes):
                # Get probabilities for this regime
                regime_probs_series = probs_array[:, regime_idx] if probs_array.shape[1] > regime_idx else np.zeros(len(dates))
                
                # Create surface
                fig.add_trace(go.Scatter3d(
                    x=x_time,
                    y=[regime_idx] * len(x_time),
                    z=regime_probs_series,
                    mode='lines+markers',
                    name=f'Regime {regime_idx + 1}',
                    line=dict(
                        color=self.color_schemes['regime'][regime_idx % len(self.color_schemes['regime'])],
                        width=4
                    ),
                    marker=dict(
                        size=3,
                        color=regime_probs_series,
                        colorscale='Viridis',
                        cmin=0,
                        cmax=1
                    )
                ))
            
            # Update layout
            fig.update_layout(
                title=f"3D Regime Probability Evolution - {ticker}",
                scene=dict(
                    xaxis_title="Time Index",
                    yaxis_title="Regime",
                    zaxis_title="Probability",
                    bgcolor='black',
                    xaxis=dict(gridcolor='gray'),
                    yaxis=dict(gridcolor='gray'),
                    zaxis=dict(gridcolor='gray')
                ),
                template='plotly_dark',
                height=600,
                font=dict(color='white')
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"Regime surface creation failed: {str(e)}")
    
    def create_dynamic_correlation_heatmap(self, correlation_data, window_size=20):
        """
        Create animated correlation heatmap showing evolution over time
        
        Args:
            correlation_data: Time-varying correlation data
            window_size: Rolling window size for correlation calculation
            
        Returns:
            plotly.graph_objects.Figure: Animated correlation heatmap
        """
        
        try:
            if not correlation_data or 'time_series' not in correlation_data:
                return self._create_error_plot("No correlation time series data available")
            
            time_series = correlation_data['time_series']
            
            if not time_series:
                return self._create_error_plot("Empty correlation time series")
            
            # Create frames for animation
            frames = []
            time_points = list(time_series.keys())
            correlations = list(time_series.values())
            
            # Create correlation matrix evolution
            n_points = len(time_points)
            frame_step = max(1, n_points // 50)  # Limit to 50 frames
            
            for i in range(0, n_points, frame_step):
                # Create mock correlation matrix for demonstration
                # In real implementation, this would be actual asset correlations
                corr_value = correlations[i]
                
                # Create a sample 5x5 correlation matrix
                assets = ['Asset 1', 'Asset 2', 'Asset 3', 'Asset 4', 'Asset 5']
                n_assets = len(assets)
                
                # Generate correlation matrix with the time-varying correlation
                corr_matrix = np.eye(n_assets)
                for row in range(n_assets):
                    for col in range(row + 1, n_assets):
                        # Use the average correlation with some variation
                        correlation = corr_value + np.random.normal(0, 0.1)
                        correlation = np.clip(correlation, -0.99, 0.99)
                        corr_matrix[row, col] = correlation
                        corr_matrix[col, row] = correlation
                
                frames.append(go.Frame(
                    data=[go.Heatmap(
                        z=corr_matrix,
                        x=assets,
                        y=assets,
                        colorscale='RdBu',
                        zmid=0,
                        zmin=-1,
                        zmax=1,
                        text=np.round(corr_matrix, 2),
                        texttemplate="%{text}",
                        textfont={"size": 10},
                        hoverongaps=False
                    )],
                    name=f'Frame {i}'
                ))
            
            # Create initial plot
            initial_corr = np.eye(5)
            fig = go.Figure(
                data=[go.Heatmap(
                    z=initial_corr,
                    x=assets,
                    y=assets,
                    colorscale='RdBu',
                    zmid=0,
                    zmin=-1,
                    zmax=1
                )],
                frames=frames
            )
            
            # Add animation controls
            fig.update_layout(
                title="Dynamic Asset Correlation Evolution",
                template='plotly_dark',
                height=500,
                updatemenus=[{
                    'type': 'buttons',
                    'showactive': False,
                    'buttons': [
                        {'label': 'Play', 'method': 'animate', 'args': [None]},
                        {'label': 'Pause', 'method': 'animate', 'args': [None, {'frame': {'duration': 0}}]}
                    ]
                }]
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"Correlation heatmap creation failed: {str(e)}")
    
    def create_stress_test_dashboard(self, stress_results):
        """
        Create comprehensive stress testing dashboard
        
        Args:
            stress_results: Stress testing results
            
        Returns:
            plotly.graph_objects.Figure: Stress test dashboard
        """
        
        try:
            if not stress_results or stress_results.get('error'):
                return self._create_error_plot("No stress test results available")
            
            # Create subplot figure
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Stress Scenario Impacts',
                    'Risk Level Assessment', 
                    'Maximum Drawdown Analysis',
                    'Regime-Specific Risks'
                ),
                specs=[
                    [{"type": "bar"}, {"type": "indicator"}],
                    [{"type": "scatter"}, {"type": "bar"}]
                ]
            )
            
            # 1. Stress scenario impacts (Bar chart)
            scenario_results = stress_results.get('stress_test_results', {})
            scenarios = []
            impacts = []
            
            for scenario_name, result in scenario_results.items():
                if isinstance(result, dict) and 'portfolio_impact' in result:
                    scenarios.append(scenario_name.replace('_', ' ').title())
                    impacts.append(abs(result['portfolio_impact']) * 100)  # Convert to percentage
            
            if scenarios:
                fig.add_trace(
                    go.Bar(
                        x=scenarios,
                        y=impacts,
                        name='Portfolio Impact (%)',
                        marker_color=['red' if impact > 5 else 'orange' if impact > 2 else 'green' 
                                    for impact in impacts]
                    ),
                    row=1, col=1
                )
            
            # 2. Risk level indicator
            overall_risk = stress_results.get('overall_risk_assessment', {})
            risk_level = overall_risk.get('risk_level', 'UNKNOWN')
            risk_score = overall_risk.get('risk_score', 0)
            
            color_map = {'LOW': 'green', 'MODERATE': 'orange', 'HIGH': 'red', 'UNKNOWN': 'gray'}
            
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=risk_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': f"Risk Level: {risk_level}"},
                    gauge={
                        'axis': {'range': [None, 10]},
                        'bar': {'color': color_map.get(risk_level, 'gray')},
                        'steps': [
                            {'range': [0, 3], 'color': "lightgreen"},
                            {'range': [3, 6], 'color': "orange"},
                            {'range': [6, 10], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 8
                        }
                    }
                ),
                row=1, col=2
            )
            
            # 3. Maximum drawdown analysis
            max_dd_analysis = stress_results.get('max_drawdown_analysis', {})
            worst_scenarios = max_dd_analysis.get('worst_scenarios', [])
            
            if worst_scenarios:
                dates = [scenario['start_date'] for scenario in worst_scenarios[:10]]
                drawdowns = [abs(scenario['max_drawdown']) * 100 for scenario in worst_scenarios[:10]]
                
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(dates))),
                        y=drawdowns,
                        mode='lines+markers',
                        name='Max Drawdown (%)',
                        line=dict(color='red', width=2),
                        marker=dict(size=8)
                    ),
                    row=2, col=1
                )
            
            # 4. Regime-specific risks
            regime_tests = stress_results.get('regime_stress_tests', {})
            regime_names = []
            regime_vars = []
            
            for regime_name, metrics in regime_tests.items():
                if isinstance(metrics, dict) and 'var_95' in metrics:
                    regime_names.append(regime_name.replace('_', ' ').title())
                    regime_vars.append(abs(metrics['var_95']) * 100)
            
            if regime_names:
                fig.add_trace(
                    go.Bar(
                        x=regime_names,
                        y=regime_vars,
                        name='VaR 95% (%)',
                        marker_color=['red' if var > 3 else 'orange' if var > 1.5 else 'green' 
                                    for var in regime_vars]
                    ),
                    row=2, col=2
                )
            
            # Update layout
            fig.update_layout(
                title="Comprehensive Stress Testing Dashboard",
                template='plotly_dark',
                height=700,
                showlegend=False
            )
            
            # Update subplot axes
            fig.update_xaxes(title_text="Stress Scenarios", row=1, col=1)
            fig.update_yaxes(title_text="Impact (%)", row=1, col=1)
            
            fig.update_xaxes(title_text="Scenario Rank", row=2, col=1)
            fig.update_yaxes(title_text="Max Drawdown (%)", row=2, col=1)
            
            fig.update_xaxes(title_text="Market Regime", row=2, col=2)
            fig.update_yaxes(title_text="VaR 95% (%)", row=2, col=2)
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"Stress test dashboard creation failed: {str(e)}")
    
    def create_real_time_risk_monitor(self, portfolio_data, risk_metrics):
        """
        Create real-time risk monitoring panel
        
        Args:
            portfolio_data: Current portfolio data
            risk_metrics: Real-time risk metrics
            
        Returns:
            plotly.graph_objects.Figure: Risk monitoring dashboard
        """
        
        try:
            # Create subplot figure
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=(
                    'Portfolio VaR',
                    'Volatility Clustering',
                    'Regime Probabilities',
                    'Correlation Risk',
                    'Concentration Risk',
                    'Performance Attribution'
                ),
                specs=[
                    [{"type": "indicator"}, {"type": "scatter"}, {"type": "bar"}],
                    [{"type": "heatmap"}, {"type": "pie"}, {"type": "bar"}]
                ]
            )
            
            # 1. Portfolio VaR Indicator
            var_95 = risk_metrics.get('var_95', 0)
            
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=abs(var_95) * 100,
                    title={'text': "Portfolio VaR 95%"},
                    gauge={
                        'axis': {'range': [0, 10]},
                        'bar': {'color': 'red' if abs(var_95) > 0.05 else 'orange' if abs(var_95) > 0.02 else 'green'},
                        'steps': [
                            {'range': [0, 2], 'color': "lightgreen"},
                            {'range': [2, 5], 'color': "orange"},
                            {'range': [5, 10], 'color': "red"}
                        ]
                    }
                ),
                row=1, col=1
            )
            
            # 2. Volatility clustering (time series)
            clustering_data = risk_metrics.get('clustering_strength', {})
            if clustering_data and 'time_series' in clustering_data:
                time_series = clustering_data['time_series']
                fig.add_trace(
                    go.Scatter(
                        y=time_series,
                        mode='lines',
                        name='Clustering Strength',
                        line=dict(color='cyan', width=2)
                    ),
                    row=1, col=2
                )
            
            # 3. Current regime probabilities
            regime_probs = risk_metrics.get('current_regime_probs', [0.5, 0.5])
            regime_names = [f'Regime {i+1}' for i in range(len(regime_probs))]
            
            fig.add_trace(
                go.Bar(
                    x=regime_names,
                    y=[p * 100 for p in regime_probs],
                    name='Regime Probability (%)',
                    marker_color=['green' if i == 0 else 'red' for i in range(len(regime_probs))]
                ),
                row=1, col=3
            )
            
            # 4. Correlation risk heatmap
            asset_correlations = risk_metrics.get('asset_correlations', {})
            if asset_correlations:
                # Create correlation matrix
                assets = list(asset_correlations.keys())
                n_assets = len(assets)
                
                if n_assets > 1:
                    corr_matrix = np.eye(n_assets)
                    # This is a simplified example - real implementation would have actual correlations
                    for i in range(n_assets):
                        for j in range(i+1, n_assets):
                            corr_value = 0.3 + np.random.normal(0, 0.2)  # Sample correlation
                            corr_value = np.clip(corr_value, -0.99, 0.99)
                            corr_matrix[i, j] = corr_value
                            corr_matrix[j, i] = corr_value
                    
                    fig.add_trace(
                        go.Heatmap(
                            z=corr_matrix,
                            x=assets,
                            y=assets,
                            colorscale='RdBu',
                            zmid=0,
                            showscale=False
                        ),
                        row=2, col=1
                    )
            
            # 5. Concentration risk (pie chart)
            portfolio_weights = portfolio_data.get('weights', {})
            if portfolio_weights:
                assets = list(portfolio_weights.keys())
                weights = list(portfolio_weights.values())
                
                fig.add_trace(
                    go.Pie(
                        labels=assets,
                        values=weights,
                        name="Portfolio Allocation"
                    ),
                    row=2, col=2
                )
            
            # 6. Performance attribution
            attribution = risk_metrics.get('performance_attribution', {})
            if attribution:
                factors = list(attribution.keys())
                contributions = list(attribution.values())
                
                fig.add_trace(
                    go.Bar(
                        x=factors,
                        y=contributions,
                        name='Performance Contribution',
                        marker_color=['green' if c > 0 else 'red' for c in contributions]
                    ),
                    row=2, col=3
                )
            
            # Update layout
            fig.update_layout(
                title="Real-Time Risk Monitoring Dashboard",
                template='plotly_dark',
                height=700,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"Risk monitor creation failed: {str(e)}")
    
    def create_volatility_clustering_3d(self, clustering_data, ticker):
        """
        Create 3D visualization of volatility clustering patterns
        
        Args:
            clustering_data: Volatility clustering analysis results
            ticker: Stock ticker
            
        Returns:
            plotly.graph_objects.Figure: 3D clustering visualization
        """
        
        try:
            individual_analysis = clustering_data.get('individual_analysis', {}).get(ticker, {})
            clustering_strength = individual_analysis.get('clustering_strength', {})
            
            if not clustering_strength or 'time_series' not in clustering_strength:
                return self._create_error_plot("No clustering strength data available")
            
            time_series = clustering_strength['time_series']
            
            if not time_series:
                return self._create_error_plot("Empty clustering time series")
            
            # Create 3D scatter plot
            fig = go.Figure()
            
            # Time indices
            time_indices = list(range(len(time_series)))
            
            # Create volatility levels (simulate different volatility regimes)
            vol_levels = []
            for strength in time_series:
                if strength > 0.5:
                    vol_levels.append(2)  # High volatility
                elif strength > 0.2:
                    vol_levels.append(1)  # Medium volatility
                else:
                    vol_levels.append(0)  # Low volatility
            
            # Create 3D scatter
            fig.add_trace(go.Scatter3d(
                x=time_indices,
                y=vol_levels,
                z=time_series,
                mode='markers+lines',
                marker=dict(
                    size=5,
                    color=time_series,
                    colorscale='Viridis',
                    colorbar=dict(title="Clustering Strength"),
                    line=dict(color='white', width=1)
                ),
                line=dict(color='cyan', width=2),
                name='Clustering Evolution'
            ))
            
            # Update layout
            fig.update_layout(
                title=f"3D Volatility Clustering Analysis - {ticker}",
                scene=dict(
                    xaxis_title="Time",
                    yaxis_title="Volatility Regime",
                    zaxis_title="Clustering Strength",
                    bgcolor='black'
                ),
                template='plotly_dark',
                height=600
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"3D clustering visualization failed: {str(e)}")
    
    def create_regime_transition_network(self, regime_data):
        """
        Create network visualization of regime transitions
        
        Args:
            regime_data: Regime analysis results with transition matrix
            
        Returns:
            plotly.graph_objects.Figure: Regime transition network
        """
        
        try:
            transitions = regime_data.get('transition_probabilities', {})
            transition_matrix = transitions.get('matrix', [])
            
            if not transition_matrix:
                return self._create_error_plot("No transition matrix available")
            
            n_regimes = len(transition_matrix)
            
            # Create network nodes
            fig = go.Figure()
            
            # Node positions (circle layout)
            angles = np.linspace(0, 2*np.pi, n_regimes, endpoint=False)
            node_x = np.cos(angles)
            node_y = np.sin(angles)
            
            # Add edges (transitions)
            for i in range(n_regimes):
                for j in range(n_regimes):
                    if i != j and transition_matrix[i][j] > 0.01:  # Only significant transitions
                        # Draw arrow from regime i to regime j
                        fig.add_trace(go.Scatter(
                            x=[node_x[i], node_x[j]],
                            y=[node_y[i], node_y[j]],
                            mode='lines',
                            line=dict(
                                color='cyan',
                                width=transition_matrix[i][j] * 10  # Width proportional to probability
                            ),
                            showlegend=False,
                            hoverinfo='text',
                            text=f"Regime {i+1} → Regime {j+1}: {transition_matrix[i][j]:.3f}"
                        ))
            
            # Add nodes
            fig.add_trace(go.Scatter(
                x=node_x,
                y=node_y,
                mode='markers+text',
                marker=dict(
                    size=50,
                    color=['green', 'red'][:n_regimes],
                    line=dict(width=2, color='white')
                ),
                text=[f'Regime {i+1}' for i in range(n_regimes)],
                textposition="middle center",
                textfont=dict(color='white', size=12),
                name='Regimes'
            ))
            
            # Update layout
            fig.update_layout(
                title="Regime Transition Network",
                template='plotly_dark',
                height=500,
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False)
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"Regime network creation failed: {str(e)}")
    
    def _create_error_plot(self, error_message):
        """Create error plot when visualization fails"""
        
        fig = go.Figure()
        
        fig.add_annotation(
            text=f"⚠️ {error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color="orange"),
            showarrow=False
        )
        
        fig.update_layout(
            title="Visualization Error",
            template='plotly_dark',
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig
    
    def create_performance_comparison_chart(self, backtest_results):
        """
        Create performance comparison chart for different strategies
        
        Args:
            backtest_results: Backtesting results
            
        Returns:
            plotly.graph_objects.Figure: Performance comparison chart
        """
        
        try:
            portfolio_history = backtest_results.get('portfolio_history')
            
            if portfolio_history is None or portfolio_history.empty:
                return self._create_error_plot("No portfolio history available")
            
            fig = go.Figure()
            
            # Portfolio value over time
            fig.add_trace(go.Scatter(
                x=portfolio_history['date'],
                y=portfolio_history['portfolio_value'],
                mode='lines',
                name='Regime-Aware Portfolio',
                line=dict(color='cyan', width=2)
            ))
            
            # Benchmark (cumulative benchmark returns)
            initial_value = portfolio_history['portfolio_value'].iloc[0]
            benchmark_values = [initial_value]
            
            for i, benchmark_return in enumerate(portfolio_history['benchmark_return'].iloc[1:], 1):
                benchmark_values.append(benchmark_values[-1] * (1 + benchmark_return))
            
            fig.add_trace(go.Scatter(
                x=portfolio_history['date'],
                y=benchmark_values,
                mode='lines',
                name='Benchmark',
                line=dict(color='orange', width=2, dash='dash')
            ))
            
            # Update layout
            fig.update_layout(
                title="Regime-Aware Strategy vs Benchmark",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                template='plotly_dark',
                height=500,
                legend=dict(x=0.02, y=0.98)
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"Performance chart creation failed: {str(e)}")
    
    def create_risk_contribution_sunburst(self, risk_attribution):
        """
        Create sunburst chart for risk contribution analysis
        
        Args:
            risk_attribution: Risk attribution data
            
        Returns:
            plotly.graph_objects.Figure: Sunburst chart
        """
        
        try:
            asset_contributions = risk_attribution.get('asset_contributions', {})
            
            if not asset_contributions:
                return self._create_error_plot("No risk attribution data available")
            
            # Prepare data for sunburst
            ids = ['Portfolio']
            labels = ['Total Risk']
            parents = ['']
            values = [1.0]  # Total portfolio
            
            # Add asset contributions
            for asset, contribution_data in asset_contributions.items():
                vol_contribution = contribution_data.get('volatility_contribution', 0)
                weight = contribution_data.get('average_weight', 0)
                
                ids.append(asset)
                labels.append(f"{asset}<br>{weight*100:.1f}% weight")
                parents.append('Portfolio')
                values.append(abs(vol_contribution))
            
            fig = go.Figure(go.Sunburst(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",
                hovertemplate='<b>%{label}</b><br>Risk Contribution: %{value:.3f}<extra></extra>',
                maxdepth=2,
            ))
            
            fig.update_layout(
                title="Portfolio Risk Attribution",
                template='plotly_dark',
                height=500
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_plot(f"Risk sunburst creation failed: {str(e)}")

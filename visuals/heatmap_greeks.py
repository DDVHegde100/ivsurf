#!/usr/bin/env python3
"""
Enhanced Greeks Heatmap Visualization Module
===========================================

Professional heatmap visualizations for Greeks analysis
with retro terminal styling and advanced filtering

Author: IVSURF Systems
Date: August 16, 2025
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional, Union


class GreeksHeatmapGenerator:
    """Professional Greeks heatmap generator with retro styling"""
    
    def __init__(self):
        self.retro_colors = {
            'primary': '#00ff41',
            'secondary': '#66ff66',
            'accent': '#88ff88',
            'background': '#000000',
            'dark_green': '#004400',
            'medium_green': '#008800',
            'warning': '#ffff00',
            'error': '#ff4444'
        }
        
        self.colorscales = {
            'delta': [
                [0, '#ff0000'],      # Red for negative
                [0.3, '#ff4444'],    
                [0.5, '#000000'],    # Black for neutral
                [0.7, '#004400'],    
                [1, '#00ff00']       # Green for positive
            ],
            'gamma': [
                [0, '#000000'],      # Black for low
                [0.3, '#004400'],    
                [0.6, '#008800'],    
                [0.8, '#00ff00'],    
                [1, '#44ff44']       # Bright green for high
            ],
            'theta': [
                [0, '#ff0000'],      # Red for high decay
                [0.4, '#ff8800'],    
                [0.6, '#ffff00'],    
                [0.8, '#88ff00'],    
                [1, '#00ff00']       # Green for low decay
            ],
            'vega': [
                [0, '#000000'],      # Black for low
                [0.25, '#004400'],   
                [0.5, '#008800'],    
                [0.75, '#00ff00'],   
                [1, '#88ff88']       # Light green for high
            ],
            'rho': [
                [0, '#ff0000'],      # Red for negative
                [0.3, '#ff4444'],    
                [0.5, '#000000'],    # Black for neutral
                [0.7, '#004400'],    
                [1, '#00ff00']       # Green for positive
            ]
        }

    def create_greeks_heatmap(
        self, 
        strikes: List[float], 
        expiries: List[float], 
        greeks_data: Dict,
        greek_type: str = 'delta',
        option_type: str = 'call',
        title_suffix: str = ""
    ) -> go.Figure:
        """
        Create professional Greeks heatmap with retro styling
        
        Args:
            strikes: List of strike prices
            expiries: List of time to expiries
            greeks_data: Dictionary containing calculated Greeks
            greek_type: Type of Greek ('delta', 'gamma', 'theta', 'vega', 'rho')
            option_type: 'call' or 'put'
            title_suffix: Additional title text
        """
        
        # Create meshgrid for strikes and expiries
        strike_grid, expiry_grid = np.meshgrid(strikes, expiries)
        
        # Initialize Greeks grid
        greeks_grid = np.zeros_like(strike_grid)
        
        # Fill in Greeks values
        for i, expiry in enumerate(expiries):
            for j, strike in enumerate(strikes):
                key = f"{strike}_{expiry}_{option_type}"
                if key in greeks_data and greek_type in greeks_data[key]:
                    greeks_grid[i, j] = greeks_data[key][greek_type]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            x=strikes,
            y=expiries,
            z=greeks_grid,
            colorscale=self.colorscales.get(greek_type, 'RdYlGn'),
            hoverongaps=False,
            hovertemplate='<b>Strike</b>: $%{x:.2f}<br>' +
                         '<b>Time to Expiry</b>: %{y:.3f} years<br>' +
                         f'<b>{greek_type.upper()}</b>: %{{z:.4f}}<br>' +
                         '<extra></extra>',
            colorbar=dict(
                title=f'{greek_type.upper()} ({option_type.upper()})',
                titlefont=dict(color=self.retro_colors['primary'], size=12),
                tickfont=dict(color=self.retro_colors['primary']),
                thickness=20
            )
        ))
        
        # Update layout with retro styling
        fig.update_layout(
            title={
                'text': f'{greek_type.upper()} HEATMAP - {option_type.upper()} OPTIONS {title_suffix}',
                'font': {'color': self.retro_colors['primary'], 'size': 16},
                'x': 0.5,
                'y': 0.95
            },
            xaxis=dict(
                title='Strike Price ($)',
                titlefont=dict(color=self.retro_colors['primary']),
                tickfont=dict(color=self.retro_colors['primary']),
                gridcolor=self.retro_colors['dark_green'],
                showgrid=True
            ),
            yaxis=dict(
                title='Time to Expiry (Years)',
                titlefont=dict(color=self.retro_colors['primary']),
                tickfont=dict(color=self.retro_colors['primary']),
                gridcolor=self.retro_colors['dark_green'],
                showgrid=True
            ),
            paper_bgcolor=self.retro_colors['background'],
            plot_bgcolor=self.retro_colors['background'],
            width=800,
            height=600,
            margin=dict(r=100, b=50, l=70, t=80)
        )
        
        return fig

    def create_multi_greeks_heatmap(
        self, 
        strikes: List[float], 
        expiries: List[float], 
        greeks_data: Dict,
        option_type: str = 'call'
    ) -> go.Figure:
        """Create comprehensive multi-Greeks heatmap dashboard"""
        
        # Create subplots for all Greeks
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[
                f'DELTA ({option_type.upper()})',
                f'GAMMA ({option_type.upper()})',
                f'THETA ({option_type.upper()})',
                f'VEGA ({option_type.upper()})',
                f'RHO ({option_type.upper()})',
                'OPTIONS OVERVIEW'
            ],
            specs=[[{"type": "heatmap"}, {"type": "heatmap"}, {"type": "heatmap"}],
                   [{"type": "heatmap"}, {"type": "heatmap"}, {"type": "scatter"}]],
            vertical_spacing=0.08,
            horizontal_spacing=0.06
        )
        
        # Create meshgrid
        strike_grid, expiry_grid = np.meshgrid(strikes, expiries)
        
        # Define Greeks to plot
        greeks_list = ['delta', 'gamma', 'theta', 'vega', 'rho']
        positions = [(1,1), (1,2), (1,3), (2,1), (2,2)]
        
        for idx, (greek, pos) in enumerate(zip(greeks_list, positions)):
            # Initialize grid
            greeks_grid = np.zeros_like(strike_grid)
            
            # Fill values
            for i, expiry in enumerate(expiries):
                for j, strike in enumerate(strikes):
                    key = f"{strike}_{expiry}_{option_type}"
                    if key in greeks_data and greek in greeks_data[key]:
                        greeks_grid[i, j] = greeks_data[key][greek]
            
            # Add heatmap
            fig.add_trace(
                go.Heatmap(
                    x=strikes,
                    y=expiries,
                    z=greeks_grid,
                    colorscale=self.colorscales.get(greek, 'RdYlGn'),
                    showscale=False,
                    hovertemplate=f'<b>{greek.upper()}</b>: %{{z:.4f}}<extra></extra>'
                ),
                row=pos[0], col=pos[1]
            )
        
        # Add overview scatter plot in the last subplot
        if greeks_data:
            overview_data = []
            for key, data in greeks_data.items():
                if option_type in key:
                    parts = key.split('_')
                    strike = float(parts[0])
                    expiry = float(parts[1])
                    overview_data.append({
                        'strike': strike,
                        'expiry': expiry,
                        'delta': data.get('delta', 0),
                        'gamma': data.get('gamma', 0),
                        'theta': data.get('theta', 0),
                        'vega': data.get('vega', 0),
                        'rho': data.get('rho', 0)
                    })
            
            if overview_data:
                df = pd.DataFrame(overview_data)
                
                # Create scatter plot sized by gamma, colored by delta
                fig.add_trace(
                    go.Scatter(
                        x=df['strike'],
                        y=df['expiry'],
                        mode='markers',
                        marker=dict(
                            size=df['gamma'] * 1000,  # Scale gamma for visibility
                            color=df['delta'],
                            colorscale='RdYlGn',
                            sizemode='diameter',
                            sizemin=4,
                            sizemax=20,
                            line=dict(color=self.retro_colors['primary'], width=1)
                        ),
                        hovertemplate='<b>Strike</b>: $%{x:.2f}<br>' +
                                     '<b>Expiry</b>: %{y:.3f} years<br>' +
                                     '<b>Delta</b>: %{marker.color:.4f}<br>' +
                                     '<b>Gamma</b>: %{marker.size:.6f}<br>' +
                                     '<extra></extra>',
                        name='Option Positions'
                    ),
                    row=2, col=3
                )
        
        # Update layout
        fig.update_layout(
            title={
                'text': f'COMPREHENSIVE GREEKS ANALYSIS - {option_type.upper()} OPTIONS',
                'font': {'color': self.retro_colors['primary'], 'size': 18},
                'x': 0.5
            },
            paper_bgcolor=self.retro_colors['background'],
            plot_bgcolor=self.retro_colors['background'],
            height=1000,
            width=1400,
            showlegend=False
        )
        
        # Update all axes
        for i in range(1, 6):
            row, col = positions[i-1]
            fig.update_xaxes(
                title='Strike ($)' if row == 2 else '',
                titlefont=dict(color=self.retro_colors['primary'], size=10),
                tickfont=dict(color=self.retro_colors['primary'], size=8),
                row=row, col=col
            )
            fig.update_yaxes(
                title='Time to Expiry' if col == 1 else '',
                titlefont=dict(color=self.retro_colors['primary'], size=10),
                tickfont=dict(color=self.retro_colors['primary'], size=8),
                row=row, col=col
            )
        
        # Update overview plot axes
        fig.update_xaxes(
            title='Strike ($)',
            titlefont=dict(color=self.retro_colors['primary'], size=10),
            tickfont=dict(color=self.retro_colors['primary'], size=8),
            row=2, col=3
        )
        fig.update_yaxes(
            title='Time to Expiry',
            titlefont=dict(color=self.retro_colors['primary'], size=10),
            tickfont=dict(color=self.retro_colors['primary'], size=8),
            row=2, col=3
        )
        
        return fig

    def create_risk_profile_heatmap(
        self, 
        strikes: List[float], 
        spot_prices: List[float], 
        greeks_data: Dict,
        option_type: str = 'call'
    ) -> go.Figure:
        """Create risk profile heatmap showing P&L across spot price movements"""
        
        # Create meshgrid
        strike_grid, spot_grid = np.meshgrid(strikes, spot_prices)
        
        # Calculate P&L for each combination
        pnl_grid = np.zeros_like(strike_grid)
        
        for i, spot in enumerate(spot_prices):
            for j, strike in enumerate(strikes):
                # Calculate intrinsic value
                if option_type == 'call':
                    intrinsic = max(0, spot - strike)
                else:
                    intrinsic = max(0, strike - spot)
                
                # Add Greeks-based adjustments (simplified)
                key = f"{strike}_0.083_{option_type}"  # Assume ~1 month expiry
                if key in greeks_data:
                    delta_pnl = greeks_data[key].get('delta', 0) * (spot - strikes[len(strikes)//2])
                    gamma_pnl = 0.5 * greeks_data[key].get('gamma', 0) * (spot - strikes[len(strikes)//2])**2
                    theta_pnl = greeks_data[key].get('theta', 0) * (1/365)  # 1 day decay
                    
                    pnl_grid[i, j] = intrinsic + delta_pnl + gamma_pnl + theta_pnl
                else:
                    pnl_grid[i, j] = intrinsic
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            x=strikes,
            y=spot_prices,
            z=pnl_grid,
            colorscale=[
                [0, '#ff0000'],      # Red for losses
                [0.3, '#ff8800'],    
                [0.5, '#000000'],    # Black for breakeven
                [0.7, '#004400'],    
                [1, '#00ff00']       # Green for profits
            ],
            hoverongaps=False,
            hovertemplate='<b>Strike</b>: $%{x:.2f}<br>' +
                         '<b>Spot Price</b>: $%{y:.2f}<br>' +
                         '<b>P&L</b>: $%{z:.2f}<br>' +
                         '<extra></extra>',
            colorbar=dict(
                title='P&L ($)',
                titlefont=dict(color=self.retro_colors['primary'], size=12),
                tickfont=dict(color=self.retro_colors['primary'])
            )
        ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': f'RISK PROFILE HEATMAP - {option_type.upper()} OPTIONS',
                'font': {'color': self.retro_colors['primary'], 'size': 16},
                'x': 0.5
            },
            xaxis=dict(
                title='Strike Price ($)',
                titlefont=dict(color=self.retro_colors['primary']),
                tickfont=dict(color=self.retro_colors['primary']),
                gridcolor=self.retro_colors['dark_green']
            ),
            yaxis=dict(
                title='Spot Price at Expiry ($)',
                titlefont=dict(color=self.retro_colors['primary']),
                tickfont=dict(color=self.retro_colors['primary']),
                gridcolor=self.retro_colors['dark_green']
            ),
            paper_bgcolor=self.retro_colors['background'],
            plot_bgcolor=self.retro_colors['background'],
            width=800,
            height=600
        )
        
        return fig

    def create_time_decay_heatmap(
        self, 
        strikes: List[float], 
        days_to_expiry: List[int], 
        greeks_data: Dict,
        option_type: str = 'call'
    ) -> go.Figure:
        """Create time decay visualization heatmap"""
        
        # Convert days to years
        expiries = [d/365.0 for d in days_to_expiry]
        
        # Create meshgrid
        strike_grid, expiry_grid = np.meshgrid(strikes, expiries)
        
        # Calculate theta values
        theta_grid = np.zeros_like(strike_grid)
        
        for i, expiry in enumerate(expiries):
            for j, strike in enumerate(strikes):
                key = f"{strike}_{expiry}_{option_type}"
                if key in greeks_data and 'theta' in greeks_data[key]:
                    theta_grid[i, j] = abs(greeks_data[key]['theta'])  # Absolute value for visualization
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            x=strikes,
            y=days_to_expiry,
            z=theta_grid,
            colorscale=self.colorscales['theta'],
            hoverongaps=False,
            hovertemplate='<b>Strike</b>: $%{x:.2f}<br>' +
                         '<b>Days to Expiry</b>: %{y:.0f}<br>' +
                         '<b>|Theta|</b>: %{z:.4f}<br>' +
                         '<extra></extra>',
            colorbar=dict(
                title='|Theta| (Time Decay)',
                titlefont=dict(color=self.retro_colors['primary'], size=12),
                tickfont=dict(color=self.retro_colors['primary'])
            )
        ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': f'TIME DECAY HEATMAP - {option_type.upper()} OPTIONS',
                'font': {'color': self.retro_colors['primary'], 'size': 16},
                'x': 0.5
            },
            xaxis=dict(
                title='Strike Price ($)',
                titlefont=dict(color=self.retro_colors['primary']),
                tickfont=dict(color=self.retro_colors['primary']),
                gridcolor=self.retro_colors['dark_green']
            ),
            yaxis=dict(
                title='Days to Expiry',
                titlefont=dict(color=self.retro_colors['primary']),
                tickfont=dict(color=self.retro_colors['primary']),
                gridcolor=self.retro_colors['dark_green']
            ),
            paper_bgcolor=self.retro_colors['background'],
            plot_bgcolor=self.retro_colors['background'],
            width=800,
            height=600
        )
        
        return fig

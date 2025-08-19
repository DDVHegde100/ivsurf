#!/usr/bin/env python3
"""
Minimal Streamlit Dashboard with Plotly Interactive Surfaces
Author: IVSURF Systems
Description: Clean, professional interface for volatility surface analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import our core modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.black_scholes import black_scholes_price, implied_volatility
from core.greeks import delta, gamma, theta, vega, rho


class MinimalDashboard:
    """Clean, professional volatility surface dashboard"""
    
    def __init__(self):
        self.setup_page()
        
    def setup_page(self):
        """Configure page settings"""
        st.set_page_config(
            page_title="Volatility Surface Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Clean, minimal CSS
        st.markdown("""
        <style>
        .main {
            padding-top: 1rem;
        }
        .stMetric {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #e9ecef;
        }
        .metric-header {
            font-size: 1.2rem;
            font-weight: bold;
            color: #495057;
            margin-bottom: 1rem;
            text-align: center;
        }
        .data-table {
            border: 1px solid #dee2e6;
            border-radius: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

    def fetch_stock_data(self, ticker, period="1y"):
        """Fetch stock data and options chain"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get stock price data
            hist = stock.history(period=period)
            if hist.empty:
                return None, None, None
                
            current_price = hist['Close'].iloc[-1]
            
            # Get options data
            options_dates = stock.options
            if not options_dates:
                return hist, current_price, None
                
            # Get options chain for multiple expiries
            options_data = []
            for exp_date in options_dates[:6]:  # Limit to first 6 expiries
                try:
                    chain = stock.option_chain(exp_date)
                    calls = chain.calls
                    puts = chain.puts
                    
                    # Add expiry date to the data
                    calls['expiry'] = exp_date
                    puts['expiry'] = exp_date
                    calls['option_type'] = 'call'
                    puts['option_type'] = 'put'
                    
                    options_data.append(calls)
                    options_data.append(puts)
                except:
                    continue
                    
            options_df = pd.concat(options_data, ignore_index=True) if options_data else None
            
            return hist, current_price, options_df
            
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {str(e)}")
            return None, None, None

    def calculate_implied_volatility(self, options_df, current_price, risk_free_rate=0.05):
        """Calculate implied volatility for options"""
        if options_df is None or options_df.empty:
            return None
            
        iv_data = []
        
        for _, option in options_df.iterrows():
            try:
                # Calculate time to expiry
                expiry_date = pd.to_datetime(option['expiry'])
                days_to_expiry = (expiry_date - datetime.now()).days
                time_to_expiry = days_to_expiry / 365.0
                
                if time_to_expiry <= 0:
                    continue
                    
                # Use mid price for IV calculation
                if pd.isna(option['bid']) or pd.isna(option['ask']):
                    continue
                    
                market_price = (option['bid'] + option['ask']) / 2
                
                if market_price <= 0:
                    continue
                
                # Calculate implied volatility
                option_type = option['option_type']
                strike = option['strike']
                option_type_bs = 'call' if option_type == 'call' else 'put'
                
                try:
                    iv = implied_volatility(
                        market_price, current_price, strike, 
                        time_to_expiry, risk_free_rate, option_type_bs
                    )
                    
                    if iv is not None and 0.01 <= iv <= 5.0:  # Reasonable IV bounds
                        iv_data.append({
                            'strike': strike,
                            'expiry': option['expiry'],
                            'time_to_expiry': time_to_expiry,
                            'implied_volatility': iv,
                            'option_type': option_type,
                            'market_price': market_price,
                            'volume': option.get('volume', 0),
                            'open_interest': option.get('openInterest', 0)
                        })
                except:
                    continue
                    
            except Exception as e:
                continue
                
        return pd.DataFrame(iv_data) if iv_data else None

    def create_volatility_surface(self, iv_data):
        """Create interactive 3D volatility surface with Plotly"""
        if iv_data is None or iv_data.empty:
            return None
            
        # Prepare data for surface
        strikes = sorted(iv_data['strike'].unique())
        expiries = sorted(iv_data['time_to_expiry'].unique())
        
        # Create meshgrid
        strike_grid, expiry_grid = np.meshgrid(strikes, expiries)
        iv_grid = np.full(strike_grid.shape, np.nan)
        
        # Fill in the grid with actual IV values
        for i, expiry in enumerate(expiries):
            for j, strike in enumerate(strikes):
                mask = (iv_data['strike'] == strike) & (iv_data['time_to_expiry'] == expiry)
                if mask.any():
                    iv_values = iv_data.loc[mask, 'implied_volatility']
                    iv_grid[i, j] = iv_values.mean()  # Average if multiple values
        
        # Interpolate missing values
        from scipy.interpolate import griddata
        
        # Get valid points
        valid_mask = ~np.isnan(iv_grid)
        if valid_mask.sum() > 3:  # Need at least 3 points for interpolation
            points = np.column_stack((strike_grid[valid_mask], expiry_grid[valid_mask]))
            values = iv_grid[valid_mask]
            
            # Interpolate
            iv_grid_interp = griddata(
                points, values, 
                (strike_grid, expiry_grid), 
                method='cubic', 
                fill_value=np.nan
            )
            
            # Use linear interpolation for remaining NaN values
            remaining_nan = np.isnan(iv_grid_interp)
            if remaining_nan.any():
                iv_grid_linear = griddata(
                    points, values, 
                    (strike_grid, expiry_grid), 
                    method='linear', 
                    fill_value=np.nanmean(values)
                )
                iv_grid_interp[remaining_nan] = iv_grid_linear[remaining_nan]
        else:
            iv_grid_interp = iv_grid
        
        # Create 3D surface plot
        fig = go.Figure(data=[
            go.Surface(
                x=expiry_grid,
                y=strike_grid,
                z=iv_grid_interp,
                colorscale='Viridis',
                name='Implied Volatility Surface',
                colorbar=dict(title="Implied Volatility"),
                hovertemplate='<b>Time to Expiry</b>: %{x:.3f} years<br>' +
                             '<b>Strike</b>: $%{y:.2f}<br>' +
                             '<b>Implied Vol</b>: %{z:.2%}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Interactive Implied Volatility Surface',
            scene=dict(
                xaxis_title='Time to Expiry (Years)',
                yaxis_title='Strike Price ($)',
                zaxis_title='Implied Volatility',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            width=800,
            height=600,
            margin=dict(r=20, b=10, l=10, t=40)
        )
        
        return fig

    def calculate_all_greeks(self, current_price, strike, time_to_expiry, volatility, risk_free_rate=0.05):
        """Calculate all Greeks for an option"""
        try:
            greeks = {}
            
            # Calculate for both calls and puts
            for option_type in ['call', 'put']:
                # Black-Scholes price
                price = black_scholes_price(
                    current_price, strike, time_to_expiry, 
                    risk_free_rate, volatility, option_type
                )
                
                # All Greeks
                delta_val = delta(
                    current_price, strike, time_to_expiry,
                    risk_free_rate, volatility, option_type
                )
                
                gamma_val = gamma(
                    current_price, strike, time_to_expiry,
                    risk_free_rate, volatility
                )
                
                theta_val = theta(
                    current_price, strike, time_to_expiry,
                    risk_free_rate, volatility, option_type
                )
                
                vega_val = vega(
                    current_price, strike, time_to_expiry,
                    risk_free_rate, volatility
                )
                
                rho_val = rho(
                    current_price, strike, time_to_expiry,
                    risk_free_rate, volatility, option_type
                )
                
                greeks[option_type] = {
                    'price': price,
                    'delta': delta_val,
                    'gamma': gamma_val,
                    'theta': theta_val,
                    'vega': vega_val,
                    'rho': rho_val
                }
                
            return greeks
            
        except Exception as e:
            st.error(f"Error calculating Greeks: {str(e)}")
            return None

    def create_greeks_visualization(self, current_price, strike, time_to_expiry, volatility):
        """Create visualizations for Greeks"""
        
        # Create range of spot prices around current price
        spot_range = np.linspace(current_price * 0.7, current_price * 1.3, 50)
        
        greeks_data = {'spot_price': spot_range}
        
        for option_type in ['call', 'put']:
            deltas = []
            gammas = []
            vegas = []
            thetas = []
            
            for spot in spot_range:
                delta_val = delta(
                    spot, strike, time_to_expiry, 0.05, volatility, option_type
                )
                gamma_val = gamma(
                    spot, strike, time_to_expiry, 0.05, volatility
                )
                vega_val = vega(
                    spot, strike, time_to_expiry, 0.05, volatility
                )
                theta_val = theta(
                    spot, strike, time_to_expiry, 0.05, volatility, option_type
                )
                
                deltas.append(delta_val)
                gammas.append(gamma_val)
                vegas.append(vega_val)
                thetas.append(theta_val)
            
            greeks_data[f'{option_type}_delta'] = deltas
            greeks_data[f'{option_type}_gamma'] = gammas
            greeks_data[f'{option_type}_vega'] = vegas
            greeks_data[f'{option_type}_theta'] = thetas
        
        df = pd.DataFrame(greeks_data)
        
        # Create subplots for Greeks
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Delta', 'Gamma', 'Vega', 'Theta'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Delta plot
        fig.add_trace(
            go.Scatter(x=df['spot_price'], y=df['call_delta'], 
                      name='Call Delta', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['spot_price'], y=df['put_delta'], 
                      name='Put Delta', line=dict(color='red')),
            row=1, col=1
        )
        
        # Gamma plot (same for calls and puts)
        fig.add_trace(
            go.Scatter(x=df['spot_price'], y=df['call_gamma'], 
                      name='Gamma', line=dict(color='green')),
            row=1, col=2
        )
        
        # Vega plot (same for calls and puts)
        fig.add_trace(
            go.Scatter(x=df['spot_price'], y=df['call_vega'], 
                      name='Vega', line=dict(color='purple')),
            row=2, col=1
        )
        
        # Theta plot
        fig.add_trace(
            go.Scatter(x=df['spot_price'], y=df['call_theta'], 
                      name='Call Theta', line=dict(color='orange')),
            row=2, col=2
        )
        fig.add_trace(
            go.Scatter(x=df['spot_price'], y=df['put_theta'], 
                      name='Put Theta', line=dict(color='brown')),
            row=2, col=2
        )
        
        # Add vertical line for current price
        for row in range(1, 3):
            for col in range(1, 3):
                fig.add_vline(x=current_price, line_dash="dash", 
                            line_color="black", row=row, col=col)
        
        fig.update_layout(
            title='Greeks Analysis',
            height=600,
            showlegend=True
        )
        
        return fig

    def run(self):
        """Main dashboard application"""
        
        st.title("Volatility Surface Dashboard")
        st.markdown("Professional options analysis with interactive surfaces")
        
        # Sidebar for inputs
        with st.sidebar:
            st.header("Parameters")
            
            # Ticker input
            ticker = st.text_input(
                "Enter Ticker Symbol", 
                value="AAPL",
                help="Enter a valid stock ticker symbol"
            ).upper()
            
            # Risk-free rate
            risk_free_rate = st.number_input(
                "Risk-Free Rate (%)", 
                min_value=0.0, 
                max_value=10.0, 
                value=5.0,
                step=0.1
            ) / 100
            
            # Greeks calculation parameters
            st.subheader("Greeks Calculator")
            strike_price = st.number_input(
                "Strike Price ($)", 
                min_value=1.0, 
                value=150.0,
                step=1.0
            )
            
            days_to_expiry = st.number_input(
                "Days to Expiry", 
                min_value=1, 
                max_value=365, 
                value=30,
                step=1
            )
            
            implied_vol = st.number_input(
                "Implied Volatility (%)", 
                min_value=1.0, 
                max_value=200.0, 
                value=25.0,
                step=1.0
            ) / 100
            
            calculate_button = st.button("Calculate", type="primary")
        
        if calculate_button and ticker:
            with st.spinner(f"Fetching data for {ticker}..."):
                hist, current_price, options_df = self.fetch_stock_data(ticker)
                
                if hist is None:
                    st.error(f"Could not fetch data for {ticker}")
                    return
                
                # Display current price
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}")
                with col2:
                    change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                    st.metric("Daily Change", f"${change:.2f}", f"{change/hist['Close'].iloc[-2]*100:.2f}%")
                with col3:
                    volatility = hist['Close'].pct_change().std() * np.sqrt(252)
                    st.metric("Historical Volatility", f"{volatility:.2%}")
                
                # Calculate implied volatility if options data available
                if options_df is not None:
                    with st.spinner("Calculating implied volatilities..."):
                        iv_data = self.calculate_implied_volatility(options_df, current_price, risk_free_rate)
                        
                        if iv_data is not None and not iv_data.empty:
                            # Create tabs for different views
                            tab1, tab2, tab3, tab4 = st.tabs([
                                "Volatility Surface", 
                                "Greeks Analysis", 
                                "Options Data", 
                                "Price Chart"
                            ])
                            
                            with tab1:
                                st.subheader("Interactive Volatility Surface")
                                surface_fig = self.create_volatility_surface(iv_data)
                                if surface_fig:
                                    st.plotly_chart(surface_fig, use_container_width=True)
                                else:
                                    st.warning("Insufficient data to create volatility surface")
                            
                            with tab2:
                                st.subheader("Greeks Analysis")
                                
                                # Calculate Greeks for specified parameters
                                time_to_expiry = days_to_expiry / 365.0
                                greeks = self.calculate_all_greeks(
                                    current_price, strike_price, time_to_expiry, 
                                    implied_vol, risk_free_rate
                                )
                                
                                if greeks:
                                    # Display Greeks table
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("**Call Option Greeks**")
                                        call_data = greeks['call']
                                        greeks_df_call = pd.DataFrame([
                                            ['Price', f"${call_data['price']:.4f}"],
                                            ['Delta', f"{call_data['delta']:.4f}"],
                                            ['Gamma', f"{call_data['gamma']:.4f}"],
                                            ['Theta', f"{call_data['theta']:.4f}"],
                                            ['Vega', f"{call_data['vega']:.4f}"],
                                            ['Rho', f"{call_data['rho']:.4f}"]
                                        ], columns=['Greek', 'Value'])
                                        st.dataframe(greeks_df_call, hide_index=True)
                                    
                                    with col2:
                                        st.markdown("**Put Option Greeks**")
                                        put_data = greeks['put']
                                        greeks_df_put = pd.DataFrame([
                                            ['Price', f"${put_data['price']:.4f}"],
                                            ['Delta', f"{put_data['delta']:.4f}"],
                                            ['Gamma', f"{put_data['gamma']:.4f}"],
                                            ['Theta', f"{put_data['theta']:.4f}"],
                                            ['Vega', f"{put_data['vega']:.4f}"],
                                            ['Rho', f"{put_data['rho']:.4f}"]
                                        ], columns=['Greek', 'Value'])
                                        st.dataframe(greeks_df_put, hide_index=True)
                                    
                                    # Greeks visualization
                                    st.subheader("Greeks vs Spot Price")
                                    greeks_fig = self.create_greeks_visualization(
                                        current_price, strike_price, time_to_expiry, implied_vol
                                    )
                                    st.plotly_chart(greeks_fig, use_container_width=True)
                            
                            with tab3:
                                st.subheader("Options Chain Data")
                                
                                # Filter and display options data
                                display_cols = ['strike', 'expiry', 'time_to_expiry', 
                                              'implied_volatility', 'option_type', 'market_price']
                                
                                if not iv_data.empty:
                                    # Sort by expiry and strike
                                    iv_display = iv_data[display_cols].sort_values(['expiry', 'strike'])
                                    iv_display['implied_volatility'] = iv_display['implied_volatility'].apply(lambda x: f"{x:.2%}")
                                    iv_display['market_price'] = iv_display['market_price'].apply(lambda x: f"${x:.2f}")
                                    iv_display['time_to_expiry'] = iv_display['time_to_expiry'].apply(lambda x: f"{x:.3f}")
                                    
                                    st.dataframe(iv_display, use_container_width=True, hide_index=True)
                                else:
                                    st.warning("No valid implied volatility data found")
                            
                            with tab4:
                                st.subheader("Stock Price Chart")
                                
                                # Create price chart
                                price_fig = go.Figure()
                                price_fig.add_trace(
                                    go.Scatter(
                                        x=hist.index,
                                        y=hist['Close'],
                                        mode='lines',
                                        name='Close Price',
                                        line=dict(color='blue')
                                    )
                                )
                                
                                price_fig.update_layout(
                                    title=f'{ticker} Stock Price',
                                    xaxis_title='Date',
                                    yaxis_title='Price ($)',
                                    height=400
                                )
                                
                                st.plotly_chart(price_fig, use_container_width=True)
                        else:
                            st.warning("No valid options data found for volatility surface")
                else:
                    st.warning("No options data available for this ticker")


if __name__ == "__main__":
    dashboard = MinimalDashboard()
    dashboard.run()

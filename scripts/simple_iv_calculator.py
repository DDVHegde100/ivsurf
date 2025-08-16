#!/usr/bin/env python3
"""
Simple IV Calculator - Single Option Analysis

Interactive tool for analyzing individual option contracts with real-time data,
implied volatility calculation, and comprehensive Greeks analysis.

Run: streamlit run scripts/simple_iv_calculator.py
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_data import OptionsDataFetcher, get_stock_price, get_single_option_quote
from core.black_scholes import black_scholes_price, implied_volatility, option_value_decomposition
from core.greeks import all_greeks


def main():
    st.set_page_config(
        page_title="IV Calculator - Single Option",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Single Option IV Calculator")
    st.markdown("**Real-time options analysis with implied volatility and Greeks**")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Option Selection")
        
        # Ticker input
        ticker = st.text_input("Stock Ticker", value="AAPL", help="Enter a valid stock ticker").upper()
        
        # Fetch stock data button
        if st.button("🔄 Fetch Options Data"):
            if ticker:
                with st.spinner("Fetching options data..."):
                    try:
                        fetcher = OptionsDataFetcher()
                        
                        # Get stock info
                        stock_info = fetcher.get_stock_info(ticker)
                        st.session_state['stock_info'] = stock_info
                        
                        # Get options chain
                        options_df = fetcher.get_options_chain(ticker, max_expiries=8)
                        st.session_state['options_df'] = options_df
                        
                        st.success(f"✅ Loaded {len(options_df)} options for {ticker}")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Display stock info if available
        if 'stock_info' in st.session_state:
            info = st.session_state['stock_info']
            st.subheader(f"{info['symbol']} - {info['company_name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Price", f"${info['current_price']:.2f}")
                st.metric("Volume", f"{info['volume']:,}")
            with col2:
                change_color = "normal" if info['change'] >= 0 else "inverse"
                st.metric("Change", f"${info['change']:.2f}", f"{info['change_percent']:.2f}%")
                if info['beta']:
                    st.metric("Beta", f"{info['beta']:.2f}")
        
        # Option selection (if data loaded)
        if 'options_df' in st.session_state:
            st.subheader("Select Option Contract")
            
            df = st.session_state['options_df']
            
            # Option type
            option_type = st.selectbox("Option Type", ['call', 'put'])
            
            # Filter by option type
            filtered_df = df[df['optionType'] == option_type].copy()
            
            # Expiration date
            expiry_dates = sorted(filtered_df['expiration'].unique())
            selected_expiry = st.selectbox("Expiration Date", expiry_dates)
            
            # Filter by expiry
            expiry_df = filtered_df[filtered_df['expiration'] == selected_expiry].copy()
            
            # Strike price
            strikes = sorted(expiry_df['strike'].unique())
            selected_strike = st.selectbox("Strike Price", strikes)
            
            # Get the selected option
            selected_option = expiry_df[expiry_df['strike'] == selected_strike].iloc[0]
            st.session_state['selected_option'] = selected_option
    
    # Main content area
    if 'selected_option' in st.session_state and 'stock_info' in st.session_state:
        option = st.session_state['selected_option']
        stock_info = st.session_state['stock_info']
        
        # Create tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Option Details", "🧮 IV Analysis", "📊 Greeks", "📈 Sensitivity"])
        
        with tab1:
            st.header("Option Contract Details")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Contract Info")
                st.write(f"**Symbol:** {stock_info['symbol']}")
                st.write(f"**Type:** {option['optionType'].title()}")
                st.write(f"**Strike:** ${option['strike']:.2f}")
                st.write(f"**Expiry:** {option['expiration']}")
                st.write(f"**Days to Expiry:** {option['daysToExpiry']}")
            
            with col2:
                st.subheader("Market Data")
                st.metric("Last Price", f"${option['lastPrice']:.3f}")
                st.metric("Bid", f"${option['bid']:.3f}")
                st.metric("Ask", f"${option['ask']:.3f}")
                st.metric("Mid Price", f"${option['midPrice']:.3f}")
                st.metric("Spread", f"${option['bidAskSpread']:.3f}")
            
            with col3:
                st.subheader("Volume & Interest")
                st.metric("Volume", f"{option['volume']:,}")
                st.metric("Open Interest", f"{option['openInterest']:,}")
                if 'impliedVolatility' in option and option['impliedVolatility'] > 0:
                    st.metric("Yahoo IV", f"{option['impliedVolatility']*100:.1f}%")
        
        with tab2:
            st.header("Implied Volatility Analysis")
            
            # Calculate IV using our engine
            try:
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05  # Assume 5% risk-free rate
                
                # Use mid price for IV calculation
                market_price = option['midPrice']
                
                if market_price > 0 and T > 0:
                    # Calculate IV using both methods
                    iv_newton = implied_volatility(market_price, S, K, T, r, option['optionType'], method='newton')
                    iv_brent = implied_volatility(market_price, S, K, T, r, option['optionType'], method='brent')
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("IV Calculation Results")
                        
                        if not np.isnan(iv_newton):
                            st.metric("Newton-Raphson IV", f"{iv_newton*100:.2f}%")
                        else:
                            st.warning("Newton-Raphson failed to converge")
                        
                        if not np.isnan(iv_brent):
                            st.metric("Brent Method IV", f"{iv_brent*100:.2f}%")
                        else:
                            st.warning("Brent method failed to converge")
                        
                        # Use best available IV for further analysis
                        best_iv = iv_newton if not np.isnan(iv_newton) else iv_brent
                        
                        if not np.isnan(best_iv):
                            st.session_state['calculated_iv'] = best_iv
                            
                            # Value decomposition
                            decomp = option_value_decomposition(S, K, T, r, best_iv, option['optionType'])
                            
                            st.subheader("Value Breakdown")
                            st.metric("Theoretical Price", f"${decomp['total_value']:.3f}")
                            st.metric("Intrinsic Value", f"${decomp['intrinsic_value']:.3f}")
                            st.metric("Time Value", f"${decomp['time_value']:.3f}")
                            
                            # Price comparison
                            price_diff = market_price - decomp['total_value']
                            st.metric("Market vs Theoretical", 
                                     f"${price_diff:.3f}",
                                     f"{price_diff/decomp['total_value']*100:.1f}%")
                    
                    with col2:
                        st.subheader("IV Convergence Visualization")
                        
                        if not np.isnan(best_iv):
                            # Create volatility smile visualization
                            strikes_range = np.linspace(S*0.8, S*1.2, 20)
                            ivs_for_smile = []
                            
                            for strike_test in strikes_range:
                                try:
                                    theo_price = black_scholes_price(S, strike_test, T, r, best_iv, option['optionType'])
                                    if theo_price > 0.01:  # Only calculate IV for meaningful prices
                                        test_iv = implied_volatility(theo_price, S, strike_test, T, r, option['optionType'])
                                        ivs_for_smile.append(test_iv if not np.isnan(test_iv) else None)
                                    else:
                                        ivs_for_smile.append(None)
                                except:
                                    ivs_for_smile.append(None)
                            
                            # Plot volatility smile
                            fig = go.Figure()
                            
                            valid_data = [(s, iv) for s, iv in zip(strikes_range, ivs_for_smile) if iv is not None]
                            if valid_data:
                                strikes_valid, ivs_valid = zip(*valid_data)
                                
                                fig.add_trace(go.Scatter(
                                    x=strikes_valid,
                                    y=[iv*100 for iv in ivs_valid],
                                    mode='lines+markers',
                                    name='Theoretical IV Smile',
                                    line=dict(color='blue')
                                ))
                            
                            # Highlight selected strike
                            fig.add_trace(go.Scatter(
                                x=[K],
                                y=[best_iv*100],
                                mode='markers',
                                name='Selected Option',
                                marker=dict(color='red', size=12)
                            ))
                            
                            fig.update_layout(
                                title="Theoretical Volatility Smile",
                                xaxis_title="Strike Price",
                                yaxis_title="Implied Volatility (%)",
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.warning("Cannot calculate IV: Invalid price or expiry data")
                    
            except Exception as e:
                st.error(f"IV calculation error: {str(e)}")
        
        with tab3:
            st.header("Greeks Analysis")
            
            if 'calculated_iv' in st.session_state:
                iv = st.session_state['calculated_iv']
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05
                
                try:
                    greeks = all_greeks(S, K, T, r, iv, option['optionType'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Risk Greeks")
                        st.metric("Delta", f"{greeks['delta']:.4f}", 
                                 help="Price sensitivity to $1 change in underlying")
                        st.metric("Gamma", f"{greeks['gamma']:.6f}",
                                 help="Delta sensitivity to $1 change in underlying") 
                        st.metric("Vega", f"{greeks['vega']:.4f}",
                                 help="Price sensitivity to 1% change in volatility")
                    
                    with col2:
                        st.subheader("Time & Rate Greeks")
                        st.metric("Theta", f"{greeks['theta']:.4f}",
                                 help="Price decay per day")
                        st.metric("Rho", f"{greeks['rho']:.4f}",
                                 help="Price sensitivity to 1% change in interest rate")
                    
                    # Greeks visualization
                    st.subheader("Greeks Sensitivity Chart")
                    
                    spot_range = np.linspace(S*0.8, S*1.2, 50)
                    deltas, gammas, vegas = [], [], []
                    
                    for spot_test in spot_range:
                        test_greeks = all_greeks(spot_test, K, T, r, iv, option['optionType'])
                        deltas.append(test_greeks['delta'])
                        gammas.append(test_greeks['gamma'])
                        vegas.append(test_greeks['vega'])
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(x=spot_range, y=deltas, name='Delta', line=dict(color='blue')))
                    fig.add_trace(go.Scatter(x=spot_range, y=gammas, name='Gamma', yaxis='y2', line=dict(color='red')))
                    
                    fig.add_vline(x=S, line_dash="dash", line_color="gray", 
                                 annotation_text="Current Price")
                    
                    fig.update_layout(
                        title="Delta and Gamma vs Spot Price",
                        xaxis_title="Spot Price",
                        yaxis_title="Delta",
                        yaxis2=dict(title="Gamma", overlaying="y", side="right"),
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Greeks calculation error: {str(e)}")
            
            else:
                st.warning("Calculate IV first to display Greeks")
        
        with tab4:
            st.header("Sensitivity Analysis")
            
            if 'calculated_iv' in st.session_state:
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05
                iv = st.session_state['calculated_iv']
                
                # Interactive sensitivity controls
                col1, col2 = st.columns(2)
                
                with col1:
                    spot_change = st.slider("Spot Price Change (%)", -20, 20, 0, 1)
                    vol_change = st.slider("Volatility Change (%)", -50, 50, 0, 5)
                
                with col2:
                    time_decay_days = st.slider("Days Forward", 0, min(30, option['daysToExpiry']), 0)
                    rate_change = st.slider("Rate Change (%)", -2.0, 2.0, 0.0, 0.1)
                
                # Calculate scenario
                new_S = S * (1 + spot_change/100)
                new_iv = iv * (1 + vol_change/100)
                new_T = max(0.001, T - time_decay_days/365)
                new_r = r + rate_change/100
                
                try:
                    original_price = black_scholes_price(S, K, T, r, iv, option['optionType'])
                    scenario_price = black_scholes_price(new_S, K, new_T, new_r, new_iv, option['optionType'])
                    
                    price_change = scenario_price - original_price
                    price_change_pct = price_change / original_price * 100
                    
                    st.subheader("Scenario Analysis Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Original Price", f"${original_price:.3f}")
                        st.metric("Scenario Price", f"${scenario_price:.3f}")
                    
                    with col2:
                        st.metric("Price Change", f"${price_change:.3f}", f"{price_change_pct:.1f}%")
                        
                        # P&L calculation
                        contracts = st.number_input("Number of Contracts", min_value=1, value=1, step=1)
                        pnl = price_change * contracts * 100  # Options are per 100 shares
                        st.metric("P&L", f"${pnl:,.0f}")
                    
                    with col3:
                        st.write("**Scenario Parameters:**")
                        st.write(f"Spot: ${new_S:.2f} ({spot_change:+.1f}%)")
                        st.write(f"Vol: {new_iv*100:.1f}% ({vol_change:+}%)")
                        st.write(f"Days: -{time_decay_days}")
                        st.write(f"Rate: {new_r*100:.1f}% ({rate_change:+.1f}%)")
                    
                except Exception as e:
                    st.error(f"Scenario calculation error: {str(e)}")
            
            else:
                st.warning("Calculate IV first to perform sensitivity analysis")
    
    else:
        # Instructions for new users
        st.info("👈 Use the sidebar to fetch options data and select a contract to analyze")
        
        st.markdown("""
        ### How to Use This Calculator:
        
        1. **Enter a stock ticker** (e.g., AAPL, MSFT, TSLA)
        2. **Click "Fetch Options Data"** to load real-time options
        3. **Select an option contract** using the dropdown menus
        4. **Explore the analysis tabs:**
           - **Option Details**: Contract specifications and market data
           - **IV Analysis**: Implied volatility calculation and comparison
           - **Greeks**: Risk sensitivities (Delta, Gamma, Vega, Theta, Rho)
           - **Sensitivity**: Scenario analysis and P&L modeling
        
        ### Features:
        - ✅ Real-time options data from Yahoo Finance
        - ✅ Advanced Newton-Raphson implied volatility calculation  
        - ✅ Complete Greeks analysis with visualizations
        - ✅ Interactive sensitivity analysis and scenario modeling
        - ✅ Value decomposition (intrinsic vs time value)
        - ✅ Market vs theoretical price comparison
        """)


if __name__ == "__main__":
    main()

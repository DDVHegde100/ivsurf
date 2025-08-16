import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.fetch_data import get_options_chain
from core.black_scholes import black_scholes_price, implied_volatility, option_value_decomposition
from core.greeks import all_greeks
from core.interpolation import interpolate_surface
from visuals.plot_surface import plot_vol_surface

st.set_page_config(page_title="Volatility Surface Explorer", layout="wide")
st.title("📈 Volatility Surface Explorer")
st.markdown("**Enhanced Black-Scholes Analysis & Implied Volatility Surface Modeling**")

# Sidebar controls
with st.sidebar:
    st.header("Parameters")
    ticker = st.text_input("Stock Ticker", value="AAPL", help="Enter a valid stock ticker")
    
    st.subheader("Black-Scholes Test")
    test_spot = st.number_input("Spot Price", value=100.0, min_value=1.0)
    test_strike = st.number_input("Strike Price", value=100.0, min_value=1.0) 
    test_time = st.number_input("Time to Expiry (years)", value=0.25, min_value=0.01, max_value=2.0)
    test_rate = st.number_input("Risk-free Rate", value=0.05, min_value=-0.1, max_value=0.2)
    test_vol = st.number_input("Volatility", value=0.20, min_value=0.01, max_value=2.0)
    test_option_type = st.selectbox("Option Type", ["call", "put"])

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["🔧 Black-Scholes Calculator", "📊 Options Chain Analysis", "🏔️ Volatility Surface"])

with tab1:
    st.header("Black-Scholes Pricing & Greeks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Option Valuation")
        try:
            # Calculate option price and value decomposition
            price = black_scholes_price(test_spot, test_strike, test_time, test_rate, test_vol, test_option_type)
            decomp = option_value_decomposition(test_spot, test_strike, test_time, test_rate, test_vol, test_option_type)
            
            st.metric("Option Price", f"${price:.4f}")
            st.metric("Intrinsic Value", f"${decomp['intrinsic_value']:.4f}")
            st.metric("Time Value", f"${decomp['time_value']:.4f}")
            
            # Test implied volatility round-trip
            implied_vol = implied_volatility(price, test_spot, test_strike, test_time, test_rate, test_option_type)
            st.metric("Implied Vol (round-trip)", f"{implied_vol:.4f}")
            
        except Exception as e:
            st.error(f"Calculation error: {e}")
    
    with col2:
        st.subheader("Greeks Analysis")
        try:
            greeks = all_greeks(test_spot, test_strike, test_time, test_rate, test_vol, test_option_type)
            
            st.metric("Delta", f"{greeks['delta']:.4f}")
            st.metric("Gamma", f"{greeks['gamma']:.6f}") 
            st.metric("Vega", f"{greeks['vega']:.4f}")
            st.metric("Theta", f"{greeks['theta']:.4f}")
            st.metric("Rho", f"{greeks['rho']:.4f}")
            
        except Exception as e:
            st.error(f"Greeks calculation error: {e}")
    
    # Sensitivity analysis
    st.subheader("Sensitivity Analysis")
    
    sens_type = st.selectbox("Analysis Type", ["Spot vs Price", "Volatility vs Price", "Time vs Price"])
    
    if sens_type == "Spot vs Price":
        spot_range = np.linspace(test_spot * 0.8, test_spot * 1.2, 50)
        prices = [black_scholes_price(s, test_strike, test_time, test_rate, test_vol, test_option_type) for s in spot_range]
        deltas = [all_greeks(s, test_strike, test_time, test_rate, test_vol, test_option_type)['delta'] for s in spot_range]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spot_range, y=prices, name="Option Price", line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=spot_range, y=deltas, name="Delta", line=dict(color='red'), yaxis="y2"))
        fig.update_layout(
            title="Price & Delta vs Spot Price",
            xaxis_title="Spot Price",
            yaxis_title="Option Price",
            yaxis2=dict(title="Delta", overlaying="y", side="right")
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Live Options Chain Analysis")
    
    if st.button("Fetch Options Data"):
        with st.spinner("Fetching options data..."):
            try:
                # Get options chain
                df = get_options_chain(ticker)
                
                if df.empty:
                    st.warning("No options data found for this ticker")
                else:
                    # Get current stock price
                    stock = yf.Ticker(ticker)
                    spot_price = stock.history(period="1d")['Close'].iloc[-1]
                    
                    st.success(f"Current {ticker} price: ${spot_price:.2f}")
                    st.write(f"Found {len(df)} option contracts")
                    
                    # Calculate implied volatilities and Greeks
                    r = 0.01  # Assumed risk-free rate
                    df_analysis = []
                    
                    for _, row in df.iterrows():
                        try:
                            T = (pd.to_datetime(row['expiration']) - pd.Timestamp.today()).days / 365
                            if T <= 0:
                                continue
                                
                            # Calculate implied vol
                            iv = implied_volatility(
                                row['lastPrice'], spot_price, row['strike'], 
                                T, r, row['optionType']
                            )
                            
                            if not np.isnan(iv):
                                # Calculate Greeks
                                greeks = all_greeks(spot_price, row['strike'], T, r, iv, row['optionType'])
                                
                                df_analysis.append({
                                    'strike': row['strike'],
                                    'expiry': T,
                                    'option_type': row['optionType'],
                                    'price': row['lastPrice'],
                                    'implied_vol': iv,
                                    'delta': greeks['delta'],
                                    'gamma': greeks['gamma'],
                                    'vega': greeks['vega'],
                                    'theta': greeks['theta']
                                })
                        except:
                            continue
                    
                    if df_analysis:
                        analysis_df = pd.DataFrame(df_analysis)
                        st.write("Options Analysis Summary:")
                        st.dataframe(analysis_df.round(4))
                        
                        # Store in session state for surface plotting
                        st.session_state['analysis_df'] = analysis_df
                        st.success("Data ready for volatility surface analysis!")
                    else:
                        st.warning("Could not calculate implied volatilities for any options")
                        
            except Exception as e:
                st.error(f"Error fetching options data: {e}")

with tab3:
    st.header("3D Volatility Surface")
    
    if 'analysis_df' in st.session_state:
        df = st.session_state['analysis_df']
        
        # Filter for calls only (for cleaner surface)
        calls_df = df[df['option_type'] == 'call'].copy()
        
        if len(calls_df) > 5:
            strikes = calls_df['strike'].values
            expiries = calls_df['expiry'].values  
            ivs = calls_df['implied_vol'].values
            
            try:
                # Create interpolated surface
                grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs)
                
                # Plot surface
                fig = plot_vol_surface(strikes, expiries, ivs, grid_x, grid_y, grid_z)
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                # Heatmap view
                st.subheader("Implied Volatility Heatmap")
                pivot_df = calls_df.pivot_table(index='expiry', columns='strike', values='implied_vol')
                
                fig_heatmap = px.imshow(
                    pivot_df, 
                    aspect="auto",
                    color_continuous_scale="Viridis",
                    title="Implied Volatility by Strike & Expiry"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
            except Exception as e:
                st.error(f"Surface plotting error: {e}")
        else:
            st.warning("Need more data points for surface interpolation")
    else:
        st.info("Please fetch options data first in the 'Options Chain Analysis' tab")

# Footer
st.markdown("---")
st.markdown("*Enhanced Black-Scholes implementation with comprehensive Greeks and robust implied volatility calculation*")

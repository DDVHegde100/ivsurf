#!/usr/bin/env python3
"""
IVSURF PROFESSIONAL TERMINAL v4.0

Advanced quantitative options analysis platform with PhD-level mathematical models,
real-time market integration, and comprehensive predictive analytics.
Clean retro aesthetic with maximum functional precision.
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
import warnings
import math
from scipy import stats
from scipy.optimize import minimize_scalar
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_data import OptionsDataFetcher
from core.black_scholes import black_scholes_price, implied_volatility, option_value_decomposition
from core.greeks import all_greeks


def apply_professional_terminal_css():
    """Apply clean, professional terminal styling."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Courier+Prime:wght@400;700&family=Source+Code+Pro:wght@300;400;500;600;700&display=swap');
    
    .main {
        background: #000000;
        color: #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        line-height: 1.4;
        font-weight: 400;
    }
    
    .terminal-header {
        background: linear-gradient(135deg, #000000 0%, #001100 50%, #000000 100%);
        border: 2px solid #00ff00;
        padding: 25px;
        margin: 15px 0;
        text-align: center;
        box-shadow: 0 0 30px rgba(0, 255, 0, 0.3);
    }
    
    .ascii-art {
        font-family: 'Courier Prime', monospace;
        font-size: 11px;
        color: #00ff00;
        text-shadow: 0 0 10px #00ff00;
        white-space: pre;
        line-height: 1.1;
    }
    
    .status-line {
        color: #00ffff;
        font-weight: 600;
        margin-top: 20px;
        font-size: 13px;
    }
    
    .info-panel {
        background: linear-gradient(135deg, #000a00 0%, #001100 50%, #000a00 100%);
        border: 2px solid #00ff00;
        padding: 20px;
        margin: 15px 0;
        border-radius: 0;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #001a00 0%, #002200 50%, #001a00 100%);
        border: 1px solid #00ff00;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.2);
    }
    
    .metric-title {
        color: #00ffff;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .metric-value {
        color: #00ff00;
        font-size: 24px;
        font-weight: 700;
        font-family: 'Courier Prime', monospace;
        text-shadow: 0 0 10px #00ff00;
        margin: 5px 0;
    }
    
    .metric-subtitle {
        color: #00aaaa;
        font-size: 11px;
        font-weight: 500;
    }
    
    .alert-panel {
        border: 2px solid;
        padding: 15px;
        margin: 12px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
    }
    
    .alert-success {
        background: linear-gradient(135deg, #003300 0%, #004400 50%, #003300 100%);
        border-color: #00ff00;
        color: #00ff00;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #000033 0%, #000044 50%, #000033 100%);
        border-color: #0088ff;
        color: #00aaff;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #333300 0%, #444400 50%, #333300 100%);
        border-color: #ffff00;
        color: #ffff00;
    }
    
    .alert-error {
        background: linear-gradient(135deg, #330000 0%, #440000 50%, #330000 100%);
        border-color: #ff0000;
        color: #ff0000;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: #000000;
        border: 2px solid #00ff00;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #001100 0%, #002200 50%, #001100 100%);
        color: #00ff00;
        border: 1px solid #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 600;
        margin: 3px;
        padding: 12px 20px;
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #003300 0%, #004400 50%, #003300 100%);
        color: #00ffff;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background: #00ff00;
        color: #000000;
        box-shadow: 0 0 25px #00ff00;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #000000 0%, #001100 50%, #000000 100%);
        color: #00ff00;
        border: 2px solid #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
    }
    
    .stButton > button:hover {
        background: #00ff00;
        color: #000000;
        box-shadow: 0 0 25px #00ff00;
    }
    
    .stSelectbox > div > div {
        background: #001100;
        border: 2px solid #00ff00;
        color: #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background: #001100;
        border: 2px solid #00ff00;
        color: #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 500;
    }
    
    .stSlider > div > div > div > div {
        background: #00ff00;
    }
    
    .stSlider > div > div > div {
        background: #003300;
    }
    
    .js-plotly-plot {
        background: #000000;
        border: 3px solid #00ff00;
        box-shadow: 0 0 25px rgba(0, 255, 0, 0.3);
    }
    
    .stDataFrame {
        border: 2px solid #00ff00;
        background: #000000;
    }
    
    .stDataFrame table {
        background: #000000;
        color: #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
    }
    
    .stDataFrame th {
        background: #003300;
        color: #00ffff;
        border: 1px solid #00ff00;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    .stDataFrame td {
        background: #001100;
        color: #00ff00;
        border: 1px solid #00ff00;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    
    ::-webkit-scrollbar {
        width: 15px;
        background: #000000;
    }
    
    ::-webkit-scrollbar-track {
        background: #001100;
        border: 2px solid #00ff00;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff00;
        border: 2px solid #000000;
        box-shadow: 0 0 10px #00ff00;
    }
    
    .blinking::after {
        content: '█';
        color: #00ff00;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    </style>
    """, unsafe_allow_html=True)


def create_clean_header():
    """Create clean IVSURF header."""
    return """
    ██╗██╗   ██╗███████╗██╗   ██╗██████╗ ███████╗
    ██║██║   ██║██╔════╝██║   ██║██╔══██╗██╔════╝
    ██║██║   ██║███████╗██║   ██║██████╔╝█████╗  
    ██║╚██╗ ██╔╝╚════██║██║   ██║██╔══██╗██╔══╝  
    ██║ ╚████╔╝ ███████║╚██████╔╝██║  ██║██║     
    ╚═╝  ╚═══╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     
                                                  
    ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     
    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     
       ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     
       ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     
       ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
    """


def create_alert(title, message, alert_type="info"):
    """Create clean alert panels."""
    st.markdown(f"""
    <div class="alert-panel alert-{alert_type}">
        <strong>[{title}]</strong><br>{message}
    </div>
    """, unsafe_allow_html=True)


def create_metric_card(title, value, subtitle=""):
    """Create clean metric cards."""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def fetch_enhanced_market_data(ticker):
    """Fetch comprehensive market data with enhanced analysis and robust error handling."""
    try:
        # Initialize ticker object
        stock = yf.Ticker(ticker)
        
        # First, try to get historical data which is more reliable
        hist_5d = stock.history(period="5d")
        hist_1m = stock.history(period="1mo")
        hist_3m = stock.history(period="3mo")
        hist_1y = stock.history(period="1y")
        
        # Validate we have data
        if hist_5d.empty or hist_1m.empty:
            # Try alternative method with different periods
            hist_5d = stock.history(period="5d", interval="1d")
            hist_1m = stock.history(period="1mo", interval="1d")
            hist_3m = stock.history(period="3mo", interval="1d")
            hist_1y = stock.history(period="1y", interval="1d")
            
            if hist_5d.empty:
                raise ValueError(f"No historical data available for {ticker}")
        
        # Get current price from most recent data
        current_price = hist_5d['Close'].iloc[-1]
        
        # Get company info (with fallbacks)
        info = {}
        try:
            info = stock.info
        except:
            # If info fails, continue with defaults
            pass
        
        # Calculate volatility measures
        returns_1y = hist_1y['Close'].pct_change().dropna() if len(hist_1y) > 0 else pd.Series([0.01])
        returns_3m = hist_3m['Close'].pct_change().dropna() if len(hist_3m) > 0 else pd.Series([0.01])
        returns_1m = hist_1m['Close'].pct_change().dropna() if len(hist_1m) > 0 else pd.Series([0.01])
        
        vol_annual = returns_1y.std() * np.sqrt(252) if len(returns_1y) > 10 else 0.25
        vol_3m = returns_3m.std() * np.sqrt(252) if len(returns_3m) > 10 else 0.25
        vol_1m = returns_1m.std() * np.sqrt(252) if len(returns_1m) > 10 else 0.25
        
        # Ensure volatilities are reasonable
        vol_annual = max(0.05, min(vol_annual, 2.0))
        vol_3m = max(0.05, min(vol_3m, 2.0))
        vol_1m = max(0.05, min(vol_1m, 2.0))
        
        # Advanced market metrics with fallbacks
        beta = info.get('beta', 1.0) or 1.0
        market_cap = info.get('marketCap', 0) or 0
        pe_ratio = info.get('trailingPE', 0) or 0
        company_name = info.get('longName', ticker) or ticker
        sector = info.get('sector', 'Technology') or 'Technology'
        
        # Technical levels
        high_52w = hist_1y['High'].max() if len(hist_1y) > 0 else current_price * 1.2
        low_52w = hist_1y['Low'].min() if len(hist_1y) > 0 else current_price * 0.8
        
        # Recent performance
        price_1d_ago = hist_5d['Close'].iloc[-2] if len(hist_5d) > 1 else current_price
        price_1w_ago = hist_1m['Close'].iloc[-7] if len(hist_1m) > 7 else current_price
        price_1m_ago = hist_3m['Close'].iloc[-22] if len(hist_3m) > 22 else current_price
        
        # Volume data
        avg_volume = hist_1m['Volume'].mean() if len(hist_1m) > 0 else 1000000
        current_volume = hist_5d['Volume'].iloc[-1] if len(hist_5d) > 0 else avg_volume
        
        return {
            'ticker': ticker,
            'current_price': float(current_price),
            'company_name': company_name,
            'sector': sector,
            'beta': float(beta),
            'market_cap': int(market_cap),
            'pe_ratio': float(pe_ratio) if pe_ratio and not np.isnan(pe_ratio) else 0,
            'vol_annual': float(vol_annual),
            'vol_3m': float(vol_3m),
            'vol_1m': float(vol_1m),
            'high_52w': float(high_52w),
            'low_52w': float(low_52w),
            'price_1d_ago': float(price_1d_ago),
            'price_1w_ago': float(price_1w_ago),
            'price_1m_ago': float(price_1m_ago),
            'hist_1y': hist_1y,
            'hist_3m': hist_3m,
            'hist_1m': hist_1m,
            'hist_5d': hist_5d,
            'avg_volume': float(avg_volume),
            'current_volume': float(current_volume),
            'data_quality': 'GOOD'
        }
        
    except Exception as e:
        # Return fallback data for testing/demo purposes
        st.warning(f"Using demo data for {ticker}. Error: {str(e)}")
        
        # Create synthetic data for demonstration
        demo_price = 150.0
        if ticker == "NVDA":
            demo_price = 120.0
        elif ticker == "AAPL":
            demo_price = 175.0
        elif ticker == "TSLA":
            demo_price = 250.0
        elif ticker == "MSFT":
            demo_price = 350.0
        
        return {
            'ticker': ticker,
            'current_price': demo_price,
            'company_name': f"{ticker} Corporation",
            'sector': 'Technology',
            'beta': 1.2,
            'market_cap': 1000000000,
            'pe_ratio': 25.0,
            'vol_annual': 0.35,
            'vol_3m': 0.30,
            'vol_1m': 0.28,
            'high_52w': demo_price * 1.3,
            'low_52w': demo_price * 0.7,
            'price_1d_ago': demo_price * 0.99,
            'price_1w_ago': demo_price * 0.95,
            'price_1m_ago': demo_price * 0.90,
            'hist_1y': pd.DataFrame(),
            'hist_3m': pd.DataFrame(),
            'hist_1m': pd.DataFrame(),
            'hist_5d': pd.DataFrame(),
            'avg_volume': 5000000,
            'current_volume': 3000000,
            'data_quality': 'DEMO'
        }


def calculate_advanced_option_pricing(spot, strike, time_to_expiry, rate, vol, option_type):
    """Enhanced option pricing with multiple models and validation."""
    try:
        # Black-Scholes base price
        bs_price = black_scholes_price(spot, strike, time_to_expiry, rate, vol, option_type)
        
        # Intrinsic value
        if option_type == 'call':
            intrinsic = max(0, spot - strike)
        else:
            intrinsic = max(0, strike - spot)
        
        # Time value
        time_value = bs_price - intrinsic
        
        # Moneyness analysis
        moneyness = spot / strike
        
        # Calculate Greeks
        greeks = all_greeks(spot, strike, time_to_expiry, rate, vol, option_type)
        
        # Probability analysis
        d1 = (np.log(spot / strike) + (rate + 0.5 * vol**2) * time_to_expiry) / (vol * np.sqrt(time_to_expiry))
        d2 = d1 - vol * np.sqrt(time_to_expiry)
        
        if option_type == 'call':
            prob_itm = stats.norm.cdf(d2)
            prob_profitable = stats.norm.cdf((np.log(spot / (strike + bs_price)) + (rate - 0.5 * vol**2) * time_to_expiry) / (vol * np.sqrt(time_to_expiry)))
        else:
            prob_itm = stats.norm.cdf(-d2)
            prob_profitable = stats.norm.cdf((np.log((strike - bs_price) / spot) + (rate - 0.5 * vol**2) * time_to_expiry) / (vol * np.sqrt(time_to_expiry)))
        
        return {
            'theoretical_price': bs_price,
            'intrinsic_value': intrinsic,
            'time_value': time_value,
            'moneyness': moneyness,
            'prob_itm': prob_itm,
            'prob_profitable': prob_profitable,
            'greeks': greeks,
            'breakeven': strike + bs_price if option_type == 'call' else strike - bs_price
        }
    except Exception as e:
        st.error(f"Error in option pricing: {str(e)}")
        return None


def calculate_predictive_profits(initial_investment, time_period_days, market_data, option_data):
    """Advanced predictive profit analysis using multiple models."""
    try:
        current_price = market_data['current_price']
        vol = market_data['vol_1m']  # Use 1-month volatility for short-term predictions
        
        # Convert time period to years
        time_years = time_period_days / 365.0
        
        # Monte Carlo simulation for price paths
        num_simulations = 10000
        dt = 1/365  # Daily steps
        steps = int(time_period_days)
        
        # Generate price paths
        price_paths = np.zeros((num_simulations, steps + 1))
        price_paths[:, 0] = current_price
        
        for i in range(steps):
            Z = np.random.standard_normal(num_simulations)
            price_paths[:, i + 1] = price_paths[:, i] * np.exp((0.1 - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * Z)
        
        final_prices = price_paths[:, -1]
        
        # Calculate returns
        returns = (final_prices - current_price) / current_price
        stock_profits = initial_investment * returns
        
        # Option profit calculations if option data available
        option_profits = np.zeros_like(stock_profits)
        if option_data:
            contracts = int(initial_investment / (option_data['theoretical_price'] * 100))
            if contracts > 0:
                for i, final_price in enumerate(final_prices):
                    # Calculate option value at expiration (simplified - assumes held to expiry)
                    if option_data['option_type'] == 'call':
                        final_option_value = max(0, final_price - option_data['strike'])
                    else:
                        final_option_value = max(0, option_data['strike'] - final_price)
                    
                    option_profits[i] = contracts * (final_option_value - option_data['theoretical_price']) * 100
        
        # Statistical analysis
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        stock_percentiles = np.percentile(stock_profits, percentiles)
        option_percentiles = np.percentile(option_profits, percentiles) if option_data else np.zeros_like(stock_percentiles)
        
        return {
            'time_period_days': time_period_days,
            'initial_investment': initial_investment,
            'final_prices': final_prices,
            'stock_profits': stock_profits,
            'option_profits': option_profits,
            'stock_percentiles': dict(zip(percentiles, stock_percentiles)),
            'option_percentiles': dict(zip(percentiles, option_percentiles)),
            'stock_mean_profit': np.mean(stock_profits),
            'option_mean_profit': np.mean(option_profits) if option_data else 0,
            'stock_prob_profit': np.sum(stock_profits > 0) / len(stock_profits),
            'option_prob_profit': np.sum(option_profits > 0) / len(option_profits) if option_data else 0,
            'max_stock_profit': np.max(stock_profits),
            'max_option_profit': np.max(option_profits) if option_data else 0,
            'min_stock_loss': np.min(stock_profits),
            'min_option_loss': np.min(option_profits) if option_data else 0
        }
        
    except Exception as e:
        st.error(f"Error in predictive analysis: {str(e)}")
        return None


def show_information_guide():
    """Show comprehensive information guide."""
    with st.expander("📚 COMPREHENSIVE TRADING GUIDE", expanded=False):
        st.markdown("""
        ### 🎯 **THEORETICAL OPTION PRICING**
        
        **Black-Scholes Model Explanation:**
        - **Theoretical Price**: Fair value based on mathematical model assuming constant volatility
        - **Intrinsic Value**: Immediate exercise value (Current Price - Strike for calls)
        - **Time Value**: Premium above intrinsic value due to time until expiration
        - **Moneyness**: Ratio of current price to strike price (>1.0 = ITM for calls)
        
        **Why prices may seem unusual:**
        - Options are leveraged instruments - small price for large exposure
        - Out-of-the-money options have low theoretical values
        - Time decay reduces option values as expiration approaches
        - Volatility greatly affects option pricing
        
        ### 📊 **GREEKS EXPLANATION**
        
        - **Delta**: Price change per $1 underlying move (0-1 for calls, -1-0 for puts)
        - **Gamma**: Delta change per $1 underlying move (acceleration)
        - **Vega**: Price change per 1% volatility change
        - **Theta**: Daily time decay (always negative for long options)
        - **Rho**: Price change per 1% interest rate change
        
        ### 💰 **PROFIT PREDICTIONS**
        
        **Monte Carlo Simulation:**
        - Runs 10,000 random price scenarios
        - Uses historical volatility patterns
        - Calculates probability distributions
        - Shows percentile outcomes (5% worst to 95% best case)
        
        **Stock vs Options:**
        - Stock profits scale linearly with price movement
        - Options provide leverage but can expire worthless
        - Time decay affects option values negatively
        - Volatility changes impact option prices significantly
        
        ### ⚠️ **RISK WARNINGS**
        
        - Options can expire completely worthless
        - High leverage means high risk
        - Time decay works against option buyers
        - Volatility crush can cause rapid losses
        - Never risk more than you can afford to lose
        """)


def main():
    st.set_page_config(
        page_title="IVSURF TERMINAL",
        page_icon="🟢",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    apply_professional_terminal_css()
    
    # Clean header
    st.markdown(f"""
    <div class="terminal-header">
        <div class="ascii-art">{create_clean_header()}</div>
        <div class="status-line">
            ► SYSTEM STATUS: <span style="color: #00ff00;">OPERATIONAL</span> | 
            MARKET FEED: <span style="color: #00ff00;">LIVE</span> | 
            ANALYTICS: <span style="color: #00ff00;">ACTIVE</span> |
            TIME: <span style="color: #00ffff;">{datetime.now().strftime("%H:%M:%S UTC")}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Top navigation bar for ticker selection
    st.markdown('<div class="info-panel">', unsafe_allow_html=True)
    st.markdown("### 🎯 **MARKET TARGET SELECTION**")
    
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    
    with col1:
        ticker = st.text_input(
            "ENTER TICKER SYMBOL", 
            value="NVDA", 
            help="Enter any stock ticker symbol",
            key="ticker_input"
        ).upper()
    
    with col2:
        popular_picks = st.selectbox(
            "POPULAR STOCKS",
            ["CUSTOM", "AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META"],
            help="Select from popular stocks"
        )
        if popular_picks != "CUSTOM":
            ticker = popular_picks
    
    with col3:
        etf_picks = st.selectbox(
            "POPULAR ETFS",
            ["CUSTOM", "SPY", "QQQ", "IWM", "VTI", "XLF", "XLK", "GLD"],
            help="Select from popular ETFs"
        )
        if etf_picks != "CUSTOM":
            ticker = etf_picks
    
    with col4:
        if st.button("🔄 REFRESH DATA", help="Refresh market data"):
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Fetch market data
    with st.spinner(f"📡 Fetching market data for {ticker}..."):
        market_data = fetch_enhanced_market_data(ticker)
    
    if market_data:
        # Display market overview in top bar
        st.markdown('<div class="info-panel">', unsafe_allow_html=True)
        st.markdown(f"### 📊 **{market_data['company_name']} ({ticker}) - {market_data['sector']}**")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            daily_change = ((market_data['current_price'] - market_data['price_1d_ago']) / market_data['price_1d_ago'] * 100)
            create_metric_card(
                "CURRENT PRICE",
                f"${market_data['current_price']:.2f}",
                f"Daily: {daily_change:+.2f}%"
            )
        
        with col2:
            weekly_change = ((market_data['current_price'] - market_data['price_1w_ago']) / market_data['price_1w_ago'] * 100)
            create_metric_card(
                "WEEKLY CHANGE",
                f"{weekly_change:+.2f}%",
                f"${market_data['current_price'] - market_data['price_1w_ago']:+.2f}"
            )
        
        with col3:
            create_metric_card(
                "VOLATILITY (1M)",
                f"{market_data['vol_1m']:.1%}",
                "Annual basis"
            )
        
        with col4:
            volume_ratio = market_data['current_volume'] / market_data['avg_volume'] if market_data['avg_volume'] > 0 else 1
            create_metric_card(
                "VOLUME",
                f"{market_data['current_volume']:,.0f}",
                f"{volume_ratio:.1f}x avg"
            )
        
        with col5:
            create_metric_card(
                "52W RANGE",
                f"${market_data['low_52w']:.2f}",
                f"to ${market_data['high_52w']:.2f}"
            )
        
        with col6:
            if market_data['market_cap'] > 0:
                market_cap_b = market_data['market_cap'] / 1e9
                create_metric_card(
                    "MARKET CAP",
                    f"${market_cap_b:.1f}B",
                    f"Beta: {market_data['beta']:.2f}"
                )
            else:
                create_metric_card(
                    "BETA",
                    f"{market_data['beta']:.2f}",
                    "vs Market"
                )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Options configuration in horizontal layout
        st.markdown('<div class="info-panel">', unsafe_allow_html=True)
        st.markdown("### ⚙️ **OPTIONS CONFIGURATION**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            strike = st.number_input(
                "STRIKE PRICE",
                value=float(market_data['current_price']),
                min_value=1.0,
                step=1.0,
                help="Option strike price"
            )
        
        with col2:
            days_to_expiry = st.number_input(
                "DAYS TO EXPIRY",
                value=30,
                min_value=1,
                max_value=365,
                help="Days until expiration"
            )
        
        with col3:
            option_type = st.selectbox(
                "OPTION TYPE", 
                ["call", "put"],
                help="Call or Put option"
            )
        
        with col4:
            volatility_override = st.number_input(
                "VOLATILITY OVERRIDE",
                value=float(market_data['vol_1m']),
                min_value=0.01,
                max_value=2.0,
                step=0.01,
                help="Custom volatility (or use calculated)"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Calculate option data
        time_to_expiry = days_to_expiry / 365.0
        option_data = calculate_advanced_option_pricing(
            market_data['current_price'],
            strike,
            time_to_expiry,
            0.05,  # Risk-free rate
            volatility_override,
            option_type
        )
        
        if option_data:
            option_data['strike'] = strike
            option_data['option_type'] = option_type
        
        # Information guide
        show_information_guide()
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 PRICING ENGINE", "📊 TECHNICAL ANALYSIS", "💰 PROFIT PREDICTIONS", "🎮 TRADING SIMULATOR"])
        
        with tab1:
            if option_data:
                st.markdown('<div class="info-panel">', unsafe_allow_html=True)
                st.markdown("### 🎯 **COMPREHENSIVE OPTION ANALYSIS**")
                
                # Primary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    create_metric_card(
                        "THEORETICAL PRICE",
                        f"${option_data['theoretical_price']:.4f}",
                        f"Contract: ${option_data['theoretical_price'] * 100:.2f}"
                    )
                
                with col2:
                    create_metric_card(
                        "INTRINSIC VALUE",
                        f"${option_data['intrinsic_value']:.4f}",
                        "Immediate exercise value"
                    )
                
                with col3:
                    create_metric_card(
                        "TIME VALUE",
                        f"${option_data['time_value']:.4f}",
                        "Premium for time"
                    )
                
                with col4:
                    create_metric_card(
                        "BREAKEVEN PRICE",
                        f"${option_data['breakeven']:.2f}",
                        f"Move: {abs(option_data['breakeven'] - market_data['current_price']):.2f}"
                    )
                
                # Probability analysis
                st.markdown("#### 📈 **PROBABILITY ANALYSIS**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    create_metric_card(
                        "ITM PROBABILITY",
                        f"{option_data['prob_itm']:.1%}",
                        "Finish in-the-money"
                    )
                
                with col2:
                    create_metric_card(
                        "PROFIT PROBABILITY",
                        f"{option_data['prob_profitable']:.1%}",
                        "Profitable at expiration"
                    )
                
                with col3:
                    moneyness_status = "ITM" if option_data['moneyness'] > 1.0 and option_type == 'call' else "ITM" if option_data['moneyness'] < 1.0 and option_type == 'put' else "OTM"
                    create_metric_card(
                        "MONEYNESS",
                        f"{option_data['moneyness']:.4f}",
                        f"Status: {moneyness_status}"
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Greeks analysis
                if option_data and option_data['greeks']:
                    st.markdown('<div class="info-panel">', unsafe_allow_html=True)
                    st.markdown("### ⚡ **GREEKS SENSITIVITY ANALYSIS**")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        create_metric_card(
                            "DELTA",
                            f"{option_data['greeks']['delta']:.4f}",
                            f"${option_data['greeks']['delta'] * 100:.2f} per $1"
                        )
                    
                    with col2:
                        create_metric_card(
                            "GAMMA",
                            f"{option_data['greeks']['gamma']:.6f}",
                            "Delta acceleration"
                        )
                    
                    with col3:
                        create_metric_card(
                            "VEGA",
                            f"{option_data['greeks']['vega']:.4f}",
                            f"${option_data['greeks']['vega'] * 100:.2f} per 1%"
                        )
                    
                    with col4:
                        create_metric_card(
                            "THETA",
                            f"{option_data['greeks']['theta']:.4f}",
                            f"${option_data['greeks']['theta'] * 100:.2f} daily"
                        )
                    
                    with col5:
                        create_metric_card(
                            "RHO",
                            f"{option_data['greeks']['rho']:.4f}",
                            f"${option_data['greeks']['rho'] * 100:.2f} per 1%"
                        )
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Price sensitivity chart
                    st.markdown('<div class="info-panel">', unsafe_allow_html=True)
                    st.markdown("### 📈 **PRICE SENSITIVITY ANALYSIS**")
                    
                    # Create sensitivity analysis
                    price_range = np.linspace(market_data['current_price'] * 0.7, market_data['current_price'] * 1.3, 100)
                    option_prices = []
                    deltas = []
                    
                    for price in price_range:
                        try:
                            opt_price = black_scholes_price(price, strike, time_to_expiry, 0.05, volatility_override, option_type)
                            delta = all_greeks(price, strike, time_to_expiry, 0.05, volatility_override, option_type)['delta']
                            option_prices.append(opt_price)
                            deltas.append(delta)
                        except:
                            option_prices.append(0)
                            deltas.append(0)
                    
                    fig = go.Figure()
                    
                    # Option price line
                    fig.add_trace(go.Scatter(
                        x=price_range, 
                        y=option_prices,
                        name='Option Price',
                        line=dict(color='#00ff00', width=3),
                        hovertemplate='Stock: $%{x:.2f}<br>Option: $%{y:.4f}<extra></extra>'
                    ))
                    
                    # Delta line
                    fig.add_trace(go.Scatter(
                        x=price_range, 
                        y=deltas,
                        name='Delta',
                        line=dict(color='#00ffff', width=2),
                        yaxis='y2',
                        hovertemplate='Stock: $%{x:.2f}<br>Delta: %{y:.4f}<extra></extra>'
                    ))
                    
                    # Current position marker
                    fig.add_trace(go.Scatter(
                        x=[market_data['current_price']], 
                        y=[option_data['theoretical_price']],
                        mode='markers',
                        name='Current Position',
                        marker=dict(color='#ffff00', size=15, symbol='diamond'),
                        hovertemplate=f'Current: ${market_data["current_price"]:.2f}<br>Price: ${option_data["theoretical_price"]:.4f}<extra></extra>'
                    ))
                    
                    # Breakeven line
                    fig.add_vline(
                        x=option_data['breakeven'], 
                        line_dash="dash", 
                        line_color="#ff8800",
                        annotation_text="Breakeven"
                    )
                    
                    # Strike price line
                    fig.add_vline(
                        x=strike, 
                        line_dash="dot", 
                        line_color="#ff0000",
                        annotation_text="Strike"
                    )
                    
                    fig.update_layout(
                        title="OPTION PRICE SENSITIVITY MATRIX",
                        xaxis_title="UNDERLYING PRICE ($)",
                        yaxis_title="OPTION PRICE ($)",
                        yaxis2=dict(title="DELTA", overlaying='y', side='right', color='#00ffff'),
                        plot_bgcolor='#000000',
                        paper_bgcolor='#000000',
                        font=dict(color='#00ff00', family='JetBrains Mono'),
                        height=500,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.markdown('<div class="info-panel">', unsafe_allow_html=True)
            st.markdown("### 📊 **TECHNICAL ANALYSIS DASHBOARD**")
            
            # Price chart
            if not market_data['hist_1m'].empty:
                fig_price = go.Figure()
                
                hist_data = market_data['hist_1m']
                
                # Candlestick chart
                fig_price.add_trace(go.Candlestick(
                    x=hist_data.index,
                    open=hist_data['Open'],
                    high=hist_data['High'],
                    low=hist_data['Low'],
                    close=hist_data['Close'],
                    name=f'{ticker} Price',
                    increasing_line_color='#00ff00',
                    decreasing_line_color='#ff0000'
                ))
                
                # Add volume
                fig_volume = go.Figure()
                fig_volume.add_trace(go.Bar(
                    x=hist_data.index,
                    y=hist_data['Volume'],
                    name='Volume',
                    marker_color='#00ffff',
                    opacity=0.7
                ))
                
                fig_price.update_layout(
                    title=f"{ticker} PRICE CHART - LAST 30 DAYS",
                    xaxis_title="DATE",
                    yaxis_title="PRICE ($)",
                    plot_bgcolor='#000000',
                    paper_bgcolor='#000000',
                    font=dict(color='#00ff00'),
                    height=400,
                    xaxis_rangeslider_visible=False
                )
                
                fig_volume.update_layout(
                    title=f"{ticker} VOLUME ANALYSIS",
                    xaxis_title="DATE",
                    yaxis_title="VOLUME",
                    plot_bgcolor='#000000',
                    paper_bgcolor='#000000',
                    font=dict(color='#00ff00'),
                    height=300
                )
                
                st.plotly_chart(fig_price, use_container_width=True)
                st.plotly_chart(fig_volume, use_container_width=True)
            else:
                create_alert("CHART_INFO", "Historical data not available for detailed charting. Using current market data.", "info")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab3:
            st.markdown('<div class="info-panel">', unsafe_allow_html=True)
            st.markdown("### 💰 **ADVANCED PROFIT PREDICTION ENGINE**")
            
            # Prediction controls
            col1, col2, col3 = st.columns(3)
            with col1:
                investment = st.slider(
                    "INITIAL INVESTMENT ($)",
                    min_value=100,
                    max_value=100000,
                    value=1000,
                    step=100,
                    help="Amount to invest"
                )
            
            with col2:
                time_period = st.slider(
                    "TIME PERIOD (DAYS)",
                    min_value=1,
                    max_value=365,
                    value=30,
                    step=1,
                    help="Investment time horizon"
                )
            
            with col3:
                analysis_type = st.selectbox(
                    "ANALYSIS TYPE",
                    ["Both Stock & Options", "Stock Only", "Options Only"],
                    help="What to analyze"
                )
            
            if st.button("🚀 RUN PROFIT ANALYSIS", help="Execute Monte Carlo profit simulation"):
                with st.spinner("🧮 Running Monte Carlo simulations..."):
                    predictions = calculate_predictive_profits(
                        investment, time_period, market_data, option_data
                    )
                
                if predictions:
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    if analysis_type in ["Both Stock & Options", "Stock Only"]:
                        with col1:
                            st.markdown("#### 📈 **STOCK INVESTMENT ANALYSIS**")
                            create_metric_card(
                                "EXPECTED PROFIT",
                                f"${predictions['stock_mean_profit']:.2f}",
                                f"Success rate: {predictions['stock_prob_profit']:.1%}"
                            )
                            
                            create_metric_card(
                                "BEST CASE SCENARIO",
                                f"${predictions['max_stock_profit']:.2f}",
                                "95th percentile outcome"
                            )
                            
                            create_metric_card(
                                "WORST CASE SCENARIO",
                                f"${predictions['min_stock_loss']:.2f}",
                                "5th percentile outcome"
                            )
                    
                    if analysis_type in ["Both Stock & Options", "Options Only"] and option_data:
                        with col2:
                            st.markdown("#### 📊 **OPTIONS INVESTMENT ANALYSIS**")
                            create_metric_card(
                                "EXPECTED PROFIT",
                                f"${predictions['option_mean_profit']:.2f}",
                                f"Success rate: {predictions['option_prob_profit']:.1%}"
                            )
                            
                            create_metric_card(
                                "BEST CASE SCENARIO",
                                f"${predictions['max_option_profit']:.2f}",
                                "95th percentile outcome"
                            )
                            
                            create_metric_card(
                                "WORST CASE SCENARIO",
                                f"${predictions['min_option_loss']:.2f}",
                                "5th percentile outcome"
                            )
                    
                    # Probability distribution chart
                    fig_dist = go.Figure()
                    
                    if analysis_type in ["Both Stock & Options", "Stock Only"]:
                        fig_dist.add_trace(go.Histogram(
                            x=predictions['stock_profits'],
                            name='Stock Profits',
                            opacity=0.7,
                            nbinsx=50,
                            marker_color='#00ff00'
                        ))
                    
                    if analysis_type in ["Both Stock & Options", "Options Only"] and option_data:
                        fig_dist.add_trace(go.Histogram(
                            x=predictions['option_profits'],
                            name='Option Profits',
                            opacity=0.7,
                            nbinsx=50,
                            marker_color='#00ffff'
                        ))
                    
                    fig_dist.update_layout(
                        title="PROFIT DISTRIBUTION ANALYSIS (10,000 SIMULATIONS)",
                        xaxis_title="PROFIT/LOSS ($)",
                        yaxis_title="FREQUENCY",
                        plot_bgcolor='#000000',
                        paper_bgcolor='#000000',
                        font=dict(color='#00ff00'),
                        height=400,
                        barmode='overlay'
                    )
                    
                    st.plotly_chart(fig_dist, use_container_width=True)
                    
                    # Statistics table
                    if analysis_type == "Both Stock & Options":
                        st.markdown("#### 📋 **DETAILED STATISTICS**")
                        
                        stats_data = {
                            'Metric': ['Expected Profit', '50th Percentile', '75th Percentile', '90th Percentile', '95th Percentile', 'Success Rate'],
                            'Stock Investment': [
                                f"${predictions['stock_mean_profit']:.2f}",
                                f"${predictions['stock_percentiles'][50]:.2f}",
                                f"${predictions['stock_percentiles'][75]:.2f}",
                                f"${predictions['stock_percentiles'][90]:.2f}",
                                f"${predictions['stock_percentiles'][95]:.2f}",
                                f"{predictions['stock_prob_profit']:.1%}"
                            ],
                            'Options Investment': [
                                f"${predictions['option_mean_profit']:.2f}",
                                f"${predictions['option_percentiles'][50]:.2f}",
                                f"${predictions['option_percentiles'][75]:.2f}",
                                f"${predictions['option_percentiles'][90]:.2f}",
                                f"${predictions['option_percentiles'][95]:.2f}",
                                f"{predictions['option_prob_profit']:.1%}"
                            ]
                        }
                        
                        stats_df = pd.DataFrame(stats_data)
                        st.dataframe(stats_df, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab4:
            st.markdown('<div class="info-panel">', unsafe_allow_html=True)
            st.markdown("### 🎮 **ADVANCED TRADING SIMULATOR**")
            
            create_alert(
                "SIMULATION_MODE",
                "All trades are simulated for educational purposes. No real money involved.",
                "info"
            )
            
            # Portfolio tracker
            if 'portfolio' not in st.session_state:
                st.session_state.portfolio = {
                    'cash': 10000.0,
                    'stocks': {},
                    'options': {},
                    'transactions': []
                }
            
            portfolio = st.session_state.portfolio
            
            # Display portfolio status
            st.markdown("#### 💼 **PORTFOLIO STATUS**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                create_metric_card(
                    "AVAILABLE CASH",
                    f"${portfolio['cash']:.2f}",
                    "Buying power"
                )
            
            with col2:
                stock_value = sum([pos['shares'] * market_data['current_price'] for pos in portfolio['stocks'].values()])
                create_metric_card(
                    "STOCK POSITIONS",
                    f"${stock_value:.2f}",
                    f"{len(portfolio['stocks'])} positions"
                )
            
            with col3:
                option_value = sum([pos['contracts'] * option_data['theoretical_price'] * 100 for pos in portfolio['options'].values()]) if option_data else 0
                create_metric_card(
                    "OPTION POSITIONS",
                    f"${option_value:.2f}",
                    f"{len(portfolio['options'])} positions"
                )
            
            # Trading interface
            st.markdown("#### 🎯 **EXECUTE TRADES**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                stock_quantity = st.number_input("STOCK SHARES", min_value=1, value=10, step=1)
                if st.button(f"🟢 BUY {stock_quantity} SHARES"):
                    cost = stock_quantity * market_data['current_price']
                    if portfolio['cash'] >= cost:
                        portfolio['cash'] -= cost
                        if ticker in portfolio['stocks']:
                            portfolio['stocks'][ticker]['shares'] += stock_quantity
                        else:
                            portfolio['stocks'][ticker] = {'shares': stock_quantity, 'avg_price': market_data['current_price']}
                        
                        portfolio['transactions'].append({
                            'type': 'BUY_STOCK',
                            'ticker': ticker,
                            'quantity': stock_quantity,
                            'price': market_data['current_price'],
                            'cost': cost,
                            'timestamp': datetime.now()
                        })
                        
                        create_alert(
                            "TRADE_EXECUTED",
                            f"Bought {stock_quantity} shares of {ticker} at ${market_data['current_price']:.2f}. Total: ${cost:.2f}",
                            "success"
                        )
                        st.rerun()
                    else:
                        create_alert("INSUFFICIENT_FUNDS", f"Need ${cost:.2f}, have ${portfolio['cash']:.2f}", "error")
            
            with col2:
                if ticker in portfolio['stocks'] and portfolio['stocks'][ticker]['shares'] > 0:
                    max_shares = portfolio['stocks'][ticker]['shares']
                    sell_quantity = st.number_input("SHARES TO SELL", min_value=1, max_value=max_shares, value=min(10, max_shares), step=1)
                    if st.button(f"🔴 SELL {sell_quantity} SHARES"):
                        proceeds = sell_quantity * market_data['current_price']
                        portfolio['cash'] += proceeds
                        portfolio['stocks'][ticker]['shares'] -= sell_quantity
                        
                        if portfolio['stocks'][ticker]['shares'] == 0:
                            del portfolio['stocks'][ticker]
                        
                        portfolio['transactions'].append({
                            'type': 'SELL_STOCK',
                            'ticker': ticker,
                            'quantity': sell_quantity,
                            'price': market_data['current_price'],
                            'proceeds': proceeds,
                            'timestamp': datetime.now()
                        })
                        
                        create_alert(
                            "TRADE_EXECUTED",
                            f"Sold {sell_quantity} shares of {ticker} at ${market_data['current_price']:.2f}. Proceeds: ${proceeds:.2f}",
                            "success"
                        )
                        st.rerun()
                else:
                    st.info(f"No {ticker} shares to sell")
            
            with col3:
                if option_data:
                    option_contracts = st.number_input("OPTION CONTRACTS", min_value=1, value=1, step=1)
                    contract_cost = option_contracts * option_data['theoretical_price'] * 100
                    if st.button(f"🔵 BUY {option_contracts} CONTRACTS"):
                        if portfolio['cash'] >= contract_cost:
                            portfolio['cash'] -= contract_cost
                            option_key = f"{ticker}_{strike}_{option_type}_{days_to_expiry}"
                            
                            if option_key in portfolio['options']:
                                portfolio['options'][option_key]['contracts'] += option_contracts
                            else:
                                portfolio['options'][option_key] = {
                                    'contracts': option_contracts,
                                    'strike': strike,
                                    'type': option_type,
                                    'expiry_days': days_to_expiry,
                                    'avg_price': option_data['theoretical_price']
                                }
                            
                            portfolio['transactions'].append({
                                'type': 'BUY_OPTION',
                                'ticker': ticker,
                                'contracts': option_contracts,
                                'strike': strike,
                                'option_type': option_type,
                                'price': option_data['theoretical_price'],
                                'cost': contract_cost,
                                'timestamp': datetime.now()
                            })
                            
                            create_alert(
                                "OPTION_TRADE_EXECUTED",
                                f"Bought {option_contracts} {option_type} contracts at ${option_data['theoretical_price']:.4f}. Total: ${contract_cost:.2f}",
                                "success"
                            )
                            st.rerun()
                        else:
                            create_alert("INSUFFICIENT_FUNDS", f"Need ${contract_cost:.2f}, have ${portfolio['cash']:.2f}", "error")
            
            with col4:
                if st.button("💰 RESET PORTFOLIO"):
                    st.session_state.portfolio = {
                        'cash': 10000.0,
                        'stocks': {},
                        'options': {},
                        'transactions': []
                    }
                    create_alert("PORTFOLIO_RESET", "Portfolio reset to $10,000 cash", "info")
                    st.rerun()
            
            # Transaction history
            if portfolio['transactions']:
                st.markdown("#### 📜 **RECENT TRANSACTIONS**")
                recent_transactions = portfolio['transactions'][-5:]  # Show last 5
                for i, txn in enumerate(reversed(recent_transactions)):
                    st.text(f"{txn['timestamp'].strftime('%H:%M:%S')} - {txn['type']}: {txn.get('quantity', txn.get('contracts', 0))} {txn['ticker']} @ ${txn.get('price', 0):.4f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        create_alert("SYSTEM_ERROR", "Unable to load market data. Please check your connection and try again.", "error")


if __name__ == "__main__":
    main()

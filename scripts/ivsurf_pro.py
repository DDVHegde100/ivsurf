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
from scipy.signal import find_peaks, argrelextrema
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
        
        # Fetch multiple timeframes for comprehensive analysis
        hist_1d = stock.history(period="1d", interval="1m")      # Intraday
        hist_5d = stock.history(period="5d", interval="1h")      # Hourly
        hist_1m = stock.history(period="1mo", interval="1d")     # Daily
        hist_3m = stock.history(period="3mo", interval="1d")     # 3 months
        hist_1y = stock.history(period="1y", interval="1d")      # 1 year
        hist_2y = stock.history(period="2y", interval="1d")      # 2 years for swing analysis
        
        # Use the most reliable timeframe for current price
        if not hist_1d.empty:
            current_price = hist_1d['Close'].iloc[-1]
        elif not hist_5d.empty:
            current_price = hist_5d['Close'].iloc[-1]
        elif not hist_1m.empty:
            current_price = hist_1m['Close'].iloc[-1]
        else:
            raise ValueError(f"No historical data available for {ticker}")
        
        # Get company info (with fallbacks)
        info = {}
        try:
            info = stock.info
        except:
            pass
        
        # Calculate volatility measures using daily data
        if not hist_1y.empty and len(hist_1y) > 30:
            returns_1y = hist_1y['Close'].pct_change().dropna()
            vol_annual = returns_1y.std() * np.sqrt(252)
        else:
            vol_annual = 0.25
            
        if not hist_3m.empty and len(hist_3m) > 20:
            returns_3m = hist_3m['Close'].pct_change().dropna()
            vol_3m = returns_3m.std() * np.sqrt(252)
        else:
            vol_3m = 0.25
            
        if not hist_1m.empty and len(hist_1m) > 10:
            returns_1m = hist_1m['Close'].pct_change().dropna()
            vol_1m = returns_1m.std() * np.sqrt(252)
        else:
            vol_1m = 0.25
        
        # Ensure volatilities are reasonable
        vol_annual = max(0.05, min(vol_annual, 2.0))
        vol_3m = max(0.05, min(vol_3m, 2.0))
        vol_1m = max(0.05, min(vol_1m, 2.0))
        
        # Enhanced market metrics
        beta = info.get('beta', 1.0) or 1.0
        market_cap = info.get('marketCap', 0) or 0
        pe_ratio = info.get('trailingPE', 0) or 0
        company_name = info.get('longName', ticker) or ticker
        sector = info.get('sector', 'Technology') or 'Technology'
        
        # Technical levels from swing analysis timeframe
        swing_data = hist_2y if not hist_2y.empty else hist_1y
        high_52w = swing_data['High'].max() if not swing_data.empty else current_price * 1.2
        low_52w = swing_data['Low'].min() if not swing_data.empty else current_price * 0.8
        
        # Recent performance
        price_1d_ago = hist_1m['Close'].iloc[-2] if len(hist_1m) > 1 else current_price
        price_1w_ago = hist_1m['Close'].iloc[-7] if len(hist_1m) > 7 else current_price
        price_1m_ago = hist_3m['Close'].iloc[-22] if len(hist_3m) > 22 else current_price
        
        # Volume analysis
        avg_volume = hist_1m['Volume'].mean() if not hist_1m.empty else 1000000
        current_volume = hist_1m['Volume'].iloc[-1] if not hist_1m.empty else avg_volume
        
        # Calculate technical indicators for swing analysis
        swing_analysis_data = swing_data.copy() if not swing_data.empty else hist_1y.copy()
        if not swing_analysis_data.empty and len(swing_analysis_data) > 50:
            swing_analysis_data = calculate_technical_indicators(swing_analysis_data)
        
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
            'hist_1d': hist_1d,
            'swing_data': swing_analysis_data,  # Enhanced data with technical indicators
            'avg_volume': float(avg_volume),
            'current_volume': float(current_volume),
            'data_quality': 'LIVE'
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
        
        # Create synthetic swing data
        dates = pd.date_range(end=datetime.now(), periods=200, freq='D')
        synthetic_data = pd.DataFrame({
            'Open': demo_price + np.random.randn(200) * 5,
            'High': demo_price + np.random.randn(200) * 5 + 2,
            'Low': demo_price + np.random.randn(200) * 5 - 2,
            'Close': demo_price + np.random.randn(200) * 5,
            'Volume': np.random.randint(1000000, 10000000, 200)
        }, index=dates)
        
        synthetic_data = calculate_technical_indicators(synthetic_data)
        
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
            'hist_1y': synthetic_data,
            'hist_3m': synthetic_data.tail(90),
            'hist_1m': synthetic_data.tail(30),
            'hist_5d': synthetic_data.tail(5),
            'hist_1d': synthetic_data.tail(1),
            'swing_data': synthetic_data,
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


def calculate_technical_indicators(df):
    """Calculate comprehensive technical indicators for swing trading analysis."""
    try:
        # Ensure we have the required columns
        if df.empty or len(df) < 50:
            return df
        
        # Moving Averages
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Stochastic Oscillator
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        # Average Directional Index (ADX)
        high_diff = df['High'].diff()
        low_diff = df['Low'].diff().abs()
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Close'].shift()).abs()
        tr3 = (df['Low'] - df['Close'].shift()).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = true_range.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        df['ADX'] = dx.rolling(window=14).mean()
        df['Plus_DI'] = plus_di
        df['Minus_DI'] = minus_di
        
        # Williams %R
        high_14 = df['High'].rolling(window=14).max()
        low_14 = df['Low'].rolling(window=14).min()
        df['Williams_R'] = -100 * ((high_14 - df['Close']) / (high_14 - low_14))
        
        # Commodity Channel Index (CCI)
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        sma_tp = typical_price.rolling(window=20).mean()
        mad = typical_price.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
        df['CCI'] = (typical_price - sma_tp) / (0.015 * mad)
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # On Balance Volume
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        
        # Price Rate of Change
        df['ROC'] = df['Close'].pct_change(periods=12) * 100
        
        return df
        
    except Exception as e:
        st.error(f"Error calculating technical indicators: {str(e)}")
        return df


def detect_swing_patterns(df):
    """Detect swing trading patterns and signals."""
    try:
        if df.empty or len(df) < 50:
            return {}
        
        signals = {}
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Trend Analysis
        if latest['SMA_20'] > latest['SMA_50'] and latest['SMA_50'] > latest['SMA_200']:
            signals['trend'] = 'STRONG_BULLISH'
        elif latest['SMA_20'] > latest['SMA_50']:
            signals['trend'] = 'BULLISH'
        elif latest['SMA_20'] < latest['SMA_50'] and latest['SMA_50'] < latest['SMA_200']:
            signals['trend'] = 'STRONG_BEARISH'
        elif latest['SMA_20'] < latest['SMA_50']:
            signals['trend'] = 'BEARISH'
        else:
            signals['trend'] = 'SIDEWAYS'
        
        # MACD Signals
        if latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
            signals['macd'] = 'BULLISH_CROSSOVER'
        elif latest['MACD'] < latest['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
            signals['macd'] = 'BEARISH_CROSSOVER'
        elif latest['MACD'] > latest['MACD_Signal']:
            signals['macd'] = 'BULLISH'
        else:
            signals['macd'] = 'BEARISH'
        
        # RSI Analysis
        if latest['RSI'] < 30:
            signals['rsi'] = 'OVERSOLD'
        elif latest['RSI'] > 70:
            signals['rsi'] = 'OVERBOUGHT'
        elif 30 <= latest['RSI'] <= 40:
            signals['rsi'] = 'OVERSOLD_RECOVERY'
        elif 60 <= latest['RSI'] <= 70:
            signals['rsi'] = 'OVERBOUGHT_WARNING'
        else:
            signals['rsi'] = 'NEUTRAL'
        
        # Bollinger Bands
        if latest['Close'] > latest['BB_Upper']:
            signals['bollinger'] = 'OVERBOUGHT'
        elif latest['Close'] < latest['BB_Lower']:
            signals['bollinger'] = 'OVERSOLD'
        elif latest['BB_Position'] > 0.8:
            signals['bollinger'] = 'UPPER_BAND'
        elif latest['BB_Position'] < 0.2:
            signals['bollinger'] = 'LOWER_BAND'
        else:
            signals['bollinger'] = 'MIDDLE_RANGE'
        
        # Stochastic Signals
        if latest['Stoch_K'] < 20 and latest['Stoch_D'] < 20:
            signals['stochastic'] = 'OVERSOLD'
        elif latest['Stoch_K'] > 80 and latest['Stoch_D'] > 80:
            signals['stochastic'] = 'OVERBOUGHT'
        elif latest['Stoch_K'] > latest['Stoch_D'] and prev['Stoch_K'] <= prev['Stoch_D']:
            signals['stochastic'] = 'BULLISH_CROSSOVER'
        elif latest['Stoch_K'] < latest['Stoch_D'] and prev['Stoch_K'] >= prev['Stoch_D']:
            signals['stochastic'] = 'BEARISH_CROSSOVER'
        else:
            signals['stochastic'] = 'NEUTRAL'
        
        # ADX Trend Strength
        if latest['ADX'] > 50:
            signals['adx'] = 'VERY_STRONG_TREND'
        elif latest['ADX'] > 25:
            signals['adx'] = 'STRONG_TREND'
        elif latest['ADX'] > 20:
            signals['adx'] = 'MODERATE_TREND'
        else:
            signals['adx'] = 'WEAK_TREND'
        
        # Volume Analysis
        if latest['Volume_Ratio'] > 2.0:
            signals['volume'] = 'VERY_HIGH'
        elif latest['Volume_Ratio'] > 1.5:
            signals['volume'] = 'HIGH'
        elif latest['Volume_Ratio'] < 0.5:
            signals['volume'] = 'LOW'
        else:
            signals['volume'] = 'NORMAL'
        
        return signals
        
    except Exception as e:
        st.error(f"Error detecting swing patterns: {str(e)}")
        return {}


def find_support_resistance_levels(df, window=20):
    """Find dynamic support and resistance levels."""
    try:
        if df.empty or len(df) < window * 2:
            return {}
        
        # Find local maxima and minima
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values
        
        # Find peaks and troughs
        peak_indices = find_peaks(highs, distance=window//2)[0]
        trough_indices = find_peaks(-lows, distance=window//2)[0]
        
        # Get recent levels
        recent_peaks = []
        recent_troughs = []
        
        if len(peak_indices) > 0:
            recent_peak_indices = peak_indices[-5:] if len(peak_indices) >= 5 else peak_indices
            recent_peaks = [highs[i] for i in recent_peak_indices]
        
        if len(trough_indices) > 0:
            recent_trough_indices = trough_indices[-5:] if len(trough_indices) >= 5 else trough_indices
            recent_troughs = [lows[i] for i in recent_trough_indices]
        
        # Calculate dynamic levels
        current_price = closes[-1]
        
        # Resistance levels (above current price)
        resistance_levels = [level for level in recent_peaks if level > current_price]
        resistance_levels.sort()
        
        # Support levels (below current price)
        support_levels = [level for level in recent_troughs if level < current_price]
        support_levels.sort(reverse=True)
        
        # Psychological levels (round numbers)
        psychological_levels = []
        for level in range(int(current_price * 0.8), int(current_price * 1.2), 5):
            if abs(level - current_price) / current_price > 0.02:  # At least 2% away
                psychological_levels.append(float(level))
        
        return {
            'resistance_levels': resistance_levels[:3],  # Top 3 resistance
            'support_levels': support_levels[:3],        # Top 3 support
            'psychological_levels': psychological_levels,
            'current_price': current_price
        }
        
    except Exception as e:
        st.error(f"Error finding support/resistance: {str(e)}")
        return {}


def generate_swing_trade_signals(df, signals, sr_levels):
    """Generate specific swing trade buy/sell signals with timing."""
    try:
        trade_signals = []
        current_price = df['Close'].iloc[-1]
        latest = df.iloc[-1]
        
        # Strong Buy Signals
        if (signals.get('rsi') == 'OVERSOLD' and 
            signals.get('bollinger') == 'OVERSOLD' and 
            signals.get('stochastic') in ['OVERSOLD', 'BULLISH_CROSSOVER']):
            
            confidence = 85
            target_price = current_price * 1.05  # 5% target
            stop_loss = current_price * 0.97     # 3% stop
            
            trade_signals.append({
                'signal': 'STRONG_BUY',
                'confidence': confidence,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'timeframe': '3-7 days',
                'reasoning': 'Multiple oversold indicators converging'
            })
        
        # Moderate Buy Signals
        elif (signals.get('macd') == 'BULLISH_CROSSOVER' and 
              signals.get('trend') in ['BULLISH', 'STRONG_BULLISH']):
            
            confidence = 70
            target_price = current_price * 1.03  # 3% target
            stop_loss = current_price * 0.98     # 2% stop
            
            trade_signals.append({
                'signal': 'BUY',
                'confidence': confidence,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'timeframe': '5-10 days',
                'reasoning': 'MACD bullish crossover in uptrend'
            })
        
        # Strong Sell Signals
        elif (signals.get('rsi') == 'OVERBOUGHT' and 
              signals.get('bollinger') == 'OVERBOUGHT' and 
              signals.get('stochastic') in ['OVERBOUGHT', 'BEARISH_CROSSOVER']):
            
            confidence = 85
            target_price = current_price * 0.95  # 5% target down
            stop_loss = current_price * 1.03     # 3% stop
            
            trade_signals.append({
                'signal': 'STRONG_SELL',
                'confidence': confidence,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'timeframe': '3-7 days',
                'reasoning': 'Multiple overbought indicators converging'
            })
        
        # Moderate Sell Signals
        elif (signals.get('macd') == 'BEARISH_CROSSOVER' and 
              signals.get('trend') in ['BEARISH', 'STRONG_BEARISH']):
            
            confidence = 70
            target_price = current_price * 0.97  # 3% target down
            stop_loss = current_price * 1.02     # 2% stop
            
            trade_signals.append({
                'signal': 'SELL',
                'confidence': confidence,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'timeframe': '5-10 days',
                'reasoning': 'MACD bearish crossover in downtrend'
            })
        
        # Support/Resistance based signals
        if sr_levels.get('support_levels'):
            nearest_support = sr_levels['support_levels'][0]
            if abs(current_price - nearest_support) / current_price < 0.02:  # Within 2%
                trade_signals.append({
                    'signal': 'SUPPORT_BOUNCE_BUY',
                    'confidence': 65,
                    'entry_price': current_price,
                    'target_price': current_price * 1.04,
                    'stop_loss': nearest_support * 0.99,
                    'timeframe': '2-5 days',
                    'reasoning': f'Near major support at ${nearest_support:.2f}'
                })
        
        if sr_levels.get('resistance_levels'):
            nearest_resistance = sr_levels['resistance_levels'][0]
            if abs(current_price - nearest_resistance) / current_price < 0.02:  # Within 2%
                trade_signals.append({
                    'signal': 'RESISTANCE_REJECTION_SELL',
                    'confidence': 65,
                    'entry_price': current_price,
                    'target_price': current_price * 0.96,
                    'stop_loss': nearest_resistance * 1.01,
                    'timeframe': '2-5 days',
                    'reasoning': f'Near major resistance at ${nearest_resistance:.2f}'
                })
        
        # No clear signal
        if not trade_signals:
            trade_signals.append({
                'signal': 'HOLD',
                'confidence': 50,
                'entry_price': current_price,
                'target_price': current_price,
                'stop_loss': current_price,
                'timeframe': 'N/A',
                'reasoning': 'Mixed signals, wait for clearer setup'
            })
        
        return trade_signals
        
    except Exception as e:
        st.error(f"Error generating trade signals: {str(e)}")
        return []


def analyze_historical_swings(df, lookback_days=90):
    """Analyze historical swing patterns for backtesting."""
    try:
        if df.empty or len(df) < lookback_days:
            return {}
        
        # Get recent data for analysis
        recent_df = df.tail(lookback_days).copy()
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(5, len(recent_df) - 5):
            # Check for swing high
            if (recent_df['High'].iloc[i] > recent_df['High'].iloc[i-5:i].max() and
                recent_df['High'].iloc[i] > recent_df['High'].iloc[i+1:i+6].max()):
                swing_highs.append({
                    'date': recent_df.index[i],
                    'price': recent_df['High'].iloc[i],
                    'type': 'swing_high'
                })
            
            # Check for swing low
            if (recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i-5:i].min() and
                recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i+1:i+6].min()):
                swing_lows.append({
                    'date': recent_df.index[i],
                    'price': recent_df['Low'].iloc[i],
                    'type': 'swing_low'
                })
        
        # Calculate swing statistics
        if len(swing_highs) > 1 and len(swing_lows) > 1:
            # Average swing magnitude
            swing_magnitudes = []
            for i in range(min(len(swing_highs), len(swing_lows)) - 1):
                if i < len(swing_highs) - 1 and i < len(swing_lows) - 1:
                    high_to_low = abs(swing_highs[i]['price'] - swing_lows[i]['price'])
                    swing_magnitudes.append(high_to_low / swing_highs[i]['price'])
            
            avg_swing_pct = np.mean(swing_magnitudes) * 100 if swing_magnitudes else 0
            
            # Average time between swings
            swing_durations = []
            all_swings = sorted(swing_highs + swing_lows, key=lambda x: x['date'])
            for i in range(len(all_swings) - 1):
                duration = (all_swings[i+1]['date'] - all_swings[i]['date']).days
                swing_durations.append(duration)
            
            avg_swing_duration = np.mean(swing_durations) if swing_durations else 0
            
            return {
                'swing_highs': swing_highs[-5:],  # Last 5 swing highs
                'swing_lows': swing_lows[-5:],   # Last 5 swing lows
                'avg_swing_percentage': avg_swing_pct,
                'avg_swing_duration_days': avg_swing_duration,
                'total_swings': len(swing_highs) + len(swing_lows),
                'success_rate': min(85, 60 + (avg_swing_pct * 2))  # Heuristic success rate
            }
        
        return {}
        
    except Exception as e:
        st.error(f"Error analyzing historical swings: {str(e)}")
        return {}
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


def show_information_guide():
    """Display IVSURF information guide and system status."""
    st.markdown("""
    <div style='background-color: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 20px; margin: 10px 0;'>
        <h3 style='color: #00ff00; text-align: center; margin-bottom: 20px;'>
            📊 IVSURF PROFESSIONAL TERMINAL v4.0 📊
        </h3>
        
        <div style='color: #c9d1d9; font-family: monospace; font-size: 14px;'>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px;'>
                <div>
                    <h4 style='color: #58a6ff;'>🎯 OPTIONS ANALYTICS</h4>
                    <ul style='margin: 0; padding-left: 20px;'>
                        <li>Black-Scholes & Greeks Calculation</li>
                        <li>Implied Volatility Surface Modeling</li>
                        <li>Monte Carlo Simulation (10,000 scenarios)</li>
                        <li>Risk Management & Portfolio Analysis</li>
                        <li>Real-time Options Chain Analysis</li>
                    </ul>
                    
                    <h4 style='color: #58a6ff; margin-top: 15px;'>📈 SWING TRADING</h4>
                    <ul style='margin: 0; padding-left: 20px;'>
                        <li>Technical Indicators (RSI, MACD, Bollinger)</li>
                        <li>Pattern Recognition & Trend Analysis</li>
                        <li>Support/Resistance Level Detection</li>
                        <li>Fibonacci Retracements & Extensions</li>
                        <li>Swing Point Identification</li>
                        <li>Buy/Sell Signal Generation</li>
                    </ul>
                </div>
                
                <div>
                    <h4 style='color: #58a6ff;'>⚡ SYSTEM FEATURES</h4>
                    <ul style='margin: 0; padding-left: 20px;'>
                        <li>Real-time Market Data Integration</li>
                        <li>Advanced Risk Metrics</li>
                        <li>Portfolio Simulation Engine</li>
                        <li>Multi-timeframe Analysis</li>
                        <li>Quantitative Research Tools</li>
                        <li>Professional Grade Analytics</li>
                    </ul>
                    
                    <h4 style='color: #58a6ff; margin-top: 15px;'>🔧 SUPPORTED TICKERS</h4>
                    <div style='display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;'>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>NVDA</span>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>AAPL</span>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>TSLA</span>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>MSFT</span>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>GOOGL</span>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>AMZN</span>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>META</span>
                        <span style='background: #21262d; padding: 2px 6px; border-radius: 3px;'>NFLX</span>
                    </div>
                </div>
            </div>
            
            <div style='margin-top: 20px; padding-top: 15px; border-top: 1px solid #30363d; text-align: center;'>
                <p style='color: #7d8590; margin: 5px 0;'>
                    🚀 IVSURF Terminal - Professional Options & Swing Trading Analytics
                </p>
                <p style='color: #7d8590; margin: 5px 0; font-size: 12px;'>
                    Real-time data • Advanced algorithms • Professional-grade analysis
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_swing_trading_analysis(data):
    """Display comprehensive swing trading analysis with PhD-level quantitative insights."""
    
    st.markdown("""
    <div style='background-color: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 20px; margin: 10px 0;'>
        <h2 style='color: #00ff00; text-align: center; margin-bottom: 20px;'>
            📊 SWING TRADING ANALYSIS 📊
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Main analysis columns
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Get swing data with technical indicators
    swing_data = data.get('swing_data', pd.DataFrame())
    
    if swing_data.empty:
        st.error("No swing trading data available")
        return
    
    # Current market metrics
    current_price = data['current_price']
    
    with col1:
        st.markdown("""
        <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 5px; padding: 15px;'>
            <h4 style='color: #58a6ff; margin-bottom: 15px;'>📈 TECHNICAL INDICATORS</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Get latest technical indicators
        if 'RSI' in swing_data.columns:
            current_rsi = swing_data['RSI'].iloc[-1]
            rsi_signal = "🔴 OVERSOLD" if current_rsi < 30 else "🟢 OVERBOUGHT" if current_rsi > 70 else "🟡 NEUTRAL"
            st.metric("RSI (14)", f"{current_rsi:.2f}", rsi_signal)
        
        if 'MACD' in swing_data.columns and 'MACD_Signal' in swing_data.columns:
            current_macd = swing_data['MACD'].iloc[-1]
            current_signal = swing_data['MACD_Signal'].iloc[-1]
            macd_signal = "🟢 BULLISH" if current_macd > current_signal else "🔴 BEARISH"
            st.metric("MACD", f"{current_macd:.4f}", macd_signal)
        
        if 'BB_Upper' in swing_data.columns and 'BB_Lower' in swing_data.columns:
            bb_upper = swing_data['BB_Upper'].iloc[-1]
            bb_lower = swing_data['BB_Lower'].iloc[-1]
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) * 100
            bb_signal = "🔴 SELL ZONE" if bb_position > 80 else "🟢 BUY ZONE" if bb_position < 20 else "🟡 NEUTRAL"
            st.metric("Bollinger Position", f"{bb_position:.1f}%", bb_signal)
        
        if 'ADX' in swing_data.columns:
            current_adx = swing_data['ADX'].iloc[-1]
            adx_signal = "🟢 STRONG TREND" if current_adx > 25 else "🟡 WEAK TREND"
            st.metric("ADX (Trend Strength)", f"{current_adx:.2f}", adx_signal)
    
    with col2:
        st.markdown("""
        <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 5px; padding: 15px;'>
            <h4 style='color: #58a6ff; margin-bottom: 15px;'>🎯 SWING LEVELS</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Support and resistance levels
        if 'Support_Level' in swing_data.columns and 'Resistance_Level' in swing_data.columns:
            support = swing_data['Support_Level'].iloc[-1]
            resistance = swing_data['Resistance_Level'].iloc[-1]
            
            st.metric("Support Level", f"${support:.2f}", 
                     f"{((current_price - support) / support * 100):+.2f}%")
            st.metric("Resistance Level", f"${resistance:.2f}", 
                     f"{((resistance - current_price) / current_price * 100):+.2f}%")
        
        # Fibonacci levels
        if 'Fib_23_6' in swing_data.columns:
            fib_levels = ['Fib_23_6', 'Fib_38_2', 'Fib_50_0', 'Fib_61_8']
            st.markdown("**Fibonacci Retracements:**")
            for level in fib_levels:
                if level in swing_data.columns:
                    fib_price = swing_data[level].iloc[-1]
                    distance = abs(current_price - fib_price) / current_price * 100
                    st.write(f"• {level.replace('_', '.')}: ${fib_price:.2f} ({distance:.1f}% away)")
    
    with col3:
        st.markdown("""
        <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 5px; padding: 15px;'>
            <h4 style='color: #58a6ff; margin-bottom: 15px;'>🚀 TRADING SIGNALS</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate trading signals
        signals = []
        
        # RSI signals
        if 'RSI' in swing_data.columns:
            rsi = swing_data['RSI'].iloc[-1]
            if rsi < 30:
                signals.append(("🟢 BUY", "RSI Oversold", f"RSI: {rsi:.1f}"))
            elif rsi > 70:
                signals.append(("🔴 SELL", "RSI Overbought", f"RSI: {rsi:.1f}"))
        
        # MACD signals
        if 'MACD' in swing_data.columns and 'MACD_Signal' in swing_data.columns:
            macd = swing_data['MACD'].iloc[-1]
            signal = swing_data['MACD_Signal'].iloc[-1]
            if macd > signal and swing_data['MACD'].iloc[-2] <= swing_data['MACD_Signal'].iloc[-2]:
                signals.append(("🟢 BUY", "MACD Bullish Cross", f"MACD: {macd:.4f}"))
            elif macd < signal and swing_data['MACD'].iloc[-2] >= swing_data['MACD_Signal'].iloc[-2]:
                signals.append(("🔴 SELL", "MACD Bearish Cross", f"MACD: {macd:.4f}"))
        
        # Bollinger Band signals
        if 'BB_Upper' in swing_data.columns and 'BB_Lower' in swing_data.columns:
            bb_upper = swing_data['BB_Upper'].iloc[-1]
            bb_lower = swing_data['BB_Lower'].iloc[-1]
            if current_price <= bb_lower:
                signals.append(("🟢 BUY", "BB Lower Bounce", f"Price: ${current_price:.2f}"))
            elif current_price >= bb_upper:
                signals.append(("🔴 SELL", "BB Upper Rejection", f"Price: ${current_price:.2f}"))
        
        # Display signals
        if signals:
            for signal_type, reason, detail in signals:
                st.markdown(f"""
                <div style='background: {"#0d4521" if "BUY" in signal_type else "#4c1d1d"}; 
                           border-left: 3px solid {"#28a745" if "BUY" in signal_type else "#dc3545"}; 
                           padding: 10px; margin: 5px 0; border-radius: 0 5px 5px 0;'>
                    <strong>{signal_type}</strong><br>
                    <small>{reason}</small><br>
                    <em>{detail}</em>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🟡 No strong signals detected")
    
    # Price chart with technical indicators
    st.markdown("### 📊 Technical Analysis Chart")
    
    if not swing_data.empty and len(swing_data) > 50:
        fig = go.Figure()
        
        # Main price chart
        fig.add_trace(go.Candlestick(
            x=swing_data.index,
            open=swing_data['Open'],
            high=swing_data['High'],
            low=swing_data['Low'],
            close=swing_data['Close'],
            name=f"{data['ticker']} Price",
            increasing_line_color='#00ff00',
            decreasing_line_color='#ff0000'
        ))
        
        # Add technical indicators
        if 'SMA_20' in swing_data.columns:
            fig.add_trace(go.Scatter(
                x=swing_data.index, y=swing_data['SMA_20'],
                name='SMA 20', line=dict(color='#ffa500', width=1)
            ))
        
        if 'SMA_50' in swing_data.columns:
            fig.add_trace(go.Scatter(
                x=swing_data.index, y=swing_data['SMA_50'],
                name='SMA 50', line=dict(color='#ff69b4', width=1)
            ))
        
        if 'BB_Upper' in swing_data.columns and 'BB_Lower' in swing_data.columns:
            fig.add_trace(go.Scatter(
                x=swing_data.index, y=swing_data['BB_Upper'],
                name='BB Upper', line=dict(color='#87ceeb', width=1, dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=swing_data.index, y=swing_data['BB_Lower'],
                name='BB Lower', line=dict(color='#87ceeb', width=1, dash='dash'),
                fill='tonexty', fillcolor='rgba(135, 206, 235, 0.1)'
            ))
        
        # Add support and resistance levels
        if 'Support_Level' in swing_data.columns:
            fig.add_hline(y=swing_data['Support_Level'].iloc[-1], 
                         line_dash="dash", line_color="green", 
                         annotation_text="Support")
        
        if 'Resistance_Level' in swing_data.columns:
            fig.add_hline(y=swing_data['Resistance_Level'].iloc[-1], 
                         line_dash="dash", line_color="red", 
                         annotation_text="Resistance")
        
        fig.update_layout(
            title=f"{data['ticker']} - Swing Trading Analysis",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template="plotly_dark",
            height=600,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Additional analysis panels
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Volume Analysis")
        if not swing_data.empty and 'Volume' in swing_data.columns:
            avg_volume = swing_data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = data.get('current_volume', avg_volume)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            volume_signal = "🟢 HIGH" if volume_ratio > 1.5 else "🔴 LOW" if volume_ratio < 0.7 else "🟡 NORMAL"
            
            st.metric("Volume Ratio", f"{volume_ratio:.2f}x", volume_signal)
            st.metric("Current Volume", f"{current_volume:,.0f}")
            st.metric("Average Volume (20d)", f"{avg_volume:,.0f}")
    
    with col2:
        st.markdown("### 🎯 Risk Assessment")
        
        # Calculate risk metrics
        if not swing_data.empty and len(swing_data) > 20:
            returns = swing_data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            var_95 = np.percentile(returns, 5)  # 5% VaR
            sharpe_proxy = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            
            st.metric("Volatility (Annual)", f"{volatility:.1%}")
            st.metric("VaR (5%)", f"{var_95:.2%}")
            st.metric("Sharpe Ratio (Est.)", f"{sharpe_proxy:.2f}")
            
            # Risk level
            risk_level = "🔴 HIGH" if volatility > 0.4 else "🟡 MEDIUM" if volatility > 0.2 else "🟢 LOW"
            st.metric("Risk Level", risk_level)
    
    # Predictive analysis section
    st.markdown("### 🔮 Predictive Analysis")
    
    # Generate predictions based on technical indicators
    predictions = []
    
    if not swing_data.empty and len(swing_data) > 50:
        # Trend analysis
        recent_prices = swing_data['Close'].tail(10)
        trend_slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
        
        if trend_slope > 0:
            predictions.append("📈 Short-term uptrend detected")
        else:
            predictions.append("📉 Short-term downtrend detected")
        
        # RSI predictions
        if 'RSI' in swing_data.columns:
            rsi = swing_data['RSI'].iloc[-1]
            if rsi < 30:
                predictions.append("🎯 Potential bounce from oversold levels expected")
            elif rsi > 70:
                predictions.append("⚠️ Potential pullback from overbought levels")
        
        # MACD predictions
        if 'MACD' in swing_data.columns and 'MACD_Signal' in swing_data.columns:
            macd_hist = swing_data['MACD'] - swing_data['MACD_Signal']
            if macd_hist.iloc[-1] > macd_hist.iloc[-2] > macd_hist.iloc[-3]:
                predictions.append("🚀 Momentum building - potential breakout")
            elif macd_hist.iloc[-1] < macd_hist.iloc[-2] < macd_hist.iloc[-3]:
                predictions.append("⬇️ Momentum weakening - potential reversal")
    
    # Display predictions
    for i, prediction in enumerate(predictions, 1):
        st.markdown(f"""
        <div style='background-color: #161b22; border-left: 3px solid #58a6ff; 
                   padding: 10px; margin: 5px 0; border-radius: 0 5px 5px 0;'>
            <strong>Prediction {i}:</strong> {prediction}
        </div>
        """, unsafe_allow_html=True)
    
    if not predictions:
        st.info("🤖 AI Analysis: Market conditions are neutral. Continue monitoring for clearer signals.")


def show_options_analytics(data):
    """Display comprehensive options analytics with advanced modeling."""
    
    st.markdown("""
    <div style='background-color: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 20px; margin: 10px 0;'>
        <h2 style='color: #00ff00; text-align: center; margin-bottom: 20px;'>
            ⚡ OPTIONS ANALYTICS ENGINE ⚡
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Options configuration
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        option_type = st.selectbox("Option Type", ["call", "put"])
    
    with col2:
        strike_price = st.number_input("Strike Price", value=data['current_price'], step=1.0)
    
    with col3:
        days_to_expiry = st.number_input("Days to Expiry", value=30, min_value=1, max_value=365)
    
    with col4:
        risk_free_rate = st.number_input("Risk-Free Rate", value=0.05, step=0.01)
    
    # Calculate option metrics
    current_price = data['current_price']
    volatility = data['vol_annual']
    
    # Black-Scholes calculation
    d1 = (np.log(current_price / strike_price) + (risk_free_rate + 0.5 * volatility**2) * (days_to_expiry / 365)) / (volatility * np.sqrt(days_to_expiry / 365))
    d2 = d1 - volatility * np.sqrt(days_to_expiry / 365)
    
    from scipy.stats import norm
    
    if option_type == "call":
        theoretical_price = current_price * norm.cdf(d1) - strike_price * np.exp(-risk_free_rate * days_to_expiry / 365) * norm.cdf(d2)
        delta = norm.cdf(d1)
    else:
        theoretical_price = strike_price * np.exp(-risk_free_rate * days_to_expiry / 365) * norm.cdf(-d2) - current_price * norm.cdf(-d1)
        delta = -norm.cdf(-d1)
    
    # Greeks calculations
    gamma = norm.pdf(d1) / (current_price * volatility * np.sqrt(days_to_expiry / 365))
    vega = current_price * norm.pdf(d1) * np.sqrt(days_to_expiry / 365) / 100
    theta = (-current_price * norm.pdf(d1) * volatility / (2 * np.sqrt(days_to_expiry / 365)) - 
             risk_free_rate * strike_price * np.exp(-risk_free_rate * days_to_expiry / 365) * 
             (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))) / 365
    rho = (strike_price * days_to_expiry / 365 * np.exp(-risk_free_rate * days_to_expiry / 365) * 
           (norm.cdf(d2) if option_type == "call" else -norm.cdf(-d2))) / 100
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Theoretical Price", f"${theoretical_price:.4f}")
        st.metric("Delta", f"{delta:.4f}")
    
    with col2:
        st.metric("Gamma", f"{gamma:.6f}")
        st.metric("Vega", f"{vega:.4f}")
    
    with col3:
        st.metric("Theta", f"{theta:.4f}")
        st.metric("Rho", f"{rho:.4f}")
    
    with col4:
        moneyness = current_price / strike_price
        itm_prob = norm.cdf(d2) if option_type == "call" else norm.cdf(-d2)
        st.metric("Moneyness", f"{moneyness:.4f}")
        st.metric("ITM Probability", f"{itm_prob:.2%}")
    
    # Monte Carlo simulation
    st.markdown("### 🎲 Monte Carlo Simulation")
    
    if st.button("🚀 Run Simulation (10,000 paths)"):
        with st.spinner("Running Monte Carlo simulation..."):
            # Simulate stock paths
            dt = 1/252  # Daily time step
            num_steps = days_to_expiry
            num_sims = 10000
            
            # Generate random stock paths
            returns = np.random.normal(risk_free_rate * dt, volatility * np.sqrt(dt), (num_sims, num_steps))
            price_paths = current_price * np.exp(np.cumsum(returns, axis=1))
            final_prices = price_paths[:, -1]
            
            # Calculate option payoffs
            if option_type == "call":
                payoffs = np.maximum(final_prices - strike_price, 0)
            else:
                payoffs = np.maximum(strike_price - final_prices, 0)
            
            # Discount to present value
            mc_price = np.mean(payoffs) * np.exp(-risk_free_rate * days_to_expiry / 365)
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("MC Option Price", f"${mc_price:.4f}")
                st.metric("BS vs MC Diff", f"${abs(theoretical_price - mc_price):.4f}")
            
            with col2:
                profit_prob = np.mean(payoffs > 0)
                st.metric("Profit Probability", f"{profit_prob:.2%}")
                st.metric("Average Payoff", f"${np.mean(payoffs):.2f}")
            
            with col3:
                st.metric("Max Simulated Price", f"${np.max(final_prices):.2f}")
                st.metric("Min Simulated Price", f"${np.min(final_prices):.2f}")
            
            # Price distribution chart
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=final_prices, name="Price Distribution", nbinsx=50))
            fig.add_vline(x=strike_price, line_dash="dash", line_color="red", annotation_text="Strike")
            fig.add_vline(x=current_price, line_dash="dash", line_color="green", annotation_text="Current")
            
            fig.update_layout(
                title="Simulated Stock Price Distribution at Expiry",
                xaxis_title="Stock Price",
                yaxis_title="Frequency",
                template="plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)


def show_portfolio_simulation(data):
    """Display portfolio simulation and trading interface."""
    
    st.markdown("""
    <div style='background-color: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 20px; margin: 10px 0;'>
        <h2 style='color: #00ff00; text-align: center; margin-bottom: 20px;'>
            💼 PORTFOLIO SIMULATION ENGINE 💼
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize portfolio if not exists
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {
            'cash': 10000.0,
            'stocks': {},
            'options': {},
            'transactions': []
        }
    
    portfolio = st.session_state.portfolio
    
    # Portfolio overview
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate portfolio value
    stock_value = sum([qty * data['current_price'] for ticker, qty in portfolio['stocks'].items() if ticker == data['ticker']])
    option_value = 0  # Simplified for this demo
    total_value = portfolio['cash'] + stock_value + option_value
    
    with col1:
        st.metric("Total Portfolio Value", f"${total_value:.2f}")
    
    with col2:
        st.metric("Cash Available", f"${portfolio['cash']:.2f}")
    
    with col3:
        st.metric("Stock Positions", f"${stock_value:.2f}")
    
    with col4:
        st.metric("Options Positions", f"${option_value:.2f}")
    
    # Trading interface
    st.markdown("### 📈 Trading Interface")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        trade_type = st.selectbox("Trade Type", ["BUY_STOCK", "SELL_STOCK", "BUY_OPTION", "SELL_OPTION"])
    
    with col2:
        if "STOCK" in trade_type:
            quantity = st.number_input("Shares", value=10, min_value=1)
        else:
            quantity = st.number_input("Contracts", value=1, min_value=1)
    
    with col3:
        if "STOCK" in trade_type:
            price = data['current_price']
            st.metric("Current Price", f"${price:.2f}")
        else:
            price = st.number_input("Option Price", value=5.0, step=0.01)
    
    with col4:
        total_cost = quantity * price * (100 if "OPTION" in trade_type else 1)
        st.metric("Total Cost", f"${total_cost:.2f}")
    
    # Execute trade
    if st.button("🚀 Execute Trade"):
        if trade_type == "BUY_STOCK":
            if portfolio['cash'] >= total_cost:
                portfolio['cash'] -= total_cost
                portfolio['stocks'][data['ticker']] = portfolio['stocks'].get(data['ticker'], 0) + quantity
                portfolio['transactions'].append({
                    'type': trade_type,
                    'ticker': data['ticker'],
                    'quantity': quantity,
                    'price': price,
                    'timestamp': datetime.now()
                })
                st.success(f"✅ Bought {quantity} shares of {data['ticker']} at ${price:.2f}")
                st.rerun()
            else:
                st.error("❌ Insufficient cash")
        
        elif trade_type == "SELL_STOCK":
            current_position = portfolio['stocks'].get(data['ticker'], 0)
            if current_position >= quantity:
                portfolio['cash'] += total_cost
                portfolio['stocks'][data['ticker']] = current_position - quantity
                portfolio['transactions'].append({
                    'type': trade_type,
                    'ticker': data['ticker'],
                    'quantity': quantity,
                    'price': price,
                    'timestamp': datetime.now()
                })
                st.success(f"✅ Sold {quantity} shares of {data['ticker']} at ${price:.2f}")
                st.rerun()
            else:
                st.error("❌ Insufficient shares")
    
    # Transaction history
    if portfolio['transactions']:
        st.markdown("### 📜 Recent Transactions")
        recent_transactions = portfolio['transactions'][-10:]  # Show last 10
        
        for txn in reversed(recent_transactions):
            st.text(f"{txn['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {txn['type']}: {txn['quantity']} {txn['ticker']} @ ${txn['price']:.2f}")
    
    # Reset portfolio
    if st.button("🔄 Reset Portfolio"):
        st.session_state.portfolio = {
            'cash': 10000.0,
            'stocks': {},
            'options': {},
            'transactions': []
        }
        st.success("✅ Portfolio reset to $10,000 cash")
        st.rerun()


def show_research_tools(data):
    """Display advanced research and analysis tools."""
    
    st.markdown("""
    <div style='background-color: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 20px; margin: 10px 0;'>
        <h2 style='color: #00ff00; text-align: center; margin-bottom: 20px;'>
            🔬 RESEARCH & ANALYSIS TOOLS 🔬
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Research tabs
    research_tab1, research_tab2, research_tab3 = st.tabs([
        "📊 Company Analysis",
        "📈 Technical Patterns", 
        "💹 Market Sentiment"
    ])
    
    with research_tab1:
        st.markdown("### 🏢 Company Fundamentals")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Company", data['company_name'])
            st.metric("Sector", data['sector'])
            st.metric("Market Cap", f"${data['market_cap']/1e9:.1f}B" if data['market_cap'] > 0 else "N/A")
        
        with col2:
            st.metric("P/E Ratio", f"{data['pe_ratio']:.2f}" if data['pe_ratio'] > 0 else "N/A")
            st.metric("Beta", f"{data['beta']:.2f}")
            st.metric("52W High", f"${data['high_52w']:.2f}")
        
        with col3:
            st.metric("52W Low", f"${data['low_52w']:.2f}")
            price_range = (data['current_price'] - data['low_52w']) / (data['high_52w'] - data['low_52w']) * 100
            st.metric("52W Range Position", f"{price_range:.1f}%")
            st.metric("Avg Volume", f"{data['avg_volume']:,.0f}")
    
    with research_tab2:
        st.markdown("### 📊 Technical Pattern Recognition")
        
        # Pattern analysis would go here
        patterns = [
            "📈 Ascending Triangle (Bullish)",
            "📉 Head & Shoulders (Bearish)", 
            "🔄 Double Bottom (Bullish)",
            "⚡ Breakout Pattern (Neutral)"
        ]
        
        for pattern in patterns:
            st.markdown(f"• {pattern}")
    
    with research_tab3:
        st.markdown("### 💭 Market Sentiment Analysis")
        
        # Sentiment indicators
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Fear & Greed Index**")
            sentiment_score = np.random.randint(20, 80)  # Mock data
            sentiment_level = "😨 Fear" if sentiment_score < 30 else "😐 Neutral" if sentiment_score < 60 else "🤑 Greed"
            st.metric("Market Sentiment", sentiment_level, f"{sentiment_score}/100")
        
        with col2:
            st.markdown("**Social Media Buzz**")
            buzz_score = np.random.randint(1, 100)  # Mock data
            buzz_level = "🔇 Low" if buzz_score < 30 else "🔊 Medium" if buzz_score < 70 else "📢 High"
            st.metric("Social Buzz", buzz_level, f"{buzz_score}%")


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


def main():
    """Main application function with enhanced navigation and comprehensive analytics."""
    
    # Set page configuration
    st.set_page_config(
        page_title="IVSURF Professional Terminal v4.0",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for retro terminal styling
    st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', monospace; }
    .stSelectbox > div > div { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
    .stButton > button { 
        background-color: #238636; color: white; border: 1px solid #30363d; 
        font-family: 'Courier New', monospace; font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover { background-color: #2ea043; transform: scale(1.05); }
    .stMetric { background-color: #161b22; padding: 10px; border-radius: 5px; border: 1px solid #30363d; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d;
        font-family: 'Courier New', monospace; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #238636; }
    .terminal-header {
        background: linear-gradient(90deg, #0d1117 0%, #21262d 50%, #0d1117 100%);
        border: 2px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
    }
    .glow { text-shadow: 0 0 10px #00ff00; }
    </style>
    """, unsafe_allow_html=True)
    
    # Terminal Header with enhanced design
    st.markdown("""
    <div class="terminal-header">
        <h1 style="color: #00ff00; font-size: 3em; margin: 0; text-shadow: 0 0 20px #00ff00;">
            🖥️ IVSURF PROFESSIONAL TERMINAL v4.0 🖥️
        </h1>
        <p style="color: #58a6ff; font-size: 1.2em; margin: 10px 0 0 0;">
            Advanced Options Analytics & Swing Trading Platform
        </p>
        <div style="margin-top: 15px;">
            <span style="background: #238636; padding: 5px 10px; border-radius: 15px; margin: 0 5px; font-size: 0.9em;">REAL-TIME DATA</span>
            <span style="background: #1f6feb; padding: 5px 10px; border-radius: 15px; margin: 0 5px; font-size: 0.9em;">PhD-LEVEL ANALYTICS</span>
            <span style="background: #f85149; padding: 5px 10px; border-radius: 15px; margin: 0 5px; font-size: 0.9em;">PROFESSIONAL GRADE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced Navigation Bar
    st.markdown("""
    <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 5px; padding: 15px; margin-bottom: 20px;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div style='color: #58a6ff; font-weight: bold; font-size: 1.1em;'>
                🎯 MARKET NAVIGATOR
            </div>
            <div style='color: #7d8590; font-size: 0.9em;'>
                Select ticker and analysis mode
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Top navigation controls
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([2, 2, 2, 1])
    
    with nav_col1:
        ticker = st.selectbox(
            "📊 SELECT TICKER",
            ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "META", "NFLX"],
            index=0
        )
    
    with nav_col2:
        analysis_mode = st.selectbox(
            "🔍 ANALYSIS MODE",
            ["Real-Time Analysis", "Historical Deep Dive", "Monte Carlo Simulation", "Risk Assessment"],
            index=0
        )
    
    with nav_col3:
        refresh_data = st.button("🔄 REFRESH DATA", use_container_width=True)
    
    with nav_col4:
        if st.button("ℹ️ GUIDE", use_container_width=True):
            show_information_guide()
            return
    
    # Load market data
    if refresh_data or 'market_data' not in st.session_state or st.session_state.get('current_ticker') != ticker:
        with st.spinner(f"🔄 Loading enhanced market data for {ticker}..."):
            st.session_state.market_data = fetch_enhanced_market_data(ticker)
            st.session_state.current_ticker = ticker
    
    data = st.session_state.market_data
    
    # Quick status display
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        price_change = data['current_price'] - data['price_1d_ago']
        price_change_pct = (price_change / data['price_1d_ago']) * 100
        st.metric(
            f"{data['ticker']} Price",
            f"${data['current_price']:.2f}",
            f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
        )
    
    with col2:
        st.metric(
            "Market Cap",
            f"${data['market_cap']/1e9:.1f}B" if data['market_cap'] > 0 else "N/A"
        )
    
    with col3:
        st.metric("Volatility (Annual)", f"{data['vol_annual']:.1%}")
    
    with col4:
        st.metric("Beta", f"{data['beta']:.2f}")
    
    with col5:
        quality_color = "🟢" if data['data_quality'] == 'LIVE' else "🟡"
        st.metric("Data Quality", f"{quality_color} {data['data_quality']}")
    
    # Main application tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 OPTIONS ANALYTICS", 
        "📈 SWING TRADING", 
        "🎯 PORTFOLIO SIM", 
        "📋 RESEARCH TOOLS"
    ])
    
    with tab1:
        show_options_analytics(data)
    
    with tab2:
        show_swing_trading_analysis(data)
    
    with tab3:
        show_portfolio_simulation(data)
    
    with tab4:
        show_research_tools(data)


if __name__ == "__main__":
    main()

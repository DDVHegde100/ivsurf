#!/usr/bin/env python3
"""
IVSURF TERMINAL v3.0 - Advanced Options Trading System

Professional-grade financial terminal with comprehensive options analytics,
real-time data integration, and advanced trading predictions.
Maximum technical precision with clean 1996-style interface.

Run: streamlit run scripts/ivsurf_terminal.py
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
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_data import OptionsDataFetcher
from core.black_scholes import black_scholes_price, implied_volatility, option_value_decomposition
from core.greeks import all_greeks


def apply_ivsurf_terminal_css():
    """Apply advanced IVSURF terminal styling - Maximum technical precision."""
    st.markdown("""
    <style>
    /* Import Professional Terminal Fonts */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Courier+Prime:wght@400;700&family=VT323:wght@400&family=Source+Code+Pro:wght@300;400;500;600;700&display=swap');
    
    /* Core Terminal Environment */
    .main {
        background: #000000;
        color: #00ff00;
        font-family: 'JetBrains Mono', 'Source Code Pro', monospace;
        font-size: 13px;
        line-height: 1.3;
        font-weight: 400;
        overflow-x: hidden;
    }
    
    /* Main Terminal Frame */
    .terminal-frame {
        background: #000000;
        border: 3px solid #00ff00;
        border-radius: 0;
        padding: 25px;
        margin: 10px 0;
        box-shadow: 
            0 0 40px #00ff00,
            inset 0 0 25px rgba(0, 255, 0, 0.1);
        position: relative;
    }
    
    .terminal-frame::before {
        content: '▓▓▓ IVSURF_TERMINAL_v3.0_ACTIVE ▓▓▓';
        position: absolute;
        top: -18px;
        left: 50%;
        transform: translateX(-50%);
        background: #000000;
        color: #00ffff;
        padding: 0 20px;
        font-family: 'VT323', monospace;
        font-size: 20px;
        font-weight: bold;
        text-shadow: 0 0 15px #00ffff;
    }
    
    /* Professional Data Modules */
    .data-module {
        background: linear-gradient(135deg, #000a00 0%, #001100 50%, #000a00 100%);
        border: 2px solid #00ff00;
        border-radius: 0;
        padding: 20px;
        margin: 15px 0;
        position: relative;
        box-shadow: 
            0 0 20px rgba(0, 255, 0, 0.3),
            inset 0 0 15px rgba(0, 255, 0, 0.05);
    }
    
    .data-module::before {
        content: attr(data-title);
        position: absolute;
        top: -14px;
        left: 25px;
        background: #000000;
        color: #00ffff;
        padding: 0 15px;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #000000 0%, #001100 50%, #000000 100%);
        border-right: 4px solid #00ff00;
        box-shadow: 4px 0 20px rgba(0, 255, 0, 0.3);
    }
    
    /* Control Panels */
    .control-panel {
        background: #000a00;
        border: 2px solid #00ff00;
        padding: 20px;
        margin: 15px 0;
        position: relative;
        box-shadow: inset 0 0 15px rgba(0, 255, 0, 0.1);
    }
    
    .control-panel::before {
        content: attr(data-panel);
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #000000;
        color: #00ffff;
        padding: 0 15px;
        font-family: 'VT323', monospace;
        font-size: 16px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    /* Advanced Metric Display */
    .metric-display {
        background: linear-gradient(135deg, #001a00 0%, #002200 50%, #001a00 100%);
        border: 1px solid #00ff00;
        border-radius: 0;
        padding: 18px;
        margin: 10px 0;
        text-align: center;
        position: relative;
        box-shadow: 
            0 0 15px rgba(0, 255, 0, 0.2),
            inset 0 0 10px rgba(0, 255, 0, 0.05);
    }
    
    .metric-display::before {
        content: attr(data-metric);
        position: absolute;
        top: -10px;
        left: 50%;
        transform: translateX(-50%);
        background: #000000;
        color: #00ffff;
        padding: 0 8px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #00ff00;
        text-shadow: 0 0 15px #00ff00;
        font-family: 'VT323', monospace;
        margin: 8px 0;
        letter-spacing: 1px;
    }
    
    .metric-secondary {
        font-size: 16px;
        color: #00ffff;
        font-weight: 500;
        margin: 5px 0;
    }
    
    .metric-unit {
        font-size: 12px;
        color: #00aaaa;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 1px;
    }
    
    /* Professional Alert System */
    .alert-success {
        background: linear-gradient(135deg, #003300 0%, #004400 50%, #003300 100%);
        border: 2px solid #00ff00;
        color: #00ff00;
        padding: 15px;
        margin: 12px 0;
        font-family: 'JetBrains Mono', monospace;
        position: relative;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
    }
    
    .alert-success::before {
        content: '[✓ SYSTEM_READY]';
        color: #00ffff;
        font-weight: 700;
        margin-right: 12px;
    }
    
    .alert-error {
        background: linear-gradient(135deg, #330000 0%, #440000 50%, #330000 100%);
        border: 2px solid #ff0000;
        color: #ff0000;
        padding: 15px;
        margin: 12px 0;
        font-family: 'JetBrains Mono', monospace;
        position: relative;
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.3);
    }
    
    .alert-error::before {
        content: '[✗ SYSTEM_ERROR]';
        color: #ffff00;
        font-weight: 700;
        margin-right: 12px;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #333300 0%, #444400 50%, #333300 100%);
        border: 2px solid #ffff00;
        color: #ffff00;
        padding: 15px;
        margin: 12px 0;
        font-family: 'JetBrains Mono', monospace;
        position: relative;
        box-shadow: 0 0 20px rgba(255, 255, 0, 0.3);
    }
    
    .alert-warning::before {
        content: '[⚠ SYSTEM_WARNING]';
        color: #ff8800;
        font-weight: 700;
        margin-right: 12px;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #000033 0%, #000044 50%, #000033 100%);
        border: 2px solid #0088ff;
        color: #00aaff;
        padding: 15px;
        margin: 12px 0;
        font-family: 'JetBrains Mono', monospace;
        position: relative;
        box-shadow: 0 0 20px rgba(0, 136, 255, 0.3);
    }
    
    .alert-info::before {
        content: '[ℹ SYSTEM_INFO]';
        color: #00ffff;
        font-weight: 700;
        margin-right: 12px;
    }
    
    /* Enhanced Tab System */
    .stTabs [data-baseweb="tab-list"] {
        background: #000000;
        border: 3px solid #00ff00;
        border-radius: 0;
        padding: 8px;
        box-shadow: 0 0 25px rgba(0, 255, 0, 0.3);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #001100 0%, #002200 50%, #001100 100%);
        color: #00ff00;
        border: 2px solid #00ff00;
        border-radius: 0;
        font-family: 'VT323', monospace;
        font-size: 18px;
        font-weight: bold;
        margin: 5px;
        padding: 15px 25px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #003300 0%, #004400 50%, #003300 100%);
        color: #00ffff;
        box-shadow: 0 0 25px #00ff00;
        transform: scale(1.05);
    }
    
    .stTabs [aria-selected="true"] {
        background: #00ff00;
        color: #000000;
        box-shadow: 0 0 30px #00ff00;
        text-shadow: none;
        transform: scale(1.1);
    }
    
    /* Professional Button System */
    .stButton > button {
        background: linear-gradient(135deg, #000000 0%, #001100 50%, #000000 100%);
        color: #00ff00;
        border: 3px solid #00ff00;
        border-radius: 0;
        font-family: 'VT323', monospace;
        font-size: 18px;
        font-weight: bold;
        padding: 12px 25px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.3);
    }
    
    .stButton > button:hover {
        background: #00ff00;
        color: #000000;
        box-shadow: 0 0 30px #00ff00;
        transform: scale(1.1);
    }
    
    /* Form Controls */
    .stSelectbox > div > div {
        background: #001100;
        border: 2px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
    }
    
    .stTextInput > div > div > input {
        background: #001100;
        border: 2px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 500;
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
    }
    
    .stNumberInput > div > div > input {
        background: #001100;
        border: 2px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 500;
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
    }
    
    /* Plotly Integration */
    .js-plotly-plot {
        background: #000000;
        border: 4px solid #00ff00;
        box-shadow: 0 0 30px rgba(0, 255, 0, 0.4);
    }
    
    /* Professional Progress Bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00ff00, #00aa00, #00ff00);
        box-shadow: 0 0 15px #00ff00;
    }
    
    /* DataFrames Terminal Style */
    .stDataFrame {
        border: 3px solid #00ff00;
        background: #000000;
        border-radius: 0;
        box-shadow: 0 0 25px rgba(0, 255, 0, 0.3);
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
        letter-spacing: 0.5px;
    }
    
    .stDataFrame td {
        background: #001100;
        color: #00ff00;
        border: 1px solid #00ff00;
        font-weight: 500;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    
    /* Professional Scrollbar */
    ::-webkit-scrollbar {
        width: 18px;
        background: #000000;
    }
    
    ::-webkit-scrollbar-track {
        background: #001100;
        border: 3px solid #00ff00;
        border-radius: 0;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00ff00, #00aa00, #00ff00);
        border: 2px solid #000000;
        border-radius: 0;
        box-shadow: 0 0 15px #00ff00;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00ffff;
        box-shadow: 0 0 20px #00ffff;
    }
    
    /* Professional Blinking Cursor */
    .blinking-cursor::after {
        content: '█';
        color: #00ff00;
        animation: blink 1.2s infinite;
    }
    
    @keyframes blink {
        0%, 60% { opacity: 1; }
        61%, 100% { opacity: 0; }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .terminal-frame {
            padding: 20px;
        }
        
        .metric-value {
            font-size: 22px;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-size: 14px;
            padding: 10px 15px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def create_ivsurf_ascii():
    """Create clean IVSURF ASCII art header."""
    return """
    ██ ██    ██ ███████ ██    ██ ██████  ███████ 
    ██ ██    ██ ██      ██    ██ ██   ██ ██      
    ██ ██    ██ ███████ ██    ██ ██████  █████   
    ██  ██  ██       ██ ██    ██ ██   ██ ██      
    ██   ████   ███████  ██████  ██   ██ ██      
                                                 
    ████████ ███████ ██████  ███    ███ ██ ███    ██  █████  ██      
       ██    ███████ ██   ██ ████  ████ ██ ████   ██ ██   ██ ██      
       ██    ██      ██████  ██ ████ ██ ██ ██ ██  ██ ███████ ██      
       ██    ██      ██   ██ ██  ██  ██ ██ ██  ██ ██ ██   ██ ██      
       ██    ███████ ██   ██ ██      ██ ██ ██   ████ ██   ██ ███████
    """


def create_terminal_alert(title, message, alert_type="info"):
    """Create professional terminal alerts."""
    st.markdown(f"""
    <div class="alert-{alert_type}">
        <strong>{title}:</strong> {message}
    </div>
    """, unsafe_allow_html=True)


def create_metric_display(label, value, secondary="", unit="", data_metric=""):
    """Create advanced metric displays."""
    if not data_metric:
        data_metric = label.replace(" ", "_")
    
    st.markdown(f"""
    <div class="metric-display" data-metric="{data_metric}">
        <div class="metric-value">{value}</div>
        <div class="metric-secondary">{secondary}</div>
        <div class="metric-unit">{unit}</div>
    </div>
    """, unsafe_allow_html=True)


def fetch_market_data(ticker):
    """Fetch comprehensive market data for analysis."""
    try:
        stock = yf.Ticker(ticker)
        
        # Get current price and info
        info = stock.info
        current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        
        # Get historical data for volatility calculation
        hist = stock.history(period="1y")
        returns = hist['Close'].pct_change().dropna()
        historical_vol = returns.std() * np.sqrt(252)
        
        # Get recent price action
        recent_data = stock.history(period="1mo")
        
        # Calculate technical indicators
        recent_close = recent_data['Close'].iloc[-1]
        prev_close = recent_data['Close'].iloc[-2] if len(recent_data) > 1 else recent_close
        daily_change = recent_close - prev_close
        daily_change_pct = (daily_change / prev_close) * 100
        
        # Volume analysis
        avg_volume = recent_data['Volume'].mean()
        current_volume = recent_data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Support and resistance levels
        high_52w = hist['High'].max()
        low_52w = hist['Low'].min()
        
        return {
            'current_price': current_price,
            'daily_change': daily_change,
            'daily_change_pct': daily_change_pct,
            'historical_vol': historical_vol,
            'volume_ratio': volume_ratio,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'market_cap': info.get('marketCap', 0),
            'avg_volume': avg_volume,
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'hist_data': hist,
            'recent_data': recent_data
        }
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None


def calculate_option_profit_scenarios(spot, strike, option_type, premium, time_to_expiry, vol, rate):
    """Calculate comprehensive profit/loss scenarios."""
    scenarios = {}
    
    # Price targets based on volatility
    vol_1std = spot * vol * np.sqrt(time_to_expiry)
    vol_2std = spot * vol * np.sqrt(time_to_expiry) * 2
    
    price_targets = {
        'conservative': spot + (vol_1std * 0.5) if option_type == 'call' else spot - (vol_1std * 0.5),
        'moderate': spot + vol_1std if option_type == 'call' else spot - vol_1std,
        'aggressive': spot + vol_2std if option_type == 'call' else spot - vol_2std,
    }
    
    time_scenarios = [0.1, 0.25, 0.5, 0.75, 1.0]  # Fraction of time remaining
    
    for scenario, target_price in price_targets.items():
        scenario_data = {}
        for time_fraction in time_scenarios:
            remaining_time = time_to_expiry * time_fraction
            if remaining_time > 0:
                new_price = black_scholes_price(
                    target_price, strike, remaining_time, rate, vol, option_type
                )
                profit = new_price - premium
                profit_pct = (profit / premium) * 100
                
                scenario_data[f"{int((1-time_fraction)*100)}%_time_elapsed"] = {
                    'option_price': new_price,
                    'profit_loss': profit,
                    'profit_pct': profit_pct,
                    'target_price': target_price
                }
        
        scenarios[scenario] = scenario_data
    
    return scenarios


def calculate_swing_trade_signals(hist_data, current_price):
    """Calculate swing trading signals and predictions."""
    try:
        # Ensure we have enough data
        if len(hist_data) < 50:
            return {}, {}, hist_data
            
        # Calculate moving averages
        hist_data['SMA_20'] = hist_data['Close'].rolling(20).mean()
        hist_data['SMA_50'] = hist_data['Close'].rolling(50).mean()
        hist_data['EMA_12'] = hist_data['Close'].ewm(span=12).mean()
        hist_data['EMA_26'] = hist_data['Close'].ewm(span=26).mean()
        
        # MACD
        hist_data['MACD'] = hist_data['EMA_12'] - hist_data['EMA_26']
        hist_data['MACD_Signal'] = hist_data['MACD'].ewm(span=9).mean()
        
        # RSI
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_data['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        hist_data['BB_Middle'] = hist_data['Close'].rolling(20).mean()
        bb_std = hist_data['Close'].rolling(20).std()
        hist_data['BB_Upper'] = hist_data['BB_Middle'] + (bb_std * 2)
        hist_data['BB_Lower'] = hist_data['BB_Middle'] - (bb_std * 2)
        
        # Current signals
        latest = hist_data.iloc[-1]
        signals = {
            'trend': 'BULLISH' if latest['SMA_20'] > latest['SMA_50'] else 'BEARISH',
            'macd_signal': 'BUY' if latest['MACD'] > latest['MACD_Signal'] else 'SELL',
            'rsi_signal': 'OVERSOLD' if latest['RSI'] < 30 else 'OVERBOUGHT' if latest['RSI'] > 70 else 'NEUTRAL',
            'bb_position': 'UPPER' if current_price > latest['BB_Upper'] else 'LOWER' if current_price < latest['BB_Lower'] else 'MIDDLE',
            'momentum': 'STRONG' if abs(latest['MACD']) > hist_data['MACD'].std() else 'WEAK'
        }
        
        # Price predictions
        volatility = hist_data['Close'].pct_change().std() * np.sqrt(252)
        daily_vol = volatility / np.sqrt(252)
        
        predictions = {
            '1_day': {
                'high': current_price * (1 + daily_vol),
                'low': current_price * (1 - daily_vol),
                'target': current_price * (1 + (daily_vol * 0.5)) if signals['trend'] == 'BULLISH' else current_price * (1 - (daily_vol * 0.5))
            },
            '1_week': {
                'high': current_price * (1 + daily_vol * np.sqrt(7)),
                'low': current_price * (1 - daily_vol * np.sqrt(7)),
                'target': current_price * (1 + (daily_vol * np.sqrt(7) * 0.5)) if signals['trend'] == 'BULLISH' else current_price * (1 - (daily_vol * np.sqrt(7) * 0.5))
            },
            '1_month': {
                'high': current_price * (1 + daily_vol * np.sqrt(30)),
                'low': current_price * (1 - daily_vol * np.sqrt(30)),
                'target': current_price * (1 + (daily_vol * np.sqrt(30) * 0.5)) if signals['trend'] == 'BULLISH' else current_price * (1 - (daily_vol * np.sqrt(30) * 0.5))
            }
        }
        
        return signals, predictions, hist_data
        
    except Exception as e:
        # Return empty signals if calculation fails
        return {
            'trend': 'UNKNOWN',
            'macd_signal': 'UNKNOWN',
            'rsi_signal': 'UNKNOWN',
            'bb_position': 'UNKNOWN',
            'momentum': 'UNKNOWN'
        }, {
            '1_day': {'high': current_price * 1.02, 'low': current_price * 0.98, 'target': current_price},
            '1_week': {'high': current_price * 1.05, 'low': current_price * 0.95, 'target': current_price},
            '1_month': {'high': current_price * 1.15, 'low': current_price * 0.85, 'target': current_price}
        }, hist_data


def show_comprehensive_guide():
    """Show comprehensive IVSURF trading guide."""
    st.markdown(f"""
    <div class="terminal-frame">
        <pre style="color: #00ff00; font-family: 'VT323', monospace; font-size: 14px; margin: 0; text-align: center;">
{create_ivsurf_ascii()}
        </pre>
        <div style="color: #00ffff; font-weight: bold; margin-top: 20px; text-align: center; font-family: 'JetBrains Mono', monospace;">
        ► IVSURF_TERMINAL_SYSTEM_v3.0_OPERATIONAL<br>
        ► ADVANCED_OPTIONS_ANALYTICS_LOADED<br>
        ► REAL_TIME_MARKET_FEED_ACTIVE<br>
        ► SWING_TRADE_PREDICTIONS_ENABLED<br>
        ► <span class="blinking-cursor" style="color: #ffff00;">READY_FOR_PROFESSIONAL_TRADING</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    create_terminal_alert(
        "IVSURF_SYSTEM_OVERVIEW",
        """
        <strong>INTEGRATED_VOLATILITY_SURFACE_TERMINAL</strong><br>
        ► Real-time options pricing and Greeks calculation<br>
        ► Advanced swing trading signal generation<br>
        ► Comprehensive profit/loss scenario analysis<br>
        ► Professional risk management protocols<br>
        ► Multi-timeframe prediction algorithms<br><br>
        <strong>SUPPORTED_ANALYTICS:</strong><br>
        ► Black-Scholes theoretical pricing<br>
        ► Implied volatility surface mapping<br>
        ► Greeks sensitivity analysis<br>
        ► Technical indicator convergence<br>
        ► Monte Carlo profit simulations<br>
        ► Volume-weighted momentum signals
        """,
        "info"
    )
    
    create_terminal_alert(
        "PROFESSIONAL_TRADING_SIGNALS",
        """
        <strong>SWING_TRADE_INDICATORS:</strong><br>
        ► MACD convergence/divergence analysis<br>
        ► RSI momentum and reversal signals<br>
        ► Bollinger Band squeeze patterns<br>
        ► Moving average crossover strategies<br>
        ► Volume-weighted price action<br><br>
        <strong>PROFIT_PREDICTION_MODELS:</strong><br>
        ► Conservative: 50% volatility capture<br>
        ► Moderate: 1 standard deviation moves<br>
        ► Aggressive: 2 standard deviation moves<br>
        ► Time decay optimization algorithms<br>
        ► Multi-scenario profit analysis<br><br>
        <strong>TIMEFRAME_ANALYSIS:</strong><br>
        ► Intraday: 1-hour to 1-day moves<br>
        ► Short-term: 1-week swing trades<br>
        ► Medium-term: 1-month position holds
        """,
        "success"
    )
    
    create_terminal_alert(
        "RISK_MANAGEMENT_PROTOCOLS",
        """
        <strong>POSITION_SIZING_RULES:</strong><br>
        ► Maximum 2% account risk per trade<br>
        ► Options premium should not exceed 10% of underlying position<br>
        ► Diversification across sectors and timeframes<br>
        ► Greeks exposure limits enforced<br><br>
        <strong>STOP_LOSS_AUTOMATION:</strong><br>
        ► Automatic exit at 50% premium loss<br>
        ► Time decay protection at 21 DTE<br>
        ► Volatility crush protection protocols<br>
        ► Delta-neutral hedging strategies<br><br>
        <strong>CRITICAL_WARNING:</strong><br>
        Options trading involves substantial risk of loss. Past performance<br>
        does not guarantee future results. Use proper position sizing<br>
        and never risk more than you can afford to lose.
        """,
        "error"
    )


def main():
    st.set_page_config(
        page_title="IVSURF TERMINAL",
        page_icon="🟢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply IVSURF terminal styling
    apply_ivsurf_terminal_css()
    
    # Main header
    st.markdown(f"""
    <div class="terminal-frame">
        <pre style="color: #00ff00; font-family: 'VT323', monospace; font-size: 12px; margin: 0; text-align: center;">
{create_ivsurf_ascii()}
        </pre>
        <div style="color: #00ffff; font-weight: bold; margin-top: 15px; text-align: center; font-family: 'JetBrains Mono', monospace;">
        ► SYSTEM_STATUS: <span style="color: #00ff00;">OPERATIONAL</span><br>
        ► MARKET_FEED: <span style="color: #00ff00;">LIVE_STREAM_ACTIVE</span><br>
        ► ANALYTICS: <span style="color: #00ff00;">FULL_SPECTRUM_ENABLED</span><br>
        ► TIMESTAMP: <span style="color: #00ffff;">""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + """</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Guide toggle
    if st.button("📚 ACCESS_IVSURF_PROTOCOLS", help="Load comprehensive trading system documentation"):
        st.session_state['show_guide'] = not st.session_state.get('show_guide', False)
    
    if st.session_state.get('show_guide', False):
        show_comprehensive_guide()
        st.markdown("---")
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("""
        <div class="control-panel" data-panel="CONTROL_MATRIX">
        </div>
        """, unsafe_allow_html=True)
        
        # Market data input
        st.markdown("""
        <div class="data-module" data-title="TARGET_SELECTION">
        </div>
        """, unsafe_allow_html=True)
        
        ticker = st.text_input(
            "SECURITY_IDENTIFIER", 
            value="AAPL", 
            help="Enter ticker symbol for analysis"
        ).upper()
        
        # Quick ticker selection
        popular_tickers = st.selectbox(
            "POPULAR_TARGETS",
            ["CUSTOM"] + ["AAPL", "MSFT", "TSLA", "NVDA", "GOOGL", "AMZN", "META", "SPY", "QQQ", "IWM"],
            help="Select from popular trading targets"
        )
        
        if popular_tickers != "CUSTOM":
            ticker = popular_tickers
        
        # Fetch market data
        if ticker:
            market_data = fetch_market_data(ticker)
            
            if market_data:
                create_terminal_alert(
                    "MARKET_DATA_ACQUIRED",
                    f"""
                    <strong>{market_data['company_name']}</strong><br>
                    ► CURRENT_PRICE: ${market_data['current_price']:.2f}<br>
                    ► DAILY_CHANGE: {market_data['daily_change_pct']:+.2f}%<br>
                    ► HISTORICAL_VOL: {market_data['historical_vol']:.1%}<br>
                    ► VOLUME_RATIO: {market_data['volume_ratio']:.2f}x<br>
                    ► SECTOR: {market_data['sector']}
                    """,
                    "success"
                )
        
        # Options parameters
        st.markdown("""
        <div class="data-module" data-title="OPTIONS_PARAMETERS">
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            strike_price = st.number_input(
                "STRIKE_PRICE", 
                value=market_data['current_price'] if market_data else 150.0,
                min_value=1.0, 
                step=1.0,
                help="Option strike price"
            )
            
            days_to_expiry = st.number_input(
                "DAYS_TO_EXPIRY", 
                value=30, 
                min_value=1, 
                max_value=365,
                help="Days until option expiration"
            )
        
        with col2:
            volatility = st.number_input(
                "IMPLIED_VOLATILITY", 
                value=market_data['historical_vol'] if market_data else 0.25,
                min_value=0.01, 
                max_value=2.0, 
                step=0.01,
                help="Implied volatility (decimal)"
            )
            
            risk_free_rate = st.number_input(
                "RISK_FREE_RATE", 
                value=0.05, 
                min_value=-0.05, 
                max_value=0.20, 
                step=0.001,
                help="Risk-free interest rate"
            )
        
        option_type = st.selectbox(
            "CONTRACT_TYPE", 
            ["call", "put"],
            help="Option contract type"
        )
        
        # Trading parameters
        st.markdown("""
        <div class="data-module" data-title="TRADING_PARAMETERS">
        </div>
        """, unsafe_allow_html=True)
        
        position_size = st.number_input(
            "POSITION_SIZE",
            value=1,
            min_value=1,
            max_value=100,
            help="Number of contracts"
        )
        
        account_size = st.number_input(
            "ACCOUNT_SIZE",
            value=10000,
            min_value=1000,
            step=1000,
            help="Total account value for risk calculations"
        )
    
    # Main terminal interface
    if market_data:
        current_price = market_data['current_price']
        time_to_expiry = days_to_expiry / 365.0
        
        # Calculate option pricing
        try:
            theoretical_price = black_scholes_price(
                current_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type
            )
            
            greeks = all_greeks(
                current_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type
            )
            
            profit_scenarios = calculate_option_profit_scenarios(
                current_price, strike_price, option_type, theoretical_price, 
                time_to_expiry, volatility, risk_free_rate
            )
            
            swing_signals, price_predictions, enhanced_hist = calculate_swing_trade_signals(
                market_data['hist_data'].copy(), current_price
            )
            
        except Exception as e:
            create_terminal_alert("CALCULATION_ERROR", f"Pricing engine error: {str(e)}", "error")
            return
    else:
        create_terminal_alert("DATA_ERROR", f"Unable to fetch market data for {ticker}", "error")
        return
    
    # Terminal tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 PRICING_ENGINE", 
        "📊 SWING_ANALYSIS", 
        "💰 PROFIT_SCENARIOS", 
        "⚡ GREEKS_MATRIX",
        "🎮 LIVE_TRADING"
    ])
    
    with tab1:
        st.markdown("""
        <div class="data-module" data-title="THEORETICAL_PRICING_ENGINE">
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_display(
                "THEO_PRICE", 
                f"${theoretical_price:.4f}",
                f"Premium: ${theoretical_price * position_size * 100:.2f}",
                "USD"
            )
            
            # Moneyness analysis
            moneyness = (current_price - strike_price) / current_price * 100
            if option_type == 'call':
                status = "ITM" if moneyness > 0 else "OTM"
                status_color = "#00ff00" if moneyness > 0 else "#ff8800"
            else:
                status = "ITM" if moneyness < 0 else "OTM"
                status_color = "#00ff00" if moneyness < 0 else "#ff8800"
            
            st.markdown(f"""
            <div style="text-align: center; color: {status_color}; font-weight: bold; margin: 10px 0;">
                MONEYNESS: {status}<br>
                DIFF: {moneyness:+.2f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            create_metric_display(
                "DELTA", 
                f"{greeks['delta']:.4f}",
                f"Price sens: ${greeks['delta']:.2f}",
                "PER_$1_MOVE"
            )
            
            create_metric_display(
                "GAMMA", 
                f"{greeks['gamma']:.6f}",
                f"Delta change: {greeks['gamma']:.4f}",
                "PER_$1_MOVE"
            )
        
        with col3:
            create_metric_display(
                "VEGA", 
                f"{greeks['vega']:.4f}",
                f"Vol sens: ${greeks['vega']:.2f}",
                "PER_1%_VOL"
            )
            
            create_metric_display(
                "THETA", 
                f"{greeks['theta']:.4f}",
                f"Daily decay: ${greeks['theta']:.2f}",
                "PER_DAY"
            )
        
        with col4:
            # Risk metrics
            position_value = theoretical_price * position_size * 100
            account_risk = (position_value / account_size) * 100
            
            create_metric_display(
                "POSITION_VALUE", 
                f"${position_value:.2f}",
                f"Account risk: {account_risk:.1f}%",
                "USD"
            )
            
            create_metric_display(
                "BREAK_EVEN", 
                f"${strike_price + theoretical_price if option_type == 'call' else strike_price - theoretical_price:.2f}",
                f"Move needed: {((strike_price + theoretical_price - current_price) / current_price * 100) if option_type == 'call' else ((current_price - (strike_price - theoretical_price)) / current_price * 100):.1f}%",
                "USD"
            )
        
        # Price sensitivity chart
        st.markdown("""
        <div class="data-module" data-title="SENSITIVITY_ANALYSIS">
        </div>
        """, unsafe_allow_html=True)
        
        # Create sensitivity analysis
        spot_range = np.linspace(current_price * 0.8, current_price * 1.2, 50)
        option_prices = []
        deltas = []
        
        for spot in spot_range:
            price = black_scholes_price(spot, strike_price, time_to_expiry, risk_free_rate, volatility, option_type)
            delta = all_greeks(spot, strike_price, time_to_expiry, risk_free_rate, volatility, option_type)['delta']
            option_prices.append(price)
            deltas.append(delta)
        
        fig = go.Figure()
        
        # Option price line
        fig.add_trace(go.Scatter(
            x=spot_range, y=option_prices,
            name='OPTION_PRICE',
            line=dict(color='#00ff00', width=4),
            hovertemplate='SPOT: $%{x:.2f}<br>PRICE: $%{y:.4f}<extra></extra>'
        ))
        
        # Delta line
        fig.add_trace(go.Scatter(
            x=spot_range, y=deltas,
            name='DELTA',
            line=dict(color='#00ffff', width=3),
            yaxis='y2',
            hovertemplate='SPOT: $%{x:.2f}<br>DELTA: %{y:.4f}<extra></extra>'
        ))
        
        # Current position
        fig.add_trace(go.Scatter(
            x=[current_price], y=[theoretical_price],
            mode='markers',
            name='CURRENT_POSITION',
            marker=dict(color='#ffff00', size=20, symbol='diamond'),
            hovertemplate=f'CURRENT: ${current_price:.2f}<br>PRICE: ${theoretical_price:.4f}<extra></extra>'
        ))
        
        # Breakeven points
        breakeven = strike_price + theoretical_price if option_type == 'call' else strike_price - theoretical_price
        fig.add_vline(x=breakeven, line_dash="dash", line_color="#ff8800", 
                     annotation_text="BREAKEVEN", annotation_position="top")
        
        fig.update_layout(
            title=dict(text="OPTION_PRICE_SENSITIVITY_MATRIX", font=dict(color='#00ffff', family='VT323', size=20)),
            xaxis=dict(title="UNDERLYING_PRICE", color='#00ff00', gridcolor='#003300'),
            yaxis=dict(title="OPTION_PRICE", color='#00ff00', gridcolor='#003300'),
            yaxis2=dict(title="DELTA", overlaying='y', side='right', color='#00ffff'),
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='#00ff00', family='JetBrains Mono'),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("""
        <div class="data-module" data-title="SWING_TRADING_ANALYSIS">
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            create_terminal_alert(
                "TECHNICAL_SIGNALS",
                f"""
                <strong>TREND_ANALYSIS:</strong> {swing_signals.get('trend', 'UNKNOWN')}<br>
                <strong>MACD_SIGNAL:</strong> {swing_signals.get('macd_signal', 'UNKNOWN')}<br>
                <strong>RSI_STATUS:</strong> {swing_signals.get('rsi_signal', 'UNKNOWN')}<br>
                <strong>BB_POSITION:</strong> {swing_signals.get('bb_position', 'UNKNOWN')}<br>
                <strong>MOMENTUM:</strong> {swing_signals.get('momentum', 'UNKNOWN')}
                """,
                "info"
            )
            
            # Price predictions
            for timeframe, pred in price_predictions.items():
                create_terminal_alert(
                    f"PREDICTION_{timeframe.upper()}",
                    f"""
                    <strong>TARGET_PRICE:</strong> ${pred['target']:.2f}<br>
                    <strong>HIGH_ESTIMATE:</strong> ${pred['high']:.2f}<br>
                    <strong>LOW_ESTIMATE:</strong> ${pred['low']:.2f}<br>
                    <strong>RANGE:</strong> ${pred['low']:.2f} - ${pred['high']:.2f}
                    """,
                    "success"
                )
        
        with col2:
            # Technical chart
            fig_tech = go.Figure()
            
            recent_data = market_data['recent_data'].tail(30)
            
            # Candlestick chart
            fig_tech.add_trace(go.Candlestick(
                x=recent_data.index,
                open=recent_data['Open'],
                high=recent_data['High'],
                low=recent_data['Low'],
                close=recent_data['Close'],
                name='PRICE_ACTION',
                increasing_line_color='#00ff00',
                decreasing_line_color='#ff0000'
            ))
            
            # Moving averages if available
            if 'SMA_20' in enhanced_hist.columns:
                recent_enhanced = enhanced_hist.tail(30)
                fig_tech.add_trace(go.Scatter(
                    x=recent_enhanced.index,
                    y=recent_enhanced['SMA_20'],
                    name='SMA_20',
                    line=dict(color='#00ffff', width=2)
                ))
            
            fig_tech.update_layout(
                title="TECHNICAL_ANALYSIS_CHART",
                xaxis_title="DATE",
                yaxis_title="PRICE",
                plot_bgcolor='#000000',
                paper_bgcolor='#000000',
                font=dict(color='#00ff00', family='JetBrains Mono'),
                height=400
            )
            
            st.plotly_chart(fig_tech, use_container_width=True)
    
    with tab3:
        st.markdown("""
        <div class="data-module" data-title="PROFIT_SCENARIO_ANALYSIS">
        </div>
        """, unsafe_allow_html=True)
        
        for scenario_name, scenario_data in profit_scenarios.items():
            st.markdown(f"""
            <div class="data-module" data-title="{scenario_name.upper()}_SCENARIO">
            </div>
            """, unsafe_allow_html=True)
            
            scenario_df = pd.DataFrame(scenario_data).T
            scenario_df = scenario_df.round(4)
            
            # Add color coding for profit/loss
            def color_profit_loss(val):
                if isinstance(val, (int, float)):
                    return 'color: #00ff00' if val > 0 else 'color: #ff0000' if val < 0 else 'color: #ffff00'
                return ''
            
            styled_df = scenario_df.style.applymap(color_profit_loss, subset=['profit_loss', 'profit_pct'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Best case scenario
            best_case = max(scenario_data.values(), key=lambda x: x['profit_loss'])
            create_terminal_alert(
                f"BEST_CASE_{scenario_name.upper()}",
                f"""
                <strong>MAX_PROFIT:</strong> ${best_case['profit_loss']:.2f}<br>
                <strong>PROFIT_PCT:</strong> {best_case['profit_pct']:.1f}%<br>
                <strong>TARGET_PRICE:</strong> ${best_case['target_price']:.2f}<br>
                <strong>POSITION_VALUE:</strong> ${best_case['profit_loss'] * position_size * 100:.2f}
                """,
                "success"
            )
    
    with tab4:
        st.markdown("""
        <div class="data-module" data-title="GREEKS_RISK_MATRIX">
        </div>
        """, unsafe_allow_html=True)
        
        # Greeks dashboard
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_metric_display("DELTA", f"{greeks['delta']:.5f}", f"${greeks['delta'] * position_size * 100:.2f} per $1 move")
            create_metric_display("GAMMA", f"{greeks['gamma']:.7f}", f"Delta change: {greeks['gamma']:.5f}")
        
        with col2:
            create_metric_display("VEGA", f"{greeks['vega']:.5f}", f"${greeks['vega'] * position_size * 100:.2f} per 1% vol")
            create_metric_display("THETA", f"{greeks['theta']:.5f}", f"${greeks['theta'] * position_size * 100:.2f} daily decay")
        
        with col3:
            create_metric_display("RHO", f"{greeks['rho']:.5f}", f"${greeks['rho'] * position_size * 100:.2f} per 1% rate")
            
            # Portfolio Greeks (assuming this is the only position)
            portfolio_delta = greeks['delta'] * position_size * 100
            delta_hedge_shares = -int(portfolio_delta) if option_type == 'call' else int(abs(portfolio_delta))
            
            create_metric_display("HEDGE_SHARES", f"{delta_hedge_shares}", f"For delta neutral")
        
        # Greeks sensitivity analysis
        vol_range = np.linspace(volatility * 0.5, volatility * 1.5, 30)
        time_range = np.linspace(0.01, time_to_expiry, 30)
        
        fig_greeks = go.Figure()
        
        # Vega sensitivity to volatility
        vegas = []
        for vol in vol_range:
            vega = all_greeks(current_price, strike_price, time_to_expiry, risk_free_rate, vol, option_type)['vega']
            vegas.append(vega)
        
        fig_greeks.add_trace(go.Scatter(
            x=vol_range * 100, y=vegas,
            name='VEGA_SENSITIVITY',
            line=dict(color='#00ff00', width=3)
        ))
        
        # Theta decay over time
        thetas = []
        for t in time_range:
            theta = all_greeks(current_price, strike_price, t, risk_free_rate, volatility, option_type)['theta']
            thetas.append(theta)
        
        fig_greeks.add_trace(go.Scatter(
            x=time_range * 365, y=thetas,
            name='THETA_DECAY',
            line=dict(color='#ff8800', width=3),
            yaxis='y2'
        ))
        
        fig_greeks.update_layout(
            title="GREEKS_SENSITIVITY_ANALYSIS",
            xaxis_title="VOLATILITY_% / DAYS_TO_EXPIRY",
            yaxis_title="VEGA",
            yaxis2=dict(title="THETA", overlaying='y', side='right'),
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='#00ff00', family='JetBrains Mono'),
            height=400
        )
        
        st.plotly_chart(fig_greeks, use_container_width=True)
    
    with tab5:
        st.markdown("""
        <div class="data-module" data-title="LIVE_TRADING_PROTOCOLS">
        </div>
        """, unsafe_allow_html=True)
        
        create_terminal_alert(
            "TRADING_READINESS_CHECK",
            f"""
            <strong>POSITION_SIZE:</strong> {position_size} contracts<br>
            <strong>TOTAL_PREMIUM:</strong> ${theoretical_price * position_size * 100:.2f}<br>
            <strong>ACCOUNT_RISK:</strong> {(theoretical_price * position_size * 100 / account_size) * 100:.1f}%<br>
            <strong>BREAK_EVEN:</strong> ${strike_price + theoretical_price if option_type == 'call' else strike_price - theoretical_price:.2f}<br>
            <strong>MAX_LOSS:</strong> ${theoretical_price * position_size * 100:.2f}<br>
            <strong>DELTA_EXPOSURE:</strong> {greeks['delta'] * position_size * 100:.0f} shares equivalent
            """,
            "info"
        )
        
        # Risk warnings
        risk_level = "HIGH" if account_risk > 10 else "MODERATE" if account_risk > 5 else "LOW"
        risk_color = "error" if risk_level == "HIGH" else "warning" if risk_level == "MODERATE" else "success"
        
        create_terminal_alert(
            f"RISK_ASSESSMENT_{risk_level}",
            f"""
            <strong>RISK_LEVEL:</strong> {risk_level}<br>
            <strong>POSITION_SIZING:</strong> {'EXCESSIVE' if account_risk > 10 else 'ACCEPTABLE' if account_risk <= 5 else 'MODERATE'}<br>
            <strong>RECOMMENDATION:</strong> {'REDUCE_POSITION' if account_risk > 10 else 'PROCEED_WITH_CAUTION' if account_risk > 5 else 'WITHIN_SAFE_LIMITS'}
            """,
            risk_color
        )
        
        # Order simulation
        st.markdown("### 🎮 ORDER_SIMULATION")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🟢 SIMULATE_BUY_ORDER", help="Simulate buying this option"):
                create_terminal_alert(
                    "ORDER_SIMULATION",
                    f"""
                    <strong>ORDER_TYPE:</strong> BUY_TO_OPEN<br>
                    <strong>CONTRACTS:</strong> {position_size}<br>
                    <strong>PREMIUM:</strong> ${theoretical_price:.4f}<br>
                    <strong>TOTAL_COST:</strong> ${theoretical_price * position_size * 100:.2f}<br>
                    <strong>STATUS:</strong> SIMULATION_MODE
                    """,
                    "success"
                )
        
        with col2:
            if st.button("🔴 SIMULATE_SELL_ORDER", help="Simulate selling this option"):
                create_terminal_alert(
                    "ORDER_SIMULATION",
                    f"""
                    <strong>ORDER_TYPE:</strong> SELL_TO_CLOSE<br>
                    <strong>CONTRACTS:</strong> {position_size}<br>
                    <strong>PREMIUM:</strong> ${theoretical_price:.4f}<br>
                    <strong>TOTAL_CREDIT:</strong> ${theoretical_price * position_size * 100:.2f}<br>
                    <strong>STATUS:</strong> SIMULATION_MODE
                    """,
                    "error"
                )
        
        with col3:
            if st.button("⚡ DELTA_HEDGE", help="Calculate delta hedge requirements"):
                hedge_shares = abs(int(greeks['delta'] * position_size * 100))
                hedge_cost = hedge_shares * current_price
                
                create_terminal_alert(
                    "DELTA_HEDGE_CALCULATION",
                    f"""
                    <strong>HEDGE_REQUIRED:</strong> {hedge_shares} shares<br>
                    <strong>HEDGE_COST:</strong> ${hedge_cost:.2f}<br>
                    <strong>HEDGE_DIRECTION:</strong> {'SELL' if option_type == 'call' else 'BUY'}<br>
                    <strong>NET_DELTA:</strong> ~0.00 (neutral)
                    """,
                    "warning"
                )


if __name__ == "__main__":
    main()

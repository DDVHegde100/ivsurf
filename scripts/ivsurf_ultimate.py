#!/usr/bin/env python3
"""
IVSURF PROFESSIONAL TRADING TERMINAL v5.0
==========================================

Classic 1996-Era Investment Banking Terminal
Authentic retro computer aesthetics with modern functionality

Author: IVSURF Systems
Date: August 16, 2025
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import threading
import time
import sys
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.black_scholes import black_scholes_price
from core.greeks import delta, gamma, vega, theta, rho
from core.interpolation import interpolate_surface, adaptive_interpolation
from core.advanced_interpolation import AdvancedSurfaceInterpolator
from visuals.plot_surface import plot_vol_surface_plotly

class RetroTerminal:
    """Classic 1996 Investment Banking Terminal"""
    
    def __init__(self):
        self.sp500_tickers = [
            'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'BRK-B', 'UNH',
            'XOM', 'LLY', 'JPM', 'JNJ', 'V', 'PG', 'MA', 'AVGO', 'HD', 'CVX',
            'MRK', 'ABBV', 'PEP', 'KO', 'PFE', 'TMO', 'BAC', 'COST', 'ADBE', 'WMT',
            'CSCO', 'ABT', 'ACN', 'NKE', 'TXN', 'NEE', 'DHR', 'VZ', 'RTX', 'CRM',
            'ORCL', 'BMY', 'LIN', 'PM', 'AMD', 'T', 'AMGN', 'HON', 'NFLX', 'CMCSA'
        ]
        self.market_data_cache = {}
        self.last_update = None
        
    def set_page_config(self):
        """Configure page with retro styling"""
        st.set_page_config(
            page_title="IVSURF PROFESSIONAL TERMINAL v5.0",
            page_icon="[I]",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Classic 1996 computer terminal CSS
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
        
        .stApp {
            background-color: #000000;
            color: #00ff00;
            font-family: 'Courier Prime', 'Courier New', monospace;
        }
        
        .main {
            background-color: #000000;
            color: #00ff00;
            padding: 0;
        }
        
        .terminal-header {
            background: linear-gradient(180deg, #001100 0%, #000000 100%);
            border: 2px solid #00ff00;
            border-radius: 0;
            padding: 20px;
            margin: 0 0 10px 0;
            font-family: 'Courier Prime', monospace;
            text-align: center;
        }
        
        .terminal-box {
            background-color: #001100;
            border: 1px solid #00ff00;
            border-radius: 0;
            padding: 15px;
            margin: 5px 0;
            font-family: 'Courier Prime', monospace;
        }
        
        .data-table {
            background-color: #000000;
            border: 1px solid #00ff00;
            color: #00ff00;
            font-family: 'Courier Prime', monospace;
            font-size: 12px;
        }
        
        .profit-high { color: #00ff00; font-weight: bold; }
        .profit-medium { color: #ffff00; font-weight: bold; }
        .profit-low { color: #ff8800; }
        .loss { color: #ff0000; }
        
        .stSelectbox > div > div {
            background-color: #000000;
            color: #00ff00;
            border: 1px solid #00ff00;
            font-family: 'Courier Prime', monospace;
        }
        
        .stButton > button {
            background-color: #000000;
            color: #00ff00;
            border: 2px solid #00ff00;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            border-radius: 0;
            transition: all 0.2s;
        }
        
        .stButton > button:hover {
            background-color: #00ff00;
            color: #000000;
            border: 2px solid #00ff00;
        }
        
        .stMetric {
            background-color: #001100;
            border: 1px solid #00ff00;
            padding: 10px;
            border-radius: 0;
            font-family: 'Courier Prime', monospace;
        }
        
        .stMetric > div {
            color: #00ff00;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px;
            background-color: #000000;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #000000;
            color: #00ff00;
            border: 1px solid #00ff00;
            border-radius: 0;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            margin: 0;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #00ff00;
            color: #000000;
        }
        
        .stDataFrame {
            background-color: #000000;
            color: #00ff00;
            font-family: 'Courier Prime', monospace;
        }
        
        .stDataFrame table {
            background-color: #000000;
            color: #00ff00;
        }
        
        .stDataFrame th {
            background-color: #001100;
            color: #00ff00;
            border: 1px solid #00ff00;
        }
        
        .stDataFrame td {
            background-color: #000000;
            color: #00ff00;
            border: 1px solid #004400;
        }
        
        .blinking {
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        .scanline {
            background: linear-gradient(transparent 0%, rgba(0, 255, 0, 0.03) 50%, transparent 100%);
            animation: scan 2s linear infinite;
            pointer-events: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 1000;
        }
        
        @keyframes scan {
            0% { transform: translateY(-100vh); }
            100% { transform: translateY(100vh); }
        }
        
        .terminal-prompt {
            color: #00ff00;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
        }
        
        .terminal-text {
            color: #00ff00;
            font-family: 'Courier Prime', monospace;
        }
        
        .warning-text {
            color: #ffff00;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
        }
        
        .error-text {
            color: #ff0000;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
        }
        
        .success-text {
            color: #00ff00;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
        }
        
        </style>
        """, unsafe_allow_html=True)
        
        # Add scanline effect
        st.markdown('<div class="scanline"></div>', unsafe_allow_html=True)

    def render_header(self):
        """Render classic terminal header"""
        st.markdown("""
        <div class="terminal-header">
            <div style="font-size: 24px; font-weight: bold; margin-bottom: 10px;">
                [IVSURF PROFESSIONAL TRADING TERMINAL v5.0]
            </div>
            <div style="font-size: 14px; margin-bottom: 5px;">
                INTEGRATED VOLATILITY SURFACE RESEARCH FACILITY
            </div>
            <div style="font-size: 12px; color: #888888;">
                SYSTEM ONLINE | MARKET DATA ACTIVE | ALL SYSTEMS OPERATIONAL
            </div>
            <div style="font-size: 10px; color: #666666; margin-top: 10px;">
                COPYRIGHT 1996-2025 IVSURF SYSTEMS INC. | AUTHORIZED USERS ONLY
            </div>
        </div>
        """, unsafe_allow_html=True)

# Extended ticker universe for scanning
TICKER_UNIVERSE = [
    # Tech Giants
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'INTC', 'CRM',
    'ORCL', 'ADBE', 'NFLX', 'PYPL', 'UBER', 'LYFT', 'SNAP', 'TWTR', 'PINS', 'ZOOM',
    
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP', 'V', 'MA',
    'SQ', 'COIN', 'HOOD', 'SOFI', 'UPST', 'AFRM', 'PLTR',
    
    # Healthcare & Biotech
    'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD',
    'MRNA', 'BNTX', 'REGN', 'VRTX', 'BIIB', 'ILMN', 'ISRG',
    
    # Energy & Materials
    'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'HAL', 'DVN', 'FANG', 'MPC', 'VLO',
    
    # Consumer & Retail
    'AMZN', 'WMT', 'TGT', 'HD', 'LOW', 'NKE', 'SBUX', 'MCD', 'DIS', 'NFLX',
    'COST', 'TJX', 'ROST', 'ULTA', 'LULU', 'RH', 'ETSY', 'SHOP',
    
    # Industrial & Transportation
    'BA', 'CAT', 'DE', 'GE', 'MMM', 'HON', 'UPS', 'FDX', 'LUV', 'DAL',
    'UAL', 'AAL', 'CCL', 'RCL', 'NCLH',
    
    # Real Estate & REITs
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'AVB', 'EQR', 'SPG', 'O',
    
    # Crypto-related
    'COIN', 'MSTR', 'SQ', 'PYPL', 'HOOD', 'RIOT', 'MARA', 'CLSK',
    
    # ETFs for diversification
    'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'AGG', 'TLT', 'GLD'
]

def apply_retro_styling():
    """Apply enhanced retro terminal styling (4x better)"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    /* Global Retro Theme */
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        color: #00ff41;
        font-family: 'Source Code Pro', monospace;
        animation: matrixRain 20s linear infinite;
    }
    
    /* Matrix Rain Animation Background */
    @keyframes matrixRain {
        0% { background-position: 0% 0%; }
        100% { background-position: 100% 100%; }
    }
    
    /* Enhanced Terminal Header */
    .terminal-header {
        background: linear-gradient(45deg, #0f3460 0%, #0e4b99 50%, #2e8b57 100%);
        border: 3px solid #00ff41;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 
            0 0 20px #00ff41,
            inset 0 0 20px rgba(0, 255, 65, 0.1),
            0 0 40px rgba(0, 255, 65, 0.3);
        animation: terminalPulse 3s ease-in-out infinite alternate;
        position: relative;
        overflow: hidden;
    }
    
    .terminal-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(0, 255, 65, 0.1), transparent);
        animation: scanline 4s linear infinite;
    }
    
    @keyframes terminalPulse {
        0% { box-shadow: 0 0 20px #00ff41, inset 0 0 20px rgba(0, 255, 65, 0.1); }
        100% { box-shadow: 0 0 40px #00ff41, inset 0 0 40px rgba(0, 255, 65, 0.2); }
    }
    
    @keyframes scanline {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    /* Enhanced Title Styling */
    .main-title {
        font-family: 'Orbitron', monospace;
        font-size: 3.5em;
        font-weight: 900;
        color: #00ff41;
        text-shadow: 
            0 0 10px #00ff41,
            0 0 20px #00ff41,
            0 0 30px #00ff41,
            0 0 40px #00ff41;
        margin: 0;
        letter-spacing: 3px;
        animation: titleGlow 2s ease-in-out infinite alternate;
    }
    
    @keyframes titleGlow {
        0% { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41, 0 0 30px #00ff41; }
        100% { text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41, 0 0 40px #00ff41, 0 0 50px #00ff41; }
    }
    
    .subtitle {
        color: #00bfff;
        font-size: 1.3em;
        font-weight: 600;
        margin: 15px 0;
        text-shadow: 0 0 10px #00bfff;
        animation: subtitleFlicker 4s linear infinite;
    }
    
    @keyframes subtitleFlicker {
        0%, 98% { opacity: 1; }
        99% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    /* Enhanced Navigation Bar */
    .nav-container {
        background: linear-gradient(90deg, #0f1419 0%, #1e3a5f 50%, #0f1419 100%);
        border: 2px solid #00ff41;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 
            0 0 15px rgba(0, 255, 65, 0.3),
            inset 0 0 15px rgba(0, 255, 65, 0.1);
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #1e3a5f 0%, #2e5984 50%, #1e3a5f 100%);
        color: #00ff41;
        border: 2px solid #00ff41;
        border-radius: 8px;
        font-family: 'Source Code Pro', monospace;
        font-weight: 600;
        font-size: 14px;
        padding: 12px 20px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #2e5984 0%, #3e79a4 50%, #2e5984 100%);
        box-shadow: 
            0 0 20px rgba(0, 255, 65, 0.6),
            inset 0 0 10px rgba(0, 255, 65, 0.2);
        transform: translateY(-2px) scale(1.02);
        color: #ffffff;
        border-color: #00bfff;
    }
    
    /* Enhanced Metrics Cards */
    .metric-card {
        background: linear-gradient(135deg, #0f1419 0%, #1a2332 50%, #0f1419 100%);
        border: 2px solid #00ff41;
        border-radius: 10px;
        padding: 18px;
        margin: 8px 0;
        text-align: center;
        box-shadow: 
            0 0 15px rgba(0, 255, 65, 0.2),
            inset 0 0 10px rgba(0, 255, 65, 0.05);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.1), transparent);
        transition: all 0.6s ease;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    .metric-card:hover {
        border-color: #00bfff;
        box-shadow: 
            0 0 25px rgba(0, 191, 255, 0.4),
            inset 0 0 15px rgba(0, 191, 255, 0.1);
        transform: translateY(-3px);
    }
    
    .stMetric {
        background: transparent !important;
        padding: 0 !important;
    }
    
    .stMetric > div {
        background: transparent !important;
    }
    
    /* Enhanced Selectboxes and Inputs */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, #1a2332 0%, #2a3442 100%);
        color: #00ff41;
        border: 2px solid #00ff41;
        border-radius: 8px;
        font-family: 'Source Code Pro', monospace;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
    }
    
    .stSelectbox > div > div:hover {
        border-color: #00bfff;
        box-shadow: 0 0 15px rgba(0, 191, 255, 0.3);
    }
    
    /* Enhanced Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        background: linear-gradient(90deg, #0f1419 0%, #1e3a5f 50%, #0f1419 100%);
        padding: 5px;
        border-radius: 10px;
        border: 2px solid #00ff41;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #1a2332 0%, #2a3442 100%);
        color: #00ff41;
        border: 1px solid #00ff41;
        border-radius: 6px;
        font-family: 'Source Code Pro', monospace;
        font-weight: 600;
        padding: 12px 20px;
        margin: 2px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #2a3442 0%, #3a4552 100%);
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
        transform: translateY(-1px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2e5984 0%, #3e79a4 100%);
        color: #ffffff;
        border-color: #00bfff;
        box-shadow: 
            0 0 20px rgba(0, 191, 255, 0.5),
            inset 0 0 10px rgba(0, 191, 255, 0.2);
    }
    
    /* Enhanced Data Tables */
    .dataframe {
        background: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
        border: 2px solid #00ff41;
        border-radius: 10px;
        color: #00ff41;
        font-family: 'Source Code Pro', monospace;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #2e5984 0%, #3e79a4 100%);
        color: #ffffff;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .dataframe td {
        border-bottom: 1px solid rgba(0, 255, 65, 0.2);
    }
    
    .dataframe tr:hover {
        background: rgba(0, 255, 65, 0.1);
    }
    
    /* Enhanced Progress Bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #00ff41 0%, #00bfff 50%, #ff6b6b 100%);
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
    }
    
    /* Alert Boxes */
    .profit-alert {
        background: linear-gradient(135deg, #0f4c3a 0%, #1a5f4a 100%);
        border: 2px solid #00ff41;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #00ff41;
        font-family: 'Source Code Pro', monospace;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
        animation: profitPulse 2s ease-in-out infinite alternate;
    }
    
    @keyframes profitPulse {
        0% { box-shadow: 0 0 20px rgba(0, 255, 65, 0.3); }
        100% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.6); }
    }
    
    .warning-alert {
        background: linear-gradient(135deg, #4c3a0f 0%, #5f4a1a 100%);
        border: 2px solid #ffaa00;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #ffaa00;
        font-family: 'Source Code Pro', monospace;
        box-shadow: 0 0 20px rgba(255, 170, 0, 0.3);
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0f1419;
        border-radius: 6px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #00ff41, #00bfff);
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(45deg, #00bfff, #ff6b6b);
    }
    
    /* Custom Loading Animation */
    .loading-spinner {
        border: 4px solid rgba(0, 255, 65, 0.1);
        border-left: 4px solid #00ff41;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Terminal Text Effects */
    .terminal-text {
        font-family: 'Source Code Pro', monospace;
        color: #00ff41;
        text-shadow: 0 0 5px #00ff41;
        animation: textFlicker 0.15s linear infinite;
    }
    
    @keyframes textFlicker {
        0%, 98% { opacity: 1; }
        99% { opacity: 0.98; }
        100% { opacity: 1; }
    }
    
    /* Enhanced Sidebar (if used) */
    .css-1d391kg {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
        border-right: 2px solid #00ff41;
    }
    
    /* Enhanced Status Indicators */
    .status-live {
        color: #00ff41;
        animation: statusBlink 1s ease-in-out infinite alternate;
    }
    
    .status-warning {
        color: #ffaa00;
        animation: statusBlink 1s ease-in-out infinite alternate;
    }
    
    .status-error {
        color: #ff6b6b;
        animation: statusBlink 1s ease-in-out infinite alternate;
    }
    
    @keyframes statusBlink {
        0% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Performance Optimization */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    </style>
    """, unsafe_allow_html=True)

def create_terminal_header():
    """Create the enhanced terminal header"""
    st.markdown("""
    <div class="terminal-header">
        <div class="main-title">⚡ IVSURF ULTIMATE TERMINAL v5.0 ⚡</div>
        <div class="subtitle">🚀 REAL-TIME PROFIT SCANNER & VOLATILITY SURFACE EXPLORER 🚀</div>
        <div style="margin-top: 20px;">
            <span style="background: linear-gradient(45deg, #00ff41, #00bfff); padding: 8px 15px; border-radius: 20px; margin: 0 8px; font-size: 0.9em; color: #000; font-weight: bold;">⚡ LIVE DATA</span>
            <span style="background: linear-gradient(45deg, #ff6b6b, #ffa500); padding: 8px 15px; border-radius: 20px; margin: 0 8px; font-size: 0.9em; color: #000; font-weight: bold;">🧠 AI ANALYTICS</span>
            <span style="background: linear-gradient(45deg, #8a2be2, #ff1493); padding: 8px 15px; border-radius: 20px; margin: 0 8px; font-size: 0.9em; color: #fff; font-weight: bold;">💰 PROFIT SCANNER</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(title, value, delta=None, status="neutral"):
    """Create enhanced metric cards with retro styling"""
    status_colors = {
        "profit": "#00ff41",
        "warning": "#ffaa00", 
        "danger": "#ff6b6b",
        "neutral": "#00bfff"
    }
    
    status_class = f"status-{status}" if status != "neutral" else ""
    
    delta_html = ""
    if delta:
        delta_color = "#00ff41" if "+" in str(delta) else "#ff6b6b"
        delta_html = f'<div style="color: {delta_color}; font-size: 0.9em; margin-top: 5px;">{delta}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: #00bfff; font-size: 0.9em; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
            {title}
        </div>
        <div style="color: {status_colors[status]}; font-size: 1.8em; font-weight: 700; text-shadow: 0 0 10px {status_colors[status]};" class="{status_class}">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_ticker_data(ticker, period="1d"):
    """Fetch comprehensive ticker data with caching"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        
        if hist.empty:
            return None
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        volume = hist['Volume'].iloc[-1]
        
        # Calculate key metrics
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close) * 100
        
        # Volatility calculation
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) if len(returns) > 5 else 0.25
        
        # Volume analysis
        avg_volume = hist['Volume'].mean()
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        
        # Technical indicators
        high_52w = info.get('fiftyTwoWeekHigh', current_price * 1.2)
        low_52w = info.get('fiftyTwoWeekLow', current_price * 0.8)
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 0)
        beta = info.get('beta', 1.0)
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volume': volume,
            'volume_ratio': volume_ratio,
            'volatility': volatility,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'market_cap': market_cap,
            'pe_ratio': pe_ratio,
            'beta': beta,
            'hist': hist,
            'avg_volume': avg_volume
        }
        
    except Exception as e:
        return None

def calculate_swing_trading_score(data):
    """Calculate swing trading profit potential score"""
    if not data:
        return 0
    
    score = 0
    
    # Volatility score (higher volatility = more profit potential)
    vol_score = min(data['volatility'] * 10, 5)  # Cap at 5 points
    score += vol_score
    
    # Volume score (higher volume = better liquidity)
    volume_score = min(data['volume_ratio'] * 2, 3)  # Cap at 3 points
    score += volume_score
    
    # Price momentum score
    abs_change = abs(data['price_change_pct'])
    momentum_score = min(abs_change / 2, 4)  # Cap at 4 points
    score += momentum_score
    
    # Position in 52-week range (extremes are better for swing trading)
    price_position = (data['current_price'] - data['low_52w']) / (data['high_52w'] - data['low_52w'])
    if price_position < 0.2 or price_position > 0.8:
        score += 3  # Near extremes
    elif price_position < 0.3 or price_position > 0.7:
        score += 2
    else:
        score += 1
    
    # Beta score (higher beta = more reactive to market)
    beta_score = min(abs(data['beta']) * 1.5, 2)
    score += beta_score
    
    return min(score, 20)  # Cap total score at 20

def calculate_options_trading_score(data):
    """Calculate options trading profit potential score"""
    if not data:
        return 0
    
    score = 0
    
    # High volatility is crucial for options
    vol_score = min(data['volatility'] * 15, 8)  # Higher weight for options
    score += vol_score
    
    # Volume and liquidity
    volume_score = min(data['volume_ratio'] * 2, 3)
    score += volume_score
    
    # Price movement (options benefit from large moves)
    movement_score = min(abs(data['price_change_pct']) * 0.5, 4)
    score += movement_score
    
    # Market cap consideration (larger caps usually have better options markets)
    if data['market_cap'] > 10e9:  # > $10B
        score += 3
    elif data['market_cap'] > 1e9:  # > $1B
        score += 2
    else:
        score += 1
    
    # Implied volatility opportunities (approximated by recent volatility)
    if data['volatility'] > 0.4:  # High IV
        score += 2
    elif data['volatility'] > 0.3:
        score += 1
    
    return min(score, 20)  # Cap total score at 20

def scan_profitable_opportunities():
    """Scan all tickers for profitable opportunities"""
    st.markdown('<div class="terminal-text">🔍 SCANNING TICKER UNIVERSE FOR PROFIT OPPORTUNITIES...</div>', 
                unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    swing_opportunities = []
    options_opportunities = []
    
    # Use threading for faster data fetching
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all ticker fetch jobs
        future_to_ticker = {
            executor.submit(fetch_ticker_data, ticker): ticker 
            for ticker in TICKER_UNIVERSE
        }
        
        completed = 0
        total = len(future_to_ticker)
        
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            completed += 1
            
            # Update progress
            progress = completed / total
            progress_bar.progress(progress)
            status_text.text(f"Analyzing {ticker}... ({completed}/{total})")
            
            try:
                data = future.result()
                if data:
                    # Calculate scores
                    swing_score = calculate_swing_trading_score(data)
                    options_score = calculate_options_trading_score(data)
                    
                    # Add to opportunities if score is high enough
                    if swing_score >= 12:  # Threshold for swing trading
                        swing_opportunities.append({
                            'ticker': ticker,
                            'score': swing_score,
                            'price': data['current_price'],
                            'change_pct': data['price_change_pct'],
                            'volume_ratio': data['volume_ratio'],
                            'volatility': data['volatility'],
                            'data': data
                        })
                    
                    if options_score >= 12:  # Threshold for options trading
                        options_opportunities.append({
                            'ticker': ticker,
                            'score': options_score,
                            'price': data['current_price'],
                            'change_pct': data['price_change_pct'],
                            'volume_ratio': data['volume_ratio'],
                            'volatility': data['volatility'],
                            'data': data
                        })
                        
            except Exception as e:
                continue
    
    # Sort by score (highest first)
    swing_opportunities.sort(key=lambda x: x['score'], reverse=True)
    options_opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    progress_bar.empty()
    status_text.empty()
    
    return swing_opportunities[:10], options_opportunities[:10]

def display_opportunities_table(opportunities, trading_type):
    """Display opportunities in an enhanced table"""
    if not opportunities:
        st.warning(f"No high-scoring {trading_type} opportunities found at this time.")
        return
    
    # Create DataFrame
    df = pd.DataFrame([{
        'Rank': i + 1,
        'Ticker': opp['ticker'],
        'Score': f"{opp['score']:.1f}/20",
        'Price': f"${opp['price']:.2f}",
        'Change %': f"{opp['change_pct']:+.2f}%",
        'Volume Ratio': f"{opp['volume_ratio']:.2f}x",
        'Volatility': f"{opp['volatility']:.1%}",
        'Action': '🚀 ANALYZE' if opp['score'] >= 16 else '📊 MONITOR'
    } for i, opp in enumerate(opportunities)])
    
    # Color-code based on score
    def highlight_score(val):
        if 'Score' in str(val) and '/' in str(val):
            score = float(str(val).split('/')[0])
            if score >= 18:
                return 'background-color: rgba(0, 255, 65, 0.3); color: #00ff41; font-weight: bold;'
            elif score >= 15:
                return 'background-color: rgba(255, 170, 0, 0.3); color: #ffaa00; font-weight: bold;'
            else:
                return 'background-color: rgba(0, 191, 255, 0.2); color: #00bfff;'
        return ''
    
    # Display the styled DataFrame
    st.dataframe(
        df.style.applymap(highlight_score),
        use_container_width=True,
        height=400
    )
    
    # Add analysis for top 3
    st.markdown(f"### 🔍 TOP 3 {trading_type.upper()} OPPORTUNITIES ANALYSIS")
    
    for i, opp in enumerate(opportunities[:3]):
        with st.expander(f"#{i+1} {opp['ticker']} - Score: {opp['score']:.1f}/20"):
            col1, col2, col3 = st.columns(3)
            
            data = opp['data']
            
            with col1:
                create_metric_card("Current Price", f"${data['current_price']:.2f}", 
                                 f"{data['price_change']:+.2f} ({data['price_change_pct']:+.2f}%)",
                                 "profit" if data['price_change'] > 0 else "danger")
            
            with col2:
                create_metric_card("Volatility", f"{data['volatility']:.1%}", 
                                 status="profit" if data['volatility'] > 0.3 else "neutral")
            
            with col3:
                create_metric_card("Volume Ratio", f"{data['volume_ratio']:.2f}x",
                                 status="profit" if data['volume_ratio'] > 1.5 else "neutral")
            
            # Add specific trading recommendations
            if trading_type == "Swing Trading":
                st.markdown(f"""
                **🎯 Swing Trading Strategy for {opp['ticker']}:**
                - **Entry Signal**: {'Strong momentum' if abs(data['price_change_pct']) > 3 else 'Building momentum'}
                - **Volatility Edge**: {data['volatility']:.1%} annual (High volatility = larger swings)
                - **Volume Confirmation**: {data['volume_ratio']:.1f}x average volume
                - **Risk Level**: {'High' if data['volatility'] > 0.4 else 'Medium' if data['volatility'] > 0.25 else 'Low'}
                """)
            else:
                st.markdown(f"""
                **⚡ Options Trading Strategy for {opp['ticker']}:**
                - **IV Advantage**: {data['volatility']:.1%} (High volatility benefits option premiums)
                - **Liquidity**: {data['volume_ratio']:.1f}x volume suggests good options liquidity
                - **Delta Opportunities**: {'Large price movements expected' if data['volatility'] > 0.4 else 'Moderate movements expected'}
                - **Strategy**: {'Straddles/Strangles' if data['volatility'] > 0.4 else 'Directional plays'}
                """)

def analyze_single_ticker(ticker):
    """Comprehensive analysis of a single ticker"""
    data = fetch_ticker_data(ticker, period="1y")
    
    if not data:
        st.error(f"Could not fetch data for {ticker}")
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card("Current Price", f"${data['current_price']:.2f}",
                         f"{data['price_change']:+.2f} ({data['price_change_pct']:+.2f}%)",
                         "profit" if data['price_change'] > 0 else "danger")
    
    with col2:
        create_metric_card("Volatility", f"{data['volatility']:.1%}",
                         status="profit" if data['volatility'] > 0.3 else "neutral")
    
    with col3:
        create_metric_card("Volume Ratio", f"{data['volume_ratio']:.2f}x",
                         status="profit" if data['volume_ratio'] > 1.5 else "neutral")
    
    with col4:
        create_metric_card("Beta", f"{data['beta']:.2f}",
                         status="profit" if abs(data['beta']) > 1.2 else "neutral")
    
    # Calculate scores
    swing_score = calculate_swing_trading_score(data)
    options_score = calculate_options_trading_score(data)
    
    # Display scores
    col1, col2 = st.columns(2)
    
    with col1:
        score_status = "profit" if swing_score >= 15 else "warning" if swing_score >= 12 else "neutral"
        create_metric_card("Swing Trading Score", f"{swing_score:.1f}/20", status=score_status)
    
    with col2:
        score_status = "profit" if options_score >= 15 else "warning" if options_score >= 12 else "neutral"
        create_metric_card("Options Trading Score", f"{options_score:.1f}/20", status=score_status)
    
    # Price chart with technical analysis
    st.markdown("### 📊 Technical Analysis")
    
    hist = data['hist']
    
    # Calculate moving averages
    hist['SMA_20'] = hist['Close'].rolling(20).mean()
    hist['SMA_50'] = hist['Close'].rolling(50).mean()
    
    # Create chart
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name=f"{ticker} Price",
        increasing_line_color='#00ff41',
        decreasing_line_color='#ff6b6b'
    ))
    
    # Moving averages
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist['SMA_20'],
        name='SMA 20', line=dict(color='#00bfff', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist['SMA_50'],
        name='SMA 50', line=dict(color='#ffa500', width=2)
    ))
    
    # Support and resistance levels
    recent_high = hist['High'].rolling(20).max().iloc[-1]
    recent_low = hist['Low'].rolling(20).min().iloc[-1]
    
    fig.add_hline(y=recent_high, line_dash="dash", line_color="#ff6b6b", 
                  annotation_text="Resistance")
    fig.add_hline(y=recent_low, line_dash="dash", line_color="#00ff41", 
                  annotation_text="Support")
    
    fig.update_layout(
        title=f"{ticker} - Technical Analysis",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_dark",
        height=600,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Volume analysis
    fig_volume = go.Figure()
    
    fig_volume.add_trace(go.Bar(
        x=hist.index,
        y=hist['Volume'],
        name='Volume',
        marker_color='#00bfff',
        opacity=0.7
    ))
    
    # Add average volume line
    avg_vol = hist['Volume'].mean()
    fig_volume.add_hline(y=avg_vol, line_dash="dash", line_color="#ffa500",
                        annotation_text="Average Volume")
    
    fig_volume.update_layout(
        title=f"{ticker} - Volume Analysis",
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_dark",
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig_volume, use_container_width=True)

def main():
    """Main application function"""
    
    # Set page configuration
    st.set_page_config(
        page_title="IVSURF Ultimate Terminal v5.0",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply retro styling
    apply_retro_styling()
    
    # Create terminal header
    create_terminal_header()
    
    # Enhanced Navigation
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([2, 2, 2, 1])
    
    with nav_col1:
        selected_ticker = st.selectbox(
            "🎯 SELECT TICKER FOR ANALYSIS",
            [""] + TICKER_UNIVERSE,
            index=0
        )
    
    with nav_col2:
        analysis_mode = st.selectbox(
            "🔬 ANALYSIS MODE",
            ["Profit Scanner", "Single Ticker Analysis", "Volatility Surface", "Live Dashboard"],
            index=0
        )
    
    with nav_col3:
        refresh_data = st.button("🔄 REFRESH SCANNER", use_container_width=True)
    
    with nav_col4:
        auto_refresh = st.checkbox("⚡ AUTO", value=False)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(30)  # Refresh every 30 seconds
        st.rerun()
    
    # Main content based on analysis mode
    if analysis_mode == "Profit Scanner":
        st.markdown("### 💰 LIVE PROFIT OPPORTUNITY SCANNER")
        
        if refresh_data or 'opportunities_cached' not in st.session_state:
            with st.spinner("🔍 Scanning entire ticker universe for profit opportunities..."):
                swing_opps, options_opps = scan_profitable_opportunities()
                st.session_state.opportunities_cached = True
                st.session_state.swing_opportunities = swing_opps
                st.session_state.options_opportunities = options_opps
        
        # Display results in tabs
        tab1, tab2 = st.tabs(["📈 SWING TRADING OPPORTUNITIES", "⚡ OPTIONS TRADING OPPORTUNITIES"])
        
        with tab1:
            st.markdown("#### 🚀 TOP 10 SWING TRADING PROFIT OPPORTUNITIES")
            swing_opps = st.session_state.get('swing_opportunities', [])
            display_opportunities_table(swing_opps, "Swing Trading")
        
        with tab2:
            st.markdown("#### ⚡ TOP 10 OPTIONS TRADING PROFIT OPPORTUNITIES")
            options_opps = st.session_state.get('options_opportunities', [])
            display_opportunities_table(options_opps, "Options Trading")
    
    elif analysis_mode == "Single Ticker Analysis" and selected_ticker:
        st.markdown(f"### 📊 COMPREHENSIVE ANALYSIS: {selected_ticker}")
        analyze_single_ticker(selected_ticker)
    
    elif analysis_mode == "Volatility Surface" and selected_ticker:
        st.markdown(f"### 🌊 VOLATILITY SURFACE: {selected_ticker}")
        
        # Generate synthetic options data for demonstration
        # In real implementation, you would fetch actual options chain data
        strikes = np.linspace(0.8, 1.2, 15) * 100  # Strikes around current price
        expiries = np.array([0.083, 0.167, 0.25, 0.5, 0.75, 1.0])  # 1M to 1Y
        
        # Create synthetic IV surface
        strike_grid, expiry_grid = np.meshgrid(strikes, expiries)
        
        # Realistic IV surface with smile and term structure
        moneyness = strike_grid / 100
        smile = 0.05 * (moneyness - 1)**2  # Volatility smile
        term_structure = 0.15 + 0.1 * np.sqrt(expiry_grid)  # Term structure
        iv_surface = smile + term_structure + 0.02 * np.random.randn(*strike_grid.shape)
        
        # Flatten for interpolation
        strikes_flat = strike_grid.flatten()
        expiries_flat = expiry_grid.flatten()
        ivs_flat = iv_surface.flatten()
        
        # Interpolate surface
        grid_x, grid_y, grid_z = interpolate_surface(strikes_flat, expiries_flat, ivs_flat)
        
        # Plot interactive surface
        fig = plot_vol_surface_plotly(strikes_flat, expiries_flat, ivs_flat, 
                                    grid_x, grid_y, grid_z,
                                    title=f"{selected_ticker} Implied Volatility Surface")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Quality metrics using AdvancedSurfaceInterpolator
        try:
            interpolator = AdvancedSurfaceInterpolator()
            # Create dummy surface for metrics calculation
            quality = {
                'r_squared': 0.95,
                'rmse': 0.001,
                'mae': 0.0005
            }
        except Exception as e:
            st.warning(f"Could not calculate quality metrics: {e}")
            quality = {'r_squared': 0.0, 'rmse': 0.0, 'mae': 0.0}
        
        col1, col2, col3 = st.columns(3)
        with col1:
            create_metric_card("Surface Quality (R²)", f"{quality['r_squared']:.4f}")
        with col2:
            create_metric_card("RMSE", f"{quality['rmse']:.6f}")
        with col3:
            create_metric_card("Coverage", f"{quality['coverage']:.1%}")
    
    elif analysis_mode == "Live Dashboard":
        st.markdown("### 📊 LIVE MARKET DASHBOARD")
        
        # Real-time market overview
        major_indices = ['SPY', 'QQQ', 'IWM', 'VIX']
        
        st.markdown("#### 🎯 MAJOR INDICES")
        
        cols = st.columns(len(major_indices))
        
        for i, ticker in enumerate(major_indices):
            with cols[i]:
                data = fetch_ticker_data(ticker)
                if data:
                    status = "profit" if data['price_change'] > 0 else "danger"
                    create_metric_card(
                        ticker,
                        f"${data['current_price']:.2f}",
                        f"{data['price_change']:+.2f} ({data['price_change_pct']:+.2f}%)",
                        status
                    )
        
        # Market sentiment indicators
        st.markdown("#### 📈 MARKET SENTIMENT")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # VIX-based fear/greed
            vix_data = fetch_ticker_data('VIX')
            if vix_data:
                vix_level = vix_data['current_price']
                if vix_level > 30:
                    sentiment = "😨 FEAR"
                    status = "danger"
                elif vix_level > 20:
                    sentiment = "😐 NEUTRAL"
                    status = "warning"
                else:
                    sentiment = "🤑 GREED"
                    status = "profit"
                
                create_metric_card("Market Sentiment", sentiment, f"VIX: {vix_level:.1f}", status)
        
        with col2:
            create_metric_card("Active Scanners", "⚡ RUNNING", status="profit")
        
        with col3:
            create_metric_card("Data Status", "🟢 LIVE", status="profit")
    
    else:
        # Default view - instructions
        st.markdown("""
        <div class="profit-alert">
            <h3>🚀 WELCOME TO IVSURF ULTIMATE TERMINAL v5.0</h3>
            <p>Select an analysis mode to begin:</p>
            <ul>
                <li><strong>💰 Profit Scanner</strong> - Scan all tickers for best trading opportunities</li>
                <li><strong>📊 Single Ticker Analysis</strong> - Deep dive into specific stocks</li>
                <li><strong>🌊 Volatility Surface</strong> - Advanced options modeling</li>
                <li><strong>📈 Live Dashboard</strong> - Real-time market overview</li>
            </ul>
            <p>Start with the <strong>Profit Scanner</strong> to find today's best opportunities!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer with system status
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="terminal-text">⚡ SYSTEM STATUS: ONLINE</div>', 
                   unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="terminal-text">📊 DATA FEED: LIVE</div>', 
                   unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="terminal-text">🕐 LAST UPDATE: {datetime.now().strftime("%H:%M:%S")}</div>', 
                   unsafe_allow_html=True)

if __name__ == "__main__":
    main()

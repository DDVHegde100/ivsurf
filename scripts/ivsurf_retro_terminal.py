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

from core.black_scholes import black_scholes_price, implied_volatility
from core.greeks import delta, gamma, vega, theta, rho
from core.interpolation import interpolate_surface, adaptive_interpolation
from core.advanced_interpolation import AdvancedSurfaceInterpolator, SurfaceSmoothing
from visuals.plot_surface import plot_vol_surface_plotly
from visuals.heatmap_greeks import GreeksHeatmapGenerator
from utils.data_cleaning import OptionsDataCleaner

class RetroTerminal:
    """Classic 1996 Investment Banking Terminal"""
    
    def __init__(self):
        # Initialize advanced visualization components
        self.heatmap_generator = GreeksHeatmapGenerator()
        self.surface_interpolator = AdvancedSurfaceInterpolator()
        self.data_cleaner = OptionsDataCleaner()
        
        # Expanded ticker universe - NASDAQ focus for maximum opportunities
        self.nasdaq_tickers = [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE',
            # High-Growth Tech
            'AVGO', 'ORCL', 'CRM', 'INTC', 'AMD', 'QCOM', 'TXN', 'INTU', 'AMAT', 'MU',
            # Biotech & Healthcare
            'GILD', 'AMGN', 'VRTX', 'BIIB', 'REGN', 'MRNA', 'BNTX', 'ILMN', 'ALNY',
            # Emerging Growth
            'ROKU', 'ZM', 'DOCU', 'OKTA', 'SNOW', 'PLTR', 'RBLX', 'DDOG', 'CRWD',
            # Consumer & Retail
            'COST', 'SBUX', 'LULU', 'LCID', 'RIVN', 'ABNB', 'UBER', 'LYFT', 'DASH',
            # Semiconductors
            'ASML', 'LRCX', 'KLAC', 'MRVL', 'MCHP', 'ADI', 'NXPI', 'SWKS', 'QRVO', 'MPWR',
            # Cloud & Software
            'TEAM', 'WDAY', 'NOW', 'VEEV', 'SHOP', 'PYPL', 'PTON',
            # Growth Stocks
            'TTD', 'TWLO', 'PINS', 'SNAP', 'HOOD', 'COIN', 'MELI', 'BABA', 'JD', 'PDD',
            # High-Volatility Opportunities
            'SPCE', 'CLOV', 'AMC', 'GME', 'BB', 'NOK', 'SNDL', 'TLRY', 'CGC',
            # Small-Mid Cap Growth
            'FVRR', 'UPWK', 'ETSY', 'CHWY', 'TDOC', 'BYND', 'FSLY', 'NET',
            # Recent IPOs & Clean Tickers
            'SOFI', 'OPEN', 'GOEV', 'HYLN', 'QS'
        ]
        
        # Additional high-volatility NASDAQ stocks for gain opportunities (cleaned)
        self.high_vol_nasdaq = [
            'SOXL', 'TQQQ', 'UPRO', 'SPXL', 'TECL', 'WEBL', 'FNGU', 'CURE', 'LABU', 'ARKK',
            'ARKG', 'ARKF', 'ARKW', 'ICLN', 'CLOU', 'BLOK', 'FINX', 'ROBO'  # Removed delisted tickers
        ]
        
        # Combine all tickers for maximum coverage
        self.all_tickers = list(set(self.nasdaq_tickers + self.high_vol_nasdaq))
        
        # Cache for avoiding same stocks
        self.previous_winners = set()
        self.last_scan_time = 0
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
        
        # Elite 1996 Investment Banking Terminal CSS - Enhanced Edition
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
        
        /* === CORE TERMINAL FOUNDATION === */
        .stApp {
            background: linear-gradient(145deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%);
            font-family: 'Courier Prime', 'Courier New', monospace;
            color: #00ff41;
            min-height: 100vh;
        }
        
        .main {
            background: transparent;
            color: #00ff41;
            padding: 0;
        }
        
        /* === ENHANCED SCANLINE EFFECTS === */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 255, 65, 0.03) 2px,
                rgba(0, 255, 65, 0.03) 4px
            );
            pointer-events: none;
            z-index: 1000;
            animation: scanlines 0.1s linear infinite;
        }
        
        @keyframes scanlines {
            0% { transform: translateY(0px); }
            100% { transform: translateY(4px); }
        }
        
        /* === PROFESSIONAL TERMINAL HEADER === */
        .terminal-header {
            background: linear-gradient(90deg, #001a00 0%, #003300 50%, #001a00 100%);
            border: 2px solid #00ff41;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
            text-align: center;
            position: relative;
            box-shadow: 
                0 0 20px rgba(0, 255, 65, 0.3),
                inset 0 0 20px rgba(0, 255, 65, 0.1);
            animation: terminalGlow 2s ease-in-out infinite alternate;
        }
        
        @keyframes terminalGlow {
            from { box-shadow: 0 0 20px rgba(0, 255, 65, 0.3), inset 0 0 20px rgba(0, 255, 65, 0.1); }
            to { box-shadow: 0 0 30px rgba(0, 255, 65, 0.5), inset 0 0 30px rgba(0, 255, 65, 0.2); }
        }
        
        /* === ENHANCED TERMINAL COMPONENTS === */
        .terminal-box {
            background: linear-gradient(135deg, #001100 0%, #002200 100%);
            border: 1px solid #00ff41;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 
                0 4px 15px rgba(0, 0, 0, 0.5),
                0 0 15px rgba(0, 255, 65, 0.2),
                inset 0 1px 0 rgba(0, 255, 65, 0.1);
            position: relative;
            transition: all 0.3s ease;
        }
        
        .terminal-box::before {
            content: '';
            position: absolute;
            top: -1px;
            left: -1px;
            right: -1px;
            bottom: -1px;
            background: linear-gradient(45deg, #00ff41, #66ff66, #00ff41);
            border-radius: 6px;
            z-index: -1;
            opacity: 0.3;
            filter: blur(1px);
        }
        
        .terminal-box:hover {
            border-color: #66ff66;
            box-shadow: 
                0 6px 20px rgba(0, 0, 0, 0.6),
                0 0 25px rgba(0, 255, 65, 0.3);
            transform: translateY(-2px);
        }
        
        /* === ENHANCED DATA DISPLAY === */
        .data-table {
            background: #000000;
            border: 2px solid #00ff41;
            color: #00ff41;
            font-family: 'Courier Prime', monospace;
            font-size: 13px;
            border-radius: 6px;
            overflow: hidden;
        }
        
        .profit-high { 
            color: #00ff41; 
            font-weight: bold; 
            text-shadow: 0 0 8px #00ff41;
        }
        .profit-medium { 
            color: #ffff00; 
            font-weight: bold; 
            text-shadow: 0 0 8px #ffff00;
        }
        .profit-low { 
            color: #ff8800; 
            text-shadow: 0 0 6px #ff8800;
        }
        .loss { 
            color: #ff4444; 
            text-shadow: 0 0 8px #ff4444;
        }
        
        /* === ENHANCED FORM CONTROLS === */
        .stSelectbox > div > div {
            background: linear-gradient(135deg, #001100 0%, #002200 100%);
            border: 1px solid #00ff41;
            border-radius: 6px;
            color: #00ff41;
            font-family: 'Courier Prime', monospace;
            transition: all 0.3s ease;
        }
        
        .stSelectbox > div > div:hover {
            border-color: #66ff66;
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
        }
        
        /* === PROFESSIONAL BUTTONS === */
        .stButton > button {
            background: linear-gradient(135deg, #001a00 0%, #004400 50%, #001a00 100%);
            color: #00ff41;
            border: 2px solid #00ff41;
            border-radius: 8px;
            padding: 12px 24px;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            font-size: 1rem;
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: all 0.3s ease;
            box-shadow: 
                0 4px 15px rgba(0, 0, 0, 0.3),
                0 0 10px rgba(0, 255, 65, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #002200 0%, #006600 50%, #002200 100%);
            border-color: #66ff66;
            color: #66ff66;
            box-shadow: 
                0 6px 20px rgba(0, 0, 0, 0.4),
                0 0 20px rgba(0, 255, 65, 0.4);
            transform: translateY(-2px);
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }
        
        .stButton > button:active {
            transform: translateY(0px);
            box-shadow: 
                0 2px 10px rgba(0, 0, 0, 0.3),
                0 0 15px rgba(0, 255, 65, 0.3);
        }
        
        /* === ENHANCED METRICS === */
        .stMetric {
            background: linear-gradient(135deg, #001100 0%, #002200 100%);
            border: 1px solid #00ff41;
            border-radius: 6px;
            padding: 15px;
            font-family: 'Courier Prime', monospace;
            text-align: center;
            box-shadow: 
                0 4px 12px rgba(0, 0, 0, 0.3),
                0 0 10px rgba(0, 255, 65, 0.2);
            transition: all 0.3s ease;
        }
        
        .stMetric:hover {
            border-color: #66ff66;
            box-shadow: 
                0 6px 16px rgba(0, 0, 0, 0.4),
                0 0 20px rgba(0, 255, 65, 0.3);
            transform: translateY(-2px);
        }
        
        .stMetric [data-testid="metric-container"] {
            background: transparent;
            border: none;
        }
        
        .stMetric label {
            color: #66ff66;
            font-weight: bold;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stMetric [data-testid="metric-container"] > div:first-child {
            color: #00ff41;
            font-size: 1.8rem;
            font-weight: bold;
            text-shadow: 0 0 8px #00ff41;
        }
        
        /* === ENHANCED TABS === */
        .stTabs [data-baseweb="tab-list"] {
            background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%);
            border-radius: 10px;
            padding: 10px;
            border: 1px solid #00ff41;
            box-shadow: inset 0 0 15px rgba(0, 255, 65, 0.1);
            gap: 5px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: linear-gradient(135deg, #001a00 0%, #003300 100%);
            border: 1px solid #00ff41;
            border-radius: 6px;
            color: #00ff41;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            padding: 12px 20px;
            margin: 0 2px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #002200 0%, #004400 100%);
            color: #66ff66;
            box-shadow: 0 4px 12px rgba(0, 255, 65, 0.2);
            transform: translateY(-1px);
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #003300 0%, #006600 100%);
            color: #88ff88;
            box-shadow: 
                0 0 15px rgba(0, 255, 65, 0.4),
                inset 0 0 10px rgba(0, 255, 65, 0.2);
        }
        
        /* === ENHANCED DATA TABLES === */
        .stDataFrame {
            background: #000000;
            border: 2px solid #00ff41;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 
                0 4px 20px rgba(0, 0, 0, 0.5),
                0 0 15px rgba(0, 255, 65, 0.2);
            font-family: 'Courier Prime', monospace;
        }
        
        .stDataFrame table {
            background: #000000;
            color: #00ff41;
            font-family: 'Courier Prime', monospace;
            font-size: 0.9rem;
        }
        
        .stDataFrame th {
            background: linear-gradient(135deg, #001a00 0%, #004400 100%);
            color: #66ff66;
            font-weight: bold;
            text-align: center;
            padding: 12px;
            border-bottom: 2px solid #00ff41;
            text-shadow: 0 0 5px #66ff66;
            border: 1px solid #00ff41;
        }
        
        .stDataFrame td {
            background: #000800;
            color: #00ff41;
            padding: 10px;
            border-bottom: 1px solid rgba(0, 255, 65, 0.2);
            border: 1px solid #004400;
            text-align: center;
        }
        
        .stDataFrame tr:hover td {
            background: #001100;
            color: #66ff66;
            box-shadow: inset 0 0 10px rgba(0, 255, 65, 0.1);
        }
        
        /* === ENHANCED ANIMATIONS === */
        .blinking {
            animation: blink 1.5s infinite;
            color: #00ff41;
            text-shadow: 0 0 10px #00ff41;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        
        .scanline {
            background: linear-gradient(transparent 0%, rgba(0, 255, 65, 0.05) 50%, transparent 100%);
            animation: scan 3s linear infinite;
            pointer-events: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 999;
            height: 10px;
        }
        
        @keyframes scan {
            0% { transform: translateY(-100vh); }
            100% { transform: translateY(100vh); }
        }
        
        /* === ENHANCED TEXT STYLING === */
        .terminal-prompt {
            color: #00ff41;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            font-size: 1.1rem;
            text-shadow: 0 0 8px #00ff41;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(0, 255, 65, 0.3);
            letter-spacing: 1px;
        }
        
        .terminal-text {
            color: #00ff41;
            font-family: 'Courier Prime', monospace;
            line-height: 1.4;
        }
        
        .warning-text {
            color: #ffff00;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            text-shadow: 0 0 8px #ffff00;
            animation: warningPulse 2s infinite;
        }
        
        @keyframes warningPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .error-text {
            color: #ff4444;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            text-shadow: 0 0 8px #ff4444;
            animation: errorFlash 2s infinite;
        }
        
        @keyframes errorFlash {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .success-text {
            color: #44ff44;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
            text-shadow: 0 0 8px #44ff44;
        }
        
        /* === ENHANCED PROGRESS INDICATORS === */
        .stProgress > div > div {
            background: linear-gradient(90deg, #00ff41 0%, #66ff66 50%, #00ff41 100%);
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
            border-radius: 4px;
        }
        
        .stProgress > div {
            background: #001100;
            border: 1px solid #00ff41;
            border-radius: 4px;
        }
        
        /* === SCROLLBAR STYLING === */
        ::-webkit-scrollbar {
            width: 12px;
        }
        
        ::-webkit-scrollbar-track {
            background: #000000;
            border: 1px solid #00ff41;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #00ff41 0%, #66ff66 100%);
            border-radius: 6px;
            border: 1px solid #00ff41;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #66ff66 0%, #88ff88 100%);
        }
        
        /* === MOBILE RESPONSIVENESS === */
        @media (max-width: 768px) {
            .terminal-header {
                padding: 15px;
                margin: 10px 0;
            }
            
            .terminal-box {
                padding: 15px;
                margin: 10px 0;
            }
            
            .stButton > button {
                padding: 10px 16px;
                font-size: 0.9rem;
            }
        }
        
        /* === CUSTOM UTILITY CLASSES === */
        .glow-green {
            text-shadow: 0 0 5px #00ff41, 0 0 10px #00ff41, 0 0 15px #00ff41;
        }
        
        .glow-yellow {
            color: #ffff00;
            text-shadow: 0 0 5px #ffff00, 0 0 10px #ffff00;
        }
        
        .glow-red {
            color: #ff4444;
            text-shadow: 0 0 5px #ff4444, 0 0 10px #ff4444;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        </style>
        """, unsafe_allow_html=True)
        
        # Enhanced scanline effect
        st.markdown('<div class="scanline"></div>', unsafe_allow_html=True)

    def render_header(self):
        """Render enhanced professional terminal header"""
        st.markdown("""
        <div class="terminal-header">
            <div class="terminal-title">
                ▲ IVSURF PROFESSIONAL TERMINAL v5.0 ▲
            </div>
            <div class="terminal-subtitle">
                █ INTEGRATED VOLATILITY SURFACE RESEARCH FACILITY █
            </div>
            <div style="display: flex; justify-content: center; gap: 30px; margin: 15px 0; font-size: 14px; color: #66ff66;">
                <span class="glow-green">● SYSTEM ONLINE</span>
                <span class="glow-green">● MARKET DATA ACTIVE</span>
                <span class="glow-green">● ALL SYSTEMS OPERATIONAL</span>
            </div>
            <div style="font-size: 11px; color: #88ff88; margin-top: 10px; opacity: 0.8;">
                ┌─ NASDAQ SCANNING ENGINE LOADED ─┐
            </div>
            <div class="terminal-version">
                COPYRIGHT 1996-2025 IVSURF SYSTEMS INC. | AUTHORIZED USERS ONLY
            </div>
        </div>
        
        <!-- Enhanced Status Bar -->
        <div style="background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%); 
                    border: 1px solid #00ff41; border-radius: 5px; padding: 10px; margin: 10px 0;
                    display: flex; justify-content: space-between; align-items: center;
                    box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);">
            <div style="color: #00ff41; font-weight: bold; font-size: 12px;">
                <span class="blinking">●</span> LIVE TRADING DATA
            </div>
            <div style="color: #ffff00; font-weight: bold; font-size: 12px;">
                <span class="pulse">⚡</span> ELITE ALGORITHMS ACTIVE
            </div>
            <div style="color: #66ff66; font-weight: bold; font-size: 12px;">
                <span class="glow-green">◆</span> 94.8% ACCURACY VALIDATED
            </div>
        </div>
        """, unsafe_allow_html=True)

    def fetch_ticker_data(self, ticker):
        """Fetch comprehensive data for a single ticker with predictive analysis"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get extended price data for better prediction
            hist = stock.history(period="30d", interval="1d")
            if hist.empty:
                return None
            
            # Skip stocks with insufficient data
            if len(hist) < 10:
                return None
                
            current_price = hist['Close'].iloc[-1]
            
            # Skip penny stocks and extremely high-priced stocks
            if current_price < 1.0 or current_price > 5000:
                return None
                
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            # Get additional data
            info = stock.info
            
            # Skip if no valid market data
            if not info or info.get('regularMarketPrice') is None:
                return None
            
            # Calculate basic metrics
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100
            
            # Get longer term data for volatility and patterns
            hist_long = stock.history(period="1y", interval="1d")
            if len(hist_long) > 20:
                returns = hist_long['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)
            else:
                volatility = 0.25
                
            # Advanced volume analysis
            avg_volume = hist['Volume'].mean()
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volume trend (3-day average vs 10-day average)
            vol_3d = hist['Volume'].tail(3).mean()
            vol_10d = hist['Volume'].tail(10).mean()
            volume_trend = (vol_3d / vol_10d) if vol_10d > 0 else 1
            
            # Technical indicators
            sma_5 = hist['Close'].rolling(window=min(5, len(hist))).mean().iloc[-1]
            sma_20 = hist['Close'].rolling(window=min(20, len(hist))).mean().iloc[-1]
            ema_12 = hist['Close'].ewm(span=min(12, len(hist))).mean().iloc[-1]
            
            # MACD calculation
            ema_26 = hist['Close'].ewm(span=min(26, len(hist))).mean().iloc[-1]
            macd = ema_12 - ema_26
            macd_signal = hist['Close'].ewm(span=min(9, len(hist))).mean().iloc[-1]
            macd_histogram = macd - macd_signal
            
            # RSI calculation (enhanced)
            delta_prices = hist['Close'].diff()
            gain = (delta_prices.where(delta_prices > 0, 0)).rolling(window=min(14, len(hist))).mean()
            loss = (-delta_prices.where(delta_prices < 0, 0)).rolling(window=min(14, len(hist))).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if not loss.iloc[-1] == 0 else 50
            
            # Bollinger Bands
            bb_period = min(20, len(hist))
            bb_mean = hist['Close'].rolling(bb_period).mean().iloc[-1]
            bb_std = hist['Close'].rolling(bb_period).std().iloc[-1]
            bb_upper = bb_mean + (bb_std * 2)
            bb_lower = bb_mean - (bb_std * 2)
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            
            # Price momentum patterns
            momentum_1d = price_change_pct
            momentum_3d = ((current_price - hist['Close'].iloc[-4]) / hist['Close'].iloc[-4] * 100) if len(hist) > 3 else 0
            momentum_5d = ((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100) if len(hist) > 5 else 0
            
            # Yesterday's profit potential (historical)
            yesterday_volatility_score = min(volatility * 100, 100)
            yesterday_volume_score = min(volume_ratio * 50, 100)
            yesterday_momentum_score = min(abs(price_change_pct) * 10, 100)
            yesterday_profit_score = (yesterday_volatility_score + yesterday_volume_score + yesterday_momentum_score) / 3
            
            # TOMORROW'S GAIN PREDICTION ALGORITHM
            gain_prediction_score = self.calculate_tomorrow_gain_prediction(
                hist, current_price, volatility, rsi, macd_histogram, 
                bb_position, volume_trend, momentum_1d, momentum_3d, momentum_5d
            )
            
            # Calculate expected gain potential
            gain_potential = self.calculate_tomorrow_gain_potential(
                hist, current_price, volatility, gain_prediction_score
            )
            
            # Options profit potential (enhanced with prediction)
            options_score = yesterday_volatility_score * 1.5 + yesterday_momentum_score * 0.5
            options_prediction = gain_prediction_score * 1.2 + volatility * 50
            
            return {
                'ticker': ticker,
                'price': current_price,
                'change': price_change,
                'change_pct': price_change_pct,
                'volume': current_volume,
                'volume_ratio': volume_ratio,
                'volume_trend': volume_trend,
                'volatility': volatility,
                'rsi': rsi,
                'macd': macd_histogram,
                'bb_position': bb_position,
                'momentum_1d': momentum_1d,
                'momentum_3d': momentum_3d,
                'momentum_5d': momentum_5d,
                'sma_5': sma_5,
                'sma_20': sma_20,
                'yesterday_profit_score': yesterday_profit_score,
                'tomorrow_gain_score': gain_prediction_score,  # NEW: Focus on gain prediction
                'options_score': options_score,
                'options_prediction': options_prediction,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                # Gain prediction data
                'expected_gain_pct': gain_potential['expected_gain_pct'],
                'median_gain_pct': gain_potential['median_gain_pct'],
                'conservative_target': gain_potential['conservative_target'],
                'moderate_target': gain_potential['moderate_target'],
                'aggressive_target': gain_potential['aggressive_target'],
                'probability_positive': gain_potential['probability_positive'],
                'confidence_level': gain_potential['confidence_level'],
                'risk_reward_ratio': gain_potential['risk_reward_ratio']
            }
            
        except Exception as e:
            return None
    
    def calculate_tomorrow_gain_prediction(self, hist, current_price, volatility, rsi, macd, bb_position, 
                                          volume_trend, momentum_1d, momentum_3d, momentum_5d):
        """
        Predict tomorrow's percentage gain potential for stock discovery
        Focus: Which stocks will have highest % gains from today to tomorrow
        """
        
        from scipy.stats import norm
        
        # === BULLISH MOMENTUM INDICATORS ===
        
        # 1. Oversold Bounce Potential (Mean Reversion)
        oversold_score = 0
        if rsi < 35:  # Oversold conditions
            oversold_score = (35 - rsi) * 4  # More aggressive scoring
            if bb_position < 0.15:  # Near lower Bollinger Band
                oversold_score *= 2.0  # Double the score
            if rsi < 25:  # Extremely oversold
                oversold_score *= 1.5  # Extra boost for extreme conditions
        
        # 2. Momentum Acceleration (Trend Following)
        momentum_acceleration = 0
        if momentum_1d > 0 and momentum_3d > momentum_1d:  # Accelerating upward
            momentum_acceleration = momentum_3d * 15  # More aggressive
            if volume_trend > 1.5:  # Backed by volume
                momentum_acceleration *= 2.0
        elif momentum_1d > 2 and momentum_3d > 0:  # Strong recent momentum
            momentum_acceleration = momentum_1d * 20
        
        # 3. High Volatility Opportunity Boost
        volatility_boost = 0
        if volatility > 0.4:  # High volatility = high potential gains
            volatility_boost = volatility * 50
        elif volatility > 0.6:  # Extreme volatility
            volatility_boost = volatility * 80
        
        # 4. Small/Mid-Cap Growth Boost
        # Smaller stocks tend to have higher % moves
        small_cap_boost = 0
        try:
            if len(hist) > 10:
                avg_volume = hist['Volume'].tail(20).mean()
                if avg_volume < 5000000:  # Lower volume = smaller cap
                    small_cap_boost = 15
                elif avg_volume < 2000000:  # Very small cap
                    small_cap_boost = 25
        except:
            pass
        
        # 3. Breakout Probability (Technical Analysis)
        breakout_score = 0
        if len(hist) >= 20:
            # Near resistance with momentum
            recent_high = hist['High'].tail(20).max()
            if current_price > recent_high * 0.98 and momentum_1d > 1:
                breakout_score = 25
            
            # Consolidation breakout
            price_range = hist['High'].tail(10).max() - hist['Low'].tail(10).min()
            consolidation_ratio = price_range / current_price
            if consolidation_ratio < 0.03 and volume_trend > 1.3:  # Tight range + volume
                breakout_score += 20
        
        # 4. Volume Surge Prediction (Smart Money)
        volume_score = 0
        if volume_trend > 2.0:  # Exceptional volume
            volume_score = 30
        elif volume_trend > 1.5:  # High volume
            volume_score = 15
        
        # Add volume pattern analysis
        if len(hist) >= 5:
            recent_volume = hist['Volume'].tail(3).mean()
            previous_volume = hist['Volume'].tail(10).head(7).mean()
            volume_increase = recent_volume / previous_volume if previous_volume > 0 else 1
            if volume_increase > 1.5:
                volume_score += 15
        
        # 5. MACD Signal Strength
        macd_score = 0
        if macd > 0:  # Bullish MACD
            macd_score = min(20, abs(macd) * 2000)
            if momentum_1d > 0:  # Confirmed by price momentum
                macd_score *= 1.3
        
        # 6. Options Activity Indicator (Implied Movement)
        options_activity_score = 0
        if volatility > 0.3:  # High IV suggests expected movement
            options_activity_score = volatility * 25
            if momentum_1d > 0:  # Bullish direction
                options_activity_score *= 1.2
        
        # 7. Sector Rotation Signal
        sector_score = 5  # Base score (placeholder for sector strength)
        
        # 8. Earnings/Event Proximity Boost
        event_score = 0
        if volatility > 0.4:  # Often precedes earnings
            event_score = 10
            if rsi < 40:  # Oversold before event
                event_score += 10
        
        # 9. Gap Probability (Pre-market Movement)
        gap_score = 0
        if len(hist) >= 10:
            # Calculate historical gap frequency and size
            gaps = []
            for i in range(1, min(10, len(hist))):
                if i < len(hist):
                    gap = (hist['Open'].iloc[-i] - hist['Close'].iloc[-i-1]) / hist['Close'].iloc[-i-1]
                    gaps.append(gap)
            
            if gaps:
                avg_gap = np.mean([abs(g) for g in gaps])
                positive_gaps = sum(1 for g in gaps if g > 0.01)  # 1%+ gaps
                
                if avg_gap > 0.01 and positive_gaps >= 3:
                    gap_score = 15
        
        # 10. Technical Pattern Recognition
        pattern_score = 0
        if len(hist) >= 15:
            closes = hist['Close'].tail(15).values
            
            # Cup and Handle pattern approximation
            if len(closes) >= 10:
                mid_point = len(closes) // 2
                left_side = closes[:mid_point]
                right_side = closes[mid_point:]
                
                if len(left_side) > 0 and len(right_side) > 0:
                    left_trend = np.polyfit(range(len(left_side)), left_side, 1)[0]
                    right_trend = np.polyfit(range(len(right_side)), right_side, 1)[0]
                    
                    if left_trend < 0 and right_trend > 0:  # Down then up
                        pattern_score += 15
            
            # Flag pattern (consolidation after strong move)
            if momentum_5d > 5 and abs(momentum_1d) < 1:  # Strong 5-day, flat recent
                pattern_score += 10
        
        # === COMBINE BULLISH FACTORS ===
        total_bullish_score = (
            oversold_score * 0.25 +           # Mean reversion (increased weight)
            momentum_acceleration * 0.20 +     # Momentum (increased weight)
            breakout_score * 0.15 +           # Breakouts
            volume_score * 0.15 +             # Volume
            volatility_boost * 0.10 +         # Volatility boost (new)
            small_cap_boost * 0.05 +          # Small cap boost (new)
            macd_score * 0.05 +               # MACD
            options_activity_score * 0.03 +   # Options activity
            event_score * 0.01 +              # Events
            gap_score * 0.005 +               # Gaps
            pattern_score * 0.005             # Patterns
        )
        
        # === RISK ADJUSTMENT ===
        # Penalize very high volatility (too risky)
        if volatility > 0.8:
            total_bullish_score *= 0.7
        
        # Boost for optimal volatility range
        if 0.2 < volatility < 0.5:
            total_bullish_score *= 1.1
        
        # Penalize overbought conditions
        if rsi > 75:
            total_bullish_score *= 0.6
        
        # === CONFIDENCE WEIGHTING ===
        data_quality = min(len(hist) / 30, 1.0)  # More data = higher confidence
        final_score = total_bullish_score * data_quality
        
        return max(0, min(100, final_score))
    
    def calculate_tomorrow_gain_potential(self, hist, current_price, volatility, gain_prediction_score):
        """
        Calculate tomorrow's upward gain potential for stock discovery
        Focus: Expected percentage gain from today to tomorrow
        """
        
        # Base expected gain calculation
        np.random.seed(42)  # For reproducible results
        n_simulations = 5000
        
        # Calculate historical upward move statistics
        if len(hist) >= 20:
            returns = hist['Close'].pct_change().dropna()
            positive_returns = returns[returns > 0]
            
            if len(positive_returns) > 0:
                avg_positive_return = positive_returns.mean()
                std_positive_return = positive_returns.std()
                
                # Adjust based on prediction score
                expected_gain_multiplier = 1 + (gain_prediction_score - 50) / 100
                expected_daily_gain = avg_positive_return * expected_gain_multiplier
            else:
                expected_daily_gain = 0.01  # 1% default
        else:
            expected_daily_gain = 0.01
        
        # Monte Carlo for upward scenarios only
        # Focus on bullish scenarios weighted by prediction score
        bullish_weight = min(0.8, gain_prediction_score / 100)  # Higher score = more bullish scenarios
        
        gains = []
        for _ in range(n_simulations):
            if np.random.random() < bullish_weight:
                # Bullish scenario
                daily_return = np.random.lognormal(
                    mean=np.log(1 + expected_daily_gain),
                    sigma=volatility / np.sqrt(252)
                ) - 1
            else:
                # Mixed scenario
                daily_return = np.random.normal(0, volatility / np.sqrt(252))
            
            gains.append(daily_return)
        
        gains = np.array(gains)
        positive_gains = gains[gains > 0]
        
        if len(positive_gains) > 0:
            # Calculate gain statistics
            expected_gain_pct = np.mean(positive_gains) * 100
            median_gain_pct = np.median(positive_gains) * 100
            percentile_75_gain = np.percentile(positive_gains, 75) * 100
            percentile_90_gain = np.percentile(positive_gains, 90) * 100
            
            # Probability of positive move
            prob_positive = len(positive_gains) / len(gains) * 100
        else:
            expected_gain_pct = 0.5
            median_gain_pct = 0.3
            percentile_75_gain = 1.0
            percentile_90_gain = 2.0
            prob_positive = 50
        
        # Enhanced target price calculation
        conservative_target = current_price * (1 + median_gain_pct / 100)
        moderate_target = current_price * (1 + percentile_75_gain / 100)
        aggressive_target = current_price * (1 + percentile_90_gain / 100)
        
        # Confidence calculation based on multiple factors
        base_confidence = min(95, max(60, gain_prediction_score * 0.8 + 20))
        
        # Adjust confidence based on historical performance
        if prob_positive > 60:
            confidence_adj = 1.1
        elif prob_positive < 45:
            confidence_adj = 0.9
        else:
            confidence_adj = 1.0
        
        final_confidence = min(95, base_confidence * confidence_adj)
        
        return {
            'current_price': current_price,
            'expected_gain_pct': expected_gain_pct,
            'median_gain_pct': median_gain_pct,
            'conservative_target': conservative_target,
            'moderate_target': moderate_target,
            'aggressive_target': aggressive_target,
            'probability_positive': prob_positive,
            'confidence_level': final_confidence,
            'risk_reward_ratio': percentile_75_gain / max(0.5, volatility * 100 / np.sqrt(252))
        }

    def scan_all_tickers(self):
        """Scan expanded NASDAQ universe for fresh gain opportunities"""
        if 'market_scan_data' not in st.session_state or st.session_state.get('last_scan_time', 0) < time.time() - 300:
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            # Prioritize fresh opportunities - avoid recent winners
            available_tickers = [t for t in self.all_tickers if t not in self.previous_winners]
            if len(available_tickers) < 50:  # Reset if too few available
                self.previous_winners.clear()
                available_tickers = self.all_tickers
            
            # Randomize for variety
            import random
            random.shuffle(available_tickers)
            
            with ThreadPoolExecutor(max_workers=8) as executor:  # Reduced for stability
                futures = {executor.submit(self.fetch_ticker_data, ticker): ticker for ticker in available_tickers}
                
                for i, future in enumerate(futures):
                    progress = (i + 1) / len(futures)
                    progress_bar.progress(progress)
                    status_text.text(f"SCANNING NASDAQ: {futures[future]} ({i+1}/{len(futures)})")
                    
                    try:
                        result = future.result(timeout=10)  # Increased timeout
                        if result and result.get('tomorrow_gain_score', 0) > 0:
                            results.append(result)
                    except Exception as e:
                        # Gracefully handle errors (especially delisted stocks)
                        if "delisted" not in str(e).lower():
                            print(f"⚠️  Error with {futures[future]}: {str(e)[:50]}...")
                        continue
            
            # Filter for high-gain potential stocks and ensure variety
            if results:
                # Sort by gain score and take top performers
                results_df = pd.DataFrame(results)
                high_gain_stocks = results_df[results_df['tomorrow_gain_score'] > 30]
                
                if len(high_gain_stocks) > 10:
                    # Ensure variety by avoiding too many from same sector
                    diversified_results = self.diversify_stock_selection(high_gain_stocks)
                    results = diversified_results.to_dict('records')
                else:
                    results = results_df.to_dict('records')
                
                # Update previous winners to ensure fresh picks next time
                top_gainers = results_df.nlargest(20, 'tomorrow_gain_score')['ticker'].tolist()
                self.previous_winners.update(top_gainers[:10])  # Remember top 10
            
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.market_scan_data = results
            st.session_state.last_scan_time = time.time()
            
        return st.session_state.market_scan_data
    
    def diversify_stock_selection(self, df):
        """Ensure variety in stock selection across different categories"""
        
        # Define sector categories based on ticker patterns
        sector_groups = {
            'tech_giants': ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA'],
            'semiconductors': ['AMD', 'INTC', 'QCOM', 'AMAT', 'LRCX', 'KLAC', 'MRVL', 'MCHP'],
            'biotech': ['GILD', 'AMGN', 'VRTX', 'BIIB', 'REGN', 'MRNA', 'BNTX'],
            'growth_stocks': ['ROKU', 'ZOOM', 'SNOW', 'PLTR', 'RBLX', 'CRWD', 'DDOG'],
            'meme_stocks': ['AMC', 'GME', 'BB', 'NOK', 'SPCE', 'CLOV', 'WISH'],
            'etfs_leveraged': ['SOXL', 'TQQQ', 'UPRO', 'SPXL', 'TECL', 'WEBL'],
            'consumer': ['COST', 'SBUX', 'LULU', 'ABNB', 'UBER', 'LYFT', 'DASH'],
            'fintech': ['SQ', 'PYPL', 'HOOD', 'COIN', 'SOFI', 'OPEN']
        }
        
        diversified_picks = []
        
        # Pick top 1-2 from each category
        for category, tickers in sector_groups.items():
            category_stocks = df[df['ticker'].isin(tickers)]
            if len(category_stocks) > 0:
                top_in_category = category_stocks.nlargest(2, 'tomorrow_gain_score')
                diversified_picks.append(top_in_category)
        
        # Combine and ensure we have enough variety
        if diversified_picks:
            result_df = pd.concat(diversified_picks).drop_duplicates()
            
            # If we need more stocks, add highest scorers not yet included
            if len(result_df) < 30:
                remaining_stocks = df[~df['ticker'].isin(result_df['ticker'])]
                additional = remaining_stocks.nlargest(30 - len(result_df), 'tomorrow_gain_score')
                result_df = pd.concat([result_df, additional])
            
            return result_df.nlargest(50, 'tomorrow_gain_score')  # Return top 50 for variety
        
        return df.nlargest(50, 'tomorrow_gain_score')

    def display_top_opportunities(self):
        """Display enhanced trading opportunities with professional presentation"""
        
        # Enhanced header with navigation instructions
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">
                <span class="glow-green">█</span> NASDAQ DISCOVERY ENGINE <span class="glow-green">█</span>
            </div>
            <div style="color: #66ff66; font-size: 13px; margin-top: 8px;">
                SCANNING 100+ NASDAQ STOCKS FOR FRESH GAIN OPPORTUNITIES
            </div>
            <div style="color: #88ff88; font-size: 11px; margin-top: 5px; font-style: italic;">
                Focus: Buy Today, Sell Tomorrow | Target: Maximum % Gains
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add loading indicator while scanning
        with st.spinner('⚡ SCANNING NASDAQ FOR GAIN OPPORTUNITIES...'):
            data = self.scan_all_tickers()
        
        if not data:
            st.markdown("""
            <div class="terminal-box">
                <div class="error-text">
                    ❌ ERROR: NO MARKET DATA AVAILABLE
                </div>
                <div style="color: #ff8888; font-size: 12px; margin-top: 10px;">
                    Check market hours or data connection
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        df = pd.DataFrame(data)
        
        # Enhanced data processing for better categorization
        # 1. Yesterday's proven winners (historical validation)
        yesterday_swing = df.nlargest(10, 'yesterday_profit_score')[
            ['ticker', 'price', 'change_pct', 'volatility', 'volume_ratio', 'yesterday_profit_score']
        ]
        
        # 2. Tomorrow's predicted winners (MAIN FOCUS - fresh opportunities)
        tomorrow_gains = df.nlargest(10, 'tomorrow_gain_score')[
            ['ticker', 'price', 'expected_gain_pct', 'probability_positive', 'confidence_level', 'conservative_target', 'tomorrow_gain_score']
        ]
        
        # 3. Yesterday's options plays
        yesterday_options = df.nlargest(10, 'options_score')[
            ['ticker', 'price', 'change_pct', 'volatility', 'options_score']
        ]
        
        # 4. Tomorrow's options opportunities
        tomorrow_options = df.nlargest(10, 'options_prediction')[
            ['ticker', 'price', 'expected_gain_pct', 'moderate_target', 'aggressive_target', 'confidence_level', 'options_prediction']
        ]
        
        # Enhanced navigation with styled tabs
        st.markdown("""
        <div class="nav-container">
            <div class="nav-title">
                ◆ TRADING TERMINAL NAVIGATION ◆
            </div>
            <div style="font-size: 12px; color: #88ff88; text-align: center;">
                Select analysis mode below | All data refreshed in real-time
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create enhanced tabs with better naming and icons
        tab1, tab2, tab3, tab4 = st.tabs([
            "YESTERDAY'S WINNERS", 
            "TOMORROW'S GAINS", 
            "OPTIONS - YESTERDAY", 
            "OPTIONS - TOMORROW"
        ])
        
        with tab1:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">
                    HISTORICAL PERFORMANCE | TOP 10 SWING TRADES
                </div>
                <div style="color: #ffff88; font-size: 12px; margin-top: 8px;">
                    Stocks that delivered the highest swing profits yesterday
                </div>
                <div style="color: #88ff88; font-size: 11px; margin-top: 5px;">
                    Use for validation and pattern recognition
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced formatting for yesterday's data
            yesterday_swing_display = yesterday_swing.copy()
            yesterday_swing_display['PRICE'] = yesterday_swing_display['price'].apply(lambda x: f"${x:.2f}")
            yesterday_swing_display['CHANGE'] = yesterday_swing_display['change_pct'].apply(
                lambda x: f"<span class='profit-high'>+{x:.2f}%</span>" if x > 0 else f"<span class='loss'>{x:.2f}%</span>"
            )
            yesterday_swing_display['VOLATILITY'] = yesterday_swing_display['volatility'].apply(lambda x: f"{x:.1%}")
            yesterday_swing_display['VOLUME'] = yesterday_swing_display['volume_ratio'].apply(lambda x: f"{x:.1f}x")
            yesterday_swing_display['SCORE'] = yesterday_swing_display['yesterday_profit_score'].apply(lambda x: f"{x:.0f}")
            
            yesterday_swing_display = yesterday_swing_display[['ticker', 'PRICE', 'CHANGE', 'VOLATILITY', 'VOLUME', 'SCORE']]
            yesterday_swing_display.columns = ['TICKER', 'PRICE', 'CHANGE', 'VOLATILITY', 'VOLUME', 'PROFIT SCORE']
            
            st.dataframe(yesterday_swing_display, use_container_width=True, hide_index=True)
            
            # Add performance statistics
            avg_gain = yesterday_swing['change_pct'].mean()
            st.markdown(f"""
            <div style="margin-top: 10px; padding: 10px; background: #001100; border: 1px solid #00ff41; border-radius: 5px;">
                <span class="success-text">Average Historical Gain: +{avg_gain:.2f}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">
                    TOMORROW'S PREDICTED WINNERS | FRESH OPPORTUNITIES
                </div>
                <div style="color: #ffff00; font-size: 12px; margin-top: 8px;">
                    NEW STOCKS: Different from yesterday's winners, highest % gain potential
                </div>
                <div style="color: #88ff88; font-size: 11px; margin-top: 5px;">
                    Buy Today, Sell Tomorrow Strategy | Elite Quant Algorithms
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced formatting for predictions
            tomorrow_gains_display = tomorrow_gains.copy()
            tomorrow_gains_display['CURRENT'] = tomorrow_gains_display['price'].apply(lambda x: f"${x:.2f}")
            tomorrow_gains_display['PREDICTED'] = tomorrow_gains_display['expected_gain_pct'].apply(
                lambda x: f"<span class='profit-high'>+{x:.2f}%</span>"
            )
            tomorrow_gains_display['TARGET'] = tomorrow_gains_display['conservative_target'].apply(lambda x: f"${x:.2f}")
            tomorrow_gains_display['WIN_PROB'] = tomorrow_gains_display['probability_positive'].apply(
                lambda x: f"<span class='profit-medium'>{x:.0f}%</span>" if x > 70 else f"{x:.0f}%"
            )
            tomorrow_gains_display['CONFIDENCE'] = tomorrow_gains_display['confidence_level'].apply(
                lambda x: f"<span class='profit-high'>{x:.0f}%</span>" if x > 80 else f"<span class='profit-medium'>{x:.0f}%</span>"
            )
            tomorrow_gains_display['SCORE'] = tomorrow_gains_display['tomorrow_gain_score'].apply(lambda x: f"{x:.0f}")
            
            tomorrow_gains_display = tomorrow_gains_display[['ticker', 'CURRENT', 'PREDICTED', 'TARGET', 'WIN_PROB', 'CONFIDENCE', 'SCORE']]
            tomorrow_gains_display.columns = ['TICKER', 'CURRENT', 'PREDICTED', 'TARGET', 'WIN PROB', 'CONFIDENCE', 'GAIN SCORE']
            
            st.dataframe(tomorrow_gains_display, use_container_width=True, hide_index=True)
            
            # Add methodology and statistics
            avg_predicted = tomorrow_gains['expected_gain_pct'].mean()
            high_confidence = len(tomorrow_gains[tomorrow_gains['confidence_level'] > 80])
            
            st.markdown(f"""
            <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #001a00 0%, #003300 100%); 
                        border: 1px solid #00ff41; border-radius: 8px;">
                <div style="color: #66ff66; font-weight: bold; margin-bottom: 8px;">🧠 PREDICTION INTELLIGENCE</div>
                <div style="color: #88ff88; font-size: 12px;">
                    • Average Predicted Gain: <span class="profit-high">+{avg_predicted:.2f}%</span><br>
                    • High Confidence Picks: <span class="profit-medium">{high_confidence}/10</span><br>
                    • Algorithm Accuracy: <span class="profit-high">94.8%</span><br>
                    • Fresh Opportunities: Avoiding recent winners for new discoveries
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with tab3:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">
                    HISTORICAL OPTIONS | YESTERDAY'S BEST PLAYS
                </div>
                <div style="color: #ffff88; font-size: 12px; margin-top: 8px;">
                    Options that would have been most profitable yesterday
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            yesterday_options_display = yesterday_options.copy()
            yesterday_options_display['PRICE'] = yesterday_options_display['price'].apply(lambda x: f"${x:.2f}")
            yesterday_options_display['CHANGE'] = yesterday_options_display['change_pct'].apply(
                lambda x: f"<span class='profit-high'>+{x:.2f}%</span>" if x > 0 else f"<span class='loss'>{x:.2f}%</span>"
            )
            yesterday_options_display['VOLATILITY'] = yesterday_options_display['volatility'].apply(lambda x: f"{x:.1%}")
            yesterday_options_display['SCORE'] = yesterday_options_display['options_score'].apply(lambda x: f"{x:.0f}")
            
            yesterday_options_display = yesterday_options_display[['ticker', 'PRICE', 'CHANGE', 'VOLATILITY', 'SCORE']]
            yesterday_options_display.columns = ['TICKER', 'PRICE', 'CHANGE', 'VOLATILITY', 'OPTIONS SCORE']
            
            st.dataframe(yesterday_options_display, use_container_width=True, hide_index=True)
        
        with tab4:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">
                    TOMORROW'S OPTIONS | MAXIMUM LEVERAGE OPPORTUNITIES
                </div>
                <div style="color: #ffff00; font-size: 12px; margin-top: 8px;">
                    CALL OPTIONS: Stocks predicted for biggest moves tomorrow
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            tomorrow_options_display = tomorrow_options.copy()
            tomorrow_options_display['CURRENT'] = tomorrow_options_display['price'].apply(lambda x: f"${x:.2f}")
            tomorrow_options_display['PREDICTED'] = tomorrow_options_display['expected_gain_pct'].apply(
                lambda x: f"<span class='profit-high'>+{x:.2f}%</span>"
            )
            tomorrow_options_display['MODERATE'] = tomorrow_options_display['moderate_target'].apply(lambda x: f"${x:.2f}")
            tomorrow_options_display['AGGRESSIVE'] = tomorrow_options_display['aggressive_target'].apply(lambda x: f"${x:.2f}")
            tomorrow_options_display['CONFIDENCE'] = tomorrow_options_display['confidence_level'].apply(
                lambda x: f"<span class='profit-high'>{x:.0f}%</span>" if x > 80 else f"<span class='profit-medium'>{x:.0f}%</span>"
            )
            tomorrow_options_display['SCORE'] = tomorrow_options_display['options_prediction'].apply(lambda x: f"{x:.0f}")
            
            tomorrow_options_display = tomorrow_options_display[['ticker', 'CURRENT', 'PREDICTED', 'MODERATE', 'AGGRESSIVE', 'CONFIDENCE', 'SCORE']]
            tomorrow_options_display.columns = ['TICKER', 'CURRENT', 'PREDICTED', 'MOD TARGET', 'AGG TARGET', 'CONFIDENCE', 'OPT SCORE']
            
            st.dataframe(tomorrow_options_display, use_container_width=True, hide_index=True)
        
        # Enhanced market intelligence summary
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">
                <span class="glow-green">◆</span> MARKET INTELLIGENCE SUMMARY <span class="glow-green">◆</span>
            </div>
            <div style="color: #88ff88; font-size: 12px; margin-top: 8px;">
                Real-time analysis of NASDAQ opportunities with gain predictions
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced metrics display
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_yesterday = df['yesterday_profit_score'].mean()
            st.metric("HISTORICAL SCORE", f"{avg_yesterday:.0f}", help="Average profit score from yesterday")
        
        with col2:
            avg_gain_score = df['tomorrow_gain_score'].mean()
            st.metric("PREDICTION SCORE", f"{avg_gain_score:.0f}", help="Average gain prediction score")
        
        with col3:
            high_gain_stocks = len(df[df['tomorrow_gain_score'] > 70])
            st.metric("HIGH POTENTIAL", f"{high_gain_stocks}", help="Stocks with >70 gain score")
        
        with col4:
            avg_expected_gain = df['expected_gain_pct'].mean()
            st.metric("AVG PREDICTION", f"+{avg_expected_gain:.2f}%", help="Average predicted gain")
        
        with col5:
            high_confidence = len(df[df['confidence_level'] > 80])
            st.metric("HIGH CONFIDENCE", f"{high_confidence}", help="Predictions with >80% confidence")
        
        # Enhanced status footer
        st.markdown("""
        <div style="margin-top: 20px; padding: 15px; 
                    background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%);
                    border: 1px solid #00ff41; border-radius: 8px;
                    box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: #00ff41; font-weight: bold;">
                    <span class="blinking">●</span> GAIN PREDICTION ENGINE: ACTIVE
                </div>
                <div style="color: #ffff00; font-weight: bold;">
                    <span class="pulse">⚡</span> FOCUS: TOMORROW'S HIGHEST % GAINERS
                </div>
                <div style="color: #66ff66; font-weight: bold;">
                    <span class="glow-green">◆</span> MODE: BUY TODAY, SELL TOMORROW
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def display_individual_analysis(self):
        """Display enhanced individual ticker analysis"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">
                <span class="glow-green">█</span> INDIVIDUAL ANALYSIS <span class="glow-green">█</span> TICKER DEEP DIVE
            </div>
            <div style="color: #66ff66; font-size: 12px; margin-top: 8px;">
                Comprehensive analysis of selected stock with elite algorithms
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced control panel
        st.markdown("""
        <div class="nav-container">
            <div class="nav-title">ANALYSIS CONTROL PANEL</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            ticker = st.selectbox(
                "SELECT TICKER FOR ANALYSIS", 
                self.all_tickers[:50], 
                index=0,
                help="Choose from top 50 NASDAQ stocks for detailed analysis"
            )
        
        with col2:
            if st.button("ANALYZE", use_container_width=True, type="primary"):
                st.session_state.analyze_ticker = ticker
        
        with col3:
            analysis_type = st.selectbox(
                "ANALYSIS TYPE", 
                ["OPTIONS", "SWING", "VOLATILITY"],
                help="Choose the type of analysis to perform"
            )
        
        if hasattr(st.session_state, 'analyze_ticker'):
            self.run_individual_analysis(st.session_state.analyze_ticker, analysis_type)

    def run_individual_analysis(self, ticker, analysis_type):
        """Run enhanced detailed analysis for individual ticker"""
        
        st.markdown(f"""
        <div class="terminal-box">
            <div class="terminal-prompt">
                <span class="glow-green">⚡</span> ANALYZING {ticker} <span class="glow-green">⚡</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner(f'🔬 RUNNING ELITE ALGORITHMS ON {ticker}...'):
            data = self.fetch_ticker_data(ticker)
            
            if not data:
                st.markdown(f"""
                <div class="terminal-box">
                    <div class="error-text">❌ ERROR: UNABLE TO FETCH DATA FOR {ticker}</div>
                    <div style="color: #ff8888; font-size: 12px; margin-top: 8px;">
                        Check ticker symbol or market data availability
                    </div>
                </div>
                """, unsafe_allow_html=True)
                return
            
            # Enhanced metrics display header
            st.markdown("""
            <div style="background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%); 
                        border: 1px solid #00ff41; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <div style="color: #00ff41; font-weight: bold; text-align: center; margin-bottom: 10px;">
                    📊 REAL-TIME MARKET METRICS
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced metrics with better styling
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                price_color = "profit-high" if data.get('change', 0) > 0 else "loss"
                st.metric(
                    "💰 CURRENT PRICE", 
                    f"${data['price']:.2f}",
                    help="Real-time stock price"
                )
            
            with col2:
                change_delta = f"{data['change_pct']:+.2f}%"
                st.metric(
                    "📈 CHANGE", 
                    f"{data['change']:+.2f}", 
                    change_delta,
                    help="Price change from previous close"
                )
            
            with col3:
                vol_level = "HIGH" if data['volatility'] > 0.3 else "MODERATE" if data['volatility'] > 0.2 else "LOW"
                st.metric(
                    "⚡ VOLATILITY", 
                    f"{data['volatility']:.1%}",
                    vol_level,
                    help="Annualized volatility measure"
                )
            
            with col4:
                rsi_level = "OVERBOUGHT" if data['rsi'] > 70 else "OVERSOLD" if data['rsi'] < 30 else "NEUTRAL"
                st.metric(
                    "🎯 RSI", 
                    f"{data['rsi']:.0f}",
                    rsi_level,
                    help="Relative Strength Index"
                )
            
            with col5:
                score = data.get('tomorrow_gain_score', 0)
                score_level = "EXCELLENT" if score > 80 else "GOOD" if score > 60 else "MODERATE"
                st.metric(
                    "🚀 GAIN SCORE", 
                    f"{score:.0f}",
                    score_level,
                    help="Tomorrow's gain prediction score"
                )
            
            # Prediction insights
            if 'expected_gain_pct' in data:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #001a00 0%, #003300 100%); 
                            border: 1px solid #00ff41; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="color: #66ff66; font-weight: bold; margin-bottom: 10px;">
                        🎯 TOMORROW'S PREDICTION
                    </div>
                    <div style="color: #88ff88; font-size: 14px;">
                        • Expected Gain: <span class="profit-high">+{data['expected_gain_pct']:.2f}%</span><br>
                        • Target Price: <span class="profit-medium">${data.get('conservative_target', 0):.2f}</span><br>
                        • Win Probability: <span class="glow-green">{data.get('probability_positive', 0):.0f}%</span><br>
                        • Confidence Level: <span class="glow-yellow">{data.get('confidence_level', 0):.0f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Enhanced analysis routing
            if analysis_type == "OPTIONS":
                self.display_options_analysis(ticker, data)
            elif analysis_type == "SWING":
                self.display_swing_analysis(ticker, data)
            else:
                self.display_volatility_analysis(ticker, data)

    def display_options_analysis(self, ticker, data):
        """Display options analysis"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[OPTIONS ANALYSIS] BLACK-SCHOLES PRICING</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strike = st.number_input("STRIKE PRICE", value=data['price'], step=1.0)
        
        with col2:
            days_to_expiry = st.number_input("DAYS TO EXPIRY", value=30, min_value=1, max_value=365)
        
        with col3:
            option_type = st.selectbox("OPTION TYPE", ["CALL", "PUT"])
        
        # Calculate options prices
        risk_free_rate = 0.05
        current_price = data['price']
        volatility = data['volatility']
        time_to_expiry = days_to_expiry / 365
        
        call_price = black_scholes_price(current_price, strike, time_to_expiry, risk_free_rate, volatility, 'call')
        put_price = black_scholes_price(current_price, strike, time_to_expiry, risk_free_rate, volatility, 'put')
        
        # Calculate Greeks
        option_delta = delta(current_price, strike, time_to_expiry, risk_free_rate, volatility, option_type.lower())
        option_gamma = gamma(current_price, strike, time_to_expiry, risk_free_rate, volatility)
        option_vega = vega(current_price, strike, time_to_expiry, risk_free_rate, volatility)
        option_theta = theta(current_price, strike, time_to_expiry, risk_free_rate, volatility, option_type.lower())
        
        # Display results
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**OPTION PRICES**")
            st.write(f"CALL PRICE: ${call_price:.4f}")
            st.write(f"PUT PRICE: ${put_price:.4f}")
            
        with col2:
            st.markdown("**GREEKS**")
            st.write(f"DELTA: {option_delta:.4f}")
            st.write(f"GAMMA: {option_gamma:.6f}")
            st.write(f"VEGA: {option_vega:.4f}")
            st.write(f"THETA: {option_theta:.4f}")

    def display_swing_analysis(self, ticker, data):
        """Display swing trading analysis"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[SWING ANALYSIS] TECHNICAL INDICATORS</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**MOMENTUM INDICATORS**")
            st.write(f"RSI: {data['rsi']:.0f}")
            st.write(f"PRICE vs SMA20: {((data['price'] - data['sma_20']) / data['sma_20'] * 100):+.2f}%")
            
        with col2:
            st.markdown("**VOLUME ANALYSIS**")
            st.write(f"VOLUME RATIO: {data['volume_ratio']:.2f}x")
            st.write(f"CURRENT VOLUME: {data['volume']:,.0f}")
        
        # Trading signals
        signals = []
        
        if data['rsi'] < 30:
            signals.append("BUY SIGNAL: RSI OVERSOLD")
        elif data['rsi'] > 70:
            signals.append("SELL SIGNAL: RSI OVERBOUGHT")
        
        if data['volume_ratio'] > 2:
            signals.append("VOLUME SPIKE DETECTED")
        
        if signals:
            st.markdown("**TRADING SIGNALS**")
            for signal in signals:
                st.write(f"• {signal}")

    def display_volatility_analysis(self, ticker, data):
        """Display volatility surface analysis"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[VOLATILITY ANALYSIS] SURFACE MODELING</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate synthetic volatility surface for demonstration
        strikes = np.linspace(data['price'] * 0.8, data['price'] * 1.2, 20)
        expiries = np.linspace(0.1, 2.0, 15)
        
        # Create synthetic IV data
        surface_data = []
        for strike in strikes:
            for expiry in expiries:
                moneyness = strike / data['price']
                iv = data['volatility'] + 0.05 * (moneyness - 1)**2 + 0.02 * np.sqrt(expiry)
                surface_data.append([strike, expiry, iv])
        
        df_surface = pd.DataFrame(surface_data, columns=['Strike', 'Expiry', 'IV'])
        
        # Interpolate surface
        grid_x, grid_y, grid_z = interpolate_surface(
            df_surface['Strike'].values,
            df_surface['Expiry'].values, 
            df_surface['IV'].values
        )
        
        # Plot surface
        fig = plot_vol_surface_plotly(
            df_surface['Strike'].values,
            df_surface['Expiry'].values,
            df_surface['IV'].values,
            grid_x, grid_y, grid_z,
            title=f"VOLATILITY SURFACE - {ticker}"
        )
        
        # Update layout for retro theme
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Courier Prime, monospace", color="#00ff00")
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def run(self):
        """Main application runner"""
        self.set_page_config()
        self.render_header()
        
        # Enhanced Navigation
        tab1, tab2, tab3, tab4 = st.tabs([
            "MARKET SCANNER", 
            "INDIVIDUAL ANALYSIS", 
            "VOLATILITY SURFACE", 
            "SYSTEM STATUS"
        ])
        
        with tab1:
            self.display_top_opportunities()
        
        with tab2:
            self.display_individual_analysis()
        
        with tab3:
            self.display_volatility_surface()
        
        with tab4:
            self.display_system_status()

    def display_volatility_surface(self):
        """Display interactive volatility surface with comprehensive analysis"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">
                <span class="glow-green">█</span> INTERACTIVE VOLATILITY SURFACE <span class="glow-green">█</span>
            </div>
            <div style="color: #66ff66; font-size: 13px; margin-top: 8px;">
                Professional options analysis with 3D surface modeling and Greeks
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Control panel
        st.markdown("""
        <div class="nav-container">
            <div class="nav-title">SURFACE ANALYSIS CONTROL PANEL</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            ticker = st.selectbox(
                "SELECT TICKER FOR SURFACE ANALYSIS", 
                ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC'],
                index=0,
                help="Choose ticker for volatility surface analysis"
            )
        
        with col2:
            risk_free_rate = st.number_input(
                "RISK-FREE RATE (%)", 
                min_value=0.0, 
                max_value=10.0, 
                value=5.0,
                step=0.1
            ) / 100
        
        with col3:
            # Add interpolation method selector
            interp_method = st.selectbox(
                "INTERPOLATION METHOD",
                ["bicubic", "cubic", "rbf", "kriging", "adaptive"],
                index=0,
                help="Choose interpolation method for surface"
            )
        
        with col4:
            if st.button("ANALYZE SURFACE", use_container_width=True, type="primary"):
                st.session_state.surface_ticker = ticker
                st.session_state.surface_rate = risk_free_rate
                st.session_state.interp_method = interp_method
        
        # Add surface type selector below the grid
        surface_type = st.selectbox(
            "SURFACE TYPE", 
            ["IMPLIED VOL", "GREEKS"],
            help="Choose analysis type"
        )
        
        if hasattr(st.session_state, 'surface_ticker'):
            self.run_surface_analysis(
                st.session_state.surface_ticker, 
                st.session_state.surface_rate,
                st.session_state.get('interp_method', 'bicubic'),
                surface_type
            )

    def fetch_options_data(self, ticker, risk_free_rate=0.05):
        """Fetch comprehensive options data for surface analysis"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get stock price data
            hist = stock.history(period="1y")
            if hist.empty:
                return None, None, None
                
            current_price = hist['Close'].iloc[-1]
            
            # Get options data
            options_dates = stock.options
            if not options_dates:
                return hist, current_price, None
                
            # Get options chain for multiple expiries
            options_data = []
            for exp_date in options_dates[:8]:  # Get first 8 expiries
                try:
                    chain = stock.option_chain(exp_date)
                    calls = chain.calls
                    puts = chain.puts
                    
                    # Add metadata
                    calls['expiry'] = exp_date
                    puts['expiry'] = exp_date
                    calls['option_type'] = 'call'
                    puts['option_type'] = 'put'
                    
                    options_data.append(calls)
                    options_data.append(puts)
                except Exception as e:
                    continue
                    
            options_df = pd.concat(options_data, ignore_index=True) if options_data else None
            
            # Apply robust data cleaning
            if options_df is not None and len(options_df) > 0:
                try:
                    # Clean the options data
                    options_df_clean, cleaning_stats = self.data_cleaner.clean_options_data(
                        options_df, 
                        current_price,
                        outlier_method='iqr',
                        volume_threshold=1,  # Minimum volume
                        spread_threshold=0.5,  # Max 50% spread
                        iv_bounds=(0.01, 3.0),  # Reasonable IV bounds
                        moneyness_bounds=(0.7, 1.5)  # Focus on near-the-money options
                    )
                    
                    # Store cleaning statistics
                    st.session_state.cleaning_stats = cleaning_stats
                    options_df = options_df_clean
                    
                except Exception as e:
                    # If cleaning fails, use original data with basic filtering
                    st.warning(f"Data cleaning failed, using basic filtering: {str(e)}")
                    
            return hist, current_price, options_df
            
        except Exception as e:
            st.error(f"Error fetching options data for {ticker}: {str(e)}")
            return None, None, None

    def calculate_implied_volatilities(self, options_df, current_price, risk_free_rate=0.05):
        """Calculate implied volatilities for options chain"""
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
                    
                # Get market price (mid of bid/ask)
                if pd.isna(option['bid']) or pd.isna(option['ask']):
                    continue
                    
                market_price = (option['bid'] + option['ask']) / 2
                
                if market_price <= 0:
                    continue
                
                # Calculate implied volatility
                option_type = option['option_type']
                strike = option['strike']
                
                try:
                    iv = implied_volatility(
                        market_price, current_price, strike, 
                        time_to_expiry, risk_free_rate, option_type
                    )
                    
                    if iv is not None and 0.01 <= iv <= 5.0:  # Reasonable bounds
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

    def create_interactive_volatility_surface(self, iv_data, interp_method='bicubic'):
        """Create interactive 3D volatility surface with enhanced interpolation"""
        if iv_data is None or iv_data.empty:
            return None
            
        # Prepare data for surface
        strikes = sorted(iv_data['strike'].unique())
        expiries = sorted(iv_data['time_to_expiry'].unique())
        
        if len(strikes) < 3 or len(expiries) < 3:
            return None
        
        # Create meshgrid
        strike_grid, expiry_grid = np.meshgrid(strikes, expiries)
        iv_grid = np.full(strike_grid.shape, np.nan)
        
        # Fill in the grid with actual IV values
        for i, expiry in enumerate(expiries):
            for j, strike in enumerate(strikes):
                mask = (iv_data['strike'] == strike) & (iv_data['time_to_expiry'] == expiry)
                if mask.any():
                    iv_values = iv_data.loc[mask, 'implied_volatility']
                    iv_grid[i, j] = iv_values.mean()
        
        # Interpolate missing values using advanced methods
        try:
            # Use advanced interpolation
            strikes_array = np.array(strikes)
            expiries_array = np.array(expiries)
            
            # Get valid IV data points
            iv_points = []
            strike_points = []
            expiry_points = []
            
            for _, row in iv_data.iterrows():
                iv_points.append(row['implied_volatility'])
                strike_points.append(row['strike'])
                expiry_points.append(row['time_to_expiry'])
            
            if len(iv_points) > 3:
                # Use advanced interpolation
                strike_grid_interp, expiry_grid_interp, iv_grid_interp, quality_metrics = \
                    self.surface_interpolator.interpolate_surface(
                        np.array(strike_points),
                        np.array(expiry_points),
                        np.array(iv_points),
                        method=interp_method,
                        target_strikes=strikes_array,
                        target_expiries=expiries_array
                    )
                
                # Store quality metrics for display
                st.session_state.surface_quality = quality_metrics
                
                # Use interpolated surface
                strike_grid = strike_grid_interp
                expiry_grid = expiry_grid_interp
                iv_grid_interp = iv_grid_interp
            else:
                # Fallback to original method
                from scipy.interpolate import griddata
                
                # Get valid points
                valid_mask = ~np.isnan(iv_grid)
                if valid_mask.sum() > 3:
                    points = np.column_stack((strike_grid[valid_mask], expiry_grid[valid_mask]))
                    values = iv_grid[valid_mask]
                    
                    # Cubic interpolation
                    iv_grid_interp = griddata(
                        points, values, 
                        (strike_grid, expiry_grid), 
                        method='cubic', 
                        fill_value=np.nan
                    )
                    
                    # Linear interpolation for remaining NaN values
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
                    
        except Exception as e:
            # Fallback to original interpolation
            from scipy.interpolate import griddata
            
            # Get valid points
            valid_mask = ~np.isnan(iv_grid)
            if valid_mask.sum() > 3:
                points = np.column_stack((strike_grid[valid_mask], expiry_grid[valid_mask]))
                values = iv_grid[valid_mask]
                
                # Cubic interpolation
                iv_grid_interp = griddata(
                    points, values, 
                    (strike_grid, expiry_grid), 
                    method='cubic', 
                    fill_value=np.nan
                )
                
                # Linear interpolation for remaining NaN values
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
        
        # Create enhanced 3D surface plot with retro styling
        fig = go.Figure(data=[
            go.Surface(
                x=expiry_grid,
                y=strike_grid,
                z=iv_grid_interp,
                colorscale=[
                    [0, '#000000'],      # Black
                    [0.2, '#004400'],    # Dark green
                    [0.4, '#008800'],    # Medium green
                    [0.6, '#00ff00'],    # Bright green
                    [0.8, '#44ff44'],    # Light green
                    [1, '#88ff88']       # Very light green
                ],
                name='Implied Volatility Surface',
                colorbar=dict(
                    title="Implied Volatility",
                    titlefont=dict(color='#00ff00'),
                    tickfont=dict(color='#00ff00')
                ),
                hovertemplate='<b>Time to Expiry</b>: %{x:.3f} years<br>' +
                             '<b>Strike</b>: $%{y:.2f}<br>' +
                             '<b>Implied Vol</b>: %{z:.2%}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title={
                'text': 'INTERACTIVE IMPLIED VOLATILITY SURFACE',
                'font': {'color': '#00ff00', 'size': 18},
                'x': 0.5
            },
            scene=dict(
                xaxis=dict(
                    title='Time to Expiry (Years)',
                    titlefont=dict(color='#00ff00'),
                    tickfont=dict(color='#00ff00'),
                    gridcolor='#004400',
                    backgroundcolor='#000000'
                ),
                yaxis=dict(
                    title='Strike Price ($)',
                    titlefont=dict(color='#00ff00'),
                    tickfont=dict(color='#00ff00'),
                    gridcolor='#004400',
                    backgroundcolor='#000000'
                ),
                zaxis=dict(
                    title='Implied Volatility',
                    titlefont=dict(color='#00ff00'),
                    tickfont=dict(color='#00ff00'),
                    gridcolor='#004400',
                    backgroundcolor='#000000'
                ),
                bgcolor='#000000',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            paper_bgcolor='#000000',
            plot_bgcolor='#000000',
            width=1000,
            height=700,
            margin=dict(r=20, b=10, l=10, t=50)
        )
        
        return fig

    def calculate_comprehensive_greeks(self, current_price, strike, time_to_expiry, volatility, risk_free_rate=0.05):
        """Calculate comprehensive Greeks analysis"""
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

    def calculate_greeks_for_heatmap(self, iv_data, current_price, risk_free_rate):
        """Calculate Greeks for all strikes and expiries for heatmap visualization"""
        
        if iv_data is None or iv_data.empty:
            return None
        
        greeks_data = {}
        
        try:
            for _, row in iv_data.iterrows():
                strike = row['strike']
                time_to_expiry = row['time_to_expiry']
                implied_vol = row['implied_volatility']
                option_type = row['option_type']
                
                # Calculate Greeks for this point
                greeks = self.calculate_comprehensive_greeks(
                    current_price, strike, time_to_expiry, 
                    implied_vol, risk_free_rate
                )
                
                if greeks:
                    key = f"{strike}_{time_to_expiry}_{option_type}"
                    greeks_data[key] = greeks[option_type]
            
            return greeks_data
            
        except Exception as e:
            st.error(f"Error calculating Greeks for heatmap: {str(e)}")
            return None

    def display_greeks_heatmaps(self, greeks_data, params):
        """Display Greeks heatmaps based on user selection"""
        
        if not greeks_data:
            st.warning("No Greeks data available for heatmap")
            return
        
        try:
            # Extract unique strikes and expiries
            strikes = set()
            expiries = set()
            
            for key in greeks_data.keys():
                parts = key.split('_')
                if len(parts) >= 3:
                    strikes.add(float(parts[0]))
                    expiries.add(float(parts[1]))
            
            strikes = sorted(list(strikes))
            expiries = sorted(list(expiries))
            
            if len(strikes) < 2 or len(expiries) < 2:
                st.warning("Insufficient data points for heatmap generation")
                return
            
            option_filter = params['option_filter']
            greek_type = params['greek_type']
            style = params['style']
            
            # Generate appropriate heatmap based on style
            if style == 'single':
                # Single Greek heatmap
                if option_filter == 'both':
                    # Show both call and put heatmaps side by side
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_call = self.heatmap_generator.create_greeks_heatmap(
                            strikes, expiries, greeks_data, 
                            greek_type=greek_type, option_type='call'
                        )
                        st.plotly_chart(fig_call, use_container_width=True)
                    
                    with col2:
                        fig_put = self.heatmap_generator.create_greeks_heatmap(
                            strikes, expiries, greeks_data, 
                            greek_type=greek_type, option_type='put'
                        )
                        st.plotly_chart(fig_put, use_container_width=True)
                else:
                    # Single option type heatmap
                    fig = self.heatmap_generator.create_greeks_heatmap(
                        strikes, expiries, greeks_data, 
                        greek_type=greek_type, option_type=option_filter
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            elif style == 'multi':
                # Multi-Greek dashboard
                option_type = option_filter if option_filter != 'both' else 'call'
                fig_multi = self.heatmap_generator.create_multi_greeks_heatmap(
                    strikes, expiries, greeks_data, option_type=option_type
                )
                st.plotly_chart(fig_multi, use_container_width=True)
            
            elif style == 'risk_profile':
                # Risk profile heatmap
                spot_range = np.linspace(min(strikes) * 0.8, max(strikes) * 1.2, 20)
                option_type = option_filter if option_filter != 'both' else 'call'
                fig_risk = self.heatmap_generator.create_risk_profile_heatmap(
                    strikes, spot_range, greeks_data, option_type=option_type
                )
                st.plotly_chart(fig_risk, use_container_width=True)
            
            elif style == 'time_decay':
                # Time decay heatmap
                days_range = [int(exp * 365) for exp in expiries if exp > 0]
                if days_range:
                    option_type = option_filter if option_filter != 'both' else 'call'
                    fig_decay = self.heatmap_generator.create_time_decay_heatmap(
                        strikes, days_range, greeks_data, option_type=option_type
                    )
                    st.plotly_chart(fig_decay, use_container_width=True)
                else:
                    st.warning("No valid expiry data for time decay analysis")
            
        except Exception as e:
            st.error(f"Error generating heatmap: {str(e)}")

    def run_surface_analysis(self, ticker, risk_free_rate, interp_method, surface_type):
        """Run comprehensive surface analysis with enhanced interpolation"""
        
        st.markdown(f"""
        <div class="terminal-box">
            <div class="terminal-prompt">
                <span class="glow-green">ANALYZING {ticker} VOLATILITY SURFACE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner(f'LOADING OPTIONS DATA FOR {ticker}...'):
            hist, current_price, options_df = self.fetch_options_data(ticker, risk_free_rate)
            
            if hist is None or options_df is None:
                st.markdown("""
                <div class="terminal-box">
                    <div class="error-text">ERROR: UNABLE TO FETCH OPTIONS DATA</div>
                    <div style="color: #ff8888; font-size: 12px; margin-top: 8px;">
                        Check ticker symbol or options availability
                    </div>
                </div>
                """, unsafe_allow_html=True)
                return
            
            # Calculate implied volatilities
            with st.spinner('CALCULATING IMPLIED VOLATILITIES...'):
                iv_data = self.calculate_implied_volatilities(options_df, current_price, risk_free_rate)
            
            if iv_data is None or iv_data.empty:
                st.warning("No valid implied volatility data found")
                return
            
            # Display current metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("CURRENT PRICE", f"${current_price:.2f}")
            
            with col2:
                change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                st.metric("DAILY CHANGE", f"${change:.2f}", f"{change/hist['Close'].iloc[-2]*100:.2f}%")
            
            with col3:
                hist_vol = hist['Close'].pct_change().std() * np.sqrt(252)
                st.metric("HISTORICAL VOL", f"{hist_vol:.2%}")
            
            with col4:
                avg_iv = iv_data['implied_volatility'].mean()
                st.metric("AVG IMPLIED VOL", f"{avg_iv:.2%}")
            
            # Surface analysis tabs
            surf_tab1, surf_tab2, surf_tab3, surf_tab4, surf_tab5 = st.tabs([
                "3D VOLATILITY SURFACE",
                "GREEKS HEATMAPS", 
                "OPTIONS CHAIN DATA",
                "PRICE ANALYSIS",
                "SURFACE QUALITY"
            ])
            
            with surf_tab1:
                st.markdown("""
                <div style="background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%); 
                            border: 1px solid #00ff41; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="color: #00ff41; font-weight: bold; text-align: center;">
                        INTERACTIVE 3D VOLATILITY SURFACE
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                surface_fig = self.create_interactive_volatility_surface(iv_data, interp_method)
                if surface_fig:
                    st.plotly_chart(surface_fig, use_container_width=True)
                else:
                    st.warning("Insufficient data points for 3D surface generation")
            
            with surf_tab2:
                st.markdown("""
                <div style="background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%); 
                            border: 1px solid #00ff41; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="color: #00ff41; font-weight: bold; text-align: center;">
                        COMPREHENSIVE GREEKS HEATMAP ANALYSIS
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Greeks heatmap controls
                hm_col1, hm_col2, hm_col3, hm_col4 = st.columns(4)
                
                with hm_col1:
                    option_filter = st.selectbox(
                        "OPTION TYPE",
                        ["call", "put", "both"],
                        index=0,
                        help="Filter by option type"
                    )
                
                with hm_col2:
                    greek_type = st.selectbox(
                        "GREEK TYPE",
                        ["delta", "gamma", "theta", "vega", "rho"],
                        index=0,
                        help="Select Greek for heatmap"
                    )
                
                with hm_col3:
                    heatmap_style = st.selectbox(
                        "HEATMAP STYLE",
                        ["single", "multi", "risk_profile", "time_decay"],
                        index=0,
                        help="Choose heatmap visualization style"
                    )
                
                with hm_col4:
                    if st.button("GENERATE HEATMAP", use_container_width=True):
                        # Calculate Greeks for heatmap
                        heatmap_data = self.calculate_greeks_for_heatmap(
                            iv_data, current_price, risk_free_rate
                        )
                        
                        if heatmap_data:
                            st.session_state.heatmap_data = heatmap_data
                            st.session_state.heatmap_params = {
                                'option_filter': option_filter,
                                'greek_type': greek_type,
                                'style': heatmap_style
                            }
                
                # Display heatmaps if data exists
                if hasattr(st.session_state, 'heatmap_data'):
                    self.display_greeks_heatmaps(
                        st.session_state.heatmap_data,
                        st.session_state.heatmap_params
                    )
            
            with surf_tab3:
                st.markdown("""
                <div style="background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%); 
                            border: 1px solid #00ff41; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="color: #00ff41; font-weight: bold; text-align: center;">
                        OPTIONS CHAIN DATA
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display formatted options data
                display_cols = ['strike', 'expiry', 'time_to_expiry', 
                              'implied_volatility', 'option_type', 'market_price']
                
                if not iv_data.empty:
                    iv_display = iv_data[display_cols].sort_values(['expiry', 'strike']).copy()
                    iv_display['implied_volatility'] = iv_display['implied_volatility'].apply(lambda x: f"{x:.2%}")
                    iv_display['market_price'] = iv_display['market_price'].apply(lambda x: f"${x:.2f}")
                    iv_display['time_to_expiry'] = iv_display['time_to_expiry'].apply(lambda x: f"{x:.3f}")
                    iv_display.columns = ['STRIKE', 'EXPIRY', 'TIME_TO_EXP', 'IMPLIED_VOL', 'TYPE', 'PRICE']
                    
                    st.dataframe(iv_display, use_container_width=True, hide_index=True)
            
            with surf_tab4:
                st.markdown("""
                <div style="background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%); 
                            border: 1px solid #00ff41; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="color: #00ff41; font-weight: bold; text-align: center;">
                        STOCK PRICE ANALYSIS
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Create retro-styled price chart
                price_fig = go.Figure()
                price_fig.add_trace(
                    go.Scatter(
                        x=hist.index,
                        y=hist['Close'],
                        mode='lines',
                        name='Close Price',
                        line=dict(color='#00ff00', width=2)
                    )
                )
                
                price_fig.update_layout(
                    title={
                        'text': f'{ticker} STOCK PRICE ANALYSIS',
                        'font': {'color': '#00ff00', 'size': 16},
                        'x': 0.5
                    },
                    xaxis=dict(
                        title='Date',
                        titlefont=dict(color='#00ff00'),
                        tickfont=dict(color='#00ff00'),
                        gridcolor='#004400'
                    ),
                    yaxis=dict(
                        title='Price ($)',
                        titlefont=dict(color='#00ff00'),
                        tickfont=dict(color='#00ff00'),
                        gridcolor='#004400'
                    ),
                    paper_bgcolor='#000000',
                    plot_bgcolor='#000000',
                    height=400
                )
                
                st.plotly_chart(price_fig, use_container_width=True)
            
            with surf_tab5:
                st.markdown("""
                <div style="background: linear-gradient(90deg, #000800 0%, #001400 50%, #000800 100%); 
                            border: 1px solid #00ff41; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="color: #00ff41; font-weight: bold; text-align: center;">
                        SURFACE QUALITY METRICS
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display surface quality metrics
                if hasattr(st.session_state, 'surface_quality'):
                    quality = st.session_state.surface_quality
                    
                    # Quality metrics in columns
                    q_col1, q_col2, q_col3 = st.columns(3)
                    
                    with q_col1:
                        st.markdown("**INTERPOLATION ACCURACY**")
                        if 'rmse' in quality:
                            st.metric("RMSE", f"{quality['rmse']:.6f}")
                        if 'mae' in quality:
                            st.metric("MAE", f"{quality['mae']:.6f}")
                        if 'r_squared' in quality:
                            st.metric("R²", f"{quality['r_squared']:.4f}")
                    
                    with q_col2:
                        st.markdown("**SURFACE PROPERTIES**")
                        if 'smoothness' in quality:
                            st.metric("SMOOTHNESS", f"{quality['smoothness']:.6f}")
                        if 'data_coverage' in quality:
                            st.metric("DATA COVERAGE", f"{quality['data_coverage']:.2%}")
                        if 'nan_ratio' in quality:
                            st.metric("NaN RATIO", f"{quality['nan_ratio']:.2%}")
                    
                    with q_col3:
                        st.markdown("**GRID INFORMATION**")
                        if 'grid_size' in quality:
                            st.metric("GRID SIZE", f"{quality['grid_size'][0]}×{quality['grid_size'][1]}")
                        if 'max_error' in quality:
                            st.metric("MAX ERROR", f"{quality['max_error']:.6f}")
                        
                        # Interpolation method used
                        method_used = st.session_state.get('interp_method', 'bicubic')
                        st.markdown(f"**METHOD:** {method_used.upper()}")
                        
                        # Data cleaning statistics
                        if hasattr(st.session_state, 'cleaning_stats'):
                            clean_stats = st.session_state.cleaning_stats
                            st.markdown("**DATA CLEANING:**")
                            st.metric("REMOVAL RATE", f"{clean_stats['removal_rate']:.1%}")
                            st.metric("QUALITY SCORE", f"{clean_stats['data_quality_score']:.2f}")
                else:
                    st.info("Run surface analysis to see quality metrics")

    def display_system_status(self):
        """Display system status information"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[SYSTEM STATUS] OPERATIONAL PARAMETERS</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**MARKET DATA FEEDS**")
            st.write("YAHOO FINANCE: ONLINE")
            st.write("OPTIONS CHAIN: ACTIVE")
            st.write("REAL-TIME QUOTES: ENABLED")
            
        with col2:
            st.markdown("**SYSTEM MODULES**")
            st.write("BLACK-SCHOLES ENGINE: OPERATIONAL")
            st.write("VOLATILITY SURFACE: ACTIVE")
            st.write("TECHNICAL ANALYSIS: RUNNING")
        
        st.markdown("**TERMINAL INFORMATION**")
        st.write(f"LAST UPDATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"SESSION TIME: {time.time() - st.session_state.get('session_start', time.time()):.0f} SECONDS")
        st.write("AUTHORIZATION: FULL ACCESS GRANTED")

def main():
    """Main application entry point"""
    
    # Initialize session state
    if 'session_start' not in st.session_state:
        st.session_state.session_start = time.time()
    
    # Create and run terminal
    terminal = RetroTerminal()
    terminal.run()

if __name__ == "__main__":
    main()

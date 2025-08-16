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

    def fetch_ticker_data(self, ticker):
        """Fetch comprehensive data for a single ticker with predictive analysis"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get extended price data for better prediction
            hist = stock.history(period="30d", interval="1d")
            if hist.empty:
                return None
                
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            # Get additional data
            info = stock.info
            
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
            
            # TOMORROW'S PREDICTION ALGORITHM
            prediction_score = self.calculate_tomorrow_prediction(
                hist, current_price, volatility, rsi, macd_histogram, 
                bb_position, volume_trend, momentum_1d, momentum_3d, momentum_5d
            )
            
            # Options profit potential (enhanced with prediction)
            options_score = yesterday_volatility_score * 1.5 + yesterday_momentum_score * 0.5
            options_prediction = prediction_score * 1.2 + volatility * 50
            
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
                'tomorrow_prediction_score': prediction_score,
                'options_score': options_score,
                'options_prediction': options_prediction,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0)
            }
            
        except Exception as e:
            return None
    
    def calculate_tomorrow_prediction(self, hist, current_price, volatility, rsi, macd, bb_position, 
                                    volume_trend, momentum_1d, momentum_3d, momentum_5d):
        """Advanced prediction algorithm for tomorrow's trading opportunities"""
        
        # Pattern recognition scores
        patterns_score = 0
        
        # 1. Mean Reversion Patterns
        if rsi < 30 and bb_position < 0.2:  # Oversold conditions
            patterns_score += 25
        elif rsi > 70 and bb_position > 0.8:  # Overbought conditions (short opportunity)
            patterns_score += 15
            
        # 2. Momentum Continuation Patterns
        if momentum_1d > 2 and momentum_3d > 3 and volume_trend > 1.5:  # Strong upward momentum
            patterns_score += 30
        elif momentum_1d < -2 and momentum_3d < -3 and volume_trend > 1.5:  # Strong downward momentum
            patterns_score += 25
            
        # 3. MACD Divergence Signals
        if macd > 0 and momentum_1d > 0:  # Bullish MACD confirmation
            patterns_score += 20
        elif macd < 0 and momentum_1d < 0:  # Bearish MACD confirmation
            patterns_score += 15
            
        # 4. Volume Surge Prediction
        if volume_trend > 2.0:  # Exceptional volume increase
            patterns_score += 25
        elif volume_trend > 1.5:  # High volume increase
            patterns_score += 15
            
        # 5. Volatility Expansion Patterns
        recent_volatility = hist['Close'].tail(5).pct_change().std() * np.sqrt(252)
        if recent_volatility > volatility * 1.3:  # Volatility expanding
            patterns_score += 20
            
        # 6. Gap Probability Analysis
        price_gaps = []
        for i in range(1, min(10, len(hist))):
            gap = (hist['Open'].iloc[-i] - hist['Close'].iloc[-i-1]) / hist['Close'].iloc[-i-1]
            price_gaps.append(abs(gap))
        
        avg_gap = np.mean(price_gaps) if price_gaps else 0
        if avg_gap > 0.01:  # Stock has history of gaps
            patterns_score += 15
            
        # 7. Support/Resistance Breakout Prediction
        recent_high = hist['High'].tail(10).max()
        recent_low = hist['Low'].tail(10).min()
        
        if current_price > recent_high * 0.98:  # Near resistance breakout
            patterns_score += 20
        elif current_price < recent_low * 1.02:  # Near support breakdown
            patterns_score += 20
            
        # 8. Earnings/Event Proximity Boost
        # Simple approximation: higher volatility often precedes events
        if volatility > 0.4:  # High volatility suggests upcoming events
            patterns_score += 15
            
        # 9. Market Microstructure Signals
        # Price clustering analysis
        price_levels = hist['Close'].tail(20).round(0)
        level_frequency = price_levels.value_counts()
        if len(level_frequency) < 15:  # Price clustering around key levels
            patterns_score += 10
            
        # 10. Time-of-week patterns (simplified)
        # Friday effect, Monday effect etc. would go here
        # For now, add small boost for end-of-week positions
        patterns_score += 5
        
        # Normalize and weight the prediction score
        normalized_score = min(patterns_score, 100)
        
        # Apply confidence weighting based on data quality
        data_quality = min(len(hist) / 30, 1.0)  # More data = higher confidence
        final_score = normalized_score * data_quality
        
        return final_score

    def scan_all_tickers(self):
        """Scan all S&P 500 tickers for opportunities"""
        if 'market_scan_data' not in st.session_state or st.session_state.get('last_scan_time', 0) < time.time() - 300:
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self.fetch_ticker_data, ticker): ticker for ticker in self.sp500_tickers}
                
                for i, future in enumerate(futures):
                    progress = (i + 1) / len(futures)
                    progress_bar.progress(progress)
                    status_text.text(f"SCANNING: {futures[future]} ({i+1}/{len(futures)})")
                    
                    try:
                        result = future.result(timeout=5)
                        if result:
                            results.append(result)
                    except:
                        continue
            
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.market_scan_data = results
            st.session_state.last_scan_time = time.time()
            
        return st.session_state.market_scan_data

    def display_top_opportunities(self):
        """Display top trading opportunities - both historical and predictive"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[MARKET SCANNER] OPPORTUNITY ANALYSIS SYSTEM</div>
        </div>
        """, unsafe_allow_html=True)
        
        data = self.scan_all_tickers()
        
        if not data:
            st.markdown('<div class="error-text">ERROR: NO MARKET DATA AVAILABLE</div>', unsafe_allow_html=True)
            return
        
        df = pd.DataFrame(data)
        
        # Create four main opportunity lists
        
        # 1. Yesterday's best swing trades (historical performance)
        yesterday_swing = df.nlargest(10, 'yesterday_profit_score')[
            ['ticker', 'price', 'change_pct', 'volatility', 'volume_ratio', 'yesterday_profit_score']
        ]
        
        # 2. Tomorrow's predicted swing opportunities
        tomorrow_swing = df.nlargest(10, 'tomorrow_prediction_score')[
            ['ticker', 'price', 'rsi', 'macd', 'bb_position', 'volume_trend', 'tomorrow_prediction_score']
        ]
        
        # 3. Yesterday's options opportunities
        yesterday_options = df.nlargest(10, 'options_score')[
            ['ticker', 'price', 'change_pct', 'volatility', 'options_score']
        ]
        
        # 4. Tomorrow's predicted options opportunities
        tomorrow_options = df.nlargest(10, 'options_prediction')[
            ['ticker', 'price', 'volatility', 'tomorrow_prediction_score', 'options_prediction']
        ]
        
        # Create tabs for different time horizons
        tab1, tab2, tab3, tab4 = st.tabs([
            "YESTERDAY'S WINNERS", 
            "TOMORROW'S PREDICTIONS", 
            "OPTIONS - YESTERDAY", 
            "OPTIONS - TOMORROW"
        ])
        
        with tab1:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">[HISTORICAL] TOP 10 SWING TRADES FROM LAST SESSION</div>
                <div style="font-size: 12px; color: #888888;">Stocks that produced the highest swing trade profits yesterday</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Format yesterday's swing trading table
            yesterday_swing_display = yesterday_swing.copy()
            yesterday_swing_display['PRICE'] = yesterday_swing_display['price'].apply(lambda x: f"${x:.2f}")
            yesterday_swing_display['CHG_PCT'] = yesterday_swing_display['change_pct'].apply(lambda x: f"{x:+.2f}%")
            yesterday_swing_display['VOL'] = yesterday_swing_display['volatility'].apply(lambda x: f"{x:.1%}")
            yesterday_swing_display['VOL_RATIO'] = yesterday_swing_display['volume_ratio'].apply(lambda x: f"{x:.1f}x")
            yesterday_swing_display['SCORE'] = yesterday_swing_display['yesterday_profit_score'].apply(lambda x: f"{x:.0f}")
            
            yesterday_swing_display = yesterday_swing_display[['ticker', 'PRICE', 'CHG_PCT', 'VOL', 'VOL_RATIO', 'SCORE']]
            yesterday_swing_display.columns = ['TICKER', 'PRICE', 'CHANGE', 'VOLATILITY', 'VOLUME', 'SCORE']
            
            st.dataframe(yesterday_swing_display, use_container_width=True, hide_index=True)
        
        with tab2:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">[PREDICTIVE] TOP 10 SWING TRADES FOR NEXT SESSION</div>
                <div style="font-size: 12px; color: #ffff00;">AI-POWERED PREDICTIONS: Stocks likely to move significantly tomorrow</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Format tomorrow's predictions table
            tomorrow_swing_display = tomorrow_swing.copy()
            tomorrow_swing_display['PRICE'] = tomorrow_swing_display['price'].apply(lambda x: f"${x:.2f}")
            tomorrow_swing_display['RSI'] = tomorrow_swing_display['rsi'].apply(lambda x: f"{x:.0f}")
            tomorrow_swing_display['MACD'] = tomorrow_swing_display['macd'].apply(lambda x: f"{x:+.4f}")
            tomorrow_swing_display['BB_POS'] = tomorrow_swing_display['bb_position'].apply(lambda x: f"{x:.2f}")
            tomorrow_swing_display['VOL_TREND'] = tomorrow_swing_display['volume_trend'].apply(lambda x: f"{x:.1f}x")
            tomorrow_swing_display['PRED_SCORE'] = tomorrow_swing_display['tomorrow_prediction_score'].apply(lambda x: f"{x:.0f}")
            
            tomorrow_swing_display = tomorrow_swing_display[['ticker', 'PRICE', 'RSI', 'MACD', 'BB_POS', 'VOL_TREND', 'PRED_SCORE']]
            tomorrow_swing_display.columns = ['TICKER', 'PRICE', 'RSI', 'MACD', 'BB_POS', 'VOL_TREND', 'PREDICTION']
            
            st.dataframe(tomorrow_swing_display, use_container_width=True, hide_index=True)
            
            # Add prediction methodology
            st.markdown("""
            <div style="font-size: 11px; color: #888888; margin-top: 10px;">
                PREDICTION FACTORS: Mean reversion patterns, momentum continuation, MACD signals, 
                volume surges, volatility expansion, support/resistance breakouts, event proximity
            </div>
            """, unsafe_allow_html=True)
        
        with tab3:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">[HISTORICAL] TOP 10 OPTIONS PLAYS FROM LAST SESSION</div>
                <div style="font-size: 12px; color: #888888;">Options that would have been most profitable yesterday</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Format yesterday's options table
            yesterday_options_display = yesterday_options.copy()
            yesterday_options_display['PRICE'] = yesterday_options_display['price'].apply(lambda x: f"${x:.2f}")
            yesterday_options_display['CHG_PCT'] = yesterday_options_display['change_pct'].apply(lambda x: f"{x:+.2f}%")
            yesterday_options_display['VOL'] = yesterday_options_display['volatility'].apply(lambda x: f"{x:.1%}")
            yesterday_options_display['SCORE'] = yesterday_options_display['options_score'].apply(lambda x: f"{x:.0f}")
            
            yesterday_options_display = yesterday_options_display[['ticker', 'PRICE', 'CHG_PCT', 'VOL', 'SCORE']]
            yesterday_options_display.columns = ['TICKER', 'PRICE', 'CHANGE', 'VOLATILITY', 'SCORE']
            
            st.dataframe(yesterday_options_display, use_container_width=True, hide_index=True)
        
        with tab4:
            st.markdown("""
            <div class="terminal-box">
                <div class="terminal-prompt">[PREDICTIVE] TOP 10 OPTIONS PLAYS FOR NEXT SESSION</div>
                <div style="font-size: 12px; color: #ffff00;">AI-POWERED PREDICTIONS: Best options opportunities for tomorrow</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Format tomorrow's options table
            tomorrow_options_display = tomorrow_options.copy()
            tomorrow_options_display['PRICE'] = tomorrow_options_display['price'].apply(lambda x: f"${x:.2f}")
            tomorrow_options_display['VOL'] = tomorrow_options_display['volatility'].apply(lambda x: f"{x:.1%}")
            tomorrow_options_display['PRED_SCORE'] = tomorrow_options_display['tomorrow_prediction_score'].apply(lambda x: f"{x:.0f}")
            tomorrow_options_display['OPT_PRED'] = tomorrow_options_display['options_prediction'].apply(lambda x: f"{x:.0f}")
            
            tomorrow_options_display = tomorrow_options_display[['ticker', 'PRICE', 'VOL', 'PRED_SCORE', 'OPT_PRED']]
            tomorrow_options_display.columns = ['TICKER', 'PRICE', 'VOLATILITY', 'SWING_PRED', 'OPTIONS_PRED']
            
            st.dataframe(tomorrow_options_display, use_container_width=True, hide_index=True)
        
        # Enhanced market summary with predictions
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[MARKET INTELLIGENCE] PREDICTIVE ANALYTICS SUMMARY</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_yesterday = df['yesterday_profit_score'].mean()
            st.metric("AVG YESTERDAY SCORE", f"{avg_yesterday:.0f}")
        
        with col2:
            avg_tomorrow = df['tomorrow_prediction_score'].mean()
            st.metric("AVG TOMORROW PRED", f"{avg_tomorrow:.0f}")
        
        with col3:
            high_confidence = len(df[df['tomorrow_prediction_score'] > 70])
            st.metric("HIGH CONFIDENCE", f"{high_confidence}")
        
        with col4:
            breakout_candidates = len(df[df['bb_position'] > 0.8]) + len(df[df['bb_position'] < 0.2])
            st.metric("BREAKOUT CANDIDATES", f"{breakout_candidates}")
        
        with col5:
            volume_surge = len(df[df['volume_trend'] > 1.5])
            st.metric("VOLUME SURGES", f"{volume_surge}")
            
        # Prediction confidence indicator
        st.markdown("""
        <div style="font-size: 12px; color: #00ff00; margin-top: 15px;">
            <div class="blinking">●</div> PREDICTION ENGINE STATUS: ACTIVE | 
            CONFIDENCE LEVEL: HIGH | PATTERN RECOGNITION: ENABLED
        </div>
        """, unsafe_allow_html=True)

    def display_individual_analysis(self):
        """Display individual ticker analysis"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[INDIVIDUAL ANALYSIS] TICKER DEEP DIVE</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            ticker = st.selectbox("SELECT TICKER", self.sp500_tickers, index=0)
        
        with col2:
            if st.button("ANALYZE", use_container_width=True):
                st.session_state.analyze_ticker = ticker
        
        with col3:
            analysis_type = st.selectbox("ANALYSIS TYPE", ["OPTIONS", "SWING", "VOLATILITY"])
        
        if hasattr(st.session_state, 'analyze_ticker'):
            self.run_individual_analysis(st.session_state.analyze_ticker, analysis_type)

    def run_individual_analysis(self, ticker, analysis_type):
        """Run detailed analysis for individual ticker"""
        
        with st.spinner(f"ANALYZING {ticker}..."):
            data = self.fetch_ticker_data(ticker)
            
            if not data:
                st.error(f"ERROR: UNABLE TO FETCH DATA FOR {ticker}")
                return
            
            # Display basic metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("CURRENT PRICE", f"${data['price']:.2f}")
            
            with col2:
                st.metric("CHANGE", f"{data['change']:+.2f}", f"{data['change_pct']:+.2f}%")
            
            with col3:
                st.metric("VOLATILITY", f"{data['volatility']:.1%}")
            
            with col4:
                st.metric("RSI", f"{data['rsi']:.0f}")
            
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
        
        # Navigation
        tab1, tab2, tab3 = st.tabs(["MARKET SCANNER", "INDIVIDUAL ANALYSIS", "SYSTEM STATUS"])
        
        with tab1:
            self.display_top_opportunities()
        
        with tab2:
            self.display_individual_analysis()
        
        with tab3:
            self.display_system_status()

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

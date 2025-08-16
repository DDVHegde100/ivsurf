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
        # Expanded ticker universe - NASDAQ focus for maximum opportunities
        self.nasdaq_tickers = [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE',
            # High-Growth Tech
            'AVGO', 'ORCL', 'CRM', 'INTC', 'AMD', 'QCOM', 'TXN', 'INTU', 'AMAT', 'MU',
            # Biotech & Healthcare
            'GILD', 'AMGN', 'VRTX', 'BIIB', 'REGN', 'MRNA', 'BNTX', 'ILMN', 'ALNY', 'SGEN',
            # Emerging Growth
            'ROKU', 'ZOOM', 'DOCU', 'OKTA', 'SNOW', 'PLTR', 'RBLX', 'U', 'DDOG', 'CRWD',
            # Consumer & Retail
            'COST', 'SBUX', 'LULU', 'NKLA', 'LCID', 'RIVN', 'ABNB', 'UBER', 'LYFT', 'DASH',
            # Semiconductors
            'ASML', 'LRCX', 'KLAC', 'MRVL', 'MCHP', 'ADI', 'NXPI', 'SWKS', 'QRVO', 'MPWR',
            # Cloud & Software
            'TEAM', 'WDAY', 'NOW', 'VEEV', 'SPLK', 'SHOP', 'SQ', 'PYPL', 'ZM', 'PTON',
            # Growth Stocks
            'TTD', 'TWLO', 'PINS', 'SNAP', 'HOOD', 'COIN', 'MELI', 'BABA', 'JD', 'PDD',
            # High-Volatility Opportunities
            'SPCE', 'WISH', 'CLOV', 'AMC', 'GME', 'BB', 'NOK', 'SNDL', 'TLRY', 'CGC',
            # Small-Mid Cap Growth
            'FVRR', 'UPWK', 'ETSY', 'CHWY', 'TDOC', 'PTON', 'BYND', 'ZI', 'FSLY', 'NET',
            # Recent IPOs & SPACs
            'RIVN', 'LCID', 'SOFI', 'OPEN', 'WISH', 'GOEV', 'NKLA', 'HYLN', 'QS', 'RIDE'
        ]
        
        # Additional high-volatility NASDAQ stocks for gain opportunities
        self.high_vol_nasdaq = [
            'SOXL', 'TQQQ', 'UPRO', 'SPXL', 'TECL', 'WEBL', 'FNGU', 'CURE', 'LABU', 'ARKK',
            'ARKG', 'ARKF', 'ARKW', 'ICLN', 'CLOU', 'BLOK', 'FINX', 'ROBO', 'MOON', 'UFO'
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
            
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = {executor.submit(self.fetch_ticker_data, ticker): ticker for ticker in available_tickers}
                
                for i, future in enumerate(futures):
                    progress = (i + 1) / len(futures)
                    progress_bar.progress(progress)
                    status_text.text(f"SCANNING NASDAQ: {futures[future]} ({i+1}/{len(futures)})")
                    
                    try:
                        result = future.result(timeout=5)
                        if result and result.get('tomorrow_gain_score', 0) > 0:
                            results.append(result)
                    except:
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
        """Display top trading opportunities - both historical and predictive"""
        
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[NASDAQ SCANNER] FRESH GAIN OPPORTUNITY DISCOVERY</div>
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
        
        # 2. Tomorrow's highest predicted gains (MAIN FOCUS)
        tomorrow_gains = df.nlargest(10, 'tomorrow_gain_score')[
            ['ticker', 'price', 'expected_gain_pct', 'probability_positive', 'confidence_level', 'conservative_target', 'tomorrow_gain_score']
        ]
        
        # 3. Yesterday's options opportunities
        yesterday_options = df.nlargest(10, 'options_score')[
            ['ticker', 'price', 'change_pct', 'volatility', 'options_score']
        ]
        
        # 4. Tomorrow's predicted options opportunities
        tomorrow_options = df.nlargest(10, 'options_prediction')[
            ['ticker', 'price', 'expected_gain_pct', 'moderate_target', 'aggressive_target', 'confidence_level', 'options_prediction']
        ]
        
        # Create tabs for different time horizons
        tab1, tab2, tab3, tab4 = st.tabs([
            "YESTERDAY'S WINNERS", 
            "TOMORROW'S BEST GAINS", 
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
                <div class="terminal-prompt">[NASDAQ DISCOVERY] TOP 10 FRESH STOCKS FOR HIGHEST GAINS</div>
                <div style="font-size: 12px; color: #ffff00;">🎯 NEW OPPORTUNITIES: Different stocks predicted for biggest % gains tomorrow</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Format tomorrow's gain predictions table
            tomorrow_gains_display = tomorrow_gains.copy()
            tomorrow_gains_display['CURRENT'] = tomorrow_gains_display['price'].apply(lambda x: f"${x:.2f}")
            tomorrow_gains_display['EXP_GAIN'] = tomorrow_gains_display['expected_gain_pct'].apply(lambda x: f"+{x:.2f}%")
            tomorrow_gains_display['TARGET'] = tomorrow_gains_display['conservative_target'].apply(lambda x: f"${x:.2f}")
            tomorrow_gains_display['WIN_PROB'] = tomorrow_gains_display['probability_positive'].apply(lambda x: f"{x:.0f}%")
            tomorrow_gains_display['CONFIDENCE'] = tomorrow_gains_display['confidence_level'].apply(lambda x: f"{x:.0f}%")
            tomorrow_gains_display['SCORE'] = tomorrow_gains_display['tomorrow_gain_score'].apply(lambda x: f"{x:.0f}")
            
            tomorrow_gains_display = tomorrow_gains_display[['ticker', 'CURRENT', 'EXP_GAIN', 'TARGET', 'WIN_PROB', 'CONFIDENCE', 'SCORE']]
            tomorrow_gains_display.columns = ['TICKER', 'CURRENT', 'EXP_GAIN', 'TARGET', 'WIN_PROB', 'CONFIDENCE', 'SCORE']
            
            st.dataframe(tomorrow_gains_display, use_container_width=True, hide_index=True)
            
            # Add prediction methodology
            st.markdown("""
            <div style="font-size: 11px; color: #888888; margin-top: 10px;">
                NASDAQ DISCOVERY: Scanning 100+ NASDAQ stocks for fresh opportunities, avoiding recent winners,
                focusing on breakout potential, oversold bounces, momentum acceleration, high-volatility plays
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
                <div class="terminal-prompt">[PREDICTIVE] TOP 10 OPTIONS PLAYS FOR MAXIMUM GAINS</div>
                <div style="font-size: 12px; color: #ffff00;">🎯 CALL OPTIONS: Stocks predicted for biggest moves tomorrow</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Format tomorrow's options table
            tomorrow_options_display = tomorrow_options.copy()
            tomorrow_options_display['CURRENT'] = tomorrow_options_display['price'].apply(lambda x: f"${x:.2f}")
            tomorrow_options_display['EXP_GAIN'] = tomorrow_options_display['expected_gain_pct'].apply(lambda x: f"+{x:.2f}%")
            tomorrow_options_display['MOD_TARGET'] = tomorrow_options_display['moderate_target'].apply(lambda x: f"${x:.2f}")
            tomorrow_options_display['AGG_TARGET'] = tomorrow_options_display['aggressive_target'].apply(lambda x: f"${x:.2f}")
            tomorrow_options_display['CONFIDENCE'] = tomorrow_options_display['confidence_level'].apply(lambda x: f"{x:.0f}%")
            tomorrow_options_display['SCORE'] = tomorrow_options_display['options_prediction'].apply(lambda x: f"{x:.0f}")
            
            tomorrow_options_display = tomorrow_options_display[['ticker', 'CURRENT', 'EXP_GAIN', 'MOD_TARGET', 'AGG_TARGET', 'CONFIDENCE', 'SCORE']]
            tomorrow_options_display.columns = ['TICKER', 'CURRENT', 'EXP_GAIN', 'MOD_TARGET', 'AGG_TARGET', 'CONFIDENCE', 'SCORE']
            
            st.dataframe(tomorrow_options_display, use_container_width=True, hide_index=True)
        
        # Enhanced market summary with gain predictions
        st.markdown("""
        <div class="terminal-box">
            <div class="terminal-prompt">[MARKET INTELLIGENCE] TOMORROW'S GAIN OPPORTUNITY SUMMARY</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_yesterday = df['yesterday_profit_score'].mean()
            st.metric("AVG YESTERDAY SCORE", f"{avg_yesterday:.0f}")
        
        with col2:
            avg_gain_score = df['tomorrow_gain_score'].mean()
            st.metric("AVG GAIN SCORE", f"{avg_gain_score:.0f}")
        
        with col3:
            high_gain_stocks = len(df[df['tomorrow_gain_score'] > 70])
            st.metric("HIGH GAIN POTENTIAL", f"{high_gain_stocks}")
        
        with col4:
            avg_expected_gain = df['expected_gain_pct'].mean()
            st.metric("AVG EXP GAIN", f"+{avg_expected_gain:.2f}%")
        
        with col5:
            high_confidence = len(df[df['confidence_level'] > 80])
            st.metric("HIGH CONFIDENCE", f"{high_confidence}")
            
        # Gain prediction indicator
        st.markdown("""
        <div style="font-size: 12px; color: #00ff00; margin-top: 15px;">
            <div class="blinking">●</div> GAIN PREDICTION ENGINE: ACTIVE | 
            FOCUS: TOMORROW'S HIGHEST % GAINERS | MODE: BUY TODAY, SELL TOMORROW
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
            ticker = st.selectbox("SELECT TICKER", self.all_tickers[:50], index=0)  # Show first 50 for performance
        
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

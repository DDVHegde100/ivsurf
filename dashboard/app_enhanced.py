#!/usr/bin/env python3
"""
Professional Volatility Surface Explorer

Advanced options analytics platform with modern UI, comprehensive education,
and professional-grade analysis tools.

Run: streamlit run dashboard/app_enhanced.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.black_scholes import black_scholes_price, implied_volatility, option_value_decomposition
from core.greeks import all_greeks
from utils.fetch_data import OptionsDataFetcher
# from visuals.plot_surface import create_volatility_surface, plot_greeks_surface
# from visuals.heatmaps import create_iv_heatmap


def apply_professional_styling():
    """Apply advanced glassmorphism styling with educational elements."""
    st.markdown("""
    <style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Main Application Background */
    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 25%, #667eea 50%, #764ba2 75%, #f093fb 100%);
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
    }
    
    /* Enhanced Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 28px;
        margin: 18px 0;
        box-shadow: 
            0 8px 32px 0 rgba(31, 38, 135, 0.4),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 
            0 16px 48px 0 rgba(31, 38, 135, 0.5),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.25);
    }
    
    /* Professional Title Styling */
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 4rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4ecdc4 75%, #44a08d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 1.4rem;
        color: rgba(255, 255, 255, 0.85);
        text-align: center;
        margin-bottom: 3rem;
        letter-spacing: 0.01em;
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(30px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .sidebar-section {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        margin: 15px 0;
    }
    
    /* Educational Information Icons */
    .info-tooltip {
        position: relative;
        display: inline-block;
        margin-left: 8px;
    }
    
    .info-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        background: linear-gradient(135deg, #4ecdc4, #44a08d);
        border-radius: 50%;
        color: white;
        font-size: 13px;
        font-weight: 600;
        cursor: help;
        box-shadow: 0 2px 8px rgba(68, 160, 141, 0.3);
        transition: all 0.2s ease;
    }
    
    .info-icon:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 12px rgba(68, 160, 141, 0.4);
    }
    
    /* Educational Panels */
    .education-panel {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(15px);
        border-radius: 18px;
        border-left: 4px solid #4ecdc4;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 4px 16px rgba(31, 38, 135, 0.2);
    }
    
    .tip-panel {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.08), rgba(139, 195, 74, 0.08));
        border-radius: 14px;
        border: 1px solid rgba(76, 175, 80, 0.25);
        padding: 18px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
    }
    
    .warning-panel {
        background: linear-gradient(135deg, rgba(255, 152, 0, 0.08), rgba(255, 193, 7, 0.08));
        border-radius: 14px;
        border: 1px solid rgba(255, 152, 0, 0.25);
        padding: 18px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
    }
    
    .danger-panel {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.08), rgba(233, 30, 99, 0.08));
        border-radius: 14px;
        border: 1px solid rgba(244, 67, 54, 0.25);
        padding: 18px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
    }
    
    /* Enhanced Metrics */
    .metric-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        margin: 12px 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #4ecdc4, #44a08d);
    }
    
    .metric-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(31, 38, 135, 0.3);
    }
    
    /* Enhanced Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 18px;
        padding: 8px;
        backdrop-filter: blur(20px);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        color: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 500;
        padding: 12px 20px;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.12);
        color: rgba(255, 255, 255, 0.9);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4ecdc4, #44a08d);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 16px rgba(68, 160, 141, 0.3);
    }
    
    /* Enhanced Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #4ecdc4, #44a08d);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.25);
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(76, 175, 80, 0.35);
        background: linear-gradient(135deg, #5dd3d0, #4fb3b0);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Enhanced Form Elements */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        color: white;
        backdrop-filter: blur(10px);
    }
    
    /* Code Blocks */
    .stCode {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Enhanced Plotly Charts */
    .js-plotly-plot {
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.25);
        backdrop-filter: blur(10px);
    }
    
    /* Progress Bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4ecdc4, #44a08d);
        border-radius: 10px;
    }
    
    /* Success/Error/Warning Messages */
    .stAlert {
        border-radius: 14px;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #4ecdc4, #44a08d);
        border-radius: 12px;
        border: 2px solid transparent;
        background-clip: content-box;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5dd3d0, #4fb3b0);
        background-clip: content-box;
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-top-color: #4ecdc4 !important;
    }
    
    /* DataFrames */
    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(31, 38, 135, 0.2);
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .hero-subtitle {
            font-size: 1.1rem;
        }
        
        .glass-card {
            padding: 20px;
            margin: 12px 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def create_info_tooltip(text, explanation, icon="ℹ️"):
    """Create enhanced information tooltip with glassmorphism styling."""
    return f"""
    <div style="display: inline-flex; align-items: center;">
        <span style="margin-right: 6px;">{text}</span>
        <div class="info-tooltip">
            <span class="info-icon" title="{explanation}">{icon}</span>
        </div>
    </div>
    """


def create_educational_section(title, content, icon="📚", panel_type="education"):
    """Create beautiful educational sections with different styling types."""
    panel_class = f"{panel_type}-panel"
    
    st.markdown(f"""
    <div class="{panel_class}">
        <h3 style="color: #4ecdc4; margin-bottom: 16px; font-weight: 600;">
            {icon} {title}
        </h3>
        <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.7; font-size: 15px;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_metric_card(title, value, subtitle="", tooltip="", trend=None):
    """Create enhanced metric cards with professional styling."""
    trend_color = ""
    trend_icon = ""
    
    if trend:
        if trend > 0:
            trend_color = "color: #4caf50;"
            trend_icon = "↗️"
        elif trend < 0:
            trend_color = "color: #f44336;"
            trend_icon = "↘️"
        else:
            trend_color = "color: #ff9800;"
            trend_icon = "→"
    
    tooltip_html = ""
    if tooltip:
        tooltip_html = f'<div class="info-tooltip"><span class="info-icon" title="{tooltip}">i</span></div>'
    
    st.markdown(f"""
    <div class="metric-container">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <h4 style="color: rgba(255,255,255,0.7); margin: 0; font-size: 14px; font-weight: 500;">
                    {title}
                </h4>
                <h2 style="color: white; margin: 8px 0 4px 0; font-size: 28px; font-weight: 700;">
                    {value}
                </h2>
                {f'<p style="margin: 0; font-size: 13px; {trend_color}"><strong>{trend_icon} {subtitle}</strong></p>' if subtitle else ''}
            </div>
            {tooltip_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_comprehensive_guide():
    """Show comprehensive options trading and volatility guide."""
    st.markdown("""
    <div class="glass-card">
        <h1 style="color: #4ecdc4; text-align: center; margin-bottom: 30px; font-size: 2.5rem;">
            🎓 Complete Volatility Surface Guide
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Volatility Surface Fundamentals
    create_educational_section(
        "What is a Volatility Surface?",
        """
        A <strong>volatility surface</strong> is a 3D visualization showing how <em>implied volatility</em> 
        changes across different <strong>strike prices</strong> and <strong>expiration dates</strong>.
        <br><br>
        <strong>🎯 Why It Matters:</strong><br>
        • Reveals market sentiment and fear levels<br>
        • Shows arbitrage opportunities<br>
        • Helps price complex derivatives<br>
        • Indicates market microstructure effects<br>
        <br>
        <strong>📊 What You'll See:</strong><br>
        • <em>Volatility Smile:</em> Higher IV for far out-of-the-money options<br>
        • <em>Term Structure:</em> How volatility changes over time<br>
        • <em>Skew Effects:</em> Put options often have higher IV than calls
        """,
        "🌊"
    )
    
    # Advanced Options Concepts
    create_educational_section(
        "Professional Options Trading Concepts",
        """
        <strong>🔥 Implied vs Historical Volatility:</strong><br>
        • <em>Historical:</em> How much the stock actually moved in the past<br>
        • <em>Implied:</em> How much the market thinks it will move<br>
        • <em>Trading Edge:</em> When these don't match, there may be opportunities<br>
        <br>
        <strong>⚡ Volatility Trading Strategies:</strong><br>
        • <em>Long Volatility:</em> Buy options when IV is low (straddles, strangles)<br>
        • <em>Short Volatility:</em> Sell options when IV is high (covered calls, spreads)<br>
        • <em>Volatility Arbitrage:</em> Exploit differences in implied vs realized volatility<br>
        <br>
        <strong>🎯 Professional Metrics:</strong><br>
        • <em>Vega Exposure:</em> How much you make/lose per 1% volatility change<br>
        • <em>Gamma Trading:</em> Delta hedging to capture realized volatility<br>
        • <em>Theta Decay:</em> Time value erosion working for or against you
        """,
        "⚡"
    )
    
    # Risk Management
    create_educational_section(
        "Advanced Risk Management",
        """
        <strong>🛡️ Portfolio Greeks Management:</strong><br>
        • <em>Delta Neutral:</em> Hedge stock price risk<br>
        • <em>Gamma Scalping:</em> Profit from volatility while staying delta neutral<br>
        • <em>Vega Hedging:</em> Manage volatility risk across the portfolio<br>
        • <em>Theta Management:</em> Balance time decay across positions<br>
        <br>
        <strong>⚠️ Common Mistakes to Avoid:</strong><br>
        • Ignoring bid-ask spreads on illiquid options<br>
        • Not understanding pin risk at expiration<br>
        • Over-leveraging with options<br>
        • Forgetting about early exercise risk on American options<br>
        • Not accounting for dividend effects on option pricing
        """,
        "🛡️",
        "warning"
    )
    
    # Market Microstructure
    create_educational_section(
        "Market Microstructure & Liquidity",
        """
        <strong>💧 Liquidity Indicators:</strong><br>
        • <em>Open Interest:</em> Total contracts outstanding (more = more liquid)<br>
        • <em>Volume:</em> Daily trading activity<br>
        • <em>Bid-Ask Spread:</em> Tighter spreads = better liquidity<br>
        • <em>Market Makers:</em> Provide liquidity but charge for it via spreads<br>
        <br>
        <strong>🕐 Market Timing Effects:</strong><br>
        • <em>Market Open/Close:</em> Higher volatility, wider spreads<br>
        • <em>Earnings Announcements:</em> IV crush after results<br>
        • <em>FOMC Days:</em> Elevated volatility in financial options<br>
        • <em>Expiration Friday:</em> Pin risk and unusual flows
        """,
        "🏛️"
    )
    
    # Professional Platforms
    create_educational_section(
        "Professional Trading Platforms",
        """
        <strong>🏆 Institutional-Grade Platforms:</strong><br>
        • <strong>Bloomberg Terminal:</strong> Industry standard, comprehensive data<br>
        • <strong>Refinitiv Eikon:</strong> Professional analytics and news<br>
        • <strong>ThinkorSwim:</strong> Advanced retail platform with institutional features<br>
        • <strong>Interactive Brokers:</strong> Low costs, advanced order types<br>
        <br>
        <strong>📊 Specialized Options Platforms:</strong><br>
        • <strong>OptionVue:</strong> Professional volatility analysis<br>
        • <strong>ORATS:</strong> Options research and technology<br>
        • <strong>LiveVol:</strong> Real-time volatility data and analytics<br>
        • <strong>TradeStation:</strong> Advanced backtesting and automation<br>
        <br>
        <strong>⚠️ Retail vs Professional:</strong><br>
        Most retail platforms show delayed data and simplified Greeks. 
        Professional trading requires real-time data feeds and advanced analytics.
        """,
        "💻"
    )


def main():
    st.set_page_config(
        page_title="Volatility Surface Explorer",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply professional styling
    apply_professional_styling()
    
    # Hero section with enhanced styling
    st.markdown("""
    <div class="hero-title">🌊 Volatility Surface Explorer</div>
    <div class="hero-subtitle">Professional Options Analytics & Risk Management Platform</div>
    """, unsafe_allow_html=True)
    
    # Professional guide toggle
    if st.button("🎓 Show Professional Trading Guide", help="Comprehensive guide to volatility surfaces and professional options trading"):
        st.session_state['show_professional_guide'] = not st.session_state.get('show_professional_guide', False)
    
    if st.session_state.get('show_professional_guide', False):
        show_comprehensive_guide()
        st.markdown("---")
    
    # Enhanced sidebar with educational content
    with st.sidebar:
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center; margin-bottom: 20px;">
                🎛️ Control Panel
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Market Data Section
        st.markdown("""
        <div class="sidebar-section">
            <h3 style="color: #4ecdc4; margin-bottom: 15px;">📊 Market Data</h3>
        </div>
        """, unsafe_allow_html=True)
        
        ticker = st.text_input(
            "Stock Symbol", 
            value="AAPL",
            help="Enter a ticker symbol (e.g., AAPL, MSFT, TSLA, SPY). Choose liquid stocks for better options data."
        ).upper()
        
        create_educational_section(
            "Choosing Good Options Stocks",
            """
            <strong>✅ Best for Options:</strong><br>
            • <em>High Volume:</em> SPY, QQQ, AAPL, TSLA<br>
            • <em>Tech Leaders:</em> MSFT, GOOGL, NVDA<br>
            • <em>Financial ETFs:</em> XLF, IWM<br>
            <br>
            <strong>❌ Avoid:</strong><br>
            • Low-volume penny stocks<br>
            • Newly listed companies<br>
            • Stocks without weekly options
            """,
            "📈",
            "tip"
        )
        
        # Black-Scholes Testing Section
        st.markdown("""
        <div class="sidebar-section">
            <h3 style="color: #4ecdc4; margin-bottom: 15px;">🧮 Theoretical Pricing</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            test_spot = st.number_input(
                "Stock Price ($)", 
                value=150.0, 
                min_value=1.0, 
                step=1.0,
                help="Current stock price for theoretical calculations"
            )
            test_strike = st.number_input(
                "Strike Price ($)", 
                value=150.0, 
                min_value=1.0, 
                step=1.0,
                help="Option strike price"
            )
        
        with col2:
            test_time = st.number_input(
                "Time (Years)", 
                value=0.25, 
                min_value=0.01, 
                max_value=2.0, 
                step=0.01,
                help="Time to expiration in years (0.25 = 3 months)"
            )
            test_vol = st.number_input(
                "Volatility", 
                value=0.25, 
                min_value=0.01, 
                max_value=2.0, 
                step=0.01,
                help="Annual volatility (0.25 = 25%)"
            )
        
        test_rate = st.number_input(
            "Risk-free Rate", 
            value=0.05, 
            min_value=-0.05, 
            max_value=0.20, 
            step=0.001,
            help="Risk-free interest rate (typically 10-year Treasury rate)"
        )
        
        test_option_type = st.selectbox(
            "Option Type", 
            ["call", "put"],
            help="Call = right to buy, Put = right to sell"
        )
        
        # Advanced Parameters
        with st.expander("🔬 Advanced Parameters", expanded=False):
            st.markdown("""
            <div class="tip-panel">
                <strong>💡 Pro Tip:</strong> These parameters significantly affect option pricing. 
                Small changes in volatility can have large impacts on option values.
            </div>
            """, unsafe_allow_html=True)
            
            vol_of_vol = st.slider(
                "Volatility of Volatility", 
                0.1, 2.0, 0.3, 0.05,
                help="For Heston model - how much volatility itself varies"
            )
            
            mean_reversion = st.slider(
                "Mean Reversion Speed", 
                0.1, 5.0, 1.0, 0.1,
                help="How quickly volatility returns to long-term average"
            )
    
    # Enhanced main content with professional tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧮 Black-Scholes Lab", 
        "📊 Options Chain", 
        "🌊 Volatility Surface", 
        "🏛️ Heston Model",
        "🎯 Portfolio Analytics"
    ])
    
    with tab1:
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center;">🧮 Black-Scholes Pricing Laboratory</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Educational content about Black-Scholes
        create_educational_section(
            "The Black-Scholes Model Explained",
            """
            The <strong>Black-Scholes model</strong> is the foundation of modern options pricing. 
            It assumes that stock prices follow a geometric Brownian motion with constant volatility and interest rates.
            <br><br>
            <strong>📊 Key Assumptions:</strong><br>
            • Constant volatility and interest rates<br>
            • No dividends during option life<br>
            • European exercise (can only exercise at expiration)<br>
            • No transaction costs<br>
            • Continuous trading<br>
            <br>
            <strong>🎯 When It Works Best:</strong><br>
            Short-term options on liquid stocks without dividends or major events.
            """,
            "📚"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="glass-card">
                <h3 style="color: #4ecdc4;">Option Valuation</h3>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Calculate theoretical option price
                theoretical_price = black_scholes_price(
                    test_spot, test_strike, test_time, test_rate, test_vol, test_option_type
                )
                
                # Value decomposition
                decomp = option_value_decomposition(
                    test_spot, test_strike, test_time, test_rate, test_vol, test_option_type
                )
                
                create_metric_card(
                    "Theoretical Price", 
                    f"${theoretical_price:.3f}",
                    tooltip="Fair value according to Black-Scholes model"
                )
                
                create_metric_card(
                    "Intrinsic Value", 
                    f"${decomp['intrinsic_value']:.3f}",
                    tooltip="Value if exercised immediately"
                )
                
                create_metric_card(
                    "Time Value", 
                    f"${decomp['time_value']:.3f}",
                    tooltip="Premium paid for time until expiration"
                )
                
                # Moneyness assessment
                moneyness = (test_spot - test_strike) / test_spot * 100
                if test_option_type == 'call':
                    if moneyness > 5:
                        money_status = "🟢 Deep ITM"
                    elif moneyness > 0:
                        money_status = "🟡 ITM"
                    elif moneyness > -5:
                        money_status = "🔵 ATM"
                    else:
                        money_status = "🔴 OTM"
                else:  # put
                    if moneyness < -5:
                        money_status = "🟢 Deep ITM"
                    elif moneyness < 0:
                        money_status = "🟡 ITM"
                    elif moneyness < 5:
                        money_status = "🔵 ATM"
                    else:
                        money_status = "🔴 OTM"
                
                st.markdown(f"""
                <div class="tip-panel">
                    <strong>Moneyness:</strong> {money_status}<br>
                    <strong>Stock vs Strike:</strong> {moneyness:+.1f}%
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Calculation error: {str(e)}")
        
        with col2:
            st.markdown("""
            <div class="glass-card">
                <h3 style="color: #4ecdc4;">The Greeks Dashboard</h3>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Calculate all Greeks
                greeks = all_greeks(test_spot, test_strike, test_time, test_rate, test_vol, test_option_type)
                
                create_metric_card(
                    "Delta (Δ)", 
                    f"{greeks['delta']:.4f}",
                    tooltip="Price change per $1 stock move"
                )
                
                create_metric_card(
                    "Gamma (Γ)", 
                    f"{greeks['gamma']:.6f}",
                    tooltip="Delta change per $1 stock move"
                )
                
                create_metric_card(
                    "Vega (ν)", 
                    f"{greeks['vega']:.4f}",
                    tooltip="Price change per 1% volatility increase"
                )
                
                create_metric_card(
                    "Theta (Θ)", 
                    f"{greeks['theta']:.4f}",
                    tooltip="Daily time decay"
                )
                
                create_metric_card(
                    "Rho (ρ)", 
                    f"{greeks['rho']:.4f}",
                    tooltip="Price change per 1% interest rate increase"
                )
                
                # Greeks interpretation
                if abs(greeks['delta']) > 0.7:
                    delta_meaning = "High sensitivity to stock price"
                elif abs(greeks['delta']) > 0.3:
                    delta_meaning = "Moderate stock price sensitivity"
                else:
                    delta_meaning = "Low stock price sensitivity"
                
                st.markdown(f"""
                <div class="tip-panel">
                    <strong>Delta Interpretation:</strong><br>
                    {delta_meaning}
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Greeks calculation error: {str(e)}")
        
        with col3:
            st.markdown("""
            <div class="glass-card">
                <h3 style="color: #4ecdc4;">Sensitivity Analysis</h3>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Create enhanced sensitivity analysis
                spot_range = np.linspace(test_spot * 0.8, test_spot * 1.2, 50)
                vol_range = np.linspace(test_vol * 0.5, test_vol * 1.5, 30)
                
                # Price sensitivity to stock movement
                prices_vs_spot = []
                for spot in spot_range:
                    price = black_scholes_price(spot, test_strike, test_time, test_rate, test_vol, test_option_type)
                    prices_vs_spot.append(price)
                
                # Price sensitivity to volatility
                prices_vs_vol = []
                for vol in vol_range:
                    price = black_scholes_price(test_spot, test_strike, test_time, test_rate, vol, test_option_type)
                    prices_vs_vol.append(price)
                
                # Create enhanced visualization
                fig = go.Figure()
                
                # Stock price sensitivity
                fig.add_trace(go.Scatter(
                    x=spot_range,
                    y=prices_vs_spot,
                    mode='lines',
                    name='Price vs Stock',
                    line=dict(color='#4ecdc4', width=3),
                    hovertemplate='Stock: $%{x:.2f}<br>Option: $%{y:.3f}<extra></extra>'
                ))
                
                # Current position marker
                fig.add_trace(go.Scatter(
                    x=[test_spot],
                    y=[theoretical_price],
                    mode='markers',
                    name='Current Position',
                    marker=dict(color='red', size=12, symbol='diamond'),
                    hovertemplate=f'Current: ${test_spot:.2f}<br>Price: ${theoretical_price:.3f}<extra></extra>'
                ))
                
                # Add profit zones
                if test_option_type == 'call':
                    breakeven = test_strike + theoretical_price
                    fig.add_vline(x=breakeven, line_dash="dash", line_color="yellow", 
                                 annotation_text=f"Breakeven: ${breakeven:.2f}")
                else:
                    breakeven = test_strike - theoretical_price
                    fig.add_vline(x=breakeven, line_dash="dash", line_color="yellow", 
                                 annotation_text=f"Breakeven: ${breakeven:.2f}")
                
                fig.update_layout(
                    title="Option Price Sensitivity",
                    xaxis_title="Stock Price ($)",
                    yaxis_title="Option Price ($)",
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    showlegend=True,
                    legend=dict(bgcolor='rgba(255,255,255,0.1)')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Profit/Loss analysis
                max_profit = "Unlimited" if test_option_type == 'call' else f"${test_strike - theoretical_price:.2f}"
                max_loss = f"${theoretical_price:.2f}"
                
                st.markdown(f"""
                <div class="warning-panel">
                    <strong>📊 P&L Analysis:</strong><br>
                    <strong>Max Profit:</strong> {max_profit}<br>
                    <strong>Max Loss:</strong> {max_loss}<br>
                    <strong>Breakeven:</strong> ${breakeven:.2f}
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Sensitivity analysis error: {str(e)}")
    
    # Continue with other enhanced tabs...
    with tab2:
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center;">📊 Live Options Chain Analysis</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🚧 Enhanced options chain analysis coming soon with real-time data integration...")
    
    with tab3:
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center;">🌊 3D Volatility Surface</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🚧 Advanced 3D volatility surface visualization coming soon...")
    
    with tab4:
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center;">🏛️ Heston Stochastic Volatility Model</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🚧 Heston model implementation and calibration coming soon...")
    
    with tab5:
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center;">🎯 Portfolio Risk Analytics</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🚧 Portfolio-level Greeks and risk management tools coming soon...")


if __name__ == "__main__":
    main()

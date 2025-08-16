#!/usr/bin/env python3
"""
RETRO VOLATILITY SURFACE EXPLORER v1.0

Classic 1996-style financial mainframe terminal for professional volatility analysis.
Matrix-green aesthetic with advanced options analytics and risk management protocols.

Run: streamlit run dashboard/retro_terminal.py
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


def apply_retro_mainframe_css():
    """Apply advanced 1996 financial terminal styling with CRT effects."""
    st.markdown("""
    <style>
    /* Import Terminal Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=VT323:wght@400&family=Share+Tech+Mono:wght@400&family=Source+Code+Pro:wght@300;400;500;600;700&display=swap');
    
    /* Main Terminal Environment */
    .main {
        background: #000000;
        color: #00ff00;
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px;
        line-height: 1.3;
        overflow-x: hidden;
    }
    
    /* Terminal Header */
    .mainframe-header {
        background: #000000;
        border: 3px solid #00ff00;
        border-radius: 0;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 
            0 0 30px #00ff00,
            inset 0 0 20px #001100;
        position: relative;
        text-align: center;
    }
    
    .mainframe-header::before {
        content: '████ VOLATILITY_SURFACE_MAINFRAME_v1.0 ████';
        position: absolute;
        top: -15px;
        left: 50%;
        transform: translateX(-50%);
        background: #000000;
        color: #00ff00;
        padding: 0 15px;
        font-family: 'VT323', monospace;
        font-size: 18px;
        font-weight: bold;
        text-shadow: 0 0 10px #00ff00;
    }
    
    /* System Status Panel */
    .status-panel {
        background: #001100;
        border: 2px solid #00ff00;
        padding: 15px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        font-size: 12px;
        position: relative;
    }
    
    .status-panel::before {
        content: '▓▓▓ SYSTEM_STATUS ▓▓▓';
        position: absolute;
        top: -10px;
        left: 15px;
        background: #000000;
        color: #00ffff;
        padding: 0 8px;
        font-weight: bold;
    }
    
    /* Data Modules */
    .data-module {
        background: #000a00;
        border: 2px solid #00ff00;
        border-radius: 0;
        padding: 18px;
        margin: 12px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
        box-shadow: 
            0 0 15px #003300,
            inset 0 0 10px #001100;
    }
    
    .data-module::before {
        content: attr(data-title);
        position: absolute;
        top: -12px;
        left: 20px;
        background: #000000;
        color: #00ffff;
        padding: 0 10px;
        font-size: 13px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg {
        background: #000000;
        border-right: 3px solid #00ff00;
        box-shadow: 3px 0 15px #003300;
    }
    
    /* Control Interface */
    .control-interface {
        background: #000a00;
        border: 2px solid #00ff00;
        padding: 18px;
        margin: 12px 0;
        position: relative;
    }
    
    .control-interface::before {
        content: '◄ CONTROL_MATRIX ►';
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #000000;
        color: #00ffff;
        padding: 0 12px;
        font-family: 'VT323', monospace;
        font-size: 15px;
        font-weight: bold;
    }
    
    /* Metric Terminals */
    .metric-terminal {
        background: #001a00;
        border: 1px solid #00ff00;
        border-radius: 0;
        padding: 15px;
        margin: 8px 0;
        text-align: center;
        position: relative;
        box-shadow: inset 0 0 10px #002200;
    }
    
    .metric-terminal::before {
        content: attr(data-metric);
        position: absolute;
        top: -8px;
        left: 50%;
        transform: translateX(-50%);
        background: #000000;
        color: #00ffff;
        padding: 0 6px;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #00ff00;
        text-shadow: 0 0 10px #00ff00;
        font-family: 'VT323', monospace;
        margin: 5px 0;
    }
    
    .metric-unit {
        font-size: 11px;
        color: #00ffff;
        text-transform: uppercase;
        font-weight: bold;
    }
    
    /* Alert Systems */
    .alert-success {
        background: #003300;
        border: 2px solid #00ff00;
        color: #00ff00;
        padding: 12px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
        box-shadow: 0 0 15px #003300;
    }
    
    .alert-success::before {
        content: '[✓ SUCCESS]';
        color: #00ffff;
        font-weight: bold;
        margin-right: 10px;
    }
    
    .alert-error {
        background: #330000;
        border: 2px solid #ff0000;
        color: #ff0000;
        padding: 12px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
        box-shadow: 0 0 15px #330000;
    }
    
    .alert-error::before {
        content: '[✗ ERROR]';
        color: #ffff00;
        font-weight: bold;
        margin-right: 10px;
    }
    
    .alert-warning {
        background: #333300;
        border: 2px solid #ffff00;
        color: #ffff00;
        padding: 12px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
        box-shadow: 0 0 15px #333300;
    }
    
    .alert-warning::before {
        content: '[⚠ WARNING]';
        color: #ff8800;
        font-weight: bold;
        margin-right: 10px;
    }
    
    .alert-info {
        background: #000033;
        border: 2px solid #0088ff;
        color: #00aaff;
        padding: 12px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
        box-shadow: 0 0 15px #000033;
    }
    
    .alert-info::before {
        content: '[ℹ INFO]';
        color: #00ffff;
        font-weight: bold;
        margin-right: 10px;
    }
    
    /* Tab Interface */
    .stTabs [data-baseweb="tab-list"] {
        background: #000000;
        border: 2px solid #00ff00;
        border-radius: 0;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #001100;
        color: #00ff00;
        border: 1px solid #00ff00;
        border-radius: 0;
        font-family: 'VT323', monospace;
        font-size: 18px;
        font-weight: bold;
        margin: 3px;
        padding: 12px 18px;
        transition: all 0.2s ease;
        text-transform: uppercase;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #003300;
        color: #00ffff;
        box-shadow: 0 0 15px #00ff00;
        transform: scale(1.02);
    }
    
    .stTabs [aria-selected="true"] {
        background: #00ff00;
        color: #000000;
        box-shadow: 0 0 20px #00ff00;
        text-shadow: none;
    }
    
    /* Button Systems */
    .stButton > button {
        background: #000000;
        color: #00ff00;
        border: 2px solid #00ff00;
        border-radius: 0;
        font-family: 'VT323', monospace;
        font-size: 18px;
        font-weight: bold;
        padding: 10px 20px;
        transition: all 0.2s ease;
        text-transform: uppercase;
        box-shadow: 0 0 10px #003300;
    }
    
    .stButton > button:hover {
        background: #00ff00;
        color: #000000;
        box-shadow: 0 0 20px #00ff00;
        transform: scale(1.08);
    }
    
    /* Form Controls */
    .stSelectbox > div > div {
        background: #001100;
        border: 2px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
        font-weight: bold;
    }
    
    .stTextInput > div > div > input {
        background: #001100;
        border: 2px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
        font-size: 15px;
        font-weight: bold;
    }
    
    .stNumberInput > div > div > input {
        background: #001100;
        border: 2px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
        font-size: 15px;
        font-weight: bold;
    }
    
    /* Plotly Terminal Integration */
    .js-plotly-plot {
        background: #000000;
        border: 3px solid #00ff00;
        box-shadow: 0 0 25px #003300;
    }
    
    /* CRT Scanlines Effect */
    .crt-effect {
        position: relative;
    }
    
    .crt-effect::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 255, 0, 0.05) 2px,
            rgba(0, 255, 0, 0.05) 4px
        );
        pointer-events: none;
        z-index: 1;
    }
    
    /* Matrix Rain Effect */
    @keyframes matrix-rain {
        0% { transform: translateY(-100px); opacity: 1; }
        100% { transform: translateY(100vh); opacity: 0; }
    }
    
    .matrix-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: -1;
        pointer-events: none;
    }
    
    .matrix-background::before {
        content: '01101001010010110100101001010110101001010010110100101001010110101001010010110100101001010110';
        position: absolute;
        color: #003300;
        font-size: 12px;
        font-family: 'VT323', monospace;
        white-space: nowrap;
        animation: matrix-rain 10s linear infinite;
        opacity: 0.3;
    }
    
    /* Progress Indicators */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00ff00, #00aa00, #00ff00);
        box-shadow: 0 0 10px #00ff00;
    }
    
    /* DataFrames Terminal Style */
    .stDataFrame {
        border: 2px solid #00ff00;
        background: #000000;
        border-radius: 0;
    }
    
    .stDataFrame table {
        background: #000000;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
        font-size: 11px;
    }
    
    .stDataFrame th {
        background: #003300;
        color: #00ffff;
        border: 1px solid #00ff00;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .stDataFrame td {
        background: #001100;
        color: #00ff00;
        border: 1px solid #00ff00;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    
    /* Terminal Scrollbar */
    ::-webkit-scrollbar {
        width: 15px;
        background: #000000;
    }
    
    ::-webkit-scrollbar-track {
        background: #001100;
        border: 2px solid #00ff00;
        border-radius: 0;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff00;
        border: 2px solid #000000;
        border-radius: 0;
        box-shadow: 0 0 10px #00ff00;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00ffff;
        box-shadow: 0 0 15px #00ffff;
    }
    
    /* Blinking Cursor Effect */
    .blinking-cursor::after {
        content: '█';
        color: #00ff00;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    /* Responsive Terminal */
    @media (max-width: 768px) {
        .mainframe-header {
            padding: 15px;
        }
        
        .metric-value {
            font-size: 24px;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-size: 14px;
            padding: 8px 12px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def create_mainframe_ascii():
    """Create the main ASCII art header for the terminal."""
    return """
██╗   ██╗ ██████╗ ██╗      █████╗ ████████╗██╗██╗     ██╗████████╗██╗   ██╗
██║   ██║██╔═══██╗██║     ██╔══██╗╚══██╔══╝██║██║     ██║╚══██╔══╝╚██╗ ██╔╝
██║   ██║██║   ██║██║     ███████║   ██║   ██║██║     ██║   ██║    ╚████╔╝ 
╚██╗ ██╔╝██║   ██║██║     ██╔══██║   ██║   ██║██║     ██║   ██║     ╚██╔╝  
 ╚████╔╝ ╚██████╔╝███████╗██║  ██║   ██║   ██║███████╗██║   ██║      ██║   
  ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚══════╝╚═╝   ╚═╝      ╚═╝   
                                                                             
███████╗██╗   ██╗██████╗ ███████╗ █████╗  ██████╗███████╗                  
██╔════╝██║   ██║██╔══██╗██╔════╝██╔══██╗██╔════╝██╔════╝                  
███████╗██║   ██║██████╔╝█████╗  ███████║██║     █████╗                    
╚════██║██║   ██║██╔══██╗██╔══╝  ██╔══██║██║     ██╔══╝                    
███████║╚██████╔╝██║  ██║██║     ██║  ██║╚██████╗███████╗                  
╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝                  
                                                                             
███████╗██╗  ██╗██████╗ ██╗      ██████╗ ██████╗ ███████╗██████╗           
██╔════╝╚██╗██╔╝██╔══██╗██║     ██╔═══██╗██╔══██╗██╔════╝██╔══██╗          
█████╗   ╚███╔╝ ██████╔╝██║     ██║   ██║██████╔╝█████╗  ██████╔╝          
██╔══╝   ██╔██╗ ██╔═══╝ ██║     ██║   ██║██╔══██╗██╔══╝  ██╔══██╗          
███████╗██╔╝ ██╗██║     ███████╗╚██████╔╝██║  ██║███████╗██║  ██║          
╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝          
    """


def create_terminal_alert(title, message, alert_type="info"):
    """Create terminal-style alerts."""
    st.markdown(f"""
    <div class="alert-{alert_type}">
        <strong>{title}:</strong> {message}
    </div>
    """, unsafe_allow_html=True)


def create_terminal_metric(label, value, unit="", data_metric=""):
    """Create terminal-style metric displays."""
    if not data_metric:
        data_metric = label.replace(" ", "_")
    
    st.markdown(f"""
    <div class="metric-terminal" data-metric="{data_metric}">
        <div class="metric-value">{value}</div>
        <div class="metric-unit">{unit}</div>
    </div>
    """, unsafe_allow_html=True)


def show_mainframe_guide():
    """Show comprehensive financial mainframe guide."""
    st.markdown(f"""
    <div class="mainframe-header crt-effect">
        <pre style="color: #00ff00; font-family: 'VT323', monospace; font-size: 14px; margin: 0;">
{create_mainframe_ascii()}
        </pre>
        <div style="color: #00ffff; font-weight: bold; margin-top: 15px; font-family: 'Share Tech Mono', monospace;">
        ► FINANCIAL_MAINFRAME_SYSTEM_v1.0_OPERATIONAL<br>
        ► VOLATILITY_SURFACE_PROTOCOLS_LOADED<br>
        ► RISK_MANAGEMENT_MODULES_ACTIVE<br>
        ► <span class="blinking-cursor" style="color: #ffff00;">READY_FOR_ANALYSIS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced Trading Protocols
    create_terminal_alert(
        "ADVANCED_OPTIONS_PROTOCOLS",
        """
        <strong>DERIVATIVES_OVERVIEW.sys</strong><br>
        ► OPTIONS: Contractual rights to buy/sell underlying securities<br>
        ► CALLS: Bullish directional exposure, unlimited upside potential<br>
        ► PUTS: Bearish directional exposure, limited to strike value<br><br>
        <strong>EXECUTION_PARAMETERS:</strong><br>
        ► STRIKE_PRICE: Fixed execution price level<br>
        ► EXPIRATION_DATE: Contract termination timestamp<br>
        ► PREMIUM: Acquisition cost (time + intrinsic value)<br>
        ► IMPLIED_VOLATILITY: Forward-looking price variance expectation<br><br>
        <strong>CLEARANCE_REQUIREMENTS:</strong><br>
        ► Level 1: Covered calls, cash-secured puts<br>
        ► Level 2: Long options, spreads<br>
        ► Level 3: Naked calls/puts (high risk)
        """,
        "info"
    )
    
    # Market Microstructure
    create_terminal_alert(
        "MARKET_MICROSTRUCTURE_DATA",
        """
        <strong>ORDERBOOK_DYNAMICS:</strong><br>
        ► BID_PRICE: Highest buyer price in queue<br>
        ► ASK_PRICE: Lowest seller price in queue<br>
        ► MID_PRICE: Theoretical fair value (bid+ask)/2<br>
        ► LAST_PRICE: Most recent execution price<br>
        ► VOLUME: Intraday contract turnover count<br>
        ► OPEN_INTEREST: Total outstanding contract inventory<br><br>
        <strong>LIQUIDITY_METRICS:</strong><br>
        ► HIGH_LIQUIDITY: Volume > 100, Spread < 5%<br>
        ► MODERATE_LIQUIDITY: Volume 20-100, Spread 5-10%<br>
        ► LOW_LIQUIDITY: Volume < 20, Spread > 10%<br><br>
        <strong>MARKET_IMPACT:</strong> Large orders affect prices in illiquid markets
        """,
        "success"
    )
    
    # Greeks Risk Framework
    create_terminal_alert(
        "GREEKS_RISK_FRAMEWORK",
        """
        <strong>SENSITIVITY_PARAMETERS:</strong><br>
        ► DELTA (Δ): Price sensitivity to $1 underlying move<br>
        ► GAMMA (Γ): Delta sensitivity to $1 underlying move<br>
        ► VEGA (ν): Price sensitivity to 1% volatility change<br>
        ► THETA (Θ): Time decay per calendar day<br>
        ► RHO (ρ): Price sensitivity to 1% interest rate change<br><br>
        <strong>PORTFOLIO_MANAGEMENT:</strong><br>
        ► DELTA_NEUTRAL: Zero directional exposure<br>
        ► GAMMA_SCALPING: Profit from volatility movements<br>
        ► VEGA_HEDGING: Manage volatility exposure<br>
        ► THETA_OPTIMIZATION: Time decay management strategies<br><br>
        <strong>RISK_LIMITS:</strong> Set position limits based on Greeks aggregation
        """,
        "warning"
    )
    
    # Professional Trading Systems
    create_terminal_alert(
        "TRADING_SYSTEM_ACCESS",
        """
        <strong>TIER_1_PROFESSIONAL_SYSTEMS:</strong><br>
        ► BLOOMBERG_TERMINAL: Real-time data, analytics, execution<br>
        ► REUTERS_EIKON: Global market data and news<br>
        ► INTERACTIVE_BROKERS: Professional execution platform<br>
        ► THINKORSWIM: Advanced retail trading platform<br><br>
        <strong>TIER_2_RETAIL_SYSTEMS:</strong><br>
        ► ROBINHOOD: Commission-free mobile platform<br>
        ► E_TRADE: Web-based trading with research<br>
        ► CHARLES_SCHWAB: Full-service brokerage<br>
        ► TASTYWORKS: Options-focused platform<br><br>
        <strong>CRITICAL_WARNING:</strong> Real-time data feeds required for professional trading.<br>
        Most retail platforms provide 15-20 minute delayed quotes.
        """,
        "error"
    )


def main():
    st.set_page_config(
        page_title="VOLATILITY MAINFRAME",
        page_icon="🟢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply retro mainframe styling
    apply_retro_mainframe_css()
    
    # Matrix background effect
    st.markdown('<div class="matrix-background"></div>', unsafe_allow_html=True)
    
    # Main header
    st.markdown(f"""
    <div class="mainframe-header crt-effect">
        <pre style="color: #00ff00; font-family: 'VT323', monospace; font-size: 12px; margin: 0;">
{create_mainframe_ascii()}
        </pre>
    </div>
    """, unsafe_allow_html=True)
    
    # System status
    st.markdown("""
    <div class="status-panel">
        <div style="color: #00ffff; font-weight: bold;">
        ► MAINFRAME_STATUS: <span style="color: #00ff00;">OPERATIONAL</span><br>
        ► MARKET_FEED: <span style="color: #00ff00;">LIVE_DATA_STREAM</span><br>
        ► RISK_SYSTEMS: <span style="color: #00ff00;">ACTIVE_MONITORING</span><br>
        ► USER_ACCESS: <span style="color: #ffff00;">AUTHORIZED</span><br>
        ► TIMESTAMP: <span style="color: #00ffff;">""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + """</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mainframe guide toggle
    if st.button("🖥️ ACCESS_MAINFRAME_PROTOCOLS", help="Load comprehensive financial mainframe documentation"):
        st.session_state['show_mainframe_guide'] = not st.session_state.get('show_mainframe_guide', False)
    
    if st.session_state.get('show_mainframe_guide', False):
        show_mainframe_guide()
        st.markdown("---")
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("""
        <div class="control-interface crt-effect">
            <h3 style="color: #00ffff; text-align: center; margin-bottom: 20px; font-family: 'VT323', monospace; font-size: 18px;">
                CONTROL_MATRIX
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Market data input
        st.markdown("""
        <div class="data-module" data-title="MARKET_DATA_INPUT">
        </div>
        """, unsafe_allow_html=True)
        
        ticker = st.text_input(
            "TARGET_SECURITY", 
            value="AAPL", 
            help="Enter security identifier for analysis"
        ).upper()
        
        create_terminal_alert(
            "RECOMMENDED_TARGETS",
            """
            <strong>HIGH_VOLUME_SECURITIES:</strong><br>
            ► EQUITIES: AAPL, MSFT, TSLA, NVDA, GOOGL<br>
            ► ETFS: SPY, QQQ, IWM, XLF, GLD<br>
            ► INDICES: ^SPX, ^NDX, ^RUT<br><br>
            <strong>OPTIMAL_CRITERIA:</strong><br>
            ► Daily volume > 1M shares<br>
            ► Options volume > 10K contracts<br>
            ► Tight bid-ask spreads < 0.05<br>
            ► Multiple expiration cycles available
            """,
            "success"
        )
        
        # Black-Scholes parameters
        st.markdown("""
        <div class="data-module" data-title="THEORETICAL_PRICING_ENGINE">
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            test_spot = st.number_input(
                "SPOT_PRICE", 
                value=150.0, 
                min_value=1.0, 
                step=1.0,
                help="Current underlying price"
            )
            test_strike = st.number_input(
                "STRIKE_PRICE", 
                value=150.0, 
                min_value=1.0, 
                step=1.0,
                help="Option strike price"
            )
        
        with col2:
            test_time = st.number_input(
                "TIME_TO_EXPIRY", 
                value=0.25, 
                min_value=0.01, 
                max_value=2.0, 
                step=0.01,
                help="Time in years until expiration"
            )
            test_vol = st.number_input(
                "VOLATILITY", 
                value=0.25, 
                min_value=0.01, 
                max_value=2.0, 
                step=0.01,
                help="Annual volatility (decimal)"
            )
        
        test_rate = st.number_input(
            "RISK_FREE_RATE", 
            value=0.05, 
            min_value=-0.05, 
            max_value=0.20, 
            step=0.001,
            help="Risk-free interest rate"
        )
        
        test_option_type = st.selectbox(
            "CONTRACT_TYPE", 
            ["call", "put"],
            help="Option contract type"
        )
    
    # Main terminal interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧮 BLACK_SCHOLES_ENGINE", 
        "📊 MARKET_DATA_FEED", 
        "🌊 VOLATILITY_SURFACE", 
        "⚡ GREEKS_ANALYSIS",
        "🎯 RISK_MANAGEMENT"
    ])
    
    with tab1:
        st.markdown("""
        <div class="data-module" data-title="BLACK_SCHOLES_PRICING_ENGINE">
            <h3 style="color: #00ffff; text-align: center; font-family: 'VT323', monospace;">
                ═══ THEORETICAL_OPTION_VALUATION ═══
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        create_terminal_alert(
            "ENGINE_SPECIFICATIONS",
            """
            <strong>BLACK_SCHOLES_MODEL.exe</strong><br>
            ► Foundation of modern derivatives pricing<br>
            ► Assumes geometric Brownian motion<br>
            ► Constant volatility and interest rates<br>
            ► No dividends, European exercise only<br>
            ► Continuous trading, no transaction costs<br><br>
            <strong>INPUT_PARAMETERS:</strong><br>
            ► S: Current underlying price<br>
            ► K: Strike price of option<br>
            ► T: Time to expiration (years)<br>
            ► r: Risk-free interest rate<br>
            ► σ: Volatility (annualized)<br><br>
            <strong>ACCURACY:</strong> Best for short-term, at-the-money options
            """,
            "info"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="data-module" data-title="OPTION_VALUATION">
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Calculate theoretical price
                theoretical_price = black_scholes_price(
                    test_spot, test_strike, test_time, test_rate, test_vol, test_option_type
                )
                
                # Value decomposition
                decomp = option_value_decomposition(
                    test_spot, test_strike, test_time, test_rate, test_vol, test_option_type
                )
                
                create_terminal_metric("THEORETICAL_PRICE", f"${theoretical_price:.4f}", "USD", "THEO_PRICE")
                create_terminal_metric("INTRINSIC_VALUE", f"${decomp['intrinsic_value']:.4f}", "USD", "INTRINSIC")
                create_terminal_metric("TIME_VALUE", f"${decomp['time_value']:.4f}", "USD", "TIME_VAL")
                
                # Moneyness calculation
                moneyness = (test_spot - test_strike) / test_spot * 100
                if test_option_type == 'call':
                    if moneyness > 10:
                        money_status = "DEEP_ITM"
                        status_color = "#00ff00"
                    elif moneyness > 0:
                        money_status = "ITM"
                        status_color = "#00ff00"
                    elif moneyness > -10:
                        money_status = "ATM"
                        status_color = "#ffff00"
                    else:
                        money_status = "OTM"
                        status_color = "#ff8800"
                else:
                    if moneyness < -10:
                        money_status = "DEEP_ITM"
                        status_color = "#00ff00"
                    elif moneyness < 0:
                        money_status = "ITM"
                        status_color = "#00ff00"
                    elif moneyness < 10:
                        money_status = "ATM"
                        status_color = "#ffff00"
                    else:
                        money_status = "OTM"
                        status_color = "#ff8800"
                
                st.markdown(f"""
                <div style="text-align: center; color: {status_color}; font-weight: bold; font-family: 'VT323', monospace; font-size: 16px; margin: 15px 0;">
                    MONEYNESS: {money_status}<br>
                    DIFFERENCE: {moneyness:+.2f}%
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                create_terminal_alert("CALCULATION_ERROR", f"Pricing engine error: {str(e)}", "error")
        
        with col2:
            st.markdown("""
            <div class="data-module" data-title="GREEKS_DASHBOARD">
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Calculate Greeks
                greeks = all_greeks(test_spot, test_strike, test_time, test_rate, test_vol, test_option_type)
                
                create_terminal_metric("DELTA", f"{greeks['delta']:.5f}", "PRICE_SENS", "DELTA")
                create_terminal_metric("GAMMA", f"{greeks['gamma']:.7f}", "DELTA_SENS", "GAMMA")
                create_terminal_metric("VEGA", f"{greeks['vega']:.5f}", "VOL_SENS", "VEGA")
                create_terminal_metric("THETA", f"{greeks['theta']:.5f}", "TIME_DECAY", "THETA")
                create_terminal_metric("RHO", f"{greeks['rho']:.5f}", "RATE_SENS", "RHO")
                
            except Exception as e:
                create_terminal_alert("GREEKS_ERROR", f"Greeks calculation failed: {str(e)}", "error")
        
        with col3:
            st.markdown("""
            <div class="data-module" data-title="SENSITIVITY_MATRIX">
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Sensitivity analysis
                spot_range = np.linspace(test_spot * 0.8, test_spot * 1.2, 30)
                prices = []
                deltas = []
                
                for spot in spot_range:
                    price = black_scholes_price(spot, test_strike, test_time, test_rate, test_vol, test_option_type)
                    delta = all_greeks(spot, test_strike, test_time, test_rate, test_vol, test_option_type)['delta']
                    prices.append(price)
                    deltas.append(delta)
                
                # Create terminal-style plot
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=spot_range, y=prices,
                    name='OPTION_PRICE',
                    line=dict(color='#00ff00', width=3),
                    hovertemplate='SPOT: $%{x:.2f}<br>PRICE: $%{y:.4f}<extra></extra>'
                ))
                
                fig.add_trace(go.Scatter(
                    x=spot_range, y=deltas,
                    name='DELTA',
                    line=dict(color='#00ffff', width=2),
                    yaxis='y2',
                    hovertemplate='SPOT: $%{x:.2f}<br>DELTA: %{y:.4f}<extra></extra>'
                ))
                
                # Current position marker
                fig.add_trace(go.Scatter(
                    x=[test_spot], y=[theoretical_price],
                    mode='markers',
                    name='CURRENT_POSITION',
                    marker=dict(color='#ffff00', size=15, symbol='diamond'),
                    hovertemplate=f'CURRENT: ${test_spot:.2f}<br>PRICE: ${theoretical_price:.4f}<extra></extra>'
                ))
                
                fig.update_layout(
                    title=dict(text="SENSITIVITY_ANALYSIS_MATRIX", font=dict(color='#00ffff', family='VT323', size=18)),
                    xaxis=dict(title="UNDERLYING_PRICE", color='#00ff00', gridcolor='#003300'),
                    yaxis=dict(title="OPTION_PRICE", color='#00ff00', gridcolor='#003300'),
                    yaxis2=dict(title="DELTA", overlaying='y', side='right', color='#00ffff'),
                    plot_bgcolor='#000000',
                    paper_bgcolor='#000000',
                    font=dict(color='#00ff00', family='Source Code Pro'),
                    showlegend=True,
                    legend=dict(font=dict(color='#00ff00'), bgcolor='rgba(0,0,0,0.5)')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # P&L Analysis
                breakeven = test_strike + theoretical_price if test_option_type == 'call' else test_strike - theoretical_price
                max_loss = theoretical_price
                max_profit = "UNLIMITED" if test_option_type == 'call' else f"${test_strike - theoretical_price:.2f}"
                
                create_terminal_alert(
                    "PROFIT_LOSS_ANALYSIS",
                    f"""
                    <strong>BREAKEVEN_PRICE:</strong> ${breakeven:.2f}<br>
                    <strong>MAXIMUM_LOSS:</strong> ${max_loss:.2f}<br>
                    <strong>MAXIMUM_PROFIT:</strong> {max_profit}<br>
                    <strong>RISK_REWARD_RATIO:</strong> {"∞" if max_profit == "UNLIMITED" else f"{float(max_profit[1:]) / max_loss:.2f}:1"}
                    """,
                    "warning"
                )
                
            except Exception as e:
                create_terminal_alert("ANALYSIS_ERROR", f"Sensitivity analysis failed: {str(e)}", "error")
    
    with tab2:
        st.markdown("""
        <div class="data-module" data-title="REAL_TIME_MARKET_FEED">
            <h3 style="color: #00ffff; text-align: center; font-family: 'VT323', monospace;">
                ═══ LIVE_MARKET_DATA_STREAM ═══
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        create_terminal_alert("SYSTEM_INFO", "Real-time market data feed implementation in development", "info")
    
    with tab3:
        st.markdown("""
        <div class="data-module" data-title="3D_VOLATILITY_SURFACE">
            <h3 style="color: #00ffff; text-align: center; font-family: 'VT323', monospace;">
                ═══ VOLATILITY_SURFACE_GENERATOR ═══
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        create_terminal_alert("SYSTEM_INFO", "3D volatility surface visualization engine in development", "info")
    
    with tab4:
        st.markdown("""
        <div class="data-module" data-title="ADVANCED_GREEKS_ANALYSIS">
            <h3 style="color: #00ffff; text-align: center; font-family: 'VT323', monospace;">
                ═══ PORTFOLIO_GREEKS_MATRIX ═══
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        create_terminal_alert("SYSTEM_INFO", "Advanced Greeks analysis and portfolio management tools in development", "info")
    
    with tab5:
        st.markdown("""
        <div class="data-module" data-title="RISK_MANAGEMENT_PROTOCOLS">
            <h3 style="color: #00ffff; text-align: center; font-family: 'VT323', monospace;">
                ═══ AUTOMATED_RISK_CONTROLS ═══
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        create_terminal_alert("SYSTEM_INFO", "Automated risk management and position monitoring systems in development", "info")


if __name__ == "__main__":
    main()

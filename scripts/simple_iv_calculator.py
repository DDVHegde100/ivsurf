#!/usr/bin/env python3
"""
RETRO IV CALCULATOR v2.0 - Single Option Analysis Terminal

Classic 1996-style hacker financial terminal with comprehensive options analysis.
Green-on-black aesthetic with maximum information density and functionality.

Run: streamlit run scripts/simple_iv_calculator.py
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

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_data import OptionsDataFetcher, get_stock_price
from core.black_scholes import black_scholes_price, implied_volatility, option_value_decomposition
from core.greeks import all_greeks


def apply_retro_terminal_css():
    """Apply classic 1990s hacker/financial terminal styling."""
    st.markdown("""
    <style>
    /* Import Retro Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=VT323:wght@400&family=Source+Code+Pro:wght@300;400;500;600;700&display=swap');
    
    /* Main Terminal Background */
    .main {
        background: #000000;
        color: #00ff00;
        font-family: 'Courier Prime', monospace;
        font-size: 14px;
        line-height: 1.4;
    }
    
    /* Classic Terminal Window */
    .terminal-window {
        background: #000000;
        border: 2px solid #00ff00;
        border-radius: 0px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 0 20px #00ff00;
        position: relative;
    }
    
    .terminal-window::before {
        content: '█ OPTION_TERMINAL_v2.0 █';
        position: absolute;
        top: -12px;
        left: 10px;
        background: #000000;
        color: #00ff00;
        padding: 0 10px;
        font-family: 'VT323', monospace;
        font-size: 16px;
        font-weight: bold;
    }
    
    /* ASCII Art Headers */
    .ascii-header {
        font-family: 'VT323', monospace;
        font-size: 20px;
        color: #00ff00;
        text-align: center;
        white-space: pre;
        background: #000000;
        border: 1px solid #00ff00;
        padding: 15px;
        margin: 15px 0;
        box-shadow: inset 0 0 10px #003300;
    }
    
    /* Data Blocks */
    .data-block {
        background: #001100;
        border: 1px solid #00ff00;
        padding: 15px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        font-size: 13px;
        position: relative;
    }
    
    .data-block::before {
        content: attr(data-label);
        position: absolute;
        top: -8px;
        left: 10px;
        background: #000000;
        color: #00ffff;
        padding: 0 5px;
        font-size: 11px;
        font-weight: bold;
    }
    
    /* Matrix-style scrolling text */
    .matrix-text {
        color: #00ff00;
        font-family: 'VT323', monospace;
        font-size: 12px;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    /* Classic CRT scanlines */
    .scanlines {
        position: relative;
    }
    
    .scanlines::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            90deg,
            transparent,
            transparent 2px,
            rgba(0, 255, 0, 0.03) 2px,
            rgba(0, 255, 0, 0.03) 4px
        );
        pointer-events: none;
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg {
        background: #000000;
        border-right: 2px solid #00ff00;
        box-shadow: 2px 0 10px #003300;
    }
    
    /* Control Panel */
    .control-panel {
        background: #001100;
        border: 2px solid #00ff00;
        padding: 15px;
        margin: 10px 0;
        position: relative;
    }
    
    .control-panel::before {
        content: '▼ CONTROL_INTERFACE ▼';
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #000000;
        color: #00ffff;
        padding: 0 10px;
        font-family: 'VT323', monospace;
        font-size: 14px;
        font-weight: bold;
    }
    
    /* Alert Boxes */
    .alert-success {
        background: #003300;
        border: 1px solid #00ff00;
        color: #00ff00;
        padding: 10px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
    }
    
    .alert-success::before {
        content: '[SUCCESS]';
        color: #00ffff;
        font-weight: bold;
    }
    
    .alert-error {
        background: #330000;
        border: 1px solid #ff0000;
        color: #ff0000;
        padding: 10px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
    }
    
    .alert-error::before {
        content: '[ERROR]';
        color: #ffff00;
        font-weight: bold;
    }
    
    .alert-warning {
        background: #333300;
        border: 1px solid #ffff00;
        color: #ffff00;
        padding: 10px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
    }
    
    .alert-warning::before {
        content: '[WARNING]';
        color: #ff8800;
        font-weight: bold;
    }
    
    /* Info Sections */
    .info-terminal {
        background: #000033;
        border: 1px solid #0088ff;
        color: #00aaff;
        padding: 15px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        font-size: 12px;
        position: relative;
    }
    
    .info-terminal::before {
        content: '[INFO]';
        color: #00ffff;
        font-weight: bold;
        position: absolute;
        top: -8px;
        left: 10px;
        background: #000000;
        padding: 0 5px;
    }
    
    /* Metric Displays */
    .metric-display {
        background: #001a00;
        border: 1px solid #00ff00;
        padding: 12px;
        margin: 8px 0;
        font-family: 'Source Code Pro', monospace;
        position: relative;
        text-align: center;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #00ff00;
        text-shadow: 0 0 5px #00ff00;
    }
    
    .metric-label {
        font-size: 11px;
        color: #00ffff;
        text-transform: uppercase;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background: #000000;
        border: 1px solid #00ff00;
        border-radius: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #001100;
        color: #00ff00;
        border: 1px solid #00ff00;
        border-radius: 0;
        font-family: 'VT323', monospace;
        font-size: 16px;
        margin: 2px;
        padding: 10px 15px;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #003300;
        color: #00ffff;
        box-shadow: 0 0 10px #00ff00;
    }
    
    .stTabs [aria-selected="true"] {
        background: #00ff00;
        color: #000000;
        font-weight: bold;
        box-shadow: 0 0 15px #00ff00;
    }
    
    /* Button Styling */
    .stButton > button {
        background: #000000;
        color: #00ff00;
        border: 2px solid #00ff00;
        border-radius: 0;
        font-family: 'VT323', monospace;
        font-size: 16px;
        font-weight: bold;
        padding: 8px 16px;
        transition: all 0.2s ease;
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        background: #00ff00;
        color: #000000;
        box-shadow: 0 0 15px #00ff00;
        transform: scale(1.05);
    }
    
    /* Form Elements */
    .stSelectbox > div > div {
        background: #001100;
        border: 1px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
    }
    
    .stTextInput > div > div > input {
        background: #001100;
        border: 1px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
        font-size: 14px;
    }
    
    .stNumberInput > div > div > input {
        background: #001100;
        border: 1px solid #00ff00;
        border-radius: 0;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
        font-size: 14px;
    }
    
    /* Plotly Charts Styling */
    .js-plotly-plot {
        background: #000000;
        border: 2px solid #00ff00;
        box-shadow: 0 0 20px #003300;
    }
    
    /* Progress Bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00ff00, #00aa00);
    }
    
    /* Success/Error/Warning Messages */
    .stAlert {
        border-radius: 0;
        font-family: 'Source Code Pro', monospace;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
        background: #000000;
    }
    
    ::-webkit-scrollbar-track {
        background: #001100;
        border: 1px solid #00ff00;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff00;
        border: 1px solid #000000;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00ffff;
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-top-color: #00ff00 !important;
        border-right-color: #00ff00 !important;
    }
    
    /* DataFrames */
    .stDataFrame {
        border: 2px solid #00ff00;
        background: #000000;
    }
    
    .stDataFrame table {
        background: #000000;
        color: #00ff00;
        font-family: 'Source Code Pro', monospace;
        font-size: 12px;
    }
    
    .stDataFrame th {
        background: #003300;
        color: #00ffff;
        border: 1px solid #00ff00;
        font-weight: bold;
    }
    
    .stDataFrame td {
        background: #001100;
        color: #00ff00;
        border: 1px solid #00ff00;
    }
    
    /* ASCII Borders */
    .ascii-box {
        font-family: 'VT323', monospace;
        border: 2px solid #00ff00;
        background: #000000;
        padding: 15px;
        margin: 10px 0;
        position: relative;
    }
    
    .ascii-box::before {
        content: '╔══════════════════════════════════════════════════════════════╗';
        position: absolute;
        top: -12px;
        left: 0;
        color: #00ff00;
        background: #000000;
        font-size: 12px;
    }
    
    /* Matrix-style background effect */
    body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 25% 25%, #003300 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, #003300 0%, transparent 50%);
        opacity: 0.1;
        z-index: -1;
        pointer-events: none;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .ascii-header {
            font-size: 16px;
        }
        
        .terminal-window {
            padding: 15px;
        }
        
        .metric-value {
            font-size: 18px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def create_ascii_header():
    """Create retro ASCII art header."""
    return """
╔══════════════════════════════════════════════════════════════╗
║  ██████╗ ██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗    ║
║ ██╔═══██╗██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝    ║
║ ██║   ██║██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗    ║
║ ██║   ██║██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║    ║
║ ╚██████╔╝██║        ██║   ██║╚██████╔╝██║ ╚████║███████║    ║
║  ╚═════╝ ╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ║
║                                                              ║
║              TERMINAL v2.0 - IMPLIED VOLATILITY             ║
║                    ANALYSIS SYSTEM                          ║
╚══════════════════════════════════════════════════════════════╝
    """


def create_info_box(title, content, box_type="info"):
    """Create retro-styled information boxes."""
    colors = {
        "info": {"bg": "#000033", "border": "#0088ff", "color": "#00aaff"},
        "success": {"bg": "#003300", "border": "#00ff00", "color": "#00ff00"},
        "warning": {"bg": "#333300", "border": "#ffff00", "color": "#ffff00"},
        "error": {"bg": "#330000", "border": "#ff0000", "color": "#ff0000"}
    }
    
    style = colors.get(box_type, colors["info"])
    
    st.markdown(f"""
    <div style="
        background: {style['bg']};
        border: 2px solid {style['border']};
        color: {style['color']};
        padding: 15px;
        margin: 10px 0;
        font-family: 'Source Code Pro', monospace;
        font-size: 13px;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: -10px;
            left: 10px;
            background: #000000;
            padding: 0 8px;
            font-weight: bold;
            color: #00ffff;
            font-size: 12px;
        ">[{title.upper()}]</div>
        {content}
    </div>
    """, unsafe_allow_html=True)


def create_metric_terminal(label, value, unit="", tooltip=""):
    """Create terminal-style metric display."""
    st.markdown(f"""
    <div class="data-block" data-label="{label.upper()}">
        <div style="text-align: center;">
            <div style="font-size: 28px; font-weight: bold; color: #00ff00; text-shadow: 0 0 10px #00ff00; font-family: 'VT323', monospace;">
                {value}
            </div>
            <div style="font-size: 12px; color: #00ffff; text-transform: uppercase; margin-top: 5px;">
                {unit}
            </div>
            {f'<div style="font-size: 11px; color: #888888; margin-top: 5px;">{tooltip}</div>' if tooltip else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_hacker_guide():
    """Show comprehensive trading guide in hacker terminal style."""
    st.markdown(f"""
    <div class="ascii-header scanlines">
{create_ascii_header()}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="terminal-window scanlines">
        <div style="color: #00ffff; font-weight: bold; margin-bottom: 15px;">
        ► ACCESSING FINANCIAL_MAINFRAME...
        ► CONNECTING TO MARKET_DATA_STREAM...
        ► INITIALIZING OPTION_ANALYSIS_PROTOCOLS...
        ► <span class="matrix-text">READY FOR OPERATION</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Options Fundamentals
    create_info_box(
        "SYSTEM_INFO",
        """
        <strong>OPTIONS_CONTRACTS.exe</strong> - Financial derivatives granting rights to buy/sell underlying assets<br><br>
        <strong>CALL_OPTION:</strong> RIGHT_TO_BUY at fixed price (STRIKE)<br>
        <strong>PUT_OPTION:</strong> RIGHT_TO_SELL at fixed price (STRIKE)<br><br>
        <strong>EXECUTION_PARAMETERS:</strong><br>
        • STRIKE_PRICE: Contractual execution price<br>
        • EXPIRATION_DATE: Contract termination timestamp<br>
        • PREMIUM: Cost of contract acquisition<br>
        • IMPLIED_VOLATILITY: Market expectation variance metric<br><br>
        <strong>ACCESS_LEVEL:</strong> Requires broker account with options clearance
        """,
        "info"
    )
    
    # Market Data Explained
    create_info_box(
        "MARKET_DATA_PROTOCOL",
        """
        <strong>BID_PRICE:</strong> Maximum buyer offer in orderbook<br>
        <strong>ASK_PRICE:</strong> Minimum seller demand in orderbook<br>
        <strong>MID_PRICE:</strong> Calculated average (BID + ASK) / 2<br>
        <strong>LAST_PRICE:</strong> Most recent transaction execution price<br>
        <strong>VOLUME:</strong> Daily contract transaction count<br>
        <strong>OPEN_INTEREST:</strong> Total outstanding contract inventory<br><br>
        <strong>LIQUIDITY_ASSESSMENT:</strong><br>
        • HIGH: Volume > 100, Spread < 5%<br>
        • MODERATE: Volume > 20, Spread < 10%<br>
        • LOW: Volume < 20, Spread > 10%
        """,
        "success"
    )
    
    # Greeks Explained
    create_info_box(
        "RISK_PARAMETERS",
        """
        <strong>DELTA (Δ):</strong> Price sensitivity coefficient to underlying movement<br>
        <strong>GAMMA (Γ):</strong> Delta acceleration factor per unit price change<br>
        <strong>VEGA (ν):</strong> Volatility sensitivity coefficient (1% change)<br>
        <strong>THETA (Θ):</strong> Time decay coefficient (daily value erosion)<br>
        <strong>RHO (ρ):</strong> Interest rate sensitivity coefficient<br><br>
        <strong>RISK_MANAGEMENT_PROTOCOL:</strong><br>
        • Monitor DELTA for directional exposure<br>
        • Track THETA for time decay impact<br>
        • Assess VEGA for volatility risk<br>
        • Calculate position Greeks aggregation
        """,
        "warning"
    )
    
    # Trading Platforms
    create_info_box(
        "TRADING_PLATFORMS",
        """
        <strong>TIER_1_SYSTEMS:</strong> Professional Grade<br>
        • BLOOMBERG_TERMINAL: Industry standard, real-time data<br>
        • INTERACTIVE_BROKERS: Low latency, advanced order types<br>
        • THINKORSWIM: Retail professional platform<br><br>
        <strong>TIER_2_SYSTEMS:</strong> Consumer Grade<br>
        • ROBINHOOD: Commission-free, mobile-first<br>
        • E_TRADE: Web-based, educational resources<br>
        • TASTYWORKS: Options-focused platform<br><br>
        <strong>WARNING:</strong> Most retail platforms show delayed data (15-20min lag)
        """,
        "error"
    )


def main():
    st.set_page_config(
        page_title="RETRO IV TERMINAL",
        page_icon="💚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply retro terminal styling
    apply_retro_terminal_css()
    
    # ASCII Header
    st.markdown(f"""
    <div class="ascii-header scanlines">
{create_ascii_header()}
    </div>
    """, unsafe_allow_html=True)
    
    # System Status
    st.markdown("""
    <div class="terminal-window">
        <div style="color: #00ffff; font-weight: bold;">
        ► SYSTEM_STATUS: <span style="color: #00ff00;">ONLINE</span><br>
        ► MARKET_CONNECTION: <span style="color: #00ff00;">ESTABLISHED</span><br>
        ► DATA_FEED: <span style="color: #00ff00;">ACTIVE</span><br>
        ► USER_CLEARANCE: <span style="color: #ffff00;">GRANTED</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hacker Guide Toggle
    if st.button("📖 ACCESS_TRADING_PROTOCOLS", help="Load comprehensive trading database"):
        st.session_state['show_hacker_guide'] = not st.session_state.get('show_hacker_guide', False)
    
    if st.session_state.get('show_hacker_guide', False):
        show_hacker_guide()
        st.markdown("---")
    
    # Enhanced sidebar with terminal styling
    with st.sidebar:
        st.markdown("""
        <div class="control-panel scanlines">
            <h3 style="color: #00ffff; text-align: center; margin-bottom: 20px; font-family: 'VT323', monospace;">
                CONTROL_INTERFACE
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Ticker input
        ticker = st.text_input(
            "TARGET_SYMBOL", 
            value="AAPL", 
            help="Enter stock ticker for analysis"
        ).upper()
        
        create_info_box(
            "OPTIMAL_TARGETS",
            """
            <strong>HIGH_LIQUIDITY:</strong> SPY, QQQ, AAPL, TSLA, MSFT<br>
            <strong>TECH_SECTOR:</strong> NVDA, GOOGL, AMZN, META<br>
            <strong>FINANCIAL:</strong> XLF, JPM, BAC, GS<br><br>
            <strong>AVOID:</strong> Low volume, penny stocks, new IPOs
            """,
            "success"
        )
        
        # Data fetch button
        if st.button("🔍 INITIATE_DATA_RETRIEVAL", help="Execute market data acquisition protocol"):
            if ticker:
                with st.spinner("► ACCESSING_MARKET_MAINFRAME..."):
                    try:
                        fetcher = OptionsDataFetcher()
                        
                        # Get stock info
                        stock_info = fetcher.get_stock_info(ticker)
                        st.session_state['stock_info'] = stock_info
                        
                        # Get options chain
                        options_df = fetcher.get_options_chain(ticker, max_expiries=8)
                        st.session_state['options_df'] = options_df
                        
                        st.success(f"✅ DATA_ACQUIRED: {len(options_df)} contracts for {ticker}")
                        
                    except Exception as e:
                        st.error(f"❌ CONNECTION_ERROR: {str(e)}")
        
        # Display stock info in terminal style
        if 'stock_info' in st.session_state:
            info = st.session_state['stock_info']
            
            st.markdown(f"""
            <div class="data-block" data-label="TARGET_ANALYSIS">
                <div style="color: #00ffff; font-weight: bold; margin-bottom: 10px;">
                    {info['symbol']} - {info['company_name']}
                </div>
                <div style="color: #00ff00; font-family: 'Source Code Pro', monospace;">
                    PRICE: ${info['current_price']:.2f}<br>
                    CHANGE: {info['change']:+.2f} ({info['change_percent']:+.2f}%)<br>
                    VOLUME: {info['volume']:,}<br>
                    SECTOR: {info.get('sector', 'N/A')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Option selection interface
        if 'options_df' in st.session_state:
            st.markdown("""
            <div class="control-panel">
                <h4 style="color: #00ffff; margin-bottom: 15px;">CONTRACT_SELECTION</h4>
            </div>
            """, unsafe_allow_html=True)
            
            df = st.session_state['options_df']
            
            # Option type
            option_type = st.selectbox(
                "CONTRACT_TYPE", 
                ['call', 'put'],
                help="CALL: Bullish position | PUT: Bearish position"
            )
            
            # Filter options
            filtered_df = df[df['optionType'] == option_type].copy()
            
            # Expiration selection
            expiry_dates = sorted(filtered_df['expiration'].unique())
            selected_expiry = st.selectbox("EXPIRATION_DATE", expiry_dates)
            
            # Filter by expiry
            expiry_df = filtered_df[filtered_df['expiration'] == selected_expiry].copy()
            
            # Days to expiry display
            days_to_expiry = expiry_df.iloc[0]['daysToExpiry']
            st.markdown(f"""
            <div style="text-align: center; color: #00ff00; font-weight: bold; font-family: 'VT323', monospace; font-size: 16px;">
                ⏱️ T-{days_to_expiry} DAYS_TO_EXPIRATION
            </div>
            """, unsafe_allow_html=True)
            
            # Strike selection
            strikes = sorted(expiry_df['strike'].unique())
            current_price = st.session_state['stock_info']['current_price']
            
            # Find closest strike for default
            closest_strike_idx = np.argmin(np.abs(np.array(strikes) - current_price))
            
            selected_strike = st.selectbox(
                "STRIKE_PRICE", 
                strikes,
                index=closest_strike_idx
            )
            
            # Get selected option
            selected_option = expiry_df[expiry_df['strike'] == selected_strike].iloc[0]
            st.session_state['selected_option'] = selected_option
    
    # Main terminal interface
    if 'selected_option' in st.session_state and 'stock_info' in st.session_state:
        option = st.session_state['selected_option']
        stock_info = st.session_state['stock_info']
        
        # Terminal tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 CONTRACT_DATA", 
            "🧮 VOLATILITY_ANALYSIS", 
            "📈 GREEKS_MATRIX",
            "🎯 RISK_ASSESSMENT"
        ])
        
        with tab1:
            st.markdown("""
            <div class="terminal-window">
                <h3 style="color: #00ffff; font-family: 'VT323', monospace; text-align: center;">
                    ═══ CONTRACT_SPECIFICATIONS ═══
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div class="data-block" data-label="CONTRACT_PARAMS">
                </div>
                """, unsafe_allow_html=True)
                
                create_metric_terminal("SYMBOL", stock_info['symbol'])
                create_metric_terminal("TYPE", option['optionType'].upper())
                create_metric_terminal("STRIKE", f"${option['strike']:.2f}")
                create_metric_terminal("EXPIRY", option['expiration'])
                create_metric_terminal("DAYS_TO_EXP", str(option['daysToExpiry']))
            
            with col2:
                st.markdown("""
                <div class="data-block" data-label="MARKET_DATA">
                </div>
                """, unsafe_allow_html=True)
                
                create_metric_terminal("LAST_PRICE", f"${option['lastPrice']:.3f}")
                create_metric_terminal("BID", f"${option['bid']:.3f}")
                create_metric_terminal("ASK", f"${option['ask']:.3f}")
                create_metric_terminal("MID_PRICE", f"${option['midPrice']:.3f}")
                create_metric_terminal("SPREAD", f"${option['bidAskSpread']:.3f}")
            
            with col3:
                st.markdown("""
                <div class="data-block" data-label="ACTIVITY_METRICS">
                </div>
                """, unsafe_allow_html=True)
                
                create_metric_terminal("VOLUME", f"{option['volume']:,}")
                create_metric_terminal("OPEN_INT", f"{option['openInterest']:,}")
                
                # Liquidity assessment
                if option['volume'] > 100 and option['bidAskSpreadPct'] < 5:
                    liquidity = "HIGH_LIQUIDITY"
                    liq_color = "#00ff00"
                elif option['volume'] > 20 and option['bidAskSpreadPct'] < 10:
                    liquidity = "MODERATE_LIQUIDITY"
                    liq_color = "#ffff00"
                else:
                    liquidity = "LOW_LIQUIDITY"
                    liq_color = "#ff0000"
                
                st.markdown(f"""
                <div style="text-align: center; color: {liq_color}; font-weight: bold; font-family: 'VT323', monospace; margin-top: 15px;">
                    STATUS: {liquidity}
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("""
            <div class="terminal-window">
                <h3 style="color: #00ffff; font-family: 'VT323', monospace; text-align: center;">
                    ═══ IMPLIED_VOLATILITY_ANALYSIS ═══
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # IV Analysis explanation
            create_info_box(
                "VOLATILITY_PROTOCOL",
                """
                <strong>IMPLIED_VOLATILITY:</strong> Market expectation of future price variance<br>
                <strong>CALCULATION_METHOD:</strong> Newton-Raphson iterative solver<br>
                <strong>INPUT_PARAMETERS:</strong> Option price, underlying price, strike, time, rate<br><br>
                <strong>INTERPRETATION:</strong><br>
                • HIGH_IV (>40%): Elevated option premiums, high uncertainty<br>
                • NORMAL_IV (20-40%): Standard market conditions<br>
                • LOW_IV (<20%): Cheap options, low expected movement
                """,
                "info"
            )
            
            # Calculate IV
            try:
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05  # Risk-free rate
                
                market_price = option['midPrice']
                
                if market_price > 0 and T > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("""
                        <div class="data-block" data-label="IV_CALCULATION">
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.spinner("► EXECUTING_IV_SOLVER..."):
                            iv_newton = implied_volatility(market_price, S, K, T, r, option['optionType'], method='newton')
                            iv_brent = implied_volatility(market_price, S, K, T, r, option['optionType'], method='brent')
                        
                        if not np.isnan(iv_newton):
                            create_metric_terminal("NEWTON_IV", f"{iv_newton*100:.2f}%", "NEWTON_RAPHSON_METHOD")
                        
                        if not np.isnan(iv_brent):
                            create_metric_terminal("BRENT_IV", f"{iv_brent*100:.2f}%", "BRENT_OPTIMIZATION")
                        
                        # Use best IV
                        best_iv = iv_newton if not np.isnan(iv_newton) else iv_brent
                        
                        if not np.isnan(best_iv):
                            st.session_state['calculated_iv'] = best_iv
                            
                            # IV Assessment
                            if best_iv > 0.4:
                                iv_status = "EXTREME_VOLATILITY"
                                status_color = "#ff0000"
                            elif best_iv > 0.3:
                                iv_status = "HIGH_VOLATILITY"
                                status_color = "#ffff00"
                            elif best_iv > 0.2:
                                iv_status = "NORMAL_VOLATILITY"
                                status_color = "#00ff00"
                            else:
                                iv_status = "LOW_VOLATILITY"
                                status_color = "#00aaff"
                            
                            st.markdown(f"""
                            <div style="text-align: center; color: {status_color}; font-weight: bold; font-family: 'VT323', monospace; font-size: 18px; margin: 20px 0;">
                                STATUS: {iv_status}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        if not np.isnan(best_iv):
                            # Option value decomposition
                            decomp = option_value_decomposition(S, K, T, r, best_iv, option['optionType'])
                            
                            st.markdown("""
                            <div class="data-block" data-label="VALUE_BREAKDOWN">
                            </div>
                            """, unsafe_allow_html=True)
                            
                            create_metric_terminal("THEORETICAL", f"${decomp['total_value']:.3f}", "BLACK_SCHOLES_PRICE")
                            create_metric_terminal("INTRINSIC", f"${decomp['intrinsic_value']:.3f}", "IMMEDIATE_EXERCISE_VALUE")
                            create_metric_terminal("TIME_VALUE", f"${decomp['time_value']:.3f}", "REMAINING_PREMIUM")
                            
                            # Price comparison
                            price_diff = market_price - decomp['total_value']
                            if abs(price_diff) < 0.05:
                                price_status = "FAIR_VALUED"
                                price_color = "#00ff00"
                            elif price_diff > 0:
                                price_status = "OVERVALUED"
                                price_color = "#ff0000"
                            else:
                                price_status = "UNDERVALUED"
                                price_color = "#00aaff"
                            
                            st.markdown(f"""
                            <div style="text-align: center; color: {price_color}; font-weight: bold; font-family: 'VT323', monospace; margin-top: 15px;">
                                VALUATION: {price_status}<br>
                                DIFFERENCE: ${price_diff:+.3f}
                            </div>
                            """, unsafe_allow_html=True)
                
                else:
                    create_info_box("ERROR", "Invalid market data for IV calculation", "error")
                    
            except Exception as e:
                create_info_box("SYSTEM_ERROR", f"IV calculation failed: {str(e)}", "error")
        
        with tab3:
            st.markdown("""
            <div class="terminal-window">
                <h3 style="color: #00ffff; font-family: 'VT323', monospace; text-align: center;">
                    ═══ GREEKS_RISK_MATRIX ═══
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            if 'calculated_iv' in st.session_state:
                iv = st.session_state['calculated_iv']
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05
                
                try:
                    greeks = all_greeks(S, K, T, r, iv, option['optionType'])
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("""
                        <div class="data-block" data-label="PRIMARY_GREEKS">
                        </div>
                        """, unsafe_allow_html=True)
                        
                        create_metric_terminal("DELTA", f"{greeks['delta']:.4f}", "PRICE_SENSITIVITY")
                        create_metric_terminal("GAMMA", f"{greeks['gamma']:.6f}", "DELTA_ACCELERATION")
                    
                    with col2:
                        st.markdown("""
                        <div class="data-block" data-label="VOLATILITY_TIME">
                        </div>
                        """, unsafe_allow_html=True)
                        
                        create_metric_terminal("VEGA", f"{greeks['vega']:.4f}", "VOLATILITY_RISK")
                        create_metric_terminal("THETA", f"{greeks['theta']:.4f}", "TIME_DECAY")
                    
                    with col3:
                        st.markdown("""
                        <div class="data-block" data-label="INTEREST_RATE">
                        </div>
                        """, unsafe_allow_html=True)
                        
                        create_metric_terminal("RHO", f"{greeks['rho']:.4f}", "RATE_SENSITIVITY")
                        
                        # Risk assessment
                        total_risk = abs(greeks['delta']) + abs(greeks['vega'])/10 + abs(greeks['theta'])
                        
                        if total_risk > 0.8:
                            risk_level = "HIGH_RISK"
                            risk_color = "#ff0000"
                        elif total_risk > 0.4:
                            risk_level = "MODERATE_RISK"
                            risk_color = "#ffff00"
                        else:
                            risk_level = "LOW_RISK"
                            risk_color = "#00ff00"
                        
                        st.markdown(f"""
                        <div style="text-align: center; color: {risk_color}; font-weight: bold; font-family: 'VT323', monospace; font-size: 16px; margin-top: 20px;">
                            RISK_LEVEL: {risk_level}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Enhanced visualization
                    st.markdown("""
                    <div class="terminal-window">
                        <h4 style="color: #00ffff; text-align: center;">SENSITIVITY_ANALYSIS</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create price sensitivity chart
                    spot_range = np.linspace(S*0.8, S*1.2, 50)
                    deltas, prices = [], []
                    
                    for spot_test in spot_range:
                        test_greeks = all_greeks(spot_test, K, T, r, iv, option['optionType'])
                        test_price = black_scholes_price(spot_test, K, T, r, iv, option['optionType'])
                        deltas.append(test_greeks['delta'])
                        prices.append(test_price)
                    
                    fig = go.Figure()
                    
                    # Option price line
                    fig.add_trace(go.Scatter(
                        x=spot_range, y=prices, 
                        name='OPTION_PRICE',
                        line=dict(color='#00ff00', width=2)
                    ))
                    
                    # Delta line
                    fig.add_trace(go.Scatter(
                        x=spot_range, y=deltas,
                        name='DELTA',
                        line=dict(color='#00ffff', width=2),
                        yaxis='y2'
                    ))
                    
                    # Current position
                    fig.add_trace(go.Scatter(
                        x=[S], y=[black_scholes_price(S, K, T, r, iv, option['optionType'])],
                        mode='markers',
                        name='CURRENT_POSITION',
                        marker=dict(color='#ffff00', size=12, symbol='diamond')
                    ))
                    
                    fig.update_layout(
                        title=dict(text="SENSITIVITY_MATRIX", font=dict(color='#00ffff', family='VT323', size=16)),
                        xaxis=dict(title="UNDERLYING_PRICE", color='#00ff00', gridcolor='#003300'),
                        yaxis=dict(title="OPTION_PRICE", color='#00ff00', gridcolor='#003300'),
                        yaxis2=dict(title="DELTA", overlaying='y', side='right', color='#00ffff'),
                        plot_bgcolor='#000000',
                        paper_bgcolor='#000000',
                        font=dict(color='#00ff00', family='Source Code Pro'),
                        showlegend=True,
                        legend=dict(font=dict(color='#00ff00'))
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                except Exception as e:
                    create_info_box("CALCULATION_ERROR", f"Greeks calculation failed: {str(e)}", "error")
            
            else:
                create_info_box("WARNING", "Calculate IMPLIED_VOLATILITY first to display Greeks matrix", "warning")
        
        with tab4:
            st.markdown("""
            <div class="terminal-window">
                <h3 style="color: #00ffff; font-family: 'VT323', monospace; text-align: center;">
                    ═══ RISK_ASSESSMENT_PROTOCOL ═══
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            if 'calculated_iv' in st.session_state:
                # Risk analysis content would go here
                create_info_box(
                    "RISK_MATRIX",
                    """
                    <strong>POSITION_ANALYSIS:</strong><br>
                    • DIRECTIONAL_RISK: Measured by Delta exposure<br>
                    • VOLATILITY_RISK: Measured by Vega exposure<br>
                    • TIME_DECAY_RISK: Measured by Theta burn rate<br>
                    • LIQUIDITY_RISK: Measured by bid-ask spread<br><br>
                    <strong>RECOMMENDED_ACTIONS:</strong><br>
                    • Monitor Greeks daily for position changes<br>
                    • Set stop-loss at 50% of premium paid<br>
                    • Consider profit-taking at 100% gain<br>
                    • Watch for volatility expansion events
                    """,
                    "warning"
                )
            else:
                create_info_box("SYSTEM_REQUIREMENT", "Complete VOLATILITY_ANALYSIS to access risk assessment", "info")
    
    else:
        # Welcome screen
        st.markdown("""
        <div class="terminal-window scanlines">
            <h3 style="color: #00ffff; text-align: center; font-family: 'VT323', monospace;">
                ═══ SYSTEM_INITIALIZATION_COMPLETE ═══
            </h3>
            <div style="color: #00ff00; font-family: 'Source Code Pro', monospace; margin: 20px 0;">
                ► SELECT TARGET_SYMBOL in control interface<br>
                ► EXECUTE DATA_RETRIEVAL protocol<br>
                ► CONFIGURE CONTRACT_PARAMETERS<br>
                ► INITIATE ANALYSIS_SEQUENCE
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        create_info_box(
            "QUICK_START",
            """
            <strong>STEP_1:</strong> Enter stock ticker (AAPL, MSFT, TSLA recommended)<br>
            <strong>STEP_2:</strong> Click INITIATE_DATA_RETRIEVAL button<br>
            <strong>STEP_3:</strong> Select contract type (CALL/PUT)<br>
            <strong>STEP_4:</strong> Choose expiration date and strike price<br>
            <strong>STEP_5:</strong> Analyze data in terminal tabs
            """,
            "success"
        )


if __name__ == "__main__":
    main()
    """Apply modern glassmorphism styling with professional appearance."""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main App Styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Title Styling */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 3.5rem;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(31, 38, 135, 0.3);
    }
    
    /* Info Icons */
    .info-icon {
        display: inline-block;
        width: 20px;
        height: 20px;
        background: linear-gradient(45deg, #4ecdc4, #44a08d);
        border-radius: 50%;
        text-align: center;
        line-height: 20px;
        color: white;
        font-size: 12px;
        font-weight: bold;
        margin-left: 5px;
        cursor: help;
    }
    
    /* Educational Panels */
    .education-panel {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border-left: 4px solid #4ecdc4;
        padding: 20px;
        margin: 15px 0;
    }
    
    .tip-box {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(139, 195, 74, 0.1));
        border-radius: 12px;
        border: 1px solid rgba(76, 175, 80, 0.3);
        padding: 15px;
        margin: 10px 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), rgba(255, 193, 7, 0.1));
        border-radius: 12px;
        border: 1px solid rgba(255, 152, 0, 0.3);
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: rgba(255, 255, 255, 0.8);
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #4ecdc4, #44a08d);
        color: white;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(45deg, #4ecdc4, #44a08d);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
    }
    
    /* Plotly Charts */
    .js-plotly-plot {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
    }
    
    /* Success/Error Messages */
    .stAlert {
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    
    /* Remove Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #4ecdc4, #44a08d);
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


def show_info_tooltip(text, explanation):
    """Create an info icon with detailed explanation tooltip."""
    return f"""
    <span style="position: relative; display: inline-block;">
        {text}
        <span class="info-icon" title="{explanation}">i</span>
    </span>
    """


def create_educational_section(title, content, icon="📚"):
    """Create a beautiful educational section with glassmorphism styling."""
    st.markdown(f"""
    <div class="education-panel">
        <h3 style="color: #4ecdc4; margin-bottom: 15px;">
            {icon} {title}
        </h3>
        <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_beginner_guide():
    """Comprehensive beginner's guide to options trading."""
    st.markdown("""
    <div class="glass-card">
        <h2 style="color: #4ecdc4; text-align: center; margin-bottom: 25px;">
            🎓 Options Trading Guide for Beginners
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # What are Options?
    create_educational_section(
        "What are Options?",
        """
        <strong>Options</strong> are financial contracts that give you the <em>right</em> (but not obligation) 
        to buy or sell a stock at a specific price before a certain date.
        <br><br>
        <strong>📞 Call Options:</strong> Give you the right to <em>buy</em> a stock at a fixed price<br>
        <strong>📉 Put Options:</strong> Give you the right to <em>sell</em> a stock at a fixed price
        <br><br>
        Think of it like a reservation: you pay a small fee to reserve the right to buy/sell, 
        but you don't have to use it if you don't want to.
        """,
        "🎯"
    )
    
    # Key Terms
    create_educational_section(
        "Essential Terms You Need to Know",
        """
        <strong>🎯 Strike Price:</strong> The fixed price at which you can buy/sell the stock<br>
        <strong>📅 Expiration Date:</strong> The last day you can use your option<br>
        <strong>💰 Premium:</strong> The price you pay to buy the option<br>
        <strong>📊 Implied Volatility (IV):</strong> Market's expectation of how much the stock will move<br>
        <strong>🔢 Volume:</strong> How many contracts traded today<br>
        <strong>🏦 Open Interest:</strong> Total number of contracts that exist
        """,
        "📝"
    )
    
    # Market Data Explained
    create_educational_section(
        "Understanding Market Data",
        """
        <strong>💵 Bid Price:</strong> Highest price someone is willing to pay for your option<br>
        <strong>💸 Ask Price:</strong> Lowest price someone is willing to sell the option for<br>
        <strong>🎯 Mid Price:</strong> Average of bid and ask - often the "fair" price<br>
        <strong>📏 Bid-Ask Spread:</strong> Difference between bid and ask (smaller = more liquid)<br>
        <strong>📈 Last Price:</strong> Price of the most recent trade
        """,
        "💹"
    )
    
    # Greeks Simplified
    create_educational_section(
        "The Greeks - Your Risk Measures",
        """
        <strong>δ Delta:</strong> How much the option price changes when stock moves $1<br>
        <strong>γ Gamma:</strong> How much Delta changes when stock moves $1<br>
        <strong>ν Vega:</strong> How much option price changes when volatility changes 1%<br>
        <strong>θ Theta:</strong> How much value you lose each day (time decay)<br>
        <strong>ρ Rho:</strong> How much option price changes when interest rates change 1%
        """,
        "🧮"
    )
    
    # Where to Trade
    create_educational_section(
        "Popular Options Trading Platforms",
        """
        <strong>🏆 Beginner-Friendly:</strong><br>
        • <strong>Robinhood:</strong> Commission-free, simple interface<br>
        • <strong>E*TRADE:</strong> Great educational resources<br>
        • <strong>TD Ameritrade (thinkorswim):</strong> Professional tools<br>
        <br>
        <strong>⚠️ Important:</strong> Options trading requires approval from your broker. 
        Start with paper trading to practice without real money!
        """,
        "🏪"
    )


def create_metric_with_tooltip(label, value, tooltip, delta=None):
    """Create a metric with an informational tooltip."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(label, value, delta)
    with col2:
        st.markdown(f'<span title="{tooltip}" style="cursor: help;">ℹ️</span>', 
                   unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Professional IV Calculator",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply retro terminal styling
    apply_retro_terminal_css()
    
    # Main title with glassmorphism effect
    st.markdown("""
    <div class="main-title">📊 Professional IV Calculator</div>
    <div class="subtitle">Advanced Options Analysis with Educational Guides</div>
    """, unsafe_allow_html=True)
    
    # Beginner's Guide Toggle
    if st.button("🎓 Show Beginner's Guide", help="Click to learn about options trading basics"):
        st.session_state['show_guide'] = not st.session_state.get('show_guide', False)
    
    if st.session_state.get('show_guide', False):
        show_beginner_guide()
        st.markdown("---")
    
    # Sidebar for inputs
    with st.sidebar:
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center;">Option Selection</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Ticker input with help
        ticker = st.text_input(
            "Stock Ticker", 
            value="AAPL", 
            help="Enter a stock symbol (e.g., AAPL, MSFT, TSLA). This is the underlying stock for the options."
        ).upper()
        
        st.markdown("""
        <div class="tip-box">
            💡 <strong>Tip:</strong> Popular options stocks include AAPL, SPY, TSLA, NVDA, and QQQ. 
            These typically have high liquidity and tight bid-ask spreads.
        </div>
        """, unsafe_allow_html=True)
        
        # Fetch data button with enhanced styling
        if st.button("🔄 Fetch Options Data", help="Get real-time options data from Yahoo Finance"):
            if ticker:
                with st.spinner("Fetching real-time market data..."):
                    try:
                        fetcher = OptionsDataFetcher()
                        
                        # Get stock info
                        stock_info = fetcher.get_stock_info(ticker)
                        st.session_state['stock_info'] = stock_info
                        
                        # Get options chain
                        options_df = fetcher.get_options_chain(ticker, max_expiries=8)
                        st.session_state['options_df'] = options_df
                        
                        st.success(f"✅ Loaded {len(options_df)} options for {ticker}")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.markdown("""
                        <div class="warning-box">
                            ⚠️ <strong>Common Issues:</strong><br>
                            • Invalid ticker symbol<br>
                            • Market is closed<br>
                            • No options available for this stock<br>
                            • Network connectivity issues
                        </div>
                        """, unsafe_allow_html=True)
        
        # Display stock info with enhanced styling
        if 'stock_info' in st.session_state:
            info = st.session_state['stock_info']
            
            st.markdown(f"""
            <div class="glass-card">
                <h3 style="color: #4ecdc4;">{info['symbol']} - {info['company_name']}</h3>
                <p style="color: rgba(255,255,255,0.7);">{info.get('sector', 'Unknown Sector')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                create_metric_with_tooltip(
                    "Current Price", 
                    f"${info['current_price']:.2f}",
                    "The latest trading price of the stock in the market"
                )
                create_metric_with_tooltip(
                    "Volume", 
                    f"{info['volume']:,}",
                    "Number of shares traded today. Higher volume indicates more interest."
                )
            
            with col2:
                change_color = "normal" if info['change'] >= 0 else "inverse"
                create_metric_with_tooltip(
                    "Daily Change", 
                    f"${info['change']:.2f}",
                    "Price change from previous close. Green = up, Red = down",
                    f"{info['change_percent']:.2f}%"
                )
                if info['beta']:
                    create_metric_with_tooltip(
                        "Beta", 
                        f"{info['beta']:.2f}",
                        "Measures stock volatility vs market. >1 = more volatile, <1 = less volatile"
                    )
        
        # Option selection interface
        if 'options_df' in st.session_state:
            st.markdown("""
            <div class="glass-card">
                <h3 style="color: #4ecdc4;">Select Option Contract</h3>
            </div>
            """, unsafe_allow_html=True)
            
            df = st.session_state['options_df']
            
            # Option type selection
            option_type = st.selectbox(
                "Option Type", 
                ['call', 'put'],
                help="Call = right to buy, Put = right to sell"
            )
            
            if option_type == 'call':
                st.markdown("""
                <div class="tip-box">
                    📞 <strong>Call Option:</strong> You're betting the stock will go UP. 
                    Profitable when stock price > strike price.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="tip-box">
                    📉 <strong>Put Option:</strong> You're betting the stock will go DOWN. 
                    Profitable when stock price < strike price.
                </div>
                """, unsafe_allow_html=True)
            
            # Filter and select options
            filtered_df = df[df['optionType'] == option_type].copy()
            
            # Expiration date
            expiry_dates = sorted(filtered_df['expiration'].unique())
            selected_expiry = st.selectbox(
                "Expiration Date", 
                expiry_dates,
                help="The last day you can exercise your option. Closer dates = less time value."
            )
            
            # Filter by expiry
            expiry_df = filtered_df[filtered_df['expiration'] == selected_expiry].copy()
            
            # Show days to expiry
            days_to_expiry = expiry_df.iloc[0]['daysToExpiry']
            st.markdown(f"""
            <div style="text-align: center; color: #4ecdc4; font-weight: bold;">
                ⏰ {days_to_expiry} days until expiration
            </div>
            """, unsafe_allow_html=True)
            
            # Strike price selection
            strikes = sorted(expiry_df['strike'].unique())
            current_price = st.session_state['stock_info']['current_price']
            
            # Find closest to current price for default
            closest_strike_idx = np.argmin(np.abs(np.array(strikes) - current_price))
            
            selected_strike = st.selectbox(
                "Strike Price", 
                strikes,
                index=closest_strike_idx,
                help="The price at which you can buy/sell. Choose based on your market outlook."
            )
            
            # Show moneyness
            moneyness = (current_price - selected_strike) / current_price * 100
            if option_type == 'call':
                if moneyness > 2:
                    money_status = "🟢 ITM (In-The-Money)"
                    money_help = "Profitable if exercised now"
                elif moneyness < -2:
                    money_status = "🔴 OTM (Out-of-The-Money)" 
                    money_help = "Not profitable if exercised now"
                else:
                    money_status = "🟡 ATM (At-The-Money)"
                    money_help = "Very close to current stock price"
            else:  # put
                if moneyness < -2:
                    money_status = "🟢 ITM (In-The-Money)"
                    money_help = "Profitable if exercised now"
                elif moneyness > 2:
                    money_status = "🔴 OTM (Out-of-The-Money)"
                    money_help = "Not profitable if exercised now"
                else:
                    money_status = "🟡 ATM (At-The-Money)"
                    money_help = "Very close to current stock price"
            
            st.markdown(f"""
            <div class="tip-box">
                <strong>{money_status}</strong><br>
                {money_help}
            </div>
            """, unsafe_allow_html=True)
            
            # Get selected option
            selected_option = expiry_df[expiry_df['strike'] == selected_strike].iloc[0]
            st.session_state['selected_option'] = selected_option
    
    # Main content area with enhanced tabs
    if 'selected_option' in st.session_state and 'stock_info' in st.session_state:
        option = st.session_state['selected_option']
        stock_info = st.session_state['stock_info']
        
        # Enhanced tab interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Contract Details", 
            "🧮 IV Analysis", 
            "📊 Greeks Dashboard", 
            "📈 Sensitivity Lab",
            "🎯 Strategy Simulator"
        ])
        
        with tab1:
            st.markdown("""
            <div class="glass-card">
                <h2 style="color: #4ecdc4; text-align: center;">📋 Option Contract Details</h2>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div class="glass-card">
                    <h3 style="color: #4ecdc4;">Contract Information</h3>
                </div>
                """, unsafe_allow_html=True)
                
                create_metric_with_tooltip(
                    "Symbol", stock_info['symbol'],
                    "The ticker symbol of the underlying stock"
                )
                create_metric_with_tooltip(
                    "Type", option['optionType'].title(),
                    "Call = right to buy, Put = right to sell"
                )
                create_metric_with_tooltip(
                    "Strike Price", f"${option['strike']:.2f}",
                    "The fixed price at which you can exercise the option"
                )
                create_metric_with_tooltip(
                    "Expiration", option['expiration'],
                    "The last day you can exercise this option"
                )
                create_metric_with_tooltip(
                    "Days to Expiry", str(option['daysToExpiry']),
                    "Time remaining until expiration. More time = higher premium."
                )
            
            with col2:
                st.markdown("""
                <div class="glass-card">
                    <h3 style="color: #4ecdc4;">Market Data</h3>
                </div>
                """, unsafe_allow_html=True)
                
                create_metric_with_tooltip(
                    "Last Price", f"${option['lastPrice']:.3f}",
                    "Price of the most recent trade"
                )
                create_metric_with_tooltip(
                    "Bid", f"${option['bid']:.3f}",
                    "Highest price buyers are willing to pay"
                )
                create_metric_with_tooltip(
                    "Ask", f"${option['ask']:.3f}",
                    "Lowest price sellers are willing to accept"
                )
                create_metric_with_tooltip(
                    "Mid Price", f"${option['midPrice']:.3f}",
                    "Average of bid and ask - often the 'fair' price"
                )
                create_metric_with_tooltip(
                    "Spread", f"${option['bidAskSpread']:.3f}",
                    "Difference between bid and ask. Smaller = more liquid."
                )
            
            with col3:
                st.markdown("""
                <div class="glass-card">
                    <h3 style="color: #4ecdc4;">Trading Activity</h3>
                </div>
                """, unsafe_allow_html=True)
                
                create_metric_with_tooltip(
                    "Volume", f"{option['volume']:,}",
                    "Number of contracts traded today"
                )
                create_metric_with_tooltip(
                    "Open Interest", f"{option['openInterest']:,}",
                    "Total number of contracts outstanding"
                )
                
                # Liquidity assessment
                if option['volume'] > 100 and option['bidAskSpreadPct'] < 5:
                    liquidity = "🟢 High Liquidity"
                    liq_help = "Easy to buy/sell, tight spreads"
                elif option['volume'] > 20 and option['bidAskSpreadPct'] < 10:
                    liquidity = "🟡 Moderate Liquidity"
                    liq_help = "Reasonable trading activity"
                else:
                    liquidity = "🔴 Low Liquidity"
                    liq_help = "May be difficult to trade, wide spreads"
                
                st.markdown(f"""
                <div class="tip-box">
                    <strong>Liquidity:</strong> {liquidity}<br>
                    {liq_help}
                </div>
                """, unsafe_allow_html=True)
                
                if 'impliedVolatility' in option and option['impliedVolatility'] > 0:
                    create_metric_with_tooltip(
                        "Yahoo IV", f"{option['impliedVolatility']*100:.1f}%",
                        "Implied volatility from Yahoo Finance"
                    )
        
        with tab2:
            st.markdown("""
            <div class="glass-card">
                <h2 style="color: #4ecdc4; text-align: center;">🧮 Implied Volatility Analysis</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Educational section about IV
            create_educational_section(
                "What is Implied Volatility?",
                """
                <strong>Implied Volatility (IV)</strong> is the market's expectation of how much the stock will move. 
                It's like the market's "fear gauge" for this specific stock.
                <br><br>
                <strong>High IV (>30%):</strong> Market expects big moves, options are expensive<br>
                <strong>Low IV (<20%):</strong> Market expects small moves, options are cheaper<br>
                <strong>Average IV (20-30%):</strong> Normal market expectations
                """,
                "📈"
            )
            
            # Calculate IV using our engine
            try:
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05  # Risk-free rate assumption
                
                market_price = option['midPrice']
                
                if market_price > 0 and T > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("""
                        <div class="glass-card">
                            <h3 style="color: #4ecdc4;">IV Calculation Results</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Calculate IV using both methods
                        with st.spinner("Calculating implied volatility..."):
                            iv_newton = implied_volatility(market_price, S, K, T, r, option['optionType'], method='newton')
                            iv_brent = implied_volatility(market_price, S, K, T, r, option['optionType'], method='brent')
                        
                        if not np.isnan(iv_newton):
                            st.success(f"✅ Newton-Raphson IV: **{iv_newton*100:.2f}%**")
                        else:
                            st.warning("⚠️ Newton-Raphson failed to converge")
                        
                        if not np.isnan(iv_brent):
                            st.info(f"📊 Brent Method IV: **{iv_brent*100:.2f}%**")
                        else:
                            st.warning("⚠️ Brent method failed to converge")
                        
                        # Use best available IV
                        best_iv = iv_newton if not np.isnan(iv_newton) else iv_brent
                        
                        if not np.isnan(best_iv):
                            st.session_state['calculated_iv'] = best_iv
                            
                            # IV assessment
                            if best_iv > 0.4:
                                iv_assessment = "🔴 Very High - Expensive options"
                            elif best_iv > 0.3:
                                iv_assessment = "🟡 High - Elevated premiums"
                            elif best_iv > 0.2:
                                iv_assessment = "🟢 Normal - Fairly priced"
                            else:
                                iv_assessment = "🔵 Low - Cheap options"
                            
                            st.markdown(f"""
                            <div class="tip-box">
                                <strong>IV Assessment:</strong> {iv_assessment}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Value decomposition
                            decomp = option_value_decomposition(S, K, T, r, best_iv, option['optionType'])
                            
                            create_metric_with_tooltip(
                                "Theoretical Price", f"${decomp['total_value']:.3f}",
                                "Fair value based on Black-Scholes model"
                            )
                            create_metric_with_tooltip(
                                "Intrinsic Value", f"${decomp['intrinsic_value']:.3f}",
                                "Value if exercised immediately"
                            )
                            create_metric_with_tooltip(
                                "Time Value", f"${decomp['time_value']:.3f}",
                                "Premium for time until expiration"
                            )
                            
                            # Price comparison
                            price_diff = market_price - decomp['total_value']
                            if abs(price_diff) < 0.05:
                                price_status = "🟢 Fairly Valued"
                            elif price_diff > 0:
                                price_status = "🔴 Overvalued"
                            else:
                                price_status = "🟢 Undervalued"
                            
                            st.markdown(f"""
                            <div class="tip-box">
                                <strong>Market vs Theoretical:</strong> ${price_diff:.3f} ({price_diff/decomp['total_value']*100:.1f}%)<br>
                                <strong>Assessment:</strong> {price_status}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div class="glass-card">
                            <h3 style="color: #4ecdc4;">Volatility Smile Visualization</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if not np.isnan(best_iv):
                            # Create enhanced volatility smile
                            strikes_range = np.linspace(S*0.8, S*1.2, 20)
                            ivs_for_smile = []
                            
                            for strike_test in strikes_range:
                                try:
                                    theo_price = black_scholes_price(S, strike_test, T, r, best_iv, option['optionType'])
                                    if theo_price > 0.01:
                                        test_iv = implied_volatility(theo_price, S, strike_test, T, r, option['optionType'])
                                        ivs_for_smile.append(test_iv if not np.isnan(test_iv) else None)
                                    else:
                                        ivs_for_smile.append(None)
                                except:
                                    ivs_for_smile.append(None)
                            
                            # Enhanced plotting
                            fig = go.Figure()
                            
                            valid_data = [(s, iv) for s, iv in zip(strikes_range, ivs_for_smile) if iv is not None]
                            if valid_data:
                                strikes_valid, ivs_valid = zip(*valid_data)
                                
                                fig.add_trace(go.Scatter(
                                    x=strikes_valid,
                                    y=[iv*100 for iv in ivs_valid],
                                    mode='lines+markers',
                                    name='Theoretical IV Smile',
                                    line=dict(color='#4ecdc4', width=3),
                                    marker=dict(size=6, color='#44a08d')
                                ))
                            
                            # Highlight current stock price and selected strike
                            fig.add_vline(x=S, line_dash="dash", line_color="yellow", 
                                         annotation_text="Current Stock Price")
                            
                            fig.add_trace(go.Scatter(
                                x=[K],
                                y=[best_iv*100],
                                mode='markers',
                                name='Selected Option',
                                marker=dict(color='red', size=15, symbol='diamond')
                            ))
                            
                            fig.update_layout(
                                title="Theoretical Volatility Smile",
                                xaxis_title="Strike Price ($)",
                                yaxis_title="Implied Volatility (%)",
                                height=400,
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='white')
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.markdown("""
                            <div class="tip-box">
                                💡 <strong>Understanding the Smile:</strong><br>
                                The volatility "smile" shows how IV changes across different strikes. 
                                Options far from the current price often have higher IV.
                            </div>
                            """, unsafe_allow_html=True)
                
                else:
                    st.error("❌ Cannot calculate IV: Invalid price or expiry data")
                    
            except Exception as e:
                st.error(f"❌ IV calculation error: {str(e)}")
        
        # Continue with enhanced Greeks tab...
        with tab3:
            st.markdown("""
            <div class="glass-card">
                <h2 style="color: #4ecdc4; text-align: center;">📊 Greeks Risk Dashboard</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Greeks education
            create_educational_section(
                "Understanding the Greeks",
                """
                The <strong>Greeks</strong> measure how your option's price changes with different market conditions. 
                Think of them as your risk dashboard:
                <br><br>
                <strong>🔄 Delta:</strong> Speed of price change with stock movement<br>
                <strong>⚡ Gamma:</strong> Acceleration of Delta changes<br>
                <strong>📊 Vega:</strong> Sensitivity to volatility changes<br>
                <strong>⏰ Theta:</strong> Daily time decay (your enemy as a buyer)<br>
                <strong>📈 Rho:</strong> Interest rate sensitivity (usually minor)
                """,
                "🧮"
            )
            
            if 'calculated_iv' in st.session_state:
                iv = st.session_state['calculated_iv']
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05
                
                try:
                    greeks = all_greeks(S, K, T, r, iv, option['optionType'])
                    
                    # Enhanced Greeks display
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("""
                        <div class="glass-card">
                            <h3 style="color: #4ecdc4;">🔄 Delta & Gamma</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        delta_val = greeks['delta']
                        create_metric_with_tooltip(
                            "Delta", f"{delta_val:.4f}",
                            f"If stock moves $1, option price changes by ${abs(delta_val):.3f}"
                        )
                        
                        # Delta interpretation
                        if option['optionType'] == 'call':
                            if delta_val > 0.7:
                                delta_meaning = "🟢 High Delta - Acts like stock"
                            elif delta_val > 0.3:
                                delta_meaning = "🟡 Moderate Delta - Balanced exposure"
                            else:
                                delta_meaning = "🔴 Low Delta - Limited stock exposure"
                        else:
                            if delta_val < -0.7:
                                delta_meaning = "🟢 High Delta - Strong inverse correlation"
                            elif delta_val < -0.3:
                                delta_meaning = "🟡 Moderate Delta - Balanced exposure"
                            else:
                                delta_meaning = "🔴 Low Delta - Limited inverse exposure"
                        
                        st.markdown(f"""
                        <div class="tip-box">
                            {delta_meaning}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        create_metric_with_tooltip(
                            "Gamma", f"{greeks['gamma']:.6f}",
                            "How much Delta changes when stock moves $1"
                        )
                    
                    with col2:
                        st.markdown("""
                        <div class="glass-card">
                            <h3 style="color: #4ecdc4;">📊 Vega & Theta</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        create_metric_with_tooltip(
                            "Vega", f"{greeks['vega']:.4f}",
                            "Option price change for 1% volatility increase"
                        )
                        
                        # Vega impact
                        vega_impact = abs(greeks['vega']) * 5  # 5% vol change
                        st.markdown(f"""
                        <div class="tip-box">
                            💡 If volatility increases 5%, option price changes by ${vega_impact:.2f}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        theta_val = greeks['theta']
                        create_metric_with_tooltip(
                            "Theta", f"{theta_val:.4f}",
                            "Daily time decay - money lost each day"
                        )
                        
                        # Theta warning for buyers
                        if theta_val < 0:
                            theta_impact = abs(theta_val) * 7  # Weekly decay
                            st.markdown(f"""
                            <div class="warning-box">
                                ⚠️ <strong>Time Decay:</strong> You lose ${theta_impact:.2f} per week if nothing else changes!
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown("""
                        <div class="glass-card">
                            <h3 style="color: #4ecdc4;">📈 Rho & Summary</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        create_metric_with_tooltip(
                            "Rho", f"{greeks['rho']:.4f}",
                            "Price change for 1% interest rate increase"
                        )
                        
                        # Overall risk assessment
                        total_risk = abs(delta_val) + abs(greeks['vega'])/10 + abs(theta_val)
                        
                        if total_risk > 0.8:
                            risk_level = "🔴 High Risk"
                            risk_advice = "Very sensitive to market changes"
                        elif total_risk > 0.4:
                            risk_level = "🟡 Moderate Risk"
                            risk_advice = "Balanced risk/reward profile"
                        else:
                            risk_level = "🟢 Lower Risk"
                            risk_advice = "Less sensitive to market moves"
                        
                        st.markdown(f"""
                        <div class="tip-box">
                            <strong>Overall Risk:</strong> {risk_level}<br>
                            {risk_advice}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Enhanced Greeks visualization
                    st.markdown("""
                    <div class="glass-card">
                        <h3 style="color: #4ecdc4; text-align: center;">📈 Greeks Sensitivity Analysis</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create comprehensive sensitivity chart
                    spot_range = np.linspace(S*0.8, S*1.2, 50)
                    deltas, gammas, vegas, thetas = [], [], [], []
                    
                    for spot_test in spot_range:
                        test_greeks = all_greeks(spot_test, K, T, r, iv, option['optionType'])
                        deltas.append(test_greeks['delta'])
                        gammas.append(test_greeks['gamma'] * 100)  # Scale for visibility
                        vegas.append(test_greeks['vega'])
                        thetas.append(test_greeks['theta'])
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=spot_range, y=deltas, name='Delta',
                        line=dict(color='#4ecdc4', width=3)
                    ))
                    fig.add_trace(go.Scatter(
                        x=spot_range, y=gammas, name='Gamma (×100)',
                        line=dict(color='#ff6b6b', width=2)
                    ))
                    fig.add_trace(go.Scatter(
                        x=spot_range, y=vegas, name='Vega',
                        line=dict(color='#feca57', width=2)
                    ))
                    
                    fig.add_vline(x=S, line_dash="dash", line_color="white", 
                                 annotation_text="Current Price")
                    
                    fig.update_layout(
                        title="Greeks vs Stock Price Movement",
                        xaxis_title="Stock Price ($)",
                        yaxis_title="Greek Values",
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        legend=dict(bgcolor='rgba(255,255,255,0.1)')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Greeks calculation error: {str(e)}")
            
            else:
                st.warning("📊 Calculate IV first to display Greeks analysis")
        
        # Enhanced Sensitivity and Strategy tabs would continue here...
        # [Additional tabs implementation would follow the same pattern]
        
        with tab4:
            st.markdown("""
            <div class="glass-card">
                <h2 style="color: #4ecdc4; text-align: center;">📈 Sensitivity Laboratory</h2>
            </div>
            """, unsafe_allow_html=True)
            
            if 'calculated_iv' in st.session_state:
                # Implementation continues with enhanced styling...
                st.info("🔬 Advanced sensitivity analysis coming soon...")
            else:
                st.warning("Calculate IV first to use the sensitivity lab")
        
        with tab5:
            st.markdown("""
            <div class="glass-card">
                <h2 style="color: #4ecdc4; text-align: center;">🎯 Strategy Simulator</h2>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("🎮 Interactive strategy simulator coming soon...")
    
    else:
        # Enhanced welcome screen
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #4ecdc4; text-align: center;">👋 Welcome to the Professional IV Calculator</h2>
            <p style="text-align: center; color: rgba(255,255,255,0.8); font-size: 1.1em;">
                Your comprehensive tool for options analysis and education
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            create_educational_section(
                "🚀 Quick Start Guide",
                """
                <strong>1.</strong> Enter a stock ticker in the sidebar (try AAPL, MSFT, or TSLA)<br>
                <strong>2.</strong> Click "Fetch Options Data" to load real-time market data<br>
                <strong>3.</strong> Select an option contract using the dropdown menus<br>
                <strong>4.</strong> Explore the analysis tabs to understand your option<br>
                <strong>5.</strong> Use the educational tooltips (ℹ️) to learn as you go
                """,
                "🎯"
            )
        
        with col2:
            create_educational_section(
                "🌟 Professional Features",
                """
                <strong>✅ Real-time Data:</strong> Live options prices from Yahoo Finance<br>
                <strong>✅ Advanced IV:</strong> Newton-Raphson & Brent method calculations<br>
                <strong>✅ Complete Greeks:</strong> Delta, Gamma, Vega, Theta, Rho analysis<br>
                <strong>✅ Educational:</strong> Comprehensive guides and tooltips<br>
                <strong>✅ Modern UI:</strong> Glassmorphism design with intuitive navigation
                """,
                "⭐"
            )


if __name__ == "__main__":
    main()
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Option Selection")
        
        # Ticker input
        ticker = st.text_input("Stock Ticker", value="AAPL", help="Enter a valid stock ticker").upper()
        
        # Fetch stock data button
        if st.button("🔄 Fetch Options Data"):
            if ticker:
                with st.spinner("Fetching options data..."):
                    try:
                        fetcher = OptionsDataFetcher()
                        
                        # Get stock info
                        stock_info = fetcher.get_stock_info(ticker)
                        st.session_state['stock_info'] = stock_info
                        
                        # Get options chain
                        options_df = fetcher.get_options_chain(ticker, max_expiries=8)
                        st.session_state['options_df'] = options_df
                        
                        st.success(f"✅ Loaded {len(options_df)} options for {ticker}")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Display stock info if available
        if 'stock_info' in st.session_state:
            info = st.session_state['stock_info']
            st.subheader(f"{info['symbol']} - {info['company_name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Price", f"${info['current_price']:.2f}")
                st.metric("Volume", f"{info['volume']:,}")
            with col2:
                change_color = "normal" if info['change'] >= 0 else "inverse"
                st.metric("Change", f"${info['change']:.2f}", f"{info['change_percent']:.2f}%")
                if info['beta']:
                    st.metric("Beta", f"{info['beta']:.2f}")
        
        # Option selection (if data loaded)
        if 'options_df' in st.session_state:
            st.subheader("Select Option Contract")
            
            df = st.session_state['options_df']
            
            # Option type
            option_type = st.selectbox("Option Type", ['call', 'put'])
            
            # Filter by option type
            filtered_df = df[df['optionType'] == option_type].copy()
            
            # Expiration date
            expiry_dates = sorted(filtered_df['expiration'].unique())
            selected_expiry = st.selectbox("Expiration Date", expiry_dates)
            
            # Filter by expiry
            expiry_df = filtered_df[filtered_df['expiration'] == selected_expiry].copy()
            
            # Strike price
            strikes = sorted(expiry_df['strike'].unique())
            selected_strike = st.selectbox("Strike Price", strikes)
            
            # Get the selected option
            selected_option = expiry_df[expiry_df['strike'] == selected_strike].iloc[0]
            st.session_state['selected_option'] = selected_option
    
    # Main content area
    if 'selected_option' in st.session_state and 'stock_info' in st.session_state:
        option = st.session_state['selected_option']
        stock_info = st.session_state['stock_info']
        
        # Create tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Option Details", "🧮 IV Analysis", "📊 Greeks", "📈 Sensitivity"])
        
        with tab1:
            st.header("Option Contract Details")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Contract Info")
                st.write(f"**Symbol:** {stock_info['symbol']}")
                st.write(f"**Type:** {option['optionType'].title()}")
                st.write(f"**Strike:** ${option['strike']:.2f}")
                st.write(f"**Expiry:** {option['expiration']}")
                st.write(f"**Days to Expiry:** {option['daysToExpiry']}")
            
            with col2:
                st.subheader("Market Data")
                st.metric("Last Price", f"${option['lastPrice']:.3f}")
                st.metric("Bid", f"${option['bid']:.3f}")
                st.metric("Ask", f"${option['ask']:.3f}")
                st.metric("Mid Price", f"${option['midPrice']:.3f}")
                st.metric("Spread", f"${option['bidAskSpread']:.3f}")
            
            with col3:
                st.subheader("Volume & Interest")
                st.metric("Volume", f"{option['volume']:,}")
                st.metric("Open Interest", f"{option['openInterest']:,}")
                if 'impliedVolatility' in option and option['impliedVolatility'] > 0:
                    st.metric("Yahoo IV", f"{option['impliedVolatility']*100:.1f}%")
        
        with tab2:
            st.header("Implied Volatility Analysis")
            
            # Calculate IV using our engine
            try:
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05  # Assume 5% risk-free rate
                
                # Use mid price for IV calculation
                market_price = option['midPrice']
                
                if market_price > 0 and T > 0:
                    # Calculate IV using both methods
                    iv_newton = implied_volatility(market_price, S, K, T, r, option['optionType'], method='newton')
                    iv_brent = implied_volatility(market_price, S, K, T, r, option['optionType'], method='brent')
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("IV Calculation Results")
                        
                        if not np.isnan(iv_newton):
                            st.metric("Newton-Raphson IV", f"{iv_newton*100:.2f}%")
                        else:
                            st.warning("Newton-Raphson failed to converge")
                        
                        if not np.isnan(iv_brent):
                            st.metric("Brent Method IV", f"{iv_brent*100:.2f}%")
                        else:
                            st.warning("Brent method failed to converge")
                        
                        # Use best available IV for further analysis
                        best_iv = iv_newton if not np.isnan(iv_newton) else iv_brent
                        
                        if not np.isnan(best_iv):
                            st.session_state['calculated_iv'] = best_iv
                            
                            # Value decomposition
                            decomp = option_value_decomposition(S, K, T, r, best_iv, option['optionType'])
                            
                            st.subheader("Value Breakdown")
                            st.metric("Theoretical Price", f"${decomp['total_value']:.3f}")
                            st.metric("Intrinsic Value", f"${decomp['intrinsic_value']:.3f}")
                            st.metric("Time Value", f"${decomp['time_value']:.3f}")
                            
                            # Price comparison
                            price_diff = market_price - decomp['total_value']
                            st.metric("Market vs Theoretical", 
                                     f"${price_diff:.3f}",
                                     f"{price_diff/decomp['total_value']*100:.1f}%")
                    
                    with col2:
                        st.subheader("IV Convergence Visualization")
                        
                        if not np.isnan(best_iv):
                            # Create volatility smile visualization
                            strikes_range = np.linspace(S*0.8, S*1.2, 20)
                            ivs_for_smile = []
                            
                            for strike_test in strikes_range:
                                try:
                                    theo_price = black_scholes_price(S, strike_test, T, r, best_iv, option['optionType'])
                                    if theo_price > 0.01:  # Only calculate IV for meaningful prices
                                        test_iv = implied_volatility(theo_price, S, strike_test, T, r, option['optionType'])
                                        ivs_for_smile.append(test_iv if not np.isnan(test_iv) else None)
                                    else:
                                        ivs_for_smile.append(None)
                                except:
                                    ivs_for_smile.append(None)
                            
                            # Plot volatility smile
                            fig = go.Figure()
                            
                            valid_data = [(s, iv) for s, iv in zip(strikes_range, ivs_for_smile) if iv is not None]
                            if valid_data:
                                strikes_valid, ivs_valid = zip(*valid_data)
                                
                                fig.add_trace(go.Scatter(
                                    x=strikes_valid,
                                    y=[iv*100 for iv in ivs_valid],
                                    mode='lines+markers',
                                    name='Theoretical IV Smile',
                                    line=dict(color='blue')
                                ))
                            
                            # Highlight selected strike
                            fig.add_trace(go.Scatter(
                                x=[K],
                                y=[best_iv*100],
                                mode='markers',
                                name='Selected Option',
                                marker=dict(color='red', size=12)
                            ))
                            
                            fig.update_layout(
                                title="Theoretical Volatility Smile",
                                xaxis_title="Strike Price",
                                yaxis_title="Implied Volatility (%)",
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.warning("Cannot calculate IV: Invalid price or expiry data")
                    
            except Exception as e:
                st.error(f"IV calculation error: {str(e)}")
        
        with tab3:
            st.header("Greeks Analysis")
            
            if 'calculated_iv' in st.session_state:
                iv = st.session_state['calculated_iv']
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05
                
                try:
                    greeks = all_greeks(S, K, T, r, iv, option['optionType'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Risk Greeks")
                        st.metric("Delta", f"{greeks['delta']:.4f}", 
                                 help="Price sensitivity to $1 change in underlying")
                        st.metric("Gamma", f"{greeks['gamma']:.6f}",
                                 help="Delta sensitivity to $1 change in underlying") 
                        st.metric("Vega", f"{greeks['vega']:.4f}",
                                 help="Price sensitivity to 1% change in volatility")
                    
                    with col2:
                        st.subheader("Time & Rate Greeks")
                        st.metric("Theta", f"{greeks['theta']:.4f}",
                                 help="Price decay per day")
                        st.metric("Rho", f"{greeks['rho']:.4f}",
                                 help="Price sensitivity to 1% change in interest rate")
                    
                    # Greeks visualization
                    st.subheader("Greeks Sensitivity Chart")
                    
                    spot_range = np.linspace(S*0.8, S*1.2, 50)
                    deltas, gammas, vegas = [], [], []
                    
                    for spot_test in spot_range:
                        test_greeks = all_greeks(spot_test, K, T, r, iv, option['optionType'])
                        deltas.append(test_greeks['delta'])
                        gammas.append(test_greeks['gamma'])
                        vegas.append(test_greeks['vega'])
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(x=spot_range, y=deltas, name='Delta', line=dict(color='blue')))
                    fig.add_trace(go.Scatter(x=spot_range, y=gammas, name='Gamma', yaxis='y2', line=dict(color='red')))
                    
                    fig.add_vline(x=S, line_dash="dash", line_color="gray", 
                                 annotation_text="Current Price")
                    
                    fig.update_layout(
                        title="Delta and Gamma vs Spot Price",
                        xaxis_title="Spot Price",
                        yaxis_title="Delta",
                        yaxis2=dict(title="Gamma", overlaying="y", side="right"),
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Greeks calculation error: {str(e)}")
            
            else:
                st.warning("Calculate IV first to display Greeks")
        
        with tab4:
            st.header("Sensitivity Analysis")
            
            if 'calculated_iv' in st.session_state:
                S = stock_info['current_price']
                K = option['strike']
                T = option['timeToExpiry']
                r = 0.05
                iv = st.session_state['calculated_iv']
                
                # Interactive sensitivity controls
                col1, col2 = st.columns(2)
                
                with col1:
                    spot_change = st.slider("Spot Price Change (%)", -20, 20, 0, 1)
                    vol_change = st.slider("Volatility Change (%)", -50, 50, 0, 5)
                
                with col2:
                    time_decay_days = st.slider("Days Forward", 0, min(30, option['daysToExpiry']), 0)
                    rate_change = st.slider("Rate Change (%)", -2.0, 2.0, 0.0, 0.1)
                
                # Calculate scenario
                new_S = S * (1 + spot_change/100)
                new_iv = iv * (1 + vol_change/100)
                new_T = max(0.001, T - time_decay_days/365)
                new_r = r + rate_change/100
                
                try:
                    original_price = black_scholes_price(S, K, T, r, iv, option['optionType'])
                    scenario_price = black_scholes_price(new_S, K, new_T, new_r, new_iv, option['optionType'])
                    
                    price_change = scenario_price - original_price
                    price_change_pct = price_change / original_price * 100
                    
                    st.subheader("Scenario Analysis Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Original Price", f"${original_price:.3f}")
                        st.metric("Scenario Price", f"${scenario_price:.3f}")
                    
                    with col2:
                        st.metric("Price Change", f"${price_change:.3f}", f"{price_change_pct:.1f}%")
                        
                        # P&L calculation
                        contracts = st.number_input("Number of Contracts", min_value=1, value=1, step=1)
                        pnl = price_change * contracts * 100  # Options are per 100 shares
                        st.metric("P&L", f"${pnl:,.0f}")
                    
                    with col3:
                        st.write("**Scenario Parameters:**")
                        st.write(f"Spot: ${new_S:.2f} ({spot_change:+.1f}%)")
                        st.write(f"Vol: {new_iv*100:.1f}% ({vol_change:+}%)")
                        st.write(f"Days: -{time_decay_days}")
                        st.write(f"Rate: {new_r*100:.1f}% ({rate_change:+.1f}%)")
                    
                except Exception as e:
                    st.error(f"Scenario calculation error: {str(e)}")
            
            else:
                st.warning("Calculate IV first to perform sensitivity analysis")
    
    else:
        # Instructions for new users
        st.info("👈 Use the sidebar to fetch options data and select a contract to analyze")
        
        st.markdown("""
        ### How to Use This Calculator:
        
        1. **Enter a stock ticker** (e.g., AAPL, MSFT, TSLA)
        2. **Click "Fetch Options Data"** to load real-time options
        3. **Select an option contract** using the dropdown menus
        4. **Explore the analysis tabs:**
           - **Option Details**: Contract specifications and market data
           - **IV Analysis**: Implied volatility calculation and comparison
           - **Greeks**: Risk sensitivities (Delta, Gamma, Vega, Theta, Rho)
           - **Sensitivity**: Scenario analysis and P&L modeling
        
        ### Features:
        - ✅ Real-time options data from Yahoo Finance
        - ✅ Advanced Newton-Raphson implied volatility calculation  
        - ✅ Complete Greeks analysis with visualizations
        - ✅ Interactive sensitivity analysis and scenario modeling
        - ✅ Value decomposition (intrinsic vs time value)
        - ✅ Market vs theoretical price comparison
        """)


if __name__ == "__main__":
    main()

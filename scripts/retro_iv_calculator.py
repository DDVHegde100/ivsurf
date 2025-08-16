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

from utils.fetch_data import OptionsDataFetcher
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
    """Create ASCII art header for the terminal."""
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
        ► ACCESSING FINANCIAL_MAINFRAME...<br>
        ► CONNECTING TO MARKET_DATA_STREAM...<br>
        ► INITIALIZING OPTION_ANALYSIS_PROTOCOLS...<br>
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
                # Risk analysis content
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

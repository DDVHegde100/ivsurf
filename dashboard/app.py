import streamlit as st
import pandas as pd
from utils.fetch_data import get_options_chain
from core.black_scholes import implied_volatility
from core.interpolation import interpolate_surface
from visuals.plot_surface import plot_vol_surface
import numpy as np

st.title("📈 Volatility Surface Explorer")

ticker = st.text_input("Enter Ticker:", "AAPL")

if ticker:
    st.write(f"Fetching data for {ticker}...")
    df = get_options_chain(ticker)
    spot_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]

    st.write("Sample Options Data:", df.head())

    strikes, expiries, ivs = [], [], []
    r = 0.01
    for _, row in df.iterrows():
        T = (pd.to_datetime(row['expiration']) - pd.Timestamp.today()).days / 365
        if T <= 0: continue
        try:
            iv = implied_volatility(row['lastPrice'], spot_price, row['strike'], T, r, row['optionType'])
            if not np.isnan(iv):
                strikes.append(row['strike'])
                expiries.append(T)
                ivs.append(iv)
        except:
            continue

    if len(strikes) > 5:
        grid_x, grid_y, grid_z = interpolate_surface(np.array(strikes), np.array(expiries), np.array(ivs))
        fig = plot_vol_surface(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        st.plotly_chart(fig)
    else:
        st.warning("Not enough valid IV data to plot surface.")

import yfinance as yf
import pandas as pd

def get_options_chain(ticker):
    stock = yf.Ticker(ticker)
    expirations = stock.options
    options_data = []
    for exp in expirations[:3]:  # limit for speed
        opt_chain = stock.option_chain(exp)
        calls = opt_chain.calls.assign(optionType='call', expiration=exp)
        puts = opt_chain.puts.assign(optionType='put', expiration=exp)
        options_data.append(calls)
        options_data.append(puts)
    return pd.concat(options_data, ignore_index=True)

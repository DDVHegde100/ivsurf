import numpy as np
import scipy.stats as si

def black_scholes_price(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'call':
        return S * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)

def implied_volatility(price, S, K, T, r, option_type='call', tol=1e-6, max_iter=100):
    sigma = 0.2
    for i in range(max_iter):
        price_est = black_scholes_price(S, K, T, r, sigma, option_type)
        vega = (S * si.norm.pdf((np.log(S/K)+(r+0.5*sigma**2)*T)/(sigma*np.sqrt(T))) * np.sqrt(T))
        diff = price_est - price
        if abs(diff) < tol:
            return sigma
        sigma -= diff / vega
    return np.nan

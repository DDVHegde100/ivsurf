"""
Test cases for enhanced Black-Scholes implementation.

Comprehensive test suite covering pricing, Greeks, and implied volatility
with edge cases and vectorization validation.
"""

import pytest
import numpy as np
from core.black_scholes import black_scholes_price, implied_volatility, BlackScholesError, option_value_decomposition
from core.greeks import delta, gamma, vega, theta, rho, all_greeks


class TestBlackScholesPricing:
    """Test Black-Scholes pricing functionality."""
    
    def test_basic_call_pricing(self):
        """Test standard call option pricing."""
        price = black_scholes_price(100, 100, 0.25, 0.05, 0.2, 'call')
        assert 5.5 < price < 6.5  # Approximately 5.987
    
    def test_basic_put_pricing(self):
        """Test standard put option pricing.""" 
        price = black_scholes_price(100, 100, 0.25, 0.05, 0.2, 'put')
        assert 4.5 < price < 5.5  # Approximately 4.749
    
    def test_put_call_parity(self):
        """Test put-call parity relationship."""
        S, K, T, r, sigma = 100, 100, 0.25, 0.05, 0.2
        call_price = black_scholes_price(S, K, T, r, sigma, 'call')
        put_price = black_scholes_price(S, K, T, r, sigma, 'put')
        
        # C - P = S - K*e^(-rT)
        left_side = call_price - put_price
        right_side = S - K * np.exp(-r * T)
        
        assert abs(left_side - right_side) < 1e-10
    
    def test_vectorized_pricing(self):
        """Test vectorized calculations."""
        S = np.array([95, 100, 105])
        K = 100
        T = 0.25
        r = 0.05
        sigma = 0.2
        
        prices = black_scholes_price(S, K, T, r, sigma, 'call')
        assert len(prices) == 3
        assert all(prices > 0)
        assert prices[1] > prices[0]  # Higher spot = higher call price
        assert prices[2] > prices[1]
    
    def test_zero_time_expiry(self):
        """Test options at expiry (T=0)."""
        # ITM call at expiry should equal intrinsic value
        price = black_scholes_price(110, 100, 0, 0.05, 0.2, 'call')
        assert abs(price - 10.0) < 1e-10
        
        # OTM call at expiry should be worthless
        price = black_scholes_price(90, 100, 0, 0.05, 0.2, 'call')
        assert abs(price) < 1e-10


class TestGreeks:
    """Test Greeks calculations."""
    
    def test_delta_bounds(self):
        """Test Delta is within valid bounds."""
        # Call delta should be between 0 and 1
        call_delta = delta(100, 100, 0.25, 0.05, 0.2, 'call')
        assert 0 <= call_delta <= 1
        
        # Put delta should be between -1 and 0
        put_delta = delta(100, 100, 0.25, 0.05, 0.2, 'put')
        assert -1 <= put_delta <= 0
    
    def test_gamma_positive(self):
        """Test Gamma is always positive."""
        gamma_val = gamma(100, 100, 0.25, 0.05, 0.2)
        assert gamma_val > 0
    
    def test_vega_positive(self):
        """Test Vega is always positive."""
        vega_val = vega(100, 100, 0.25, 0.05, 0.2)
        assert vega_val > 0
    
    def test_theta_call_negative(self):
        """Test call Theta is typically negative (time decay)."""
        theta_val = theta(100, 100, 0.25, 0.05, 0.2, 'call')
        assert theta_val < 0  # Time decay
    
    def test_all_greeks_consistency(self):
        """Test all_greeks returns consistent values."""
        greeks = all_greeks(100, 100, 0.25, 0.05, 0.2, 'call')
        
        individual_delta = delta(100, 100, 0.25, 0.05, 0.2, 'call')
        assert abs(greeks['delta'] - individual_delta) < 1e-10


class TestImpliedVolatility:
    """Test implied volatility calculations."""
    
    def test_iv_round_trip(self):
        """Test IV calculation round-trip accuracy."""
        S, K, T, r, sigma = 100, 100, 0.25, 0.05, 0.2
        
        # Calculate theoretical price
        theo_price = black_scholes_price(S, K, T, r, sigma, 'call')
        
        # Back out implied vol
        implied_vol = implied_volatility(theo_price, S, K, T, r, 'call')
        
        # Should recover original volatility
        assert abs(implied_vol - sigma) < 1e-6
    
    def test_iv_vectorized(self):
        """Test vectorized implied volatility."""
        prices = np.array([2.5, 5.99, 10.5])
        S = np.array([95, 100, 105])
        K = 100
        T = 0.25
        r = 0.05
        
        ivs = implied_volatility(prices, S, K, T, r, 'call')
        assert len(ivs) == 3
        assert all(~np.isnan(ivs))  # Should all converge
        assert all(ivs > 0)


class TestInputValidation:
    """Test input validation and error handling."""
    
    def test_negative_stock_price(self):
        """Test negative stock price raises error."""
        with pytest.raises(BlackScholesError):
            black_scholes_price(-100, 100, 0.25, 0.05, 0.2)
    
    def test_negative_volatility(self):
        """Test negative volatility raises error.""" 
        with pytest.raises(BlackScholesError):
            black_scholes_price(100, 100, 0.25, 0.05, -0.2)
    
    def test_invalid_option_type(self):
        """Test invalid option type raises error."""
        with pytest.raises(BlackScholesError):
            black_scholes_price(100, 100, 0.25, 0.05, 0.2, 'invalid')


class TestValueDecomposition:
    """Test option value decomposition."""
    
    def test_itm_call_decomposition(self):
        """Test ITM call value decomposition."""
        decomp = option_value_decomposition(110, 100, 0.25, 0.05, 0.2, 'call')
        
        assert decomp['intrinsic_value'] == 10.0  # 110 - 100
        assert decomp['time_value'] > 0
        assert abs(decomp['total_value'] - decomp['intrinsic_value'] - decomp['time_value']) < 1e-10
    
    def test_otm_call_decomposition(self):
        """Test OTM call value decomposition."""
        decomp = option_value_decomposition(90, 100, 0.25, 0.05, 0.2, 'call')
        
        assert decomp['intrinsic_value'] == 0.0
        assert decomp['time_value'] > 0
        assert abs(decomp['total_value'] - decomp['time_value']) < 1e-10


def test_smoke():
    """Basic smoke test to ensure modules import correctly."""
    assert True


if __name__ == "__main__":
    # Run basic smoke tests
    test = TestBlackScholesPricing()
    test.test_basic_call_pricing()
    test.test_put_call_parity()
    
    print("✅ All basic tests passed!")

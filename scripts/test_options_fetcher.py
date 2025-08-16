#!/usr/bin/env python3
"""
Test script for options data fetcher and IV calculator.

This script demonstrates the enhanced options data fetching capabilities
and validates the IV calculation functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_data import OptionsDataFetcher, get_single_option_quote
from core.black_scholes import implied_volatility, black_scholes_price
from core.greeks import all_greeks
import pandas as pd


def test_options_fetcher():
    """Test the enhanced options data fetcher."""
    
    print("🧪 Testing Enhanced Options Data Fetcher")
    print("=" * 50)
    
    # Initialize fetcher
    fetcher = OptionsDataFetcher()
    
    # Test 1: Stock info
    print("📊 Test 1: Stock Information")
    print("-" * 30)
    
    try:
        ticker = "AAPL"
        stock_info = fetcher.get_stock_info(ticker)
        
        print(f"✅ Successfully fetched info for {stock_info['symbol']}")
        print(f"   Company: {stock_info['company_name']}")
        print(f"   Current Price: ${stock_info['current_price']:.2f}")
        print(f"   Change: ${stock_info['change']:.2f} ({stock_info['change_percent']:.1f}%)")
        print(f"   Volume: {stock_info['volume']:,}")
        if stock_info['sector']:
            print(f"   Sector: {stock_info['sector']}")
        
    except Exception as e:
        print(f"❌ Stock info test failed: {e}")
        return False
    
    # Test 2: Options chain
    print(f"\n📋 Test 2: Options Chain")
    print("-" * 30)
    
    try:
        options_df = fetcher.get_options_chain(ticker, max_expiries=3)
        
        print(f"✅ Successfully fetched {len(options_df)} option contracts")
        print(f"   Expiration dates: {sorted(options_df['expiration'].unique())}")
        print(f"   Strike range: ${options_df['strike'].min():.0f} - ${options_df['strike'].max():.0f}")
        print(f"   Call contracts: {len(options_df[options_df['optionType'] == 'call'])}")
        print(f"   Put contracts: {len(options_df[options_df['optionType'] == 'put'])}")
        
        # Show sample data
        print(f"\n   Sample contracts:")
        sample = options_df[['optionType', 'strike', 'expiration', 'lastPrice', 'volume']].head(3)
        for _, row in sample.iterrows():
            print(f"   {row['optionType'].upper()} ${row['strike']:.0f} {row['expiration']} @ ${row['lastPrice']:.2f} (vol: {row['volume']})")
        
    except Exception as e:
        print(f"❌ Options chain test failed: {e}")
        return False
    
    # Test 3: Single option analysis
    print(f"\n🎯 Test 3: Single Option Analysis")
    print("-" * 30)
    
    try:
        # Find an ATM call option
        current_price = stock_info['current_price']
        atm_options = options_df[
            (options_df['optionType'] == 'call') &
            (options_df['strike'] >= current_price * 0.95) &
            (options_df['strike'] <= current_price * 1.05) &
            (options_df['volume'] > 0)
        ].sort_values('daysToExpiry')
        
        if not atm_options.empty:
            option = atm_options.iloc[0]
            
            print(f"✅ Analyzing {option['optionType'].upper()} ${option['strike']:.0f} {option['expiration']}")
            print(f"   Market Price: ${option['lastPrice']:.3f} (Bid: ${option['bid']:.3f}, Ask: ${option['ask']:.3f})")
            print(f"   Volume: {option['volume']:,}, Open Interest: {option['openInterest']:,}")
            print(f"   Days to Expiry: {option['daysToExpiry']}")
            
            # Calculate IV using our engine
            S = current_price
            K = option['strike']
            T = option['timeToExpiry']
            r = 0.05
            market_price = option['midPrice']
            
            if market_price > 0 and T > 0:
                iv = implied_volatility(market_price, S, K, T, r, option['optionType'])
                
                if not pd.isna(iv):
                    print(f"   📈 Calculated IV: {iv*100:.1f}%")
                    
                    # Calculate theoretical price
                    theo_price = black_scholes_price(S, K, T, r, iv, option['optionType'])
                    print(f"   💰 Theoretical Price: ${theo_price:.3f}")
                    
                    # Calculate Greeks
                    greeks = all_greeks(S, K, T, r, iv, option['optionType'])
                    print(f"   📊 Greeks:")
                    print(f"      Delta: {greeks['delta']:.3f}")
                    print(f"      Gamma: {greeks['gamma']:.5f}")
                    print(f"      Vega:  {greeks['vega']:.3f}")
                    print(f"      Theta: {greeks['theta']:.3f}")
                    
                else:
                    print(f"   ⚠️  Could not calculate IV")
            else:
                print(f"   ⚠️  Invalid price or expiry data")
        
        else:
            print(f"   ⚠️  No suitable ATM options found")
    
    except Exception as e:
        print(f"❌ Single option analysis failed: {e}")
        return False
    
    # Test 4: Filtered options search
    print(f"\n🔍 Test 4: Filtered Options Search")
    print("-" * 30)
    
    try:
        # Search for high-volume calls expiring in 1-60 days
        high_vol_calls = fetcher.get_option_by_criteria(
            ticker, 
            option_type='call',
            days_to_expiry_range=(1, 60),
            min_volume=100
        )
        
        print(f"✅ Found {len(high_vol_calls)} high-volume calls")
        
        if not high_vol_calls.empty:
            # Show top 3 by volume
            top_volume = high_vol_calls.nlargest(3, 'volume')
            print(f"   Top 3 by volume:")
            for _, opt in top_volume.iterrows():
                print(f"   ${opt['strike']:.0f} {opt['expiration']} - Vol: {opt['volume']:,} @ ${opt['lastPrice']:.2f}")
        
    except Exception as e:
        print(f"❌ Filtered search test failed: {e}")
        return False
    
    print(f"\n🎉 All tests passed successfully!")
    print(f"\n💡 Next steps:")
    print(f"   • Launch IV Calculator: streamlit run scripts/simple_iv_calculator.py")
    print(f"   • Launch Main Dashboard: streamlit run dashboard/app.py") 
    print(f"   • View running apps at:")
    print(f"     - Simple IV Calculator: http://localhost:8502")
    print(f"     - Main Dashboard: http://localhost:8503")
    
    return True


if __name__ == "__main__":
    try:
        test_options_fetcher()
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

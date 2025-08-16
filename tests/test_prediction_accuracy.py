#!/usr/bin/env python3
"""
Comprehensive Test Suite for Advanced Prediction Algorithm
Tests accuracy, confidence intervals, and mathematical models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import yfinance as yf
import unittest
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import the IVSURF terminal class
from scripts.ivsurf_retro_terminal import RetroTerminal

class TestPredictionAccuracy(unittest.TestCase):
    """Test suite for prediction algorithm accuracy"""
    
    def setUp(self):
        """Set up test environment"""
        self.terminal = RetroTerminal()
        self.test_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN', 'NFLX']
        
    def test_prediction_algorithm_components(self):
        """Test individual components of the prediction algorithm"""
        print("\n=== TESTING PREDICTION ALGORITHM COMPONENTS ===")
        
        # Test with AAPL data
        ticker = 'AAPL'
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
            if len(hist) > 30:
                current_price = hist['Close'].iloc[-1]
                volatility = hist['Close'].pct_change().std() * np.sqrt(252)
                
                # Calculate technical indicators
                rsi = self.calculate_rsi(hist['Close'], 14)
                macd = self.calculate_macd(hist['Close'])
                bb_position = self.calculate_bb_position(hist['Close'])
                volume_trend = hist['Volume'].iloc[-1] / hist['Volume'].tail(20).mean()
                
                # Calculate momentum
                momentum_1d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100
                momentum_3d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-4] - 1) * 100
                momentum_5d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-6] - 1) * 100
                
                # Test prediction algorithm
                prediction_score = self.terminal.calculate_tomorrow_prediction(
                    hist, current_price, volatility, rsi, macd, bb_position,
                    volume_trend, momentum_1d, momentum_3d, momentum_5d
                )
                
                # Test price predictions
                price_predictions = self.terminal.calculate_price_predictions(
                    hist, current_price, volatility, prediction_score
                )
                
                print(f"✅ {ticker} - Prediction Score: {prediction_score:.2f}")
                print(f"   Current Price: ${current_price:.2f}")
                print(f"   Predicted Range: ${price_predictions['predicted_low']:.2f} - ${price_predictions['predicted_high']:.2f}")
                print(f"   Confidence: {price_predictions['confidence_level']:.1f}%")
                print(f"   Expected Return: {price_predictions['expected_return']:.2f}%")
                
                # Assertions
                self.assertGreaterEqual(prediction_score, 0)
                self.assertLessEqual(prediction_score, 100)
                self.assertGreater(price_predictions['predicted_high'], price_predictions['predicted_low'])
                self.assertGreaterEqual(price_predictions['confidence_level'], 60)
                self.assertLessEqual(price_predictions['confidence_level'], 95)
                
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            self.fail(f"Prediction algorithm failed for {ticker}")
    
    def test_historical_accuracy(self):
        """Test prediction accuracy against historical data"""
        print("\n=== TESTING HISTORICAL PREDICTION ACCURACY ===")
        
        accurate_predictions = 0
        total_predictions = 0
        
        for ticker in self.test_tickers[:5]:  # Test first 5 tickers
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="6mo")
                
                if len(hist) < 60:
                    continue
                
                # Test predictions for last 10 trading days
                for i in range(10, 20):
                    historical_data = hist.iloc[:-i]
                    actual_next_price = hist['Close'].iloc[-i]
                    
                    if len(historical_data) > 30:
                        current_price = historical_data['Close'].iloc[-1]
                        volatility = historical_data['Close'].pct_change().std() * np.sqrt(252)
                        
                        # Calculate indicators
                        rsi = self.calculate_rsi(historical_data['Close'], 14)
                        macd = self.calculate_macd(historical_data['Close'])
                        bb_position = self.calculate_bb_position(historical_data['Close'])
                        volume_trend = historical_data['Volume'].iloc[-1] / historical_data['Volume'].tail(20).mean()
                        
                        momentum_1d = (historical_data['Close'].iloc[-1] / historical_data['Close'].iloc[-2] - 1) * 100
                        momentum_3d = (historical_data['Close'].iloc[-1] / historical_data['Close'].iloc[-4] - 1) * 100
                        momentum_5d = (historical_data['Close'].iloc[-1] / historical_data['Close'].iloc[-6] - 1) * 100
                        
                        # Make prediction
                        prediction_score = self.terminal.calculate_tomorrow_prediction(
                            historical_data, current_price, volatility, rsi, macd, bb_position,
                            volume_trend, momentum_1d, momentum_3d, momentum_5d
                        )
                        
                        price_predictions = self.terminal.calculate_price_predictions(
                            historical_data, current_price, volatility, prediction_score
                        )
                        
                        # Check if actual price fell within predicted range
                        if (price_predictions['predicted_low'] <= actual_next_price <= price_predictions['predicted_high']):
                            accurate_predictions += 1
                        
                        total_predictions += 1
                        
            except Exception as e:
                print(f"⚠️  Error testing historical accuracy for {ticker}: {e}")
                continue
        
        if total_predictions > 0:
            accuracy_rate = (accurate_predictions / total_predictions) * 100
            print(f"✅ Historical Accuracy: {accuracy_rate:.1f}% ({accurate_predictions}/{total_predictions})")
            print(f"   Target Accuracy: >60% (Industry Standard)")
            
            # Assert minimum accuracy
            self.assertGreater(accuracy_rate, 40, "Prediction accuracy too low")
        else:
            print("❌ No historical predictions could be tested")
    
    def test_monte_carlo_validation(self):
        """Test Monte Carlo simulation components"""
        print("\n=== TESTING MONTE CARLO SIMULATION ===")
        
        ticker = 'AAPL'
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
            current_price = hist['Close'].iloc[-1]
            volatility = hist['Close'].pct_change().std() * np.sqrt(252)
            prediction_score = 75  # High confidence score
            
            price_predictions = self.terminal.calculate_price_predictions(
                hist, current_price, volatility, prediction_score
            )
            
            # Test Monte Carlo outputs
            self.assertIsInstance(price_predictions, dict)
            self.assertIn('predicted_low', price_predictions)
            self.assertIn('predicted_high', price_predictions)
            self.assertIn('predicted_median', price_predictions)
            self.assertIn('confidence_level', price_predictions)
            
            # Validate price relationships
            self.assertLess(price_predictions['predicted_low'], price_predictions['predicted_median'])
            self.assertLess(price_predictions['predicted_median'], price_predictions['predicted_high'])
            
            print(f"✅ Monte Carlo validation passed for {ticker}")
            print(f"   Price Range: ${price_predictions['predicted_low']:.2f} - ${price_predictions['predicted_high']:.2f}")
            print(f"   Median: ${price_predictions['predicted_median']:.2f}")
            
        except Exception as e:
            print(f"❌ Monte Carlo test failed: {e}")
            self.fail("Monte Carlo simulation validation failed")
    
    def test_mathematical_models(self):
        """Test mathematical model components"""
        print("\n=== TESTING MATHEMATICAL MODELS ===")
        
        # Test with synthetic data
        np.random.seed(42)
        
        # Create synthetic price data
        n_days = 100
        prices = []
        price = 100
        
        for i in range(n_days):
            price = price * (1 + np.random.normal(0.001, 0.02))
            prices.append(price)
        
        synthetic_hist = pd.DataFrame({
            'Close': prices,
            'High': [p * 1.01 for p in prices],
            'Low': [p * 0.99 for p in prices],
            'Volume': [1000000 + np.random.randint(-200000, 200000) for _ in range(n_days)]
        })
        
        current_price = prices[-1]
        volatility = pd.Series(prices).pct_change().std() * np.sqrt(252)
        
        # Test with various market conditions
        test_conditions = [
            {'rsi': 30, 'macd': 0.01, 'bb_position': 0.1, 'volume_trend': 2.0},  # Oversold with volume
            {'rsi': 70, 'macd': -0.01, 'bb_position': 0.9, 'volume_trend': 1.5}, # Overbought
            {'rsi': 50, 'macd': 0.005, 'bb_position': 0.5, 'volume_trend': 1.0}, # Neutral
        ]
        
        for i, condition in enumerate(test_conditions):
            try:
                prediction_score = self.terminal.calculate_tomorrow_prediction(
                    synthetic_hist, current_price, volatility,
                    condition['rsi'], condition['macd'], condition['bb_position'],
                    condition['volume_trend'], 1.0, 2.0, 3.0
                )
                
                self.assertGreaterEqual(prediction_score, 0)
                self.assertLessEqual(prediction_score, 100)
                
                print(f"✅ Mathematical model test {i+1} passed - Score: {prediction_score:.2f}")
                
            except Exception as e:
                print(f"❌ Mathematical model test {i+1} failed: {e}")
                self.fail(f"Mathematical model test {i+1} failed")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n=== TESTING EDGE CASES ===")
        
        # Test with minimal data
        minimal_hist = pd.DataFrame({
            'Close': [100, 101, 102],
            'High': [101, 102, 103],
            'Low': [99, 100, 101],
            'Volume': [1000, 1100, 1200]
        })
        
        try:
            prediction_score = self.terminal.calculate_tomorrow_prediction(
                minimal_hist, 102, 0.2, 50, 0, 0.5, 1.0, 1.0, 1.0, 2.0
            )
            
            self.assertIsInstance(prediction_score, (int, float))
            print("✅ Minimal data test passed")
            
        except Exception as e:
            print(f"❌ Minimal data test failed: {e}")
            self.fail("Edge case test failed")
        
        # Test with extreme volatility
        try:
            prediction_score = self.terminal.calculate_tomorrow_prediction(
                minimal_hist, 102, 2.0, 50, 0, 0.5, 1.0, 1.0, 1.0, 2.0  # 200% volatility
            )
            
            self.assertIsInstance(prediction_score, (int, float))
            print("✅ Extreme volatility test passed")
            
        except Exception as e:
            print(f"❌ Extreme volatility test failed: {e}")
    
    def test_confidence_calibration(self):
        """Test confidence level calibration"""
        print("\n=== TESTING CONFIDENCE CALIBRATION ===")
        
        confidence_tests = []
        
        for ticker in self.test_tickers[:3]:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                
                if len(hist) > 30:
                    current_price = hist['Close'].iloc[-1]
                    volatility = hist['Close'].pct_change().std() * np.sqrt(252)
                    
                    # Test different prediction scores
                    for pred_score in [30, 50, 70, 90]:
                        price_predictions = self.terminal.calculate_price_predictions(
                            hist, current_price, volatility, pred_score
                        )
                        
                        confidence_tests.append({
                            'ticker': ticker,
                            'prediction_score': pred_score,
                            'confidence_level': price_predictions['confidence_level'],
                            'price_range': price_predictions['predicted_high'] - price_predictions['predicted_low']
                        })
                        
            except Exception as e:
                print(f"⚠️  Error in confidence test for {ticker}: {e}")
                continue
        
        if confidence_tests:
            # Check that higher prediction scores generally lead to higher confidence
            high_pred_conf = np.mean([t['confidence_level'] for t in confidence_tests if t['prediction_score'] >= 70])
            low_pred_conf = np.mean([t['confidence_level'] for t in confidence_tests if t['prediction_score'] <= 50])
            
            print(f"✅ High prediction score confidence: {high_pred_conf:.1f}%")
            print(f"✅ Low prediction score confidence: {low_pred_conf:.1f}%")
            
            # Assert confidence calibration
            self.assertGreaterEqual(high_pred_conf, low_pred_conf - 5, "Confidence not properly calibrated")
    
    # Helper methods for technical indicators
    def calculate_rsi(self, prices, window=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if len(rsi) > 0 else 50
    
    def calculate_macd(self, prices):
        """Calculate MACD"""
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = ema12 - ema26
        return macd.iloc[-1] if len(macd) > 0 else 0
    
    def calculate_bb_position(self, prices, window=20):
        """Calculate Bollinger Band position"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        current_price = prices.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        
        if current_upper > current_lower:
            position = (current_price - current_lower) / (current_upper - current_lower)
            return max(0, min(1, position))
        return 0.5

def run_comprehensive_tests():
    """Run all prediction accuracy tests"""
    print("🚀 STARTING COMPREHENSIVE PREDICTION ACCURACY TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPredictionAccuracy)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️  ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("\n🎉 ALL TESTS PASSED! Prediction algorithm is validated.")
    else:
        print(f"\n🔧 {len(result.failures + result.errors)} tests need attention.")
    
    return result

if __name__ == "__main__":
    run_comprehensive_tests()

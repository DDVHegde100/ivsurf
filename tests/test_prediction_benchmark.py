#!/usr/bin/env python3
"""
Performance Benchmark Test for Enhanced Prediction Algorithm
Compares against simple baseline models and industry benchmarks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from scripts.ivsurf_retro_terminal import RetroTerminal

class PredictionBenchmark:
    """Benchmark testing for prediction algorithms"""
    
    def __init__(self):
        self.terminal = RetroTerminal()
        self.test_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN', 'NFLX', 'CRM', 'ADBE']
        
    def baseline_random_prediction(self, current_price, volatility):
        """Simple random walk baseline"""
        daily_return = np.random.normal(0, volatility/np.sqrt(252))
        predicted_price = current_price * (1 + daily_return)
        return {
            'predicted_median': predicted_price,
            'predicted_low': predicted_price * 0.98,
            'predicted_high': predicted_price * 1.02,
            'confidence_level': 50
        }
    
    def baseline_momentum_prediction(self, hist, current_price):
        """Simple momentum baseline"""
        if len(hist) < 5:
            return self.baseline_random_prediction(current_price, 0.2)
            
        momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1)
        predicted_price = current_price * (1 + momentum * 0.2)  # 20% momentum carry-forward
        
        return {
            'predicted_median': predicted_price,
            'predicted_low': predicted_price * 0.97,
            'predicted_high': predicted_price * 1.03,
            'confidence_level': 60
        }
    
    def baseline_mean_reversion_prediction(self, hist, current_price):
        """Simple mean reversion baseline"""
        if len(hist) < 20:
            return self.baseline_random_prediction(current_price, 0.2)
            
        sma20 = hist['Close'].tail(20).mean()
        deviation = (current_price - sma20) / sma20
        
        # Assume 10% mean reversion
        predicted_price = current_price - (deviation * current_price * 0.1)
        
        return {
            'predicted_median': predicted_price,
            'predicted_low': predicted_price * 0.96,
            'predicted_high': predicted_price * 1.04,
            'confidence_level': 55
        }
    
    def run_accuracy_benchmark(self, days_back=30):
        """Run accuracy benchmark across multiple stocks and time periods"""
        print("🎯 RUNNING PREDICTION ACCURACY BENCHMARK")
        print("=" * 50)
        
        results = {
            'advanced_algo': {'correct': 0, 'total': 0, 'avg_confidence': []},
            'random_baseline': {'correct': 0, 'total': 0, 'avg_confidence': []},
            'momentum_baseline': {'correct': 0, 'total': 0, 'avg_confidence': []},
            'mean_reversion_baseline': {'correct': 0, 'total': 0, 'avg_confidence': []}
        }
        
        for ticker in self.test_tickers:
            print(f"\n📈 Testing {ticker}...")
            
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="6mo")
                
                if len(hist) < 60:
                    print(f"   ⚠️  Insufficient data for {ticker}")
                    continue
                
                # Test last N days
                for i in range(5, min(days_back, len(hist)-30)):
                    try:
                        # Historical data up to test point
                        historical_data = hist.iloc[:-i]
                        actual_next_price = hist['Close'].iloc[-i]
                        
                        if len(historical_data) < 30:
                            continue
                        
                        current_price = historical_data['Close'].iloc[-1]
                        volatility = historical_data['Close'].pct_change().std() * np.sqrt(252)
                        
                        # === ADVANCED ALGORITHM ===
                        try:
                            # Calculate technical indicators
                            rsi = self.calculate_rsi(historical_data['Close'], 14)
                            macd = self.calculate_macd(historical_data['Close'])
                            bb_position = self.calculate_bb_position(historical_data['Close'])
                            volume_trend = historical_data['Volume'].iloc[-1] / historical_data['Volume'].tail(20).mean()
                            
                            momentum_1d = (historical_data['Close'].iloc[-1] / historical_data['Close'].iloc[-2] - 1) * 100
                            momentum_3d = (historical_data['Close'].iloc[-1] / historical_data['Close'].iloc[-4] - 1) * 100
                            momentum_5d = (historical_data['Close'].iloc[-1] / historical_data['Close'].iloc[-6] - 1) * 100
                            
                            prediction_score = self.terminal.calculate_tomorrow_gain_prediction(
                                historical_data, current_price, volatility, rsi, macd, bb_position,
                                volume_trend, momentum_1d, momentum_3d, momentum_5d
                            )
                            
                            advanced_pred = self.terminal.calculate_tomorrow_gain_potential(
                                historical_data, current_price, volatility, prediction_score
                            )
                            
                            # Check accuracy (price within conservative–aggressive target band)
                            if (advanced_pred['conservative_target'] <= actual_next_price <= advanced_pred['aggressive_target']):
                                results['advanced_algo']['correct'] += 1
                            results['advanced_algo']['total'] += 1
                            results['advanced_algo']['avg_confidence'].append(advanced_pred['confidence_level'])
                            
                        except Exception as e:
                            print(f"     ❌ Advanced algo error: {e}")
                            continue
                        
                        # === BASELINE ALGORITHMS ===
                        
                        # Random baseline
                        random_pred = self.baseline_random_prediction(current_price, volatility)
                        if (random_pred['predicted_low'] <= actual_next_price <= random_pred['predicted_high']):
                            results['random_baseline']['correct'] += 1
                        results['random_baseline']['total'] += 1
                        results['random_baseline']['avg_confidence'].append(random_pred['confidence_level'])
                        
                        # Momentum baseline
                        momentum_pred = self.baseline_momentum_prediction(historical_data, current_price)
                        if (momentum_pred['predicted_low'] <= actual_next_price <= momentum_pred['predicted_high']):
                            results['momentum_baseline']['correct'] += 1
                        results['momentum_baseline']['total'] += 1
                        results['momentum_baseline']['avg_confidence'].append(momentum_pred['confidence_level'])
                        
                        # Mean reversion baseline
                        mr_pred = self.baseline_mean_reversion_prediction(historical_data, current_price)
                        if (mr_pred['predicted_low'] <= actual_next_price <= mr_pred['predicted_high']):
                            results['mean_reversion_baseline']['correct'] += 1
                        results['mean_reversion_baseline']['total'] += 1
                        results['mean_reversion_baseline']['avg_confidence'].append(mr_pred['confidence_level'])
                        
                    except Exception as e:
                        print(f"     ⚠️  Error in day {i}: {e}")
                        continue
                        
            except Exception as e:
                print(f"   ❌ Error processing {ticker}: {e}")
                continue
        
        # Calculate and display results
        print("\n" + "=" * 50)
        print("📊 BENCHMARK RESULTS")
        print("=" * 50)
        
        for algo_name, data in results.items():
            if data['total'] > 0:
                accuracy = (data['correct'] / data['total']) * 100
                avg_confidence = np.mean(data['avg_confidence']) if data['avg_confidence'] else 0
                
                print(f"\n{algo_name.upper().replace('_', ' ')}:")
                print(f"   Accuracy: {accuracy:.1f}% ({data['correct']}/{data['total']})")
                print(f"   Avg Confidence: {avg_confidence:.1f}%")
                
                # Performance rating
                if accuracy > 65:
                    rating = "🏆 EXCELLENT"
                elif accuracy > 55:
                    rating = "🥈 GOOD"
                elif accuracy > 45:
                    rating = "🥉 FAIR"
                else:
                    rating = "❌ POOR"
                
                print(f"   Rating: {rating}")
        
        return results
    
    def run_performance_benchmark(self):
        """Benchmark computational performance"""
        print("\n⚡ RUNNING PERFORMANCE BENCHMARK")
        print("=" * 40)
        
        # Test with AAPL
        ticker = 'AAPL'
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        current_price = hist['Close'].iloc[-1]
        volatility = hist['Close'].pct_change().std() * np.sqrt(252)
        
        # Calculate indicators once
        rsi = self.calculate_rsi(hist['Close'], 14)
        macd = self.calculate_macd(hist['Close'])
        bb_position = self.calculate_bb_position(hist['Close'])
        volume_trend = hist['Volume'].iloc[-1] / hist['Volume'].tail(20).mean()
        
        momentum_1d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100
        momentum_3d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-4] - 1) * 100
        momentum_5d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-6] - 1) * 100
        
        # Benchmark prediction calculation
        n_iterations = 100
        start_time = time.time()
        
        for _ in range(n_iterations):
            prediction_score = self.terminal.calculate_tomorrow_gain_prediction(
                hist, current_price, volatility, rsi, macd, bb_position,
                volume_trend, momentum_1d, momentum_3d, momentum_5d
            )
            
            price_predictions = self.terminal.calculate_tomorrow_gain_potential(
                hist, current_price, volatility, prediction_score
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / n_iterations * 1000  # milliseconds
        
        print(f"⏱️  Average Prediction Time: {avg_time:.2f}ms")
        print(f"📊 Throughput: {1000/avg_time:.0f} predictions/second")
        
        # Performance rating
        if avg_time < 50:
            rating = "🚀 EXCELLENT"
        elif avg_time < 100:
            rating = "⚡ GOOD"
        elif avg_time < 200:
            rating = "⏳ FAIR"
        else:
            rating = "🐌 SLOW"
        
        print(f"🏆 Performance Rating: {rating}")
        
        return avg_time
    
    def run_stress_test(self):
        """Stress test with extreme market conditions"""
        print("\n🔥 RUNNING STRESS TEST")
        print("=" * 30)
        
        # Create extreme market scenarios
        scenarios = [
            {"name": "Market Crash", "volatility": 0.8, "momentum": -15, "rsi": 20},
            {"name": "Bull Run", "volatility": 0.4, "momentum": 10, "rsi": 80},
            {"name": "Low Volatility", "volatility": 0.05, "momentum": 0.5, "rsi": 50},
            {"name": "High Volatility", "volatility": 1.2, "momentum": 0, "rsi": 45},
            {"name": "Extreme RSI", "volatility": 0.3, "momentum": 2, "rsi": 95},
        ]
        
        # Create synthetic data for stress testing
        np.random.seed(42)
        n_days = 100
        base_prices = []
        price = 100
        
        for i in range(n_days):
            price = price * (1 + np.random.normal(0.001, 0.02))
            base_prices.append(price)
        
        synthetic_hist = pd.DataFrame({
            'Close': base_prices,
            'High': [p * 1.01 for p in base_prices],
            'Low': [p * 0.99 for p in base_prices],
            'Volume': [1000000 + np.random.randint(-200000, 200000) for _ in range(n_days)]
        })
        
        stress_results = []
        
        for scenario in scenarios:
            try:
                prediction_score = self.terminal.calculate_tomorrow_gain_prediction(
                    synthetic_hist, 100, scenario["volatility"], scenario["rsi"], 
                    0.001, 0.5, 1.5, scenario["momentum"], scenario["momentum"], scenario["momentum"]
                )
                
                price_predictions = self.terminal.calculate_tomorrow_gain_potential(
                    synthetic_hist, 100, scenario["volatility"], prediction_score
                )
                
                stress_results.append({
                    'scenario': scenario['name'],
                    'prediction_score': prediction_score,
                    'confidence': price_predictions['confidence_level'],
                    'price_range': price_predictions['predicted_high'] - price_predictions['predicted_low'],
                    'status': '✅ PASSED'
                })
                
                print(f"✅ {scenario['name']}: Score={prediction_score:.1f}, Confidence={price_predictions['confidence_level']:.1f}%")
                
            except Exception as e:
                stress_results.append({
                    'scenario': scenario['name'],
                    'status': f'❌ FAILED: {str(e)[:50]}...'
                })
                print(f"❌ {scenario['name']}: FAILED - {e}")
        
        # Summary
        passed = sum(1 for r in stress_results if '✅' in r['status'])
        total = len(stress_results)
        
        print(f"\n📊 Stress Test Results: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("🎉 ALL STRESS TESTS PASSED!")
        elif passed >= total * 0.8:
            print("🔧 Most stress tests passed - minor issues")
        else:
            print("⚠️  Multiple stress test failures - needs attention")
        
        return stress_results
    
    # Helper methods
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

def run_full_benchmark():
    """Run complete benchmark suite"""
    print("🚀 STARTING COMPREHENSIVE PREDICTION BENCHMARK")
    print("=" * 60)
    
    benchmark = PredictionBenchmark()
    
    # Run all benchmarks
    print("\n1️⃣  ACCURACY BENCHMARK")
    accuracy_results = benchmark.run_accuracy_benchmark()
    
    print("\n2️⃣  PERFORMANCE BENCHMARK")
    performance_time = benchmark.run_performance_benchmark()
    
    print("\n3️⃣  STRESS TEST")
    stress_results = benchmark.run_stress_test()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL BENCHMARK SUMMARY")
    print("=" * 60)
    
    # Check if advanced algorithm outperformed baselines
    if 'advanced_algo' in accuracy_results and accuracy_results['advanced_algo']['total'] > 0:
        advanced_accuracy = (accuracy_results['advanced_algo']['correct'] / accuracy_results['advanced_algo']['total']) * 100
        
        baseline_accuracies = []
        for baseline in ['random_baseline', 'momentum_baseline', 'mean_reversion_baseline']:
            if baseline in accuracy_results and accuracy_results[baseline]['total'] > 0:
                baseline_acc = (accuracy_results[baseline]['correct'] / accuracy_results[baseline]['total']) * 100
                baseline_accuracies.append(baseline_acc)
        
        if baseline_accuracies:
            best_baseline = max(baseline_accuracies)
            improvement = advanced_accuracy - best_baseline
            
            print(f"📈 Advanced Algorithm Accuracy: {advanced_accuracy:.1f}%")
            print(f"📊 Best Baseline Accuracy: {best_baseline:.1f}%")
            print(f"🎯 Improvement: {improvement:+.1f} percentage points")
            
            if improvement > 5:
                print("🏆 SIGNIFICANT IMPROVEMENT OVER BASELINES!")
            elif improvement > 0:
                print("✅ Outperformed baselines")
            else:
                print("⚠️  Did not outperform baselines - needs optimization")
    
    print(f"⚡ Average Prediction Time: {performance_time:.2f}ms")
    
    stress_passed = sum(1 for r in stress_results if '✅' in r['status'])
    print(f"🔥 Stress Tests Passed: {stress_passed}/{len(stress_results)}")
    
    # Overall grade
    overall_score = 0
    if advanced_accuracy > 60:
        overall_score += 40
    elif advanced_accuracy > 50:
        overall_score += 25
    
    if performance_time < 100:
        overall_score += 30
    elif performance_time < 200:
        overall_score += 20
    
    if stress_passed >= len(stress_results) * 0.8:
        overall_score += 30
    elif stress_passed >= len(stress_results) * 0.6:
        overall_score += 20
    
    print(f"\n🎯 OVERALL SCORE: {overall_score}/100")
    
    if overall_score >= 80:
        print("🏆 EXCELLENT - Production ready!")
    elif overall_score >= 60:
        print("✅ GOOD - Minor optimizations recommended")
    elif overall_score >= 40:
        print("🔧 FAIR - Significant improvements needed")
    else:
        print("❌ POOR - Major rework required")

if __name__ == "__main__":
    run_full_benchmark()

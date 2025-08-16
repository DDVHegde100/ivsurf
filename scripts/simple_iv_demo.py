#!/usr/bin/env python3
"""
Simple IV Solver Demo (Text-based output)

Demonstrates the Newton-Raphson implied volatility solver with text output.
Perfect for testing the core functionality without GUI dependencies.

Run: python scripts/simple_iv_demo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time

# Import our enhanced modules
from core.black_scholes import black_scholes_price, implied_volatility, BlackScholesError
from core.greeks import vega, all_greeks


def newton_raphson_detailed(target_price, S, K, T, r, option_type='call', 
                           initial_guess=0.2, tol=1e-8, max_iter=50, verbose=True):
    """
    Detailed Newton-Raphson IV solver with step-by-step output.
    
    This demonstrates the core algorithm that powers our enhanced IV calculation.
    """
    
    if verbose:
        print(f"\n🔍 Newton-Raphson IV Solver")
        print(f"Target Price: ${target_price:.6f}")
        print(f"Parameters: S=${S}, K=${K}, T={T:.4f}y, r={r:.1%}")
        print(f"Initial Guess: σ = {initial_guess:.4f}")
        print("-" * 60)
        print(f"{'Iter':<4} {'Sigma':<10} {'BS Price':<12} {'Error':<12} {'Vega':<10} {'Step':<10}")
        print("-" * 60)
    
    sigma = initial_guess
    convergence_path = []
    
    for i in range(max_iter):
        try:
            # Calculate Black-Scholes price at current sigma
            bs_price = black_scholes_price(S, K, T, r, sigma, option_type)
            
            # Calculate Vega (sensitivity to volatility)
            vega_val = vega(S, K, T, r, sigma) * 100  # Convert from per-1% to per-unit
            
            # Price error
            price_error = bs_price - target_price
            
            # Record step
            step = price_error / vega_val if vega_val > 1e-10 else 0
            convergence_path.append({
                'iteration': i,
                'sigma': sigma,
                'price': bs_price,
                'error': price_error,
                'vega': vega_val,
                'step': step
            })
            
            if verbose:
                print(f"{i:<4} {sigma:<10.6f} {bs_price:<12.6f} {price_error:<12.6f} {vega_val:<10.4f} {step:<10.6f}")
            
            # Check convergence
            if abs(price_error) < tol:
                if verbose:
                    print("-" * 60)
                    print(f"✅ CONVERGED in {i+1} iterations!")
                    print(f"Final IV: {sigma:.8f}")
                    print(f"Final Error: {abs(price_error):.2e}")
                
                return {
                    'iv': sigma,
                    'converged': True,
                    'iterations': i + 1,
                    'final_error': abs(price_error),
                    'path': convergence_path
                }
            
            # Newton-Raphson update
            if vega_val < 1e-10:
                if verbose:
                    print("⚠️  Vega too small, stopping")
                break
            
            sigma_new = sigma - step
            
            # Bounds checking
            sigma_new = max(0.001, min(5.0, sigma_new))
            
            sigma = sigma_new
            
        except Exception as e:
            if verbose:
                print(f"❌ Error in iteration {i}: {e}")
            break
    
    if verbose:
        print("-" * 60)
        print(f"❌ FAILED to converge after {max_iter} iterations")
        print(f"Final IV: {sigma:.8f}")
        print(f"Final Error: {abs(price_error) if 'price_error' in locals() else 'N/A'}")
    
    return {
        'iv': np.nan,
        'converged': False,
        'iterations': max_iter,
        'final_error': abs(price_error) if 'price_error' in locals() else np.inf,
        'path': convergence_path
    }


def demo_basic_iv():
    """Basic demonstration of IV solver."""
    
    print("=" * 70)
    print("🚀 IMPLIED VOLATILITY SOLVER DEMONSTRATION")
    print("=" * 70)
    
    # Test parameters - realistic option
    S = 100.0      # Stock price
    K = 100.0      # Strike price (ATM)
    T = 0.25       # 3 months to expiry
    r = 0.05       # 5% risk-free rate
    true_sigma = 0.20  # 20% true volatility
    option_type = 'call'
    
    print(f"📊 Test Setup:")
    print(f"   Stock Price (S): ${S}")
    print(f"   Strike Price (K): ${K}")
    print(f"   Time to Expiry (T): {T:.2f} years")
    print(f"   Risk-free Rate (r): {r:.1%}")
    print(f"   True Volatility: {true_sigma:.1%}")
    print(f"   Option Type: {option_type}")
    
    # Step 1: Calculate target price using true volatility
    target_price = black_scholes_price(S, K, T, r, true_sigma, option_type)
    print(f"   Target Option Price: ${target_price:.6f}")
    
    # Step 2: Solve for IV using our detailed Newton-Raphson
    print(f"\n🎯 Solving for Implied Volatility...")
    result = newton_raphson_detailed(
        target_price, S, K, T, r, option_type,
        initial_guess=0.15,  # Start with 15% (away from true 20%)
        tol=1e-8,
        verbose=True
    )
    
    # Step 3: Validation and analysis
    if result['converged']:
        solved_iv = result['iv']
        error_pct = abs(solved_iv - true_sigma) / true_sigma * 100
        
        print(f"\n📈 RESULTS ANALYSIS:")
        print(f"   Solved IV: {solved_iv:.8f} ({solved_iv:.4%})")
        print(f"   True IV: {true_sigma:.8f} ({true_sigma:.4%})")
        print(f"   Absolute Error: {abs(solved_iv - true_sigma):.2e}")
        print(f"   Relative Error: {error_pct:.6f}%")
        print(f"   Convergence: {result['iterations']} iterations")
        
        # Verify by pricing with solved IV
        verification_price = black_scholes_price(S, K, T, r, solved_iv, option_type)
        price_error = abs(verification_price - target_price)
        
        print(f"\n🔍 VERIFICATION:")
        print(f"   Target Price: ${target_price:.8f}")
        print(f"   Solved Price: ${verification_price:.8f}")
        print(f"   Price Error: ${price_error:.2e}")
        
        # Calculate Greeks at solved IV
        print(f"\n🧮 GREEKS AT SOLVED IV:")
        greeks = all_greeks(S, K, T, r, solved_iv, option_type)
        for greek_name, value in greeks.items():
            print(f"   {greek_name.capitalize()}: {value:.6f}")
        
    else:
        print(f"\n❌ Failed to converge!")
    
    return result


def demo_edge_cases():
    """Test IV solver on challenging scenarios."""
    
    print(f"\n" + "=" * 70)
    print("🧪 EDGE CASE TESTING")
    print("=" * 70)
    
    edge_cases = [
        {
            'name': 'Deep ITM Call',
            'params': {'S': 150, 'K': 100, 'T': 0.25, 'r': 0.05, 'sigma': 0.2},
            'option_type': 'call'
        },
        {
            'name': 'Deep OTM Call', 
            'params': {'S': 80, 'K': 120, 'T': 0.25, 'r': 0.05, 'sigma': 0.3},
            'option_type': 'call'
        },
        {
            'name': 'Short Expiry ATM',
            'params': {'S': 100, 'K': 100, 'T': 0.01, 'r': 0.05, 'sigma': 0.4},
            'option_type': 'call'
        },
        {
            'name': 'High Volatility',
            'params': {'S': 100, 'K': 100, 'T': 0.25, 'r': 0.05, 'sigma': 0.8},
            'option_type': 'call'
        },
        {
            'name': 'Low Volatility',
            'params': {'S': 100, 'K': 100, 'T': 0.25, 'r': 0.05, 'sigma': 0.05},
            'option_type': 'call'
        }
    ]
    
    results = []
    
    for case in edge_cases:
        print(f"\n🔬 Testing: {case['name']}")
        print("-" * 40)
        
        params = case['params']
        option_type = case['option_type']
        
        # Generate target price
        target_price = black_scholes_price(**params, option_type=option_type)
        
        print(f"Parameters: S=${params['S']}, K=${params['K']}, T={params['T']:.3f}, σ={params['sigma']:.1%}")
        print(f"Target Price: ${target_price:.6f}")
        
        # Solve using our method
        start_time = time.perf_counter()
        result = newton_raphson_detailed(
            target_price, params['S'], params['K'], params['T'], params['r'],
            option_type, initial_guess=0.2, tol=1e-6, verbose=False
        )
        solve_time = time.perf_counter() - start_time
        
        if result['converged']:
            accuracy = abs(result['iv'] - params['sigma'])
            print(f"✅ Success: IV={result['iv']:.6f}, Error={accuracy:.2e}, Time={solve_time*1000:.2f}ms")
            results.append({'case': case['name'], 'success': True, 'accuracy': accuracy, 'time': solve_time})
        else:
            print(f"❌ Failed: No convergence")
            results.append({'case': case['name'], 'success': False, 'accuracy': np.inf, 'time': solve_time})
    
    # Summary
    print(f"\n📊 EDGE CASE SUMMARY:")
    print("-" * 40)
    success_rate = sum(1 for r in results if r['success']) / len(results)
    avg_time = np.mean([r['time'] for r in results if r['success']])
    
    print(f"Success Rate: {success_rate:.1%}")
    print(f"Avg Time: {avg_time*1000:.2f}ms")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['case']}")


def demo_method_comparison():
    """Compare our detailed method with library methods."""
    
    print(f"\n" + "=" * 70)
    print("⚡ METHOD COMPARISON")
    print("=" * 70)
    
    # Standard test case
    S, K, T, r, true_sigma = 100, 100, 0.25, 0.05, 0.20
    target_price = black_scholes_price(S, K, T, r, true_sigma, 'call')
    
    print(f"Comparison test: S=${S}, K=${K}, T={T}, σ={true_sigma:.1%}")
    print(f"Target price: ${target_price:.6f}")
    print()
    
    methods_to_test = [
        ('Detailed Newton-Raphson', lambda: newton_raphson_detailed(target_price, S, K, T, r, verbose=False)),
        ('Library Newton-Raphson', lambda: {'iv': implied_volatility(target_price, S, K, T, r, method='newton'), 'converged': True}),
        ('Library Brent Method', lambda: {'iv': implied_volatility(target_price, S, K, T, r, method='brent'), 'converged': True})
    ]
    
    for method_name, method_func in methods_to_test:
        print(f"🔧 {method_name}:")
        
        try:
            start_time = time.perf_counter()
            result = method_func()
            end_time = time.perf_counter()
            
            if result['converged'] and not np.isnan(result['iv']):
                accuracy = abs(result['iv'] - true_sigma)
                print(f"   ✅ IV: {result['iv']:.8f}")
                print(f"   📏 Accuracy: {accuracy:.2e}")
                print(f"   ⏱️  Time: {(end_time - start_time)*1000:.3f}ms")
                if 'iterations' in result:
                    print(f"   🔄 Iterations: {result['iterations']}")
            else:
                print(f"   ❌ Failed to converge")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()


def main():
    """Run the complete IV solver demonstration."""
    
    try:
        # Basic demonstration
        demo_basic_iv()
        
        # Edge case testing
        demo_edge_cases()
        
        # Method comparison
        demo_method_comparison()
        
        print(f"\n" + "=" * 70)
        print("🎉 IV SOLVER DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("💡 Next Steps:")
        print("   • Run the full dashboard: streamlit run dashboard/app.py")
        print("   • Try the visual demo: python scripts/iv_solver_demo.py")
        print("   • Run tests: pytest tests/test_black_scholes.py")
        print()
        print("🔗 The IV solver is fully integrated with:")
        print("   • Black-Scholes pricing engine")
        print("   • Greeks calculations")
        print("   • Options chain analysis")
        print("   • Volatility surface modeling")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

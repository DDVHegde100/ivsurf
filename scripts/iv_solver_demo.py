#!/usr/bin/env python3
"""
Implied Volatility Solver Demo & Visualization

Interactive demonstration of Newton-Raphson implied volatility calculation
with convergence visualization, method comparisons, and performance benchmarks.

Run this file to see the IV solver in action:
    python scripts/iv_solver_demo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
from typing import List, Tuple, Dict
import warnings

from core.black_scholes import black_scholes_price, implied_volatility, BlackScholesError
from core.greeks import vega, all_greeks


class ImpliedVolatilitySolver:
    """
    Advanced implied volatility solver with detailed convergence tracking and analysis.
    
    Features:
    - Newton-Raphson with adaptive step sizing
    - Convergence path visualization
    - Multiple starting guess strategies
    - Performance benchmarking
    - Robust error handling
    """
    
    def __init__(self):
        self.convergence_history = []
        self.method_stats = {}
    
    def solve_with_tracking(
        self, 
        target_price: float,
        S: float, K: float, T: float, r: float,
        option_type: str = 'call',
        initial_guess: float = 0.2,
        tol: float = 1e-8,
        max_iter: int = 50,
        adaptive_step: bool = True
    ) -> Dict:
        """
        Solve for implied volatility with detailed convergence tracking.
        
        Returns:
            dict: Contains 'iv', 'converged', 'iterations', 'path', 'final_error'
        """
        
        # Initialize tracking
        self.convergence_history = []
        sigma = initial_guess
        
        for i in range(max_iter):
            # Calculate current price and vega
            try:
                current_price = black_scholes_price(S, K, T, r, sigma, option_type)
                vega_val = vega(S, K, T, r, sigma) * 100  # Convert from per-1% to per-unit
                
                price_error = current_price - target_price
                
                # Track convergence
                self.convergence_history.append({
                    'iteration': i,
                    'sigma': sigma,
                    'price': current_price,
                    'error': price_error,
                    'abs_error': abs(price_error),
                    'vega': vega_val
                })
                
                # Check convergence
                if abs(price_error) < tol:
                    return {
                        'iv': sigma,
                        'converged': True,
                        'iterations': i + 1,
                        'path': self.convergence_history.copy(),
                        'final_error': abs(price_error)
                    }
                
                # Newton-Raphson step with safeguards
                if vega_val < 1e-10:
                    break  # Avoid division by zero
                
                step = price_error / vega_val
                
                # Adaptive step sizing to improve convergence
                if adaptive_step and i > 0:
                    prev_error = self.convergence_history[-2]['abs_error']
                    current_error = abs(price_error)
                    
                    if current_error > prev_error:
                        # Error increased, reduce step size
                        step *= 0.5
                
                sigma_new = sigma - step
                
                # Clamp to reasonable bounds
                sigma_new = np.clip(sigma_new, 0.001, 5.0)
                
                sigma = sigma_new
                
            except Exception as e:
                warnings.warn(f"Error in iteration {i}: {e}")
                break
        
        # Failed to converge
        return {
            'iv': np.nan,
            'converged': False,
            'iterations': max_iter,
            'path': self.convergence_history.copy(),
            'final_error': abs(price_error) if 'price_error' in locals() else np.inf
        }
    
    def benchmark_methods(
        self, 
        target_price: float,
        S: float, K: float, T: float, r: float,
        option_type: str = 'call',
        num_trials: int = 100
    ) -> Dict:
        """Benchmark different IV calculation methods."""
        
        methods = {
            'newton_raphson': [],
            'library_newton': [],
            'library_brent': []
        }
        
        print(f"Benchmarking IV methods ({num_trials} trials)...")
        
        for trial in range(num_trials):
            # Add small random perturbation for realistic testing
            perturbed_price = target_price * (1 + np.random.normal(0, 0.001))
            
            # Method 1: Our detailed Newton-Raphson
            start_time = time.perf_counter()
            result = self.solve_with_tracking(perturbed_price, S, K, T, r, option_type)
            newton_time = time.perf_counter() - start_time
            methods['newton_raphson'].append({
                'time': newton_time,
                'converged': result['converged'],
                'iterations': result['iterations'],
                'iv': result['iv']
            })
            
            # Method 2: Library Newton-Raphson
            start_time = time.perf_counter()
            try:
                lib_iv_newton = implied_volatility(perturbed_price, S, K, T, r, option_type, method='newton')
                lib_newton_time = time.perf_counter() - start_time
                methods['library_newton'].append({
                    'time': lib_newton_time,
                    'converged': not np.isnan(lib_iv_newton),
                    'iv': lib_iv_newton
                })
            except:
                methods['library_newton'].append({
                    'time': np.inf,
                    'converged': False,
                    'iv': np.nan
                })
            
            # Method 3: Library Brent's method
            start_time = time.perf_counter()
            try:
                lib_iv_brent = implied_volatility(perturbed_price, S, K, T, r, option_type, method='brent')
                lib_brent_time = time.perf_counter() - start_time
                methods['library_brent'].append({
                    'time': lib_brent_time,
                    'converged': not np.isnan(lib_iv_brent),
                    'iv': lib_iv_brent
                })
            except:
                methods['library_brent'].append({
                    'time': np.inf,
                    'converged': False,
                    'iv': np.nan
                })
        
        # Calculate statistics
        stats = {}
        for method_name, results in methods.items():
            valid_results = [r for r in results if r['converged']]
            if valid_results:
                times = [r['time'] for r in valid_results]
                ivs = [r['iv'] for r in valid_results if not np.isnan(r['iv'])]
                
                stats[method_name] = {
                    'success_rate': len(valid_results) / len(results),
                    'avg_time': np.mean(times),
                    'std_time': np.std(times),
                    'avg_iv': np.mean(ivs) if ivs else np.nan,
                    'std_iv': np.std(ivs) if ivs else np.nan,
                    'avg_iterations': np.mean([r.get('iterations', 0) for r in valid_results])
                }
            else:
                stats[method_name] = {
                    'success_rate': 0,
                    'avg_time': np.inf,
                    'std_time': 0,
                    'avg_iv': np.nan,
                    'std_iv': 0,
                    'avg_iterations': 0
                }
        
        return stats


def visualize_convergence(solver_result: Dict, title: str = "IV Convergence"):
    """Create detailed convergence visualization."""
    
    if not solver_result['path']:
        print("No convergence path to visualize")
        return
    
    path_df = pd.DataFrame(solver_result['path'])
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f"{title} - {'Converged' if solver_result['converged'] else 'Failed'}", fontsize=16)
    
    # 1. Sigma convergence
    ax1.plot(path_df['iteration'], path_df['sigma'], 'b-o', markersize=4)
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Implied Volatility (σ)')
    ax1.set_title('Volatility Convergence')
    ax1.grid(True, alpha=0.3)
    
    if solver_result['converged']:
        ax1.axhline(y=solver_result['iv'], color='r', linestyle='--', alpha=0.7, label='Final IV')
        ax1.legend()
    
    # 2. Error reduction
    ax2.semilogy(path_df['iteration'], path_df['abs_error'], 'r-o', markersize=4)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Absolute Price Error (log scale)')
    ax2.set_title('Error Reduction')
    ax2.grid(True, alpha=0.3)
    
    # 3. Price convergence
    ax3.plot(path_df['iteration'], path_df['price'], 'g-o', markersize=4, label='BS Price')
    if 'target_price' in solver_result:
        ax3.axhline(y=solver_result['target_price'], color='r', linestyle='--', alpha=0.7, label='Target Price')
    ax3.set_xlabel('Iteration')
    ax3.set_ylabel('Option Price')
    ax3.set_title('Price Convergence')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Vega evolution
    ax4.plot(path_df['iteration'], path_df['vega'], 'm-o', markersize=4)
    ax4.set_xlabel('Iteration')
    ax4.set_ylabel('Vega')
    ax4.set_title('Vega Evolution')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def demo_iv_solver():
    """Main demonstration of the IV solver capabilities."""
    
    print("🚀 Implied Volatility Solver Demonstration")
    print("=" * 50)
    
    # Test parameters
    S, K, T, r = 100.0, 100.0, 0.25, 0.05
    true_sigma = 0.20
    option_type = 'call'
    
    # Generate target price using true volatility
    target_price = black_scholes_price(S, K, T, r, true_sigma, option_type)
    
    print(f"Test Setup:")
    print(f"  Spot: ${S}, Strike: ${K}, Time: {T:.2f}y, Rate: {r:.1%}")
    print(f"  True σ: {true_sigma:.1%}, Target Price: ${target_price:.4f}")
    print()
    
    # Initialize solver
    solver = ImpliedVolatilitySolver()
    
    # Test 1: Standard convergence
    print("📊 Test 1: Standard Convergence")
    print("-" * 30)
    
    result = solver.solve_with_tracking(
        target_price, S, K, T, r, option_type,
        initial_guess=0.15,  # Start away from true value
        tol=1e-8
    )
    
    print(f"✅ Converged: {result['converged']}")
    print(f"📍 Final IV: {result['iv']:.6f} (True: {true_sigma:.6f})")
    print(f"🔄 Iterations: {result['iterations']}")
    print(f"📉 Final Error: {result['final_error']:.2e}")
    print(f"🎯 Accuracy: {abs(result['iv'] - true_sigma):.2e}")
    print()
    
    # Visualize convergence
    result['target_price'] = target_price  # For visualization
    visualize_convergence(result, "Newton-Raphson IV Convergence")
    
    # Test 2: Benchmark different methods
    print("⚡ Test 2: Method Benchmarking")
    print("-" * 30)
    
    benchmark_stats = solver.benchmark_methods(target_price, S, K, T, r, option_type, num_trials=50)
    
    print("Performance Comparison:")
    for method, stats in benchmark_stats.items():
        print(f"\n{method.replace('_', ' ').title()}:")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        print(f"  Avg Time: {stats['avg_time']*1000:.3f}ms")
        print(f"  Avg IV: {stats['avg_iv']:.6f}")
        if 'avg_iterations' in stats:
            print(f"  Avg Iterations: {stats['avg_iterations']:.1f}")
    
    # Test 3: Stress testing with difficult cases
    print("\n🧪 Test 3: Stress Testing")
    print("-" * 30)
    
    stress_cases = [
        {"name": "Deep ITM", "S": 150, "K": 100},
        {"name": "Deep OTM", "S": 80, "K": 120},
        {"name": "Short Expiry", "S": 100, "K": 100, "T": 0.01},
        {"name": "High Vol", "sigma": 0.8},
        {"name": "Low Vol", "sigma": 0.05},
    ]
    
    stress_results = []
    
    for case in stress_cases:
        params = {"S": S, "K": K, "T": T, "r": r, "sigma": true_sigma}
        params.update(case)
        case_name = params.pop("name")
        
        try:
            case_target = black_scholes_price(**params, option_type=option_type)
            case_result = solver.solve_with_tracking(
                case_target, params["S"], params["K"], params["T"], params["r"], 
                option_type, tol=1e-6, max_iter=100
            )
            
            stress_results.append({
                "case": case_name,
                "converged": case_result['converged'],
                "iterations": case_result['iterations'],
                "accuracy": abs(case_result['iv'] - params["sigma"]) if case_result['converged'] else np.inf
            })
            
            status = "✅" if case_result['converged'] else "❌"
            print(f"{status} {case_name}: {case_result['iterations']} iter, "
                  f"accuracy: {abs(case_result['iv'] - params['sigma']):.2e}")
            
        except Exception as e:
            print(f"❌ {case_name}: Failed ({str(e)})")
            stress_results.append({
                "case": case_name,
                "converged": False,
                "iterations": 0,
                "accuracy": np.inf
            })
    
    # Test 4: Greeks consistency check
    print(f"\n🧮 Test 4: Greeks Integration")
    print("-" * 30)
    
    if result['converged']:
        greeks = all_greeks(S, K, T, r, result['iv'], option_type)
        
        print("Greeks at solved IV:")
        for greek_name, value in greeks.items():
            print(f"  {greek_name.capitalize()}: {value:.6f}")
        
        # Verify vega matches our calculation
        manual_vega = vega(S, K, T, r, result['iv']) * 100
        lib_vega = greeks['vega'] * 100
        print(f"\nVega verification:")
        print(f"  Manual calculation: {manual_vega:.6f}")
        print(f"  Greeks function: {lib_vega:.6f}")
        print(f"  Difference: {abs(manual_vega - lib_vega):.2e}")
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"💡 The IV solver is fully integrated with the Black-Scholes pricing engine")
    print(f"🔗 Use 'streamlit run dashboard/app.py' for the interactive dashboard")


if __name__ == "__main__":
    # Ensure we can import our modules
    try:
        demo_iv_solver()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
        print("   Try: python scripts/iv_solver_demo.py")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

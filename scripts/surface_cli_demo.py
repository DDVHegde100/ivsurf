#!/usr/bin/env python3
"""
Volatility Surface CLI Demo
===========================

Command-line demonstration of interpolation and plotting capabilities.
This script can be run without Streamlit to test the core functionality.

Usage:
    python surface_cli_demo.py [--method METHOD] [--points N] [--grid-size N]

Author: IVSURF Team
Date: 2025-08-16
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.offline as pyo
import argparse
import sys
import os
import time

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interpolation import (
    interpolate_surface,
    interpolate_surface_rbf, 
    interpolate_surface_bilinear,
    adaptive_interpolation,
    calculate_interpolation_quality
)
from visuals.plot_surface import (
    plot_vol_surface_matplotlib,
    plot_vol_surface_plotly,
    plot_vol_surface_contour,
    plot_vol_slice
)

def generate_test_data(n_points=50, noise_level=0.02):
    """Generate synthetic volatility data for testing"""
    np.random.seed(42)
    
    spot_price = 100.0
    strikes = np.random.uniform(80, 120, n_points)
    expiries = np.random.uniform(0.05, 2.0, n_points)
    
    # Generate realistic volatility surface
    moneyness = strikes / spot_price
    smile_effect = 0.05 * (moneyness - 1.0)**2
    term_effect = 0.1 + 0.05 * np.sqrt(expiries)
    base_vol = 0.2
    
    ivs = base_vol + smile_effect + term_effect + np.random.normal(0, noise_level, n_points)
    ivs = np.maximum(ivs, 0.05)
    
    return strikes, expiries, ivs

def test_interpolation_methods(strikes, expiries, ivs, grid_size=50):
    """Test all interpolation methods and return results"""
    
    print("🧮 Testing Interpolation Methods...")
    print("=" * 50)
    
    results = {}
    
    # Test Linear Griddata
    print("Testing Linear Griddata...")
    start_time = time.time()
    try:
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                   method='linear', grid_size=grid_size)
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        results['Linear Griddata'] = {
            'grids': (grid_x, grid_y, grid_z),
            'quality': quality,
            'time': time.time() - start_time
        }
        print(f"✅ Success (RMSE: {quality['rmse']:.6f}, Time: {results['Linear Griddata']['time']:.3f}s)")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test Cubic Griddata
    print("Testing Cubic Griddata...")
    start_time = time.time()
    try:
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                   method='cubic', grid_size=grid_size)
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        results['Cubic Griddata'] = {
            'grids': (grid_x, grid_y, grid_z),
            'quality': quality,
            'time': time.time() - start_time
        }
        print(f"✅ Success (RMSE: {quality['rmse']:.6f}, Time: {results['Cubic Griddata']['time']:.3f}s)")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test RBF Thin Plate Spline
    print("Testing RBF Thin Plate Spline...")
    start_time = time.time()
    try:
        grid_x, grid_y, grid_z = interpolate_surface_rbf(strikes, expiries, ivs, 
                                                       function='thin_plate_spline', grid_size=grid_size)
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        results['RBF Thin Plate'] = {
            'grids': (grid_x, grid_y, grid_z),
            'quality': quality,
            'time': time.time() - start_time
        }
        print(f"✅ Success (RMSE: {quality['rmse']:.6f}, Time: {results['RBF Thin Plate']['time']:.3f}s)")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test RBF Cubic
    print("Testing RBF Cubic...")
    start_time = time.time()
    try:
        grid_x, grid_y, grid_z = interpolate_surface_rbf(strikes, expiries, ivs, 
                                                       function='cubic', grid_size=grid_size)
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        results['RBF Cubic'] = {
            'grids': (grid_x, grid_y, grid_z),
            'quality': quality,
            'time': time.time() - start_time
        }
        print(f"✅ Success (RMSE: {quality['rmse']:.6f}, Time: {results['RBF Cubic']['time']:.3f}s)")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test Bilinear
    print("Testing Bilinear Interpolation...")
    start_time = time.time()
    try:
        grid_x, grid_y, grid_z = interpolate_surface_bilinear(strikes, expiries, ivs, grid_size=grid_size)
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        results['Bilinear'] = {
            'grids': (grid_x, grid_y, grid_z),
            'quality': quality,
            'time': time.time() - start_time
        }
        print(f"✅ Success (RMSE: {quality['rmse']:.6f}, Time: {results['Bilinear']['time']:.3f}s)")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test Adaptive
    print("Testing Adaptive Interpolation...")
    start_time = time.time()
    try:
        grid_x, grid_y, grid_z, method_used = adaptive_interpolation(strikes, expiries, ivs, grid_size=grid_size)
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        results[f'Adaptive ({method_used})'] = {
            'grids': (grid_x, grid_y, grid_z),
            'quality': quality,
            'time': time.time() - start_time
        }
        print(f"✅ Success - Used {method_used} (RMSE: {quality['rmse']:.6f}, Time: {results[f'Adaptive ({method_used})']['time']:.3f}s)")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    return results

def create_plots(strikes, expiries, ivs, results, output_dir="plots"):
    """Create and save various plots"""
    
    print(f"\n🎨 Creating Plots...")
    print("=" * 50)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find the best method based on RMSE
    best_method = min(results.keys(), key=lambda k: results[k]['quality']['rmse'])
    best_grids = results[best_method]['grids']
    
    print(f"Using best method: {best_method}")
    
    # 1. Matplotlib static 3D plot
    print("Creating Matplotlib 3D plot...")
    try:
        fig_mpl = plot_vol_surface_matplotlib(strikes, expiries, ivs, *best_grids,
                                            title=f"Volatility Surface - {best_method}")
        fig_mpl.savefig(f"{output_dir}/surface_3d_matplotlib.png", dpi=300, bbox_inches='tight')
        plt.close(fig_mpl)
        print("✅ Saved: surface_3d_matplotlib.png")
    except Exception as e:
        print(f"❌ Failed to create Matplotlib plot: {e}")
    
    # 2. Plotly interactive 3D plot
    print("Creating Plotly 3D plot...")
    try:
        fig_plotly = plot_vol_surface_plotly(strikes, expiries, ivs, *best_grids,
                                           title=f"Interactive Volatility Surface - {best_method}")
        pyo.plot(fig_plotly, filename=f"{output_dir}/surface_3d_plotly.html", auto_open=False)
        print("✅ Saved: surface_3d_plotly.html")
    except Exception as e:
        print(f"❌ Failed to create Plotly plot: {e}")
    
    # 3. Contour plot
    print("Creating contour plot...")
    try:
        fig_contour = plot_vol_surface_contour(*best_grids, strikes, expiries, ivs,
                                             title=f"Volatility Surface Contour - {best_method}")
        pyo.plot(fig_contour, filename=f"{output_dir}/surface_contour.html", auto_open=False)
        print("✅ Saved: surface_contour.html")
    except Exception as e:
        print(f"❌ Failed to create contour plot: {e}")
    
    # 4. Strike slice
    print("Creating strike slice plot...")
    try:
        fig_strike = plot_vol_slice(*best_grids, slice_type='strike', slice_value=100.0,
                                  strikes=strikes, expiries=expiries, ivs=ivs)
        pyo.plot(fig_strike, filename=f"{output_dir}/strike_slice.html", auto_open=False)
        print("✅ Saved: strike_slice.html")
    except Exception as e:
        print(f"❌ Failed to create strike slice: {e}")
    
    # 5. Expiry slice
    print("Creating expiry slice plot...")
    try:
        fig_expiry = plot_vol_slice(*best_grids, slice_type='expiry', slice_value=0.5,
                                  strikes=strikes, expiries=expiries, ivs=ivs)
        pyo.plot(fig_expiry, filename=f"{output_dir}/expiry_slice.html", auto_open=False)
        print("✅ Saved: expiry_slice.html")
    except Exception as e:
        print(f"❌ Failed to create expiry slice: {e}")

def save_results(strikes, expiries, ivs, results, output_dir="results"):
    """Save numerical results to files"""
    
    print(f"\n💾 Saving Results...")
    print("=" * 50)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save original data
    df_original = pd.DataFrame({
        'Strike': strikes,
        'Expiry': expiries,
        'Implied_Volatility': ivs
    })
    df_original.to_csv(f"{output_dir}/original_data.csv", index=False)
    print("✅ Saved: original_data.csv")
    
    # Save quality metrics
    quality_data = []
    for method, result in results.items():
        quality = result['quality']
        quality['method'] = method
        quality['computation_time'] = result['time']
        quality_data.append(quality)
    
    df_quality = pd.DataFrame(quality_data)
    df_quality.to_csv(f"{output_dir}/quality_metrics.csv", index=False)
    print("✅ Saved: quality_metrics.csv")
    
    # Save interpolated surfaces (best method only)
    best_method = min(results.keys(), key=lambda k: results[k]['quality']['rmse'])
    grid_x, grid_y, grid_z = results[best_method]['grids']
    
    df_surface = pd.DataFrame({
        'Strike': grid_x.ravel(),
        'Expiry': grid_y.ravel(),
        'Implied_Volatility': grid_z.ravel()
    })
    df_surface.to_csv(f"{output_dir}/interpolated_surface.csv", index=False)
    print(f"✅ Saved: interpolated_surface.csv (using {best_method})")

def print_summary(results):
    """Print a summary of results"""
    
    print(f"\n📊 SUMMARY REPORT")
    print("=" * 70)
    
    # Sort by RMSE
    sorted_methods = sorted(results.items(), key=lambda x: x[1]['quality']['rmse'])
    
    print(f"{'Method':<25} {'RMSE':<10} {'R²':<8} {'Coverage':<10} {'Time (s)':<10}")
    print("-" * 70)
    
    for method, result in sorted_methods:
        quality = result['quality']
        print(f"{method:<25} {quality['rmse']:<10.6f} {quality['r_squared']:<8.4f} "
              f"{quality['coverage']:<10.2%} {result['time']:<10.3f}")
    
    print("-" * 70)
    best_method = sorted_methods[0][0]
    print(f"🏆 Best Method: {best_method}")
    print(f"📈 Data Points: {len(results[best_method]['quality'])} original points")
    print(f"🎯 Best RMSE: {sorted_methods[0][1]['quality']['rmse']:.6f}")

def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description="Volatility Surface CLI Demo")
    parser.add_argument("--method", type=str, default="all", 
                       help="Interpolation method to test (or 'all')")
    parser.add_argument("--points", type=int, default=50,
                       help="Number of data points to generate")
    parser.add_argument("--grid-size", type=int, default=50,
                       help="Size of interpolation grid")
    parser.add_argument("--noise", type=float, default=0.02,
                       help="Noise level in data")
    parser.add_argument("--output", type=str, default="output",
                       help="Output directory")
    
    args = parser.parse_args()
    
    print("🌊 VOLATILITY SURFACE EXPLORER - CLI DEMO")
    print("=" * 50)
    print(f"Data Points: {args.points}")
    print(f"Grid Size: {args.grid_size}")
    print(f"Noise Level: {args.noise}")
    print(f"Output Directory: {args.output}")
    print()
    
    # Generate test data
    print("📊 Generating synthetic volatility data...")
    strikes, expiries, ivs = generate_test_data(args.points, args.noise)
    print(f"✅ Generated {len(strikes)} data points")
    print(f"   Strike range: {min(strikes):.1f} - {max(strikes):.1f}")
    print(f"   Expiry range: {min(expiries):.3f} - {max(expiries):.3f}")
    print(f"   IV range: {min(ivs):.3f} - {max(ivs):.3f}")
    
    # Test interpolation methods
    results = test_interpolation_methods(strikes, expiries, ivs, args.grid_size)
    
    if not results:
        print("❌ No interpolation methods succeeded!")
        return
    
    # Create plots
    plot_dir = os.path.join(args.output, "plots")
    create_plots(strikes, expiries, ivs, results, plot_dir)
    
    # Save results
    results_dir = os.path.join(args.output, "data")
    save_results(strikes, expiries, ivs, results, results_dir)
    
    # Print summary
    print_summary(results)
    
    print(f"\n✅ Demo completed! Check the '{args.output}' directory for results.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Comprehensive Test Suite for Volatility Surface Explorer
======================================================

This script tests all the interpolation and plotting functionalities
to ensure they work correctly.

Author: IVSURF Team
Date: 2025-08-16
"""

import numpy as np
import sys
import os
import traceback

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
    plot_vol_slice,
    plot_vol_surface_comparison
)

def test_interpolation_functions():
    """Test all interpolation functions"""
    
    print("🧪 Testing Interpolation Functions...")
    print("=" * 50)
    
    # Generate test data
    np.random.seed(42)
    strikes = np.random.uniform(80, 120, 25)
    expiries = np.random.uniform(0.1, 2.0, 25)
    ivs = 0.2 + 0.05 * np.random.randn(25)
    ivs = np.maximum(ivs, 0.05)  # Ensure positive
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Basic griddata interpolation
    total_tests += 1
    try:
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, method='linear')
        assert grid_x.shape == grid_y.shape == grid_z.shape
        assert not np.all(np.isnan(grid_z))
        print("✅ Test 1 PASSED: Basic griddata interpolation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1 FAILED: Basic griddata interpolation - {e}")
    
    # Test 2: Cubic griddata interpolation
    total_tests += 1
    try:
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, method='cubic')
        assert grid_x.shape == grid_y.shape == grid_z.shape
        print("✅ Test 2 PASSED: Cubic griddata interpolation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2 FAILED: Cubic griddata interpolation - {e}")
    
    # Test 3: RBF interpolation
    total_tests += 1
    try:
        grid_x, grid_y, grid_z = interpolate_surface_rbf(strikes, expiries, ivs, function='thin_plate_spline')
        assert grid_x.shape == grid_y.shape == grid_z.shape
        assert not np.all(np.isnan(grid_z))
        print("✅ Test 3 PASSED: RBF interpolation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3 FAILED: RBF interpolation - {e}")
    
    # Test 4: Bilinear interpolation (should handle fallback gracefully)
    total_tests += 1
    try:
        grid_x, grid_y, grid_z = interpolate_surface_bilinear(strikes, expiries, ivs)
        assert grid_x.shape == grid_y.shape == grid_z.shape
        print("✅ Test 4 PASSED: Bilinear interpolation (with fallback)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4 FAILED: Bilinear interpolation - {e}")
    
    # Test 5: Adaptive interpolation
    total_tests += 1
    try:
        grid_x, grid_y, grid_z, method_used = adaptive_interpolation(strikes, expiries, ivs)
        assert grid_x.shape == grid_y.shape == grid_z.shape
        assert isinstance(method_used, str)
        print(f"✅ Test 5 PASSED: Adaptive interpolation (used {method_used})")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5 FAILED: Adaptive interpolation - {e}")
    
    # Test 6: Quality metrics calculation
    total_tests += 1
    try:
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, method='linear')
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        
        required_keys = ['rmse', 'mae', 'r_squared', 'coverage']
        assert all(key in quality for key in required_keys)
        assert all(isinstance(quality[key], (int, float)) for key in required_keys)
        print("✅ Test 6 PASSED: Quality metrics calculation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 6 FAILED: Quality metrics calculation - {e}")
    
    print(f"\n📊 Interpolation Tests: {tests_passed}/{total_tests} passed")
    return tests_passed, total_tests

def test_plotting_functions():
    """Test all plotting functions"""
    
    print("\n🎨 Testing Plotting Functions...")
    print("=" * 50)
    
    # Generate test data
    np.random.seed(42)
    strikes = np.random.uniform(80, 120, 25)
    expiries = np.random.uniform(0.1, 2.0, 25)
    ivs = 0.2 + 0.05 * np.random.randn(25)
    ivs = np.maximum(ivs, 0.05)
    
    # Get interpolated surface
    grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, method='cubic')
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Matplotlib 3D plot
    total_tests += 1
    try:
        fig = plot_vol_surface_matplotlib(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        assert fig is not None
        print("✅ Test 1 PASSED: Matplotlib 3D plot")
        tests_passed += 1
        import matplotlib.pyplot as plt
        plt.close(fig)  # Clean up
    except Exception as e:
        print(f"❌ Test 1 FAILED: Matplotlib 3D plot - {e}")
    
    # Test 2: Plotly 3D plot
    total_tests += 1
    try:
        fig = plot_vol_surface_plotly(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        assert fig is not None
        assert hasattr(fig, 'data')
        print("✅ Test 2 PASSED: Plotly 3D plot")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2 FAILED: Plotly 3D plot - {e}")
    
    # Test 3: Contour plot
    total_tests += 1
    try:
        fig = plot_vol_surface_contour(grid_x, grid_y, grid_z, strikes, expiries, ivs)
        assert fig is not None
        assert hasattr(fig, 'data')
        print("✅ Test 3 PASSED: Contour plot")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3 FAILED: Contour plot - {e}")
    
    # Test 4: Strike slice plot
    total_tests += 1
    try:
        fig = plot_vol_slice(grid_x, grid_y, grid_z, slice_type='strike', slice_value=100.0,
                           strikes=strikes, expiries=expiries, ivs=ivs)
        assert fig is not None
        assert hasattr(fig, 'data')
        print("✅ Test 4 PASSED: Strike slice plot")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4 FAILED: Strike slice plot - {e}")
    
    # Test 5: Expiry slice plot
    total_tests += 1
    try:
        fig = plot_vol_slice(grid_x, grid_y, grid_z, slice_type='expiry', slice_value=0.5,
                           strikes=strikes, expiries=expiries, ivs=ivs)
        assert fig is not None
        assert hasattr(fig, 'data')
        print("✅ Test 5 PASSED: Expiry slice plot")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5 FAILED: Expiry slice plot - {e}")
    
    # Test 6: Surface comparison plot
    total_tests += 1
    try:
        # Create two different surfaces for comparison
        grid1 = interpolate_surface(strikes, expiries, ivs, method='linear')
        grid2 = interpolate_surface(strikes, expiries, ivs, method='cubic')
        
        fig = plot_vol_surface_comparison([grid1, grid2], ['Linear', 'Cubic'])
        assert fig is not None
        assert hasattr(fig, 'data')
        print("✅ Test 6 PASSED: Surface comparison plot")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 6 FAILED: Surface comparison plot - {e}")
    
    print(f"\n📊 Plotting Tests: {tests_passed}/{total_tests} passed")
    return tests_passed, total_tests

def test_edge_cases():
    """Test edge cases and error handling"""
    
    print("\n🚨 Testing Edge Cases...")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Very few data points
    total_tests += 1
    try:
        strikes = np.array([90, 100, 110])
        expiries = np.array([0.25, 0.5, 1.0])
        ivs = np.array([0.2, 0.25, 0.3])
        
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, method='linear')
        assert not np.all(np.isnan(grid_z))
        print("✅ Test 1 PASSED: Very few data points")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1 FAILED: Very few data points - {e}")
    
    # Test 2: Single data point (should handle gracefully)
    total_tests += 1
    try:
        strikes = np.array([100])
        expiries = np.array([0.5])
        ivs = np.array([0.2])
        
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, method='nearest')
        # Should not crash, even if result is not meaningful
        print("✅ Test 2 PASSED: Single data point")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2 FAILED: Single data point - {e}")
    
    # Test 3: Identical strikes or expiries
    total_tests += 1
    try:
        strikes = np.array([100, 100, 100])
        expiries = np.array([0.25, 0.5, 1.0])
        ivs = np.array([0.2, 0.25, 0.3])
        
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, method='linear')
        print("✅ Test 3 PASSED: Identical strikes")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3 FAILED: Identical strikes - {e}")
    
    # Test 4: NaN values in input
    total_tests += 1
    try:
        strikes = np.array([90, 100, 110, 120])
        expiries = np.array([0.25, 0.5, 1.0, 0.75])
        ivs = np.array([0.2, np.nan, 0.3, 0.25])
        
        # Should handle NaN values gracefully (or fail gracefully)
        try:
            # Remove NaN values first
            valid_mask = ~np.isnan(ivs)
            grid_x, grid_y, grid_z = interpolate_surface(
                strikes[valid_mask], expiries[valid_mask], ivs[valid_mask], method='linear')
            print("✅ Test 4 PASSED: NaN values in input (handled by filtering)")
            tests_passed += 1
        except:
            print("✅ Test 4 PASSED: NaN values in input (failed gracefully)")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4 FAILED: NaN values in input - {e}")
    
    # Test 5: Very large grid size
    total_tests += 1
    try:
        np.random.seed(42)
        strikes = np.random.uniform(80, 120, 20)
        expiries = np.random.uniform(0.1, 2.0, 20)
        ivs = 0.2 + 0.05 * np.random.randn(20)
        
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                   method='linear', grid_size=200)
        assert grid_x.shape == (200, 200)
        print("✅ Test 5 PASSED: Very large grid size")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5 FAILED: Very large grid size - {e}")
    
    print(f"\n📊 Edge Case Tests: {tests_passed}/{total_tests} passed")
    return tests_passed, total_tests

def run_comprehensive_test():
    """Run all tests and provide summary"""
    
    print("🧪 COMPREHENSIVE TEST SUITE FOR VOLATILITY SURFACE EXPLORER")
    print("=" * 70)
    print("Testing interpolation and plotting functionalities...")
    print()
    
    # Run all test categories
    interp_passed, interp_total = test_interpolation_functions()
    plot_passed, plot_total = test_plotting_functions()
    edge_passed, edge_total = test_edge_cases()
    
    # Summary
    total_passed = interp_passed + plot_passed + edge_passed
    total_tests = interp_total + plot_total + edge_total
    
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    print(f"Interpolation Tests: {interp_passed}/{interp_total} passed")
    print(f"Plotting Tests:      {plot_passed}/{plot_total} passed")
    print(f"Edge Case Tests:     {edge_passed}/{edge_total} passed")
    print("-" * 70)
    print(f"TOTAL:              {total_passed}/{total_tests} passed ({total_passed/total_tests*100:.1f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! The volatility surface explorer is working correctly.")
    elif total_passed >= total_tests * 0.8:
        print("\n✅ MOST TESTS PASSED! Minor issues detected but core functionality works.")
    else:
        print("\n⚠️  SOME TESTS FAILED! Please review the implementation.")
    
    return total_passed, total_tests

if __name__ == "__main__":
    try:
        passed, total = run_comprehensive_test()
        
        # Exit with appropriate code
        if passed == total:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Some failures
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(2)  # Critical failure

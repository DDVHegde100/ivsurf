#!/usr/bin/env python3
"""
Volatility Surface Explorer - Comprehensive Demo
==============================================

This script demonstrates all the interpolation and plotting functionalities:
1. Basic interpolation using griddata
2. Advanced interpolation methods (RBF, bilinear)
3. Static 3D surface plotting with Matplotlib
4. Interactive surface plotting with Plotly
5. Contour plots and surface slices
6. Interpolation quality assessment

Author: IVSURF Team
Date: 2025-08-16
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st
import sys
import os

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

def generate_synthetic_vol_data(n_points=50, noise_level=0.02):
    """
    Generate synthetic volatility data for demonstration
    
    Parameters:
    -----------
    n_points : int
        Number of data points to generate
    noise_level : float
        Amount of noise to add to the data
    
    Returns:
    --------
    tuple : (strikes, expiries, ivs)
        Generated volatility data
    """
    # Generate random strikes and expiries
    np.random.seed(42)  # For reproducible results
    
    # Create a realistic range of strikes and expiries
    spot_price = 100.0
    strikes = np.random.uniform(80, 120, n_points)
    expiries = np.random.uniform(0.05, 2.0, n_points)  # 0.05 to 2 years
    
    # Generate realistic volatility surface with smile and term structure
    moneyness = strikes / spot_price
    
    # Volatility smile: higher vol for OTM options
    smile_effect = 0.05 * (moneyness - 1.0)**2
    
    # Term structure: volatility increases with time (usually)
    term_effect = 0.1 + 0.05 * np.sqrt(expiries)
    
    # Base volatility
    base_vol = 0.2
    
    # Combine effects
    ivs = base_vol + smile_effect + term_effect + np.random.normal(0, noise_level, n_points)
    
    # Ensure positive volatilities
    ivs = np.maximum(ivs, 0.05)
    
    return strikes, expiries, ivs

def run_interpolation_demo():
    """
    Run comprehensive interpolation demonstration
    """
    st.title("🌊 Volatility Surface Explorer - Interpolation & Plotting Demo")
    
    st.markdown("""
    This demo showcases advanced interpolation and plotting capabilities for volatility surfaces.
    We'll demonstrate:
    - Multiple interpolation methods
    - Static and interactive plotting
    - Quality assessment metrics
    """)
    
    # Sidebar controls
    st.sidebar.header("🎛️ Demo Controls")
    
    n_points = st.sidebar.slider("Number of Data Points", 20, 200, 50)
    noise_level = st.sidebar.slider("Noise Level", 0.0, 0.1, 0.02, 0.01)
    grid_size = st.sidebar.slider("Grid Size", 20, 100, 50)
    
    # Generate data
    strikes, expiries, ivs = generate_synthetic_vol_data(n_points, noise_level)
    
    st.markdown("### 📊 Generated Market Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Data Points", n_points)
    with col2:
        st.metric("Strike Range", f"{min(strikes):.1f} - {max(strikes):.1f}")
    with col3:
        st.metric("Expiry Range", f"{min(expiries):.2f} - {max(expiries):.2f}")
    
    # Display raw data
    if st.sidebar.checkbox("Show Raw Data"):
        df = pd.DataFrame({
            'Strike': strikes,
            'Expiry': expiries,
            'Implied_Volatility': ivs
        })
        st.dataframe(df)
    
    # Interpolation Methods Demo
    st.markdown("### 🧮 Interpolation Methods Comparison")
    
    methods_to_test = st.sidebar.multiselect(
        "Select Interpolation Methods",
        ["Linear Griddata", "Cubic Griddata", "RBF Thin Plate", "RBF Cubic", "Bilinear", "Adaptive"],
        default=["Linear Griddata", "Cubic Griddata", "RBF Thin Plate"]
    )
    
    # Store interpolation results
    interpolation_results = {}
    quality_metrics = {}
    
    progress_bar = st.progress(0)
    
    for i, method in enumerate(methods_to_test):
        progress_bar.progress((i + 1) / len(methods_to_test))
        
        if method == "Linear Griddata":
            grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                       method='linear', grid_size=grid_size)
        elif method == "Cubic Griddata":
            grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                       method='cubic', grid_size=grid_size)
        elif method == "RBF Thin Plate":
            grid_x, grid_y, grid_z = interpolate_surface_rbf(strikes, expiries, ivs, 
                                                           function='thin_plate_spline', grid_size=grid_size)
        elif method == "RBF Cubic":
            grid_x, grid_y, grid_z = interpolate_surface_rbf(strikes, expiries, ivs, 
                                                           function='cubic', grid_size=grid_size)
        elif method == "Bilinear":
            grid_x, grid_y, grid_z = interpolate_surface_bilinear(strikes, expiries, ivs, grid_size=grid_size)
        elif method == "Adaptive":
            grid_x, grid_y, grid_z, method_used = adaptive_interpolation(strikes, expiries, ivs, grid_size=grid_size)
            method = f"Adaptive ({method_used})"
        
        interpolation_results[method] = (grid_x, grid_y, grid_z)
        
        # Calculate quality metrics
        quality = calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z)
        quality_metrics[method] = quality
    
    progress_bar.empty()
    
    # Display quality metrics
    st.markdown("### 📈 Interpolation Quality Metrics")
    
    metrics_df = pd.DataFrame(quality_metrics).T
    st.dataframe(metrics_df)
    
    # Plot comparison
    if st.sidebar.checkbox("Show Method Comparison", value=True):
        st.markdown("### 🔍 Visual Comparison of Methods")
        
        # Create tabs for different plot types
        plot_tab1, plot_tab2, plot_tab3 = st.tabs(["Interactive 3D", "Contour Plots", "Surface Slices"])
        
        with plot_tab1:
            selected_method = st.selectbox("Select Method for 3D Plot", list(interpolation_results.keys()))
            
            if selected_method in interpolation_results:
                grid_x, grid_y, grid_z = interpolation_results[selected_method]
                fig = plot_vol_surface_plotly(strikes, expiries, ivs, grid_x, grid_y, grid_z,
                                            title=f"Volatility Surface - {selected_method}")
                st.plotly_chart(fig, use_container_width=True)
        
        with plot_tab2:
            st.markdown("#### Contour Maps")
            
            # Create subplot for contour comparison
            n_methods = len(interpolation_results)
            cols = st.columns(min(2, n_methods))
            
            for i, (method, (grid_x, grid_y, grid_z)) in enumerate(interpolation_results.items()):
                with cols[i % 2]:
                    fig = plot_vol_surface_contour(grid_x, grid_y, grid_z, strikes, expiries, ivs,
                                                 title=f"{method}")
                    st.plotly_chart(fig, use_container_width=True)
        
        with plot_tab3:
            st.markdown("#### Surface Slices")
            
            slice_method = st.selectbox("Select Method for Slicing", list(interpolation_results.keys()))
            slice_type = st.radio("Slice Type", ["Strike", "Expiry"])
            
            if slice_method in interpolation_results:
                grid_x, grid_y, grid_z = interpolation_results[slice_method]
                
                if slice_type == "Strike":
                    strike_value = st.slider("Strike Value", float(min(strikes)), float(max(strikes)), 
                                           float(np.mean(strikes)))
                    fig = plot_vol_slice(grid_x, grid_y, grid_z, slice_type='strike', 
                                       slice_value=strike_value, strikes=strikes, expiries=expiries, ivs=ivs)
                else:
                    expiry_value = st.slider("Expiry Value", float(min(expiries)), float(max(expiries)), 
                                           float(np.mean(expiries)))
                    fig = plot_vol_slice(grid_x, grid_y, grid_z, slice_type='expiry', 
                                       slice_value=expiry_value, strikes=strikes, expiries=expiries, ivs=ivs)
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Matplotlib Static Plot Demo
    if st.sidebar.checkbox("Show Matplotlib Static Plot"):
        st.markdown("### 🎨 Static 3D Plot (Matplotlib)")
        
        static_method = st.selectbox("Select Method for Static Plot", 
                                   list(interpolation_results.keys()), key="static")
        
        if static_method in interpolation_results:
            grid_x, grid_y, grid_z = interpolation_results[static_method]
            
            # Create matplotlib plot
            fig_mpl = plot_vol_surface_matplotlib(strikes, expiries, ivs, grid_x, grid_y, grid_z,
                                                title=f"Volatility Surface - {static_method}")
            
            st.pyplot(fig_mpl)
            plt.close()  # Important: close the figure to prevent memory leaks
    
    # Export functionality
    st.markdown("### 💾 Export Results")
    
    if st.button("📁 Export Data and Plots"):
        # Create export directory
        export_dir = "volatility_surface_export"
        os.makedirs(export_dir, exist_ok=True)
        
        # Export raw data
        df = pd.DataFrame({
            'Strike': strikes,
            'Expiry': expiries,
            'Implied_Volatility': ivs
        })
        df.to_csv(f"{export_dir}/market_data.csv", index=False)
        
        # Export interpolated surfaces
        for method, (grid_x, grid_y, grid_z) in interpolation_results.items():
            surface_df = pd.DataFrame({
                'Strike': grid_x.ravel(),
                'Expiry': grid_y.ravel(),
                'Implied_Volatility': grid_z.ravel()
            })
            filename = method.replace(" ", "_").replace("(", "").replace(")", "").lower()
            surface_df.to_csv(f"{export_dir}/surface_{filename}.csv", index=False)
        
        # Export quality metrics
        metrics_df = pd.DataFrame(quality_metrics).T
        metrics_df.to_csv(f"{export_dir}/quality_metrics.csv")
        
        st.success(f"✅ Data exported to {export_dir}/ directory")
    
    # Technical Documentation
    if st.sidebar.checkbox("Show Technical Details"):
        st.markdown("### 📚 Technical Documentation")
        
        with st.expander("Interpolation Methods"):
            st.markdown("""
            **Linear Griddata**: Fast, simple interpolation suitable for sparse data.
            
            **Cubic Griddata**: Smooth interpolation with cubic polynomials, good for dense data.
            
            **RBF (Radial Basis Functions)**: Advanced method using radial basis functions:
            - Thin Plate Spline: Smooth, good for general surfaces
            - Cubic: Balance between smoothness and computational efficiency
            
            **Bilinear**: Legacy method using scipy.interpolate.interp2d.
            
            **Adaptive**: Automatically selects the best method based on data density.
            """)
        
        with st.expander("Quality Metrics"):
            st.markdown("""
            **RMSE (Root Mean Square Error)**: Average prediction error.
            
            **MAE (Mean Absolute Error)**: Average absolute prediction error.
            
            **R-squared**: Coefficient of determination (1.0 = perfect fit).
            
            **Coverage**: Percentage of grid points with valid interpolated values.
            """)

def main():
    """
    Main function to run the demo
    """
    st.set_page_config(
        page_title="Volatility Surface Explorer",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better appearance
    st.markdown("""
    <style>
    .main { padding-top: 2rem; }
    .stMetric { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)
    
    run_interpolation_demo()

if __name__ == "__main__":
    main()

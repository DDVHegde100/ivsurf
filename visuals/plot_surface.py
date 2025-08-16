import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import streamlit as st

def plot_vol_surface_matplotlib(strikes, expiries, ivs, grid_x, grid_y, grid_z, 
                               title="Implied Volatility Surface", save_path=None):
    """
    Plot static 3D surface using Matplotlib
    
    Parameters:
    -----------
    strikes, expiries, ivs : array-like
        Original data points
    grid_x, grid_y, grid_z : array-like
        Interpolated surface grids
    title : str
        Plot title
    save_path : str, optional
        Path to save the plot
    
    Returns:
    --------
    matplotlib.figure.Figure : The figure object
    """
    # Create figure and 3D axis
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot the surface
    surf = ax.plot_surface(grid_x, grid_y, grid_z, 
                          cmap=cm.viridis, 
                          alpha=0.8, 
                          linewidth=0, 
                          antialiased=True)
    
    # Plot original data points
    ax.scatter(strikes, expiries, ivs, 
              color='red', s=50, alpha=0.8, label='Market Data')
    
    # Customize the plot
    ax.set_xlabel('Strike Price', fontsize=12)
    ax.set_ylabel('Time to Expiry (Years)', fontsize=12)
    ax.set_zlabel('Implied Volatility', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add colorbar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Implied Volatility')
    
    # Add legend
    ax.legend()
    
    # Set viewing angle
    ax.view_init(elev=30, azim=45)
    
    # Improve layout
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def plot_vol_surface_plotly(strikes, expiries, ivs, grid_x, grid_y, grid_z, 
                           title="Interactive Implied Volatility Surface"):
    """
    Plot interactive 3D surface using Plotly
    
    Parameters:
    -----------
    strikes, expiries, ivs : array-like
        Original data points
    grid_x, grid_y, grid_z : array-like
        Interpolated surface grids
    title : str
        Plot title
    
    Returns:
    --------
    plotly.graph_objects.Figure : The interactive figure object
    """
    # Create the surface plot
    surface = go.Surface(
        x=grid_x,
        y=grid_y,
        z=grid_z,
        colorscale='Viridis',
        opacity=0.8,
        name='Volatility Surface',
        hovertemplate='<b>Strike:</b> %{x:.2f}<br>' +
                     '<b>Expiry:</b> %{y:.3f}<br>' +
                     '<b>IV:</b> %{z:.4f}<extra></extra>'
    )
    
    # Add market data points
    scatter = go.Scatter3d(
        x=strikes,
        y=expiries,
        z=ivs,
        mode='markers',
        marker=dict(
            size=8,
            color='red',
            opacity=0.8,
            symbol='circle'
        ),
        name='Market Data',
        hovertemplate='<b>Strike:</b> %{x:.2f}<br>' +
                     '<b>Expiry:</b> %{y:.3f}<br>' +
                     '<b>IV:</b> %{z:.4f}<extra></extra>'
    )
    
    # Create figure
    fig = go.Figure(data=[surface, scatter])
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': 'white'}
        },
        scene=dict(
            xaxis=dict(
                title='Strike Price',
                backgroundcolor="rgb(230, 230,230)",
                gridcolor="white",
                showbackground=True,
                zerolinecolor="white"
            ),
            yaxis=dict(
                title='Time to Expiry (Years)',
                backgroundcolor="rgb(230, 230,230)",
                gridcolor="white",
                showbackground=True,
                zerolinecolor="white"
            ),
            zaxis=dict(
                title='Implied Volatility',
                backgroundcolor="rgb(230, 230,230)",
                gridcolor="white",
                showbackground=True,
                zerolinecolor="white"
            ),
            bgcolor="rgba(0,0,0,0)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=900,
        height=700,
        margin=dict(r=20, b=10, l=10, t=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def plot_vol_surface_contour(grid_x, grid_y, grid_z, strikes=None, expiries=None, ivs=None,
                            title="Volatility Surface Contour Plot"):
    """
    Plot contour map of volatility surface
    
    Parameters:
    -----------
    grid_x, grid_y, grid_z : array-like
        Interpolated surface grids
    strikes, expiries, ivs : array-like, optional
        Original data points to overlay
    title : str
        Plot title
    
    Returns:
    --------
    plotly.graph_objects.Figure : The contour figure
    """
    # Create contour plot
    contour = go.Contour(
        x=grid_x[0, :],
        y=grid_y[:, 0],
        z=grid_z,
        colorscale='Viridis',
        contours=dict(
            showlabels=True,
            labelfont=dict(size=12, color='white')
        ),
        hovertemplate='<b>Strike:</b> %{x:.2f}<br>' +
                     '<b>Expiry:</b> %{y:.3f}<br>' +
                     '<b>IV:</b> %{z:.4f}<extra></extra>'
    )
    
    fig = go.Figure(data=[contour])
    
    # Add market data points if provided
    if strikes is not None and expiries is not None and ivs is not None:
        scatter = go.Scatter(
            x=strikes,
            y=expiries,
            mode='markers',
            marker=dict(
                size=8,
                color='red',
                opacity=0.8,
                symbol='circle',
                line=dict(width=1, color='white')
            ),
            name='Market Data',
            hovertemplate='<b>Strike:</b> %{x:.2f}<br>' +
                         '<b>Expiry:</b> %{y:.3f}<extra></extra>'
        )
        fig.add_trace(scatter)
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(title='Strike Price'),
        yaxis=dict(title='Time to Expiry (Years)'),
        width=800,
        height=600
    )
    
    return fig

def plot_vol_slice(grid_x, grid_y, grid_z, slice_type='strike', slice_value=None,
                  strikes=None, expiries=None, ivs=None):
    """
    Plot a slice of the volatility surface (either constant strike or constant expiry)
    
    Parameters:
    -----------
    grid_x, grid_y, grid_z : array-like
        Interpolated surface grids
    slice_type : str
        'strike' for constant strike slice, 'expiry' for constant expiry slice
    slice_value : float, optional
        Value at which to slice. If None, uses middle value
    strikes, expiries, ivs : array-like, optional
        Original data points for comparison
    
    Returns:
    --------
    plotly.graph_objects.Figure : The slice plot
    """
    fig = go.Figure()
    
    if slice_type == 'strike':
        # Find closest strike index
        if slice_value is None:
            slice_idx = grid_x.shape[1] // 2
        else:
            slice_idx = np.argmin(np.abs(grid_x[0, :] - slice_value))
        
        actual_strike = grid_x[0, slice_idx]
        
        # Plot the slice
        fig.add_trace(go.Scatter(
            x=grid_y[:, slice_idx],
            y=grid_z[:, slice_idx],
            mode='lines+markers',
            name=f'Strike = {actual_strike:.2f}',
            line=dict(width=3)
        ))
        
        # Add market data points if available
        if strikes is not None and expiries is not None and ivs is not None:
            # Find points close to this strike
            strike_mask = np.abs(np.array(strikes) - actual_strike) < (max(strikes) - min(strikes)) * 0.05
            if np.any(strike_mask):
                fig.add_trace(go.Scatter(
                    x=np.array(expiries)[strike_mask],
                    y=np.array(ivs)[strike_mask],
                    mode='markers',
                    name='Market Data',
                    marker=dict(size=8, color='red')
                ))
        
        fig.update_layout(
            title=f'Volatility Term Structure (Strike = {actual_strike:.2f})',
            xaxis_title='Time to Expiry (Years)',
            yaxis_title='Implied Volatility'
        )
        
    else:  # expiry slice
        # Find closest expiry index
        if slice_value is None:
            slice_idx = grid_y.shape[0] // 2
        else:
            slice_idx = np.argmin(np.abs(grid_y[:, 0] - slice_value))
        
        actual_expiry = grid_y[slice_idx, 0]
        
        # Plot the slice
        fig.add_trace(go.Scatter(
            x=grid_x[slice_idx, :],
            y=grid_z[slice_idx, :],
            mode='lines+markers',
            name=f'Expiry = {actual_expiry:.3f}',
            line=dict(width=3)
        ))
        
        # Add market data points if available
        if strikes is not None and expiries is not None and ivs is not None:
            # Find points close to this expiry
            expiry_mask = np.abs(np.array(expiries) - actual_expiry) < (max(expiries) - min(expiries)) * 0.05
            if np.any(expiry_mask):
                fig.add_trace(go.Scatter(
                    x=np.array(strikes)[expiry_mask],
                    y=np.array(ivs)[expiry_mask],
                    mode='markers',
                    name='Market Data',
                    marker=dict(size=8, color='red')
                ))
        
        fig.update_layout(
            title=f'Volatility Smile (Expiry = {actual_expiry:.3f} years)',
            xaxis_title='Strike Price',
            yaxis_title='Implied Volatility'
        )
    
    return fig

def plot_vol_surface_comparison(data_sets, method_names, title="Volatility Surface Comparison"):
    """
    Compare multiple volatility surfaces
    
    Parameters:
    -----------
    data_sets : list of tuples
        Each tuple contains (grid_x, grid_y, grid_z)
    method_names : list of str
        Names for each method
    title : str
        Plot title
    
    Returns:
    --------
    plotly.graph_objects.Figure : The comparison figure
    """
    fig = go.Figure()
    
    colors = ['Viridis', 'Plasma', 'Inferno', 'Magma', 'Cividis']
    
    for i, ((grid_x, grid_y, grid_z), method_name) in enumerate(zip(data_sets, method_names)):
        colorscale = colors[i % len(colors)]
        
        surface = go.Surface(
            x=grid_x,
            y=grid_y,
            z=grid_z,
            colorscale=colorscale,
            opacity=0.7,
            name=method_name,
            showscale=i == 0  # Only show colorbar for first surface
        )
        
        fig.add_trace(surface)
    
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='Strike Price',
            yaxis_title='Time to Expiry (Years)',
            zaxis_title='Implied Volatility'
        ),
        width=900,
        height=700
    )
    
    return fig

# Legacy function for backward compatibility
def plot_vol_surface(strikes, expiries, ivs, grid_x, grid_y, grid_z):
    """
    Legacy function - now calls the Plotly version
    """
    return plot_vol_surface_plotly(strikes, expiries, ivs, grid_x, grid_y, grid_z)

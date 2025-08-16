import plotly.graph_objects as go

def plot_vol_surface(strikes, expiries, ivs, grid_x, grid_y, grid_z):
    fig = go.Figure(data=[
        go.Surface(x=grid_x, y=grid_y, z=grid_z, colorscale='Viridis')
    ])
    fig.update_layout(
        title='Implied Volatility Surface',
        scene=dict(
            xaxis_title='Strike',
            yaxis_title='Time to Expiry (Years)',
            zaxis_title='Implied Volatility'
        )
    )
    return fig

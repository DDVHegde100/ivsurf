import numpy as np
from scipy.interpolate import griddata

def interpolate_surface(strikes, expiries, ivs, method='cubic'):
    grid_x, grid_y = np.meshgrid(
        np.linspace(min(strikes), max(strikes), 50),
        np.linspace(min(expiries), max(expiries), 50)
    )
    grid_z = griddata((strikes, expiries), ivs, (grid_x, grid_y), method=method)
    return grid_x, grid_y, grid_z

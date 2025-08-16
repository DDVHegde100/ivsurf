import numpy as np
from scipy.interpolate import griddata, RBFInterpolator, interp2d
from scipy.spatial import distance_matrix
import warnings

def interpolate_surface(strikes, expiries, ivs, method='cubic', grid_size=50):
    """
    Basic interpolation using scipy.interpolate.griddata
    
    Parameters:
    -----------
    strikes : array-like
        Strike prices
    expiries : array-like
        Time to expiries
    ivs : array-like
        Implied volatilities
    method : str, default 'cubic'
        Interpolation method ('linear', 'nearest', 'cubic')
    grid_size : int, default 50
        Size of interpolation grid
    
    Returns:
    --------
    tuple : (grid_x, grid_y, grid_z)
        Interpolated surface grids
    """
    # Create meshgrid for interpolation
    strike_range = np.linspace(min(strikes), max(strikes), grid_size)
    expiry_range = np.linspace(min(expiries), max(expiries), grid_size)
    grid_x, grid_y = np.meshgrid(strike_range, expiry_range)
    
    # Combine input points
    points = np.column_stack((strikes, expiries))
    
    # Perform griddata interpolation
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        grid_z = griddata(points, ivs, (grid_x, grid_y), method=method, fill_value=np.nan)
    
    # Handle NaN values by filling with nearest neighbor
    if np.isnan(grid_z).any():
        grid_z_nearest = griddata(points, ivs, (grid_x, grid_y), method='nearest')
        grid_z = np.where(np.isnan(grid_z), grid_z_nearest, grid_z)
    
    return grid_x, grid_y, grid_z

def interpolate_surface_rbf(strikes, expiries, ivs, function='thin_plate_spline', grid_size=50, smoothing=0.0):
    """
    Advanced interpolation using Radial Basis Functions (RBF)
    
    Parameters:
    -----------
    strikes : array-like
        Strike prices
    expiries : array-like
        Time to expiries
    ivs : array-like
        Implied volatilities
    function : str, default 'thin_plate_spline'
        RBF function ('thin_plate_spline', 'linear', 'cubic', 'quintic', 'multiquadric', 'inverse_multiquadric', 'inverse_quadratic', 'gaussian')
    grid_size : int, default 50
        Size of interpolation grid
    smoothing : float, default 0.0
        Smoothing parameter for RBF interpolation
    
    Returns:
    --------
    tuple : (grid_x, grid_y, grid_z)
        Interpolated surface grids
    """
    # Create meshgrid for interpolation
    strike_range = np.linspace(min(strikes), max(strikes), grid_size)
    expiry_range = np.linspace(min(expiries), max(expiries), grid_size)
    grid_x, grid_y = np.meshgrid(strike_range, expiry_range)
    
    # Prepare input data
    points = np.column_stack((strikes, expiries))
    
    # Create RBF interpolator
    try:
        rbf = RBFInterpolator(points, ivs, kernel=function, smoothing=smoothing)
        
        # Evaluate on grid
        grid_points = np.column_stack((grid_x.ravel(), grid_y.ravel()))
        grid_z_flat = rbf(grid_points)
        grid_z = grid_z_flat.reshape(grid_x.shape)
        
    except Exception as e:
        print(f"RBF interpolation failed: {e}")
        # Fallback to griddata
        return interpolate_surface(strikes, expiries, ivs, method='cubic', grid_size=grid_size)
    
    return grid_x, grid_y, grid_z

def interpolate_surface_bilinear(strikes, expiries, ivs, grid_size=50):
    """
    Bilinear interpolation using interp2d (legacy method)
    
    Parameters:
    -----------
    strikes : array-like
        Strike prices
    expiries : array-like
        Time to expiries
    ivs : array-like
        Implied volatilities
    grid_size : int, default 50
        Size of interpolation grid
    
    Returns:
    --------
    tuple : (grid_x, grid_y, grid_z)
        Interpolated surface grids
    """
    try:
        # Sort data for interp2d
        sorted_indices = np.lexsort((expiries, strikes))
        strikes_sorted = np.array(strikes)[sorted_indices]
        expiries_sorted = np.array(expiries)[sorted_indices]
        ivs_sorted = np.array(ivs)[sorted_indices]
        
        # Create unique sorted arrays
        unique_strikes = np.unique(strikes_sorted)
        unique_expiries = np.unique(expiries_sorted)
        
        # If we have enough data points, try interp2d
        if len(unique_strikes) > 2 and len(unique_expiries) > 2:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                f = interp2d(strikes_sorted, expiries_sorted, ivs_sorted, kind='linear')
                
                # Create grid
                strike_range = np.linspace(min(strikes), max(strikes), grid_size)
                expiry_range = np.linspace(min(expiries), max(expiries), grid_size)
                grid_x, grid_y = np.meshgrid(strike_range, expiry_range)
                
                # Interpolate
                grid_z = f(strike_range, expiry_range)
                
                return grid_x, grid_y, grid_z
        else:
            # Fallback to griddata
            return interpolate_surface(strikes, expiries, ivs, method='linear', grid_size=grid_size)
            
    except Exception as e:
        print(f"Bilinear interpolation failed: {e}")
        # Fallback to griddata
        return interpolate_surface(strikes, expiries, ivs, method='linear', grid_size=grid_size)

def adaptive_interpolation(strikes, expiries, ivs, density_threshold=10, grid_size=50):
    """
    Adaptive interpolation that chooses method based on data density
    
    Parameters:
    -----------
    strikes : array-like
        Strike prices
    expiries : array-like
        Time to expiries
    ivs : array-like
        Implied volatilities
    density_threshold : int, default 10
        Minimum number of points to use advanced methods
    grid_size : int, default 50
        Size of interpolation grid
    
    Returns:
    --------
    tuple : (grid_x, grid_y, grid_z, method_used)
        Interpolated surface grids and method used
    """
    n_points = len(strikes)
    
    # Choose interpolation method based on data density
    if n_points >= 50:
        # Use RBF for dense data
        try:
            grid_x, grid_y, grid_z = interpolate_surface_rbf(strikes, expiries, ivs, 
                                                           function='thin_plate_spline', 
                                                           grid_size=grid_size)
            method_used = "RBF (Thin Plate Spline)"
        except:
            grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                       method='cubic', grid_size=grid_size)
            method_used = "Cubic Griddata"
    elif n_points >= density_threshold:
        # Use cubic interpolation for moderate data
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                   method='cubic', grid_size=grid_size)
        method_used = "Cubic Griddata"
    else:
        # Use linear interpolation for sparse data
        grid_x, grid_y, grid_z = interpolate_surface(strikes, expiries, ivs, 
                                                   method='linear', grid_size=grid_size)
        method_used = "Linear Griddata"
    
    return grid_x, grid_y, grid_z, method_used

def calculate_interpolation_quality(strikes, expiries, ivs, grid_x, grid_y, grid_z):
    """
    Calculate quality metrics for interpolation
    
    Parameters:
    -----------
    strikes, expiries, ivs : array-like
        Original data points
    grid_x, grid_y, grid_z : array-like
        Interpolated grid
    
    Returns:
    --------
    dict : Quality metrics
    """
    # Interpolate back to original points to check accuracy
    points = np.column_stack((strikes, expiries))
    interpolated_ivs = griddata((grid_x.ravel(), grid_y.ravel()), grid_z.ravel(), 
                               points, method='linear')
    
    # Calculate metrics
    valid_mask = ~np.isnan(interpolated_ivs)
    if np.sum(valid_mask) == 0:
        return {"rmse": np.inf, "mae": np.inf, "r_squared": 0.0, "coverage": 0.0}
    
    rmse = np.sqrt(np.mean((ivs[valid_mask] - interpolated_ivs[valid_mask])**2))
    mae = np.mean(np.abs(ivs[valid_mask] - interpolated_ivs[valid_mask]))
    
    # R-squared
    ss_res = np.sum((ivs[valid_mask] - interpolated_ivs[valid_mask])**2)
    ss_tot = np.sum((ivs[valid_mask] - np.mean(ivs[valid_mask]))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # Coverage (percentage of grid points with valid values)
    coverage = np.sum(~np.isnan(grid_z)) / grid_z.size
    
    return {
        "rmse": rmse,
        "mae": mae,
        "r_squared": r_squared,
        "coverage": coverage,
        "valid_points": np.sum(valid_mask),
        "total_points": len(ivs)
    }

#!/usr/bin/env python3
"""
Advanced Surface Interpolation Module
====================================

Bicubic spline interpolation and advanced surface reconstruction
for volatility surfaces with multiple methods and quality assessment

Author: IVSURF Systems
Date: August 19, 2025
"""

import numpy as np
import pandas as pd
from scipy import interpolate
from scipy.spatial.distance import cdist
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel
import warnings
from typing import Tuple, Optional, Dict, List, Union

warnings.filterwarnings('ignore')


class AdvancedSurfaceInterpolator:
    """
    Advanced volatility surface interpolation with multiple methods
    """
    
    def __init__(self):
        self.methods = {
            'linear': self._linear_interpolation,
            'cubic': self._cubic_interpolation,
            'bicubic': self._bicubic_interpolation,
            'rbf': self._rbf_interpolation,
            'kriging': self._kriging_interpolation,
            'adaptive': self._adaptive_interpolation
        }
        
        self.quality_metrics = {}
        
    def interpolate_surface(
        self, 
        strikes: np.ndarray,
        expiries: np.ndarray, 
        volatilities: np.ndarray,
        method: str = 'bicubic',
        target_strikes: Optional[np.ndarray] = None,
        target_expiries: Optional[np.ndarray] = None,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict]:
        """
        Interpolate volatility surface using specified method
        
        Args:
            strikes: Array of strike prices
            expiries: Array of time to expiries
            volatilities: Array of implied volatilities
            method: Interpolation method
            target_strikes: Target strike grid (optional)
            target_expiries: Target expiry grid (optional)
            **kwargs: Method-specific parameters
            
        Returns:
            Tuple of (strike_grid, expiry_grid, vol_grid, quality_metrics)
        """
        
        # Clean input data
        valid_mask = ~(np.isnan(strikes) | np.isnan(expiries) | np.isnan(volatilities))
        strikes_clean = strikes[valid_mask]
        expiries_clean = expiries[valid_mask]
        vols_clean = volatilities[valid_mask]
        
        if len(strikes_clean) < 4:
            raise ValueError("Insufficient valid data points for interpolation")
        
        # Create target grid if not provided
        if target_strikes is None:
            target_strikes = np.linspace(
                strikes_clean.min() * 0.8, 
                strikes_clean.max() * 1.2, 
                50
            )
        
        if target_expiries is None:
            target_expiries = np.linspace(
                max(expiries_clean.min(), 0.01), 
                expiries_clean.max() * 1.1, 
                30
            )
        
        # Perform interpolation
        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}")
        
        strike_grid, expiry_grid, vol_grid = self.methods[method](
            strikes_clean, expiries_clean, vols_clean,
            target_strikes, target_expiries, **kwargs
        )
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(
            strikes_clean, expiries_clean, vols_clean,
            strike_grid, expiry_grid, vol_grid
        )
        
        return strike_grid, expiry_grid, vol_grid, quality_metrics
    
    def _linear_interpolation(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray, 
        vols: np.ndarray,
        target_strikes: np.ndarray, 
        target_expiries: np.ndarray,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Linear interpolation using scipy griddata"""
        
        points = np.column_stack((strikes, expiries))
        strike_grid, expiry_grid = np.meshgrid(target_strikes, target_expiries)
        
        vol_grid = interpolate.griddata(
            points, vols, 
            (strike_grid, expiry_grid), 
            method='linear',
            fill_value=np.nan
        )
        
        return strike_grid, expiry_grid, vol_grid
    
    def _cubic_interpolation(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray, 
        vols: np.ndarray,
        target_strikes: np.ndarray, 
        target_expiries: np.ndarray,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Cubic interpolation using scipy griddata"""
        
        points = np.column_stack((strikes, expiries))
        strike_grid, expiry_grid = np.meshgrid(target_strikes, target_expiries)
        
        vol_grid = interpolate.griddata(
            points, vols, 
            (strike_grid, expiry_grid), 
            method='cubic',
            fill_value=np.nan
        )
        
        # Fill NaN values with linear interpolation
        nan_mask = np.isnan(vol_grid)
        if nan_mask.any():
            vol_grid_linear = interpolate.griddata(
                points, vols, 
                (strike_grid, expiry_grid), 
                method='linear',
                fill_value=vols.mean()
            )
            vol_grid[nan_mask] = vol_grid_linear[nan_mask]
        
        return strike_grid, expiry_grid, vol_grid
    
    def _bicubic_interpolation(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray, 
        vols: np.ndarray,
        target_strikes: np.ndarray, 
        target_expiries: np.ndarray,
        smoothing: float = 0.0,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Bicubic spline interpolation with B-splines
        """
        
        try:
            # Create bicubic spline
            tck = interpolate.bisplrep(
                strikes, expiries, vols, 
                s=smoothing,
                kx=min(3, len(np.unique(strikes)) - 1),
                ky=min(3, len(np.unique(expiries)) - 1)
            )
            
            # Evaluate on target grid
            strike_grid, expiry_grid = np.meshgrid(target_strikes, target_expiries)
            vol_grid = interpolate.bisplev(
                target_strikes, target_expiries, tck
            ).T
            
        except Exception:
            # Fallback to cubic interpolation
            return self._cubic_interpolation(
                strikes, expiries, vols, 
                target_strikes, target_expiries
            )
        
        return strike_grid, expiry_grid, vol_grid
    
    def _rbf_interpolation(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray, 
        vols: np.ndarray,
        target_strikes: np.ndarray, 
        target_expiries: np.ndarray,
        function: str = 'thin_plate',
        epsilon: Optional[float] = None,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Radial Basis Function interpolation
        """
        
        # Normalize coordinates for better conditioning
        strike_norm = (strikes - strikes.min()) / (strikes.max() - strikes.min())
        expiry_norm = (expiries - expiries.min()) / (expiries.max() - expiries.min())
        
        target_strike_norm = (target_strikes - strikes.min()) / (strikes.max() - strikes.min())
        target_expiry_norm = (target_expiries - expiries.min()) / (expiries.max() - expiries.min())
        
        # Create RBF interpolator
        rbf = interpolate.Rbf(
            strike_norm, expiry_norm, vols,
            function=function,
            epsilon=epsilon
        )
        
        # Evaluate on target grid
        strike_grid, expiry_grid = np.meshgrid(target_strikes, target_expiries)
        strike_grid_norm, expiry_grid_norm = np.meshgrid(target_strike_norm, target_expiry_norm)
        
        vol_grid = rbf(strike_grid_norm, expiry_grid_norm)
        
        return strike_grid, expiry_grid, vol_grid
    
    def _kriging_interpolation(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray, 
        vols: np.ndarray,
        target_strikes: np.ndarray, 
        target_expiries: np.ndarray,
        kernel_type: str = 'matern',
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Kriging interpolation using Gaussian Process
        """
        
        # Prepare data
        X = np.column_stack((strikes, expiries))
        y = vols
        
        # Normalize features
        X_mean = X.mean(axis=0)
        X_std = X.std(axis=0)
        X_norm = (X - X_mean) / X_std
        
        # Create kernel
        if kernel_type == 'rbf':
            kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.01)
        elif kernel_type == 'matern':
            kernel = Matern(length_scale=1.0, nu=2.5) + WhiteKernel(noise_level=0.01)
        else:
            kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.01)
        
        # Fit Gaussian Process
        gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            normalize_y=True
        )
        gp.fit(X_norm, y)
        
        # Predict on target grid
        strike_grid, expiry_grid = np.meshgrid(target_strikes, target_expiries)
        X_target = np.column_stack((strike_grid.ravel(), expiry_grid.ravel()))
        X_target_norm = (X_target - X_mean) / X_std
        
        vol_pred, vol_std = gp.predict(X_target_norm, return_std=True)
        vol_grid = vol_pred.reshape(strike_grid.shape)
        
        # Store prediction uncertainty
        self.prediction_std = vol_std.reshape(strike_grid.shape)
        
        return strike_grid, expiry_grid, vol_grid
    
    def _adaptive_interpolation(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray, 
        vols: np.ndarray,
        target_strikes: np.ndarray, 
        target_expiries: np.ndarray,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Adaptive interpolation based on data density and quality
        """
        
        # Calculate data density
        points = np.column_stack((strikes, expiries))
        distances = cdist(points, points)
        np.fill_diagonal(distances, np.inf)
        min_distances = distances.min(axis=1)
        
        # Use different methods based on density
        dense_regions = min_distances < np.percentile(min_distances, 25)
        
        if dense_regions.sum() > len(strikes) * 0.7:
            # Use bicubic for dense data
            return self._bicubic_interpolation(
                strikes, expiries, vols, 
                target_strikes, target_expiries
            )
        else:
            # Use RBF for sparse data
            return self._rbf_interpolation(
                strikes, expiries, vols, 
                target_strikes, target_expiries
            )
    
    def _calculate_quality_metrics(
        self, 
        strikes_orig: np.ndarray,
        expiries_orig: np.ndarray,
        vols_orig: np.ndarray,
        strike_grid: np.ndarray,
        expiry_grid: np.ndarray,
        vol_grid: np.ndarray
    ) -> Dict:
        """Calculate interpolation quality metrics"""
        
        metrics = {}
        
        try:
            # Interpolate back to original points for validation
            points_orig = np.column_stack((strikes_orig, expiries_orig))
            vols_interp = interpolate.griddata(
                np.column_stack((strike_grid.ravel(), expiry_grid.ravel())),
                vol_grid.ravel(),
                points_orig,
                method='linear'
            )
            
            # Remove NaN values for metrics calculation
            valid_mask = ~np.isnan(vols_interp)
            if valid_mask.sum() > 0:
                vols_orig_valid = vols_orig[valid_mask]
                vols_interp_valid = vols_interp[valid_mask]
                
                # Calculate metrics
                mse = np.mean((vols_orig_valid - vols_interp_valid) ** 2)
                mae = np.mean(np.abs(vols_orig_valid - vols_interp_valid))
                r2 = 1 - np.sum((vols_orig_valid - vols_interp_valid) ** 2) / \
                     np.sum((vols_orig_valid - np.mean(vols_orig_valid)) ** 2)
                
                metrics.update({
                    'mse': mse,
                    'mae': mae,
                    'rmse': np.sqrt(mse),
                    'r_squared': r2,
                    'max_error': np.max(np.abs(vols_orig_valid - vols_interp_valid))
                })
            
            # Surface smoothness metrics
            grad_x = np.gradient(vol_grid, axis=1)
            grad_y = np.gradient(vol_grid, axis=0)
            smoothness = np.mean(grad_x**2 + grad_y**2)
            
            metrics.update({
                'smoothness': smoothness,
                'data_coverage': valid_mask.sum() / len(vols_orig),
                'grid_size': vol_grid.shape,
                'nan_ratio': np.isnan(vol_grid).sum() / vol_grid.size
            })
            
        except Exception as e:
            metrics['error'] = str(e)
        
        return metrics


class SurfaceSmoothing:
    """
    Advanced surface smoothing techniques
    """
    
    @staticmethod
    def gaussian_smooth(
        vol_grid: np.ndarray, 
        sigma: float = 1.0
    ) -> np.ndarray:
        """Apply Gaussian smoothing to surface"""
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(vol_grid, sigma=sigma)
    
    @staticmethod
    def bilateral_smooth(
        vol_grid: np.ndarray,
        sigma_spatial: float = 1.0,
        sigma_intensity: float = 0.1
    ) -> np.ndarray:
        """Apply bilateral filtering to preserve edges"""
        try:
            from skimage.restoration import denoise_bilateral
            return denoise_bilateral(
                vol_grid,
                sigma_spatial=sigma_spatial,
                sigma_color=sigma_intensity
            )
        except ImportError:
            # Fallback to Gaussian
            return SurfaceSmoothing.gaussian_smooth(vol_grid, sigma_spatial)
    
    @staticmethod
    def total_variation_smooth(
        vol_grid: np.ndarray,
        weight: float = 0.1,
        max_iter: int = 100
    ) -> np.ndarray:
        """Total variation denoising"""
        try:
            from skimage.restoration import denoise_tv_chambolle
            return denoise_tv_chambolle(
                vol_grid,
                weight=weight,
                max_num_iter=max_iter
            )
        except ImportError:
            return vol_grid


def interpolate_surface(
    strikes: np.ndarray,
    expiries: np.ndarray,
    volatilities: np.ndarray,
    method: str = 'bicubic',
    **kwargs
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convenience function for surface interpolation
    """
    interpolator = AdvancedSurfaceInterpolator()
    strike_grid, expiry_grid, vol_grid, _ = interpolator.interpolate_surface(
        strikes, expiries, volatilities, method=method, **kwargs
    )
    return strike_grid, expiry_grid, vol_grid


def adaptive_interpolation(
    strikes: np.ndarray,
    expiries: np.ndarray,
    volatilities: np.ndarray,
    **kwargs
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Adaptive interpolation based on data characteristics
    """
    interpolator = AdvancedSurfaceInterpolator()
    strike_grid, expiry_grid, vol_grid, _ = interpolator.interpolate_surface(
        strikes, expiries, volatilities, method='adaptive', **kwargs
    )
    return strike_grid, expiry_grid, vol_grid

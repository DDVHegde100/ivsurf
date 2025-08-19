#!/usr/bin/env python3
"""
Surface Smoothing Module
=======================

Advanced surface smoothing techniques including Gaussian Process,
bilateral filtering, total variation denoising, and adaptive smoothing

Author: IVSURF Systems
Date: August 19, 2025
"""

import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.ndimage import gaussian_filter, uniform_filter
from scipy.signal import medfilt2d
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
from typing import Tuple, Dict, Optional, Union, List
import warnings

from .gaussian_process import VolatilitySurfaceGP

warnings.filterwarnings('ignore')


class SurfaceSmoothingEngine:
    """
    Comprehensive surface smoothing engine with multiple techniques
    """
    
    def __init__(self):
        self.smoothing_methods = {
            'gaussian': self._gaussian_smoothing,
            'bilateral': self._bilateral_smoothing,
            'total_variation': self._total_variation_smoothing,
            'adaptive': self._adaptive_smoothing,
            'gaussian_process': self._gp_smoothing,
            'median': self._median_smoothing,
            'wiener': self._wiener_smoothing,
            'anisotropic': self._anisotropic_smoothing
        }
        
        self.smoothing_stats = {}
        
    def smooth_surface(
        self,
        vol_surface: np.ndarray,
        method: str = 'gaussian_process',
        strikes: Optional[np.ndarray] = None,
        expiries: Optional[np.ndarray] = None,
        original_points: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None,
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply smoothing to volatility surface
        
        Args:
            vol_surface: 2D volatility surface array
            method: Smoothing method to use
            strikes: Strike prices corresponding to surface
            expiries: Expiries corresponding to surface  
            original_points: (strikes, expiries, vols) for GP methods
            **kwargs: Method-specific parameters
            
        Returns:
            Smoothed surface and smoothing statistics
        """
        
        if method not in self.smoothing_methods:
            raise ValueError(f"Unknown smoothing method: {method}")
        
        # Apply smoothing
        if method == 'gaussian_process' and original_points is not None:
            smoothed_surface, stats = self.smoothing_methods[method](
                vol_surface, strikes, expiries, original_points, **kwargs
            )
        else:
            smoothed_surface, stats = self.smoothing_methods[method](
                vol_surface, **kwargs
            )
        
        # Calculate general smoothing metrics
        general_stats = self._calculate_smoothing_metrics(vol_surface, smoothed_surface)
        stats.update(general_stats)
        
        self.smoothing_stats = stats
        
        return smoothed_surface, stats
    
    def _gaussian_smoothing(
        self, 
        surface: np.ndarray, 
        sigma: float = 1.0,
        mode: str = 'reflect',
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """Apply Gaussian smoothing"""
        
        smoothed = gaussian_filter(surface, sigma=sigma, mode=mode)
        
        stats = {
            'method': 'gaussian',
            'sigma': sigma,
            'mode': mode
        }
        
        return smoothed, stats
    
    def _bilateral_smoothing(
        self,
        surface: np.ndarray,
        sigma_spatial: float = 1.0,
        sigma_intensity: float = 0.1,
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply bilateral filtering to preserve edges while smoothing
        """
        
        try:
            # Try to use scikit-image if available
            from skimage.restoration import denoise_bilateral
            
            smoothed = denoise_bilateral(
                surface,
                sigma_spatial=sigma_spatial,
                sigma_color=sigma_intensity,
                channel_axis=None
            )
            
            stats = {
                'method': 'bilateral',
                'sigma_spatial': sigma_spatial,
                'sigma_intensity': sigma_intensity,
                'implementation': 'skimage'
            }
            
        except ImportError:
            # Fallback implementation
            smoothed = self._bilateral_filter_manual(
                surface, sigma_spatial, sigma_intensity
            )
            
            stats = {
                'method': 'bilateral',
                'sigma_spatial': sigma_spatial,
                'sigma_intensity': sigma_intensity,
                'implementation': 'manual'
            }
        
        return smoothed, stats
    
    def _bilateral_filter_manual(
        self,
        surface: np.ndarray,
        sigma_spatial: float,
        sigma_intensity: float
    ) -> np.ndarray:
        """Manual implementation of bilateral filter"""
        
        rows, cols = surface.shape
        filtered = np.zeros_like(surface)
        
        # Define spatial kernel size
        kernel_size = int(2 * np.ceil(2 * sigma_spatial) + 1)
        half_size = kernel_size // 2
        
        # Pad surface
        padded = np.pad(surface, half_size, mode='reflect')
        
        for i in range(rows):
            for j in range(cols):
                # Extract local patch
                patch = padded[i:i+kernel_size, j:j+kernel_size]
                center_val = surface[i, j]
                
                # Calculate spatial weights
                y, x = np.ogrid[-half_size:half_size+1, -half_size:half_size+1]
                spatial_weights = np.exp(-(x**2 + y**2) / (2 * sigma_spatial**2))
                
                # Calculate intensity weights
                intensity_weights = np.exp(-((patch - center_val)**2) / (2 * sigma_intensity**2))
                
                # Combine weights
                weights = spatial_weights * intensity_weights
                weights_sum = np.sum(weights)
                
                if weights_sum > 0:
                    filtered[i, j] = np.sum(weights * patch) / weights_sum
                else:
                    filtered[i, j] = center_val
        
        return filtered
    
    def _total_variation_smoothing(
        self,
        surface: np.ndarray,
        weight: float = 0.1,
        max_iter: int = 100,
        tol: float = 1e-3,
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply total variation denoising to preserve sharp features
        """
        
        try:
            # Try scikit-image implementation
            from skimage.restoration import denoise_tv_chambolle
            
            smoothed = denoise_tv_chambolle(
                surface,
                weight=weight,
                max_num_iter=max_iter
            )
            
            stats = {
                'method': 'total_variation',
                'weight': weight,
                'max_iter': max_iter,
                'implementation': 'skimage'
            }
            
        except ImportError:
            # Manual implementation using gradient descent
            smoothed = self._total_variation_manual(surface, weight, max_iter, tol)
            
            stats = {
                'method': 'total_variation',
                'weight': weight,
                'max_iter': max_iter,
                'tolerance': tol,
                'implementation': 'manual'
            }
        
        return smoothed, stats
    
    def _total_variation_manual(
        self,
        surface: np.ndarray,
        weight: float,
        max_iter: int,
        tol: float
    ) -> np.ndarray:
        """Manual implementation of total variation denoising"""
        
        u = surface.copy().astype(float)
        rows, cols = u.shape
        
        for iteration in range(max_iter):
            u_old = u.copy()
            
            # Calculate gradients
            ux = np.diff(u, axis=1, append=u[:, [-1]])
            uy = np.diff(u, axis=0, append=u[[-1], :])
            
            # Calculate gradient magnitude
            grad_mag = np.sqrt(ux**2 + uy**2 + 1e-8)
            
            # Calculate divergence of normalized gradient
            ux_norm = ux / grad_mag
            uy_norm = uy / grad_mag
            
            div_x = np.diff(ux_norm, axis=1, prepend=ux_norm[:, [0]])
            div_y = np.diff(uy_norm, axis=0, prepend=uy_norm[[0], :])
            
            div = div_x + div_y
            
            # Update step
            dt = 0.125  # Time step
            u = u + dt * (weight * div - (u - surface))
            
            # Check convergence
            if np.max(np.abs(u - u_old)) < tol:
                break
        
        return u
    
    def _adaptive_smoothing(
        self,
        surface: np.ndarray,
        edge_threshold: float = 0.1,
        smooth_sigma: float = 1.0,
        edge_sigma: float = 0.1,
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply adaptive smoothing based on local surface characteristics
        """
        
        # Calculate local gradients
        grad_x = np.gradient(surface, axis=1)
        grad_y = np.gradient(surface, axis=0)
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Identify edge regions
        edge_mask = grad_magnitude > edge_threshold
        
        # Apply different smoothing to edge and smooth regions
        smoothed = surface.copy()
        
        # Smooth regions: stronger smoothing
        smooth_mask = ~edge_mask
        if np.any(smooth_mask):
            smoothed[smooth_mask] = gaussian_filter(surface, sigma=smooth_sigma)[smooth_mask]
        
        # Edge regions: weaker smoothing
        if np.any(edge_mask):
            smoothed[edge_mask] = gaussian_filter(surface, sigma=edge_sigma)[edge_mask]
        
        stats = {
            'method': 'adaptive',
            'edge_threshold': edge_threshold,
            'smooth_sigma': smooth_sigma,
            'edge_sigma': edge_sigma,
            'edge_ratio': np.mean(edge_mask)
        }
        
        return smoothed, stats
    
    def _gp_smoothing(
        self,
        surface: np.ndarray,
        strikes: np.ndarray,
        expiries: np.ndarray,
        original_points: Tuple[np.ndarray, np.ndarray, np.ndarray],
        kernel_type: str = 'matern',
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply Gaussian Process smoothing using original data points
        """
        
        strike_orig, expiry_orig, vol_orig = original_points
        
        # Initialize GP
        gp = VolatilitySurfaceGP(
            kernel_type=kernel_type,
            n_restarts=kwargs.get('n_restarts', 5)
        )
        
        # Fit GP to original data
        gp.fit(strike_orig, expiry_orig, vol_orig)
        
        # Create grid for prediction
        strike_grid, expiry_grid = np.meshgrid(strikes, expiries)
        
        # Predict on grid
        smoothed_surface, uncertainty = gp.predict_surface(
            strike_grid, expiry_grid, return_std=True
        )
        
        # Get GP statistics
        gp_stats = gp.calculate_smoothing_metrics()
        hyperparams = gp.get_hyperparameters()
        
        stats = {
            'method': 'gaussian_process',
            'kernel_type': kernel_type,
            'mean_uncertainty': np.mean(uncertainty),
            'max_uncertainty': np.max(uncertainty),
            'gp_metrics': gp_stats,
            'hyperparameters': hyperparams
        }
        
        return smoothed_surface, stats
    
    def _median_smoothing(
        self,
        surface: np.ndarray,
        kernel_size: int = 3,
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """Apply median filtering for robust smoothing"""
        
        # Ensure odd kernel size
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        smoothed = medfilt2d(surface, kernel_size=kernel_size)
        
        stats = {
            'method': 'median',
            'kernel_size': kernel_size
        }
        
        return smoothed, stats
    
    def _wiener_smoothing(
        self,
        surface: np.ndarray,
        noise_var: Optional[float] = None,
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply Wiener filtering for optimal smoothing given noise characteristics
        """
        
        try:
            from scipy.signal import wiener
            
            # Estimate noise variance if not provided
            if noise_var is None:
                # Use Laplacian method for noise estimation
                laplacian = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])
                convolved = ndimage.convolve(surface, laplacian)
                noise_var = np.var(convolved) * 0.5
            
            # Apply Wiener filter
            smoothed = wiener(surface, noise=noise_var)
            
            stats = {
                'method': 'wiener',
                'noise_variance': noise_var
            }
            
        except ImportError:
            # Fallback to Gaussian smoothing
            smoothed = gaussian_filter(surface, sigma=1.0)
            stats = {
                'method': 'wiener_fallback',
                'fallback_to': 'gaussian'
            }
        
        return smoothed, stats
    
    def _anisotropic_smoothing(
        self,
        surface: np.ndarray,
        kappa: float = 50.0,
        gamma: float = 0.1,
        n_iter: int = 10,
        **kwargs
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply anisotropic diffusion smoothing (Perona-Malik)
        """
        
        u = surface.copy().astype(float)
        
        for _ in range(n_iter):
            # Calculate gradients
            ux = np.diff(u, axis=1, append=u[:, [-1]])
            uy = np.diff(u, axis=0, append=u[[-1], :])
            
            # Calculate diffusion coefficients
            c_x = np.exp(-(ux / kappa)**2)
            c_y = np.exp(-(uy / kappa)**2)
            
            # Calculate divergence
            div_x = np.diff(c_x * ux, axis=1, prepend=np.zeros((u.shape[0], 1)))
            div_y = np.diff(c_y * uy, axis=0, prepend=np.zeros((1, u.shape[1])))
            
            # Update
            u = u + gamma * (div_x + div_y)
        
        stats = {
            'method': 'anisotropic',
            'kappa': kappa,
            'gamma': gamma,
            'n_iterations': n_iter
        }
        
        return u, stats
    
    def _calculate_smoothing_metrics(
        self,
        original: np.ndarray,
        smoothed: np.ndarray
    ) -> Dict[str, float]:
        """Calculate general smoothing quality metrics"""
        
        # Remove NaN values for calculations
        valid_mask = ~(np.isnan(original) | np.isnan(smoothed))
        if not np.any(valid_mask):
            return {'error': 'No valid data for metrics calculation'}
        
        orig_valid = original[valid_mask]
        smooth_valid = smoothed[valid_mask]
        
        # Basic metrics
        mse = np.mean((orig_valid - smooth_valid)**2)
        mae = np.mean(np.abs(orig_valid - smooth_valid))
        
        # Correlation
        correlation = np.corrcoef(orig_valid, smooth_valid)[0, 1]
        
        # Smoothness metrics
        orig_roughness = self._calculate_roughness(original)
        smooth_roughness = self._calculate_roughness(smoothed)
        smoothness_improvement = (orig_roughness - smooth_roughness) / orig_roughness
        
        # Gradient preservation
        orig_grad = np.gradient(original)
        smooth_grad = np.gradient(smoothed)
        gradient_preservation = np.corrcoef(
            np.concatenate([g.ravel() for g in orig_grad]),
            np.concatenate([g.ravel() for g in smooth_grad])
        )[0, 1]
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': np.sqrt(mse),
            'correlation': correlation,
            'original_roughness': orig_roughness,
            'smoothed_roughness': smooth_roughness,
            'smoothness_improvement': smoothness_improvement,
            'gradient_preservation': gradient_preservation
        }
    
    def _calculate_roughness(self, surface: np.ndarray) -> float:
        """Calculate surface roughness using total variation"""
        
        grad_x = np.gradient(surface, axis=1)
        grad_y = np.gradient(surface, axis=0)
        
        # Total variation
        tv = np.sum(np.sqrt(grad_x**2 + grad_y**2))
        
        # Normalize by surface area
        roughness = tv / surface.size
        
        return roughness
    
    def compare_smoothing_methods(
        self,
        surface: np.ndarray,
        methods: List[str] = None,
        **kwargs
    ) -> Dict[str, Dict]:
        """
        Compare different smoothing methods on the same surface
        
        Args:
            surface: Input surface to smooth
            methods: List of methods to compare
            **kwargs: Parameters for smoothing methods
            
        Returns:
            Dictionary with results for each method
        """
        
        if methods is None:
            methods = ['gaussian', 'bilateral', 'total_variation', 'adaptive', 'median']
        
        results = {}
        
        for method in methods:
            try:
                smoothed, stats = self.smooth_surface(surface, method=method, **kwargs)
                results[method] = {
                    'smoothed_surface': smoothed,
                    'statistics': stats
                }
            except Exception as e:
                results[method] = {
                    'error': str(e)
                }
        
        return results


class AdaptiveSurfaceSmoothing:
    """
    Adaptive smoothing that adjusts parameters based on local surface characteristics
    """
    
    def __init__(self):
        self.base_smoother = SurfaceSmoothingEngine()
    
    def adaptive_smooth(
        self,
        surface: np.ndarray,
        strikes: Optional[np.ndarray] = None,
        expiries: Optional[np.ndarray] = None,
        adaptation_method: str = 'gradient_based'
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply adaptive smoothing based on local surface characteristics
        
        Args:
            surface: Input volatility surface
            strikes: Strike prices (optional)
            expiries: Time to expiries (optional)
            adaptation_method: Method for adapting smoothing parameters
            
        Returns:
            Adaptively smoothed surface and statistics
        """
        
        if adaptation_method == 'gradient_based':
            return self._gradient_based_adaptive_smoothing(surface)
        elif adaptation_method == 'curvature_based':
            return self._curvature_based_adaptive_smoothing(surface)
        elif adaptation_method == 'noise_based':
            return self._noise_based_adaptive_smoothing(surface)
        else:
            raise ValueError(f"Unknown adaptation method: {adaptation_method}")
    
    def _gradient_based_adaptive_smoothing(
        self, 
        surface: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """Adapt smoothing based on local gradients"""
        
        # Calculate gradients
        grad_x = np.gradient(surface, axis=1)
        grad_y = np.gradient(surface, axis=0)
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Define smoothing parameter based on gradient
        max_grad = np.percentile(grad_magnitude, 95)
        min_sigma, max_sigma = 0.1, 2.0
        
        # Adaptive sigma: low where gradients are high, high where gradients are low
        sigma_map = max_sigma - (max_sigma - min_sigma) * (grad_magnitude / max_grad)
        sigma_map = np.clip(sigma_map, min_sigma, max_sigma)
        
        # Apply adaptive Gaussian smoothing
        smoothed = self._adaptive_gaussian_smooth(surface, sigma_map)
        
        stats = {
            'method': 'gradient_based_adaptive',
            'mean_sigma': np.mean(sigma_map),
            'std_sigma': np.std(sigma_map),
            'min_sigma': np.min(sigma_map),
            'max_sigma': np.max(sigma_map)
        }
        
        return smoothed, stats
    
    def _curvature_based_adaptive_smoothing(
        self, 
        surface: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """Adapt smoothing based on local curvature"""
        
        # Calculate second derivatives (curvature)
        d2_dx2 = np.gradient(np.gradient(surface, axis=1), axis=1)
        d2_dy2 = np.gradient(np.gradient(surface, axis=0), axis=0)
        d2_dxdy = np.gradient(np.gradient(surface, axis=1), axis=0)
        
        # Mean curvature
        mean_curvature = np.abs(d2_dx2 + d2_dy2) / 2
        
        # Gaussian curvature
        gaussian_curvature = np.abs(d2_dx2 * d2_dy2 - d2_dxdy**2)
        
        # Combined curvature measure
        curvature = mean_curvature + gaussian_curvature
        
        # Adaptive smoothing based on curvature
        max_curv = np.percentile(curvature, 95)
        min_sigma, max_sigma = 0.1, 2.0
        
        sigma_map = min_sigma + (max_sigma - min_sigma) * (curvature / max_curv)
        sigma_map = np.clip(sigma_map, min_sigma, max_sigma)
        
        smoothed = self._adaptive_gaussian_smooth(surface, sigma_map)
        
        stats = {
            'method': 'curvature_based_adaptive',
            'mean_curvature': np.mean(curvature),
            'max_curvature': np.max(curvature),
            'mean_sigma': np.mean(sigma_map)
        }
        
        return smoothed, stats
    
    def _noise_based_adaptive_smoothing(
        self, 
        surface: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """Adapt smoothing based on estimated local noise levels"""
        
        # Estimate local noise using local standard deviation
        from scipy.ndimage import uniform_filter
        
        # Local mean and variance
        local_mean = uniform_filter(surface, size=3)
        local_var = uniform_filter(surface**2, size=3) - local_mean**2
        
        # Noise estimate (local standard deviation)
        noise_estimate = np.sqrt(np.maximum(local_var, 0))
        
        # Adaptive smoothing: more smoothing where noise is higher
        max_noise = np.percentile(noise_estimate, 95)
        min_sigma, max_sigma = 0.1, 2.0
        
        sigma_map = min_sigma + (max_sigma - min_sigma) * (noise_estimate / max_noise)
        sigma_map = np.clip(sigma_map, min_sigma, max_sigma)
        
        smoothed = self._adaptive_gaussian_smooth(surface, sigma_map)
        
        stats = {
            'method': 'noise_based_adaptive',
            'mean_noise': np.mean(noise_estimate),
            'max_noise': np.max(noise_estimate),
            'mean_sigma': np.mean(sigma_map)
        }
        
        return smoothed, stats
    
    def _adaptive_gaussian_smooth(
        self, 
        surface: np.ndarray, 
        sigma_map: np.ndarray
    ) -> np.ndarray:
        """Apply Gaussian smoothing with spatially varying sigma"""
        
        smoothed = np.zeros_like(surface)
        
        # Use discrete sigma values for efficiency
        sigma_values = np.unique(np.round(sigma_map, 1))
        
        for sigma in sigma_values:
            mask = np.abs(sigma_map - sigma) < 0.05  # Small tolerance
            if np.any(mask):
                # Apply Gaussian filter with this sigma
                temp_smooth = gaussian_filter(surface, sigma=sigma)
                smoothed[mask] = temp_smooth[mask]
        
        return smoothed


def smooth_volatility_surface(
    surface: np.ndarray,
    method: str = 'gaussian_process',
    **kwargs
) -> Tuple[np.ndarray, Dict]:
    """
    Convenience function for surface smoothing
    
    Args:
        surface: Volatility surface to smooth
        method: Smoothing method
        **kwargs: Method-specific parameters
        
    Returns:
        Smoothed surface and statistics
    """
    smoother = SurfaceSmoothingEngine()
    return smoother.smooth_surface(surface, method=method, **kwargs)

#!/usr/bin/env python3
"""
Gaussian Process Surface Smoothing Module
========================================

Advanced Gaussian Process regression for volatility surface smoothing
with hyperparameter optimization and uncertainty quantification

Author: IVSURF Systems
Date: August 19, 2025
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.linalg import cholesky, solve_triangular
from scipy.spatial.distance import cdist
import warnings
from typing import Tuple, Dict, Optional, Union, Callable
import logging

warnings.filterwarnings('ignore')


class KernelFunction:
    """Base class for kernel functions"""
    
    def __init__(self):
        self.hyperparameters = {}
    
    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        raise NotImplementedError
    
    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> Dict[str, np.ndarray]:
        raise NotImplementedError


class RBFKernel(KernelFunction):
    """
    Radial Basis Function (Gaussian) kernel
    k(x1, x2) = σ² * exp(-||x1 - x2||² / (2 * l²))
    """
    
    def __init__(self, length_scale: float = 1.0, variance: float = 1.0):
        super().__init__()
        self.length_scale = length_scale
        self.variance = variance
        self.hyperparameters = {
            'length_scale': length_scale,
            'variance': variance
        }
    
    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute RBF kernel matrix"""
        # Ensure inputs are 2D
        if X1.ndim == 1:
            X1 = X1.reshape(-1, 1)
        if X2.ndim == 1:
            X2 = X2.reshape(-1, 1)
        
        # Compute squared distances
        sq_dists = cdist(X1 / self.length_scale, X2 / self.length_scale, 'sqeuclidean')
        
        # Compute kernel matrix
        K = self.variance * np.exp(-0.5 * sq_dists)
        
        return K
    
    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute gradients with respect to hyperparameters"""
        K = self(X1, X2)
        
        # Gradient w.r.t. variance
        grad_variance = K / self.variance
        
        # Gradient w.r.t. length scale
        if X1.ndim == 1:
            X1 = X1.reshape(-1, 1)
        if X2.ndim == 1:
            X2 = X2.reshape(-1, 1)
        
        sq_dists = cdist(X1 / self.length_scale, X2 / self.length_scale, 'sqeuclidean')
        grad_length_scale = K * sq_dists / self.length_scale
        
        return {
            'variance': grad_variance,
            'length_scale': grad_length_scale
        }


class MaternKernel(KernelFunction):
    """
    Matérn kernel with nu = 2.5
    More flexible than RBF, allows for non-smooth functions
    """
    
    def __init__(self, length_scale: float = 1.0, variance: float = 1.0, nu: float = 2.5):
        super().__init__()
        self.length_scale = length_scale
        self.variance = variance
        self.nu = nu
        self.hyperparameters = {
            'length_scale': length_scale,
            'variance': variance,
            'nu': nu
        }
    
    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute Matérn kernel matrix"""
        if X1.ndim == 1:
            X1 = X1.reshape(-1, 1)
        if X2.ndim == 1:
            X2 = X2.reshape(-1, 1)
        
        # Compute distances
        dists = cdist(X1 / self.length_scale, X2 / self.length_scale)
        
        if self.nu == 0.5:
            # Exponential kernel
            K = self.variance * np.exp(-dists)
        elif self.nu == 1.5:
            sqrt3_dists = np.sqrt(3) * dists
            K = self.variance * (1 + sqrt3_dists) * np.exp(-sqrt3_dists)
        elif self.nu == 2.5:
            sqrt5_dists = np.sqrt(5) * dists
            K = self.variance * (1 + sqrt5_dists + (5/3) * dists**2) * np.exp(-sqrt5_dists)
        else:
            # General case (more expensive)
            from scipy.special import gamma, kv
            if np.any(dists > 0):
                sqrt_nu_dists = np.sqrt(2 * self.nu) * dists
                K = np.zeros_like(dists)
                non_zero = dists > 0
                K[non_zero] = (2**(1-self.nu) / gamma(self.nu)) * \
                             (sqrt_nu_dists[non_zero]**self.nu) * \
                             kv(self.nu, sqrt_nu_dists[non_zero])
                K[dists == 0] = 1.0
                K *= self.variance
            else:
                K = self.variance * np.ones_like(dists)
        
        return K
    
    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute gradients (simplified for nu=2.5)"""
        K = self(X1, X2)
        
        # Gradient w.r.t. variance
        grad_variance = K / self.variance
        
        # For nu=2.5 case
        if X1.ndim == 1:
            X1 = X1.reshape(-1, 1)
        if X2.ndim == 1:
            X2 = X2.reshape(-1, 1)
        
        dists = cdist(X1 / self.length_scale, X2 / self.length_scale)
        sqrt5_dists = np.sqrt(5) * dists
        
        # Gradient w.r.t. length scale (for nu=2.5)
        grad_length_scale = K * (5/3) * dists**2 / self.length_scale
        
        return {
            'variance': grad_variance,
            'length_scale': grad_length_scale
        }


class WhiteNoiseKernel(KernelFunction):
    """White noise kernel for modeling observation noise"""
    
    def __init__(self, noise_level: float = 1.0):
        super().__init__()
        self.noise_level = noise_level
        self.hyperparameters = {'noise_level': noise_level}
    
    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute white noise kernel (diagonal only)"""
        if X1.shape[0] == X2.shape[0] and np.allclose(X1, X2):
            return self.noise_level * np.eye(X1.shape[0])
        else:
            return np.zeros((X1.shape[0], X2.shape[0]))
    
    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> Dict[str, np.ndarray]:
        """Gradient w.r.t. noise level"""
        K = self(X1, X2)
        grad_noise = K / self.noise_level if self.noise_level > 0 else np.zeros_like(K)
        return {'noise_level': grad_noise}


class CompositeKernel(KernelFunction):
    """Composite kernel for combining multiple kernels"""
    
    def __init__(self, kernels: list, operators: list = None):
        super().__init__()
        self.kernels = kernels
        self.operators = operators or ['+'] * (len(kernels) - 1)
        
        # Combine hyperparameters
        self.hyperparameters = {}
        for i, kernel in enumerate(kernels):
            for key, value in kernel.hyperparameters.items():
                self.hyperparameters[f'kernel_{i}_{key}'] = value
    
    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute composite kernel"""
        if not self.kernels:
            return np.zeros((X1.shape[0], X2.shape[0]))
        
        K = self.kernels[0](X1, X2)
        
        for i, (kernel, op) in enumerate(zip(self.kernels[1:], self.operators)):
            K_next = kernel(X1, X2)
            if op == '+':
                K = K + K_next
            elif op == '*':
                K = K * K_next
            else:
                raise ValueError(f"Unknown operator: {op}")
        
        return K


class GaussianProcessRegressor:
    """
    Gaussian Process Regressor for volatility surface smoothing
    """
    
    def __init__(
        self,
        kernel: KernelFunction = None,
        alpha: float = 1e-10,
        optimizer: str = 'fmin_l_bfgs_b',
        n_restarts_optimizer: int = 5,
        normalize_y: bool = True,
        copy_X_train: bool = True,
        random_state: Optional[int] = None
    ):
        """
        Initialize Gaussian Process Regressor
        
        Args:
            kernel: Kernel function to use
            alpha: Regularization parameter
            optimizer: Optimization method for hyperparameters
            n_restarts_optimizer: Number of random restarts for optimization
            normalize_y: Whether to normalize target values
            copy_X_train: Whether to copy training data
            random_state: Random seed for reproducibility
        """
        self.kernel = kernel or RBFKernel()
        self.alpha = alpha
        self.optimizer = optimizer
        self.n_restarts_optimizer = n_restarts_optimizer
        self.normalize_y = normalize_y
        self.copy_X_train = copy_X_train
        self.random_state = random_state
        
        # Set random seed
        if random_state is not None:
            np.random.seed(random_state)
        
        # Training data
        self.X_train_ = None
        self.y_train_ = None
        self.y_train_mean_ = 0.0
        self.y_train_std_ = 1.0
        
        # Fitted parameters
        self.L_ = None
        self.alpha_ = None
        self.log_marginal_likelihood_value_ = None
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'GaussianProcessRegressor':
        """
        Fit the Gaussian Process model
        
        Args:
            X: Training inputs of shape (n_samples, n_features)
            y: Training targets of shape (n_samples,)
        """
        X = np.asarray(X)
        y = np.asarray(y)
        
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        # Store training data
        if self.copy_X_train:
            self.X_train_ = X.copy()
        else:
            self.X_train_ = X
        
        # Normalize targets if requested
        if self.normalize_y:
            self.y_train_mean_ = np.mean(y)
            self.y_train_std_ = np.std(y)
            if self.y_train_std_ == 0:
                self.y_train_std_ = 1.0
            self.y_train_ = (y - self.y_train_mean_) / self.y_train_std_
        else:
            self.y_train_ = y.copy()
        
        # Optimize hyperparameters
        if self.optimizer:
            self._optimize_hyperparameters()
        
        # Compute training kernel matrix and Cholesky decomposition
        K = self.kernel(self.X_train_, self.X_train_)
        K[np.diag_indices_from(K)] += self.alpha
        
        try:
            self.L_ = cholesky(K, lower=True)
        except np.linalg.LinAlgError:
            # If Cholesky fails, add more regularization
            K[np.diag_indices_from(K)] += 1e-6
            self.L_ = cholesky(K, lower=True)
        
        # Solve for alpha coefficients
        self.alpha_ = solve_triangular(
            self.L_, self.y_train_, lower=True
        )
        
        return self
    
    def predict(
        self, 
        X: np.ndarray, 
        return_std: bool = False, 
        return_cov: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Make predictions with the fitted GP
        
        Args:
            X: Test inputs of shape (n_samples, n_features)
            return_std: Whether to return prediction standard deviation
            return_cov: Whether to return full covariance matrix
            
        Returns:
            Predictions and optionally uncertainties
        """
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        # Compute kernel matrices
        K_star = self.kernel(self.X_train_, X)  # (n_train, n_test)
        
        # Compute mean prediction
        v = solve_triangular(self.L_, K_star, lower=True)
        y_mean = v.T @ self.alpha_
        
        # Denormalize if necessary
        if self.normalize_y:
            y_mean = y_mean * self.y_train_std_ + self.y_train_mean_
        
        if not (return_std or return_cov):
            return y_mean
        
        # Compute predictive variance
        K_star_star = self.kernel(X, X)
        y_cov = K_star_star - v.T @ v
        
        # Ensure positive semi-definite
        y_cov = np.clip(y_cov, 0, None)
        
        if self.normalize_y:
            y_cov *= self.y_train_std_**2
        
        if return_cov:
            return y_mean, y_cov
        else:
            y_std = np.sqrt(np.diag(y_cov))
            return y_mean, y_std
    
    def log_marginal_likelihood(
        self, 
        theta: Optional[np.ndarray] = None,
        eval_gradient: bool = False
    ) -> Union[float, Tuple[float, np.ndarray]]:
        """
        Compute log marginal likelihood of the data
        
        Args:
            theta: Hyperparameters (if None, use current values)
            eval_gradient: Whether to compute gradient
            
        Returns:
            Log marginal likelihood and optionally gradient
        """
        if theta is not None:
            self._set_hyperparameters(theta)
        
        # Compute kernel matrix
        K = self.kernel(self.X_train_, self.X_train_)
        K[np.diag_indices_from(K)] += self.alpha
        
        try:
            L = cholesky(K, lower=True)
        except np.linalg.LinAlgError:
            return -np.inf if not eval_gradient else (-np.inf, np.zeros(len(theta)))
        
        # Compute log marginal likelihood
        alpha = solve_triangular(L, self.y_train_, lower=True)
        
        log_likelihood = -0.5 * np.dot(alpha, alpha)
        log_likelihood -= np.sum(np.log(np.diag(L)))
        log_likelihood -= 0.5 * len(self.y_train_) * np.log(2 * np.pi)
        
        if not eval_gradient:
            return log_likelihood
        
        # Compute gradient (simplified)
        # This is a basic implementation - could be made more sophisticated
        gradient = np.zeros(len(theta))
        
        return log_likelihood, gradient
    
    def _optimize_hyperparameters(self):
        """Optimize kernel hyperparameters using marginal likelihood"""
        
        def objective(theta):
            return -self.log_marginal_likelihood(theta)
        
        # Get initial hyperparameters
        initial_theta = self._get_hyperparameters()
        
        # Set bounds (log scale)
        bounds = [(1e-5, 1e5) for _ in initial_theta]
        
        best_result = None
        best_value = np.inf
        
        # Multiple random restarts
        for _ in range(self.n_restarts_optimizer):
            if _ == 0:
                theta_initial = initial_theta
            else:
                # Random initialization
                theta_initial = np.random.uniform(
                    low=[b[0] for b in bounds],
                    high=[b[1] for b in bounds]
                )
            
            try:
                if self.optimizer == 'fmin_l_bfgs_b':
                    result = minimize(
                        objective, theta_initial, 
                        method='L-BFGS-B', bounds=bounds
                    )
                else:
                    result = minimize(objective, theta_initial, method=self.optimizer)
                
                if result.success and result.fun < best_value:
                    best_result = result
                    best_value = result.fun
                    
            except Exception:
                continue
        
        if best_result is not None:
            self._set_hyperparameters(best_result.x)
            self.log_marginal_likelihood_value_ = -best_value
    
    def _get_hyperparameters(self) -> np.ndarray:
        """Get current hyperparameters as array"""
        if hasattr(self.kernel, 'length_scale'):
            if hasattr(self.kernel, 'variance'):
                return np.array([self.kernel.length_scale, self.kernel.variance])
            else:
                return np.array([self.kernel.length_scale])
        else:
            return np.array([1.0])
    
    def _set_hyperparameters(self, theta: np.ndarray):
        """Set hyperparameters from array"""
        if hasattr(self.kernel, 'length_scale'):
            self.kernel.length_scale = theta[0]
            if hasattr(self.kernel, 'variance') and len(theta) > 1:
                self.kernel.variance = theta[1]


class VolatilitySurfaceGP:
    """
    Specialized Gaussian Process for volatility surface modeling
    """
    
    def __init__(
        self,
        kernel_type: str = 'matern',
        length_scale_bounds: Tuple[float, float] = (0.01, 10.0),
        variance_bounds: Tuple[float, float] = (0.01, 10.0),
        noise_bounds: Tuple[float, float] = (1e-5, 1e-1),
        n_restarts: int = 10
    ):
        """
        Initialize volatility surface GP
        
        Args:
            kernel_type: Type of kernel ('rbf', 'matern', 'composite')
            length_scale_bounds: Bounds for length scale parameter
            variance_bounds: Bounds for variance parameter  
            noise_bounds: Bounds for noise parameter
            n_restarts: Number of optimization restarts
        """
        self.kernel_type = kernel_type
        self.length_scale_bounds = length_scale_bounds
        self.variance_bounds = variance_bounds
        self.noise_bounds = noise_bounds
        self.n_restarts = n_restarts
        
        # Initialize kernel
        self._initialize_kernel()
        
        # GP regressor
        self.gp = GaussianProcessRegressor(
            kernel=self.kernel,
            alpha=1e-6,
            n_restarts_optimizer=n_restarts,
            normalize_y=True
        )
        
        # Fitted attributes
        self.is_fitted_ = False
        self.training_score_ = None
        self.smoothing_factor_ = None
    
    def _initialize_kernel(self):
        """Initialize kernel based on type"""
        if self.kernel_type == 'rbf':
            self.kernel = CompositeKernel([
                RBFKernel(length_scale=1.0, variance=1.0),
                WhiteNoiseKernel(noise_level=0.01)
            ], ['+'])
        
        elif self.kernel_type == 'matern':
            self.kernel = CompositeKernel([
                MaternKernel(length_scale=1.0, variance=1.0, nu=2.5),
                WhiteNoiseKernel(noise_level=0.01)
            ], ['+'])
        
        elif self.kernel_type == 'composite':
            # More sophisticated composite kernel
            self.kernel = CompositeKernel([
                MaternKernel(length_scale=1.0, variance=1.0, nu=2.5),
                RBFKernel(length_scale=0.1, variance=0.1),
                WhiteNoiseKernel(noise_level=0.01)
            ], ['+', '+'])
        
        else:
            raise ValueError(f"Unknown kernel type: {self.kernel_type}")
    
    def fit(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray, 
        volatilities: np.ndarray
    ) -> 'VolatilitySurfaceGP':
        """
        Fit GP to volatility surface data
        
        Args:
            strikes: Strike prices
            expiries: Time to expiries
            volatilities: Implied volatilities
        """
        # Prepare input features (strike, expiry)
        X = np.column_stack((strikes, expiries))
        y = volatilities
        
        # Remove any NaN values
        valid_mask = ~(np.isnan(strikes) | np.isnan(expiries) | np.isnan(volatilities))
        X = X[valid_mask]
        y = y[valid_mask]
        
        if len(X) < 3:
            raise ValueError("Insufficient valid data points for GP fitting")
        
        # Normalize features for better conditioning
        self.X_mean_ = np.mean(X, axis=0)
        self.X_std_ = np.std(X, axis=0)
        self.X_std_[self.X_std_ == 0] = 1.0  # Avoid division by zero
        
        X_norm = (X - self.X_mean_) / self.X_std_
        
        # Fit GP
        self.gp.fit(X_norm, y)
        
        # Store training data
        self.X_train_ = X
        self.y_train_ = y
        self.is_fitted_ = True
        
        # Calculate training score
        y_pred = self.predict(X[:, 0], X[:, 1])[0]
        self.training_score_ = 1 - np.mean((y - y_pred)**2) / np.var(y)
        
        return self
    
    def predict(
        self, 
        strikes: np.ndarray, 
        expiries: np.ndarray,
        return_std: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Predict volatilities for given strikes and expiries
        
        Args:
            strikes: Strike prices
            expiries: Time to expiries  
            return_std: Whether to return prediction uncertainty
            
        Returns:
            Predicted volatilities and optionally standard deviations
        """
        if not self.is_fitted_:
            raise ValueError("GP must be fitted before making predictions")
        
        # Prepare features
        X = np.column_stack((strikes, expiries))
        X_norm = (X - self.X_mean_) / self.X_std_
        
        # Make predictions
        if return_std:
            y_pred, y_std = self.gp.predict(X_norm, return_std=True)
            return y_pred, y_std
        else:
            y_pred = self.gp.predict(X_norm, return_std=False)
            return y_pred, None
    
    def predict_surface(
        self, 
        strike_grid: np.ndarray, 
        expiry_grid: np.ndarray,
        return_std: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Predict volatility surface on a grid
        
        Args:
            strike_grid: 2D array of strikes
            expiry_grid: 2D array of expiries
            return_std: Whether to return uncertainty
            
        Returns:
            Predicted surface and optionally uncertainty surface
        """
        # Flatten grids
        strikes_flat = strike_grid.ravel()
        expiries_flat = expiry_grid.ravel()
        
        # Make predictions
        if return_std:
            vol_pred, vol_std = self.predict(strikes_flat, expiries_flat, return_std=True)
            vol_surface = vol_pred.reshape(strike_grid.shape)
            std_surface = vol_std.reshape(strike_grid.shape)
            return vol_surface, std_surface
        else:
            vol_pred, _ = self.predict(strikes_flat, expiries_flat, return_std=False)
            vol_surface = vol_pred.reshape(strike_grid.shape)
            return vol_surface, None
    
    def get_hyperparameters(self) -> Dict[str, float]:
        """Get optimized hyperparameters"""
        if not self.is_fitted_:
            return {}
        
        hyperparams = {}
        if hasattr(self.gp.kernel, 'kernels'):
            for i, kernel in enumerate(self.gp.kernel.kernels):
                for key, value in kernel.hyperparameters.items():
                    hyperparams[f'kernel_{i}_{key}'] = value
        else:
            hyperparams = self.gp.kernel.hyperparameters.copy()
        
        hyperparams['log_marginal_likelihood'] = getattr(
            self.gp, 'log_marginal_likelihood_value_', np.nan
        )
        hyperparams['training_score'] = self.training_score_
        
        return hyperparams
    
    def calculate_smoothing_metrics(self) -> Dict[str, float]:
        """Calculate metrics for smoothing quality"""
        if not self.is_fitted_:
            return {}
        
        # Predict on training data
        y_pred, y_std = self.predict(
            self.X_train_[:, 0], 
            self.X_train_[:, 1], 
            return_std=True
        )
        
        # Calculate metrics
        mse = np.mean((self.y_train_ - y_pred)**2)
        mae = np.mean(np.abs(self.y_train_ - y_pred))
        r2 = 1 - np.sum((self.y_train_ - y_pred)**2) / np.sum((self.y_train_ - np.mean(self.y_train_))**2)
        
        # Uncertainty metrics
        mean_uncertainty = np.mean(y_std)
        uncertainty_coverage = np.mean(
            np.abs(self.y_train_ - y_pred) <= 2 * y_std
        )  # 95% coverage
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': np.sqrt(mse),
            'r_squared': r2,
            'mean_uncertainty': mean_uncertainty,
            'uncertainty_coverage': uncertainty_coverage,
            'n_training_points': len(self.y_train_)
        }

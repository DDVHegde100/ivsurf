"""
Regime Switching Models Module
Markov regime switching with EM algorithm for market state detection
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class MarkovRegimeSwitching:
    """
    Markov Regime Switching Model for detecting market regimes
    """
    
    def __init__(self, n_regimes=2):
        """
        Initialize regime switching model
        
        Args:
            n_regimes: Number of market regimes to detect (default: 2)
        """
        self.n_regimes = n_regimes
        self.transition_matrix = None
        self.regime_parameters = None
        self.regime_probabilities = None
        self.fitted = False
        
    def fit(self, returns, max_iterations=100, tolerance=1e-6):
        """
        Fit regime switching model using Expectation-Maximization algorithm
        
        Args:
            returns: Time series of returns
            max_iterations: Maximum EM iterations
            tolerance: Convergence tolerance
            
        Returns:
            dict: Fitted model parameters
        """
        returns = np.array(returns)
        n_obs = len(returns)
        
        # Initialize parameters
        self._initialize_parameters(returns)
        
        log_likelihood_old = -np.inf
        
        for iteration in range(max_iterations):
            # E-step: Calculate regime probabilities
            regime_probs = self._expectation_step(returns)
            
            # M-step: Update parameters
            self._maximization_step(returns, regime_probs)
            
            # Calculate log-likelihood
            log_likelihood = self._calculate_log_likelihood(returns)
            
            # Check convergence
            if abs(log_likelihood - log_likelihood_old) < tolerance:
                break
                
            log_likelihood_old = log_likelihood
        
        self.fitted = True
        
        # Calculate final regime probabilities
        self.regime_probabilities = self._expectation_step(returns)
        
        return {
            'n_regimes': self.n_regimes,
            'transition_matrix': self.transition_matrix,
            'regime_parameters': self.regime_parameters,
            'log_likelihood': log_likelihood,
            'iterations': iteration + 1,
            'converged': iteration < max_iterations - 1
        }
    
    def _initialize_parameters(self, returns):
        """Initialize model parameters"""
        n_obs = len(returns)
        
        # Initialize regime parameters (mean and variance for each regime)
        self.regime_parameters = []
        
        # Use quantiles to initialize regimes
        for i in range(self.n_regimes):
            if self.n_regimes == 2:
                # Bull and Bear regimes
                if i == 0:  # Bull regime
                    mask = returns > np.median(returns)
                else:  # Bear regime
                    mask = returns <= np.median(returns)
            else:
                # Multiple regimes based on quantiles
                q_low = i / self.n_regimes
                q_high = (i + 1) / self.n_regimes
                mask = (returns >= np.quantile(returns, q_low)) & (returns < np.quantile(returns, q_high))
            
            if np.sum(mask) > 0:
                regime_returns = returns[mask]
                mean = np.mean(regime_returns)
                var = np.var(regime_returns)
            else:
                mean = np.mean(returns)
                var = np.var(returns)
            
            self.regime_parameters.append({'mean': mean, 'variance': max(var, 1e-6)})
        
        # Initialize transition matrix (equal probabilities)
        self.transition_matrix = np.ones((self.n_regimes, self.n_regimes)) / self.n_regimes
        
        # Initialize steady-state probabilities
        self.steady_state_probs = np.ones(self.n_regimes) / self.n_regimes
    
    def _expectation_step(self, returns):
        """E-step: Calculate regime probabilities"""
        n_obs = len(returns)
        regime_probs = np.zeros((n_obs, self.n_regimes))
        
        # Forward algorithm to calculate regime probabilities
        # Initialize
        for j in range(self.n_regimes):
            regime_probs[0, j] = (self.steady_state_probs[j] * 
                                self._gaussian_density(returns[0], 
                                                     self.regime_parameters[j]['mean'],
                                                     self.regime_parameters[j]['variance']))
        
        # Normalize
        regime_probs[0, :] /= np.sum(regime_probs[0, :])
        
        # Forward pass
        for t in range(1, n_obs):
            for j in range(self.n_regimes):
                regime_probs[t, j] = (np.sum(regime_probs[t-1, :] * self.transition_matrix[:, j]) *
                                    self._gaussian_density(returns[t],
                                                         self.regime_parameters[j]['mean'],
                                                         self.regime_parameters[j]['variance']))
            
            # Normalize to prevent numerical issues
            if np.sum(regime_probs[t, :]) > 0:
                regime_probs[t, :] /= np.sum(regime_probs[t, :])
        
        return regime_probs
    
    def _maximization_step(self, returns, regime_probs):
        """M-step: Update parameters"""
        n_obs = len(returns)
        
        # Update regime parameters
        for j in range(self.n_regimes):
            weights = regime_probs[:, j]
            total_weight = np.sum(weights)
            
            if total_weight > 1e-8:
                # Update mean
                self.regime_parameters[j]['mean'] = np.sum(weights * returns) / total_weight
                
                # Update variance
                residuals = returns - self.regime_parameters[j]['mean']
                self.regime_parameters[j]['variance'] = max(
                    np.sum(weights * residuals**2) / total_weight, 1e-6
                )
        
        # Update transition matrix
        for i in range(self.n_regimes):
            for j in range(self.n_regimes):
                numerator = np.sum(regime_probs[:-1, i] * regime_probs[1:, j])
                denominator = np.sum(regime_probs[:-1, i])
                
                if denominator > 1e-8:
                    self.transition_matrix[i, j] = numerator / denominator
                else:
                    self.transition_matrix[i, j] = 1.0 / self.n_regimes
        
        # Normalize transition matrix rows
        for i in range(self.n_regimes):
            row_sum = np.sum(self.transition_matrix[i, :])
            if row_sum > 0:
                self.transition_matrix[i, :] /= row_sum
    
    def _gaussian_density(self, x, mean, variance):
        """Calculate Gaussian probability density"""
        return (1.0 / np.sqrt(2 * np.pi * variance)) * np.exp(-0.5 * (x - mean)**2 / variance)
    
    def _calculate_log_likelihood(self, returns):
        """Calculate log-likelihood of the model"""
        regime_probs = self._expectation_step(returns)
        log_likelihood = 0
        
        for t in range(len(returns)):
            likelihood_t = 0
            for j in range(self.n_regimes):
                likelihood_t += (regime_probs[t, j] * 
                               self._gaussian_density(returns[t],
                                                    self.regime_parameters[j]['mean'],
                                                    self.regime_parameters[j]['variance']))
            
            if likelihood_t > 0:
                log_likelihood += np.log(likelihood_t)
        
        return log_likelihood
    
    def predict_regime(self, returns):
        """
        Predict most likely regime for each observation
        
        Args:
            returns: Time series of returns
            
        Returns:
            np.array: Most likely regime for each observation
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        regime_probs = self._expectation_step(returns)
        return np.argmax(regime_probs, axis=1)
    
    def get_regime_probabilities(self, returns):
        """
        Get regime probabilities for each observation
        
        Args:
            returns: Time series of returns
            
        Returns:
            np.array: Regime probabilities matrix
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        return self._expectation_step(returns)
    
    def regime_statistics(self):
        """
        Get regime statistics and interpretation
        
        Returns:
            dict: Regime statistics
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        stats = {}
        
        for i in range(self.n_regimes):
            regime_name = self._get_regime_name(i)
            
            stats[regime_name] = {
                'regime_id': i,
                'mean_return': self.regime_parameters[i]['mean'],
                'volatility': np.sqrt(self.regime_parameters[i]['variance']),
                'annual_return': self.regime_parameters[i]['mean'] * 252,
                'annual_volatility': np.sqrt(self.regime_parameters[i]['variance']) * np.sqrt(252),
                'persistence': self.transition_matrix[i, i],  # Probability of staying in regime
                'steady_state_prob': self._calculate_steady_state_prob(i)
            }
        
        return stats
    
    def _get_regime_name(self, regime_id):
        """Get descriptive name for regime"""
        if self.n_regimes == 2:
            if regime_id == 0:
                mean_0 = self.regime_parameters[0]['mean']
                mean_1 = self.regime_parameters[1]['mean']
                return 'Bull Market' if mean_0 > mean_1 else 'Bear Market'
            else:
                mean_0 = self.regime_parameters[0]['mean']
                mean_1 = self.regime_parameters[1]['mean']
                return 'Bear Market' if mean_0 > mean_1 else 'Bull Market'
        else:
            return f'Regime_{regime_id}'
    
    def _calculate_steady_state_prob(self, regime_id):
        """Calculate steady-state probability for regime"""
        try:
            # Calculate steady-state distribution
            eigenvals, eigenvecs = np.linalg.eig(self.transition_matrix.T)
            
            # Find eigenvector corresponding to eigenvalue 1
            stationary_idx = np.argmin(np.abs(eigenvals - 1))
            steady_state = np.real(eigenvecs[:, stationary_idx])
            steady_state = steady_state / np.sum(steady_state)
            
            return steady_state[regime_id]
        except:
            return 1.0 / self.n_regimes
    
    def detect_regime_changes(self, returns, threshold=0.7):
        """
        Detect regime change points
        
        Args:
            returns: Time series of returns
            threshold: Probability threshold for regime detection
            
        Returns:
            list: List of regime change points
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        regime_probs = self.get_regime_probabilities(returns)
        most_likely_regimes = np.argmax(regime_probs, axis=1)
        max_probs = np.max(regime_probs, axis=1)
        
        # Find high-confidence regime changes
        change_points = []
        
        for t in range(1, len(most_likely_regimes)):
            if (most_likely_regimes[t] != most_likely_regimes[t-1] and 
                max_probs[t] > threshold and max_probs[t-1] > threshold):
                change_points.append({
                    'date_index': t,
                    'from_regime': most_likely_regimes[t-1],
                    'to_regime': most_likely_regimes[t],
                    'confidence': min(max_probs[t], max_probs[t-1])
                })
        
        return change_points

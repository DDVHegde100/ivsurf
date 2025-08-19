"""
GARCH Models Module
GARCH(1,1) and EGARCH volatility models for volatility clustering analysis
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class GARCHModel:
    """
    GARCH(1,1) Model for volatility modeling and prediction
    """
    
    def __init__(self, model_type='GARCH'):
        """
        Initialize GARCH model
        
        Args:
            model_type: 'GARCH' or 'EGARCH' for different model specifications
        """
        self.model_type = model_type
        self.parameters = None
        self.fitted = False
        self.conditional_volatility = None
        self.returns = None
        
    def fit(self, returns, method='MLE'):
        """
        Fit GARCH model to returns data
        
        Args:
            returns: Time series of returns
            method: Estimation method ('MLE' for Maximum Likelihood)
            
        Returns:
            dict: Fitted model parameters
        """
        self.returns = np.array(returns)
        
        # Remove any NaN values
        self.returns = self.returns[~np.isnan(self.returns)]
        
        if len(self.returns) < 50:
            raise ValueError("Need at least 50 observations for GARCH estimation")
        
        # Initial parameter estimates
        if self.model_type == 'GARCH':
            initial_params = self._get_initial_garch_params()
            bounds = [(1e-6, 1), (0, 1), (0, 1)]  # omega, alpha, beta
            
            # Constraint: alpha + beta < 1 for stationarity
            constraints = {'type': 'ineq', 'fun': lambda params: 0.999 - params[1] - params[2]}
            
        elif self.model_type == 'EGARCH':
            initial_params = self._get_initial_egarch_params()
            bounds = [(-10, 10), (0, 1), (-1, 1), (0, 1)]  # omega, alpha, gamma, beta
            constraints = None
        
        # Maximum likelihood estimation
        try:
            result = minimize(
                fun=self._negative_log_likelihood,
                x0=initial_params,
                bounds=bounds,
                constraints=constraints,
                method='SLSQP',
                options={'maxiter': 1000}
            )
            
            if result.success:
                self.parameters = result.x
                self.fitted = True
                
                # Calculate conditional volatility
                self.conditional_volatility = self._calculate_conditional_volatility()
                
                return {
                    'model_type': self.model_type,
                    'parameters': self._format_parameters(),
                    'log_likelihood': -result.fun,
                    'aic': 2 * len(self.parameters) - 2 * (-result.fun),
                    'bic': len(self.parameters) * np.log(len(self.returns)) - 2 * (-result.fun),
                    'success': True
                }
            else:
                return {'success': False, 'message': 'Optimization failed'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error in estimation: {str(e)}'}
    
    def _get_initial_garch_params(self):
        """Get initial parameter estimates for GARCH(1,1)"""
        # Simple method: use sample variance and reasonable starting values
        sample_var = np.var(self.returns)
        
        omega = sample_var * 0.1  # 10% of sample variance
        alpha = 0.1  # Typical starting value
        beta = 0.8   # Typical starting value
        
        return [omega, alpha, beta]
    
    def _get_initial_egarch_params(self):
        """Get initial parameter estimates for EGARCH(1,1)"""
        sample_var = np.var(self.returns)
        
        omega = np.log(sample_var)
        alpha = 0.1
        gamma = -0.1  # Leverage effect
        beta = 0.9
        
        return [omega, alpha, gamma, beta]
    
    def _negative_log_likelihood(self, params):
        """Calculate negative log-likelihood for optimization"""
        try:
            if self.model_type == 'GARCH':
                return -self._garch_log_likelihood(params)
            elif self.model_type == 'EGARCH':
                return -self._egarch_log_likelihood(params)
        except:
            return 1e10  # Return large value if calculation fails
    
    def _garch_log_likelihood(self, params):
        """Calculate GARCH(1,1) log-likelihood"""
        omega, alpha, beta = params
        
        # Check parameter constraints
        if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1:
            return -1e10
        
        n = len(self.returns)
        sigma2 = np.zeros(n)
        
        # Initialize with sample variance
        sigma2[0] = np.var(self.returns)
        
        # Calculate conditional variances
        for t in range(1, n):
            sigma2[t] = omega + alpha * self.returns[t-1]**2 + beta * sigma2[t-1]
        
        # Ensure positive variances
        sigma2 = np.maximum(sigma2, 1e-8)
        
        # Calculate log-likelihood
        log_likelihood = -0.5 * np.sum(np.log(2 * np.pi * sigma2) + self.returns**2 / sigma2)
        
        return log_likelihood
    
    def _egarch_log_likelihood(self, params):
        """Calculate EGARCH(1,1) log-likelihood"""
        omega, alpha, gamma, beta = params
        
        n = len(self.returns)
        log_sigma2 = np.zeros(n)
        
        # Initialize
        log_sigma2[0] = np.log(np.var(self.returns))
        
        # Calculate log conditional variances
        for t in range(1, n):
            z_t = self.returns[t-1] / np.sqrt(np.exp(log_sigma2[t-1]))
            
            log_sigma2[t] = (omega + 
                           alpha * (np.abs(z_t) - np.sqrt(2/np.pi)) + 
                           gamma * z_t + 
                           beta * log_sigma2[t-1])
        
        sigma2 = np.exp(log_sigma2)
        sigma2 = np.maximum(sigma2, 1e-8)
        
        # Calculate log-likelihood
        log_likelihood = -0.5 * np.sum(np.log(2 * np.pi * sigma2) + self.returns**2 / sigma2)
        
        return log_likelihood
    
    def _calculate_conditional_volatility(self):
        """Calculate conditional volatility series"""
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        n = len(self.returns)
        
        if self.model_type == 'GARCH':
            omega, alpha, beta = self.parameters
            sigma2 = np.zeros(n)
            sigma2[0] = np.var(self.returns)
            
            for t in range(1, n):
                sigma2[t] = omega + alpha * self.returns[t-1]**2 + beta * sigma2[t-1]
            
            return np.sqrt(np.maximum(sigma2, 1e-8))
        
        elif self.model_type == 'EGARCH':
            omega, alpha, gamma, beta = self.parameters
            log_sigma2 = np.zeros(n)
            log_sigma2[0] = np.log(np.var(self.returns))
            
            for t in range(1, n):
                z_t = self.returns[t-1] / np.sqrt(np.exp(log_sigma2[t-1]))
                log_sigma2[t] = (omega + 
                               alpha * (np.abs(z_t) - np.sqrt(2/np.pi)) + 
                               gamma * z_t + 
                               beta * log_sigma2[t-1])
            
            return np.sqrt(np.exp(log_sigma2))
    
    def _format_parameters(self):
        """Format parameters with meaningful names"""
        if self.model_type == 'GARCH':
            return {
                'omega': self.parameters[0],
                'alpha': self.parameters[1],
                'beta': self.parameters[2],
                'persistence': self.parameters[1] + self.parameters[2]
            }
        elif self.model_type == 'EGARCH':
            return {
                'omega': self.parameters[0],
                'alpha': self.parameters[1],
                'gamma': self.parameters[2],
                'beta': self.parameters[3],
                'leverage_effect': self.parameters[2] < 0
            }
    
    def forecast_volatility(self, steps=1):
        """
        Forecast volatility for specified number of steps ahead
        
        Args:
            steps: Number of steps ahead to forecast
            
        Returns:
            np.array: Volatility forecasts
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        forecasts = np.zeros(steps)
        
        if self.model_type == 'GARCH':
            omega, alpha, beta = self.parameters
            
            # Last conditional variance
            last_sigma2 = self.conditional_volatility[-1]**2
            last_return = self.returns[-1]
            
            # One-step ahead forecast
            forecasts[0] = np.sqrt(omega + alpha * last_return**2 + beta * last_sigma2)
            
            # Multi-step ahead forecasts
            unconditional_var = omega / (1 - alpha - beta)
            
            for h in range(1, steps):
                persistence = (alpha + beta)**h
                forecasts[h] = np.sqrt(unconditional_var * (1 - persistence) + 
                                     last_sigma2 * persistence)
        
        elif self.model_type == 'EGARCH':
            # EGARCH forecasting is more complex, simplified here
            last_vol = self.conditional_volatility[-1]
            forecasts.fill(last_vol)  # Simplified constant forecast
        
        return forecasts
    
    def volatility_clustering_test(self):
        """
        Test for volatility clustering using various statistics
        
        Returns:
            dict: Volatility clustering test results
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        # Ljung-Box test on squared returns
        squared_returns = self.returns**2
        
        # Calculate autocorrelations
        lags = [1, 5, 10, 20]
        autocorrs = []
        
        for lag in lags:
            if len(squared_returns) > lag:
                autocorr = np.corrcoef(squared_returns[:-lag], squared_returns[lag:])[0, 1]
                autocorrs.append(autocorr if not np.isnan(autocorr) else 0)
            else:
                autocorrs.append(0)
        
        # ARCH test (simplified)
        n = len(self.returns)
        arch_stat = n * np.sum([ac**2 for ac in autocorrs]) if autocorrs else 0
        arch_p_value = 1 - stats.chi2.cdf(arch_stat, len(lags))
        
        return {
            'autocorrelations_squared_returns': dict(zip(lags, autocorrs)),
            'arch_test_statistic': arch_stat,
            'arch_p_value': arch_p_value,
            'volatility_clustering_detected': arch_p_value < 0.05,
            'mean_conditional_volatility': np.mean(self.conditional_volatility),
            'volatility_persistence': self.parameters[1] + self.parameters[2] if self.model_type == 'GARCH' else None
        }
    
    def model_diagnostics(self):
        """
        Perform model diagnostics
        
        Returns:
            dict: Model diagnostic results
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        # Standardized residuals
        standardized_residuals = self.returns / self.conditional_volatility
        
        # Jarque-Bera test for normality of standardized residuals
        jb_stat, jb_p_value = stats.jarque_bera(standardized_residuals)
        
        # Ljung-Box test on standardized residuals
        residual_autocorr = np.corrcoef(standardized_residuals[:-1], standardized_residuals[1:])[0, 1]
        if np.isnan(residual_autocorr):
            residual_autocorr = 0
        
        # Ljung-Box test on squared standardized residuals
        squared_residuals = standardized_residuals**2
        squared_autocorr = np.corrcoef(squared_residuals[:-1], squared_residuals[1:])[0, 1]
        if np.isnan(squared_autocorr):
            squared_autocorr = 0
        
        return {
            'standardized_residuals_mean': np.mean(standardized_residuals),
            'standardized_residuals_std': np.std(standardized_residuals),
            'standardized_residuals_skewness': stats.skew(standardized_residuals),
            'standardized_residuals_kurtosis': stats.kurtosis(standardized_residuals),
            'jarque_bera_statistic': jb_stat,
            'jarque_bera_p_value': jb_p_value,
            'residuals_normally_distributed': jb_p_value > 0.05,
            'residual_autocorrelation': residual_autocorr,
            'squared_residual_autocorrelation': squared_autocorr,
            'model_adequate': jb_p_value > 0.05 and abs(squared_autocorr) < 0.1
        }

class VolatilityBreakpointDetection:
    """
    Detect structural breaks in volatility using various methods
    """
    
    def __init__(self):
        """Initialize breakpoint detector"""
        self.returns = None
        self.breakpoints = None
        
    def detect_breakpoints(self, returns, method='ICSS', significance_level=0.05):
        """
        Detect volatility breakpoints
        
        Args:
            returns: Time series of returns
            method: Detection method ('ICSS', 'CUSUM', 'Rolling')
            significance_level: Statistical significance level
            
        Returns:
            dict: Breakpoint detection results
        """
        self.returns = np.array(returns)
        
        if method == 'ICSS':
            return self._icss_algorithm(significance_level)
        elif method == 'CUSUM':
            return self._cusum_test(significance_level)
        elif method == 'Rolling':
            return self._rolling_variance_test()
        else:
            raise ValueError("Method must be 'ICSS', 'CUSUM', or 'Rolling'")
    
    def _icss_algorithm(self, significance_level):
        """
        Iterative Cumulative Sum of Squares (ICSS) algorithm
        """
        n = len(self.returns)
        squared_returns = self.returns**2
        
        # Calculate cumulative sum of squares
        cumsum_sq = np.cumsum(squared_returns)
        total_sum_sq = cumsum_sq[-1]
        
        # Calculate ICSS test statistic
        max_stat = 0
        max_location = 0
        
        for k in range(1, n-1):
            # Test statistic at point k
            stat = (cumsum_sq[k] / total_sum_sq - k / n) / np.sqrt(k * (n - k) / n**3)
            
            if abs(stat) > max_stat:
                max_stat = abs(stat)
                max_location = k
        
        # Critical value (approximate)
        critical_value = stats.norm.ppf(1 - significance_level/2)
        
        breakpoints = []
        if max_stat > critical_value:
            breakpoints.append({
                'location': max_location,
                'test_statistic': max_stat,
                'critical_value': critical_value,
                'significant': True
            })
        
        return {
            'method': 'ICSS',
            'breakpoints': breakpoints,
            'significance_level': significance_level,
            'max_test_statistic': max_stat,
            'critical_value': critical_value
        }
    
    def _cusum_test(self, significance_level):
        """
        CUSUM test for variance change
        """
        n = len(self.returns)
        squared_returns = self.returns**2
        mean_sq = np.mean(squared_returns)
        
        # Calculate CUSUM statistics
        cusum = np.cumsum(squared_returns - mean_sq)
        
        # Find maximum absolute CUSUM
        max_cusum = np.max(np.abs(cusum))
        max_location = np.argmax(np.abs(cusum))
        
        # Critical value (Brown, Durbin, Evans)
        critical_value = np.sqrt(n) * 0.948  # Approximate for 5% level
        
        breakpoints = []
        if max_cusum > critical_value:
            breakpoints.append({
                'location': max_location,
                'test_statistic': max_cusum,
                'critical_value': critical_value,
                'significant': True
            })
        
        return {
            'method': 'CUSUM',
            'breakpoints': breakpoints,
            'significance_level': significance_level,
            'max_test_statistic': max_cusum,
            'critical_value': critical_value
        }
    
    def _rolling_variance_test(self, window=30):
        """
        Rolling variance test for structural breaks
        """
        n = len(self.returns)
        
        if n < 2 * window:
            return {
                'method': 'Rolling',
                'breakpoints': [],
                'error': 'Insufficient data for rolling variance test'
            }
        
        # Calculate rolling variance
        rolling_var = []
        for i in range(window, n - window):
            var1 = np.var(self.returns[i-window:i])
            var2 = np.var(self.returns[i:i+window])
            
            # F-test for variance equality
            if var2 > 0 and var1 > 0:
                f_stat = max(var1, var2) / min(var1, var2)
                rolling_var.append({'location': i, 'f_statistic': f_stat, 'var_ratio': var2/var1})
        
        # Find significant changes (simplified)
        critical_f = 2.0  # Simplified critical value
        
        breakpoints = []
        for item in rolling_var:
            if item['f_statistic'] > critical_f:
                breakpoints.append({
                    'location': item['location'],
                    'test_statistic': item['f_statistic'],
                    'variance_ratio': item['var_ratio'],
                    'significant': True
                })
        
        return {
            'method': 'Rolling',
            'window_size': window,
            'breakpoints': breakpoints,
            'critical_value': critical_f,
            'rolling_statistics': rolling_var
        }

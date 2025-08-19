"""
Correlation Engine for Multi-Asset Monte Carlo Simulation
=========================================================

Advanced correlation modeling for multi-asset derivatives:
- Cholesky decomposition for Gaussian copulas
- Student-t copulas for heavy-tailed dependence
- Archimedean copulas (Clayton, Gumbel, Frank)
- Time-varying correlation models (DCC-GARCH)
- Empirical copula estimation

Mathematical Framework:
- Cholesky decomposition: L such that LL^T = Σ
- Gaussian copula: C(u₁,...,uₙ) = Φₙ(Φ⁻¹(u₁),...,Φ⁻¹(uₙ); R)
- Student-t copula: Heavy-tailed dependence structure
- Archimedean: C(u₁,...,uₙ) = φ⁻¹(φ(u₁) + ... + φ(uₙ))

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Callable, Any
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats, optimize, special
from scipy.stats import multivariate_normal, multivariate_t

class CopulaType(Enum):
    """Copula type enumeration"""
    GAUSSIAN = "gaussian"
    STUDENT_T = "student_t"
    CLAYTON = "clayton"
    GUMBEL = "gumbel"
    FRANK = "frank"
    EMPIRICAL = "empirical"

@dataclass
class CopulaParameters:
    """Copula parameters container"""
    copula_type: CopulaType
    correlation_matrix: np.ndarray
    degrees_of_freedom: Optional[float] = None  # For Student-t copula
    theta: Optional[float] = None  # For Archimedean copulas
    
class CorrelationEngine:
    """
    Master correlation engine for multi-asset simulation
    
    Provides unified interface for various correlation structures:
    - Linear correlation (Pearson)
    - Rank correlation (Spearman, Kendall)
    - Copula-based dependence
    - Time-varying correlation
    """
    
    def __init__(self):
        self.cholesky_sampler = CholeskySampler()
        self.copula_sampler = CopulaSampler()
    
    def estimate_correlation_matrix(self, returns_data: pd.DataFrame, 
                                  method: str = "pearson") -> np.ndarray:
        """
        Estimate correlation matrix from historical data
        
        Args:
            returns_data: DataFrame with asset returns
            method: "pearson", "spearman", or "kendall"
            
        Returns:
            Correlation matrix
        """
        if method == "pearson":
            return returns_data.corr().values
        elif method == "spearman":
            return returns_data.corr(method="spearman").values
        elif method == "kendall":
            return returns_data.corr(method="kendall").values
        else:
            raise ValueError(f"Unknown correlation method: {method}")
    
    def validate_correlation_matrix(self, correlation_matrix: np.ndarray) -> bool:
        """
        Validate correlation matrix properties
        
        Args:
            correlation_matrix: Correlation matrix to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check if matrix is square
        if correlation_matrix.shape[0] != correlation_matrix.shape[1]:
            return False
        
        # Check if diagonal elements are 1
        if not np.allclose(np.diag(correlation_matrix), 1.0):
            return False
        
        # Check if matrix is symmetric
        if not np.allclose(correlation_matrix, correlation_matrix.T):
            return False
        
        # Check if matrix is positive semi-definite
        eigenvalues = np.linalg.eigvals(correlation_matrix)
        if np.any(eigenvalues < -1e-10):
            return False
        
        # Check if off-diagonal elements are in [-1, 1]
        off_diagonal = correlation_matrix - np.diag(np.diag(correlation_matrix))
        if np.any(np.abs(off_diagonal) > 1.0):
            return False
        
        return True
    
    def fix_correlation_matrix(self, correlation_matrix: np.ndarray) -> np.ndarray:
        """
        Fix invalid correlation matrix using nearest correlation matrix method
        
        Args:
            correlation_matrix: Potentially invalid correlation matrix
            
        Returns:
            Valid correlation matrix
        """
        # Ensure symmetry
        corr_fixed = 0.5 * (correlation_matrix + correlation_matrix.T)
        
        # Ensure diagonal is 1
        np.fill_diagonal(corr_fixed, 1.0)
        
        # Ensure positive semi-definiteness using eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(corr_fixed)
        
        # Clip negative eigenvalues to small positive value
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        
        # Reconstruct matrix
        corr_fixed = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
        
        # Rescale to ensure diagonal is 1
        scaling = np.sqrt(np.diag(corr_fixed))
        corr_fixed = corr_fixed / np.outer(scaling, scaling)
        
        return corr_fixed
    
    def generate_correlated_samples(self, copula_params: CopulaParameters,
                                  n_samples: int) -> np.ndarray:
        """
        Generate correlated samples using specified copula
        
        Args:
            copula_params: Copula parameters
            n_samples: Number of samples to generate
            
        Returns:
            Array of correlated uniform samples [0,1]
        """
        if copula_params.copula_type == CopulaType.GAUSSIAN:
            return self.cholesky_sampler.generate_gaussian_copula_samples(
                copula_params.correlation_matrix, n_samples
            )
        elif copula_params.copula_type == CopulaType.STUDENT_T:
            return self.copula_sampler.generate_student_t_samples(
                copula_params.correlation_matrix, 
                copula_params.degrees_of_freedom,
                n_samples
            )
        else:
            return self.copula_sampler.generate_archimedean_samples(
                copula_params, n_samples
            )

class CholeskySampler:
    """
    Cholesky decomposition-based sampling for Gaussian copulas
    
    Fast and efficient for high-dimensional problems when Gaussian
    dependence structure is appropriate.
    """
    
    def __init__(self):
        pass
    
    def generate_gaussian_copula_samples(self, correlation_matrix: np.ndarray,
                                       n_samples: int) -> np.ndarray:
        """
        Generate samples from Gaussian copula using Cholesky decomposition
        
        Args:
            correlation_matrix: Asset correlation matrix
            n_samples: Number of samples to generate
            
        Returns:
            Array of shape (n_samples, n_assets) with uniform marginals
        """
        n_assets = correlation_matrix.shape[0]
        
        try:
            # Cholesky decomposition
            L = np.linalg.cholesky(correlation_matrix)
        except np.linalg.LinAlgError:
            # If not positive definite, use eigenvalue decomposition
            eigenvals, eigenvecs = np.linalg.eigh(correlation_matrix)
            eigenvals = np.maximum(eigenvals, 1e-10)  # Ensure positive
            L = eigenvecs @ np.diag(np.sqrt(eigenvals))
        
        # Generate independent standard normal samples
        Z = np.random.randn(n_samples, n_assets)
        
        # Apply correlation structure
        correlated_Z = Z @ L.T
        
        # Transform to uniform marginals using normal CDF
        uniform_samples = stats.norm.cdf(correlated_Z)
        
        return uniform_samples
    
    def generate_correlated_normals(self, correlation_matrix: np.ndarray,
                                  n_samples: int) -> np.ndarray:
        """
        Generate correlated normal samples directly
        
        Args:
            correlation_matrix: Correlation matrix
            n_samples: Number of samples
            
        Returns:
            Correlated normal samples
        """
        n_assets = correlation_matrix.shape[0]
        
        try:
            L = np.linalg.cholesky(correlation_matrix)
        except np.linalg.LinAlgError:
            # Fallback using eigendecomposition
            eigenvals, eigenvecs = np.linalg.eigh(correlation_matrix)
            eigenvals = np.maximum(eigenvals, 1e-10)
            L = eigenvecs @ np.diag(np.sqrt(eigenvals))
        
        # Independent normals
        Z = np.random.randn(n_samples, n_assets)
        
        # Apply correlation
        return Z @ L.T

class CopulaSampler:
    """
    Advanced copula sampling for non-Gaussian dependence structures
    
    Supports:
    - Student-t copula for heavy-tailed dependence
    - Archimedean copulas (Clayton, Gumbel, Frank)
    - Empirical copulas from historical data
    """
    
    def __init__(self):
        pass
    
    def generate_student_t_samples(self, correlation_matrix: np.ndarray,
                                 degrees_of_freedom: float,
                                 n_samples: int) -> np.ndarray:
        """
        Generate samples from Student-t copula
        
        Args:
            correlation_matrix: Correlation matrix
            degrees_of_freedom: Degrees of freedom parameter
            n_samples: Number of samples
            
        Returns:
            Uniform samples from t-copula
        """
        n_assets = correlation_matrix.shape[0]
        
        # Generate multivariate t-distributed samples
        try:
            # Use scipy's multivariate_t if available
            mvt_samples = multivariate_t.rvs(
                loc=np.zeros(n_assets),
                shape=correlation_matrix,
                df=degrees_of_freedom,
                size=n_samples
            )
        except:
            # Fallback implementation
            # Generate from multivariate normal and chi-squared
            cholesky_sampler = CholeskySampler()
            normal_samples = cholesky_sampler.generate_correlated_normals(
                correlation_matrix, n_samples
            )
            
            # Chi-squared samples for scaling
            chi2_samples = np.random.chisquare(degrees_of_freedom, n_samples)
            scaling = np.sqrt(degrees_of_freedom / chi2_samples)
            
            mvt_samples = normal_samples * scaling[:, np.newaxis]
        
        # Transform to uniform using t-distribution CDF
        uniform_samples = np.zeros_like(mvt_samples)
        for i in range(n_assets):
            uniform_samples[:, i] = stats.t.cdf(mvt_samples[:, i], df=degrees_of_freedom)
        
        return uniform_samples
    
    def generate_archimedean_samples(self, copula_params: CopulaParameters,
                                   n_samples: int) -> np.ndarray:
        """
        Generate samples from Archimedean copulas
        
        Args:
            copula_params: Copula parameters including theta
            n_samples: Number of samples
            
        Returns:
            Uniform samples from Archimedean copula
        """
        n_assets = copula_params.correlation_matrix.shape[0]
        theta = copula_params.theta
        
        if copula_params.copula_type == CopulaType.CLAYTON:
            return self._generate_clayton_samples(theta, n_assets, n_samples)
        elif copula_params.copula_type == CopulaType.GUMBEL:
            return self._generate_gumbel_samples(theta, n_assets, n_samples)
        elif copula_params.copula_type == CopulaType.FRANK:
            return self._generate_frank_samples(theta, n_assets, n_samples)
        else:
            raise ValueError(f"Unsupported copula type: {copula_params.copula_type}")
    
    def _generate_clayton_samples(self, theta: float, n_assets: int, 
                                n_samples: int) -> np.ndarray:
        """Generate Clayton copula samples"""
        if n_assets != 2:
            raise NotImplementedError("Clayton copula only implemented for 2 assets")
        
        # Generate Clayton copula using conditional distribution method
        U1 = np.random.uniform(0, 1, n_samples)
        U2_given_U1 = np.random.uniform(0, 1, n_samples)
        
        # Clayton copula conditional distribution
        U2 = (U1**(-theta) * (U2_given_U1**(-theta/(1+theta)) - 1) + 1)**(-1/theta)
        
        return np.column_stack([U1, U2])
    
    def _generate_gumbel_samples(self, theta: float, n_assets: int,
                               n_samples: int) -> np.ndarray:
        """Generate Gumbel copula samples"""
        if n_assets != 2:
            raise NotImplementedError("Gumbel copula only implemented for 2 assets")
        
        # Use Fréchet distribution approach for Gumbel copula
        # This is a simplified implementation
        W = np.random.exponential(1, n_samples)
        V1 = np.random.exponential(1, n_samples)
        V2 = np.random.exponential(1, n_samples)
        
        X1 = W / (W + V1)**(1/theta)
        X2 = W / (W + V2)**(1/theta)
        
        U1 = np.exp(-X1)
        U2 = np.exp(-X2)
        
        return np.column_stack([U1, U2])
    
    def _generate_frank_samples(self, theta: float, n_assets: int,
                              n_samples: int) -> np.ndarray:
        """Generate Frank copula samples"""
        if n_assets != 2:
            raise NotImplementedError("Frank copula only implemented for 2 assets")
        
        # Frank copula using inverse transform method
        U1 = np.random.uniform(0, 1, n_samples)
        V = np.random.uniform(0, 1, n_samples)
        
        if abs(theta) < 1e-10:
            # Independent case
            U2 = V
        else:
            # Frank copula conditional distribution
            numerator = np.exp(-theta * V) - 1
            denominator = (np.exp(-theta * U1) - 1) * np.exp(-theta * V) + np.exp(-theta) - 1
            
            U2 = -np.log(1 + numerator / denominator * (np.exp(-theta) - 1)) / theta
        
        return np.column_stack([U1, U2])
    
    def estimate_copula_parameters(self, data: np.ndarray, 
                                 copula_type: CopulaType) -> Dict[str, Any]:
        """
        Estimate copula parameters from data
        
        Args:
            data: Historical data for parameter estimation
            copula_type: Type of copula to fit
            
        Returns:
            Dictionary of estimated parameters
        """
        n_samples, n_assets = data.shape
        
        # Convert to uniform marginals using empirical CDF
        uniform_data = np.zeros_like(data)
        for i in range(n_assets):
            ranks = stats.rankdata(data[:, i])
            uniform_data[:, i] = ranks / (n_samples + 1)
        
        if copula_type == CopulaType.GAUSSIAN:
            # Estimate correlation matrix
            normal_data = stats.norm.ppf(uniform_data)
            correlation_matrix = np.corrcoef(normal_data.T)
            return {"correlation_matrix": correlation_matrix}
        
        elif copula_type == CopulaType.STUDENT_T:
            # Estimate correlation and degrees of freedom
            normal_data = stats.norm.ppf(uniform_data)
            correlation_matrix = np.corrcoef(normal_data.T)
            
            # Estimate degrees of freedom using method of moments
            # (Simplified approach)
            df_estimate = self._estimate_t_degrees_of_freedom(uniform_data)
            
            return {
                "correlation_matrix": correlation_matrix,
                "degrees_of_freedom": df_estimate
            }
        
        elif copula_type in [CopulaType.CLAYTON, CopulaType.GUMBEL, CopulaType.FRANK]:
            if n_assets != 2:
                raise NotImplementedError("Archimedean copulas only implemented for 2 assets")
            
            # Estimate theta parameter using method of moments
            theta_estimate = self._estimate_archimedean_theta(uniform_data, copula_type)
            
            return {"theta": theta_estimate}
        
        else:
            raise ValueError(f"Unsupported copula type: {copula_type}")
    
    def _estimate_t_degrees_of_freedom(self, uniform_data: np.ndarray) -> float:
        """Estimate degrees of freedom for Student-t copula"""
        # Convert to t-distribution domain
        t_data = stats.t.ppf(uniform_data, df=10)  # Initial guess
        
        # Use sample kurtosis to estimate degrees of freedom
        # This is a simplified method
        sample_kurtosis = np.mean([stats.kurtosis(t_data[:, i]) for i in range(t_data.shape[1])])
        
        # For t-distribution: kurtosis = 6/(df-4) for df > 4
        if sample_kurtosis > 0:
            df_estimate = 6 / sample_kurtosis + 4
            return max(5.0, min(30.0, df_estimate))  # Reasonable bounds
        else:
            return 10.0  # Default value
    
    def _estimate_archimedean_theta(self, uniform_data: np.ndarray, 
                                  copula_type: CopulaType) -> float:
        """Estimate theta parameter for Archimedean copulas"""
        # Calculate Kendall's tau
        tau = stats.kendalltau(uniform_data[:, 0], uniform_data[:, 1])[0]
        
        if copula_type == CopulaType.CLAYTON:
            # For Clayton: tau = theta / (theta + 2)
            if tau > 0:
                theta = 2 * tau / (1 - tau)
            else:
                theta = 0.1  # Small positive value
        
        elif copula_type == CopulaType.GUMBEL:
            # For Gumbel: tau = 1 - 1/theta
            if tau > 0:
                theta = 1 / (1 - tau)
            else:
                theta = 1.1  # Slightly above 1
        
        elif copula_type == CopulaType.FRANK:
            # For Frank: tau = 1 - 4/theta * (1 - debye_1(theta))
            # This requires numerical solution
            if abs(tau) < 1e-10:
                theta = 0.0
            else:
                # Approximate solution
                theta = 4.0 * tau / (1.0 - abs(tau))
        
        else:
            theta = 1.0
        
        return theta

# Utility functions for correlation analysis
def plot_correlation_matrix(correlation_matrix: np.ndarray, 
                          asset_names: Optional[List[str]] = None) -> None:
    """
    Plot correlation matrix heatmap
    
    Args:
        correlation_matrix: Correlation matrix to plot
        asset_names: Optional asset names for labels
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        plt.figure(figsize=(10, 8))
        
        if asset_names is None:
            asset_names = [f"Asset_{i+1}" for i in range(correlation_matrix.shape[0])]
        
        sns.heatmap(
            correlation_matrix,
            annot=True,
            cmap="RdBu_r",
            center=0,
            xticklabels=asset_names,
            yticklabels=asset_names,
            fmt=".3f"
        )
        
        plt.title("Asset Correlation Matrix")
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        print("Matplotlib/Seaborn not available for plotting")

def simulate_correlated_asset_returns(correlation_matrix: np.ndarray,
                                    volatilities: List[float],
                                    expected_returns: List[float],
                                    n_periods: int,
                                    dt: float = 1/252) -> np.ndarray:
    """
    Simulate correlated asset returns
    
    Args:
        correlation_matrix: Asset correlation matrix
        volatilities: Individual asset volatilities
        expected_returns: Expected returns for each asset
        n_periods: Number of time periods
        dt: Time step size
        
    Returns:
        Simulated returns array
    """
    n_assets = len(volatilities)
    
    # Generate correlated normal innovations
    cholesky_sampler = CholeskySampler()
    innovations = cholesky_sampler.generate_correlated_normals(
        correlation_matrix, n_periods
    )
    
    # Scale by volatilities and add drift
    returns = np.zeros_like(innovations)
    
    for i in range(n_assets):
        drift = expected_returns[i] * dt
        volatility = volatilities[i] * np.sqrt(dt)
        
        returns[:, i] = drift + volatility * innovations[:, i]
    
    return returns

# Example usage and testing
if __name__ == "__main__":
    print("=== CORRELATION ENGINE TESTING ===")
    
    # Generate sample correlation matrix
    n_assets = 4
    np.random.seed(42)
    
    # Create a valid correlation matrix
    A = np.random.randn(n_assets, n_assets)
    correlation_matrix = np.corrcoef(A)
    
    print(f"Sample correlation matrix:")
    print(correlation_matrix)
    
    # Test correlation engine
    corr_engine = CorrelationEngine()
    
    # Validate matrix
    is_valid = corr_engine.validate_correlation_matrix(correlation_matrix)
    print(f"\nCorrelation matrix is valid: {is_valid}")
    
    # Test Gaussian copula sampling
    print("\n=== GAUSSIAN COPULA SAMPLING ===")
    gaussian_params = CopulaParameters(
        copula_type=CopulaType.GAUSSIAN,
        correlation_matrix=correlation_matrix
    )
    
    gaussian_samples = corr_engine.generate_correlated_samples(gaussian_params, 1000)
    print(f"Generated {gaussian_samples.shape[0]} samples with {gaussian_samples.shape[1]} assets")
    print(f"Sample correlation matrix:")
    # Convert back to normal and check correlation
    normal_samples = stats.norm.ppf(gaussian_samples)
    empirical_corr = np.corrcoef(normal_samples.T)
    print(empirical_corr)
    
    # Test Student-t copula
    print("\n=== STUDENT-T COPULA SAMPLING ===")
    t_params = CopulaParameters(
        copula_type=CopulaType.STUDENT_T,
        correlation_matrix=correlation_matrix,
        degrees_of_freedom=5.0
    )
    
    t_samples = corr_engine.generate_correlated_samples(t_params, 1000)
    print(f"Generated Student-t copula samples: {t_samples.shape}")
    
    # Test Clayton copula (2D only)
    print("\n=== CLAYTON COPULA SAMPLING ===")
    clayton_corr = correlation_matrix[:2, :2]  # Use 2x2 submatrix
    clayton_params = CopulaParameters(
        copula_type=CopulaType.CLAYTON,
        correlation_matrix=clayton_corr,
        theta=2.0
    )
    
    clayton_samples = corr_engine.generate_correlated_samples(clayton_params, 1000)
    print(f"Generated Clayton copula samples: {clayton_samples.shape}")
    
    # Test parameter estimation
    print("\n=== PARAMETER ESTIMATION ===")
    copula_sampler = CopulaSampler()
    
    # Generate some test data
    test_data = np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 500)
    
    # Estimate Gaussian copula parameters
    gaussian_est = copula_sampler.estimate_copula_parameters(test_data, CopulaType.GAUSSIAN)
    print(f"Estimated Gaussian correlation:")
    print(gaussian_est["correlation_matrix"])
    
    # Estimate Student-t copula parameters
    t_est = copula_sampler.estimate_copula_parameters(test_data, CopulaType.STUDENT_T)
    print(f"Estimated t-copula correlation:")
    print(t_est["correlation_matrix"])
    print(f"Estimated degrees of freedom: {t_est['degrees_of_freedom']:.2f}")
    
    # Test asset return simulation
    print("\n=== ASSET RETURN SIMULATION ===")
    volatilities = [0.15, 0.20, 0.25, 0.18]
    expected_returns = [0.08, 0.10, 0.12, 0.09]
    
    simulated_returns = simulate_correlated_asset_returns(
        correlation_matrix,
        volatilities,
        expected_returns,
        n_periods=252,  # 1 year of daily returns
        dt=1/252
    )
    
    print(f"Simulated returns shape: {simulated_returns.shape}")
    print(f"Empirical return correlations:")
    print(np.corrcoef(simulated_returns.T))
    
    print("\nCorrelation engine testing completed!")

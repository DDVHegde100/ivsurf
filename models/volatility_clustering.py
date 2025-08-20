"""
Advanced Volatility Clustering Analysis
======================================

Sophisticated volatility clustering detection and analysis with:
- Multi-scale volatility clustering
- Dynamic correlation analysis
- Regime-dependent volatility forecasting
- Cross-asset volatility spillovers
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import jarque_bera, normaltest
from scipy.linalg import LinAlgError
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings

warnings.filterwarnings('ignore')

class VolatilityClusteringAnalyzer:
    """
    Advanced volatility clustering analysis with multi-scale detection
    """
    
    def __init__(self):
        self.clustering_results = {}
        self.volatility_states = None
        self.transition_matrix = None
        
    def analyze_clustering(self, returns_data, window_sizes=[5, 10, 20, 50]):
        """
        Comprehensive volatility clustering analysis
        
        Args:
            returns_data: Dictionary of ticker -> returns series
            window_sizes: List of window sizes for analysis
            
        Returns:
            dict: Comprehensive clustering analysis results
        """
        
        results = {
            'individual_analysis': {},
            'cross_asset_analysis': {},
            'dynamic_clustering': {},
            'volatility_states': {}
        }
        
        # Individual asset analysis
        for ticker, returns in returns_data.items():
            if len(returns) < 100:
                continue
                
            results['individual_analysis'][ticker] = self._analyze_individual_clustering(
                returns, window_sizes
            )
        
        # Cross-asset analysis if multiple assets
        if len(returns_data) > 1:
            results['cross_asset_analysis'] = self._analyze_cross_asset_clustering(
                returns_data, window_sizes
            )
        
        # Dynamic clustering states
        if len(returns_data) >= 1:
            first_ticker = list(returns_data.keys())[0]
            results['dynamic_clustering'] = self._analyze_dynamic_clustering(
                returns_data[first_ticker], window_sizes
            )
            
            results['volatility_states'] = self._identify_volatility_states(
                returns_data
            )
        
        self.clustering_results = results
        return results
    
    def _analyze_individual_clustering(self, returns, window_sizes):
        """Analyze clustering for individual asset"""
        
        results = {
            'basic_tests': {},
            'multi_scale_clustering': {},
            'volatility_persistence': {},
            'clustering_strength': {}
        }
        
        # Basic ARCH effects tests
        results['basic_tests'] = self._arch_tests(returns)
        
        # Multi-scale clustering analysis
        for window in window_sizes:
            if len(returns) > window * 3:
                clustering_metrics = self._calculate_clustering_metrics(returns, window)
                results['multi_scale_clustering'][f'window_{window}'] = clustering_metrics
        
        # Volatility persistence analysis
        results['volatility_persistence'] = self._analyze_volatility_persistence(returns)
        
        # Clustering strength over time
        results['clustering_strength'] = self._measure_clustering_strength(returns)
        
        return results
    
    def _analyze_cross_asset_clustering(self, returns_data, window_sizes):
        """Analyze clustering across multiple assets"""
        
        results = {
            'correlation_clustering': {},
            'volatility_spillovers': {},
            'contagion_analysis': {},
            'dynamic_correlations': {}
        }
        
        # Align data
        aligned_data = self._align_return_data(returns_data)
        
        if aligned_data.empty or len(aligned_data) < 50:
            return results
        
        # Correlation-based clustering
        results['correlation_clustering'] = self._correlation_clustering_analysis(aligned_data)
        
        # Volatility spillover analysis
        results['volatility_spillovers'] = self._volatility_spillover_analysis(aligned_data)
        
        # Contagion analysis
        results['contagion_analysis'] = self._contagion_analysis(aligned_data)
        
        # Dynamic correlations
        for window in window_sizes:
            if len(aligned_data) > window * 2:
                dynamic_corr = self._calculate_dynamic_correlations(aligned_data, window)
                results['dynamic_correlations'][f'window_{window}'] = dynamic_corr
        
        return results
    
    def _analyze_dynamic_clustering(self, returns, window_sizes):
        """Analyze dynamic clustering patterns"""
        
        results = {
            'regime_dependent_clustering': {},
            'time_varying_clustering': {},
            'volatility_bursts': {},
            'calm_periods': {}
        }
        
        # Time-varying clustering intensity
        clustering_intensity = []
        volatility_series = []
        
        for window in window_sizes:
            if len(returns) > window * 3:
                intensity_series = self._calculate_time_varying_clustering(returns, window)
                clustering_intensity.append(intensity_series)
                
                # Calculate rolling volatility
                vol_series = returns.rolling(window=window).std()
                volatility_series.append(vol_series)
        
        results['time_varying_clustering'] = clustering_intensity
        
        # Identify volatility bursts and calm periods
        if volatility_series:
            combined_vol = np.nanmean(volatility_series, axis=0)
            vol_threshold_high = np.nanpercentile(combined_vol, 80)
            vol_threshold_low = np.nanpercentile(combined_vol, 20)
            
            burst_periods = combined_vol > vol_threshold_high
            calm_periods = combined_vol < vol_threshold_low
            
            results['volatility_bursts'] = {
                'periods': burst_periods,
                'threshold': vol_threshold_high,
                'frequency': np.sum(burst_periods) / len(burst_periods) if len(burst_periods) > 0 else 0
            }
            
            results['calm_periods'] = {
                'periods': calm_periods,
                'threshold': vol_threshold_low,
                'frequency': np.sum(calm_periods) / len(calm_periods) if len(calm_periods) > 0 else 0
            }
        
        return results
    
    def _identify_volatility_states(self, returns_data):
        """Identify distinct volatility states using clustering"""
        
        results = {
            'states': {},
            'transition_probabilities': {},
            'state_characteristics': {}
        }
        
        # Combine all volatility measures
        vol_features = []
        
        for ticker, returns in returns_data.items():
            if len(returns) < 50:
                continue
                
            # Calculate various volatility measures
            features = self._extract_volatility_features(returns)
            vol_features.append(features)
        
        if not vol_features:
            return results
        
        # Combine features
        combined_features = np.column_stack(vol_features) if len(vol_features) > 1 else vol_features[0]
        
        # Remove NaN values
        valid_idx = ~np.isnan(combined_features).any(axis=1)
        clean_features = combined_features[valid_idx]
        
        if len(clean_features) < 20:
            return results
        
        # Standardize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(clean_features)
        
        # K-means clustering to identify volatility states
        optimal_k = self._find_optimal_clusters(scaled_features)
        
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        states = kmeans.fit_predict(scaled_features)
        
        results['states'] = {
            'labels': states,
            'centers': kmeans.cluster_centers_,
            'n_clusters': optimal_k,
            'valid_indices': valid_idx
        }
        
        # Calculate transition probabilities
        results['transition_probabilities'] = self._calculate_state_transitions(states)
        
        # Characterize each state
        results['state_characteristics'] = self._characterize_volatility_states(
            states, clean_features
        )
        
        self.volatility_states = results
        return results
    
    def _arch_tests(self, returns):
        """Comprehensive ARCH effects testing"""
        
        results = {}
        
        try:
            # Basic ARCH test (Ljung-Box on squared returns)
            squared_returns = returns ** 2
            
            # Remove NaN values
            clean_squared = squared_returns.dropna()
            
            if len(clean_squared) < 20:
                return {'error': 'Insufficient data for ARCH tests'}
            
            # Ljung-Box test on squared returns
            from statsmodels.stats.diagnostic import acorr_ljungbox
            
            lb_result = acorr_ljungbox(clean_squared, lags=10, return_df=True)
            
            results['ljung_box_squared'] = {
                'statistic': lb_result['lb_stat'].iloc[-1],
                'p_value': lb_result['lb_pvalue'].iloc[-1],
                'significant': lb_result['lb_pvalue'].iloc[-1] < 0.05
            }
            
        except Exception as e:
            results['ljung_box_squared'] = {'error': str(e)}
        
        try:
            # ARCH-LM test
            from arch.diagnostic import het_arch
            
            arch_result = het_arch(returns.dropna())
            
            results['arch_lm'] = {
                'statistic': arch_result[0],
                'p_value': arch_result[1],
                'significant': arch_result[1] < 0.05
            }
            
        except Exception as e:
            results['arch_lm'] = {'error': str(e)}
        
        return results
    
    def _calculate_clustering_metrics(self, returns, window):
        """Calculate clustering metrics for given window"""
        
        metrics = {}
        
        try:
            # Rolling volatility
            vol = returns.rolling(window=window).std()
            vol_clean = vol.dropna()
            
            if len(vol_clean) < 10:
                return {'error': 'Insufficient data'}
            
            # Volatility of volatility (clustering indicator)
            vol_of_vol = vol_clean.rolling(window=min(10, len(vol_clean)//2)).std()
            
            metrics['volatility_of_volatility'] = {
                'mean': float(np.nanmean(vol_of_vol)),
                'std': float(np.nanstd(vol_of_vol)),
                'max': float(np.nanmax(vol_of_vol))
            }
            
            # Autocorrelation of absolute returns
            abs_returns = np.abs(returns)
            autocorr_1 = abs_returns.autocorr(lag=1)
            autocorr_5 = abs_returns.autocorr(lag=5)
            
            metrics['autocorrelations'] = {
                'lag_1': float(autocorr_1) if not np.isnan(autocorr_1) else 0,
                'lag_5': float(autocorr_5) if not np.isnan(autocorr_5) else 0
            }
            
            # Clustering ratio (high vol periods clustering)
            vol_threshold = np.nanpercentile(vol_clean, 75)
            high_vol_periods = vol_clean > vol_threshold
            
            if len(high_vol_periods) > 1:
                clustering_ratio = self._calculate_clustering_ratio(high_vol_periods)
                metrics['clustering_ratio'] = float(clustering_ratio)
            
        except Exception as e:
            metrics['error'] = str(e)
        
        return metrics
    
    def _calculate_clustering_ratio(self, binary_series):
        """Calculate how clustered high volatility periods are"""
        
        if len(binary_series) < 2:
            return 0
        
        # Count consecutive runs of True values
        runs = []
        current_run = 0
        
        for val in binary_series:
            if val:
                current_run += 1
            else:
                if current_run > 0:
                    runs.append(current_run)
                    current_run = 0
        
        if current_run > 0:
            runs.append(current_run)
        
        if not runs:
            return 0
        
        # Clustering ratio: average run length / expected run length under independence
        total_true = np.sum(binary_series)
        p_true = total_true / len(binary_series)
        
        if p_true == 0:
            return 0
        
        expected_run_length = 1 / (1 - p_true) if p_true < 1 else 1
        actual_run_length = np.mean(runs)
        
        return actual_run_length / expected_run_length
    
    def _analyze_volatility_persistence(self, returns):
        """Analyze volatility persistence patterns"""
        
        results = {}
        
        try:
            # Calculate absolute returns for persistence analysis
            abs_returns = np.abs(returns)
            
            # Autocorrelation function of absolute returns
            lags = [1, 2, 3, 5, 10, 20]
            autocorrs = {}
            
            for lag in lags:
                if len(abs_returns) > lag:
                    autocorr = abs_returns.autocorr(lag=lag)
                    autocorrs[f'lag_{lag}'] = float(autocorr) if not np.isnan(autocorr) else 0
            
            results['autocorrelations'] = autocorrs
            
            # Half-life of volatility shocks
            if autocorrs.get('lag_1', 0) > 0:
                # Simple approximation: half-life = ln(0.5) / ln(autocorr)
                half_life = np.log(0.5) / np.log(autocorrs['lag_1'])
                results['volatility_half_life'] = float(half_life) if half_life > 0 else None
            
            # Persistence measure (sum of first 10 autocorrelations)
            persistence = sum([autocorrs.get(f'lag_{i}', 0) for i in range(1, 11)])
            results['persistence_measure'] = float(persistence)
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _measure_clustering_strength(self, returns):
        """Measure clustering strength over time"""
        
        results = {}
        
        try:
            # Rolling clustering strength
            window = min(50, len(returns) // 4)
            
            if window < 10:
                return {'error': 'Insufficient data for clustering strength'}
            
            clustering_strength = []
            
            for i in range(window, len(returns)):
                window_returns = returns.iloc[i-window:i]
                abs_returns = np.abs(window_returns)
                
                # Local clustering measure: autocorrelation of absolute returns
                if len(abs_returns) > 1:
                    autocorr = abs_returns.autocorr(lag=1)
                    clustering_strength.append(autocorr if not np.isnan(autocorr) else 0)
            
            results['time_series'] = clustering_strength
            results['mean_strength'] = float(np.mean(clustering_strength))
            results['max_strength'] = float(np.max(clustering_strength))
            results['min_strength'] = float(np.min(clustering_strength))
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _align_return_data(self, returns_data):
        """Align multiple return series by date"""
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(returns_data)
            
            # Drop rows with any NaN values
            df_clean = df.dropna()
            
            return df_clean
            
        except Exception:
            return pd.DataFrame()
    
    def _correlation_clustering_analysis(self, aligned_data):
        """Analyze correlation-based clustering"""
        
        results = {}
        
        try:
            # Calculate correlation matrix
            corr_matrix = aligned_data.corr()
            
            # PCA analysis
            pca = PCA()
            pca.fit(aligned_data.dropna())
            
            results['correlation_matrix'] = corr_matrix.to_dict()
            results['eigenvalues'] = pca.explained_variance_.tolist()
            results['explained_variance_ratio'] = pca.explained_variance_ratio_.tolist()
            
            # Average correlation
            upper_tri = np.triu(corr_matrix.values, k=1)
            avg_correlation = np.mean(upper_tri[upper_tri != 0])
            results['average_correlation'] = float(avg_correlation)
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _volatility_spillover_analysis(self, aligned_data):
        """Analyze volatility spillovers between assets"""
        
        results = {}
        
        try:
            # Calculate volatility spillover index
            # Simple approach: correlation of absolute returns
            abs_returns = aligned_data.abs()
            spillover_corr = abs_returns.corr()
            
            # Spillover intensity
            upper_tri = np.triu(spillover_corr.values, k=1)
            spillover_intensity = np.mean(upper_tri[upper_tri != 0])
            
            results['spillover_correlation_matrix'] = spillover_corr.to_dict()
            results['spillover_intensity'] = float(spillover_intensity)
            
            # Directional spillovers (simplified)
            directional_spillovers = {}
            for col in spillover_corr.columns:
                others = [c for c in spillover_corr.columns if c != col]
                avg_spillover_to_others = spillover_corr[col][others].mean()
                directional_spillovers[col] = float(avg_spillover_to_others)
            
            results['directional_spillovers'] = directional_spillovers
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _contagion_analysis(self, aligned_data):
        """Analyze contagion effects during stress periods"""
        
        results = {}
        
        try:
            # Identify stress periods (high volatility)
            combined_vol = aligned_data.std(axis=1)
            stress_threshold = np.percentile(combined_vol, 90)
            stress_periods = combined_vol > stress_threshold
            
            if stress_periods.sum() < 5:
                return {'error': 'Insufficient stress periods for analysis'}
            
            # Normal vs stress period correlations
            normal_data = aligned_data[~stress_periods]
            stress_data = aligned_data[stress_periods]
            
            normal_corr = normal_data.corr()
            stress_corr = stress_data.corr()
            
            # Contagion measure: increase in correlations during stress
            contagion_matrix = stress_corr - normal_corr
            
            upper_tri = np.triu(contagion_matrix.values, k=1)
            avg_contagion = np.mean(upper_tri[upper_tri != 0])
            
            results['normal_correlation'] = normal_corr.to_dict()
            results['stress_correlation'] = stress_corr.to_dict()
            results['contagion_matrix'] = contagion_matrix.to_dict()
            results['average_contagion'] = float(avg_contagion)
            results['stress_periods_count'] = int(stress_periods.sum())
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _calculate_dynamic_correlations(self, aligned_data, window):
        """Calculate time-varying correlations"""
        
        results = {}
        
        try:
            dynamic_corrs = {}
            
            for i in range(window, len(aligned_data)):
                window_data = aligned_data.iloc[i-window:i]
                corr_matrix = window_data.corr()
                
                # Store average correlation for this window
                upper_tri = np.triu(corr_matrix.values, k=1)
                avg_corr = np.mean(upper_tri[upper_tri != 0])
                dynamic_corrs[i] = avg_corr
            
            results['time_series'] = dynamic_corrs
            results['mean_correlation'] = float(np.mean(list(dynamic_corrs.values())))
            results['correlation_volatility'] = float(np.std(list(dynamic_corrs.values())))
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _calculate_time_varying_clustering(self, returns, window):
        """Calculate time-varying clustering intensity"""
        
        clustering_series = []
        
        try:
            for i in range(window, len(returns)):
                window_returns = returns.iloc[i-window:i]
                abs_returns = np.abs(window_returns)
                
                # Local clustering measure
                if len(abs_returns) > 1:
                    autocorr = abs_returns.autocorr(lag=1)
                    clustering_series.append(autocorr if not np.isnan(autocorr) else 0)
                
        except Exception:
            pass
        
        return clustering_series
    
    def _extract_volatility_features(self, returns):
        """Extract volatility features for clustering"""
        
        features = []
        
        try:
            # Rolling volatilities at different scales
            windows = [5, 10, 20]
            
            for window in windows:
                vol = returns.rolling(window=window).std()
                features.append(vol)
            
            # Absolute returns
            abs_returns = np.abs(returns)
            features.append(abs_returns)
            
            # Squared returns
            squared_returns = returns ** 2
            features.append(squared_returns)
            
            # Combine features
            combined = np.column_stack([f.values for f in features])
            
            return combined
            
        except Exception:
            return np.array([])
    
    def _find_optimal_clusters(self, features, max_k=8):
        """Find optimal number of clusters using elbow method"""
        
        if len(features) < max_k * 2:
            return 2
        
        try:
            inertias = []
            K_range = range(2, min(max_k + 1, len(features) // 2))
            
            for k in K_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(features)
                inertias.append(kmeans.inertia_)
            
            # Simple elbow detection
            if len(inertias) >= 3:
                diffs = np.diff(inertias)
                second_diffs = np.diff(diffs)
                
                # Find elbow (maximum second difference)
                elbow_idx = np.argmax(second_diffs)
                optimal_k = K_range[elbow_idx + 1]
                return optimal_k
            
        except Exception:
            pass
        
        return 3  # Default fallback
    
    def _calculate_state_transitions(self, states):
        """Calculate state transition probabilities"""
        
        try:
            n_states = len(np.unique(states))
            transition_matrix = np.zeros((n_states, n_states))
            
            for i in range(len(states) - 1):
                current_state = states[i]
                next_state = states[i + 1]
                transition_matrix[current_state][next_state] += 1
            
            # Normalize rows to get probabilities
            row_sums = transition_matrix.sum(axis=1)
            transition_matrix = transition_matrix / row_sums[:, np.newaxis]
            
            return {
                'matrix': transition_matrix.tolist(),
                'steady_state': self._calculate_steady_state(transition_matrix)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_steady_state(self, transition_matrix):
        """Calculate steady-state probabilities"""
        
        try:
            eigenvals, eigenvecs = np.linalg.eig(transition_matrix.T)
            
            # Find eigenvector corresponding to eigenvalue 1
            idx = np.argmin(np.abs(eigenvals - 1))
            steady_state = np.real(eigenvecs[:, idx])
            steady_state = steady_state / steady_state.sum()
            
            return steady_state.tolist()
            
        except Exception:
            return []
    
    def _characterize_volatility_states(self, states, features):
        """Characterize each volatility state"""
        
        characteristics = {}
        
        try:
            unique_states = np.unique(states)
            
            for state in unique_states:
                state_mask = states == state
                state_features = features[state_mask]
                
                characteristics[f'state_{state}'] = {
                    'frequency': float(np.sum(state_mask) / len(states)),
                    'mean_volatility': float(np.mean(state_features[:, 0])),
                    'volatility_persistence': float(np.mean(state_features[:, 1])),
                    'description': self._describe_volatility_state(state_features)
                }
                
        except Exception as e:
            characteristics['error'] = str(e)
        
        return characteristics
    
    def _describe_volatility_state(self, state_features):
        """Generate description for volatility state"""
        
        try:
            mean_vol = np.mean(state_features[:, 0])
            
            if mean_vol > np.percentile(state_features[:, 0], 75):
                return "High Volatility State"
            elif mean_vol < np.percentile(state_features[:, 0], 25):
                return "Low Volatility State"
            else:
                return "Moderate Volatility State"
                
        except Exception:
            return "Unknown State"

#!/usr/bin/env python3
"""
Data Cleaning and Robust Estimation Module
==========================================

Advanced data cleaning for options data with missing value handling,
outlier detection, and robust statistical estimation

Author: IVSURF Systems
Date: August 19, 2025
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import mahalanobis
from scipy.optimize import minimize
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
import warnings
from typing import Tuple, Dict, List, Optional, Union

warnings.filterwarnings('ignore')


class OptionsDataCleaner:
    """
    Advanced options data cleaning and preprocessing
    """
    
    def __init__(self):
        self.outlier_methods = {
            'iqr': self._iqr_outliers,
            'zscore': self._zscore_outliers,
            'mahalanobis': self._mahalanobis_outliers,
            'isolation_forest': self._isolation_forest_outliers,
            'elliptic_envelope': self._elliptic_envelope_outliers
        }
        
        self.cleaning_stats = {}
    
    def clean_options_data(
        self,
        options_df: pd.DataFrame,
        current_price: float,
        outlier_method: str = 'iqr',
        volume_threshold: int = 0,
        oi_threshold: int = 0,
        spread_threshold: float = 0.5,
        iv_bounds: Tuple[float, float] = (0.01, 5.0),
        moneyness_bounds: Tuple[float, float] = (0.5, 2.0)
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Comprehensive options data cleaning
        
        Args:
            options_df: Raw options dataframe
            current_price: Current stock price
            outlier_method: Method for outlier detection
            volume_threshold: Minimum volume filter
            oi_threshold: Minimum open interest filter
            spread_threshold: Maximum bid-ask spread ratio
            iv_bounds: (min_iv, max_iv) bounds for implied volatility
            moneyness_bounds: (min_moneyness, max_moneyness) bounds
        
        Returns:
            Cleaned dataframe and cleaning statistics
        """
        
        original_size = len(options_df)
        df_clean = options_df.copy()
        cleaning_log = []
        
        # 1. Basic data validation
        df_clean, log1 = self._basic_validation(df_clean)
        cleaning_log.extend(log1)
        
        # 2. Volume and Open Interest filtering
        if volume_threshold > 0:
            before_vol = len(df_clean)
            df_clean = df_clean[df_clean['volume'].fillna(0) >= volume_threshold]
            after_vol = len(df_clean)
            cleaning_log.append(f"Volume filter: {before_vol - after_vol} removed")
        
        if oi_threshold > 0:
            before_oi = len(df_clean)
            df_clean = df_clean[df_clean['openInterest'].fillna(0) >= oi_threshold]
            after_oi = len(df_clean)
            cleaning_log.append(f"Open Interest filter: {before_oi - after_oi} removed")
        
        # 3. Bid-Ask spread filtering
        if spread_threshold > 0:
            df_clean, spread_removed = self._filter_bid_ask_spread(
                df_clean, spread_threshold
            )
            cleaning_log.append(f"Bid-Ask spread filter: {spread_removed} removed")
        
        # 4. Moneyness filtering
        df_clean['moneyness'] = df_clean['strike'] / current_price
        before_money = len(df_clean)
        df_clean = df_clean[
            (df_clean['moneyness'] >= moneyness_bounds[0]) & 
            (df_clean['moneyness'] <= moneyness_bounds[1])
        ]
        after_money = len(df_clean)
        cleaning_log.append(f"Moneyness filter: {before_money - after_money} removed")
        
        # 5. Calculate implied volatilities and filter
        df_clean = self._calculate_and_filter_iv(
            df_clean, current_price, iv_bounds
        )
        
        # 6. Outlier detection and removal
        if len(df_clean) > 10:  # Need sufficient data for outlier detection
            df_clean, outliers_removed = self._detect_and_remove_outliers(
                df_clean, outlier_method
            )
            cleaning_log.append(f"Outlier detection ({outlier_method}): {outliers_removed} removed")
        
        # 7. Final validation
        df_clean, log_final = self._final_validation(df_clean)
        cleaning_log.extend(log_final)
        
        # Prepare statistics
        stats = {
            'original_size': original_size,
            'final_size': len(df_clean),
            'removal_rate': (original_size - len(df_clean)) / original_size,
            'cleaning_log': cleaning_log,
            'data_quality_score': self._calculate_quality_score(df_clean)
        }
        
        self.cleaning_stats = stats
        
        return df_clean, stats
    
    def _basic_validation(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Basic data validation and cleaning"""
        
        log = []
        initial_size = len(df)
        
        # Remove rows with missing critical data
        required_columns = ['strike', 'bid', 'ask']
        for col in required_columns:
            if col in df.columns:
                before = len(df)
                df = df.dropna(subset=[col])
                after = len(df)
                if before != after:
                    log.append(f"Missing {col}: {before - after} removed")
        
        # Ensure positive strikes and prices
        if 'strike' in df.columns:
            before = len(df)
            df = df[df['strike'] > 0]
            after = len(df)
            if before != after:
                log.append(f"Non-positive strikes: {before - after} removed")
        
        # Ensure positive bid/ask
        for col in ['bid', 'ask']:
            if col in df.columns:
                before = len(df)
                df = df[df[col] >= 0]
                after = len(df)
                if before != after:
                    log.append(f"Negative {col}: {before - after} removed")
        
        # Ensure bid <= ask
        if 'bid' in df.columns and 'ask' in df.columns:
            before = len(df)
            df = df[df['bid'] <= df['ask']]
            after = len(df)
            if before != after:
                log.append(f"Bid > Ask: {before - after} removed")
        
        return df, log
    
    def _filter_bid_ask_spread(self, df: pd.DataFrame, threshold: float) -> Tuple[pd.DataFrame, int]:
        """Filter options by bid-ask spread"""
        
        if 'bid' not in df.columns or 'ask' not in df.columns:
            return df, 0
        
        # Calculate spread ratio
        mid_price = (df['bid'] + df['ask']) / 2
        spread_ratio = (df['ask'] - df['bid']) / mid_price
        
        before = len(df)
        df_filtered = df[spread_ratio <= threshold]
        after = len(df_filtered)
        
        return df_filtered, before - after
    
    def _calculate_and_filter_iv(
        self, 
        df: pd.DataFrame, 
        current_price: float, 
        iv_bounds: Tuple[float, float]
    ) -> pd.DataFrame:
        """Calculate implied volatilities and filter by bounds"""
        
        from core.black_scholes import implied_volatility
        from datetime import datetime
        
        df = df.copy()
        iv_list = []
        
        for _, row in df.iterrows():
            try:
                # Calculate time to expiry
                if 'expiry' in row:
                    expiry_date = pd.to_datetime(row['expiry'])
                    days_to_expiry = (expiry_date - datetime.now()).days
                    time_to_expiry = max(days_to_expiry / 365.0, 1/365)
                else:
                    time_to_expiry = 0.083  # ~1 month default
                
                # Get market price (mid of bid/ask)
                market_price = (row['bid'] + row['ask']) / 2
                
                if market_price <= 0:
                    iv_list.append(np.nan)
                    continue
                
                # Determine option type
                option_type = row.get('option_type', 'call')
                if pd.isna(option_type):
                    option_type = 'call'
                
                # Calculate implied volatility
                iv = implied_volatility(
                    market_price, current_price, row['strike'],
                    time_to_expiry, 0.05, option_type
                )
                
                iv_list.append(iv)
                
            except Exception:
                iv_list.append(np.nan)
        
        df['implied_volatility'] = iv_list
        df['time_to_expiry'] = df.get('time_to_expiry', 0.083)
        df['market_price'] = (df['bid'] + df['ask']) / 2
        
        # Filter by IV bounds
        before = len(df)
        df = df[
            (df['implied_volatility'] >= iv_bounds[0]) & 
            (df['implied_volatility'] <= iv_bounds[1]) &
            (~df['implied_volatility'].isna())
        ]
        
        return df
    
    def _detect_and_remove_outliers(
        self, 
        df: pd.DataFrame, 
        method: str
    ) -> Tuple[pd.DataFrame, int]:
        """Detect and remove outliers using specified method"""
        
        if method not in self.outlier_methods:
            return df, 0
        
        before = len(df)
        outlier_mask = self.outlier_methods[method](df)
        df_clean = df[~outlier_mask]
        after = len(df_clean)
        
        return df_clean, before - after
    
    def _iqr_outliers(self, df: pd.DataFrame) -> np.ndarray:
        """Detect outliers using Interquartile Range method"""
        
        features = ['implied_volatility', 'market_price', 'moneyness']
        available_features = [f for f in features if f in df.columns]
        
        if not available_features:
            return np.zeros(len(df), dtype=bool)
        
        outlier_mask = np.zeros(len(df), dtype=bool)
        
        for feature in available_features:
            values = df[feature].values
            q25, q75 = np.percentile(values, [25, 75])
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            
            feature_outliers = (values < lower_bound) | (values > upper_bound)
            outlier_mask |= feature_outliers
        
        return outlier_mask
    
    def _zscore_outliers(self, df: pd.DataFrame, threshold: float = 3.0) -> np.ndarray:
        """Detect outliers using Z-score method"""
        
        features = ['implied_volatility', 'market_price', 'moneyness']
        available_features = [f for f in features if f in df.columns]
        
        if not available_features:
            return np.zeros(len(df), dtype=bool)
        
        outlier_mask = np.zeros(len(df), dtype=bool)
        
        for feature in available_features:
            values = df[feature].values
            z_scores = np.abs(stats.zscore(values))
            feature_outliers = z_scores > threshold
            outlier_mask |= feature_outliers
        
        return outlier_mask
    
    def _mahalanobis_outliers(self, df: pd.DataFrame, threshold: float = 3.0) -> np.ndarray:
        """Detect outliers using Mahalanobis distance"""
        
        features = ['implied_volatility', 'market_price', 'moneyness']
        available_features = [f for f in features if f in df.columns and not df[f].isna().all()]
        
        if len(available_features) < 2:
            return np.zeros(len(df), dtype=bool)
        
        try:
            # Prepare data
            data = df[available_features].dropna()
            if len(data) < 3:
                return np.zeros(len(df), dtype=bool)
            
            # Calculate covariance matrix
            cov_matrix = np.cov(data.T)
            
            # Calculate Mahalanobis distances
            mean = data.mean().values
            distances = []
            
            for _, row in df.iterrows():
                row_values = row[available_features].values
                if np.any(np.isnan(row_values)):
                    distances.append(0)
                else:
                    try:
                        dist = mahalanobis(row_values, mean, np.linalg.inv(cov_matrix))
                        distances.append(dist)
                    except:
                        distances.append(0)
            
            distances = np.array(distances)
            return distances > threshold
            
        except Exception:
            return np.zeros(len(df), dtype=bool)
    
    def _isolation_forest_outliers(
        self, 
        df: pd.DataFrame, 
        contamination: float = 0.1
    ) -> np.ndarray:
        """Detect outliers using Isolation Forest"""
        
        features = ['implied_volatility', 'market_price', 'moneyness']
        available_features = [f for f in features if f in df.columns]
        
        if len(available_features) < 2:
            return np.zeros(len(df), dtype=bool)
        
        try:
            # Prepare data
            data = df[available_features].fillna(df[available_features].mean())
            
            # Fit Isolation Forest
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=42
            )
            
            outlier_labels = iso_forest.fit_predict(data)
            return outlier_labels == -1
            
        except Exception:
            return np.zeros(len(df), dtype=bool)
    
    def _elliptic_envelope_outliers(
        self, 
        df: pd.DataFrame, 
        contamination: float = 0.1
    ) -> np.ndarray:
        """Detect outliers using Elliptic Envelope"""
        
        features = ['implied_volatility', 'market_price', 'moneyness']
        available_features = [f for f in features if f in df.columns]
        
        if len(available_features) < 2:
            return np.zeros(len(df), dtype=bool)
        
        try:
            # Prepare data
            data = df[available_features].fillna(df[available_features].mean())
            
            # Fit Elliptic Envelope
            envelope = EllipticEnvelope(
                contamination=contamination,
                random_state=42
            )
            
            outlier_labels = envelope.fit_predict(data)
            return outlier_labels == -1
            
        except Exception:
            return np.zeros(len(df), dtype=bool)
    
    def _final_validation(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Final validation and cleanup"""
        
        log = []
        
        # Remove any remaining NaN values in critical columns
        critical_cols = ['strike', 'implied_volatility', 'market_price']
        available_critical = [c for c in critical_cols if c in df.columns]
        
        if available_critical:
            before = len(df)
            df = df.dropna(subset=available_critical)
            after = len(df)
            if before != after:
                log.append(f"Final NaN cleanup: {before - after} removed")
        
        # Sort by strike and expiry for better organization
        sort_cols = []
        if 'expiry' in df.columns:
            sort_cols.append('expiry')
        if 'strike' in df.columns:
            sort_cols.append('strike')
        
        if sort_cols:
            df = df.sort_values(sort_cols)
        
        return df, log
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score (0-1)"""
        
        if len(df) == 0:
            return 0.0
        
        score = 1.0
        
        # Penalize for missing data
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        score -= missing_ratio * 0.3
        
        # Reward for data diversity
        if 'strike' in df.columns:
            unique_strikes = len(df['strike'].unique())
            total_strikes = len(df)
            diversity_score = min(unique_strikes / max(total_strikes * 0.1, 1), 1.0)
            score += diversity_score * 0.2
        
        # Reward for volume/OI presence
        volume_score = 0
        if 'volume' in df.columns:
            volume_score += 0.1 if df['volume'].sum() > 0 else 0
        if 'openInterest' in df.columns:
            volume_score += 0.1 if df['openInterest'].sum() > 0 else 0
        score += volume_score
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))


class RobustEstimation:
    """
    Robust statistical estimation methods for options data
    """
    
    @staticmethod
    def robust_mean(data: np.ndarray, method: str = 'trimmed') -> float:
        """Calculate robust mean using various methods"""
        
        if method == 'trimmed':
            return stats.trim_mean(data, 0.1)  # Trim 10% from each end
        elif method == 'winsorized':
            from scipy.stats.mstats import winsorize
            return np.mean(winsorize(data, limits=[0.05, 0.05]))
        elif method == 'median':
            return np.median(data)
        elif method == 'huber':
            # Huber M-estimator (simplified)
            return np.median(data)  # Fallback to median
        else:
            return np.mean(data)
    
    @staticmethod
    def robust_std(data: np.ndarray, method: str = 'mad') -> float:
        """Calculate robust standard deviation"""
        
        if method == 'mad':
            # Median Absolute Deviation
            median = np.median(data)
            mad = np.median(np.abs(data - median))
            return mad * 1.4826  # Scale factor for normal distribution
        elif method == 'iqr':
            # Interquartile Range
            q75, q25 = np.percentile(data, [75, 25])
            return (q75 - q25) / 1.349  # Scale factor for normal distribution
        else:
            return np.std(data)
    
    @staticmethod
    def detect_changepoints(
        data: np.ndarray, 
        method: str = 'pelt'
    ) -> List[int]:
        """Detect structural breaks/changepoints in time series data"""
        
        try:
            if method == 'cusum':
                # Simple CUSUM test
                mean_val = np.mean(data)
                cusum = np.cumsum(data - mean_val)
                changepoints = []
                
                # Find local maxima/minima as potential changepoints
                for i in range(1, len(cusum) - 1):
                    if (cusum[i] > cusum[i-1] and cusum[i] > cusum[i+1]) or \
                       (cusum[i] < cusum[i-1] and cusum[i] < cusum[i+1]):
                        changepoints.append(i)
                
                return changepoints
            else:
                # Simple variance-based method
                window_size = max(10, len(data) // 10)
                changepoints = []
                
                for i in range(window_size, len(data) - window_size):
                    before = data[i-window_size:i]
                    after = data[i:i+window_size]
                    
                    if len(before) > 1 and len(after) > 1:
                        var_before = np.var(before)
                        var_after = np.var(after)
                        
                        # Significant variance change indicates changepoint
                        if abs(var_before - var_after) > 0.5 * (var_before + var_after):
                            changepoints.append(i)
                
                return changepoints
                
        except Exception:
            return []


def clean_options_data(
    options_df: pd.DataFrame,
    current_price: float,
    **kwargs
) -> Tuple[pd.DataFrame, Dict]:
    """
    Convenience function for options data cleaning
    """
    cleaner = OptionsDataCleaner()
    return cleaner.clean_options_data(options_df, current_price, **kwargs)

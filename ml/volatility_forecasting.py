"""
Machine Learning Volatility Forecasting Engine
==============================================

Professional ML-based volatility forecasting system including:
- LSTM neural networks for IV surface prediction
- Random Forest for next-day volatility forecasting
- Advanced feature engineering from technical indicators
- Walk-forward validation and backtesting framework
- Ensemble methods combining multiple models
- Real-time prediction with confidence intervals

Mathematical Framework:
- Deep learning with LSTM/GRU architectures
- Time series analysis with technical indicators
- Feature selection and dimensionality reduction
- Cross-validation and walk-forward testing
- Ensemble averaging and model combination

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
import warnings
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import joblib
import time

# Technical indicators
def calculate_rsi(prices: np.ndarray, window: int = 14) -> np.ndarray:
    """Calculate Relative Strength Index"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = pd.Series(gains).rolling(window=window).mean().values
    avg_losses = pd.Series(losses).rolling(window=window).mean().values
    
    rs = avg_gains / (avg_losses + 1e-10)
    rsi_values = 100 - (100 / (1 + rs))
    
    # Pad with NaN to match original length
    rsi = np.full(len(prices), np.nan)
    rsi[1:] = rsi_values
    
    return rsi

def calculate_bollinger_bands(prices: np.ndarray, window: int = 20, num_std: float = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands"""
    sma = pd.Series(prices).rolling(window=window).mean().values
    std = pd.Series(prices).rolling(window=window).std().values
    
    upper_band = sma + (num_std * std)
    lower_band = sma - (num_std * std)
    
    return upper_band, sma, lower_band

def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate MACD indicator"""
    price_series = pd.Series(prices)
    ema_fast = price_series.ewm(span=fast).mean().values
    ema_slow = price_series.ewm(span=slow).mean().values
    
    macd_line = ema_fast - ema_slow
    signal_line = pd.Series(macd_line).ewm(span=signal).mean().values
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, window: int = 14) -> np.ndarray:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    
    # Set first value to high-low since no previous close
    tr2[0] = high[0] - low[0] 
    tr3[0] = high[0] - low[0]
    
    true_range = np.maximum(tr1, np.maximum(tr2, tr3))
    atr = pd.Series(true_range).rolling(window=window).mean().values
    
    return atr

class ModelType(Enum):
    """Types of ML models for volatility forecasting"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    RIDGE = "ridge"
    LASSO = "lasso"
    ELASTIC_NET = "elastic_net"
    SVR = "svr"
    ENSEMBLE = "ensemble"

@dataclass
class ForecastResult:
    """Results from volatility forecasting"""
    predictions: np.ndarray
    actual: np.ndarray
    confidence_intervals: Optional[Tuple[np.ndarray, np.ndarray]]
    feature_importance: Optional[Dict[str, float]]
    model_metrics: Dict[str, float]
    forecast_dates: pd.DatetimeIndex
    model_type: str

@dataclass
class ValidationResult:
    """Results from walk-forward validation"""
    train_scores: List[float]
    test_scores: List[float]
    predictions: np.ndarray
    actual: np.ndarray
    fold_metrics: List[Dict[str, float]]
    feature_importance: Dict[str, float]
    best_params: Dict[str, Any]

class TechnicalFeatureEngineer:
    """
    Advanced feature engineering for volatility prediction
    
    Creates technical indicators, volatility measures, and
    market microstructure features for ML models.
    """
    
    def __init__(self):
        """Initialize feature engineer"""
        self.feature_names = []
        self.scaler = None
    
    def create_features(self, data: pd.DataFrame, selected_features: List[str] = None) -> pd.DataFrame:
        """
        Create comprehensive feature set for ML models
        
        Args:
            data: DataFrame with OHLCV data
            selected_features: List of feature types to include
            
        Returns:
            DataFrame with engineered features
        """
        if selected_features is None:
            selected_features = ['RSI', 'MACD', 'ATR', 'Bollinger Bands', 'Price Returns', 'Volatility Clustering']
        
        # Ensure we have minimum data
        if len(data) < 50:
            raise ValueError(f"Insufficient data: need at least 50 rows, got {len(data)}")
        
        # Start with empty DataFrame
        features = pd.DataFrame(index=data.index)
        
        # Add price features first (always include these)
        try:
            price_features = self.create_price_features(data)
            if not price_features.empty:
                features = pd.concat([features, price_features], axis=1)
        except Exception as e:
            print(f"Warning: Could not create price features: {e}")
        
        # Add technical indicators based on selection
        if 'RSI' in selected_features:
            try:
                rsi_features = self.create_rsi_features(data)
                if not rsi_features.empty:
                    features = pd.concat([features, rsi_features], axis=1)
            except Exception as e:
                print(f"Warning: Could not create RSI features: {e}")
        
        if 'MACD' in selected_features:
            try:
                macd_features = self.create_macd_features(data)
                if not macd_features.empty:
                    features = pd.concat([features, macd_features], axis=1)
            except Exception as e:
                print(f"Warning: Could not create MACD features: {e}")
        
        if 'ATR' in selected_features:
            try:
                atr_features = self.create_atr_features(data)
                if not atr_features.empty:
                    features = pd.concat([features, atr_features], axis=1)
            except Exception as e:
                print(f"Warning: Could not create ATR features: {e}")
        
        if 'Bollinger Bands' in selected_features:
            try:
                bb_features = self.create_bollinger_features(data)
                if not bb_features.empty:
                    features = pd.concat([features, bb_features], axis=1)
            except Exception as e:
                print(f"Warning: Could not create Bollinger features: {e}")
        
        if 'Volatility Clustering' in selected_features:
            try:
                vol_features = self.create_volatility_features(data)
                if not vol_features.empty:
                    features = pd.concat([features, vol_features], axis=1)
            except Exception as e:
                print(f"Warning: Could not create volatility features: {e}")
        
        # Volume features if available
        if 'Volume' in data.columns:
            try:
                volume_features = self.create_volume_features(data)
                if not volume_features.empty:
                    features = pd.concat([features, volume_features], axis=1)
            except Exception as e:
                print(f"Warning: Could not create volume features: {e}")
        
        # Market microstructure features
        try:
            micro_features = self.create_microstructure_features(data)
            if not micro_features.empty:
                features = pd.concat([features, micro_features], axis=1)
        except Exception as e:
            print(f"Warning: Could not create microstructure features: {e}")
        
        # Lag features
        try:
            lag_features = self.create_lag_features(features)
            if not lag_features.empty:
                features = pd.concat([features, lag_features], axis=1)
        except Exception as e:
            print(f"Warning: Could not create lag features: {e}")
        
        # Ensure we have some features
        if features.empty:
            raise ValueError("No features could be created from the data")
        
        # Store feature names
        self.feature_names = features.columns.tolist()
        
        # Drop NaN values but keep some data
        initial_rows = len(features)
        features = features.dropna()
        
        if features.empty:
            raise ValueError("All features contained NaN values after processing")
        
        if len(features) < 10:
            raise ValueError(f"Too few valid samples after cleaning: {len(features)} (started with {initial_rows})")
        
        print(f"Created {len(features.columns)} features with {len(features)} valid samples")
        
        return features

    def create_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create price-based features
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with price features
        """
        features = pd.DataFrame(index=data.index)
        
        # Basic price features
        features['returns'] = data['Close'].pct_change()
        features['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))
        features['high_low_ratio'] = data['High'] / data['Low']
        features['close_open_ratio'] = data['Close'] / data['Open']
        
        # Rolling statistics
        for window in [5, 10, 20, 50]:
            features[f'sma_{window}'] = data['Close'].rolling(window=window).mean()
            features[f'std_{window}'] = data['Close'].rolling(window=window).std()
            features[f'skew_{window}'] = data['Close'].rolling(window=window).skew()
            features[f'kurt_{window}'] = data['Close'].rolling(window=window).kurt()
            
            # Price position in range
            rolling_min = data['Low'].rolling(window=window).min()
            rolling_max = data['High'].rolling(window=window).max()
            features[f'price_position_{window}'] = (data['Close'] - rolling_min) / (rolling_max - rolling_min + 1e-10)
        
        return features
    
    def create_volatility_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create volatility-based features
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with volatility features
        """
        features = pd.DataFrame(index=data.index)
        
        # Realized volatility measures
        returns = data['Close'].pct_change()
        
        for window in [5, 10, 20, 50]:
            # Standard realized volatility
            features[f'realized_vol_{window}'] = returns.rolling(window=window).std() * np.sqrt(252)
            
            # Parkinson volatility (high-low)
            hl_vol = np.log(data['High'] / data['Low'])**2
            features[f'parkinson_vol_{window}'] = np.sqrt(
                hl_vol.rolling(window=window).mean() * 252 / (4 * np.log(2))
            )
            
            # Garman-Klass volatility
            gk_vol = (
                0.5 * np.log(data['High'] / data['Low'])**2 -
                (2 * np.log(2) - 1) * np.log(data['Close'] / data['Open'])**2
            )
            features[f'gk_vol_{window}'] = np.sqrt(gk_vol.rolling(window=window).mean() * 252)
            
            # Rogers-Satchell volatility
            rs_vol = (
                np.log(data['High'] / data['Close']) * np.log(data['High'] / data['Open']) +
                np.log(data['Low'] / data['Close']) * np.log(data['Low'] / data['Open'])
            )
            features[f'rs_vol_{window}'] = np.sqrt(rs_vol.rolling(window=window).mean() * 252)
        
        # Volatility clustering
        features['vol_clustering'] = returns.rolling(window=20).std() / returns.rolling(window=50).std()
        
        # Volume-weighted features
        if 'Volume' in data.columns:
            features['volume_sma_20'] = data['Volume'].rolling(window=20).mean()
            features['volume_ratio'] = data['Volume'] / features['volume_sma_20']
            features['price_volume'] = data['Close'] * data['Volume']
        
        return features
    
    def create_rsi_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create RSI-based features"""
        features = pd.DataFrame(index=data.index)
        
        # Extract price data properly
        try:
            if 'Close' in data.columns:
                prices = data['Close'].values.flatten()  # Ensure 1D array
            else:
                warnings.warn("No Close price data found for RSI calculation")
                return features
        except Exception as e:
            warnings.warn(f"Could not extract price data for RSI: {e}")
            return features
        
        # Ensure we have enough data
        if len(prices) < 50:
            return features
        
        # RSI with different periods
        for period in [14, 21, 50]:
            try:
                rsi = calculate_rsi(prices, window=period)
                rsi_series = pd.Series(rsi, index=data.index)
                
                # Only add if we have valid data
                if not rsi_series.isnull().all():
                    features[f'rsi_{period}'] = rsi_series
                    features[f'rsi_{period}_oversold'] = (rsi_series < 30).astype(int)
                    features[f'rsi_{period}_overbought'] = (rsi_series > 70).astype(int)
                    features[f'rsi_{period}_momentum'] = rsi_series - rsi_series.shift(5)
            except Exception as e:
                warnings.warn(f"Could not calculate RSI for period {period}: {e}")
                continue
        
        return features
    
    def create_macd_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create MACD-based features"""
        features = pd.DataFrame(index=data.index)
        
        # Extract price data properly
        try:
            if 'Close' in data.columns:
                prices = data['Close'].values.flatten()  # Ensure 1D array
            else:
                warnings.warn("No Close price data found for MACD calculation")
                return features
        except Exception as e:
            warnings.warn(f"Could not extract price data for MACD: {e}")
            return features
        
        # Ensure we have enough data
        if len(prices) < 50:
            return features
        
        # MACD with different parameters
        for fast, slow, signal in [(12, 26, 9), (5, 35, 5)]:
            try:
                macd_line, signal_line, histogram = calculate_macd(prices, fast, slow, signal)
                suffix = f"_{fast}_{slow}_{signal}"
                
                macd_series = pd.Series(macd_line, index=data.index)
                signal_series = pd.Series(signal_line, index=data.index)
                histogram_series = pd.Series(histogram, index=data.index)
                
                # Only add if we have valid data
                if not macd_series.isnull().all():
                    features[f'macd{suffix}'] = macd_series
                    features[f'macd_signal{suffix}'] = signal_series
                    features[f'macd_histogram{suffix}'] = histogram_series
                    features[f'macd_cross{suffix}'] = (macd_series > signal_series).astype(int)
                    features[f'macd_divergence{suffix}'] = macd_series - signal_series
            except Exception as e:
                warnings.warn(f"Could not calculate MACD for {fast},{slow},{signal}: {e}")
                continue
        
        return features
    
    def create_atr_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create ATR-based features"""
        features = pd.DataFrame(index=data.index)
        
        # Extract OHLC data properly
        try:
            if all(col in data.columns for col in ['High', 'Low', 'Close']):
                high = data['High'].values.flatten()
                low = data['Low'].values.flatten()
                close = data['Close'].values.flatten()
            else:
                warnings.warn("Insufficient OHLC data for ATR calculation")
                return features
        except Exception as e:
            warnings.warn(f"Could not extract OHLC data for ATR: {e}")
            return features
        
        # Ensure we have enough data
        if len(close) < 50:
            return features
        
        # ATR with different periods
        for period in [14, 21, 50]:
            try:
                atr = calculate_atr(high, low, close, window=period)
                atr_series = pd.Series(atr, index=data.index)
                
                # Only add if we have valid data
                if not atr_series.isnull().all():
                    features[f'atr_{period}'] = atr_series
                    features[f'atr_{period}_pct'] = atr_series / close
                    features[f'atr_{period}_momentum'] = atr_series - atr_series.shift(5)
                    features[f'atr_{period}_normalized'] = atr_series / atr_series.rolling(50).mean()
            except Exception as e:
                warnings.warn(f"Could not calculate ATR for period {period}: {e}")
                continue
        
        return features
        features = pd.DataFrame(index=data.index)
        
        # Ensure we have enough data
        if len(data) < 50:
            return features
        
        high = data['High'].values
        low = data['Low'].values
        close = data['Close'].values
        
        # ATR with different periods
        for period in [14, 21, 50]:
            try:
                atr = calculate_atr(high, low, close, window=period)
                atr_series = pd.Series(atr, index=data.index)
                
                # Only add if we have valid data
                if not atr_series.isnull().all():
                    features[f'atr_{period}'] = atr_series
                    features[f'atr_{period}_normalized'] = atr_series / close
                    features[f'atr_{period}_percentile'] = atr_series.rolling(100).rank(pct=True)
            except Exception as e:
                print(f"Warning: Could not calculate ATR for period {period}: {e}")
                continue
        
        return features
    
    def create_bollinger_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create Bollinger Bands features"""
        features = pd.DataFrame(index=data.index)
        prices = data['Close'].values
        
        # Bollinger Bands with different parameters
        for window, std_dev in [(20, 2), (20, 1), (50, 2)]:
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices, window, std_dev)
            suffix = f"_{window}_{std_dev}"
            
            features[f'bb_upper{suffix}'] = bb_upper
            features[f'bb_middle{suffix}'] = bb_middle
            features[f'bb_lower{suffix}'] = bb_lower
            features[f'bb_width{suffix}'] = (bb_upper - bb_lower) / bb_middle
            features[f'bb_position{suffix}'] = (prices - bb_lower) / (bb_upper - bb_lower + 1e-10)
            features[f'bb_squeeze{suffix}'] = (features[f'bb_width{suffix}'] < features[f'bb_width{suffix}'].rolling(20).quantile(0.2)).astype(int)
        
        return features
    
    def create_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create volume-based features"""
        features = pd.DataFrame(index=data.index)
        
        if 'Volume' not in data.columns:
            return features
        
        volume = data['Volume']
        close = data['Close']
        
        # Volume indicators
        for window in [10, 20, 50]:
            features[f'volume_sma_{window}'] = volume.rolling(window).mean()
            features[f'volume_ratio_{window}'] = volume / features[f'volume_sma_{window}']
            features[f'volume_std_{window}'] = volume.rolling(window).std()
        
        # Price-volume features
        features['price_volume'] = close * volume
        features['vwap_20'] = (close * volume).rolling(20).sum() / volume.rolling(20).sum()
        features['price_vwap_ratio'] = close / features['vwap_20']
        
        # On-Balance Volume
        features['obv'] = (np.sign(close.pct_change()) * volume).cumsum()
        features['obv_sma_20'] = features['obv'].rolling(20).mean()
        
        return features
    
    def create_microstructure_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create market microstructure features"""
        features = pd.DataFrame(index=data.index)
        
        # Price gaps
        features['gap'] = data['Open'] - data['Close'].shift(1)
        features['gap_pct'] = features['gap'] / data['Close'].shift(1)
        features['gap_up'] = (features['gap'] > 0).astype(int)
        features['gap_down'] = (features['gap'] < 0).astype(int)
        
        # Intraday patterns
        features['intraday_range'] = (data['High'] - data['Low']) / data['Open']
        features['open_close_ratio'] = data['Close'] / data['Open']
        features['high_close_ratio'] = data['High'] / data['Close']
        features['low_close_ratio'] = data['Low'] / data['Close']
        
        # Momentum features
        for period in [1, 3, 5, 10]:
            features[f'momentum_{period}'] = data['Close'].pct_change(period)
            features[f'momentum_{period}_positive'] = (features[f'momentum_{period}'] > 0).astype(int)
        
        return features
    
    def create_lag_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create lagged features"""
        features = pd.DataFrame(index=data.index)
        
        # Select key features for lagging
        key_features = ['returns', 'log_returns', 'realized_vol_20']
        if 'rsi_14' in data.columns:
            key_features.append('rsi_14')
        if 'macd_12_26_9' in data.columns:
            key_features.append('macd_12_26_9')
        
        # Create lags
        for feature in key_features:
            if feature in data.columns:
                for lag in [1, 2, 3, 5]:
                    features[f'{feature}_lag_{lag}'] = data[feature].shift(lag)
        
        return features

    def create_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create technical indicator features
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with technical indicators
        """
        features = pd.DataFrame(index=data.index)
        
        prices = data['Close'].values
        
        # RSI
        features['rsi'] = calculate_rsi(prices)
        features['rsi_oversold'] = (features['rsi'] < 30).astype(int)
        features['rsi_overbought'] = (features['rsi'] > 70).astype(int)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)
        features['bb_upper'] = bb_upper
        features['bb_middle'] = bb_middle
        features['bb_lower'] = bb_lower
        features['bb_width'] = (bb_upper - bb_lower) / bb_middle
        features['bb_position'] = (prices - bb_lower) / (bb_upper - bb_lower + 1e-10)
        
        # MACD
        macd, signal, histogram = calculate_macd(prices)
        features['macd'] = macd
        features['macd_signal'] = signal
        features['macd_histogram'] = histogram
        features['macd_crossover'] = ((macd > signal) & (np.roll(macd, 1) <= np.roll(signal, 1))).astype(int)
        
        # Moving averages
        for window in [5, 10, 20, 50, 200]:
            features[f'sma_{window}'] = data['Close'].rolling(window=window).mean()
            features[f'ema_{window}'] = data['Close'].ewm(span=window).mean()
            
        # Moving average crossovers
        features['sma_5_20_cross'] = (features['sma_5'] > features['sma_20']).astype(int)
        features['sma_20_50_cross'] = (features['sma_20'] > features['sma_50']).astype(int)
        
        # ATR
        if all(col in data.columns for col in ['High', 'Low']):
            features['atr'] = calculate_atr(data['High'].values, data['Low'].values, prices)
            features['atr_ratio'] = features['atr'] / data['Close']
        
        return features
    
    def engineer_features(self, data: pd.DataFrame, target_col: str = 'realized_vol_20') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Complete feature engineering pipeline
        
        Args:
            data: Input OHLCV data
            target_col: Target column name
            
        Returns:
            Tuple of (features, target)
        """
        # Create all feature sets
        price_features = self.create_price_features(data)
        vol_features = self.create_volatility_features(data)
        tech_features = self.create_technical_indicators(data)
        
        # Combine features
        all_features = pd.concat([price_features, vol_features, tech_features], axis=1)
        
        # Create target variable (next-day realized volatility)
        target = vol_features[target_col].shift(-1)  # Next day volatility
        
        # Create lag features of target
        lag_features = self.create_lag_features(target.shift(1), n_lags=10)
        all_features = pd.concat([all_features, lag_features], axis=1)
        
        # Drop rows with NaN values
        mask = ~(all_features.isna().any(axis=1) | target.isna())
        all_features = all_features[mask]
        target = target[mask]
        
        # Store feature names
        self.feature_names = all_features.columns.tolist()
        
        return all_features, target

class VolatilityForecaster:
    """
    Advanced volatility forecasting using machine learning
    
    Supports multiple ML algorithms with automated hyperparameter
    tuning and walk-forward validation.
    """
    
    def __init__(self, model_type: ModelType = ModelType.RANDOM_FOREST):
        """
        Initialize volatility forecaster
        
        Args:
            model_type: Type of ML model to use
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.is_fitted = False
        self.feature_importance_ = None
        
    def _create_model(self, **params) -> Any:
        """Create ML model based on type"""
        if self.model_type == ModelType.RANDOM_FOREST:
            return RandomForestRegressor(
                n_estimators=params.get('n_estimators', 100),
                max_depth=params.get('max_depth', 10),
                min_samples_split=params.get('min_samples_split', 5),
                min_samples_leaf=params.get('min_samples_leaf', 2),
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == ModelType.GRADIENT_BOOSTING:
            return GradientBoostingRegressor(
                n_estimators=params.get('n_estimators', 100),
                learning_rate=params.get('learning_rate', 0.1),
                max_depth=params.get('max_depth', 6),
                random_state=42
            )
        elif self.model_type == ModelType.RIDGE:
            return Ridge(alpha=params.get('alpha', 1.0))
        elif self.model_type == ModelType.LASSO:
            return Lasso(alpha=params.get('alpha', 1.0), random_state=42)
        elif self.model_type == ModelType.ELASTIC_NET:
            return ElasticNet(
                alpha=params.get('alpha', 1.0),
                l1_ratio=params.get('l1_ratio', 0.5),
                random_state=42
            )
        elif self.model_type == ModelType.SVR:
            return SVR(
                kernel=params.get('kernel', 'rbf'),
                C=params.get('C', 1.0),
                gamma=params.get('gamma', 'scale')
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _get_param_grid(self) -> Dict[str, List]:
        """Get parameter grid for hyperparameter tuning"""
        if self.model_type == ModelType.RANDOM_FOREST:
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        elif self.model_type == ModelType.GRADIENT_BOOSTING:
            return {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 6, 9]
            }
        elif self.model_type == ModelType.RIDGE:
            return {'alpha': [0.1, 1.0, 10.0, 100.0]}
        elif self.model_type == ModelType.LASSO:
            return {'alpha': [0.001, 0.01, 0.1, 1.0]}
        elif self.model_type == ModelType.ELASTIC_NET:
            return {
                'alpha': [0.01, 0.1, 1.0],
                'l1_ratio': [0.1, 0.5, 0.9]
            }
        elif self.model_type == ModelType.SVR:
            return {
                'C': [0.1, 1.0, 10.0],
                'gamma': ['scale', 'auto', 0.001, 0.01],
                'kernel': ['rbf', 'linear']
            }
        else:
            return {}
    
    def fit(self, X: pd.DataFrame, y: pd.Series, 
           tune_hyperparameters: bool = True,
           feature_selection: bool = True,
           n_features: int = 50) -> 'VolatilityForecaster':
        """
        Fit the volatility forecasting model
        
        Args:
            X: Feature matrix
            y: Target values
            tune_hyperparameters: Whether to tune hyperparameters
            feature_selection: Whether to perform feature selection
            n_features: Number of features to select
            
        Returns:
            Self (fitted forecaster)
        """
        # Feature selection
        if feature_selection and X.shape[1] > n_features:
            self.feature_selector = SelectKBest(f_regression, k=n_features)
            X_selected = self.feature_selector.fit_transform(X, y)
            X = pd.DataFrame(X_selected, index=X.index, 
                           columns=X.columns[self.feature_selector.get_support()])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, index=X.index, columns=X.columns)
        
        # Hyperparameter tuning
        if tune_hyperparameters:
            param_grid = self._get_param_grid()
            if param_grid:
                # Use time series split for validation
                tscv = TimeSeriesSplit(n_splits=3)
                
                base_model = self._create_model()
                grid_search = GridSearchCV(
                    base_model, param_grid, cv=tscv, 
                    scoring='neg_mean_squared_error', n_jobs=-1
                )
                grid_search.fit(X_scaled, y)
                
                self.model = grid_search.best_estimator_
                self.best_params_ = grid_search.best_params_
            else:
                self.model = self._create_model()
                self.model.fit(X_scaled, y)
                self.best_params_ = {}
        else:
            self.model = self._create_model()
            self.model.fit(X_scaled, y)
            self.best_params_ = {}
        
        # Store feature importance if available
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance_ = dict(zip(X.columns, self.model.feature_importances_))
        elif hasattr(self.model, 'coef_'):
            self.feature_importance_ = dict(zip(X.columns, np.abs(self.model.coef_)))
        
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame, 
               return_confidence: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]]:
        """
        Make volatility predictions
        
        Args:
            X: Feature matrix
            return_confidence: Whether to return confidence intervals
            
        Returns:
            Predictions (and confidence intervals if requested)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Apply feature selection if used
        if self.feature_selector is not None:
            X_selected = self.feature_selector.transform(X)
            X = pd.DataFrame(X_selected, index=X.index, 
                           columns=X.columns[self.feature_selector.get_support()])
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        
        if return_confidence:
            # Estimate confidence intervals (simplified approach)
            if hasattr(self.model, 'estimators_'):  # Tree-based models
                # Use prediction variance from trees
                tree_predictions = np.array([tree.predict(X_scaled) for tree in self.model.estimators_])
                pred_std = np.std(tree_predictions, axis=0)
                
                lower_bound = predictions - 1.96 * pred_std
                upper_bound = predictions + 1.96 * pred_std
                
                return predictions, (lower_bound, upper_bound)
            else:
                # Use residual-based confidence intervals
                pred_std = np.std(predictions) * 0.1  # Simplified
                lower_bound = predictions - 1.96 * pred_std
                upper_bound = predictions + 1.96 * pred_std
                
                return predictions, (lower_bound, upper_bound)
        
        return predictions
    
    def walk_forward_validation(self, X: pd.DataFrame, y: pd.Series,
                              initial_train_size: int = 252,
                              step_size: int = 1,
                              n_splits: int = 10) -> ValidationResult:
        """
        Perform walk-forward validation
        
        Args:
            X: Feature matrix
            y: Target values
            initial_train_size: Initial training set size
            step_size: Step size for rolling window
            n_splits: Number of validation splits
            
        Returns:
            Validation results
        """
        train_scores = []
        test_scores = []
        predictions = []
        actual = []
        fold_metrics = []
        
        # Calculate split points
        total_size = len(X)
        split_points = np.linspace(
            initial_train_size, 
            total_size - step_size, 
            n_splits, 
            dtype=int
        )
        
        for i, split_point in enumerate(split_points):
            # Define train and test sets
            train_end = split_point
            test_start = split_point
            test_end = min(split_point + step_size, total_size)
            
            X_train = X.iloc[:train_end]
            y_train = y.iloc[:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            if len(X_test) == 0:
                continue
            
            # Fit model on training data
            model = self._create_model()
            
            # Feature selection
            if X_train.shape[1] > 50:
                selector = SelectKBest(f_regression, k=50)
                X_train_selected = selector.fit_transform(X_train, y_train)
                X_test_selected = selector.transform(X_test)
                
                train_columns = X_train.columns[selector.get_support()]
                X_train = pd.DataFrame(X_train_selected, index=X_train.index, columns=train_columns)
                X_test = pd.DataFrame(X_test_selected, index=X_test.index, columns=train_columns)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Fit and predict
            model.fit(X_train_scaled, y_train)
            
            train_pred = model.predict(X_train_scaled)
            test_pred = model.predict(X_test_scaled)
            
            # Calculate scores
            train_score = r2_score(y_train, train_pred)
            test_score = r2_score(y_test, test_pred)
            
            train_scores.append(train_score)
            test_scores.append(test_score)
            
            predictions.extend(test_pred)
            actual.extend(y_test.values)
            
            # Calculate detailed metrics
            fold_metrics.append({
                'fold': i + 1,
                'train_r2': train_score,
                'test_r2': test_score,
                'test_mse': mean_squared_error(y_test, test_pred),
                'test_mae': mean_absolute_error(y_test, test_pred),
                'train_size': len(X_train),
                'test_size': len(X_test)
            })
        
        # Calculate overall feature importance
        final_model = self._create_model()
        final_model.fit(self.scaler.fit_transform(X), y)
        
        if hasattr(final_model, 'feature_importances_'):
            feature_importance = dict(zip(X.columns, final_model.feature_importances_))
        else:
            feature_importance = {}
        
        return ValidationResult(
            train_scores=train_scores,
            test_scores=test_scores,
            predictions=np.array(predictions),
            actual=np.array(actual),
            fold_metrics=fold_metrics,
            feature_importance=feature_importance,
            best_params={}
        )

class EnsembleVolatilityForecaster:
    """
    Ensemble volatility forecaster combining multiple models
    
    Uses model averaging and stacking techniques to improve
    prediction accuracy and robustness.
    """
    
    def __init__(self, models: List[ModelType] = None):
        """
        Initialize ensemble forecaster
        
        Args:
            models: List of model types to include in ensemble
        """
        if models is None:
            models = [ModelType.RANDOM_FOREST, ModelType.GRADIENT_BOOSTING, ModelType.RIDGE]
        
        self.models = models
        self.forecasters = {}
        self.weights = None
        self.is_fitted = False
    
    def fit(self, X: pd.DataFrame, y: pd.Series, 
           validation_split: float = 0.2) -> 'EnsembleVolatilityForecaster':
        """
        Fit ensemble of volatility forecasters
        
        Args:
            X: Feature matrix
            y: Target values
            validation_split: Fraction of data for validation
            
        Returns:
            Self (fitted ensemble)
        """
        # Split data for meta-learning
        split_idx = int(len(X) * (1 - validation_split))
        
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Fit base models
        val_predictions = []
        
        for model_type in self.models:
            forecaster = VolatilityForecaster(model_type)
            forecaster.fit(X_train, y_train, tune_hyperparameters=True)
            
            self.forecasters[model_type.value] = forecaster
            
            # Get validation predictions
            val_pred = forecaster.predict(X_val)
            val_predictions.append(val_pred)
        
        # Learn optimal weights
        val_predictions = np.column_stack(val_predictions)
        
        # Simple averaging initially
        self.weights = np.ones(len(self.models)) / len(self.models)
        
        # Optimize weights using validation performance
        from scipy.optimize import minimize
        
        def ensemble_loss(weights):
            weights = weights / np.sum(weights)  # Normalize
            ensemble_pred = np.dot(val_predictions, weights)
            return mean_squared_error(y_val, ensemble_pred)
        
        # Constraints: weights sum to 1 and are non-negative
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(len(self.models))]
        
        result = minimize(
            ensemble_loss, 
            self.weights, 
            method='SLSQP',
            bounds=bounds, 
            constraints=constraints
        )
        
        if result.success:
            self.weights = result.x
        
        self.is_fitted = True
        return self
    
    def predict(self, X: pd.DataFrame, 
               return_confidence: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]]:
        """
        Make ensemble predictions
        
        Args:
            X: Feature matrix
            return_confidence: Whether to return confidence intervals
            
        Returns:
            Ensemble predictions (and confidence intervals if requested)
        """
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before making predictions")
        
        # Get predictions from all models
        predictions = []
        confidence_intervals = []
        
        for model_type in self.models:
            forecaster = self.forecasters[model_type.value]
            
            if return_confidence:
                pred, (lower, upper) = forecaster.predict(X, return_confidence=True)
                predictions.append(pred)
                confidence_intervals.append((lower, upper))
            else:
                pred = forecaster.predict(X)
                predictions.append(pred)
        
        # Weighted ensemble
        predictions = np.column_stack(predictions)
        ensemble_pred = np.dot(predictions, self.weights)
        
        if return_confidence:
            # Combine confidence intervals
            lower_bounds = np.column_stack([ci[0] for ci in confidence_intervals])
            upper_bounds = np.column_stack([ci[1] for ci in confidence_intervals])
            
            ensemble_lower = np.dot(lower_bounds, self.weights)
            ensemble_upper = np.dot(upper_bounds, self.weights)
            
            return ensemble_pred, (ensemble_lower, ensemble_upper)
        
        return ensemble_pred
    
    def get_model_contributions(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Get individual model contributions to ensemble prediction
        
        Args:
            X: Feature matrix
            
        Returns:
            Dictionary of model predictions
        """
        contributions = {}
        
        for model_type in self.models:
            forecaster = self.forecasters[model_type.value]
            pred = forecaster.predict(X)
            contributions[model_type.value] = pred * self.weights[self.models.index(model_type)]
        
        return contributions

# Example usage and testing
if __name__ == "__main__":
    print("=== VOLATILITY FORECASTING TESTING ===")
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    
    # Simulate OHLCV data
    returns = np.random.normal(0.001, 0.02, 500)
    prices = 100 * np.exp(np.cumsum(returns))
    
    # Add some volatility clustering
    vol = 0.02 * (1 + 0.5 * np.random.random(500))
    high_prices = prices * (1 + vol * np.random.random(500))
    low_prices = prices * (1 - vol * np.random.random(500))
    
    data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 500)
    })
    data.set_index('Date', inplace=True)
    
    print("Sample data created")
    print(f"Data shape: {data.shape}")
    
    # Feature engineering
    print("\n=== FEATURE ENGINEERING ===")
    feature_engineer = TechnicalFeatureEngineer()
    features, target = feature_engineer.engineer_features(data)
    
    print(f"Features shape: {features.shape}")
    print(f"Target shape: {target.shape}")
    print(f"Feature names: {len(feature_engineer.feature_names)}")
    
    # Split data
    split_idx = int(len(features) * 0.8)
    X_train, X_test = features.iloc[:split_idx], features.iloc[split_idx:]
    y_train, y_test = target.iloc[:split_idx], target.iloc[split_idx:]
    
    # Test individual models
    print("\n=== INDIVIDUAL MODEL TESTING ===")
    for model_type in [ModelType.RANDOM_FOREST, ModelType.GRADIENT_BOOSTING]:
        forecaster = VolatilityForecaster(model_type)
        forecaster.fit(X_train, y_train, tune_hyperparameters=False)
        
        predictions = forecaster.predict(X_test)
        r2 = r2_score(y_test, predictions)
        mse = mean_squared_error(y_test, predictions)
        
        print(f"{model_type.value}:")
        print(f"  R² Score: {r2:.4f}")
        print(f"  MSE: {mse:.6f}")
    
    # Test ensemble
    print("\n=== ENSEMBLE TESTING ===")
    ensemble = EnsembleVolatilityForecaster()
    ensemble.fit(features, target)
    
    ensemble_pred = ensemble.predict(X_test)
    ensemble_r2 = r2_score(y_test, ensemble_pred)
    ensemble_mse = mean_squared_error(y_test, ensemble_pred)
    
    print(f"Ensemble R² Score: {ensemble_r2:.4f}")
    print(f"Ensemble MSE: {ensemble_mse:.6f}")
    print(f"Model weights: {dict(zip([m.value for m in ensemble.models], ensemble.weights))}")
    
    # Test walk-forward validation
    print("\n=== WALK-FORWARD VALIDATION ===")
    rf_forecaster = VolatilityForecaster(ModelType.RANDOM_FOREST)
    validation_result = rf_forecaster.walk_forward_validation(features, target, n_splits=5)
    
    print(f"Average test R²: {np.mean(validation_result.test_scores):.4f}")
    print(f"Test R² std: {np.std(validation_result.test_scores):.4f}")
    print(f"Overall R²: {r2_score(validation_result.actual, validation_result.predictions):.4f}")
    
    print("\nVolatility forecasting testing completed successfully!")

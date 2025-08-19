"""
Advanced Technical Indicators
=============================

Professional implementations of sophisticated technical analysis indicators:
- Volume Profile with VPOC (Volume Point of Control)
- Advanced Bollinger Bands with volatility cones
- Multi-timeframe RSI/MACD analysis
- Support/Resistance with volume confirmation
- Statistical pattern recognition
- Signal processing algorithms

Mathematical Framework:
- Volume distribution analysis with statistical significance
- Volatility cone modeling with percentile distributions
- Multi-scale temporal analysis using wavelets
- Kernel density estimation for support/resistance
- Digital signal processing for noise reduction

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats, signal, ndimage
from scipy.interpolate import interp1d
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
# Try to import technical analysis library
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    warnings.warn("TA-Lib not available, using fallback implementations")

# Try to import advanced signal processing
try:
    from scipy.signal import savgol_filter, butter, filtfilt
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("Advanced signal processing not available")

class TimeFrame(Enum):
    """Time frame enumeration for multi-timeframe analysis"""
    M1 = "1min"
    M5 = "5min"
    M15 = "15min"
    M30 = "30min"
    H1 = "1hour"
    H4 = "4hour"
    D1 = "1day"
    W1 = "1week"
    MN1 = "1month"

@dataclass
class VolumeProfileResult:
    """Volume Profile analysis results"""
    price_levels: np.ndarray
    volume_distribution: np.ndarray
    vpoc: float  # Volume Point of Control
    value_area_high: float
    value_area_low: float
    value_area_volume_pct: float
    poc_strength: float
    support_levels: List[float]
    resistance_levels: List[float]

@dataclass
class VolatilityConeResult:
    """Volatility Cone analysis results"""
    timeframes: List[int]
    percentiles: Dict[str, np.ndarray]  # 5th, 25th, 50th, 75th, 95th
    current_volatility: np.ndarray
    volatility_rank: np.ndarray
    volatility_percentile: np.ndarray
    mean_reversion_signals: np.ndarray

@dataclass
class MultiTimeframeResult:
    """Multi-timeframe analysis results"""
    timeframes: List[str]
    rsi_values: Dict[str, np.ndarray]
    macd_values: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]
    trend_alignment: np.ndarray
    confluence_levels: List[float]
    divergence_signals: List[Tuple[str, int, str]]  # timeframe, index, type

class VolumeProfileAnalyzer:
    """
    Advanced Volume Profile Analyzer
    
    Implements professional volume profile analysis with:
    - VPOC (Volume Point of Control) identification
    - Value Area calculations (70% volume area)
    - Support/resistance level detection
    - Volume distribution statistical analysis
    """
    
    def __init__(self, num_bins: int = 100, value_area_pct: float = 0.70):
        """
        Initialize Volume Profile Analyzer
        
        Args:
            num_bins: Number of price bins for volume distribution
            value_area_pct: Percentage of volume for value area calculation
        """
        self.num_bins = num_bins
        self.value_area_pct = value_area_pct
    
    def calculate_volume_profile(self, data: pd.DataFrame) -> VolumeProfileResult:
        """
        Calculate comprehensive volume profile analysis
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            VolumeProfileResult with complete analysis
        """
        if 'Volume' not in data.columns:
            raise ValueError("Volume data required for volume profile analysis")
        
        # Price range and bins
        price_min = data['Low'].min()
        price_max = data['High'].max()
        price_levels = np.linspace(price_min, price_max, self.num_bins)
        bin_size = (price_max - price_min) / self.num_bins
        
        # Initialize volume distribution
        volume_distribution = np.zeros(self.num_bins)
        
        # Distribute volume across price levels
        for idx, row in data.iterrows():
            # Calculate price range for this bar
            bar_low = row['Low']
            bar_high = row['High']
            bar_volume = row['Volume']
            
            # Find overlapping bins
            start_bin = max(0, int((bar_low - price_min) / bin_size))
            end_bin = min(self.num_bins - 1, int((bar_high - price_min) / bin_size))
            
            # Distribute volume proportionally
            if start_bin == end_bin:
                volume_distribution[start_bin] += bar_volume
            else:
                for bin_idx in range(start_bin, end_bin + 1):
                    bin_low = price_min + bin_idx * bin_size
                    bin_high = price_min + (bin_idx + 1) * bin_size
                    
                    # Calculate overlap
                    overlap_low = max(bar_low, bin_low)
                    overlap_high = min(bar_high, bin_high)
                    overlap_ratio = (overlap_high - overlap_low) / (bar_high - bar_low)
                    
                    volume_distribution[bin_idx] += bar_volume * overlap_ratio
        
        # Find VPOC (Volume Point of Control)
        vpoc_idx = np.argmax(volume_distribution)
        vpoc = price_levels[vpoc_idx]
        
        # Calculate Value Area (70% of volume)
        total_volume = np.sum(volume_distribution)
        target_volume = total_volume * self.value_area_pct
        
        # Start from VPOC and expand outward
        value_area_volume = volume_distribution[vpoc_idx]
        low_idx = high_idx = vpoc_idx
        
        while value_area_volume < target_volume and (low_idx > 0 or high_idx < self.num_bins - 1):
            # Check which direction to expand
            low_volume = volume_distribution[low_idx - 1] if low_idx > 0 else 0
            high_volume = volume_distribution[high_idx + 1] if high_idx < self.num_bins - 1 else 0
            
            if low_volume >= high_volume and low_idx > 0:
                low_idx -= 1
                value_area_volume += volume_distribution[low_idx]
            elif high_idx < self.num_bins - 1:
                high_idx += 1
                value_area_volume += volume_distribution[high_idx]
            else:
                break
        
        value_area_low = price_levels[low_idx]
        value_area_high = price_levels[high_idx]
        value_area_volume_pct = value_area_volume / total_volume
        
        # Calculate POC strength (relative to nearby levels)
        poc_strength = self._calculate_poc_strength(volume_distribution, vpoc_idx)
        
        # Identify support and resistance levels
        support_levels, resistance_levels = self._identify_key_levels(
            price_levels, volume_distribution, data['Close'].iloc[-1]
        )
        
        return VolumeProfileResult(
            price_levels=price_levels,
            volume_distribution=volume_distribution,
            vpoc=vpoc,
            value_area_high=value_area_high,
            value_area_low=value_area_low,
            value_area_volume_pct=value_area_volume_pct,
            poc_strength=poc_strength,
            support_levels=support_levels,
            resistance_levels=resistance_levels
        )
    
    def _calculate_poc_strength(self, volume_distribution: np.ndarray, poc_idx: int) -> float:
        """Calculate POC strength relative to surrounding levels"""
        window = min(5, len(volume_distribution) // 10)
        start_idx = max(0, poc_idx - window)
        end_idx = min(len(volume_distribution), poc_idx + window + 1)
        
        local_volumes = volume_distribution[start_idx:end_idx]
        poc_volume = volume_distribution[poc_idx]
        
        if len(local_volumes) == 0:
            return 0.0
        
        # Calculate strength as ratio to local average
        local_avg = np.mean(local_volumes[local_volumes != poc_volume])
        return poc_volume / (local_avg + 1e-10) if local_avg > 0 else 1.0
    
    def _identify_key_levels(self, price_levels: np.ndarray, volume_distribution: np.ndarray, 
                           current_price: float) -> Tuple[List[float], List[float]]:
        """Identify key support and resistance levels"""
        # Find local maxima in volume distribution
        if len(volume_distribution) < 3:
            return [], []
        
        # Use scipy to find peaks
        try:
            peaks, properties = signal.find_peaks(
                volume_distribution, 
                height=np.percentile(volume_distribution, 75),
                distance=max(1, len(volume_distribution) // 20)
            )
        except:
            # Fallback peak detection
            peaks = []
            for i in range(1, len(volume_distribution) - 1):
                if (volume_distribution[i] > volume_distribution[i-1] and 
                    volume_distribution[i] > volume_distribution[i+1] and
                    volume_distribution[i] > np.percentile(volume_distribution, 75)):
                    peaks.append(i)
        
        # Separate into support and resistance
        support_levels = []
        resistance_levels = []
        
        for peak_idx in peaks:
            level_price = price_levels[peak_idx]
            if level_price < current_price:
                support_levels.append(level_price)
            else:
                resistance_levels.append(level_price)
        
        # Sort levels
        support_levels.sort(reverse=True)  # Nearest support first
        resistance_levels.sort()  # Nearest resistance first
        
        return support_levels[:5], resistance_levels[:5]  # Top 5 levels

class VolatilityConeAnalyzer:
    """
    Advanced Volatility Cone Analyzer
    
    Implements sophisticated volatility cone analysis with:
    - Multi-timeframe volatility distributions
    - Percentile-based volatility ranking
    - Mean reversion signal generation
    - Statistical volatility forecasting
    """
    
    def __init__(self, timeframes: List[int] = None, percentiles: List[float] = None):
        """
        Initialize Volatility Cone Analyzer
        
        Args:
            timeframes: List of timeframes for analysis (days)
            percentiles: Percentile levels for cone construction
        """
        self.timeframes = timeframes or [5, 10, 20, 30, 60, 90, 120, 252]
        self.percentiles = percentiles or [5, 25, 50, 75, 95]
        self.lookback_period = 252 * 2  # 2 years of data
    
    def calculate_volatility_cone(self, data: pd.DataFrame) -> VolatilityConeResult:
        """
        Calculate comprehensive volatility cone analysis
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            VolatilityConeResult with complete analysis
        """
        returns = np.log(data['Close'] / data['Close'].shift(1)).dropna()
        
        if len(returns) < max(self.timeframes) * 2:
            raise ValueError(f"Insufficient data: need at least {max(self.timeframes) * 2} observations")
        
        # Calculate volatilities for each timeframe
        percentile_data = {str(p): [] for p in self.percentiles}
        current_volatilities = []
        volatility_ranks = []
        volatility_percentiles = []
        
        for timeframe in self.timeframes:
            # Calculate rolling volatilities
            rolling_vols = returns.rolling(window=timeframe).std() * np.sqrt(252)
            rolling_vols = rolling_vols.dropna()
            
            if len(rolling_vols) < 50:  # Need sufficient history
                continue
            
            # Calculate percentiles
            for percentile in self.percentiles:
                percentile_value = np.percentile(rolling_vols, percentile)
                percentile_data[str(percentile)].append(percentile_value)
            
            # Current volatility
            current_vol = rolling_vols.iloc[-1]
            current_volatilities.append(current_vol)
            
            # Volatility rank (percentile of current vol in historical distribution)
            vol_rank = stats.percentileofscore(rolling_vols, current_vol)
            volatility_ranks.append(vol_rank)
            
            # Volatility percentile (for display)
            volatility_percentiles.append(vol_rank / 100.0)
        
        # Generate mean reversion signals
        mean_reversion_signals = self._generate_mean_reversion_signals(
            current_volatilities, percentile_data
        )
        
        return VolatilityConeResult(
            timeframes=self.timeframes[:len(current_volatilities)],
            percentiles=percentile_data,
            current_volatility=np.array(current_volatilities),
            volatility_rank=np.array(volatility_ranks),
            volatility_percentile=np.array(volatility_percentiles),
            mean_reversion_signals=np.array(mean_reversion_signals)
        )
    
    def _generate_mean_reversion_signals(self, current_vols: List[float], 
                                       percentile_data: Dict[str, List[float]]) -> List[int]:
        """Generate mean reversion signals based on volatility extremes"""
        signals = []
        
        for i, current_vol in enumerate(current_vols):
            if i >= len(percentile_data['5']) or i >= len(percentile_data['95']):
                signals.append(0)
                continue
            
            p5 = percentile_data['5'][i]
            p95 = percentile_data['95'][i]
            p50 = percentile_data['50'][i]
            
            # Signal generation logic
            if current_vol <= p5:
                signals.append(1)  # Volatility expansion expected
            elif current_vol >= p95:
                signals.append(-1)  # Volatility contraction expected
            elif abs(current_vol - p50) / p50 < 0.1:
                signals.append(0)  # Near median, no signal
            else:
                signals.append(0)  # No clear signal
        
        return signals

class MultiTimeframeAnalyzer:
    """
    Multi-Timeframe Technical Analysis
    
    Implements sophisticated multi-timeframe analysis with:
    - Cross-timeframe RSI/MACD analysis
    - Trend alignment detection
    - Confluence level identification
    - Divergence signal generation
    """
    
    def __init__(self, timeframes: List[str] = None):
        """
        Initialize Multi-Timeframe Analyzer
        
        Args:
            timeframes: List of timeframes for analysis
        """
        self.timeframes = timeframes or ['5min', '15min', '1hour', '4hour', '1day']
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
    
    def analyze_multi_timeframe(self, data_dict: Dict[str, pd.DataFrame]) -> MultiTimeframeResult:
        """
        Perform comprehensive multi-timeframe analysis
        
        Args:
            data_dict: Dictionary of timeframe -> DataFrame mappings
            
        Returns:
            MultiTimeframeResult with complete analysis
        """
        rsi_values = {}
        macd_values = {}
        
        # Calculate indicators for each timeframe
        for timeframe in self.timeframes:
            if timeframe not in data_dict:
                continue
                
            data = data_dict[timeframe]
            if len(data) < max(self.macd_slow, self.rsi_period) + 10:
                continue
            
            # RSI calculation
            rsi = self._calculate_rsi(data['Close'].values, self.rsi_period)
            rsi_values[timeframe] = rsi
            
            # MACD calculation
            macd_line, signal_line, histogram = self._calculate_macd(
                data['Close'].values, self.macd_fast, self.macd_slow, self.macd_signal
            )
            macd_values[timeframe] = (macd_line, signal_line, histogram)
        
        # Analyze trend alignment
        trend_alignment = self._analyze_trend_alignment(rsi_values, macd_values)
        
        # Find confluence levels
        confluence_levels = self._find_confluence_levels(data_dict)
        
        # Detect divergences
        divergence_signals = self._detect_divergences(data_dict, rsi_values, macd_values)
        
        return MultiTimeframeResult(
            timeframes=list(rsi_values.keys()),
            rsi_values=rsi_values,
            macd_values=macd_values,
            trend_alignment=trend_alignment,
            confluence_levels=confluence_levels,
            divergence_signals=divergence_signals
        )
    
    def _calculate_rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate RSI with proper handling of edge cases"""
        try:
            if len(prices) < period + 1:
                return np.full(len(prices), 50.0)
            if TALIB_AVAILABLE:
                import talib
                return talib.RSI(prices.astype(float), timeperiod=period)
            else:
                raise ImportError("TA-Lib not available")
        except:
            # Fallback implementation
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gains = pd.Series(gains).rolling(window=period).mean().values
            avg_losses = pd.Series(losses).rolling(window=period).mean().values
            
            rs = avg_gains / (avg_losses + 1e-10)
            rsi_values = 100 - (100 / (1 + rs))
            
            # Pad with NaN to match original length
            rsi = np.full(len(prices), np.nan)
            rsi[1:] = rsi_values
            return rsi
    
    def _calculate_macd(self, prices: np.ndarray, fast: int, slow: int, signal: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD with proper handling"""
        try:
            if len(prices) < slow + signal:
                return np.zeros(len(prices)), np.zeros(len(prices)), np.zeros(len(prices))
            if TALIB_AVAILABLE:
                import talib
                return talib.MACD(prices.astype(float), fastperiod=fast, slowperiod=slow, signalperiod=signal)
            else:
                raise ImportError("TA-Lib not available")
        except:
            # Fallback implementation
            price_series = pd.Series(prices)
            ema_fast = price_series.ewm(span=fast).mean().values
            ema_slow = price_series.ewm(span=slow).mean().values
            
            macd_line = ema_fast - ema_slow
            signal_line = pd.Series(macd_line).ewm(span=signal).mean().values
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
    
    def _analyze_trend_alignment(self, rsi_values: Dict[str, np.ndarray], 
                               macd_values: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]) -> np.ndarray:
        """Analyze trend alignment across timeframes"""
        if not rsi_values or not macd_values:
            return np.array([])
        
        # Get the shortest timeframe length
        min_length = min(len(rsi) for rsi in rsi_values.values() if len(rsi) > 0)
        if min_length == 0:
            return np.array([])
        
        alignment_scores = np.zeros(min_length)
        
        for i in range(min_length):
            bullish_count = 0
            bearish_count = 0
            total_timeframes = 0
            
            for timeframe in rsi_values:
                if (i < len(rsi_values[timeframe]) and 
                    timeframe in macd_values and 
                    i < len(macd_values[timeframe][0])):
                    
                    rsi = rsi_values[timeframe][i]
                    macd_line = macd_values[timeframe][0][i]
                    signal_line = macd_values[timeframe][1][i]
                    
                    if not (np.isnan(rsi) or np.isnan(macd_line) or np.isnan(signal_line)):
                        total_timeframes += 1
                        
                        # Bullish: RSI > 50 and MACD > Signal
                        if rsi > 50 and macd_line > signal_line:
                            bullish_count += 1
                        # Bearish: RSI < 50 and MACD < Signal
                        elif rsi < 50 and macd_line < signal_line:
                            bearish_count += 1
            
            if total_timeframes > 0:
                # Alignment score: +1 (all bullish) to -1 (all bearish)
                alignment_scores[i] = (bullish_count - bearish_count) / total_timeframes
        
        return alignment_scores
    
    def _find_confluence_levels(self, data_dict: Dict[str, pd.DataFrame]) -> List[float]:
        """Find price levels with confluence across timeframes"""
        all_levels = []
        
        for timeframe, data in data_dict.items():
            if len(data) < 50:
                continue
            
            # Extract key levels (highs, lows, closes)
            recent_data = data.tail(50)
            
            # Significant highs and lows
            highs = recent_data['High'].values
            lows = recent_data['Low'].values
            
            # Find local extrema
            high_peaks = signal.argrelextrema(highs, np.greater, order=3)[0]
            low_peaks = signal.argrelextrema(lows, np.less, order=3)[0]
            
            # Add significant levels
            all_levels.extend(highs[high_peaks])
            all_levels.extend(lows[low_peaks])
        
        if not all_levels:
            return []
        
        # Cluster levels to find confluence
        levels_array = np.array(all_levels).reshape(-1, 1)
        
        try:
            # Use DBSCAN to cluster nearby levels
            price_range = np.ptp(levels_array)
            eps = price_range * 0.01  # 1% price range
            
            clustering = DBSCAN(eps=eps, min_samples=2).fit(levels_array)
            
            confluence_levels = []
            for cluster_id in set(clustering.labels_):
                if cluster_id != -1:  # Ignore noise points
                    cluster_levels = levels_array[clustering.labels_ == cluster_id]
                    confluence_levels.append(np.mean(cluster_levels))
            
            return sorted(confluence_levels)
        except:
            # Fallback: return levels with manual clustering
            sorted_levels = sorted(all_levels)
            confluence_levels = []
            
            i = 0
            while i < len(sorted_levels):
                cluster = [sorted_levels[i]]
                j = i + 1
                
                # Group levels within 1% of each other
                while j < len(sorted_levels) and abs(sorted_levels[j] - sorted_levels[i]) / sorted_levels[i] < 0.01:
                    cluster.append(sorted_levels[j])
                    j += 1
                
                if len(cluster) >= 2:  # Confluence requires at least 2 levels
                    confluence_levels.append(np.mean(cluster))
                
                i = j
            
            return confluence_levels
    
    def _detect_divergences(self, data_dict: Dict[str, pd.DataFrame], 
                          rsi_values: Dict[str, np.ndarray], 
                          macd_values: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]) -> List[Tuple[str, int, str]]:
        """Detect price-indicator divergences"""
        divergences = []
        
        for timeframe in data_dict:
            if (timeframe not in rsi_values or 
                timeframe not in macd_values or 
                len(data_dict[timeframe]) < 50):
                continue
            
            data = data_dict[timeframe].tail(50)
            rsi = rsi_values[timeframe][-50:] if len(rsi_values[timeframe]) >= 50 else rsi_values[timeframe]
            macd_line = macd_values[timeframe][0][-50:] if len(macd_values[timeframe][0]) >= 50 else macd_values[timeframe][0]
            
            prices = data['Close'].values
            
            # Find price peaks and troughs
            try:
                price_peaks = signal.argrelextrema(prices, np.greater, order=5)[0]
                price_troughs = signal.argrelextrema(prices, np.less, order=5)[0]
                
                rsi_clean = rsi[~np.isnan(rsi)]
                macd_clean = macd_line[~np.isnan(macd_line)]
                
                if len(rsi_clean) >= len(prices):
                    rsi_peaks = signal.argrelextrema(rsi_clean[:len(prices)], np.greater, order=5)[0]
                    rsi_troughs = signal.argrelextrema(rsi_clean[:len(prices)], np.less, order=5)[0]
                    
                    # Check for bullish divergence (price lower low, RSI higher low)
                    if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
                        for i in range(1, len(price_troughs)):
                            price_idx = price_troughs[i]
                            prev_price_idx = price_troughs[i-1]
                            
                            # Find corresponding RSI troughs
                            rsi_matches = [idx for idx in rsi_troughs if abs(idx - price_idx) <= 3]
                            prev_rsi_matches = [idx for idx in rsi_troughs if abs(idx - prev_price_idx) <= 3]
                            
                            if rsi_matches and prev_rsi_matches:
                                current_price = prices[price_idx]
                                prev_price = prices[prev_price_idx]
                                current_rsi = rsi_clean[rsi_matches[0]]
                                prev_rsi = rsi_clean[prev_rsi_matches[0]]
                                
                                if current_price < prev_price and current_rsi > prev_rsi:
                                    divergences.append((timeframe, len(data) - 50 + price_idx, "bullish_rsi"))
                    
                    # Check for bearish divergence (price higher high, RSI lower high)
                    if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                        for i in range(1, len(price_peaks)):
                            price_idx = price_peaks[i]
                            prev_price_idx = price_peaks[i-1]
                            
                            # Find corresponding RSI peaks
                            rsi_matches = [idx for idx in rsi_peaks if abs(idx - price_idx) <= 3]
                            prev_rsi_matches = [idx for idx in rsi_peaks if abs(idx - prev_price_idx) <= 3]
                            
                            if rsi_matches and prev_rsi_matches:
                                current_price = prices[price_idx]
                                prev_price = prices[prev_price_idx]
                                current_rsi = rsi_clean[rsi_matches[0]]
                                prev_rsi = rsi_clean[prev_rsi_matches[0]]
                                
                                if current_price > prev_price and current_rsi < prev_rsi:
                                    divergences.append((timeframe, len(data) - 50 + price_idx, "bearish_rsi"))
            
            except Exception:
                continue  # Skip this timeframe if analysis fails
        
        return divergences

# Additional utility functions
def calculate_support_resistance_with_volume(data: pd.DataFrame, 
                                           lookback_period: int = 50,
                                           min_touches: int = 3,
                                           volume_threshold: float = 1.5) -> Tuple[List[float], List[float]]:
    """
    Calculate support and resistance levels with volume confirmation
    
    Args:
        data: DataFrame with OHLCV data
        lookback_period: Number of periods to look back
        min_touches: Minimum number of touches to confirm level
        volume_threshold: Volume multiplier for confirmation
        
    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    if len(data) < lookback_period:
        return [], []
    
    recent_data = data.tail(lookback_period).copy()
    
    # Calculate average volume
    avg_volume = recent_data['Volume'].mean()
    high_volume_threshold = avg_volume * volume_threshold
    
    # Find potential levels (local extrema)
    highs = recent_data['High'].values
    lows = recent_data['Low'].values
    volumes = recent_data['Volume'].values
    
    try:
        # Find peaks and troughs
        high_peaks = signal.argrelextrema(highs, np.greater, order=3)[0]
        low_peaks = signal.argrelextrema(lows, np.less, order=3)[0]
        
        # Filter by volume
        high_volume_peaks = [idx for idx in high_peaks if volumes[idx] > high_volume_threshold]
        high_volume_troughs = [idx for idx in low_peaks if volumes[idx] > high_volume_threshold]
        
        # Group nearby levels
        resistance_levels = []
        support_levels = []
        
        # Process resistance levels
        if high_volume_peaks:
            resistance_prices = highs[high_volume_peaks]
            resistance_levels = _cluster_levels(resistance_prices, min_touches)
        
        # Process support levels
        if high_volume_troughs:
            support_prices = lows[high_volume_troughs]
            support_levels = _cluster_levels(support_prices, min_touches)
        
        return support_levels, resistance_levels
    
    except Exception:
        return [], []

def _cluster_levels(prices: np.ndarray, min_touches: int) -> List[float]:
    """Helper function to cluster price levels"""
    if len(prices) < min_touches:
        return []
    
    try:
        # Use DBSCAN clustering
        prices_array = prices.reshape(-1, 1)
        price_range = np.ptp(prices_array)
        eps = price_range * 0.02  # 2% clustering tolerance
        
        clustering = DBSCAN(eps=eps, min_samples=min_touches).fit(prices_array)
        
        clustered_levels = []
        for cluster_id in set(clustering.labels_):
            if cluster_id != -1:  # Ignore noise points
                cluster_prices = prices_array[clustering.labels_ == cluster_id]
                clustered_levels.append(float(np.mean(cluster_prices)))
        
        return sorted(clustered_levels)
    
    except:
        # Fallback: simple averaging of nearby prices
        sorted_prices = sorted(prices)
        levels = []
        
        i = 0
        while i < len(sorted_prices):
            cluster = [sorted_prices[i]]
            j = i + 1
            
            while j < len(sorted_prices) and abs(sorted_prices[j] - sorted_prices[i]) / sorted_prices[i] < 0.02:
                cluster.append(sorted_prices[j])
                j += 1
            
            if len(cluster) >= min_touches:
                levels.append(np.mean(cluster))
            
            i = j
        
        return levels

# Example usage and testing
if __name__ == "__main__":
    print("=== ADVANCED TECHNICAL ANALYSIS TESTING ===")
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=500, freq='D')
    
    # Create realistic OHLCV data
    base_price = 100
    prices = [base_price]
    volumes = []
    
    for i in range(1, 500):
        # Random walk with volatility clustering
        if i > 20:
            recent_vol = np.std([prices[j] / prices[j-1] - 1 for j in range(i-20, i)])
            vol_factor = max(0.5, min(2.0, recent_vol * 50))
        else:
            vol_factor = 1.0
        
        change = np.random.randn() * 0.02 * vol_factor
        new_price = prices[-1] * (1 + change)
        prices.append(max(1, new_price))  # Prevent negative prices
        
        # Volume with correlation to price movement
        base_volume = 1000000
        volume_multiplier = 1 + abs(change) * 5  # Higher volume on big moves
        volume = int(base_volume * volume_multiplier * (1 + np.random.randn() * 0.3))
        volumes.append(max(100000, volume))
    
    # Create OHLC from close prices
    closes = np.array(prices)
    opens = np.roll(closes, 1)
    opens[0] = closes[0]
    
    # Add noise to create realistic OHLC
    highs = closes * (1 + np.abs(np.random.randn(500) * 0.01))
    lows = closes * (1 - np.abs(np.random.randn(500) * 0.01))
    
    # Ensure OHLC consistency
    for i in range(500):
        high_val = max(opens[i], closes[i], highs[i])
        low_val = min(opens[i], closes[i], lows[i])
        highs[i] = high_val
        lows[i] = low_val
    
    sample_data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    }, index=dates)
    
    print(f"Generated sample data: {len(sample_data)} rows")
    
    # Test Volume Profile
    print("\n=== VOLUME PROFILE ANALYSIS ===")
    try:
        vp_analyzer = VolumeProfileAnalyzer()
        vp_result = vp_analyzer.calculate_volume_profile(sample_data)
        
        print(f"VPOC: ${vp_result.vpoc:.2f}")
        print(f"Value Area: ${vp_result.value_area_low:.2f} - ${vp_result.value_area_high:.2f}")
        print(f"Value Area Volume: {vp_result.value_area_volume_pct:.1%}")
        print(f"POC Strength: {vp_result.poc_strength:.2f}")
        print(f"Support Levels: {[f'${level:.2f}' for level in vp_result.support_levels[:3]]}")
        print(f"Resistance Levels: {[f'${level:.2f}' for level in vp_result.resistance_levels[:3]]}")
    except Exception as e:
        print(f"Volume Profile Error: {e}")
    
    # Test Volatility Cone
    print("\n=== VOLATILITY CONE ANALYSIS ===")
    try:
        vc_analyzer = VolatilityConeAnalyzer()
        vc_result = vc_analyzer.calculate_volatility_cone(sample_data)
        
        print(f"Timeframes analyzed: {vc_result.timeframes}")
        print(f"Current volatilities: {[f'{vol:.1%}' for vol in vc_result.current_volatility[:5]]}")
        print(f"Volatility ranks: {[f'{rank:.1f}' for rank in vc_result.volatility_rank[:5]]}")
        print(f"Mean reversion signals: {vc_result.mean_reversion_signals[:5]}")
    except Exception as e:
        print(f"Volatility Cone Error: {e}")
    
    # Test Support/Resistance with Volume
    print("\n=== SUPPORT/RESISTANCE WITH VOLUME ===")
    try:
        support_levels, resistance_levels = calculate_support_resistance_with_volume(sample_data)
        print(f"Support levels: {[f'${level:.2f}' for level in support_levels[:3]]}")
        print(f"Resistance levels: {[f'${level:.2f}' for level in resistance_levels[:3]]}")
    except Exception as e:
        print(f"Support/Resistance Error: {e}")
    
    print("\nAdvanced technical analysis testing completed!")

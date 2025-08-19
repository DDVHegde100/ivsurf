"""
Deep Learning Neural Networks for Volatility Forecasting
========================================================

Professional deep learning implementation for volatility surface prediction:
- LSTM networks for time series volatility forecasting
- GRU networks for sequence modeling
- CNN-LSTM hybrid models for pattern recognition
- Attention mechanisms for feature importance
- Multi-output models for volatility surface prediction
- Advanced regularization and optimization techniques

Mathematical Framework:
- Recurrent neural networks with memory cells
- Convolutional layers for pattern extraction
- Attention mechanisms for sequence modeling
- Multi-task learning for surface prediction
- Batch normalization and dropout regularization

Author: Volatility Surface Explorer
Date: August 2025
"""

import numpy as np
import pandas as pd
import warnings
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import time

# Try to import deep learning libraries with fallbacks
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (
        LSTM, GRU, Dense, Dropout, BatchNormalization, 
        Conv1D, MaxPooling1D, Flatten, Input, Concatenate,
        Attention, MultiHeadAttention, LayerNormalization
    )
    from tensorflow.keras.optimizers import Adam, RMSprop
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    from tensorflow.keras.regularizers import l1, l2, l1_l2
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    warnings.warn("TensorFlow not available. Using sklearn-based neural networks as fallback.")

# Fallback to sklearn if TensorFlow not available
try:
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class NetworkArchitecture(Enum):
    """Types of neural network architectures"""
    LSTM = "lstm"
    GRU = "gru"
    CNN_LSTM = "cnn_lstm"
    ATTENTION_LSTM = "attention_lstm"
    TRANSFORMER = "transformer"
    MLP = "mlp"

@dataclass
class LSTMConfig:
    """Configuration for LSTM models"""
    sequence_length: int = 60
    lstm_units: List[int] = None
    dropout_rate: float = 0.2
    recurrent_dropout: float = 0.2
    batch_size: int = 32
    epochs: int = 100
    learning_rate: float = 0.001
    patience: int = 10
    
    def __post_init__(self):
        if self.lstm_units is None:
            self.lstm_units = [50, 25]

@dataclass
class PredictionResult:
    """Results from neural network prediction"""
    predictions: np.ndarray
    actual: np.ndarray
    confidence_intervals: Optional[Tuple[np.ndarray, np.ndarray]]
    training_history: Optional[Dict[str, List[float]]]
    model_metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]]
    architecture: str

class SequencePreprocessor:
    """
    Preprocessor for creating sequences from time series data
    
    Handles data normalization, sequence creation, and
    train/validation/test splits for neural networks.
    """
    
    def __init__(self, sequence_length: int = 60, target_steps: int = 1):
        """
        Initialize sequence preprocessor
        
        Args:
            sequence_length: Length of input sequences
            target_steps: Number of steps to predict ahead
        """
        self.sequence_length = sequence_length
        self.target_steps = target_steps
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.is_fitted = False
    
    def create_sequences(self, data: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training
        
        Args:
            data: Input feature matrix
            target: Target values
            
        Returns:
            Tuple of (X_sequences, y_sequences)
        """
        X_sequences = []
        y_sequences = []
        
        for i in range(self.sequence_length, len(data) - self.target_steps + 1):
            # Input sequence
            X_seq = data[i - self.sequence_length:i]
            
            # Target sequence (can be single value or multiple steps)
            if self.target_steps == 1:
                y_seq = target[i]
            else:
                y_seq = target[i:i + self.target_steps]
            
            X_sequences.append(X_seq)
            y_sequences.append(y_seq)
        
        return np.array(X_sequences), np.array(y_sequences)
    
    def prepare_data(self, features: pd.DataFrame, target: pd.Series,
                    train_split: float = 0.7, val_split: float = 0.15) -> Dict[str, np.ndarray]:
        """
        Prepare data for neural network training
        
        Args:
            features: Feature matrix
            target: Target series
            train_split: Fraction of data for training
            val_split: Fraction of data for validation
            
        Returns:
            Dictionary with train/val/test splits
        """
        # Align features and target
        aligned_data = pd.concat([features, target], axis=1).dropna()
        features_clean = aligned_data.iloc[:, :-1].values
        target_clean = aligned_data.iloc[:, -1].values
        
        # Normalize data
        features_scaled = self.scaler_X.fit_transform(features_clean)
        target_scaled = self.scaler_y.fit_transform(target_clean.reshape(-1, 1)).flatten()
        
        # Create sequences
        X_sequences, y_sequences = self.create_sequences(features_scaled, target_scaled)
        
        # Split data
        n_total = len(X_sequences)
        n_train = int(n_total * train_split)
        n_val = int(n_total * val_split)
        
        X_train = X_sequences[:n_train]
        y_train = y_sequences[:n_train]
        
        X_val = X_sequences[n_train:n_train + n_val]
        y_val = y_sequences[n_train:n_train + n_val]
        
        X_test = X_sequences[n_train + n_val:]
        y_test = y_sequences[n_train + n_val:]
        
        self.is_fitted = True
        
        return {
            'X_train': X_train, 'y_train': y_train,
            'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test
        }
    
    def inverse_transform_predictions(self, predictions: np.ndarray) -> np.ndarray:
        """Inverse transform predictions to original scale"""
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before inverse transform")
        
        if predictions.ndim == 1:
            predictions = predictions.reshape(-1, 1)
        
        return self.scaler_y.inverse_transform(predictions).flatten()

class LSTMVolatilityForecaster:
    """
    LSTM-based volatility forecasting model
    
    Implements LSTM networks for time series volatility prediction
    with advanced regularization and optimization techniques.
    """
    
    def __init__(self, config: LSTMConfig = None, architecture: NetworkArchitecture = NetworkArchitecture.LSTM):
        """
        Initialize LSTM forecaster
        
        Args:
            config: LSTM configuration
            architecture: Network architecture type
        """
        self.config = config if config is not None else LSTMConfig()
        self.architecture = architecture
        self.model = None
        self.preprocessor = SequencePreprocessor(self.config.sequence_length)
        self.training_history = None
        self.is_fitted = False
        
        if not TF_AVAILABLE and architecture != NetworkArchitecture.MLP:
            warnings.warn("TensorFlow not available. Falling back to MLP architecture.")
            self.architecture = NetworkArchitecture.MLP
    
    def _build_lstm_model(self, input_shape: Tuple[int, int]) -> Model:
        """Build LSTM model"""
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(
            self.config.lstm_units[0],
            return_sequences=len(self.config.lstm_units) > 1,
            input_shape=input_shape,
            dropout=self.config.dropout_rate,
            recurrent_dropout=self.config.recurrent_dropout
        ))
        model.add(BatchNormalization())
        
        # Additional LSTM layers
        for i, units in enumerate(self.config.lstm_units[1:], 1):
            return_sequences = i < len(self.config.lstm_units) - 1
            model.add(LSTM(
                units,
                return_sequences=return_sequences,
                dropout=self.config.dropout_rate,
                recurrent_dropout=self.config.recurrent_dropout
            ))
            model.add(BatchNormalization())
        
        # Dense layers
        model.add(Dense(25, activation='relu'))
        model.add(Dropout(self.config.dropout_rate))
        model.add(Dense(1, activation='linear'))
        
        return model
    
    def _build_gru_model(self, input_shape: Tuple[int, int]) -> Model:
        """Build GRU model"""
        model = Sequential()
        
        # First GRU layer
        model.add(GRU(
            self.config.lstm_units[0],
            return_sequences=len(self.config.lstm_units) > 1,
            input_shape=input_shape,
            dropout=self.config.dropout_rate,
            recurrent_dropout=self.config.recurrent_dropout
        ))
        model.add(BatchNormalization())
        
        # Additional GRU layers
        for i, units in enumerate(self.config.lstm_units[1:], 1):
            return_sequences = i < len(self.config.lstm_units) - 1
            model.add(GRU(
                units,
                return_sequences=return_sequences,
                dropout=self.config.dropout_rate,
                recurrent_dropout=self.config.recurrent_dropout
            ))
            model.add(BatchNormalization())
        
        # Dense layers
        model.add(Dense(25, activation='relu'))
        model.add(Dropout(self.config.dropout_rate))
        model.add(Dense(1, activation='linear'))
        
        return model
    
    def _build_cnn_lstm_model(self, input_shape: Tuple[int, int]) -> Model:
        """Build CNN-LSTM hybrid model"""
        model = Sequential()
        
        # CNN layers for pattern extraction
        model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Conv1D(filters=32, kernel_size=3, activation='relu'))
        model.add(Dropout(self.config.dropout_rate))
        
        # LSTM layers
        model.add(LSTM(
            self.config.lstm_units[0],
            return_sequences=len(self.config.lstm_units) > 1,
            dropout=self.config.dropout_rate
        ))
        model.add(BatchNormalization())
        
        for units in self.config.lstm_units[1:]:
            model.add(LSTM(units, dropout=self.config.dropout_rate))
            model.add(BatchNormalization())
        
        # Dense layers
        model.add(Dense(25, activation='relu'))
        model.add(Dropout(self.config.dropout_rate))
        model.add(Dense(1, activation='linear'))
        
        return model
    
    def _build_attention_lstm_model(self, input_shape: Tuple[int, int]) -> Model:
        """Build LSTM model with attention mechanism"""
        # Input layer
        inputs = Input(shape=input_shape)
        
        # LSTM layers
        lstm_out = LSTM(self.config.lstm_units[0], return_sequences=True)(inputs)
        lstm_out = BatchNormalization()(lstm_out)
        
        # Attention mechanism
        attention = MultiHeadAttention(num_heads=4, key_dim=self.config.lstm_units[0] // 4)(lstm_out, lstm_out)
        attention = LayerNormalization()(attention + lstm_out)
        
        # Final LSTM
        lstm_final = LSTM(self.config.lstm_units[-1])(attention)
        lstm_final = BatchNormalization()(lstm_final)
        
        # Dense layers
        dense = Dense(25, activation='relu')(lstm_final)
        dense = Dropout(self.config.dropout_rate)(dense)
        outputs = Dense(1, activation='linear')(dense)
        
        return Model(inputs=inputs, outputs=outputs)
    
    def _build_mlp_model(self, input_shape: Tuple[int, int]) -> Any:
        """Build MLP model using sklearn (fallback)"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("Neither TensorFlow nor scikit-learn available")
        
        # Flatten input for MLP
        input_size = input_shape[0] * input_shape[1]
        
        return MLPRegressor(
            hidden_layer_sizes=(100, 50, 25),
            activation='relu',
            solver='adam',
            alpha=0.001,
            batch_size=self.config.batch_size,
            learning_rate_init=self.config.learning_rate,
            max_iter=self.config.epochs,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=self.config.patience,
            random_state=42
        )
    
    def _build_model(self, input_shape: Tuple[int, int]) -> Any:
        """Build model based on architecture"""
        if not TF_AVAILABLE:
            return self._build_mlp_model(input_shape)
        
        if self.architecture == NetworkArchitecture.LSTM:
            return self._build_lstm_model(input_shape)
        elif self.architecture == NetworkArchitecture.GRU:
            return self._build_gru_model(input_shape)
        elif self.architecture == NetworkArchitecture.CNN_LSTM:
            return self._build_cnn_lstm_model(input_shape)
        elif self.architecture == NetworkArchitecture.ATTENTION_LSTM:
            return self._build_attention_lstm_model(input_shape)
        elif self.architecture == NetworkArchitecture.MLP:
            return self._build_mlp_model(input_shape)
        else:
            raise ValueError(f"Unsupported architecture: {self.architecture}")
    
    def fit(self, features: pd.DataFrame, target: pd.Series) -> 'LSTMVolatilityForecaster':
        """
        Fit the LSTM model
        
        Args:
            features: Feature matrix
            target: Target series
            
        Returns:
            Self (fitted forecaster)
        """
        # Prepare data
        data_splits = self.preprocessor.prepare_data(features, target)
        
        X_train = data_splits['X_train']
        y_train = data_splits['y_train']
        X_val = data_splits['X_val']
        y_val = data_splits['y_val']
        
        input_shape = (X_train.shape[1], X_train.shape[2])
        
        # Build model
        self.model = self._build_model(input_shape)
        
        if TF_AVAILABLE and self.architecture != NetworkArchitecture.MLP:
            # Compile TensorFlow model
            self.model.compile(
                optimizer=Adam(learning_rate=self.config.learning_rate),
                loss='mse',
                metrics=['mae']
            )
            
            # Callbacks
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=self.config.patience,
                    restore_best_weights=True
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=self.config.patience // 2,
                    min_lr=1e-7
                )
            ]
            
            # Train model
            history = self.model.fit(
                X_train, y_train,
                batch_size=self.config.batch_size,
                epochs=self.config.epochs,
                validation_data=(X_val, y_val),
                callbacks=callbacks,
                verbose=0
            )
            
            self.training_history = history.history
        
        else:
            # Train sklearn MLP
            X_train_flat = X_train.reshape(X_train.shape[0], -1)
            X_val_flat = X_val.reshape(X_val.shape[0], -1) if len(X_val) > 0 else None
            
            if X_val_flat is not None:
                # Combine for sklearn early stopping
                X_combined = np.vstack([X_train_flat, X_val_flat])
                y_combined = np.hstack([y_train, y_val])
                self.model.fit(X_combined, y_combined)
            else:
                self.model.fit(X_train_flat, y_train)
            
            self.training_history = None
        
        self.is_fitted = True
        return self
    
    def predict(self, features: pd.DataFrame, 
               return_confidence: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]]:
        """
        Make predictions
        
        Args:
            features: Feature matrix
            return_confidence: Whether to return confidence intervals
            
        Returns:
            Predictions (and confidence intervals if requested)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Prepare prediction data
        features_scaled = self.preprocessor.scaler_X.transform(features.values)
        
        # Create sequences
        if len(features_scaled) < self.config.sequence_length:
            raise ValueError(f"Need at least {self.config.sequence_length} data points for prediction")
        
        # Use last sequence for prediction
        X_pred = features_scaled[-self.config.sequence_length:].reshape(1, self.config.sequence_length, -1)
        
        if TF_AVAILABLE and self.architecture != NetworkArchitecture.MLP:
            # TensorFlow prediction
            pred_scaled = self.model.predict(X_pred, verbose=0)[0, 0]
        else:
            # sklearn prediction
            X_pred_flat = X_pred.reshape(1, -1)
            pred_scaled = self.model.predict(X_pred_flat)[0]
        
        # Inverse transform
        predictions = self.preprocessor.inverse_transform_predictions(np.array([pred_scaled]))
        
        if return_confidence:
            # Simplified confidence intervals
            pred_std = np.abs(predictions[0] * 0.1)  # 10% of prediction as std
            lower_bound = predictions - 1.96 * pred_std
            upper_bound = predictions + 1.96 * pred_std
            
            return predictions, (lower_bound, upper_bound)
        
        return predictions
    
    def evaluate(self, features: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            features: Feature matrix
            target: Target series
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Prepare test data
        data_splits = self.preprocessor.prepare_data(features, target)
        X_test = data_splits['X_test']
        y_test = data_splits['y_test']
        
        if len(X_test) == 0:
            return {'mse': np.nan, 'mae': np.nan, 'r2': np.nan}
        
        if TF_AVAILABLE and self.architecture != NetworkArchitecture.MLP:
            # TensorFlow evaluation
            y_pred_scaled = self.model.predict(X_test, verbose=0).flatten()
        else:
            # sklearn evaluation
            X_test_flat = X_test.reshape(X_test.shape[0], -1)
            y_pred_scaled = self.model.predict(X_test_flat)
        
        # Inverse transform
        y_pred = self.preprocessor.inverse_transform_predictions(y_pred_scaled)
        y_true = self.preprocessor.inverse_transform_predictions(y_test)
        
        # Calculate metrics
        mse = mean_squared_error(y_true, y_pred)
        mae = np.mean(np.abs(y_true - y_pred))
        r2 = r2_score(y_true, y_pred)
        
        return {
            'mse': mse,
            'mae': mae,
            'r2': r2,
            'rmse': np.sqrt(mse)
        }

class VolatilitySurfacePredictor:
    """
    Multi-output neural network for predicting entire volatility surfaces
    
    Uses deep learning to predict volatility surfaces across multiple
    strikes and expiries simultaneously.
    """
    
    def __init__(self, strikes: List[float], expiries: List[float]):
        """
        Initialize surface predictor
        
        Args:
            strikes: List of strike prices
            expiries: List of expiry times
        """
        self.strikes = np.array(strikes)
        self.expiries = np.array(expiries)
        self.n_outputs = len(strikes) * len(expiries)
        self.model = None
        self.preprocessor = SequencePreprocessor(sequence_length=30)
        self.is_fitted = False
    
    def _build_surface_model(self, input_shape: Tuple[int, int]) -> Model:
        """Build multi-output model for surface prediction"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow required for surface prediction")
        
        # Input layer
        inputs = Input(shape=input_shape)
        
        # LSTM backbone
        lstm1 = LSTM(100, return_sequences=True)(inputs)
        lstm1 = BatchNormalization()(lstm1)
        lstm1 = Dropout(0.3)(lstm1)
        
        lstm2 = LSTM(50, return_sequences=True)(lstm1)
        lstm2 = BatchNormalization()(lstm2)
        lstm2 = Dropout(0.3)(lstm2)
        
        lstm3 = LSTM(25)(lstm2)
        lstm3 = BatchNormalization()(lstm3)
        lstm3 = Dropout(0.3)(lstm3)
        
        # Dense layers for surface prediction
        dense1 = Dense(100, activation='relu')(lstm3)
        dense1 = Dropout(0.3)(dense1)
        
        dense2 = Dense(50, activation='relu')(dense1)
        dense2 = Dropout(0.3)(dense2)
        
        # Output layer (volatility surface)
        outputs = Dense(self.n_outputs, activation='softplus')(dense2)  # Ensure positive volatilities
        
        return Model(inputs=inputs, outputs=outputs)
    
    def fit(self, features: pd.DataFrame, volatility_surfaces: np.ndarray) -> 'VolatilitySurfacePredictor':
        """
        Fit the surface prediction model
        
        Args:
            features: Feature matrix
            volatility_surfaces: 3D array of volatility surfaces (time, strikes, expiries)
            
        Returns:
            Self (fitted predictor)
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow required for surface prediction")
        
        # Reshape surfaces to 2D (time, surface_points)
        n_time = volatility_surfaces.shape[0]
        surfaces_2d = volatility_surfaces.reshape(n_time, -1)
        
        # Prepare sequences
        features_scaled = self.preprocessor.scaler_X.fit_transform(features.values)
        surfaces_scaled = self.preprocessor.scaler_y.fit_transform(surfaces_2d)
        
        X_sequences, y_sequences = self.preprocessor.create_sequences(features_scaled, surfaces_scaled)
        
        # Split data
        n_train = int(len(X_sequences) * 0.8)
        X_train, X_val = X_sequences[:n_train], X_sequences[n_train:]
        y_train, y_val = y_sequences[:n_train], y_sequences[n_train:]
        
        # Build and compile model
        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self._build_surface_model(input_shape)
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # Train model
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7, min_lr=1e-7)
        ]
        
        history = self.model.fit(
            X_train, y_train,
            batch_size=32,
            epochs=200,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=0
        )
        
        self.training_history = history.history
        self.is_fitted = True
        return self
    
    def predict_surface(self, features: pd.DataFrame) -> np.ndarray:
        """
        Predict volatility surface
        
        Args:
            features: Feature matrix
            
        Returns:
            Predicted volatility surface (strikes, expiries)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Prepare data
        features_scaled = self.preprocessor.scaler_X.transform(features.values)
        X_pred = features_scaled[-self.preprocessor.sequence_length:].reshape(1, self.preprocessor.sequence_length, -1)
        
        # Predict
        surface_pred_scaled = self.model.predict(X_pred, verbose=0)[0]
        surface_pred = self.preprocessor.scaler_y.inverse_transform(surface_pred_scaled.reshape(1, -1))[0]
        
        # Reshape to surface format
        surface = surface_pred.reshape(len(self.strikes), len(self.expiries))
        
        return surface

# Example usage and testing
if __name__ == "__main__":
    print("=== NEURAL NETWORKS TESTING ===")
    
    # Check TensorFlow availability
    print(f"TensorFlow available: {TF_AVAILABLE}")
    print(f"Scikit-learn available: {SKLEARN_AVAILABLE}")
    
    if not TF_AVAILABLE and not SKLEARN_AVAILABLE:
        print("No ML libraries available for testing")
        exit()
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=300, freq='D')
    
    # Create sample features (technical indicators)
    n_features = 10
    features = pd.DataFrame(
        np.random.randn(300, n_features),
        index=dates,
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    # Create sample target (realized volatility with some pattern)
    base_vol = 0.2
    vol_pattern = 0.05 * np.sin(np.arange(300) * 2 * np.pi / 252)  # Annual pattern
    noise = np.random.normal(0, 0.02, 300)
    target = pd.Series(base_vol + vol_pattern + noise, index=dates, name='volatility')
    
    print(f"Generated data: {features.shape[0]} samples, {features.shape[1]} features")
    
    # Test LSTM forecaster
    print("\n=== LSTM FORECASTER TESTING ===")
    
    config = LSTMConfig(sequence_length=30, epochs=50, patience=5)
    
    for arch in [NetworkArchitecture.LSTM, NetworkArchitecture.GRU, NetworkArchitecture.MLP]:
        if not TF_AVAILABLE and arch != NetworkArchitecture.MLP:
            continue
        
        print(f"\nTesting {arch.value} architecture:")
        
        try:
            forecaster = LSTMVolatilityForecaster(config, arch)
            forecaster.fit(features, target)
            
            # Evaluate
            metrics = forecaster.evaluate(features, target)
            print(f"  R² Score: {metrics['r2']:.4f}")
            print(f"  RMSE: {metrics['rmse']:.6f}")
            print(f"  MAE: {metrics['mae']:.6f}")
            
            # Test prediction
            pred = forecaster.predict(features.tail(50))
            print(f"  Next volatility prediction: {pred[0]:.4f}")
            
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    print("\nNeural networks testing completed!")

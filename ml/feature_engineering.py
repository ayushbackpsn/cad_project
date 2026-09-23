"""
Feature Engineering for Time-Series Workload Prediction
Creates lag features for Random Forest model
"""

import pandas as pd
import numpy as np


class FeatureEngineer:
    """Creates time-series lag features for workload prediction"""
    
    def __init__(self, n_lags=3):
        """
        Initialize feature engineer
        
        Args:
            n_lags: Number of time steps to look back (default: 3)
        """
        self.n_lags = n_lags
        self.feature_columns = None
        
    def create_lag_features(self, data):
        """
        Create lag features for time-series prediction
        
        For each feature, create:
        - feature(t-1)
        - feature(t-2)
        - feature(t-3)
        ...
        
        This allows the model to learn from historical patterns
        """
        df = data.copy()
        self.feature_columns = list(df.columns)
        
        lag_features = pd.DataFrame(index=df.index)
        
        # Create lag features for each column
        for col in df.columns:
            for lag in range(1, self.n_lags + 1):
                lag_col_name = f"{col}_lag_{lag}"
                lag_features[lag_col_name] = df[col].shift(lag)
        
        # Combine original data with lag features
        # We'll use lag features to predict current values
        result = pd.concat([lag_features, df], axis=1)
        
        # Drop rows with NaN (from lag creation)
        result = result.dropna()
        
        print(f"Created lag features: {len(result)} records (after dropping NaN)")
        print(f"Total features: {len(result.columns)}")
        
        return result
    
    def create_target_features(self, data, forecast_horizon=1):
        """
        Create target features for prediction
        
        Args:
            data: Original data
            forecast_horizon: How many steps ahead to predict (default: 1)
        
        Returns:
            Features (X) and targets (y)
        """
        df = data.copy()
        
        # Create lag features
        lag_data = self.create_lag_features(df)
        
        # Create targets (shifted values)
        targets = pd.DataFrame(index=lag_data.index)
        
        for col in self.feature_columns:
            target_col_name = f"{col}_target"
            # Target is the value at t+forecast_horizon
            targets[target_col_name] = df[col].shift(-forecast_horizon)
        
        # Combine
        result = pd.concat([lag_data, targets], axis=1)
        
        # Drop rows with NaN (from target creation)
        result = result.dropna()
        
        # Separate features and targets
        # Features are all columns except targets
        target_cols = [f"{col}_target" for col in self.feature_columns]
        feature_cols = [col for col in result.columns if col not in target_cols]
        
        X = result[feature_cols]
        y = result[target_cols]
        
        print(f"Features shape: {X.shape}")
        print(f"Targets shape: {y.shape}")
        
        return X, y, feature_cols, target_cols
    
    def get_feature_importance_names(self, feature_cols):
        """
        Get human-readable feature names for importance analysis
        """
        importance_names = {}
        
        for col in feature_cols:
            if '_lag_' in col:
                # Extract base feature name and lag number
                parts = col.split('_lag_')
                base_feature = parts[0]
                lag_num = parts[1]
                importance_names[col] = f"{base_feature} (t-{lag_num})"
            else:
                importance_names[col] = col
        
        return importance_names


def main():
    """Test feature engineering"""
    from data_loader import BitbrainsDataLoader
    from preprocessing import DataPreprocessor
    
    # Load and preprocess data
    loader = BitbrainsDataLoader()
    try:
        data = loader.load_data()
    except FileNotFoundError:
        print("Dataset not found. Creating synthetic data for testing.")
        # Create synthetic data for testing
        data = pd.DataFrame({
            'cpu_usage_percent': np.random.uniform(10, 90, 100),
            'memory_usage_percent': np.random.uniform(20, 80, 100),
            'disk_read_kb_s': np.random.uniform(0, 1000, 100),
            'disk_write_kb_s': np.random.uniform(0, 500, 100),
            'network_received_kb_s': np.random.uniform(0, 2000, 100),
            'network_transmitted_kb_s': np.random.uniform(0, 1500, 100)
        })
    
    preprocessor = DataPreprocessor()
    train, test, derived = preprocessor.get_preprocessing_pipeline(data)
    
    # Feature engineering
    engineer = FeatureEngineer(n_lags=3)
    X, y, feature_cols, target_cols = engineer.create_target_features(train)
    
    print("\n=== Feature Columns ===")
    print(feature_cols)
    
    print("\n=== Target Columns ===")
    print(target_cols)
    
    print("\n=== Sample Features ===")
    print(X.head())
    
    print("\n=== Sample Targets ===")
    print(y.head())


if __name__ == '__main__':
    main()

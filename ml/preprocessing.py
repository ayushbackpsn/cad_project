"""
Data Preprocessing for Bitbrains Dataset
Handles cleaning, normalization, and preparation for ML
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler


class DataPreprocessor:
    """Preprocesses cloud workload data for ML"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = None
        
    def clean_data(self, data):
        """
        Clean the dataset
        
        Steps:
        1. Remove duplicates
        2. Handle missing values
        3. Remove outliers
        4. Sort by timestamp
        """
        df = data.copy()
        
        # Remove duplicates
        initial_len = len(df)
        df = df.drop_duplicates()
        if len(df) < initial_len:
            print(f"Removed {initial_len - len(df)} duplicate records")
        
        # Handle missing values - forward fill then backward fill
        df = df.ffill().bfill()
        
        # If still missing, drop those rows
        # Replace inf and -inf with NaN
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.ffill().bfill()
        df = df.dropna()
        
        # Sort by timestamp if available
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"Cleaned dataset: {len(df)} records")
        return df
    
    def calculate_derived_features(self, data):
        """
        Calculate derived features
        
        - Memory usage percentage
        - CPU usage percentage (if not already present)
        - Total disk I/O
        - Total network I/O
        """
        df = data.copy()
        
        # Memory usage percentage
        if 'memory_capacity_kb' in df.columns and 'memory_usage_kb' in df.columns:
            capacity = df['memory_capacity_kb'].replace(0, np.nan)
            df['memory_usage_percent'] = (df['memory_usage_kb'] / capacity) * 100
            df['memory_usage_percent'] = df['memory_usage_percent'].fillna(0.0).clip(0, 100)
        
        if 'cpu_usage_percent' in df.columns:
            df['cpu_usage_percent'] = df['cpu_usage_percent'].fillna(0.0).clip(0, 100)
            
        # Total disk I/O
        if 'disk_read_kb_s' in df.columns and 'disk_write_kb_s' in df.columns:
            df['disk_total_kb_s'] = df['disk_read_kb_s'] + df['disk_write_kb_s']
        
        # Total network I/O
        if 'network_received_kb_s' in df.columns and 'network_transmitted_kb_s' in df.columns:
            df['network_total_kb_s'] = df['network_received_kb_s'] + df['network_transmitted_kb_s']
            
        # Clean any inf or nan introduced in derived features
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        
        return df
    
    def select_features(self, data):
        """
        Select relevant features for ML
        """
        df = data.copy()
        
        # Define key feature columns
        key_features = [
            'cpu_usage_percent',
            'memory_usage_percent',
            'disk_read_kb_s',
            'disk_write_kb_s',
            'network_received_kb_s',
            'network_transmitted_kb_s'
        ]
        
        # Check which features are available
        available_features = [f for f in key_features if f in df.columns]
        
        # Sanitize selected feature data
        result = df[available_features].copy()
        result = result.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        
        print(f"Selected {len(available_features)} features: {available_features}")
        self.feature_columns = available_features
        
        return result
    
    def normalize_features(self, data, fit=True):
        """
        Normalize features using StandardScaler
        
        Args:
            data: DataFrame with features
            fit: Whether to fit the scaler (True for training, False for testing)
        """
        if self.feature_columns is None:
            raise ValueError("Must call select_features() first")
        
        df = data.copy()
        
        if fit:
            normalized = self.scaler.fit_transform(df[self.feature_columns])
        else:
            normalized = self.scaler.transform(df[self.feature_columns])
        
        df_normalized = pd.DataFrame(
            normalized,
            columns=self.feature_columns,
            index=df.index
        )
        
        return df_normalized
    
    def split_chronological(self, data, train_ratio=0.8):
        """
        Split data chronologically (NOT random)
        
        Important: Do not shuffle time-series data
        """
        split_idx = int(len(data) * train_ratio)
        
        train_data = data.iloc[:split_idx]
        test_data = data.iloc[split_idx:]
        
        print(f"Train size: {len(train_data)}, Test size: {len(test_data)}")
        
        return train_data, test_data
    
    def get_preprocessing_pipeline(self, data):
        """
        Run full preprocessing pipeline
        """
        print("=== Running Preprocessing Pipeline ===")
        
        # Step 1: Clean data
        cleaned = self.clean_data(data)
        
        # Step 2: Calculate derived features
        derived = self.calculate_derived_features(cleaned)
        
        # Step 3: Select features
        features = self.select_features(derived)
        
        # Step 4: Split chronologically
        train, test = self.split_chronological(features)
        
        # Step 5: Normalize
        train_normalized = self.normalize_features(train, fit=True)
        test_normalized = self.normalize_features(test, fit=False)
        
        return train_normalized, test_normalized, derived


def main():
    """Test the preprocessor"""
    from data_loader import BitbrainsDataLoader
    
    # Load data
    loader = BitbrainsDataLoader()
    try:
        data = loader.load_data()
    except FileNotFoundError:
        print("Dataset not found. Skipping preprocessing test.")
        return
    
    # Preprocess
    preprocessor = DataPreprocessor()
    train, test, derived = preprocessor.get_preprocessing_pipeline(data)
    
    print("\n=== Preprocessed Train Data ===")
    print(train.head())
    
    print("\n=== Preprocessed Test Data ===")
    print(test.head())


if __name__ == '__main__':
    main()

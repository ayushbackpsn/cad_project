"""
Workload Prediction Module
Makes predictions using trained Random Forest model
"""

import pandas as pd
import numpy as np
from train_model import WorkloadPredictor


class WorkloadPrediction:
    """Handles workload prediction using trained model"""
    
    def __init__(self, model_path='results/model.pkl'):
        """Load trained model"""
        self.predictor = WorkloadPredictor()
        self.predictor.load_model(model_path)
        
    def predict_future_workload(self, current_workload):
        """
        Predict future workload based on current and historical data
        
        Args:
            current_workload: DataFrame or dict with workload metrics
        
        Returns:
            Dictionary with predicted CPU and memory utilization
        """
        if isinstance(current_workload, dict):
            current_workload = pd.DataFrame([current_workload])
            
        required_cols = [
            'cpu_usage_percent',
            'memory_usage_percent',
            'disk_read_kb_s',
            'disk_write_kb_s',
            'network_received_kb_s',
            'network_transmitted_kb_s'
        ]
        
        # Ensure all base features exist
        for col in required_cols:
            if col not in current_workload.columns:
                current_workload[col] = 0.0
                
        # Build feature DataFrame matching self.predictor.feature_cols
        X_dict = {}
        for feat in self.predictor.feature_cols:
            if '_lag_' in feat:
                base_col, lag_num = feat.split('_lag_')
                lag_num = int(lag_num)
                if len(current_workload) > lag_num:
                    X_dict[feat] = [current_workload[base_col].iloc[-1 - lag_num]]
                else:
                    X_dict[feat] = [current_workload[base_col].iloc[-1]]
            else:
                X_dict[feat] = [current_workload[feat].iloc[-1] if feat in current_workload.columns else 0.0]
                
        X = pd.DataFrame(X_dict)
        
        # Predict
        predictions = self.predictor.predict(X)
        
        # Extract CPU and memory predictions
        cpu_target = [col for col in predictions.columns if 'cpu' in col.lower()][0]
        memory_target = [col for col in predictions.columns if 'memory' in col.lower()][0]
        
        result = {
            'predicted_cpu_percent': float(np.clip(predictions[cpu_target].iloc[0], 0, 100)),
            'predicted_memory_percent': float(np.clip(predictions[memory_target].iloc[0], 0, 100)),
            'all_predictions': {col: float(predictions[col].iloc[0]) for col in predictions.columns},
            'prediction_timestamp': str(pd.Timestamp.now())
        }
        
        return result
    
    def predict_batch(self, workload_history):
        """
        Predict workload for a batch of historical data
        """
        from feature_engineering import FeatureEngineer
        
        engineer = FeatureEngineer(n_lags=3)
        X, y, feature_cols, target_cols = engineer.create_target_features(workload_history)
        
        # Align features to trained model
        missing_cols = [c for c in self.predictor.feature_cols if c not in X.columns]
        for c in missing_cols:
            X[c] = 0.0
        X = X[self.predictor.feature_cols]
        
        predictions = self.predictor.predict(X)
        return predictions


def main():
    """Test prediction functionality"""
    from data_loader import BitbrainsDataLoader
    from preprocessing import DataPreprocessor
    
    # Initialize
    predictor = WorkloadPrediction()
    
    # Load and preprocess some test data
    loader = BitbrainsDataLoader()
    try:
        data = loader.load_data()
        preprocessor = DataPreprocessor()
        train, test, derived = preprocessor.get_preprocessing_pipeline(data)
        
        # Get the last row as "current" workload
        current_workload = derived.iloc[[-1]]
        
        print("=== Current Workload ===")
        print(current_workload[['cpu_usage_percent', 'memory_usage_percent']].head())
        
        # Predict future
        prediction = predictor.predict_future_workload(current_workload)
        
        print("\n=== Predicted Future Workload ===")
        print(f"Predicted CPU: {prediction['predicted_cpu_percent']:.2f}%")
        print(f"Predicted Memory: {prediction['predicted_memory_percent']:.2f}%")
        
    except FileNotFoundError:
        print("Dataset not found. Skipping prediction test.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

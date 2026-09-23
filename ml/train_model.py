"""
Random Forest Model Training for Workload Prediction
Trains ML model to predict future CPU and memory utilization
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import os
from pathlib import Path

from data_loader import BitbrainsDataLoader
from preprocessing import DataPreprocessor
from feature_engineering import FeatureEngineer


class WorkloadPredictor:
    """Random Forest-based workload predictor"""
    
    def __init__(self, n_estimators=100, max_depth=10, random_state=42):
        """
        Initialize the predictor
        
        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees
            random_state: Random seed for reproducibility
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = None
        self.feature_cols = None
        self.target_cols = None
        
    def train(self, X_train, y_train):
        """
        Train the Random Forest model
        
        Args:
            X_train: Training features
            y_train: Training targets
        """
        print("=== Training Random Forest Model ===")
        print(f"Training data shape: {X_train.shape}")
        print(f"Target shape: {y_train.shape}")
        
        # Initialize model
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1  # Use all available cores
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Store feature and target column names
        self.feature_cols = X_train.columns.tolist()
        self.target_cols = y_train.columns.tolist()
        
        print("Model training completed")
        
        # Print feature importance
        self.print_feature_importance()
        
    def print_feature_importance(self):
        """Print feature importance"""
        if self.model is None:
            print("Model not trained yet")
            return
        
        print("\n=== Feature Importance ===")
        importances = self.model.feature_importances_
        if importances.ndim > 1:
            importances = importances.mean(axis=0)
            
        indices = np.argsort(importances)[::-1]
        
        # Print top 10 features
        for j in range(min(10, len(indices))):
            idx = indices[j]
            print(f"  {self.feature_cols[idx]}: {importances[idx]:.4f}")
            
    def get_feature_importances_dict(self):
        """Get dictionary of feature importances"""
        if self.model is None:
            return {}
        importances = self.model.feature_importances_
        if importances.ndim > 1:
            importances = importances.mean(axis=0)
        return {col: float(imp) for col, imp in zip(self.feature_cols, importances)}
    
    def predict(self, X):
        """
        Make predictions
        
        Args:
            X: Features to predict on
        
        Returns:
            Predictions DataFrame
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = self.model.predict(X)
        
        # Convert to DataFrame
        pred_df = pd.DataFrame(predictions, columns=self.target_cols, index=X.index)
        
        return pred_df
    
    def save_model(self, path='results/model.pkl', extra_metadata=None):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save")
        
        # Create directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_cols': self.feature_cols,
            'target_cols': self.target_cols,
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'feature_importances': self.get_feature_importances_dict()
        }
        
        if extra_metadata:
            model_data.update(extra_metadata)
        
        joblib.dump(model_data, path)
        print(f"Model saved to {path}")
    
    def load_model(self, path='results/model.pkl'):
        """Load trained model from disk"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        
        model_data = joblib.load(path)
        
        self.model = model_data['model']
        self.feature_cols = model_data['feature_cols']
        self.target_cols = model_data['target_cols']
        self.n_estimators = model_data.get('n_estimators', 100)
        self.max_depth = model_data.get('max_depth', 10)
        self.metadata = model_data
        
        print(f"Model loaded from {path}")


def main():
    """Train and save the model"""
    # Initialize components
    loader = BitbrainsDataLoader()
    preprocessor = DataPreprocessor()
    engineer = FeatureEngineer(n_lags=3)
    predictor = WorkloadPredictor(n_estimators=100, max_depth=10)
    
    try:
        # Load data
        print("Loading dataset...")
        data = loader.load_data()
        
        # Preprocess
        print("\nPreprocessing data...")
        train, test, derived = preprocessor.get_preprocessing_pipeline(data)
        
        # Feature engineering
        print("\nCreating features...")
        X_train, y_train, feature_cols, target_cols = engineer.create_target_features(train)
        X_test, y_test, _, _ = engineer.create_target_features(test)
        
        # Train model
        print("\nTraining model...")
        predictor.train(X_train, y_train)
        
        # Evaluate performance on test set
        y_pred = predictor.predict(X_test)
        test_metrics = {}
        for col in y_test.columns:
            actual = y_test[col]
            pred = y_pred[col]
            mae = float(mean_absolute_error(actual, pred))
            rmse = float(np.sqrt(mean_squared_error(actual, pred)))
            r2 = float(r2_score(actual, pred))
            test_metrics[col] = {'MAE': mae, 'RMSE': rmse, 'R2': r2}
            print(f"Test Metric - {col}: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")
        
        # Save model with evaluation metrics
        predictor.save_model(extra_metadata={'metrics': test_metrics, 'num_train_samples': len(X_train)})
        
        print("\n=== Training Complete ===")
        print(f"Model saved to results/model.pkl")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease ensure the Bitbrains dataset is in data/fastStorage/")
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

"""
Model Evaluation for Workload Prediction
Evaluates Random Forest model using MAE, RMSE, R²
Implements naive persistence baseline for comparison
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pathlib import Path
import os

from train_model import WorkloadPredictor
from feature_engineering import FeatureEngineer


class ModelEvaluator:
    """Evaluates workload prediction model"""
    
    def __init__(self, model_path='results/model.pkl'):
        """Load trained model"""
        self.predictor = WorkloadPredictor()
        self.predictor.load_model(model_path)
        
    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test data
        
        Returns:
            Dictionary of metrics for each target
        """
        # Make predictions
        y_pred = self.predictor.predict(X_test)
        
        metrics = {}
        
        for target in y_test.columns:
            actual = y_test[target]
            predicted = y_pred[target]
            
            # Calculate metrics
            mae = mean_absolute_error(actual, predicted)
            rmse = np.sqrt(mean_squared_error(actual, predicted))
            r2 = r2_score(actual, predicted)
            
            metrics[target] = {
                'MAE': mae,
                'RMSE': rmse,
                'R2': r2
            }
        
        return metrics, y_pred
    
    def naive_persistence_baseline(self, y_test):
        """
        Implement naive persistence baseline
        
        Prediction: future value = current value
        
        This is a simple baseline that assumes the next value
        will be the same as the current value.
        """
        baseline_predictions = baseline_predictions.bfill().ffill()
        
        metrics = {}
        
        for target in y_test.columns:
            actual = y_test[target]
            predicted = baseline_predictions[target]
            
            mae = mean_absolute_error(actual, predicted)
            rmse = np.sqrt(mean_squared_error(actual, predicted))
            r2 = r2_score(actual, predicted)
            
            metrics[target] = {
                'MAE': mae,
                'RMSE': rmse,
                'R2': r2
            }
        
        return metrics, baseline_predictions
    
    def print_metrics(self, metrics, title="Model Metrics"):
        """Print evaluation metrics"""
        print(f"\n=== {title} ===")
        
        for target, metric_dict in metrics.items():
            print(f"\nTarget: {target}")
            print(f"  MAE:  {metric_dict['MAE']:.4f}")
            print(f"  RMSE: {metric_dict['RMSE']:.4f}")
            print(f"  R²:   {metric_dict['R2']:.4f}")
    
    def compare_with_baseline(self, model_metrics, baseline_metrics):
        """Compare model performance with baseline"""
        print("\n=== Model vs Baseline Comparison ===")
        
        for target in model_metrics.keys():
            print(f"\nTarget: {target}")
            
            model_mae = model_metrics[target]['MAE']
            baseline_mae = baseline_metrics[target]['MAE']
            improvement = ((baseline_mae - model_mae) / baseline_mae) * 100
            
            print(f"  Model MAE:     {model_mae:.4f}")
            print(f"  Baseline MAE:  {baseline_mae:.4f}")
            print(f"  Improvement:   {improvement:.2f}%")
    
    def plot_predictions(self, y_test, y_pred, target, save_path='results/predictions.png'):
        """
        Plot actual vs predicted values
        
        Args:
            y_test: Actual values
            y_pred: Predicted values
            target: Target column name
            save_path: Path to save plot
        """
        plt.figure(figsize=(12, 6))
        
        # Plot first 100 points for clarity
        n_points = min(100, len(y_test))
        
        plt.plot(y_test[target].iloc[:n_points].values, label='Actual', alpha=0.7)
        plt.plot(y_pred[target].iloc[:n_points].values, label='Predicted', alpha=0.7)
        
        plt.xlabel('Time Step')
        plt.ylabel('Value')
        plt.title(f'Actual vs Predicted: {target}')
        plt.legend()
        plt.grid(True)
        
        # Create directory if it doesn't exist
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
        plt.close()
    
    def save_metrics(self, metrics, path='results/metrics.txt'):
        """Save metrics to file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            for target, metric_dict in metrics.items():
                f.write(f"Target: {target}\n")
                f.write(f"  MAE:  {metric_dict['MAE']:.4f}\n")
                f.write(f"  RMSE: {metric_dict['RMSE']:.4f}\n")
                f.write(f"  R²:   {metric_dict['R2']:.4f}\n")
                f.write("\n")
        
        print(f"Metrics saved to {path}")


def main():
    """Run model evaluation"""
    from data_loader import BitbrainsDataLoader
    from preprocessing import DataPreprocessor
    
    # Initialize components
    loader = BitbrainsDataLoader()
    preprocessor = DataPreprocessor()
    engineer = FeatureEngineer(n_lags=3)
    evaluator = ModelEvaluator()
    
    try:
        # Load data
        print("Loading dataset...")
        data = loader.load_data()
        
        # Preprocess
        print("\nPreprocessing data...")
        train, test, derived = preprocessor.get_preprocessing_pipeline(data)
        
        # Feature engineering
        print("\nCreating features...")
        X_train, y_train, _, _ = engineer.create_target_features(train)
        X_test, y_test, _, _ = engineer.create_target_features(test)
        
        # Evaluate model
        print("\nEvaluating model...")
        model_metrics, y_pred = evaluator.evaluate(X_test, y_test)
        evaluator.print_metrics(model_metrics, "Random Forest Model")
        
        # Baseline
        print("\nEvaluating naive persistence baseline...")
        baseline_metrics, baseline_pred = evaluator.naive_persistence_baseline(y_test)
        evaluator.print_metrics(baseline_metrics, "Naive Persistence Baseline")
        
        # Compare
        evaluator.compare_with_baseline(model_metrics, baseline_metrics)
        
        # Save metrics
        evaluator.save_metrics(model_metrics, 'results/model_metrics.txt')
        evaluator.save_metrics(baseline_metrics, 'results/baseline_metrics.txt')
        
        # Plot predictions for CPU and memory
        cpu_target = [col for col in y_test.columns if 'cpu' in col.lower()][0]
        memory_target = [col for col in y_test.columns if 'memory' in col.lower()][0]
        
        evaluator.plot_predictions(y_test, y_pred, cpu_target, 'results/cpu_predictions.png')
        evaluator.plot_predictions(y_test, y_pred, memory_target, 'results/memory_predictions.png')
        
        print("\n=== Evaluation Complete ===")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease ensure:")
        print("1. The Bitbrains dataset is in data/bitbrains/")
        print("2. The trained model is at results/model.pkl")
        print("3. Run train_model.py first if model doesn't exist")
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

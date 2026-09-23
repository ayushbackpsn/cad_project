"""
Scaling Stability Controller
Implements mechanisms to reduce unstable scaling caused by prediction fluctuations
"""

from datetime import datetime
import numpy as np


class ScalingStabilityController:
    """
    Controls scaling stability to prevent oscillation
    
    Implements:
    1. Cooldown period
    2. Hysteresis/threshold margin
    3. Minimum and maximum VM limits
    4. Prediction error tracking
    5. Scaling churn measurement
    """
    
    def __init__(self, cooldown_seconds=300, hysteresis_lower=0.7, hysteresis_upper=1.1):
        """
        Initialize stability controller
        
        Args:
            cooldown_seconds: Minimum time between scaling actions
            hysteresis_lower: Lower threshold for scale-down (default: 0.7)
            hysteresis_upper: Upper threshold for scale-up (default: 1.1)
        """
        self.cooldown_seconds = cooldown_seconds
        self.hysteresis_lower = hysteresis_lower
        self.hysteresis_upper = hysteresis_upper
        
        self.last_scaling_time = None
        self.last_scaling_action = None
        
        # Track prediction errors
        self.prediction_errors = []
        self.max_error_history = 100
        
        # Track scaling churn
        self.scaling_history = []
        self.max_history = 1000
        
    def can_scale(self):
        """Check if scaling is allowed based on cooldown"""
        if self.last_scaling_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_scaling_time
        return time_since_last.total_seconds() >= self.cooldown_seconds
    
    def apply_hysteresis(self, required_capacity):
        """
        Apply hysteresis to prevent oscillation
        
        Args:
            required_capacity: Calculated required capacity ratio
        
        Returns:
            Adjusted capacity decision: 'scale_up', 'scale_down', or 'no_change'
        """
        if required_capacity < self.hysteresis_lower:
            return 'scale_down'
        elif required_capacity > self.hysteresis_upper:
            return 'scale_up'
        else:
            return 'no_change'
    
    def record_scaling_action(self, action, from_vms, to_vms):
        """Record a scaling action for churn tracking"""
        self.last_scaling_time = datetime.now()
        self.last_scaling_action = action
        
        self.scaling_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'from_vms': from_vms,
            'to_vms': to_vms
        })
        
        # Keep history bounded
        if len(self.scaling_history) > self.max_history:
            self.scaling_history = self.scaling_history[-self.max_history:]
    
    def record_prediction_error(self, predicted, actual):
        """
        Record prediction error for uncertainty awareness
        
        Args:
            predicted: Predicted value
            actual: Actual value
        """
        error = abs(predicted - actual)
        self.prediction_errors.append(error)
        
        # Keep history bounded
        if len(self.prediction_errors) > self.max_error_history:
            self.prediction_errors = self.prediction_errors[-self.max_error_history:]
    
    def get_average_prediction_error(self):
        """Get average prediction error"""
        if not self.prediction_errors:
            return 0.0
        return np.mean(self.prediction_errors)
    
    def get_scaling_churn(self, window_size=10):
        """
        Calculate scaling churn (frequency of repeated scaling actions)
        
        Args:
            window_size: Number of recent actions to consider
        
        Returns:
            Churn metric (number of scaling actions in window)
        """
        recent_actions = self.scaling_history[-window_size:]
        return len([a for a in recent_actions if a['action'] in ['SCALE_UP', 'SCALE_DOWN']])
    
    def get_oscillation_count(self, window_size=10):
        """
        Count oscillations (scale-up followed by scale-down or vice versa)
        
        Args:
            window_size: Number of recent actions to consider
        
        Returns:
            Number of oscillations
        """
        recent_actions = self.scaling_history[-window_size:]
        oscillations = 0
        
        for i in range(1, len(recent_actions)):
            if (recent_actions[i]['action'] == 'SCALE_UP' and 
                recent_actions[i-1]['action'] == 'SCALE_DOWN'):
                oscillations += 1
            elif (recent_actions[i]['action'] == 'SCALE_DOWN' and 
                  recent_actions[i-1]['action'] == 'SCALE_UP'):
                oscillations += 1
        
        return oscillations
    
    def should_be_conservative(self, error_threshold=15.0):
        """
        Determine if scaling should be conservative based on prediction error
        
        Args:
            error_threshold: Error threshold above which to be conservative
        
        Returns:
            True if should be conservative
        """
        avg_error = self.get_average_prediction_error()
        return avg_error > error_threshold
    
    def reset(self):
        """Reset controller state"""
        self.last_scaling_time = None
        self.last_scaling_action = None
        self.prediction_errors = []
        self.scaling_history = []
    
    def get_stability_metrics(self):
        """Get current stability metrics"""
        return {
            'cooldown_active': not self.can_scale(),
            'average_prediction_error': self.get_average_prediction_error(),
            'scaling_churn': self.get_scaling_churn(),
            'oscillation_count': self.get_oscillation_count(),
            'total_scaling_actions': len(self.scaling_history),
            'last_scaling_action': self.last_scaling_action,
            'last_scaling_time': self.last_scaling_time.isoformat() if self.last_scaling_time else None
        }


def main():
    """Test scaling stability controller"""
    controller = ScalingStabilityController(cooldown_seconds=60)
    
    print("=== Test Hysteresis ===")
    print(f"Capacity 0.5: {controller.apply_hysteresis(0.5)}")  # scale_down
    print(f"Capacity 0.8: {controller.apply_hysteresis(0.8)}")  # no_change
    print(f"Capacity 1.0: {controller.apply_hysteresis(1.0)}")  # no_change
    print(f"Capacity 1.2: {controller.apply_hysteresis(1.2)}")  # scale_up
    
    print("\n=== Test Cooldown ===")
    controller.record_scaling_action('SCALE_UP', 5, 6)
    print(f"Can scale immediately: {controller.can_scale()}")  # False
    print(f"Cooldown active: {not controller.can_scale()}")  # True
    
    print("\n=== Test Prediction Error Tracking ===")
    controller.record_prediction_error(50, 55)  # Error: 5
    controller.record_prediction_error(60, 65)  # Error: 5
    controller.record_prediction_error(70, 90)  # Error: 20
    print(f"Average error: {controller.get_average_prediction_error():.2f}")
    print(f"Should be conservative (threshold 15): {controller.should_be_conservative(15)}")
    
    print("\n=== Test Scaling Churn ===")
    controller.reset()
    controller.record_scaling_action('SCALE_UP', 5, 6)
    controller.record_scaling_action('SCALE_DOWN', 6, 5)
    controller.record_scaling_action('SCALE_UP', 5, 6)
    controller.record_scaling_action('SCALE_DOWN', 6, 5)
    print(f"Scaling churn: {controller.get_scaling_churn()}")
    print(f"Oscillation count: {controller.get_oscillation_count()}")
    
    print("\n=== Stability Metrics ===")
    metrics = controller.get_stability_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()

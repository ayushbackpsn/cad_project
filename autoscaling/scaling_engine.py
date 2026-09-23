"""
Auto-Scaling Engine
Decides when to scale up, scale down, or make no change
Implements cooldown period to prevent oscillation
"""

import time
from enum import Enum
from datetime import datetime, timedelta
from .scaling_stability import ScalingStabilityController


class ScalingAction(Enum):
    """Scaling action types"""
    SCALE_UP = "SCALE_UP"
    SCALE_DOWN = "SCALE_DOWN"
    NO_CHANGE = "NO_CHANGE"


class ScalingEngine:
    """
    Auto-scaling engine that determines scaling actions
    
    Input:
    - current VM count
    - predicted CPU demand
    - predicted memory demand
    - current utilization
    - configured minimum VM count
    - configured maximum VM count
    - thresholds
    - cooldown period
    
    Output:
    - required VM count
    - scaling action
    - number of VMs to add/remove
    """
    
    def __init__(self, min_vms=1, max_vms=100, cpu_threshold=70, 
                 memory_threshold=70, cooldown_seconds=300, hysteresis_lower=0.7, hysteresis_upper=1.1):
        """
        Initialize scaling engine
        
        Args:
            min_vms: Minimum number of VMs allowed
            max_vms: Maximum number of VMs allowed
            cpu_threshold: CPU utilization threshold for scaling (%)
            memory_threshold: Memory utilization threshold for scaling (%)
            cooldown_seconds: Cooldown period between scaling actions (default: 300s = 5min)
            hysteresis_lower: Lower hysteresis threshold (default: 0.7)
            hysteresis_upper: Upper hysteresis threshold (default: 1.1)
        """
        self.min_vms = min_vms
        self.max_vms = max_vms
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.cooldown_seconds = cooldown_seconds
        
        # Initialize stability controller
        self.stability_controller = ScalingStabilityController(
            cooldown_seconds=cooldown_seconds,
            hysteresis_lower=hysteresis_lower,
            hysteresis_upper=hysteresis_upper
        )
        
        # Track last scaling action (for backward compatibility)
        self.last_scaling_time = None
        self.last_scaling_action = None
        
    def decide_scaling_action(self, current_vms, predicted_cpu, predicted_memory,
                              current_cpu=None, current_memory=None,
                              disk_io=0, network_io=0):
        """
        Decide scaling action based on predicted workload
        
        Args:
            current_vms: Current number of VMs
            predicted_cpu: Predicted CPU utilization (%)
            predicted_memory: Predicted memory utilization (%)
            current_cpu: Current CPU utilization (%) - optional for reactive
            current_memory: Current memory utilization (%) - optional for reactive
            disk_io: Disk I/O (KB/s)
            network_io: Network I/O (KB/s)
        
        Returns:
            Dictionary with scaling decision
        """
        # Check cooldown using stability controller
        if not self.stability_controller.can_scale():
            return self._no_change_decision(current_vms, "Cooldown period active")
        
        # Calculate required VMs based on predicted workload
        from .resource_estimator import ResourceEstimator
        estimator = ResourceEstimator(self.cpu_threshold, self.memory_threshold)
        
        required_info = estimator.calculate_required_vms(
            current_vms=current_vms,
            cpu_util=predicted_cpu,
            memory_util=predicted_memory,
            disk_io=disk_io,
            network_io=network_io,
            min_vms=self.min_vms,
            max_vms=self.max_vms
        )
        
        required_capacity = required_info['cpu_ratio']  # Use the capacity ratio for hysteresis
        required_vms = required_info['required_vms']
        
        # Apply hysteresis using stability controller
        hysteresis_decision = self.stability_controller.apply_hysteresis(required_capacity)
        
        # Override required VMs based on hysteresis
        if hysteresis_decision == 'no_change':
            required_vms = current_vms
        elif hysteresis_decision == 'scale_down':
            # Recalculate with lower threshold
            required_vms = int(current_vms * required_capacity)
            required_vms = max(self.min_vms, required_vms)
        elif hysteresis_decision == 'scale_up':
            # Recalculate with upper threshold
            required_vms = int(current_vms * required_capacity)
            required_vms = min(self.max_vms, required_vms)
        
        # Determine scaling action
        if required_vms > current_vms:
            action = ScalingAction.SCALE_UP
            vms_to_change = required_vms - current_vms
        elif required_vms < current_vms:
            action = ScalingAction.SCALE_DOWN
            vms_to_change = current_vms - required_vms
        else:
            action = ScalingAction.NO_CHANGE
            vms_to_change = 0
        
        # Update stability controller if action is taken
        if action != ScalingAction.NO_CHANGE:
            self.stability_controller.record_scaling_action(action.value, current_vms, required_vms)
            # Update backward compatibility tracking
            self.last_scaling_time = datetime.now()
            self.last_scaling_action = action
        
        return {
            'action': action.value,
            'current_vms': current_vms,
            'required_vms': required_vms,
            'vms_to_add': vms_to_change if action == ScalingAction.SCALE_UP else 0,
            'vms_to_remove': vms_to_change if action == ScalingAction.SCALE_DOWN else 0,
            'constraint_type': required_info['constraint_type'],
            'predicted_cpu': predicted_cpu,
            'predicted_memory': predicted_memory,
            'reason': required_info['calculation'],
            'hysteresis_decision': hysteresis_decision,
            'timestamp': datetime.now().isoformat()
        }
    
    def decide_reactive_scaling(self, current_vms, current_cpu, current_memory,
                                disk_io=0, network_io=0):
        """
        Decide scaling action based on CURRENT workload (reactive)
        
        This is for the Reactive Scaling policy
        """
        # Check cooldown using stability controller
        if not self.stability_controller.can_scale():
            return self._no_change_decision(current_vms, "Cooldown period active")
        
        # Calculate required VMs based on current workload
        from .resource_estimator import ResourceEstimator
        estimator = ResourceEstimator(self.cpu_threshold, self.memory_threshold)
        
        required_info = estimator.calculate_required_vms(
            current_vms=current_vms,
            cpu_util=current_cpu,
            memory_util=current_memory,
            disk_io=disk_io,
            network_io=network_io,
            min_vms=self.min_vms,
            max_vms=self.max_vms
        )
        
        required_capacity = required_info['cpu_ratio']
        required_vms = required_info['required_vms']
        
        # Apply hysteresis using stability controller
        hysteresis_decision = self.stability_controller.apply_hysteresis(required_capacity)
        
        # Override required VMs based on hysteresis
        if hysteresis_decision == 'no_change':
            required_vms = current_vms
        elif hysteresis_decision == 'scale_down':
            required_vms = int(current_vms * required_capacity)
            required_vms = max(self.min_vms, required_vms)
        elif hysteresis_decision == 'scale_up':
            required_vms = int(current_vms * required_capacity)
            required_vms = min(self.max_vms, required_vms)
        
        # Determine scaling action
        if required_vms > current_vms:
            action = ScalingAction.SCALE_UP
            vms_to_change = required_vms - current_vms
        elif required_vms < current_vms:
            action = ScalingAction.SCALE_DOWN
            vms_to_change = current_vms - required_vms
        else:
            action = ScalingAction.NO_CHANGE
            vms_to_change = 0
        
        # Update stability controller if action is taken
        if action != ScalingAction.NO_CHANGE:
            self.stability_controller.record_scaling_action(action.value, current_vms, required_vms)
            # Update backward compatibility tracking
            self.last_scaling_time = datetime.now()
            self.last_scaling_action = action
        
        return {
            'action': action.value,
            'current_vms': current_vms,
            'required_vms': required_vms,
            'vms_to_add': vms_to_change if action == ScalingAction.SCALE_UP else 0,
            'vms_to_remove': vms_to_change if action == ScalingAction.SCALE_DOWN else 0,
            'constraint_type': required_info['constraint_type'],
            'current_cpu': current_cpu,
            'current_memory': current_memory,
            'reason': required_info['calculation'],
            'hysteresis_decision': hysteresis_decision,
            'timestamp': datetime.now().isoformat()
        }
    
    def decide_static_scaling(self, current_vms, target_vms):
        """
        Static scaling: maintain fixed number of VMs
        
        Args:
            current_vms: Current number of VMs
            target_vms: Target (fixed) number of VMs
        
        Returns:
            Dictionary with scaling decision
        """
        if current_vms < target_vms:
            action = ScalingAction.SCALE_UP
            vms_to_change = target_vms - current_vms
        elif current_vms > target_vms:
            action = ScalingAction.SCALE_DOWN
            vms_to_change = current_vms - target_vms
        else:
            action = ScalingAction.NO_CHANGE
            vms_to_change = 0
        
        return {
            'action': action.value,
            'current_vms': current_vms,
            'required_vms': target_vms,
            'vms_to_add': vms_to_change if action == ScalingAction.SCALE_UP else 0,
            'vms_to_remove': vms_to_change if action == ScalingAction.SCALE_DOWN else 0,
            'reason': f"Static scaling to maintain {target_vms} VMs",
            'timestamp': datetime.now().isoformat()
        }
    
    def _can_scale(self):
        """Check if scaling is allowed (cooldown period)"""
        if self.last_scaling_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_scaling_time
        return time_since_last.total_seconds() >= self.cooldown_seconds
    
    def _no_change_decision(self, current_vms, reason):
        """Return a no-change decision"""
        return {
            'action': ScalingAction.NO_CHANGE.value,
            'current_vms': current_vms,
            'required_vms': current_vms,
            'vms_to_add': 0,
            'vms_to_remove': 0,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_cooldown(self):
        """Reset cooldown (for testing)"""
        self.stability_controller.reset()
        self.last_scaling_time = None
        self.last_scaling_action = None
    
    def get_stability_metrics(self):
        """Get stability metrics from the stability controller"""
        return self.stability_controller.get_stability_metrics()


def main():
    """Test scaling engine"""
    engine = ScalingEngine(
        min_vms=1,
        max_vms=20,
        cpu_threshold=70,
        memory_threshold=70,
        cooldown_seconds=0  # Disable cooldown for testing
    )
    
    print("=== Test Case 1: Scale Up (Predictive) ===")
    result1 = engine.decide_scaling_action(
        current_vms=5,
        predicted_cpu=90,
        predicted_memory=85
    )
    print(f"Action: {result1['action']}")
    print(f"Current VMs: {result1['current_vms']}")
    print(f"Required VMs: {result1['required_vms']}")
    print(f"VMs to add: {result1['vms_to_add']}")
    print(f"Reason: {result1['reason']}\n")
    
    print("=== Test Case 2: Scale Down (Predictive) ===")
    result2 = engine.decide_scaling_action(
        current_vms=7,
        predicted_cpu=30,
        predicted_memory=35
    )
    print(f"Action: {result2['action']}")
    print(f"Current VMs: {result2['current_vms']}")
    print(f"Required VMs: {result2['required_vms']}")
    print(f"VMs to remove: {result2['vms_to_remove']}")
    print(f"Reason: {result2['reason']}\n")
    
    print("=== Test Case 3: No Change (Predictive) ===")
    result3 = engine.decide_scaling_action(
        current_vms=5,
        predicted_cpu=50,
        predicted_memory=55
    )
    print(f"Action: {result3['action']}")
    print(f"Current VMs: {result3['current_vms']}")
    print(f"Required VMs: {result3['required_vms']}")
    print(f"Reason: {result3['reason']}\n")
    
    print("=== Test Case 4: Reactive Scaling ===")
    result4 = engine.decide_reactive_scaling(
        current_vms=5,
        current_cpu=85,
        current_memory=60
    )
    print(f"Action: {result4['action']}")
    print(f"Current VMs: {result4['current_vms']}")
    print(f"Required VMs: {result4['required_vms']}")
    print(f"Reason: {result4['reason']}\n")
    
    print("=== Test Case 5: Static Scaling ===")
    result5 = engine.decide_static_scaling(
        current_vms=3,
        target_vms=5
    )
    print(f"Action: {result5['action']}")
    print(f"Current VMs: {result5['current_vms']}")
    print(f"Required VMs: {result5['required_vms']}")
    print(f"Reason: {result5['reason']}\n")
    
    print("=== Test Case 6: Cooldown ===")
    engine_with_cooldown = ScalingEngine(
        min_vms=1,
        max_vms=20,
        cpu_threshold=70,
        memory_threshold=70,
        cooldown_seconds=60
    )
    result6 = engine_with_cooldown.decide_scaling_action(
        current_vms=5,
        predicted_cpu=95,
        predicted_memory=90
    )
    print(f"Action: {result6['action']}")
    print(f"Reason: {result6['reason']}")


if __name__ == '__main__':
    main()

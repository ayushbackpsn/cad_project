"""
Scaling Policies
Implements Static, Reactive, and Predictive scaling policies
"""

from .scaling_engine import ScalingEngine, ScalingAction
from .resource_estimator import ResourceEstimator


class ScalingPolicy:
    """Base class for scaling policies"""
    
    def __init__(self, min_vms=1, max_vms=100, cpu_threshold=70, 
                 memory_threshold=70, cooldown_seconds=300, hysteresis_lower=0.7, hysteresis_upper=1.1):
        """
        Initialize policy
        
        Args:
            min_vms: Minimum VM count
            max_vms: Maximum VM count
            cpu_threshold: CPU threshold for scaling
            memory_threshold: Memory threshold for scaling
            cooldown_seconds: Cooldown period
            hysteresis_lower: Lower hysteresis threshold
            hysteresis_upper: Upper hysteresis threshold
        """
        self.min_vms = min_vms
        self.max_vms = max_vms
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.cooldown_seconds = cooldown_seconds
        
        self.engine = ScalingEngine(
            min_vms=min_vms,
            max_vms=max_vms,
            cpu_threshold=cpu_threshold,
            memory_threshold=memory_threshold,
            cooldown_seconds=cooldown_seconds,
            hysteresis_lower=hysteresis_lower,
            hysteresis_upper=hysteresis_upper
        )
        self.estimator = ResourceEstimator(cpu_threshold, memory_threshold)
        
    def get_scaling_decision(self, current_vms, workload_data):
        """
        Get scaling decision based on policy
        
        Args:
            current_vms: Current number of VMs
            workload_data: Dictionary with workload metrics
        
        Returns:
            Dictionary with scaling decision
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def reset(self):
        """Reset policy state (e.g., cooldown)"""
        self.engine.reset_cooldown()


class StaticScalingPolicy(ScalingPolicy):
    """
    Static Scaling Policy
    
    Maintains a fixed number of VMs regardless of workload.
    This is the baseline policy with no auto-scaling.
    """
    
    def __init__(self, fixed_vm_count, min_vms=1, max_vms=100):
        """
        Initialize static scaling policy
        
        Args:
            fixed_vm_count: Fixed number of VMs to maintain
            min_vms: Minimum VM count (for bounds)
            max_vms: Maximum VM count (for bounds)
        """
        super().__init__(min_vms=min_vms, max_vms=max_vms)
        self.fixed_vm_count = fixed_vm_count
        
    def get_scaling_decision(self, current_vms, workload_data):
        """
        Get scaling decision for static policy
        
        Always returns decision to maintain fixed_vm_count
        """
        return self.engine.decide_static_scaling(
            current_vms=current_vms,
            target_vms=self.fixed_vm_count
        )


class ReactiveScalingPolicy(ScalingPolicy):
    """
    Reactive Scaling Policy
    
    Makes scaling decisions based on CURRENT workload.
    Scales up when current utilization exceeds threshold.
    Scales down when current utilization is below threshold.
    """
    
    def __init__(self, min_vms=1, max_vms=100, cpu_threshold=70,
                 memory_threshold=70, cooldown_seconds=300, hysteresis_lower=0.7, hysteresis_upper=1.1):
        """
        Initialize reactive scaling policy
        
        Args:
            min_vms: Minimum VM count
            max_vms: Maximum VM count
            cpu_threshold: CPU threshold for scaling (%)
            memory_threshold: Memory threshold for scaling (%)
            cooldown_seconds: Cooldown period
            hysteresis_lower: Lower hysteresis threshold
            hysteresis_upper: Upper hysteresis threshold
        """
        super().__init__(min_vms, max_vms, cpu_threshold, memory_threshold, cooldown_seconds, hysteresis_lower, hysteresis_upper)
        
    def get_scaling_decision(self, current_vms, workload_data):
        """
        Get scaling decision for reactive policy
        
        Uses current (not predicted) workload metrics
        """
        current_cpu = workload_data.get('current_cpu', 0)
        current_memory = workload_data.get('current_memory', 0)
        disk_io = workload_data.get('disk_io', 0)
        network_io = workload_data.get('network_io', 0)
        
        return self.engine.decide_reactive_scaling(
            current_vms=current_vms,
            current_cpu=current_cpu,
            current_memory=current_memory,
            disk_io=disk_io,
            network_io=network_io
        )


class PredictiveScalingPolicy(ScalingPolicy):
    """
    Predictive Scaling Policy
    
    Makes scaling decisions based on PREDICTED future workload.
    Scales up before demand arrives.
    Scales down when demand is predicted to decrease.
    """
    
    def __init__(self, min_vms=1, max_vms=100, cpu_threshold=70,
                 memory_threshold=70, cooldown_seconds=300, hysteresis_lower=0.7, hysteresis_upper=1.1):
        """
        Initialize predictive scaling policy
        
        Args:
            min_vms: Minimum VM count
            max_vms: Maximum VM count
            cpu_threshold: CPU threshold for scaling (%)
            memory_threshold: Memory threshold for scaling (%)
            cooldown_seconds: Cooldown period
            hysteresis_lower: Lower hysteresis threshold
            hysteresis_upper: Upper hysteresis threshold
        """
        super().__init__(min_vms, max_vms, cpu_threshold, memory_threshold, cooldown_seconds, hysteresis_lower, hysteresis_upper)
        
    def get_scaling_decision(self, current_vms, workload_data):
        """
        Get scaling decision for predictive policy
        
        Uses predicted future workload metrics
        """
        predicted_cpu = workload_data.get('predicted_cpu', 0)
        predicted_memory = workload_data.get('predicted_memory', 0)
        current_cpu = workload_data.get('current_cpu', None)
        current_memory = workload_data.get('current_memory', None)
        disk_io = workload_data.get('disk_io', 0)
        network_io = workload_data.get('network_io', 0)
        
        return self.engine.decide_scaling_action(
            current_vms=current_vms,
            predicted_cpu=predicted_cpu,
            predicted_memory=predicted_memory,
            current_cpu=current_cpu,
            current_memory=current_memory,
            disk_io=disk_io,
            network_io=network_io
        )


class PolicyFactory:
    """Factory for creating scaling policies"""
    
    @staticmethod
    def create_policy(policy_type, **kwargs):
        """
        Create a scaling policy
        
        Args:
            policy_type: 'static', 'reactive', or 'predictive'
            **kwargs: Policy-specific parameters
        
        Returns:
            ScalingPolicy instance
        """
        policy_type = policy_type.lower()
        
        if policy_type == 'static':
            fixed_vm_count = kwargs.get('fixed_vm_count', 5)
            return StaticScalingPolicy(
                fixed_vm_count=fixed_vm_count,
                min_vms=kwargs.get('min_vms', 1),
                max_vms=kwargs.get('max_vms', 100)
            )
        elif policy_type == 'reactive':
            return ReactiveScalingPolicy(
                min_vms=kwargs.get('min_vms', 1),
                max_vms=kwargs.get('max_vms', 100),
                cpu_threshold=kwargs.get('cpu_threshold', 70),
                memory_threshold=kwargs.get('memory_threshold', 70),
                cooldown_seconds=kwargs.get('cooldown_seconds', 300),
                hysteresis_lower=kwargs.get('hysteresis_lower', 0.7),
                hysteresis_upper=kwargs.get('hysteresis_upper', 1.1)
            )
        elif policy_type == 'predictive':
            return PredictiveScalingPolicy(
                min_vms=kwargs.get('min_vms', 1),
                max_vms=kwargs.get('max_vms', 100),
                cpu_threshold=kwargs.get('cpu_threshold', 70),
                memory_threshold=kwargs.get('memory_threshold', 70),
                cooldown_seconds=kwargs.get('cooldown_seconds', 300),
                hysteresis_lower=kwargs.get('hysteresis_lower', 0.7),
                hysteresis_upper=kwargs.get('hysteresis_upper', 1.1)
            )
        else:
            raise ValueError(f"Unknown policy type: {policy_type}")


def main():
    """Test scaling policies"""
    print("=== Testing Static Scaling Policy ===")
    static_policy = PolicyFactory.create_policy('static', fixed_vm_count=5)
    
    decision1 = static_policy.get_scaling_decision(
        current_vms=3,
        workload_data={'current_cpu': 90, 'current_memory': 85}
    )
    print(f"Decision: {decision1['action']}, VMs: {decision1['current_vms']} -> {decision1['required_vms']}")
    
    print("\n=== Testing Reactive Scaling Policy ===")
    reactive_policy = PolicyFactory.create_policy(
        'reactive',
        min_vms=1,
        max_vms=20,
        cpu_threshold=70,
        memory_threshold=70,
        cooldown_seconds=60
    )
    
    decision2 = reactive_policy.get_scaling_decision(
        current_vms=5,
        workload_data={'current_cpu': 85, 'current_memory': 60}
    )
    print(f"Decision: {decision2['action']}, VMs: {decision2['current_vms']} -> {decision2['required_vms']}")
    
    print("\n=== Testing Predictive Scaling Policy ===")
    predictive_policy = PolicyFactory.create_policy(
        'predictive',
        min_vms=1,
        max_vms=20,
        cpu_threshold=70,
        memory_threshold=70,
        cooldown_seconds=60
    )
    
    decision3 = predictive_policy.get_scaling_decision(
        current_vms=5,
        workload_data={
            'predicted_cpu': 90,
            'predicted_memory': 85,
            'current_cpu': 70,
            'current_memory': 65
        }
    )
    print(f"Decision: {decision3['action']}, VMs: {decision3['current_vms']} -> {decision3['required_vms']}")
    print(f"Reason: {decision3['reason']}")


if __name__ == '__main__':
    main()

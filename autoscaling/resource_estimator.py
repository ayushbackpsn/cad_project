"""
Resource Estimator for Auto-Scaling
Determines resource constraints and calculates required VM capacity
"""


class ResourceEstimator:
    """
    Estimates resource demand and determines resource constraints
    
    Considers:
    - CPU utilization
    - Memory utilization
    - Disk I/O
    - Network I/O
    
    Determines whether the VM/application is:
    - CPU constrained
    - Memory constrained
    - I/O intensive
    - Normal
    """
    
    def __init__(self, cpu_threshold=70, memory_threshold=70):
        """
        Initialize resource estimator
        
        Args:
            cpu_threshold: CPU utilization threshold for "high" (default: 70%)
            memory_threshold: Memory utilization threshold for "high" (default: 70%)
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        
    def determine_resource_constraint(self, cpu_util, memory_util, disk_io=0, network_io=0):
        """
        Determine the primary resource constraint
        
        Args:
            cpu_util: CPU utilization percentage
            memory_util: Memory utilization percentage
            disk_io: Disk I/O (KB/s)
            network_io: Network I/O (KB/s)
        
        Returns:
            String indicating constraint type
        """
        # Normalize disk and network I/O to comparable scale
        # This is a simplified approach - in practice you'd use historical baselines
        
        if cpu_util > self.cpu_threshold and cpu_util >= memory_util:
            return 'CPU_CONSTRAINED'
        elif memory_util > self.memory_threshold and memory_util > cpu_util:
            return 'MEMORY_CONSTRAINED'
        elif disk_io > 1000 or network_io > 1000:  # Thresholds in KB/s
            return 'IO_INTENSIVE'
        else:
            return 'NORMAL'
    
    def calculate_required_capacity(self, cpu_util, memory_util, disk_io=0, network_io=0):
        """
        Calculate required VM capacity based on current utilization
        
        The calculation is:
        - If CPU is the bottleneck, scale based on CPU
        - If memory is the bottleneck, scale based on memory
        - If I/O is intensive, consider I/O in the calculation
        
        Formula:
        required_capacity = max(cpu_ratio, memory_ratio, io_ratio)
        
        where:
        cpu_ratio = current_cpu / target_cpu_threshold
        memory_ratio = current_memory / target_memory_threshold
        io_ratio = current_io / io_threshold (simplified)
        
        Args:
            cpu_util: Current CPU utilization (%)
            memory_util: Current memory utilization (%)
            disk_io: Disk I/O (KB/s)
            network_io: Network I/O (KB/s)
        
        Returns:
            Required capacity multiplier (e.g., 1.5 means need 1.5x current capacity)
        """
        # Calculate ratios
        cpu_ratio = cpu_util / self.cpu_threshold if self.cpu_threshold > 0 else 1
        memory_ratio = memory_util / self.memory_threshold if self.memory_threshold > 0 else 1
        
        # Simplified I/O ratio (using 1000 KB/s as baseline)
        total_io = disk_io + network_io
        io_ratio = total_io / 1000 if total_io > 0 else 0
        
        # Required capacity is the maximum of the ratios
        # Allow values below 1.0 for scale-down scenarios
        required_capacity = max(cpu_ratio, memory_ratio, io_ratio)
        
        # Determine constraint type
        constraint = self.determine_resource_constraint(cpu_util, memory_util, disk_io, network_io)
        
        return {
            'required_capacity': required_capacity,
            'constraint_type': constraint,
            'cpu_ratio': cpu_ratio,
            'memory_ratio': memory_ratio,
            'io_ratio': io_ratio
        }
    
    def calculate_required_vms(self, current_vms, cpu_util, memory_util, 
                               disk_io=0, network_io=0, min_vms=1, max_vms=100):
        """
        Calculate required number of VMs
        
        Args:
            current_vms: Current number of VMs
            cpu_util: Current CPU utilization (%)
            memory_util: Current memory utilization (%)
            disk_io: Disk I/O (KB/s)
            network_io: Network I/O (KB/s)
            min_vms: Minimum VM limit
            max_vms: Maximum VM limit
        
        Returns:
            Dictionary with required VMs and calculation details
        """
        # Calculate required capacity
        capacity_info = self.calculate_required_capacity(cpu_util, memory_util, disk_io, network_io)
        
        # Calculate required VMs
        # Add hysteresis to prevent oscillation:
        # - If capacity < 0.7: scale down
        # - If 0.7 <= capacity <= 1.1: no change (buffer zone)
        # - If capacity > 1.1: scale up
        required_capacity = capacity_info['required_capacity']
        
        if required_capacity < 0.7:
            required_vms = int(current_vms * required_capacity)  # Scale down
        elif required_capacity > 1.1:
            required_vms = int(current_vms * required_capacity)  # Scale up
        else:
            required_vms = current_vms  # No change (buffer zone)
        
        # Ensure within bounds
        required_vms = max(min_vms, min(required_vms, max_vms))
        
        return {
            'required_vms': required_vms,
            'current_vms': current_vms,
            'constraint_type': capacity_info['constraint_type'],
            'cpu_ratio': capacity_info['cpu_ratio'],
            'memory_ratio': capacity_info['memory_ratio'],
            'io_ratio': capacity_info['io_ratio'],
            'calculation': f"required_vms = current_vms * max(cpu_ratio, memory_ratio, io_ratio) = {current_vms} * {capacity_info['required_capacity']:.2f} = {required_vms}"
        }


def main():
    """Test resource estimator"""
    estimator = ResourceEstimator(cpu_threshold=70, memory_threshold=70)
    
    # Test case 1: CPU constrained
    result1 = estimator.calculate_required_vms(
        current_vms=5,
        cpu_util=90,
        memory_util=50,
        disk_io=500,
        network_io=500
    )
    print("=== Test Case 1: CPU Constrained ===")
    print(f"CPU: 90%, Memory: 50%")
    print(f"Required VMs: {result1['required_vms']}")
    print(f"Constraint: {result1['constraint_type']}")
    print(f"Calculation: {result1['calculation']}\n")
    
    # Test case 2: Memory constrained
    result2 = estimator.calculate_required_vms(
        current_vms=5,
        cpu_util=40,
        memory_util=85,
        disk_io=500,
        network_io=500
    )
    print("=== Test Case 2: Memory Constrained ===")
    print(f"CPU: 40%, Memory: 85%")
    print(f"Required VMs: {result2['required_vms']}")
    print(f"Constraint: {result2['constraint_type']}")
    print(f"Calculation: {result2['calculation']}\n")
    
    # Test case 3: Normal workload
    result3 = estimator.calculate_required_vms(
        current_vms=5,
        cpu_util=30,
        memory_util=35,
        disk_io=200,
        network_io=200
    )
    print("=== Test Case 3: Normal Workload ===")
    print(f"CPU: 30%, Memory: 35%")
    print(f"Required VMs: {result3['required_vms']}")
    print(f"Constraint: {result3['constraint_type']}")
    print(f"Calculation: {result3['calculation']}\n")
    
    # Test case 4: I/O intensive
    result4 = estimator.calculate_required_vms(
        current_vms=5,
        cpu_util=50,
        memory_util=50,
        disk_io=1500,
        network_io=1500
    )
    print("=== Test Case 4: I/O Intensive ===")
    print(f"CPU: 50%, Memory: 50%, Disk: 1500 KB/s, Network: 1500 KB/s")
    print(f"Required VMs: {result4['required_vms']}")
    print(f"Constraint: {result4['constraint_type']}")
    print(f"Calculation: {result4['calculation']}\n")


if __name__ == '__main__':
    main()

"""
CloudSim Plus Simulation Wrapper
Python interface for CloudSim Plus cloud simulation
"""

import subprocess
import json
import os
from pathlib import Path
import time
import sys
sys.path.append(str(Path(__file__).parent.parent / 'autoscaling'))
from metrics_calculator import MetricsCalculator


class CloudSimulation:
    """
    Python wrapper for CloudSim Plus simulation
    
    This provides a simplified interface to run cloud simulations
    and collect metrics for auto-scaling experiments.
    """
    
    def __init__(self):
        """Initialize simulation"""
        self.java_path = "java"
        self.cloudsim_jar = None
        self.results = {}
        self.metrics_calculator = MetricsCalculator()
        
    def compile_java_project(self):
        """Compile the Java CloudSim project using Maven"""
        cloudsim_dir = Path(__file__).parent
        
        print("Compiling CloudSim project with Maven...")
        result = subprocess.run(
            ["mvn", "clean", "package"],
            cwd=cloudsim_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            return False
        
        print("Compilation successful")
        return True
    
    def run_simulation(self, config):
        """
        Run cloud simulation with given configuration
        
        Args:
            config: Dictionary with simulation parameters
                - initial_vms: Initial number of VMs
                - vm_count_over_time: List of VM counts at each time step
                - cpu_utilization_over_time: List of CPU utilizations
                - memory_utilization_over_time: List of memory utilizations
                - duration: Simulation duration
                - vm_cost: Hourly VM cost
                - scaling_events: List of scaling events
                - required_vms_over_time: List of required VM counts
        
        Returns:
            Dictionary with simulation results
        """
        # For now, return simulated results without actual CloudSim
        # This allows the dashboard to work while Java integration is set up
        return self._simulate_with_python(config)
    
    def _simulate_with_python(self, config):
        """
        Simulate cloud behavior in Python (simplified version)
        
        This is a fallback when CloudSim Java is not compiled/available.
        It provides a reasonable approximation for demonstration.
        """
        initial_vms = config.get('initial_vms', 5)
        vm_count_over_time = config.get('vm_count_over_time', [5] * 100)
        cpu_utilization_over_time = config.get('cpu_utilization_over_time', [50] * 100)
        memory_utilization_over_time = config.get('memory_utilization_over_time', [50] * 100)
        duration = config.get('duration', 100)
        vm_cost = config.get('vm_cost', 0.1)
        scaling_events = config.get('scaling_events', [])
        required_vms_over_time = config.get('required_vms_over_time', vm_count_over_time)
        
        # Use MetricsCalculator for comprehensive metrics
        all_metrics = self.metrics_calculator.calculate_all_metrics(
            active_vms_over_time=vm_count_over_time,
            required_vms_over_time=required_vms_over_time,
            cpu_utilization_over_time=cpu_utilization_over_time[:duration],
            memory_utilization_over_time=memory_utilization_over_time[:duration],
            scaling_events=scaling_events,
            vm_hourly_cost=vm_cost,
            duration=duration
        )
        
        # Combine results
        results = {
            'total_energy': all_metrics['energy']['total_energy_kwh'],
            'total_cost': all_metrics['cost']['total_cost'],
            'sla_violations': all_metrics['sla']['total_sla_violations'],
            'cpu_violations': all_metrics['sla']['cpu_violations'],
            'memory_violations': all_metrics['sla']['memory_violations'],
            'sla_violation_rate': all_metrics['sla']['sla_violation_rate'],
            'avg_cpu_utilization': all_metrics['utilization']['avg_cpu_utilization'],
            'avg_memory_utilization': all_metrics['utilization']['avg_memory_utilization'],
            'max_cpu_utilization': all_metrics['utilization']['max_cpu_utilization'],
            'max_memory_utilization': all_metrics['utilization']['max_memory_utilization'],
            'avg_active_vms': all_metrics['vms']['avg_active_vms'],
            'max_active_vms': all_metrics['vms']['max_active_vms'],
            'min_active_vms': all_metrics['vms']['min_active_vms'],
            'scale_up_events': all_metrics['scaling']['scale_up_events'],
            'scale_down_events': all_metrics['scaling']['scale_down_events'],
            'total_scaling_events': all_metrics['scaling']['total_scaling_actions'],
            'scaling_oscillations': all_metrics['scaling']['oscillations'],
            'scaling_churn': all_metrics['scaling']['scaling_churn'],
            'over_provisioned_steps': all_metrics['provisioning']['over_provisioned_steps'],
            'under_provisioned_steps': all_metrics['provisioning']['under_provisioned_steps'],
            'over_provisioning_rate': all_metrics['provisioning']['over_provisioning_rate'],
            'under_provisioning_rate': all_metrics['provisioning']['under_provisioning_rate'],
            'active_vms_over_time': vm_count_over_time[:duration],
            'required_vms_over_time': required_vms_over_time[:duration],
            'energy_over_time': all_metrics['energy']['energy_over_time'],
            'cost_over_time': all_metrics['cost']['cost_over_time'],
            'cpu_utilization_over_time': cpu_utilization_over_time[:duration],
            'memory_utilization_over_time': memory_utilization_over_time[:duration],
            'duration': duration,
            'detailed_metrics': all_metrics
        }
        
        return results


def main():
    """Test the simulation"""
    sim = CloudSimulation()
    
    # Test configuration
    config = {
        'initial_vms': 5,
        'vm_count_over_time': [5, 6, 7, 8, 8, 7, 6, 5, 5, 5],
        'cpu_utilization_over_time': [50, 60, 70, 85, 90, 75, 60, 50, 45, 40],
        'memory_utilization_over_time': [50, 55, 65, 80, 85, 70, 55, 50, 45, 40],
        'duration': 10,
        'vm_cost': 0.1
    }
    
    results = sim.run_simulation(config)
    
    print("=== Simulation Results ===")
    print(f"Total Energy: {results['total_energy']:.2f} kWh")
    print(f"Total Cost: ${results['total_cost']:.2f}")
    print(f"SLA Violations: {results['sla_violations']}")
    print(f"Average CPU Utilization: {results['avg_cpu_utilization']:.2f}%")
    print(f"Average Memory Utilization: {results['avg_memory_utilization']:.2f}%")
    print(f"Average Active VMs: {results['avg_active_vms']:.2f}")


if __name__ == '__main__':
    main()

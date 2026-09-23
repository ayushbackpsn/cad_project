"""
Metrics Calculator for Auto-Scaling Evaluation
Calculates energy, cost, SLA/QoS, scaling overhead, and resource utilization metrics
"""

import numpy as np
import pandas as pd


class MetricsCalculator:
    """
    Calculates comprehensive metrics for auto-scaling evaluation
    
    Metrics:
    1. Energy consumption
    2. Simulated infrastructure cost
    3. SLA/QoS violations
    4. Scaling overhead
    5. Over-provisioning and under-provisioning
    """
    
    def __init__(self, base_power_per_vm=100, dynamic_power_factor=0.5, 
                 sla_threshold=90, time_step_hours=0.01):
        """
        Initialize metrics calculator
        
        Args:
            base_power_per_vm: Base power consumption per VM in Watts
            dynamic_power_factor: Dynamic power factor based on CPU utilization
            sla_threshold: SLA violation threshold (utilization %)
            time_step_hours: Duration of each time step in hours
        """
        self.base_power_per_vm = base_power_per_vm
        self.dynamic_power_factor = dynamic_power_factor
        self.sla_threshold = sla_threshold
        self.time_step_hours = time_step_hours
    
    def calculate_energy(self, active_vms_over_time, cpu_utilization_over_time):
        """
        Calculate total energy consumption
        
        Formula: Energy = (base_power * vms + dynamic_power * vms * cpu_util) * time_step
        
        Args:
            active_vms_over_time: List of active VM counts
            cpu_utilization_over_time: List of CPU utilizations (%)
        
        Returns:
            Dictionary with energy metrics
        """
        total_energy = 0
        energy_over_time = []
        
        for vms, cpu_util in zip(active_vms_over_time, cpu_utilization_over_time):
            # Energy in kWh
            energy = (self.base_power_per_vm * vms + 
                     self.dynamic_power_factor * vms * (cpu_util / 100)) * self.time_step_hours
            total_energy += energy
            energy_over_time.append(energy)
        
        return {
            'total_energy_kwh': total_energy,
            'energy_over_time': energy_over_time,
            'average_power_kw': total_energy / (len(active_vms_over_time) * self.time_step_hours)
        }
    
    def calculate_cost(self, active_vms_over_time, vm_hourly_cost):
        """
        Calculate simulated infrastructure cost
        
        Formula: Cost = active_vms * vm_hourly_cost * time_step
        
        Args:
            active_vms_over_time: List of active VM counts
            vm_hourly_cost: Cost per VM per hour ($)
        
        Returns:
            Dictionary with cost metrics
        """
        total_cost = 0
        cost_over_time = []
        
        for vms in active_vms_over_time:
            cost = vms * vm_hourly_cost * self.time_step_hours
            total_cost += cost
            cost_over_time.append(cost)
        
        return {
            'total_cost': total_cost,
            'cost_over_time': cost_over_time,
            'average_hourly_cost': total_cost / (len(active_vms_over_time) * self.time_step_hours)
        }
    
    def calculate_sla_violations(self, cpu_utilization_over_time, memory_utilization_over_time):
        """
        Calculate SLA/QoS violations
        
        SLA violation: utilization > sla_threshold (default 90%)
        
        Args:
            cpu_utilization_over_time: List of CPU utilizations (%)
            memory_utilization_over_time: List of memory utilizations (%)
        
        Returns:
            Dictionary with SLA metrics
        """
        total_violations = 0
        cpu_violations = 0
        memory_violations = 0
        violation_intervals = []
        
        for i, (cpu, memory) in enumerate(zip(cpu_utilization_over_time, memory_utilization_over_time)):
            cpu_violated = cpu > self.sla_threshold
            memory_violated = memory > self.sla_threshold
            
            if cpu_violated or memory_violated:
                total_violations += 1
                violation_intervals.append(i)
                if cpu_violated:
                    cpu_violations += 1
                if memory_violated:
                    memory_violations += 1
        
        return {
            'total_sla_violations': total_violations,
            'cpu_violations': cpu_violations,
            'memory_violations': memory_violations,
            'sla_violation_rate': total_violations / len(cpu_utilization_over_time) if cpu_utilization_over_time else 0,
            'violation_intervals': violation_intervals
        }
    
    def calculate_scaling_overhead(self, scaling_events, duration):
        """
        Calculate scaling overhead metrics
        
        Args:
            scaling_events: List of scaling events with 'action', 'from', 'to'
            duration: Total simulation duration
        
        Returns:
            Dictionary with scaling overhead metrics
        """
        scale_up_events = [e for e in scaling_events if e['action'] == 'SCALE_UP']
        scale_down_events = [e for e in scaling_events if e['action'] == 'SCALE_DOWN']
        
        total_scaling_actions = len(scaling_events)
        scale_up_count = len(scale_up_events)
        scale_down_count = len(scale_down_events)
        
        # Calculate scaling frequency (actions per time unit)
        scaling_frequency = total_scaling_actions / duration if duration > 0 else 0
        
        # Calculate unnecessary scaling (oscillations)
        oscillations = 0
        for i in range(1, len(scaling_events)):
            if (scaling_events[i]['action'] == 'SCALE_UP' and 
                scaling_events[i-1]['action'] == 'SCALE_DOWN'):
                oscillations += 1
            elif (scaling_events[i]['action'] == 'SCALE_DOWN' and 
                  scaling_events[i-1]['action'] == 'SCALE_UP'):
                oscillations += 1
        
        return {
            'total_scaling_actions': total_scaling_actions,
            'scale_up_events': scale_up_count,
            'scale_down_events': scale_down_count,
            'scaling_frequency': scaling_frequency,
            'oscillations': oscillations,
            'scaling_churn': oscillations
        }
    
    def calculate_over_under_provisioning(self, required_vms_over_time, active_vms_over_time):
        """
        Calculate over-provisioning and under-provisioning
        
        Args:
            required_vms_over_time: List of required VM counts
            active_vms_over_time: List of active VM counts
        
        Returns:
            Dictionary with provisioning metrics
        """
        over_provisioned = 0
        under_provisioned = 0
        perfectly_provisioned = 0
        over_provisioning_amount = []
        under_provisioning_amount = []
        
        for required, active in zip(required_vms_over_time, active_vms_over_time):
            if active > required:
                over_provisioned += 1
                over_provisioning_amount.append(active - required)
            elif active < required:
                under_provisioned += 1
                under_provisioning_amount.append(required - active)
            else:
                perfectly_provisioned += 1
        
        total_steps = len(required_vms_over_time)
        
        return {
            'over_provisioned_steps': over_provisioned,
            'under_provisioned_steps': under_provisioned,
            'perfectly_provisioned_steps': perfectly_provisioned,
            'over_provisioning_rate': over_provisioned / total_steps if total_steps > 0 else 0,
            'under_provisioning_rate': under_provisioned / total_steps if total_steps > 0 else 0,
            'average_over_provisioning': np.mean(over_provisioning_amount) if over_provisioning_amount else 0,
            'average_under_provisioning': np.mean(under_provisioning_amount) if under_provisioning_amount else 0
        }
    
    def calculate_utilization_metrics(self, cpu_utilization_over_time, memory_utilization_over_time):
        """
        Calculate resource utilization metrics
        
        Args:
            cpu_utilization_over_time: List of CPU utilizations (%)
            memory_utilization_over_time: List of memory utilizations (%)
        
        Returns:
            Dictionary with utilization metrics
        """
        return {
            'avg_cpu_utilization': np.mean(cpu_utilization_over_time) if cpu_utilization_over_time else 0,
            'max_cpu_utilization': np.max(cpu_utilization_over_time) if cpu_utilization_over_time else 0,
            'min_cpu_utilization': np.min(cpu_utilization_over_time) if cpu_utilization_over_time else 0,
            'std_cpu_utilization': np.std(cpu_utilization_over_time) if cpu_utilization_over_time else 0,
            'avg_memory_utilization': np.mean(memory_utilization_over_time) if memory_utilization_over_time else 0,
            'max_memory_utilization': np.max(memory_utilization_over_time) if memory_utilization_over_time else 0,
            'min_memory_utilization': np.min(memory_utilization_over_time) if memory_utilization_over_time else 0,
            'std_memory_utilization': np.std(memory_utilization_over_time) if memory_utilization_over_time else 0
        }
    
    def calculate_vm_metrics(self, active_vms_over_time):
        """
        Calculate VM-related metrics
        
        Args:
            active_vms_over_time: List of active VM counts
        
        Returns:
            Dictionary with VM metrics
        """
        return {
            'avg_active_vms': np.mean(active_vms_over_time) if active_vms_over_time else 0,
            'max_active_vms': np.max(active_vms_over_time) if active_vms_over_time else 0,
            'min_active_vms': np.min(active_vms_over_time) if active_vms_over_time else 0,
            'std_active_vms': np.std(active_vms_over_time) if active_vms_over_time else 0
        }
    
    def calculate_all_metrics(self, active_vms_over_time, required_vms_over_time,
                              cpu_utilization_over_time, memory_utilization_over_time,
                              scaling_events, vm_hourly_cost, duration):
        """
        Calculate all metrics in one call
        
        Args:
            active_vms_over_time: List of active VM counts
            required_vms_over_time: List of required VM counts
            cpu_utilization_over_time: List of CPU utilizations (%)
            memory_utilization_over_time: List of memory utilizations (%)
            scaling_events: List of scaling events
            vm_hourly_cost: Cost per VM per hour
            duration: Simulation duration
        
        Returns:
            Dictionary with all metrics
        """
        energy_metrics = self.calculate_energy(active_vms_over_time, cpu_utilization_over_time)
        cost_metrics = self.calculate_cost(active_vms_over_time, vm_hourly_cost)
        sla_metrics = self.calculate_sla_violations(cpu_utilization_over_time, memory_utilization_over_time)
        scaling_metrics = self.calculate_scaling_overhead(scaling_events, duration)
        provisioning_metrics = self.calculate_over_under_provisioning(required_vms_over_time, active_vms_over_time)
        utilization_metrics = self.calculate_utilization_metrics(cpu_utilization_over_time, memory_utilization_over_time)
        vm_metrics = self.calculate_vm_metrics(active_vms_over_time)
        
        return {
            'energy': energy_metrics,
            'cost': cost_metrics,
            'sla': sla_metrics,
            'scaling': scaling_metrics,
            'provisioning': provisioning_metrics,
            'utilization': utilization_metrics,
            'vms': vm_metrics
        }


def main():
    """Test metrics calculator"""
    calculator = MetricsCalculator()
    
    # Sample data
    active_vms = [5, 6, 7, 8, 7, 6, 5, 5]
    required_vms = [5, 6, 7, 8, 7, 6, 5, 5]
    cpu_util = [50, 60, 70, 95, 75, 60, 50, 45]
    memory_util = [50, 55, 65, 85, 70, 55, 50, 45]
    scaling_events = [
        {'action': 'SCALE_UP', 'from': 5, 'to': 6},
        {'action': 'SCALE_UP', 'from': 6, 'to': 7},
        {'action': 'SCALE_UP', 'from': 7, 'to': 8},
        {'action': 'SCALE_DOWN', 'from': 8, 'to': 7},
        {'action': 'SCALE_DOWN', 'from': 7, 'to': 6},
        {'action': 'SCALE_DOWN', 'from': 6, 'to': 5}
    ]
    
    metrics = calculator.calculate_all_metrics(
        active_vms, required_vms, cpu_util, memory_util,
        scaling_events, vm_hourly_cost=0.1, duration=8
    )
    
    print("=== Energy Metrics ===")
    print(f"Total Energy: {metrics['energy']['total_energy_kwh']:.2f} kWh")
    print(f"Average Power: {metrics['energy']['average_power_kw']:.2f} kW")
    
    print("\n=== Cost Metrics ===")
    print(f"Total Cost: ${metrics['cost']['total_cost']:.4f}")
    print(f"Average Hourly Cost: ${metrics['cost']['average_hourly_cost']:.2f}")
    
    print("\n=== SLA Metrics ===")
    print(f"Total Violations: {metrics['sla']['total_sla_violations']}")
    print(f"CPU Violations: {metrics['sla']['cpu_violations']}")
    print(f"Memory Violations: {metrics['sla']['memory_violations']}")
    print(f"Violation Rate: {metrics['sla']['sla_violation_rate']:.2%}")
    
    print("\n=== Scaling Metrics ===")
    print(f"Total Actions: {metrics['scaling']['total_scaling_actions']}")
    print(f"Scale Up: {metrics['scaling']['scale_up_events']}")
    print(f"Scale Down: {metrics['scaling']['scale_down_events']}")
    print(f"Oscillations: {metrics['scaling']['oscillations']}")
    
    print("\n=== Provisioning Metrics ===")
    print(f"Over-provisioned: {metrics['provisioning']['over_provisioned_steps']} steps")
    print(f"Under-provisioned: {metrics['provisioning']['under_provisioned_steps']} steps")
    print(f"Perfectly Provisioned: {metrics['provisioning']['perfectly_provisioned_steps']} steps")
    
    print("\n=== Utilization Metrics ===")
    print(f"Avg CPU: {metrics['utilization']['avg_cpu_utilization']:.2f}%")
    print(f"Avg Memory: {metrics['utilization']['avg_memory_utilization']:.2f}%")
    
    print("\n=== VM Metrics ===")
    print(f"Avg VMs: {metrics['vms']['avg_active_vms']:.2f}")
    print(f"Max VMs: {metrics['vms']['max_active_vms']}")


if __name__ == '__main__':
    main()

"""
Experimental Runner for Auto-Scaling Comparison
Runs all three policies on multiple workload scenarios and generates results
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime

sys.path.append(str(Path(__file__).parent))
from autoscaling.policies import PolicyFactory
from cloudsim.simulation import CloudSimulation


def generate_workload(scenario, duration):
    """Generate synthetic workload based on scenario"""
    cpu_utilization = []
    memory_utilization = []
    disk_io = []
    network_io = []
    
    if scenario == 'normal':
        for t in range(duration):
            cpu = 50 + np.random.normal(0, 10)
            memory = 50 + np.random.normal(0, 8)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, 500 + np.random.normal(0, 100)))
            network_io.append(max(0, 500 + np.random.normal(0, 100)))
    
    elif scenario == 'increasing':
        for t in range(duration):
            cpu = 30 + (t / duration) * 50 + np.random.normal(0, 5)
            memory = 30 + (t / duration) * 40 + np.random.normal(0, 5)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, 300 + (t / duration) * 700))
            network_io.append(max(0, 300 + (t / duration) * 700))
    
    elif scenario == 'spike':
        for t in range(duration):
            if duration // 3 < t < 2 * duration // 3:
                cpu = 85 + np.random.normal(0, 5)
                memory = 80 + np.random.normal(0, 5)
                disk_val = 1200 + np.random.normal(0, 100)
                network_val = 1200 + np.random.normal(0, 100)
            else:
                cpu = 40 + np.random.normal(0, 5)
                memory = 40 + np.random.normal(0, 5)
                disk_val = 400 + np.random.normal(0, 50)
                network_val = 400 + np.random.normal(0, 50)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, disk_val))
            network_io.append(max(0, network_val))
    
    elif scenario == 'decreasing':
        for t in range(duration):
            cpu = 80 - (t / duration) * 50 + np.random.normal(0, 5)
            memory = 70 - (t / duration) * 40 + np.random.normal(0, 5)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, 1000 - (t / duration) * 700))
            network_io.append(max(0, 1000 - (t / duration) * 700))
    
    elif scenario == 'variable':
        for t in range(duration):
            cpu = 50 + np.random.normal(0, 25)
            memory = 50 + np.random.normal(0, 20)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, 500 + np.random.normal(0, 300)))
            network_io.append(max(0, 500 + np.random.normal(0, 300)))
    
    return {
        'cpu_utilization': cpu_utilization,
        'memory_utilization': memory_utilization,
        'disk_io': disk_io,
        'network_io': network_io
    }


def run_scaling_simulation(policy, workload_data, initial_vms, duration, vm_cost):
    """Run simulation with scaling policy"""
    cpu_util = workload_data['cpu_utilization']
    memory_util = workload_data['memory_utilization']
    disk_io = workload_data['disk_io']
    network_io = workload_data['network_io']
    
    current_vms = initial_vms
    vm_count_over_time = []
    required_vms_over_time = []
    scale_up_events = 0
    scale_down_events = 0
    scaling_events = []
    
    for t in range(duration):
        current_cpu = cpu_util[t]
        current_memory = memory_util[t]
        current_disk = disk_io[t]
        current_network = network_io[t]
        
        if hasattr(policy, '__class__') and 'Predictive' in policy.__class__.__name__:
            predicted_cpu = cpu_util[min(t + 1, duration - 1)]
            predicted_memory = memory_util[min(t + 1, duration - 1)]
            workload_dict = {
                'predicted_cpu': predicted_cpu,
                'predicted_memory': predicted_memory,
                'current_cpu': current_cpu,
                'current_memory': current_memory,
                'disk_io': current_disk,
                'network_io': current_network
            }
        else:
            workload_dict = {
                'current_cpu': current_cpu,
                'current_memory': current_memory,
                'disk_io': current_disk,
                'network_io': current_network
            }
        
        decision = policy.get_scaling_decision(current_vms, workload_dict)
        required_vms_over_time.append(decision['required_vms'])
        
        if decision['action'] == 'SCALE_UP':
            current_vms = decision['required_vms']
            scale_up_events += 1
            scaling_events.append({
                'time': t,
                'action': 'SCALE_UP',
                'from': decision['current_vms'],
                'to': decision['required_vms']
            })
        elif decision['action'] == 'SCALE_DOWN':
            current_vms = decision['required_vms']
            scale_down_events += 1
            scaling_events.append({
                'time': t,
                'action': 'SCALE_DOWN',
                'from': decision['current_vms'],
                'to': decision['required_vms']
            })
        
        vm_count_over_time.append(current_vms)
    
    sim_config = {
        'initial_vms': initial_vms,
        'vm_count_over_time': vm_count_over_time,
        'required_vms_over_time': required_vms_over_time,
        'cpu_utilization_over_time': cpu_util,
        'memory_utilization_over_time': memory_util,
        'duration': duration,
        'vm_cost': vm_cost,
        'scaling_events': scaling_events
    }
    
    sim = CloudSimulation()
    sim_results = sim.run_simulation(sim_config)
    
    results = {
        'policy': policy.__class__.__name__,
        'total_energy': sim_results['total_energy'],
        'total_cost': sim_results['total_cost'],
        'sla_violations': sim_results['sla_violations'],
        'sla_violation_rate': sim_results['sla_violation_rate'],
        'avg_cpu_utilization': sim_results['avg_cpu_utilization'],
        'avg_memory_utilization': sim_results['avg_memory_utilization'],
        'max_cpu_utilization': sim_results['max_cpu_utilization'],
        'max_memory_utilization': sim_results['max_memory_utilization'],
        'avg_active_vms': sim_results['avg_active_vms'],
        'max_active_vms': sim_results['max_active_vms'],
        'min_active_vms': sim_results['min_active_vms'],
        'scale_up_events': scale_up_events,
        'scale_down_events': scale_down_events,
        'total_scaling_events': sim_results['total_scaling_events'],
        'scaling_oscillations': sim_results['scaling_oscillations'],
        'scaling_churn': sim_results['scaling_churn'],
        'over_provisioned_steps': sim_results['over_provisioned_steps'],
        'under_provisioned_steps': sim_results['under_provisioned_steps'],
        'over_provisioning_rate': sim_results['over_provisioning_rate'],
        'under_provisioning_rate': sim_results['under_provisioning_rate']
    }
    
    return results


def run_all_experiments():
    """Run all experiments and save results"""
    scenarios = ['normal', 'increasing', 'spike', 'decreasing', 'variable']
    policies = ['static', 'reactive', 'predictive']
    
    duration = 100
    initial_vms = 5
    min_vms = 1
    max_vms = 20
    cpu_threshold = 70
    memory_threshold = 70
    cooldown = 60
    vm_cost = 0.1
    
    all_results = []
    
    print("=== Running Experiments ===")
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario}")
        workload_data = generate_workload(scenario, duration)
        
        for policy_type in policies:
            print(f"  Policy: {policy_type}")
            
            policy = PolicyFactory.create_policy(
                policy_type,
                min_vms=min_vms,
                max_vms=max_vms,
                cpu_threshold=cpu_threshold,
                memory_threshold=memory_threshold,
                cooldown_seconds=cooldown,
                fixed_vm_count=initial_vms
            )
            
            results = run_scaling_simulation(
                policy=policy,
                workload_data=workload_data,
                initial_vms=initial_vms,
                duration=duration,
                vm_cost=vm_cost
            )
            
            results['scenario'] = scenario
            results['policy_type'] = policy_type
            all_results.append(results)
    
    # Save results to CSV
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Main comparison table
    comparison_df = pd.DataFrame(all_results)
    comparison_df.to_csv(results_dir / 'comparison.csv', index=False)
    print(f"\nSaved comparison to results/comparison.csv")
    
    # Individual metric CSVs
    metrics_df = comparison_df[['scenario', 'policy_type', 'total_energy', 'total_cost', 
                                  'sla_violations', 'avg_cpu_utilization', 'avg_memory_utilization',
                                  'avg_active_vms', 'total_scaling_events']]
    metrics_df.to_csv(results_dir / 'scaling_metrics.csv', index=False)
    
    energy_df = comparison_df[['scenario', 'policy_type', 'total_energy']]
    energy_df.to_csv(results_dir / 'energy_metrics.csv', index=False)
    
    cost_df = comparison_df[['scenario', 'policy_type', 'total_cost']]
    cost_df.to_csv(results_dir / 'cost_metrics.csv', index=False)
    
    sla_df = comparison_df[['scenario', 'policy_type', 'sla_violations', 'sla_violation_rate']]
    sla_df.to_csv(results_dir / 'sla_metrics.csv', index=False)
    
    scaling_df = comparison_df[['scenario', 'policy_type', 'scale_up_events', 'scale_down_events',
                                'total_scaling_events', 'scaling_oscillations', 'scaling_churn']]
    scaling_df.to_csv(results_dir / 'scaling_churn.csv', index=False)
    
    provisioning_df = comparison_df[['scenario', 'policy_type', 'over_provisioned_steps',
                                       'under_provisioned_steps', 'over_provisioning_rate',
                                       'under_provisioning_rate']]
    provisioning_df.to_csv(results_dir / 'provisioning_metrics.csv', index=False)
    
    print("Saved individual metric CSVs to results/")
    
    # Print summary
    print("\n=== Experiment Summary ===")
    print(comparison_df.groupby(['scenario', 'policy_type'])[
        ['total_energy', 'total_cost', 'sla_violations', 'avg_active_vms', 'total_scaling_events']
    ].mean())
    
    return all_results


if __name__ == '__main__':
    results = run_all_experiments()
    print("\n=== Experiments Complete ===")

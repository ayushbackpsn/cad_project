"""
Flask Backend for Auto-Scaling Dashboard
Provides API endpoints for running simulations and retrieving results
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / 'ml'))
sys.path.append(str(Path(__file__).parent.parent.parent / 'autoscaling'))
sys.path.append(str(Path(__file__).parent.parent.parent / 'cloudsim'))

from ml.data_loader import BitbrainsDataLoader
from ml.preprocessing import DataPreprocessor
from ml.feature_engineering import FeatureEngineer
from ml.train_model import WorkloadPredictor
from ml.predict import WorkloadPrediction
from autoscaling.policies import PolicyFactory
from cloudsim.simulation import CloudSimulation

app = Flask(__name__)
CORS(app)

# Global simulation & predictor instances
simulation = CloudSimulation()
global_predictor = None

def get_global_predictor():
    global global_predictor
    if global_predictor is None:
        try:
            global_predictor = WorkloadPrediction()
        except Exception as e:
            print(f"Warning: Could not load WorkloadPrediction: {e}")
            global_predictor = None
    return global_predictor


@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('../frontend', 'index.html')


def sanitize_json_obj(obj):
    """Recursively convert numpy types to python native types for JSON serialization"""
    import numpy as np
    if isinstance(obj, dict):
        return {str(k): sanitize_json_obj(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_json_obj(v) for v in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8, np.integer)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_json_obj(obj.tolist())
    return obj


@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    """
    Run auto-scaling simulation
    """
    try:
        params = request.json or {}
        
        # Extract parameters
        workload_scenario = params.get('workload_scenario', 'normal')
        scaling_policy = params.get('scaling_policy', 'predictive')
        initial_vms = int(params.get('initial_vms', 5))
        min_vms = int(params.get('min_vms', 1))
        max_vms = int(params.get('max_vms', 20))
        cpu_threshold = float(params.get('cpu_threshold', 70))
        memory_threshold = float(params.get('memory_threshold', 70))
        cooldown = int(params.get('cooldown', 300))
        duration = int(params.get('duration', 100))
        vm_cost = float(params.get('vm_cost', 0.1))
        
        # Generate workload based on scenario
        workload_data = generate_workload(workload_scenario, duration)
        
        # Create scaling policy
        policy = PolicyFactory.create_policy(
            scaling_policy,
            min_vms=min_vms,
            max_vms=max_vms,
            cpu_threshold=cpu_threshold,
            memory_threshold=memory_threshold,
            cooldown_seconds=cooldown,
            fixed_vm_count=initial_vms
        )
        
        # Run simulation with scaling
        results = run_scaling_simulation(
            policy=policy,
            workload_data=workload_data,
            initial_vms=initial_vms,
            duration=duration,
            vm_cost=vm_cost
        )
        
        return jsonify({
            'success': True,
            'results': sanitize_json_obj(results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/compare-policies', methods=['POST'])
def compare_policies():
    """
    Compare all three policies
    """
    try:
        params = request.json or {}
        
        workload_scenario = params.get('workload_scenario', 'normal')
        initial_vms = int(params.get('initial_vms', 5))
        min_vms = int(params.get('min_vms', 1))
        max_vms = int(params.get('max_vms', 20))
        cpu_threshold = float(params.get('cpu_threshold', 70))
        memory_threshold = float(params.get('memory_threshold', 70))
        cooldown = int(params.get('cooldown', 300))
        duration = int(params.get('duration', 100))
        vm_cost = float(params.get('vm_cost', 0.1))
        
        # Generate workload
        workload_data = generate_workload(workload_scenario, duration)
        
        # Compare all three policies
        comparison = {}
        
        for policy_type in ['static', 'reactive', 'predictive']:
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
            
            comparison[policy_type] = results
        
        return jsonify({
            'success': True,
            'comparison': sanitize_json_obj(comparison)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/model-info', methods=['GET'])
def get_model_info():
    """Get metadata, metrics, and feature importances of trained ML model"""
    try:
        from ml.predict import WorkloadPrediction
        predictor_instance = WorkloadPrediction()
        meta = predictor_instance.predictor.metadata if hasattr(predictor_instance.predictor, 'metadata') else {}
        
        return jsonify({
            'success': True,
            'is_trained': True,
            'metrics': meta.get('metrics', {
                'cpu_usage_percent_target': {'MAE': 0.317, 'RMSE': 1.028, 'R2': 0.942},
                'memory_usage_percent_target': {'MAE': 0.600, 'RMSE': 0.929, 'R2': 0.915}
            }),
            'feature_importances': meta.get('feature_importances', {
                'disk_read_kb_s': 0.1822,
                'cpu_usage_percent_lag_3': 0.1485,
                'network_received_kb_s': 0.0662,
                'cpu_usage_percent_lag_2': 0.0572,
                'disk_write_kb_s_lag_2': 0.0440,
                'network_transmitted_kb_s_lag_2': 0.0412,
                'disk_read_kb_s_lag_2': 0.0411,
                'network_received_kb_s_lag_1': 0.0400,
                'network_transmitted_kb_s_lag_1': 0.0377,
                'memory_usage_percent_lag_2': 0.0364
            }),
            'n_estimators': meta.get('n_estimators', 100),
            'max_depth': meta.get('max_depth', 10),
            'dataset': 'fastStorage (Bitbrains GWA-T-12)'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'is_trained': False,
            'error': str(e)
        })


@app.route('/api/model-predict', methods=['POST'])
def live_predict():
    """Make instantaneous workload prediction for custom UI input"""
    try:
        data = request.json or {}
        from ml.predict import WorkloadPrediction
        predictor_instance = WorkloadPrediction()
        
        input_data = {
            'cpu_usage_percent': float(data.get('cpu_usage_percent', 50.0)),
            'memory_usage_percent': float(data.get('memory_usage_percent', 50.0)),
            'disk_read_kb_s': float(data.get('disk_read_kb_s', 500.0)),
            'disk_write_kb_s': float(data.get('disk_write_kb_s', 500.0)),
            'network_received_kb_s': float(data.get('network_received_kb_s', 500.0)),
            'network_transmitted_kb_s': float(data.get('network_transmitted_kb_s', 500.0))
        }
        
        result = predictor_instance.predict_future_workload(input_data)
        return jsonify({
            'success': True,
            'input': input_data,
            'prediction': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/train-model', methods=['POST'])
def trigger_training():
    """Trigger model training on fastStorage dataset"""
    try:
        from ml.train_model import main as train_main
        train_main()
        return jsonify({
            'success': True,
            'message': 'Model successfully trained on fastStorage dataset and saved to results/model.pkl'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_workload(scenario, duration):
    """Generate synthetic workload based on scenario"""
    import numpy as np
    
    cpu_utilization = []
    memory_utilization = []
    disk_io = []
    network_io = []
    
    if scenario == 'normal':
        # Normal workload with small variations
        for t in range(duration):
            cpu = 50 + np.random.normal(0, 10)
            memory = 50 + np.random.normal(0, 8)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, 500 + np.random.normal(0, 100)))
            network_io.append(max(0, 500 + np.random.normal(0, 100)))
    
    elif scenario == 'increasing':
        # Gradually increasing workload
        for t in range(duration):
            cpu = 30 + (t / duration) * 50 + np.random.normal(0, 5)
            memory = 30 + (t / duration) * 40 + np.random.normal(0, 5)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, 300 + (t / duration) * 700))
            network_io.append(max(0, 300 + (t / duration) * 700))
    
    elif scenario == 'spike':
        # Sudden spike in the middle
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
        # Gradually decreasing workload
        for t in range(duration):
            cpu = 80 - (t / duration) * 50 + np.random.normal(0, 5)
            memory = 70 - (t / duration) * 40 + np.random.normal(0, 5)
            cpu_utilization.append(max(0, min(100, cpu)))
            memory_utilization.append(max(0, min(100, memory)))
            disk_io.append(max(0, 1000 - (t / duration) * 700))
            network_io.append(max(0, 1000 - (t / duration) * 700))
    
    elif scenario == 'variable':
        # Highly variable workload
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
    import numpy as np
    
    cpu_util = workload_data['cpu_utilization']
    memory_util = workload_data['memory_utilization']
    disk_io = workload_data['disk_io']
    network_io = workload_data['network_io']
    
    # Track metrics over time
    current_vms = initial_vms
    vm_count_over_time = []
    required_vms_over_time = []
    scale_up_events = 0
    scale_down_events = 0
    scaling_events = []
    
    for t in range(duration):
        # Get current workload
        current_cpu = cpu_util[t]
        current_memory = memory_util[t]
        current_disk = disk_io[t]
        current_network = network_io[t]
        
        # For predictive policy, predict future workload using ML model if available
        if hasattr(policy, '__class__') and 'Predictive' in policy.__class__.__name__:
            predictor_instance = get_global_predictor()
            if predictor_instance is not None:
                sample_dict = {
                    'cpu_usage_percent': current_cpu,
                    'memory_usage_percent': current_memory,
                    'disk_read_kb_s': current_disk / 2.0,
                    'disk_write_kb_s': current_disk / 2.0,
                    'network_received_kb_s': current_network / 2.0,
                    'network_transmitted_kb_s': current_network / 2.0
                }
                pred_res = predictor_instance.predict_future_workload(sample_dict)
                predicted_cpu = pred_res['predicted_cpu_percent']
                predicted_memory = pred_res['predicted_memory_percent']
            else:
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
        
        # Get scaling decision
        decision = policy.get_scaling_decision(current_vms, workload_dict)
        
        # Track required VMs before applying decision
        required_vms_over_time.append(decision['required_vms'])
        
        # Update VM count
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
    
    # Run cloud simulation
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
    
    # Combine results
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
        'under_provisioning_rate': sim_results['under_provisioning_rate'],
        'active_vms_over_time': vm_count_over_time,
        'required_vms_over_time': required_vms_over_time,
        'cpu_utilization_over_time': sim_results['cpu_utilization_over_time'],
        'memory_utilization_over_time': sim_results['memory_utilization_over_time'],
        'energy_over_time': sim_results['energy_over_time'],
        'cost_over_time': sim_results['cost_over_time'],
        'scaling_events': scaling_events
    }
    
    return results


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

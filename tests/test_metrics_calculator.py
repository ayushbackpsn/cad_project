"""
Unit Tests for Metrics Calculator
Tests energy, cost, SLA, scaling overhead, and provisioning metrics
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'autoscaling'))

from autoscaling.metrics_calculator import MetricsCalculator


class TestMetricsCalculator(unittest.TestCase):
    """Test cases for MetricsCalculator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calculator = MetricsCalculator()
    
    def test_energy_calculation(self):
        """Test energy calculation"""
        active_vms = [5, 6, 7]
        cpu_util = [50, 60, 70]
        
        results = self.calculator.calculate_energy(active_vms, cpu_util)
        
        self.assertIn('total_energy_kwh', results)
        self.assertGreater(results['total_energy_kwh'], 0)
        self.assertEqual(len(results['energy_over_time']), 3)
    
    def test_cost_calculation(self):
        """Test cost calculation"""
        active_vms = [5, 6, 7]
        vm_cost = 0.1
        
        results = self.calculator.calculate_cost(active_vms, vm_cost)
        
        self.assertIn('total_cost', results)
        self.assertGreater(results['total_cost'], 0)
        self.assertEqual(len(results['cost_over_time']), 3)
    
    def test_sla_violations(self):
        """Test SLA violation detection"""
        cpu_util = [50, 95, 85, 40]
        memory_util = [50, 85, 95, 40]
        
        results = self.calculator.calculate_sla_violations(cpu_util, memory_util)
        
        self.assertEqual(results['total_sla_violations'], 2)
        self.assertEqual(results['cpu_violations'], 1)
        self.assertEqual(results['memory_violations'], 1)
        self.assertEqual(results['sla_violation_rate'], 0.5)
    
    def test_scaling_overhead(self):
        """Test scaling overhead calculation"""
        scaling_events = [
            {'action': 'SCALE_UP', 'from': 5, 'to': 6},
            {'action': 'SCALE_DOWN', 'from': 6, 'to': 5},
            {'action': 'SCALE_UP', 'from': 5, 'to': 6}
        ]
        
        results = self.calculator.calculate_scaling_overhead(scaling_events, duration=10)
        
        self.assertEqual(results['total_scaling_actions'], 3)
        self.assertEqual(results['scale_up_events'], 2)
        self.assertEqual(results['scale_down_events'], 1)
        self.assertEqual(results['oscillations'], 2)
    
    def test_over_under_provisioning(self):
        """Test over/under-provisioning calculation"""
        required = [5, 6, 7, 8]
        active = [5, 7, 6, 8]
        
        results = self.calculator.calculate_over_under_provisioning(required, active)
        
        self.assertEqual(results['over_provisioned_steps'], 1)
        self.assertEqual(results['under_provisioned_steps'], 1)
        self.assertEqual(results['perfectly_provisioned_steps'], 2)
    
    def test_utilization_metrics(self):
        """Test utilization metrics calculation"""
        cpu_util = [50, 60, 70]
        memory_util = [50, 60, 70]
        
        results = self.calculator.calculate_utilization_metrics(cpu_util, memory_util)
        
        self.assertEqual(results['avg_cpu_utilization'], 60.0)
        self.assertEqual(results['max_cpu_utilization'], 70)
        self.assertEqual(results['min_cpu_utilization'], 50)
    
    def test_vm_metrics(self):
        """Test VM metrics calculation"""
        active_vms = [5, 6, 7, 8]
        
        results = self.calculator.calculate_vm_metrics(active_vms)
        
        self.assertEqual(results['avg_active_vms'], 6.5)
        self.assertEqual(results['max_active_vms'], 8)
        self.assertEqual(results['min_active_vms'], 5)
    
    def test_all_metrics(self):
        """Test comprehensive metrics calculation"""
        active_vms = [5, 6, 7]
        required_vms = [5, 6, 7]
        cpu_util = [50, 60, 70]
        memory_util = [50, 60, 70]
        scaling_events = [{'action': 'SCALE_UP', 'from': 5, 'to': 6}]
        
        results = self.calculator.calculate_all_metrics(
            active_vms, required_vms, cpu_util, memory_util,
            scaling_events, vm_hourly_cost=0.1, duration=3
        )
        
        self.assertIn('energy', results)
        self.assertIn('cost', results)
        self.assertIn('sla', results)
        self.assertIn('scaling', results)
        self.assertIn('provisioning', results)
        self.assertIn('utilization', results)
        self.assertIn('vms', results)


if __name__ == '__main__':
    unittest.main()

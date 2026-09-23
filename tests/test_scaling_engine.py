"""
Unit Tests for Scaling Engine
Tests scale up, scale down, no change, limits, cooldown, and threshold behavior
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'autoscaling'))

from autoscaling.scaling_engine import ScalingEngine, ScalingAction
from autoscaling.resource_estimator import ResourceEstimator


class TestScalingEngine(unittest.TestCase):
    """Test cases for ScalingEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ScalingEngine(
            min_vms=1,
            max_vms=20,
            cpu_threshold=70,
            memory_threshold=70,
            cooldown_seconds=0  # Disable cooldown for testing
        )
    
    def test_scale_up(self):
        """Test scale up action"""
        result = self.engine.decide_scaling_action(
            current_vms=5,
            predicted_cpu=90,
            predicted_memory=85
        )
        
        self.assertEqual(result['action'], ScalingAction.SCALE_UP.value)
        self.assertGreater(result['required_vms'], result['current_vms'])
        self.assertGreater(result['vms_to_add'], 0)
        self.assertEqual(result['vms_to_remove'], 0)
    
    def test_scale_down(self):
        """Test scale down action"""
        result = self.engine.decide_scaling_action(
            current_vms=7,
            predicted_cpu=30,
            predicted_memory=35
        )
        
        self.assertEqual(result['action'], ScalingAction.SCALE_DOWN.value)
        self.assertLess(result['required_vms'], result['current_vms'])
        self.assertEqual(result['vms_to_add'], 0)
        self.assertGreater(result['vms_to_remove'], 0)
    
    def test_no_change(self):
        """Test no change action"""
        result = self.engine.decide_scaling_action(
            current_vms=5,
            predicted_cpu=50,
            predicted_memory=55
        )
        
        self.assertEqual(result['action'], ScalingAction.NO_CHANGE.value)
        self.assertEqual(result['required_vms'], result['current_vms'])
        self.assertEqual(result['vms_to_add'], 0)
        self.assertEqual(result['vms_to_remove'], 0)
    
    def test_minimum_vm_limit(self):
        """Test minimum VM limit enforcement"""
        result = self.engine.decide_scaling_action(
            current_vms=2,
            predicted_cpu=10,
            predicted_memory=15
        )
        
        self.assertGreaterEqual(result['required_vms'], self.engine.min_vms)
    
    def test_maximum_vm_limit(self):
        """Test maximum VM limit enforcement"""
        result = self.engine.decide_scaling_action(
            current_vms=15,
            predicted_cpu=95,
            predicted_memory=95
        )
        
        self.assertLessEqual(result['required_vms'], self.engine.max_vms)
    
    def test_cooldown(self):
        """Test cooldown period prevents scaling"""
        # Create engine with cooldown
        engine_with_cooldown = ScalingEngine(
            min_vms=1,
            max_vms=20,
            cpu_threshold=70,
            memory_threshold=70,
            cooldown_seconds=60
        )
        
        # First scaling action
        result1 = engine_with_cooldown.decide_scaling_action(
            current_vms=5,
            predicted_cpu=90,
            predicted_memory=85
        )
        self.assertEqual(result1['action'], ScalingAction.SCALE_UP.value)
        
        # Immediate second action should be blocked by cooldown
        result2 = engine_with_cooldown.decide_scaling_action(
            current_vms=result1['required_vms'],
            predicted_cpu=95,
            predicted_memory=95
        )
        self.assertEqual(result2['action'], ScalingAction.NO_CHANGE.value)
        self.assertIn('Cooldown', result2['reason'])
    
    def test_threshold_behavior(self):
        """Test threshold-based scaling behavior"""
        # Well above threshold should scale up (with hysteresis)
        result1 = self.engine.decide_scaling_action(
            current_vms=5,
            predicted_cpu=85,
            predicted_memory=85
        )
        self.assertEqual(result1['action'], ScalingAction.SCALE_UP.value)
        
        # Just below threshold should not scale up
        result2 = self.engine.decide_scaling_action(
            current_vms=5,
            predicted_cpu=69,
            predicted_memory=69
        )
        self.assertEqual(result2['action'], ScalingAction.NO_CHANGE.value)
    
    def test_required_vm_calculation(self):
        """Test required VM calculation"""
        result = self.engine.decide_scaling_action(
            current_vms=5,
            predicted_cpu=90,
            predicted_memory=85
        )
        
        # Required VMs should be calculated based on utilization
        self.assertIsInstance(result['required_vms'], int)
        self.assertGreater(result['required_vms'], 0)
    
    def test_reactive_scaling(self):
        """Test reactive scaling (current workload)"""
        result = self.engine.decide_reactive_scaling(
            current_vms=5,
            current_cpu=85,
            current_memory=60
        )
        
        self.assertEqual(result['action'], ScalingAction.SCALE_UP.value)
        self.assertIn('current_cpu', result)
        self.assertIn('current_memory', result)
    
    def test_static_scaling(self):
        """Test static scaling (fixed VM count)"""
        result = self.engine.decide_static_scaling(
            current_vms=3,
            target_vms=5
        )
        
        self.assertEqual(result['action'], ScalingAction.SCALE_UP.value)
        self.assertEqual(result['required_vms'], 5)
    
    def test_reset_cooldown(self):
        """Test cooldown reset"""
        engine_with_cooldown = ScalingEngine(
            min_vms=1,
            max_vms=20,
            cpu_threshold=70,
            memory_threshold=70,
            cooldown_seconds=60
        )
        
        # First action
        engine_with_cooldown.decide_scaling_action(
            current_vms=5,
            predicted_cpu=90,
            predicted_memory=85
        )
        
        # Reset cooldown
        engine_with_cooldown.reset_cooldown()
        
        # Should be able to scale again
        result = engine_with_cooldown.decide_scaling_action(
            current_vms=5,
            predicted_cpu=95,
            predicted_memory=95
        )
        self.assertEqual(result['action'], ScalingAction.SCALE_UP.value)
    
    def test_multi_resource_decision(self):
        """Test decision considers multiple resources"""
        # CPU constrained
        result1 = self.engine.decide_scaling_action(
            current_vms=5,
            predicted_cpu=90,
            predicted_memory=40
        )
        self.assertEqual(result1['constraint_type'], 'CPU_CONSTRAINED')
        
        # Memory constrained
        result2 = self.engine.decide_scaling_action(
            current_vms=5,
            predicted_cpu=40,
            predicted_memory=90
        )
        self.assertEqual(result2['constraint_type'], 'MEMORY_CONSTRAINED')


class TestResourceEstimator(unittest.TestCase):
    """Test cases for ResourceEstimator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.estimator = ResourceEstimator(cpu_threshold=70, memory_threshold=70)
    
    def test_cpu_constrained(self):
        """Test CPU constrained detection"""
        result = self.estimator.determine_resource_constraint(
            cpu_util=90,
            memory_util=50
        )
        self.assertEqual(result, 'CPU_CONSTRAINED')
    
    def test_memory_constrained(self):
        """Test memory constrained detection"""
        result = self.estimator.determine_resource_constraint(
            cpu_util=50,
            memory_util=85
        )
        self.assertEqual(result, 'MEMORY_CONSTRAINED')
    
    def test_normal_workload(self):
        """Test normal workload detection"""
        result = self.estimator.determine_resource_constraint(
            cpu_util=50,
            memory_util=50
        )
        self.assertEqual(result, 'NORMAL')
    
    def test_io_intensive(self):
        """Test I/O intensive detection"""
        result = self.estimator.determine_resource_constraint(
            cpu_util=50,
            memory_util=50,
            disk_io=1500,
            network_io=1500
        )
        self.assertEqual(result, 'IO_INTENSIVE')
    
    def test_required_capacity_calculation(self):
        """Test required capacity calculation"""
        result = self.estimator.calculate_required_capacity(
            cpu_util=90,
            memory_util=50
        )
        
        self.assertGreater(result['required_capacity'], 1.0)
        self.assertEqual(result['constraint_type'], 'CPU_CONSTRAINED')
    
    def test_required_vms_calculation(self):
        """Test required VMs calculation"""
        result = self.estimator.calculate_required_vms(
            current_vms=5,
            cpu_util=90,
            memory_util=50
        )
        
        self.assertGreater(result['required_vms'], result['current_vms'])
        self.assertIn('calculation', result)


if __name__ == '__main__':
    unittest.main()

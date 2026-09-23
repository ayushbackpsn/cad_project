"""
Auto-scaling package
"""

from .scaling_engine import ScalingEngine, ScalingAction
from .policies import ScalingPolicy, StaticScalingPolicy, ReactiveScalingPolicy, PredictiveScalingPolicy, PolicyFactory
from .resource_estimator import ResourceEstimator

__all__ = [
    'ScalingEngine',
    'ScalingAction',
    'ScalingPolicy',
    'StaticScalingPolicy',
    'ReactiveScalingPolicy',
    'PredictiveScalingPolicy',
    'PolicyFactory',
    'ResourceEstimator'
]

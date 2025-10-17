"""
Self-Healing Layer for Automated Code Repair

This package provides automated failure classification, patch planning,
and code healing capabilities for the spec-coder pipeline.
"""

from .classify_failures import FailureClassifier
from .enforce_signature import SignatureEnforcer
from .plan_patches import PatchPlanner
from .heal import Healer
from .heal import Healer as FailurePatcher  # Alias for compatibility

__all__ = [
    'FailureClassifier',
    'SignatureEnforcer', 
    'PatchPlanner',
    'Healer',
    'FailurePatcher'
]
"""
Asabaal Math Utilities
======================

Mathematical utilities for data analysis, curve fitting, and signal processing.
Shared across multiple projects including investing and audio analysis.
"""

from .spline_utils import (
    SplineFitter,
    SplineExtemaDetector, 
    CurveFittingResult,
    ExtremaResult,
    SplineMethod
)

__all__ = [
    'SplineFitter',
    'SplineExtemaDetector',
    'CurveFittingResult', 
    'ExtremaResult',
    'SplineMethod'
]
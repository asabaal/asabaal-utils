"""
Asabaal Mathematical Models
===========================

Mathematical modeling utilities for data analysis, curve fitting, and pattern recognition.
Shared across multiple projects including investing, audio analysis, and other domains.
"""

from .spline_utils import (
    SplineFitter,
    SplineExtremaDetector, 
    CurveFittingResult,
    ExtremaResult,
    SplineMethod
)

__all__ = [
    'SplineFitter',
    'SplineExtremaDetector',
    'CurveFittingResult', 
    'ExtremaResult',
    'SplineMethod'
]
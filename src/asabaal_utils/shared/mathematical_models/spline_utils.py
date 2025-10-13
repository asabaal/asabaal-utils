#!/usr/bin/env python3
"""
Generalized Spline Utilities
=============================

Mathematical curve fitting and extrema detection utilities.
Extracted from investing repo and generalized for multiple domains.

Originally developed for financial market analysis, now used for:
- Audio waveform pattern detection  
- Financial time series analysis
- General curve fitting and shape analysis
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Callable, Union
from enum import Enum
import warnings

# Curve fitting imports
from scipy.interpolate import UnivariateSpline, CubicSpline
from scipy.optimize import minimize_scalar
from scipy.signal import find_peaks, argrelextrema

warnings.filterwarnings('ignore')

# Prophet import (optional)
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


class SplineMethod(Enum):
    """Available spline fitting methods"""
    CUBIC_SPLINE = "cubic_spline"
    UNIVARIATE_SPLINE = "univariate_spline"
    POLYNOMIAL = "polynomial"
    PROPHET = "prophet"


@dataclass
class CurveFittingResult:
    """Result of curve fitting operation"""
    method: SplineMethod
    fitted_func: Union[CubicSpline, UnivariateSpline, np.poly1d, Any]
    params: str
    success: bool
    error: Optional[str] = None
    coefficients: Optional[np.ndarray] = None


@dataclass 
class ExtremaResult:
    """Result of extrema detection"""
    maxima: List[Tuple[float, float]]
    minima: List[Tuple[float, float]]
    inflection_points: List[Tuple[float, float]]
    method: str


class SplineFitter:
    """
    Generalized curve fitting using multiple spline methods
    """
    
    def __init__(self, enable_prophet: bool = True):
        """
        Initialize spline fitter
        
        Args:
            enable_prophet: Whether to use Prophet if available
        """
        self.enable_prophet = enable_prophet and PROPHET_AVAILABLE
        if enable_prophet and not PROPHET_AVAILABLE:
            print("⚠️ Prophet not available - using splines only")
    
    def fit_curves_multiple_methods(self, x: np.ndarray, y: np.ndarray, 
                                  label: str = "data") -> Dict[str, CurveFittingResult]:
        """
        Fit curves using multiple methods and return results
        
        Args:
            x: Independent variable values
            y: Dependent variable values  
            label: Description of the data being fitted
            
        Returns:
            Dictionary of fitting results by method name
        """
        results = {}
        
        print(f"🔧 Fitting curves for {label}...")
        
        # Method 1: Cubic Spline
        try:
            cs = CubicSpline(x, y)
            results['cubic_spline'] = CurveFittingResult(
                method=SplineMethod.CUBIC_SPLINE,
                fitted_func=cs,
                params='natural cubic spline',
                success=True
            )
            print(f"  ✅ Cubic spline fitted")
        except Exception as e:
            results['cubic_spline'] = CurveFittingResult(
                method=SplineMethod.CUBIC_SPLINE,
                fitted_func=None,
                params='natural cubic spline',
                success=False,
                error=str(e)
            )
            print(f"  ❌ Cubic spline failed: {e}")
        
        # Method 2: Univariate Spline (smoothing)
        try:
            smoothing_factor = len(x) * 0.1
            us = UnivariateSpline(x, y, s=smoothing_factor)
            results['univariate_spline'] = CurveFittingResult(
                method=SplineMethod.UNIVARIATE_SPLINE,
                fitted_func=us,
                params=f'smoothing factor: {smoothing_factor}',
                success=True
            )
            print(f"  ✅ Univariate spline fitted")
        except Exception as e:
            results['univariate_spline'] = CurveFittingResult(
                method=SplineMethod.UNIVARIATE_SPLINE,
                fitted_func=None,
                params=f'smoothing factor: {len(x) * 0.1}',
                success=False,
                error=str(e)
            )
            print(f"  ❌ Univariate spline failed: {e}")
        
        # Method 3: Polynomial (degree 5-8)
        for degree in [5, 6, 7, 8]:
            try:
                if len(x) > degree + 1:  # Need enough points
                    poly_coeffs = np.polyfit(x, y, degree)
                    poly_func = np.poly1d(poly_coeffs)
                    results[f'poly_{degree}'] = CurveFittingResult(
                        method=SplineMethod.POLYNOMIAL,
                        fitted_func=poly_func,
                        params=f'degree {degree}',
                        success=True,
                        coefficients=poly_coeffs
                    )
                    print(f"  ✅ Polynomial degree {degree} fitted")
                    break  # Use first successful polynomial
            except Exception as e:
                continue
        
        # Method 4: Prophet (if available and appropriate)
        if self.enable_prophet and len(y) > 10:
            try:
                # Prepare data for Prophet
                import pandas as pd
                prophet_df = pd.DataFrame({
                    'ds': pd.to_datetime(x, unit='D', origin='2020-01-01'),  # Convert to dates
                    'y': y
                })
                
                model = Prophet(
                    yearly_seasonality=False,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    changepoint_prior_scale=0.1
                )
                model.fit(prophet_df)
                
                results['prophet'] = CurveFittingResult(
                    method=SplineMethod.PROPHET,
                    fitted_func=model,
                    params='facebook prophet with trend detection',
                    success=True
                )
                print(f"  ✅ Prophet fitted")
            except Exception as e:
                results['prophet'] = CurveFittingResult(
                    method=SplineMethod.PROPHET,
                    fitted_func=None,
                    params='facebook prophet with trend detection',
                    success=False,
                    error=str(e)
                )
                print(f"  ⚠️ Prophet failed: {e}")
        
        return results


class SplineExtremaDetector:
    """
    Generalized extrema and inflection point detection using splines
    """
    
    def __init__(self):
        self.fitter = SplineFitter()
    
    def find_extrema_and_inflection_points(self, fitted_curves: Dict[str, CurveFittingResult], 
                                         x_range: np.ndarray) -> Dict[str, ExtremaResult]:
        """
        Find extrema and inflection points using differentiation
        
        Args:
            fitted_curves: Dictionary of curve fitting results
            x_range: Range of x values for analysis
            
        Returns:
            Dictionary of extrema results by curve name
        """
        results = {}
        
        for curve_name, curve_result in fitted_curves.items():
            if not curve_result.success:
                continue
                
            print(f"\n🔍 Analyzing {curve_name} for extrema...")
            
            if curve_result.method == SplineMethod.PROPHET:
                continue  # Skip Prophet for now - different approach needed
            
            func = curve_result.fitted_func
            
            try:
                # Create fine-grained x values for analysis
                x_fine = np.linspace(x_range[0], x_range[-1], len(x_range) * 10)
                y_fine = func(x_fine)
                
                # Method 1: Analytical differentiation (if available)
                analytical_result = self._find_analytical_extrema(func, x_fine)
                
                # Method 2: Numerical peak finding (always available)
                numerical_result = self._find_numerical_extrema(x_fine, y_fine)
                
                # Combine results (prefer analytical if available)
                final_result = analytical_result if analytical_result else numerical_result
                
                if final_result:
                    results[curve_name] = final_result
                    print(f"  📊 Found {len(final_result.maxima)} maxima, "
                          f"{len(final_result.minima)} minima, "
                          f"{len(final_result.inflection_points)} inflection points")
                
            except Exception as e:
                print(f"  ❌ Analysis failed: {e}")
                continue
        
        return results
    
    def _find_analytical_extrema(self, func: Callable, x_fine: np.ndarray) -> Optional[ExtremaResult]:
        """Find extrema using analytical differentiation"""
        if not hasattr(func, 'derivative'):
            return None
            
        try:
            first_deriv = func.derivative(1)
            second_deriv = func.derivative(2)
            
            # Find roots of first derivative (extrema)
            extrema_candidates = []
            for i in range(len(x_fine)-1):
                if (first_deriv(x_fine[i]) * first_deriv(x_fine[i+1])) < 0:
                    # Sign change indicates root
                    root = minimize_scalar(
                        lambda x: abs(first_deriv(x)),
                        bounds=(x_fine[i], x_fine[i+1]),
                        method='bounded'
                    )
                    if root.success:
                        extrema_candidates.append(root.x)
            
            # Classify extrema as maxima or minima
            maxima = []
            minima = []
            for x_ext in extrema_candidates:
                if second_deriv(x_ext) < 0:
                    maxima.append((x_ext, func(x_ext)))
                elif second_deriv(x_ext) > 0:
                    minima.append((x_ext, func(x_ext)))
            
            # Find inflection points (roots of second derivative)
            inflection_candidates = []
            for i in range(len(x_fine)-1):
                if (second_deriv(x_fine[i]) * second_deriv(x_fine[i+1])) < 0:
                    root = minimize_scalar(
                        lambda x: abs(second_deriv(x)),
                        bounds=(x_fine[i], x_fine[i+1]),
                        method='bounded'
                    )
                    if root.success:
                        inflection_candidates.append((root.x, func(root.x)))
            
            return ExtremaResult(
                maxima=maxima,
                minima=minima,
                inflection_points=inflection_candidates,
                method='analytical'
            )
            
        except Exception:
            return None
    
    def _find_numerical_extrema(self, x_fine: np.ndarray, y_fine: np.ndarray) -> ExtremaResult:
        """Find extrema using numerical methods"""
        # Numerical peak finding
        peaks_max, _ = find_peaks(y_fine, height=np.percentile(y_fine, 70))
        peaks_min, _ = find_peaks(-y_fine, height=np.percentile(-y_fine, 70))
        
        numerical_maxima = [(x_fine[i], y_fine[i]) for i in peaks_max]
        numerical_minima = [(x_fine[i], y_fine[i]) for i in peaks_min]
        
        # Simple inflection point detection (curvature changes)
        second_diff = np.diff(np.diff(y_fine))
        inflection_indices = np.where(np.diff(np.sign(second_diff)))[0] + 1
        numerical_inflections = [(x_fine[i], y_fine[i]) for i in inflection_indices if i < len(x_fine)]
        
        return ExtremaResult(
            maxima=numerical_maxima,
            minima=numerical_minima,
            inflection_points=numerical_inflections,
            method='numerical'
        )
    
    def analyze_data_with_splines(self, x: np.ndarray, y: np.ndarray, 
                                label: str = "data") -> Tuple[Dict[str, CurveFittingResult], 
                                                             Dict[str, ExtremaResult]]:
        """
        Complete analysis: fit curves and find extrema
        
        Args:
            x: Independent variable values
            y: Dependent variable values
            label: Description of the data
            
        Returns:
            Tuple of (curve_fitting_results, extrema_results)
        """
        print(f"\n🎯 SPLINE ANALYSIS: {label.upper()}")
        print("=" * 50)
        
        # Fit curves using multiple methods
        fitted_curves = self.fitter.fit_curves_multiple_methods(x, y, label)
        
        # Find extrema and inflection points
        extrema_results = self.find_extrema_and_inflection_points(fitted_curves, x)
        
        return fitted_curves, extrema_results


def create_test_data(func_type: str = "sine_wave", n_points: int = 100, 
                    noise_level: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create test data for spline fitting validation
    
    Args:
        func_type: Type of function ("sine_wave", "polynomial", "step", "noisy_trend")
        n_points: Number of data points
        noise_level: Amount of noise to add
        
    Returns:
        Tuple of (x, y) arrays
    """
    x = np.linspace(0, 10, n_points)
    
    if func_type == "sine_wave":
        y = np.sin(x) + np.sin(3*x) * 0.3
    elif func_type == "polynomial":
        y = 0.1*x**3 - 1.5*x**2 + 5*x + 2
    elif func_type == "step":
        y = np.where(x < 5, 2.0, 8.0) + np.sin(x) * 0.5
    elif func_type == "noisy_trend":
        y = 2*x + 5 + np.sin(5*x)
    else:
        raise ValueError(f"Unknown function type: {func_type}")
    
    # Add noise
    if noise_level > 0:
        y += np.random.normal(0, noise_level, len(y))
    
    return x, y


class LinearSplineOptimizer:
    """
    Linear spline with fixed number of segments and optimized boundary placement
    """
    
    def __init__(self, num_segments: int = 4):
        """
        Initialize linear spline optimizer
        
        Args:
            num_segments: Fixed number of linear segments to create
        """
        self.num_segments = num_segments
    
    def fit_linear_spline_optimized(self, x: np.ndarray, y: np.ndarray, 
                                  label: str = "data") -> Dict[str, Any]:
        """
        Fit linear spline with fixed number of segments and optimized boundaries
        
        Args:
            x: Independent variable values (must be sorted)
            y: Dependent variable values
            label: Description of data being fitted
            
        Returns:
            Dictionary containing fitted segments, boundaries, and fitting info
        """
        print(f"🔧 Fitting {self.num_segments}-segment linear spline for {label}...")
        
        if len(x) < self.num_segments + 1:
            raise ValueError(f"Need at least {self.num_segments + 1} data points for {self.num_segments} segments")
        
        # Find optimal boundaries
        optimal_boundaries = self._optimize_boundaries(x, y)
        
        # Fit linear segments
        segments = self._fit_linear_segments(x, y, optimal_boundaries)
        
        # Create continuous function
        spline_func = self._create_spline_function(segments, optimal_boundaries)
        
        result = {
            'fitted_func': spline_func,
            'segments': segments,
            'boundaries': optimal_boundaries,
            'num_segments': self.num_segments,
            'method': 'linear_spline_optimized',
            'params': f'{self.num_segments} segments, optimized boundaries',
            'success': True,
            'rmse': self._calculate_rmse(x, y, spline_func)
        }
        
        print(f"  ✅ Linear spline fitted: {self.num_segments} segments, RMSE={result['rmse']:.6f}")
        return result
    
    def _optimize_boundaries(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Find optimal boundary locations to minimize fitting error
        """
        from scipy.optimize import minimize
        
        # Initial guess: evenly spaced boundaries
        x_min, x_max = x[0], x[-1]
        initial_boundaries = np.linspace(x_min, x_max, self.num_segments + 1)
        
        # Only optimize interior boundaries (keep endpoints fixed)
        initial_interior = initial_boundaries[1:-1]
        
        def objective(interior_boundaries):
            # Reconstruct full boundary array
            boundaries = np.concatenate([[x_min], interior_boundaries, [x_max]])
            boundaries = np.sort(boundaries)  # Ensure sorted
            
            # Fit segments and calculate error
            try:
                segments = self._fit_linear_segments(x, y, boundaries)
                spline_func = self._create_spline_function(segments, boundaries)
                return self._calculate_rmse(x, y, spline_func)
            except:
                return 1e6  # Large penalty for invalid boundaries
        
        # Bounds: interior boundaries must be between endpoints
        bounds = [(x_min + 0.01*(x_max-x_min), x_max - 0.01*(x_max-x_min)) 
                  for _ in range(self.num_segments - 1)]
        
        # Optimize
        result = minimize(objective, initial_interior, bounds=bounds, method='L-BFGS-B')
        
        if result.success:
            optimal_interior = result.x
            optimal_boundaries = np.concatenate([[x_min], optimal_interior, [x_max]])
            optimal_boundaries = np.sort(optimal_boundaries)
        else:
            print("  ⚠️ Optimization failed, using evenly spaced boundaries")
            optimal_boundaries = initial_boundaries
        
        return optimal_boundaries
    
    def _fit_linear_segments(self, x: np.ndarray, y: np.ndarray, 
                           boundaries: np.ndarray) -> List[Dict]:
        """
        Fit linear segments between boundaries
        """
        segments = []
        
        for i in range(self.num_segments):
            x_start, x_end = boundaries[i], boundaries[i+1]
            
            # Find data points in this segment
            mask = (x >= x_start) & (x <= x_end)
            x_seg = x[mask]
            y_seg = y[mask]
            
            if len(x_seg) < 2:
                # Not enough points, use linear interpolation from boundaries
                x_seg = np.array([x_start, x_end])
                y_start = np.interp(x_start, x, y)
                y_end = np.interp(x_end, x, y)
                y_seg = np.array([y_start, y_end])
            
            # Fit linear regression: y = mx + b
            if len(x_seg) >= 2:
                slope, intercept = np.polyfit(x_seg, y_seg, 1)
            else:
                slope, intercept = 0, y_seg[0]
            
            segments.append({
                'x_start': x_start,
                'x_end': x_end,
                'slope': slope,
                'intercept': intercept,
                'n_points': len(x_seg)
            })
        
        return segments
    
    def _create_spline_function(self, segments: List[Dict], 
                              boundaries: np.ndarray) -> Callable:
        """
        Create continuous spline function from segments
        """
        def spline_func(x_eval):
            # Handle both scalar and array inputs
            x_eval = np.atleast_1d(x_eval)
            y_eval = np.zeros_like(x_eval)
            
            for i, seg in enumerate(segments):
                # Find points in this segment
                if i == len(segments) - 1:  # Last segment includes right endpoint
                    mask = (x_eval >= seg['x_start']) & (x_eval <= seg['x_end'])
                else:
                    mask = (x_eval >= seg['x_start']) & (x_eval < seg['x_end'])
                
                # Apply linear function: y = mx + b
                y_eval[mask] = seg['slope'] * x_eval[mask] + seg['intercept']
            
            # Handle points outside range (extrapolate with first/last segment)
            left_mask = x_eval < boundaries[0]
            if np.any(left_mask):
                seg = segments[0]
                y_eval[left_mask] = seg['slope'] * x_eval[left_mask] + seg['intercept']
            
            right_mask = x_eval > boundaries[-1]
            if np.any(right_mask):
                seg = segments[-1]
                y_eval[right_mask] = seg['slope'] * x_eval[right_mask] + seg['intercept']
            
            return y_eval if len(y_eval) > 1 else y_eval[0]
        
        return spline_func
    
    def _calculate_rmse(self, x: np.ndarray, y: np.ndarray, 
                       spline_func: Callable) -> float:
        """
        Calculate root mean square error
        """
        y_pred = spline_func(x)
        return np.sqrt(np.mean((y - y_pred) ** 2))


if __name__ == "__main__":
    print("🚀 GENERALIZED SPLINE UTILITIES TEST")
    print("Testing curve fitting and extrema detection")
    print()
    
    # Test LINEAR SPLINE OPTIMIZER (main feature)
    print("🔧 TESTING LINEAR SPLINE OPTIMIZER")
    print("="*50)
    
    # Create test waveform data
    x, y = create_test_data("sine_wave", n_points=100, noise_level=0.02)
    
    # Test different numbers of segments
    for num_segments in [3, 5, 8]:
        print(f"\n📊 Testing {num_segments}-segment linear spline:")
        optimizer = LinearSplineOptimizer(num_segments=num_segments)
        result = optimizer.fit_linear_spline_optimized(x, y, f"sine_wave_{num_segments}seg")
        
        print(f"   Boundaries: {result['boundaries']}")
        print(f"   RMSE: {result['rmse']:.6f}")
        slopes = [f'slope={seg["slope"]:.3f}' for seg in result['segments']]
        print(f"   Segments: {slopes}")
    
    # Test original complex spline methods for comparison
    print(f"\n🔧 TESTING ORIGINAL COMPLEX METHODS (for comparison)")
    print("="*50)
    detector = SplineExtremaDetector()
    
    for func_type in ["sine_wave"]:  # Just test one
        x, y = create_test_data(func_type, n_points=50, noise_level=0.05)
        
        fitted_curves, extrema_results = detector.analyze_data_with_splines(x, y, func_type)
        
        print(f"\n📊 {func_type.upper()} RESULTS:")
        print(f"   Successful fits: {sum(1 for r in fitted_curves.values() if r.success)}")
        print(f"   Extrema detected: {len(extrema_results)} methods")
    
    print("\n✅ GENERALIZED SPLINE UTILITIES READY!")
    print("Available for use in:")
    print("  • Audio waveform pattern detection")
    print("  • Financial market analysis") 
    print("  • General curve fitting and shape analysis")
    print("🎯 NEW: LinearSplineOptimizer for simple fixed-segment linear splines")
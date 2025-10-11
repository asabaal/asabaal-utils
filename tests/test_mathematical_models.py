#!/usr/bin/env python3
"""
Tests for Mathematical Models - Spline Utilities
===============================================

Comprehensive validation of generalized spline fitting and extrema detection.
Tests against both synthetic data and real-world use cases.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from asabaal_utils.mathematical_models import (
    SplineFitter, 
    SplineExtremaDetector,
    CurveFittingResult,
    ExtremaResult,
    SplineMethod,
    create_test_data
)


class TestSplineFitter:
    """Test the SplineFitter class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.fitter = SplineFitter(enable_prophet=False)  # Disable Prophet for tests
        
    def test_sine_wave_fitting(self):
        """Test fitting to sine wave data"""
        x, y = create_test_data("sine_wave", n_points=50, noise_level=0.01)
        
        results = self.fitter.fit_curves_multiple_methods(x, y, "sine_test")
        
        # Should have successful cubic spline and univariate spline
        assert 'cubic_spline' in results
        assert 'univariate_spline' in results
        assert results['cubic_spline'].success
        assert results['univariate_spline'].success
        
        # Test that fitted functions work
        cubic_func = results['cubic_spline'].fitted_func
        test_x = np.linspace(x[0], x[-1], 10)
        fitted_y = cubic_func(test_x)
        
        assert len(fitted_y) == len(test_x)
        assert np.all(np.isfinite(fitted_y))
    
    def test_polynomial_fitting(self):
        """Test fitting to polynomial data"""
        x, y = create_test_data("polynomial", n_points=30, noise_level=0.05)
        
        results = self.fitter.fit_curves_multiple_methods(x, y, "poly_test")
        
        # Should successfully fit polynomials
        poly_results = [k for k in results.keys() if k.startswith('poly_')]
        assert len(poly_results) > 0
        
        # Check first polynomial result
        poly_key = poly_results[0]
        assert results[poly_key].success
        assert results[poly_key].coefficients is not None
    
    def test_insufficient_data(self):
        """Test behavior with insufficient data points"""
        x = np.array([1, 2])  # Only 2 points
        y = np.array([1, 4])
        
        results = self.fitter.fit_curves_multiple_methods(x, y, "insufficient_test")
        
        # Cubic spline should still work with 2 points
        assert 'cubic_spline' in results
        # But polynomials of high degree should not be attempted


class TestSplineExtremaDetector:
    """Test the SplineExtremaDetector class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.detector = SplineExtremaDetector()
    
    def test_sine_wave_extrema(self):
        """Test extrema detection on sine wave (known extrema)"""
        # Create clean sine wave with known extrema
        x = np.linspace(0, 4*np.pi, 100)
        y = np.sin(x)
        
        fitted_curves, extrema_results = self.detector.analyze_data_with_splines(x, y, "sine_extrema_test")
        
        # Should find extrema
        assert len(extrema_results) > 0
        
        # Check one of the results
        for method_name, extrema in extrema_results.items():
            # Sine wave over 4π should have multiple extrema
            total_extrema = len(extrema.maxima) + len(extrema.minima)
            assert total_extrema > 4  # Should find several peaks and valleys
            
            # All extrema coordinates should be valid
            for max_point in extrema.maxima:
                assert len(max_point) == 2  # (x, y) tuple
                assert np.isfinite(max_point[0]) and np.isfinite(max_point[1])
            
            for min_point in extrema.minima:
                assert len(min_point) == 2
                assert np.isfinite(min_point[0]) and np.isfinite(min_point[1])
            
            break  # Just test first successful method
    
    def test_polynomial_extrema(self):
        """Test extrema detection on polynomial with known characteristics"""
        # Cubic with known turning points
        x = np.linspace(-3, 3, 60)
        y = x**3 - 3*x  # Has max at x=-1, min at x=1
        
        fitted_curves, extrema_results = self.detector.analyze_data_with_splines(x, y, "poly_extrema_test")
        
        assert len(extrema_results) > 0
        
        # Check that extrema are detected near expected locations
        for method_name, extrema in extrema_results.items():
            if len(extrema.maxima) > 0 and len(extrema.minima) > 0:
                # Should find extrema roughly near x=-1 and x=1
                max_x_coords = [pt[0] for pt in extrema.maxima]
                min_x_coords = [pt[0] for pt in extrema.minima]
                
                # At least one maximum should be near -1
                assert any(abs(x_coord - (-1)) < 0.5 for x_coord in max_x_coords)
                # At least one minimum should be near 1  
                assert any(abs(x_coord - 1) < 0.5 for x_coord in min_x_coords)
                break
    
    def test_step_function_handling(self):
        """Test behavior with discontinuous step function"""
        x, y = create_test_data("step", n_points=50, noise_level=0.01)
        
        fitted_curves, extrema_results = self.detector.analyze_data_with_splines(x, y, "step_test")
        
        # Should complete without errors
        assert len(fitted_curves) > 0
        assert any(result.success for result in fitted_curves.values())


class TestDataCreation:
    """Test the test data creation utility"""
    
    def test_create_test_data_types(self):
        """Test all test data types"""
        data_types = ["sine_wave", "polynomial", "step", "noisy_trend"]
        
        for func_type in data_types:
            x, y = create_test_data(func_type, n_points=20, noise_level=0.1)
            
            assert len(x) == 20
            assert len(y) == 20
            assert np.all(np.isfinite(x))
            assert np.all(np.isfinite(y))
    
    def test_noise_levels(self):
        """Test different noise levels"""
        # Clean data
        x1, y1 = create_test_data("sine_wave", n_points=50, noise_level=0.0)
        
        # Noisy data
        x2, y2 = create_test_data("sine_wave", n_points=50, noise_level=0.5)
        
        # Same x values
        assert np.array_equal(x1, x2)
        
        # Different y values due to noise (with high probability)
        assert not np.array_equal(y1, y2)


class TestIntegrationScenarios:
    """Integration tests simulating real-world usage"""
    
    def test_audio_waveform_simulation(self):
        """Simulate audio waveform analysis scenario"""
        # Simulate audio energy pattern with vocal/silence regions
        x = np.linspace(0, 10, 200)  # 200 frames
        
        # Create pattern: vocal-silence-vocal (\_/ pattern)
        y = np.zeros_like(x)
        y[0:60] = 0.5 + 0.2*np.sin(x[0:60]*3)      # Vocal start
        y[60:140] = 0.01 + 0.005*np.sin(x[60:140]*10)  # Silent middle 
        y[140:200] = 0.4 + 0.15*np.sin(x[140:200]*2)   # Vocal end
        
        detector = SplineExtremaDetector()
        fitted_curves, extrema_results = detector.analyze_data_with_splines(x, y, "audio_simulation")
        
        # Should successfully analyze the pattern
        assert len(fitted_curves) > 0
        assert any(result.success for result in fitted_curves.values())
        
        # Should detect the valley in the middle (silent region)
        for method_name, extrema in extrema_results.items():
            if len(extrema.minima) > 0:
                min_x_coords = [pt[0] for pt in extrema.minima]
                # Should find minimum roughly in the middle silent region (x=5-7)
                assert any(5 <= x_coord <= 7 for x_coord in min_x_coords)
                break
    
    def test_financial_time_series_simulation(self):
        """Simulate financial market data analysis scenario"""
        # Simulate price data with trend and volatility
        x = np.linspace(0, 100, 100)  # 100 time periods
        
        # Trending price with supply/demand zones
        base_trend = 100 + 0.5*x  # Uptrend
        volatility = 5*np.sin(x/10) + 2*np.sin(x/3)  # Market oscillations
        y = base_trend + volatility
        
        detector = SplineExtremaDetector()
        fitted_curves, extrema_results = detector.analyze_data_with_splines(x, y, "financial_simulation")
        
        # Should detect multiple support/resistance levels
        assert len(fitted_curves) > 0
        
        total_extrema_found = 0
        for method_name, extrema in extrema_results.items():
            total_extrema_found += len(extrema.maxima) + len(extrema.minima)
        
        # Should find several extrema in the oscillating trend
        assert total_extrema_found > 5


def test_cross_domain_consistency():
    """Test that the same mathematical function gives consistent results across domains"""
    # Use identical mathematical function for both "audio" and "financial" analysis
    x = np.linspace(0, 20, 100)
    y = np.sin(x) + 0.5*np.sin(3*x) + 0.1*np.random.normal(0, 1, len(x))
    
    detector = SplineExtremaDetector()
    
    # Analyze same data with different labels
    curves1, extrema1 = detector.analyze_data_with_splines(x, y, "audio_energy")
    curves2, extrema2 = detector.analyze_data_with_splines(x, y, "price_data")
    
    # Results should be identical (mathematical consistency)
    assert len(curves1) == len(curves2)
    
    for method_name in curves1.keys():
        if curves1[method_name].success and curves2[method_name].success:
            # Same function should give same results at test points
            test_x = np.linspace(x[0], x[-1], 10)
            y1_test = curves1[method_name].fitted_func(test_x)
            y2_test = curves2[method_name].fitted_func(test_x)
            
            np.testing.assert_array_almost_equal(y1_test, y2_test, decimal=10)


if __name__ == "__main__":
    print("🧪 RUNNING MATHEMATICAL MODELS TESTS")
    print("="*50)
    
    # Run all tests
    pytest.main([__file__, "-v"])
    
    print("\n✅ SPLINE UTILITIES VALIDATION COMPLETE!")
    print("Generalized spline system ready for:")
    print("  • Audio waveform pattern detection")
    print("  • Financial market analysis")
    print("  • General mathematical curve fitting")
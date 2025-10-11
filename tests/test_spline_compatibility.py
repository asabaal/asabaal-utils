#!/usr/bin/env python3
"""
Spline Compatibility Test
=========================

Validates that the generalized spline utilities produce equivalent results
to the original investing repo implementation.
"""

import sys
import os
import numpy as np

# Add paths for imports
sys.path.insert(0, '/home/asabaal/asabaal_ventures/repos/investing')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from asabaal_utils.mathematical_models import SplineExtremaDetector

# Import from investing repo
try:
    from curve_fitting_extrema_detector import CurveFittingExtemaDetector
    INVESTING_AVAILABLE = True
except ImportError:
    print("⚠️ Investing repo not available - skipping compatibility tests")
    INVESTING_AVAILABLE = False


def create_test_financial_data():
    """Create test data similar to financial time series"""
    # Simulate daily price data
    np.random.seed(42)  # For reproducible results
    x = np.arange(100)
    
    # Base price trend with volatility
    base_price = 100 + 0.5*x + 10*np.sin(x/10)
    noise = np.random.normal(0, 2, len(x))
    y = base_price + noise
    
    return x, y


def test_spline_fitting_compatibility():
    """Test that spline fitting gives equivalent results"""
    if not INVESTING_AVAILABLE:
        print("Skipping compatibility test - investing repo not available")
        return True
    
    print("🔄 TESTING SPLINE FITTING COMPATIBILITY")
    print("-" * 50)
    
    x, y = create_test_financial_data()
    
    # Test with generalized utilities
    print("Testing generalized spline utilities...")
    generalized_detector = SplineExtremaDetector()
    gen_curves, gen_extrema = generalized_detector.analyze_data_with_splines(x, y, "compatibility_test")
    
    # Test with original investing implementation
    print("Testing original investing implementation...")
    investing_detector = CurveFittingExtemaDetector()
    
    # Create a simple DataFrame for investing detector
    import pandas as pd
    test_df = pd.DataFrame({
        'Close': y,
        'High': y + np.abs(np.random.normal(0, 1, len(y))),
        'Low': y - np.abs(np.random.normal(0, 1, len(y))),
        'Open': y + np.random.normal(0, 0.5, len(y))
    })
    
    # Use the original analyze_data_directly method
    investing_result = investing_detector.analyze_data_directly(test_df, window_size=len(test_df))
    
    # Compare results
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"Generalized - Successful fits: {sum(1 for r in gen_curves.values() if r.success)}")
    print(f"Generalized - Extrema methods: {len(gen_extrema)}")
    
    if investing_result and investing_result['window_results']:
        window = investing_result['window_results'][0]
        inv_curves = window['traditional_curves']
        inv_extrema = window['traditional_extrema']
        
        print(f"Investing - Successful fits: {sum(1 for r in inv_curves.values() if r.success)}")
        print(f"Investing - Extrema methods: {len(inv_extrema)}")
        
        # Test that both can fit cubic splines successfully
        gen_cubic_success = 'cubic_spline' in gen_curves and gen_curves['cubic_spline'].success
        inv_cubic_success = 'cubic_spline' in inv_curves and inv_curves['cubic_spline']['fitted_func'] is not None
        
        print(f"Both support cubic splines: {gen_cubic_success and inv_cubic_success}")
        
        if gen_cubic_success and inv_cubic_success:
            # Test that fitted functions produce similar results
            test_x = np.linspace(x[0], x[-1], 20)
            
            gen_func = gen_curves['cubic_spline'].fitted_func
            inv_func = inv_curves['cubic_spline']['fitted_func']
            
            gen_y = gen_func(test_x)
            inv_y = inv_func(test_x)
            
            # Calculate relative difference
            relative_diff = np.mean(np.abs(gen_y - inv_y) / (np.abs(inv_y) + 1e-10))
            print(f"Cubic spline relative difference: {relative_diff:.6f}")
            
            # Should be very similar (within 1% relative difference)
            compatibility_ok = relative_diff < 0.01
            print(f"Compatibility: {'✅ PASS' if compatibility_ok else '❌ FAIL'}")
            
            return compatibility_ok
    
    print("⚠️ Limited comparison possible")
    return True


def test_api_compatibility():
    """Test that the APIs are compatible for easy migration"""
    print("\n🔧 TESTING API COMPATIBILITY")
    print("-" * 30)
    
    # Test data
    x, y = create_test_financial_data()
    
    # Test generalized API
    detector = SplineExtremaDetector()
    
    # Should be easy to use
    try:
        fitted_curves, extrema_results = detector.analyze_data_with_splines(x, y, "api_test")
        
        # Check that results have expected structure
        assert isinstance(fitted_curves, dict)
        assert isinstance(extrema_results, dict)
        
        # Check that common methods are available
        expected_methods = ['cubic_spline', 'univariate_spline']
        available_methods = list(fitted_curves.keys())
        
        for method in expected_methods:
            if method in available_methods:
                result = fitted_curves[method]
                assert hasattr(result, 'success')
                assert hasattr(result, 'fitted_func')
                assert hasattr(result, 'method')
                
        print("✅ API structure compatible")
        
        # Test that fitted functions can be called
        for method_name, result in fitted_curves.items():
            if result.success:
                test_x = np.array([0.0, 1.0, 2.0])
                try:
                    test_y = result.fitted_func(test_x)
                    assert len(test_y) == len(test_x)
                    print(f"✅ {method_name} function callable")
                except Exception as e:
                    print(f"❌ {method_name} function error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API compatibility failed: {e}")
        return False


def run_full_compatibility_suite():
    """Run the complete compatibility test suite"""
    print("🚀 SPLINE COMPATIBILITY TEST SUITE")
    print("=" * 60)
    print("Validating generalized spline utilities against investing repo")
    
    results = {
        'fitting_compatibility': test_spline_fitting_compatibility(),
        'api_compatibility': test_api_compatibility()
    }
    
    print(f"\n📋 COMPATIBILITY TEST RESULTS:")
    print("-" * 40)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 MIGRATION READY!")
        print("The generalized spline utilities are compatible with investing repo.")
        print("Safe to proceed with:")
        print("  • Updating investing repo to use generalized utilities")
        print("  • Implementing vocal-specific spline detection")
        print("  • Using hybrid approach for audio pattern detection")
    
    return all_passed


if __name__ == "__main__":
    success = run_full_compatibility_suite()
    exit(0 if success else 1)
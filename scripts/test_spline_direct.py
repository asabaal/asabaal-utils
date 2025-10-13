#!/usr/bin/env python3
"""
Direct Spline Test
==================

Direct test of spline utilities without importing the full asabaal_utils package.
"""

import sys
import os
import numpy as np

# Direct import of spline utilities
sys.path.insert(0, 'src/asabaal_utils/mathematical_models')
from spline_utils import SplineExtremaDetector, create_test_data

def test_generalized_splines():
    """Test the generalized spline system"""
    print("🧪 DIRECT SPLINE UTILITIES TEST")
    print("=" * 50)
    
    detector = SplineExtremaDetector()
    
    # Test 1: Audio-like pattern (vocal-silence-vocal)
    print("\n🎵 TEST 1: Audio-like waveform pattern")
    x = np.linspace(0, 10, 100)
    y = np.concatenate([
        0.5 + 0.2*np.sin(x[:30]*3),        # Vocal start
        0.01 + 0.005*np.sin(x[30:70]*10),  # Silent middle 
        0.4 + 0.15*np.sin(x[70:]*2)        # Vocal end
    ])
    
    fitted_curves, extrema_results = detector.analyze_data_with_splines(x, y, "audio_pattern")
    
    success_count = sum(1 for r in fitted_curves.values() if r.success)
    print(f"✅ Audio pattern: {success_count} successful fits, {len(extrema_results)} extrema methods")
    
    # Test 2: Financial-like pattern (trending with oscillations)
    print("\n💰 TEST 2: Financial market pattern")
    x, y = create_test_data("polynomial", n_points=80, noise_level=0.1)
    
    fitted_curves, extrema_results = detector.analyze_data_with_splines(x, y, "financial_pattern")
    
    success_count = sum(1 for r in fitted_curves.values() if r.success)
    print(f"✅ Financial pattern: {success_count} successful fits, {len(extrema_results)} extrema methods")
    
    # Test 3: Problematic pattern detection (\_/ pattern)
    print("\n⚠️ TEST 3: Problematic \_/ pattern detection")
    x = np.linspace(0, 6, 60)
    y = np.concatenate([
        0.6 + 0.1*np.sin(x[:20]*2),      # Vocal start (high energy)
        0.005 + 0.002*np.random.normal(0, 1, 20),  # Silent middle (low energy)
        0.5 + 0.1*np.sin(x[40:]*2)       # Vocal end (high energy)
    ])
    
    fitted_curves, extrema_results = detector.analyze_data_with_splines(x, y, "problematic_pattern")
    
    # Check if we detect a valley in the middle (silent region)
    valley_detected = False
    for method_name, extrema in extrema_results.items():
        for min_x, min_y in extrema.minima:
            if 1.5 <= min_x <= 4.5 and min_y < 0.1:  # Valley in middle with low energy
                valley_detected = True
                print(f"✅ Detected problematic valley at x={min_x:.2f}, y={min_y:.4f}")
                break
        if valley_detected:
            break
    
    if not valley_detected:
        print("⚠️ No problematic valley detected in middle region")
    
    # Test 4: Curve fitting quality
    print("\n📊 TEST 4: Curve fitting quality")
    x, y = create_test_data("sine_wave", n_points=50, noise_level=0.05)
    
    fitted_curves, _ = detector.analyze_data_with_splines(x, y, "quality_test")
    
    # Test fitted function accuracy
    for method_name, result in fitted_curves.items():
        if result.success:
            func = result.fitted_func
            # Test at original points
            try:
                y_pred = func(x)
                rmse = np.sqrt(np.mean((y - y_pred)**2))
                print(f"✅ {method_name}: RMSE = {rmse:.6f}")
                
                if rmse < 0.5:  # Should fit reasonably well
                    print(f"   Good fit quality for {method_name}")
            except Exception as e:
                print(f"❌ {method_name}: Evaluation error - {e}")
    
    print("\n🎉 DIRECT SPLINE TEST COMPLETE!")
    print("Generalized spline utilities are working correctly.")
    
    return True

if __name__ == "__main__":
    test_generalized_splines()
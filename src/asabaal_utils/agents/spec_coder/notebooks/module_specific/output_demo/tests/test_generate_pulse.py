import pytest
import numpy as np
from unittest.mock import patch, MagicMock
# Assuming the function is in a module called pulse_generator
from pulse_generator import generate_pulse
def test_generate_pulse_basic_functionality():
    """Test basic pulse generation with valid parameters"""
    result = generate_pulse(bpm=120, duration=2.0)
    # Should return a list or array
    assert isinstance(result, (list, np.ndarray))
    assert len(result) > 0
    # Should contain only 0s and 1s
    assert all(x in [0, 1] for x in result)
    # Should have correct duration (approximately)
    expected_length = int(120 * 2.0 / 60)  # 4 beats at 120 BPM
    assert len(result) >= expected_length - 1
    assert len(result) <= expected_length + 1
def test_generate_pulse_different_bpm():
    """Test pulse generation with different BPM values"""
    result_60 = generate_pulse(bpm=60, duration=1.0)
    result_180 = generate_pulse(bpm=180, duration=1.0)
    # Higher BPM should result in more pulses
    assert len(result_180) >= len(result_60)
def test_generate_pulse_different_duration():
    """Test pulse generation with different durations"""
    result_short = generate_pulse(bpm=120, duration=0.5)
    result_long = generate_pulse(bpm=120, duration=2.0)
    # Longer duration should result in more pulses
    assert len(result_long) >= len(result_short)
def test_generate_pulse_edge_cases():
    """Test edge cases for pulse generation"""
    # Zero duration
    result = generate_pulse(bpm=120, duration=0.0)
    assert len(result) == 0
    # Very short duration
    result = generate_pulse(bpm=120, duration=0.001)
    assert len(result) >= 0
    # Very high BPM
    result = generate_pulse(bpm=1000, duration=1.0)
    assert isinstance(result, (list, np.ndarray))
    assert all(x in [0, 1] for x in result)
def test_generate_pulse_type_safety():
    """Test type safety of parameters"""
    # Test with integer BPM
    result = generate_pulse(bpm=120, duration=2.0)
    assert isinstance(result, (list, np.ndarray))
    # Test with float BPM
    result = generate_pulse(bpm=120.5, duration=2.0)
    assert isinstance(result, (list, np.ndarray))
    # Test with integer duration
    result = generate_pulse(bpm=120, duration=2)
    assert isinstance(result, (list, np.ndarray))
def test_generate_pulse_invalid_parameters():
    """Test invalid parameter handling"""
    # Negative BPM
    with pytest.raises(ValueError):
        generate_pulse(bpm=-10, duration=1.0)
    # Negative duration
    with pytest.raises(ValueError):
        generate_pulse(bpm=120, duration=-1.0)
    # Zero BPM
    with pytest.raises(ValueError):
        generate_pulse(bpm=0, duration=1.0)
def test_generate_pulse_invalid_types():
    """Test invalid parameter types"""
    # Invalid BPM type
    with pytest.raises(TypeError):
        generate_pulse(bpm="120", duration=1.0)
    with pytest.raises(TypeError):
        generate_pulse(bpm=None, duration=1.0)
    # Invalid duration type
    with pytest.raises(TypeError):
        generate_pulse(bpm=120, duration="1.0")
    with pytest.raises(TypeError):
        generate_pulse(bpm=120, duration=None)
def test_generate_pulse_precision():
    """Test precision of pulse generation"""
    result = generate_pulse(bpm=120, duration=1.5)
    # Should be approximately correct
    expected_beats = 120 * 1.5 / 60  # 3 beats
    assert len(result) >= 2  # At least 2 pulses
    assert len(result) <= 4  # At most 4 pulses
def test_generate_pulse_consistency():
    """Test that same parameters produce consistent results"""
    result1 = generate_pulse(bpm=120, duration=2.0)
    result2 = generate_pulse(bpm=120, duration=2.0)
    # Results should be identical for same inputs
    assert len(result1) == len(result2)
    assert all(a == b for a, b in zip(result1, result2))
def test_generate_pulse_with_numpy_array_output():
    """Test that function can return numpy arrays when requested"""
    # Mock the function to return numpy array
    with patch('pulse_generator.numpy.array') as mock_array:
        mock_array.return_value = np.array([1, 0, 1, 0])
        result = generate_pulse(bpm=120, duration=1.0)
        assert isinstance(result, np.ndarray)
def test_generate_pulse_with_custom_parameters():
    """Test with custom parameters that should work"""
    # Test with various combinations
    test_cases = [
        (60, 1.0),
        (180, 0.5),
        (120, 3.0),
        (80, 2.5),
        (240, 0.25)
    ]
    for bpm, duration in test_cases:
        result = generate_pulse(bpm=bpm, duration=duration)
        assert isinstance(result, (list, np.ndarray))
        assert all(x in [0, 1] for x in result)
        assert len(result) >= 0
def test_generate_pulse_large_duration():
    """Test with large duration values"""
    result = generate_pulse(bpm=120, duration=100.0)
    assert isinstance(result, (list, np.ndarray))
    assert len(result) > 0
    assert all(x in [0, 1] for x in result)
def test_generate_pulse_very_high_bpm():
    """Test with very high BPM values"""
    result = generate_pulse(bpm=10000, duration=0.1)
    assert isinstance(result, (list, np.ndarray))
    assert all(x in [0, 1] for x in result)
    assert len(result) >= 0
def test_generate_pulse_zero_duration():
    """Test with zero duration specifically"""
    result = generate_pulse(bpm=120, duration=0.0)
    assert isinstance(result, (list, np.ndarray))
    assert len(result) == 0
def test_generate_pulse_single_beat():
    """Test with duration equal to one beat"""
    result = generate_pulse(bpm=120, duration=0.5)  # 0.5 seconds = 1 beat at 120 BPM
    assert isinstance(result, (list, np.ndarray))
    assert len(result) >= 0
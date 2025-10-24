```python
import pytest
from your_module import generate_time_grid, apply_accent_pattern, export_as_midi

def test_generate_time_grid_happy_path():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    assert len(time_grid) > 0
    for timestamp in time_grid:
        assert isinstance(timestamp, float)

def test_generate_time_grid_edge_cases():
    tempo_bpm = -1.0
    with pytest.raises(ValueError):
        generate_time_grid(tempo_bpm, 10.0)
    
    tempo_bpm = 1000000.0
    with pytest.raises(OverflowError):
        generate_time_grid(tempo_bpm, 10.0)

def test_apply_accent_pattern_happy_path():
    time_grid = [1.0, 2.0, 3.0]
    pattern = [1, 0, 1]
    result = apply_accent_pattern(time_grid, pattern)
    assert len(result) == len(time_grid)
    for timestamp, accent in result:
        assert isinstance(timestamp, float)
        assert isinstance(accent, int)

def test_apply_accent_pattern_edge_cases():
    time_grid = [1.0, 2.0, 3.0]
    pattern = [-1]  # invalid value
    with pytest.raises(ValueError):
        apply_accent_pattern(time_grid, pattern)
    
    time_grid = [1.0, 2.0, 3.0]
    pattern = ['a']  # non-integer value
    with pytest.raises(TypeError):
        apply_accent_pattern(time_grid, pattern)

def test_export_as_midi_happy_path():
    time_grid = [1.0, 2.0, 3.0]
    accents = [(1.0, 1), (2.0, 0)]
    outfile = 'test.mid'
    assert export_as_midi(time_grid, accents, outfile) == True

def test_export_as_midi_edge_cases():
    time_grid = [1.0, 2.0, 3.0]
    accents = [(1.0, -1)]  # invalid accent value
    with pytest.raises(ValueError):
        export_as_midi(time_grid, accents, 'test.mid')
    
    time_grid = [1.0, 2.0, 3.0]
    accents = [('a', 1)]  # non-numeric timestamp
    with pytest.raises(TypeError):
        export_as_midi(time_grid, accents, 'test.mid')

def test_export_as_midi_invalid_outfile():
    time_grid = [1.0, 2.0, 3.0]
    accents = [(1.0, 1), (2.0, 0)]
    outfile = None
    with pytest.raises(TypeError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_type():
    time_grid = [1.0, 2.0, 3.0]
    accents = [(1.0, 1), (2.0, 0)]
    outfile = 123
    with pytest.raises(TypeError):
        export_as_midi(time_grid, accents, outfile)
```
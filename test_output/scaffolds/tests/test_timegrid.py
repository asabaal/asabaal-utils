```python
import pytest
from unittest.mock import patch, MagicMock
import math
import os

def test_generate_time_grid_happy_path():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    assert len(time_grid) > 0
    assert all(isinstance(t, float) for t in time_grid)

def test_generate_time_grid_zero_duration():
    tempo_bpm = 120.0
    duration_sec = 0.0
    with pytest.raises(ValueError):
        generate_time_grid(tempo_bpm, duration_sec)

def test_generate_time_grid_negative_tempo():
    tempo_bpm = -1.0
    duration_sec = 10.0
    with pytest.raises(ValueError):
        generate_time_grid(tempo_bpm, duration_sec)

def test_apply_accent_pattern_happy_path():
    time_grid = [1.0, 2.0, 3.0]
    pattern = [1, 0, 1]
    accents = apply_accent_pattern(time_grid, pattern)
    assert len(accents) == len(time_grid)
    assert all(isinstance(a, tuple) and len(a) == 2 for a in accents)

def test_apply_accent_pattern_invalid_pattern():
    time_grid = [1.0, 2.0, 3.0]
    pattern = ['a', 'b', 'c']
    with pytest.raises(ValueError):
        apply_accent_pattern(time_grid, pattern)

def test_export_as_midi_happy_path(tmpdir):
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = os.path.join(str(tmpdir), 'test.mid')
    assert export_as_midi(time_grid, accents, outfile) is True

def test_export_as_midi_invalid_outfile():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'invalid_file'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_accents():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = [(1.0, 'a'), (2.0, 1)]
    outfile = os.path.join(str(tmpdir), 'test.mid')
    with pytest.raises(TypeError):
        export_as_midi(time_grid, accents, outfile)

def test_generate_time_grid_type_safety():
    tempo_bpm = 120
    duration_sec = 10.0
    with pytest.raises(TypeError):
        generate_time_grid(tempo_bpm, duration_sec)
```
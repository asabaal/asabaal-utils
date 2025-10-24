```python
import pytest
from unittest.mock import patch, MagicMock
import os

def test_generate_time_grid_happy_path():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    assert len(time_grid) > 0
    assert all(isinstance(timestamp, float) for timestamp in time_grid)

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
    assert all(isinstance(accent, tuple) and len(accent) == 2 for accent in accents)

def test_apply_accent_pattern_invalid_pattern():
    time_grid = [1.0, 2.0, 3.0]
    pattern = ['a', 'b', 'c']
    with pytest.raises(TypeError):
        apply_accent_pattern(time_grid, pattern)

def test_export_as_midi_happy_path(tmpdir):
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = os.path.join(tmpdir, 'test.mid')
    assert export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'invalid_outfile'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_time_grid():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = None
    accents = apply_accent_pattern([1.0, 2.0, 3.0], [1, 0, 1])
    with pytest.raises(TypeError):
        export_as_midi(time_grid, accents, 'test.mid')

def test_export_as_midi_invalid_accents():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = None
    with pytest.raises(TypeError):
        export_as_midi(time_grid, accents, 'test.mid')

def test_export_as_midi_invalid_outfile_type():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 12345
    with pytest.raises(TypeError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_path():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = '/invalid/path'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_name():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'invalid name'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_extension():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_mode():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_encoding():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_permissions():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_owner():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_group():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_atime():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_mtime():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_ctime():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_atime_nsec():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_mtime_nsec():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_ctime_nsec():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_bpm, duration_sec)
    accents = apply_accent_pattern(time_grid, [1, 0, 1])
    outfile = 'test.mid'
    with pytest.raises(FileNotFoundError):
        export_as_midi(time_grid, accents, outfile)

def test_export_as_midi_invalid_outfile_dev():
    tempo_bpm = 120.0
    duration_sec = 10.0
    time_grid = generate_time_grid(tempo_b
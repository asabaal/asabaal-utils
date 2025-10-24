**Rhythmic Pulse Generator**
==========================

### Project Overview

The Rhythmic Pulse Generator is a Python library designed to generate rhythmic data and export it as MIDI files.

### Installation Instructions

```bash
pip install rhythmic-pulse-generator
```

### Usage Examples

#### Generate Time Grid
```python
from rhythmic_pulse_generator import TimeGridGenerator

generator = TimeGridGenerator(tempo=120, duration=10)
time_grid = generator.generate_time_grid()
print(time_grid)
```

#### Apply Accent Pattern
```python
from rhythmic_pulse_generator import AccentPatternApplier

applier = AccentPatternApplier(pattern=[1, 0, 1, 1])
accented_time_grid = applier.apply_accent_pattern(time_grid)
print(accented_time_grid)
```

#### Export as MIDI
```python
from rhythmic_pulse_generator import MIDIEncoder

encoder = MIDIEncoder()
midi_data = encoder.encode(accented_time_grid)
with open('output.mid', 'wb') as f:
    f.write(midi_data)
```

### API Documentation

#### TimeGridGenerator

* `generate_time_grid(tempo, duration)`: Generate a deterministic sequence of beat timestamps.
	+ Parameters: `tempo` (int), `duration` (float)
	+ Returns: list of timestamps
* `validate_time_grid(time_grid)`: Validate the generated time grid.
	+ Parameters: list of timestamps
	+ Returns: None

#### AccentPatternApplier

* `apply_accent_pattern(pattern, time_grid)`: Overlay a binary pattern over the generated time grid.
	+ Parameters: list of integers (pattern), list of timestamps (time_grid)
	+ Returns: list of tuples (timestamp, accent)

#### MIDIEncoder

* `encode(time_grid)`: Convert rhythmic data into a valid MIDI file.
	+ Parameters: list of tuples (timestamp, accent)
	+ Returns: bytes object representing the MIDI file

### Requirements Traceability

| Requirement ID | Description |
| --- | --- |
| RPG-001 | Generate Time Grid |
| RPG-002 | Apply Accent Pattern |
| RPG-003 | Export as MIDI |

**Unit Tests**

* `test_timegrid.py`: Unit tests for TimeGridGenerator
* `test_accents.py`: Unit tests for AccentPatternApplier
* `test_midi_export.py`: Unit tests for MIDIEncoder
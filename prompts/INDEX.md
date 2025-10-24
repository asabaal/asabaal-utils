# Function Prompts Index

This file lists all available function prompts organized by category.

## Creation

- [generate_time_grid.prompt](generate_time_grid.prompt) - The function should produce a non-empty list of time grid timestamps when given valid tempo, duration, and time grid parameters. (Tests: 4, Alignment: 0.00)
- [generate_time_grid_zero_duration.prompt](generate_time_grid_zero_duration.prompt) - The function should handle zero duration inputs gracefully, likely by raising an exception or returning an empty result. (Tests: 1, Alignment: 0.00)
- [generate_time_grid_negative_tempo.prompt](generate_time_grid_negative_tempo.prompt) - The function should handle negative tempo values by raising an exception, ensuring tempo is always positive. (Tests: 1, Alignment: 0.00)

## Utility

- [apply_accent_pattern.prompt](apply_accent_pattern.prompt) - The function must process a time grid and accent pattern to produce a structured output where each timestamp is a float and each accent value is an integer. (Tests: 3, Alignment: 0.00)
- [apply_accent_pattern_pattern.prompt](apply_accent_pattern_pattern.prompt) - The function should raise an exception when given an invalid pattern, specifically when the pattern contains elements that cannot be processed correctly. (Tests: 1, Alignment: 0.00)

## Export

- [export_as_midi.prompt](export_as_midi.prompt) - The function must process time grid and accent data to generate a valid MIDI file and return True upon successful completion. (Tests: 3, Alignment: 0.00)
- [export_as_midi_outfile.prompt](export_as_midi_outfile.prompt) - The function should raise an exception when attempting to export MIDI data with a None outfile parameter, ensuring proper error handling for invalid output destinations. (Tests: 3, Alignment: 0.00)
- [export_as_midi_accents.prompt](export_as_midi_accents.prompt) - The function should process time grid generation with accent markers, handling invalid accent specifications gracefully by raising an exception. (Tests: 1, Alignment: 0.00)


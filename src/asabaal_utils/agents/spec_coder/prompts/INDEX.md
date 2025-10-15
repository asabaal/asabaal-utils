# Function Prompts Index

This file lists all available function prompts organized by category.

## Creation

- [generate_time_grid.prompt](generate_time_grid.prompt) - The function must produce a non-empty list of floating-point timestamps representing evenly spaced beats for a given tempo and duration. (Tests: 5, Alignment: 0.90)
- [generate_time_grid_zero_tempo.prompt](generate_time_grid_zero_tempo.prompt) - The function should handle edge cases like zero tempo by raising an exception, ensuring the time grid generation process fails gracefully when given invalid tempo values. (Tests: 1, Alignment: 0.00)
- [generate_time_grid_negative_tempo.prompt](generate_time_grid_negative_tempo.prompt) - The function should reject negative tempo values and raise an exception to enforce valid tempo constraints. (Tests: 1, Alignment: 0.00)

## Utility

- [apply_accent_pattern.prompt](apply_accent_pattern.prompt) - The function must pair each time grid timestamp with a corresponding accent value from the binary pattern, ensuring the output maintains the same length as the input time grid and that each element is a tuple containing a float timestamp and an integer accent value. (Tests: 5, Alignment: 0.00)

## Export

- [export_as_midi.prompt](export_as_midi.prompt) - The function must successfully convert rhythmic data into a valid MIDI file format and return a boolean true value upon successful completion. (Tests: 7, Alignment: 0.00)
- [export_as_midi_time_grid.prompt](export_as_midi_time_grid.prompt) - The function must validate that the time grid contains valid timestamp values and raise an exception when invalid data is provided. (Tests: 2, Alignment: 0.00)
- [export_as_midi_accents.prompt](export_as_midi_accents.prompt) - The function must validate that accents data matches the time grid and raise an exception when there is a mismatch in the number of accents or invalid accent values. (Tests: 1, Alignment: 0.00)
- [export_as_midi_outfile.prompt](export_as_midi_outfile.prompt) - The function must validate the output file path parameter and raise an exception when it is invalid or cannot be written to. (Tests: 2, Alignment: 0.00)

## Validation

- [apply_accent_pattern_pattern.prompt](apply_accent_pattern_pattern.prompt) - The function must validate that the accent pattern matches the length of the time grid and raise an exception when there is a mismatch. (Tests: 1, Alignment: 0.00)


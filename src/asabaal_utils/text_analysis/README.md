# Syllable Counter

A utility for analyzing syllable counts in song lyrics.

## Installation

Ensure you have the required dependencies:

```bash
pip install nltk
```

For first-time use, you may need to download the CMU Pronunciation Dictionary:

```python
import nltk
nltk.download('cmudict')
```

Or let the tool automatically download it when first used.

## Usage

### Command Line

The syllable counter is accessible via the command line once installed:

```bash
# Basic usage - prints analysis to console
syllable-counter lyrics.txt

# Export results to CSV
syllable-counter lyrics.txt --csv

# Export both results and statistics to CSV
syllable-counter lyrics.txt --csv --stats-csv

# Specify custom output paths
syllable-counter lyrics.txt --csv --output custom_output.csv --stats-csv --stats-output statistics.csv

# Disable section detection
syllable-counter lyrics.txt --no-sections

# Suppress console output (useful when just generating CSVs)
syllable-counter lyrics.txt --csv --quiet
```

### Python API

You can also use the syllable counter in your Python code:

```python
from asabaal_utils.text_analysis.syllable_counter import (
    analyze_lyrics_file,
    print_analysis,
    calculate_statistics,
    detect_sections,
    export_to_csv
)

# Basic analysis
results = analyze_lyrics_file("lyrics.txt")

# Detect sections (e.g., Verse, Chorus)
sections = detect_sections(results)

# Print analysis to console
print_analysis(results, sections)

# Calculate and print statistics
calculate_statistics(results, sections)

# Export to CSV
export_to_csv(results, sections, "output.csv")
```

## CSV Output Format

The tool can generate two types of CSV files:

### Main Results CSV

Contains the raw syllable count data with the following columns:

- Line Number
- Section (if section detection is enabled)
- Line
- Syllables

### Statistics CSV

Contains the statistical analysis of syllable counts:

- Overall statistics (total lines, average, min, max)
- Section-by-section statistics (if section detection is enabled)
- Potential rhythm issues (lines with significantly more syllables than average)

## Preparing Your Lyrics File

For best results with section detection, use standard section markers in your lyrics file:

```
[Verse 1]
Mourning, death, crying, pain
Passed away is the order of old

[Chorus]
Do you see it?
Have you opened your eyes?
```

The following section markers are automatically recognized:
- [Section]
- Verse or Verse 1:
- Chorus or Chorus:
- Bridge or Bridge:
- Intro or Intro:
- Outro or Outro:
- Pre-Chorus or Prechorus:
- Hook or Hook:

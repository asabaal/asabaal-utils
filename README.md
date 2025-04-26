# asabaal-utils

A collection of personal utilities for asabaal.

## Video Processing Utilities

Tools to speed up video editing workflows by automating common tasks.

### Silence Detection and Removal

Automatically detects and removes silent/near-silent portions of videos to create tighter, more engaging content.

#### Features:

- Adjustable silence threshold to accommodate different recording environments
- Customizable minimum silence duration to avoid choppy editing
- Padding controls to ensure smooth transitions
- Supports large video files (multiple GB)
- Advanced audio analysis with aggressive silence detection option

#### Installation

```bash
# Clone the repository
git clone https://github.com/asabaal/asabaal-utils.git
cd asabaal-utils

# Install with development dependencies
pip install -e .
```

#### Usage

```bash
# Command-line usage
remove-silence input.mp4 output.mp4 --threshold-db -45 --min-silence 0.7

# Import and use in your own Python scripts
from asabaal_utils.video_processing import remove_silence

remove_silence(
    "input.mp4",
    "output.mp4",
    threshold_db=-40.0,
    min_silence_duration=0.5,
    min_sound_duration=0.3,
    padding=0.1
)
```

### Transcript Analysis for Intelligent Clip Splitting

Analyzes video transcripts (such as those from CapCut) to suggest optimal points to split your videos into coherent clips.

#### Features:

- Topic change detection using NLP techniques
- Speaker change detection
- Identifies natural break points in speech
- Handles CapCut and custom JSON transcript formats
- Configurable minimum and maximum clip durations

#### Usage

```bash
# Command-line usage
analyze-transcript transcript.txt --output-file suggestions.json --min-clip-duration 15 --max-clip-duration 90

# Import and use in your own Python scripts
from asabaal_utils.video_processing import analyze_transcript

suggestions = analyze_transcript(
    "transcript.txt",
    output_file="suggestions.json",
    transcript_format="capcut",
    min_clip_duration=10.0,
    max_clip_duration=60.0
)
```

## Budget Utility

A command-line utility to help manage monthly budgets and projections.

### Installation

```bash
# Clone the repository
git clone https://github.com/asabaal/asabaal-utils.git
cd asabaal-utils

# Install dependencies
npm install
```

### Usage

```bash
# Start the budget utility
npm start

# Or use the shorthand command
npm run budget
```

#### Helper Commands

```bash
# Generate sample data
npm run sample

# Load sample data into the application
npm run load-sample

# Backup your data
npm run backup

# Clean/reset your data
npm run clean
```

### Quick Start with Sample Data

To quickly get started with sample data:

```bash
# Generate sample data
npm run sample

# Load the sample data into the application
npm run load-sample

# Run the application
npm start
```

### Features

- Clean month-by-month view of budget data
- Space for projections of upcoming months
- Calculation of surplus/deficit
- Category-based spending tracking
- Import/export functionality

### Data Privacy and Storage

All data is stored locally on your machine and is not committed to the repository. The application uses the following techniques to protect your data:

- `.gitignore` rules to exclude data files from Git
- Local file storage only (no cloud or remote storage)
- Backup functionality for data protection

For detailed information on data handling, see the [Data Handling Guidelines](budget-utility/DATA_HANDLING.md).

### Documentation

- [Budget Utility Usage Guide](budget-utility/USAGE.md)
- [Data Handling Guidelines](budget-utility/DATA_HANDLING.md)

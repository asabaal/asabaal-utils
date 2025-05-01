# Quick Start Guide

This guide will help you get started with Asabaal Video Utilities quickly. We'll cover basic usage of both the command-line interface (CLI) and the Python API.

## Basic CLI Usage

Asabaal Video Utilities provides several command-line tools to process videos without writing any code.

### Remove Silent Segments

```bash
# Remove silent segments from a video
remove-silence input.mp4 output.mp4

# Customize silence detection thresholds
remove-silence input.mp4 output.mp4 --threshold -30 --duration 1.0
```

### Analyze a Video Transcript

```bash
# Analyze transcript to find optimal clip points
analyze-transcript input.mp4 --output analysis.json

# Analyze with custom parameters
analyze-transcript input.mp4 --min-clip-length 3 --output analysis.json
```

### Generate Thumbnails

```bash
# Generate thumbnail candidates
generate-thumbnails input.mp4 --output thumbnails/

# Generate a specific number of thumbnails
generate-thumbnails input.mp4 --count 10 --output thumbnails/
```

### Create a Video Summary

```bash
# Create an automatic summary video
create-summary input.mp4 summary.mp4 --style highlights

# Create a summary with a specific duration
create-summary input.mp4 summary.mp4 --duration 60 --style trailer
```

### Extract Clips Based on Content

```bash
# Extract clips based on transcript analysis
extract-clips input.mp4 clips/ --transcript transcript.srt

# Extract clips with custom parameters
extract-clips input.mp4 clips/ --min-length 5 --max-length 30 --transcript transcript.srt
```

## Basic Python API Usage

For more control and integration with your own code, you can use the Python API.

### Remove Silent Segments

```python
from asabaal_utils.video_processing import remove_silence

# Basic usage
remove_silence("input.mp4", "output.mp4")

# With custom parameters
remove_silence(
    "input.mp4", 
    "output.mp4", 
    threshold=-30,  # dB
    min_silence_duration=1.0,  # seconds
    chunk_size=10  # MB, for memory optimization
)
```

### Analyze Transcript

```python
from asabaal_utils.video_processing import analyze_transcript

# Analyze transcript
results = analyze_transcript("input.mp4")

# Print optimal clip points
for clip in results['clips']:
    print(f"Clip from {clip['start']} to {clip['end']}: {clip['topic']}")
    
# Save analysis results
import json
with open("analysis.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Generate Thumbnails

```python
from asabaal_utils.video_processing import generate_thumbnails

# Generate thumbnails
thumbnails = generate_thumbnails("input.mp4", count=5)

# Print thumbnail information
for i, thumb in enumerate(thumbnails):
    print(f"Thumbnail {i+1}: Time: {thumb['timestamp']}s, Score: {thumb['quality_score']}")
    
# Save thumbnails
for i, thumb in enumerate(thumbnails):
    thumb['image'].save(f"thumbnail_{i+1}.jpg")
```

### Create a Video Summary

```python
from asabaal_utils.video_processing import create_summary

# Create a summary video
create_summary(
    "input.mp4", 
    "summary.mp4", 
    style="highlights",
    duration=90  # seconds
)
```

## Next Steps

Now that you're familiar with the basic functionality, you can explore more advanced features:

- [Memory Optimization Guide](guides/memory-optimization.md) for processing large videos
- [Transcript Enhancement Guide](guides/transcript-enhancement.md) for improving analysis
- [Full CLI Reference](cli/index.md) for detailed command-line options
- [API Reference](api/index.md) for complete Python API documentation
- [Example Workflows](examples/silence-removal.md) for end-to-end usage scenarios
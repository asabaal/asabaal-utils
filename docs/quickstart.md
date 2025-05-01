# Quick Start Guide

This guide will help you get started with Asabaal Video Utilities quickly. We'll cover basic usage of both the command-line interface (CLI) and the Python API.

## Basic CLI Usage

Asabaal Video Utilities provides several command-line tools to process videos without writing any code.

### Remove Silent Segments

```bash
# Remove silent segments from a video
remove-silence input.mp4 output.mp4

# Customize silence detection thresholds
remove-silence input.mp4 output.mp4 --threshold-db -30 --min-silence 1.0
```

### Analyze a Video Transcript

```bash
# Analyze transcript to find optimal clip points
analyze-transcript subtitles.srt --format srt --output-file analysis.json

# Analyze with custom parameters
analyze-transcript subtitles.srt --format srt --min-clip-duration 3 --output-file analysis.json

# Enhance transcript during analysis
analyze-transcript subtitles.srt --format srt --enhance-transcript --save-enhanced-transcript
```

### Generate Thumbnails

```bash
# Generate thumbnail candidates
generate-thumbnails input.mp4 --output-dir thumbnails/

# Generate a specific number of thumbnails
generate-thumbnails input.mp4 --count 10 --output-dir thumbnails/
```

### Create a Video Summary

```bash
# Create an automatic summary video
create-summary input.mp4 summary.mp4 --style highlights

# Create a summary with a specific duration
create-summary input.mp4 summary.mp4 --target-duration 60 --style trailer
```

### Extract Clips Based on Content

```bash
# Extract clips based on transcript analysis
extract-clips input.mp4 suggestions.json --output-dir clips/

# Extract clips with custom parameters
extract-clips input.mp4 suggestions.json --output-dir clips/ --min-duration 5 --max-duration 30
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
    threshold_db=-30,  # dB
    min_silence_duration=1.0,  # seconds
    chunk_size=10  # MB, for memory optimization
)
```

### Analyze Transcript

```python
from asabaal_utils.video_processing import analyze_transcript

# Analyze transcript
results = analyze_transcript("transcript_file.srt", transcript_format="srt")

# Print optimal clip points
for clip in results:
    print(f"Clip from {clip['start_time']} to {clip['end_time']}: {clip['topic']}")
    
# Save analysis results
import json
with open("analysis.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Generate Thumbnails

```python
from asabaal_utils.video_processing import generate_thumbnails

# Generate thumbnails
thumbnails = generate_thumbnails("input.mp4", frames_to_extract=5)

# Print thumbnail information
for i, thumb in enumerate(thumbnails):
    print(f"Thumbnail {i+1}: Time: {thumb['timestamp']}s, Score: {thumb['quality_score']}")
    
# Save thumbnails
for i, thumb in enumerate(thumbnails):
    print(f"Thumbnail saved to: {thumb['frame_path']}")
```

### Create a Video Summary

```python
from asabaal_utils.video_processing import create_video_summary
from asabaal_utils.video_processing.video_summarizer import SummaryStyle

# Create a summary video
create_video_summary(
    "input.mp4", 
    "summary.mp4", 
    summary_style=SummaryStyle.HIGHLIGHTS.value,
    target_duration=90  # seconds
)
```

## Next Steps

Now that you're familiar with the basic functionality, you can explore more advanced features:

- [Memory Optimization Guide](guides/memory-optimization.md) for processing large videos
- [Transcript Enhancement Guide](guides/transcript-enhancement.md) for improving analysis
- [Full CLI Reference](cli/index.md) for detailed command-line options
- [API Reference](api/index.md) for complete Python API documentation
- [Example Workflows](examples/silence-removal.md) for end-to-end usage scenarios
# Memory Optimization Guide

Processing large video files can be memory-intensive. This guide explains how to optimize memory usage when working with the Asabaal Video Utilities to process videos of any size efficiently.

## Understanding Memory Challenges

Video processing typically requires loading frames into memory, which can quickly exhaust available RAM when working with large files. For example:

- A 1080p (1920×1080) video at 30fps can require approximately 6MB of memory per second of footage in raw format
- A 10-minute 4K video could potentially require several gigabytes of memory

## Memory-Adaptive Processing

Asabaal Video Utilities implements several strategies to handle large files efficiently:

1. **Chunked Processing**: Process videos in small, manageable chunks
2. **Stream Processing**: Stream data rather than loading entire files
3. **Memory Monitoring**: Automatically adjust processing parameters based on available memory
4. **Temporary File Management**: Efficient use of disk space for intermediate results

## Key Memory Optimization Parameters

The following parameters are available in most CLI commands and API functions:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `chunk_size` | Process video in chunks of this size (MB) | Varies by function |
| `max_memory` | Maximum memory usage allowed (MB) | 75% of system RAM |
| `temp_dir` | Directory for temporary files | System temp directory |
| `keep_temp` | Keep temporary files after processing | False |

## Memory Optimization Strategies

### 1. Adjusting Chunk Size

The chunk size determines how much of the video is processed at once:

```python
from asabaal_utils.video_processing import remove_silence

# Process in smaller chunks (less memory, slower)
remove_silence(
    "large_video.mp4", 
    "output.mp4", 
    chunk_size=5  # 5MB chunks
)

# Process in larger chunks (more memory, faster)
remove_silence(
    "large_video.mp4", 
    "output.mp4", 
    chunk_size=50  # 50MB chunks
)
```

CLI example:
```bash
remove-silence large_video.mp4 output.mp4 --chunk-size 5
```

### 2. Setting Memory Limits

Explicitly limit maximum memory usage:

```python
from asabaal_utils.video_processing import video_summarizer

# Limit memory usage to 2GB
video_summarizer.create_summary(
    "4k_documentary.mp4", 
    "summary.mp4", 
    max_memory=2000  # 2000MB = 2GB
)
```

CLI example:
```bash
create-summary 4k_documentary.mp4 summary.mp4 --max-memory 2000
```

### 3. Managing Temporary Files

For very large files, specify a temporary directory with sufficient space:

```python
from asabaal_utils.video_processing import clip_extractor

# Specify temp directory with enough space
clip_extractor.extract_clips(
    "movie_file.mp4",
    "clips/",
    temp_dir="/path/with/sufficient/space"
)
```

CLI example:
```bash
extract-clips movie_file.mp4 clips/ --temp-dir /path/with/sufficient/space
```

### 4. Estimating Memory Requirements

Use the memory utilities to estimate memory requirements before processing:

```python
from asabaal_utils.video_processing.memory_utils import estimate_memory_usage, check_memory_available

# Estimate memory usage for processing a file
file_path = "documentary.mp4"
estimated_memory = estimate_memory_usage(file_path, processing_type="full")
print(f"Estimated memory requirement: {estimated_memory} MB")

# Check if enough memory is available
memory_available = check_memory_available(required_memory=estimated_memory)
print(f"Sufficient memory available: {memory_available}")

# Get recommended chunk size
from asabaal_utils.video_processing.memory_utils import recommend_chunk_size
recommended_chunk = recommend_chunk_size(file_path)
print(f"Recommended chunk size: {recommended_chunk} MB")
```

## Optimizing Different Processing Types

### Video Silence Detection

Silence detection primarily works with audio and is less memory-intensive:

```python
from asabaal_utils.video_processing import silence_detector

# Efficient silence detection for large files
detector = silence_detector.SilenceDetector(
    chunk_size=10,
    threshold=-30,
    min_silence_duration=0.5
)

# Process large file
detector.process_video("long_interview.mp4", "result.mp4")
```

### Transcript Analysis

Transcript analysis works with text data and is memory-efficient by default:

```python
from asabaal_utils.video_processing import transcript_analyzer

# Even for large files, transcript analysis is typically memory-efficient
analysis = transcript_analyzer.analyze_transcript("long_lecture.mp4")
```

### Video Color Analysis

Color analysis requires frame processing and benefits from memory optimization:

```python
from asabaal_utils.video_processing import color_analyzer

# Memory-efficient color analysis
colors = color_analyzer.analyze_colors(
    "4k_film.mp4",
    chunk_size=5,
    max_memory=1000,
    sample_rate=0.5  # Analyze every other frame
)
```

## Advanced Optimization Techniques

### 1. Two-Pass Processing

For very large files, use a two-pass approach:

```python
from asabaal_utils.video_processing import silence_detector

# First pass: Detect silence points
silence_info = silence_detector.detect_silence(
    "massive_video.mp4",
    chunk_size=2,
    max_memory=500
)

# Save silence information for later use
import json
with open("silence_points.json", "w") as f:
    json.dump(silence_info, f)

# Second pass: Process the video using pre-computed information
result = silence_detector.process_video_with_info(
    "massive_video.mp4",
    "processed_video.mp4",
    silence_info=silence_info,
    chunk_size=2,
    max_memory=500
)
```

### 2. Downsampling for Analysis

Reduce resolution or frame rate for initial analysis:

```python
from asabaal_utils.video_processing import video_summarizer

# Analyze at lower resolution, then apply to original
summarizer = video_summarizer.VideoSummarizer(
    analysis_scale=0.5,  # Analyze at half resolution
    output_original_quality=True  # Output at original quality
)

summarizer.create_summary("4k_video.mp4", "summary.mp4")
```

### 3. Parallel Chunk Processing

Process chunks in parallel when multiple cores are available:

```python
from asabaal_utils.video_processing import clip_extractor

# Use parallel processing
clips = clip_extractor.extract_clips(
    "documentary.mp4",
    "clips/",
    parallel_chunks=True,
    max_workers=4  # Use 4 CPU cores
)
```

## Monitoring Memory Usage

Monitor memory usage during processing:

```python
from asabaal_utils.video_processing import video_summarizer
from asabaal_utils.video_processing.memory_utils import enable_memory_monitoring

# Enable memory monitoring
enable_memory_monitoring(log_interval=5)  # Log every 5 seconds

# Process video with monitoring
video_summarizer.create_summary("large_file.mp4", "summary.mp4")
```

## Best Practices Summary

1. **Start conservatively**: Use smaller chunk sizes for very large files
2. **Monitor system resources**: Watch memory usage during processing
3. **Use appropriate temp directories**: Ensure sufficient disk space for temporary files
4. **Adjust based on hardware**: Higher spec machines can use larger chunk sizes
5. **Consider file format**: Some formats require more memory to decode
6. **Pre-process when necessary**: Convert complex formats to more efficient ones before processing
7. **Use two-pass approaches** for extremely large files

By following these strategies, you can process videos of virtually any size, even on hardware with limited RAM.
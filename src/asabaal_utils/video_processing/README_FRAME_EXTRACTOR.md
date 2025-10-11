# Frame Extractor Module

A robust utility for extracting frames from video files with multiple extraction methods, quality assessment, and path handling compatibility.

## Features

- Multiple extraction methods with automatic fallback
- Frame quality assessment (brightness, contrast, etc.)
- Path handling compatibility with WSL/Windows
- Proper logging and error handling

## Installation

The Frame Extractor is part of the `asabaal_utils` package. Install it with:

```bash
pip install -e .
```

## Usage

### Basic Frame Extraction

```python
from asabaal_utils.video_processing.frame_extractor import FrameExtractor, extract_frame_from_video

# Quick extraction with convenience function
result = extract_frame_from_video(
    video_path="/path/to/video.mp4",
    timestamp=10.5,  # seconds
    output_path="/path/to/output/frame.jpg"
)

# Create an extractor instance for multiple operations
extractor = FrameExtractor(
    output_dir="/path/to/output",
    output_width=320,
    output_height=180,
    output_format="jpg",
    output_quality=85
)

# Extract a single frame
result = extractor.extract_frame(
    video_path="/path/to/video.mp4",
    timestamp=10.5,  # seconds
    frame_id="my_frame"
)

# Extract multiple frames
timestamps = [5.0, 10.0, 15.0, 20.0]
results = extractor.extract_multiple_frames(
    video_path="/path/to/video.mp4",
    timestamps=timestamps
)
```

### Testing Extraction Methods

The package includes a test script that can check all available extraction methods on a video file:

```bash
# Use the CLI command
test-frame-extractor /path/to/video.mp4 --timestamp 10.5 --output-dir ./extracted_frames

# Or run the script directly
python -m asabaal_utils.video_processing.test_frame_extractor /path/to/video.mp4
```

The test script will:
1. Try all available extraction methods
2. Analyze the quality of extracted frames
3. Generate a report showing which methods worked best
4. Optionally create an HTML visualization of the results

### Comparing Extraction Methods in Code

```python
from asabaal_utils.video_processing.frame_extractor import FrameExtractor

extractor = FrameExtractor()

# Get a list of available methods
methods = extractor.get_available_methods()
print(f"Available methods: {len(methods)}")

# Compare all methods on a specific video and timestamp
results = extractor.compare_extraction_methods(
    video_path="/path/to/video.mp4",
    timestamp=10.5
)

# See which methods succeeded
print(f"Successful methods: {results['successful_methods']}")

# Get the best method for this video
best_method = results['successful_methods'][0] if results['successful_methods'] else None
print(f"Best method: {best_method}")
```

## Available Extraction Methods

The module includes many extraction methods with different strategies:

1. **primary**: Standard seek before input (most accurate)
2. **midpoint_seek**: Seek to midpoint before input
3. **seek_after_input**: Seek after input (faster but less accurate)
4. **one_third_point**: Seek to 1/3 of clip duration after input
5. **two_thirds_point**: Seek to 2/3 of clip duration after input
6. **near_end**: Seek to near end of clip after input
7. **first_frame**: Extract first frame (most reliable)
8. **fast_seek**: Fast seek without accuracy
9. **select_filter**: Select filter at midpoint
10. **force_fps**: Force 30fps with seek
11. **keyframes_only**: Keyframes only at midpoint
12. **error_concealment**: Error concealment with first frame
13. **i_frame_selection**: I-frame selection only
14. **hardware_decoder**: Hardware decoder attempt
15. **scene_change**: Scene change detection

Additionally, format-specific methods are available for:
- MP4/MOV files: Force YUV420P format
- AVI/WMV files: PNG codec for lossless extraction
- MKV/WebM files: Force first video stream

## Quality Assessment

The frame extractor assesses the quality of extracted frames based on:

- **Brightness**: Average pixel intensity
- **Contrast**: Standard deviation of pixel values
- **Black frame detection**: Identifies frames with very low brightness

Quality ratings include:
- **high**: Good brightness and contrast
- **low**: Low brightness or low contrast
- **poor**: Very low brightness or contrast (may be black frames)

## WSL/Windows Path Handling

The module includes special handling for paths across different operating systems:

- Automatically detects WSL environment
- Converts Windows paths to Linux paths when running in WSL
- Handles different WSL mount point configurations
- Provides fallback path resolution options
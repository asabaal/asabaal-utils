# Frame Extractor

A robust utility for extracting frames from video files with multiple extraction methods, quality assessment, and fallback strategies.

## Features

- **Multiple Extraction Methods**: 15+ different methods with automatic fallbacks for challenging videos
- **Quality Assessment**: Evaluates brightness, contrast, and detects black/poor quality frames
- **Format-Specific Approaches**: Special methods for different video formats (MP4, AVI, MKV, etc.)
- **Path Handling**: Handles Windows/WSL path conversions automatically
- **Comprehensive Error Handling**: Graceful recovery and detailed error reporting
- **Testing Utility**: CLI tool to evaluate which methods work best for specific formats

## Usage

### Basic Usage

```python
from asabaal_utils.video_processing.frame_extractor import extract_frame_from_video

# Extract a frame at 5 seconds into the video
result = extract_frame_from_video(
    video_path="/path/to/video.mp4",
    timestamp=5.0,
    output_path="/path/to/output/frame.jpg"
)

# Check if extraction was successful
if result['success']:
    print(f"Frame extracted to: {result['frame_path']}")
    print(f"Frame quality: {result['quality_info']['quality']}")
    print(f"Frame brightness: {result['quality_info']['brightness']}")
else:
    print(f"Frame extraction failed: {result.get('error')}")
```

### Advanced Usage with FrameExtractor Class

```python
from asabaal_utils.video_processing.frame_extractor import FrameExtractor

# Create an extractor instance
extractor = FrameExtractor(
    output_dir="/path/to/output/directory",
    output_width=320,
    output_height=180,
    output_format="jpg",
    output_quality=85,
    ffmpeg_path="ffmpeg"
)

# Extract a frame
result = extractor.extract_frame(
    video_path="/path/to/video.mp4",
    timestamp=5.0,
    frame_id="my_frame"
)

# Extract multiple frames at different timestamps
timestamps = [5.0, 10.0, 15.0]
results = extractor.extract_multiple_frames(
    video_path="/path/to/video.mp4",
    timestamps=timestamps
)

# Extract a frame with a specific method
result = extractor.extract_frame_with_method(
    video_path="/path/to/video.mp4",
    timestamp=5.0,
    method_id="keyframes_only"
)

# Compare all extraction methods
comparison = extractor.compare_extraction_methods(
    video_path="/path/to/video.mp4",
    timestamp=5.0
)
```

### Available Extraction Methods

The Frame Extractor includes the following methods (in order of priority):

1. **primary** - Standard method with accurate seeking before input
2. **midpoint_seek** - Seek to midpoint before input
3. **seek_after_input** - Seek after input (faster but less accurate)
4. **one_third_point** - Seek to 1/3 of clip duration after input
5. **two_thirds_point** - Seek to 2/3 of clip duration after input
6. **near_end** - Seek to near end of clip after input
7. **first_frame** - Extract first frame (most reliable)
8. **fast_seek** - Fast seek without accuracy
9. **select_filter** - Select filter at midpoint
10. **force_fps** - Force 30fps with seek
11. **keyframes_only** - Keyframes only at midpoint
12. **error_concealment** - Error concealment with first frame
13. **i_frame_selection** - I-frame selection only
14. **hardware_decoder** - Hardware decoder attempt
15. **scene_change** - Scene change detection
16. **yuv420p_format** - Force yuv420p format (MP4/MOV specific)
17. **png_codec** - PNG codec for lossless extraction (AVI/WMV specific)
18. **force_first_stream** - Force first video stream (MKV/WebM specific)

## Testing Frame Extraction

The module includes a test script to evaluate all extraction methods on a specific video:

```bash
# Basic usage
python -m asabaal_utils.video_processing.test_frame_extractor /path/to/video.mp4

# Specify timestamp and output directory
python -m asabaal_utils.video_processing.test_frame_extractor /path/to/video.mp4 \
    --timestamp 10.0 \
    --output-dir /path/to/output

# Generate HTML report
python -m asabaal_utils.video_processing.test_frame_extractor /path/to/video.mp4 \
    --generate-html
```

This will:
1. Try all extraction methods
2. Report which methods succeed or fail
3. Show quality metrics for extracted frames
4. Identify the best method for that video
5. Generate an HTML report (if requested)

## Quality Assessment

The Frame Extractor includes automatic quality assessment for extracted frames:

- **Brightness**: Average pixel intensity (0-255)
- **Contrast**: Standard deviation of pixel values
- **Black Frame Detection**: Detects frames with extremely low brightness
- **Quality Rating**: Classifies frames as "high", "low", or "poor" quality

## Path Handling

The Frame Extractor handles different path formats automatically:

- Windows paths (C:\path\to\video.mp4)
- WSL paths (/mnt/c/path/to/video.mp4)
- Mixed path styles

When running in WSL, it will automatically find and convert Windows paths to the appropriate format.
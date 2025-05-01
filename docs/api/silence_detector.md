# Silence Detector

The silence detector module provides utilities for detecting and removing silent portions from videos with memory-adaptive processing.

## SilenceDetector Class

The SilenceDetector class provides methods for detecting and removing silent segments from videos.

```python
class SilenceDetector:
    """
    Detects and removes silent segments from videos with memory-adaptive processing.
    
    This class provides methods for analyzing audio to detect silent segments
    and processing videos to remove those segments.
    
    Attributes:
        threshold (float): The silence detection threshold in dB (default: -30.0)
        min_silence_duration (float): Minimum silence duration to detect in seconds (default: 0.5)
        padding (float): Padding to add around non-silent segments in seconds (default: 0.1)
        chunk_size (int): Size of chunks to process in MB (default: 20)
    """
    
    def __init__(
        self,
        threshold=-30.0,
        min_silence_duration=0.5,
        padding=0.1,
        chunk_size=20,
        max_memory=None
    ):
        """
        Initialize the SilenceDetector with detection parameters.
        
        Args:
            threshold: Silence detection threshold in dB (default: -30.0)
            min_silence_duration: Minimum duration of silence to detect in seconds (default: 0.5)
            padding: Amount of padding to keep around non-silent segments in seconds (default: 0.1)
            chunk_size: Process video in chunks of this size in MB (default: 20)
            max_memory: Maximum memory usage in MB (default: 75% of system RAM)
        """
        pass
        
    def detect_silence(self, input_file):
        """
        Detect silent segments in a video or audio file.
        
        Args:
            input_file: Path to the input video or audio file
            
        Returns:
            Dict containing information about the detected silent segments
        """
        pass
        
    def process_video(self, input_file, output_file, **kwargs):
        """
        Process a video file to remove silent segments.
        
        Args:
            input_file: Path to the input video file
            output_file: Path where the processed video will be saved
            **kwargs: Additional parameters to override instance settings
            
        Returns:
            Dict containing information about the processing results
        """
        pass
```

## Functions

### remove_silence

```python
def remove_silence(
    input_file,
    output_file,
    threshold=-30.0,
    min_silence_duration=0.5,
    padding=0.1,
    chunk_size=20,
    max_memory=None,
    temp_dir=None,
    keep_temp=False,
    audio_only=False,
    dry_run=False,
    report=False,
    report_file=None,
    **kwargs
):
    """
    Remove silent segments from a video file.
    
    Args:
        input_file: Path to the input video file
        output_file: Path where the processed video will be saved
        threshold: Silence detection threshold in dB (default: -30.0)
        min_silence_duration: Minimum duration of silence to detect in seconds (default: 0.5)
        padding: Amount of padding to keep around non-silent segments in seconds (default: 0.1)
        chunk_size: Process video in chunks of this size in MB (default: 20)
        max_memory: Maximum memory usage in MB (default: 75% of system RAM)
        temp_dir: Directory for temporary files (default: system temp)
        keep_temp: Keep temporary files after processing (default: False)
        audio_only: Process only the audio track (default: False)
        dry_run: Analyze but don't create output file (default: False)
        report: Save a JSON report of detected silence (default: False)
        report_file: Path for the JSON silence report (default: None)
        **kwargs: Additional parameters
        
    Returns:
        Dict containing information about the detected silent segments and processing statistics
    """
    pass
```

## Example Usage

### Basic Usage

```python
from asabaal_utils.video_processing.silence_detector import remove_silence

# Remove silent segments with default settings
result = remove_silence(
    input_file="interview.mp4",
    output_file="interview_no_silence.mp4"
)

# Print processing statistics
print(f"Original duration: {result['total_duration']:.2f} seconds")
print(f"Processed duration: {result['output_duration']:.2f} seconds")
print(f"Time saved: {result['time_saved']:.2f} seconds")
```

### Advanced Usage with SilenceDetector Class

```python
from asabaal_utils.video_processing.silence_detector import SilenceDetector

# Create a detector with custom settings
detector = SilenceDetector(
    threshold=-35.0,  # dB
    min_silence_duration=1.0,  # seconds
    padding=0.2,  # seconds
    chunk_size=10  # MB
)

# Detect silent segments without creating an output file
silence_segments = detector.detect_silence("lecture.mp4")

# Print detected silent segments
for i, segment in enumerate(silence_segments):
    print(f"Silent segment {i+1}: {segment['start']:.2f}s to {segment['end']:.2f}s (duration: {segment['duration']:.2f}s)")

# Process the video with the same settings
result = detector.process_video(
    input_file="lecture.mp4",
    output_file="lecture_no_silence.mp4"
)

# Access processing statistics
print(f"Removed {len(result['silence_segments'])} silent segments")
print(f"Reduced duration by {result['time_saved']:.2f} seconds ({result['time_saved']/result['total_duration']*100:.1f}%)")
```

### Memory-Efficient Processing of Large Files

```python
from asabaal_utils.video_processing.silence_detector import SilenceDetector

# Create a detector with memory optimization for large files
detector = SilenceDetector(
    threshold=-30.0,
    min_silence_duration=0.5,
    chunk_size=5,  # Process in smaller chunks
    max_memory=1000  # Limit memory usage to 1GB
)

# Process the large video
result = detector.process_video(
    input_file="large_video.mp4",
    output_file="large_video_no_silence.mp4",
    temp_dir="/path/with/sufficient/space",  # Specify temp directory with enough space
    keep_temp=False  # Delete temporary files after processing
)
```

## Performance Considerations

- **Threshold value**: Lower threshold values (e.g., -40dB) will detect more silence but may include quiet background noises
- **Min silence duration**: Higher values improve processing speed but may miss short silent segments
- **Chunk size**: Smaller chunks reduce memory usage but increase processing time
- **Video codec**: Some codecs require more memory to decode; consider converting complex formats to MP4 first
- **Temp directory**: Processing large files creates temporary files; ensure sufficient disk space
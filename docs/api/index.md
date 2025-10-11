# API Reference

The Asabaal Video Utilities package provides a comprehensive Python API for video processing, analysis, and enhancement. This reference documentation covers all modules, classes, and functions available for use in your Python applications.

## Core Modules

| Module | Description |
|--------|-------------|
| [silence_detector](silence_detector.md) | Detect and remove silent segments from videos |
| [transcript_analyzer](transcript_analyzer.md) | Analyze video transcripts to identify topics and optimal clip points |

## Installation

All API modules are automatically available when you install the package:

```bash
pip install asabaal-utils
```

## Basic Usage

Here's a simple example demonstrating how to use the API to remove silent segments from a video:

```python
from asabaal_utils.video_processing import silence_detector

# Remove silent segments
silence_detector.remove_silence(
    input_file="input.mp4",
    output_file="output.mp4",
    threshold=-30,  # dB
    min_silence_duration=0.5  # seconds
)
```

## Import Patterns

You can import modules in several ways:

```python
# Import the entire package
import asabaal_utils

# Import a specific module
from asabaal_utils.video_processing import transcript_analyzer

# Import specific functions or classes
from asabaal_utils.video_processing.silence_detector import remove_silence, SilenceDetector
```

## Module Independence

Most modules can be used independently, but some share common utilities.

## Advanced Usage

For more advanced usage patterns and comprehensive examples, see:

- [User Guides](../guides/memory-optimization.md) - Detailed guides on advanced topics
- [Example Workflows](../examples/silence-removal.md) - End-to-end examples

## Type Annotations

All API functions and classes include type annotations for better IDE integration and type checking:

```python
def remove_silence(
    input_file: str,
    output_file: str,
    threshold: float = -30.0,
    min_silence_duration: float = 0.5,
    padding: float = 0.1,
    chunk_size: int = 20
) -> Dict[str, Any]:
    """
    Remove silent segments from a video file.
    
    Args:
        input_file: Path to the input video file
        output_file: Path where the processed video will be saved
        threshold: Silence detection threshold in dB (default: -30.0)
        min_silence_duration: Minimum duration of silence to detect in seconds (default: 0.5)
        padding: Amount of padding to keep around non-silent segments in seconds (default: 0.1)
        chunk_size: Process video in chunks of this size in MB (default: 20)
        
    Returns:
        Dict containing information about the detected silent segments and processing statistics
    """
```

## Reference Documentation

For detailed documentation of each module, including all available classes, methods, and functions, see the module-specific pages listed above.
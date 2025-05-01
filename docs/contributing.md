# Contributing to Asabaal Video Utilities

Thank you for your interest in contributing to Asabaal Video Utilities! This guide will help you get started with contributing to the project.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- FFmpeg 4.2 or higher
- Git

### Setting Up the Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/asabaal/asabaal-utils.git
   cd asabaal-utils
   ```

2. **Install development dependencies**:
   ```bash
   # Install the package in development mode
   pip install -e .
   
   # Install development dependencies
   pip install -r tests/requirements.txt
   ```

3. **Verify the setup**:
   ```bash
   # Run tests to verify your setup
   python -m pytest tests/
   ```

## Development Workflow

### Branching Strategy

- `main` branch is the stable release branch
- Create feature branches from `main` for new features or bug fixes
- Use the naming convention `feature/feature-name` or `fix/bug-name`

### Making Changes

1. **Create a new branch**:
   ```bash
   git checkout main
   git pull
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following the code style guidelines
   - Add tests for your changes
   - Update documentation if necessary

3. **Run tests**:
   ```bash
   # Run all tests
   python -m pytest tests/
   
   # Run specific test file
   python -m pytest tests/test_file.py
   
   # Run with coverage
   python -m pytest --cov=asabaal_utils tests/
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push your branch**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

6. **Open a pull request** against the `main` branch

## Code Style Guidelines

### Python Style

We follow Google's Python Style Guide with some modifications:

- Use 4 spaces for indentation
- Maximum line length of 100 characters
- Use Google-style docstrings

### Imports

Order imports as follows, separated by blank lines:

1. Standard library imports
2. Third-party library imports
3. Local application imports

Example:
```python
import os
import sys
from typing import List, Dict, Optional

import numpy as np
import cv2
from scipy import signal

from asabaal_utils.video_processing import memory_utils
from asabaal_utils.video_processing.silence_detector import SilenceDetector
```

### Type Annotations

Use type annotations for all function parameters and return values:

```python
def process_video(
    input_file: str,
    output_file: str,
    threshold: float = -30.0
) -> Dict[str, Any]:
    """Process a video file.
    
    Args:
        input_file: Path to the input video file
        output_file: Path where the processed video will be saved
        threshold: Processing threshold in dB
        
    Returns:
        Dict containing processing statistics
    """
```

### Docstrings

Use Google-style docstrings with Args, Returns, and Raises sections:

```python
def extract_clips(
    video_file: str,
    output_dir: str,
    timestamps: List[Dict[str, float]]
) -> List[str]:
    """Extract clips from a video file.
    
    Args:
        video_file: Path to the video file
        output_dir: Directory to save extracted clips
        timestamps: List of dictionaries with 'start' and 'end' keys in seconds
        
    Returns:
        List of paths to the extracted clip files
        
    Raises:
        FileNotFoundError: If the video file does not exist
        ValueError: If timestamps are invalid
    """
```

### Error Handling

- Use specific exceptions in try/except blocks
- Clean up resources in finally blocks
- Log errors with context information

Example:
```python
try:
    with open(file_path, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    logger.error(f"Could not find file: {file_path}")
    raise
except json.JSONDecodeError:
    logger.error(f"Invalid JSON in file: {file_path}")
    raise ValueError(f"File contains invalid JSON: {file_path}")
finally:
    # Clean up any temporary files or resources
    cleanup_temp_files()
```

## Testing Guidelines

### Test Structure

- Use pytest for all tests
- Organize tests to mirror the package structure
- Name test files with `test_` prefix

### Writing Tests

- Test both normal operation and edge cases
- Use fixtures for common setup
- Mock external dependencies

Example:
```python
import pytest
from unittest.mock import patch
from asabaal_utils.video_processing import silence_detector

@pytest.fixture
def sample_video():
    # Setup code
    return "path/to/test/video.mp4"

def test_silence_detection(sample_video):
    # Test normal operation
    result = silence_detector.detect_silence(sample_video)
    assert "silence_segments" in result
    assert isinstance(result["silence_segments"], list)

@patch("asabaal_utils.video_processing.ffmpeg.run")
def test_silence_detection_ffmpeg_error(mock_run, sample_video):
    # Test error handling
    mock_run.side_effect = Exception("FFmpeg error")
    with pytest.raises(RuntimeError):
        silence_detector.detect_silence(sample_video)
```

### Running Tests

- Run tests before submitting pull requests
- Ensure all tests pass
- Aim for good test coverage

## Documentation Guidelines

### Code Documentation

- All modules, classes, and functions should have docstrings
- Document parameter units (seconds, percentage, etc.)
- Include examples for non-trivial functions

### User Documentation

When adding new features, update:

1. The relevant API documentation
2. The CLI command documentation, if applicable
3. Example workflows or guides, if appropriate

### Documentation Format

- Use Markdown for all documentation
- Follow the existing documentation structure
- Include code examples where appropriate

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Request review from maintainers
4. Address any feedback from code review
5. Once approved, your changes will be merged

## Reporting Issues

When reporting issues, please include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected and actual behavior
- Version information (Python, package version, OS)
- Sample code or files, if possible

## Feature Requests

For feature requests, please include:

- A clear description of the feature
- The use case or problem it solves
- Any alternatives you've considered
- If possible, a sketch of the API or implementation

## Contact

If you have any questions, feel free to reach out:

- Open an issue on GitHub
- Contact the maintainers directly

Thank you for contributing to Asabaal Video Utilities!
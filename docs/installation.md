# Installation Guide

This guide covers how to install the Asabaal Video Utilities package and its dependencies.

## Prerequisites

Before installing, ensure your system meets the following requirements:

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows (with WSL recommended for best performance)
- **External Dependencies**:
  - FFmpeg 4.2+ (required for video processing)
  - SoX (optional, used for some audio processing functions)

### Installing FFmpeg

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Windows
Install FFmpeg using [chocolatey](https://chocolatey.org/):
```bash
choco install ffmpeg
```
Or download from the [official FFmpeg website](https://ffmpeg.org/download.html).

## Installation Methods

### Using pip (Recommended)

The simplest way to install Asabaal Video Utilities is using pip:

```bash
pip install asabaal-utils
```

This will install the package and all its Python dependencies.

### Installing from Source

For the latest development version or to contribute to the project:

```bash
git clone https://github.com/asabaal/asabaal-utils.git
cd asabaal-utils
pip install -e .
```

## Verifying Installation

After installation, verify that everything is working correctly:

```bash
# Check the CLI tools are available
create-summary --help

# Run a simple test
python -c "from asabaal_utils.video_processing import silence_detector; print('Installation successful!')"
```

## Dependencies

Asabaal Video Utilities depends on the following Python packages:

- numpy
- scipy
- opencv-python
- ffmpeg-python
- pydub
- nltk
- scikit-learn
- transformers (optional, for advanced transcript analysis)

These dependencies are automatically installed when using pip.

## Troubleshooting

### Common Issues

#### FFmpeg Not Found

If you encounter an error like `FFmpeg executable not found`:

1. Ensure FFmpeg is installed on your system
2. Make sure FFmpeg is in your system PATH
3. If using a virtual environment, you may need to specify the FFmpeg path:

```python
import os
os.environ["FFMPEG_BINARY"] = "/path/to/ffmpeg"
```

#### Memory Errors with Large Videos

If you encounter memory errors when processing large videos:

1. Try using the memory-adaptive processing options (see [Memory Optimization Guide](guides/memory-optimization.md))
2. Increase the chunk size for processing

#### Import Errors

If you encounter import errors:

1. Check that you've installed the package with all optional dependencies:
```bash
pip install asabaal-utils[all]
```

2. Verify your Python version is compatible (3.8+)

For more troubleshooting guidance, please see our [GitHub Issues](https://github.com/asabaal/asabaal-utils/issues) page or open a new issue.
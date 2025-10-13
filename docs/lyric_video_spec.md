# Claude Code Implementation Prompt: Automated Lyric Video Generator

## Project Overview
Build a complete automated lyric video generation system for content creators that takes audio files, background videos, and lyrics (SRT/LRC or plain text) to create professional lyric videos with audio-reactive animations. The system should support both GPU-accelerated and CPU-only processing modes.

## Core Requirements

### Input Support
- Audio formats: MP3, WAV, FLAC, M4A
- Video formats: MP4, MOV, AVI (for background videos)
- Lyric formats: SRT, LRC files, or plain text with manual timing
- Configuration: JSON-based templates for styling and effects

### Output Requirements
- Multiple quality tiers: 1080p, 720p, 480p
- Platform-optimized encoding (YouTube, TikTok, Instagram)
- Fast-start MP4 for web delivery
- Progress tracking and preview generation

## Technical Architecture

### System Design
Create a modular pipeline with these components:

1. **AudioAnalyzer**: Extract beats, tempo, frequency bands, onset detection
2. **LyricProcessor**: Parse SRT/LRC, align text with timing, word-level synchronization
3. **VideoCompositor**: Layer management, alpha compositing, effects application
4. **TextRenderer**: Typography engine with animations and effects
5. **OutputEncoder**: Multi-format encoding with quality optimization
6. **JobManager**: Queue system for batch processing

### Hardware Adaptation
Implement automatic hardware detection and optimization:
- **GPU Mode**: Use FFmpeg with hardware acceleration (NVENC/QuickSync/AMF)
- **CPU Mode**: Optimized software encoding with multi-threading
- **Hybrid Mode**: GPU for effects, CPU for encoding when GPU encoding unavailable

## Implementation Details

### 1. Audio Analysis Pipeline
```python
# Use librosa for comprehensive audio analysis
class AudioAnalyzer:
    def analyze_audio(self, audio_path):
        # Extract tempo, beats, spectral features
        # Return timing data for video synchronization
        pass
    
    def get_beat_times(self):
        # Precise beat detection for animation triggers
        pass
    
    def get_frequency_bands(self, timestamp):
        # Real-time frequency analysis for reactive effects
        pass
```

Requirements:
- Beat detection with sub-frame accuracy
- Frequency band analysis (bass, mids, highs)
- Onset detection for text animation triggers
- RMS energy calculation for size/intensity effects

### 2. Lyric Synchronization System
```python
class LyricProcessor:
    def parse_lyrics(self, lyric_file_or_text):
        # Support SRT, LRC, and plain text
        pass
    
    def align_to_audio(self, audio_analysis):
        # Synchronize lyrics with audio features
        pass
    
    def get_words_at_time(self, timestamp):
        # Return active words with timing info
        pass
```

Features needed:
- SRT/LRC parser with error handling
- Word-level timing interpolation
- Karaoke-style highlighting support
- Manual timing adjustment interface

### 3. Video Compositing Engine
```python
class VideoCompositor:
    def __init__(self, gpu_mode=True):
        self.gpu_accelerated = gpu_mode
        self.setup_rendering_context()
    
    def composite_frame(self, background, text_overlay, effects):
        # Layer composition with alpha blending
        pass
    
    def apply_audio_reactive_effects(self, frame, audio_features):
        # Dynamic effects based on audio analysis
        pass
```

Implement:
- Multi-layer compositing (background, text, effects, UI)
- Audio-reactive visual effects (pulse, glow, particle systems)
- Smooth transitions and easing functions
- Efficient frame buffer management

### 4. Typography and Animation System
```python
class TextRenderer:
    def __init__(self):
        self.font_cache = {}
        self.animation_presets = {}
    
    def render_animated_text(self, text, style, progress, audio_features):
        # Create animated text with audio synchronization
        pass
    
    def apply_text_effects(self, text_surface, effects_config):
        # Glow, shadow, gradient, outline effects
        pass
```

Text animation features:
- Kinetic typography with beat synchronization
- Character-by-character reveals
- Multiple font support with fallbacks
- Text effects: glow, shadow, stroke, gradient
- Smooth interpolation between states

### 5. Hardware-Adaptive Encoding
```python
class OutputEncoder:
    def __init__(self):
        self.detect_hardware_capabilities()
    
    def detect_hardware_capabilities(self):
        # Auto-detect GPU encoding support
        pass
    
    def encode_video(self, frame_sequence, audio_path, output_config):
        # Choose optimal encoding path
        if self.gpu_available:
            return self.gpu_encode(frame_sequence, audio_path, output_config)
        else:
            return self.cpu_encode(frame_sequence, audio_path, output_config)
```

Encoding requirements:
- Hardware detection (NVIDIA NVENC, Intel QuickSync, AMD AMF)
- Fallback to optimized software encoding
- Multiple output formats and qualities
- Progress tracking and error handling

## Configuration System

### Template Structure
```json
{
  "video_config": {
    "resolution": [1920, 1080],
    "fps": 30,
    "duration_padding": 2.0
  },
  "text_config": {
    "font_family": "Arial Bold",
    "font_size": 72,
    "color": "#FFFFFF",
    "stroke_color": "#000000",
    "stroke_width": 3,
    "glow_color": "#00FF00",
    "glow_radius": 10
  },
  "animation_config": {
    "entrance_type": "fade_up",
    "sync_to_beats": true,
    "character_delay": 0.05,
    "word_highlight_duration": 0.5
  },
  "audio_reactive": {
    "enable_beat_sync": true,
    "enable_frequency_reactive": true,
    "bass_threshold": 0.3,
    "energy_scaling": 0.2
  }
}
```

## Performance Optimization

### CPU-Only Optimizations
- Multi-threaded frame processing
- Efficient memory management with frame pooling
- Optimized software rendering with Skia or Cairo
- Smart caching of rendered text elements
- Batch processing for similar frames

### GPU Optimizations (when available)
- CUDA/OpenCL acceleration for effects
- Hardware-accelerated video encoding
- GPU memory management for large videos
- Parallel processing pipelines

### Memory Management
```python
class FrameBufferManager:
    def __init__(self, buffer_size=10):
        self.frame_pool = Queue(maxsize=buffer_size)
        self.setup_reusable_buffers()
    
    def get_frame_buffer(self, resolution):
        # Reuse allocated frame buffers
        pass
    
    def return_frame_buffer(self, frame_buffer):
        # Return to pool for reuse
        pass
```

## File Structure and Organization

```
lyric_video_generator/
├── src/
│   ├── audio/
│   │   ├── analyzer.py
│   │   └── features.py
│   ├── video/
│   │   ├── compositor.py
│   │   ├── effects.py
│   │   └── encoder.py
│   ├── text/
│   │   ├── renderer.py
│   │   ├── animations.py
│   │   └── fonts.py
│   ├── lyrics/
│   │   ├── parser.py
│   │   └── synchronizer.py
│   ├── pipeline/
│   │   ├── job_manager.py
│   │   └── processor.py
│   └── utils/
│       ├── hardware_detection.py
│       └── config_loader.py
├── templates/
│   ├── default.json
│   ├── modern.json
│   └── retro.json
├── examples/
│   ├── sample_audio.mp3
│   ├── sample_lyrics.srt
│   └── sample_background.mp4
├── tests/
└── requirements.txt
```

## Dependencies and Libraries

### Core Dependencies
```
librosa>=0.10.0           # Audio analysis
opencv-python>=4.8.0      # Video processing
pillow>=10.0.0           # Image manipulation
moviepy>=1.0.3           # Video editing (CPU fallback)
pydub>=0.25.1            # Audio manipulation
numpy>=1.24.0            # Numerical computing
scipy>=1.10.0            # Scientific computing
```

### Optional GPU Dependencies
```
cupy-cuda11x             # CUDA acceleration
opencv-contrib-python    # Extended OpenCV with CUDA support
pycuda                   # Direct CUDA programming
```

### System Dependencies
```bash
# FFmpeg with hardware acceleration
sudo apt-get install ffmpeg
# or with NVIDIA support
sudo apt-get install ffmpeg-nvidia

# Font rendering
sudo apt-get install libcairo2-dev libgirepository1.0-dev
```

## Usage Examples

### Basic Usage
```python
from lyric_video_generator import LyricVideoGenerator

generator = LyricVideoGenerator()

# Simple generation
video_path = generator.create_video(
    audio_path="song.mp3",
    lyrics_path="lyrics.srt",
    background_video="background.mp4",
    template="modern",
    output_path="output.mp4"
)
```

### Advanced Configuration
```python
# Custom configuration
config = {
    "text_config": {
        "font_family": "Roboto Bold",
        "color": "#FF6B35",
        "glow_color": "#FFE66D"
    },
    "animation_config": {
        "sync_to_beats": True,
        "entrance_type": "typewriter"
    }
}

video_path = generator.create_video(
    audio_path="song.mp3",
    lyrics_path="lyrics.srt",
    background_video="background.mp4",
    custom_config=config,
    output_path="custom_output.mp4"
)
```

## Testing and Quality Assurance

### Unit Tests
- Audio analysis accuracy verification
- Lyric parsing with various formats
- Text rendering quality checks
- Frame composition validation

### Performance Tests
- Memory usage monitoring
- Processing speed benchmarks
- GPU vs CPU performance comparison
- Large file handling

### Integration Tests
- End-to-end video generation
- Multiple format support
- Error handling and recovery
- Hardware compatibility

## Error Handling and Logging

Implement comprehensive error handling:
- Graceful degradation when GPU unavailable
- Input validation with helpful error messages
- Progress tracking with detailed logging
- Recovery mechanisms for interrupted processing

## CLI Interface

```bash
# Basic usage
python -m lyric_video_generator \
  --audio song.mp3 \
  --lyrics lyrics.srt \
  --background background.mp4 \
  --template modern \
  --output result.mp4

# Advanced options
python -m lyric_video_generator \
  --audio song.mp3 \
  --lyrics lyrics.srt \
  --background background.mp4 \
  --config custom_config.json \
  --gpu-mode auto \
  --quality 1080p \
  --preset fast \
  --output result.mp4
```

## Success Criteria

The implementation should:
1. Process a 3-minute song with lyrics in under 5 minutes on modern hardware
2. Support both GPU and CPU-only environments seamlessly
3. Produce broadcast-quality output (1080p, proper encoding)
4. Handle common edge cases (missing lyrics, audio format issues)
5. Provide clear progress feedback and error messages
6. Include comprehensive documentation and examples

## Additional Features (Nice to Have)

- Web interface for easy configuration
- Batch processing for multiple videos
- Template marketplace integration
- Real-time preview during processing
- Social media platform presets
- Automatic background video selection
- AI-powered lyric timing suggestions

Please implement this system with clean, well-documented code, comprehensive error handling, and efficient performance for both GPU and CPU processing modes. Focus on creating a production-ready tool that content creators can reliably use for their business.
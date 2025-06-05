# Lyric Video Generator

Part of asabaal-utils video processing toolkit. Creates automated lyric videos with synchronized text animations and audio-reactive visual effects.

## Features

- **Multiple Format Support**: SRT, LRC, and plain text lyrics
- **Audio Analysis**: Beat detection, frequency analysis, onset detection using librosa
- **GPU Acceleration**: Automatic hardware detection (NVIDIA NVENC, Intel QuickSync, AMD AMF)
- **Rich Animations**: Fade, slide, bounce, typewriter, elastic, and more effects
- **Audio-Reactive**: Visual effects that respond to music energy and beats
- **Professional Effects**: Glow, shadow, stroke, and particle effects
- **Customizable Templates**: JSON-based styling system

## Quick Usage

### From Python

```python
from asabaal_utils.video_processing import LyricVideoGenerator

# Create generator
generator = LyricVideoGenerator(resolution=(1920, 1080), fps=30.0)

# Generate video
generator.create_video(
    audio_path="song.mp3",
    lyrics_path="lyrics.srt",
    output_path="output.mp4",
    background_video="background.mp4",  # Optional
    template="default"
)
```

### From Command Line

```bash
# Install asabaal-utils first
pip install -e .

# Basic usage
create-lyric-video --audio song.mp3 --lyrics lyrics.srt --output video.mp4

# With background and custom settings
create-lyric-video --audio song.mp3 --lyrics lyrics.srt --background bg.mp4 \
  --font-family "Arial Bold" --font-size 80 --text-color "#FF6B35" \
  --quality high_quality --output video.mp4

# Show system info
create-lyric-video --system-info
```

## Architecture

- **Audio Analysis** (`audio/`): Beat detection and frequency analysis with librosa
- **Lyrics Processing** (`lyrics/`): SRT/LRC parsing with word-level timing
- **Text Rendering** (`text/`): Typography engine with animations and effects  
- **Video Composition** (`compositor.py`): GPU/CPU adaptive layer compositing
- **Hardware Detection** (`hardware_detection.py`): Automatic GPU encoding optimization
- **Output Encoding** (`encoder.py`): Multi-format encoding with hardware acceleration

## Templates

Templates control visual style and animation behavior:

```json
{
  "text_config": {
    "font_family": "Arial",
    "font_size": 72,
    "color": "#FFFFFF",
    "glow_radius": 10
  },
  "animation_config": {
    "entrance_type": "bounce_in", 
    "sync_to_beats": true
  }
}
```

Built-in templates: `default` (more coming soon)

## System Requirements

- Python 3.8+
- FFmpeg (for audio/video processing)
- Optional: NVIDIA, Intel, or AMD GPU for hardware acceleration

## Performance

- **GPU Mode**: Real-time processing on modern hardware
- **CPU Mode**: Optimized software rendering with multi-threading
- **Memory Efficient**: Frame buffer pooling and adaptive quality scaling
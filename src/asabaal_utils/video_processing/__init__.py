"""
Video processing utilities for asabaal-utils.

This module provides utilities for processing video files, including:
- Silence detection and removal
- Video splitting based on content
- Transcript analysis for coherent clip generation
- Automatic thumbnail generation
- Video color theme and palette analysis
"""

from .silence_detector import SilenceDetector, remove_silence
from .transcript_analyzer import analyze_transcript
from .thumbnail_generator import ThumbnailGenerator, generate_thumbnails
from .color_analyzer import ColorAnalyzer, analyze_video_colors

__all__ = [
    'SilenceDetector',
    'remove_silence',
    'analyze_transcript',
    'ThumbnailGenerator',
    'generate_thumbnails',
    'ColorAnalyzer',
    'analyze_video_colors',
]

"""
Video processing utilities for asabaal-utils.

This module provides utilities for processing video files, including:
- Silence detection and removal
- Video splitting based on content
- Transcript analysis for coherent clip generation
- Automatic thumbnail generation
- Video color theme and palette analysis
- Jump cut detection and smoothing
"""

from .silence_detector import SilenceDetector, remove_silence
from .transcript_analyzer import analyze_transcript
from .thumbnail_generator import ThumbnailGenerator, generate_thumbnails
from .color_analyzer import ColorAnalyzer, analyze_video_colors
from .jump_cut_detector import JumpCutDetector, detect_jump_cuts, smooth_jump_cuts

__all__ = [
    'SilenceDetector',
    'remove_silence',
    'analyze_transcript',
    'ThumbnailGenerator',
    'generate_thumbnails',
    'ColorAnalyzer',
    'analyze_video_colors',
    'JumpCutDetector',
    'detect_jump_cuts',
    'smooth_jump_cuts',
]

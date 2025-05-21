"""
Video processing utilities for asabaal-utils.

This module provides utilities for processing video files, including:
- Silence detection and removal
- Video splitting based on content
- Transcript analysis for coherent clip generation
- Automatic thumbnail generation
- Video color theme and palette analysis
- Jump cut detection and smoothing
- Content-aware video summarization
- Frame extraction with multiple methods and quality assessment
"""

from .silence_detector import SilenceDetector, remove_silence
from .transcript_analyzer import analyze_transcript
from .thumbnail_generator import ThumbnailGenerator, generate_thumbnails
from .color_analyzer import ColorAnalyzer, analyze_video_colors
from .jump_cut_detector import JumpCutDetector, detect_jump_cuts, smooth_jump_cuts
from .video_summarizer import VideoSummarizer, create_video_summary, SummaryStyle
from .frame_extractor import FrameExtractor, extract_frame_from_video

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
    'VideoSummarizer',
    'create_video_summary',
    'SummaryStyle',
    'FrameExtractor',
    'extract_frame_from_video',
]

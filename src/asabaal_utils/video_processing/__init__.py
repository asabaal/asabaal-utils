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
- Automated lyric video generation with audio-reactive animations
"""

# Import lyric video generator first (doesn't need moviepy)
from .lyric_video import LyricVideoGenerator

# Conditionally import modules that require moviepy
try:
    from .silence_detector import SilenceDetector, remove_silence
    from .video_summarizer import VideoSummarizer, create_video_summary, SummaryStyle
    from .jump_cut_detector import JumpCutDetector, detect_jump_cuts, smooth_jump_cuts
except ImportError as e:
    import warnings
    warnings.warn(f"Some video processing modules unavailable due to MoviePy import issues: {e}")
    # Define dummy classes/functions
    SilenceDetector = None
    remove_silence = None
    VideoSummarizer = None
    create_video_summary = None
    SummaryStyle = None
    JumpCutDetector = None
    detect_jump_cuts = None
    smooth_jump_cuts = None

# Import modules that don't require moviepy
from .transcript_analyzer import analyze_transcript
from .thumbnail_generator import ThumbnailGenerator, generate_thumbnails
from .color_analyzer import ColorAnalyzer, analyze_video_colors
from .frame_extractor import FrameExtractor, extract_frame_from_video

# Import church service analysis modules
try:
    from .church_service_analyzer import ChurchServiceAnalyzer, ServiceAnalysisResult
    from .church_audio_classifier import ChurchAudioClassifier
except ImportError:
    ChurchServiceAnalyzer = None
    ServiceAnalysisResult = None
    ChurchAudioClassifier = None

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
    'LyricVideoGenerator',
]

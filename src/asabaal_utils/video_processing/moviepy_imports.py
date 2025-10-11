"""
MoviePy import compatibility module.

Handles the different import structures between MoviePy 1.x and 2.x versions.
"""

import sys

# Try different import patterns for MoviePy compatibility
try:
    # Try MoviePy 2.x import structure first (most recent)
    from moviepy import (
        VideoFileClip, 
        AudioFileClip,
        concatenate_videoclips,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        ColorClip,
        VideoClip
    )
    from moviepy import vfx, afx
    MOVIEPY_VERSION = 2
except ImportError:
    try:
        # Fallback to MoviePy 1.x import structure
        from moviepy.editor import (
            VideoFileClip,
            AudioFileClip, 
            concatenate_videoclips,
            CompositeVideoClip,
            ImageClip,
            TextClip,
            ColorClip,
            vfx,
            afx
        )
        from moviepy.video.VideoClip import VideoClip
        MOVIEPY_VERSION = 1
    except ImportError:
        # Try alternative import paths for specific modules
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
            from moviepy.audio.io.AudioFileClip import AudioFileClip
            from moviepy.video.compositing.concatenate import concatenate_videoclips
            from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
            from moviepy.video.VideoClip import VideoClip, ImageClip, TextClip, ColorClip
            from moviepy.video import fx as vfx
            from moviepy.audio import fx as afx
            MOVIEPY_VERSION = 1.5
        except ImportError:
            raise ImportError(
                "Could not import MoviePy. Please install it with: pip install moviepy\n"
                "If you have multiple Python environments, make sure you're using the right one."
            )

# Export all imports for easy access
__all__ = [
    'VideoFileClip',
    'AudioFileClip',
    'concatenate_videoclips',
    'CompositeVideoClip',
    'VideoClip',
    'ImageClip',
    'TextClip',
    'ColorClip',
    'vfx',
    'afx',
    'MOVIEPY_VERSION'
]

def get_moviepy_version():
    """Get the detected MoviePy version."""
    return MOVIEPY_VERSION

def check_moviepy_import():
    """Check if MoviePy is properly imported and return diagnostics."""
    return {
        'imported': True,
        'version': MOVIEPY_VERSION,
        'modules': {
            'VideoFileClip': VideoFileClip is not None,
            'AudioFileClip': AudioFileClip is not None,
            'concatenate_videoclips': concatenate_videoclips is not None,
            'CompositeVideoClip': CompositeVideoClip is not None,
            'ImageClip': ImageClip is not None,
            'TextClip': TextClip is not None,
            'ColorClip': ColorClip is not None,
            'vfx': vfx is not None,
            'afx': afx is not None
        }
    }
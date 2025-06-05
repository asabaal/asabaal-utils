"""Lyrics processing module for parsing and synchronization."""

from .parser import LyricParser, LyricLine, LyricWord
from .synchronizer import LyricSynchronizer
from .processor import LyricProcessor

__all__ = ["LyricParser", "LyricLine", "LyricWord", "LyricSynchronizer", "LyricProcessor"]
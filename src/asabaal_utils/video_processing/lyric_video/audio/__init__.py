"""Audio processing module for lyric video generation."""

from .analyzer import AudioAnalyzer
from .features import AudioFeatures, BeatInfo, FrequencyBands

__all__ = ["AudioAnalyzer", "AudioFeatures", "BeatInfo", "FrequencyBands"]
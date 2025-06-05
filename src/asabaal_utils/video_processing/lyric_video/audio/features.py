"""Audio feature extraction data structures."""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class BeatInfo:
    """Information about detected beats in audio."""
    times: np.ndarray  # Beat times in seconds
    tempo: float  # Overall tempo in BPM
    confidence: float  # Tempo estimation confidence
    
    def get_nearest_beat(self, time: float) -> Tuple[float, int]:
        """Get the nearest beat time and index for a given time."""
        idx = np.argmin(np.abs(self.times - time))
        return self.times[idx], idx
    
    def is_on_beat(self, time: float, tolerance: float = 0.05) -> bool:
        """Check if a time is on or near a beat."""
        nearest_beat, _ = self.get_nearest_beat(time)
        return abs(time - nearest_beat) <= tolerance


@dataclass
class FrequencyBands:
    """Frequency band analysis results."""
    bass: float  # 20-250 Hz
    low_mid: float  # 250-500 Hz
    mid: float  # 500-2000 Hz
    high_mid: float  # 2000-4000 Hz
    high: float  # 4000+ Hz
    
    def get_dominant_band(self) -> str:
        """Get the name of the dominant frequency band."""
        bands = {
            'bass': self.bass,
            'low_mid': self.low_mid,
            'mid': self.mid,
            'high_mid': self.high_mid,
            'high': self.high
        }
        return max(bands, key=bands.get)
    
    def get_energy_level(self) -> float:
        """Get overall energy level (0.0 to 1.0)."""
        total = self.bass + self.low_mid + self.mid + self.high_mid + self.high
        return min(total / 5.0, 1.0)


@dataclass
class AudioFeatures:
    """Complete audio feature analysis results."""
    duration: float
    sample_rate: int
    beats: BeatInfo
    onset_times: np.ndarray  # Times of detected onsets
    rms_energy: np.ndarray  # RMS energy over time
    spectral_centroids: np.ndarray  # Spectral centroid over time
    zero_crossing_rate: np.ndarray  # ZCR over time
    
    def get_features_at_time(self, time: float) -> dict:
        """Get interpolated features at a specific time."""
        # Find frame index for the given time
        frame_rate = len(self.rms_energy) / self.duration
        frame_idx = int(time * frame_rate)
        frame_idx = min(frame_idx, len(self.rms_energy) - 1)
        
        return {
            'rms_energy': float(self.rms_energy[frame_idx]),
            'spectral_centroid': float(self.spectral_centroids[frame_idx]),
            'zero_crossing_rate': float(self.zero_crossing_rate[frame_idx]),
            'is_onset': self._is_onset(time),
            'on_beat': self.beats.is_on_beat(time)
        }
    
    def _is_onset(self, time: float, tolerance: float = 0.025) -> bool:
        """Check if time is near an onset."""
        if len(self.onset_times) == 0:
            return False
        return np.min(np.abs(self.onset_times - time)) <= tolerance
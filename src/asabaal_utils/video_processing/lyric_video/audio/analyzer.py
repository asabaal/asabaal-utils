"""Audio analysis module for beat detection and feature extraction."""

import numpy as np
import librosa
import librosa.display
from typing import Optional, Tuple, Union
from pathlib import Path
import logging

from .features import AudioFeatures, BeatInfo, FrequencyBands

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Comprehensive audio analysis for lyric video synchronization."""
    
    def __init__(self, hop_length: int = 512, n_fft: int = 2048):
        """Initialize audio analyzer.
        
        Args:
            hop_length: Number of samples between frames
            n_fft: FFT window size
        """
        self.hop_length = hop_length
        self.n_fft = n_fft
        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate: Optional[int] = None
        self._features: Optional[AudioFeatures] = None
        
    def load_audio(self, audio_path: Union[str, Path]) -> None:
        """Load audio file for analysis.
        
        Args:
            audio_path: Path to audio file
        """
        logger.info(f"Loading audio from {audio_path}")
        self._audio_data, self._sample_rate = librosa.load(
            str(audio_path), sr=None, mono=True
        )
        logger.info(f"Loaded {len(self._audio_data)/self._sample_rate:.2f}s of audio at {self._sample_rate}Hz")
        
    def analyze_audio(self, audio_path: Optional[Union[str, Path]] = None) -> AudioFeatures:
        """Perform comprehensive audio analysis.
        
        Args:
            audio_path: Optional path to audio file (if not already loaded)
            
        Returns:
            AudioFeatures object with complete analysis
        """
        if audio_path:
            self.load_audio(audio_path)
            
        if self._audio_data is None:
            raise ValueError("No audio data loaded")
            
        logger.info("Starting audio analysis...")
        
        # Beat tracking
        beats = self._detect_beats()
        
        # Onset detection
        onset_times = self._detect_onsets()
        
        # Energy and spectral features
        rms_energy = self._calculate_rms_energy()
        spectral_centroids = self._calculate_spectral_centroids()
        zcr = self._calculate_zero_crossing_rate()
        
        # Create features object
        self._features = AudioFeatures(
            duration=len(self._audio_data) / self._sample_rate,
            sample_rate=self._sample_rate,
            beats=beats,
            onset_times=onset_times,
            rms_energy=rms_energy,
            spectral_centroids=spectral_centroids,
            zero_crossing_rate=zcr
        )
        
        logger.info(f"Analysis complete: {len(beats.times)} beats, {len(onset_times)} onsets detected")
        return self._features
        
    def get_beat_times(self) -> np.ndarray:
        """Get array of beat times in seconds."""
        if self._features is None:
            raise ValueError("Audio not analyzed yet")
        return self._features.beats.times
        
    def get_frequency_bands(self, timestamp: float, window_size: float = 0.1) -> FrequencyBands:
        """Get frequency band analysis at specific timestamp.
        
        Args:
            timestamp: Time in seconds
            window_size: Analysis window size in seconds
            
        Returns:
            FrequencyBands object with energy levels
        """
        if self._audio_data is None:
            raise ValueError("No audio data loaded")
            
        # Extract audio window
        start_sample = int((timestamp - window_size/2) * self._sample_rate)
        end_sample = int((timestamp + window_size/2) * self._sample_rate)
        
        # Clamp to valid range
        start_sample = max(0, start_sample)
        end_sample = min(len(self._audio_data), end_sample)
        
        window = self._audio_data[start_sample:end_sample]
        
        # Compute FFT
        fft = np.abs(np.fft.rfft(window * np.hanning(len(window))))
        freqs = np.fft.rfftfreq(len(window), 1/self._sample_rate)
        
        # Define frequency bands
        bands = {
            'bass': (20, 250),
            'low_mid': (250, 500),
            'mid': (500, 2000),
            'high_mid': (2000, 4000),
            'high': (4000, self._sample_rate/2)
        }
        
        # Calculate energy in each band
        band_energies = {}
        for band_name, (low, high) in bands.items():
            mask = (freqs >= low) & (freqs < high)
            if np.any(mask):
                energy = np.sum(fft[mask]) / np.sum(fft)
            else:
                energy = 0.0
            band_energies[band_name] = energy
            
        return FrequencyBands(**band_energies)
        
    def _detect_beats(self) -> BeatInfo:
        """Detect beats using librosa's beat tracker."""
        logger.info("Detecting beats...")
        
        # Use dynamic beat tracking
        tempo, beats = librosa.beat.beat_track(
            y=self._audio_data,
            sr=self._sample_rate,
            hop_length=self.hop_length
        )
        
        # Convert beat frames to time
        beat_times = librosa.frames_to_time(
            beats, sr=self._sample_rate, hop_length=self.hop_length
        )
        
        # Estimate tempo stability
        if len(beats) > 1:
            beat_intervals = np.diff(beat_times)
            tempo_std = np.std(60 / beat_intervals)
            confidence = 1.0 - min(tempo_std / 10, 1.0)  # Simple confidence metric
        else:
            confidence = 0.0
            
        return BeatInfo(times=beat_times, tempo=float(tempo), confidence=confidence)
        
    def _detect_onsets(self) -> np.ndarray:
        """Detect note onsets in the audio."""
        logger.info("Detecting onsets...")
        
        # Compute onset strength
        onset_envelope = librosa.onset.onset_strength(
            y=self._audio_data,
            sr=self._sample_rate,
            hop_length=self.hop_length
        )
        
        # Pick peaks in onset strength
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_envelope,
            sr=self._sample_rate,
            hop_length=self.hop_length,
            backtrack=True
        )
        
        # Convert to time
        onset_times = librosa.frames_to_time(
            onset_frames, sr=self._sample_rate, hop_length=self.hop_length
        )
        
        return onset_times
        
    def _calculate_rms_energy(self) -> np.ndarray:
        """Calculate RMS energy over time."""
        # Compute RMS energy
        rms = librosa.feature.rms(
            y=self._audio_data,
            frame_length=self.n_fft,
            hop_length=self.hop_length
        )[0]
        
        # Normalize to 0-1 range
        if rms.max() > 0:
            rms = rms / rms.max()
            
        return rms
        
    def _calculate_spectral_centroids(self) -> np.ndarray:
        """Calculate spectral centroids over time."""
        centroids = librosa.feature.spectral_centroid(
            y=self._audio_data,
            sr=self._sample_rate,
            hop_length=self.hop_length
        )[0]
        
        # Normalize
        if centroids.max() > 0:
            centroids = centroids / centroids.max()
            
        return centroids
        
    def _calculate_zero_crossing_rate(self) -> np.ndarray:
        """Calculate zero crossing rate over time."""
        zcr = librosa.feature.zero_crossing_rate(
            self._audio_data,
            frame_length=self.n_fft,
            hop_length=self.hop_length
        )[0]
        
        return zcr
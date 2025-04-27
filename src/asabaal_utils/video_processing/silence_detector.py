"""
Silence detector module for video processing.

This module provides utilities for detecting and removing silence from videos.
"""

import os
import numpy as np
import tempfile
from typing import List, Tuple, Optional, Union, Dict
from dataclasses import dataclass
from pathlib import Path
import logging
from tqdm import tqdm

from moviepy.editor import VideoFileClip
from moviepy.editor import concatenate_videoclips
import librosa

logger = logging.getLogger(__name__)

@dataclass
class AudioSegment:
    """Represents an audio segment with start and end times and silence information."""
    start: float
    end: float
    is_silence: bool
    rms_power: float = 0.0
    
    @property
    def duration(self) -> float:
        """Get the duration of the segment."""
        return self.end - self.start


class SilenceDetector:
    """
    Detector for silences in audio/video files.
    
    This class detects silent segments in audio or video files based on
    configurable thresholds.
    """
    
    def __init__(
        self,
        threshold_db: float = -40.0,
        min_silence_duration: float = 0.5,
        min_sound_duration: float = 0.3,
        padding: float = 0.1,
        chunk_size: float = 0.05,
        aggressive_silence_rejection: bool = False,
    ):
        """
        Initialize the silence detector.
        
        Args:
            threshold_db: Threshold in decibels below which audio is considered silence.
                Lower values are more tolerant of background noise.
            min_silence_duration: Minimum duration in seconds for a segment to be considered silence.
            min_sound_duration: Minimum duration in seconds for a segment to be considered sound.
            padding: Padding in seconds to add before and after non-silent segments.
            chunk_size: Size of audio chunks for analysis in seconds.
            aggressive_silence_rejection: If True, uses additional algorithms to detect
                silences even in the presence of background noise.
        """
        self.threshold_db = threshold_db
        self.min_silence_duration = min_silence_duration
        self.min_sound_duration = min_sound_duration
        self.padding = padding
        self.chunk_size = chunk_size
        self.aggressive_silence_rejection = aggressive_silence_rejection
    
    def detect_silence_segments(self, file_path: Union[str, Path]) -> List[AudioSegment]:
        """
        Detect silent segments in an audio or video file.
        
        Args:
            file_path: Path to the audio or video file.
            
        Returns:
            List of AudioSegment objects.
        """
        logger.info(f"Detecting silence in {file_path}")
        file_path = str(file_path)
        
        # For video files, extract the audio
        if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
            with VideoFileClip(file_path) as video:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    audio_path = temp_file.name
                    video.audio.write_audiofile(audio_path, logger=None)
        else:
            audio_path = file_path
            
        try:
            # Load audio using librosa
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Convert threshold from dB to amplitude
            threshold_amplitude = 10 ** (self.threshold_db / 20)
            
            # Calculate chunk size in samples
            chunk_samples = int(self.chunk_size * sr)
            
            # Detect silence
            segments = []
            chunk_count = int(np.ceil(len(y) / chunk_samples))
            
            start_time = 0
            is_current_silence = False
            segment_start = 0
            current_rms = 0
            
            for i in tqdm(range(chunk_count), desc="Analyzing audio"):
                chunk_start = i * chunk_samples
                chunk_end = min((i + 1) * chunk_samples, len(y))
                chunk = y[chunk_start:chunk_end]
                
                # Calculate RMS power
                rms = np.sqrt(np.mean(chunk**2))
                is_silence = rms < threshold_amplitude
                
                # Dynamic threshold adjustment if aggressive rejection is enabled
                if self.aggressive_silence_rejection:
                    # Analyze spectral flatness (noisy silence vs. true silence)
                    if len(chunk) >= 512:  # Minimum size for spectral analysis
                        spectral_flatness = librosa.feature.spectral_flatness(y=chunk)
                        is_silence = is_silence and np.mean(spectral_flatness) > 0.5
                
                # Time for this chunk
                chunk_time = chunk_start / sr
                
                # State transition
                if is_silence != is_current_silence:
                    # End the current segment
                    if is_current_silence:
                        segments.append(AudioSegment(
                            start=segment_start,
                            end=chunk_time,
                            is_silence=True,
                            rms_power=current_rms
                        ))
                    else:
                        segments.append(AudioSegment(
                            start=segment_start,
                            end=chunk_time,
                            is_silence=False,
                            rms_power=current_rms
                        ))
                    
                    # Start a new segment
                    segment_start = chunk_time
                    is_current_silence = is_silence
                    current_rms = rms
                else:
                    # Update RMS with moving average
                    current_rms = 0.7 * current_rms + 0.3 * rms
            
            # Add the final segment
            segments.append(AudioSegment(
                start=segment_start,
                end=duration,
                is_silence=is_current_silence,
                rms_power=current_rms
            ))
            
            # Filter out segments that are too short
            filtered_segments = []
            for segment in segments:
                if segment.is_silence and segment.duration < self.min_silence_duration:
                    segment.is_silence = False
                if not segment.is_silence and segment.duration < self.min_sound_duration:
                    segment.is_silence = True
                filtered_segments.append(segment)
            
            # Merge adjacent segments of the same type
            merged_segments = []
            current_segment = None
            
            for segment in filtered_segments:
                if current_segment is None:
                    current_segment = segment
                elif current_segment.is_silence == segment.is_silence:
                    current_segment.end = segment.end
                    current_segment.rms_power = max(current_segment.rms_power, segment.rms_power)
                else:
                    merged_segments.append(current_segment)
                    current_segment = segment
            
            if current_segment is not None:
                merged_segments.append(current_segment)
            
            logger.info(f"Found {sum(1 for s in merged_segments if s.is_silence)} silence segments")
            return merged_segments
            
        finally:
            # Clean up temporary files
            if file_path != audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary audio file: {e}")
    
    def get_active_segments(self, segments: List[AudioSegment]) -> List[AudioSegment]:
        """
        Extract non-silent segments from the list of segments.
        
        Args:
            segments: List of AudioSegment objects from detect_silence_segments.
            
        Returns:
            List of non-silent AudioSegment objects with padding applied.
        """
        active_segments = []
        
        for segment in segments:
            if not segment.is_silence:
                # Apply padding but don't go below 0 or overlap with other segments
                start = max(0, segment.start - self.padding)
                end = segment.end + self.padding
                
                active_segments.append(AudioSegment(
                    start=start,
                    end=end,
                    is_silence=False,
                    rms_power=segment.rms_power
                ))
        
        # Merge overlapping segments
        if active_segments:
            active_segments.sort(key=lambda x: x.start)
            merged = [active_segments[0]]
            
            for segment in active_segments[1:]:
                if segment.start <= merged[-1].end:
                    merged[-1].end = max(merged[-1].end, segment.end)
                    merged[-1].rms_power = max(merged[-1].rms_power, segment.rms_power)
                else:
                    merged.append(segment)
            
            return merged
        
        return []


def remove_silence(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    threshold_db: float = -40.0,
    min_silence_duration: float = 0.5,
    min_sound_duration: float = 0.3,
    padding: float = 0.1,
    chunk_size: float = 0.05,
    aggressive_silence_rejection: bool = False,
    metadata: Optional[Dict[str, str]] = None,
) -> Tuple[float, float, float]:
    """
    Remove silence from a video file.
    
    Args:
        input_file: Path to the input video file.
        output_file: Path to save the output video file.
        threshold_db: Threshold in decibels below which audio is considered silence.
        min_silence_duration: Minimum duration in seconds for a segment to be considered silence.
        min_sound_duration: Minimum duration in seconds for a segment to be considered sound.
        padding: Padding in seconds to add before and after non-silent segments.
        chunk_size: Size of audio chunks for analysis in seconds.
        aggressive_silence_rejection: If True, uses additional algorithms to detect
            silences even in the presence of background noise.
        metadata: Optional dictionary of metadata to add to the output file.
        
    Returns:
        Tuple of (original_duration, output_duration, time_saved)
    """
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Create silence detector
    detector = SilenceDetector(
        threshold_db=threshold_db,
        min_silence_duration=min_silence_duration,
        min_sound_duration=min_sound_duration,
        padding=padding,
        chunk_size=chunk_size,
        aggressive_silence_rejection=aggressive_silence_rejection,
    )
    
    # Detect silence segments
    segments = detector.detect_silence_segments(input_file)
    active_segments = detector.get_active_segments(segments)
    
    # If no active segments were found, return the original video
    if not active_segments:
        logger.warning("No active segments found, returning original video")
        with VideoFileClip(input_file) as video:
            video.write_videofile(output_file, logger=None)
        return 0, 0, 0
    
    # Create subclips from the original video and concatenate them
    with VideoFileClip(input_file) as video:
        original_duration = video.duration
        original_size = video.size  # Store the original video dimensions
        
        subclips = []
        for segment in active_segments:
            # Ensure segment times are within video duration
            start = max(0, min(segment.start, original_duration))
            end = max(start, min(segment.end, original_duration))
            
            # Skip segments with zero duration
            if end <= start:
                continue
                
            subclips.append(video.subclip(start, end))
        
        if not subclips:
            logger.warning("No valid subclips found, returning original video")
            video.write_videofile(output_file, logger=None)
            return original_duration, original_duration, 0
        
        # Concatenate subclips, preserving the original size
        final_clip = concatenate_videoclips(subclips, method="compose")
        # Ensure the final clip has the same size as the original
        if final_clip.size != original_size:
            final_clip = final_clip.resize(width=original_size[0], height=original_size[1])
            
        output_duration = final_clip.duration
        time_saved = original_duration - output_duration
        
        logger.info(f"Original duration: {original_duration:.2f}s")
        logger.info(f"Output duration: {output_duration:.2f}s")
        logger.info(f"Time saved: {time_saved:.2f}s ({100 * time_saved / original_duration:.1f}%)")
        
        # Write output file with original size
        final_clip.write_videofile(output_file, logger=None)
        final_clip.close()
        
        # Clean up subclips to avoid memory leaks
        for clip in subclips:
            clip.close()
    
    return original_duration, output_duration, time_saved

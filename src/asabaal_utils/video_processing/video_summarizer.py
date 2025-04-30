"""
Video summarizer module for content-aware video summary generation.

This module provides utilities for automatically creating concise video
summaries by extracting the most engaging or important segments.
"""

import os
import logging
import tempfile
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import heapq

import numpy as np
from tqdm import tqdm
from moviepy.editor import VideoFileClip
from moviepy.editor import concatenate_videoclips, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import librosa
from scipy.signal import find_peaks
from scipy import stats
from PIL import Image, ImageStat

from .silence_detector import SilenceDetector
from .thumbnail_generator import ThumbnailGenerator
from .memory_utils import memory_adaptive_processing

logger = logging.getLogger(__name__)


class SummaryStyle(Enum):
    """Style options for video summaries."""
    HIGHLIGHTS = "highlights"  # Fast-paced montage style
    TRAILER = "trailer"        # Movie trailer style with tension build-up
    OVERVIEW = "overview"      # Balanced summary covering key moments
    TEASER = "teaser"          # Short teaser focusing on interesting bits
    CONDENSED = "condensed"    # Chronological mini-version of full video


@dataclass
class VideoSegment:
    """A segment of video with scoring information."""
    start_time: float
    end_time: float
    score: float = 0.0
    visual_interest: float = 0.0
    audio_interest: float = 0.0
    motion_level: float = 0.0
    speech_presence: float = 0.0
    peak_moment: bool = False
    representative: bool = False
    category: str = "general"
    
    @property
    def duration(self) -> float:
        """Get the duration of this segment."""
        return self.end_time - self.start_time


class VideoSummarizer:
    """
    Creates content-aware summaries of videos.
    
    This class analyzes videos to identify the most interesting or important
    segments and creates a shorter summary video.
    """
    
    def __init__(
        self,
        target_duration: float = 60.0,  # Target duration in seconds
        segment_length: float = 3.0,    # Default segment length in seconds
        min_segment_length: float = 2.0, # Minimum segment length to include
        max_segment_length: float = 10.0, # Maximum segment length to include
        frame_sample_rate: float = 2.0,  # Frames per second to analyze
        skip_start_percent: float = 0.05,
        skip_end_percent: float = 0.05,
        speech_weight: float = 1.0,
        visual_weight: float = 1.0,
        audio_weight: float = 0.8,
        motion_weight: float = 0.7,
        favor_beginning: bool = True,   # Include more content from beginning
        favor_ending: bool = True,      # Include more content from ending
        transition_duration: float = 0.5,
        summary_style: SummaryStyle = SummaryStyle.OVERVIEW,
        use_memory_adaptation: bool = True,
    ):
        """
        Initialize the video summarizer.
        
        Args:
            target_duration: Target duration for the summary in seconds
            segment_length: Default segment length in seconds
            min_segment_length: Minimum segment length to include
            max_segment_length: Maximum segment length to include
            frame_sample_rate: Frames per second to analyze
            skip_start_percent: Percentage of video to skip from the start
            skip_end_percent: Percentage of video to skip from the end
            speech_weight: Weight for speech presence in scoring
            visual_weight: Weight for visual interest in scoring
            audio_weight: Weight for audio interest in scoring
            motion_weight: Weight for motion level in scoring
            favor_beginning: Whether to favor segments at the beginning
            favor_ending: Whether to favor segments at the ending
            transition_duration: Duration for transitions between segments
            summary_style: Style of the summary to create
            use_memory_adaptation: Whether to use memory-adaptive processing
        """
        self.target_duration = target_duration
        self.segment_length = segment_length
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length
        self.frame_sample_rate = frame_sample_rate
        self.skip_start_percent = skip_start_percent
        self.skip_end_percent = skip_end_percent
        self.speech_weight = speech_weight
        self.visual_weight = visual_weight
        self.audio_weight = audio_weight
        self.motion_weight = motion_weight
        self.favor_beginning = favor_beginning
        self.favor_ending = favor_ending
        self.transition_duration = transition_duration
        self.summary_style = summary_style
        self.use_memory_adaptation = use_memory_adaptation
        
        # Silence detector for finding speech segments
        self.silence_detector = SilenceDetector(
            threshold_db=-35.0,  # Less sensitive than default
            min_silence_duration=1.0,
            min_sound_duration=0.2,
            padding=0.1
        )
        
        # Thumbnail generator for analyzing visual interest
        self.thumbnail_generator = ThumbnailGenerator(
            frames_to_extract=20,
            min_frame_interval=segment_length / 2,
            skip_start_percent=skip_start_percent,
            skip_end_percent=skip_end_percent
        )
    
    def _analyze_visual_interest(self, frame: np.ndarray) -> float:
        """
        Calculate visual interest score for a frame.
        
        Args:
            frame: Frame as numpy array
            
        Returns:
            Visual interest score (0-1)
        """
        # Convert to PIL for analysis
        pil_img = Image.fromarray(frame)
        
        # Calculate brightness
        gray = pil_img.convert("L")
        stat = ImageStat.Stat(gray)
        brightness = stat.mean[0] / 255.0
        
        # Calculate contrast
        extrema = gray.getextrema()
        contrast = (extrema[1] - extrema[0]) / 255.0
        
        # Calculate colorfulness - variance of color channels
        stat = ImageStat.Stat(pil_img)
        r_var = np.var(stat.mean[:3]) / 255.0
        colorfulness = min(1.0, r_var * 5)  # Scale up for better distribution
        
        # Calculate sharpness - standard deviation of Laplacian
        laplacian = pil_img.filter(Image.FIND_EDGES)
        stat = ImageStat.Stat(laplacian)
        sharpness = min(1.0, stat.stddev[0] / 50.0)  # Normalize to 0-1
        
        # Calculate visual complexity - approximate entropy of image
        gray_np = np.array(gray)
        gray_flat = gray_np.flatten()
        hist, _ = np.histogram(gray_flat, bins=32, range=(0, 255))
        hist = hist.astype(float) / len(gray_flat)
        hist = hist[hist > 0]  # Remove zeros
        entropy = -np.sum(hist * np.log2(hist))
        complexity = min(1.0, entropy / 5.0)  # Normalize to 0-1
        
        # Combine metrics with weights
        interest_score = (
            0.1 * (1 - abs(brightness - 0.5) * 2) +  # Mid-brightness is best
            0.3 * contrast +
            0.3 * colorfulness +
            0.2 * sharpness +
            0.1 * complexity
        )
        
        return min(1.0, max(0.0, interest_score))
    
    def _calculate_motion_level(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Calculate motion level between consecutive frames.
        
        Args:
            frame1: First frame as numpy array
            frame2: Second frame as numpy array
            
        Returns:
            Motion level score (0-1)
        """
        # Calculate mean absolute difference
        diff = np.abs(frame1.astype(float) - frame2.astype(float)) / 255.0
        
        # Compute median of differences to be robust to small changes
        motion_score = np.median(diff)
        
        # Scale the score to get better distribution
        scaled_score = min(1.0, motion_score * 10.0)
        
        return scaled_score
    
    def _analyze_audio_interest(self, audio: np.ndarray, sr: int) -> float:
        """
        Calculate audio interest score.
        
        Args:
            audio: Audio data as numpy array
            sr: Sample rate
            
        Returns:
            Audio interest score (0-1)
        """
        if len(audio) == 0:
            return 0.0
        
        # Calculate volume (RMS)
        rms = np.sqrt(np.mean(audio ** 2))
        volume = min(1.0, rms * 10.0)  # Scale for better distribution
        
        # Calculate spectral centroid (brightness)
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        normalized_centroids = spectral_centroids / (sr / 2)  # Normalize to 0-1
        brightness = np.mean(normalized_centroids)
        
        # Calculate spectral contrast
        try:
            contrast = np.mean(librosa.feature.spectral_contrast(y=audio, sr=sr))
            contrast = min(1.0, max(0.0, contrast / 50.0))  # Normalize
        except:
            contrast = 0.5  # Default if calculation fails
        
        # Calculate spectral flatness (noisiness vs. tonalness)
        flatness = np.mean(librosa.feature.spectral_flatness(y=audio))
        
        # Calculate audio complexity/variety
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        mfcc_var = np.var(mfccs, axis=1).mean()
        complexity = min(1.0, mfcc_var / 20.0)  # Normalize
        
        # Combine metrics with weights
        interest_score = (
            0.3 * volume +
            0.2 * brightness +
            0.2 * contrast +
            0.1 * (1 - flatness) +  # Lower flatness is more interesting
            0.2 * complexity
        )
        
        return min(1.0, max(0.0, interest_score))
    
    def _detect_speech_segments(self, audio: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """
        Detect segments containing speech.
        
        Args:
            audio: Audio data as numpy array
            sr: Sample rate
            
        Returns:
            List of (start_time, end_time) tuples for speech segments
        """
        # Simple method based on volume threshold and filtering
        
        # Calculate short-time energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        energy = np.array([
            np.sum(audio[i:i+frame_length]**2)
            for i in range(0, len(audio)-frame_length, hop_length)
        ])
        
        # Normalize energy
        energy = energy / energy.max() if energy.max() > 0 else energy
        
        # Apply threshold
        threshold = 0.1  # Adjustable threshold
        speech_frames = energy > threshold
        
        # Convert frames to time segments
        segments = []
        in_segment = False
        start_time = 0
        
        for i, is_speech in enumerate(speech_frames):
            time = i * hop_length / sr
            
            if is_speech and not in_segment:
                # Start of new segment
                start_time = time
                in_segment = True
            elif not is_speech and in_segment:
                # End of segment
                segments.append((start_time, time))
                in_segment = False
        
        # Add final segment if still in one
        if in_segment:
            segments.append((start_time, len(audio) / sr))
        
        # Merge segments that are close together
        merged_segments = []
        min_pause = 0.3  # Minimum pause to separate segments
        
        if segments:
            current_start, current_end = segments[0]
            
            for next_start, next_end in segments[1:]:
                if next_start - current_end <= min_pause:
                    # Merge with previous segment
                    current_end = next_end
                else:
                    # Add previous segment and start new one
                    merged_segments.append((current_start, current_end))
                    current_start, current_end = next_start, next_end
            
            # Add final segment
            merged_segments.append((current_start, current_end))
        
        return merged_segments
    
    def _score_segments(
        self,
        video: VideoFileClip,
        segment_times: List[Tuple[float, float]],
        speech_segments: List[Tuple[float, float]]
    ) -> List[VideoSegment]:
        """
        Score video segments based on interest metrics.
        
        Args:
            video: VideoFileClip to analyze
            segment_times: List of (start_time, end_time) tuples
            speech_segments: List of (start_time, end_time) tuples for speech
            
        Returns:
            List of VideoSegment objects with scores
        """
        logger.info(f"Scoring {len(segment_times)} segments")
        
        segments = []
        prev_frame = None
        
        for i, (start_time, end_time) in enumerate(tqdm(segment_times, desc="Scoring segments")):
            # Extract frames for this segment
            frame_times = np.arange(start_time, end_time, 1.0/self.frame_sample_rate)
            frames = []
            
            for time in frame_times:
                try:
                    frame = video.get_frame(time)
                    frames.append(frame)
                except Exception as e:
                    logger.warning(f"Error extracting frame at {time}: {e}")
            
            if not frames:
                logger.warning(f"No frames extracted for segment {i} ({start_time}-{end_time})")
                continue
            
            # Calculate visual interest
            visual_scores = []
            for frame in frames:
                visual_scores.append(self._analyze_visual_interest(frame))
            
            # Calculate motion level
            motion_scores = []
            if prev_frame is not None:
                motion_scores.append(self._calculate_motion_level(prev_frame, frames[0]))
            
            for j in range(1, len(frames)):
                motion_scores.append(self._calculate_motion_level(frames[j-1], frames[j]))
            
            if not motion_scores:
                motion_scores = [0.0]
            
            # Extract audio for this segment
            try:
                audio = video.audio.subclip(start_time, end_time)
                audio_data = audio.to_soundarray(fps=22050)
                
                # Convert stereo to mono if needed
                if audio_data.ndim > 1:
                    audio_data = audio_data.mean(axis=1)
                
                sr = 22050  # Sample rate
                
                # Calculate audio interest
                audio_interest = self._analyze_audio_interest(audio_data, sr)
                
                # Check speech presence
                segment_duration = end_time - start_time
                speech_duration = 0.0
                
                for speech_start, speech_end in speech_segments:
                    # Calculate overlap
                    overlap_start = max(start_time, speech_start)
                    overlap_end = min(end_time, speech_end)
                    
                    if overlap_end > overlap_start:
                        speech_duration += overlap_end - overlap_start
                
                speech_presence = speech_duration / segment_duration if segment_duration > 0 else 0.0
                
            except Exception as e:
                logger.warning(f"Error processing audio for segment {i}: {e}")
                audio_interest = 0.0
                speech_presence = 0.0
            
            # Calculate combined interest score
            visual_interest = np.mean(visual_scores)
            motion_level = np.mean(motion_scores)
            
            # Combine scores with weights
            score = (
                self.speech_weight * speech_presence +
                self.visual_weight * visual_interest +
                self.audio_weight * audio_interest +
                self.motion_weight * motion_level
            ) / (self.speech_weight + self.visual_weight + 
                 self.audio_weight + self.motion_weight)
            
            # Position-based scoring adjustments
            video_duration = video.duration
            relative_pos = start_time / video_duration
            
            # Favor beginning and ending if configured
            if self.favor_beginning and relative_pos < 0.2:
                # Boost score for first 20% of video
                boost = 0.2 * (1 - relative_pos / 0.2)
                score = min(1.0, score + boost)
            
            if self.favor_ending and relative_pos > 0.8:
                # Boost score for last 20% of video
                boost = 0.2 * ((relative_pos - 0.8) / 0.2)
                score = min(1.0, score + boost)
            
            # Create segment with scores
            segment = VideoSegment(
                start_time=start_time,
                end_time=end_time,
                score=score,
                visual_interest=visual_interest,
                audio_interest=audio_interest,
                motion_level=motion_level,
                speech_presence=speech_presence
            )
            
            segments.append(segment)
            
            # Update previous frame for next iteration
            prev_frame = frames[-1] if frames else None
        
        return segments
    
    def _detect_peaks(self, segments: List[VideoSegment]) -> List[VideoSegment]:
        """
        Detect peak moments (highly interesting segments).
        
        Args:
            segments: List of scored VideoSegment objects
            
        Returns:
            Updated list with peak_moment flags set
        """
        # Extract scores
        scores = np.array([s.score for s in segments])
        
        # Apply smoothing
        smoothed = np.convolve(scores, np.ones(5)/5, mode='same')
        
        # Find peaks
        try:
            peaks, _ = find_peaks(smoothed, height=0.6, distance=10)
        except:
            # Fallback if find_peaks fails
            peaks = []
            for i in range(2, len(smoothed) - 2):
                if (smoothed[i] > smoothed[i-1] and 
                    smoothed[i] > smoothed[i-2] and
                    smoothed[i] > smoothed[i+1] and
                    smoothed[i] > smoothed[i+2] and
                    smoothed[i] > 0.6):
                    peaks.append(i)
        
        # Mark peaks
        for idx in peaks:
            if 0 <= idx < len(segments):
                segments[idx].peak_moment = True
        
        return segments
    
    def _select_representative_segments(
        self, 
        segments: List[VideoSegment],
        num_representative: int = 10
    ) -> List[VideoSegment]:
        """
        Select representative segments from the video, distributed throughout.
        
        Args:
            segments: List of scored VideoSegment objects
            num_representative: Number of representative segments to select
            
        Returns:
            Updated list with representative flags set
        """
        if len(segments) <= num_representative:
            # All segments are representative if we have fewer than requested
            for segment in segments:
                segment.representative = True
            return segments
        
        # Divide video into equal sections and pick best segment from each
        sections = np.array_split(np.arange(len(segments)), num_representative)
        
        for section_indices in sections:
            if len(section_indices) == 0:
                continue
                
            # Get segments in this section
            section_segments = [segments[i] for i in section_indices]
            
            # Find segment with highest score in this section
            best_segment = max(section_segments, key=lambda s: s.score)
            
            # Find the index in the original list
            for i, segment in enumerate(segments):
                if segment is best_segment:
                    segments[i].representative = True
                    break
        
        return segments
    
    def _categorize_segments(self, segments: List[VideoSegment]) -> List[VideoSegment]:
        """
        Categorize segments based on their content characteristics.
        
        Args:
            segments: List of scored VideoSegment objects
            
        Returns:
            Updated list with category labels
        """
        for segment in segments:
            # Determine primary category based on metrics
            if segment.peak_moment:
                segment.category = "peak"
            elif segment.speech_presence > 0.7:
                segment.category = "speech"
            elif segment.motion_level > 0.7:
                segment.category = "action"
            elif segment.visual_interest > 0.7:
                segment.category = "visual"
            elif segment.audio_interest > 0.7:
                segment.category = "audio"
            elif segment.representative:
                segment.category = "representative"
            else:
                segment.category = "general"
        
        return segments
    
    def _select_segments_for_summary(
        self, 
        segments: List[VideoSegment],
        target_duration: float
    ) -> List[VideoSegment]:
        """
        Select segments to include in the summary based on style and target duration.
        
        Args:
            segments: List of scored VideoSegment objects
            target_duration: Target duration for summary in seconds
            
        Returns:
            List of selected segments for the summary
        """
        if not segments:
            return []
        
        # Sort segments by time to ensure chronological order
        sorted_segments = sorted(segments, key=lambda s: s.start_time)
        
        # Filter by minimum quality
        min_quality = 0.3  # Minimum quality threshold
        qualified_segments = [s for s in sorted_segments if s.score >= min_quality]
        
        if not qualified_segments:
            # Fall back to best segments if none meet minimum quality
            qualified_segments = sorted(sorted_segments, key=lambda s: s.score, reverse=True)[:5]
        
        # Different selection strategies based on summary style
        if self.summary_style == SummaryStyle.HIGHLIGHTS:
            # Emphasize peak moments and high scores
            # Sort by score and take top segments up to target duration
            selected = []
            total_duration = 0.0
            
            # First add peak moments
            peak_segments = [s for s in qualified_segments if s.peak_moment]
            peak_segments.sort(key=lambda s: s.score, reverse=True)
            
            for segment in peak_segments:
                if total_duration + segment.duration <= target_duration:
                    selected.append(segment)
                    total_duration += segment.duration
            
            # Then add other high-scoring segments
            remaining = [s for s in qualified_segments if s not in selected]
            remaining.sort(key=lambda s: s.score, reverse=True)
            
            for segment in remaining:
                if total_duration + segment.duration <= target_duration:
                    selected.append(segment)
                    total_duration += segment.duration
        
        elif self.summary_style == SummaryStyle.TRAILER:
            # Movie trailer style with tension build-up
            # Mix of chronological segments with emphasis on peaks
            selected = []
            total_duration = 0.0
            
            # Allocate portions to different segment types
            peak_allocation = 0.4  # 40% for peak moments
            intro_allocation = 0.2  # 20% for introduction
            ending_allocation = 0.2  # 20% for ending
            middle_allocation = 0.2  # 20% for middle content
            
            # Get peak segments
            peak_segments = [s for s in qualified_segments if s.peak_moment]
            peak_segments.sort(key=lambda s: s.score, reverse=True)
            
            # Get introduction segments (first 25% of video)
            intro_segments = [s for s in qualified_segments 
                             if s.start_time < sorted_segments[-1].start_time * 0.25]
            intro_segments.sort(key=lambda s: s.score, reverse=True)
            
            # Get ending segments (last 25% of video)
            ending_segments = [s for s in qualified_segments 
                              if s.start_time > sorted_segments[-1].start_time * 0.75]
            ending_segments.sort(key=lambda s: s.score, reverse=True)
            
            # Get middle segments
            middle_segments = [s for s in qualified_segments 
                              if s not in peak_segments + intro_segments + ending_segments]
            middle_segments.sort(key=lambda s: s.score, reverse=True)
            
            # Add segments from each category up to their allocation
            for category, allocation, segment_list in [
                ("peak", peak_allocation, peak_segments),
                ("intro", intro_allocation, intro_segments),
                ("ending", ending_allocation, ending_segments),
                ("middle", middle_allocation, middle_segments)
            ]:
                category_duration = 0.0
                category_target = target_duration * allocation
                
                for segment in segment_list:
                    if (category_duration + segment.duration <= category_target and
                        total_duration + segment.duration <= target_duration):
                        selected.append(segment)
                        category_duration += segment.duration
                        total_duration += segment.duration
        
        elif self.summary_style == SummaryStyle.TEASER:
            # Short teaser with high-interest moments
            # Prioritize variety and spread throughout video
            selected = []
            total_duration = 0.0
            
            # First add representative segments
            representative = [s for s in qualified_segments if s.representative]
            representative.sort(key=lambda s: s.score, reverse=True)
            
            for segment in representative[:3]:  # Limit to top 3
                if total_duration + segment.duration <= target_duration:
                    selected.append(segment)
                    total_duration += segment.duration
            
            # Then add peak moments not already included
            remaining_peaks = [s for s in qualified_segments 
                             if s.peak_moment and s not in selected]
            remaining_peaks.sort(key=lambda s: s.score, reverse=True)
            
            for segment in remaining_peaks[:2]:  # Limit to top 2
                if total_duration + segment.duration <= target_duration:
                    selected.append(segment)
                    total_duration += segment.duration
            
            # Fill remaining time with high-scoring segments
            remaining = [s for s in qualified_segments if s not in selected]
            remaining.sort(key=lambda s: s.score, reverse=True)
            
            for segment in remaining:
                if total_duration + segment.duration <= target_duration:
                    selected.append(segment)
                    total_duration += segment.duration
        
        elif self.summary_style == SummaryStyle.CONDENSED:
            # Chronological mini-version of the full video
            # Prioritize evenly distributed segments throughout
            
            # Use all representative segments as a starting point
            representative = [s for s in qualified_segments if s.representative]
            representative.sort(key=lambda s: s.start_time)
            
            # Calculate target number of segments based on average duration
            avg_duration = sum(s.duration for s in representative) / len(representative) if representative else 3.0
            target_segments = int(target_duration / avg_duration)
            
            # Ensure we don't exceed the target duration
            while representative and sum(s.duration for s in representative) > target_duration:
                # Remove the lowest scoring segment
                lowest_idx = min(range(len(representative)), key=lambda i: representative[i].score)
                representative.pop(lowest_idx)
            
            selected = representative
            
            # If we have room for more, add high-scoring segments not already included
            total_duration = sum(s.duration for s in selected)
            remaining = [s for s in qualified_segments if s not in selected]
            remaining.sort(key=lambda s: s.score, reverse=True)
            
            for segment in remaining:
                if total_duration + segment.duration <= target_duration:
                    selected.append(segment)
                    total_duration += segment.duration
        
        else:  # SummaryStyle.OVERVIEW or default
            # Balanced approach with focus on representative content
            selected = []
            total_duration = 0.0
            
            # Allocate portions to different segment types
            speech_allocation = 0.4  # 40% for speech segments
            peaks_allocation = 0.3   # 30% for peak moments
            visual_allocation = 0.2  # 20% for visually interesting segments
            other_allocation = 0.1   # 10% for other segments
            
            # Get segments by category
            speech_segments = [s for s in qualified_segments if s.category == "speech"]
            speech_segments.sort(key=lambda s: s.score, reverse=True)
            
            peak_segments = [s for s in qualified_segments if s.category == "peak"]
            peak_segments.sort(key=lambda s: s.score, reverse=True)
            
            visual_segments = [s for s in qualified_segments if s.category == "visual"]
            visual_segments.sort(key=lambda s: s.score, reverse=True)
            
            other_segments = [s for s in qualified_segments 
                            if s.category not in ["speech", "peak", "visual"]]
            other_segments.sort(key=lambda s: s.score, reverse=True)
            
            # Add segments from each category up to their allocation
            for category, allocation, segment_list in [
                ("speech", speech_allocation, speech_segments),
                ("peak", peaks_allocation, peak_segments),
                ("visual", visual_allocation, visual_segments),
                ("other", other_allocation, other_segments)
            ]:
                category_duration = 0.0
                category_target = target_duration * allocation
                
                for segment in segment_list:
                    if (category_duration + segment.duration <= category_target and
                        total_duration + segment.duration <= target_duration):
                        selected.append(segment)
                        category_duration += segment.duration
                        total_duration += segment.duration
            
            # If we still have room, add more representative segments
            remaining = [s for s in qualified_segments 
                       if s.representative and s not in selected]
            remaining.sort(key=lambda s: s.score, reverse=True)
            
            for segment in remaining:
                if total_duration + segment.duration <= target_duration:
                    selected.append(segment)
                    total_duration += segment.duration
        
        # Sort selected segments by time for chronological order
        selected.sort(key=lambda s: s.start_time)
        
        return selected
    
    def _create_summary_video(
        self, 
        video: VideoFileClip,
        selected_segments: List[VideoSegment],
        output_path: str
    ) -> None:
        """
        Create a summary video from selected segments.
        
        Args:
            video: Original VideoFileClip
            selected_segments: List of segments to include
            output_path: Path to save the output video
        """
        logger.info(f"Creating summary video with {len(selected_segments)} segments")
        
        if not selected_segments:
            logger.warning("No segments selected for summary")
            return
        
        # Store the original video size
        original_size = video.size
        
        # Extract subclips for each segment
        subclips = []
        
        for i, segment in enumerate(selected_segments):
            try:
                subclip = video.subclip(segment.start_time, segment.end_time)
                
                # Apply transition effects based on summary style
                if self.summary_style == SummaryStyle.HIGHLIGHTS:
                    # Fast-paced transitions
                    if i > 0:  # Don't apply to first clip
                        subclip = subclip.fx(fadein, min(0.2, segment.duration / 4))
                    if i < len(selected_segments) - 1:  # Don't apply to last clip
                        subclip = subclip.fx(fadeout, min(0.2, segment.duration / 4))
                
                elif self.summary_style == SummaryStyle.TRAILER:
                    # Dynamic transitions based on segment position
                    fade_duration = min(0.3, segment.duration / 3)
                    
                    if segment.category == "peak":
                        # Quick transitions for peak moments
                        subclip = subclip.fx(fadein, min(0.1, segment.duration / 5))
                    else:
                        # Standard fades for other segments
                        subclip = subclip.fx(fadein, fade_duration)
                    
                    # All clips fade out slightly
                    subclip = subclip.fx(fadeout, min(0.15, segment.duration / 4))
                
                else:
                    # Standard smooth transitions
                    transition_duration = min(self.transition_duration, segment.duration / 3)
                    
                    if i > 0:  # Don't apply to first clip
                        subclip = subclip.fx(fadein, transition_duration)
                    if i < len(selected_segments) - 1:  # Don't apply to last clip
                        subclip = subclip.fx(fadeout, transition_duration)
                
                subclips.append(subclip)
                
            except Exception as e:
                logger.warning(f"Error processing segment {i}: {e}")
        
        if not subclips:
            logger.error("Failed to create any valid subclips")
            return
        
        # Concatenate subclips
        try:
            final_video = concatenate_videoclips(subclips, method="compose")
            
            # Ensure the final video has the same size as the original
            if final_video.size != original_size:
                final_video = final_video.resize(width=original_size[0], height=original_size[1])
            
            # Add fade in/out to entire video
            final_video = final_video.fx(fadein, 0.5)
            final_video = final_video.fx(fadeout, 0.5)
            
            # Write output file
            logger.info(f"Writing summary video to {output_path}")
            # Use threads=1 to reduce memory usage
            final_video.write_videofile(output_path, threads=1)
            
            # Close clips
            final_video.close()
            for clip in subclips:
                clip.close()
                
        except Exception as e:
            logger.error(f"Error creating summary video: {e}")
            
            # Attempt to close clips
            for clip in subclips:
                try:
                    clip.close()
                except:
                    pass
    
    def _create_video_summary_impl(
        self,
        video_path: Union[str, Path],
        output_path: Union[str, Path],
        metadata_file: Optional[Union[str, Path]] = None
    ) -> List[Dict[str, Any]]:
        """
        Implementation of video summary creation (without memory adaptation).
        
        Args:
            video_path: Path to the input video file
            output_path: Path to save the summary video
            metadata_file: Optional path to save segment metadata as JSON
            
        Returns:
            List of dictionaries with segment information
        """
        video_path = str(video_path)
        output_path = str(output_path)
        
        logger.info(f"Creating summary for {video_path}")
        logger.info(f"Target duration: {self.target_duration}s")
        logger.info(f"Summary style: {self.summary_style.value}")
        
        segment_info = []
        
        with VideoFileClip(video_path) as video:
            # Calculate processing parameters
            duration = video.duration
            start_time = duration * self.skip_start_percent
            end_time = duration * (1.0 - self.skip_end_percent)
            effective_duration = end_time - start_time
            
            logger.info(f"Video duration: {duration:.2f}s")
            logger.info(f"Analyzing from {start_time:.2f}s to {end_time:.2f}s")
            
            # Generate segment boundaries
            # Approach 1: Fixed-length segments
            segment_times = []
            for t in np.arange(start_time, end_time, self.segment_length):
                segment_end = min(t + self.segment_length, end_time)
                segment_times.append((t, segment_end))
            
            # Extract audio for speech detection
            temp_audio_file = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_audio_file = temp_file.name
                    video.audio.write_audiofile(temp_audio_file, logger=None)
                
                # Load audio for speech detection
                y, sr = librosa.load(temp_audio_file, sr=22050)
                
                # Detect speech segments
                speech_segments = self._detect_speech_segments(y, sr)
                logger.info(f"Detected {len(speech_segments)} speech segments")
                
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                speech_segments = []
            
            finally:
                # Clean up temporary file
                if temp_audio_file and os.path.exists(temp_audio_file):
                    try:
                        os.unlink(temp_audio_file)
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary audio file: {e}")
            
            # Score segments
            segments = self._score_segments(video, segment_times, speech_segments)
            
            # Detect peak moments
            segments = self._detect_peaks(segments)
            
            # Select representative segments
            segments = self._select_representative_segments(segments)
            
            # Categorize segments
            segments = self._categorize_segments(segments)
            
            # Select segments for summary
            selected_segments = self._select_segments_for_summary(
                segments, self.target_duration
            )
            
            # Create summary video
            self._create_summary_video(video, selected_segments, output_path)
            
            # Prepare segment information for return
            for segment in selected_segments:
                mins_start = int(segment.start_time // 60)
                secs_start = int(segment.start_time % 60)
                mins_end = int(segment.end_time // 60)
                secs_end = int(segment.end_time % 60)
                
                segment_info.append({
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "duration": segment.duration,
                    "timestamp_str": f"{mins_start:02d}:{secs_start:02d} - {mins_end:02d}:{secs_end:02d}",
                    "score": round(segment.score, 3),
                    "category": segment.category,
                    "is_peak": segment.peak_moment,
                    "is_representative": segment.representative,
                    "metrics": {
                        "visual_interest": round(segment.visual_interest, 3),
                        "audio_interest": round(segment.audio_interest, 3),
                        "motion_level": round(segment.motion_level, 3),
                        "speech_presence": round(segment.speech_presence, 3)
                    }
                })
        
        # Save metadata if requested
        if metadata_file:
            metadata = {
                "video_file": video_path,
                "summary_file": output_path,
                "target_duration": self.target_duration,
                "actual_duration": sum(segment["duration"] for segment in segment_info),
                "summary_style": self.summary_style.value,
                "segments": segment_info
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved summary metadata to {metadata_file}")
        
        # Log summary information
        total_duration = sum(segment["duration"] for segment in segment_info)
        logger.info(f"Created summary with {len(segment_info)} segments")
        logger.info(f"Summary duration: {total_duration:.2f}s")
        
        return segment_info
    
    def create_video_summary(
        self, 
        video_path: Union[str, Path],
        output_path: Union[str, Path],
        metadata_file: Optional[Union[str, Path]] = None,
        strategy: Optional[str] = None,
        segment_count: Optional[int] = None,
        chunk_duration: Optional[float] = None,
        resolution_scale: Optional[float] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Create a content-aware summary of a video with memory adaptation.
        
        Args:
            video_path: Path to the input video file
            output_path: Path to save the summary video
            metadata_file: Optional path to save segment metadata as JSON
            strategy: Manual strategy selection (auto, full_quality, reduced_resolution, chunked, segment, streaming)
            segment_count: Number of segments to split video into when using segment strategy
            chunk_duration: Duration of each chunk in seconds when using chunked strategy
            resolution_scale: Scale factor for resolution when using reduced_resolution strategy
            
        Returns:
            List of dictionaries with segment information or
            Dict with processing results if memory adaptation is used
        """
        if not self.use_memory_adaptation:
            # Use the direct implementation without memory adaptation
            return self._create_video_summary_impl(
                video_path=video_path,
                output_path=output_path,
                metadata_file=metadata_file
            )
        
        # Prepare memory management options
        memory_options = {}
        if strategy:
            memory_options["strategy"] = strategy
        if segment_count is not None:
            memory_options["segment_count"] = segment_count
        if chunk_duration is not None:
            memory_options["chunk_duration"] = chunk_duration
        if resolution_scale is not None:
            memory_options["resolution_scale"] = resolution_scale
        
        # Use memory-adaptive processing with specific operation type
        result = memory_adaptive_processing(
            input_file=video_path,
            output_file=output_path,
            process_function=self._create_video_summary_impl,
            _operation_type='video_summary',  # Specify operation type for better memory estimation
            metadata_file=metadata_file,
            **memory_options
        )
        
        return result


def create_video_summary(
    video_path: Union[str, Path],
    output_path: Union[str, Path],
    target_duration: float = 60.0,
    summary_style: str = "overview",
    segment_length: float = 3.0,
    favor_beginning: bool = True,
    favor_ending: bool = True,
    metadata_file: Optional[Union[str, Path]] = None,
    use_memory_adaptation: bool = True,
    strategy: Optional[str] = None,
    segment_count: Optional[int] = None,
    chunk_duration: Optional[float] = None,
    resolution_scale: Optional[float] = None,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a content-aware summary of a video.
    
    Args:
        video_path: Path to the input video file
        output_path: Path to save the summary video
        target_duration: Target duration for the summary in seconds
        summary_style: Style of summary to create (highlights, trailer, overview, teaser, condensed)
        segment_length: Default segment length in seconds
        favor_beginning: Whether to favor segments at the beginning
        favor_ending: Whether to favor segments at the ending
        metadata_file: Optional path to save segment metadata as JSON
        use_memory_adaptation: Whether to use memory-adaptive processing
        strategy: Manual strategy selection (auto, full_quality, reduced_resolution, chunked, segment, streaming)
        segment_count: Number of segments to split video into when using segment strategy
        chunk_duration: Duration of each chunk in seconds when using chunked strategy
        resolution_scale: Scale factor for resolution when using reduced_resolution strategy
        
    Returns:
        List of dictionaries with segment information or
        Dict with processing results if memory adaptation is used
    """
    # Convert style string to enum
    try:
        style = SummaryStyle(summary_style.lower())
    except (ValueError, AttributeError):
        style = SummaryStyle.OVERVIEW
        logger.warning(f"Invalid summary style: {summary_style}, using 'overview'")
    
    # Create summarizer
    summarizer = VideoSummarizer(
        target_duration=target_duration,
        segment_length=segment_length,
        favor_beginning=favor_beginning,
        favor_ending=favor_ending,
        summary_style=style,
        use_memory_adaptation=use_memory_adaptation
    )
    
    # Create summary
    result = summarizer.create_video_summary(
        video_path=video_path,
        output_path=output_path,
        metadata_file=metadata_file,
        strategy=strategy,
        segment_count=segment_count,
        chunk_duration=chunk_duration,
        resolution_scale=resolution_scale
    )
    
    return result

"""
Thumbnail generator module for video processing.

This module provides utilities for automatically generating thumbnail
candidates from videos by analyzing content and extracting the most
visually appealing frames.
"""

import os
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
from tqdm import tqdm
from moviepy.video.io import VideoFileClip
from PIL import Image, ImageStat, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


@dataclass
class ThumbnailCandidate:
    """A candidate thumbnail extracted from a video."""
    timestamp: float
    frame_path: str
    quality_score: float
    width: int
    height: int
    brightness: float
    contrast: float
    colorfulness: float
    sharpness: float
    motion_score: float


class ThumbnailGenerator:
    """
    Generates candidate thumbnails from videos.
    
    This class analyzes videos and extracts frames that would make good thumbnails
    based on various quality metrics like brightness, contrast, colorfulness, etc.
    """
    
    def __init__(
        self,
        frames_to_extract: int = 10,
        min_frame_interval: float = 1.0,
        skip_start_percent: float = 0.05,
        skip_end_percent: float = 0.05,
        min_brightness: float = 0.2,
        max_brightness: float = 0.8,
        min_contrast: float = 0.4,
        min_colorfulness: float = 0.3,
        motion_threshold: float = 0.15,
        prefer_human_frames: bool = True,
        output_format: str = "jpg",
        output_quality: int = 90,
    ):
        """
        Initialize the thumbnail generator.
        
        Args:
            frames_to_extract: Number of candidate frames to extract
            min_frame_interval: Minimum interval between candidate frames in seconds
            skip_start_percent: Percentage of video to skip from the start
            skip_end_percent: Percentage of video to skip from the end
            min_brightness: Minimum brightness (0-1) for a good thumbnail
            max_brightness: Maximum brightness (0-1) for a good thumbnail
            min_contrast: Minimum contrast (0-1) for a good thumbnail
            min_colorfulness: Minimum colorfulness (0-1) for a good thumbnail
            motion_threshold: Motion threshold for selecting stable frames
            prefer_human_frames: If True, will prioritize frames with human subjects
            output_format: Format to save thumbnails (jpg, png)
            output_quality: Output quality (0-100) for JPEG format
        """
        self.frames_to_extract = frames_to_extract
        self.min_frame_interval = min_frame_interval
        self.skip_start_percent = skip_start_percent
        self.skip_end_percent = skip_end_percent
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.min_contrast = min_contrast
        self.min_colorfulness = min_colorfulness
        self.motion_threshold = motion_threshold
        self.prefer_human_frames = prefer_human_frames
        self.output_format = output_format.lower()
        self.output_quality = output_quality
        
        # Validate parameters
        if self.output_format not in ["jpg", "jpeg", "png"]:
            logger.warning(f"Unsupported output format: {self.output_format}, using jpg")
            self.output_format = "jpg"
        
        if self.output_quality < 1 or self.output_quality > 100:
            logger.warning(f"Invalid output quality: {self.output_quality}, using 90")
            self.output_quality = 90
    
    def _calculate_motion_score(self, frame: np.ndarray, prev_frame: Optional[np.ndarray]) -> float:
        """
        Calculate a motion score between the current frame and previous frame.
        
        Args:
            frame: Current frame as numpy array
            prev_frame: Previous frame as numpy array or None
            
        Returns:
            Motion score (0-1), where 0 indicates no motion
        """
        if prev_frame is None:
            return 0.0
        
        # Calculate mean absolute difference between frames
        diff = np.abs(frame.astype(np.float32) - prev_frame.astype(np.float32))
        motion_score = np.mean(diff) / 255.0
        
        return motion_score
    
    def _calculate_frame_metrics(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Calculate image quality metrics for a frame.
        
        Args:
            frame: Frame as numpy array
            
        Returns:
            Dictionary of quality metrics
        """
        # Convert to PIL Image for analysis
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
        laplacian = pil_img.filter(ImageFilter.FIND_EDGES)
        stat = ImageStat.Stat(laplacian)
        sharpness = min(1.0, stat.stddev[0] / 50.0)  # Normalize to 0-1
        
        return {
            "brightness": brightness,
            "contrast": contrast,
            "colorfulness": colorfulness,
            "sharpness": sharpness,
        }
    
    def _calculate_quality_score(self, metrics: Dict[str, float], motion_score: float) -> float:
        """
        Calculate an overall quality score for a frame based on its metrics.
        
        Args:
            metrics: Dictionary of frame quality metrics
            motion_score: Motion score for the frame
            
        Returns:
            Overall quality score (0-1)
        """
        # Define weights for different metrics
        weights = {
            "brightness": 1.0,
            "contrast": 1.5,
            "colorfulness": 2.0,
            "sharpness": 1.5,
            "motion": -3.0,  # Negative weight to penalize motion
        }
        
        # Calculate brightness score (highest in middle range)
        brightness = metrics["brightness"]
        if brightness < self.min_brightness or brightness > self.max_brightness:
            brightness_score = 0.3
        else:
            # Higher score for middle brightness (not too dark, not too bright)
            brightness_score = 1.0 - 2.0 * abs(brightness - 0.5)
        
        # Apply thresholds for minimum quality
        contrast_score = max(0, metrics["contrast"] - self.min_contrast) / (1.0 - self.min_contrast)
        colorfulness_score = max(0, metrics["colorfulness"] - self.min_colorfulness) / (1.0 - self.min_colorfulness)
        
        # Calculate motion penalty (stable frames get higher scores)
        motion_penalty = min(1.0, max(0, motion_score / self.motion_threshold))
        
        # Combine scores
        quality_score = (
            weights["brightness"] * brightness_score +
            weights["contrast"] * contrast_score +
            weights["colorfulness"] * colorfulness_score +
            weights["sharpness"] * metrics["sharpness"] +
            weights["motion"] * motion_penalty
        )
        
        # Normalize to 0-1 range
        max_possible_score = (
            weights["brightness"] + 
            weights["contrast"] + 
            weights["colorfulness"] + 
            weights["sharpness"]
        )
        quality_score = max(0, min(1, quality_score / max_possible_score))
        
        return quality_score
    
    def generate_thumbnails(
        self, 
        video_path: Union[str, Path], 
        output_dir: Optional[Union[str, Path]] = None,
        save_frames: bool = True,
        metadata_file: Optional[Union[str, Path]] = None
    ) -> List[ThumbnailCandidate]:
        """
        Generate candidate thumbnails from a video.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save thumbnails (if None, creates a temp dir)
            save_frames: If True, saves the candidate frames to disk
            metadata_file: Optional path to save thumbnail metadata as JSON
            
        Returns:
            List of ThumbnailCandidate objects.
        """
        video_path = str(video_path)
        logger.info(f"Generating thumbnails for {video_path}")
        
        # Create output directory if needed
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="thumbnails_")
            logger.info(f"Created temporary thumbnail directory: {output_dir}")
        else:
            output_dir = str(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Saving thumbnails to: {output_dir}")
        
        # Extract video basename without extension
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        
        candidates = []
        
        with VideoFileClip(video_path) as video:
            # Calculate frame sampling parameters
            duration = video.duration
            start_time = duration * self.skip_start_percent
            end_time = duration * (1.0 - self.skip_end_percent)
            effective_duration = end_time - start_time
            
            # Calculate frame sampling interval
            sampling_interval = max(
                self.min_frame_interval,
                effective_duration / (self.frames_to_extract * 3)  # 3x oversampling
            )
            
            # Extract and analyze frames
            logger.info(f"Analyzing video frames every {sampling_interval:.2f} seconds")
            
            prev_frame = None
            candidate_times = []
            
            # First pass: analyze frames and collect candidates
            for time in tqdm(np.arange(start_time, end_time, sampling_interval), desc="Analyzing frames"):
                # Extract frame at the specified time
                frame = video.get_frame(time)
                
                # Calculate motion score
                motion_score = self._calculate_motion_score(frame, prev_frame)
                
                # Calculate frame metrics
                metrics = self._calculate_frame_metrics(frame)
                
                # Calculate overall quality score
                quality_score = self._calculate_quality_score(metrics, motion_score)
                
                # Record as candidate if it meets basic criteria
                if (metrics["brightness"] >= self.min_brightness and 
                    metrics["brightness"] <= self.max_brightness and
                    metrics["contrast"] >= self.min_contrast and
                    metrics["colorfulness"] >= self.min_colorfulness and
                    motion_score <= self.motion_threshold):
                    
                    candidate_times.append((time, quality_score, metrics, motion_score))
                
                # Update previous frame
                prev_frame = frame
            
            # Sort candidates by quality score
            candidate_times.sort(key=lambda x: x[1], reverse=True)
            
            # Second pass: extract top candidates with sufficient spacing
            final_candidates = []
            min_spacing = self.min_frame_interval * 2  # Ensure good spacing between candidates
            
            for time, score, metrics, motion_score in candidate_times:
                # Skip if too close to an existing candidate
                if any(abs(time - c[0]) < min_spacing for c in final_candidates):
                    continue
                
                final_candidates.append((time, score, metrics, motion_score))
                
                # Stop when we have enough candidates
                if len(final_candidates) >= self.frames_to_extract:
                    break
            
            # Sort final candidates by timestamp
            final_candidates.sort(key=lambda x: x[0])
            
            # Save frames and create ThumbnailCandidate objects
            for i, (time, score, metrics, motion_score) in enumerate(final_candidates):
                # Format timestamp for filename
                timestamp_str = f"{int(time // 60):02d}_{int(time % 60):02d}"
                frame_filename = f"{video_basename}_thumb_{i+1:02d}_{timestamp_str}.{self.output_format}"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # Save frame if requested
                if save_frames:
                    frame = video.get_frame(time)
                    img = Image.fromarray(frame)
                    
                    if self.output_format in ["jpg", "jpeg"]:
                        img.save(frame_path, "JPEG", quality=self.output_quality)
                    else:
                        img.save(frame_path, "PNG")
                
                # Create candidate object
                candidate = ThumbnailCandidate(
                    timestamp=time,
                    frame_path=frame_path,
                    quality_score=score,
                    width=video.size[0],
                    height=video.size[1],
                    brightness=metrics["brightness"],
                    contrast=metrics["contrast"],
                    colorfulness=metrics["colorfulness"],
                    sharpness=metrics["sharpness"],
                    motion_score=motion_score
                )
                
                candidates.append(candidate)
        
        # Save metadata if requested
        if metadata_file is not None:
            metadata = [{
                "timestamp": candidate.timestamp,
                "frame_path": candidate.frame_path,
                "quality_score": candidate.quality_score,
                "brightness": candidate.brightness,
                "contrast": candidate.contrast,
                "colorfulness": candidate.colorfulness,
                "sharpness": candidate.sharpness,
                "motion_score": candidate.motion_score,
                "dimensions": f"{candidate.width}x{candidate.height}"
            } for candidate in candidates]
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved metadata to {metadata_file}")
        
        return candidates


def generate_thumbnails(
    video_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    frames_to_extract: int = 10,
    min_frame_interval: float = 1.0,
    skip_start_percent: float = 0.05,
    skip_end_percent: float = 0.05,
    output_format: str = "jpg",
    output_quality: int = 90,
    metadata_file: Optional[Union[str, Path]] = None
) -> List[Dict[str, Any]]:
    """
    Generate candidate thumbnails from a video.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save thumbnails (if None, creates a temp dir)
        frames_to_extract: Number of candidate frames to extract
        min_frame_interval: Minimum interval between candidate frames in seconds
        skip_start_percent: Percentage of video to skip from the start
        skip_end_percent: Percentage of video to skip from the end
        output_format: Format to save thumbnails ("jpg" or "png")
        output_quality: Output quality for JPEG format (1-100)
        metadata_file: Optional path to save thumbnail metadata as JSON
        
    Returns:
        List of dictionaries with thumbnail information
    """
    # Create the generator with the specified parameters
    generator = ThumbnailGenerator(
        frames_to_extract=frames_to_extract,
        min_frame_interval=min_frame_interval,
        skip_start_percent=skip_start_percent,
        skip_end_percent=skip_end_percent,
        output_format=output_format,
        output_quality=output_quality
    )
    
    # Generate thumbnails
    candidates = generator.generate_thumbnails(
        video_path=video_path,
        output_dir=output_dir,
        save_frames=True,
        metadata_file=metadata_file
    )
    
    # Convert to list of dictionaries
    result = []
    for i, candidate in enumerate(candidates):
        mins = int(candidate.timestamp // 60)
        secs = int(candidate.timestamp % 60)
        
        result.append({
            "index": i + 1,
            "timestamp": candidate.timestamp,
            "timestamp_str": f"{mins:02d}:{secs:02d}",
            "quality_score": round(candidate.quality_score, 3),
            "frame_path": candidate.frame_path,
            "dimensions": f"{candidate.width}x{candidate.height}",
            "metrics": {
                "brightness": round(candidate.brightness, 3),
                "contrast": round(candidate.contrast, 3),
                "colorfulness": round(candidate.colorfulness, 3),
                "sharpness": round(candidate.sharpness, 3),
                "motion_score": round(candidate.motion_score, 3)
            }
        })
    
    return result

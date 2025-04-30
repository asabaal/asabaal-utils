"""
Jump cut detector module for video processing.

This module provides utilities for detecting and optionally smoothing jump cuts in videos.
"""

import os
import logging
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import math

import numpy as np
from tqdm import tqdm

from moviepy.editor import concatenate_videoclips, VideoFileClip, CompositeVideoClip
from moviepy.video.VideoClip import VideoClip, ColorClip
from moviepy.video.compositing.transitions import crossfadein
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from PIL import Image, ImageChops, ImageFilter
from scipy.ndimage import gaussian_filter
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """Types of transitions that can be applied to jump cuts."""
    CROSSFADE = "crossfade"
    FADE_BLACK = "fade_black"
    FADE_WHITE = "fade_white"
    DISSOLVE = "dissolve"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    WIPE_UP = "wipe_up"
    WIPE_DOWN = "wipe_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    NONE = "none"  # No transition, just for detection


@dataclass
class JumpCut:
    """A detected jump cut in a video."""
    frame_index: int
    timestamp: float
    similarity_score: float
    difference_score: float
    motion_score: float
    color_change_score: float
    total_score: float
    confidence: float
    frame_before_path: str = ""
    frame_after_path: str = ""
    suggested_transition: TransitionType = TransitionType.NONE
    transition_duration: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "frame_index": self.frame_index,
            "timestamp": self.timestamp,
            "similarity_score": self.similarity_score,
            "difference_score": self.difference_score,
            "motion_score": self.motion_score,
            "color_change_score": self.color_change_score,
            "total_score": self.total_score,
            "confidence": self.confidence,
            "frame_before_path": self.frame_before_path,
            "frame_after_path": self.frame_after_path,
            "suggested_transition": self.suggested_transition.value,
            "transition_duration": self.transition_duration
        }


class JumpCutDetector:
    """
    Detector for jump cuts in videos.
    
    This class analyzes videos to detect jump cuts (abrupt transitions between shots)
    and can optionally apply smoothing transitions.
    """
    
    def __init__(
        self,
        sensitivity: float = 0.5,  # 0.0-1.0, higher means more sensitive
        min_jump_interval: float = 0.5,  # Minimum time between detected jump cuts
        frame_sample_rate: float = 10.0,  # Frames per second to analyze
        skip_start_percent: float = 0.0,
        skip_end_percent: float = 0.0,
        save_frames: bool = True,
        similarity_weight: float = 1.0,
        difference_weight: float = 1.0,
        motion_weight: float = 0.8,
        color_weight: float = 0.6,
        smoothing_window: int = 3,  # Number of frames to smooth detection results
    ):
        """
        Initialize the jump cut detector.
        
        Args:
            sensitivity: Sensitivity for detection (0.0-1.0, higher means more sensitive)
            min_jump_interval: Minimum interval between detected jump cuts in seconds
            frame_sample_rate: Frames per second to analyze
            skip_start_percent: Percentage of video to skip from the start
            skip_end_percent: Percentage of video to skip from the end
            save_frames: Whether to save frames before and after jump cuts
            similarity_weight: Weight of structural similarity in detection
            difference_weight: Weight of pixel differences in detection
            motion_weight: Weight of motion detection in detection
            color_weight: Weight of color changes in detection
            smoothing_window: Number of frames to smooth detection results
        """
        self.sensitivity = sensitivity
        self.min_jump_interval = min_jump_interval
        self.frame_sample_rate = frame_sample_rate
        self.skip_start_percent = skip_start_percent
        self.skip_end_percent = skip_end_percent
        self.save_frames = save_frames
        self.similarity_weight = similarity_weight
        self.difference_weight = difference_weight
        self.motion_weight = motion_weight
        self.color_weight = color_weight
        self.smoothing_window = smoothing_window
        
        # Thresholds based on sensitivity
        self.similarity_threshold = 0.8 - (sensitivity * 0.3)  # Lower is more sensitive
        self.difference_threshold = 0.1 + (sensitivity * 0.2)  # Higher is more sensitive
        self.motion_threshold = 0.1 + (sensitivity * 0.2)  # Higher is more sensitive
        self.color_threshold = 0.1 + (sensitivity * 0.2)  # Higher is more sensitive
    
    def _calculate_frame_difference(
        self, 
        frame1: np.ndarray, 
        frame2: np.ndarray
    ) -> Tuple[float, float, float, float]:
        """
        Calculate various difference metrics between two frames.
        
        Args:
            frame1: First frame as numpy array
            frame2: Second frame as numpy array
            
        Returns:
            Tuple of (similarity_score, difference_score, motion_score, color_change_score)
        """
        # Convert to grayscale for structural similarity
        gray1 = np.mean(frame1, axis=2).astype(np.uint8)
        gray2 = np.mean(frame2, axis=2).astype(np.uint8)
        
        # Calculate structural similarity
        try:
            similarity_score = ssim(gray1, gray2)
        except Exception:
            # Fallback if SSIM fails (e.g., if images are too different)
            similarity_score = 0.0
        
        # Calculate mean absolute difference
        diff = np.abs(frame1.astype(np.float32) - frame2.astype(np.float32))
        difference_score = np.mean(diff) / 255.0
        
        # Calculate motion score using edge detection and difference
        # Convert to PIL for edge detection
        pil_img1 = Image.fromarray(gray1)
        pil_img2 = Image.fromarray(gray2)
        
        # Apply edge detection
        edges1 = pil_img1.filter(ImageFilter.FIND_EDGES)
        edges2 = pil_img2.filter(ImageFilter.FIND_EDGES)
        
        # Calculate edge difference
        edge_diff = ImageChops.difference(edges1, edges2)
        edge_diff_array = np.array(edge_diff)
        motion_score = np.mean(edge_diff_array) / 255.0
        
        # Calculate color histogram difference
        hist1 = np.histogram(frame1, bins=64, range=(0, 255))[0]
        hist2 = np.histogram(frame2, bins=64, range=(0, 255))[0]
        
        # Normalize histograms
        hist1 = hist1.astype(float) / np.sum(hist1)
        hist2 = hist2.astype(float) / np.sum(hist2)
        
        # Calculate histogram difference
        color_change_score = np.sum(np.abs(hist1 - hist2)) / 2.0  # Normalized to 0-1
        
        return similarity_score, difference_score, motion_score, color_change_score
    
    def _get_transition_type(
        self, 
        frame1: np.ndarray, 
        frame2: np.ndarray, 
        similarity: float, 
        difference: float
    ) -> Tuple[TransitionType, float]:
        """
        Determine the best transition type for a jump cut.
        
        Args:
            frame1: Frame before jump cut
            frame2: Frame after jump cut
            similarity: Similarity score between frames
            difference: Difference score between frames
            
        Returns:
            Tuple of (transition_type, duration)
        """
        # Calculate brightness of both frames
        brightness1 = np.mean(frame1) / 255.0
        brightness2 = np.mean(frame2) / 255.0
        
        # Calculate overall motion direction using optical flow approximation
        h, w = frame1.shape[:2]
        center_before = frame1[h//4:3*h//4, w//4:3*w//4]
        center_after = frame2[h//4:3*h//4, w//4:3*w//4]
        
        # A very simple approximation of dominant motion
        diff_left = np.mean(np.abs(frame1[:, :w//2] - frame2[:, w//2:]))
        diff_right = np.mean(np.abs(frame1[:, w//2:] - frame2[:, :w//2]))
        diff_up = np.mean(np.abs(frame1[:h//2, :] - frame2[h//2:, :]))
        diff_down = np.mean(np.abs(frame1[h//2:, :] - frame2[:h//2, :]))
        
        # Find the most likely motion direction
        motion_scores = {
            TransitionType.WIPE_LEFT: diff_left,
            TransitionType.WIPE_RIGHT: diff_right,
            TransitionType.WIPE_UP: diff_up,
            TransitionType.WIPE_DOWN: diff_down
        }
        
        # Determine transition type
        if similarity < 0.2:  # Very different shots
            if abs(brightness1 - brightness2) > 0.3:
                # Significant brightness change
                if brightness1 < brightness2:
                    # Going from dark to light
                    transition = TransitionType.FADE_WHITE
                else:
                    # Going from light to dark
                    transition = TransitionType.FADE_BLACK
            else:
                # Similar brightness, use directional wipe or crossfade
                if max(motion_scores.values()) > 0.2:
                    # Clear motion direction, use wipe
                    transition = max(motion_scores.items(), key=lambda x: x[1])[0]
                else:
                    # No clear direction, use crossfade
                    transition = TransitionType.CROSSFADE
        else:
            # More similar shots
            if difference > 0.4:
                # Still quite different, use dissolve
                transition = TransitionType.DISSOLVE
            else:
                # Minor difference, use subtle crossfade
                transition = TransitionType.CROSSFADE
        
        # Determine duration based on difference
        # More different shots need longer transitions
        base_duration = 0.5
        if difference > 0.6:
            duration = base_duration + 0.5  # 1.0 second
        elif difference > 0.4:
            duration = base_duration + 0.3  # 0.8 seconds
        elif difference > 0.2:
            duration = base_duration         # 0.5 seconds
        else:
            duration = base_duration - 0.2  # 0.3 seconds
        
        return transition, duration
    
    def _save_frame_pair(
        self, 
        frame1: np.ndarray, 
        frame2: np.ndarray, 
        output_dir: str,
        index: int
    ) -> Tuple[str, str]:
        """
        Save a pair of frames before and after a jump cut.
        
        Args:
            frame1: Frame before jump cut
            frame2: Frame after jump cut
            output_dir: Directory to save frames
            index: Index of the jump cut
            
        Returns:
            Tuple of (path_to_frame1, path_to_frame2)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save frames
        frame1_path = os.path.join(output_dir, f"jump_cut_{index:03d}_before.jpg")
        frame2_path = os.path.join(output_dir, f"jump_cut_{index:03d}_after.jpg")
        
        Image.fromarray(frame1).save(frame1_path, quality=95)
        Image.fromarray(frame2).save(frame2_path, quality=95)
        
        return frame1_path, frame2_path
    
    def detect_jump_cuts(
        self, 
        video_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        metadata_file: Optional[Union[str, Path]] = None
    ) -> List[JumpCut]:
        """
        Detect jump cuts in a video.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save output files (if None, creates a temp dir)
            metadata_file: Optional path to save jump cut metadata as JSON
            
        Returns:
            List of JumpCut objects
        """
        video_path = str(video_path)
        logger.info(f"Detecting jump cuts in {video_path}")
        
        # Create output directory if needed
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="jump_cuts_")
            logger.info(f"Created temporary output directory: {output_dir}")
        else:
            output_dir = str(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Saving jump cut detection to: {output_dir}")
        
        # Extract video basename without extension
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        
        jump_cuts = []
        
        # Process the video
        with VideoFileClip(video_path) as video:
            # Calculate processing parameters
            duration = video.duration
            start_time = duration * self.skip_start_percent
            end_time = duration * (1.0 - self.skip_end_percent)
            
            # Calculate frame sampling interval
            frame_interval = 1.0 / self.frame_sample_rate
            sample_times = np.arange(start_time, end_time, frame_interval)
            
            # Extract frames
            frames = []
            timestamps = []
            
            logger.info(f"Sampling {len(sample_times)} frames for analysis")
            
            for time in tqdm(sample_times, desc="Extracting frames"):
                frame = video.get_frame(time)
                frames.append(frame)
                timestamps.append(time)
            
            # Analyze consecutive frames for jump cuts
            logger.info("Analyzing frames for jump cuts")
            frame_scores = []
            
            for i in tqdm(range(1, len(frames)), desc="Analyzing frame pairs"):
                prev_frame = frames[i-1]
                curr_frame = frames[i]
                
                # Calculate frame differences
                similarity, difference, motion, color_change = self._calculate_frame_difference(
                    prev_frame, curr_frame
                )
                
                # Calculate weighted score
                total_score = (
                    (1 - similarity) * self.similarity_weight +
                    difference * self.difference_weight +
                    motion * self.motion_weight +
                    color_change * self.color_weight
                ) / (self.similarity_weight + self.difference_weight + 
                     self.motion_weight + self.color_weight)
                
                frame_scores.append({
                    "frame_index": i,
                    "timestamp": timestamps[i],
                    "similarity_score": similarity,
                    "difference_score": difference,
                    "motion_score": motion,
                    "color_change_score": color_change,
                    "total_score": total_score
                })
            
            # Smooth scores to reduce false positives
            if self.smoothing_window > 1:
                smoothed_scores = []
                window = self.smoothing_window
                
                for i in range(len(frame_scores)):
                    start_idx = max(0, i - window // 2)
                    end_idx = min(len(frame_scores), i + window // 2 + 1)
                    window_scores = [frame_scores[j]["total_score"] for j in range(start_idx, end_idx)]
                    # Use median for robustness
                    smoothed_score = np.median(window_scores)
                    
                    smoothed_scores.append(smoothed_score)
                
                # Update original scores
                for i, score in enumerate(smoothed_scores):
                    frame_scores[i]["total_score"] = score
            
            # Apply threshold and identify potential jump cuts
            # A jump cut needs to have a high total score (indicating significant change)
            threshold = 0.2 + (self.sensitivity * 0.3)  # Adjust based on sensitivity
            
            potential_cuts = []
            for score in frame_scores:
                if score["total_score"] > threshold:
                    potential_cuts.append(score)
            
            # Filter out jump cuts that are too close together
            filtered_cuts = []
            if potential_cuts:
                filtered_cuts = [potential_cuts[0]]
                
                for cut in potential_cuts[1:]:
                    last_cut = filtered_cuts[-1]
                    if cut["timestamp"] - last_cut["timestamp"] >= self.min_jump_interval:
                        filtered_cuts.append(cut)
            
            # Create JumpCut objects
            for i, cut in enumerate(filtered_cuts):
                # Determine confidence based on how much the score exceeds the threshold
                confidence = min(1.0, (cut["total_score"] - threshold) / threshold)
                
                # Get frames before and after the cut
                frame_idx = cut["frame_index"]
                frame_before = frames[frame_idx - 1]
                frame_after = frames[frame_idx]
                
                # Determine best transition type
                transition_type, transition_duration = self._get_transition_type(
                    frame_before, frame_after,
                    cut["similarity_score"], cut["difference_score"]
                )
                
                # Save frames if requested
                frame_before_path = ""
                frame_after_path = ""
                if self.save_frames:
                    frame_before_path, frame_after_path = self._save_frame_pair(
                        frame_before, frame_after,
                        output_dir, i+1
                    )
                
                jump_cut = JumpCut(
                    frame_index=frame_idx,
                    timestamp=cut["timestamp"],
                    similarity_score=cut["similarity_score"],
                    difference_score=cut["difference_score"],
                    motion_score=cut["motion_score"],
                    color_change_score=cut["color_change_score"],
                    total_score=cut["total_score"],
                    confidence=confidence,
                    frame_before_path=frame_before_path,
                    frame_after_path=frame_after_path,
                    suggested_transition=transition_type,
                    transition_duration=transition_duration
                )
                
                jump_cuts.append(jump_cut)
        
        # Save metadata if requested
        if metadata_file:
            metadata = {
                "video_file": video_path,
                "settings": {
                    "sensitivity": self.sensitivity,
                    "min_jump_interval": self.min_jump_interval,
                    "frame_sample_rate": self.frame_sample_rate
                },
                "jump_cuts": [cut.to_dict() for cut in jump_cuts]
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved jump cut metadata to {metadata_file}")
        
        return jump_cuts
    
    def _apply_transition(
        self, 
        clip1: VideoClip, 
        clip2: VideoClip, 
        transition_type: TransitionType,
        duration: float
    ) -> VideoClip:
        """
        Apply a transition between two video clips.
        
        Args:
            clip1: First video clip
            clip2: Second video clip
            transition_type: Type of transition to apply
            duration: Duration of the transition in seconds
            
        Returns:
            VideoClip with the transition applied
        """
        # Adjust duration to not exceed clip lengths
        duration = min(duration, clip1.duration / 2, clip2.duration / 2)
        
        if transition_type == TransitionType.CROSSFADE:
            # Simple crossfade transition
            clip2 = clip2.with_start(clip1.end - duration)
            clip2 = crossfadein(clip2, duration)
            return CompositeVideoClip([clip1, clip2])
        
        elif transition_type == TransitionType.FADE_BLACK:
            # Fade to black transition
            clip1 = clip1.fx(fadeout, duration)
            clip2 = clip2.fx(fadein, duration)
            clip2 = clip2.with_start(clip1.end)
            return concatenate_videoclips([clip1, clip2])
        
        elif transition_type == TransitionType.FADE_WHITE:
            # Fade to white transition
            # Create white clip for the transition
            white_clip = ColorClip(
                size=clip1.size, 
                color=(255, 255, 255),
                duration=duration / 2
            )
            white_clip = white_clip.with_start(clip1.end - duration / 2)
            
            # Fade out clip1 to white
            clip1 = clip1.fx(fadeout, duration)
            
            # Fade in clip2 from white
            clip2 = clip2.fx(fadein, duration)
            clip2 = clip2.with_start(clip1.end)
            
            return CompositeVideoClip([clip1, white_clip, clip2])
        
        elif transition_type == TransitionType.DISSOLVE:
            # Similar to crossfade but with a slight brightness increase
            clip2 = clip2.with_start(clip1.end - duration)
            
            # Add slight brightness increase during transition
            def brightness_increase(gf, t):
                """Temporary brightness increase during dissolve."""
                if t < (clip1.end - duration) or t > clip1.end:
                    # Outside transition, no change
                    return gf(t)
                else:
                    # During transition, increase brightness
                    progress = (t - (clip1.end - duration)) / duration
                    # Bell curve brightness - peaks in middle of transition
                    brightness = 1.0 + 0.2 * math.sin(progress * math.pi)
                    return np.minimum(gf(t) * brightness, 255).astype('uint8')
            
            # Apply brightness effect and crossfade
            clip1 = clip1.fl(brightness_increase)
            clip2 = clip2.fl(brightness_increase)
            clip2 = crossfadein(clip2, duration)
            
            return CompositeVideoClip([clip1, clip2])
        
        elif transition_type in [TransitionType.WIPE_LEFT, TransitionType.WIPE_RIGHT, 
                                TransitionType.WIPE_UP, TransitionType.WIPE_DOWN]:
            # Directional wipe transitions
            clip2 = clip2.with_start(clip1.end - duration)
            
            # Create a mask clip for the wipe
            w, h = clip1.size
            
            def wipe_mask_function(t):
                """Create a wipe mask."""
                progress = (t - (clip1.end - duration)) / duration
                progress = max(0, min(1, progress))
                
                mask = np.zeros((h, w), dtype=np.uint8)
                
                if transition_type == TransitionType.WIPE_LEFT:
                    # Wipe from right to left
                    x_cutoff = int(w * (1 - progress))
                    mask[:, :x_cutoff] = 255
                
                elif transition_type == TransitionType.WIPE_RIGHT:
                    # Wipe from left to right
                    x_cutoff = int(w * progress)
                    mask[:, x_cutoff:] = 255
                
                elif transition_type == TransitionType.WIPE_UP:
                    # Wipe from bottom to top
                    y_cutoff = int(h * (1 - progress))
                    mask[:y_cutoff, :] = 255
                
                elif transition_type == TransitionType.WIPE_DOWN:
                    # Wipe from top to bottom
                    y_cutoff = int(h * progress)
                    mask[y_cutoff:, :] = 255
                
                # Add feathering to the edge for smoother transition
                mask = gaussian_filter(mask, sigma=5)
                
                return mask
            
            # Create the mask clip
            mask_clip = VideoClip(
                make_frame=lambda t: wipe_mask_function(t),
                duration=clip2.duration
            )
            
            # Apply the mask to clip2
            clip2 = clip2.with_mask(mask_clip)
            
            return CompositeVideoClip([clip1, clip2])
        
        elif transition_type == TransitionType.ZOOM_IN:
            # Zoom in transition
            clip2 = clip2.with_start(clip1.end - duration)
            
            # Create zoom effect on clip1
            def zoom_in_transform(t):
                """Zoom in transform function."""
                if t < (clip1.end - duration) or t > clip1.end:
                    # Outside transition, no zoom
                    return {'zoom': 1.0}
                else:
                    # During transition, zoom in
                    progress = (t - (clip1.end - duration)) / duration
                    zoom = 1.0 + (0.3 * progress)
                    return {'zoom': zoom}
            
            # Apply zoom effect and crossfade
            clip1 = clip1.transform(zoom_in_transform)
            clip2 = crossfadein(clip2, duration)
            
            return CompositeVideoClip([clip1, clip2])
        
        elif transition_type == TransitionType.ZOOM_OUT:
            # Zoom out transition
            clip2 = clip2.with_start(clip1.end - duration)
            
            # Create zoom effect on clip2
            def zoom_out_transform(t):
                """Zoom out transform function."""
                if t < clip2.start or t > (clip2.start + duration):
                    # Outside transition, no zoom
                    return {'zoom': 1.0}
                else:
                    # During transition, start zoomed in and zoom out
                    progress = (t - clip2.start) / duration
                    zoom = 1.3 - (0.3 * progress)
                    return {'zoom': zoom}
            
            # Apply zoom effect and crossfade
            clip2 = clip2.transform(zoom_out_transform)
            clip2 = crossfadein(clip2, duration)
            
            return CompositeVideoClip([clip1, clip2])
        
        else:
            # Default: no transition, just concatenate
            return concatenate_videoclips([clip1, clip2])
    
    def smooth_jump_cuts(
        self, 
        video_path: Union[str, Path],
        jump_cuts: List[JumpCut],
        output_path: Union[str, Path],
        apply_all_transitions: bool = True
    ) -> None:
        """
        Apply smoothing transitions to jump cuts in a video.
        
        Args:
            video_path: Path to the input video file
            jump_cuts: List of detected jump cuts
            output_path: Path to save the output video
            apply_all_transitions: Whether to apply all transitions or only high-confidence ones
        """
        video_path = str(video_path)
        output_path = str(output_path)
        
        logger.info(f"Smoothing {len(jump_cuts)} jump cuts in {video_path}")
        
        # Sort jump cuts by timestamp
        jump_cuts = sorted(jump_cuts, key=lambda x: x.timestamp)
        
        # Filter jump cuts if needed
        if not apply_all_transitions:
            # Only apply transitions to high-confidence jump cuts
            jump_cuts = [cut for cut in jump_cuts if cut.confidence > 0.5]
            logger.info(f"Applying transitions to {len(jump_cuts)} high-confidence jump cuts")
        
        if not jump_cuts:
            logger.warning("No jump cuts to smooth, copying input video to output")
            with VideoFileClip(video_path) as video:
                video.write_videofile(output_path)
            return
        
        # Process the video
        with VideoFileClip(video_path) as video:
            # Extract clip segments
            segments = []
            last_cut_time = 0
            
            for i, cut in enumerate(jump_cuts):
                # Extract segment before the cut
                if cut.timestamp > last_cut_time:
                    segment = video.subclip(last_cut_time, cut.timestamp)
                    segments.append(segment)
                
                last_cut_time = cut.timestamp
            
            # Add final segment after the last cut
            if last_cut_time < video.duration:
                final_segment = video.subclip(last_cut_time, video.duration)
                segments.append(final_segment)
            
            # Apply transitions
            smoothed_segments = []
            
            if len(segments) == 1:
                # Only one segment, no transitions needed
                smoothed_segments = segments
            else:
                # Apply transitions between segments
                for i in range(len(segments) - 1):
                    if i < len(jump_cuts):
                        transition_type = jump_cuts[i].suggested_transition
                        transition_duration = jump_cuts[i].transition_duration
                    else:
                        # Default transition for any extra segments
                        transition_type = TransitionType.CROSSFADE
                        transition_duration = 0.5
                    
                    # Apply transition
                    if i == len(segments) - 2:
                        # Last transition, include both segments
                        transition = self._apply_transition(
                            segments[i], segments[i+1], 
                            transition_type, transition_duration
                        )
                        smoothed_segments.append(transition)
                    else:
                        # Apply only to first segment, later transitions will handle the rest
                        if transition_type != TransitionType.NONE:
                            transition = self._apply_transition(
                                segments[i], segments[i+1], 
                                transition_type, transition_duration
                            )
                            smoothed_segments.append(transition.subclip(0, segments[i].duration))
                        else:
                            smoothed_segments.append(segments[i])
            
            # Combine all segments
            final_video = concatenate_videoclips(smoothed_segments)
            
            # Write output file
            logger.info(f"Writing smoothed video to {output_path}")
            final_video.write_videofile(output_path)
            
            # Close all clips
            for segment in segments:
                segment.close()
            for segment in smoothed_segments:
                segment.close()
            final_video.close()


def detect_jump_cuts(
    video_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    sensitivity: float = 0.5,
    min_jump_interval: float = 0.5,
    frame_sample_rate: float = 10.0,
    save_frames: bool = True,
    metadata_file: Optional[Union[str, Path]] = None,
    use_memory_adaptation: bool = True
) -> List[Dict[str, Any]]:
    """
    Detect jump cuts in a video.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save output files (if None, creates a temp dir)
        sensitivity: Sensitivity for detection (0.0-1.0, higher means more sensitive)
        min_jump_interval: Minimum interval between detected jump cuts in seconds
        frame_sample_rate: Frames per second to analyze
        save_frames: Whether to save frames before and after jump cuts
        metadata_file: Optional path to save jump cut metadata as JSON
        use_memory_adaptation: Whether to use memory-adaptive processing
        
    Returns:
        List of dictionaries with jump cut information
    """
    # Create detector with specified parameters
    detector = JumpCutDetector(
        sensitivity=sensitivity,
        min_jump_interval=min_jump_interval,
        frame_sample_rate=frame_sample_rate,
        save_frames=save_frames
    )
    
    if use_memory_adaptation:
        # Import here to avoid circular imports
        from .memory_utils import memory_adaptive_processing, adaptive_memory_wrapper
        
        # Create a wrapper function that matches the signature expected by memory_adaptive_processing
        def _detect_jump_cuts_impl(input_file, output_file, **kwargs):
            # Extract parameters from kwargs
            _output_dir = kwargs.get('output_dir', output_dir)
            _metadata_file = kwargs.get('metadata_file', metadata_file)
            
            # Detect jump cuts
            jump_cuts = detector.detect_jump_cuts(
                video_path=input_file,
                output_dir=_output_dir,
                metadata_file=_metadata_file
            )
            
            # Return the jump cuts directly (we'll convert to dict format outside)
            return jump_cuts
        
        # Use memory-adaptive processing
        result = memory_adaptive_processing(
            input_file=video_path,
            output_file=output_dir or tempfile.mkdtemp(prefix="jump_cuts_"),  # Dummy output
            process_function=_detect_jump_cuts_impl,
            _operation_type='jump_cut_detection',
            output_dir=output_dir,
            metadata_file=metadata_file
        )
        
        # If memory adaptation succeeded, extract the jump cuts
        if isinstance(result, dict) and result.get("status") == "success":
            jump_cuts = result.get("result", [])
        else:
            # Fallback to direct processing if memory adaptation failed
            jump_cuts = detector.detect_jump_cuts(
                video_path=video_path,
                output_dir=output_dir,
                metadata_file=metadata_file
            )
    else:
        # Direct processing without memory adaptation
        jump_cuts = detector.detect_jump_cuts(
            video_path=video_path,
            output_dir=output_dir,
            metadata_file=metadata_file
        )
    
    # Convert to list of dictionaries
    result = []
    for i, cut in enumerate(jump_cuts):
        mins = int(cut.timestamp // 60)
        secs = int(cut.timestamp % 60)
        
        result.append({
            "index": i + 1,
            "timestamp": cut.timestamp,
            "timestamp_str": f"{mins:02d}:{secs:02d}",
            "confidence": round(cut.confidence, 3),
            "frame_before": cut.frame_before_path,
            "frame_after": cut.frame_after_path,
            "suggested_transition": cut.suggested_transition.value,
            "transition_duration": cut.transition_duration,
            "metrics": {
                "similarity": round(cut.similarity_score, 3),
                "difference": round(cut.difference_score, 3),
                "motion": round(cut.motion_score, 3),
                "color_change": round(cut.color_change_score, 3),
                "total_score": round(cut.total_score, 3)
            }
        })
    
    return result


def smooth_jump_cuts(
    video_path: Union[str, Path],
    output_path: Union[str, Path],
    jump_cuts_data: List[Dict[str, Any]],
    apply_all_transitions: bool = True
) -> None:
    """
    Apply smoothing transitions to jump cuts in a video.
    
    Args:
        video_path: Path to the input video file
        output_path: Path to save the output video
        jump_cuts_data: List of jump cut dictionaries from detect_jump_cuts
        apply_all_transitions: Whether to apply all transitions or only high-confidence ones
    """
    # Convert jump cuts data to JumpCut objects
    jump_cuts = []
    
    for cut_data in jump_cuts_data:
        try:
            jump_cut = JumpCut(
                frame_index=0,  # Not used for smoothing
                timestamp=cut_data["timestamp"],
                similarity_score=cut_data["metrics"]["similarity"],
                difference_score=cut_data["metrics"]["difference"],
                motion_score=cut_data["metrics"]["motion"],
                color_change_score=cut_data["metrics"]["color_change"],
                total_score=cut_data["metrics"]["total_score"],
                confidence=cut_data["confidence"],
                frame_before_path=cut_data.get("frame_before", ""),
                frame_after_path=cut_data.get("frame_after", ""),
                suggested_transition=TransitionType(cut_data["suggested_transition"]),
                transition_duration=cut_data["transition_duration"]
            )
            jump_cuts.append(jump_cut)
        except (KeyError, ValueError) as e:
            logger.warning(f"Skipping invalid jump cut data: {e}")
    
    # Create detector (parameters don't matter for smoothing)
    detector = JumpCutDetector()
    
    # Apply smoothing
    detector.smooth_jump_cuts(
        video_path=video_path,
        jump_cuts=jump_cuts,
        output_path=output_path,
        apply_all_transitions=apply_all_transitions
    )

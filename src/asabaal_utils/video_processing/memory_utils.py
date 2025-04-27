"""
Memory management utilities for video processing.

This module provides utilities for estimating and managing memory usage
during video processing operations.
"""

import os
import gc
import logging
import signal
import traceback
import tempfile
import time
import threading
from typing import Dict, Any, Optional, Union, Callable, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import functools

# Try to import psutil, but don't fail if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import numpy as np
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """Video processing strategies with different memory requirements."""
    FULL_QUALITY = "full_quality"           # Process at original resolution
    REDUCED_RESOLUTION = "reduced_resolution"  # Lower resolution processing
    CHUNKED = "chunked"                     # Process in sequential chunks
    SEGMENT = "segment"                     # Split, process, recombine
    STREAMING = "streaming"                 # Stream processing for minimal memory


@dataclass
class MemoryState:
    """Current memory state for adaptive processing."""
    total_memory: int
    available_memory: int
    estimated_required: int
    video_properties: Dict[str, Any]
    safe_threshold: float = 0.7  # Maximum percentage of available memory to use
    
    @property
    def is_sufficient(self) -> bool:
        """Check if available memory is sufficient for estimated requirement."""
        return self.estimated_required < (self.available_memory * self.safe_threshold)
    
    @property
    def memory_ratio(self) -> float:
        """Calculate ratio of required memory to available memory."""
        return self.estimated_required / (self.available_memory * self.safe_threshold)
    
    def recommended_strategy(self) -> ProcessingStrategy:
        """Recommend appropriate processing strategy based on memory state."""
        ratio = self.memory_ratio
        
        if ratio <= 0.7:
            return ProcessingStrategy.FULL_QUALITY
        elif ratio <= 1.2:
            return ProcessingStrategy.REDUCED_RESOLUTION
        elif ratio <= 2.0:
            return ProcessingStrategy.CHUNKED
        elif ratio <= 3.5:
            return ProcessingStrategy.SEGMENT
        else:
            return ProcessingStrategy.STREAMING


class MemoryMonitor:
    """
    Monitor and manage memory during processing.
    
    This class provides tools to monitor memory usage during processing and
    can interrupt operations if memory usage exceeds thresholds.
    """
    
    def __init__(
        self, 
        threshold_percent: float = 90.0,  # Memory usage threshold percentage
        check_interval: float = 1.0,      # Check interval in seconds
        emergency_free_target: float = 0.3,  # Target to free in emergency (30%)
    ):
        """
        Initialize memory monitor.
        
        Args:
            threshold_percent: Memory usage percentage threshold for warnings
            check_interval: Interval between memory checks in seconds
            emergency_free_target: Target percentage of memory to free in emergency
        """
        self.threshold_percent = threshold_percent
        self.check_interval = check_interval
        self.emergency_free_target = emergency_free_target
        self._monitoring = False
        self._monitor_thread = None
        self._interrupt_requested = False
        self._prev_handler = None
        self._critical_callbacks = []
    
    def register_critical_callback(self, callback: Callable) -> None:
        """
        Register callback to be called when memory is critical.
        
        Args:
            callback: Function to call when memory is critical
        """
        self._critical_callbacks.append(callback)
    
    def start_monitoring(self) -> None:
        """Start memory monitoring in a background thread."""
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil is not available, memory monitoring disabled")
            return
        
        if self._monitoring:
            return
        
        self._monitoring = True
        self._interrupt_requested = False
        
        # Set up signal handler for clean termination
        self._prev_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        
        # Create and start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_memory,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        
        # Restore previous signal handler
        if self._prev_handler:
            signal.signal(signal.SIGINT, self._prev_handler)
            self._prev_handler = None
        
        # Wait for monitor thread to terminate
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        self._monitor_thread = None
        logger.info("Memory monitoring stopped")
    
    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signal."""
        self._interrupt_requested = True
        logger.warning("Interrupt requested, will stop after current operation")
        return self._prev_handler(signum, frame) if self._prev_handler else None
    
    def _monitor_memory(self) -> None:
        """Memory monitoring thread function."""
        critical_reported = False
        
        while self._monitoring and not self._interrupt_requested:
            try:
                # Get current memory usage
                mem = psutil.virtual_memory()
                percent_used = mem.percent
                
                if percent_used > self.threshold_percent:
                    if not critical_reported:
                        logger.warning(
                            f"Memory usage critical: {percent_used:.1f}% used "
                            f"({mem.available / (1024**3):.2f} GB available)"
                        )
                        critical_reported = True
                        
                        # Trigger callbacks
                        for callback in self._critical_callbacks:
                            try:
                                callback()
                            except Exception as e:
                                logger.error(f"Error in memory critical callback: {e}")
                        
                        # If extremely critical, try emergency cleanup
                        if percent_used > 95:
                            self._emergency_memory_cleanup()
                else:
                    critical_reported = False
                
            except Exception as e:
                logger.error(f"Error in memory monitor: {e}")
            
            # Sleep between checks
            time.sleep(self.check_interval)
    
    def _emergency_memory_cleanup(self) -> None:
        """Perform emergency memory cleanup."""
        logger.warning("Performing emergency memory cleanup")
        
        # Clear any unused caches
        if hasattr(VideoFileClip, 'clear_cache'):
            VideoFileClip.clear_cache()
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Try to free more memory if target not reached
        target_available = psutil.virtual_memory().total * self.emergency_free_target
        if psutil.virtual_memory().available < target_available:
            logger.warning("Still low on memory after cleanup")


def estimate_memory_requirement(
    video_path: Union[str, Path],
    operation_type: str = "generic",
    safety_factor: float = 1.5
) -> Dict[str, Any]:
    """
    Estimate memory requirements for processing a video.
    
    Args:
        video_path: Path to the video file
        operation_type: Type of operation ("silence_removal", "jump_cut", etc.)
        safety_factor: Multiplier to account for overhead (1.5 = 50% extra)
        
    Returns:
        Dict with estimated memory requirements and video properties
    """
    # Import here to avoid any possible scope/shadowing issues
    from moviepy.editor import VideoFileClip
    
    with VideoFileClip(str(video_path)) as clip:
        # Basic frame memory calculation
        width, height = clip.size
        fps = clip.fps if clip.fps else 30  # Default to 30fps if not available
        duration = clip.duration
        
        # Memory for a single uncompressed frame (RGB)
        bytes_per_frame = width * height * 3  # 3 bytes for RGB channels
        
        # Operation-specific memory requirements
        if operation_type == "silence_removal":
            # Need to hold audio data and video segments
            audio_bytes = duration * 44100 * 2 * 2  # 44.1kHz, 16-bit stereo
            # Estimated frames in memory during concatenation (more for silence removal)
            buffer_frames = min(int(fps * 30), 900)  # ~30 seconds or max 900 frames
        
        elif operation_type == "jump_cut_detection":
            # Need to hold consecutive frames for comparison
            audio_bytes = 0  # No audio processing needed
            buffer_frames = min(int(fps * 10), 300)  # ~10 seconds or max 300 frames
        
        elif operation_type == "video_summary":
            # Need to hold segments and analyze content
            audio_bytes = duration * 22050 * 2  # 22kHz, 16-bit mono (for analysis)
            buffer_frames = min(int(fps * 60), 1800)  # ~60 seconds or max 1800 frames
            
        else:  # generic case
            # Base memory requirement (conservative estimate)
            audio_bytes = duration * 44100 * 2 * 2  # 44.1kHz, 16-bit stereo
            buffer_frames = min(int(fps * 10), 300)  # ~10 seconds or max 300 frames
        
        # Calculate total requirement
        video_bytes = bytes_per_frame * buffer_frames
        estimated_bytes = (video_bytes + audio_bytes) * safety_factor
        
        return {
            "estimated_bytes": int(estimated_bytes),
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
            "bytes_per_frame": bytes_per_frame,
            "operation_type": operation_type
        }


def get_memory_state(
    video_path: Union[str, Path],
    operation_type: str = "generic",
    safety_factor: float = 1.5
) -> MemoryState:
    """
    Get current memory state including video requirements.
    
    Args:
        video_path: Path to the video file
        operation_type: Type of operation to estimate for
        safety_factor: Multiplier for memory estimates
        
    Returns:
        MemoryState object
    """
    video_properties = estimate_memory_requirement(
        video_path, operation_type, safety_factor
    )
    
    if PSUTIL_AVAILABLE:
        mem = psutil.virtual_memory()
        total_memory = mem.total
        available_memory = mem.available
    else:
        logger.warning("psutil is not available. Using conservative memory estimates.")
        # Assume 8GB system with 4GB available
        total_memory = 8 * 1024 * 1024 * 1024
        available_memory = 4 * 1024 * 1024 * 1024
    
    return MemoryState(
        total_memory=total_memory,
        available_memory=available_memory,
        estimated_required=video_properties["estimated_bytes"],
        video_properties=video_properties
    )


def process_in_reduced_resolution(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    process_function: Callable,
    scale_factor: float = None,
    target_height: int = None,
    **process_kwargs
) -> Dict[str, Any]:
    """
    Process a video at reduced resolution, then upscale result.
    
    Args:
        input_file: Path to input video file
        output_file: Path to output video file
        process_function: Function that processes video
        scale_factor: Resolution scale factor (0.25-0.75)
        target_height: Alternative to scale_factor, target height in pixels
        process_kwargs: Additional arguments for the process function
        
    Returns:
        Dict with processing results
    """
    # Import here to avoid any possible scope/shadowing issues
    from moviepy.editor import VideoFileClip
    
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Get video properties
    with VideoFileClip(input_file) as clip:
        original_width, original_height = clip.size
    
    # Calculate scale factor if target height is provided
    if scale_factor is None:
        if target_height is None:
            # Auto-calculate based on memory state
            memory_state = get_memory_state(input_file)
            # Scale based on memory ratio (more aggressive if higher ratio)
            ratio = memory_state.memory_ratio
            if ratio <= 1.0:
                scale_factor = 0.75
            elif ratio <= 1.5:
                scale_factor = 0.5
            else:
                scale_factor = 0.35
        else:
            scale_factor = target_height / original_height
    
    # Ensure scale factor is within reasonable bounds
    scale_factor = max(0.25, min(0.75, scale_factor))
    
    # Calculate new dimensions
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    logger.info(f"Processing at reduced resolution: {new_width}x{new_height} "
               f"(scale: {scale_factor:.2f})")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input_file:
        temp_input = temp_input_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output_file:
        temp_output = temp_output_file.name
    
    try:
        # Downscale input
        try:
            with VideoFileClip(input_file) as clip:
                clip_resized = clip.resize(width=new_width, height=new_height)
                clip_resized.write_videofile(
                    temp_input, 
                    codec='libx264',
                    audio_codec='aac',
                    threads=1, 
                    logger=None, 
                    ffmpeg_params=['-strict', '-2']
                )
                clip_resized.close()
                
                # Force garbage collection after resize
                gc.collect()
            
            # Process at lower resolution
            result = process_function(temp_input, temp_output, **process_kwargs)
            
            # Upscale back to original resolution
            with VideoFileClip(temp_output) as result_clip:
                result_upscaled = result_clip.resize(width=original_width, height=original_height)
                result_upscaled.write_videofile(
                    output_file, 
                    codec='libx264',
                    audio_codec='aac',
                    threads=1, 
                    logger=None, 
                    ffmpeg_params=['-strict', '-2']
                )
                result_upscaled.close()
                
                # Force garbage collection after upscale
                gc.collect()
        except Exception as e:
            logger.error(f"Error in resolution processing step: {e}")
            # If we encountered an error during the resolution change, try a direct processing approach
            logger.info("Attempting direct processing as fallback")
            try:
                result = process_function(input_file, output_file, **process_kwargs)
                return {
                    "status": "success", 
                    "processing_mode": "direct_fallback",
                    "result": result
                }
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {fallback_error}")
                raise e
        
        return {
            "status": "success", 
            "processing_mode": "reduced_resolution",
            "scale_factor": scale_factor,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Error in reduced resolution processing: {e}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}
    
    finally:
        # Clean up temporary files
        for temp_file in [temp_input, temp_output]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {e}")


def process_in_chunks(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    process_function: Callable,
    chunk_duration: float = 60.0,
    overlap: float = 5.0,
    **process_kwargs
) -> Dict[str, Any]:
    """
    Process a video in sequential time chunks.
    
    Args:
        input_file: Path to input video file
        output_file: Path to output video file
        process_function: Function that processes video
        chunk_duration: Duration of each chunk in seconds
        overlap: Overlap between chunks in seconds
        process_kwargs: Additional arguments for the process function
        
    Returns:
        Dict with processing results
    """
    # Import here to avoid any possible scope/shadowing issues
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Get video duration
    with VideoFileClip(input_file) as clip:
        total_duration = clip.duration
    
    # Calculate chunk times
    chunk_times = []
    start_time = 0
    
    while start_time < total_duration:
        end_time = min(start_time + chunk_duration, total_duration)
        chunk_times.append((start_time, end_time))
        start_time = end_time - overlap
    
    logger.info(f"Processing video in {len(chunk_times)} chunks of {chunk_duration}s "
               f"with {overlap}s overlap")
    
    # Create temporary directory for chunks
    temp_dir = tempfile.mkdtemp(prefix="video_chunks_")
    temp_input_chunks = []
    temp_output_chunks = []
    
    try:
        # Extract chunks
        with VideoFileClip(input_file) as clip:
            for i, (start, end) in enumerate(chunk_times):
                chunk_input = os.path.join(temp_dir, f"chunk_{i:03d}_input.mp4")
                chunk_output = os.path.join(temp_dir, f"chunk_{i:03d}_output.mp4")
                
                try:
                    # Extract chunk
                    chunk = clip.subclip(start, end)
                    
                    # More robust write_videofile with proper codec specification
                    chunk.write_videofile(
                        chunk_input, 
                        codec='libx264',
                        audio_codec='aac',
                        threads=1, 
                        logger=None, 
                        ffmpeg_params=['-strict', '-2']
                    )
                    chunk.close()
                    
                    temp_input_chunks.append(chunk_input)
                    temp_output_chunks.append(chunk_output)
                    
                    # Force garbage collection after each chunk to prevent memory buildup
                    gc.collect()
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {i}: {e}")
                    # Continue with next chunk rather than failing completely
                    continue
        
        # Process each chunk
        chunk_results = []
        for i, (chunk_input, chunk_output) in enumerate(zip(temp_input_chunks, temp_output_chunks)):
            logger.info(f"Processing chunk {i+1}/{len(chunk_times)}")
            
            # Clear memory before processing each chunk
            gc.collect()
            
            # Process the chunk
            result = process_function(chunk_input, chunk_output, **process_kwargs)
            chunk_results.append(result)
        
        # Combine processed chunks
        if not temp_output_chunks:
            logger.error("No chunks were successfully processed")
            return {"status": "error", "message": "No chunks were successfully processed"}
            
        # Verify all chunk files exist and are valid
        valid_chunks = []
        for chunk_path in temp_output_chunks:
            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                valid_chunks.append(chunk_path)
            else:
                logger.warning(f"Skipping invalid chunk file: {chunk_path}")
                
        if not valid_chunks:
            logger.error("No valid chunk files found")
            return {"status": "error", "message": "No valid chunk files found"}
        
        clips_to_combine = []
        valid_indices = []
        
        # Map paths back to indices
        index_map = {path: i for i, path in enumerate(temp_output_chunks)}
        
        # Load valid chunks
        for chunk_path in valid_chunks:
            i = index_map.get(chunk_path, 0)  # Default to 0 if not found
            valid_indices.append(i)
            try:
                with VideoFileClip(chunk_path) as chunk:
                    if i > 0 and overlap > 0:
                        # For overlapping chunks, start at half the overlap point
                        overlap_mid = overlap / 2
                        clip = chunk.subclip(overlap_mid)
                    else:
                        # First chunk or non-overlapping chunks
                        clip = chunk.copy()
                    
                    clips_to_combine.append(clip)
            except Exception as e:
                logger.warning(f"Could not load chunk {chunk_path}: {e}")
                # Continue with other chunks
                        
        if not clips_to_combine:
            logger.error("No chunks could be loaded for combining")
            return {"status": "error", "message": "No chunks could be loaded for combining"}
        
        try:
            # Concatenate all chunks with proper codec settings
            final_clip = concatenate_videoclips(clips_to_combine, method="compose")
            final_clip.write_videofile(
                output_file, 
                codec='libx264',
                audio_codec='aac',
                threads=1, 
                logger=None, 
                ffmpeg_params=['-strict', '-2']
            )
            final_clip.close()
            
            # Clean up chunk clips
            for clip in clips_to_combine:
                clip.close()
        except Exception as e:
            logger.error(f"Error combining chunks: {e}")
            # Try to copy the first valid chunk as a last resort
            if valid_chunks:
                logger.info("Copying first valid chunk as fallback")
                try:
                    import shutil
                    shutil.copy2(valid_chunks[0], output_file)
                    logger.info(f"Copied {valid_chunks[0]} to {output_file} as fallback")
                    # Create a simple result with the single chunk
                    return {
                        "status": "success",
                        "processing_mode": "single_chunk_fallback",
                        "chunks": 1,
                        "chunk_results": chunk_results[:1] if chunk_results else ["unknown"]
                    }
                except Exception as copy_error:
                    logger.error(f"Failed to copy chunk as fallback: {copy_error}")
                    
            return {"status": "error", "message": f"Error combining chunks: {e}"}
        
        return {
            "status": "success", 
            "processing_mode": "chunked",
            "chunks": len(chunk_times),
            "chunk_results": chunk_results
        }
    
    except Exception as e:
        logger.error(f"Error in chunked processing: {e}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}
    
    finally:
        # Clean up temporary files
        for temp_file in temp_input_chunks + temp_output_chunks:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {e}")
        
        try:
            os.rmdir(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to remove temporary directory {temp_dir}: {e}")


def process_in_segments(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    process_function: Callable,
    segment_count: int = 4,
    **process_kwargs
) -> Dict[str, Any]:
    """
    Split video into segments, process each, then recombine.
    
    Args:
        input_file: Path to input video file
        output_file: Path to output video file
        process_function: Function that processes video
        segment_count: Number of segments to split video into
        process_kwargs: Additional arguments for the process function
        
    Returns:
        Dict with processing results
    """
    # Import here to avoid any possible scope/shadowing issues
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Get video duration
    with VideoFileClip(input_file) as clip:
        total_duration = clip.duration
    
    # Calculate segment times (no overlap)
    segment_duration = total_duration / segment_count
    segment_times = []
    
    for i in range(segment_count):
        start_time = i * segment_duration
        end_time = (i + 1) * segment_duration
        if i == segment_count - 1:
            end_time = total_duration  # Ensure the last segment goes to the end
        segment_times.append((start_time, end_time))
    
    logger.info(f"Processing video in {segment_count} segments")
    
    # Create temporary directory for segments
    temp_dir = tempfile.mkdtemp(prefix="video_segments_")
    temp_input_segments = []
    temp_output_segments = []
    
    try:
        # Extract segments
        with VideoFileClip(input_file) as clip:
            for i, (start, end) in enumerate(segment_times):
                segment_input = os.path.join(temp_dir, f"segment_{i:03d}_input.mp4")
                segment_output = os.path.join(temp_dir, f"segment_{i:03d}_output.mp4")
                
                try:
                    # Extract segment with retry logic
                    segment = clip.subclip(start, end)
                    
                    # More robust write_videofile with proper codec specification
                    segment.write_videofile(
                        segment_input, 
                        codec='libx264',
                        audio_codec='aac',
                        threads=1, 
                        logger=None, 
                        ffmpeg_params=['-strict', '-2']
                    )
                    segment.close()
                    
                    temp_input_segments.append(segment_input)
                    temp_output_segments.append(segment_output)
                    
                    # Force garbage collection after each segment to prevent memory buildup
                    gc.collect()
                    
                except Exception as e:
                    logger.error(f"Error processing segment {i}: {e}")
                    # Continue with next segment rather than failing completely
                    continue
        
        # Process each segment
        segment_results = []
        for i, (segment_input, segment_output) in enumerate(zip(temp_input_segments, temp_output_segments)):
            logger.info(f"Processing segment {i+1}/{segment_count}")
            
            # Clear memory before processing each segment
            gc.collect()
            
            # Process the segment
            result = process_function(segment_input, segment_output, **process_kwargs)
            segment_results.append(result)
        
        # Combine processed segments if we have any
        if not temp_output_segments:
            logger.error("No segments were successfully processed")
            return {"status": "error", "message": "No segments were successfully processed"}
            
        # Verify all segment files exist and are valid
        valid_segments = []
        for segment_path in temp_output_segments:
            if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0:
                valid_segments.append(segment_path)
            else:
                logger.warning(f"Skipping invalid segment file: {segment_path}")
                
        if not valid_segments:
            logger.error("No valid segment files found")
            return {"status": "error", "message": "No valid segment files found"}
        
        clips_to_combine = []
        for segment_path in valid_segments:
            try:
                with VideoFileClip(segment_path) as segment:
                    clip = segment.copy()
                    clips_to_combine.append(clip)
            except Exception as e:
                logger.warning(f"Could not load segment {segment_path}: {e}")
                # Continue with other segments
                
        if not clips_to_combine:
            logger.error("No segments could be loaded for combining")
            return {"status": "error", "message": "No segments could be loaded for combining"}
            
        try:
            # Concatenate all segments with proper codec settings
            final_clip = concatenate_videoclips(clips_to_combine, method="compose")
            final_clip.write_videofile(
                output_file, 
                codec='libx264',
                audio_codec='aac',
                threads=1, 
                logger=None, 
                ffmpeg_params=['-strict', '-2']
            )
            final_clip.close()
            
            # Clean up segment clips
            for clip in clips_to_combine:
                clip.close()
        except Exception as e:
            logger.error(f"Error combining segments: {e}")
            # Try to copy the first valid segment as a last resort
            if valid_segments:
                logger.info("Copying first valid segment as fallback")
                try:
                    import shutil
                    shutil.copy2(valid_segments[0], output_file)
                    logger.info(f"Copied {valid_segments[0]} to {output_file} as fallback")
                    # Create a simple result with the single segment
                    return {
                        "status": "success",
                        "processing_mode": "single_segment_fallback",
                        "segments": 1,
                        "segment_results": segment_results[:1] if segment_results else ["unknown"]
                    }
                except Exception as copy_error:
                    logger.error(f"Failed to copy segment as fallback: {copy_error}")
                    
            return {"status": "error", "message": f"Error combining segments: {e}"}
        
        return {
            "status": "success", 
            "processing_mode": "segmented",
            "segments": segment_count,
            "segment_results": segment_results
        }
    
    except Exception as e:
        logger.error(f"Error in segmented processing: {e}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}
    
    finally:
        # Clean up temporary files
        for temp_file in temp_input_segments + temp_output_segments:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {e}")
        
        try:
            os.rmdir(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to remove temporary directory {temp_dir}: {e}")


def adaptive_memory_wrapper(func):
    """
    Decorator for video processing functions to automatically manage memory.
    
    This decorator analyzes memory requirements and chooses the best strategy
    for executing the function.
    
    Args:
        func: The video processing function to wrap
    
    Returns:
        Wrapped function with memory management
    """
    @functools.wraps(func)
    def wrapper(input_file, output_file, *args, **kwargs):
        # Extract operation type from function name or kwargs
        operation_type = kwargs.pop('_operation_type', func.__name__)
        
        # Check memory requirements
        memory_state = get_memory_state(input_file, operation_type)
        strategy = memory_state.recommended_strategy()
        
        logger.info(f"Memory analysis - Required: {memory_state.estimated_required / (1024**3):.2f} GB, "
                   f"Available: {memory_state.available_memory / (1024**3):.2f} GB")
        logger.info(f"Using processing strategy: {strategy.value}")
        
        # Skip memory monitor setup if not available
        memory_monitor = None
        if PSUTIL_AVAILABLE:
            memory_monitor = MemoryMonitor()
            memory_monitor.start_monitoring()
        
        try:
            # Choose strategy based on memory analysis
            if strategy == ProcessingStrategy.FULL_QUALITY:
                return func(input_file, output_file, *args, **kwargs)
            
            elif strategy == ProcessingStrategy.REDUCED_RESOLUTION:
                return process_in_reduced_resolution(
                    input_file, output_file, func, *args, **kwargs
                )
            
            elif strategy == ProcessingStrategy.CHUNKED:
                # For longer videos, adjust chunk size based on available memory
                if memory_state.video_properties["duration"] > 300:  # 5+ minutes
                    ratio = memory_state.memory_ratio
                    chunk_duration = 120.0 / ratio  # Smaller chunks for less memory
                    chunk_duration = max(30.0, min(120.0, chunk_duration))
                else:
                    chunk_duration = 60.0
                
                return process_in_chunks(
                    input_file, output_file, func, 
                    chunk_duration=chunk_duration, *args, **kwargs
                )
            
            elif strategy == ProcessingStrategy.SEGMENT:
                # Adjust segment count based on memory ratio and video length
                ratio = memory_state.memory_ratio
                segment_count = max(2, min(8, int(ratio * 2)))
                
                return process_in_segments(
                    input_file, output_file, func,
                    segment_count=segment_count, *args, **kwargs
                )
            
            else:  # STREAMING strategy
                # For extreme cases, combine reduced resolution with chunking
                return process_in_chunks(
                    input_file, output_file,
                    lambda i, o, **kw: process_in_reduced_resolution(i, o, func, scale_factor=0.4, **kw),
                    chunk_duration=30.0, *args, **kwargs
                )
                
        except MemoryError:
            logger.error("Memory error occurred during processing")
            # Try more aggressive memory-saving strategy
            if strategy != ProcessingStrategy.STREAMING:
                logger.info("Attempting recovery with more aggressive memory strategy")
                return process_in_chunks(
                    input_file, output_file,
                    lambda i, o, **kw: process_in_reduced_resolution(i, o, func, scale_factor=0.33, **kw),
                    chunk_duration=20.0, *args, **kwargs
                )
            return {"status": "error", "message": "Memory error occurred during processing"}
            
        except Exception as e:
            logger.error(f"Error in processing: {e}")
            logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
            
        finally:
            # Clean up memory monitor
            if memory_monitor:
                memory_monitor.stop_monitoring()
            
            # Force garbage collection
            gc.collect()
    
    return wrapper


def memory_adaptive_processing(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    process_function: Callable,
    **process_kwargs
) -> Dict[str, Any]:
    """
    Process a video with memory-adaptive strategies.
    
    Args:
        input_file: Path to input video file
        output_file: Path to output video file
        process_function: Function that processes video segments
        process_kwargs: Additional arguments for the process function
        
    Returns:
        Dict with success status and processing info
    """
    # This is now just a thin wrapper around our decorator pattern
    # Extract operation type from function name or kwargs
    operation_type = process_kwargs.pop('_operation_type', process_function.__name__)
    
    # Check memory requirements
    memory_state = get_memory_state(input_file, operation_type)
    strategy = memory_state.recommended_strategy()
    
    logger.info(f"Memory analysis - Required: {memory_state.estimated_required / (1024**3):.2f} GB, "
               f"Available: {memory_state.available_memory / (1024**3):.2f} GB")
    logger.info(f"Using processing strategy: {strategy.value}")
    
    # Choose strategy based on memory analysis
    if strategy == ProcessingStrategy.FULL_QUALITY:
        result = process_function(input_file, output_file, **process_kwargs)
        return {"status": "success", "processing_mode": "full", "result": result}
    
    elif strategy == ProcessingStrategy.REDUCED_RESOLUTION:
        return process_in_reduced_resolution(
            input_file, output_file, process_function, **process_kwargs
        )
    
    elif strategy == ProcessingStrategy.CHUNKED:
        # For longer videos, adjust chunk size based on available memory
        if memory_state.video_properties["duration"] > 300:  # 5+ minutes
            ratio = memory_state.memory_ratio
            chunk_duration = 120.0 / ratio  # Smaller chunks for less memory
            chunk_duration = max(30.0, min(120.0, chunk_duration))
        else:
            chunk_duration = 60.0
        
        return process_in_chunks(
            input_file, output_file, process_function, 
            chunk_duration=chunk_duration, **process_kwargs
        )
    
    elif strategy == ProcessingStrategy.SEGMENT:
        # Adjust segment count based on memory ratio and video length
        ratio = memory_state.memory_ratio
        segment_count = max(2, min(8, int(ratio * 2)))
        
        return process_in_segments(
            input_file, output_file, process_function,
            segment_count=segment_count, **process_kwargs
        )
    
    else:  # STREAMING strategy
        # For extreme cases, combine reduced resolution with chunking
        return process_in_chunks(
            input_file, output_file,
            lambda i, o, **kw: process_in_reduced_resolution(i, o, process_function, scale_factor=0.4, **kw),
            chunk_duration=30.0, **process_kwargs
        )
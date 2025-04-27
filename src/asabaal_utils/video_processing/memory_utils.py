"""
Memory management utilities for video processing.

This module provides utilities for estimating and managing memory usage
during video processing operations.
"""

import os
import logging
from typing import Dict, Any, Optional, Union, Callable
from pathlib import Path
import tempfile

# Try to import psutil, but don't fail if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


def estimate_memory_requirement(video_path: Union[str, Path], safety_factor: float = 1.5) -> Dict[str, Any]:
    """
    Estimate memory requirements for processing a video.
    
    Args:
        video_path: Path to the video file
        safety_factor: Multiplier to account for overhead (1.5 = 50% extra)
        
    Returns:
        Dict with estimated memory requirements and video properties
    """
    with VideoFileClip(str(video_path)) as clip:
        # Basic frame memory calculation
        width, height = clip.size
        fps = clip.fps if clip.fps else 30  # Default to 30fps if not available
        duration = clip.duration
        
        # Memory for a single uncompressed frame (RGB)
        bytes_per_frame = width * height * 3  # 3 bytes for RGB channels
        
        # Base memory requirement (conservative estimate)
        # We need enough memory for:
        # 1. Original clip reference
        # 2. Processed frames in buffer
        # 3. Output buffer
        # 4. Additional processing overhead
        
        # For processing with effects, we might need several frames in memory
        buffer_frames = min(int(fps * 5), 300)  # Buffer for ~5 seconds or max 300 frames
        
        estimated_bytes = bytes_per_frame * buffer_frames * safety_factor
        
        return {
            "estimated_bytes": estimated_bytes,
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
            "bytes_per_frame": bytes_per_frame
        }


def get_available_memory() -> int:
    """
    Get available system memory in bytes.
    
    Returns:
        Available memory in bytes, or -1 if psutil is not available
    """
    if PSUTIL_AVAILABLE:
        return psutil.virtual_memory().available
    else:
        logger.warning("psutil is not available. Cannot determine available memory.")
        # Return a conservative default (4GB)
        return 4 * 1024 * 1024 * 1024  # 4GB


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
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Estimate memory requirements
    mem_estimate = estimate_memory_requirement(input_file)
    available_mem = get_available_memory()
    
    logger.info(f"Estimated memory requirement: {mem_estimate['estimated_bytes'] / (1024**3):.2f} GB")
    logger.info(f"Available memory: {available_mem / (1024**3):.2f} GB")
    
    # If we have enough memory, process normally
    if mem_estimate["estimated_bytes"] < available_mem * 0.7:  # Leave 30% memory buffer
        logger.info("Processing video in one pass (sufficient memory available)")
        result = process_function(input_file, output_file, **process_kwargs)
        return {"status": "success", "processing_mode": "full", "result": result}
    
    # Otherwise use memory-saving strategies
    logger.info("Using memory-saving strategies...")
    
    # Strategy 1: Reduce resolution during processing if memory requirement is too high
    if mem_estimate["estimated_bytes"] > available_mem * 0.8:
        # Calculate scale factor to fit in memory (target using 60% of available memory)
        target_mem = available_mem * 0.6
        scale_factor = (target_mem / mem_estimate["estimated_bytes"]) ** 0.5  # Square root for 2D scaling
        scale_factor = max(0.25, min(0.75, scale_factor))  # Keep between 25% and 75%
        
        temp_width = int(mem_estimate["width"] * scale_factor)
        temp_height = int(mem_estimate["height"] * scale_factor)
        
        logger.info(f"Temporarily reducing resolution to {temp_width}x{temp_height} for processing")
        
        # Create temp downscaled video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input_file:
            temp_input = temp_input_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output_file:
            temp_output = temp_output_file.name
            
        try:
            # Downscale input
            with VideoFileClip(input_file) as clip:
                clip_resized = clip.resize(width=temp_width, height=temp_height)
                clip_resized.write_videofile(temp_input, threads=1, logger=None)
                
            # Process at lower resolution
            process_function(temp_input, temp_output, **process_kwargs)
            
            # Upscale back to original resolution
            with VideoFileClip(temp_output) as result_clip:
                result_upscaled = result_clip.resize(width=mem_estimate["width"], height=mem_estimate["height"])
                result_upscaled.write_videofile(output_file, threads=1, logger=None)
                
            return {"status": "success", "processing_mode": "resolution_reduction"}
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(temp_output):
                os.remove(temp_output)
    
    # Strategy 2: Process in chunks (could be implemented for specific process functions)
    # This would require the process function to support chunk-based processing
    
    return {"status": "error", "message": "Could not find suitable processing strategy for available memory"}

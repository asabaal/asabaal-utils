"""
Clip extractor module for video processing.

This module provides utilities for extracting video clips based on
transcript analysis results.
"""

import json
import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from .moviepy_imports import VideoFileClip

logger = logging.getLogger(__name__)

def extract_clips_from_json(
    video_file: Union[str, Path],
    json_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    clip_prefix: str = "clip",
    top_n: Optional[int] = None,
    min_score: Optional[float] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    add_padding: float = 0.5,
    use_ffmpeg: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract video clips based on a JSON file with clip suggestions.
    
    Args:
        video_file: Path to the source video file.
        json_file: Path to the JSON file with clip suggestions.
        output_dir: Directory to save the clips (default: <video_name>_clips).
        clip_prefix: Prefix for output clip filenames.
        top_n: Only extract the top N clips by importance score.
        min_score: Only extract clips with importance score above this value.
        min_duration: Only extract clips longer than this duration (seconds).
        max_duration: Only extract clips shorter than this duration (seconds).
        add_padding: Add this many seconds of padding before/after each clip.
        use_ffmpeg: Use direct FFmpeg calls instead of MoviePy for better memory efficiency.
        
    Returns:
        A list of dictionaries with information about the extracted clips.
    """
    video_file = str(video_file)
    json_file = str(json_file)
    
    # Load the JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        clips_data = json.load(f)
    
    # Handle different JSON formats
    if isinstance(clips_data, list):
        # Direct list of clips
        filtered_clips = clips_data
    elif isinstance(clips_data, dict) and 'clips' in clips_data:
        # JSON with clips in a 'clips' key
        filtered_clips = clips_data['clips']
    else:
        # Try to find any list in the JSON that might be clips
        for key, value in clips_data.items():
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict) and 'start_time' in value[0] and 'end_time' in value[0]:
                    filtered_clips = value
                    break
        else:
            # If we couldn't identify the clip format, just use the whole data
            filtered_clips = clips_data
    
    # Create output directory if not specified
    if not output_dir:
        video_path = Path(video_file)
        output_dir = str(video_path.stem + "_clips")
    
    output_dir = str(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter by score if specified
    if min_score is not None:
        filtered_clips = [clip for clip in filtered_clips 
                          if clip.get('importance_score', 0) >= min_score]
    
    # Filter by duration if specified
    if min_duration is not None:
        filtered_clips = [clip for clip in filtered_clips 
                          if clip.get('duration', 0) >= min_duration]
    
    if max_duration is not None:
        filtered_clips = [clip for clip in filtered_clips 
                          if clip.get('duration', float('inf')) <= max_duration]
    
    # Sort by importance score (descending)
    filtered_clips = sorted(filtered_clips, 
                           key=lambda x: x.get('importance_score', 0), 
                           reverse=True)
    
    # Limit to top N if specified
    if top_n is not None:
        filtered_clips = filtered_clips[:top_n]
    
    # Now sort by start time to process in chronological order
    filtered_clips = sorted(filtered_clips, key=lambda x: x.get('start_time', 0))
    
    logger.info(f"Extracting {len(filtered_clips)} clips from {video_file}")
    
    # Get video duration to validate clip boundaries
    if use_ffmpeg:
        # Get duration using FFprobe
        duration_cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration",
            "-of", "json",
            video_file
        ]
        
        try:
            duration_result = subprocess.run(
                duration_cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            duration_data = json.loads(duration_result.stdout)
            video_duration = float(duration_data["format"]["duration"])
        except Exception as e:
            logger.warning(f"Failed to get video duration with FFprobe: {e}")
            # Fall back to MoviePy
            with VideoFileClip(video_file) as video:
                video_duration = video.duration
    else:
        # Get duration using MoviePy
        with VideoFileClip(video_file) as video:
            video_duration = video.duration
    
    # Extract each clip
    results = []
    
    for i, clip_data in enumerate(filtered_clips):
        clip_id = clip_data.get('id', i + 1)
        start_time = clip_data.get('start_time', 0)
        end_time = clip_data.get('end_time', 0)
        topic = clip_data.get('topic', f"Clip {clip_id}")
        
        # Add padding, but ensure we don't go beyond video boundaries
        start_with_padding = max(0, start_time - add_padding)
        end_with_padding = min(video_duration, end_time + add_padding)
        
        # Skip if clip duration is invalid
        if end_with_padding <= start_with_padding:
            logger.warning(f"Skipping invalid clip {clip_id} with duration <= 0")
            continue
        
        # Generate output filename
        # Sanitize topic for filename
        safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)
        safe_topic = safe_topic[:30].strip()  # Limit length
        
        output_file = f"{clip_prefix}_{clip_id:02d}_{safe_topic}.mp4"
        output_path = os.path.join(output_dir, output_file)
        
        logger.info(f"Extracting clip {clip_id}: {start_with_padding:.2f}s - {end_with_padding:.2f}s")
        
        success = False
        
        if use_ffmpeg:
            try:
                # Use FFmpeg directly for better memory efficiency
                extract_cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output files
                    "-i", video_file,
                    "-ss", str(start_with_padding),
                    "-to", str(end_with_padding),
                    "-c", "copy",  # Copy codecs without re-encoding
                    output_path
                ]
                
                # Run FFmpeg command
                subprocess.run(extract_cmd, check=True, capture_output=True)
                
                # Verify the clip was created
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    success = True
                    logger.info(f"Saved clip to {output_path}")
                else:
                    logger.error(f"Failed to create clip: {output_path} (file not created or empty)")
            except Exception as e:
                logger.error(f"Error extracting clip with FFmpeg: {e}")
                # Log error but continue to the MoviePy fallback
                logger.info("Falling back to MoviePy for this clip")
                # Success will still be False, so it will use MoviePy below
        
        # Use MoviePy if FFmpeg is disabled or failed
        if not use_ffmpeg or not success:
            try:
                with VideoFileClip(video_file) as video:
                    subclip = video.subclip(start_with_padding, end_with_padding)
                    
                    # Write to file
                    subclip.write_videofile(
                        output_path,
                        codec="libx264",
                        audio_codec="aac",
                        temp_audiofile=None,
                        remove_temp=True,
                        preset='medium',
                        threads=2,
                        logger=None  # Suppress moviepy progress bars
                    )
                    
                    success = True
                    logger.info(f"Saved clip to {output_path}")
            except Exception as e:
                logger.error(f"Error extracting clip with MoviePy: {e}")
                continue  # Skip this clip
        
        if success:
            # Add to results
            results.append({
                "clip_id": clip_id,
                "original_start": start_time,
                "original_end": end_time,
                "extracted_start": start_with_padding,
                "extracted_end": end_with_padding,
                "duration": end_with_padding - start_with_padding,
                "topic": topic,
                "output_file": output_path,
                "importance_score": clip_data.get('importance_score', 0)
            })
    
    # Save a summary of the extracted clips
    summary_file = os.path.join(output_dir, "extracted_clips.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extracted {len(results)} clips to {output_dir}")
    logger.info(f"Summary saved to {summary_file}")
    
    return results
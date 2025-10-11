#!/usr/bin/env python3
"""
Example video editing workflow using asabaal-utils video processing tools.

This script demonstrates how to use the video processing utilities to:
1. Remove silence from a video
2. Extract thumbnail candidates
3. Analyze a transcript to suggest clip points

Usage:
    python video_processing_workflow.py input_video.mp4 [transcript.txt]
"""

import os
import sys
import argparse
import time
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Import asabaal_utils video processing tools
try:
    from asabaal_utils.video_processing import (
        remove_silence, 
        generate_thumbnails, 
        analyze_transcript
    )
except ImportError:
    logger.error("Could not import asabaal_utils. Make sure it's installed properly.")
    logger.info("Install with: pip install -e /path/to/asabaal-utils")
    sys.exit(1)


def process_video(video_path, transcript_path=None):
    """Process a video file using asabaal_utils video processing tools."""
    video_path = Path(video_path)
    
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return False
    
    # Create output directory for results
    output_dir = video_path.with_suffix('')
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Remove silence from video
    start_time = time.time()
    logger.info(f"Step 1: Removing silence from {video_path}")
    
    clean_video_path = output_dir / f"{video_path.stem}_no_silence{video_path.suffix}"
    
    try:
        original_duration, output_duration, time_saved = remove_silence(
            input_file=str(video_path),
            output_file=str(clean_video_path),
            threshold_db=-45.0,  # Slightly more aggressive silence detection
            min_silence_duration=0.7,
            min_sound_duration=0.3,
            padding=0.1,
        )
        
        logger.info(f"Silence removal complete:")
        logger.info(f"- Original duration: {original_duration:.2f}s")
        logger.info(f"- Output duration: {output_duration:.2f}s")
        logger.info(f"- Time saved: {time_saved:.2f}s ({100 * time_saved / original_duration:.1f}%)")
        logger.info(f"- Output file: {clean_video_path}")
    except Exception as e:
        logger.error(f"Error removing silence: {e}")
        logger.warning("Continuing with original video...")
        clean_video_path = video_path
    
    logger.info(f"Step 1 completed in {time.time() - start_time:.2f}s")
    
    # Step 2: Generate thumbnails from the cleaned video
    start_time = time.time()
    logger.info(f"Step 2: Generating thumbnails from {clean_video_path}")
    
    thumbnail_dir = output_dir / "thumbnails"
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    try:
        thumbnails = generate_thumbnails(
            video_path=str(clean_video_path),
            output_dir=str(thumbnail_dir),
            frames_to_extract=10,
            skip_start_percent=0.05,
            skip_end_percent=0.05,
            output_format="jpg",
            metadata_file=str(thumbnail_dir / "thumbnails.json")
        )
        
        logger.info(f"Thumbnail generation complete:")
        logger.info(f"- Generated {len(thumbnails)} thumbnail candidates")
        logger.info(f"- Saved to: {thumbnail_dir}")
        
        # Print the best thumbnail
        if thumbnails:
            best_thumbnail = max(thumbnails, key=lambda x: x['quality_score'])
            logger.info(f"- Best thumbnail: {os.path.basename(best_thumbnail['frame_path'])}")
            logger.info(f"  Time: {best_thumbnail['timestamp_str']}")
            logger.info(f"  Score: {best_thumbnail['quality_score']:.3f}")
    except Exception as e:
        logger.error(f"Error generating thumbnails: {e}")
    
    logger.info(f"Step 2 completed in {time.time() - start_time:.2f}s")
    
    # Step 3: Process transcript if provided
    if transcript_path and os.path.exists(transcript_path):
        start_time = time.time()
        logger.info(f"Step 3: Analyzing transcript {transcript_path}")
        
        try:
            suggestions = analyze_transcript(
                transcript_file=transcript_path,
                output_file=str(output_dir / "clip_suggestions.json"),
                transcript_format="capcut",  # Adjust based on your transcript format
                min_clip_duration=15.0,
                max_clip_duration=60.0,
            )
            
            logger.info(f"Transcript analysis complete:")
            logger.info(f"- Found {len(suggestions)} suggested clips")
            
            # Print top 3 clip suggestions
            for i, suggestion in enumerate(suggestions[:3]):
                start_min = int(suggestion['start_time'] // 60)
                start_sec = int(suggestion['start_time'] % 60)
                end_min = int(suggestion['end_time'] // 60)
                end_sec = int(suggestion['end_time'] % 60)
                
                logger.info(f"\nClip {i+1}: {suggestion['topic']}")
                logger.info(f"- Time: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} "
                           f"({suggestion['duration']:.1f}s)")
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
        
        logger.info(f"Step 3 completed in {time.time() - start_time:.2f}s")
    else:
        logger.info("Step 3: No transcript provided, skipping transcript analysis")
    
    logger.info(f"\nAll processing completed. Results saved to: {output_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Process video files using asabaal-utils")
    parser.add_argument("video_path", help="Path to the input video file")
    parser.add_argument("transcript_path", nargs="?", help="Optional path to transcript file")
    
    args = parser.parse_args()
    
    process_video(args.video_path, args.transcript_path)


if __name__ == "__main__":
    main()

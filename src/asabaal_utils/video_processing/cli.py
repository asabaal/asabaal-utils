"""
Command-line interface for video processing utilities.

This module provides a CLI for the video processing utilities.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from .silence_detector import remove_silence
from .transcript_analyzer import analyze_transcript
from .thumbnail_generator import generate_thumbnails

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def remove_silence_cli():
    """CLI entry point for silence removal."""
    parser = argparse.ArgumentParser(description="Remove silence from video files")
    parser.add_argument("input_file", help="Path to input video file")
    parser.add_argument("output_file", help="Path to output video file")
    parser.add_argument("--threshold-db", type=float, default=-40.0,
                        help="Threshold in dB below which audio is considered silence (default: -40.0)")
    parser.add_argument("--min-silence", type=float, default=0.5,
                        help="Minimum duration of silence to remove in seconds (default: 0.5)")
    parser.add_argument("--min-sound", type=float, default=0.3,
                        help="Minimum duration of sound to keep in seconds (default: 0.3)")
    parser.add_argument("--padding", type=float, default=0.1,
                        help="Padding around non-silent segments in seconds (default: 0.1)")
    parser.add_argument("--chunk-size", type=float, default=0.05,
                        help="Size of audio chunks for analysis in seconds (default: 0.05)")
    parser.add_argument("--aggressive", action="store_true",
                        help="Use aggressive silence rejection algorithms")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        original_duration, output_duration, time_saved = remove_silence(
            input_file=args.input_file,
            output_file=args.output_file,
            threshold_db=args.threshold_db,
            min_silence_duration=args.min_silence,
            min_sound_duration=args.min_sound,
            padding=args.padding,
            chunk_size=args.chunk_size,
            aggressive_silence_rejection=args.aggressive,
        )
        
        print(f"\nSilence removal complete:")
        print(f"- Original duration: {original_duration:.2f}s")
        print(f"- Output duration: {output_duration:.2f}s")
        print(f"- Time saved: {time_saved:.2f}s ({100 * time_saved / original_duration:.1f}%)")
        print(f"- Output file: {os.path.abspath(args.output_file)}")
        
        return 0
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        return 1


def analyze_transcript_cli():
    """CLI entry point for transcript analysis."""
    parser = argparse.ArgumentParser(description="Analyze video transcripts for optimal clip splits")
    parser.add_argument("transcript_file", help="Path to transcript file")
    parser.add_argument("--output-file", help="Path to output JSON file with suggestions")
    parser.add_argument("--format", default="capcut", choices=["capcut", "json"],
                        help="Format of the transcript file (default: capcut)")
    parser.add_argument("--min-clip-duration", type=float, default=10.0,
                        help="Minimum clip duration in seconds (default: 10.0)")
    parser.add_argument("--max-clip-duration", type=float, default=60.0,
                        help="Maximum clip duration in seconds (default: 60.0)")
    parser.add_argument("--topic-change-threshold", type=float, default=0.3,
                        help="Topic change detection threshold (default: 0.3)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # If no output file is specified, create one based on the input file
        if not args.output_file:
            input_path = Path(args.transcript_file)
            output_path = input_path.with_suffix('.clips.json')
            args.output_file = str(output_path)
        
        suggestions = analyze_transcript(
            transcript_file=args.transcript_file,
            output_file=args.output_file,
            transcript_format=args.format,
            min_clip_duration=args.min_clip_duration,
            max_clip_duration=args.max_clip_duration,
            topic_change_threshold=args.topic_change_threshold,
        )
        
        print(f"\nTranscript analysis complete:")
        print(f"- Found {len(suggestions)} suggested clips")
        print(f"- Suggestions saved to: {os.path.abspath(args.output_file)}")
        
        # Print a summary of the suggestions
        for i, suggestion in enumerate(suggestions):
            start_min = int(suggestion['start_time'] // 60)
            start_sec = int(suggestion['start_time'] % 60)
            end_min = int(suggestion['end_time'] // 60)
            end_sec = int(suggestion['end_time'] % 60)
            
            print(f"\nClip {i+1}: {suggestion['topic']}")
            print(f"- Time: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} "
                  f"({suggestion['duration']:.1f}s)")
            
            # Print a short excerpt of the text
            text = suggestion['text']
            if len(text) > 100:
                text = text[:97] + "..."
            print(f"- Text: {text}")
        
        return 0
    except Exception as e:
        logger.error(f"Error analyzing transcript: {e}", exc_info=True)
        return 1


def generate_thumbnails_cli():
    """CLI entry point for thumbnail generation."""
    parser = argparse.ArgumentParser(description="Generate thumbnail candidates from video files")
    parser.add_argument("video_file", help="Path to input video file")
    parser.add_argument("--output-dir", help="Directory to save thumbnail images (default: creates a temp dir)")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of thumbnail candidates to generate (default: 10)")
    parser.add_argument("--min-interval", type=float, default=1.0,
                        help="Minimum interval between thumbnails in seconds (default: 1.0)")
    parser.add_argument("--skip-start", type=float, default=0.05,
                        help="Percentage of video to skip from start (default: 0.05, i.e., 5%%)")
    parser.add_argument("--skip-end", type=float, default=0.05,
                        help="Percentage of video to skip from end (default: 0.05, i.e., 5%%)")
    parser.add_argument("--format", default="jpg", choices=["jpg", "png"],
                        help="Output image format (default: jpg)")
    parser.add_argument("--quality", type=int, default=90,
                        help="JPEG quality (1-100, default: 90)")
    parser.add_argument("--metadata-file", 
                        help="Path to save thumbnail metadata as JSON (default: <output_dir>/thumbnails.json)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Create default output directory based on video file name if not specified
        if not args.output_dir:
            video_path = Path(args.video_file)
            args.output_dir = str(video_path.with_suffix('_thumbnails'))
        
        # Create default metadata file if not specified
        if not args.metadata_file:
            metadata_path = os.path.join(args.output_dir, "thumbnails.json")
            args.metadata_file = metadata_path
        
        # Generate thumbnails
        thumbnails = generate_thumbnails(
            video_path=args.video_file,
            output_dir=args.output_dir,
            frames_to_extract=args.count,
            min_frame_interval=args.min_interval,
            skip_start_percent=args.skip_start,
            skip_end_percent=args.skip_end,
            output_format=args.format,
            output_quality=args.quality,
            metadata_file=args.metadata_file
        )
        
        print(f"\nThumbnail generation complete:")
        print(f"- Generated {len(thumbnails)} thumbnail candidates")
        print(f"- Saved to: {os.path.abspath(args.output_dir)}")
        print(f"- Metadata: {os.path.abspath(args.metadata_file)}")
        
        # Print thumbnail information
        print("\nThumbnail candidates (sorted by quality):")
        sorted_thumbnails = sorted(thumbnails, key=lambda x: x['quality_score'], reverse=True)
        
        for i, thumb in enumerate(sorted_thumbnails):
            print(f"\n{i+1}. {os.path.basename(thumb['frame_path'])}")
            print(f"   Time: {thumb['timestamp_str']} - "
                  f"Quality: {thumb['quality_score']:.3f}")
            print(f"   Brightness: {thumb['metrics']['brightness']:.2f}, "
                  f"Contrast: {thumb['metrics']['contrast']:.2f}, "
                  f"Colorfulness: {thumb['metrics']['colorfulness']:.2f}")
        
        return 0
    except Exception as e:
        logger.error(f"Error generating thumbnails: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(remove_silence_cli())

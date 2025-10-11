#!/usr/bin/env python3
"""
Transcript and Video Combiner Utility

Combines multiple transcript segments and corresponding video files 
into a single unified transcript and video file for analysis.

Usage:
    python transcript_combiner.py --input-dir /path/to/episode/output --output-dir /path/to/output
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import logging

logger = logging.getLogger(__name__)


class TranscriptVideoCombiner:
    """
    Combines transcript segments and video files from multiple output directories.
    """
    
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def combine_transcripts(self) -> Dict[str, Any]:
        """
        Combine all transcript JSON files into a single unified transcript.
        
        Returns:
            Combined transcript dictionary with segments and timing adjusted
        """
        logger.info(f"Combining transcripts from {self.input_dir}")
        
        # Get all transcript directories sorted by timestamp
        transcript_dirs = sorted([d for d in self.input_dir.iterdir() if d.is_dir()])
        
        all_segments = []
        time_offset = 0.0
        segment_counter = 0
        
        for transcript_dir in transcript_dirs:
            transcript_file = transcript_dir / "transcript.json"
            if not transcript_file.exists():
                logger.warning(f"No transcript.json found in {transcript_dir}")
                continue
                
            logger.info(f"Processing {transcript_dir.name}...")
            
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading {transcript_file}: {e}")
                continue
            
            # Extract segments and adjust timing
            segments = []
            if 'segments' in data:
                segments = data['segments']
            elif isinstance(data, list):
                segments = data
            else:
                logger.warning(f"  No segments found in {transcript_dir.name}")
                continue
            
            # Adjust timing for each segment
            for segment in segments:
                adjusted_segment = {
                    'text': segment['text'],
                    'start': segment['start'] + time_offset,
                    'end': segment['end'] + time_offset,
                    'segment_id': f"{transcript_dir.name}_{segment.get('id', f'seg_{segment_counter}')}"
                }
                
                # Preserve additional fields if present
                if 'confidence' in segment:
                    adjusted_segment['confidence'] = segment['confidence']
                if 'speaker' in segment:
                    adjusted_segment['speaker'] = segment['speaker']
                if 'words' in segment:
                    adjusted_segment['words'] = segment['words']
                    
                all_segments.append(adjusted_segment)
                segment_counter += 1
            
            # Update time offset for next segment (add 2 second gap between segments)
            if segments:
                max_end = max(seg['end'] for seg in segments)
                time_offset += max_end + 2.0
        
        # Create combined transcript
        combined_transcript = {
            'language': 'en',
            'duration': time_offset,
            'segments': all_segments,
            'source_directories': [d.name for d in transcript_dirs if (d / "transcript.json").exists()],
            'total_segments': len(all_segments)
        }
        
        logger.info(f"Combined {len(all_segments)} segments with total duration {time_offset:.1f}s")
        return combined_transcript
    
    def combine_videos(self) -> Optional[Path]:
        """
        Combine all video files into a single video using ffmpeg.
        
        Returns:
            Path to combined video file, or None if no videos found
        """
        logger.info("Combining video files...")
        
        # Get all transcript directories sorted by timestamp
        transcript_dirs = sorted([d for d in self.input_dir.iterdir() if d.is_dir()])
        video_files = []
        
        for transcript_dir in transcript_dirs:
            # First, look for videos in the transcript directory itself
            found_video = False
            for pattern in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
                videos = list(transcript_dir.glob(pattern))
                if videos:
                    video_files.extend(videos)
                    found_video = True
                    break
            
            # If not found in subdirectory, look in parent directory with matching timestamp
            if not found_video:
                dir_timestamp = transcript_dir.name
                parent_dir = transcript_dir.parent  # This is the output directory
                grandparent_dir = parent_dir.parent  # This is the episode directory
                logger.debug(f"Looking for video with timestamp: {dir_timestamp} in grandparent: {grandparent_dir}")
                
                # Try exact match first (most likely case)
                exact_file = grandparent_dir / f"{dir_timestamp}.mp4"
                logger.debug(f"Checking exact file: {exact_file}, exists: {exact_file.exists()}")
                if exact_file.exists():
                    video_files.append(exact_file)
                    logger.info(f"Found exact video: {exact_file}")
                    continue
                
                # Then try pattern matching for other extensions
                for pattern in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
                    matching_videos = list(grandparent_dir.glob(f"{dir_timestamp}{pattern}"))
                    logger.debug(f"Pattern {dir_timestamp}{pattern} found: {len(matching_videos)} files")
                    if matching_videos:
                        video_files.extend(matching_videos)
                        logger.info(f"Found video in grandparent: {matching_videos[0]}")
                        break
        
        if not video_files:
            logger.warning("No video files found")
            return None
        
        # Sort video files to match transcript order
        video_files.sort(key=lambda x: x.parent.name)
        
        logger.info(f"Found {len(video_files)} video files to combine")
        
        # Create file list for ffmpeg
        file_list_path = self.output_dir / "video_file_list.txt"
        with open(file_list_path, 'w') as f:
            for video_file in video_files:
                # Use absolute paths to avoid issues
                f.write(f"file '{video_file.absolute()}'\n")
        
        # Output video path
        output_video = self.output_dir / "combined_video.mp4"
        
        # Use ffmpeg to combine videos
        try:
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(file_list_path),
                '-c', 'copy',
                '-y',  # Overwrite output file
                str(output_video)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Video combination successful: {output_video}")
            return output_video
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error combining videos: {e}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg for video combining.")
            return None
    
    def combine_all(self) -> tuple[Dict[str, Any], Optional[Path]]:
        """
        Combine both transcripts and videos.
        
        Returns:
            Tuple of (combined_transcript, combined_video_path)
        """
        logger.info("Starting transcript and video combination...")
        
        # Combine transcripts
        combined_transcript = self.combine_transcripts()
        
        # Save combined transcript
        transcript_output = self.output_dir / "combined_transcript.json"
        with open(transcript_output, 'w', encoding='utf-8') as f:
            json.dump(combined_transcript, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Combined transcript saved to: {transcript_output}")
        
        # Combine videos
        combined_video = self.combine_videos()
        
        return combined_transcript, combined_video


def main():
    """CLI entry point for transcript and video combiner."""
    parser = argparse.ArgumentParser(
        description="Combine transcript segments and video files from multiple directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Combine episode 3 outputs
  transcript-combiner --input-dir /path/to/episode3/output --output-dir /path/to/combined
  
  # Combine with custom naming
  transcript-combiner --input-dir ./episode_outputs --output-dir ./combined --prefix episode3
        """
    )
    
    parser.add_argument("--input-dir", "-i", required=True,
                        help="Directory containing transcript/video subdirectories")
    parser.add_argument("--output-dir", "-o", required=True,
                        help="Output directory for combined files")
    parser.add_argument("--prefix", "-p", default="",
                        help="Prefix for output files")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize combiner
        combiner = TranscriptVideoCombiner(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir)
        )
        
        # Combine everything
        combined_transcript, combined_video = combiner.combine_all()
        
        # Print summary
        print(f"\n✅ Combination complete!")
        print(f"📁 Output directory: {args.output_dir}")
        print(f"📝 Combined transcript: {len(combined_transcript['segments'])} segments")
        print(f"⏱️ Total duration: {combined_transcript['duration']:.1f} seconds")
        
        if combined_video:
            print(f"🎬 Combined video: {combined_video}")
            print(f"📊 Video size: {combined_video.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("⚠️  No video combination completed")
        
        print(f"\n📂 Files created:")
        print(f"   • {Path(args.output_dir) / 'combined_transcript.json'}")
        if combined_video:
            print(f"   • {combined_video}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during combination: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Simple script to create a 30-second sample from a video for faster iteration.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def create_sample_video(input_video: str, output_video: str = None, duration: int = 30, start_time: int = 0):
    """
    Create a 30-second sample video using ffmpeg.
    
    Args:
        input_video: Path to input video
        output_video: Path to output video (optional)
        duration: Duration in seconds (default: 30)
        start_time: Start time in seconds (default: 0)
    """
    input_path = Path(input_video)
    
    if not input_path.exists():
        print(f"Error: Input video {input_video} not found!")
        return False
    
    # Generate output filename if not provided
    if output_video is None:
        output_video = input_path.parent / f"{input_path.stem}_sample_{duration}s{input_path.suffix}"
    
    output_path = Path(output_video)
    
    print(f"Creating {duration}-second sample from {input_video}...")
    print(f"Start time: {start_time}s")
    print(f"Output: {output_path}")
    
    # Use ffmpeg to extract sample
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-ss', str(start_time),        # Start time
        '-t', str(duration),           # Duration
        '-c', 'copy',                  # Copy streams without re-encoding (faster)
        '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
        '-y',                          # Overwrite output file
        str(output_path)
    ]
    
    try:
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Sample video created successfully: {output_path}")
        print(f"📁 File size: {output_path.stat().st_size / (1024*1024):.1f} MB")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating sample video:")
        print(f"Return code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        
        # Try with re-encoding if copy failed
        print("\n🔄 Trying with re-encoding...")
        cmd_reencode = [
            'ffmpeg',
            '-i', str(input_path),
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:v', 'libx264',            # Re-encode video
            '-c:a', 'aac',                # Re-encode audio
            '-crf', '23',                 # Good quality
            '-preset', 'fast',            # Fast encoding
            '-y',
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd_reencode, capture_output=True, text=True, check=True)
            print(f"✅ Sample video created with re-encoding: {output_path}")
            print(f"📁 File size: {output_path.stat().st_size / (1024*1024):.1f} MB")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ Re-encoding also failed:")
            print(f"Return code: {e2.returncode}")
            print(f"Error output: {e2.stderr}")
            return False
    
    except FileNotFoundError:
        print("❌ Error: ffmpeg not found. Please install ffmpeg first.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Create a sample video for faster iteration")
    parser.add_argument('input_video', help='Input video file path')
    parser.add_argument('-o', '--output', help='Output video file path (optional)')
    parser.add_argument('-d', '--duration', type=int, default=30, help='Sample duration in seconds (default: 30)')
    parser.add_argument('-s', '--start', type=int, default=0, help='Start time in seconds (default: 0)')
    
    args = parser.parse_args()
    
    success = create_sample_video(
        input_video=args.input_video,
        output_video=args.output,
        duration=args.duration,
        start_time=args.start
    )
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
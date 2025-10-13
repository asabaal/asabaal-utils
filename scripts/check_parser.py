#!/usr/bin/env python
"""
Simple script to verify the CLI parser for extract-clips.
"""

import argparse

parser = argparse.ArgumentParser(description="Extract video clips based on transcript analysis")
parser.add_argument("video_file", help="Path to source video file")
parser.add_argument("json_file", help="Path to JSON file with clip suggestions")
parser.add_argument("--output-dir", help="Directory to save extracted clips")
parser.add_argument("--clip-prefix", default="clip",
                    help="Prefix for output clip filenames (default: 'clip')")
parser.add_argument("--top-n", type=int, default=None,
                    help="Only extract the top N clips by importance score")
parser.add_argument("--min-score", type=float, default=None,
                    help="Only extract clips with importance score above this value")
parser.add_argument("--min-duration", type=float, default=None,
                    help="Only extract clips longer than this duration in seconds")
parser.add_argument("--max-duration", type=float, default=None,
                    help="Only extract clips shorter than this duration in seconds")
parser.add_argument("--padding", type=float, default=0.5,
                    help="Add padding in seconds before/after each clip (default: 0.5)")
parser.add_argument("--disable-ffmpeg", action="store_true",
                    help="Disable direct FFmpeg implementation and use MoviePy instead")
parser.add_argument("--log-level", default="INFO",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    help="Set the logging level")

# Transcript enhancement options
enhancement_group = parser.add_argument_group('Transcript Enhancement Options')
enhancement_group.add_argument("--enhance-transcript", action="store_true",
                    help="Apply transcript enhancement before extracting clips")
enhancement_group.add_argument("--remove-fillers", action="store_true",
                    help="Remove filler words like 'um', 'uh', etc.")
enhancement_group.add_argument("--handle-repetitions", action="store_true",
                    help="Remove or consolidate repeated phrases")
enhancement_group.add_argument("--respect-sentences", action="store_true",
                    help="Optimize clip boundaries to respect sentence boundaries")
enhancement_group.add_argument("--preserve-semantic-units", action="store_true",
                    help="Preserve semantic units like explanations and lists")
enhancement_group.add_argument("--filler-policy", choices=["remove_all", "keep_all", "context_sensitive"],
                    default="remove_all", help="Policy for handling filler words (default: remove_all)")
enhancement_group.add_argument("--repetition-strategy", choices=["first_instance", "cleanest_instance", "combine"],
                    default="first_instance", help="Strategy for handling repetitions (default: first_instance)")

# Check if help flag is provided
import sys
if "--help" in sys.argv or "-h" in sys.argv:
    parser.print_help()
    sys.exit(0)

# Parse test arguments
args = parser.parse_args([
    "/path/to/video.mp4",  # video_file
    "/path/to/transcript.json",  # json_file
    "--enhance-transcript",  # Enable transcript enhancement
    "--remove-fillers",  # Remove filler words
    "--handle-repetitions",  # Handle repetitions
    "--respect-sentences",  # Respect sentence boundaries
    "--filler-policy", "remove_all",  # Filler word policy
    "--repetition-strategy", "first_instance",  # Repetition strategy
    "--log-level", "DEBUG"  # Log level
])

# Print out the parsed arguments
print("Parsed arguments:")
for arg, value in vars(args).items():
    print(f"  {arg}: {value}")
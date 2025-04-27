#!/usr/bin/env python
"""
Test script for extract-clips command with transcript enhancement.
This script simulates command-line arguments for extract-clips
and runs the CLI function directly.
"""

import sys
import argparse
from src.asabaal_utils.video_processing.cli import extract_clips_cli

# Override the argparse parser to capture the arguments
class CaptureArgsParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = None
        
    def parse_args(self, args=None, namespace=None):
        self.args = super().parse_args(args, namespace)
        # Print the parsed arguments
        print("\nParsed arguments:")
        for arg, value in vars(self.args).items():
            print(f"  {arg}: {value}")
        return self.args
        
    def exit(self, status=0, message=None):
        # Don't exit, just print the message
        if message:
            print(message)

# Sample arguments for a transcript enhancement run
test_args = [
    "/path/to/video.mp4",  # video_file
    "/path/to/transcript.json",  # json_file
    "--enhance-transcript",  # Enable transcript enhancement
    "--remove-fillers",  # Remove filler words
    "--handle-repetitions",  # Handle repetitions
    "--respect-sentences",  # Respect sentence boundaries
    "--filler-policy", "remove_all",  # Filler word policy
    "--repetition-strategy", "first_instance",  # Repetition strategy
    "--log-level", "DEBUG"  # Log level
]

# Replace the original parser and run the CLI function
original_parser = argparse.ArgumentParser
argparse.ArgumentParser = CaptureArgsParser

# Set up command-line arguments
print(f"Running extract_clips_cli with args: {test_args}")
sys.argv = ["extract-clips"] + test_args

try:
    # This should parse arguments but not actually run the function
    # since we overrode the parser's exit method
    extract_clips_cli()
except Exception as e:
    print(f"Error: {e}")
finally:
    # Restore the original parser
    argparse.ArgumentParser = original_parser
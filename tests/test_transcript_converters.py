#!/usr/bin/env python3
"""
Test script for transcript format converters.

This script tests the transcript conversion functions with sample inputs
to verify they work correctly before implementing in Abacus AI.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import our module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the conversion functions
from src.asabaal_utils.video_processing.transcript_converters import (
    convert_single_line_srt_to_json,
    convert_standard_srt_to_json,
    detect_and_convert_transcript
)


def test_single_line_srt():
    """Test conversion with a sample single-line SRT format."""
    print("\n=== Testing Single-Line SRT Format ===\n")
    
    # Sample single-line SRT content
    sample_input = """1 00:00:00,000 --> 00:00:00,983 hey everyone what's up  2 00:00:00,983 --> 00:00:04,566 so I'm here today to tell you that I have  3 00:00:05,700 --> 00:00:06,583 so I'm here today  4 00:00:06,583 --> 00:00:09,100 not only to give you an update on the only permits  5 00:00:09,100 --> 00:00:10,850 blessing um  6 00:00:12,100 --> 00:00:15,450 I'm also here to tell you that in  7 00:00:16,300 --> 00:00:18,383 I'm also here to tell you that I'm starting"""
    
    # Convert to JSON
    result = convert_single_line_srt_to_json(sample_input)
    
    # Print the number of segments
    print(f"Found {len(result['segments'])} segments.")
    
    # Print segment details
    for i, segment in enumerate(result["segments"]):
        print(f"\nSegment {i+1}:")
        print(f"  ID: {segment['id']}")
        print(f"  Start time: {segment['start_time']}")
        print(f"  End time: {segment['end_time']}")
        print(f"  Duration: {segment['duration']}")
        print(f"  Text: {segment['text']}")
    
    # Save result to a file for inspection
    with open("test_single_line_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nSaved full result to test_single_line_result.json")
    
    # Verify expectations
    assert len(result["segments"]) == 7, f"Expected 7 segments, got {len(result['segments'])}"
    assert result["segments"][0]["text"] == "hey everyone what's up", f"First segment text doesn't match"
    assert result["segments"][6]["start_time"] == 16.3, f"Last segment start time doesn't match"
    
    print("\n✓ All tests passed!")
    return result


def test_from_file(file_path):
    """Test conversion with a transcript file."""
    print(f"\n=== Testing File: {file_path} ===\n")
    
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Auto-detect format and convert
    result = detect_and_convert_transcript(content)
    
    # Print format and segment count
    print(f"Detected format: {result['metadata'].get('source_format', 'unknown')}")
    print(f"Found {len(result['segments'])} segments.")
    
    # Print the first and last segments
    if result["segments"]:
        print("\nFirst segment:")
        first = result["segments"][0]
        print(f"  Start time: {first.get('start_time', 'N/A')}")
        print(f"  Text: {first.get('text', 'N/A')}")
        
        if len(result["segments"]) > 1:
            print("\nLast segment:")
            last = result["segments"][-1]
            print(f"  Start time: {last.get('start_time', 'N/A')}")
            print(f"  Text: {last.get('text', 'N/A')}")
    
    # Save result to a file for inspection
    output_file = f"{Path(file_path).stem}_converted.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nSaved full result to {output_file}")
    return result


def main():
    """Main function to run tests based on command line arguments."""
    parser = argparse.ArgumentParser(description="Test transcript conversion functions.")
    parser.add_argument("--file", help="Path to transcript file to test")
    parser.add_argument("--sample", action="store_true", help="Test with built-in sample")
    args = parser.parse_args()
    
    if args.file:
        test_from_file(args.file)
    elif args.sample:
        test_single_line_srt()
    else:
        # If no arguments, run the sample test
        test_single_line_srt()


if __name__ == "__main__":
    main()

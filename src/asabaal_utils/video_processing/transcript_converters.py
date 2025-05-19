"""
Transcript format conversion utilities.

This module provides functions for converting various transcript formats
(SRT, VTT, single-line SRT, etc.) to a standardized JSON structure
for use in the transcript enhancement pipeline.
"""

import re
import json
import logging

logger = logging.getLogger(__name__)


def convert_single_line_srt_to_json(srt_content):
    """
    Convert a single-line SRT-like format to structured JSON.
    
    This handles formats where each subtitle entry is on the same line
    with entry numbers and timestamps inline. Example format:
    "1 00:00:00,000 --> 00:00:00,983 text here 2 00:00:00,983 --> 00:00:04,566 more text"
    
    Args:
        srt_content (str): The content in single-line SRT-like format
        
    Returns:
        dict: A structured representation with segments
    """
    # Initialize result structure
    result = {
        "segments": [],
        "metadata": {
            "source_format": "single_line_srt",
            "segment_count": 0
        }
    }
    
    # Pattern to match segments in the single-line format
    # Looking for: number timestamp --> timestamp text (followed by another number or end of string)
    pattern = re.compile(r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+(.+?)(?=\s+\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->|$)', re.DOTALL)
    
    # Find all segments
    matches = pattern.findall(srt_content)
    
    if not matches:
        logger.warning("No matches found in single-line SRT format. Check input format.")
        result["metadata"]["error"] = "No matches found in input content"
        return result
    
    # Process each segment
    for match in matches:
        segment_id, start_time_str, end_time_str, text = match
        
        # Convert timestamps to seconds
        start_time = timestamp_to_seconds(start_time_str)
        end_time = timestamp_to_seconds(end_time_str)
        
        # Clean up text
        text = text.strip()
        
        # Create segment
        segment = {
            "id": int(segment_id),
            "start_time": start_time,
            "end_time": end_time,
            "duration": round(end_time - start_time, 3),
            "text": text
        }
        
        # Add to result
        result["segments"].append(segment)
    
    # Update metadata
    result["metadata"]["segment_count"] = len(result["segments"])
    
    # Add full transcript text
    full_text = " ".join(segment["text"] for segment in result["segments"])
    result["text"] = full_text
    
    return result


def convert_standard_srt_to_json(srt_content):
    """
    Convert standard multi-line SRT subtitle content to structured JSON.
    
    Args:
        srt_content (str): The content of an SRT file as a string
        
    Returns:
        dict: A structured representation with segments
    """
    # Initialize result structure
    result = {
        "segments": [],
        "metadata": {
            "source_format": "standard_srt",
            "segment_count": 0
        }
    }
    
    # Pattern to match the entire subtitle entry in standard SRT format
    pattern = re.compile(r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+((?:.+\s*)+?)(?:\n\s*\n|$)', re.MULTILINE)
    
    # Find all subtitle entries
    matches = pattern.findall(srt_content)
    
    if not matches:
        logger.warning("No matches found in standard SRT format. Check input format.")
        result["metadata"]["error"] = "No matches found in input content"
        return result
    
    # Process each subtitle entry
    for match in matches:
        segment_id, start_time_str, end_time_str, text = match
        
        # Convert timestamps to seconds
        start_time = timestamp_to_seconds(start_time_str)
        end_time = timestamp_to_seconds(end_time_str)
        
        # Clean up text
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
        text = text.strip()                  # Trim whitespace
        
        # Create segment
        segment = {
            "id": int(segment_id),
            "start_time": start_time,
            "end_time": end_time,
            "duration": round(end_time - start_time, 3),
            "text": text
        }
        
        # Add to result
        result["segments"].append(segment)
    
    # Update metadata
    result["metadata"]["segment_count"] = len(result["segments"])
    
    # Add full transcript text
    full_text = " ".join(segment["text"] for segment in result["segments"])
    result["text"] = full_text
    
    return result


def timestamp_to_seconds(timestamp):
    """
    Convert an SRT timestamp to seconds.
    
    Args:
        timestamp (str): Timestamp in format HH:MM:SS,mmm
        
    Returns:
        float: Time in seconds
    """
    hours, minutes, rest = timestamp.split(':')
    seconds, milliseconds = rest.split(',')
    total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + int(seconds) + (int(milliseconds) / 1000)
    return round(total_seconds, 3)


def detect_and_convert_transcript(content):
    """
    Detect the transcript format and convert to structured JSON.
    
    Args:
        content (str): Transcript content in any supported format
        
    Returns:
        dict: Structured representation of the transcript
    """
    # Check if it looks like standard SRT (with proper line breaks)
    if re.search(r'\d+\n\d{2}:\d{2}:\d{2},\d{3}\s+-->', content):
        logger.info("Detected standard SRT format")
        return convert_standard_srt_to_json(content)
    
    # Check if it looks like single-line SRT
    elif re.search(r'\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->', content):
        logger.info("Detected single-line SRT format")
        return convert_single_line_srt_to_json(content)
    
    # Check if it looks like JSON
    elif content.strip().startswith('{') or content.strip().startswith('['):
        logger.info("Detected JSON format")
        try:
            parsed = json.loads(content)
            return {
                "segments": parsed.get("segments", []),
                "text": parsed.get("text", ""),
                "metadata": {
                    "source_format": "json",
                    "segment_count": len(parsed.get("segments", []))
                }
            }
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON format")
            return {
                "segments": [],
                "metadata": {
                    "source_format": "unknown",
                    "error": "Failed to parse JSON format"
                }
            }
    
    # Default to plain text
    else:
        logger.info("Format not recognized, treating as plain text")
        return {
            "segments": [{
                "id": 1,
                "start_time": 0,
                "end_time": 0,
                "duration": 0,
                "text": content.strip()
            }],
            "text": content.strip(),
            "metadata": {
                "source_format": "plain_text",
                "segment_count": 1,
                "warning": "Plain text lacks timing information. Timestamps set to 0."
            }
        }

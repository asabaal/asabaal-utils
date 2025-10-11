"""
Transcription-based silence removal tool.

This module uses audio transcription to accurately detect speech boundaries
and remove only true silence, preserving all spoken content.
"""

import os
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Union, Optional, Dict, Any
import logging

from .moviepy_imports import VideoFileClip
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from audio_transcription.config import TranscriptionConfig
from audio_transcription.transcriber import process_media_file, extract_audio
from audio_transcription.models import Transcript, Segment, Word

logger = logging.getLogger(__name__)


class TranscriptionSilenceRemover:
    """
    Silence remover that uses transcription to detect actual speech boundaries.
    
    This approach ensures that:
    1. No spoken content is cut off
    2. Video continuity is preserved through FFmpeg stream copying
    3. Transcript consistency is maintained between raw and processed files
    """
    
    def __init__(
        self,
        min_gap_duration: float = 1.0,
        max_gap_duration: float = 10.0,
        padding: float = 0.2,
        transcription_model: str = "base",
        device: str = "auto",
        use_vad: bool = True,
    ):
        """
        Initialize the transcription-based silence remover.
        
        Args:
            min_gap_duration: Minimum gap duration to consider for removal (seconds)
            max_gap_duration: Maximum gap duration to remove at once (seconds)
            padding: Padding to keep around speech segments (seconds)
            transcription_model: Whisper model size for transcription
            device: Device for transcription (auto, cpu, cuda)
            use_vad: Whether to use voice activity detection
        """
        self.min_gap_duration = min_gap_duration
        self.max_gap_duration = max_gap_duration
        self.padding = padding
        self.transcription_model = transcription_model
        self.device = device
        self.use_vad = use_vad
    
    def transcribe_for_silence_detection(self, video_path: Union[str, Path]) -> Transcript:
        """
        Transcribe video to get accurate speech timing.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Transcript with word-level timing information
        """
        video_path = Path(video_path)
        
        # Create temporary config for transcription
        with tempfile.TemporaryDirectory() as temp_dir:
            config = TranscriptionConfig(
                asr_model=self.transcription_model,
                device=self.device,
                use_vad=self.use_vad,
                outbox=Path(temp_dir),
                use_whisperx=False,  # We don't need alignment for basic silence detection
                enable_llm_post=False,
            )
            
            # Process the media file to get transcription
            output_dir = process_media_file(video_path, config)
            
            # Load the transcript
            transcript_file = output_dir / "transcript.json"
            if transcript_file.exists():
                transcript_data = json.loads(transcript_file.read_text(encoding="utf-8"))
                return Transcript(**transcript_data)
            else:
                raise RuntimeError("Transcription failed - no transcript.json generated")
    
    def detect_speech_segments(self, transcript: Transcript) -> List[Tuple[float, float]]:
        """
        Extract speech segments from transcript.
        
        Args:
            transcript: Transcript with timing information
            
        Returns:
            List of (start, end) tuples for speech segments
        """
        speech_segments = []
        
        if not transcript.segments:
            return speech_segments
        
        # If we have word-level timing, use that for precision
        if any(segment.words for segment in transcript.segments):
            # Collect all words with timing
            words_with_timing = []
            for segment in transcript.segments:
                if segment.words:
                    words_with_timing.extend([
                        (word.start, word.end) for word in segment.words
                        if word.start is not None and word.end is not None
                    ])
            
            if words_with_timing:
                # Sort by start time
                words_with_timing.sort(key=lambda x: x[0])
                
                # Merge consecutive words into speech segments
                current_start, current_end = words_with_timing[0]
                
                for start, end in words_with_timing[1:]:
                    # If this word starts soon after the previous one, merge it
                    if start <= current_end + self.padding:
                        current_end = max(current_end, end)
                    else:
                        speech_segments.append((current_start, current_end))
                        current_start, current_end = start, end
                
                speech_segments.append((current_start, current_end))
                return speech_segments
        
        # Fall back to segment-level timing
        for segment in transcript.segments:
            if segment.start < segment.end:  # Valid segment
                speech_segments.append((segment.start, segment.end))
        
        return speech_segments
    
    def find_gaps_to_remove(
        self, 
        speech_segments: List[Tuple[float, float]], 
        total_duration: float
    ) -> List[Tuple[float, float]]:
        """
        Identify gaps between speech segments that should be removed.
        
        Args:
            speech_segments: List of (start, end) tuples for speech
            total_duration: Total duration of the video
            
        Returns:
            List of (start, end) tuples for gaps to remove
        """
        gaps_to_remove = []
        
        if not speech_segments:
            return gaps_to_remove
        
        # Sort speech segments by start time
        speech_segments.sort(key=lambda x: x[0])
        
        # Find gap before first speech segment
        first_speech_start = speech_segments[0][0]
        if first_speech_start > self.min_gap_duration:
            gaps_to_remove.append((0, min(first_speech_start, self.max_gap_duration)))
        
        # Find gaps between speech segments
        for i in range(len(speech_segments) - 1):
            current_end = speech_segments[i][1]
            next_start = speech_segments[i + 1][0]
            
            gap_duration = next_start - current_end
            if gap_duration >= self.min_gap_duration:
                # Remove the gap, but respect max_gap_duration
                gap_end = min(next_start, current_end + self.max_gap_duration)
                gaps_to_remove.append((current_end, gap_end))
        
        # Find gap after last speech segment
        last_speech_end = speech_segments[-1][1]
        if total_duration - last_speech_end > self.min_gap_duration:
            gap_start = max(last_speech_end, total_duration - self.max_gap_duration)
            gaps_to_remove.append((gap_start, total_duration))
        
        return gaps_to_remove
    
    def remove_silence_ffmpeg(
        self,
        input_file: Union[str, Path],
        output_file: Union[str, Path],
        gaps_to_remove: List[Tuple[float, float]]
    ) -> Tuple[float, float, float]:
        """
        Remove silence using FFmpeg with stream copying for perfect quality.
        
        Args:
            input_file: Path to input video
            output_file: Path to output video
            gaps_to_remove: List of (start, end) tuples to remove
            
        Returns:
            Tuple of (original_duration, output_duration, time_saved)
        """
        input_file = str(input_file)
        output_file = str(output_file)
        
        # Get original duration
        duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", input_file
        ]
        duration_result = subprocess.run(
            duration_cmd, capture_output=True, text=True, check=True
        )
        original_duration = float(json.loads(duration_result.stdout)["format"]["duration"])
        
        if not gaps_to_remove:
            # No gaps to remove, just copy the file
            shutil.copy2(input_file, output_file)
            return original_duration, original_duration, 0.0
        
        # Create segments to keep (inverse of gaps to remove)
        segments_to_keep = []
        current_time = 0.0
        
        for gap_start, gap_end in sorted(gaps_to_remove):
            if current_time < gap_start:
                segments_to_keep.append((current_time, gap_start))
            current_time = gap_end
        
        # Add final segment if there's remaining content
        if current_time < original_duration:
            segments_to_keep.append((current_time, original_duration))
        
        if not segments_to_keep:
            # Nothing to keep, copy original
            shutil.copy2(input_file, output_file)
            return original_duration, original_duration, 0.0
        
        # Use FFmpeg to extract and concatenate segments
        with tempfile.TemporaryDirectory() as temp_dir:
            segment_files = []
            
            # Extract each segment
            for i, (start, end) in enumerate(segments_to_keep):
                segment_file = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
                duration = end - start
                
                extract_cmd = [
                    "ffmpeg", "-y",
                    "-i", input_file,
                    "-ss", str(start),
                    "-t", str(duration),
                    "-c", "copy",  # Stream copy for perfect quality
                    "-avoid_negative_ts", "make_zero",
                    segment_file
                ]
                
                subprocess.run(extract_cmd, check=True, capture_output=True)
                segment_files.append(segment_file)
            
            # Create concat file
            concat_file = os.path.join(temp_dir, "segments.txt")
            with open(concat_file, 'w') as f:
                for segment_file in segment_files:
                    f.write(f"file '{segment_file}'\n")
            
            # Concatenate segments
            concat_cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",  # Stream copy for perfect quality
                output_file
            ]
            
            subprocess.run(concat_cmd, check=True, capture_output=True)
        
        # Get output duration
        output_duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", output_file
        ]
        output_duration_result = subprocess.run(
            output_duration_cmd, capture_output=True, text=True, check=True
        )
        output_duration = float(json.loads(output_duration_result.stdout)["format"]["duration"])
        
        time_saved = original_duration - output_duration
        return original_duration, output_duration, time_saved
    
    def remove_silence(
        self, 
        input_file: Union[str, Path], 
        output_file: Union[str, Path]
    ) -> Tuple[float, float, float]:
        """
        Remove silence from video using transcription-based detection.
        
        Args:
            input_file: Path to input video file
            output_file: Path to output video file
            
        Returns:
            Tuple of (original_duration, output_duration, time_saved)
        """
        logger.info(f"Starting transcription-based silence removal for {input_file}")
        
        # Step 1: Transcribe to get speech timing
        logger.info("Transcribing audio to detect speech boundaries...")
        transcript = self.transcribe_for_silence_detection(input_file)
        
        # Step 2: Extract speech segments
        logger.info("Analyzing speech patterns...")
        speech_segments = self.detect_speech_segments(transcript)
        
        if not speech_segments:
            logger.warning("No speech detected in the audio")
            shutil.copy2(input_file, output_file)
            return 0, 0, 0
        
        # Step 3: Find gaps to remove
        total_duration = transcript.duration or self._get_video_duration(input_file)
        gaps_to_remove = self.find_gaps_to_remove(speech_segments, total_duration)
        
        logger.info(f"Found {len(gaps_to_remove)} gaps to remove")
        total_gap_time = sum(end - start for start, end in gaps_to_remove)
        logger.info(f"Total silence to remove: {total_gap_time:.2f} seconds")
        
        # Step 4: Remove gaps using FFmpeg
        logger.info("Processing video with FFmpeg...")
        return self.remove_silence_ffmpeg(input_file, output_file, gaps_to_remove)
    
    def _get_video_duration(self, video_path: Union[str, Path]) -> float:
        """Get video duration using FFprobe."""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(json.loads(result.stdout)["format"]["duration"])


def remove_silence_transcription(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    min_gap_duration: float = 1.0,
    max_gap_duration: float = 10.0,
    padding: float = 0.2,
    transcription_model: str = "base",
    device: str = "auto",
    use_vad: bool = True,
) -> Tuple[float, float, float]:
    """
    Remove silence from video using transcription-based detection.
    
    This function provides a simple interface to the transcription-based silence
    removal functionality.
    
    Args:
        input_file: Path to the input video file
        output_file: Path to save the output video file
        min_gap_duration: Minimum gap duration to consider for removal (seconds)
        max_gap_duration: Maximum gap duration to remove at once (seconds)
        padding: Padding to keep around speech segments (seconds)
        transcription_model: Whisper model size for transcription
        device: Device for transcription (auto, cpu, cuda)
        use_vad: Whether to use voice activity detection
        
    Returns:
        Tuple of (original_duration, output_duration, time_saved)
    """
    remover = TranscriptionSilenceRemover(
        min_gap_duration=min_gap_duration,
        max_gap_duration=max_gap_duration,
        padding=padding,
        transcription_model=transcription_model,
        device=device,
        use_vad=use_vad,
    )
    
    return remover.remove_silence(input_file, output_file)
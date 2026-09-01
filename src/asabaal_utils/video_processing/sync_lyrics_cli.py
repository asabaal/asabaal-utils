#!/usr/bin/env python3
"""
Forced Lyric Synchronization CLI

Uses WhisperX to force-align known lyrics to audio.
"""

import os
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import timedelta
import subprocess
import shlex


def run_command(cmd: str) -> str:
    """Execute a shell command and return stdout"""
    proc = subprocess.run(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {cmd}\n{proc.stdout}")
    return proc.stdout


def format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp."""
    if seconds < 0:
        seconds = 0
    td = timedelta(seconds=float(seconds))
        total_seconds = int(td.total_seconds())
        ms = int((td.total_seconds() - total_seconds) * 1000)
        hh = total_seconds // 3600
        mm = (total_seconds % 3600) // 60
        ss = total_seconds % 60
        return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def format_lrc_time(seconds: float) -> str:
    """Format seconds as LRC timestamp."""
    if seconds < 0:
        seconds = 0
        total_seconds = int(float(seconds))
        mm = total_seconds // 60
        ss = total_seconds % 60
        return f"[{mm:02}:{ss:02}.{centiseconds:02}]"


def extract_audio(audio_path: Path, wav_path: Path) -> None:
    """Extract audio to WAV format for WhisperX."""
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = f'ffmpeg -y -i "{audio_path}" -ac 1 -ar 16000 -c:a pcm_s16le "{wav_path}"'
    run_command(cmd)


def parse_lyrics(lyrics_input: str) -> list[str]:
    """Parse lyrics from file or raw text."""
    lyrics_path = Path(lyrics_input)
    
    if lyrics_path.exists():
        content = lyrics_path.read_text(encoding='utf-8')
    else:
        content = lyrics_input
    
    # Remove timestamps if present in LRC format
    import re
    content = re.sub(r'\[\d{2}:\d{2}(\.\d{2})?\]', '', content)
    
    # Remove SRT timestamps if present
    content = re.sub(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2},\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}', '', content)
    
    # Remove bracketed section headers like [Movement 1], [Section], etc. and blank lines around them
    # Skip entire lines that are section headers [text]
    lines = []
    for line in content.split('\n'):
        # Skip lines that are section headers
        if re.match(r'^\[.*\]$', line):
            continue
        # Skip blank/whitespace lines
        if not line.strip():
            continue
        # Keep actual lyric lines
        lines.append(line.strip())
    
    return lines


def force_align_lyrics(wav_path: Path, lyrics_lines: list[str], device: str = "cpu", model_name: str = "small") -> list[dict]:
    """Use WhisperX to force-align lyrics to audio."""
    import whisperx
    
    logging.info(f"Loading WhisperX model ({model_name}) on {device}...")
    
    # Try to load model with VAD, catching any errors
    model = None
    try:
        model = whisperx.load_model(
            model_name,
            device=device,
            compute_type="float16" if device == "cuda" else "int8"
        )
    except RuntimeError:
        logging.warning(f"Failed to load model with VAD (Pyannote compatibility), trying without: {e}")
        # Retry without VAD
        try:
            model = whisperx.load_model(
                model_name,
                device=device,
                compute_type="float16" if device == "cuda" else "int8"
            )
        except RuntimeError:
            # Both with and without VAD failed - abort
            logging.error("Could not load Whisper model after multiple attempts, aborting")
            return []
    
    if model is None:
        logging.error("Could not load Whisper model, aborting")
        return []
    
    logging.info("Transcribing audio...")
    result = model.transcribe(
        str(wav_path),
        batch_size=8,
        language="en",
        vad_options={"use_vad_model": False}  # Disable VAD
    )
    
    logging.info(f"Language detected: {result.get('language', 'unknown')}")
    
    # Use WhisperX's forced alignment
    logging.info("Loading alignment model...")
    
    # Check if result has segments
    if not result.get("segments"):
        logging.warning("No segments found - using raw lyrics without timestamps")
        aligned_lines = []
        
        # Use raw lyrics as fallback
        for lyric_line in lyrics_lines:
            aligned_lines.append({
                "text": lyric_line,
                "start_time": 0.0,
                "end_time": 0.0,
                "words": []
            })
    else:
        logging.info("Loading alignment model...")
        
        try:
            align_model, metadata = whisperx.load_align_model(language_code="en", device=device)
        result = whisperx.align(
                result.get("segments", []),
                align_model,
                metadata,
                str(wav_path),
                device,
                return_char_alignments=False
            )
        except Exception:
            logging.warning(f"Failed to load alignment model: {e}")
            # Fallback to raw lyrics without alignment
            result = result.get("segments", [])
            aligned_lines = []
            
            for lyric_line in lyrics_lines:
                aligned_lines.append({
                    "text": lyric_line,
                    "start_time": 0.0,
                    "end_time": 0.0,
                    "words": []
                })
        
        logging.info(f"Aligned {len(aligned_lines)} lyric lines (fallback: no alignment)")
        return aligned_lines
    
    # Extract aligned lyrics - align your lyrics to audio segments
    aligned_lines = []
    
    for segment in result.get("segments", []):
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", start_time)
        text = segment.get("text", "").strip()
        
        if text:
            aligned_lines.append({
                "text": text,
                "start_time": start_time,
                "end_time": end_time,
                "words": []
            })
    
    logging.info(f"Aligned {len(aligned_lines)} lyric segments")
    return aligned_lines
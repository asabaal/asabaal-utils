"""
Chunked Audio Analysis for Large Video Files

Memory-efficient audio processing that handles large church service videos
by processing audio in manageable chunks.
"""

import numpy as np
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union, Any
import json
import os

logger = logging.getLogger(__name__)


class ChunkedAudioAnalyzer:
    """
    Memory-efficient audio analyzer that processes large files in chunks.
    
    Uses ffmpeg to extract and process audio without loading entire file into memory.
    """
    
    def __init__(self, 
                 chunk_duration: float = 60.0,  # Process 1 minute at a time
                 sample_rate: int = 22050,
                 temp_dir: Optional[str] = None):
        """
        Initialize chunked audio analyzer.
        
        Args:
            chunk_duration: Duration of each chunk in seconds
            sample_rate: Audio sample rate for processing
            temp_dir: Directory for temporary files
        """
        self.chunk_duration = chunk_duration
        self.sample_rate = sample_rate
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
    def extract_audio_metadata(self, video_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract basic metadata from video file using ffprobe."""
        video_path = str(video_path)
        
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_streams',
            '-select_streams', 'a:0',
            '-show_format',
            '-print_format', 'json',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)
            
            # Extract relevant information
            audio_stream = None
            for stream in metadata.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise ValueError("No audio stream found in video")
            
            duration = float(metadata['format'].get('duration', 0))
            
            return {
                'duration': duration,
                'sample_rate': int(audio_stream.get('sample_rate', self.sample_rate)),
                'channels': int(audio_stream.get('channels', 1)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bit_rate': int(audio_stream.get('bit_rate', 0))
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe failed: {e}")
            raise RuntimeError(f"Failed to extract audio metadata: {e}")
    
    def extract_audio_chunk(self, 
                           video_path: Union[str, Path],
                           start_time: float,
                           duration: float,
                           output_path: Optional[str] = None) -> str:
        """
        Extract a chunk of audio from video file.
        
        Args:
            video_path: Path to video file
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Output path for audio chunk (temp file if None)
            
        Returns:
            Path to extracted audio chunk
        """
        video_path = str(video_path)
        
        if output_path is None:
            output_path = os.path.join(
                self.temp_dir, 
                f"audio_chunk_{start_time}_{duration}.wav"
            )
        
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-acodec', 'pcm_s16le',  # WAV format
            '-ar', str(self.sample_rate),
            '-ac', '1',  # Mono
            '-vn',  # No video
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed: {e}")
            raise RuntimeError(f"Failed to extract audio chunk: {e}")
    
    def analyze_video_in_chunks(self, 
                               video_path: Union[str, Path],
                               analyzer_func,
                               overlap: float = 5.0) -> List[Dict[str, Any]]:
        """
        Analyze video audio in chunks using provided analyzer function.
        
        Args:
            video_path: Path to video file
            analyzer_func: Function that takes (audio_path, start_time, end_time) and returns analysis
            overlap: Overlap between chunks in seconds
            
        Returns:
            List of analysis results for each chunk
        """
        video_path = Path(video_path)
        
        # Get video metadata
        logger.info(f"Extracting metadata from {video_path}")
        metadata = self.extract_audio_metadata(video_path)
        total_duration = metadata['duration']
        
        logger.info(f"Video duration: {total_duration:.1f}s, processing in {self.chunk_duration}s chunks")
        
        results = []
        current_time = 0.0
        chunk_num = 0
        
        # Calculate total chunks for progress
        total_chunks = int(np.ceil(total_duration / (self.chunk_duration - overlap)))
        
        while current_time < total_duration:
            chunk_num += 1
            chunk_duration = min(self.chunk_duration, total_duration - current_time)
            
            logger.info(f"Processing chunk {chunk_num}/{total_chunks} "
                       f"({current_time:.1f}s - {current_time + chunk_duration:.1f}s)")
            
            # Extract audio chunk
            temp_audio = None
            try:
                temp_audio = self.extract_audio_chunk(
                    video_path, 
                    current_time, 
                    chunk_duration
                )
                
                # Analyze chunk
                chunk_result = analyzer_func(
                    temp_audio, 
                    current_time, 
                    current_time + chunk_duration
                )
                
                if chunk_result:
                    results.append(chunk_result)
                
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_num}: {e}")
                # Continue with next chunk
                
            finally:
                # Clean up temp file
                if temp_audio and os.path.exists(temp_audio):
                    try:
                        os.remove(temp_audio)
                    except:
                        pass
            
            # Move to next chunk with overlap
            current_time += (self.chunk_duration - overlap)
        
        logger.info(f"Completed processing {chunk_num} chunks")
        return results
    
    def merge_overlapping_results(self, 
                                 results: List[Dict[str, Any]], 
                                 overlap_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Merge results from overlapping chunks.
        
        Args:
            results: List of chunk analysis results
            overlap_threshold: Minimum overlap ratio to merge segments
            
        Returns:
            Merged results
        """
        if not results:
            return []
        
        # Sort by start time
        sorted_results = sorted(results, key=lambda x: x.get('start_time', 0))
        
        merged = [sorted_results[0]]
        
        for current in sorted_results[1:]:
            last = merged[-1]
            
            # Check for overlap
            if current['start_time'] < last['end_time']:
                # Calculate overlap ratio
                overlap = (last['end_time'] - current['start_time']) / \
                         (current['end_time'] - current['start_time'])
                
                if overlap > overlap_threshold:
                    # Merge segments
                    last['end_time'] = max(last['end_time'], current['end_time'])
                    # Merge other properties as needed
                    if 'confidence' in last and 'confidence' in current:
                        last['confidence'] = (last['confidence'] + current['confidence']) / 2
                else:
                    merged.append(current)
            else:
                merged.append(current)
        
        return merged


def create_memory_efficient_analyzer(video_path: str, 
                                   chunk_duration: float = 60.0) -> ChunkedAudioAnalyzer:
    """
    Create a memory-efficient analyzer for large video files.
    
    Args:
        video_path: Path to video file
        chunk_duration: Duration of each chunk to process
        
    Returns:
        Configured ChunkedAudioAnalyzer
    """
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffmpeg not found. Please install ffmpeg for video processing.")
    
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffprobe not found. Please install ffmpeg for video processing.")
    
    return ChunkedAudioAnalyzer(chunk_duration=chunk_duration)


def extract_audio_to_file(video_path: str, output_path: str, sample_rate: int = 22050) -> None:
    """
    Extract entire audio track to a separate file for processing.
    
    This is useful when you want to process the audio separately from video.
    
    Args:
        video_path: Path to video file
        output_path: Path for output audio file
        sample_rate: Sample rate for output audio
    """
    cmd = [
        'ffmpeg',
        '-y',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # WAV format
        '-ar', str(sample_rate),
        '-ac', '1',  # Mono
        output_path
    ]
    
    logger.info(f"Extracting audio from {video_path} to {output_path}")
    
    try:
        # Run with progress
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Monitor progress
        for line in process.stderr:
            if 'time=' in line:
                # Extract time from ffmpeg output
                time_str = line.split('time=')[1].split()[0]
                print(f"\rExtracting audio... {time_str}", end='', flush=True)
        
        process.wait()
        print()  # New line after progress
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
            
        logger.info(f"Audio extracted successfully to {output_path}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract audio: {e}")
        raise
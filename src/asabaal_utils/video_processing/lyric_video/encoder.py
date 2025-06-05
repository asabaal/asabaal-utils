"""Output encoder with hardware acceleration support."""

import subprocess
import tempfile
import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple, Union
from pathlib import Path
import logging
import json

from .hardware_detection import HardwareDetector, GPUType

logger = logging.getLogger(__name__)


class OutputEncoder:
    """Handles video encoding with hardware acceleration when available."""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080), fps: float = 30.0):
        """Initialize encoder.
        
        Args:
            resolution: Output resolution (width, height)
            fps: Output frame rate
        """
        self.resolution = resolution
        self.fps = fps
        self.hardware = HardwareDetector()
        self.encoding_settings = self.hardware.recommend_encoding_settings()
        
    def encode_video(self, frame_generator, audio_path: Union[str, Path], 
                    output_path: Union[str, Path], 
                    quality_preset: str = "balanced") -> bool:
        """Encode video from frame generator.
        
        Args:
            frame_generator: Generator yielding numpy arrays (frames)
            audio_path: Path to audio file
            output_path: Output video path
            quality_preset: Quality preset ('fast', 'balanced', 'high_quality')
            
        Returns:
            True if encoding succeeded
        """
        audio_path = str(audio_path)
        output_path = str(output_path)
        
        logger.info(f"Starting video encoding to {output_path}")
        
        # Create temporary video file for frames
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            temp_video_path = temp_video.name
            
        try:
            # Encode frames to temporary video
            if not self._encode_frames_to_video(frame_generator, temp_video_path, quality_preset):
                return False
                
            # Combine with audio
            return self._combine_video_audio(temp_video_path, audio_path, output_path)
            
        finally:
            # Clean up temporary file
            try:
                Path(temp_video_path).unlink(missing_ok=True)
            except:
                pass
                
    def _encode_frames_to_video(self, frame_generator, output_path: str, 
                               quality_preset: str) -> bool:
        """Encode frames to video file."""
        # Get encoding parameters
        encoder_params = self._get_encoder_params(quality_preset)
        
        if self.encoding_settings['gpu_acceleration']:
            return self._encode_with_ffmpeg_hw(frame_generator, output_path, encoder_params)
        else:
            return self._encode_with_opencv(frame_generator, output_path, encoder_params)
            
    def _encode_with_opencv(self, frame_generator, output_path: str, 
                           params: Dict) -> bool:
        """Encode using OpenCV (CPU fallback)."""
        try:
            # Define codec
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # Create video writer
            writer = cv2.VideoWriter(
                output_path,
                fourcc,
                self.fps,
                self.resolution
            )
            
            if not writer.isOpened():
                logger.error("Failed to open video writer")
                return False
                
            frame_count = 0
            for frame in frame_generator:
                try:
                    # Debug: log frame shape
                    if frame_count == 0:
                        logger.info(f"First frame shape: {frame.shape}, dtype: {frame.dtype}")
                    
                    # Ensure frame is the right shape and type
                    if len(frame.shape) != 3:
                        logger.error(f"Unexpected frame shape: {frame.shape}")
                        continue
                        
                    h, w, channels = frame.shape
                    
                    if channels == 4:
                        # RGBA to RGB conversion
                        alpha = frame[:, :, 3].astype(np.float32) / 255.0
                        alpha = alpha[:, :, np.newaxis]  # Make it (H, W, 1)
                        rgb_part = frame[:, :, :3].astype(np.float32)
                        
                        # Alpha composite over black background
                        bgr_frame = (alpha * rgb_part).astype(np.uint8)
                        
                    elif channels == 3:
                        # Already RGB, just copy
                        bgr_frame = frame.astype(np.uint8)
                        
                    else:
                        logger.error(f"Unsupported channel count: {channels}")
                        continue
                    
                    # Convert RGB to BGR for OpenCV
                    bgr_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_RGB2BGR)
                    
                    writer.write(bgr_frame)
                    frame_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing frame {frame_count}: {e}")
                    if frame_count == 0:
                        logger.error(f"Frame details: shape={frame.shape}, dtype={frame.dtype}")
                    continue
                
                if frame_count % 30 == 0:
                    logger.info(f"Encoded {frame_count} frames...")
                    
            writer.release()
            logger.info(f"OpenCV encoding complete: {frame_count} frames")
            return True
            
        except Exception as e:
            logger.error(f"OpenCV encoding failed: {e}")
            return False
            
    def _encode_with_ffmpeg_hw(self, frame_generator, output_path: str, 
                              params: Dict) -> bool:
        """Encode using FFmpeg with hardware acceleration."""
        try:
            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-s', f"{self.resolution[0]}x{self.resolution[1]}",
                '-pix_fmt', 'rgb24',
                '-r', str(self.fps),
                '-i', '-',  # Input from stdin
                '-c:v', self.encoding_settings['encoder']
            ]
            
            # Add encoder-specific parameters
            if 'nvenc' in self.encoding_settings['encoder']:
                cmd.extend(['-preset', self.encoding_settings['preset']])
                if 'cq' in self.encoding_settings:
                    cmd.extend(['-cq', str(self.encoding_settings['cq'])])
            elif 'qsv' in self.encoding_settings['encoder']:
                cmd.extend(['-preset', self.encoding_settings['preset']])
                if 'global_quality' in self.encoding_settings:
                    cmd.extend(['-global_quality', str(self.encoding_settings['global_quality'])])
            elif 'amf' in self.encoding_settings['encoder']:
                cmd.extend(['-quality', self.encoding_settings['quality']])
                if 'qp' in self.encoding_settings:
                    cmd.extend(['-qp', str(self.encoding_settings['qp'])])
            else:
                # Software encoder fallback
                cmd.extend(['-preset', params.get('preset', 'medium')])
                cmd.extend(['-crf', str(params.get('crf', 23))])
                
            cmd.append(output_path)
            
            logger.info(f"Starting FFmpeg hardware encoding: {' '.join(cmd[:10])}...")
            
            # Start FFmpeg process
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            frame_count = 0
            for frame in frame_generator:
                # Convert to RGB if needed
                if frame.shape[2] == 4:
                    # Alpha composite over black
                    rgb_frame = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
                    alpha = frame[:, :, 3:4] / 255.0
                    rgb_frame = (alpha * frame[:, :, :3] + (1 - alpha) * rgb_frame).astype(np.uint8)
                elif frame.shape[2] == 3 and len(frame.shape) == 3:
                    # Already RGB
                    rgb_frame = frame
                else:
                    logger.error(f"Unexpected frame format: {frame.shape}")
                    continue
                    
                # Write frame to FFmpeg
                try:
                    proc.stdin.write(rgb_frame.tobytes())
                    frame_count += 1
                    
                    if frame_count % 30 == 0:
                        logger.info(f"Encoded {frame_count} frames...")
                        
                except BrokenPipeError:
                    logger.error("FFmpeg process terminated unexpectedly")
                    break
                    
            # Close stdin and wait for completion
            proc.stdin.close()
            stdout, stderr = proc.communicate()
            
            if proc.returncode == 0:
                logger.info(f"FFmpeg hardware encoding complete: {frame_count} frames")
                return True
            else:
                logger.error(f"FFmpeg encoding failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"FFmpeg hardware encoding failed: {e}")
            return False
            
    def _combine_video_audio(self, video_path: str, audio_path: str, 
                            output_path: str) -> bool:
        """Combine video and audio using FFmpeg."""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  # Copy video stream
                '-c:a', 'aac',   # Re-encode audio to AAC
                '-shortest',     # Match shortest stream
                output_path
            ]
            
            logger.info("Combining video and audio...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Video/audio combination complete")
                return True
            else:
                logger.error(f"Audio combination failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to combine audio: {e}")
            return False
            
    def _get_encoder_params(self, quality_preset: str) -> Dict:
        """Get encoding parameters for quality preset."""
        presets = {
            'fast': {
                'preset': 'fast',
                'crf': 28
            },
            'balanced': {
                'preset': 'medium', 
                'crf': 23
            },
            'high_quality': {
                'preset': 'slow',
                'crf': 18
            }
        }
        
        return presets.get(quality_preset, presets['balanced'])
        
    def get_encoding_info(self) -> Dict:
        """Get information about available encoding options."""
        gpu_info = self.hardware.detect_gpu()
        encoders = self.hardware.get_available_encoders()
        
        return {
            'gpu_detected': gpu_info.gpu_type != GPUType.NONE if gpu_info else False,
            'gpu_name': gpu_info.name if gpu_info else "None",
            'hardware_encoders': encoders,
            'recommended_settings': self.encoding_settings
        }
"""
Frame extraction utility for video files.

This module provides a robust utility for extracting frames from video files
with support for various formats, multiple extraction methods, and quality assessment.
It handles path conversions between different operating systems, particularly for
WSL and Windows interoperability.
"""

import os
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import subprocess
from PIL import Image, ImageStat
import numpy as np

from .path_utils import convert_path_to_current_os, resolve_media_path, get_available_wsl_mounts

logger = logging.getLogger(__name__)


class FrameExtractor:
    """
    A robust utility for extracting frames from video files.
    
    Features:
    - Multiple extraction methods with automatic fallback
    - Frame quality assessment (brightness, contrast, etc.)
    - Path handling compatibility with WSL/Windows
    - Proper logging and error handling
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        output_width: int = 320,
        output_height: int = 180,
        output_format: str = "jpg",
        output_quality: int = 85,
        ffmpeg_path: str = "ffmpeg",
    ):
        """
        Initialize the frame extractor.
        
        Args:
            output_dir: Directory to save extracted frames (if None, creates a temp dir)
            output_width: Width of output frames in pixels
            output_height: Height of output frames in pixels
            output_format: Format to save frames (jpg, png)
            output_quality: Output quality (0-100) for JPEG format
            ffmpeg_path: Path to the ffmpeg executable
        """
        self.output_width = output_width
        self.output_height = output_height
        self.output_format = output_format.lower()
        self.output_quality = output_quality
        self.ffmpeg_path = ffmpeg_path
        
        # Create output directory if needed
        if output_dir is None:
            self.output_dir = tempfile.mkdtemp(prefix="frame_extractor_")
            logger.info(f"Created temporary directory for frames: {self.output_dir}")
        else:
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Saving frames to: {self.output_dir}")
        
        # Store available extraction methods
        self.extraction_methods = self._get_extraction_methods()
        
    def _get_extraction_methods(self) -> List[Dict[str, Any]]:
        """
        Get a list of available extraction methods to try in order.
        
        Returns:
            List of extraction methods, each with a command template and description
        """
        # Basic extraction methods
        basic_methods = [
            {
                'id': 'primary',
                'name': 'Standard seek before input',
                'description': "Standard method with accurate seeking before input",
                'template': [
                    self.ffmpeg_path,
                    '-y',  # Overwrite output file without asking
                    '-ss', "{timestamp}",  # Seek to position before input
                    '-i', "{input_path}",  # Input file
                    '-vframes', '1',  # Extract just one frame
                    '-q:v', '2',  # High quality
                    '-avoid_negative_ts', '1',  # Handle negative timestamps
                    '-threads', '1',  # Single thread for more reliable seeking
                    '{output_path}'  # Output file
                ],
                'priority': 1
            },
            {
                'id': 'midpoint_seek',
                'name': 'Midpoint seek before input',
                'description': "Seek to midpoint before input",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-ss', "{midpoint}",  # Seek to middle of clip before input
                    '-i', "{input_path}",
                    '-vframes', '1',
                    '-q:v', '2',
                    '{output_path}'
                ],
                'priority': 2
            },
            {
                'id': 'seek_after_input',
                'name': 'Seek after input',
                'description': "Seek after input (faster but less accurate)",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-ss', "{timestamp}",  # Seek after input
                    '-vframes', '1',
                    '-q:v', '2',
                    '{output_path}'
                ],
                'priority': 3
            },
            {
                'id': 'one_third_point',
                'name': 'One-third point seek',
                'description': "Seek to 1/3 of clip duration after input",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-ss', "{one_third}",  # Seek to 1/3 point
                    '-vframes', '1',
                    '-q:v', '2',
                    '{output_path}'
                ],
                'priority': 4
            },
            {
                'id': 'two_thirds_point',
                'name': 'Two-thirds point seek',
                'description': "Seek to 2/3 of clip duration after input",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-ss', "{two_thirds}",  # Seek to 2/3 point
                    '-vframes', '1',
                    '-q:v', '2',
                    '{output_path}'
                ],
                'priority': 5
            },
            {
                'id': 'near_end',
                'name': 'Near end seek',
                'description': "Seek to near end of clip after input",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-ss', "{near_end}",  # Seek to 90% of clip
                    '-vframes', '1',
                    '-q:v', '2',
                    '{output_path}'
                ],
                'priority': 6
            },
            {
                'id': 'first_frame',
                'name': 'First frame',
                'description': "Extract first frame (most reliable)",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-vframes', '1',
                    '-q:v', '2',
                    '{output_path}'
                ],
                'priority': 7
            }
        ]
        
        # Advanced extraction methods
        advanced_methods = [
            {
                'id': 'fast_seek',
                'name': 'Fast seek (not accurate)',
                'description': "Fast seek without accuracy",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-noaccurate_seek',
                    '-ss', "{timestamp}",
                    '-i', "{input_path}",
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 8
            },
            {
                'id': 'select_filter',
                'name': 'Select filter at midpoint',
                'description': "Select filter at midpoint",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-ss', "{midpoint}",
                    '-vf', 'select=eq(n\\,0)',
                    '-q:v', '2',
                    '{output_path}'
                ],
                'priority': 9
            },
            {
                'id': 'force_fps',
                'name': 'Force 30fps with seek',
                'description': "Force 30fps with seek",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-r', '30',  # Force 30fps
                    '-ss', "{timestamp}",
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 10
            },
            {
                'id': 'keyframes_only',
                'name': 'Keyframes only at midpoint',
                'description': "Keyframes only at midpoint",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-skip_frame', 'nokey',  # Only process keyframes
                    '-i', "{input_path}",
                    '-ss', "{midpoint}",
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 11
            },
            {
                'id': 'error_concealment',
                'name': 'Error concealment first frame',
                'description': "Error concealment with first frame",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-err_detect', 'ignore_err',
                    '-i', "{input_path}",
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 12
            },
            {
                'id': 'i_frame_selection',
                'name': 'I-frame selection only',
                'description': "I-frame selection only",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-vf', 'select=eq(pict_type\\,I)',  # Only select I-frames
                    '-vsync', 'vfr',  # Variable frame rate
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 13
            },
            {
                'id': 'hardware_decoder',
                'name': 'Hardware decoder attempt',
                'description': "Hardware decoder attempt",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-c:v', 'h264_cuvid',  # Try hardware decoding if available
                    '-i', "{input_path}",
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 14
            },
            {
                'id': 'scene_change',
                'name': 'Scene change detection',
                'description': "Scene change detection",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-vf', 'select=gt(scene\\,0.5)',  # Select frames with scene change
                    '-vsync', 'vfr',
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 15
            }
        ]
        
        # Combine all methods
        return basic_methods + advanced_methods
    
    def _get_format_specific_methods(self, file_ext: str) -> List[Dict[str, Any]]:
        """
        Get extraction methods specific to a file format.
        
        Args:
            file_ext: The file extension (e.g., '.mp4', '.mov')
            
        Returns:
            List of format-specific extraction methods
        """
        # Format-specific methods to try
        format_methods = []
        
        if file_ext in ['.mp4', '.mov', '.m4v']:
            # MP4/MOV specific method
            format_methods.append({
                'id': 'yuv420p_format',
                'name': 'Force YUV420P format',
                'description': "Force yuv420p format",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-vf', 'format=yuv420p',  # Force yuv420p format
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 16
            })
        elif file_ext in ['.avi', '.wmv']:
            # AVI/WMV specific method
            format_methods.append({
                'id': 'png_codec',
                'name': 'PNG codec for lossless',
                'description': "PNG codec for lossless extraction",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-codec:v', 'png',  # Use PNG codec for lossless frame
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 16
            })
        elif file_ext in ['.mkv', '.webm']:
            # MKV/WebM specific method
            format_methods.append({
                'id': 'force_first_stream',
                'name': 'Force first video stream',
                'description': "Force first video stream",
                'template': [
                    self.ffmpeg_path,
                    '-y',
                    '-i', "{input_path}",
                    '-map', '0:v:0',  # Force first video stream
                    '-vframes', '1',
                    '{output_path}'
                ],
                'priority': 16
            })
        
        return format_methods
    
    def extract_frame(
        self, 
        video_path: str, 
        timestamp: float,
        frame_id: str = "frame",
        duration: Optional[float] = None,
        wsl_path_prefix: Optional[str] = None,
        method_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract a frame from a video at the specified timestamp.
        
        Args:
            video_path: Path to the video file
            timestamp: Timestamp in seconds to extract the frame
            frame_id: Unique identifier for the frame, used in output filename
            duration: Optional duration of clip (for percentage-based methods)
            wsl_path_prefix: Optional WSL path prefix for Windows paths
            method_filter: Optional list of method IDs to try (None = try all)
            
        Returns:
            Dictionary with extraction results including:
            - frame_path: Path to extracted frame
            - success: Whether extraction was successful
            - method_used: The extraction method that worked
            - quality_info: Information about frame quality
        """
        # Try to convert the path to the current OS format
        resolved_path, exists = resolve_media_path(
            video_path, 
            possible_mount_points=get_available_wsl_mounts(),
            wsl_path_prefix=wsl_path_prefix
        )
        
        if not exists:
            logger.warning(f"Video file not found: {video_path} (tried: {resolved_path})")
            return {
                'frame_id': frame_id,
                'frame_path': None,
                'original_path': video_path,
                'resolved_path': resolved_path,
                'error': 'File not found',
                'method_used': None,
                'success': False,
                'quality_info': None
            }
        
        try:
            # Calculate useful timestamps if duration is provided
            timestamps = {
                'timestamp': timestamp,
                'midpoint': timestamp + (duration / 2) if duration else timestamp,
                'one_third': timestamp + (duration / 3) if duration else timestamp,
                'two_thirds': timestamp + (2 * duration / 3) if duration else timestamp,
                'near_end': timestamp + (duration * 0.9) if duration else timestamp
            }
            
            # Normalize resolved path to avoid double slashes
            safe_path = resolved_path
            while '//' in safe_path:
                safe_path = safe_path.replace('//', '/')
            
            # Create filename based on frame ID
            file_stem = Path(safe_path).stem
            file_ext = Path(safe_path).suffix.lower()
            frame_filename = f"{file_stem}_{frame_id}.{self.output_format}"
            frame_path = os.path.join(self.output_dir, frame_filename)
            
            # Get format-specific methods to try
            format_methods = self._get_format_specific_methods(file_ext)
            
            # Combine all methods
            all_methods = self.extraction_methods + format_methods
            
            # Sort methods by priority
            all_methods.sort(key=lambda x: x['priority'])
            
            # Filter methods if requested
            if method_filter:
                all_methods = [m for m in all_methods if m['id'] in method_filter]
            
            # Create a secure temporary file for the extracted frame
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_frame_path = temp_file.name
            temp_file.close()  # Close the file to avoid permission issues
            
            try:
                # Try each method until one works
                success = False
                used_method = None
                
                for method in all_methods:
                    try:
                        logger.info(f"Trying extraction method '{method['id']}': {method['description']}")
                        
                        # Fill in the command template
                        cmd = [
                            part.format(
                                input_path=safe_path,
                                output_path=temp_frame_path,
                                **timestamps
                            ) if isinstance(part, str) else part
                            for part in method['template']
                        ]
                        
                        # Add a short timeout to avoid hanging on problematic files
                        process = subprocess.run(
                            cmd, 
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=20  # 20-second timeout to avoid hanging
                        )
                        
                        # Check if the file exists and has content
                        if os.path.exists(temp_frame_path) and os.path.getsize(temp_frame_path) > 0:
                            # Try to open it with PIL to confirm it's a valid image
                            img = Image.open(temp_frame_path)
                            img.verify()  # Verify it's a valid image
                            img.close()
                            
                            # Open it again (verify closed the file)
                            img = Image.open(temp_frame_path)
                            img.load()  # Load the image data
                            
                            # Extract quality information
                            quality_info = self._assess_frame_quality(img)
                            
                            # Resize the image
                            img = img.resize((self.output_width, self.output_height), Image.LANCZOS)
                            
                            # Save the frame
                            if self.output_format in ["jpg", "jpeg"]:
                                img.save(frame_path, "JPEG", quality=self.output_quality)
                            else:
                                img.save(frame_path, "PNG")
                            
                            success = True
                            used_method = method['id']
                            break
                            
                    except subprocess.CalledProcessError as e:
                        stderr = e.stderr.decode('utf-8', errors='ignore')
                        # Log only the first 200 chars of stderr to keep logs manageable
                        logger.warning(f"Method '{method['id']}' failed: {stderr[:200]}{'...' if len(stderr) > 200 else ''}")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Method '{method['id']}' timed out after 20 seconds")
                    except Exception as e:
                        logger.warning(f"Method '{method['id']}' failed with error: {str(e)}")
                
                # Clean up temporary file
                try:
                    if os.path.exists(temp_frame_path):
                        os.unlink(temp_frame_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file {temp_frame_path}: {cleanup_error}")
                
                if success:
                    return {
                        'frame_id': frame_id,
                        'frame_path': frame_path,
                        'original_path': video_path,
                        'resolved_path': resolved_path,
                        'timestamp': timestamp,
                        'method_used': used_method,
                        'success': True,
                        'quality_info': quality_info
                    }
                else:
                    # Create a dummy image as a last resort
                    try:
                        dummy_img = Image.new('RGB', (self.output_width, self.output_height), color=(50, 50, 50))
                        
                        # Draw some text on it if PIL.ImageDraw is available
                        try:
                            from PIL import ImageDraw, ImageFont
                            draw = ImageDraw.Draw(dummy_img)
                            
                            # Try to get a font, fallback to default if needed
                            try:
                                font = ImageFont.truetype("Arial", 20)
                            except:
                                font = None
                                
                            # Draw text with frame info
                            draw.text((10, 10), f"Frame {frame_id}", fill=(200, 200, 200), font=font)
                            draw.text((10, 40), "Frame extraction failed", fill=(255, 100, 100), font=font)
                            
                        except:
                            # If text drawing fails, just use the colored background
                            pass
                        
                        # Save the dummy frame
                        if self.output_format in ["jpg", "jpeg"]:
                            dummy_img.save(frame_path, "JPEG", quality=self.output_quality)
                        else:
                            dummy_img.save(frame_path, "PNG")
                        
                        return {
                            'frame_id': frame_id,
                            'frame_path': frame_path,
                            'original_path': video_path,
                            'resolved_path': resolved_path,
                            'timestamp': timestamp,
                            'method_used': 'dummy',
                            'success': False,
                            'quality_info': {
                                'quality': 'poor',
                                'brightness': 0,
                                'contrast': 0,
                                'is_black': False,
                                'is_dummy': True
                            },
                            'error': 'All extraction methods failed'
                        }
                    except Exception as dummy_error:
                        logger.error(f"Failed to create dummy image: {dummy_error}")
                        return {
                            'frame_id': frame_id,
                            'frame_path': None,
                            'original_path': video_path,
                            'resolved_path': resolved_path,
                            'error': 'All extraction methods failed',
                            'method_used': None,
                            'success': False,
                            'quality_info': None
                        }
                    
            except Exception as e:
                # Clean up temporary file if it exists
                try:
                    if os.path.exists(temp_frame_path):
                        os.unlink(temp_frame_path)
                except:
                    pass
                
                # Re-raise the exception
                raise e
                
        except Exception as e:
            logger.error(f"Error extracting frame from {resolved_path} at {timestamp}s: {e}")
            return {
                'frame_id': frame_id,
                'frame_path': None,
                'original_path': video_path,
                'resolved_path': resolved_path,
                'error': str(e),
                'method_used': None,
                'success': False,
                'quality_info': None
            }
    
    def _assess_frame_quality(self, img: Image.Image) -> Dict[str, Any]:
        """
        Assess the quality of an extracted frame.
        
        Args:
            img: PIL Image to analyze
            
        Returns:
            Dictionary with quality assessment information
        """
        # Set default quality values
        quality_info = {
            'quality': 'unknown',  # high, medium, low, poor
            'brightness': 0,
            'contrast': 0,
            'is_black': False,
            'is_dummy': False
        }
        
        try:
            # Convert to RGB to standardize analysis
            if img.mode != 'RGB':
                img_rgb = img.convert('RGB')
            else:
                img_rgb = img
                
            # Get image statistics
            stat = ImageStat.Stat(img_rgb)
            
            # Calculate average brightness (0-255)
            avg_brightness = sum(stat.mean) / 3
            quality_info['brightness'] = avg_brightness
            
            # Calculate contrast (standard deviation)
            avg_std = sum(stat.stddev) / 3
            quality_info['contrast'] = avg_std
            
            # Define thresholds
            dark_threshold = 10  # Very low brightness
            low_brightness_threshold = 30  # Low brightness
            low_contrast_threshold = 20  # Low contrast/detail
            
            # Determine quality based on thresholds
            if avg_brightness < dark_threshold:
                quality_info['is_black'] = True
                quality_info['quality'] = 'poor'
                logger.warning(f"Extracted frame appears to be black (brightness: {avg_brightness:.2f})")
            elif avg_brightness < low_brightness_threshold:
                quality_info['quality'] = 'low'
                logger.warning(f"Extracted frame has low brightness (brightness: {avg_brightness:.2f})")
            elif avg_std < low_contrast_threshold:
                quality_info['quality'] = 'low'
                logger.warning(f"Extracted frame has low contrast (std dev: {avg_std:.2f})")
            else:
                quality_info['quality'] = 'high'
        
        except Exception as e:
            logger.warning(f"Error assessing frame quality: {e}")
        
        return quality_info
    
    def extract_multiple_frames(
        self, 
        video_path: str,
        timestamps: List[float],
        frame_ids: Optional[List[str]] = None,
        duration: Optional[float] = None,
        wsl_path_prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract multiple frames from a video at specified timestamps.
        
        Args:
            video_path: Path to the video file
            timestamps: List of timestamps in seconds
            frame_ids: Optional list of frame IDs (if None, will use sequential numbers)
            duration: Optional duration of clip
            wsl_path_prefix: Optional WSL path prefix for Windows paths
            
        Returns:
            List of dictionaries with extraction results for each frame
        """
        results = []
        
        # Generate frame IDs if not provided
        if frame_ids is None:
            frame_ids = [f"frame_{i:04d}" for i in range(len(timestamps))]
        
        # Extract each frame
        for i, timestamp in enumerate(timestamps):
            frame_id = frame_ids[i] if i < len(frame_ids) else f"frame_{i:04d}"
            result = self.extract_frame(
                video_path=video_path,
                timestamp=timestamp,
                frame_id=frame_id,
                duration=duration,
                wsl_path_prefix=wsl_path_prefix
            )
            results.append(result)
        
        return results
    
    def get_available_methods(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available extraction methods.
        
        Returns:
            List of dictionaries with method information
        """
        methods = []
        for method in self.extraction_methods:
            methods.append({
                'id': method['id'],
                'name': method['name'],
                'description': method['description'],
                'priority': method['priority']
            })
        return methods
    
    def extract_frame_with_method(
        self, 
        video_path: str, 
        timestamp: float,
        method_id: str,
        frame_id: str = "frame",
        duration: Optional[float] = None,
        wsl_path_prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract a frame using a specific extraction method.
        
        Args:
            video_path: Path to the video file
            timestamp: Timestamp in seconds to extract the frame
            method_id: ID of the extraction method to use
            frame_id: Unique identifier for the frame
            duration: Optional duration of clip
            wsl_path_prefix: Optional WSL path prefix for Windows paths
            
        Returns:
            Dictionary with extraction results
        """
        return self.extract_frame(
            video_path=video_path,
            timestamp=timestamp,
            frame_id=frame_id,
            duration=duration,
            wsl_path_prefix=wsl_path_prefix,
            method_filter=[method_id]
        )
    
    def compare_extraction_methods(
        self,
        video_path: str,
        timestamp: float,
        duration: Optional[float] = None,
        wsl_path_prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare all extraction methods on the same video and timestamp.
        
        Args:
            video_path: Path to the video file
            timestamp: Timestamp in seconds to extract the frame
            duration: Optional duration of clip
            wsl_path_prefix: Optional WSL path prefix for Windows paths
            
        Returns:
            Dictionary with results for each method and overall summary
        """
        methods = self.get_available_methods()
        results = {}
        successful_methods = []
        failed_methods = []
        
        # Try each method
        for method in methods:
            method_id = method['id']
            logger.info(f"Testing extraction method: {method_id}")
            
            result = self.extract_frame_with_method(
                video_path=video_path,
                timestamp=timestamp,
                method_id=method_id,
                frame_id=f"method_{method_id}",
                duration=duration,
                wsl_path_prefix=wsl_path_prefix
            )
            
            results[method_id] = result
            
            if result['success']:
                successful_methods.append(method_id)
            else:
                failed_methods.append(method_id)
        
        # Calculate statistics
        total_methods = len(methods)
        success_count = len(successful_methods)
        success_rate = success_count / total_methods if total_methods > 0 else 0
        
        # Add format-specific methods
        file_ext = Path(video_path).suffix.lower()
        format_methods = self._get_format_specific_methods(file_ext)
        for method in format_methods:
            method_id = method['id']
            logger.info(f"Testing format-specific method: {method_id}")
            
            result = self.extract_frame_with_method(
                video_path=video_path,
                timestamp=timestamp,
                method_id=method_id,
                frame_id=f"method_{method_id}",
                duration=duration,
                wsl_path_prefix=wsl_path_prefix
            )
            
            results[method_id] = result
            
            if result['success']:
                successful_methods.append(method_id)
            else:
                failed_methods.append(method_id)
        
        return {
            'video_path': video_path,
            'timestamp': timestamp,
            'duration': duration,
            'method_results': results,
            'successful_methods': successful_methods,
            'failed_methods': failed_methods,
            'success_count': success_count,
            'total_methods_tried': total_methods,
            'success_rate': success_rate
        }


def extract_frame_from_video(
    video_path: str,
    timestamp: float,
    output_path: Optional[str] = None,
    output_width: int = 320,
    output_height: int = 180,
    output_format: str = "jpg",
    output_quality: int = 85,
    ffmpeg_path: str = "ffmpeg",
    wsl_path_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to extract a single frame from a video.
    
    Args:
        video_path: Path to the video file
        timestamp: Timestamp in seconds to extract the frame
        output_path: Path to save the extracted frame (if None, auto-generates)
        output_width: Width of output frame in pixels
        output_height: Height of output frame in pixels
        output_format: Format to save the frame (jpg, png)
        output_quality: Output quality (0-100) for JPEG format
        ffmpeg_path: Path to the ffmpeg executable
        wsl_path_prefix: Optional WSL path prefix for Windows paths
        
    Returns:
        Dictionary with extraction results
    """
    # Create output directory if needed
    output_dir = None
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    # Create extractor
    extractor = FrameExtractor(
        output_dir=output_dir,
        output_width=output_width,
        output_height=output_height,
        output_format=output_format,
        output_quality=output_quality,
        ffmpeg_path=ffmpeg_path
    )
    
    # Generate a frame ID based on the output path if provided
    frame_id = "frame"
    if output_path:
        frame_id = os.path.splitext(os.path.basename(output_path))[0]
    
    # Extract the frame
    result = extractor.extract_frame(
        video_path=video_path,
        timestamp=timestamp,
        frame_id=frame_id,
        wsl_path_prefix=wsl_path_prefix
    )
    
    # If output_path is specified, move the extracted frame there
    if output_path and result['frame_path'] and os.path.exists(result['frame_path']):
        os.rename(result['frame_path'], output_path)
        result['frame_path'] = output_path
    
    return result
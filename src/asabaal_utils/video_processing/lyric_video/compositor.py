"""Video composition engine with GPU/CPU adaptive rendering."""

import numpy as np
import cv2
from typing import Optional, Tuple, List, Union
from pathlib import Path
import logging
from dataclasses import dataclass
from queue import Queue
import threading

from .hardware_detection import HardwareDetector, GPUType

logger = logging.getLogger(__name__)


@dataclass
class CompositeLayer:
    """A single layer in the composite."""
    image: np.ndarray
    position: Tuple[int, int] = (0, 0)
    opacity: float = 1.0
    blend_mode: str = "normal"


class FrameBufferManager:
    """Manage reusable frame buffers for memory efficiency."""
    
    def __init__(self, buffer_size: int = 10):
        self.buffer_size = buffer_size
        self.frame_pool = Queue(maxsize=buffer_size)
        self.resolution: Optional[Tuple[int, int]] = None
        
    def setup_buffers(self, resolution: Tuple[int, int], channels: int = 3):
        """Initialize reusable frame buffers."""
        self.resolution = resolution
        height, width = resolution
        
        # Pre-allocate frame buffers
        for _ in range(self.buffer_size):
            buffer = np.zeros((height, width, channels), dtype=np.uint8)
            self.frame_pool.put(buffer)
            
        logger.info(f"Initialized {self.buffer_size} frame buffers at {width}x{height}")
        
    def get_frame_buffer(self) -> np.ndarray:
        """Get a reusable frame buffer."""
        if self.frame_pool.empty():
            # Create new buffer if pool is empty
            height, width = self.resolution
            return np.zeros((height, width, 3), dtype=np.uint8)
        return self.frame_pool.get()
        
    def return_frame_buffer(self, frame: np.ndarray):
        """Return frame buffer to pool."""
        if not self.frame_pool.full():
            # Clear the buffer before returning
            frame.fill(0)
            self.frame_pool.put(frame)


class VideoCompositor:
    """GPU/CPU adaptive video composition engine."""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080), 
                 fps: float = 30.0, gpu_mode: Optional[bool] = None):
        """Initialize video compositor.
        
        Args:
            resolution: Output resolution (width, height)
            fps: Output frame rate
            gpu_mode: Force GPU mode (None for auto-detect)
        """
        self.resolution = resolution
        self.fps = fps
        self.frame_time = 1.0 / fps
        
        # Hardware detection
        self.hardware = HardwareDetector()
        gpu_info = self.hardware.detect_gpu()
        
        if gpu_mode is None:
            self.gpu_accelerated = gpu_info and gpu_info.gpu_type != GPUType.NONE
        else:
            self.gpu_accelerated = gpu_mode
            
        if self.gpu_accelerated and gpu_info.gpu_type == GPUType.NONE:
            logger.warning("GPU mode requested but no GPU detected, falling back to CPU")
            self.gpu_accelerated = False
            
        # Frame buffer management
        self.buffer_manager = FrameBufferManager()
        self.buffer_manager.setup_buffers(resolution[::-1], channels=3)  # OpenCV uses (height, width), BGR
        
        # Background video handling
        self.background_video: Optional[cv2.VideoCapture] = None
        self.background_frame_cache: Optional[np.ndarray] = None
        self.background_clips: List[Dict] = []  # List of {path, capture, info}
        self.current_clip_index: int = 0
        self.last_beat_time: float = 0.0
        
        self._setup_rendering_context()
        
    def _setup_rendering_context(self):
        """Initialize rendering context based on available hardware."""
        if self.gpu_accelerated:
            try:
                # Try to enable OpenCV GPU support
                if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                    cv2.cuda.setDevice(0)
                    logger.info("CUDA-accelerated OpenCV enabled")
                else:
                    logger.info("OpenCV CUDA support not available")
                    self.gpu_accelerated = False
            except AttributeError:
                logger.info("OpenCV not compiled with CUDA support")
                self.gpu_accelerated = False
        else:
            logger.info("Using CPU-based rendering")
            
    def load_background_video(self, video_path: Union[str, Path]):
        """Load background video for compositing.
        
        Args:
            video_path: Path to background video file
        """
        video_path = str(video_path)
        self.background_video = cv2.VideoCapture(video_path)
        
        if not self.background_video.isOpened():
            raise ValueError(f"Failed to open background video: {video_path}")
            
        # Get video properties
        width = int(self.background_video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.background_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.background_video.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"Loaded background video: {width}x{height} @ {fps}fps")
        
    def load_background_clips_from_directory(self, clips_dir: Union[str, Path], 
                                           supported_formats: List[str] = None):
        """Load multiple background clips from a directory for beat-based switching.
        
        Args:
            clips_dir: Directory containing background video clips
            supported_formats: List of supported video formats (default: mp4, mov, avi)
        """
        if supported_formats is None:
            supported_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            
        clips_dir = Path(clips_dir)
        if not clips_dir.exists():
            raise ValueError(f"Background clips directory not found: {clips_dir}")
            
        # Find all video files
        video_files = []
        for fmt in supported_formats:
            video_files.extend(clips_dir.glob(f"*{fmt}"))
            video_files.extend(clips_dir.glob(f"*{fmt.upper()}"))
            
        if not video_files:
            raise ValueError(f"No video files found in {clips_dir}")
            
        logger.info(f"Found {len(video_files)} background clips")
        
        # Load clip information
        for video_file in sorted(video_files):
            try:
                cap = cv2.VideoCapture(str(video_file))
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = frame_count / fps if fps > 0 else 0
                    
                    clip_info = {
                        'path': str(video_file),
                        'name': video_file.stem,
                        'capture': cap,
                        'width': width,
                        'height': height,
                        'fps': fps,
                        'duration': duration,
                        'frame_count': frame_count,
                        'current_frame': 0
                    }
                    
                    self.background_clips.append(clip_info)
                    logger.info(f"Loaded clip: {video_file.name} ({duration:.1f}s, {width}x{height})")
                else:
                    logger.warning(f"Could not open video file: {video_file}")
                    
            except Exception as e:
                logger.warning(f"Error loading {video_file}: {e}")
                
        if not self.background_clips:
            raise ValueError("No valid background clips could be loaded")
            
        logger.info(f"Successfully loaded {len(self.background_clips)} background clips")
        
    def get_background_frame(self, timestamp: float, beat_times: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """Get background frame at specific timestamp with beat-based clip switching.
        
        Args:
            timestamp: Time in seconds
            beat_times: Array of beat times for smart clip switching
            
        Returns:
            Background frame or None if no background loaded
        """
        # Use multiple clips if available
        if self.background_clips:
            return self._get_frame_from_clips(timestamp, beat_times)
        elif self.background_video:
            return self._get_frame_from_single_video(timestamp)
        else:
            return None
            
    def _get_frame_from_clips(self, timestamp: float, beat_times: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """Get frame from multiple clips with beat-based switching."""
        if not self.background_clips:
            return None
            
        # Check if we should switch clips on a beat
        if beat_times is not None:
            # Find if we're near a beat
            beat_mask = np.abs(beat_times - timestamp) < 0.1  # Within 100ms of a beat
            if np.any(beat_mask) and timestamp - self.last_beat_time > 2.0:  # Don't switch too frequently
                # Switch to next clip on beat
                self.current_clip_index = (self.current_clip_index + 1) % len(self.background_clips)
                self.last_beat_time = timestamp
                logger.debug(f"Switched to clip {self.current_clip_index} on beat at {timestamp:.1f}s")
                
        # Get current clip
        current_clip = self.background_clips[self.current_clip_index]
        cap = current_clip['capture']
        
        # Calculate relative time within this clip
        # Loop the clip if we've exceeded its duration
        clip_time = timestamp % current_clip['duration']
        frame_number = int(clip_time * current_clip['fps'])
        
        # Seek to frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read frame
        ret, frame = cap.read()
        if not ret:
            # Try from beginning of clip
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            
        if ret:
            # Resize to output resolution if needed
            if frame.shape[:2][::-1] != self.resolution:
                frame = cv2.resize(frame, self.resolution)
            return frame
            
        return None
        
    def _get_frame_from_single_video(self, timestamp: float) -> Optional[np.ndarray]:
        """Get frame from single background video (original behavior)."""
        # Calculate frame number
        frame_number = int(timestamp * self.background_video.get(cv2.CAP_PROP_FPS))
        
        # Seek to frame
        self.background_video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read frame
        ret, frame = self.background_video.read()
        if not ret:
            # Try to loop video
            self.background_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.background_video.read()
            
        if ret:
            # Resize to output resolution if needed
            if frame.shape[:2][::-1] != self.resolution:
                frame = cv2.resize(frame, self.resolution)
            return frame
            
        return None
        
    def composite_frame(self, background: Optional[np.ndarray], 
                       layers: List[CompositeLayer]) -> np.ndarray:
        """Composite multiple layers into a single frame.
        
        Args:
            background: Background image or None for black
            layers: List of layers to composite
            
        Returns:
            Composited frame
        """
        # Get frame buffer
        output = self.buffer_manager.get_frame_buffer()
        
        # Set background
        if background is not None:
            output[:] = background
        else:
            output.fill(0)  # Black background
            
        # Composite layers
        for layer in layers:
            self._blend_layer(output, layer)
            
        return output
        
    def _blend_layer(self, base: np.ndarray, layer: CompositeLayer):
        """Blend a layer onto the base image.
        
        Args:
            base: Base image to blend onto
            layer: Layer to blend
        """
        if layer.opacity <= 0:
            return
            
        x, y = layer.position
        h, w = layer.image.shape[:2]
        base_h, base_w = base.shape[:2]
        
        # Calculate valid region
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(base_w, x + w)
        y2 = min(base_h, y + h)
        
        if x2 <= x1 or y2 <= y1:
            return  # Layer is completely outside
            
        # Get regions
        base_region = base[y1:y2, x1:x2]
        layer_region = layer.image[y1-y:y2-y, x1-x:x2-x]
        
        # Handle channel mismatch (RGBA layer on RGB base)
        if layer_region.shape[2] == 4 and base_region.shape[2] == 3:
            # Extract RGB and alpha from layer
            layer_rgb = layer_region[:, :, :3]
            layer_alpha = layer_region[:, :, 3:4] / 255.0
            
            if layer.opacity >= 1.0:
                # Use layer's built-in alpha
                alpha = layer_alpha
            else:
                # Combine layer opacity with layer alpha
                alpha = layer_alpha * layer.opacity
                
            # Alpha composite: result = alpha * foreground + (1-alpha) * background
            base_region[:] = (alpha * layer_rgb + (1 - alpha) * base_region).astype(np.uint8)
            
        elif layer_region.shape[2] == base_region.shape[2]:
            # Same number of channels - normal blending
            if layer.blend_mode == "normal":
                if layer.opacity >= 1.0:
                    base_region[:] = layer_region
                else:
                    # Alpha blending
                    alpha = layer.opacity
                    base_region[:] = (alpha * layer_region + (1 - alpha) * base_region).astype(np.uint8)
        else:
            logger.warning(f"Channel mismatch: layer has {layer_region.shape[2]} channels, base has {base_region.shape[2]} channels")
            
        # Handle other blend modes (only for same-channel cases)
        if layer_region.shape[2] == base_region.shape[2] and layer.blend_mode != "normal":
            if layer.blend_mode == "add":
                # Additive blending
                result = base_region.astype(np.float32) + layer_region * layer.opacity
                base_region[:] = np.clip(result, 0, 255).astype(np.uint8)
            elif layer.blend_mode == "multiply":
                # Multiply blending
                result = (base_region.astype(np.float32) * layer_region / 255.0) * layer.opacity
                base_region[:] = result.astype(np.uint8)
            
    def apply_audio_reactive_effects(self, frame: np.ndarray, 
                                   audio_features: dict) -> np.ndarray:
        """Apply audio-reactive visual effects to frame.
        
        Args:
            frame: Input frame
            audio_features: Dictionary of audio features at current time
            
        Returns:
            Frame with effects applied
        """
        # Create a copy to avoid modifying the original
        output = frame.copy()
        
        # Energy-based brightness adjustment
        if 'rms_energy' in audio_features:
            energy = audio_features['rms_energy']
            if energy > 0.7:  # High energy threshold
                # Add glow effect
                if self.gpu_accelerated:
                    output = self._gpu_glow_effect(output, intensity=energy)
                else:
                    output = self._cpu_glow_effect(output, intensity=energy)
                    
        # Beat pulse effect
        if audio_features.get('on_beat', False):
            # Quick brightness pulse
            output = cv2.convertScaleAbs(output, alpha=1.2, beta=10)
            
        # Spectral color shift
        if 'spectral_centroid' in audio_features:
            centroid = audio_features['spectral_centroid']
            # Shift hue based on spectral centroid
            output = self._apply_color_shift(output, centroid)
            
        return output
        
    def _cpu_glow_effect(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """CPU-based glow effect."""
        # Create glow by blurring bright areas
        bright_mask = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 
                                   200, 255, cv2.THRESH_BINARY)[1]
        
        # Blur the bright areas
        glow = cv2.GaussianBlur(image, (21, 21), 0)
        
        # Apply glow only to bright areas
        glow_mask = cv2.cvtColor(bright_mask, cv2.COLOR_GRAY2BGR) / 255.0
        result = image + (glow * glow_mask * intensity * 0.5).astype(np.uint8)
        
        return np.clip(result, 0, 255).astype(np.uint8)
        
    def _gpu_glow_effect(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """GPU-accelerated glow effect using CUDA."""
        try:
            # Upload to GPU
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(image)
            
            # Convert to grayscale for threshold
            gpu_gray = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2GRAY)
            
            # Threshold for bright areas
            _, gpu_mask = cv2.cuda.threshold(gpu_gray, 200, 255, cv2.THRESH_BINARY)
            
            # Blur for glow
            gpu_blur = cv2.cuda.GaussianBlur(gpu_image, (21, 21), 0)
            
            # Download results
            mask = gpu_mask.download()
            blur = gpu_blur.download()
            
            # Composite (CPU for now, could be optimized)
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            result = image + (blur * mask_3ch * intensity * 0.5).astype(np.uint8)
            
            return np.clip(result, 0, 255).astype(np.uint8)
            
        except Exception as e:
            logger.warning(f"GPU glow effect failed, falling back to CPU: {e}")
            return self._cpu_glow_effect(image, intensity)
            
    def _apply_color_shift(self, image: np.ndarray, shift_amount: float) -> np.ndarray:
        """Apply color shift based on spectral content."""
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Shift hue
        hsv[:, :, 0] = (hsv[:, :, 0] + shift_amount * 30) % 180
        
        # Convert back
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
    def release(self):
        """Release resources."""
        if self.background_video:
            self.background_video.release()
            self.background_video = None
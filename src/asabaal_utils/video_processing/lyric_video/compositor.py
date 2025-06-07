"""Video composition engine with GPU/CPU adaptive rendering."""

import numpy as np
import cv2
from typing import Optional, Tuple, List, Union, Dict
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
        
        # Motion detection
        self.previous_frame: Optional[np.ndarray] = None
        self.motion_vectors: List[Tuple[float, float]] = []
        self.motion_history: List[float] = []
        
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
        """Apply dramatic audio-reactive visual effects to frame.
        
        Args:
            frame: Input frame
            audio_features: Dictionary of audio features at current time
            
        Returns:
            Frame with bold effects applied
        """
        # Create a copy to avoid modifying the original
        output = frame.copy()
        
        # DRAMATIC energy-based effects
        if 'rms_energy' in audio_features:
            energy = audio_features['rms_energy']
            
            # Multi-layered energy effects
            if energy > 0.8:  # Very high energy - intense effects
                # Intense multi-color glow
                output = self._apply_intense_energy_burst(output, energy)
                # Chromatic aberration for impact
                output = self._apply_chromatic_aberration(output, int(energy * 8))
                # Color explosion
                output = self._apply_energy_color_explosion(output, energy)
                
            elif energy > 0.6:  # High energy
                # Enhanced glow with color shifting
                if self.gpu_accelerated:
                    output = self._gpu_glow_effect(output, intensity=energy * 1.5)
                else:
                    output = self._cpu_glow_effect(output, intensity=energy * 1.5)
                # Dynamic color shift
                output = self._apply_energy_color_shift(output, energy)
                
            elif energy > 0.4:  # Medium energy
                # Subtle glow and brightness boost
                if self.gpu_accelerated:
                    output = self._gpu_glow_effect(output, intensity=energy)
                else:
                    output = self._cpu_glow_effect(output, intensity=energy)
                    
        # DRAMATIC beat effects
        if audio_features.get('on_beat', False):
            # Multi-effect beat impact
            output = self._apply_beat_impact_combo(output, audio_features)
            
        # Enhanced spectral effects
        if 'spectral_centroid' in audio_features:
            centroid = audio_features['spectral_centroid']
            # More dramatic spectral-based effects
            output = self._apply_spectral_effects(output, centroid, audio_features.get('rms_energy', 0))
            
        # Motion-based warping
        if 'motion_magnitude' in audio_features:
            motion_mag = audio_features.get('motion_magnitude', 0)
            if motion_mag > 3.0:
                output = self._apply_motion_warp(output, motion_mag, audio_features)
                
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
        
    def detect_motion(self, frame: np.ndarray) -> Tuple[float, Tuple[float, float]]:
        """Detect motion in background video frame.
        
        Args:
            frame: Current background frame
            
        Returns:
            Tuple of (motion_magnitude, motion_vector)
        """
        if self.previous_frame is None:
            self.previous_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return 0.0, (0.0, 0.0)
            
        # Convert to grayscale
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate optical flow using Lucas-Kanade method
        try:
            # Detect features in previous frame
            corners = cv2.goodFeaturesToTrack(
                self.previous_frame,
                maxCorners=100,
                qualityLevel=0.01,
                minDistance=10,
                blockSize=3
            )
            
            if corners is not None and len(corners) > 0:
                # Calculate optical flow
                flow, status, error = cv2.calcOpticalFlowPyrLK(
                    self.previous_frame,
                    current_gray,
                    corners,
                    None
                )
                
                # Filter good points
                good_new = flow[status == 1]
                good_old = corners[status == 1]
                
                if len(good_new) > 0:
                    # Calculate average motion vector
                    motion_vectors = good_new - good_old
                    avg_motion = np.mean(motion_vectors, axis=0)
                    motion_magnitude = np.linalg.norm(avg_motion)
                    
                    # Update motion history
                    self.motion_vectors.append((avg_motion[0], avg_motion[1]))
                    self.motion_history.append(motion_magnitude)
                    
                    # Keep only recent history (last 10 frames)
                    if len(self.motion_history) > 10:
                        self.motion_history.pop(0)
                        self.motion_vectors.pop(0)
                    
                    self.previous_frame = current_gray.copy()
                    return motion_magnitude, (avg_motion[0], avg_motion[1])
                    
        except Exception as e:
            logger.debug(f"Motion detection error: {e}")
            
        self.previous_frame = current_gray.copy()
        return 0.0, (0.0, 0.0)
        
    def get_motion_features(self) -> Dict:
        """Get motion-based features for text effects.
        
        Returns:
            Dictionary with motion features
        """
        if not self.motion_history:
            return {
                'motion_magnitude': 0.0,
                'motion_vector': (0.0, 0.0),
                'motion_smoothness': 1.0,
                'motion_direction': 0.0
            }
            
        # Calculate motion features
        avg_magnitude = np.mean(self.motion_history)
        recent_vector = self.motion_vectors[-1] if self.motion_vectors else (0.0, 0.0)
        
        # Calculate motion smoothness (lower variance = smoother)
        motion_variance = np.var(self.motion_history) if len(self.motion_history) > 1 else 0.0
        smoothness = max(0.0, 1.0 - motion_variance / 10.0)  # Normalize
        
        # Calculate motion direction
        direction = np.arctan2(recent_vector[1], recent_vector[0]) if recent_vector != (0.0, 0.0) else 0.0
        
        return {
            'motion_magnitude': float(avg_magnitude),
            'motion_vector': recent_vector,
            'motion_smoothness': float(smoothness),
            'motion_direction': float(direction)
        }
        
    def enhance_background_motion(self, frame: np.ndarray, motion_features: Dict) -> np.ndarray:
        """Enhance background video with motion-based effects.
        
        Args:
            frame: Background video frame
            motion_features: Motion features from get_motion_features()
            
        Returns:
            Enhanced background frame
        """
        if motion_features['motion_magnitude'] < 1.0:
            return frame
            
        enhanced = frame.copy()
        
        # Motion-based color enhancement
        magnitude = motion_features['motion_magnitude']
        if magnitude > 3.0:  # Significant motion
            # Increase saturation and contrast for high motion
            hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] *= 1.2  # Increase saturation
            hsv[:, :, 2] *= 1.1  # Increase brightness
            hsv = np.clip(hsv, 0, 255).astype(np.uint8)
            enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
        # Motion blur for fast movement
        if magnitude > 5.0:
            motion_vector = motion_features['motion_vector']
            kernel_size = min(15, int(magnitude / 2))
            if kernel_size >= 3:
                # Create motion blur kernel
                angle = motion_features['motion_direction']
                kernel = np.zeros((kernel_size, kernel_size))
                center = kernel_size // 2
                
                # Create line kernel based on motion direction
                for i in range(-center, center + 1):
                    x = int(center + i * np.cos(angle))
                    y = int(center + i * np.sin(angle))
                    if 0 <= x < kernel_size and 0 <= y < kernel_size:
                        kernel[y, x] = 1
                        
                if np.sum(kernel) > 0:
                    kernel /= np.sum(kernel)
                    enhanced = cv2.filter2D(enhanced, -1, kernel)
                    
        return enhanced
        
    def _apply_intense_energy_burst(self, image: np.ndarray, energy: float) -> np.ndarray:
        """Apply intense energy burst with multiple layers."""
        h, w = image.shape[:2]
        result = image.copy()
        
        # Create energy layers with different colors
        energy_layer = np.zeros_like(image, dtype=np.float32)
        
        # Radial energy burst from center
        center_x, center_y = w // 2, h // 2
        y_coords, x_coords = np.ogrid[:h, :w]
        distance_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        
        # Create pulsing energy field
        max_distance = np.sqrt(center_x**2 + center_y**2)
        normalized_distance = distance_from_center / max_distance
        
        # Multiple energy rings
        energy_rings = np.sin(normalized_distance * np.pi * 8 * energy) * (1 - normalized_distance)
        energy_rings = np.maximum(0, energy_rings) * energy
        
        # Apply to color channels with different intensities
        energy_layer[:, :, 0] = energy_rings * 255 * 0.8  # Blue
        energy_layer[:, :, 1] = energy_rings * 255 * 0.4  # Green
        energy_layer[:, :, 2] = energy_rings * 255 * 1.0  # Red
        
        # Blur for glow effect
        energy_layer = cv2.GaussianBlur(energy_layer, (15, 15), 0)
        
        # Composite with additive blending
        result = result.astype(np.float32)
        result += energy_layer * 0.6
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
        
    def _apply_chromatic_aberration(self, image: np.ndarray, offset: int) -> np.ndarray:
        """Apply dramatic chromatic aberration effect."""
        if offset < 2:
            return image
            
        result = image.copy()
        h, w = image.shape[:2]
        
        # Create multiple offset layers for stronger effect
        for i in range(1, offset + 1):
            strength = 1.0 - (i / offset) * 0.7  # Diminishing strength
            
            # Red channel - shift right and up
            if i < w and i < h:
                red_shifted = np.zeros_like(result[:, :, 2])
                red_shifted[:-i, i:] = result[i:, :-i, 2]
                result[:, :, 2] = (result[:, :, 2] * (1 - strength) + red_shifted * strength).astype(np.uint8)
                
            # Blue channel - shift left and down  
            if i < w and i < h:
                blue_shifted = np.zeros_like(result[:, :, 0])
                blue_shifted[i:, :-i] = result[:-i, i:, 0]
                result[:, :, 0] = (result[:, :, 0] * (1 - strength) + blue_shifted * strength).astype(np.uint8)
        
        return result
        
    def _apply_energy_color_explosion(self, image: np.ndarray, energy: float) -> np.ndarray:
        """Apply energy-based color explosion effect."""
        # Convert to HSV for hue manipulation
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Create explosive color zones
        h, w = hsv.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Create radial color explosion
        y_coords, x_coords = np.ogrid[:h, :w]
        angles = np.arctan2(y_coords - center_y, x_coords - center_x)
        distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        
        # Color explosion based on angle and energy
        hue_shift = (angles + np.pi) / (2 * np.pi) * 180 * energy
        hue_shift += np.sin(distances * 0.1) * 60 * energy  # Distance-based modulation
        
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + energy * 0.5), 0, 255)  # Boost saturation
        
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
    def _apply_energy_color_shift(self, image: np.ndarray, energy: float) -> np.ndarray:
        """Apply energy-based dynamic color shifting."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Dynamic hue shift based on energy
        hue_shift = energy * 60 * np.sin(energy * np.pi * 4)
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
        
        # Energy-based saturation boost
        saturation_boost = 1.0 + energy * 0.4
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_boost, 0, 255)
        
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
    def _apply_beat_impact_combo(self, image: np.ndarray, audio_features: dict) -> np.ndarray:
        """Apply dramatic beat impact combination effects."""
        result = image.copy()
        energy = audio_features.get('rms_energy', 0.5)
        
        # Quick brightness flash
        flash_intensity = 1.3 + energy * 0.5
        result = cv2.convertScaleAbs(result, alpha=flash_intensity, beta=15)
        
        # Beat-synchronized zoom pulse
        zoom_factor = 1.05 + energy * 0.1
        h, w = result.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, 0, zoom_factor)
        result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        
        # Color saturation pop
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.2 + energy * 0.3), 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        return result
        
    def _apply_spectral_effects(self, image: np.ndarray, centroid: float, energy: float) -> np.ndarray:
        """Apply dramatic spectral-based effects."""
        # More dramatic frequency-based color and distortion effects
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Frequency-based hue mapping (more dramatic)
        if centroid > 0.7:  # High frequencies - cooler colors
            hue_shift = (centroid - 0.5) * 120  # Blue/cyan range
            brightness_boost = 1.1 + energy * 0.2
        elif centroid < 0.3:  # Low frequencies - warmer colors  
            hue_shift = (0.5 - centroid) * 60   # Red/orange range
            brightness_boost = 1.0 + energy * 0.3
        else:  # Mid frequencies - green/yellow
            hue_shift = np.sin(centroid * np.pi * 2) * 30
            brightness_boost = 1.05 + energy * 0.1
            
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * brightness_boost, 0, 255)
        
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        # Add wave distortion for extreme frequencies
        if centroid > 0.8 or centroid < 0.2:
            result = self._apply_frequency_wave_distortion(result, centroid, energy)
            
        return result
        
    def _apply_frequency_wave_distortion(self, image: np.ndarray, centroid: float, energy: float) -> np.ndarray:
        """Apply frequency-based wave distortion."""
        h, w = image.shape[:2]
        amplitude = energy * 15 * abs(centroid - 0.5) * 2  # More extreme for edge frequencies
        frequency = 0.1 + energy * 0.1
        
        x_map = np.zeros((h, w), dtype=np.float32)
        y_map = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                # Frequency-dependent wave direction
                if centroid > 0.6:  # High freq - vertical waves
                    x_map[y, x] = x + amplitude * np.sin(2 * np.pi * y * frequency / h)
                    y_map[y, x] = y
                else:  # Low freq - horizontal waves
                    x_map[y, x] = x
                    y_map[y, x] = y + amplitude * np.sin(2 * np.pi * x * frequency / w)
                    
        return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        
    def _apply_motion_warp(self, image: np.ndarray, motion_magnitude: float, audio_features: dict) -> np.ndarray:
        """Apply motion-based warping effects."""
        h, w = image.shape[:2]
        
        # Motion-direction based distortion
        motion_vector = audio_features.get('motion_vector', (0, 0))
        if motion_magnitude > 5.0:
            # Dramatic motion-based transformation
            motion_angle = np.arctan2(motion_vector[1], motion_vector[0])
            
            # Create motion-based displacement
            x_map = np.zeros((h, w), dtype=np.float32)
            y_map = np.zeros((h, w), dtype=np.float32)
            
            displacement_strength = min(20, motion_magnitude * 2)
            
            for y in range(h):
                for x in range(w):
                    # Motion trail effect
                    trail_x = displacement_strength * np.cos(motion_angle) * np.sin(y * 0.1)
                    trail_y = displacement_strength * np.sin(motion_angle) * np.sin(x * 0.1)
                    
                    x_map[y, x] = x + trail_x
                    y_map[y, x] = y + trail_y
                    
            return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        
        return image
        
    def release(self):
        """Release resources."""
        if self.background_video:
            self.background_video.release()
            self.background_video = None
            
        # Release clip captures
        for clip in self.background_clips:
            if 'capture' in clip and clip['capture']:
                clip['capture'].release()
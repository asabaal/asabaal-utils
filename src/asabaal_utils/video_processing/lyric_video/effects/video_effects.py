"""Video effects for lyric videos."""

from enum import Enum
import numpy as np
import cv2
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EffectType(Enum):
    """Available video effect types."""
    GLOW = "glow"
    SHADOW = "shadow"
    BLUR = "blur"
    PARTICLE = "particle"
    WAVE = "wave"
    SHAKE = "shake"
    ZOOM = "zoom"
    ROTATE = "rotate"


class VideoEffects:
    """Collection of video effects for lyric videos."""
    
    @staticmethod
    def apply_glow(image: np.ndarray, color: Tuple[int, int, int] = (255, 255, 255),
                   radius: int = 10, intensity: float = 0.5) -> np.ndarray:
        """Apply glow effect to image.
        
        Args:
            image: Input image
            color: Glow color (B, G, R)
            radius: Blur radius for glow
            intensity: Glow intensity (0.0 to 1.0)
            
        Returns:
            Image with glow effect
        """
        # Create glow layer
        glow = cv2.GaussianBlur(image, (radius*2+1, radius*2+1), 0)
        
        # Color the glow
        glow_colored = np.zeros_like(glow)
        for i in range(3):
            glow_colored[:, :, i] = (glow[:, :, i] * color[i] / 255.0).astype(np.uint8)
            
        # Blend with original
        result = cv2.addWeighted(image, 1.0, glow_colored, intensity, 0)
        
        return np.clip(result, 0, 255).astype(np.uint8)
        
    @staticmethod
    def apply_shadow(image: np.ndarray, offset: Tuple[int, int] = (5, 5),
                     blur_radius: int = 5, opacity: float = 0.5) -> np.ndarray:
        """Apply drop shadow effect.
        
        Args:
            image: Input image with alpha channel
            offset: Shadow offset (x, y)
            blur_radius: Shadow blur radius
            opacity: Shadow opacity
            
        Returns:
            Image with shadow
        """
        h, w = image.shape[:2]
        
        # Create shadow canvas
        shadow_canvas = np.zeros((h + abs(offset[1]) * 2, w + abs(offset[0]) * 2, 4), dtype=np.uint8)
        
        # Place image on canvas
        y_start = abs(offset[1])
        x_start = abs(offset[0])
        
        # Create shadow (black with alpha from original)
        if image.shape[2] == 4:
            shadow = np.zeros_like(image)
            shadow[:, :, 3] = image[:, :, 3]  # Copy alpha
        else:
            # Create alpha from luminance
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            shadow = np.zeros((h, w, 4), dtype=np.uint8)
            shadow[:, :, 3] = gray
            
        # Place shadow with offset
        shadow_y = y_start + offset[1]
        shadow_x = x_start + offset[0]
        shadow_canvas[shadow_y:shadow_y+h, shadow_x:shadow_x+w] = shadow
        
        # Blur shadow
        shadow_canvas = cv2.GaussianBlur(shadow_canvas, (blur_radius*2+1, blur_radius*2+1), 0)
        
        # Apply opacity
        shadow_canvas[:, :, 3] = (shadow_canvas[:, :, 3] * opacity).astype(np.uint8)
        
        # Place original image on top
        if image.shape[2] == 3:
            image_rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            image_rgba[:, :, 3] = 255
        else:
            image_rgba = image
            
        # Composite
        result = shadow_canvas.copy()
        result[y_start:y_start+h, x_start:x_start+w] = image_rgba
        
        # Crop to original size plus shadow
        crop_h = h + abs(offset[1])
        crop_w = w + abs(offset[0])
        
        return result[:crop_h, :crop_w]
        
    @staticmethod
    def apply_motion_blur(image: np.ndarray, angle: float = 0, strength: int = 15) -> np.ndarray:
        """Apply directional motion blur.
        
        Args:
            image: Input image
            angle: Blur angle in degrees
            strength: Blur strength
            
        Returns:
            Blurred image
        """
        # Create motion blur kernel
        kernel = np.zeros((strength, strength))
        
        # Calculate kernel center
        center = strength // 2
        
        # Create line in kernel
        angle_rad = np.radians(angle)
        for i in range(strength):
            x = int(center + (i - center) * np.cos(angle_rad))
            y = int(center + (i - center) * np.sin(angle_rad))
            if 0 <= x < strength and 0 <= y < strength:
                kernel[y, x] = 1
                
        # Normalize kernel
        kernel = kernel / np.sum(kernel)
        
        # Apply motion blur
        return cv2.filter2D(image, -1, kernel)
        
    @staticmethod
    def apply_zoom_blur(image: np.ndarray, center: Optional[Tuple[int, int]] = None,
                       strength: float = 0.1) -> np.ndarray:
        """Apply radial zoom blur effect.
        
        Args:
            image: Input image
            center: Blur center (defaults to image center)
            strength: Zoom strength
            
        Returns:
            Zoom blurred image
        """
        h, w = image.shape[:2]
        
        if center is None:
            center = (w // 2, h // 2)
            
        # Create zoom transformation
        result = np.zeros_like(image)
        
        # Sample multiple zoom levels
        samples = 10
        for i in range(samples):
            scale = 1.0 + (i / samples) * strength
            
            # Create transformation matrix
            M = cv2.getRotationMatrix2D(center, 0, scale)
            
            # Apply transformation
            zoomed = cv2.warpAffine(image, M, (w, h))
            
            # Accumulate
            result = cv2.addWeighted(result, float(i) / (i + 1), zoomed, 1.0 / (i + 1), 0)
            
        return result
        
    @staticmethod
    def apply_shake(image: np.ndarray, amplitude: int = 5, 
                   direction: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """Apply camera shake effect.
        
        Args:
            image: Input image
            amplitude: Shake amplitude in pixels
            direction: Specific shake direction or None for random
            
        Returns:
            Shaken image
        """
        h, w = image.shape[:2]
        
        if direction is None:
            # Random shake
            dx = np.random.randint(-amplitude, amplitude + 1)
            dy = np.random.randint(-amplitude, amplitude + 1)
        else:
            dx, dy = direction
            
        # Create translation matrix
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        
        # Apply translation
        return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        
    @staticmethod
    def create_particle_overlay(size: Tuple[int, int], num_particles: int = 100,
                              particle_size: int = 3, color: Tuple[int, int, int] = (255, 255, 255),
                              velocity_range: Tuple[float, float] = (1.0, 3.0)) -> np.ndarray:
        """Create particle effect overlay.
        
        Args:
            size: Canvas size (width, height)
            num_particles: Number of particles
            particle_size: Size of each particle
            color: Particle color
            velocity_range: Min and max velocity
            
        Returns:
            Particle overlay with alpha channel
        """
        w, h = size
        overlay = np.zeros((h, w, 4), dtype=np.uint8)
        
        # Generate random particles
        for _ in range(num_particles):
            x = np.random.randint(0, w)
            y = np.random.randint(0, h)
            
            # Draw particle with glow
            cv2.circle(overlay, (x, y), particle_size, (*color, 255), -1)
            
            # Add glow
            for radius in range(particle_size + 1, particle_size + 5):
                alpha = int(255 * (1 - (radius - particle_size) / 4))
                cv2.circle(overlay, (x, y), radius, (*color, alpha), 1)
                
        return overlay
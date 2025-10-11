"""Traditional video editor style motion effects with timeline evolution."""

import numpy as np
import cv2
from typing import Dict, Tuple, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class EffectType(Enum):
    """Traditional video editor effect types."""
    # Transform effects
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    ROTATE_CW = "rotate_cw"
    ROTATE_CCW = "rotate_ccw"
    
    # Scale effects
    SCALE_PULSE = "scale_pulse"
    SCALE_BOUNCE = "scale_bounce"
    SCALE_ELASTIC = "scale_elastic"
    
    # Position effects
    SLIDE_IN_LEFT = "slide_in_left"
    SLIDE_IN_RIGHT = "slide_in_right"
    SLIDE_IN_TOP = "slide_in_top"
    SLIDE_IN_BOTTOM = "slide_in_bottom"
    SLIDE_OUT_LEFT = "slide_out_left"
    SLIDE_OUT_RIGHT = "slide_out_right"
    SLIDE_OUT_TOP = "slide_out_top"
    SLIDE_OUT_BOTTOM = "slide_out_bottom"
    
    # Opacity effects
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    FLASH = "flash"
    STROBE = "strobe"
    
    # Distortion effects
    WAVE_HORIZONTAL = "wave_horizontal"
    WAVE_VERTICAL = "wave_vertical"
    LENS_DISTORTION = "lens_distortion"
    FISHEYE = "fisheye"
    
    # Motion effects
    CAMERA_SHAKE = "camera_shake"
    MOTION_BLUR = "motion_blur"
    ZOOM_BLUR = "zoom_blur"
    RADIAL_BLUR = "radial_blur"
    
    # Color effects
    COLOR_SHIFT = "color_shift"
    SATURATION_PULSE = "saturation_pulse"
    BRIGHTNESS_PULSE = "brightness_pulse"
    CONTRAST_PULSE = "contrast_pulse"
    
    # BOLD NEW EFFECTS
    GLITCH_DIGITAL = "glitch_digital"
    SHATTER_BREAK = "shatter_break"
    LIQUID_WARP = "liquid_warp"
    PORTAL_SWIRL = "portal_swirl"
    MATRIX_RAIN = "matrix_rain"
    NEON_GLOW = "neon_glow"
    HOLOGRAM_FLICKER = "hologram_flicker"
    ENERGY_BURST = "energy_burst"
    FRACTAL_ZOOM = "fractal_zoom"
    MIRROR_KALEIDOSCOPE = "mirror_kaleidoscope"


@dataclass
class EffectKeyframe:
    """A keyframe for effect animation."""
    time: float  # Time in seconds
    value: float  # Effect intensity/value at this time
    easing: str = "linear"  # Easing function: linear, ease_in, ease_out, ease_in_out, bounce, elastic


@dataclass
class MotionEffect:
    """A motion effect with timeline evolution."""
    effect_type: EffectType
    duration: float  # Total duration of effect
    keyframes: List[EffectKeyframe]
    properties: Dict = None  # Additional effect properties
    loop: bool = False
    reverse: bool = False
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class EffectEvolution:
    """Handles effect evolution over time with keyframes and easing."""
    
    @staticmethod
    def ease_in(t: float) -> float:
        """Ease in (slow start)."""
        return t * t
    
    @staticmethod
    def ease_out(t: float) -> float:
        """Ease out (slow end)."""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        """Ease in-out (slow start and end)."""
        if t < 0.5:
            return 2 * t * t
        return 1 - 2 * (1 - t) * (1 - t)
    
    @staticmethod
    def bounce(t: float) -> float:
        """Bounce easing."""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
    
    @staticmethod
    def elastic(t: float) -> float:
        """Elastic easing."""
        if t == 0 or t == 1:
            return t
        
        c4 = (2 * math.pi) / 3
        return -(2 ** (10 * (t - 1))) * math.sin((t - 1.1) * c4)
    
    @classmethod
    def apply_easing(cls, t: float, easing: str) -> float:
        """Apply easing function to time value."""
        t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
        
        if easing == "ease_in":
            return cls.ease_in(t)
        elif easing == "ease_out":
            return cls.ease_out(t)
        elif easing == "ease_in_out":
            return cls.ease_in_out(t)
        elif easing == "bounce":
            return cls.bounce(t)
        elif easing == "elastic":
            return cls.elastic(t)
        else:  # linear
            return t
    
    @classmethod
    def get_effect_value(cls, effect: MotionEffect, current_time: float) -> float:
        """Get effect intensity at given time using keyframe interpolation."""
        if not effect.keyframes:
            return 0.0
        
        # Handle looping
        if effect.loop and effect.duration > 0:
            current_time = current_time % effect.duration
        
        # Handle reverse
        if effect.reverse:
            current_time = effect.duration - current_time
        
        # Clamp time to effect duration
        current_time = max(0.0, min(effect.duration, current_time))
        
        # Sort keyframes by time
        keyframes = sorted(effect.keyframes, key=lambda k: k.time)
        
        # Find surrounding keyframes
        if current_time <= keyframes[0].time:
            return keyframes[0].value
        
        if current_time >= keyframes[-1].time:
            return keyframes[-1].value
        
        # Find interpolation segment
        for i in range(len(keyframes) - 1):
            k1, k2 = keyframes[i], keyframes[i + 1]
            
            if k1.time <= current_time <= k2.time:
                # Interpolate between keyframes
                if k2.time == k1.time:
                    return k2.value
                
                # Calculate normalized time
                t = (current_time - k1.time) / (k2.time - k1.time)
                
                # Apply easing
                eased_t = cls.apply_easing(t, k2.easing)
                
                # Linear interpolation with easing
                return k1.value + eased_t * (k2.value - k1.value)
        
        return 0.0


class MotionEffectRenderer:
    """Renders motion effects on images/video frames."""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080)):
        self.resolution = resolution
        self.width, self.height = resolution
    
    def apply_effect(self, image: np.ndarray, effect: MotionEffect, current_time: float,
                    audio_features: Optional[Dict] = None) -> np.ndarray:
        """Apply motion effect to image at given time."""
        intensity = EffectEvolution.get_effect_value(effect, current_time)
        
        if intensity == 0.0:
            return image
        
        # Apply audio-reactive modulation if available
        if audio_features and effect.properties.get('audio_reactive', False):
            if 'rms_energy' in audio_features:
                energy_mod = audio_features['rms_energy'] * effect.properties.get('energy_sensitivity', 0.3)
                intensity *= (1.0 + energy_mod)
            
            if audio_features.get('on_beat', False):
                intensity *= effect.properties.get('beat_multiplier', 1.5)
        
        # Apply specific effect
        return self._apply_specific_effect(image, effect.effect_type, intensity, effect.properties)
    
    def _apply_specific_effect(self, image: np.ndarray, effect_type: EffectType, 
                             intensity: float, properties: Dict) -> np.ndarray:
        """Apply specific effect type with given intensity."""
        
        # Transform effects
        if effect_type == EffectType.ZOOM_IN:
            return self._apply_zoom(image, 1.0 + intensity * 0.5, properties)
        elif effect_type == EffectType.ZOOM_OUT:
            return self._apply_zoom(image, 1.0 - intensity * 0.3, properties)
        elif effect_type == EffectType.PAN_LEFT:
            return self._apply_pan(image, -intensity * 100, 0, properties)
        elif effect_type == EffectType.PAN_RIGHT:
            return self._apply_pan(image, intensity * 100, 0, properties)
        elif effect_type == EffectType.PAN_UP:
            return self._apply_pan(image, 0, -intensity * 100, properties)
        elif effect_type == EffectType.PAN_DOWN:
            return self._apply_pan(image, 0, intensity * 100, properties)
        elif effect_type == EffectType.ROTATE_CW:
            return self._apply_rotation(image, intensity * 360, properties)
        elif effect_type == EffectType.ROTATE_CCW:
            return self._apply_rotation(image, -intensity * 360, properties)
        
        # Scale effects
        elif effect_type == EffectType.SCALE_PULSE:
            pulse = math.sin(intensity * math.pi * 4) * 0.2 + 1.0
            return self._apply_zoom(image, pulse, properties)
        elif effect_type == EffectType.SCALE_BOUNCE:
            bounce = abs(math.sin(intensity * math.pi * 2)) * 0.3 + 1.0
            return self._apply_zoom(image, bounce, properties)
        
        # Position effects
        elif effect_type == EffectType.SLIDE_IN_LEFT:
            offset_x = -self.width * (1.0 - intensity)
            return self._apply_pan(image, offset_x, 0, properties)
        elif effect_type == EffectType.SLIDE_IN_RIGHT:
            offset_x = self.width * (1.0 - intensity)
            return self._apply_pan(image, offset_x, 0, properties)
        elif effect_type == EffectType.SLIDE_IN_TOP:
            offset_y = -self.height * (1.0 - intensity)
            return self._apply_pan(image, 0, offset_y, properties)
        elif effect_type == EffectType.SLIDE_IN_BOTTOM:
            offset_y = self.height * (1.0 - intensity)
            return self._apply_pan(image, 0, offset_y, properties)
        
        # Opacity effects
        elif effect_type == EffectType.FADE_IN:
            return self._apply_opacity(image, intensity, properties)
        elif effect_type == EffectType.FADE_OUT:
            return self._apply_opacity(image, 1.0 - intensity, properties)
        elif effect_type == EffectType.FLASH:
            flash = abs(math.sin(intensity * math.pi * 8))
            return self._apply_opacity(image, flash, properties)
        
        # Motion effects
        elif effect_type == EffectType.CAMERA_SHAKE:
            shake_x = (np.random.random() - 0.5) * intensity * 20
            shake_y = (np.random.random() - 0.5) * intensity * 20
            return self._apply_pan(image, shake_x, shake_y, properties)
        elif effect_type == EffectType.MOTION_BLUR:
            angle = properties.get('angle', 0)
            strength = int(intensity * 15)
            return self._apply_motion_blur(image, angle, strength)
        
        # Distortion effects
        elif effect_type == EffectType.WAVE_HORIZONTAL:
            return self._apply_wave(image, intensity, 'horizontal', properties)
        elif effect_type == EffectType.WAVE_VERTICAL:
            return self._apply_wave(image, intensity, 'vertical', properties)
        
        # Color effects
        elif effect_type == EffectType.COLOR_SHIFT:
            hue_shift = intensity * properties.get('hue_range', 60)
            return self._apply_color_shift(image, hue_shift, properties)
        elif effect_type == EffectType.BRIGHTNESS_PULSE:
            brightness = 1.0 + math.sin(intensity * math.pi * 4) * 0.3
            return self._apply_brightness(image, brightness, properties)
        
        # BOLD NEW EFFECTS
        elif effect_type == EffectType.GLITCH_DIGITAL:
            return self._apply_digital_glitch(image, intensity, properties)
        elif effect_type == EffectType.SHATTER_BREAK:
            return self._apply_shatter_effect(image, intensity, properties)
        elif effect_type == EffectType.LIQUID_WARP:
            return self._apply_liquid_warp(image, intensity, properties)
        elif effect_type == EffectType.PORTAL_SWIRL:
            return self._apply_portal_swirl(image, intensity, properties)
        elif effect_type == EffectType.NEON_GLOW:
            return self._apply_neon_glow(image, intensity, properties)
        elif effect_type == EffectType.HOLOGRAM_FLICKER:
            return self._apply_hologram_flicker(image, intensity, properties)
        elif effect_type == EffectType.ENERGY_BURST:
            return self._apply_energy_burst(image, intensity, properties)
        elif effect_type == EffectType.MIRROR_KALEIDOSCOPE:
            return self._apply_kaleidoscope(image, intensity, properties)
        
        return image
    
    def _apply_zoom(self, image: np.ndarray, scale: float, properties: Dict) -> np.ndarray:
        """Apply zoom effect."""
        h, w = image.shape[:2]
        center = properties.get('center', (w // 2, h // 2))
        
        # Create transformation matrix
        M = cv2.getRotationMatrix2D(center, 0, scale)
        
        # Apply transformation
        return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    
    def _apply_pan(self, image: np.ndarray, dx: float, dy: float, properties: Dict) -> np.ndarray:
        """Apply pan (translation) effect."""
        h, w = image.shape[:2]
        
        # Create translation matrix
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        
        # Apply transformation
        return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    
    def _apply_rotation(self, image: np.ndarray, angle: float, properties: Dict) -> np.ndarray:
        """Apply rotation effect."""
        h, w = image.shape[:2]
        center = properties.get('center', (w // 2, h // 2))
        
        # Create rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Apply transformation
        return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    
    def _apply_opacity(self, image: np.ndarray, opacity: float, properties: Dict) -> np.ndarray:
        """Apply opacity effect."""
        if image.shape[2] == 4:  # Has alpha channel
            result = image.copy()
            result[:, :, 3] = (result[:, :, 3] * opacity).astype(np.uint8)
            return result
        else:
            # Create alpha channel
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = int(255 * opacity)
            return result
    
    def _apply_motion_blur(self, image: np.ndarray, angle: float, strength: int) -> np.ndarray:
        """Apply motion blur effect."""
        if strength < 3:
            return image
        
        # Create motion blur kernel
        kernel = np.zeros((strength, strength))
        center = strength // 2
        
        # Create line in kernel
        angle_rad = np.radians(angle)
        for i in range(strength):
            x = int(center + (i - center) * np.cos(angle_rad))
            y = int(center + (i - center) * np.sin(angle_rad))
            if 0 <= x < strength and 0 <= y < strength:
                kernel[y, x] = 1
                
        # Normalize kernel
        if np.sum(kernel) > 0:
            kernel = kernel / np.sum(kernel)
            return cv2.filter2D(image, -1, kernel)
        
        return image
    
    def _apply_wave(self, image: np.ndarray, intensity: float, direction: str, properties: Dict) -> np.ndarray:
        """Apply wave distortion effect."""
        h, w = image.shape[:2]
        amplitude = intensity * properties.get('amplitude', 20)
        frequency = properties.get('frequency', 0.1)
        
        # Create displacement map
        x_map = np.zeros((h, w), dtype=np.float32)
        y_map = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                if direction == 'horizontal':
                    x_map[y, x] = x + amplitude * np.sin(2 * np.pi * y * frequency / h)
                    y_map[y, x] = y
                else:  # vertical
                    x_map[y, x] = x
                    y_map[y, x] = y + amplitude * np.sin(2 * np.pi * x * frequency / w)
                    
        # Apply remap
        return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    def _apply_color_shift(self, image: np.ndarray, hue_shift: float, properties: Dict) -> np.ndarray:
        """Apply color shift effect."""
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Shift hue
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
        
        # Convert back
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def _apply_brightness(self, image: np.ndarray, brightness: float, properties: Dict) -> np.ndarray:
        """Apply brightness effect."""
        return cv2.convertScaleAbs(image, alpha=brightness, beta=0)
    
    def _apply_digital_glitch(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply digital glitch effect."""
        result = image.copy()
        h, w = image.shape[:2]
        
        # Random pixel displacement
        if np.random.random() < intensity:
            # Horizontal line glitches
            num_lines = int(intensity * 20)
            for _ in range(num_lines):
                y = np.random.randint(0, h)
                shift = int(np.random.randint(-50, 50) * intensity)
                if shift != 0:
                    result[y] = np.roll(result[y], shift, axis=0)
        
        # Color channel separation
        if intensity > 0.5:
            offset = int(intensity * 10)
            # Shift red channel
            result[:, offset:, 0] = image[:, :-offset, 0]
            # Shift blue channel
            result[:, :-offset, 2] = image[:, offset:, 2]
        
        return result
    
    def _apply_neon_glow(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply neon glow effect."""
        # Multiple glow layers with neon colors
        result = image.copy()
        
        # Create edge-based glow
        if len(image.shape) == 4:
            edges = cv2.Canny(image[:,:,3], 50, 150)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            edges = cv2.Canny(gray, 50, 150)
        
        # Create glow layers
        for glow_size in [5, 10, 15]:
            glow_mask = cv2.dilate(edges, np.ones((glow_size, glow_size)), iterations=1)
            glow_mask = cv2.GaussianBlur(glow_mask, (glow_size*2+1, glow_size*2+1), 0)
            
            # Apply neon color (cyan/magenta)
            if len(result.shape) == 3:
                glow_color = np.zeros_like(result)
                glow_color[:,:,0] = glow_mask  # Blue
                glow_color[:,:,2] = glow_mask  # Red -> Magenta
                result = cv2.addWeighted(result, 1.0, glow_color, intensity * 0.3, 0)
        
        return result
    
    def _apply_energy_burst(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply energy burst effect."""
        h, w = image.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Create energy rays
        burst = np.zeros_like(image)
        num_rays = int(intensity * 16)
        
        for i in range(num_rays):
            angle = (2 * np.pi * i) / num_rays
            ray_length = int(intensity * min(w, h) * 0.4)
            
            end_x = int(center_x + ray_length * np.cos(angle))
            end_y = int(center_y + ray_length * np.sin(angle))
            
            color = (255, 255, 255) if len(image.shape) == 3 else (255, 255, 255, 255)
            cv2.line(burst, (center_x, center_y), (end_x, end_y), color, max(1, int(intensity * 2)))
        
        # Blur for energy effect
        burst = cv2.GaussianBlur(burst, (11, 11), 0)
        return cv2.addWeighted(image, 1.0, burst, intensity * 0.5, 0)
    
    def _apply_liquid_warp(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply liquid warp effect."""
        h, w = image.shape[:2]
        amplitude = intensity * 20
        
        # Create wave displacement
        x_map = np.zeros((h, w), dtype=np.float32)
        y_map = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                # Liquid wave distortion
                wave_x = amplitude * np.sin(2 * np.pi * y / (h * 0.1))
                wave_y = amplitude * np.sin(2 * np.pi * x / (w * 0.1))
                
                x_map[y, x] = x + wave_x
                y_map[y, x] = y + wave_y
        
        return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    def _apply_shatter_effect(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply shatter effect with cracks."""
        result = image.copy()
        h, w = image.shape[:2]
        
        # Draw crack lines
        num_cracks = int(intensity * 8)
        for _ in range(num_cracks):
            x1, y1 = np.random.randint(0, w), np.random.randint(0, h)
            x2, y2 = np.random.randint(0, w), np.random.randint(0, h)
            
            # Draw crack
            cv2.line(result, (x1, y1), (x2, y2), (0, 0, 0), max(1, int(intensity * 3)))
        
        return result
    
    def _apply_portal_swirl(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply portal swirl effect."""
        h, w = image.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Create swirl transformation
        x_map = np.zeros((h, w), dtype=np.float32)
        y_map = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                dx = x - center_x
                dy = y - center_y
                distance = np.sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    angle = np.arctan2(dy, dx)
                    swirl_factor = intensity * 0.1 / (distance / min(w, h) + 0.1)
                    new_angle = angle + swirl_factor
                    
                    x_map[y, x] = center_x + distance * np.cos(new_angle)
                    y_map[y, x] = center_y + distance * np.sin(new_angle)
                else:
                    x_map[y, x] = x
                    y_map[y, x] = y
        
        return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    def _apply_hologram_flicker(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply hologram flicker effect."""
        result = image.copy()
        
        # Random opacity flicker
        if np.random.random() < intensity:
            flicker = 0.5 + 0.5 * np.random.random()
            result = (result * flicker).astype(np.uint8)
        
        # Scan lines
        for y in range(0, image.shape[0], 3):
            if np.random.random() < intensity * 0.3:
                result[y] = result[y] * 0.8
        
        return result
    
    def _apply_kaleidoscope(self, image: np.ndarray, intensity: float, properties: Dict) -> np.ndarray:
        """Apply kaleidoscope mirror effect."""
        # Simple mirror effect
        h, w = image.shape[:2]
        
        # Create mirrored sections
        result = image.copy()
        
        # Vertical mirror
        if intensity > 0.3:
            left_half = result[:, :w//2]
            result[:, w//2:] = cv2.flip(left_half, 1)
        
        # Horizontal mirror
        if intensity > 0.6:
            top_half = result[:h//2, :]
            result[h//2:, :] = cv2.flip(top_half, 0)
        
        return cv2.addWeighted(image, 1 - intensity, result, intensity, 0)


def create_effect(effect_type: EffectType, duration: float, **kwargs) -> MotionEffect:
    """Create a motion effect with common keyframe patterns."""
    
    # Extract common parameters
    start_value = kwargs.get('start_value', 0.0)
    peak_value = kwargs.get('peak_value', 1.0)
    end_value = kwargs.get('end_value', 0.0)
    easing = kwargs.get('easing', 'ease_in_out')
    loop = kwargs.get('loop', False)
    reverse = kwargs.get('reverse', False)
    
    # Create default keyframes
    keyframes = [
        EffectKeyframe(0.0, start_value, 'linear'),
        EffectKeyframe(duration, peak_value, easing)
    ]
    
    # Add end keyframe if different from peak
    if end_value != peak_value:
        keyframes.append(EffectKeyframe(duration, end_value, easing))
    
    # Extract properties
    properties = {k: v for k, v in kwargs.items() 
                 if k not in ['start_value', 'peak_value', 'end_value', 'easing', 'loop', 'reverse']}
    
    return MotionEffect(
        effect_type=effect_type,
        duration=duration,
        keyframes=keyframes,
        properties=properties,
        loop=loop,
        reverse=reverse
    )
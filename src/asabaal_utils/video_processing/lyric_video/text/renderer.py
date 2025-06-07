"""Text rendering engine with animations and effects."""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, replace
import logging

from .fonts import FontManager
from .animations import TextAnimation, AnimationType, AnimationEasing, AnimationState
from ..lyrics.parser import LyricWord

logger = logging.getLogger(__name__)


@dataclass
class TextStyle:
    """Text rendering style configuration."""
    font_family: str = "Arial"
    font_size: int = 72
    color: Tuple[int, int, int] = (255, 255, 255)
    stroke_width: int = 3
    stroke_color: Tuple[int, int, int] = (0, 0, 0)
    glow_radius: int = 0
    glow_color: Optional[Tuple[int, int, int]] = None
    shadow_offset: Optional[Tuple[int, int]] = None
    shadow_blur: int = 5
    shadow_opacity: float = 0.5
    line_spacing: float = 1.2
    alignment: str = "center"  # left, center, right
    vertical_position: str = "center"  # top, center, bottom
    dynamic_positioning: bool = False  # Enable dynamic positioning based on content
    motion_tracking: bool = False  # Enable motion-based effects


@dataclass
class AnimationConfig:
    """Animation configuration for text."""
    entrance_type: AnimationType = AnimationType.FADE_IN
    exit_type: AnimationType = AnimationType.FADE_OUT
    easing: AnimationEasing = AnimationEasing.EASE_OUT
    duration: float = 0.5
    character_delay: float = 0.05
    word_delay: float = 0.1
    sync_to_beats: bool = True
    amplitude: float = 1.0
    
    def copy(self):
        """Create a copy of this animation config."""
        return replace(self)


class TextRenderer:
    """Renders animated text for lyric videos."""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080)):
        """Initialize text renderer.
        
        Args:
            resolution: Output resolution (width, height)
        """
        self.resolution = resolution
        self.font_manager = FontManager()
        self.animation_presets: Dict[str, AnimationConfig] = self._create_presets()
        
    def _create_presets(self) -> Dict[str, AnimationConfig]:
        """Create animation presets."""
        return {
            "subtle": AnimationConfig(
                entrance_type=AnimationType.FADE_IN,
                exit_type=AnimationType.FADE_OUT,
                duration=0.3
            ),
            "dynamic": AnimationConfig(
                entrance_type=AnimationType.BOUNCE_IN,
                exit_type=AnimationType.SCALE_OUT,
                easing=AnimationEasing.BOUNCE,
                duration=0.5
            ),
            "typewriter": AnimationConfig(
                entrance_type=AnimationType.TYPEWRITER,
                exit_type=AnimationType.FADE_OUT,
                character_delay=0.05
            ),
            "energetic": AnimationConfig(
                entrance_type=AnimationType.ELASTIC_IN,
                exit_type=AnimationType.ROTATE_IN,
                easing=AnimationEasing.ELASTIC,
                sync_to_beats=True
            ),
            "smooth": AnimationConfig(
                entrance_type=AnimationType.SLIDE_IN,
                exit_type=AnimationType.SLIDE_OUT,
                easing=AnimationEasing.EASE_IN_OUT
            )
        }
        
    def render_animated_text(self, text: str, style: TextStyle,
                           progress: float, animation_config: AnimationConfig,
                           audio_features: Optional[Dict] = None,
                           effects_config: Optional[Dict] = None) -> np.ndarray:
        """Render animated text with effects.
        
        Args:
            text: Text to render
            style: Text style configuration
            progress: Animation progress (0.0 to 1.0)
            animation_config: Animation configuration
            audio_features: Optional audio features for reactive effects
            
        Returns:
            RGBA image with rendered text
        """
        # Calculate animation state
        if progress < 0.5:
            # Entrance animation
            anim_progress = progress * 2
            anim_state = TextAnimation.calculate_animation_state(
                animation_config.entrance_type,
                anim_progress,
                animation_config.easing,
                amplitude=animation_config.amplitude
            )
        else:
            # Exit animation
            anim_progress = (progress - 0.5) * 2
            anim_state = TextAnimation.calculate_animation_state(
                animation_config.exit_type,
                anim_progress,
                animation_config.easing,
                amplitude=animation_config.amplitude
            )
            
        # Apply audio-reactive modifications
        if audio_features and animation_config.sync_to_beats:
            if audio_features.get('on_beat', False):
                # Pulse on beat
                anim_state.scale = (
                    anim_state.scale[0] * 1.1,
                    anim_state.scale[1] * 1.1
                )
            
            # Energy-based glow
            if 'rms_energy' in audio_features:
                energy = audio_features['rms_energy']
                if energy > 0.7 and style.glow_radius > 0:
                    style = replace(style, glow_radius=int(style.glow_radius * (1 + energy)))
                    
        # Render text with effects
        text_img = self.font_manager.render_text_with_effects(
            text=text,
            font_family=style.font_family,
            font_size=int(style.font_size * anim_state.scale[0]),
            color=style.color,
            stroke_width=style.stroke_width,
            stroke_color=style.stroke_color,
            shadow_offset=style.shadow_offset,
            shadow_blur=style.shadow_blur,
            shadow_opacity=style.shadow_opacity,
            glow_radius=style.glow_radius,
            glow_color=style.glow_color
        )
        
        # Apply opacity
        if anim_state.opacity < 1.0:
            text_img[:, :, 3] = (text_img[:, :, 3] * anim_state.opacity).astype(np.uint8)
            
        # Apply rotation if needed
        if anim_state.rotation != 0:
            text_img = self._rotate_image(text_img, anim_state.rotation)
            
        # Character animation (typewriter effect)
        if animation_config.entrance_type == AnimationType.TYPEWRITER:
            text_img = self._apply_typewriter_effect(text_img, text, anim_state.char_progress)
            
        # Apply section-based dramatic text effects
        if effects_config is None:
            effects_config = {
                'ambient_glow': True,
                'dynamic_colors': True,
                'lighting_effects': True,
                'energy_bursts': True,
                'wave_effect': False,
                'chromatic_aberration': False
            }
        text_img = self.apply_text_effects(text_img, effects_config, audio_features, progress)
            
        return text_img
        
    def render_lyric_line(self, words: List[LyricWord], current_time: float,
                         style: TextStyle, animation_config: AnimationConfig,
                         line_start: float, line_end: float,
                         audio_features: Optional[Dict] = None,
                         effects_config: Optional[Dict] = None) -> np.ndarray:
        """Render a complete lyric line with word-level animations.
        
        Args:
            words: List of words in the line
            current_time: Current timestamp
            style: Text style
            animation_config: Animation configuration
            line_start: Line start time
            line_end: Line end time
            audio_features: Optional audio features
            
        Returns:
            RGBA image with rendered line
        """
        # Create LARGER canvas with padding to prevent text cutoff
        CANVAS_PADDING = 200  # Extra padding to prevent any clipping
        canvas_height = self.resolution[1] + CANVAS_PADDING * 2
        canvas_width = self.resolution[0] + CANVAS_PADDING * 2
        canvas = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)
        
        # We'll render with padding offset and crop at the end
        
        # Calculate line progress
        if current_time < line_start:
            line_progress = 0.0
        elif current_time > line_end:
            line_progress = 1.0
        else:
            line_progress = (current_time - line_start) / (line_end - line_start)
            
        # Render each word
        word_images = []
        total_width = 0
        max_height = 0
        
        for i, word in enumerate(words):
            # Calculate word progress
            if current_time < word.start_time:
                word_progress = 0.0
            elif current_time > word.end_time:
                word_progress = 1.0
            else:
                if word.duration > 0:
                    word_progress = (current_time - word.start_time) / word.duration
                else:
                    word_progress = 1.0  # Word appears instantly if duration is 0
                
            # Apply word delay for staggered animations
            if animation_config.word_delay > 0:
                delay_offset = i * animation_config.word_delay
                adjusted_progress = max(0, min(1, line_progress - delay_offset))
            else:
                adjusted_progress = word_progress
                
            # Render word
            word_img = self.render_animated_text(
                word.text,
                style,
                adjusted_progress,
                animation_config,
                audio_features,
                effects_config
            )
            
            word_images.append(word_img)
            total_width += word_img.shape[1] + 20  # Add spacing
            max_height = max(max_height, word_img.shape[0])
            
        # Remove last spacing
        total_width -= 20
        
        # HORIZONTAL SAFE ZONES - prevent negative coordinates for wide text
        SAFE_LEFT_MARGIN = 50
        SAFE_RIGHT_MARGIN = 50
        available_width = self.resolution[0] - SAFE_LEFT_MARGIN - SAFE_RIGHT_MARGIN
        
        # Calculate starting position based on alignment (add padding offset)
        if style.alignment == "center":
            if total_width <= available_width:
                # Text fits: center it normally
                x_pos = (self.resolution[0] - total_width) // 2 + CANVAS_PADDING
            else:
                # Text too wide: start from safe left margin
                x_pos = SAFE_LEFT_MARGIN + CANVAS_PADDING
        elif style.alignment == "right":
            if total_width <= available_width:
                # Text fits: align right normally
                x_pos = self.resolution[0] - total_width - SAFE_RIGHT_MARGIN + CANVAS_PADDING
            else:
                # Text too wide: start from safe left margin
                x_pos = SAFE_LEFT_MARGIN + CANVAS_PADDING
        else:  # left
            x_pos = SAFE_LEFT_MARGIN + CANVAS_PADDING
            
        # Calculate vertical position based on style (add padding offset)
        y_pos = self._calculate_vertical_position(max_height, style, current_time, audio_features) + CANVAS_PADDING
        
        # Composite words onto canvas
        current_x = x_pos
        for word_img in word_images:
            h, w = word_img.shape[:2]
            
            # With padding, we don't need to clip - just composite
            self._composite_image(canvas, word_img, current_x, y_pos)
            current_x += w + 20
            
        # IMPORTANT: Crop canvas back to original resolution
        # This ensures we only return the visible area without padding
        final_canvas = canvas[CANVAS_PADDING:CANVAS_PADDING + self.resolution[1], 
                             CANVAS_PADDING:CANVAS_PADDING + self.resolution[0]]
        
        return final_canvas
        
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image around its center.
        
        Args:
            image: Input image
            angle: Rotation angle in degrees
            
        Returns:
            Rotated image
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new bounds
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Adjust rotation matrix for new bounds
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # Rotate with transparent background
        rotated = cv2.warpAffine(image, M, (new_w, new_h), 
                               flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT,
                               borderValue=(0, 0, 0, 0))
        
        return rotated
        
    def _apply_typewriter_effect(self, image: np.ndarray, text: str, 
                               progress: float) -> np.ndarray:
        """Apply typewriter reveal effect.
        
        Args:
            image: Rendered text image
            text: Original text
            progress: Reveal progress (0.0 to 1.0)
            
        Returns:
            Image with typewriter effect
        """
        if progress >= 1.0:
            return image
            
        # Calculate how many characters to show
        num_chars = int(len(text) * progress)
        if num_chars == 0:
            return np.zeros_like(image)
            
        # Estimate character width (simple approach)
        char_width = image.shape[1] / len(text)
        reveal_width = int(char_width * num_chars)
        
        # Create mask
        mask = np.zeros_like(image)
        mask[:, :reveal_width] = image[:, :reveal_width]
        
        return mask
        
    def _composite_image(self, base: np.ndarray, overlay: np.ndarray, 
                        x: int, y: int):
        """Composite overlay onto base image.
        
        Args:
            base: Base image (modified in place)
            overlay: Overlay image with alpha
            x: X position
            y: Y position
        """
        h, w = overlay.shape[:2]
        base_h, base_w = base.shape[:2]
        
        # Calculate valid region
        y1 = max(0, y)
        y2 = min(base_h, y + h)
        x1 = max(0, x)
        x2 = min(base_w, x + w)
        
        if x2 <= x1 or y2 <= y1:
            return
            
        # Get regions
        base_region = base[y1:y2, x1:x2]
        overlay_region = overlay[y1-y:y2-y, x1-x:x2-x]
        
        # Alpha composite
        alpha = overlay_region[:, :, 3:4] / 255.0
        base_region[:] = (alpha * overlay_region + (1 - alpha) * base_region).astype(np.uint8)
        
    def apply_text_effects(self, text_surface: np.ndarray, 
                          effects_config: Dict, audio_features: Optional[Dict] = None,
                          current_time: float = 0.0) -> np.ndarray:
        """Apply dramatic text effects with audio reactivity.
        
        Args:
            text_surface: Rendered text surface
            effects_config: Effects configuration
            audio_features: Optional audio features for reactive effects
            current_time: Current timestamp for time-based effects
            
        Returns:
            Text with enhanced effects applied
        """
        result = text_surface.copy()
        
        # DRAMATIC AMBIENT GLOW EFFECTS
        if effects_config.get('ambient_glow', True):
            result = self._apply_ambient_glow_system(result, audio_features, current_time)
            
        # DYNAMIC COLOR SYSTEMS
        if effects_config.get('dynamic_colors', True):
            result = self._apply_dynamic_color_system(result, audio_features, current_time)
            
        # LIGHTING EFFECTS
        if effects_config.get('lighting_effects', True):
            result = self._apply_lighting_effects(result, audio_features, current_time)
            
        # Original effects (enhanced)
        if effects_config.get('wave_effect', False):
            amplitude = effects_config.get('wave_amplitude', 10)
            frequency = effects_config.get('wave_frequency', 0.1)
            # Make wave effect audio-reactive
            if audio_features and 'rms_energy' in audio_features:
                amplitude *= (1 + audio_features['rms_energy'])
            result = self._apply_wave_distortion(result, amplitude, frequency)
            
        # Enhanced chromatic aberration
        if effects_config.get('chromatic_aberration', False):
            offset = effects_config.get('aberration_offset', 3)
            # Make chromatic aberration beat-reactive
            if audio_features and audio_features.get('on_beat', False):
                offset *= 2
            result = self._apply_chromatic_aberration(result, offset)
            
        # ENERGY BURST EFFECTS
        if effects_config.get('energy_bursts', True) and audio_features:
            result = self._apply_energy_burst_effects(result, audio_features, current_time)
            
        # SPECIAL INSTRUMENTAL HOOK EFFECTS
        if effects_config.get('instrumental_mode', False) and audio_features:
            result = self._apply_instrumental_hook_effects(result, audio_features, current_time, effects_config)
            
        return result
        
    def _apply_wave_distortion(self, image: np.ndarray, amplitude: float, 
                              frequency: float) -> np.ndarray:
        """Apply wave distortion effect.
        
        Args:
            image: Input image
            amplitude: Wave amplitude
            frequency: Wave frequency
            
        Returns:
            Distorted image
        """
        h, w = image.shape[:2]
        
        # Create displacement map
        x_map = np.zeros((h, w), dtype=np.float32)
        y_map = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                x_map[y, x] = x + amplitude * np.sin(2 * np.pi * y * frequency / h)
                y_map[y, x] = y
                
        # Apply remap
        return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT,
                        borderValue=(0, 0, 0, 0))
        
    def _apply_chromatic_aberration(self, image: np.ndarray, offset: int) -> np.ndarray:
        """Apply chromatic aberration effect.
        
        Args:
            image: Input image
            offset: Pixel offset for channels
            
        Returns:
            Image with chromatic aberration
        """
        if image.shape[2] < 3:
            return image
            
        result = image.copy()
        
        # Shift red channel right
        result[:, offset:, 0] = image[:, :-offset, 0]
        
        # Shift blue channel left
        result[:, :-offset, 2] = image[:, offset:, 2]
        
        return result
        
    def _calculate_vertical_position(self, text_height: int, style: TextStyle, 
                                   current_time: float, audio_features: Optional[Dict] = None) -> int:
        """Calculate vertical position using FIXED SAFE ZONES - no more cutoff!
        
        Args:
            text_height: Height of the text in pixels
            style: Text style configuration
            current_time: Current timestamp
            audio_features: Optional audio features for reactive positioning
            
        Returns:
            Y position for text
        """
        # FIXED SAFE ZONES - absolutely guarantee no cutoff
        screen_height = self.resolution[1]
        
        # Define safe zones with massive buffers
        SAFE_TOP_MARGIN = 150  # Increased from 100
        SAFE_BOTTOM_MARGIN = 350  # Increased from 200 - much larger buffer from bottom
        
        # Calculate the safe zone height
        safe_zone_height = screen_height - SAFE_TOP_MARGIN - SAFE_BOTTOM_MARGIN
        
        # If text is too big for safe zone, adjust margins while maintaining bottom safety
        if text_height > safe_zone_height:
            logger.warning(f"Text height {text_height} too large for safe zone {safe_zone_height}")
            # Force text to fit by reducing safe zone top, but keep large bottom margin
            SAFE_TOP_MARGIN = 50
            SAFE_BOTTOM_MARGIN = max(300, SAFE_BOTTOM_MARGIN)  # Never go below 300px bottom margin
            safe_zone_height = screen_height - SAFE_TOP_MARGIN - SAFE_BOTTOM_MARGIN
        
        # FIXED POSITIONS - no calculations, just safe fixed spots
        if style.vertical_position == "top":
            # Top safe zone
            base_y = SAFE_TOP_MARGIN
        elif style.vertical_position == "bottom":
            # Bottom of safe zone (well above actual bottom)
            base_y = screen_height - SAFE_BOTTOM_MARGIN - text_height
        else:
            # CENTER of safe zone (default)
            safe_zone_center = SAFE_TOP_MARGIN + (safe_zone_height // 2)
            base_y = safe_zone_center - (text_height // 2)
        
        # ABSOLUTELY NO DYNAMIC POSITIONING - keep it fixed and safe
        # All audio-reactive effects disabled for now to ensure text stays visible
        
        # FINAL SAFETY CLAMP - never let text go outside safe bounds
        absolute_min_y = SAFE_TOP_MARGIN
        absolute_max_y = screen_height - SAFE_BOTTOM_MARGIN - text_height
        
        base_y = max(absolute_min_y, min(absolute_max_y, base_y))
        
        # Debug logging
        logger.debug(f"Text positioning: height={text_height}, safe_zone={safe_zone_height}, y={base_y}")
        logger.debug(f"Screen bounds: top={absolute_min_y}, bottom={absolute_max_y}, actual={base_y}")
        
        return base_y
        
    def add_motion_blur_effect(self, frame: np.ndarray, motion_vector: Tuple[float, float]) -> np.ndarray:
        """Add motion blur effect to text frame.
        
        Args:
            frame: Input frame with text
            motion_vector: Motion vector (dx, dy)
            
        Returns:
            Frame with motion blur applied
        """
        if abs(motion_vector[0]) < 1 and abs(motion_vector[1]) < 1:
            return frame  # No significant motion
            
        # Create motion blur kernel
        motion_magnitude = np.sqrt(motion_vector[0]**2 + motion_vector[1]**2)
        if motion_magnitude < 2:
            return frame
            
        # Simple motion blur using directional blur
        kernel_size = min(15, int(motion_magnitude))
        if kernel_size % 2 == 0:
            kernel_size += 1
            
        # Create directional blur kernel
        angle = np.arctan2(motion_vector[1], motion_vector[0])
        kernel = np.zeros((kernel_size, kernel_size))
        
        # Draw line in kernel based on motion direction
        center = kernel_size // 2
        for i in range(-center, center + 1):
            x = int(center + i * np.cos(angle))
            y = int(center + i * np.sin(angle))
            if 0 <= x < kernel_size and 0 <= y < kernel_size:
                kernel[y, x] = 1
                
        # Normalize kernel
        if np.sum(kernel) > 0:
            kernel /= np.sum(kernel)
            
            # Apply blur only to alpha channel areas (where text exists)
            if frame.shape[2] == 4:
                # Apply to RGB channels where alpha > 0
                alpha_mask = frame[:, :, 3] > 0
                for c in range(3):
                    channel = frame[:, :, c].astype(np.float32)
                    blurred = cv2.filter2D(channel, -1, kernel)
                    frame[:, :, c] = np.where(alpha_mask, blurred, channel).astype(np.uint8)
                    
        return frame
        
    def _apply_ambient_glow_system(self, image: np.ndarray, audio_features: Optional[Dict], 
                                  current_time: float) -> np.ndarray:
        """Apply dramatic ambient glow system with multiple layers."""
        if image.shape[2] < 4:
            return image
            
        result = image.copy().astype(np.float32)
        
        # Extract text alpha for glow generation
        alpha = image[:, :, 3]
        text_mask = alpha > 0
        
        if not np.any(text_mask):
            return image
            
        # Multiple glow layers for EXTREME dramatic effect
        glow_layers = []
        base_intensity = 1.5  # Increased from 0.8
        
        # Audio-reactive intensity modulation (much more dramatic)
        if audio_features:
            energy = audio_features.get('rms_energy', 0.5)
            base_intensity *= (0.3 + energy * 2.0)  # More extreme scaling
            
            # Beat-synchronized MASSIVE glow pulses
            if audio_features.get('on_beat', False):
                base_intensity *= 3.0  # Increased from 1.8
                
            # Extreme energy boost for high energy moments
            if energy > 0.85:
                base_intensity *= 2.5
        
        # Layer 1: Inner glow (SUPER bright core)
        inner_glow = cv2.dilate(alpha, np.ones((8, 8)), iterations=2)  # Larger dilation
        inner_glow = cv2.GaussianBlur(inner_glow, (15, 15), 0)  # Softer blur
        glow_layers.append((inner_glow, base_intensity * 2.0, (255, 255, 255)))  # Much brighter
        
        # Layer 2: Middle glow (INTENSE energy color)
        middle_glow = cv2.dilate(alpha, np.ones((15, 15)), iterations=2)  # Larger
        middle_glow = cv2.GaussianBlur(middle_glow, (31, 31), 0)  # Much softer
        
        # Dynamic color based on audio (EXTREME variations)
        if audio_features and 'spectral_centroid' in audio_features:
            centroid = audio_features['spectral_centroid']
            energy = audio_features.get('rms_energy', 0.5)
            
            if centroid > 0.7:  # High frequencies - ELECTRIC cool colors
                color = (255, 100, 50) if energy > 0.8 else (255, 180, 100)  # Electric cyan
            elif centroid < 0.3:  # Low frequencies - MOLTEN warm colors
                color = (50, 100, 255) if energy > 0.8 else (100, 150, 255)  # Molten orange
            else:  # Mid frequencies - COSMIC purple/magenta
                color = (255, 50, 255) if energy > 0.8 else (255, 150, 255)  # Cosmic magenta
        else:
            # Time-based RAINBOW cycling (faster)
            hue_shift = (current_time * 60) % 360  # Faster cycling
            color = self._hsv_to_rgb(hue_shift, 1.0, 1.0)  # Full saturation
            
        glow_layers.append((middle_glow, base_intensity * 1.3, color))  # Brighter middle glow
        
        # Layer 3: Outer glow (MASSIVE ambient halo)
        outer_glow = cv2.dilate(alpha, np.ones((30, 30)), iterations=2)  # Much larger
        outer_glow = cv2.GaussianBlur(outer_glow, (61, 61), 0)  # Huge blur
        glow_layers.append((outer_glow, base_intensity * 0.8, (180, 180, 255)))  # Brighter outer glow
        
        # Layer 4: EXTREME outer halo for high energy
        if audio_features and audio_features.get('rms_energy', 0) > 0.8:
            extreme_glow = cv2.dilate(alpha, np.ones((50, 50)), iterations=3)
            extreme_glow = cv2.GaussianBlur(extreme_glow, (101, 101), 0)
            glow_layers.append((extreme_glow, base_intensity * 0.6, (255, 200, 255)))
        
        # Apply all glow layers
        for glow_mask, intensity, color in glow_layers:
            # Create colored glow
            glow_layer = np.zeros_like(result)
            for c in range(3):
                glow_layer[:, :, c] = (glow_mask / 255.0) * color[c] * intensity
                
            # Additive blending
            result[:, :, :3] += glow_layer[:, :, :3]
            
        # Clamp values
        result = np.clip(result, 0, 255)
        return result.astype(np.uint8)
        
    def _apply_dynamic_color_system(self, image: np.ndarray, audio_features: Optional[Dict],
                                   current_time: float) -> np.ndarray:
        """Apply dynamic color transformations based on audio and time."""
        if image.shape[2] < 4:
            return image
            
        result = image.copy()
        alpha = image[:, :, 3]
        text_mask = alpha > 0
        
        if not np.any(text_mask):
            return image
            
        # Extract RGB channels where text exists
        text_rgb = result[text_mask, :3].astype(np.float32)
        
        # Base color transformation
        if audio_features:
            # Energy-based saturation boost
            energy = audio_features.get('rms_energy', 0.5)
            saturation_boost = 1.0 + energy * 0.8
            
            # Convert to HSV for manipulation
            text_hsv = cv2.cvtColor(text_rgb.reshape(1, -1, 3), cv2.COLOR_RGB2HSV).reshape(-1, 3)
            
            # Spectral-based hue shifting
            if 'spectral_centroid' in audio_features:
                centroid = audio_features['spectral_centroid']
                hue_shift = (centroid - 0.5) * 120  # ±60 degree shift
                text_hsv[:, 0] = (text_hsv[:, 0] + hue_shift) % 180
                
            # Energy-based saturation
            text_hsv[:, 1] = np.clip(text_hsv[:, 1] * saturation_boost, 0, 255)
            
            # Beat-based brightness flash
            if audio_features.get('on_beat', False):
                text_hsv[:, 2] = np.clip(text_hsv[:, 2] * 1.4, 0, 255)
                
            # Convert back to RGB
            text_rgb = cv2.cvtColor(text_hsv.reshape(1, -1, 3), cv2.COLOR_HSV2RGB).reshape(-1, 3)
        else:
            # Time-based color cycling when no audio features
            time_hue = (current_time * 20) % 360
            text_hsv = cv2.cvtColor(text_rgb.reshape(1, -1, 3), cv2.COLOR_RGB2HSV).reshape(-1, 3)
            text_hsv[:, 0] = time_hue / 2  # Convert to OpenCV hue range
            text_rgb = cv2.cvtColor(text_hsv.reshape(1, -1, 3), cv2.COLOR_HSV2RGB).reshape(-1, 3)
            
        # Apply transformed colors back to image
        result[text_mask, :3] = np.clip(text_rgb, 0, 255).astype(np.uint8)
        
        return result
        
    def _apply_lighting_effects(self, image: np.ndarray, audio_features: Optional[Dict],
                               current_time: float) -> np.ndarray:
        """Apply dramatic lighting effects."""
        if image.shape[2] < 4:
            return image
            
        result = image.copy().astype(np.float32)
        h, w = result.shape[:2]
        
        # Create lighting gradient
        center_x, center_y = w // 2, h // 2
        y_coords, x_coords = np.ogrid[:h, :w]
        
        # Distance from center for radial lighting
        distance_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        max_distance = np.sqrt(center_x**2 + center_y**2)
        normalized_distance = distance_from_center / max_distance
        
        # Audio-reactive lighting intensity
        base_intensity = 0.3
        if audio_features:
            energy = audio_features.get('rms_energy', 0.5)
            base_intensity *= (0.5 + energy * 1.5)
            
        # Multiple lighting modes based on audio content
        if audio_features and 'spectral_centroid' in audio_features:
            centroid = audio_features['spectral_centroid']
            
            if centroid > 0.7:  # High frequency - spotlight effect
                spotlight = np.exp(-normalized_distance * 3) * base_intensity
                result[:, :, :3] *= (1 + spotlight[:, :, np.newaxis])
                
            elif centroid < 0.3:  # Low frequency - warm ambient
                ambient = (1 - normalized_distance * 0.5) * base_intensity * 0.5
                warm_tint = np.array([1.2, 1.0, 0.8])  # Warm lighting
                result[:, :, :3] *= (1 + ambient[:, :, np.newaxis] * warm_tint)
                
            else:  # Mid frequency - rim lighting
                rim_light = np.abs(normalized_distance - 0.7) * base_intensity
                rim_light = np.maximum(0, 1 - rim_light * 3)
                result[:, :, :3] *= (1 + rim_light[:, :, np.newaxis])
        
        # Beat-based flash lighting
        if audio_features and audio_features.get('on_beat', False):
            flash_intensity = 0.4
            result[:, :, :3] *= (1 + flash_intensity)
            
        return np.clip(result, 0, 255).astype(np.uint8)
        
    def _apply_energy_burst_effects(self, image: np.ndarray, audio_features: Dict,
                                   current_time: float) -> np.ndarray:
        """Apply EXTREME energy burst effects on high energy moments."""
        energy = audio_features.get('rms_energy', 0)
        
        if energy < 0.6:  # Lower threshold for more frequent bursts
            return image
            
        result = image.copy().astype(np.float32)
        
        # Create DRAMATIC energy burst pattern
        h, w = result.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # MASSIVE radial burst pattern
        burst_strength = (energy - 0.6) * 12  # Much stronger scaling
        
        # Create INTENSE burst rays
        num_rays = 32 if energy > 0.9 else 24 if energy > 0.8 else 16  # More rays for higher energy
        ray_thickness = max(3, int(energy * 8))  # Thicker rays
        
        for i in range(num_rays):
            angle = (2 * np.pi * i) / num_rays
            ray_length = min(w, h) * 0.6 * burst_strength  # Longer rays
            
            end_x = int(center_x + ray_length * np.cos(angle))
            end_y = int(center_y + ray_length * np.sin(angle))
            
            # Draw THICK energy ray
            ray_mask = np.zeros((h, w), dtype=np.float32)
            if 0 <= end_x < w and 0 <= end_y < h:
                cv2.line(ray_mask, (center_x, center_y), (end_x, end_y), 1.0, ray_thickness)
                
            # DRAMATIC blur for massive glow effect
            blur_size = max(15, int(energy * 25))
            if blur_size % 2 == 0:
                blur_size += 1
            ray_mask = cv2.GaussianBlur(ray_mask, (blur_size, blur_size), 0)
            
            # Apply INTENSE ray to image
            ray_intensity = burst_strength * 0.8  # Much stronger
            
            # Color-coded rays based on energy level
            if energy > 0.9:
                ray_color = [255, 100, 100]  # Electric red
            elif energy > 0.8:
                ray_color = [255, 255, 100]  # Electric yellow
            else:
                ray_color = [100, 255, 255]  # Electric cyan
                
            for c in range(3):
                result[:, :, c] += ray_mask * ray_color[c] * ray_intensity
        
        # Add EXPLOSIVE center burst for extreme energy
        if energy > 0.85:
            center_burst = np.zeros((h, w), dtype=np.float32)
            cv2.circle(center_burst, (center_x, center_y), int(min(w, h) * 0.1 * energy), 1.0, -1)
            center_burst = cv2.GaussianBlur(center_burst, (31, 31), 0)
            
            # BLINDING white center
            result[:, :, :3] += center_burst[:, :, np.newaxis] * 200 * (energy - 0.85) * 4
            
        return np.clip(result, 0, 255).astype(np.uint8)
        
    def _apply_instrumental_hook_effects(self, image: np.ndarray, audio_features: Dict,
                                        current_time: float, effects_config: Dict) -> np.ndarray:
        """Apply EXTREME instrumental hook effects for maximum visual impact."""
        result = image.copy().astype(np.float32)
        energy = audio_features.get('rms_energy', 0.5)
        h, w = result.shape[:2]
        
        # RAINBOW STROBE EFFECT
        if effects_config.get('strobe_on_beats', False) and audio_features.get('on_beat', False):
            strobe_intensity = 0.6 + energy * 0.4
            rainbow_hue = (current_time * 120) % 360
            strobe_color = self._hsv_to_rgb(rainbow_hue, 1.0, 1.0)
            
            # Apply rainbow strobe flash
            for c in range(3):
                result[:, :, c] = result[:, :, c] * (1 - strobe_intensity) + strobe_color[c] * strobe_intensity
        
        # KALEIDOSCOPE MIRROR EFFECT
        if effects_config.get('kaleidoscope_effect', False) and energy > 0.6:
            result = self._apply_kaleidoscope_mirror(result, current_time, energy)
        
        # PARTICLE SYSTEM EFFECT
        if effects_config.get('particle_effects', False) and energy > 0.5:
            result = self._apply_particle_system(result, audio_features, current_time)
        
        # PSYCHEDELIC WAVE DISTORTION
        if effects_config.get('psychedelic_mode', False):
            result = self._apply_psychedelic_waves(result, current_time, energy)
        
        # EXTREME RAINBOW MODE
        if effects_config.get('rainbow_mode', False):
            result = self._apply_extreme_rainbow_effect(result, current_time, energy)
        
        # MAXIMUM ENERGY VISUAL OVERLOAD
        if effects_config.get('max_energy_bursts', False) and energy > 0.8:
            result = self._apply_visual_overload(result, audio_features, current_time)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _apply_kaleidoscope_mirror(self, image: np.ndarray, current_time: float, energy: float) -> np.ndarray:
        """Apply kaleidoscope mirror effect."""
        h, w = image.shape[:2]
        result = image.copy()
        
        # Create multiple mirror segments
        num_segments = 8 if energy > 0.8 else 6 if energy > 0.7 else 4
        angle_per_segment = 360 / num_segments
        
        for i in range(num_segments):
            angle = (current_time * 30 + i * angle_per_segment) % 360
            
            # Create rotated and mirrored version
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h))
            
            # Mirror effect
            if i % 2 == 0:
                rotated = cv2.flip(rotated, 1)  # Horizontal flip
            
            # Blend with main image
            alpha = 0.3 * energy
            result = cv2.addWeighted(result, 1 - alpha, rotated, alpha, 0)
        
        return result
    
    def _apply_particle_system(self, image: np.ndarray, audio_features: Dict, current_time: float) -> np.ndarray:
        """Apply dynamic particle system effect."""
        h, w = image.shape[:2]
        particles = np.zeros_like(image)
        energy = audio_features.get('rms_energy', 0.5)
        
        # Generate energy-based particles
        num_particles = int(50 + energy * 100)
        
        for i in range(num_particles):
            # Particle position (spiraling outward)
            angle = (current_time * 200 + i * 137.5) % 360  # Golden angle spiral
            radius = (i / num_particles) * min(w, h) * 0.4
            
            center_x, center_y = w // 2, h // 2
            particle_x = int(center_x + radius * np.cos(np.radians(angle)))
            particle_y = int(center_y + radius * np.sin(np.radians(angle)))
            
            if 0 <= particle_x < w and 0 <= particle_y < h:
                # Particle color based on position and time
                hue = (angle + current_time * 60) % 360
                color = self._hsv_to_rgb(hue, 1.0, energy)
                
                # Draw particle with glow
                particle_size = max(2, int(energy * 6))
                cv2.circle(particles, (particle_x, particle_y), particle_size, color, -1)
        
        # Blur particles for glow effect
        particles = cv2.GaussianBlur(particles, (11, 11), 0)
        
        # Blend with image
        return cv2.addWeighted(image, 1.0, particles, 0.4 * energy, 0)
    
    def _apply_psychedelic_waves(self, image: np.ndarray, current_time: float, energy: float) -> np.ndarray:
        """Apply psychedelic wave distortion."""
        h, w = image.shape[:2]
        
        # Create complex wave displacement
        x_map = np.zeros((h, w), dtype=np.float32)
        y_map = np.zeros((h, w), dtype=np.float32)
        
        wave_intensity = energy * 20
        time_factor = current_time * 2
        
        for y in range(h):
            for x in range(w):
                # Multiple overlapping sine waves
                wave1 = np.sin(2 * np.pi * x / (w * 0.1) + time_factor) * wave_intensity
                wave2 = np.sin(2 * np.pi * y / (h * 0.1) + time_factor * 1.3) * wave_intensity
                wave3 = np.sin(2 * np.pi * (x + y) / (max(w, h) * 0.05) + time_factor * 0.7) * wave_intensity * 0.5
                
                x_map[y, x] = x + wave1 + wave3
                y_map[y, x] = y + wave2 + wave3
        
        return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    def _apply_extreme_rainbow_effect(self, image: np.ndarray, current_time: float, energy: float) -> np.ndarray:
        """Apply extreme rainbow color cycling."""
        if image.shape[2] < 4:
            return image
            
        result = image.copy()
        alpha = image[:, :, 3]
        text_mask = alpha > 0
        
        if not np.any(text_mask):
            return image
        
        # Create rainbow gradient across the text
        h, w = result.shape[:2]
        for y in range(h):
            for x in range(w):
                if text_mask[y, x]:
                    # Position-based hue with time animation
                    position_hue = (x / w * 360 + y / h * 180 + current_time * 120) % 360
                    rainbow_color = self._hsv_to_rgb(position_hue, 1.0, 1.0)
                    
                    # Blend with original color
                    blend_factor = 0.5 + energy * 0.5
                    for c in range(3):
                        result[y, x, c] = int(result[y, x, c] * (1 - blend_factor) + rainbow_color[c] * blend_factor)
        
        return result
    
    def _apply_visual_overload(self, image: np.ndarray, audio_features: Dict, current_time: float) -> np.ndarray:
        """Apply maximum visual overload for extreme energy moments."""
        result = image.copy().astype(np.float32)
        energy = audio_features.get('rms_energy', 0.5)
        h, w = result.shape[:2]
        
        # SCREEN SHAKE SIMULATION
        shake_intensity = (energy - 0.8) * 10
        shake_x = int(np.sin(current_time * 50) * shake_intensity)
        shake_y = int(np.cos(current_time * 50) * shake_intensity)
        
        if abs(shake_x) > 0 or abs(shake_y) > 0:
            M = np.float32([[1, 0, shake_x], [0, 1, shake_y]])
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        
        # EXTREME BRIGHTNESS PULSE
        pulse_intensity = 1.0 + (energy - 0.8) * 2.0
        result *= pulse_intensity
        
        # CHAOS OVERLAY
        if audio_features.get('on_beat', False):
            chaos_overlay = np.random.random((h, w, 3)) * 100 * (energy - 0.8)
            result[:, :, :3] += chaos_overlay
        
        return result
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB color."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
        return (int(r*255), int(g*255), int(b*255))
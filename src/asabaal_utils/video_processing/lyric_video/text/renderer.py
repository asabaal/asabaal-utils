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
                           audio_features: Optional[Dict] = None) -> np.ndarray:
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
            
        return text_img
        
    def render_lyric_line(self, words: List[LyricWord], current_time: float,
                         style: TextStyle, animation_config: AnimationConfig,
                         line_start: float, line_end: float,
                         audio_features: Optional[Dict] = None) -> np.ndarray:
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
        # Create canvas
        canvas = np.zeros((self.resolution[1], self.resolution[0], 4), dtype=np.uint8)
        
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
                audio_features
            )
            
            word_images.append(word_img)
            total_width += word_img.shape[1] + 20  # Add spacing
            max_height = max(max_height, word_img.shape[0])
            
        # Remove last spacing
        total_width -= 20
        
        # Calculate starting position based on alignment
        if style.alignment == "center":
            x_pos = (self.resolution[0] - total_width) // 2
        elif style.alignment == "right":
            x_pos = self.resolution[0] - total_width - 50
        else:  # left
            x_pos = 50
            
        y_pos = (self.resolution[1] - max_height) // 2
        
        # Composite words onto canvas
        current_x = x_pos
        for word_img in word_images:
            h, w = word_img.shape[:2]
            
            # Calculate valid region
            if current_x >= 0 and current_x + w <= self.resolution[0]:
                # Simple case - word fits entirely
                self._composite_image(canvas, word_img, current_x, y_pos)
            else:
                # Word extends beyond canvas - clip it
                src_x1 = max(0, -current_x)
                src_x2 = min(w, self.resolution[0] - current_x)
                
                if src_x2 > src_x1:
                    word_region = word_img[:, src_x1:src_x2]
                    dest_x = max(0, current_x)
                    self._composite_image(canvas, word_region, dest_x, y_pos)
                    
            current_x += w + 20
            
        return canvas
        
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
                          effects_config: Dict) -> np.ndarray:
        """Apply additional text effects.
        
        Args:
            text_surface: Rendered text surface
            effects_config: Effects configuration
            
        Returns:
            Text with effects applied
        """
        result = text_surface.copy()
        
        # Apply wave distortion
        if effects_config.get('wave_effect', False):
            amplitude = effects_config.get('wave_amplitude', 10)
            frequency = effects_config.get('wave_frequency', 0.1)
            result = self._apply_wave_distortion(result, amplitude, frequency)
            
        # Apply chromatic aberration
        if effects_config.get('chromatic_aberration', False):
            offset = effects_config.get('aberration_offset', 3)
            result = self._apply_chromatic_aberration(result, offset)
            
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
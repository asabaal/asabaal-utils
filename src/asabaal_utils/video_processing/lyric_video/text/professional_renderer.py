"""
Compatible Professional Text Renderer that works with existing asabaal-utils system
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import math

# Compatibility imports - provide what the system expects
from ..text.renderer import TextRenderer, TextStyle
from ..text.animations import AnimationType, AnimationState

class ProfessionalTextStyle(Enum):
    """Professional text styles compatible with existing system"""
    MODERN_BOLD = "modern_bold"
    NEON_GLOW = "neon_glow" 
    ELEGANT_GOLD = "elegant_gold"
    HIP_HOP = "hip_hop"
    CLEAN_WHITE = "clean_white"
    DRAMATIC_RED = "dramatic_red"

@dataclass
class CharacterTransform:
    """Per-character transform state - compatibility stub"""
    position: Tuple[float, float]
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)
    opacity: float = 1.0

class KineticTypography:
    """Compatibility stub for kinetic typography"""
    def __init__(self):
        self.character_states = []

class PrecisionSyncSystem:
    """Compatibility stub for precision sync"""
    def __init__(self):
        pass

class TextPath:
    """Compatibility stub for text path"""
    def __init__(self):
        pass

class AdvancedTextLayout:
    """Compatibility stub for advanced layout"""
    def __init__(self):
        pass

class Transform3D:
    """Compatibility stub for 3D transform"""
    def __init__(self):
        pass

class Timeline:
    """Compatibility stub for timeline"""
    def __init__(self):
        pass

def create_professional_config(text=None, style=None, duration=None, **kwargs):
    """Create professional config - compatibility function"""
    return {
        'style': {
            'kinetic_enabled': False,
            'kinetic_animation': 'wave',
            'path_animation': None,
            'transform_3d': None
        },
        'text': text or '',
        'duration': duration or 1.0
    }

class ProfessionalTextRenderer:
    """
    Professional Text Renderer - IMPROVED VERSION
    Compatible with existing asabaal-utils system
    """
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080)):
        self.width, self.height = resolution
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        
        # Professional font settings
        self.fonts = {
            'primary': cv2.FONT_HERSHEY_TRIPLEX,
            'bold': cv2.FONT_HERSHEY_DUPLEX,
            'elegant': cv2.FONT_HERSHEY_COMPLEX
        }
        
    def render_word(self, word: str, style: ProfessionalTextStyle = ProfessionalTextStyle.MODERN_BOLD,
                   font_size: float = 120, position: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        Render a single word with professional styling
        """
        # Normalize text to fix encoding issues with apostrophes and quotes
        word = self._normalize_text_encoding(word)
        
        # Create frame with alpha channel
        frame = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        
        # Style configurations
        style_config = self._get_style_config(style, font_size)
        
        # Calculate text metrics
        font = style_config['font']
        thickness = style_config['thickness']
        scale = style_config['scale']
        
        (text_width, text_height), baseline = cv2.getTextSize(word, font, scale, thickness)
        
        # Position calculation
        if position:
            x, y = position
        else:
            # Center text
            x = (self.width - text_width) // 2
            y = (self.height + text_height) // 2
        
        # Render layers (back to front)
        self._render_shadow(frame, word, (x, y), style_config)
        self._render_glow(frame, word, (x, y), style_config)  
        self._render_outline(frame, word, (x, y), style_config)
        self._render_fill(frame, word, (x, y), style_config)
        
        return frame
    
    def render_lyric_line(self, words, current_time: float, style, 
                         animation_config, line_start: float, line_end: float,
                         audio_features=None, effects_config=None) -> np.ndarray:
        """
        Main method expected by existing system - render lyric line professionally
        
        Args:
            words: List of LyricWord objects  
            current_time: Current timestamp
            style: TextStyle object
            animation_config: Animation configuration
            line_start: Line start time
            line_end: Line end time
            audio_features: Optional audio features
            effects_config: Optional effects config
            
        Returns:
            RGBA image with rendered line
        """
        # Create frame with alpha channel
        frame = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        
        # Find the active word at current time
        active_word = None
        active_text = ""
        
        for word in words:
            # Check if this word should be displayed at current time
            if hasattr(word, 'start_time') and hasattr(word, 'end_time'):
                if word.start_time <= current_time <= word.end_time:
                    active_word = word
                    active_text = word.text
                    break
            elif hasattr(word, 'text'):
                # Fallback - just use the first word with text
                active_text = word.text
                break
        
        if not active_text and words:
            # Ultimate fallback - use first word
            active_text = getattr(words[0], 'text', str(words[0]))
        
        if active_text:
            # Normalize text to fix encoding issues with apostrophes and quotes
            active_text = self._normalize_text_encoding(active_text)
            
            # Convert TextStyle to our ProfessionalTextStyle
            prof_style = ProfessionalTextStyle.MODERN_BOLD
            
            if hasattr(style, 'font_family') and style.font_family:
                font_family = style.font_family.lower()
                if 'neon' in font_family or 'glow' in font_family:
                    prof_style = ProfessionalTextStyle.NEON_GLOW
                elif 'gold' in font_family or 'elegant' in font_family:
                    prof_style = ProfessionalTextStyle.ELEGANT_GOLD
                elif 'hip' in font_family or 'bold' in font_family:
                    prof_style = ProfessionalTextStyle.HIP_HOP
                elif 'red' in font_family or 'dramatic' in font_family:
                    prof_style = ProfessionalTextStyle.DRAMATIC_RED
            
            # Get font size from style
            font_size = getattr(style, 'font_size', 120)
            
            # Render the active word with professional styling
            word_frame = self.render_word(active_text, prof_style, font_size)
            
            # Copy to main frame
            frame = word_frame
        
        return frame
    
    def setup_from_config(self, config):
        """Setup method expected by existing system"""
        # Store config for potential use
        self.config = config
    
    def render_text_professional(self, text: str, style: TextStyle, 
                               animation_progress: float = 1.0, **kwargs) -> np.ndarray:
        """
        Compatibility method for professional text rendering
        """
        font_size = getattr(style, 'font_size', 120)
        return self.render_word(text, ProfessionalTextStyle.MODERN_BOLD, font_size)
        
    def _get_style_config(self, style: ProfessionalTextStyle, font_size: float) -> Dict[str, Any]:
        """Get configuration for a text style"""
        
        # Base scale calculation
        base_scale = font_size / 80.0  # 80px as reference
        
        configs = {
            ProfessionalTextStyle.MODERN_BOLD: {
                'font': self.fonts['bold'],
                'scale': base_scale * 1.2,
                'thickness': max(3, int(base_scale * 4)),
                'fill_color': (255, 255, 255, 255),  # White
                'outline_color': (0, 0, 0, 255),     # Black
                'shadow_color': (0, 0, 0, 180),      # Semi-transparent black
                'glow_color': None,
                'shadow_offset': (4, 4),
                'outline_thickness': 2
            },
            
            ProfessionalTextStyle.NEON_GLOW: {
                'font': self.fonts['primary'],
                'scale': base_scale * 1.1,
                'thickness': max(2, int(base_scale * 3)),
                'fill_color': (255, 255, 255, 255),  # White core
                'outline_color': (255, 0, 255, 255), # Magenta outline
                'shadow_color': None,
                'glow_color': (255, 0, 255, 120),    # Magenta glow
                'shadow_offset': (0, 0),
                'outline_thickness': 1,
                'glow_radius': 15
            },
            
            ProfessionalTextStyle.ELEGANT_GOLD: {
                'font': self.fonts['elegant'],
                'scale': base_scale,
                'thickness': max(2, int(base_scale * 3)),
                'fill_color': (0, 215, 255, 255),    # Gold
                'outline_color': (0, 100, 150, 255), # Dark gold
                'shadow_color': (0, 0, 0, 200),      # Black shadow
                'glow_color': (0, 255, 255, 60),     # Subtle gold glow
                'shadow_offset': (3, 3),
                'outline_thickness': 2,
                'glow_radius': 8
            },
            
            ProfessionalTextStyle.HIP_HOP: {
                'font': self.fonts['bold'],
                'scale': base_scale * 1.3,
                'thickness': max(4, int(base_scale * 5)),
                'fill_color': (0, 255, 255, 255),    # Yellow
                'outline_color': (0, 0, 0, 255),     # Black thick outline
                'shadow_color': (128, 0, 128, 150),  # Purple shadow
                'glow_color': None,
                'shadow_offset': (6, 6),
                'outline_thickness': 3
            },
            
            ProfessionalTextStyle.CLEAN_WHITE: {
                'font': self.fonts['primary'],
                'scale': base_scale,
                'thickness': max(2, int(base_scale * 3)),
                'fill_color': (255, 255, 255, 255),  # Pure white
                'outline_color': (64, 64, 64, 255),  # Dark gray outline
                'shadow_color': (0, 0, 0, 120),      # Subtle shadow
                'glow_color': None,
                'shadow_offset': (2, 2),
                'outline_thickness': 1
            },
            
            ProfessionalTextStyle.DRAMATIC_RED: {
                'font': self.fonts['bold'],
                'scale': base_scale * 1.1,
                'thickness': max(3, int(base_scale * 4)),
                'fill_color': (0, 0, 255, 255),      # Red
                'outline_color': (0, 0, 139, 255),   # Dark red
                'shadow_color': (0, 0, 0, 200),      # Black shadow
                'glow_color': (0, 0, 255, 100),      # Red glow
                'shadow_offset': (4, 4),
                'outline_thickness': 2,
                'glow_radius': 10
            }
        }
        
        return configs.get(style, configs[ProfessionalTextStyle.CLEAN_WHITE])
    
    def _render_shadow(self, frame: np.ndarray, text: str, pos: Tuple[int, int], config: Dict):
        """Render drop shadow"""
        if not config['shadow_color']:
            return
            
        shadow_x = pos[0] + config['shadow_offset'][0]
        shadow_y = pos[1] + config['shadow_offset'][1]
        
        # Create shadow layer
        shadow_frame = np.zeros_like(frame)
        
        cv2.putText(shadow_frame, text, (shadow_x, shadow_y),
                   config['font'], config['scale'], config['shadow_color'], 
                   config['thickness'], cv2.LINE_AA)
        
        # Blur shadow for softer effect
        shadow_frame = cv2.GaussianBlur(shadow_frame, (7, 7), 2)
        
        # Composite shadow
        self._alpha_blend(frame, shadow_frame)
    
    def _render_glow(self, frame: np.ndarray, text: str, pos: Tuple[int, int], config: Dict):
        """Render glow effect"""
        if not config.get('glow_color'):
            return
            
        # Create glow layers with increasing thickness
        glow_radius = config.get('glow_radius', 10)
        
        for radius in range(glow_radius, 0, -2):
            glow_frame = np.zeros_like(frame)
            
            # Calculate alpha based on distance from center
            alpha = int(config['glow_color'][3] * (1.0 - (radius / glow_radius)))
            glow_color = (*config['glow_color'][:3], alpha)
            
            cv2.putText(glow_frame, text, pos,
                       config['font'], config['scale'], glow_color,
                       config['thickness'] + radius, cv2.LINE_AA)
            
            # Blur for glow effect
            glow_frame = cv2.GaussianBlur(glow_frame, (radius*2 + 1, radius*2 + 1), radius/3)
            
            # Composite glow
            self._alpha_blend(frame, glow_frame)
    
    def _render_outline(self, frame: np.ndarray, text: str, pos: Tuple[int, int], config: Dict):
        """Render text outline"""
        if config['outline_thickness'] > 0:
            outline_thickness = config['thickness'] + config['outline_thickness'] * 2
            
            cv2.putText(frame, text, pos,
                       config['font'], config['scale'], config['outline_color'],
                       outline_thickness, cv2.LINE_AA)
    
    def _render_fill(self, frame: np.ndarray, text: str, pos: Tuple[int, int], config: Dict):
        """Render main text fill"""
        cv2.putText(frame, text, pos,
                   config['font'], config['scale'], config['fill_color'],
                   config['thickness'], cv2.LINE_AA)
    
    def _alpha_blend(self, dest: np.ndarray, src: np.ndarray):
        """Alpha blend source onto destination"""
        if src.shape[2] == 4:  # Has alpha channel
            alpha = src[:, :, 3:4] / 255.0
            dest[:, :, :3] = dest[:, :, :3] * (1 - alpha) + src[:, :, :3] * alpha
            dest[:, :, 3:4] = np.maximum(dest[:, :, 3:4], src[:, :, 3:4])
    
    def _normalize_text_encoding(self, text: str) -> str:
        """Normalize text to fix encoding issues with apostrophes, quotes, and special characters.
        
        This function converts problematic Unicode characters that can cause ???? symbols
        when rendered in videos to their safe ASCII equivalents.
        
        Args:
            text: Input text that may contain problematic characters
            
        Returns:
            Normalized text with safe character replacements
        """
        if not text:
            return text
            
        # Dictionary of problematic characters and their safe replacements
        char_replacements = {
            # Various apostrophe and quote characters (using Unicode escape codes for reliability)
            '\u2019': "'",    # Right single quotation mark (U+2019) - most common cause
            '\u2018': "'",    # Left single quotation mark (U+2018)
            '\u201C': '"',    # Left double quotation mark (U+201C)
            '\u201D': '"',    # Right double quotation mark (U+201D)
            '\u201A': "'",    # Single low-9 quotation mark (U+201A)
            '\u201E': '"',    # Double low-9 quotation mark (U+201E)
            '‹': '<',    # Single left-pointing angle quotation mark (U+2039)
            '›': '>',    # Single right-pointing angle quotation mark (U+203A)
            '«': '"',    # Left-pointing double angle quotation mark (U+00AB)
            '»': '"',    # Right-pointing double angle quotation mark (U+00BB)
            
            # Dashes
            '–': '-',    # En dash (U+2013)
            '—': '-',    # Em dash (U+2014)
            '―': '-',    # Horizontal bar (U+2015)
            
            # Other problematic characters
            '…': '...',  # Horizontal ellipsis (U+2026)
            '′': "'",    # Prime (U+2032)
            '″': '"',    # Double prime (U+2033)
            '‛': "'",    # Single high-reversed-9 quotation mark (U+201B)
        }
        
        # Apply character replacements
        normalized_text = text
        for problem_char, replacement in char_replacements.items():
            normalized_text = normalized_text.replace(problem_char, replacement)
        
        # Ensure the text is properly UTF-8 encoded
        try:
            # Try to encode/decode to catch any remaining encoding issues
            normalized_text = normalized_text.encode('utf-8', errors='replace').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            # If there are still encoding issues, fall back to ASCII-safe version
            normalized_text = normalized_text.encode('ascii', errors='replace').decode('ascii')
            
        return normalized_text
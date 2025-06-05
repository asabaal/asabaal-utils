"""Font management and caching system."""

import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import logging
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class FontManager:
    """Manages font loading and caching."""
    
    def __init__(self):
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        self.system_fonts = self._discover_system_fonts()
        
    def _discover_system_fonts(self) -> Dict[str, str]:
        """Discover available system fonts."""
        fonts = {}
        
        # Common font directories
        font_dirs = []
        
        if os.name == 'posix':  # Linux/Mac
            font_dirs.extend([
                '/usr/share/fonts',
                '/usr/local/share/fonts',
                '/System/Library/Fonts',  # macOS
                '~/.fonts',
                '~/.local/share/fonts'
            ])
        elif os.name == 'nt':  # Windows
            font_dirs.extend([
                'C:\\Windows\\Fonts',
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
            ])
            
        # Scan directories for font files
        for font_dir in font_dirs:
            font_path = Path(font_dir).expanduser()
            if font_path.exists():
                for font_file in font_path.rglob('*.ttf'):
                    font_name = font_file.stem
                    fonts[font_name] = str(font_file)
                for font_file in font_path.rglob('*.otf'):
                    font_name = font_file.stem
                    fonts[font_name] = str(font_file)
                    
        logger.info(f"Discovered {len(fonts)} system fonts")
        return fonts
        
    def get_font(self, font_family: str, font_size: int) -> ImageFont.FreeTypeFont:
        """Get font object, loading from cache if available.
        
        Args:
            font_family: Font family name or path
            font_size: Font size in points
            
        Returns:
            PIL font object
        """
        cache_key = f"{font_family}_{font_size}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
            
        # Try to load font
        font = None
        
        # First try as direct path
        if os.path.exists(font_family):
            try:
                font = ImageFont.truetype(font_family, font_size)
                logger.info(f"Loaded font from path: {font_family}")
            except Exception as e:
                logger.error(f"Failed to load font from path {font_family}: {e}")
                
        # Try system fonts
        if font is None and font_family in self.system_fonts:
            try:
                font = ImageFont.truetype(self.system_fonts[font_family], font_size)
                logger.info(f"Loaded system font: {font_family}")
            except Exception as e:
                logger.error(f"Failed to load system font {font_family}: {e}")
                
        # Try common font names
        if font is None:
            common_fonts = {
                'Arial': ['Arial', 'arial', 'ArialMT'],
                'Helvetica': ['Helvetica', 'helvetica'],
                'Times': ['Times', 'times', 'Times New Roman'],
                'Courier': ['Courier', 'courier', 'Courier New']
            }
            
            for base_name, variants in common_fonts.items():
                if font_family.lower().startswith(base_name.lower()):
                    for variant in variants:
                        if variant in self.system_fonts:
                            try:
                                font = ImageFont.truetype(self.system_fonts[variant], font_size)
                                logger.info(f"Loaded font variant: {variant}")
                                break
                            except:
                                continue
                if font:
                    break
                    
        # Fallback to default
        if font is None:
            logger.warning(f"Font {font_family} not found, using default")
            font = ImageFont.load_default()
            
        self.font_cache[cache_key] = font
        return font
        
    def render_text(self, text: str, font: ImageFont.FreeTypeFont,
                   color: Tuple[int, int, int] = (255, 255, 255),
                   stroke_width: int = 0,
                   stroke_color: Tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
        """Render text to numpy array.
        
        Args:
            text: Text to render
            font: Font object
            color: Text color (R, G, B)
            stroke_width: Stroke width in pixels
            stroke_color: Stroke color (R, G, B)
            
        Returns:
            RGBA numpy array
        """
        # Get text size
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0] + stroke_width * 2 + 10
        height = bbox[3] - bbox[1] + stroke_width * 2 + 10
        
        # Create RGBA image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate position
        x = stroke_width + 5
        y = stroke_width + 5
        
        # Draw text with stroke
        if stroke_width > 0:
            draw.text((x, y), text, font=font, fill=stroke_color, 
                     stroke_width=stroke_width, stroke_fill=stroke_color)
            
        # Draw main text
        draw.text((x, y), text, font=font, fill=color)
        
        # Convert to numpy array
        return np.array(img)
        
    def measure_text(self, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
        """Measure text dimensions.
        
        Args:
            text: Text to measure
            font: Font object
            
        Returns:
            (width, height) tuple
        """
        bbox = font.getbbox(text)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        
    def render_text_with_effects(self, text: str, font_family: str, font_size: int,
                               color: Tuple[int, int, int] = (255, 255, 255),
                               stroke_width: int = 0,
                               stroke_color: Tuple[int, int, int] = (0, 0, 0),
                               shadow_offset: Optional[Tuple[int, int]] = None,
                               shadow_blur: int = 0,
                               shadow_opacity: float = 0.5,
                               glow_radius: int = 0,
                               glow_color: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
        """Render text with multiple effects.
        
        Args:
            text: Text to render
            font_family: Font family name
            font_size: Font size
            color: Text color
            stroke_width: Stroke width
            stroke_color: Stroke color
            shadow_offset: Shadow offset (x, y)
            shadow_blur: Shadow blur radius
            shadow_opacity: Shadow opacity
            glow_radius: Glow effect radius
            glow_color: Glow color (defaults to text color)
            
        Returns:
            RGBA numpy array with effects
        """
        # Get font
        font = self.get_font(font_family, font_size)
        
        # Render base text
        text_img = self.render_text(text, font, color, stroke_width, stroke_color)
        
        # Calculate total canvas size
        h, w = text_img.shape[:2]
        total_h = h
        total_w = w
        
        if shadow_offset:
            total_h += abs(shadow_offset[1]) + shadow_blur * 2
            total_w += abs(shadow_offset[0]) + shadow_blur * 2
            
        if glow_radius > 0:
            total_h += glow_radius * 4
            total_w += glow_radius * 4
            
        # Create canvas
        canvas = np.zeros((total_h, total_w, 4), dtype=np.uint8)
        
        # Calculate base position
        base_x = (total_w - w) // 2
        base_y = (total_h - h) // 2
        
        # Apply shadow if requested
        if shadow_offset:
            shadow_x = base_x + shadow_offset[0]
            shadow_y = base_y + shadow_offset[1]
            
            # Create shadow
            shadow = text_img.copy()
            shadow[:, :, :3] = 0  # Make black
            shadow[:, :, 3] = (shadow[:, :, 3] * shadow_opacity).astype(np.uint8)
            
            # Blur shadow
            if shadow_blur > 0:
                shadow = cv2.GaussianBlur(shadow, (shadow_blur*2+1, shadow_blur*2+1), 0)
                
            # Composite shadow
            self._composite_over(canvas, shadow, shadow_x, shadow_y)
            
        # Apply glow if requested
        if glow_radius > 0:
            glow_color = glow_color or color
            
            # Create multiple glow layers
            for i in range(glow_radius, 0, -1):
                glow = text_img.copy()
                glow[:, :, :3] = glow_color
                glow[:, :, 3] = (glow[:, :, 3] * (0.5 / glow_radius * i)).astype(np.uint8)
                
                # Blur glow
                blur_size = i * 2 + 1
                glow = cv2.GaussianBlur(glow, (blur_size, blur_size), 0)
                
                # Composite glow
                self._composite_over(canvas, glow, base_x, base_y)
                
        # Composite main text
        self._composite_over(canvas, text_img, base_x, base_y)
        
        return canvas
        
    def _composite_over(self, base: np.ndarray, overlay: np.ndarray, x: int, y: int):
        """Composite overlay onto base at position.
        
        Args:
            base: Base image (modified in place)
            overlay: Overlay image
            x: X position
            y: Y position
        """
        h, w = overlay.shape[:2]
        base_h, base_w = base.shape[:2]
        
        # Calculate valid region
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(base_w, x + w)
        y2 = min(base_h, y + h)
        
        if x2 <= x1 or y2 <= y1:
            return
            
        # Get regions
        base_region = base[y1:y2, x1:x2]
        overlay_region = overlay[y1-y:y2-y, x1-x:x2-x]
        
        # Alpha composite
        alpha = overlay_region[:, :, 3:4] / 255.0
        base_region[:] = (alpha * overlay_region + (1 - alpha) * base_region).astype(np.uint8)
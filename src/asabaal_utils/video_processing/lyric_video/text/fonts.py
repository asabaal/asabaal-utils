"""Font management and caching system."""

import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import logging
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
from .font_loader import EnhancedFontLoader
from .font_generator import BespokeFontGenerator

logger = logging.getLogger(__name__)


class FontManager:
    """Manages font loading and caching."""
    
    def __init__(self):
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        self.font_loader = EnhancedFontLoader()
        self.font_generator = BespokeFontGenerator()
        self.system_fonts = self._discover_system_fonts()
        
        # Auto-download popular fonts on first use
        self._ensure_popular_fonts()
        
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
            
        # Use enhanced font loader
        font = self.font_loader.load_font(font_family, font_size)
        
        # If font loader returns None, create a large bitmap font as fallback
        if font is None:
            logger.error(f"Font {font_family} not available, creating emergency fallback")
            # Instead of using the tiny default font, we'll create a basic large font
            # by using the first available TrueType font at the requested size
            available_fonts = self.font_loader.list_available_fonts()
            if available_fonts:
                # Try to load any available font at the requested size
                for fallback_name in ["DejaVuSans", "Ubuntu-R", "DejaVuSans-Bold"]:
                    if fallback_name in available_fonts:
                        font = self.font_loader.load_font(fallback_name, font_size)
                        if font:
                            logger.warning(f"Using {fallback_name} as emergency fallback")
                            break
            
            # Absolute last resort - but we should never get here with the enhanced loader
            if font is None:
                font = ImageFont.load_default()
                logger.error("WARNING: Using tiny default font - text will be very small!")
        
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
        
        # Use full font height (ascent + descent) instead of just bbox height
        # This prevents cutoff of characters with descenders (g, j, p, q, y)
        ascent, descent = font.getmetrics()
        height = ascent + descent + stroke_width * 2 + 10
        
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
    
    def _ensure_popular_fonts(self):
        """Ensure popular fonts are available, downloading if needed."""
        try:
            # Try to download popular fonts in background
            self.font_loader.auto_download_popular_fonts()
        except Exception as e:
            logger.debug(f"Could not auto-download fonts: {e}")
    
    def render_bespoke_text(self, text: str, style: str, size: int = 72) -> np.ndarray:
        """Render text using bespoke font generation.
        
        Args:
            text: Text to render
            style: Bespoke style (neon, graffiti, chrome, fire, etc.)
            size: Font size
            
        Returns:
            RGBA numpy array with stylized text
        """
        return self.font_generator.generate_stylized_text(text, style, size)
    
    def get_available_font_styles(self) -> Dict[str, List[str]]:
        """Get all available font styles categorized.
        
        Returns:
            Dictionary with categories and their fonts
        """
        styles = {
            "System Fonts": list(self.system_fonts.keys()),
            "Downloaded Fonts": self.font_loader.list_available_fonts(),
            "Font Categories": self.font_loader.get_all_categories(),
            "Bespoke Styles": self.font_generator.list_available_styles()
        }
        return styles
    
    def suggest_font_for_genre(self, genre: str) -> str:
        """Suggest font based on music genre.
        
        Args:
            genre: Music genre (rock, pop, classical, electronic, etc.)
            
        Returns:
            Suggested font name
        """
        genre_lower = genre.lower()
        
        if any(word in genre_lower for word in ['rock', 'metal', 'punk', 'grunge']):
            return "Bebas Neue"  # Bold impact for rock
        elif any(word in genre_lower for word in ['pop', 'dance', 'electronic', 'edm']):
            return "Montserrat Bold"  # Modern for pop/electronic
        elif any(word in genre_lower for word in ['classical', 'opera', 'symphony']):
            return "Playfair Display"  # Elegant for classical
        elif any(word in genre_lower for word in ['jazz', 'blues', 'soul']):
            return "Dancing Script"  # Smooth script for jazz
        elif any(word in genre_lower for word in ['hip-hop', 'rap', 'urban']):
            return "Oswald Bold"  # Strong display for hip-hop
        elif any(word in genre_lower for word in ['indie', 'alternative', 'folk']):
            return "Open Sans"  # Clean modern for indie
        elif any(word in genre_lower for word in ['country', 'americana', 'western']):
            return "Merriweather"  # Traditional serif
        elif any(word in genre_lower for word in ['techno', 'synthwave', 'cyberpunk']):
            return "Orbitron"  # Futuristic for electronic
        else:
            return "Righteous"  # Good all-around display font
    
    def suggest_bespoke_style_for_mood(self, mood: str) -> str:
        """Suggest bespoke style based on song mood.
        
        Args:
            mood: Song mood (energetic, calm, mysterious, etc.)
            
        Returns:
            Suggested bespoke style name
        """
        mood_lower = mood.lower()
        
        if any(word in mood_lower for word in ['energetic', 'high-energy', 'exciting', 'party']):
            return "neon"  # Bright and energetic
        elif any(word in mood_lower for word in ['mysterious', 'dark', 'atmospheric']):
            return "matrix"  # Digital/mysterious
        elif any(word in mood_lower for word in ['romantic', 'love', 'emotional']):
            return "gold"  # Warm and luxurious
        elif any(word in mood_lower for word in ['cool', 'chill', 'calm', 'peaceful']):
            return "ice"  # Cool and calm
        elif any(word in mood_lower for word in ['intense', 'powerful', 'aggressive']):
            return "fire"  # Intense and powerful
        elif any(word in mood_lower for word in ['futuristic', 'sci-fi', 'space']):
            return "hologram"  # Sci-fi effect
        elif any(word in mood_lower for word in ['urban', 'street', 'gritty']):
            return "graffiti"  # Street style
        elif any(word in mood_lower for word in ['elegant', 'classy', 'luxury']):
            return "chrome"  # Metallic luxury
        else:
            return "basic"  # Colorful fallback
    
    def get_font_recommendations(self, text: str, genre: str = None, mood: str = None) -> Dict[str, str]:
        """Get comprehensive font recommendations.
        
        Args:
            text: Text to be rendered
            genre: Optional music genre
            mood: Optional song mood
            
        Returns:
            Dictionary with different font recommendations
        """
        recommendations = {}
        
        # Basic recommendations
        recommendations["modern"] = "Montserrat Bold"
        recommendations["classic"] = "Playfair Display"
        recommendations["bold"] = "Bebas Neue"
        recommendations["elegant"] = "Dancing Script"
        
        # Genre-based recommendation
        if genre:
            recommendations["genre_match"] = self.suggest_font_for_genre(genre)
        
        # Mood-based bespoke style
        if mood:
            recommendations["bespoke_style"] = self.suggest_bespoke_style_for_mood(mood)
        
        # Text length based
        if len(text.split()) > 10:  # Long text
            recommendations["readability"] = "Open Sans"
        else:  # Short text
            recommendations["impact"] = "Anton"
        
        return recommendations
    
    def list_downloadable_fonts_by_category(self) -> Dict[str, List[str]]:
        """List downloadable fonts organized by category."""
        categories = {}
        for category in self.font_loader.get_all_categories():
            categories[category] = self.font_loader.get_fonts_by_category(category)
        return categories
    
    def download_fonts_for_style(self, style: str) -> List[str]:
        """Download fonts that match a particular style.
        
        Args:
            style: Style description (modern, bold, elegant, etc.)
            
        Returns:
            List of downloaded font paths
        """
        style_lower = style.lower()
        downloaded = []
        
        # Map styles to categories
        if "modern" in style_lower:
            downloaded.extend(self.font_loader.download_fonts_by_category("modern"))
        if "bold" in style_lower or "impact" in style_lower:
            downloaded.extend(self.font_loader.download_fonts_by_category("impact"))
            downloaded.extend(self.font_loader.download_fonts_by_category("display"))
        if "elegant" in style_lower:
            downloaded.extend(self.font_loader.download_fonts_by_category("elegant"))
            downloaded.extend(self.font_loader.download_fonts_by_category("script"))
        if "tech" in style_lower or "futuristic" in style_lower:
            downloaded.extend(self.font_loader.download_fonts_by_category("tech"))
        
        return downloaded
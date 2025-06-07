"""Procedural font generation for custom artistic fonts."""

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, Optional, List
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class BespokeFontGenerator:
    """Generate custom artistic fonts procedurally."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize font generator.
        
        Args:
            cache_dir: Directory to cache generated fonts
        """
        self.cache_dir = Path(cache_dir or "~/.cache/lyric_video_fonts/generated").expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_stylized_text(self, text: str, style: str, size: int = 72) -> np.ndarray:
        """Generate stylized text with custom effects.
        
        Args:
            text: Text to render
            style: Style name (neon, graffiti, chrome, fire, etc.)
            size: Base font size
            
        Returns:
            RGBA numpy array with stylized text
        """
        if style == "neon":
            return self._generate_neon_text(text, size)
        elif style == "graffiti":
            return self._generate_graffiti_text(text, size)
        elif style == "chrome":
            return self._generate_chrome_text(text, size)
        elif style == "fire":
            return self._generate_fire_text(text, size)
        elif style == "ice":
            return self._generate_ice_text(text, size)
        elif style == "gold":
            return self._generate_gold_text(text, size)
        elif style == "hologram":
            return self._generate_hologram_text(text, size)
        elif style == "matrix":
            return self._generate_matrix_text(text, size)
        else:
            # Fallback to basic stylized text
            return self._generate_basic_stylized_text(text, size)
    
    def _generate_neon_text(self, text: str, size: int) -> np.ndarray:
        """Generate neon-style text with glowing edges."""
        # Create base text with bold font
        base_img = self._create_base_text(text, size * 1.2, bold=True)
        h, w = base_img.shape[:2]
        
        # Create larger canvas for glow
        canvas_h, canvas_w = h + 100, w + 100
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        
        # Position base text in center
        offset_x, offset_y = 50, 50
        
        # Create multiple glow layers
        colors = [
            (255, 0, 255),   # Bright magenta core
            (255, 100, 255), # Pink glow
            (200, 0, 200),   # Purple outer glow
            (100, 0, 100)    # Dark purple far glow
        ]
        
        blur_sizes = [3, 8, 15, 25]
        intensities = [1.0, 0.8, 0.6, 0.4]
        
        for color, blur_size, intensity in zip(colors, blur_sizes, intensities):
            # Create colored glow layer
            glow_layer = base_img.copy()
            
            # Color the glow
            mask = glow_layer[:, :, 3] > 0
            glow_layer[mask, :3] = color
            glow_layer[mask, 3] = (glow_layer[mask, 3] * intensity).astype(np.uint8)
            
            # Blur the glow
            if blur_size > 1:
                glow_layer = cv2.GaussianBlur(glow_layer, (blur_size*2+1, blur_size*2+1), 0)
            
            # Composite onto canvas
            self._composite_over(canvas, glow_layer, offset_x, offset_y)
        
        # Add the main text on top with bright color
        main_text = base_img.copy()
        mask = main_text[:, :, 3] > 0
        main_text[mask, :3] = (255, 255, 255)  # Bright white core
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _generate_graffiti_text(self, text: str, size: int) -> np.ndarray:
        """Generate graffiti-style text with outlines and shadows."""
        # Create base text
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        # Create larger canvas
        canvas_h, canvas_w = h + 60, w + 60
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 30, 30
        
        # Create shadow (offset)
        shadow = base_img.copy()
        shadow_mask = shadow[:, :, 3] > 0
        shadow[shadow_mask, :3] = (0, 0, 0)  # Black shadow
        shadow[shadow_mask, 3] = 150  # Semi-transparent
        self._composite_over(canvas, shadow, offset_x + 5, offset_y + 5)
        
        # Create thick outline
        outline_thickness = max(2, size // 20)
        outline = self._create_outline(base_img, outline_thickness)
        outline_mask = outline[:, :, 3] > 0
        outline[outline_mask, :3] = (0, 0, 0)  # Black outline
        self._composite_over(canvas, outline, offset_x, offset_y)
        
        # Main text with gradient colors
        main_text = base_img.copy()
        main_mask = main_text[:, :, 3] > 0
        
        # Create vertical gradient (red to yellow)
        for y in range(h):
            progress = y / h
            r = int(255 * (1 - progress * 0.3))  # Red to orange
            g = int(255 * progress)               # Black to yellow
            b = 0
            
            row_mask = main_mask[y, :]
            main_text[y, row_mask, :3] = (r, g, b)
        
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _generate_chrome_text(self, text: str, size: int) -> np.ndarray:
        """Generate chrome/metallic text with reflections."""
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        canvas_h, canvas_w = h + 40, w + 40
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 20, 20
        
        # Create metallic gradient
        main_text = base_img.copy()
        mask = main_text[:, :, 3] > 0
        
        # Chrome gradient (dark to light to dark)
        for y in range(h):
            progress = y / h
            # Create metallic curve
            metallic_value = int(80 + 120 * np.sin(progress * np.pi))
            
            row_mask = mask[y, :]
            main_text[y, row_mask, :3] = (metallic_value, metallic_value, metallic_value + 20)
        
        # Add highlights
        highlight_positions = [h // 4, 3 * h // 4]
        for highlight_y in highlight_positions:
            if highlight_y < h:
                row_mask = mask[highlight_y, :]
                main_text[highlight_y, row_mask, :3] = (255, 255, 255)
        
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _generate_fire_text(self, text: str, size: int) -> np.ndarray:
        """Generate fire-effect text."""
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        canvas_h, canvas_w = h + 80, w + 80
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 40, 40
        
        # Create fire gradient colors
        fire_colors = [
            (255, 0, 0),     # Red core
            (255, 100, 0),   # Orange
            (255, 200, 0),   # Yellow
            (255, 255, 100)  # Light yellow
        ]
        
        # Create multiple flame layers
        for i, color in enumerate(fire_colors):
            flame_layer = base_img.copy()
            mask = flame_layer[:, :, 3] > 0
            
            # Apply color
            flame_layer[mask, :3] = color
            
            # Add random distortion for flame effect
            if i > 0:
                # Create wavy distortion
                distortion = np.random.random((h, w)) * 0.3
                flame_layer = self._apply_wave_distortion(flame_layer, amplitude=i*2, frequency=0.1)
            
            # Blur outer layers more
            if i > 0:
                blur_size = i * 3 + 1
                flame_layer = cv2.GaussianBlur(flame_layer, (blur_size, blur_size), 0)
            
            self._composite_over(canvas, flame_layer, offset_x, offset_y)
        
        return canvas
    
    def _generate_ice_text(self, text: str, size: int) -> np.ndarray:
        """Generate ice-effect text."""
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        canvas_h, canvas_w = h + 60, w + 60
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 30, 30
        
        # Create ice gradient (blue to white)
        main_text = base_img.copy()
        mask = main_text[:, :, 3] > 0
        
        for y in range(h):
            progress = y / h
            # Ice gradient
            r = int(150 + 105 * progress)  # Light blue to white
            g = int(200 + 55 * progress)   
            b = 255
            
            row_mask = mask[y, :]
            main_text[y, row_mask, :3] = (r, g, b)
        
        # Add crystalline highlights
        for _ in range(h // 10):  # Random highlights
            highlight_y = np.random.randint(0, h)
            highlight_x = np.random.randint(0, w)
            if mask[highlight_y, highlight_x]:
                # Create small bright spot
                cv2.circle(main_text, (highlight_x, highlight_y), 2, (255, 255, 255, 255), -1)
        
        # Add cold blue glow
        glow = base_img.copy()
        glow_mask = glow[:, :, 3] > 0
        glow[glow_mask, :3] = (100, 150, 255)  # Cold blue
        glow[glow_mask, 3] = 80  # Semi-transparent
        glow = cv2.GaussianBlur(glow, (15, 15), 0)
        
        self._composite_over(canvas, glow, offset_x, offset_y)
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _generate_gold_text(self, text: str, size: int) -> np.ndarray:
        """Generate gold-effect text."""
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        canvas_h, canvas_w = h + 40, w + 40
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 20, 20
        
        # Create gold gradient
        main_text = base_img.copy()
        mask = main_text[:, :, 3] > 0
        
        for y in range(h):
            progress = y / h
            # Gold gradient
            r = int(200 + 55 * np.sin(progress * np.pi))  # Gold variation
            g = int(150 + 55 * np.sin(progress * np.pi))  
            b = int(50 + 30 * np.sin(progress * np.pi))
            
            row_mask = mask[y, :]
            main_text[y, row_mask, :3] = (r, g, b)
        
        # Add golden glow
        glow = base_img.copy()
        glow_mask = glow[:, :, 3] > 0
        glow[glow_mask, :3] = (255, 200, 50)  # Golden glow
        glow[glow_mask, 3] = 100
        glow = cv2.GaussianBlur(glow, (20, 20), 0)
        
        self._composite_over(canvas, glow, offset_x, offset_y)
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _generate_hologram_text(self, text: str, size: int) -> np.ndarray:
        """Generate hologram-effect text with scan lines."""
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        canvas_h, canvas_w = h + 40, w + 40
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 20, 20
        
        # Create hologram base
        main_text = base_img.copy()
        mask = main_text[:, :, 3] > 0
        
        # Hologram cyan color
        main_text[mask, :3] = (0, 255, 255)
        main_text[mask, 3] = 200  # Semi-transparent
        
        # Add scan lines
        for y in range(0, h, 3):  # Every 3rd line
            if y < h:
                row_mask = mask[y, :]
                main_text[y, row_mask, 3] = 100  # More transparent scan lines
        
        # Add hologram flicker effect (random transparency)
        noise = np.random.random((h, w)) * 0.3 + 0.7
        main_text[:, :, 3] = (main_text[:, :, 3] * noise).astype(np.uint8)
        
        # Add cyan glow
        glow = base_img.copy()
        glow_mask = glow[:, :, 3] > 0
        glow[glow_mask, :3] = (0, 255, 255)
        glow[glow_mask, 3] = 60
        glow = cv2.GaussianBlur(glow, (25, 25), 0)
        
        self._composite_over(canvas, glow, offset_x, offset_y)
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _generate_matrix_text(self, text: str, size: int) -> np.ndarray:
        """Generate Matrix-style green text effect."""
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        canvas_h, canvas_w = h + 60, w + 60
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 30, 30
        
        # Matrix green gradient
        main_text = base_img.copy()
        mask = main_text[:, :, 3] > 0
        
        for y in range(h):
            progress = y / h
            # Bright green at top, darker at bottom
            g = int(255 * (1 - progress * 0.5))
            
            row_mask = mask[y, :]
            main_text[y, row_mask, :3] = (0, g, 0)
        
        # Add digital distortion
        for _ in range(w // 20):  # Random digital artifacts
            artifact_x = np.random.randint(0, w)
            artifact_y = np.random.randint(0, h)
            if mask[artifact_y, artifact_x]:
                # Random bright green pixel
                main_text[artifact_y, artifact_x, :3] = (0, 255, 0)
        
        # Add green glow
        glow = base_img.copy()
        glow_mask = glow[:, :, 3] > 0
        glow[glow_mask, :3] = (0, 255, 0)
        glow[glow_mask, 3] = 80
        glow = cv2.GaussianBlur(glow, (15, 15), 0)
        
        self._composite_over(canvas, glow, offset_x, offset_y)
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _generate_basic_stylized_text(self, text: str, size: int) -> np.ndarray:
        """Generate basic stylized text with gradient and glow."""
        base_img = self._create_base_text(text, size, bold=True)
        h, w = base_img.shape[:2]
        
        canvas_h, canvas_w = h + 40, w + 40
        canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        offset_x, offset_y = 20, 20
        
        # Create rainbow gradient
        main_text = base_img.copy()
        mask = main_text[:, :, 3] > 0
        
        for x in range(w):
            progress = x / w
            # HSV to RGB for rainbow
            hue = progress * 360
            r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
            
            col_mask = mask[:, x]
            main_text[col_mask, x, :3] = (r, g, b)
        
        # Add colorful glow
        glow = base_img.copy()
        glow_mask = glow[:, :, 3] > 0
        glow[glow_mask, :3] = (255, 100, 255)  # Magenta glow
        glow[glow_mask, 3] = 100
        glow = cv2.GaussianBlur(glow, (20, 20), 0)
        
        self._composite_over(canvas, glow, offset_x, offset_y)
        self._composite_over(canvas, main_text, offset_x, offset_y)
        
        return canvas
    
    def _create_base_text(self, text: str, size: int, bold: bool = False) -> np.ndarray:
        """Create base text rendering."""
        try:
            # Try to use a good system font
            if bold:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size))
            else:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(size))
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Get text size
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0] + 20
        height = bbox[3] - bbox[1] + 20
        
        # Create image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw text
        draw.text((10, 10), text, font=font, fill=(255, 255, 255, 255))
        
        return np.array(img)
    
    def _create_outline(self, image: np.ndarray, thickness: int) -> np.ndarray:
        """Create outline from text image."""
        alpha = image[:, :, 3]
        
        # Dilate to create outline
        kernel = np.ones((thickness*2+1, thickness*2+1), np.uint8)
        outline_alpha = cv2.dilate(alpha, kernel, iterations=1)
        
        # Create outline image
        outline = np.zeros_like(image)
        outline[:, :, 3] = outline_alpha
        
        return outline
    
    def _apply_wave_distortion(self, image: np.ndarray, amplitude: float, frequency: float) -> np.ndarray:
        """Apply wave distortion to image."""
        h, w = image.shape[:2]
        
        # Create displacement map
        x_map = np.zeros((h, w), dtype=np.float32)
        y_map = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                x_map[y, x] = x + amplitude * np.sin(2 * np.pi * y * frequency / h)
                y_map[y, x] = y
        
        return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    
    def _composite_over(self, base: np.ndarray, overlay: np.ndarray, x: int, y: int):
        """Composite overlay onto base at position."""
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
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
        return (int(r*255), int(g*255), int(b*255))
    
    def list_available_styles(self) -> List[str]:
        """List all available bespoke font styles."""
        return [
            "neon",      # Bright glowing neon effect
            "graffiti",  # Street art style with outlines
            "chrome",    # Metallic reflective surface
            "fire",      # Flame effect with warm colors
            "ice",       # Cold crystalline effect
            "gold",      # Luxury golden effect
            "hologram",  # Sci-fi holographic effect
            "matrix",    # Digital rain effect
            "basic"      # Rainbow gradient with glow
        ]
    
    def get_style_description(self, style: str) -> str:
        """Get description of a font style."""
        descriptions = {
            "neon": "Bright glowing neon effect perfect for nightclub vibes",
            "graffiti": "Street art style with bold outlines and shadows",
            "chrome": "Metallic reflective surface for luxury feel",
            "fire": "Flame effect with warm colors for energy",
            "ice": "Cold crystalline effect for winter themes",
            "gold": "Luxury golden effect for premium content",
            "hologram": "Sci-fi holographic effect for futuristic themes",
            "matrix": "Digital rain effect for tech content",
            "basic": "Rainbow gradient with glow for general use"
        }
        return descriptions.get(style, "Custom stylized text effect")
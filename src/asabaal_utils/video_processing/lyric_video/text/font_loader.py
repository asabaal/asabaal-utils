"""Enhanced font loader with fallback support and custom font downloading."""

import os
import json
import logging
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from PIL import ImageFont

logger = logging.getLogger(__name__)


# Map common font names to available system fonts
FONT_MAPPINGS = {
    # Arial variants
    "Arial": ["DejaVuSans", "Ubuntu-R", "FreeSans", "LiberationSans-Regular"],
    "Arial Bold": ["DejaVuSans-Bold", "Ubuntu-B", "FreeSans-Bold", "LiberationSans-Bold"],
    "Arial Black": ["Ubuntu-B", "DejaVuSans-Bold", "FreeSans-Bold"],
    
    # Helvetica variants
    "Helvetica": ["DejaVuSans", "Ubuntu-R", "FreeSans"],
    
    # Times variants
    "Times": ["DejaVuSerif", "LiberationSerif-Regular", "FreeSerif"],
    "Times New Roman": ["DejaVuSerif", "LiberationSerif-Regular", "FreeSerif"],
    
    # Modern fonts
    "Ubuntu": ["Ubuntu-R", "DejaVuSans"],
    "DejaVu Sans": ["DejaVuSans", "Ubuntu-R"],
}

# Known font paths on different systems
KNOWN_FONT_PATHS = {
    "DejaVuSans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "DejaVuSans-Bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSerif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "Ubuntu-R": "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    "Ubuntu-B": "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "Ubuntu-L": "/usr/share/fonts/truetype/ubuntu/Ubuntu-L.ttf",
}

# Free fonts we can download - MASSIVE ARTISTIC COLLECTION
DOWNLOADABLE_FONTS = {
    # MODERN & CLEAN FONTS
    "OpenSans-Regular": {
        "url": "https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Regular.ttf",
        "fallback_name": "Open Sans",
        "category": "modern"
    },
    "OpenSans-Bold": {
        "url": "https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf",
        "fallback_name": "Open Sans Bold",
        "category": "modern"
    },
    "Roboto-Regular": {
        "url": "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf",
        "fallback_name": "Roboto",
        "category": "modern"
    },
    "Roboto-Bold": {
        "url": "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf",
        "fallback_name": "Roboto Bold",
        "category": "modern"
    },
    "Montserrat-Regular": {
        "url": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf",
        "fallback_name": "Montserrat",
        "category": "modern"
    },
    "Montserrat-Bold": {
        "url": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf",
        "fallback_name": "Montserrat Bold",
        "category": "modern"
    },
    
    # ARTISTIC & DISPLAY FONTS
    "Oswald-Regular": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf",
        "fallback_name": "Oswald",
        "category": "display"
    },
    "Oswald-Bold": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf",
        "fallback_name": "Oswald Bold",
        "category": "display"
    },
    "Playfair-Regular": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
        "fallback_name": "Playfair Display",
        "category": "elegant"
    },
    "Playfair-Bold": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
        "fallback_name": "Playfair Display Bold",
        "category": "elegant"
    },
    
    # IMPACT & BOLD FONTS
    "BebasNeue-Regular": {
        "url": "https://raw.githubusercontent.com/dharmatype/Bebas-Neue/master/fonts/BebasNeue(2018)ByDhamraType/ttf/BebasNeue-Regular.ttf",
        "fallback_name": "Bebas Neue",
        "category": "impact"
    },
    "Anton-Regular": {
        "url": "https://github.com/googlefonts/antonFont/raw/main/fonts/ttf/Anton-Regular.ttf",
        "fallback_name": "Anton",
        "category": "impact"
    },
    
    # SCRIPT & HANDWRITTEN FONTS
    "GreatVibes-Regular": {
        "url": "https://github.com/googlefonts/greatvibes/raw/main/fonts/ttf/GreatVibes-Regular.ttf",
        "fallback_name": "Great Vibes",
        "category": "script"
    },
    "DancingScript-Regular": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/dancingscript/DancingScript%5Bwght%5D.ttf",
        "fallback_name": "Dancing Script",
        "category": "script"
    },
    "DancingScript-Bold": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/dancingscript/DancingScript%5Bwght%5D.ttf",
        "fallback_name": "Dancing Script Bold",
        "category": "script"
    },
    
    # DECORATIVE & ARTISTIC
    "Bangers-Regular": {
        "url": "https://github.com/googlefonts/bangers/raw/main/fonts/ttf/Bangers-Regular.ttf",
        "fallback_name": "Bangers",
        "category": "decorative"
    },
    "Fredoka-Regular": {
        "url": "https://github.com/googlefonts/fredoka/raw/main/fonts/ttf/Fredoka-Regular.ttf",
        "fallback_name": "Fredoka",
        "category": "decorative"
    },
    "Fredoka-Bold": {
        "url": "https://github.com/googlefonts/fredoka/raw/main/fonts/ttf/Fredoka-Bold.ttf",
        "fallback_name": "Fredoka Bold",
        "category": "decorative"
    },
    
    # CONDENSED & NARROW
    "FiraSansCondensed-Regular": {
        "url": "https://github.com/mozilla/Fira/raw/master/ttf/FiraSansCondensed-Regular.ttf",
        "fallback_name": "Fira Sans Condensed",
        "category": "condensed"
    },
    "FiraSansCondensed-Bold": {
        "url": "https://github.com/mozilla/Fira/raw/master/ttf/FiraSansCondensed-Bold.ttf",
        "fallback_name": "Fira Sans Condensed Bold",
        "category": "condensed"
    },
    
    # TECH & FUTURISTIC
    "Orbitron-Regular": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf",
        "fallback_name": "Orbitron",
        "category": "tech"
    },
    "Orbitron-Bold": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf",
        "fallback_name": "Orbitron Bold",
        "category": "tech"
    },
    
    # RETRO & VINTAGE
    "PressStart2P-Regular": {
        "url": "https://github.com/googlefonts/PressStart2P/raw/main/fonts/ttf/PressStart2P-Regular.ttf",
        "fallback_name": "Press Start 2P",
        "category": "retro"
    },
    
    # SERIF & CLASSIC
    "Merriweather-Regular": {
        "url": "https://github.com/googlefonts/merriweather/raw/master/fonts/ttf/Merriweather-Regular.ttf",
        "fallback_name": "Merriweather",
        "category": "serif"
    },
    "Merriweather-Bold": {
        "url": "https://github.com/googlefonts/merriweather/raw/master/fonts/ttf/Merriweather-Bold.ttf",
        "fallback_name": "Merriweather Bold",
        "category": "serif"
    },
    
    # BOLD DISPLAY FONTS
    "Righteous-Regular": {
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/righteous/Righteous-Regular.ttf",
        "fallback_name": "Righteous",
        "category": "display"
    },
    "Russo-Regular": {
        "url": "https://github.com/googlefonts/RussoOneFont/raw/master/fonts/ttf/RussoOne-Regular.ttf",
        "fallback_name": "Russo One",
        "category": "display"
    }
}


class EnhancedFontLoader:
    """Enhanced font loader with better fallback support."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize font loader.
        
        Args:
            cache_dir: Directory to store downloaded fonts
        """
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.cache/lyric_video_fonts"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        self.available_fonts = self._scan_system_fonts()
        
        # Create font index
        self.font_index_file = self.cache_dir / "font_index.json"
        self._update_font_index()
    
    def _scan_system_fonts(self) -> Dict[str, str]:
        """Scan for available system fonts."""
        fonts = {}
        
        # Add known font paths that exist
        for font_name, font_path in KNOWN_FONT_PATHS.items():
            if os.path.exists(font_path):
                fonts[font_name] = font_path
                logger.info(f"Found system font: {font_name} at {font_path}")
        
        # Scan common directories
        font_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "/System/Library/Fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
            str(self.cache_dir)  # Include our cache directory
        ]
        
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                font_path = Path(font_dir)
                for font_file in font_path.rglob("*.ttf"):
                    font_name = font_file.stem
                    fonts[font_name] = str(font_file)
        
        logger.info(f"Found {len(fonts)} fonts on system")
        return fonts
    
    def _update_font_index(self):
        """Update the font index file."""
        index_data = {
            "system_fonts": self.available_fonts,
            "font_mappings": FONT_MAPPINGS,
            "downloaded_fonts": {}
        }
        
        # Check downloaded fonts
        for font_file in self.cache_dir.glob("*.ttf"):
            index_data["downloaded_fonts"][font_file.stem] = str(font_file)
        
        with open(self.font_index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
    
    def download_font(self, font_key: str) -> Optional[str]:
        """Download a font from the internet.
        
        Args:
            font_key: Key from DOWNLOADABLE_FONTS
            
        Returns:
            Path to downloaded font or None
        """
        if font_key not in DOWNLOADABLE_FONTS:
            return None
        
        font_info = DOWNLOADABLE_FONTS[font_key]
        font_path = self.cache_dir / f"{font_key}.ttf"
        
        # Check if already downloaded
        if font_path.exists():
            logger.info(f"Font {font_key} already downloaded")
            return str(font_path)
        
        # Download font
        try:
            logger.info(f"Downloading font {font_key} from {font_info['url']}")
            urllib.request.urlretrieve(font_info['url'], font_path)
            
            # Update available fonts
            self.available_fonts[font_key] = str(font_path)
            self._update_font_index()
            
            logger.info(f"Successfully downloaded {font_key}")
            return str(font_path)
            
        except Exception as e:
            logger.error(f"Failed to download font {font_key}: {e}")
            return None
    
    def get_font_path(self, font_name: str) -> Optional[str]:
        """Get the best available font path for a given font name.
        
        Args:
            font_name: Requested font name
            
        Returns:
            Path to font file or None
        """
        # Direct match
        if font_name in self.available_fonts:
            return self.available_fonts[font_name]
        
        # Check mappings
        if font_name in FONT_MAPPINGS:
            for fallback in FONT_MAPPINGS[font_name]:
                if fallback in self.available_fonts:
                    logger.info(f"Using {fallback} as fallback for {font_name}")
                    return self.available_fonts[fallback]
        
        # Try downloading if it's a downloadable font
        for dl_key, dl_info in DOWNLOADABLE_FONTS.items():
            if font_name == dl_info.get('fallback_name'):
                font_path = self.download_font(dl_key)
                if font_path:
                    return font_path
        
        # Search for partial matches
        font_name_lower = font_name.lower()
        for available_name, path in self.available_fonts.items():
            if font_name_lower in available_name.lower():
                logger.info(f"Using {available_name} as partial match for {font_name}")
                return path
        
        return None
    
    def load_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """Load a font with the given name and size.
        
        Args:
            font_name: Font name
            size: Font size in points
            
        Returns:
            Loaded font object
        """
        cache_key = f"{font_name}_{size}"
        
        # Check cache
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # Get font path
        font_path = self.get_font_path(font_name)
        
        if font_path:
            try:
                font = ImageFont.truetype(font_path, size)
                self.font_cache[cache_key] = font
                logger.info(f"Loaded font {font_name} (size {size}) from {font_path}")
                return font
            except Exception as e:
                logger.error(f"Failed to load font from {font_path}: {e}")
        
        # Final fallback - try to use the best available font
        if self.available_fonts:
            # Prefer DejaVu Sans or Ubuntu
            for preferred in ["DejaVuSans", "Ubuntu-R", "DejaVuSans-Bold"]:
                if preferred in self.available_fonts:
                    try:
                        font = ImageFont.truetype(self.available_fonts[preferred], size)
                        self.font_cache[cache_key] = font
                        logger.warning(f"Using {preferred} as final fallback for {font_name}")
                        return font
                    except:
                        continue
            
            # Use first available font
            first_font = list(self.available_fonts.values())[0]
            try:
                font = ImageFont.truetype(first_font, size)
                self.font_cache[cache_key] = font
                logger.warning(f"Using {first_font} as last resort for {font_name}")
                return font
            except:
                pass
        
        # Absolute last resort - create a large bitmap font
        logger.error(f"No suitable font found for {font_name}, creating large bitmap font")
        # PIL's default font is tiny, so we'll return None and handle it differently
        return None
    
    def list_available_fonts(self) -> List[str]:
        """List all available font names."""
        fonts = list(self.available_fonts.keys())
        fonts.extend(DOWNLOADABLE_FONTS.keys())
        return sorted(set(fonts))
    
    def ensure_font_available(self, font_name: str) -> bool:
        """Ensure a font is available, downloading if necessary.
        
        Args:
            font_name: Font name to ensure
            
        Returns:
            True if font is available
        """
        font_path = self.get_font_path(font_name)
        return font_path is not None
    
    def get_fonts_by_category(self, category: str) -> List[str]:
        """Get all fonts in a specific category.
        
        Args:
            category: Font category (modern, display, impact, script, etc.)
            
        Returns:
            List of font names in that category
        """
        fonts = []
        for font_key, font_info in DOWNLOADABLE_FONTS.items():
            if font_info.get('category') == category:
                fonts.append(font_info['fallback_name'])
        return fonts
    
    def get_all_categories(self) -> List[str]:
        """Get all available font categories."""
        categories = set()
        for font_info in DOWNLOADABLE_FONTS.values():
            if 'category' in font_info:
                categories.add(font_info['category'])
        return sorted(categories)
    
    def download_fonts_by_category(self, category: str) -> List[str]:
        """Download all fonts in a specific category.
        
        Args:
            category: Font category to download
            
        Returns:
            List of successfully downloaded font paths
        """
        downloaded = []
        for font_key, font_info in DOWNLOADABLE_FONTS.items():
            if font_info.get('category') == category:
                font_path = self.download_font(font_key)
                if font_path:
                    downloaded.append(font_path)
        return downloaded
    
    def suggest_font_for_style(self, style: str) -> str:
        """Suggest a font based on desired style.
        
        Args:
            style: Style description (bold, elegant, modern, retro, etc.)
            
        Returns:
            Suggested font name
        """
        style_lower = style.lower()
        
        # Style-based suggestions
        if any(word in style_lower for word in ['bold', 'strong', 'impact', 'heavy']):
            return "Bebas Neue"  # Strong impact font
        elif any(word in style_lower for word in ['elegant', 'classy', 'sophisticated']):
            return "Playfair Display"  # Elegant serif
        elif any(word in style_lower for word in ['modern', 'clean', 'simple']):
            return "Montserrat"  # Clean modern
        elif any(word in style_lower for word in ['tech', 'futuristic', 'sci-fi']):
            return "Orbitron"  # Futuristic tech
        elif any(word in style_lower for word in ['retro', 'vintage', 'old', '80s']):
            return "Press Start 2P"  # Retro gaming
        elif any(word in style_lower for word in ['script', 'handwritten', 'cursive']):
            return "Dancing Script"  # Script/handwritten
        elif any(word in style_lower for word in ['fun', 'playful', 'comic', 'cartoon']):
            return "Bangers"  # Fun/comic style
        elif any(word in style_lower for word in ['condensed', 'narrow', 'thin']):
            return "Fira Sans Condensed"  # Condensed style
        else:
            return "Oswald"  # Good all-around display font
    
    def get_font_info(self, font_name: str) -> Dict:
        """Get detailed information about a font.
        
        Args:
            font_name: Font name to get info for
            
        Returns:
            Dictionary with font information
        """
        # Look for exact match first
        for font_key, font_info in DOWNLOADABLE_FONTS.items():
            if font_info['fallback_name'] == font_name or font_key == font_name:
                return {
                    'name': font_info['fallback_name'],
                    'key': font_key,
                    'category': font_info.get('category', 'unknown'),
                    'available': self.ensure_font_available(font_name),
                    'description': self._get_font_description(font_info.get('category', ''))
                }
        
        return {
            'name': font_name,
            'key': font_name,
            'category': 'system',
            'available': font_name in self.available_fonts,
            'description': 'System font'
        }
    
    def _get_font_description(self, category: str) -> str:
        """Get description for font category."""
        descriptions = {
            'modern': 'Clean and contemporary design, perfect for professional content',
            'display': 'Bold and eye-catching, great for titles and headers',
            'impact': 'Strong and powerful, commands attention',
            'script': 'Elegant handwritten style, adds personal touch',
            'decorative': 'Fun and playful, great for creative projects',
            'condensed': 'Space-efficient, fits more text in narrow areas',
            'tech': 'Futuristic and digital, perfect for tech content',
            'retro': 'Vintage styling, evokes nostalgia',
            'serif': 'Classic and readable, traditional and trustworthy',
            'elegant': 'Sophisticated and refined, luxury feel'
        }
        return descriptions.get(category, 'Stylish font choice')
    
    def auto_download_popular_fonts(self) -> List[str]:
        """Automatically download a curated set of popular fonts.
        
        Returns:
            List of downloaded font paths
        """
        popular_fonts = [
            "Montserrat-Bold",      # Modern bold
            "BebasNeue-Regular",    # Impact display
            "Oswald-Bold",          # Strong display
            "DancingScript-Bold",   # Script
            "Bangers-Regular",      # Fun/decorative
            "Orbitron-Bold",        # Tech/futuristic
            "Righteous-Regular",    # Bold display
            "Playfair-Bold"         # Elegant serif
        ]
        
        downloaded = []
        logger.info("Auto-downloading popular fonts for better text rendering...")
        
        for font_key in popular_fonts:
            font_path = self.download_font(font_key)
            if font_path:
                downloaded.append(font_path)
        
        logger.info(f"Downloaded {len(downloaded)} popular fonts")
        return downloaded
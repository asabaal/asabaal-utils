"""
Section-based visual variation system for lyric videos.

Provides different visual styles for different song sections (verse, chorus, bridge, instrumental).
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SectionType(Enum):
    """Types of song sections."""
    INTRO = "intro"
    VERSE = "verse"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    INSTRUMENTAL = "instrumental"
    OUTRO = "outro"
    UNKNOWN = "unknown"


@dataclass
class SectionConfig:
    """Visual configuration for a song section."""
    # Text effects
    ambient_glow_intensity: float = 1.0
    dynamic_colors_enabled: bool = True
    lighting_effects_enabled: bool = True
    energy_bursts_enabled: bool = True
    
    # Color schemes
    primary_color_hue: Optional[float] = None  # 0-360
    color_temperature: str = "neutral"  # warm, cool, neutral
    saturation_boost: float = 1.0
    
    # Motion and positioning
    dynamic_positioning: bool = True
    motion_tracking: bool = True
    positioning_style: str = "lower_third"  # center, lower_third, dynamic
    
    # Background effects
    background_intensity: float = 1.0
    clip_switching_frequency: str = "normal"  # slow, normal, fast, beat_sync
    
    # Effect combinations
    wave_effect: bool = False
    chromatic_aberration: bool = False
    energy_burst_threshold: float = 0.8


class SectionManager:
    """Manages visual variations across different song sections."""
    
    def __init__(self):
        self.sections: List[Tuple[float, float, SectionType]] = []
        self.section_configs: Dict[SectionType, SectionConfig] = {}
        self.current_section: Optional[SectionType] = None
        self.current_config: Optional[SectionConfig] = None
        
        # Initialize default configurations
        self._create_default_configs()
        
    def _create_default_configs(self):
        """Create default visual configurations for each section type."""
        
        # VERSE: Subtle, intimate, focused
        self.section_configs[SectionType.VERSE] = SectionConfig(
            ambient_glow_intensity=0.6,
            dynamic_colors_enabled=True,
            lighting_effects_enabled=True,
            energy_bursts_enabled=False,
            primary_color_hue=220,  # Blue tones
            color_temperature="cool",
            saturation_boost=0.8,
            dynamic_positioning=False,
            motion_tracking=True,
            positioning_style="lower_third",
            background_intensity=0.7,
            clip_switching_frequency="slow"
        )
        
        # CHORUS: Explosive, energetic, dramatic
        self.section_configs[SectionType.CHORUS] = SectionConfig(
            ambient_glow_intensity=1.5,
            dynamic_colors_enabled=True,
            lighting_effects_enabled=True,
            energy_bursts_enabled=True,
            primary_color_hue=30,  # Orange/red tones
            color_temperature="warm",
            saturation_boost=1.3,
            dynamic_positioning=True,
            motion_tracking=True,
            positioning_style="dynamic",
            background_intensity=1.2,
            clip_switching_frequency="beat_sync",
            chromatic_aberration=True,
            energy_burst_threshold=0.6
        )
        
        # BRIDGE: Ethereal, different, atmospheric
        self.section_configs[SectionType.BRIDGE] = SectionConfig(
            ambient_glow_intensity=1.0,
            dynamic_colors_enabled=True,
            lighting_effects_enabled=True,
            energy_bursts_enabled=False,
            primary_color_hue=280,  # Purple tones
            color_temperature="cool",
            saturation_boost=1.1,
            dynamic_positioning=True,
            motion_tracking=True,
            positioning_style="center",
            background_intensity=0.8,
            clip_switching_frequency="slow",
            wave_effect=True
        )
        
        # INSTRUMENTAL: MAXIMUM VISUAL SPECTACLE - absolutely captivating
        self.section_configs[SectionType.INSTRUMENTAL] = SectionConfig(
            ambient_glow_intensity=3.0,  # Extreme glow
            dynamic_colors_enabled=True,
            lighting_effects_enabled=True,
            energy_bursts_enabled=True,
            primary_color_hue=None,  # Full rainbow spectrum
            color_temperature="neutral",
            saturation_boost=2.0,  # Maximum saturation
            dynamic_positioning=True,
            motion_tracking=True,
            positioning_style="dynamic",
            background_intensity=2.0,  # Maximum background effects
            clip_switching_frequency="beat_sync",  # Fastest switching
            wave_effect=True,
            chromatic_aberration=True,
            energy_burst_threshold=0.3  # Lower threshold = more frequent bursts
        )
        
        # INTRO: Build up, anticipation
        self.section_configs[SectionType.INTRO] = SectionConfig(
            ambient_glow_intensity=0.4,
            dynamic_colors_enabled=True,
            lighting_effects_enabled=False,
            energy_bursts_enabled=False,
            primary_color_hue=180,  # Cyan tones
            color_temperature="cool",
            saturation_boost=0.7,
            dynamic_positioning=False,
            motion_tracking=False,
            positioning_style="center",
            background_intensity=0.5,
            clip_switching_frequency="slow"
        )
        
        # OUTRO: Wind down, fade
        self.section_configs[SectionType.OUTRO] = SectionConfig(
            ambient_glow_intensity=0.3,
            dynamic_colors_enabled=True,
            lighting_effects_enabled=True,
            energy_bursts_enabled=False,
            primary_color_hue=60,  # Golden tones
            color_temperature="warm",
            saturation_boost=0.6,
            dynamic_positioning=False,
            motion_tracking=True,
            positioning_style="lower_third",
            background_intensity=0.6,
            clip_switching_frequency="slow"
        )
        
    def add_section(self, start_time: float, end_time: float, section_type: SectionType):
        """Add a song section with timing information."""
        self.sections.append((start_time, end_time, section_type))
        # Sort sections by start time
        self.sections.sort(key=lambda x: x[0])
        
    def load_structure_from_file(self, structure_file_path: str, song_duration: float) -> List[Tuple[float, float, SectionType]]:
        """Load song structure from a structure file.
        
        Args:
            structure_file_path: Path to structure file (JSON, YAML-like, or simple text)
            song_duration: Total song duration to set end time of last section
            
        Returns:
            List of (start_time, end_time, section_type) tuples
        """
        from .structure_loader import StructureLoader
        
        loader = StructureLoader()
        custom_sections = loader.load_structure_file(structure_file_path)
        
        # Set song duration for last section
        loader.set_song_duration(song_duration)
        
        # Validate structure
        issues = loader.validate_structure()
        if issues:
            logger.warning("Structure validation issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        # Apply custom configurations
        custom_configs = loader.get_custom_configs()
        for section_name, config in custom_configs.items():
            logger.info(f"Applying custom config for section '{section_name}': {config}")
            # Custom configs would be applied here - for now just log them
            
        # Get sections for manager
        loaded_sections = loader.get_sections_for_manager()
        
        # Clear existing sections and add loaded ones
        self.sections.clear()
        for start, end, section_type in loaded_sections:
            self.add_section(start, end, section_type)
            
        logger.info(f"Successfully loaded {len(loaded_sections)} sections from structure file")
        return loaded_sections
        
    def detect_sections_from_audio(self, audio_features, lyrics_list) -> List[Tuple[float, float, SectionType]]:
        """Auto-detect song sections from audio features and lyrics.
        
        This is a fallback method when no structure file is provided.
        """
        duration = audio_features.duration
        detected_sections = []
        
        logger.info("Auto-detecting song sections (consider using --structure-file for better results)")
        
        # Simple fallback structure
        detected_sections = [
            (0, min(15, duration * 0.1), SectionType.INTRO),
            (min(15, duration * 0.1), duration * 0.9, SectionType.VERSE),
            (duration * 0.9, duration, SectionType.OUTRO)
        ]
                
        # Add detected sections
        for start, end, section_type in detected_sections:
            self.add_section(start, end, section_type)
            
        return detected_sections
        
    def get_section_at_time(self, timestamp: float) -> Tuple[SectionType, SectionConfig]:
        """Get the section type and configuration at a given timestamp."""
        for start_time, end_time, section_type in self.sections:
            if start_time <= timestamp < end_time:
                self.current_section = section_type
                self.current_config = self.section_configs[section_type]
                return section_type, self.current_config
                
        # Default to verse if no section found
        default_section = SectionType.VERSE
        self.current_section = default_section
        self.current_config = self.section_configs[default_section]
        return default_section, self.current_config
        
    def get_text_effects_config(self, timestamp: float, base_effects: Dict) -> Dict:
        """Get text effects configuration for current section."""
        section_type, config = self.get_section_at_time(timestamp)
        
        # Override base effects with section-specific settings
        effects_config = base_effects.copy()
        effects_config.update({
            'ambient_glow': config.lighting_effects_enabled,
            'ambient_glow_intensity': config.ambient_glow_intensity,
            'dynamic_colors': config.dynamic_colors_enabled,
            'lighting_effects': config.lighting_effects_enabled,
            'energy_bursts': config.energy_bursts_enabled,
            'energy_burst_threshold': config.energy_burst_threshold,
            'wave_effect': config.wave_effect,
            'chromatic_aberration': config.chromatic_aberration,
            'saturation_boost': config.saturation_boost,
            'primary_color_hue': config.primary_color_hue,
            'color_temperature': config.color_temperature
        })
        
        # SPECIAL INSTRUMENTAL HOOK EFFECTS
        if section_type == SectionType.INSTRUMENTAL:
            effects_config.update({
                'instrumental_mode': True,
                'extreme_effects': True,
                'rainbow_mode': True,
                'max_energy_bursts': True,
                'psychedelic_mode': True,
                'kaleidoscope_effect': True,
                'strobe_on_beats': True,
                'particle_effects': True
            })
        
        return effects_config
        
    def get_text_style_modifications(self, timestamp: float, base_style) -> Dict:
        """Get text style modifications for current section."""
        section_type, config = self.get_section_at_time(timestamp)
        
        modifications = {
            'dynamic_positioning': config.dynamic_positioning,
            'motion_tracking': config.motion_tracking,
            'vertical_position': self._convert_positioning_style(config.positioning_style)
        }
        
        return modifications
        
    def get_background_config(self, timestamp: float) -> Dict:
        """Get background configuration for current section."""
        section_type, config = self.get_section_at_time(timestamp)
        
        return {
            'intensity_multiplier': config.background_intensity,
            'clip_switching_mode': config.clip_switching_frequency,
            'section_type': section_type.value
        }
        
    def _convert_positioning_style(self, style: str) -> str:
        """Convert positioning style to text renderer format."""
        style_mapping = {
            'center': 'center',
            'lower_third': 'bottom',
            'dynamic': 'center'  # Will use dynamic positioning
        }
        return style_mapping.get(style, 'bottom')
        
    def log_section_transitions(self, duration: float):
        """Log the section structure for debugging."""
        logger.info("Song section structure:")
        for start, end, section_type in self.sections:
            logger.info(f"  {start:.1f}s - {end:.1f}s: {section_type.value.upper()}")
            
    def customize_section(self, section_type: SectionType, **kwargs):
        """Customize configuration for a specific section type."""
        if section_type in self.section_configs:
            config = self.section_configs[section_type]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    logger.warning(f"Unknown config parameter: {key}")
        else:
            logger.warning(f"Unknown section type: {section_type}")
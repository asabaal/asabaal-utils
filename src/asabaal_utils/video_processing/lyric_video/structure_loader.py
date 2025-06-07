"""
Song structure file loader for custom section definitions.

Supports JSON and simple text formats for defining song sections with timing.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import re

from .section_manager import SectionType, SectionConfig

logger = logging.getLogger(__name__)


@dataclass
class CustomSection:
    """A custom song section with flexible naming and configuration."""
    name: str
    start_time: float
    end_time: float
    section_type: SectionType  # Mapped from name or explicitly set
    custom_config: Optional[Dict] = None  # Custom visual overrides


class StructureLoader:
    """Loads song structure from various file formats."""
    
    def __init__(self):
        self.sections: List[CustomSection] = []
        
        # Default section type mappings for common names
        self.section_name_mappings = {
            # Standard sections
            'intro': SectionType.INTRO,
            'verse': SectionType.VERSE,
            'verse1': SectionType.VERSE,
            'verse2': SectionType.VERSE,
            'verse3': SectionType.VERSE,
            'chorus': SectionType.CHORUS,
            'hook': SectionType.CHORUS,
            'refrain': SectionType.CHORUS,
            'bridge': SectionType.BRIDGE,
            'instrumental': SectionType.INSTRUMENTAL,
            'solo': SectionType.INSTRUMENTAL,
            'breakdown': SectionType.INSTRUMENTAL,
            'drop': SectionType.INSTRUMENTAL,
            'outro': SectionType.OUTRO,
            'ending': SectionType.OUTRO,
            
            # Extended naming
            'pre-chorus': SectionType.BRIDGE,
            'pre_chorus': SectionType.BRIDGE,
            'prechorus': SectionType.BRIDGE,
            'buildup': SectionType.BRIDGE,
            'build': SectionType.BRIDGE,
            'interlude': SectionType.INSTRUMENTAL,
            'break': SectionType.INSTRUMENTAL,
            'instrumental_break': SectionType.INSTRUMENTAL,
            'guitar_solo': SectionType.INSTRUMENTAL,
            'drum_solo': SectionType.INSTRUMENTAL,
        }
        
    def load_structure_file(self, file_path: Union[str, Path]) -> List[CustomSection]:
        """Load song structure from file.
        
        Supports JSON, YAML-like, and simple text formats.
        
        Args:
            file_path: Path to structure file
            
        Returns:
            List of CustomSection objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Structure file not found: {file_path}")
            
        content = file_path.read_text().strip()
        
        # Detect file format
        if file_path.suffix.lower() == '.json' or content.startswith('{'):
            sections = self._load_json_format(content)
        elif file_path.suffix.lower() in ['.yaml', '.yml'] or ':' in content:
            sections = self._load_yaml_like_format(content)
        else:
            sections = self._load_simple_text_format(content)
            
        self.sections = sections
        logger.info(f"Loaded {len(sections)} sections from {file_path}")
        
        return sections
        
    def _load_json_format(self, content: str) -> List[CustomSection]:
        """Load JSON format structure file.
        
        Expected format:
        {
            "sections": [
                {
                    "name": "intro",
                    "start": 0.0,
                    "end": 15.5,
                    "type": "intro",  // optional
                    "config": {...}   // optional custom config
                }
            ]
        }
        """
        try:
            data = json.loads(content)
            sections = []
            
            if 'sections' not in data:
                raise ValueError("JSON must contain 'sections' array")
                
            for i, section_data in enumerate(data['sections']):
                if 'name' not in section_data or 'start' not in section_data:
                    raise ValueError(f"Section {i} missing required 'name' or 'start' field")
                    
                name = section_data['name']
                start_time = float(section_data['start'])
                
                # End time can be explicit or calculated from next section
                if 'end' in section_data:
                    end_time = float(section_data['end'])
                elif i < len(data['sections']) - 1:
                    end_time = float(data['sections'][i + 1]['start'])
                else:
                    # Last section - will be set later
                    end_time = start_time + 30.0  # Default 30s
                    
                # Map section type
                if 'type' in section_data:
                    section_type = self._parse_section_type(section_data['type'])
                else:
                    section_type = self._map_name_to_type(name)
                    
                # Custom configuration
                custom_config = section_data.get('config', None)
                
                sections.append(CustomSection(
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    section_type=section_type,
                    custom_config=custom_config
                ))
                
            return sections
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
            
    def _load_yaml_like_format(self, content: str) -> List[CustomSection]:
        """Load YAML-like format (simplified).
        
        Expected format:
        intro: 0:00-0:15
        verse1: 0:15-0:45
        chorus: 0:45-1:15
        verse2: 1:15-1:45
        instrumental_break: 1:45-2:15
        """
        sections = []
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                # Parse "name: start-end" or "name: start:end"
                if ':' not in line:
                    continue
                    
                parts = line.split(':', 1)
                name = parts[0].strip()
                time_range = parts[1].strip()
                
                # Parse time range
                start_time, end_time = self._parse_time_range(time_range)
                
                section_type = self._map_name_to_type(name)
                
                sections.append(CustomSection(
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    section_type=section_type
                ))
                
            except Exception as e:
                logger.warning(f"Could not parse line {line_num}: {line} - {e}")
                continue
                
        return sections
        
    def _load_simple_text_format(self, content: str) -> List[CustomSection]:
        """Load simple text format.
        
        Expected format:
        intro 0:00
        verse1 0:15
        chorus 0:45
        verse2 1:15
        instrumental_break 1:45
        outro 2:15
        """
        sections = []
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        for i, line in enumerate(lines):
            try:
                parts = line.split()
                if len(parts) < 2:
                    continue
                    
                name = parts[0]
                start_time = self._parse_timestamp(parts[1])
                
                # Calculate end time from next section or default
                if i < len(lines) - 1:
                    next_parts = lines[i + 1].split()
                    if len(next_parts) >= 2:
                        end_time = self._parse_timestamp(next_parts[1])
                    else:
                        end_time = start_time + 30.0
                else:
                    end_time = start_time + 30.0
                    
                section_type = self._map_name_to_type(name)
                
                sections.append(CustomSection(
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    section_type=section_type
                ))
                
            except Exception as e:
                logger.warning(f"Could not parse line: {line} - {e}")
                continue
                
        return sections
        
    def _parse_time_range(self, time_range: str) -> Tuple[float, float]:
        """Parse time range like '0:15-1:30' or '15.5-90.0'."""
        # Handle different separators
        for sep in ['-', 'to', '→', '..']:
            if sep in time_range:
                start_str, end_str = time_range.split(sep, 1)
                start_time = self._parse_timestamp(start_str.strip())
                end_time = self._parse_timestamp(end_str.strip())
                return start_time, end_time
                
        raise ValueError(f"Could not parse time range: {time_range}")
        
    def _parse_timestamp(self, timestamp: str) -> float:
        """Parse timestamp like '1:30.5' or '90.5' to seconds."""
        timestamp = timestamp.strip()
        
        # Handle MM:SS.mmm format
        if ':' in timestamp:
            parts = timestamp.split(':')
            if len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        
        # Handle direct seconds format
        return float(timestamp)
        
    def _map_name_to_type(self, name: str) -> SectionType:
        """Map section name to SectionType."""
        # Clean name for lookup
        clean_name = re.sub(r'[^a-zA-Z_]', '', name.lower())
        
        # Direct mapping
        if clean_name in self.section_name_mappings:
            return self.section_name_mappings[clean_name]
            
        # Partial matching
        for pattern, section_type in self.section_name_mappings.items():
            if pattern in clean_name or clean_name in pattern:
                return section_type
                
        # Default based on name patterns
        if any(word in clean_name for word in ['intro', 'begin', 'start']):
            return SectionType.INTRO
        elif any(word in clean_name for word in ['outro', 'end', 'finish']):
            return SectionType.OUTRO
        elif any(word in clean_name for word in ['verse', 'story']):
            return SectionType.VERSE
        elif any(word in clean_name for word in ['chorus', 'hook', 'main']):
            return SectionType.CHORUS
        elif any(word in clean_name for word in ['bridge', 'middle', 'transition']):
            return SectionType.BRIDGE
        elif any(word in clean_name for word in ['instrumental', 'solo', 'break', 'drop']):
            return SectionType.INSTRUMENTAL
        else:
            # Default to verse for unknown sections
            logger.info(f"Unknown section name '{name}', defaulting to VERSE")
            return SectionType.VERSE
            
    def _parse_section_type(self, type_str: str) -> SectionType:
        """Parse explicit section type string."""
        try:
            # Try direct enum lookup
            return SectionType(type_str.lower())
        except ValueError:
            # Fall back to name mapping
            return self._map_name_to_type(type_str)
            
    def get_sections_for_manager(self) -> List[Tuple[float, float, SectionType]]:
        """Get sections in format expected by SectionManager."""
        return [(s.start_time, s.end_time, s.section_type) for s in self.sections]
        
    def get_custom_configs(self) -> Dict[str, Dict]:
        """Get custom configurations by section name."""
        return {s.name: s.custom_config for s in self.sections if s.custom_config}
        
    def set_song_duration(self, duration: float):
        """Set the end time of the last section to song duration."""
        if self.sections:
            self.sections[-1].end_time = duration
            
    def create_example_files(self, output_dir: Union[str, Path]):
        """Create example structure files in different formats."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # JSON example
        json_example = {
            "sections": [
                {"name": "intro", "start": 0.0, "end": 15.0},
                {"name": "verse1", "start": 15.0, "end": 45.0},
                {"name": "chorus", "start": 45.0, "end": 75.0},
                {"name": "verse2", "start": 75.0, "end": 105.0},
                {"name": "chorus", "start": 105.0, "end": 135.0},
                {"name": "instrumental_break", "start": 135.0, "end": 165.0, 
                 "config": {"ambient_glow_intensity": 3.0, "energy_burst_threshold": 0.2}},
                {"name": "bridge", "start": 165.0, "end": 180.0},
                {"name": "final_chorus", "start": 180.0, "end": 210.0},
                {"name": "outro", "start": 210.0, "end": 240.0}
            ]
        }
        
        (output_dir / "song_structure.json").write_text(json.dumps(json_example, indent=2))
        
        # YAML-like example
        yaml_example = """# Song Structure File (YAML-like format)
# Format: section_name: start_time-end_time

intro: 0:00-0:15
verse1: 0:15-0:45
chorus: 0:45-1:15
verse2: 1:15-1:45
chorus: 1:45-2:15
instrumental_break: 2:15-2:45
bridge: 2:45-3:00
final_chorus: 3:00-3:30
outro: 3:30-4:00
"""
        
        (output_dir / "song_structure.yaml").write_text(yaml_example)
        
        # Simple text example
        text_example = """# Song Structure File (Simple format)
# Format: section_name start_time

intro 0:00
verse1 0:15
chorus 0:45
verse2 1:15
chorus 1:45
instrumental_break 2:15
bridge 2:45
final_chorus 3:00
outro 3:30
"""
        
        (output_dir / "song_structure.txt").write_text(text_example)
        
        logger.info(f"Created example structure files in {output_dir}")
        
    def validate_structure(self) -> List[str]:
        """Validate the loaded structure and return any issues."""
        issues = []
        
        if not self.sections:
            issues.append("No sections defined")
            return issues
            
        # Check for overlapping sections
        sorted_sections = sorted(self.sections, key=lambda s: s.start_time)
        
        for i in range(len(sorted_sections) - 1):
            current = sorted_sections[i]
            next_section = sorted_sections[i + 1]
            
            if current.end_time > next_section.start_time:
                issues.append(f"Section '{current.name}' overlaps with '{next_section.name}'")
                
        # Check for gaps
        for i in range(len(sorted_sections) - 1):
            current = sorted_sections[i]
            next_section = sorted_sections[i + 1]
            
            gap = next_section.start_time - current.end_time
            if gap > 1.0:  # More than 1 second gap
                issues.append(f"Gap of {gap:.1f}s between '{current.name}' and '{next_section.name}'")
                
        # Check for negative durations
        for section in self.sections:
            if section.end_time <= section.start_time:
                issues.append(f"Section '{section.name}' has invalid duration")
                
        return issues
"""CLI for song structure analysis."""

import argparse
import json
import logging
from pathlib import Path
from .song_structure import SongStructureAnalyzer, SectionType

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def analyze_structure_cli():
    """CLI for analyzing song structure."""
    parser = argparse.ArgumentParser(
        description="Analyze song structure in terms of sections, bars, and time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze audio and save structure
  analyze-structure song.mp3 -o structure.json
  
  # Analyze with custom tempo
  analyze-structure song.mp3 --tempo 120 -o structure.yaml
  
  # Convert existing structure between formats
  analyze-structure --input structure.json --output structure.yaml
  
  # Display structure without saving
  analyze-structure song.mp3 --display
        """
    )
    
    parser.add_argument("audio", nargs='?',
                        help="Path to audio file to analyze")
    parser.add_argument("-o", "--output",
                        help="Output file path (JSON or YAML)")
    parser.add_argument("--input",
                        help="Input structure file to convert/process")
    parser.add_argument("--tempo", type=float,
                        help="Override detected tempo (BPM)")
    parser.add_argument("--time-signature", default="4/4",
                        help="Time signature (default: 4/4)")
    parser.add_argument("--display", action="store_true",
                        help="Display structure to console")
    parser.add_argument("--format", choices=["bars", "time", "both"], default="both",
                        help="Output format preference")
    parser.add_argument("--structure-file", 
                        help="Path to song structure file (JSON or YAML) for instrumental-guided detection")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.audio and not args.input:
        parser.error("Either audio file or --input structure file required")
    
    analyzer = SongStructureAnalyzer()
    
    # Parse time signature
    if '/' in args.time_signature:
        num, denom = map(int, args.time_signature.split('/'))
        analyzer.time_signature = (num, denom)
    
    # Load song structure from file if provided
    song_structure = None
    if args.structure_file:
        logger.info(f"Loading song structure from {args.structure_file}")
        with open(args.structure_file, 'r') as f:
            if args.structure_file.endswith('.json'):
                structure_data = json.load(f)
            elif args.structure_file.endswith(('.yaml', '.yml')):
                import yaml
                structure_data = yaml.safe_load(f)
            else:
                raise ValueError("Structure file must be JSON or YAML")
        
        # Convert to list of tuples
        song_structure = []
        if 'bar_sections' in structure_data:
            for section in structure_data['bar_sections']:
                name = section.get('name', section['type'])
                bars = section['end_bar'] - section['start_bar'] + 1
                song_structure.append((name, bars))
        else:
            raise ValueError("Structure file must contain 'bar_sections'")
        
        logger.info(f"Loaded {len(song_structure)} sections from structure file")
    
    # Load or analyze structure
    if args.input:
        logger.info(f"Loading structure from {args.input}")
        analyzer.load_from_file(args.input)
    else:
        logger.info(f"Analyzing audio: {args.audio}")
        results = analyzer.analyze_audio(args.audio, song_structure=song_structure)
        
        # Override tempo if specified
        if args.tempo:
            analyzer.tempo = args.tempo
            logger.info(f"Using tempo: {args.tempo} BPM")
        
        # Load analyzed sections
        for section in results['time_sections']:
            analyzer.sections.append(section)
        for section in results.get('bar_sections', []):
            analyzer.sections.append(section)
    
    # Display structure
    if args.display or not args.output:
        display_structure(analyzer, args.format)
    
    # Save structure
    if args.output:
        logger.info(f"Saving structure to {args.output}")
        analyzer.save_to_file(args.output)


def display_structure(analyzer: SongStructureAnalyzer, format_pref: str = "both"):
    """Display structure in human-readable format."""
    print("\n🎵 Song Structure Analysis")
    print("=" * 50)
    
    if analyzer.tempo:
        print(f"Tempo: {analyzer.tempo:.1f} BPM")
        print(f"Time Signature: {analyzer.time_signature[0]}/{analyzer.time_signature[1]}")
        print()
    
    # Check if we have confidence information
    has_confidence = hasattr(analyzer, '_confidence_info')
    if has_confidence:
        info = analyzer._confidence_info
        print(f"🎯 Boundary Detection Summary:")
        print(f"   High-confidence boundaries: {info['high_confidence_count']}/{info['total_sections']}")
        print(f"   Using expected timing: {info['expected_count']}")
        print()
    
    # Separate sections by type
    bar_sections = [s for s in analyzer.sections if hasattr(s, 'start_bar')]
    time_sections = [s for s in analyzer.sections if hasattr(s, 'start_time')]
    
    # Display bar-based sections
    if bar_sections and format_pref in ["bars", "both"]:
        print("📊 Bar-Based Structure:")
        for section in sorted(bar_sections, key=lambda s: s.start_bar):
            name = f" ({section.name})" if section.name else ""
            print(f"  Bars {section.start_bar:3d}-{section.end_bar:3d}: "
                  f"{section.section_type.value.upper()}{name} "
                  f"[{section.bar_count} bars]")
        print()
    
    # Display time-based sections with confidence info
    if time_sections and format_pref in ["time", "both"]:
        print("⏱️  Time-Based Structure:")
        for i, section in enumerate(sorted(time_sections, key=lambda s: s.start_time)):
            name = f" ({section.name})" if section.name else ""
            start = format_time(section.start_time)
            end = format_time(section.end_time)
            duration = format_time(section.duration)
            
            # Add confidence marker if available
            confidence_marker = ""
            if has_confidence and i < len(info.get('section_sources', [])):
                source = info['section_sources'][i]
                if 'DETECTED' in source:
                    confidence_marker = " ✓"
                else:
                    confidence_marker = " ○"
            
            print(f"  {start} - {end}: "
                  f"{section.section_type.value.upper()}{name} "
                  f"[{duration}]{confidence_marker}")
        
        if has_confidence:
            print("\n  Legend: ✓ = Detected boundary, ○ = Expected timing")
        print()
    
    # Display total duration
    if time_sections:
        total_duration = max(s.end_time for s in time_sections)
        print(f"Total Duration: {format_time(total_duration)}")


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


if __name__ == "__main__":
    analyze_structure_cli()
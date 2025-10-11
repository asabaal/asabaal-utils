#!/usr/bin/env python3
"""
Biblical Visual Gap Analysis Generator - Traditional NLP Approach
Analyzes SRT files and generates MidJourney prompts for visual gaps.
"""

import json
import argparse
from typing import Dict, List
from pathlib import Path

from srt_parser import parse_srt_content, get_total_duration, validate_time_ranges
from gap_processor import GapProcessor


def detect_input_mode(config: Dict) -> str:
    """Auto-detect input mode from configuration."""
    if "gap_times" in config:
        return "gaps"
    elif "existing_visuals" in config:
        return "existing_visuals"
    elif "full_take" in config and config["full_take"]:
        return "full_take"
    else:
        raise ValueError("Unable to detect input mode. Please specify gap_times, existing_visuals, or full_take")


def format_output(results: Dict, output_format: str = "json") -> str:
    """Format results for output."""
    if output_format == "json":
        return json.dumps(results, indent=2)
    
    elif output_format == "markdown":
        md_lines = [
            f"# Biblical Visual Gap Analysis Results",
            f"\n## Summary",
            f"- Input Mode: {results['input_mode']}",
            f"- Total Duration: {results['total_duration']}",
            f"- Gaps Processed: {results['gaps_processed']}",
            f"\n## Visual Concepts\n"
        ]
        
        for i, (gap_id, gap_data) in enumerate(results['results'].items(), 1):
            md_lines.extend([
                f"### {i}. {gap_data['time_range']}",
                f"**Duration:** {gap_data['duration_seconds']:.2f} seconds",
                f"\n**Narrative Context:**",
                f"> {gap_data['narrative_context']}",
                f"\n**Themes:** {', '.join(gap_data['themes'])}",
                f"\n**Visual Concept:**",
                f"> {gap_data['visual_concept']}",
                f"\n**MidJourney Prompts:**",
                f"\n*Text-to-Image:*",
                f"```",
                gap_data['prompts']['text_to_image'],
                f"```",
                f"\n*Image-to-Video:*",
                f"```",
                gap_data['prompts']['image_to_video'],
                f"```",
                f"\n**Extension Strategy:**",
                f"- Type: {gap_data['extension_strategy']['type']}",
                f"- Coverage: {gap_data['extension_strategy']['coverage']}",
                f"- Instructions: {gap_data['extension_strategy']['instructions']}",
                "\n---\n"
            ])
        
        return '\n'.join(md_lines)
    
    else:
        # Simple text format
        lines = [
            f"Biblical Visual Gap Analysis - {results['input_mode']} mode",
            f"Total Duration: {results['total_duration']}",
            f"Gaps to Fill: {results['gaps_processed']}",
            ""
        ]
        
        for i, (gap_id, gap_data) in enumerate(results['results'].items(), 1):
            lines.extend([
                f"{i}. Gap: {gap_data['time_range']} ({gap_data['duration_seconds']:.1f}s)",
                f"   Context: {gap_data['narrative_context'][:100]}...",
                f"   Prompt: {gap_data['prompts']['text_to_image'][:150]}...",
                f"   Strategy: {gap_data['extension_strategy']['instructions']}",
                ""
            ])
        
        return '\n'.join(lines)


def process_srt_file(srt_path: str, config: Dict, output_format: str = "json") -> str:
    """Main processing function."""
    # Read and parse SRT file
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    
    subtitles = parse_srt_content(srt_content)
    total_duration = get_total_duration(subtitles)
    
    # Detect input mode
    input_mode = detect_input_mode(config)
    
    # Initialize processor
    processor = GapProcessor(midjourney_duration=config.get("midjourney_duration", 5.07))
    
    # Process based on mode
    if input_mode == "gaps":
        gap_times = config["gap_times"]
        validated_gaps, errors = validate_time_ranges(gap_times, total_duration)
        
        if errors:
            print("Validation warnings:")
            for error in errors:
                print(f"  - {error}")
        
        visual_concepts = processor.process_gaps_mode(validated_gaps, subtitles, total_duration)
    
    elif input_mode == "existing_visuals":
        existing_times = config["existing_visuals"]
        visual_concepts = processor.process_existing_visuals_mode(existing_times, subtitles, total_duration)
    
    elif input_mode == "full_take":
        segment_length = config.get("segment_length", 15)
        visual_concepts = processor.process_full_take_mode(subtitles, total_duration, segment_length)
    
    # Format results
    results = {
        "input_mode": input_mode,
        "total_duration": f"{int(total_duration//3600)}:{int((total_duration%3600)//60):02d}:{int(total_duration%60):02d}",
        "gaps_processed": len(visual_concepts),
        "results": {}
    }
    
    # Add mode-specific metadata
    if input_mode == "existing_visuals":
        results["existing_coverage"] = config["existing_visuals"]
        results["calculated_gaps"] = [vc.gap.time_range_str for vc in visual_concepts]
    elif input_mode == "full_take":
        results["segment_length"] = config.get("segment_length", 15)
        results["segments_created"] = len(visual_concepts)
    
    # Process each visual concept
    for i, vc in enumerate(visual_concepts):
        gap_key = f"gap_{i+1}" if input_mode == "gaps" else f"segment_{i+1}"
        
        results["results"][gap_key] = {
            "time_range": vc.gap.time_range_str,
            "duration_seconds": vc.gap.duration,
            "narrative_context": vc.gap.narrative_context,
            "themes": vc.themes,
            "visual_concept": vc.concept_description,
            "prompts": {
                "text_to_image": vc.text_to_image_prompt,
                "image_to_video": vc.image_to_video_prompt
            },
            "animation_style": vc.animation_style,
            "extension_strategy": vc.extension_strategy
        }
    
    return format_output(results, output_format)


def main():
    parser = argparse.ArgumentParser(
        description="Biblical Visual Gap Analysis Generator - Traditional NLP Approach"
    )
    parser.add_argument("srt_file", help="Path to SRT subtitle file")
    parser.add_argument("-c", "--config", help="JSON configuration file", required=True)
    parser.add_argument("-o", "--output", help="Output file (optional)")
    parser.add_argument("-f", "--format", choices=["json", "markdown", "text"], 
                       default="json", help="Output format")
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Process SRT file
    try:
        results = process_srt_file(args.srt_file, config, args.format)
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                f.write(results)
            print(f"Results written to {args.output}")
        else:
            print(results)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
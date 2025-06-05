#!/usr/bin/env python3
"""
Find unused media files in a CapCut project.

This script analyzes a CapCut project file to identify media files that are in the
project's media pool but not used in the timeline. This helps identify unused assets
that can be removed to reduce project size.
"""

import json
import os
import argparse
import sys
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
import pprint

def find_project_files(directory: str) -> List[str]:
    """
    Find all potential CapCut project files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of paths to potential project files
    """
    project_files = []
    
    # Look for common CapCut project file names
    common_names = [
        "draft_content.json",
        "project.json",
        "draft_meta.json",
        "project_meta.json"
    ]
    
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename in common_names or (filename.endswith('.json') and 'project' in filename.lower()):
                full_path = os.path.join(root, filename)
                # Verify it looks like a CapCut project
                if is_likely_capcut_project(full_path):
                    project_files.append(full_path)
    
    return project_files


def is_likely_capcut_project(file_path: str) -> bool:
    """
    Check if a file is likely to be a CapCut project file.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is likely a CapCut project, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Look for common CapCut project indicators
            indicators = [
                'materials' in data,
                'tracks' in data,
                'timeline' in data,
                'mediaPool' in data,
                'resources' in data,
                'assets' in data
            ]
            
            # If at least one indicator is found, it might be a CapCut project
            return any(indicators)
    except Exception:
        # If we can't read the file or it's not valid JSON, it's not a project file
        return False


def process_projects(project_paths: List[str], output_dir: Optional[str], 
                    generate_html: bool, verbose: bool) -> List[Dict[str, Any]]:
    """
    Process multiple CapCut projects.
    
    Args:
        project_paths: List of paths to project files
        output_dir: Base directory for outputs
        generate_html: Whether to generate HTML reports
        verbose: Whether to print verbose output
        
    Returns:
        List of analysis results
    """
    results = []
    
    for project_path in project_paths:
        print(f"\n{'-' * 80}")
        print(f"Processing project: {project_path}")
        print(f"{'-' * 80}")
        
        # Create project-specific output directory if needed
        if output_dir is not None:
            project_name = os.path.basename(os.path.dirname(project_path))
            project_output_dir = os.path.join(output_dir, project_name)
        else:
            project_output_dir = None
        
        # Process the project
        result = find_unused_media(
            json_file_path=project_path,
            output_file=project_output_dir if project_output_dir else None,
            verbose=verbose
        )
        
        results.append({
            'project_path': project_path,
            'result': result
        })
    
    return results


def find_unused_media(json_file_path: str, output_file: str = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze a CapCut project file to find unused media files.
    
    Args:
        json_file_path: Path to the CapCut draft_content.json file
        output_file: Optional path to save the report
        verbose: Whether to print detailed information
        
    Returns:
        A dictionary with analysis results
    """
    print(f"Analyzing CapCut project file: {json_file_path}")
    
    # Load the JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            try:
                project_data = json.load(f)
                print("JSON loaded successfully!")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Step 1: Extract all materials from the media pool
    all_materials = extract_all_materials(project_data, verbose)
    
    # Step 2: Extract all materials used in the timeline
    used_materials = extract_used_materials(project_data, verbose)
    
    # Step 3: Identify unused materials
    unused_materials = identify_unused_materials(all_materials, used_materials)
    
    # Step 4: Generate report
    report = generate_report(all_materials, used_materials, unused_materials)
    
    # Step 5: Save report if requested
    if output_file:
        save_report(report, output_file)
    
    return report

def extract_all_materials(project_data: Dict, verbose: bool = False) -> Dict[str, Dict]:
    """
    Extract all materials from the project's media pool.
    
    Args:
        project_data: The parsed CapCut project data
        verbose: Whether to print detailed information
        
    Returns:
        A dictionary mapping material IDs to material info
    """
    all_materials = {}
    material_types = defaultdict(int)
    
    if 'materials' in project_data:
        materials = project_data['materials']
        
        # Extract video materials
        if 'videos' in materials and isinstance(materials['videos'], list):
            for video in materials['videos']:
                if 'id' in video and 'path' in video:
                    material_id = video['id']
                    material_path = video['path']
                    material_name = os.path.basename(material_path)
                    material_types['video'] += 1
                    
                    all_materials[material_id] = {
                        'id': material_id,
                        'path': material_path,
                        'name': material_name,
                        'type': 'video',
                        'duration': video.get('duration', 0) / 1000000 if 'duration' in video else None,  # Convert to seconds
                        'size': video.get('size', None)
                    }
        
        # Extract audio materials
        if 'audios' in materials and isinstance(materials['audios'], list):
            for audio in materials['audios']:
                if 'id' in audio and 'path' in audio:
                    material_id = audio['id']
                    material_path = audio['path']
                    material_name = os.path.basename(material_path)
                    material_types['audio'] += 1
                    
                    all_materials[material_id] = {
                        'id': material_id,
                        'path': material_path,
                        'name': material_name,
                        'type': 'audio',
                        'duration': audio.get('duration', 0) / 1000000 if 'duration' in audio else None,  # Convert to seconds
                        'size': audio.get('size', None)
                    }
        
        # Extract image materials
        if 'images' in materials and isinstance(materials['images'], list):
            for image in materials['images']:
                if 'id' in image and 'path' in image:
                    material_id = image['id']
                    material_path = image['path']
                    material_name = os.path.basename(material_path)
                    material_types['image'] += 1
                    
                    all_materials[material_id] = {
                        'id': material_id,
                        'path': material_path,
                        'name': material_name,
                        'type': 'image',
                        'size': image.get('size', None)
                    }
        
        # Extract sticker/effect materials if present
        for material_type in ['stickers', 'effects', 'texts', 'transitions']:
            if material_type in materials and isinstance(materials[material_type], list):
                for item in materials[material_type]:
                    if 'id' in item:
                        material_id = item['id']
                        material_path = item.get('path', None)
                        material_name = os.path.basename(material_path) if material_path else item.get('name', f"Unnamed {material_type}")
                        material_types[material_type] += 1
                        
                        all_materials[material_id] = {
                            'id': material_id,
                            'path': material_path,
                            'name': material_name,
                            'type': material_type
                        }
    
    if verbose:
        print("\n=== MATERIALS INVENTORY ===")
        print(f"Found {len(all_materials)} total materials:")
        for material_type, count in material_types.items():
            print(f"  - {material_type}: {count}")
    
    return all_materials

def extract_used_materials(project_data: Dict, verbose: bool = False) -> Dict[str, Dict]:
    """
    Extract all materials actually used in the timeline.
    
    Args:
        project_data: The parsed CapCut project data
        verbose: Whether to print detailed information
        
    Returns:
        A dictionary mapping material IDs to usage info
    """
    used_materials = {}
    usage_count = defaultdict(int)
    
    # Find all material_id references in tracks/segments
    if 'tracks' in project_data and isinstance(project_data['tracks'], list):
        for track_idx, track in enumerate(project_data['tracks']):
            track_type = track.get('type', 'unknown')
            
            if 'segments' in track and isinstance(track['segments'], list):
                for segment_idx, segment in enumerate(track['segments']):
                    # Check if segment has a material_id
                    if 'material_id' in segment:
                        material_id = segment['material_id']
                        usage_count[material_id] += 1
                        
                        # Extract timeline and source positioning info
                        timeline_start = None
                        timeline_duration = None
                        
                        if 'target_timerange' in segment:
                            timerange = segment['target_timerange']
                            if isinstance(timerange, dict):
                                timeline_start = timerange.get('start', 0) / 1000000  # Convert to seconds
                                timeline_duration = timerange.get('duration', 0) / 1000000  # Convert to seconds
                        
                        # Extract source timerange if available
                        source_start = None
                        source_duration = None
                        
                        if 'source_timerange' in segment:
                            timerange = segment['source_timerange']
                            if isinstance(timerange, dict):
                                source_start = timerange.get('start', 0) / 1000000  # Convert to seconds
                                source_duration = timerange.get('duration', 0) / 1000000  # Convert to seconds
                        
                        # Add or update usage info
                        if material_id not in used_materials:
                            used_materials[material_id] = {
                                'id': material_id,
                                'usage_count': 1,
                                'timeline_occurrences': []
                            }
                        else:
                            used_materials[material_id]['usage_count'] += 1
                        
                        # Add this occurrence
                        used_materials[material_id]['timeline_occurrences'].append({
                            'track_idx': track_idx,
                            'track_type': track_type,
                            'segment_idx': segment_idx,
                            'timeline_start': timeline_start,
                            'timeline_duration': timeline_duration,
                            'source_start': source_start,
                            'source_duration': source_duration
                        })
    
    if verbose:
        print("\n=== TIMELINE USAGE ===")
        print(f"Found {len(used_materials)} materials used in the timeline")
        print("Top 5 most used materials:")
        for material_id, count in sorted(usage_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - Material ID {material_id}: {count} times")
    
    return used_materials

def identify_unused_materials(all_materials: Dict, used_materials: Dict) -> Dict[str, Dict]:
    """
    Identify materials that are in the pool but not used in the timeline.
    
    Args:
        all_materials: Dictionary of all materials in the pool
        used_materials: Dictionary of materials used in the timeline
        
    Returns:
        Dictionary of unused materials
    """
    unused_materials = {}
    
    # Find materials that are in all_materials but not in used_materials
    for material_id, material_info in all_materials.items():
        if material_id not in used_materials:
            unused_materials[material_id] = material_info
    
    return unused_materials

def generate_report(all_materials: Dict, used_materials: Dict, unused_materials: Dict) -> Dict[str, Any]:
    """
    Generate a comprehensive report of material usage.
    
    Args:
        all_materials: Dictionary of all materials in the pool
        used_materials: Dictionary of materials used in the timeline
        unused_materials: Dictionary of unused materials
        
    Returns:
        Dictionary with report data
    """
    # Calculate some statistics
    total_materials = len(all_materials)
    used_count = len(used_materials)
    unused_count = len(unused_materials)
    
    # Calculate usage by type
    material_types = defaultdict(lambda: {'total': 0, 'used': 0, 'unused': 0})
    
    for material_id, material in all_materials.items():
        material_type = material.get('type', 'unknown')
        material_types[material_type]['total'] += 1
        
        if material_id in used_materials:
            material_types[material_type]['used'] += 1
        else:
            material_types[material_type]['unused'] += 1
    
    # For each unused material, add reference to the original material info
    enhanced_unused_materials = {}
    for material_id, unused_material in unused_materials.items():
        # Copy the original material info
        enhanced_unused_materials[material_id] = {**unused_material}
    
    # For each used material, add reference to the original material info
    enhanced_used_materials = {}
    for material_id, used_material in used_materials.items():
        if material_id in all_materials:
            # Combine original material info with usage info
            enhanced_used_materials[material_id] = {
                **all_materials[material_id],
                'usage_count': used_material['usage_count'],
                'timeline_occurrences': used_material['timeline_occurrences']
            }
    
    # Create the report
    report = {
        'summary': {
            'total_materials': total_materials,
            'used_materials': used_count,
            'unused_materials': unused_count,
            'unused_percentage': round((unused_count / total_materials) * 100, 2) if total_materials > 0 else 0,
            'material_types': dict(material_types)
        },
        'used_materials': enhanced_used_materials,
        'unused_materials': enhanced_unused_materials
    }
    
    return report

def save_report(report: Dict[str, Any], output_file: str):
    """
    Save the report to a JSON file.
    
    Args:
        report: Report dictionary
        output_file: Path to save the report
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to {output_file}")

def display_summary(report: Dict[str, Any]):
    """
    Display a summary of the analysis results.
    
    Args:
        report: Report dictionary
    """
    summary = report['summary']
    
    print("\n=== MEDIA USAGE SUMMARY ===")
    print(f"Total materials in project: {summary['total_materials']}")
    print(f"Materials used in timeline: {summary['used_materials']}")
    print(f"Unused materials: {summary['unused_materials']} ({summary['unused_percentage']}%)")
    
    print("\nBreakdown by material type:")
    for material_type, counts in summary['material_types'].items():
        if counts['total'] > 0:
            unused_percentage = round((counts['unused'] / counts['total']) * 100, 2)
            print(f"  - {material_type}: {counts['total']} total, {counts['used']} used, {counts['unused']} unused ({unused_percentage}%)")
    
    print("\n=== UNUSED MATERIALS ===")
    for material_id, material in sorted(report['unused_materials'].items(), key=lambda x: x[1].get('type', '')):
        material_path = material.get('path', 'No path')
        material_name = material.get('name', os.path.basename(material_path) if material_path else f"Material {material_id}")
        material_type = material.get('type', 'unknown')
        
        print(f"  - [{material_type}] {material_name}")

def generate_cleanup_instructions(report: Dict[str, Any], output_file: str = None):
    """
    Generate instructions for cleaning up unused media.
    
    Args:
        report: Report dictionary
        output_file: Optional path to save the instructions
    """
    unused_materials = report['unused_materials']
    
    instructions = "# Unused Media Cleanup Instructions\n\n"
    instructions += "The following media files are in your project but are not used in the timeline.\n"
    instructions += "You can safely remove them to reduce project size.\n\n"
    
    # Group by type
    by_type = defaultdict(list)
    for material_id, material in unused_materials.items():
        material_type = material.get('type', 'unknown')
        by_type[material_type].append(material)
    
    for material_type, materials in sorted(by_type.items()):
        instructions += f"## {material_type.title()} Files\n\n"
        
        for material in sorted(materials, key=lambda x: x.get('name', '')):
            material_name = material.get('name', 'Unnamed')
            material_path = material.get('path', 'No path')
            
            instructions += f"- {material_name}\n"
            if material_path and material_path != 'No path':
                instructions += f"  Path: {material_path}\n"
        
        instructions += "\n"
    
    instructions += "## How to Remove Unused Media\n\n"
    instructions += "1. Open your CapCut project\n"
    instructions += "2. Go to the Media panel\n"
    instructions += "3. Right-click on each unused media file and select 'Remove'\n"
    instructions += "4. Save your project\n\n"
    instructions += "Note: This will reduce your project file size and clean up your media panel.\n"
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        print(f"Cleanup instructions saved to {output_file}")
    else:
        print(instructions)

def main():
    parser = argparse.ArgumentParser(description="Find unused media files in a CapCut project")
    parser.add_argument("--project", required=True, help="Path to CapCut draft_content.json file")
    parser.add_argument("--output", help="Output file for analysis report (JSON)")
    parser.add_argument("--instructions", help="Output file for cleanup instructions (Markdown)")
    parser.add_argument("--verbose", action="store_true", help="Print detailed information")
    
    args = parser.parse_args()
    
    try:
        # Run the analysis
        report = find_unused_media(args.project, args.output, args.verbose)
        
        # Display summary
        display_summary(report)
        
        # Generate cleanup instructions if requested
        if args.instructions:
            generate_cleanup_instructions(report, args.instructions)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
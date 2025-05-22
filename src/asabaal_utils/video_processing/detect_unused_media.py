#!/usr/bin/env python3
"""
Detect unused media files in a CapCut project.

This script provides a comprehensive analysis of unused media in a CapCut project,
identifying files that are in the project's media pool but not used in the timeline.
It can generate both JSON reports and HTML visualizations of the results.
"""

import json
import os
import sys
import argparse
from typing import Dict, List, Any, Set, Optional, Tuple
from collections import defaultdict
import datetime
import base64
from pathlib import Path
import shutil

def detect_unused_media(project_file: str, output_dir: Optional[str] = None, 
                       generate_html: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze a CapCut project to detect unused media files.
    
    Args:
        project_file: Path to the CapCut project file
        output_dir: Directory to save output files
        generate_html: Whether to generate an HTML report
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary with analysis results
    """
    print(f"Analyzing project file: {project_file}")
    
    # Create output directory if needed
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(project_file), "unused_media_analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the project data
    try:
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            print("Project file loaded successfully!")
    except Exception as e:
        print(f"Error loading project file: {str(e)}")
        sys.exit(1)
    
    # Step 1: Extract all media from the project
    all_media = extract_all_media(project_data, verbose)
    print(f"Found {len(all_media)} media files in the project")
    
    # Step 2: Extract all media used in the timeline
    used_media = extract_used_media(project_data, verbose)
    print(f"Found {len(used_media)} media files used in the timeline")
    
    # Step 3: Identify unused media
    unused_media = identify_unused_media(all_media, used_media)
    print(f"Found {len(unused_media)} potentially unused media files")
    
    # Step 4: Generate reports
    reports = generate_reports(all_media, used_media, unused_media, output_dir, generate_html)
    
    return {
        'all_media_count': len(all_media),
        'used_media_count': len(used_media),
        'unused_media_count': len(unused_media),
        'unused_media': unused_media,
        'reports': reports
    }

def extract_all_media(project_data: Dict[str, Any], verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Extract all media files referenced in the project.
    
    Args:
        project_data: The project data
        verbose: Whether to print verbose output
        
    Returns:
        List of media information dictionaries
    """
    all_media = []
    media_paths = set()  # Track paths to avoid duplicates
    
    # Method 1: Check 'materials' section (common in CapCut)
    if 'materials' in project_data and isinstance(project_data['materials'], dict):
        materials = project_data['materials']
        
        # Check for different media types
        for media_type in ['videos', 'audios', 'images']:
            if media_type in materials and isinstance(materials[media_type], list):
                for item in materials[media_type]:
                    if isinstance(item, dict):
                        media = extract_media_info(item, media_type.rstrip('s'))
                        if media and 'path' in media and media['path'] not in media_paths:
                            all_media.append(media)
                            media_paths.add(media['path'])
    
    # Method 2: Check 'mediaPool' or similar sections
    for pool_key in ['mediaPool', 'media_pool', 'resources', 'assets']:
        if pool_key in project_data and isinstance(project_data[pool_key], list):
            for item in project_data[pool_key]:
                if isinstance(item, dict):
                    media = extract_media_info(item)
                    if media and 'path' in media and media['path'] not in media_paths:
                        all_media.append(media)
                        media_paths.add(media['path'])
    
    # Method 3: Search recursively for media-like objects
    if verbose and not all_media:
        print("No standard media pools found, searching recursively...")
        
    recursive_media = find_media_objects_recursive(project_data)
    for item in recursive_media:
        media = extract_media_info(item)
        if media and 'path' in media and media['path'] not in media_paths:
            all_media.append(media)
            media_paths.add(media['path'])
    
    # Group by type and print summary
    if verbose:
        type_counts = defaultdict(int)
        for media in all_media:
            type_counts[media.get('type', 'unknown')] += 1
        
        print("\nMedia types found:")
        for media_type, count in type_counts.items():
            print(f"  - {media_type}: {count} files")
    
    return all_media

def extract_media_info(item: Dict[str, Any], default_type: str = 'unknown') -> Dict[str, Any]:
    """
    Extract media information from a dictionary.
    
    Args:
        item: Dictionary that might represent a media file
        default_type: Default media type if not specified
        
    Returns:
        Media information dictionary or None if not a valid media item
    """
    # Check if this looks like a media item
    path = None
    for path_key in ['path', 'filePath', 'resourcePath', 'source', 'src', 'url']:
        if path_key in item:
            if isinstance(item[path_key], str):
                path = item[path_key]
                break
            elif item[path_key] is not None:
                # Convert non-string path to string if possible
                try:
                    path = str(item[path_key])
                    break
                except:
                    continue
    
    if not path:
        return None
    
    # Get media type
    media_type = item.get('type', default_type)
    if media_type == 'unknown':
        # Try to determine from file extension
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.mkv']:
            media_type = 'video'
        elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
            media_type = 'audio'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            media_type = 'image'
    
    # Create media info
    media_info = {
        'id': item.get('id', None),
        'path': path,
        'name': os.path.basename(path),
        'type': media_type
    }
    
    # Add duration if available
    if 'duration' in item:
        duration = item['duration']
        # Convert to seconds if in microseconds
        if duration > 10000:  # Likely in microseconds
            duration /= 1000000
        media_info['duration'] = duration
    
    # Add additional metadata
    for key in ['width', 'height', 'size']:
        if key in item:
            media_info[key] = item[key]
    
    return media_info

def find_media_objects_recursive(data: Any, path: str = "") -> List[Dict[str, Any]]:
    """
    Recursively search for objects that look like media items.
    
    Args:
        data: Data to search
        path: Current path in the data structure
        
    Returns:
        List of potential media item dictionaries
    """
    results = []
    
    if isinstance(data, dict):
        # Check if this dictionary looks like a media item
        has_path = any(key in data for key in ['path', 'filePath', 'resourcePath', 'source'])
        has_type = 'type' in data or 'mediaType' in data
        
        if has_path and (has_type or 'id' in data):
            results.append(data)
        
        # Recurse into children
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else key
            child_results = find_media_objects_recursive(value, child_path)
            results.extend(child_results)
    
    elif isinstance(data, list):
        # Recurse into list items
        for i, item in enumerate(data):
            child_path = f"{path}[{i}]"
            child_results = find_media_objects_recursive(item, child_path)
            results.extend(child_results)
    
    return results

def extract_used_media(project_data: Dict[str, Any], verbose: bool = False) -> Set[str]:
    """
    Extract all media files actually used in the timeline.
    
    Args:
        project_data: The project data
        verbose: Whether to print verbose output
        
    Returns:
        Set of used media paths and filenames
    """
    used_media_paths = set()
    
    # Method 1: Check tracks and segments
    if 'tracks' in project_data and isinstance(project_data['tracks'], list):
        for track in project_data['tracks']:
            if not isinstance(track, dict):
                continue
                
            # Look for segments
            for segments_key in ['segments', 'clips', 'items', 'content']:
                if segments_key in track and isinstance(track[segments_key], list):
                    for segment in track[segments_key]:
                        if not isinstance(segment, dict):
                            continue
                            
                        # Check for material_id reference
                        if 'material_id' in segment:
                            material_id = segment['material_id']
                            # Find corresponding material in materials section
                            if 'materials' in project_data and isinstance(project_data['materials'], dict):
                                for media_type in ['videos', 'audios', 'images']:
                                    if media_type in project_data['materials'] and isinstance(project_data['materials'][media_type], list):
                                        for item in project_data['materials'][media_type]:
                                            if isinstance(item, dict) and item.get('id') == material_id:
                                                for path_key in ['path', 'filePath', 'resourcePath', 'source']:
                                                    if path_key in item:
                                                        path = item[path_key]
                                                        if isinstance(path, (str, bytes, os.PathLike)):
                                                            used_media_paths.add(path)
                                                            used_media_paths.add(os.path.basename(path))
                        
                        # Check for direct path reference
                        for path_key in ['material_path', 'path', 'source', 'filePath', 'resourcePath']:
                            if path_key in segment and isinstance(segment[path_key], str):
                                path = segment[path_key]
                                if isinstance(path, (str, bytes, os.PathLike)):
                                    used_media_paths.add(path)
                                    used_media_paths.add(os.path.basename(path))
    
    # Method 2: Recursively search for segment-like objects with material references
    if verbose and not used_media_paths:
        print("No standard tracks/segments found, searching recursively...")
    
    segments = find_segments_recursive(project_data)
    for segment in segments:
        # Check for material_id reference
        if 'material_id' in segment:
            material_id = segment['material_id']
            material_path = find_material_path_by_id(project_data, material_id)
            if material_path:
                if isinstance(material_path, (str, bytes, os.PathLike)):
                    used_media_paths.add(material_path)
                    used_media_paths.add(os.path.basename(material_path))
        
        # Check for direct path reference
        for path_key in ['material_path', 'path', 'source', 'filePath', 'resourcePath']:
            if path_key in segment and isinstance(segment[path_key], str):
                path = segment[path_key]
                if isinstance(path, (str, bytes, os.PathLike)):
                    used_media_paths.add(path)
                    used_media_paths.add(os.path.basename(path))
    
    if verbose:
        print(f"Found {len(used_media_paths)} unique media references in the timeline")
    
    return used_media_paths

def find_segments_recursive(data: Any, path: str = "") -> List[Dict[str, Any]]:
    """
    Recursively search for objects that look like segments/clips.
    
    Args:
        data: Data to search
        path: Current path in the data structure
        
    Returns:
        List of potential segment dictionaries
    """
    segments = []
    
    if isinstance(data, dict):
        # Check if this dictionary looks like a segment
        time_indicators = ['start', 'duration', 'timeRange', 'target_timerange', 'source_timerange']
        material_indicators = ['material_id', 'material_path', 'source']
        
        has_time = any(key in data for key in time_indicators)
        has_material = any(key in data for key in material_indicators)
        
        if has_time and has_material:
            segments.append(data)
        
        # Recurse into children
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else key
            child_segments = find_segments_recursive(value, child_path)
            segments.extend(child_segments)
    
    elif isinstance(data, list):
        # Recurse into list items
        for i, item in enumerate(data):
            child_path = f"{path}[{i}]"
            child_segments = find_segments_recursive(item, child_path)
            segments.extend(child_segments)
    
    return segments

def find_material_path_by_id(project_data: Dict[str, Any], material_id: str) -> Optional[str]:
    """
    Find the file path for a material by its ID.
    
    Args:
        project_data: The project data
        material_id: The material ID to find
        
    Returns:
        File path or None if not found
    """
    # Check materials section
    if 'materials' in project_data and isinstance(project_data['materials'], dict):
        for media_type in ['videos', 'audios', 'images']:
            if media_type in project_data['materials'] and isinstance(project_data['materials'][media_type], list):
                for item in project_data['materials'][media_type]:
                    if isinstance(item, dict) and item.get('id') == material_id:
                        for path_key in ['path', 'filePath', 'resourcePath', 'source']:
                            if path_key in item:
                                return item[path_key]
    
    # Try recursive search
    def search_recursive(data):
        if isinstance(data, dict):
            if data.get('id') == material_id:
                for path_key in ['path', 'filePath', 'resourcePath', 'source']:
                    if path_key in data:
                        return data[path_key]
            
            for value in data.values():
                result = search_recursive(value)
                if result:
                    return result
        
        elif isinstance(data, list):
            for item in data:
                result = search_recursive(item)
                if result:
                    return result
        
        return None
    
    return search_recursive(project_data)

def identify_unused_media(all_media: List[Dict[str, Any]], used_media_paths: Set[str]) -> List[Dict[str, Any]]:
    """
    Identify media files that are in the project but not used in the timeline.
    
    Args:
        all_media: List of all media information dictionaries
        used_media_paths: Set of used media paths and filenames
        
    Returns:
        List of unused media information dictionaries
    """
    unused_media = []
    
    for media in all_media:
        if 'path' not in media:
            continue
        
        path = media['path']
        filename = os.path.basename(path)
        
        # Check if the path or filename is in the used paths
        if path in used_media_paths or filename in used_media_paths:
            continue
        
        unused_media.append(media)
    
    return unused_media

def generate_reports(all_media: List[Dict[str, Any]], used_media: Set[str], 
                    unused_media: List[Dict[str, Any]], output_dir: str,
                    generate_html: bool) -> Dict[str, str]:
    """
    Generate reports for the analysis results.
    
    Args:
        all_media: List of all media information dictionaries
        used_media: Set of used media paths and filenames
        unused_media: List of unused media information dictionaries
        output_dir: Directory to save reports
        generate_html: Whether to generate an HTML report
        
    Returns:
        Dictionary with report file paths
    """
    reports = {}
    
    # Generate JSON report
    json_report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'stats': {
            'total_media': len(all_media),
            'used_media': len(used_media) // 2,  # Divide by 2 because we store both paths and filenames
            'unused_media': len(unused_media),
            'unused_percentage': round(len(unused_media) / len(all_media) * 100, 2) if all_media else 0
        },
        'unused_media': unused_media
    }
    
    json_path = os.path.join(output_dir, 'unused_media_report.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2)
    
    reports['json'] = json_path
    print(f"JSON report saved to {json_path}")
    
    # Generate Markdown report
    md_content = "# Unused Media Report\n\n"
    md_content += f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md_content += "## Summary\n\n"
    md_content += f"- Total media files in project: {len(all_media)}\n"
    md_content += f"- Media files used in timeline: {len(used_media) // 2}\n"
    md_content += f"- Unused media files: {len(unused_media)} ({json_report['stats']['unused_percentage']}%)\n\n"
    
    # Group by type
    by_type = defaultdict(list)
    for media in unused_media:
        media_type = media.get('type', 'unknown')
        by_type[media_type].append(media)
    
    md_content += "## Unused Media Files\n\n"
    for media_type, media_list in by_type.items():
        md_content += f"### {media_type.title()} Files ({len(media_list)})\n\n"
        
        for media in sorted(media_list, key=lambda x: x.get('name', '')):
            name = media.get('name', 'Unknown')
            path = media.get('path', 'Unknown')
            duration = media.get('duration')
            
            md_content += f"- **{name}**\n"
            md_content += f"  - Path: `{path}`\n"
            if duration is not None:
                md_content += f"  - Duration: {duration:.2f}s\n"
            md_content += "\n"
    
    md_content += "## How to Clean Up\n\n"
    md_content += "1. Open your CapCut project\n"
    md_content += "2. Go to the Media panel\n"
    md_content += "3. Right-click on each unused media file and select 'Remove'\n"
    md_content += "4. Save your project\n\n"
    md_content += "This will reduce your project file size and clean up your media panel.\n"
    
    md_path = os.path.join(output_dir, 'unused_media_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    reports['markdown'] = md_path
    print(f"Markdown report saved to {md_path}")
    
    # Generate HTML report if requested
    if generate_html:
        html_path = os.path.join(output_dir, 'unused_media_report.html')
        generate_html_report(all_media, used_media, unused_media, html_path)
        reports['html'] = html_path
        print(f"HTML report saved to {html_path}")
    
    return reports

def generate_html_report(all_media: List[Dict[str, Any]], used_media: Set[str],
                       unused_media: List[Dict[str, Any]], output_file: str):
    """
    Generate an HTML report with visualization of unused media.
    
    Args:
        all_media: List of all media information dictionaries
        used_media: Set of used media paths and filenames
        unused_media: List of unused media information dictionaries
        output_file: Path to save the HTML report
    """
    # Group by type
    by_type = defaultdict(list)
    for media in unused_media:
        media_type = media.get('type', 'unknown')
        by_type[media_type].append(media)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unused Media Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #222;
            --text-color: #eee;
            --card-bg: #333;
            --card-border: #444;
        }}
        
        body {{ 
            padding: 20px; 
            background-color: var(--bg-color); 
            color: var(--text-color);
        }}
        .navbar {{ margin-bottom: 20px; }}
        .card {{ background-color: var(--card-bg); border-color: var(--card-border); margin-bottom: 20px; }}
        .card-body {{ color: var(--text-color); }}
        .stats-card {{ margin-bottom: 20px; }}
        .table {{ color: var(--text-color); }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand">Unused Media Report</span>
            <div class="navbar-text">
                Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </nav>
    
    <div class="container-fluid">
        <!-- Stats Card -->
        <div class="row stats-card">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Media Usage Statistics</h5>
                        <div class="row">
                            <div class="col-md-4">
                                <p><strong>Total Media Files:</strong> {len(all_media)}</p>
                            </div>
                            <div class="col-md-4">
                                <p><strong>Used Media Files:</strong> {len(used_media) // 2}</p>
                            </div>
                            <div class="col-md-4">
                                <p><strong class="text-warning">Unused Media Files:</strong> {len(unused_media)} ({round(len(unused_media) / len(all_media) * 100, 2) if all_media else 0}%)</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Unused Media Section -->
        <h3>Unused Media Files</h3>
        <p class="text-muted">These files are in your project but are not used in the timeline</p>
"""
    
    # Add a card for each media type
    for media_type, media_list in by_type.items():
        html += f"""
        <div class="card mb-4">
            <div class="card-header bg-warning">
                <h5 class="card-title mb-0 text-dark">Unused {media_type.title()} Files ({len(media_list)})</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped table-dark">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Path</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
"""
        
        for media in sorted(media_list, key=lambda x: x.get('name', '')):
            name = media.get('name', 'Unknown')
            path = media.get('path', 'Unknown')
            duration = media.get('duration', None)
            duration_str = f"{duration:.2f}s" if duration is not None else "N/A"
            
            html += f"""
                            <tr>
                                <td>{name}</td>
                                <td>{path}</td>
                                <td>{duration_str}</td>
                            </tr>
"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
"""
    
    # Add cleanup instructions
    html += """
        <div class="card mb-4">
            <div class="card-header bg-info">
                <h5 class="card-title mb-0 text-dark">How to Clean Up Unused Media</h5>
            </div>
            <div class="card-body">
                <ol>
                    <li>Open your CapCut project</li>
                    <li>Go to the Media panel</li>
                    <li>Right-click on each unused media file and select 'Remove'</li>
                    <li>Save your project</li>
                </ol>
                <p>This will reduce your project file size and clean up your media panel.</p>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    
    # Save HTML report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    parser = argparse.ArgumentParser(description="Detect unused media files in CapCut projects")
    parser.add_argument("project_file", help="Path to the CapCut project file (usually draft_content.json)")
    parser.add_argument("--output", "-o", help="Directory to save output files")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    
    args = parser.parse_args()
    
    detect_unused_media(args.project_file, args.output, args.html, args.verbose)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Interactive visualization tool for CapCut project structure.

This script creates an interactive web-based visualization of a CapCut project's
structure, allowing users to explore the project, see relationships between
components, and understand how media files are used.
"""

import json
import os
import sys
import argparse
from typing import Dict, List, Any, Set, Optional, Tuple
import datetime
import webbrowser
from pathlib import Path
import shutil
import re
import math
from collections import defaultdict
import base64

def visualize_project_structure(project_file: str, output_dir: Optional[str] = None, 
                             open_browser: bool = True, verbose: bool = False):
    """
    Create an interactive visualization of a CapCut project structure.
    
    Args:
        project_file: Path to the CapCut project file
        output_dir: Directory to save visualization files
        open_browser: Whether to open the visualization in a browser
        verbose: Whether to print verbose output
    """
    print(f"Analyzing project file: {project_file}")
    
    # Create output directory if needed
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(project_file), "project_visualization")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the project data
    try:
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            print("Project file loaded successfully!")
    except Exception as e:
        print(f"Error loading project file: {str(e)}")
        sys.exit(1)
    
    # Get project file size for display
    file_size = os.path.getsize(project_file) / (1024 * 1024)  # Convert to MB
    
    # Analyze the project structure
    print("Analyzing project structure...")
    structure_data = analyze_project_structure(project_data, verbose)
    
    # Build visualization assets
    asset_dir = os.path.join(output_dir, "assets")
    os.makedirs(asset_dir, exist_ok=True)
    
    # Copy required libraries
    copy_visualization_assets(asset_dir)
    
    # Generate the visualization HTML
    html_file = os.path.join(output_dir, "project_structure.html")
    generate_visualization_html(
        project_data,
        structure_data,
        html_file,
        os.path.basename(project_file),
        file_size
    )
    
    print(f"Visualization created at: {html_file}")
    
    # Open in browser if requested
    if open_browser:
        try:
            webbrowser.open(f"file://{os.path.abspath(html_file)}")
            print("Visualization opened in browser")
        except Exception as e:
            print(f"Couldn't open browser automatically: {str(e)}")
            print(f"Please open {html_file} manually in your browser")

def analyze_project_structure(project_data: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze the project structure to extract visualization data.
    
    Args:
        project_data: The project data
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary with structure analysis data
    """
    # Extract top-level structure
    top_level = {
        "name": "Project Root",
        "children": []
    }
    
    # Add top-level keys
    for key, value in project_data.items():
        node = {"name": key}
        
        if isinstance(value, dict):
            node["size"] = len(value)
            node["type"] = "object"
            node["children"] = []
            for subkey in list(value.keys())[:10]:  # Limit to first 10 keys
                subvalue = value[subkey]
                size = get_size_estimate(subvalue)
                child = {
                    "name": subkey,
                    "size": size,
                    "type": get_type_name(subvalue)
                }
                node["children"].append(child)
            
            if len(value) > 10:
                node["children"].append({
                    "name": f"... {len(value) - 10} more items",
                    "size": 1,
                    "type": "ellipsis"
                })
                
        elif isinstance(value, list):
            node["size"] = len(value)
            node["type"] = "array"
            if value and len(value) > 0:
                # Add sample items
                node["children"] = []
                for i, item in enumerate(value[:5]):  # Limit to first 5 items
                    size = get_size_estimate(item)
                    child = {
                        "name": f"[{i}]",
                        "size": size,
                        "type": get_type_name(item)
                    }
                    node["children"].append(child)
                
                if len(value) > 5:
                    node["children"].append({
                        "name": f"... {len(value) - 5} more items",
                        "size": 1,
                        "type": "ellipsis"
                    })
        else:
            node["size"] = get_size_estimate(value)
            node["type"] = get_type_name(value)
            
        top_level["children"].append(node)
    
    # Extract media information
    media_info = extract_media_info(project_data)
    
    # Extract timeline information
    timeline_info = extract_timeline_info(project_data)
    
    # Build relationships
    relationships = build_relationships(project_data, media_info, timeline_info)
    
    return {
        "structure": top_level,
        "media_info": media_info,
        "timeline_info": timeline_info,
        "relationships": relationships
    }

def get_size_estimate(obj: Any) -> int:
    """
    Get a size estimate for an object.
    
    Args:
        obj: The object to estimate size for
        
    Returns:
        Size estimate (for visualization purposes)
    """
    if isinstance(obj, dict):
        return len(obj)
    elif isinstance(obj, list):
        return len(obj)
    elif isinstance(obj, str):
        return min(len(obj) // 10, 100)  # Scale down string length
    else:
        return 1

def get_type_name(obj: Any) -> str:
    """
    Get a descriptive type name for an object.
    
    Args:
        obj: The object to get type for
        
    Returns:
        Type name
    """
    if isinstance(obj, dict):
        return "object"
    elif isinstance(obj, list):
        return "array"
    elif isinstance(obj, str):
        if len(obj) > 100:
            return "longtext"
        return "text"
    elif isinstance(obj, int):
        return "number"
    elif isinstance(obj, float):
        return "float"
    elif isinstance(obj, bool):
        return "boolean"
    elif obj is None:
        return "null"
    else:
        return type(obj).__name__

def extract_media_info(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract media information from the project.
    
    Args:
        project_data: The project data
        
    Returns:
        Dictionary with media information
    """
    media_items = []
    media_paths = set()
    
    # Method 1: Check 'materials' section (common in CapCut)
    if 'materials' in project_data and isinstance(project_data['materials'], dict):
        materials = project_data['materials']
        
        # Check for different media types
        for media_type in ['videos', 'audios', 'images']:
            if media_type in materials and isinstance(materials[media_type], list):
                for idx, item in enumerate(materials[media_type]):
                    if isinstance(item, dict):
                        # Extract media path
                        media_path = None
                        for path_key in ['path', 'filePath', 'resourcePath', 'source']:
                            if path_key in item:
                                media_path = item[path_key]
                                break
                        
                        if not media_path:
                            continue
                            
                        if media_path in media_paths:
                            continue
                            
                        media_paths.add(media_path)
                        
                        # Create media item
                        media_item = {
                            "id": item.get('id', f"{media_type}_{idx}"),
                            "path": media_path,
                            "name": os.path.basename(media_path),
                            "type": media_type.rstrip('s'),  # Remove trailing 's'
                            "duration": item.get('duration', None),
                            "location": f"materials.{media_type}[{idx}]"
                        }
                        
                        media_items.append(media_item)
    
    # Method 2: Check other possible locations
    for pool_key in ['mediaPool', 'media_pool', 'resources', 'assets']:
        if pool_key in project_data and isinstance(project_data[pool_key], list):
            for idx, item in enumerate(project_data[pool_key]):
                if isinstance(item, dict):
                    # Extract media path
                    media_path = None
                    for path_key in ['path', 'filePath', 'resourcePath', 'source']:
                        if path_key in item:
                            media_path = item[path_key]
                            break
                    
                    if not media_path or media_path in media_paths:
                        continue
                        
                    media_paths.add(media_path)
                    
                    # Determine media type
                    media_type = item.get('type', 'unknown')
                    if media_type == 'unknown':
                        ext = os.path.splitext(media_path)[1].lower()
                        if ext in ['.mp4', '.mov', '.avi', '.mkv']:
                            media_type = 'video'
                        elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
                            media_type = 'audio'
                        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                            media_type = 'image'
                    
                    # Create media item
                    media_item = {
                        "id": item.get('id', f"{pool_key}_{idx}"),
                        "path": media_path,
                        "name": os.path.basename(media_path),
                        "type": media_type,
                        "duration": item.get('duration', None),
                        "location": f"{pool_key}[{idx}]"
                    }
                    
                    media_items.append(media_item)
    
    # Group by type
    by_type = defaultdict(list)
    for media in media_items:
        by_type[media['type']].append(media)
    
    # Calculate stats
    total_count = len(media_items)
    type_counts = {media_type: len(items) for media_type, items in by_type.items()}
    
    return {
        "total_count": total_count,
        "type_counts": type_counts,
        "by_type": dict(by_type),
        "all_items": media_items
    }

def extract_timeline_info(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract timeline information from the project.
    
    Args:
        project_data: The project data
        
    Returns:
        Dictionary with timeline information
    """
    tracks = []
    clips = []
    
    # Find tracks in project
    if 'tracks' in project_data and isinstance(project_data['tracks'], list):
        for track_idx, track in enumerate(project_data['tracks']):
            if not isinstance(track, dict):
                continue
                
            track_info = {
                "id": track.get('id', f"track_{track_idx}"),
                "index": track_idx,
                "type": track.get('type', 'unknown'),
                "location": f"tracks[{track_idx}]"
            }
            
            tracks.append(track_info)
            
            # Find clips/segments in track
            for segments_key in ['segments', 'clips', 'items', 'content']:
                if segments_key in track and isinstance(track[segments_key], list):
                    for clip_idx, clip in enumerate(track[segments_key]):
                        if not isinstance(clip, dict):
                            continue
                            
                        # Extract timeline position
                        timeline_start = None
                        timeline_duration = None
                        
                        # Try different paths to timeline information
                        if 'target_timerange' in clip:
                            timerange = clip['target_timerange']
                            if isinstance(timerange, dict):
                                timeline_start = timerange.get('start')
                                timeline_duration = timerange.get('duration')
                        elif 'timeRange' in clip:
                            timerange = clip['timeRange']
                            if isinstance(timerange, dict):
                                timeline_start = timerange.get('start')
                                timeline_duration = timerange.get('duration')
                        elif 'start' in clip:
                            timeline_start = clip['start']
                            if 'duration' in clip:
                                timeline_duration = clip['duration']
                            elif 'end' in clip:
                                timeline_duration = clip['end'] - clip['start']
                        
                        # Extract media reference
                        material_id = clip.get('material_id', None)
                        media_path = None
                        
                        for path_key in ['material_path', 'path', 'source', 'filePath', 'resourcePath']:
                            if path_key in clip:
                                media_path = clip[path_key]
                                break
                        
                        # Create clip info
                        clip_info = {
                            "id": clip.get('id', f"clip_{track_idx}_{clip_idx}"),
                            "track_id": track_info['id'],
                            "track_index": track_idx,
                            "clip_index": clip_idx,
                            "material_id": material_id,
                            "media_path": media_path,
                            "timeline_start": timeline_start,
                            "timeline_duration": timeline_duration,
                            "location": f"tracks[{track_idx}].{segments_key}[{clip_idx}]"
                        }
                        
                        clips.append(clip_info)
    
    # Calculate stats
    total_tracks = len(tracks)
    total_clips = len(clips)
    
    track_types = defaultdict(int)
    for track in tracks:
        track_types[track['type']] += 1
    
    return {
        "total_tracks": total_tracks,
        "total_clips": total_clips,
        "track_types": dict(track_types),
        "tracks": tracks,
        "clips": clips
    }

def build_relationships(project_data: Dict[str, Any], 
                      media_info: Dict[str, Any],
                      timeline_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build relationships between project components.
    
    Args:
        project_data: The project data
        media_info: Media information
        timeline_info: Timeline information
        
    Returns:
        Dictionary with relationship information
    """
    relationships = []
    
    # Build media-to-clip relationships
    media_by_id = {media['id']: media for media in media_info['all_items']}
    media_by_path = {media['path']: media for media in media_info['all_items']}
    
    # Track used media
    used_media_ids = set()
    used_media_paths = set()
    
    for clip in timeline_info['clips']:
        source = None
        target = clip['id']
        source_type = None
        
        # Check for material_id reference
        if clip['material_id'] and clip['material_id'] in media_by_id:
            source = clip['material_id']
            source_type = 'id'
            used_media_ids.add(source)
        # Check for path reference
        elif clip['media_path'] and clip['media_path'] in media_by_path:
            source = clip['media_path']
            source_type = 'path'
            used_media_paths.add(source)
        
        if source:
            relationships.append({
                "source": source,
                "target": target,
                "type": "media_to_clip",
                "source_type": source_type
            })
    
    # Identify unused media
    unused_media = []
    
    for media in media_info['all_items']:
        is_used = False
        
        if media['id'] in used_media_ids:
            is_used = True
        
        if media['path'] in used_media_paths:
            is_used = True
        
        if not is_used:
            unused_media.append(media)
    
    return {
        "relationships": relationships,
        "used_media_ids": list(used_media_ids),
        "used_media_paths": list(used_media_paths),
        "unused_media": unused_media
    }

def copy_visualization_assets(asset_dir: str):
    """
    Copy required visualization assets to the output directory.
    
    Args:
        asset_dir: Directory to copy assets to
    """
    # We'll embed the required libraries in the HTML
    pass

def generate_visualization_html(project_data: Dict[str, Any],
                             structure_data: Dict[str, Any],
                             output_file: str,
                             project_filename: str,
                             file_size: float):
    """
    Generate the visualization HTML file.
    
    Args:
        project_data: The project data
        structure_data: Project structure analysis data
        output_file: Output HTML file path
        project_filename: Project file name
        file_size: Project file size in MB
    """
    # Prepare data for JSON embedding
    structure_json = json.dumps(structure_data['structure'])
    media_json = json.dumps(structure_data['media_info'])
    timeline_json = json.dumps(structure_data['timeline_info'])
    relationships_json = json.dumps(structure_data['relationships'])
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CapCut Project Structure Visualization</title>
    
    <!-- D3.js for visualization -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <!-- Bootstrap 5 for UI -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    
    <style>
        :root {{
            --bg-color: #111;
            --text-color: #eee;
            --card-bg: #222;
            --card-border: #333;
            --highlight-color: #3498db;
            --unused-color: #e74c3c;
            --used-color: #2ecc71;
            --audio-color: #9b59b6;
            --video-color: #f39c12;
            --image-color: #1abc9c;
        }}
        
        body {{ 
            background-color: var(--bg-color); 
            color: var(--text-color);
            padding-top: 60px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .navbar {{
            background-color: rgba(17, 17, 17, 0.9);
            backdrop-filter: blur(10px);
        }}
        
        .container-fluid {{
            padding: 20px;
        }}
        
        .card {{ 
            background-color: var(--card-bg); 
            border-color: var(--card-border);
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .nav-tabs {{
            border-bottom-color: var(--card-border);
        }}
        
        .nav-tabs .nav-link {{
            color: var(--text-color);
            border: none;
            border-bottom: 3px solid transparent;
            padding: 10px 15px;
            margin-right: 5px;
            border-radius: 0;
        }}
        
        .nav-tabs .nav-link:hover {{
            border-color: var(--highlight-color);
            background-color: rgba(52, 152, 219, 0.1);
        }}
        
        .nav-tabs .nav-link.active {{
            color: var(--highlight-color);
            background-color: transparent;
            border-bottom-color: var(--highlight-color);
        }}
        
        .tab-content {{
            padding: 20px 0;
        }}
        
        /* Visualization specific styles */
        .visualization {{
            width: 100%;
            height: 600px;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .tree-container {{
            width: 100%;
            height: 600px;
            overflow: auto;
        }}
        
        .node {{
            cursor: pointer;
        }}
        
        .node circle {{
            fill: var(--card-bg);
            stroke: var(--highlight-color);
            stroke-width: 2px;
        }}
        
        .node text {{
            font-size: 12px;
            fill: var(--text-color);
        }}
        
        .link {{
            fill: none;
            stroke: var(--card-border);
            stroke-width: 2px;
        }}
        
        /* Media gallery styles */
        .media-item {{
            padding: 10px;
            border-radius: 6px;
            background-color: rgba(255, 255, 255, 0.05);
            margin-bottom: 10px;
            transition: all 0.2s ease;
        }}
        
        .media-item:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }}
        
        .media-item.unused {{
            border-left: 4px solid var(--unused-color);
        }}
        
        .media-item.used {{
            border-left: 4px solid var(--used-color);
        }}
        
        .media-type-video {{
            color: var(--video-color);
        }}
        
        .media-type-audio {{
            color: var(--audio-color);
        }}
        
        .media-type-image {{
            color: var(--image-color);
        }}
        
        /* Timeline styles */
        .timeline-track {{
            height: 40px;
            background-color: rgba(255, 255, 255, 0.05);
            margin-bottom: 10px;
            border-radius: 6px;
            position: relative;
        }}
        
        .timeline-clip {{
            position: absolute;
            height: 100%;
            background-color: rgba(52, 152, 219, 0.3);
            border: 2px solid var(--highlight-color);
            border-radius: 4px;
            padding: 2px 5px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            font-size: 12px;
            display: flex;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .timeline-clip:hover {{
            background-color: rgba(52, 152, 219, 0.5);
            transform: scaleY(1.1);
            z-index: 10;
        }}
        
        /* Search styles */
        .search-container {{
            margin-bottom: 20px;
        }}
        
        .search-result {{
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 6px;
            background-color: rgba(255, 255, 255, 0.05);
            transition: all 0.2s ease;
        }}
        
        .search-result:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}
        
        .path-navigator {{
            font-family: monospace;
            cursor: pointer;
            color: var(--highlight-color);
        }}
        
        .path-navigator:hover {{
            text-decoration: underline;
        }}
        
        /* Tooltip */
        .tooltip-inner {{
            max-width: 300px;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
            padding: 10px;
            border-radius: 6px;
            text-align: left;
        }}
        
        /* Stats */
        .stats-card {{
            margin-bottom: 20px;
        }}
        
        .stats-number {{
            font-size: 24px;
            font-weight: bold;
        }}
        
        .stats-label {{
            font-size: 14px;
            opacity: 0.7;
        }}
        
        /* Json viewer */
        .json-viewer {{
            font-family: monospace;
            font-size: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 500px;
        }}
        
        .json-key {{
            color: #f8c555;
        }}
        
        .json-string {{
            color: #7ec699;
        }}
        
        .json-number {{
            color: #f08d49;
        }}
        
        .json-boolean {{
            color: #cc99cd;
        }}
        
        .json-null {{
            color: #999999;
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="fas fa-project-diagram me-2"></i>
                CapCut Project Explorer
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link active" href="#overview" data-bs-toggle="tab">Overview</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#structure" data-bs-toggle="tab">Structure</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#media" data-bs-toggle="tab">Media</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#timeline" data-bs-toggle="tab">Timeline</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#search" data-bs-toggle="tab">Search</a>
                    </li>
                </ul>
            </div>
            <span class="navbar-text">
                {project_filename} ({file_size:.2f} MB)
            </span>
        </div>
    </nav>
    
    <!-- Main content -->
    <div class="container-fluid">
        <div class="tab-content">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Project Overview</h5>
                                <p>This interactive visualization allows you to explore the structure of your CapCut project file.</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Stats Cards -->
                <div class="row">
                    <div class="col-md-3">
                        <div class="card stats-card">
                            <div class="card-body">
                                <div class="stats-number" id="stat-total-keys">0</div>
                                <div class="stats-label">Top-level Keys</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card">
                            <div class="card-body">
                                <div class="stats-number" id="stat-total-media">0</div>
                                <div class="stats-label">Media Files</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card">
                            <div class="card-body">
                                <div class="stats-number" id="stat-unused-media">0</div>
                                <div class="stats-label">Unused Media</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card">
                            <div class="card-body">
                                <div class="stats-number" id="stat-total-clips">0</div>
                                <div class="stats-label">Timeline Clips</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Visualizations Preview -->
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Structure Preview</h5>
                                <div class="visualization-preview" id="structure-preview"></div>
                                <div class="text-center mt-3">
                                    <button class="btn btn-primary" onclick="document.querySelector('.nav-link[href=`#structure`]').click()">
                                        <i class="fas fa-sitemap me-2"></i>
                                        Explore Full Structure
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Media Usage</h5>
                                <div class="visualization-preview" id="media-preview"></div>
                                <div class="text-center mt-3">
                                    <button class="btn btn-primary" onclick="document.querySelector('.nav-link[href=`#media`]').click()">
                                        <i class="fas fa-photo-video me-2"></i>
                                        Explore Media Files
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Structure Tab -->
            <div class="tab-pane fade" id="structure">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Project Structure</h5>
                                <div class="tree-container" id="tree-visualization"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Selected Node Details -->
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Selected Node Details</h5>
                                <div id="node-details">
                                    <p class="text-muted">Click on a node in the tree to view its details</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Media Tab -->
            <div class="tab-pane fade" id="media">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Media Files</h5>
                                
                                <!-- Media Type Filter -->
                                <div class="btn-group mb-3" role="group">
                                    <button type="button" class="btn btn-outline-primary active" data-media-filter="all">All</button>
                                    <button type="button" class="btn btn-outline-primary" data-media-filter="video">Video</button>
                                    <button type="button" class="btn btn-outline-primary" data-media-filter="audio">Audio</button>
                                    <button type="button" class="btn btn-outline-primary" data-media-filter="image">Image</button>
                                </div>
                                
                                <!-- Usage Filter -->
                                <div class="btn-group mb-3 ms-3" role="group">
                                    <button type="button" class="btn btn-outline-secondary active" data-usage-filter="all">All</button>
                                    <button type="button" class="btn btn-outline-secondary" data-usage-filter="used">Used</button>
                                    <button type="button" class="btn btn-outline-secondary" data-usage-filter="unused">Unused</button>
                                </div>
                                
                                <!-- Media List -->
                                <div class="media-list" id="media-list">
                                    <p class="text-muted">Loading media files...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Timeline Tab -->
            <div class="tab-pane fade" id="timeline">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Timeline</h5>
                                <div class="timeline-container" id="timeline-visualization"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Clip Details -->
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Selected Clip Details</h5>
                                <div id="clip-details">
                                    <p class="text-muted">Click on a clip in the timeline to view its details</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Search Tab -->
            <div class="tab-pane fade" id="search">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Search Project</h5>
                                <div class="search-container">
                                    <div class="input-group mb-3">
                                        <input type="text" class="form-control" id="search-input" placeholder="Search for keys, values, paths...">
                                        <button class="btn btn-primary" id="search-button">
                                            <i class="fas fa-search me-2"></i>
                                            Search
                                        </button>
                                    </div>
                                </div>
                                
                                <div id="search-results">
                                    <p class="text-muted">Enter a search term above</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Visualization Scripts -->
    <script>
        // Project data (embedded JSON)
        const structureData = {structure_json};
        const mediaInfo = {media_json};
        const timelineInfo = {timeline_json};
        const relationshipInfo = {relationships_json};
        
        // Raw project data for search and exploration
        const rawProjectData = structureData;
        
        // Initialize visualizations when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {{
            // Initialize stats
            updateStats();
            
            // Initialize structure visualization
            initializeStructureVisualization();
            
            // Initialize media view
            initializeMediaView();
            
            // Initialize timeline view
            initializeTimelineView();
            
            // Initialize search
            initializeSearch();
            
            // Initialize overview previews
            initializeOverviewPreviews();
            
            // Initialize tooltips
            initializeTooltips();
        }});
        
        function updateStats() {{
            // Update stats on the overview page
            document.getElementById('stat-total-keys').textContent = 
                structureData.children ? structureData.children.length : 0;
                
            document.getElementById('stat-total-media').textContent = 
                mediaInfo.total_count || 0;
                
            document.getElementById('stat-unused-media').textContent = 
                relationshipInfo.unused_media ? relationshipInfo.unused_media.length : 0;
                
            document.getElementById('stat-total-clips').textContent = 
                timelineInfo.total_clips || 0;
        }}
        
        function initializeStructureVisualization() {{
            // Create a tree visualization of the project structure
            const container = document.getElementById('tree-visualization');
            
            // Set dimensions based on container size
            const width = container.clientWidth;
            const height = 600;
            
            // Create the SVG container
            const svg = d3.select(container).append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(40, 0)");
            
            // Create a tree layout
            const treeLayout = d3.tree().size([height, width - 160]);
            
            // Create a root hierarchy from the data
            const root = d3.hierarchy(structureData);
            
            // Assign x,y positions to nodes
            treeLayout(root);
            
            // Add links (edges)
            svg.selectAll(".link")
                .data(root.links())
                .enter().append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x));
            
            // Add nodes
            const nodes = svg.selectAll(".node")
                .data(root.descendants())
                .enter().append("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`)
                .on("click", function(event, d) {{
                    // Show node details when clicked
                    showNodeDetails(d);
                }});
            
            // Add circles to nodes
            nodes.append("circle")
                .attr("r", d => {{
                    // Size based on number of children or data size
                    if (d.children) return Math.min(5 + d.children.length, 10);
                    return d.data.size ? Math.min(3 + Math.sqrt(d.data.size), 8) : 4;
                }})
                .style("fill", d => {{
                    // Color based on node type
                    if (d.data.type === "object") return "#3498db";
                    if (d.data.type === "array") return "#2ecc71";
                    if (d.data.type === "text") return "#e67e22";
                    if (d.data.type === "longtext") return "#e74c3c";
                    if (d.data.type === "number") return "#f1c40f";
                    return "#9b59b6";
                }});
            
            // Add labels to nodes
            nodes.append("text")
                .attr("dy", ".35em")
                .attr("x", d => d.children ? -12 : 12)
                .style("text-anchor", d => d.children ? "end" : "start")
                .text(d => d.data.name)
                .style("font-size", "12px")
                .style("fill", "#eee");
            
            // Add tooltips
            nodes.append("title")
                .text(d => `${{d.data.name}}\nType: ${{d.data.type}}\nSize: ${{d.data.size || 'N/A'}}`);
        }}
        
        function showNodeDetails(node) {{
            // Display details for the selected node
            const detailsContainer = document.getElementById('node-details');
            
            let html = `<h6>${{node.data.name}}</h6>`;
            html += `<p><strong>Type:</strong> ${{node.data.type}}</p>`;
            
            if (node.data.size) {{
                html += `<p><strong>Size:</strong> ${{node.data.size}}</p>`;
            }}
            
            // Build path to this node
            const path = [];
            let current = node;
            while (current.parent) {{
                path.unshift(current.data.name);
                current = current.parent;
            }}
            
            const pathString = path.join('.');
            html += `<p><strong>Path:</strong> <code>${{pathString}}</code></p>`;
            
            // If this is an object or array with children, show preview
            if (node.data.children && node.data.children.length > 0) {{
                html += `<p><strong>Children:</strong></p>`;
                html += `<ul>`;
                node.data.children.forEach(child => {{
                    html += `<li><code>${{child.name}}</code>: ${{child.type}}${{child.size ? ` (size: ${{child.size}})` : ''}}</li>`;
                }});
                html += `</ul>`;
            }}
            
            // Add value explorer for leaf nodes
            if (!node.children && node.data.type !== 'object' && node.data.type !== 'array') {{
                // Try to find the actual value in the raw data
                try {{
                    const pathParts = pathString.split('.');
                    let value = rawProjectData;
                    
                    for (const part of pathParts) {{
                        if (part.includes('[')) {{
                            // Handle array indices
                            const name = part.split('[')[0];
                            const index = parseInt(part.split('[')[1]);
                            value = value[name][index];
                        }} else {{
                            value = value[part];
                        }}
                    }}
                    
                    if (value !== undefined) {{
                        html += `<p><strong>Value:</strong></p>`;
                        html += `<div class="json-viewer">${{formatJsonValue(value)}}</div>`;
                    }}
                }} catch (e) {{
                    // If we can't find the value, just skip this part
                }}
            }}
            
            detailsContainer.innerHTML = html;
        }}
        
        function formatJsonValue(value) {{
            // Format a JSON value for display
            if (value === null) return '<span class="json-null">null</span>';
            
            switch (typeof value) {{
                case 'string':
                    // Truncate long strings
                    if (value.length > 500) {{
                        value = value.substring(0, 500) + '...';
                    }}
                    return `<span class="json-string">"${{escapeHtml(value)}}"</span>`;
                case 'number':
                    return `<span class="json-number">${{value}}</span>`;
                case 'boolean':
                    return `<span class="json-boolean">${{value}}</span>`;
                case 'object':
                    if (Array.isArray(value)) {{
                        if (value.length === 0) return '[]';
                        if (value.length > 10) {{
                            return `[Array with ${{value.length}} items]`;
                        }}
                        
                        let result = '[<br>';
                        value.slice(0, 10).forEach((item, index) => {{
                            result += '&nbsp;&nbsp;' + formatJsonValue(item);
                            if (index < value.length - 1) result += ',';
                            result += '<br>';
                        }});
                        if (value.length > 10) {{
                            result += `&nbsp;&nbsp;... ${{value.length - 10}} more items<br>`;
                        }}
                        result += ']';
                        return result;
                    }} else {{
                        const keys = Object.keys(value);
                        if (keys.length === 0) return '{{}}';
                        if (keys.length > 10) {{
                            return `{{Object with ${{keys.length}} properties}}`;
                        }}
                        
                        let result = '{{<br>';
                        keys.slice(0, 10).forEach((key, index) => {{
                            result += `&nbsp;&nbsp;<span class="json-key">"${{escapeHtml(key)}}"</span>: ` + formatJsonValue(value[key]);
                            if (index < keys.length - 1) result += ',';
                            result += '<br>';
                        }});
                        if (keys.length > 10) {{
                            result += `&nbsp;&nbsp;... ${{keys.length - 10}} more properties<br>`;
                        }}
                        result += '}}';
                        return result;
                    }}
                default:
                    return String(value);
            }}
        }}
        
        function escapeHtml(str) {{
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }}
        
        function initializeMediaView() {{
            // Populate the media list
            const mediaListContainer = document.getElementById('media-list');
            const mediaItems = mediaInfo.all_items || [];
            
            if (mediaItems.length === 0) {{
                mediaListContainer.innerHTML = '<p class="text-muted">No media files found in the project</p>';
                return;
            }}
            
            // Determine which media items are used
            const usedMediaIds = new Set(relationshipInfo.used_media_ids || []);
            const usedMediaPaths = new Set(relationshipInfo.used_media_paths || []);
            
            // Create HTML for each media item
            let html = '';
            
            mediaItems.forEach(media => {{
                // Determine if media is used
                const isUsed = usedMediaIds.has(media.id) || usedMediaPaths.has(media.path);
                const usageClass = isUsed ? 'used' : 'unused';
                const mediaTypeClass = `media-type-${{media.type}}`;
                
                // Create media item card
                html += `<div class="media-item ${{usageClass}}" data-media-type="${{media.type}}" data-media-usage="${{isUsed ? 'used' : 'unused'}}">`;
                html += `<div class="row">`;
                html += `<div class="col-md-1">`;
                html += `<i class="fas fa-${{media.type === 'video' ? 'video' : media.type === 'audio' ? 'music' : 'image'}} fa-2x ${{mediaTypeClass}}"></i>`;
                html += `</div>`;
                html += `<div class="col-md-11">`;
                html += `<h6>${{media.name}}</h6>`;
                html += `<p class="text-muted mb-0">${{media.path}}</p>`;
                
                // Add duration if available
                if (media.duration) {{
                    const formattedDuration = formatDuration(media.duration);
                    html += `<p class="mb-0"><small>Duration: ${{formattedDuration}}</small></p>`;
                }}
                
                // Add usage indicator
                if (isUsed) {{
                    html += `<span class="badge bg-success">Used in Timeline</span>`;
                }} else {{
                    html += `<span class="badge bg-danger">Unused</span>`;
                }}
                
                html += `</div>`;
                html += `</div>`;
                html += `</div>`;
            }});
            
            mediaListContainer.innerHTML = html;
            
            // Add event listeners to filter buttons
            document.querySelectorAll('[data-media-filter]').forEach(button => {{
                button.addEventListener('click', function() {{
                    // Update active button
                    document.querySelectorAll('[data-media-filter]').forEach(btn => {{
                        btn.classList.remove('active');
                    }});
                    this.classList.add('active');
                    
                    // Apply filter
                    const filterType = this.getAttribute('data-media-filter');
                    applyMediaFilters();
                }});
            }});
            
            document.querySelectorAll('[data-usage-filter]').forEach(button => {{
                button.addEventListener('click', function() {{
                    // Update active button
                    document.querySelectorAll('[data-usage-filter]').forEach(btn => {{
                        btn.classList.remove('active');
                    }});
                    this.classList.add('active');
                    
                    // Apply filter
                    applyMediaFilters();
                }});
            }});
        }}
        
        function applyMediaFilters() {{
            // Get selected filters
            const typeFilter = document.querySelector('[data-media-filter].active').getAttribute('data-media-filter');
            const usageFilter = document.querySelector('[data-usage-filter].active').getAttribute('data-usage-filter');
            
            // Apply filters to media items
            document.querySelectorAll('.media-item').forEach(item => {{
                const mediaType = item.getAttribute('data-media-type');
                const mediaUsage = item.getAttribute('data-media-usage');
                
                const matchesType = typeFilter === 'all' || mediaType === typeFilter;
                const matchesUsage = usageFilter === 'all' || mediaUsage === usageFilter;
                
                if (matchesType && matchesUsage) {{
                    item.style.display = '';
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }}
        
        function formatDuration(seconds) {{
            // Format duration in seconds to MM:SS or HH:MM:SS
            if (isNaN(seconds)) return 'N/A';
            
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            if (hours > 0) {{
                return `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }} else {{
                return `${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }}
        }}
        
        function initializeTimelineView() {{
            // Create a visual representation of the timeline
            const container = document.getElementById('timeline-visualization');
            const tracks = timelineInfo.tracks || [];
            const clips = timelineInfo.clips || [];
            
            if (tracks.length === 0 || clips.length === 0) {{
                container.innerHTML = '<p class="text-muted">No timeline data found in the project</p>';
                return;
            }}
            
            // Create tracks
            let html = '';
            
            tracks.forEach(track => {{
                html += `<div class="timeline-track" data-track-id="${{track.id}}">`;
                html += `<div class="track-label" style="position:absolute;left:0;top:0;background:#333;z-index:10;padding:2px 5px;border-radius:4px;">Track ${{track.index}} (${{track.type}})</div>`;
                html += `</div>`;
            }});
            
            container.innerHTML = html;
            
            // Find max timeline value for scaling
            const maxTimelineEnd = Math.max(...clips.map(clip => clip.timeline_start + clip.timeline_duration));
            
            // Add clips to tracks
            clips.forEach(clip => {{
                const trackElement = container.querySelector('[data-track-id="' + clip.track_id + '"]');
                if (!trackElement) return;
                
                // Skip clips without position info
                if (clip.timeline_start === null || clip.timeline_duration === null) return;
                
                // Calculate position
                const start = clip.timeline_start / maxTimelineEnd * 100;
                const width = clip.timeline_duration / maxTimelineEnd * 100;
                
                // Create clip element
                const clipElement = document.createElement('div');
                clipElement.className = 'timeline-clip';
                clipElement.setAttribute('data-clip-id', clip.id);
                clipElement.setAttribute('title', 'Clip ' + clip.clip_index);
                clipElement.style.left = `${{start}}%`;
                clipElement.style.width = `${{width}}%`;
                
                // Add material info if available
                if (clip.material_id || clip.media_path) {{
                    const mediaName = clip.media_path ? clip.media_path.split('/').pop() : 'Unknown';
                    clipElement.textContent = mediaName;
                }} else {{
                    clipElement.textContent = 'Clip ' + clip.clip_index;
                }}
                
                // Add click handler
                clipElement.addEventListener('click', function() {{
                    showClipDetails(clip);
                }});
                
                trackElement.appendChild(clipElement);
            }});
        }}
        
        function showClipDetails(clip) {{
            // Display details for the selected clip
            const detailsContainer = document.getElementById('clip-details');
            
            let html = '<h6>Clip ' + clip.clip_index + ' on Track ' + clip.track_index + '</h6>';
            
            // Add timeline position
            if (clip.timeline_start !== null && clip.timeline_duration !== null) {{
                const start = formatDuration(clip.timeline_start / 1000000);  // Convert from microseconds
                const duration = formatDuration(clip.timeline_duration / 1000000);
                const end = formatDuration((clip.timeline_start + clip.timeline_duration) / 1000000);
                
                html += '<p><strong>Timeline Position:</strong> ' + start + ' - ' + end + ' (Duration: ' + duration + ')</p>';
            }}
            
            // Add material info
            if (clip.material_id) {{
                html += '<p><strong>Material ID:</strong> ' + clip.material_id + '</p>';
            }}
            
            if (clip.media_path) {{
                html += '<p><strong>Media Path:</strong> ' + clip.media_path + '</p>';
            }}
            
            // Add location in project
            html += '<p><strong>Location:</strong> <code>' + clip.location + '</code></p>';
            
            // Add JSON data for the clip
            html += '<p><strong>Raw Data:</strong></p>';
            html += '<pre class="json-viewer">' + formatJsonValue(clip) + '</pre>';
            
            detailsContainer.innerHTML = html;
        }}
        
        function initializeSearch() {{
            // Initialize the search functionality
            const searchInput = document.getElementById('search-input');
            const searchButton = document.getElementById('search-button');
            const resultsContainer = document.getElementById('search-results');
            
            // Add event listeners
            searchButton.addEventListener('click', function() {{
                performSearch(searchInput.value);
            }});
            
            searchInput.addEventListener('keydown', function(event) {{
                if (event.key === 'Enter') {{
                    performSearch(searchInput.value);
                }}
            }});
            
            function performSearch(query) {{
                if (!query.trim()) {{
                    resultsContainer.innerHTML = '<p class="text-muted">Enter a search term above</p>';
                    return;
                }}
                
                // Convert to lowercase for case-insensitive search
                const searchTerm = query.trim().toLowerCase();
                
                // Perform search
                const results = searchInObject(rawProjectData, searchTerm);
                
                // Display results
                if (results.length === 0) {{
                    resultsContainer.innerHTML = '<p class="text-muted">No results found</p>';
                }} else {{
                    let html = `<p>Found ${{results.length}} matches for "${{query}}"</p>`;
                    
                    results.forEach(result => {{
                        html += `<div class="search-result">`;
                        html += `<p class="path-navigator" onclick="navigateToPath('${{result.path}}')"><code>${{result.path}}</code></p>`;
                        html += `<div>${{formatSearchResultValue(result.value, searchTerm)}}</div>`;
                        html += `</div>`;
                    }});
                    
                    resultsContainer.innerHTML = html;
                }}
            }}
            
            function searchInObject(obj, term, path = '', results = []) {{
                if (!obj || typeof obj !== 'object') return results;
                
                // Search in object properties
                if (!Array.isArray(obj)) {{
                    for (const key in obj) {{
                        const value = obj[key];
                        const currentPath = path ? `${{path}}.${{key}}` : key;
                        
                        // Check if key matches
                        if (key.toLowerCase().includes(term)) {{
                            results.push({{ path: currentPath, value: value }});
                        }}
                        
                        // Check if value matches (if it's a primitive)
                        if (typeof value === 'string' && value.toLowerCase().includes(term)) {{
                            results.push({{ path: currentPath, value: value }});
                        }} else if (typeof value === 'number' && String(value).includes(term)) {{
                            results.push({{ path: currentPath, value: value }});
                        }}
                        
                        // Recursively search in nested objects
                        if (value && typeof value === 'object') {{
                            searchInObject(value, term, currentPath, results);
                        }}
                    }}
                }} 
                // Search in arrays
                else {{
                    for (let i = 0; i < obj.length; i++) {{
                        const value = obj[i];
                        const currentPath = `${{path}}[${{i}}]`;
                        
                        // Check if value matches (if it's a primitive)
                        if (typeof value === 'string' && value.toLowerCase().includes(term)) {{
                            results.push({{ path: currentPath, value: value }});
                        }} else if (typeof value === 'number' && String(value).includes(term)) {{
                            results.push({{ path: currentPath, value: value }});
                        }}
                        
                        // Recursively search in nested objects
                        if (value && typeof value === 'object') {{
                            searchInObject(value, term, currentPath, results);
                        }}
                    }}
                }}
                
                return results;
            }}
        }}
        
        function formatSearchResultValue(value, term) {{
            if (value === null) return '<span class="json-null">null</span>';
            
            switch (typeof value) {{
                case 'string':
                    // Highlight the search term
                    const highlighted = escapeHtml(value).replace(
                        new RegExp(escapeRegExp(term), 'gi'),
                        match => `<mark>${{match}}</mark>`
                    );
                    
                    // Truncate long strings
                    if (value.length > 200) {{
                        // Find a window around the match
                        const matchIndex = value.toLowerCase().indexOf(term.toLowerCase());
                        const start = Math.max(0, matchIndex - 50);
                        const end = Math.min(value.length, matchIndex + term.length + 50);
                        
                        let displayValue = '';
                        if (start > 0) displayValue += '... ';
                        displayValue += highlighted.substring(start, end);
                        if (end < value.length) displayValue += ' ...';
                        
                        return `<span class="json-string">"${{displayValue}}"</span>`;
                    }}
                    
                    return `<span class="json-string">"${{highlighted}}"</span>`;
                    
                case 'number':
                    return `<span class="json-number">${{value}}</span>`;
                case 'boolean':
                    return `<span class="json-boolean">${{value}}</span>`;
                case 'object':
                    if (Array.isArray(value)) {{
                        return `[Array with ${{value.length}} items]`;
                    }} else {{
                        return `{{Object with ${{Object.keys(value).length}} properties}}`;
                    }}
                default:
                    return String(value);
            }}
        }}
        
        function escapeRegExp(string) {{
            return string.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&');
        }}
        
        function navigateToPath(path) {{
            // Navigate to a specific path in the project
            // This function will be called when clicking on a search result
            
            // Switch to the structure tab
            document.querySelector('.nav-link[href="#structure"]').click();
            
            // TODO: Implement path navigation in the structure view
            alert(`Navigation to path "${{path}}" is not yet implemented.`);
        }}
        
        function initializeOverviewPreviews() {{
            // Initialize the overview page preview visualizations
            
            // Structure preview (simplified version of the main visualization)
            const structurePreview = document.getElementById('structure-preview');
            structurePreview.style.height = '200px';
            
            // Create a simplified version of the structure visualization
            const width = structurePreview.clientWidth;
            const height = 200;
            
            // Create the SVG container
            const svg = d3.select(structurePreview).append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(40, 0)");
            
            // Create a simplified tree layout
            const treeLayout = d3.tree().size([height, width - 100]);
            
            // Create a root hierarchy from the data, but limit depth
            const root = d3.hierarchy(structureData);
            limitTreeDepth(root, 2);
            
            // Assign x,y positions to nodes
            treeLayout(root);
            
            // Add links (edges)
            svg.selectAll(".link")
                .data(root.links())
                .enter().append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x));
            
            // Add nodes
            const nodes = svg.selectAll(".node")
                .data(root.descendants())
                .enter().append("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`)
                .on("click", function(event, d) {{
                    // Switch to structure tab
                    document.querySelector('.nav-link[href="#structure"]').click();
                }});
            
            // Add circles to nodes
            nodes.append("circle")
                .attr("r", 4)
                .style("fill", d => {{
                    // Color based on node type
                    if (d.data.type === "object") return "#3498db";
                    if (d.data.type === "array") return "#2ecc71";
                    return "#9b59b6";
                }});
            
            // Add labels to nodes for first level only
            nodes.filter(d => d.depth <= 1)
                .append("text")
                .attr("dy", ".35em")
                .attr("x", d => d.children ? -8 : 8)
                .style("text-anchor", d => d.children ? "end" : "start")
                .text(d => d.data.name)
                .style("font-size", "10px")
                .style("fill", "#eee");
            
            // Media preview (pie chart of media usage)
            const mediaPreview = document.getElementById('media-preview');
            mediaPreview.style.height = '200px';
            
            // Create a pie chart of used vs unused media
            const usedCount = mediaInfo.total_count - relationshipInfo.unused_media.length;
            const unusedCount = relationshipInfo.unused_media.length;
            
            // Skip if no media
            if (mediaInfo.total_count === 0) {{
                mediaPreview.innerHTML = '<p class="text-muted text-center mt-5">No media files found</p>';
                return;
            }}
            
            // Create the SVG container
            const mediaSvg = d3.select(mediaPreview).append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", `translate(${{width / 2}}, ${{height / 2}})`);
            
            // Create a pie chart
            const pie = d3.pie().value(d => d.value);
            const data = pie([
                {{ name: 'Used', value: usedCount, color: '#2ecc71' }},
                {{ name: 'Unused', value: unusedCount, color: '#e74c3c' }}
            ]);
            
            const arcGenerator = d3.arc()
                .innerRadius(50)
                .outerRadius(80);
            
            // Add pie slices
            mediaSvg.selectAll('path')
                .data(data)
                .enter()
                .append('path')
                .attr('d', arcGenerator)
                .attr('fill', d => d.data.color)
                .attr('stroke', '#222')
                .attr('stroke-width', 1)
                .on("click", function(event, d) {{
                    // Switch to media tab
                    document.querySelector('.nav-link[href="#media"]').click();
                    
                    // Apply filter
                    const filterButton = document.querySelector(`[data-usage-filter="${{d.data.name.toLowerCase()}}"]`);
                    if (filterButton) filterButton.click();
                }});
            
            // Add labels
            mediaSvg.selectAll('text')
                .data(data)
                .enter()
                .append('text')
                .text(d => d.data.name + ': ' + d.data.value)
                .attr('transform', d => {{
                    const centroid = arcGenerator.centroid(d);
                    return `translate(${{centroid[0]}}, ${{centroid[1]}})`;
                }})
                .style('text-anchor', 'middle')
                .style('font-size', '12px')
                .style('fill', '#fff');
        }}
        
        function limitTreeDepth(node, maxDepth) {{
            // Limit the depth of a tree for visualization
            if (!node) return;
            
            if (node.depth === maxDepth) {{
                node.children = null;
            }} else if (node.children) {{
                node.children.forEach(child => limitTreeDepth(child, maxDepth));
            }}
        }}
        
        function initializeTooltips() {{
            // Initialize Bootstrap tooltips
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {{
                return new bootstrap.Tooltip(tooltipTriggerEl);
            }});
        }}
    </script>
</body>
</html>
"""
    
    # Save HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    parser = argparse.ArgumentParser(description="Interactive visualization of CapCut project structure")
    parser.add_argument("project_file", help="Path to the CapCut project file (usually draft_content.json)")
    parser.add_argument("--output", "-o", help="Directory to save visualization files")
    parser.add_argument("--no-browser", action="store_true", help="Don't open visualization in browser")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    
    args = parser.parse_args()
    
    visualize_project_structure(
        args.project_file, 
        args.output,
        not args.no_browser,
        args.verbose
    )

if __name__ == "__main__":
    main()
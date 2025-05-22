#!/usr/bin/env python3
"""
Analyze CapCut project file structure to understand where media pools and timeline clips are stored.

This script dissects a CapCut project file and identifies the key structures related to
media pools, used clips, and the overall project organization. It helps understand how
to correctly identify unused media in the project.
"""

import json
import os
import sys
import argparse
from typing import Dict, List, Any, Set, Optional, Tuple
from collections import defaultdict
import pprint

def analyze_project_structure(file_path: str, output_dir: Optional[str] = None, 
                             verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze the structure of a CapCut project file to understand its organization.
    
    Args:
        file_path: Path to the CapCut project file (usually draft_content.json)
        output_dir: Directory to save analysis results
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary with analysis results
    """
    print(f"Analyzing project file: {file_path}")
    print(f"File size: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
    
    # Load the project data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            print("JSON loaded successfully!")
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        sys.exit(1)
    
    # Create output directory if needed
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Analyze top-level structure
    top_level_keys = list(project_data.keys())
    print(f"\nProject has {len(top_level_keys)} top-level keys:")
    for key in sorted(top_level_keys):
        value = project_data[key]
        type_info = type(value).__name__
        
        if isinstance(value, dict):
            size_info = f"{len(value)} items"
        elif isinstance(value, list):
            size_info = f"{len(value)} elements"
        elif isinstance(value, str) and len(value) > 50:
            size_info = f"{len(value)} chars"
        else:
            size_info = str(value)
            
        print(f"  - {key}: {type_info}, {size_info}")
    
    # Find keys related to media
    media_keys = [k for k in top_level_keys if any(term in k.lower() for term in 
                  ['media', 'material', 'asset', 'resource', 'file', 'video', 'audio', 'image'])]
    
    print(f"\nPotential media-related keys: {media_keys}")
    
    # Find keys related to timeline/tracks
    timeline_keys = [k for k in top_level_keys if any(term in k.lower() for term in 
                    ['timeline', 'track', 'segment', 'clip', 'edit'])]
    
    print(f"\nPotential timeline-related keys: {timeline_keys}")
    
    # Detailed analysis of each section
    analysis_results = {
        'top_level_keys': top_level_keys,
        'media_pools': {},
        'timeline_data': {},
        'clip_references': {},
        'media_references': set()
    }
    
    # Analyze potential media pools
    print("\n=== ANALYZING MEDIA POOLS ===")
    for key in media_keys:
        if key in project_data:
            media_pool_info = analyze_media_pool(project_data[key], key, verbose)
            if media_pool_info['total_items'] > 0:
                analysis_results['media_pools'][key] = media_pool_info
                print(f"\nFound media pool in '{key}': {media_pool_info['total_items']} items")
                for media_type, count in media_pool_info['type_counts'].items():
                    print(f"  - {media_type}: {count} items")
    
    # Analyze timeline/tracks
    print("\n=== ANALYZING TIMELINE DATA ===")
    for key in timeline_keys:
        if key in project_data:
            timeline_info = analyze_timeline(project_data[key], key, verbose)
            if timeline_info['total_clips'] > 0:
                analysis_results['timeline_data'][key] = timeline_info
                print(f"\nFound timeline data in '{key}': {timeline_info['total_clips']} clips")
                print(f"  - {timeline_info['tracks_count']} tracks")
                print(f"  - {timeline_info['segments_count']} segments")
    
    # Extract all media references throughout the file
    print("\n=== EXTRACTING ALL MEDIA REFERENCES ===")
    media_refs = extract_all_media_references(project_data)
    analysis_results['media_references'] = media_refs
    
    print(f"Found {len(media_refs)} unique media references throughout the project")
    if verbose and media_refs:
        print("\nSample media references:")
        for ref in list(media_refs)[:10]:
            print(f"  - {ref}")
    
    # Identify clip to media mappings
    print("\n=== IDENTIFYING CLIP-TO-MEDIA MAPPINGS ===")
    clip_media_mappings = identify_clip_media_mappings(project_data)
    analysis_results['clip_references'] = clip_media_mappings
    
    print(f"Found {len(clip_media_mappings)} clip-to-media mappings")
    if verbose and clip_media_mappings:
        print("\nSample clip-media mappings:")
        for clip_id, media_info in list(clip_media_mappings.items())[:5]:
            print(f"  - Clip {clip_id}: {media_info.get('path', 'Unknown path')}")
    
    # If we have both media pools and clip references, we can identify unused media
    if analysis_results['media_pools'] and analysis_results['clip_references']:
        print("\n=== IDENTIFYING UNUSED MEDIA ===")
        unused_media = identify_unused_media(analysis_results['media_pools'], 
                                            analysis_results['clip_references'],
                                            analysis_results['media_references'])
        analysis_results['unused_media'] = unused_media
        
        print(f"Found {len(unused_media)} potentially unused media items")
        if verbose and unused_media:
            print("\nSample unused media:")
            for media in unused_media[:10]:
                print(f"  - {media.get('name', 'Unnamed')}: {media.get('path', 'No path')}")
    
    # Save analysis results if output directory is specified
    if output_dir:
        # Convert sets to lists for JSON serialization
        serializable_results = analysis_results.copy()
        serializable_results['media_references'] = list(analysis_results['media_references'])
        
        output_file = os.path.join(output_dir, "project_structure_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2)
        print(f"\nAnalysis results saved to {output_file}")
    
    return analysis_results

def analyze_media_pool(data: Any, key_path: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze a potential media pool structure.
    
    Args:
        data: The data to analyze
        key_path: The key path leading to this data
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary with media pool analysis
    """
    result = {
        'key_path': key_path,
        'total_items': 0,
        'type_counts': defaultdict(int),
        'items': []
    }
    
    # Different possible structures for media pools
    if isinstance(data, dict):
        # Case 1: Dictionary with media type keys (videos, audios, images, etc.)
        media_type_keys = [k for k in data.keys() if k.lower() in 
                          ['videos', 'video', 'audios', 'audio', 'images', 'image', 
                           'stickers', 'effects', 'texts', 'transitions']]
        
        for type_key in media_type_keys:
            if isinstance(data[type_key], list):
                media_list = data[type_key]
                result['type_counts'][type_key] = len(media_list)
                result['total_items'] += len(media_list)
                
                # Extract info for each media item
                for item in media_list:
                    if isinstance(item, dict):
                        media_info = extract_media_info(item, type_key)
                        result['items'].append(media_info)
                        
                        if verbose and len(result['items']) <= 3:
                            print(f"\nSample {type_key} item:")
                            pprint.pprint(media_info)
    
    elif isinstance(data, list):
        # Case 2: List of media items
        for item in data:
            if isinstance(item, dict) and 'path' in item:
                # Looks like a media item
                media_type = determine_media_type(item)
                result['type_counts'][media_type] += 1
                result['total_items'] += 1
                
                media_info = extract_media_info(item, media_type)
                result['items'].append(media_info)
                
                if verbose and len(result['items']) <= 3:
                    print(f"\nSample media item:")
                    pprint.pprint(media_info)
    
    return result

def determine_media_type(item: Dict[str, Any]) -> str:
    """
    Determine the type of a media item based on its properties.
    
    Args:
        item: Media item dictionary
        
    Returns:
        String indicating the media type
    """
    # Check if type is explicitly specified
    if 'type' in item:
        return item['type']
    
    # Try to determine from file extension
    if 'path' in item:
        ext = os.path.splitext(item['path'])[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.mkv']:
            return 'video'
        elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
            return 'audio'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return 'image'
    
    # Default to unknown
    return 'unknown'

def extract_media_info(item: Dict[str, Any], media_type: str) -> Dict[str, Any]:
    """
    Extract relevant information from a media item.
    
    Args:
        item: Media item dictionary
        media_type: Type of the media item
        
    Returns:
        Dictionary with extracted media info
    """
    media_info = {
        'type': media_type,
        'id': item.get('id', None)
    }
    
    # Extract path/filename
    if 'path' in item:
        media_info['path'] = item['path']
        media_info['name'] = os.path.basename(item['path'])
    elif 'filePath' in item:
        media_info['path'] = item['filePath']
        media_info['name'] = os.path.basename(item['filePath'])
    elif 'resourcePath' in item:
        media_info['path'] = item['resourcePath']
        media_info['name'] = os.path.basename(item['resourcePath'])
    elif 'name' in item:
        media_info['name'] = item['name']
    
    # Extract duration if available
    if 'duration' in item:
        # Convert to seconds if in microseconds
        duration = item['duration']
        if duration > 10000:  # Likely in microseconds
            duration /= 1000000
        media_info['duration'] = duration
    
    # Extract additional metadata
    for key in ['width', 'height', 'size', 'created', 'modified']:
        if key in item:
            media_info[key] = item[key]
    
    return media_info

def analyze_timeline(data: Any, key_path: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze a potential timeline structure.
    
    Args:
        data: The data to analyze
        key_path: The key path leading to this data
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary with timeline analysis
    """
    result = {
        'key_path': key_path,
        'total_clips': 0,
        'tracks_count': 0,
        'segments_count': 0,
        'tracks': []
    }
    
    # Try to find tracks
    tracks = find_tracks_in_data(data)
    
    if tracks:
        result['tracks_count'] = len(tracks)
        
        # Analyze each track
        for track_idx, track in enumerate(tracks):
            track_info = {
                'index': track_idx,
                'type': track.get('type', 'unknown'),
                'segments': []
            }
            
            # Look for segments/clips
            segments = find_segments_in_track(track)
            
            if segments:
                track_info['segments'] = []
                for seg_idx, segment in enumerate(segments):
                    segment_info = extract_segment_info(segment, seg_idx)
                    track_info['segments'].append(segment_info)
                
                result['segments_count'] += len(segments)
                result['total_clips'] += len(segments)
            
            result['tracks'].append(track_info)
            
            if verbose and track_idx < 2:
                print(f"\nTrack {track_idx} ({track_info['type']}):")
                print(f"  - {len(track_info['segments'])} segments/clips")
                if track_info['segments'] and verbose:
                    print("  Sample segment info:")
                    pprint.pprint(track_info['segments'][0])
    
    return result

def find_tracks_in_data(data: Any) -> List[Dict[str, Any]]:
    """
    Find track structures in the data.
    
    Args:
        data: Data to search
        
    Returns:
        List of track dictionaries
    """
    # Direct case: data is a list of tracks
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        # Check if these look like tracks
        track_indicators = ['type', 'segments', 'clips', 'items']
        if any(any(indicator in item for indicator in track_indicators) for item in data):
            return data
    
    # Case where data is a dictionary containing tracks
    if isinstance(data, dict):
        # Look for common track keys
        for key in ['tracks', 'track', 'videoTracks', 'audioTracks']:
            if key in data and isinstance(data[key], list):
                return data[key]
    
    # Recursive search in dictionary
    if isinstance(data, dict):
        for key, value in data.items():
            tracks = find_tracks_in_data(value)
            if tracks:
                return tracks
    
    # Not found
    return []

def find_segments_in_track(track: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find segments or clips in a track.
    
    Args:
        track: Track dictionary
        
    Returns:
        List of segment dictionaries
    """
    # Look for common segment/clip keys
    for key in ['segments', 'clips', 'items', 'content']:
        if key in track and isinstance(track[key], list):
            return track[key]
    
    # Look for any list that contains time-related fields
    for key, value in track.items():
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            # Check if these look like segments/clips
            time_indicators = ['start', 'duration', 'timeRange', 'target_timerange']
            if any(any(indicator in item for indicator in time_indicators) for item in value[:3]):
                return value
    
    # Not found
    return []

def extract_segment_info(segment: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Extract relevant information from a segment/clip.
    
    Args:
        segment: Segment dictionary
        index: Segment index
        
    Returns:
        Dictionary with extracted segment info
    """
    segment_info = {
        'index': index,
        'material_id': segment.get('material_id', None)
    }
    
    # Extract timeline position
    timeline_start = None
    timeline_duration = None
    
    # Try different paths to timeline information
    if 'target_timerange' in segment:
        timerange = segment['target_timerange']
        if isinstance(timerange, dict):
            timeline_start = timerange.get('start')
            timeline_duration = timerange.get('duration')
    elif 'timeRange' in segment:
        timerange = segment['timeRange']
        if isinstance(timerange, dict):
            timeline_start = timerange.get('start')
            timeline_duration = timerange.get('duration')
    elif 'start' in segment:
        timeline_start = segment['start']
        if 'duration' in segment:
            timeline_duration = segment['duration']
        elif 'end' in segment:
            timeline_duration = segment['end'] - segment['start']
    
    if timeline_start is not None:
        segment_info['timeline_start'] = timeline_start
        if timeline_duration is not None:
            segment_info['timeline_end'] = timeline_start + timeline_duration
            segment_info['timeline_duration'] = timeline_duration
    
    # Extract source position
    source_start = None
    source_duration = None
    
    if 'source_timerange' in segment:
        timerange = segment['source_timerange']
        if isinstance(timerange, dict):
            source_start = timerange.get('start')
            source_duration = timerange.get('duration')
    
    if source_start is not None:
        segment_info['source_start'] = source_start
        if source_duration is not None:
            segment_info['source_duration'] = source_duration
    
    # Check for direct media path references
    for key in ['material_path', 'source', 'path', 'filePath', 'resourcePath']:
        if key in segment and isinstance(segment[key], str):
            segment_info['media_path'] = segment[key]
            break
    
    # Extract any other material references
    for key, value in segment.items():
        if 'material' in key.lower() and key != 'material_id':
            segment_info[key] = value
    
    return segment_info

def extract_all_media_references(data: Any, path: str = "") -> Set[str]:
    """
    Extract all media file references from the project data.
    
    Args:
        data: The data to search
        path: Current path in the data structure
        
    Returns:
        Set of media file paths
    """
    media_refs = set()
    
    if isinstance(data, dict):
        # Check for common media path keys
        for key in ['path', 'filePath', 'resourcePath', 'source', 'src', 'url']:
            if key in data and isinstance(data[key], str):
                file_path = data[key]
                # Check if it looks like a media file path
                if any(file_path.lower().endswith(ext) for ext in 
                      ['.mp4', '.mov', '.avi', '.mkv', '.mp3', '.wav', '.m4a', 
                       '.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    media_refs.add(file_path)
        
        # Recurse into nested dictionaries
        for key, value in data.items():
            nested_path = f"{path}.{key}" if path else key
            nested_refs = extract_all_media_references(value, nested_path)
            media_refs.update(nested_refs)
    
    elif isinstance(data, list):
        # Recurse into lists
        for i, item in enumerate(data):
            nested_path = f"{path}[{i}]"
            nested_refs = extract_all_media_references(item, nested_path)
            media_refs.update(nested_refs)
    
    return media_refs

def identify_clip_media_mappings(project_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Identify mappings between clips/segments and their source media files.
    
    Args:
        project_data: The project data
        
    Returns:
        Dictionary mapping clip IDs to media info
    """
    clip_media_mappings = {}
    
    # First look for direct material mappings
    material_map = {}
    
    # Check if there's a materials section with material IDs
    if 'materials' in project_data and isinstance(project_data['materials'], dict):
        materials = project_data['materials']
        
        for media_type in ['videos', 'audios', 'images']:
            if media_type in materials and isinstance(materials[media_type], list):
                for item in materials[media_type]:
                    if 'id' in item and ('path' in item or 'filePath' in item or 'resourcePath' in item):
                        material_id = item['id']
                        media_path = item.get('path', item.get('filePath', item.get('resourcePath')))
                        material_map[material_id] = {
                            'path': media_path,
                            'type': media_type.rstrip('s'),  # Remove trailing 's'
                            'name': os.path.basename(media_path)
                        }
    
    # Now find clips and their material references
    def process_segments(segments, track_info=None):
        for seg_idx, segment in enumerate(segments):
            if not isinstance(segment, dict):
                continue
                
            clip_id = segment.get('id', f"clip_{seg_idx}")
            clip_info = {'id': clip_id}
            
            if track_info:
                clip_info['track_type'] = track_info.get('type', 'unknown')
                clip_info['track_index'] = track_info.get('index', 0)
            
            # Check for material_id reference
            if 'material_id' in segment and segment['material_id'] in material_map:
                material_id = segment['material_id']
                clip_info.update(material_map[material_id])
                clip_media_mappings[clip_id] = clip_info
            
            # Check for direct path reference
            for key in ['material_path', 'path', 'source', 'filePath', 'resourcePath']:
                if key in segment and isinstance(segment[key], str):
                    clip_info['path'] = segment[key]
                    clip_info['name'] = os.path.basename(segment[key])
                    clip_media_mappings[clip_id] = clip_info
                    break
    
    # Process tracks and segments
    if 'tracks' in project_data and isinstance(project_data['tracks'], list):
        for track_idx, track in enumerate(project_data['tracks']):
            if not isinstance(track, dict):
                continue
                
            track_info = {
                'type': track.get('type', 'unknown'),
                'index': track_idx
            }
            
            # Look for segments
            for key in ['segments', 'clips', 'items']:
                if key in track and isinstance(track[key], list):
                    process_segments(track[key], track_info)
    
    return clip_media_mappings

def identify_unused_media(media_pools: Dict[str, Dict[str, Any]], 
                        clip_references: Dict[str, Dict[str, Any]],
                        all_references: Set[str]) -> List[Dict[str, Any]]:
    """
    Identify media files that are in the media pool but not used in clips.
    
    Args:
        media_pools: Media pool analysis results
        clip_references: Clip-to-media mappings
        all_references: All media references found in the project
        
    Returns:
        List of unused media items
    """
    unused_media = []
    
    # Collect all media items from the pools
    all_pool_media = []
    for pool_key, pool_info in media_pools.items():
        all_pool_media.extend(pool_info['items'])
    
    # Collect all used media paths
    used_media_paths = set()
    for clip_id, media_info in clip_references.items():
        if 'path' in media_info:
            used_media_paths.add(media_info['path'])
            used_media_paths.add(os.path.basename(media_info['path']))
    
    # Also consider all media references as potentially used
    for ref in all_references:
        used_media_paths.add(ref)
        used_media_paths.add(os.path.basename(ref))
    
    # Identify unused media
    for media in all_pool_media:
        if 'path' not in media:
            continue
            
        is_used = False
        path = media['path']
        filename = os.path.basename(path)
        
        # Check if the path or filename is in the used paths
        if path in used_media_paths or filename in used_media_paths:
            is_used = True
        
        if not is_used:
            unused_media.append(media)
    
    return unused_media

def main():
    parser = argparse.ArgumentParser(description="Analyze CapCut project file structure")
    parser.add_argument("file_path", help="Path to the CapCut project file (usually draft_content.json)")
    parser.add_argument("--output", "-o", help="Directory to save analysis results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    
    args = parser.parse_args()
    
    analyze_project_structure(args.file_path, args.output, args.verbose)

if __name__ == "__main__":
    main()
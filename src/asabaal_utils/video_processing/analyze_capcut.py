#!/usr/bin/env python3
import json
import os
import sys
import csv
from collections import defaultdict
import pprint

def analyze_capcut_project(json_file_path, output_dir=None):
    print(f"Analyzing CapCut project file: {json_file_path}")
    print("File size: {:.2f} MB".format(os.path.getsize(json_file_path) / (1024 * 1024)))
    
    # Create output directory if specified
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load the JSON file
    print("Loading JSON file (this may take a moment for large files)...")
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

    # Basic project info
    print("\n=== PROJECT OVERVIEW ===")
    project_name = project_data.get('projectName', project_data.get('name', 'Unknown'))
    print(f"Project Name: {project_name}")
    if 'createTime' in project_data:
        print(f"Created: {project_data.get('createTime', 'Unknown')}")
    elif 'create_time' in project_data:
        print(f"Created: {project_data.get('create_time', 'Unknown')}")
    if 'modifyTime' in project_data:
        print(f"Last Modified: {project_data.get('modifyTime', 'Unknown')}")
    elif 'update_time' in project_data:
        print(f"Last Modified: {project_data.get('update_time', 'Unknown')}")
    
    # First, let's inspect the top-level structure
    print("\n=== PROJECT STRUCTURE ===")
    top_level_keys = list(project_data.keys())
    print(f"Top-level keys: {top_level_keys}")
    
    # Look for timeline-related keys
    timeline_keys = [k for k in top_level_keys if any(term in k.lower() for term in 
                     ['time', 'track', 'segment', 'clip', 'material', 'media', 'edit'])]
    
    print(f"Potential timeline-related keys: {timeline_keys}")
    
    # Analyze materials if present
    if 'materials' in project_data:
        analyze_materials(project_data['materials'])
    
    # Try to find and analyze tracks
    tracks_data = find_tracks(project_data)
    if tracks_data:
        print("\n=== TRACK ANALYSIS ===")
        print(f"Found {len(tracks_data)} tracks")
        analyze_tracks(tracks_data)
    
    # Try to find clips directly
    clips_data = find_clips(project_data)
    if clips_data:
        print("\n=== CLIPS ANALYSIS ===")
        print(f"Found {len(clips_data)} clips")
        analyze_found_clips(clips_data)
    
    # Media references analysis
    media_refs = analyze_media_references(project_data)
    
    # Find segment structure
    segments = find_segments(project_data)
    if segments:
        print("\n=== SEGMENTS ANALYSIS ===")
        print(f"Found {len(segments)} segments")
        analyze_segments(segments)
    
    # Identify potential split points
    identify_split_points(project_data, clips_data, segments)
    
    # Extract clip timestamps and plan splits
    print("\n=== EXTRACTING DETAILED TIMELINE INFO ===")
    clip_timeline = extract_clip_timestamps(project_data, tracks_data, media_refs)
    print(f"Extracted timing information for {len(clip_timeline)} clips")
    
    # Generate split plans based on different strategies
    print("\n=== GENERATING SPLIT PLANS ===")
    # Split by source media
    media_splits = split_by_media(clip_timeline)
    print(f"Generated {len(media_splits)} splits based on source media")
    
    # Split by fixed duration
    time_splits = split_by_duration(clip_timeline, 300000000)  # 5 minutes in timeline units
    print(f"Generated {len(time_splits)} splits based on fixed duration")
    
    # Export results if output directory specified
    if output_dir:
        # Export clip timeline
        timeline_csv = os.path.join(output_dir, "clip_timeline.csv")
        export_clip_timeline_csv(clip_timeline, timeline_csv)
        print(f"Exported clip timeline to {timeline_csv}")
        
        # Export split plans
        media_splits_json = os.path.join(output_dir, "media_splits.json")
        with open(media_splits_json, 'w', encoding='utf-8') as f:
            json.dump(media_splits, f, indent=2)
        print(f"Exported media-based splits to {media_splits_json}")
        
        time_splits_json = os.path.join(output_dir, "time_splits.json")
        with open(time_splits_json, 'w', encoding='utf-8') as f:
            json.dump(time_splits, f, indent=2)
        print(f"Exported time-based splits to {time_splits_json}")
        
        # Export split instructions
        split_instructions = os.path.join(output_dir, "split_instructions.txt")
        export_split_instructions(time_splits, split_instructions)
        print(f"Exported split instructions to {split_instructions}")

def find_tracks(data, path=""):
    """Recursively search for track data"""
    if isinstance(data, dict):
        # Direct match for tracks key
        if 'tracks' in data and isinstance(data['tracks'], list):
            return data['tracks']
        
        # Check other keys
        for key, value in data.items():
            if key == 'track' and isinstance(value, list):
                return value
            elif isinstance(value, (dict, list)):
                result = find_tracks(value, f"{path}.{key}" if path else key)
                if result:
                    return result
    elif isinstance(data, list):
        # Check if this list itself looks like tracks
        if all(isinstance(item, dict) for item in data):
            track_indicators = ['type', 'id', 'clips', 'segments']
            if any(any(indicator in item for indicator in track_indicators) for item in data):
                return data
        
        # Otherwise recurse
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                result = find_tracks(item, f"{path}[{i}]")
                if result:
                    return result
    
    return None

def find_clips(data, path="", clips=None):
    """Recursively find all clips in the project"""
    if clips is None:
        clips = []
    
    if isinstance(data, dict):
        # Check if this dict looks like a clip
        clip_indicators = ['start', 'duration', 'source']
        if any(indicator in data for indicator in clip_indicators):
            # This might be a clip, add path info
            data['_path'] = path
            clips.append(data)
        
        # Recurse into child elements
        for key, value in data.items():
            # Special case for clips key
            if key == 'clips' and isinstance(value, list):
                for i, clip in enumerate(value):
                    if isinstance(clip, dict):
                        clip['_path'] = f"{path}.{key}[{i}]"
                        clips.append(clip)
            elif isinstance(value, (dict, list)):
                find_clips(value, f"{path}.{key}" if path else key, clips)
                
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                find_clips(item, f"{path}[{i}]", clips)
    
    return clips

def find_segments(data, path="", segments=None):
    """Recursively find all segments in the project"""
    if segments is None:
        segments = []
    
    if isinstance(data, dict):
        # Check if this dict looks like a segment
        segment_indicators = ['start', 'end', 'duration', 'type']
        indicator_count = sum(1 for indicator in segment_indicators if indicator in data)
        
        if indicator_count >= 2:
            # This might be a segment, add path info
            data['_path'] = path
            segments.append(data)
        
        # Special case for segments key
        if 'segments' in data and isinstance(data['segments'], list):
            for i, segment in enumerate(data['segments']):
                if isinstance(segment, dict):
                    segment['_path'] = f"{path}.segments[{i}]"
                    segments.append(segment)
        
        # Recurse into other values
        for key, value in data.items():
            if key != 'segments' and isinstance(value, (dict, list)):
                find_segments(value, f"{path}.{key}" if path else key, segments)
                
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                find_segments(item, f"{path}[{i}]", segments)
    
    return segments

def analyze_materials(materials):
    """Analyze the materials section of the project"""
    print("\n=== MATERIALS ANALYSIS ===")
    
    if isinstance(materials, dict):
        for material_type, items in materials.items():
            if isinstance(items, list):
                print(f"Material type '{material_type}': {len(items)} items")
                
                # Sample a few items
                if items:
                    print(f"  Sample keys in first item: {list(items[0].keys()) if isinstance(items[0], dict) else 'Not a dict'}")
    
    elif isinstance(materials, list):
        print(f"Materials list has {len(materials)} items")
        
        # Categorize by type
        material_types = defaultdict(int)
        for item in materials:
            if isinstance(item, dict):
                material_type = item.get('type', 'unknown')
                material_types[material_type] += 1
        
        print(f"Material types: {dict(material_types)}")

def analyze_tracks(tracks):
    """Analyze the structure of tracks"""
    if not tracks:
        return
    
    track_types = defaultdict(int)
    
    for i, track in enumerate(tracks):
        if not isinstance(track, dict):
            continue
        
        # Get track type
        track_type = track.get('type', 'unknown')
        track_types[track_type] += 1
        
        # Print track details
        print(f"\nTrack {i} ({track_type}):")
        print(f"  Keys: {list(track.keys())}")
        
        # Look for clips
        clips = []
        
        # Try different potential clip keys
        for clip_key in ['clips', 'segments', 'items', 'content']:
            if clip_key in track and isinstance(track[clip_key], list):
                clips = track[clip_key]
                print(f"  Found {len(clips)} items in '{clip_key}'")
                break
        
        # If no clips found via common keys, look more deeply
        if not clips:
            for key, value in track.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    # This might be clips
                    time_indicators = ['start', 'duration', 'timeRange']
                    if any(any(indicator in item for indicator in time_indicators) for item in value[:3]):
                        clips = value
                        print(f"  Found {len(clips)} potential clips in '{key}'")
                        break
        
        # Analyze clips if found
        if clips:
            analyze_track_clips(clips)
    
    print(f"\nTrack types summary: {dict(track_types)}")

def analyze_track_clips(clips):
    """Analyze clips within a track"""
    if not clips:
        return
    
    # Sample clip structure
    if isinstance(clips[0], dict):
        print(f"  Sample clip keys: {list(clips[0].keys())}")
    
    # Calculate durations if possible
    durations = []
    for clip in clips:
        if isinstance(clip, dict):
            # Try different ways duration might be stored
            duration = None
            
            if 'duration' in clip:
                duration = clip['duration']
            elif 'timeRange' in clip and isinstance(clip['timeRange'], dict):
                if 'duration' in clip['timeRange']:
                    duration = clip['timeRange']['duration']
                elif 'start' in clip['timeRange'] and 'end' in clip['timeRange']:
                    duration = clip['timeRange']['end'] - clip['timeRange']['start']
            
            if duration is not None:
                durations.append(duration)
    
    # Print duration stats
    if durations:
        total_duration = sum(durations)
        print(f"  Total duration: {total_duration:.2f}")
        print(f"  Average clip duration: {total_duration/len(durations):.2f}")
        print(f"  Min/Max clip durations: {min(durations):.2f} / {max(durations):.2f}")

def analyze_found_clips(clips):
    """Analyze clips found across the project"""
    if not clips:
        return
    
    # Group by path pattern
    path_groups = defaultdict(list)
    for clip in clips:
        if '_path' in clip:
            path_parts = clip['_path'].split('.')
            if len(path_parts) > 1:
                # Use the parent container as a group key
                group_key = path_parts[-2]
                path_groups[group_key].append(clip)
            else:
                path_groups['root'].append(clip)
    
    print(f"Clips found in {len(path_groups)} different container types")
    for group, group_clips in path_groups.items():
        print(f"\nClip group '{group}': {len(group_clips)} clips")
        
        # Analyze time ranges if available
        time_ranges = []
        for clip in group_clips:
            if 'timeRange' in clip and isinstance(clip['timeRange'], dict):
                if 'start' in clip['timeRange'] and 'end' in clip['timeRange']:
                    time_ranges.append((clip['timeRange']['start'], clip['timeRange']['end']))
        
        if time_ranges:
            # Sort by start time
            time_ranges.sort()
            
            # Find potential breaks (gaps in timeline)
            potential_breaks = []
            for i in range(len(time_ranges) - 1):
                current_end = time_ranges[i][1]
                next_start = time_ranges[i+1][0]
                
                if next_start - current_end > 0.1:  # Threshold for a gap
                    potential_breaks.append((i, current_end, next_start - current_end))
            
            if potential_breaks:
                print("  Potential timeline breaks (clip index, position, gap size):")
                for idx, pos, gap in potential_breaks:
                    print(f"  - After clip {idx}: position {pos:.2f}, gap {gap:.2f}")

def analyze_media_references(project_data):
    """Find and analyze media file references"""
    print("\n=== MEDIA REFERENCES ANALYSIS ===")
    
    # Collect all media references
    media_refs = defaultdict(int)
    matting_refs = defaultdict(int)
    
    def search_media_refs(obj, path=""):
        """Recursively search for media references"""
        if isinstance(obj, dict):
            # Look for common media reference keys
            for key in ['path', 'filePath', 'resourcePath', 'source', 'src']:
                if key in obj and isinstance(obj[key], str):
                    file_path = obj[key]
                    media_refs[file_path] += 1
                    
                    # Check if it's a matting reference
                    if 'matting' in file_path:
                        matting_refs[file_path] += 1
            
            # Recurse into nested dictionaries
            for k, v in obj.items():
                search_media_refs(v, f"{path}.{k}" if path else k)
                
        elif isinstance(obj, list):
            # Recurse into lists
            for i, item in enumerate(obj):
                search_media_refs(item, f"{path}[{i}]")
    
    # Start recursive search
    search_media_refs(project_data)
    
    # Print results
    print(f"Total unique media references: {len(media_refs)}")
    print(f"Total matting references: {len(matting_refs)}")
    
    # Print top referenced media files
    if media_refs:
        print("\nTop 10 most referenced media files:")
        for path, count in sorted(media_refs.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {path}: {count} references")
    
    # Print matting references
    if matting_refs:
        print("\nMatting references:")
        for path, count in sorted(matting_refs.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {path}: {count} references")
            
    return media_refs

def analyze_segments(segments):
    """Analyze segment structure"""
    if not segments:
        return
    
    # Try to find segment durations
    durations = []
    segment_types = defaultdict(int)
    
    for segment in segments:
        segment_type = segment.get('type', 'unknown')
        segment_types[segment_type] += 1
        
        # Extract duration
        duration = None
        if 'duration' in segment:
            duration = segment['duration']
        elif 'end' in segment and 'start' in segment:
            duration = segment['end'] - segment['start']
        
        if duration is not None:
            durations.append((segment.get('_path', ''), duration))
    
    # Print segment types
    print(f"Segment types: {dict(segment_types)}")
    
    # Print durations
    if durations:
        # Sort by duration
        durations.sort(key=lambda x: x[1], reverse=True)
        
        print("\nTop 10 longest segments:")
        for path, duration in durations[:10]:
            print(f"  - Duration: {duration:.2f}, Path: {path}")
        
        # Calculate some stats
        total_duration = sum(d for _, d in durations)
        print(f"\nTotal segment duration: {total_duration:.2f}")

def identify_split_points(project_data, clips, segments):
    """Identify logical points to split the project"""
    print("\n=== RECOMMENDED SPLIT POINTS ===")
    
    recommendations = []
    
    # 1. By matting file
    matting_refs = defaultdict(int)
    def find_matting_refs(obj):
        if isinstance(obj, dict):
            for key in ['path', 'filePath', 'resourcePath', 'source']:
                if key in obj and isinstance(obj[key], str) and 'matting' in obj[key]:
                    matting_refs[obj[key]] += 1
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    find_matting_refs(v)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    find_matting_refs(item)
    
    find_matting_refs(project_data)
    
    if matting_refs:
        top_matting = sorted(matting_refs.items(), key=lambda x: x[1], reverse=True)
        recommendations.append("1. Split by matting file usage:")
        for matting_file, count in top_matting[:3]:
            recommendations.append(f"   - Create a separate project for sections using: {matting_file.split('/')[-1]}")
    
    # 2. By timeline segments
    if segments:
        # Find significant breaks between segments
        significant_breaks = []
        
        # Group segments by similar path structure
        path_segments = defaultdict(list)
        for segment in segments:
            if '_path' in segment:
                path_parts = segment['_path'].split('.')
                if len(path_parts) > 1:
                    path_key = '.'.join(path_parts[:-1])  # Use parent path as key
                    path_segments[path_key].append(segment)
        
        # For each group, find breaks
        for path_key, group_segments in path_segments.items():
            if len(group_segments) < 2:
                continue
                
            # Try to sort by position
            position_segments = []
            for segment in group_segments:
                pos = None
                if 'start' in segment:
                    pos = segment['start']
                elif 'timeRange' in segment and isinstance(segment['timeRange'], dict) and 'start' in segment['timeRange']:
                    pos = segment['timeRange']['start']
                
                if pos is not None:
                    position_segments.append((segment, pos))
            
            if position_segments:
                position_segments.sort(key=lambda x: x[1])
                
                # Find gaps
                for i in range(len(position_segments) - 1):
                    curr_segment, curr_pos = position_segments[i]
                    next_segment, next_pos = position_segments[i+1]
                    
                    curr_end = None
                    if 'end' in curr_segment:
                        curr_end = curr_segment['end']
                    elif 'timeRange' in curr_segment and isinstance(curr_segment['timeRange'], dict) and 'end' in curr_segment['timeRange']:
                        curr_end = curr_segment['timeRange']['end']
                    elif 'duration' in curr_segment:
                        curr_end = curr_pos + curr_segment['duration']
                    
                    if curr_end is not None and next_pos - curr_end > 0.5:  # Threshold for significant gap
                        significant_breaks.append((path_key, i, curr_end, next_pos - curr_end))
        
        if significant_breaks:
            recommendations.append("\n2. Split at these timeline breaks:")
            for path, idx, pos, gap in sorted(significant_breaks, key=lambda x: x[3], reverse=True)[:5]:
                recommendations.append(f"   - At position {pos:.2f} (gap of {gap:.2f}) in {path}")
    
    # 3. By media file usage
    media_refs = defaultdict(int)
    def find_video_refs(obj):
        if isinstance(obj, dict):
            for key in ['path', 'filePath', 'resourcePath', 'source']:
                if key in obj and isinstance(obj[key], str):
                    file_path = obj[key].lower()
                    if any(ext in file_path for ext in ['.mp4', '.mov', '.avi', '.mkv']):
                        media_refs[obj[key]] += 1
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    find_video_refs(v)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    find_video_refs(item)
    
    find_video_refs(project_data)
    
    if media_refs:
        recommendations.append("\n3. Split by source media:")
        for media_file, count in sorted(media_refs.items(), key=lambda x: x[1], reverse=True)[:3]:
            file_name = media_file.split('/')[-1] if '/' in media_file else media_file.split('\\')[-1] if '\\' in media_file else media_file
            recommendations.append(f"   - Create a project focused on: {file_name}")
    
    # Print all recommendations
    if recommendations:
        print("Based on the project structure, here are the recommended ways to split your project:")
        for rec in recommendations:
            print(rec)
    else:
        print("No clear split points identified. Consider manual review of your timeline.")
    
    print("\nImplementation approach:")
    print("1. Create separate CapCut projects for each logical section")
    print("2. Export each section as a separate rendered video")
    print("3. Import these rendered videos into a master project if needed")

# New functions for enhanced analysis
def export_clip_timeline_csv(clip_timeline, output_file):
    """Export clip timeline to CSV file"""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['track_idx', 'track_type', 'segment_idx', 'timeline_start', 'timeline_end', 
                     'timeline_duration', 'source_file', 'source_start', 'source_end', 'source_duration']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for clip in clip_timeline:
            # Calculate source_end if possible
            source_end = None
            if clip['source_start'] is not None and clip['source_duration'] is not None:
                source_end = clip['source_start'] + clip['source_duration']
                
            writer.writerow({
                'track_idx': clip['track_idx'],
                'track_type': clip['track_type'],
                'segment_idx': clip['segment_idx'],
                'timeline_start': clip['timeline_start'],
                'timeline_end': clip['timeline_end'],
                'timeline_duration': clip['timeline_duration'],
                'source_file': clip['source_file'] or '',
                'source_start': clip['source_start'] if clip['source_start'] is not None else '',
                'source_end': source_end if source_end is not None else '',
                'source_duration': clip['source_duration'] if clip['source_duration'] is not None else ''
            })

def extract_clip_timestamps(project_data, tracks_data, media_refs):
    """Extract timestamp information for all clips in the project"""
    clip_timeline = []
    
    # Direct mapping from material_id to source file
    material_to_source = {}
    
    # Try to build material_id to source_file mapping
    if 'materials' in project_data:
        materials = project_data['materials']
        
        # Check videos
        if 'videos' in materials and isinstance(materials['videos'], list):
            for video in materials['videos']:
                if 'id' in video and 'path' in video:
                    material_to_source[video['id']] = video['path']
        
        # Check audios
        if 'audios' in materials and isinstance(materials['audios'], list):
            for audio in materials['audios']:
                if 'id' in audio and 'path' in audio:
                    material_to_source[audio['id']] = audio['path']
    
    # Process each track
    for track_idx, track in enumerate(tracks_data):
        track_type = track.get('type', 'unknown')
        
        # Process segments in each track
        for seg_idx, segment in enumerate(track.get('segments', [])):
            # Extract timeline position and duration
            timeline_start = None
            timeline_duration = None
            
            # Try different paths to find timeline information
            if 'target_timerange' in segment:
                timerange = segment['target_timerange']
                if isinstance(timerange, dict):
                    timeline_start = timerange.get('start')
                    timeline_duration = timerange.get('duration')
            elif 'render_timerange' in segment:
                timerange = segment['render_timerange']
                if isinstance(timerange, dict):
                    timeline_start = timerange.get('start')
                    timeline_duration = timerange.get('duration')
            
            # Extract source file and source timestamp
            source_file = None
            source_start = None
            source_duration = None
            
            # Try to get material ID
            material_id = segment.get('material_id')
            
            if material_id:
                # Look up in our mapping
                source_file = material_to_source.get(material_id)
            
            # Try to get source timerange
            if 'source_timerange' in segment:
                timerange = segment['source_timerange']
                if isinstance(timerange, dict):
                    source_start = timerange.get('start')
                    source_duration = timerange.get('duration')
            
            # If we have timeline information but not source information,
            # try to infer from other clips with the same material_id
            if timeline_start is not None and timeline_duration is not None and material_id:
                if source_start is None or source_duration is None:
                    for other_clip in clip_timeline:
                        if other_clip['material_id'] == material_id and other_clip['source_start'] is not None:
                            source_start = other_clip['source_start']
                            if other_clip['source_duration'] is not None:
                                source_duration = other_clip['source_duration']
                            break
            
            # Only add if we have meaningful timeline information
            if timeline_start is not None and timeline_duration is not None:
                clip_info = {
                    'track_idx': track_idx,
                    'track_type': track_type,
                    'segment_idx': seg_idx,
                    'timeline_start': timeline_start,
                    'timeline_end': timeline_start + timeline_duration,
                    'timeline_duration': timeline_duration,
                    'source_file': source_file,
                    'source_start': source_start,
                    'source_duration': source_duration,
                    'material_id': material_id
                }
                
                clip_timeline.append(clip_info)
    
    # Sort clips by timeline start time
    clip_timeline.sort(key=lambda x: x['timeline_start'])
    
    return clip_timeline

def split_by_media(clip_timeline):
    """Split the project based on source media files"""
    if not clip_timeline:
        return []
    
    # Group clips by source media
    media_groups = defaultdict(list)
    for clip in clip_timeline:
        source_file = clip.get('source_file')
        if source_file:
            media_groups[source_file].append(clip)
        else:
            # Group clips with no source under 'unknown'
            media_groups['unknown'].append(clip)
    
    # Create splits based on media groups
    splits = []
    for source_file, clips in media_groups.items():
        if source_file == 'unknown' and len(media_groups) > 1:
            # Skip 'unknown' if we have other groups
            continue
            
        # Sort clips by timeline position
        clips.sort(key=lambda x: x['timeline_start'])
        
        if clips:
            splits.append({
                'source_file': source_file,
                'start_time': clips[0]['timeline_start'],
                'end_time': clips[-1]['timeline_end'],
                'duration': clips[-1]['timeline_end'] - clips[0]['timeline_start'],
                'clips': clips
            })
    
    # Sort splits by start time
    splits.sort(key=lambda x: x['start_time'])
    
    return splits

def split_by_duration(clip_timeline, max_duration=300000000):
    """Split the project into chunks of specified maximum duration"""
    if not clip_timeline:
        return []
        
    # Find total timeline duration
    max_end = max(clip['timeline_end'] for clip in clip_timeline)
    
    # Create splits
    splits = []
    current_start = min(clip['timeline_start'] for clip in clip_timeline)
    
    while current_start < max_end:
        current_end = min(current_start + max_duration, max_end)
        
        # Find clips that belong in this split
        split_clips = []
        for clip in clip_timeline:
            # Include if the clip overlaps with this split's timerange
            if clip['timeline_start'] < current_end and clip['timeline_end'] > current_start:
                split_clips.append(clip)
        
        splits.append({
            'start_time': current_start,
            'end_time': current_end,
            'duration': current_end - current_start,
            'clips': split_clips
        })
        
        current_start = current_end
    
    return splits

def export_split_instructions(splits, output_file):
    """Export instructions for recreating each split"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CapCut Project Split Instructions\n\n")
        f.write("This file contains instructions for recreating your CapCut project as smaller chunks.\n")
        f.write("Each split section represents a portion of the timeline that can be created as a separate project.\n\n")
        
        for i, split in enumerate(splits):
            f.write(f"## SPLIT {i+1}\n")
            f.write(f"Timeline Range: {format_time(split['start_time'])} to {format_time(split['end_time'])}")
            f.write(f" (Duration: {format_time(split['duration'])})\n\n")
            
            # Group clips by track
            tracks = {}
            for clip in split['clips']:
                track_idx = clip['track_idx']
                if track_idx not in tracks:
                    tracks[track_idx] = []
                tracks[track_idx].append(clip)
            
            # Write clip details by track
            for track_idx, clips in sorted(tracks.items()):
                f.write(f"### Track {track_idx} ({clips[0]['track_type']})\n")
                
                for clip in sorted(clips, key=lambda x: x['timeline_start']):
                    timeline_start_time = format_time(clip['timeline_start'])
                    timeline_end_time = format_time(clip['timeline_end'])
                    f.write(f"- Timeline: {timeline_start_time} to {timeline_end_time}")
                    
                    if clip['source_file']:
                        source_file = os.path.basename(clip['source_file']) if clip['source_file'] else 'Unknown'
                        f.write(f", Source: {source_file}")
                        
                        if clip['source_start'] is not None:
                            source_start_time = format_time(clip['source_start'])
                            f.write(f" (from {source_start_time}")
                            
                            if clip['source_duration'] is not None:
                                source_duration = format_time(clip['source_duration'])
                                f.write(f" for {source_duration})")
                            else:
                                f.write(")")
                    
                    f.write("\n")
                
                f.write("\n")
            
            f.write("\n")
        
        # Add script generation instructions
        f.write("## How to Use These Instructions\n\n")
        f.write("1. For each split, create a new CapCut project\n")
        f.write("2. Import the source media files needed for that split\n")
        f.write("3. Place each clip on the appropriate track at the relative position\n")
        f.write("   (subtract the split start time from the timeline time)\n")
        f.write("4. Apply any effects or transitions needed\n")
        f.write("5. Export each split project as a rendered video\n")
        f.write("6. Create a final CapCut project that combines all the split videos in sequence\n")

def format_time(time_value):
    """Format timeline units to a readable time format (assumes units are in microseconds)"""
    if time_value is None:
        return "Unknown"
        
    # Convert to seconds
    seconds = time_value / 1000000
    
    # Format as HH:MM:SS.mmm
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_capcut.py path/to/draft_content.json [output_directory]")
        sys.exit(1)
        
    json_file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyze_capcut_project(json_file_path, output_dir)
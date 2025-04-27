#!/usr/bin/env python3
import json
import csv
import os
import subprocess
import argparse
import shutil
import concurrent.futures
from pathlib import Path
from tqdm import tqdm  # Make sure to pip install tqdm

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Split CapCut project into smaller chunks')
    parser.add_argument('--csv', required=True, help='Path to clip_timeline.csv file')
    parser.add_argument('--splits', required=True, help='Path to splits JSON file (time_splits.json or media_splits.json)')
    parser.add_argument('--output', default='split_projects', help='Output directory for split projects')
    parser.add_argument('--ffmpeg', default='ffmpeg', help='Path to ffmpeg executable')
    parser.add_argument('--parallel', type=int, default=1, help='Number of parallel ffmpeg processes to run')
    parser.add_argument('--split-index', type=int, help='Process only the specified split index (1-based)')
    parser.add_argument('--wsl-path', help='WSL path prefix for Windows paths (e.g., /mnt)')
    parser.add_argument('--skip-existing', action='store_true', help='Skip extraction if output file already exists')
    parser.add_argument('--debug', action='store_true', help='Show detailed debug information')
    parser.add_argument('--report-only', action='store_true', help='Only report missing files, don\'t extract')
    args = parser.parse_args()
    
    # Load split plan first
    with open(args.splits, 'r') as f:
        splits = json.load(f)
    print(f"Loaded {len(splits)} splits from {args.splits}")
    
    # Process only a specific split if requested
    if args.split_index is not None:
        if args.split_index < 1 or args.split_index > len(splits):
            print(f"Error: Split index {args.split_index} is out of range (1-{len(splits)})")
            return
        
        splits_to_process = [splits[args.split_index - 1]]
        split_indices = [args.split_index - 1]
        print(f"Processing only split {args.split_index} of {len(splits)}")
    else:
        splits_to_process = splits
        split_indices = list(range(len(splits)))
    
    # Check for source file existence
    all_source_files = set()
    for split in splits_to_process:
        for clip in split["clips"]:
            if clip.get('source_file'):
                all_source_files.add(clip['source_file'])
    
    print(f"Found {len(all_source_files)} unique source files in splits")
    
    # Check source file existence
    missing_files = []
    accessible_files = []
    
    for source_file in all_source_files:
        # Convert Windows path to WSL path if needed
        converted_path = convert_windows_path(source_file, args.wsl_path)
        
        if os.path.exists(converted_path):
            accessible_files.append((source_file, converted_path))
        else:
            missing_files.append((source_file, converted_path))
    
    print(f"Found {len(accessible_files)} accessible files")
    print(f"Missing {len(missing_files)} files")
    
    # Report missing files
    if missing_files:
        print("\nMissing files:")
        for win_path, converted_path in missing_files[:10]:  # Show first 10
            print(f"  - Original: {win_path}")
            print(f"    Converted: {converted_path}")
        
        if len(missing_files) > 10:
            print(f"  (and {len(missing_files) - 10} more)")
    
    # Create file mapping
    file_mapping = {win_path: converted_path for win_path, converted_path in accessible_files}
    
    # Save file mapping
    mapping_path = os.path.join(args.output, "file_mapping.json")
    os.makedirs(args.output, exist_ok=True)
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(file_mapping, f, indent=2)
    
    print(f"File mapping saved to {mapping_path}")
    
    # Exit if report-only mode
    if args.report_only:
        print("Report-only mode. Exiting without extraction.")
        return
    
    # Process each split using the file mapping
    for i, split in zip(split_indices, splits_to_process):
        split_dir = os.path.join(args.output, f"split_{i+1}")
        os.makedirs(split_dir, exist_ok=True)
        
        # Process clips in this split
        split_clips = split["clips"]
        print(f"Processing Split {i+1} with {len(split_clips)} clips...")
        
        # Map any source file references to accessible paths
        for clip in split_clips:
            if clip.get('source_file') in file_mapping:
                clip['_accessible_path'] = file_mapping[clip['source_file']]
            else:
                clip['_accessible_path'] = None
        
        # Extract clips and generate ordered CSV
        process_split(
            split_dir, 
            split_clips, 
            i+1, 
            args.ffmpeg, 
            args.parallel,
            args.skip_existing,
            args.debug
        )
    
    print(f"All splits processed and saved to {args.output}")

def convert_windows_path(win_path, wsl_path_prefix=None):
    """Convert Windows path to Linux path if needed"""
    if not win_path:
        return None
        
    # Check if this is a Windows path
    if ':' in win_path:
        # This is a Windows path, convert it
        if wsl_path_prefix:
            # Extract drive letter and rest of path
            drive_letter = win_path[0].lower()
            
            # Handle both slash types
            if '/' in win_path:
                # Format with forward slashes
                path_part = win_path[2:] if win_path[2] == '/' else win_path[3:]
                return f"{wsl_path_prefix}/{drive_letter}/{path_part}".replace('\\', '/')
            else:
                # Format with backslashes
                path_part = win_path[2:] if win_path[2] == '\\' else win_path[3:]
                return f"{wsl_path_prefix}/{drive_letter}/{path_part}".replace('\\', '/')
        else:
            # Running on Windows - path is already correct
            return win_path.replace('\\', '/')
    else:
        # Not a Windows path or already converted
        return win_path

def sanitize_filename(filename):
    """Make a string safe to use as a filename"""
    # Replace invalid characters with underscores
    import re
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def get_output_filename(clip, track_idx, clip_idx):
    """Generate an ordered output filename based on clip position"""
    if not clip.get('source_file'):
        return None
        
    # Get base name from source
    source_basename = os.path.basename(clip['source_file'])
    base_name, ext = os.path.splitext(source_basename)
    
    # Clean up the base name
    base_name = sanitize_filename(base_name)
    
    # Format timeline position for sorting (HH_MM_SS_mmm)
    pos_seconds = clip['timeline_start'] / 1000000
    pos_hours = int(pos_seconds // 3600)
    pos_minutes = int((pos_seconds % 3600) // 60)
    pos_seconds = pos_seconds % 60
    pos_str = f"{pos_hours:02d}_{pos_minutes:02d}_{int(pos_seconds):02d}_{int((pos_seconds % 1) * 1000):03d}"
    
    # Construct final filename
    filename = f"T{track_idx:02d}_P{pos_str}_{base_name}_clip{clip_idx:03d}{ext}"
    
    return filename

def process_split(output_dir, clips, split_num, ffmpeg_path, parallel_count=1, skip_existing=False, debug=False):
    """Process clips for a single split"""
    # Group clips by track and source file for better organization
    track_clips = {}
    for clip in clips:
        track_idx = clip.get('track_idx')
        if track_idx not in track_clips:
            track_clips[track_idx] = []
        track_clips[track_idx].append(clip)
    
    # Prepare clip extraction tasks
    extract_tasks = []
    clip_metadata = []
    
    for track_idx, track_clip_list in track_clips.items():
        # Sort clips by timeline position
        track_clip_list.sort(key=lambda x: x['timeline_start'])
        
        for clip_idx, clip in enumerate(track_clip_list):
            source_file = clip.get('_accessible_path')  # Use the accessible path
            source_start = clip.get('source_start')
            source_duration = clip.get('source_duration')
            
            # Skip clips with missing information
            if not source_file or source_start is None or source_duration is None:
                print(f"  Warning: Missing info for clip at position {format_time(clip['timeline_start'])} on track {track_idx}")
                continue
            
            # Skip clips with inaccessible files
            if not os.path.exists(source_file):
                print(f"  Warning: Source file not accessible: {source_file}")
                continue
            
            # Generate output filename with order information
            output_filename = get_output_filename(clip, track_idx, clip_idx)
            if not output_filename:
                continue
                
            output_path = os.path.join(output_dir, output_filename)
            
            # Add to extraction tasks
            extract_tasks.append({
                'source_file': source_file,
                'output_path': output_path,
                'start_time': source_start / 1000000,  # Convert to seconds
                'duration': source_duration / 1000000,  # Convert to seconds
                'ffmpeg_path': ffmpeg_path,
                'skip_existing': skip_existing,
                'debug': debug,
                'file_type': os.path.splitext(source_file.lower())[1]
            })
            
            # Add to metadata for CSV
            clip_metadata.append({
                'filename': output_filename,
                'track_idx': track_idx,
                'track_type': clip.get('track_type', 'unknown'),
                'timeline_start': clip['timeline_start'],
                'timeline_end': clip['timeline_end'],
                'timeline_duration': clip['timeline_duration'],
                'source_file': clip.get('source_file'),  # Original path
                'source_start': source_start,
                'source_duration': source_duration,
                'readable_position': format_time(clip['timeline_start']),
                'readable_duration': format_time(clip['timeline_duration'])
            })
    
    # Execute extraction tasks
    if len(extract_tasks) > 1:
        print(f"  Extracting {len(extract_tasks)} clips using up to {parallel_count} parallel processes...")
    else:
        print(f"  Extracting {len(extract_tasks)} clip...")
        
    successful_extractions = 0
    
    if parallel_count > 1 and len(extract_tasks) > 1:
        # Use parallel execution with progress bar
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
            futures = [executor.submit(extract_clip_task, task) for task in extract_tasks]
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(extract_tasks), desc="Extracting clips"):
                if future.result():
                    successful_extractions += 1
    else:
        # Use sequential execution with progress bar
        for task in tqdm(extract_tasks, desc="Extracting clips"):
            if extract_clip_task(task):
                successful_extractions += 1
    
    print(f"  Successfully extracted {successful_extractions} of {len(extract_tasks)} clips")
    
    # Generate CSV with ordered clip information
    if clip_metadata:
        csv_path = os.path.join(output_dir, "clips_order.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'filename', 'track_idx', 'track_type', 
                'timeline_start', 'timeline_end', 'timeline_duration',
                'source_file', 'source_start', 'source_duration',
                'readable_position', 'readable_duration'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for metadata in sorted(clip_metadata, key=lambda x: (x['track_idx'], x['timeline_start'])):
                writer.writerow(metadata)
        
        print(f"  Generated clip order CSV: {csv_path}")
        
        # Generate import instructions
        generate_import_instructions(output_dir, clip_metadata, split_num)

def extract_clip_task(task):
    """Extract a clip using ffmpeg (for parallel execution)"""
    source_file = task['source_file']
    output_path = task['output_path']
    start_time = task['start_time']
    duration = task['duration']
    ffmpeg_path = task['ffmpeg_path']
    skip_existing = task.get('skip_existing', False)
    debug = task.get('debug', False)
    file_type = task.get('file_type', '')
    
    # Skip if output already exists and is a valid file
    if skip_existing and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"  Skipping existing file: {os.path.basename(output_path)}")
        return True
    
    return extract_clip(source_file, output_path, start_time, duration, ffmpeg_path, file_type, debug)

def extract_clip(source_file, output_path, start_time, duration, ffmpeg_path, file_type='', debug=False):
    """Extract a clip using ffmpeg with fallbacks for different file types"""
    try:
        # Handle different file types
        if file_type in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            # For image files, just copy the file
            shutil.copy2(source_file, output_path)
            print(f"  Copied image: {os.path.basename(output_path)}")
            return True
            
        elif file_type in ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a']:
            # For audio files
            if debug:
                print(f"DEBUG: Extracting audio file: {source_file} to {output_path}")
                print(f"DEBUG: Start time: {start_time}, Duration: {duration}")
                
            # First try with copy (faster)
            try:
                cmd = [
                    ffmpeg_path,
                    "-y",  # Overwrite output files without asking
                    "-ss", str(start_time),
                    "-i", source_file,
                    "-t", str(duration),
                    "-acodec", "copy",
                    output_path
                ]
                
                if debug:
                    print(f"DEBUG: Running command: {' '.join(cmd)}")
                    
                result = subprocess.run(cmd, check=True, capture_output=True)
                return True
                
            except subprocess.CalledProcessError:
                # Fallback to the slower but more reliable method
                try:
                    cmd = [
                        ffmpeg_path,
                        "-y",
                        "-i", source_file,
                        "-ss", str(start_time),
                        "-t", str(duration),
                        output_path
                    ]
                    
                    if debug:
                        print(f"DEBUG: Fallback command: {' '.join(cmd)}")
                        
                    result = subprocess.run(cmd, check=True, capture_output=True)
                    return True
                    
                except subprocess.CalledProcessError as e:
                    if debug:
                        print(f"DEBUG: Error with fallback command: {e}")
                        try:
                            error_output = e.stderr.decode('utf-8', errors='replace')
                            print(f"DEBUG: FFmpeg error: {error_output}")
                        except:
                            pass
                    
                    # Last resort: try to copy the entire file
                    print(f"  Warning: Couldn't extract audio segment. Copying entire file instead: {os.path.basename(source_file)}")
                    try:
                        shutil.copy2(source_file, output_path)
                        return True
                    except Exception as copy_error:
                        print(f"  Error copying file: {copy_error}")
                        return False
                        
        else:
            # For video files
            if debug:
                print(f"DEBUG: Extracting video file: {source_file} to {output_path}")
                print(f"DEBUG: Start time: {start_time}, Duration: {duration}")
                
            # First try with copy (faster)
            try:
                cmd = [
                    ffmpeg_path,
                    "-y",
                    "-ss", str(start_time),
                    "-i", source_file,
                    "-t", str(duration),
                    "-c", "copy",
                    "-avoid_negative_ts", "1",
                    output_path
                ]
                
                if debug:
                    print(f"DEBUG: Running command: {' '.join(cmd)}")
                    
                result = subprocess.run(cmd, check=True, capture_output=True)
                return True
                
            except subprocess.CalledProcessError:
                # Try with re-encoding but seek before input (faster)
                try:
                    cmd = [
                        ffmpeg_path,
                        "-y",
                        "-ss", str(start_time),
                        "-i", source_file,
                        "-t", str(duration),
                        "-c:v", "libx264",
                        "-preset", "veryfast",
                        "-crf", "23",
                        output_path
                    ]
                    
                    if debug:
                        print(f"DEBUG: First fallback command: {' '.join(cmd)}")
                        
                    result = subprocess.run(cmd, check=True, capture_output=True)
                    return True
                    
                except subprocess.CalledProcessError:
                    # Last try with the most accurate but slowest method
                    try:
                        cmd = [
                            ffmpeg_path,
                            "-y",
                            "-i", source_file,
                            "-ss", str(start_time),
                            "-t", str(duration),
                            "-c:v", "libx264",
                            "-preset", "veryfast",
                            "-crf", "23",
                            output_path
                        ]
                        
                        if debug:
                            print(f"DEBUG: Last fallback command: {' '.join(cmd)}")
                            
                        result = subprocess.run(cmd, check=True, capture_output=True)
                        return True
                        
                    except subprocess.CalledProcessError as e:
                        if debug:
                            print(f"DEBUG: Error with last fallback command: {e}")
                            try:
                                error_output = e.stderr.decode('utf-8', errors='replace')
                                print(f"DEBUG: FFmpeg error: {error_output}")
                            except:
                                pass
                        
                        return False
                        
    except Exception as e:
        print(f"  Unexpected error extracting clip: {e}")
        if debug:
            import traceback
            traceback.print_exc()
            
        return False

def generate_import_instructions(output_dir, clip_metadata, split_num):
    """Generate instructions for importing clips to CapCut"""
    instruction_path = os.path.join(output_dir, "import_instructions.txt")
    
    with open(instruction_path, 'w', encoding='utf-8') as f:
        f.write(f"# Import Instructions for Split {split_num}\n\n")
        f.write("1. Create a new CapCut project\n")
        f.write("2. Import all the extracted clip files in this directory\n")
        f.write("3. The filenames are structured for easy ordering: T{track}_P{position}_{source}_{clip}\n")
        f.write("4. Place clips according to the 'clips_order.csv' file\n\n")
        
        # Group by track
        tracks = {}
        for clip in clip_metadata:
            track_idx = clip['track_idx']
            if track_idx not in tracks:
                tracks[track_idx] = []
            tracks[track_idx].append(clip)
        
        # Write clip details by track
        for track_idx, track_clips in sorted(tracks.items()):
            track_type = track_clips[0]['track_type']
            f.write(f"## Track {track_idx} ({track_type})\n")
            
            for clip in sorted(track_clips, key=lambda x: x['timeline_start']):
                f.write(f"- {os.path.basename(clip['filename'])}\n")
                f.write(f"  Position: {clip['readable_position']}, Duration: {clip['readable_duration']}\n")
            
            f.write("\n")

def format_time(time_value):
    """Format timeline units to a readable time format"""
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
    main()
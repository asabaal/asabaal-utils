#!/usr/bin/env python3
import csv
import os
import json
import argparse
import glob
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Create file mapping for CapCut files')
    parser.add_argument('--csv', required=True, help='Path to clip_timeline.csv file')
    parser.add_argument('--search-dirs', required=True, nargs='+', help='Directories to search for files')
    parser.add_argument('--output', default='file_mapping.json', help='Output mapping file')
    args = parser.parse_args()
    
    # Load CSV file
    clips = []
    with open(args.csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('source_file'):
                clips.append(row)
    
    print(f"Found {len(clips)} clips with source files in CSV")
    
    # Get unique source files
    source_files = set()
    for clip in clips:
        if clip.get('source_file'):
            source_files.add(clip['source_file'])
    
    print(f"Found {len(source_files)} unique source files")
    
    # Search for files
    file_mapping = {}
    found_count = 0
    
    for source_file in source_files:
        basename = os.path.basename(source_file)
        
        # Search in specified directories
        matches = []
        for search_dir in args.search_dirs:
            # Use glob to find files with this name
            pattern = f"{search_dir}/**/{basename}"
            matches.extend(glob.glob(pattern, recursive=True))
        
        if matches:
            file_mapping[source_file] = matches[0]  # Use first match
            found_count += 1
        else:
            file_mapping[source_file] = None
    
    print(f"Found {found_count} of {len(source_files)} files")
    
    # Save mapping
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(file_mapping, f, indent=2)
    
    print(f"File mapping saved to {args.output}")
    
    # Report missing files
    missing = [f for f, m in file_mapping.items() if m is None]
    if missing:
        print(f"\nMissing {len(missing)} files:")
        for f in missing[:10]:  # Show first 10
            print(f"  - {os.path.basename(f)}")
        
        if len(missing) > 10:
            print(f"  (and {len(missing) - 10} more)")

if __name__ == "__main__":
    main()

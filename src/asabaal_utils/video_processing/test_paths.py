#!/usr/bin/env python3
import json
import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Test file access in WSL')
    parser.add_argument('--splits', required=True, help='Path to media_splits.json')
    parser.add_argument('--wsl-path', default='/mnt', help='WSL path prefix for Windows drives')
    args = parser.parse_args()
    
    # Load splits file
    with open(args.splits, 'r') as f:
        splits = json.load(f)
    
    # Extract source files
    source_files = set()
    for split in splits:
        for clip in split.get('clips', []):
            if clip.get('source_file'):
                source_files.add(clip['source_file'])
    
    print(f"Found {len(source_files)} unique source files")
    
    # Test different WSL path prefixes
    prefixes = [
        args.wsl_path,  # User-provided
        '/mnt',         # Standard WSL
        '/media/' + os.environ.get('USER', 'user'),  # Some distros
        ''              # No prefix (direct path)
    ]
    
    # Try each prefix
    for prefix in prefixes:
        found = 0
        print(f"\nTesting with prefix: {prefix}")
        
        # Sample source files
        for source in list(source_files)[:10]:  # Show first 10
            # Convert Windows path
            if ':' in source:
                drive = source[0].lower()
                if prefix:
                    converted = source.replace(f"{drive}:/", f"{prefix}/{drive}/").replace('\\', '/')
                else:
                    converted = source.replace('\\', '/')
            else:
                converted = source
            breakpoint()
            # Check if it exists
            exists = os.path.exists(converted)
            if exists:
                found += 1
                status = "✓ EXISTS"
            else:
                status = "✗ NOT FOUND"
                
            print(f"{status}: {converted}")
        
        print(f"Found {found} of {len(source_files)} files with prefix '{prefix}'")

if __name__ == "__main__":
    main()

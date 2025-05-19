#!/usr/bin/env python
import sys
import argparse
import os
from pathlib import Path
from .syllable_counter import (
    analyze_lyrics_file, 
    print_analysis, 
    calculate_statistics, 
    detect_sections, 
    export_to_csv,
    export_statistics_to_csv
)

def main():
    parser = argparse.ArgumentParser(description="Analyze syllable counts in song lyrics.")
    parser.add_argument("file_path", help="Path to the lyrics file")
    parser.add_argument("--no-sections", action="store_true", help="Disable section detection")
    parser.add_argument("--csv", action="store_true", help="Export results to CSV")
    parser.add_argument("--stats-csv", action="store_true", help="Export statistics to CSV")
    parser.add_argument("--output", "-o", help="Output file path (defaults to input filename with .csv extension)")
    parser.add_argument("--stats-output", help="Statistics output file path (defaults to input filename with _stats.csv extension)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress console output")
    args = parser.parse_args()
    
    # Analyze the lyrics file
    results = analyze_lyrics_file(args.file_path)
    
    if not results:
        return 1
    
    # Detect sections if not disabled
    sections = detect_sections(results) if not args.no_sections else None
    has_sections = sections and len(set(sections)) > 1
    
    # Print analysis to console if not quiet
    if not args.quiet:
        print_analysis(results, sections if has_sections else None)
        calculate_statistics(results, sections if has_sections else None)
    
    # Export to CSV if requested
    if args.csv:
        input_path = Path(args.file_path)
        
        # Determine output path for main CSV
        if args.output:
            csv_path = args.output
        else:
            csv_path = input_path.with_suffix('.csv')
            
        export_to_csv(results, sections if has_sections else None, csv_path)
    
    # Export statistics to CSV if requested
    if args.stats_csv:
        input_path = Path(args.file_path)
        
        # Determine output path for statistics CSV
        if args.stats_output:
            stats_csv_path = args.stats_output
        else:
            stats_csv_path = input_path.with_suffix('.stats.csv')
            
        export_statistics_to_csv(results, sections if has_sections else None, stats_csv_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

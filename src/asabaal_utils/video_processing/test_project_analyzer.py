#!/usr/bin/env python3
"""
Test script for the project structure analyzer.

Usage:
    python test_project_analyzer.py path/to/draft_content.json
"""

import os
import sys
from analyze_project_structure import analyze_project_structure

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_project_analyzer.py path/to/draft_content.json")
        sys.exit(1)
    
    project_file = sys.argv[1]
    
    if not os.path.exists(project_file):
        print(f"Error: File {project_file} does not exist")
        sys.exit(1)
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(project_file), "project_analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the analyzer
    print(f"Analyzing project file: {project_file}")
    analyze_project_structure(project_file, output_dir, verbose=True)
    
    print(f"\nAnalysis complete. Results saved to {output_dir}")
    print("To use this analysis for detecting unused media, update the ClipPreviewGenerator with the correct structure information.")

if __name__ == "__main__":
    main()
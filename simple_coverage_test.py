#!/usr/bin/env python3
"""Simple test to verify file coverage in PR analyzer results"""

import json
from pathlib import Path

def check_file_coverage():
    """Check which files are being analyzed"""
    
    # Load Stage 1 file list
    stage1_file = Path("test_projects/pr_analysis_output/debug_outputs/stage1/file_classification_debug.json")
    if stage1_file.exists():
        with open(stage1_file) as f:
            stage1_data = json.load(f)
        
        # Extract all files from Stage 1
        stage1_files = set()
        for category_info in stage1_data.get('category_summary', {}).values():
            for file_path in category_info.get('files', []):
                stage1_files.add(file_path)
        
        print(f"Stage 1 identified {len(stage1_files)} files:")
        for f in sorted(stage1_files):
            print(f"  - {f}")
    else:
        print("❌ Stage 1 file not found")
        return False
    
    # Load Stage 7 analysis
    stage7_file = Path("test_projects/pr_analysis_output/detailed_analysis_results.json")
    if stage7_file.exists():
        with open(stage7_file) as f:
            stage7_data = json.load(f)
        
        stage7_files = {item['file_path'] for item in stage7_data.get('file_analyses', [])}
        
        print(f"\nStage 7 analyzed {len(stage7_files)} files:")
        for f in sorted(stage7_files):
            print(f"  - {f}")
        
        # Check for missing files
        missing_files = stage1_files - stage7_files
        if missing_files:
            print(f"\n❌ MISSING FILES ({len(missing_files)}):")
            for f in sorted(missing_files):
                print(f"  - {f}")
            return False
        else:
            print("\n✅ All files accounted for!")
            return True
    else:
        print("❌ Stage 7 file not found")
        return False

if __name__ == "__main__":
    success = check_file_coverage()
    print(f"\nResult: {'PASS' if success else 'FAIL'}")
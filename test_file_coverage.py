#!/usr/bin/env python3
"""Test script to verify file coverage fix in PR analyzer"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.pr_analyzer.stage7_detailed_analysis_v2 import DetailedAnalysisEngine
from asabaal_utils.pr_analyzer.core.git_analyzer import GitAnalyzer

def test_file_coverage():
    """Test that all files are being analyzed"""
    
    # Initialize git analyzer to get file list
    git_analyzer = GitAnalyzer(repo_path=".", from_branch="test-projects", to_branch="main")
    git_analyzer.analyze_changes()
    
    # Get files from Stage 1
    files_array = git_analyzer.get_files_array()
    stage1_files = {f['path'] for f in files_array if not f.get('deleted', False)}
    
    print(f"Stage 1 identified {len(stage1_files)} files:")
    for f in sorted(stage1_files):
        print(f"  - {f}")
    
    # Initialize Stage 7 engine
    engine = DetailedAnalysisEngine(repo_path=".", from_branch="test-projects", to_branch="main")
    
    # Load existing analysis if available
    analysis_file = Path("test_projects/pr_analysis_output/detailed_analysis_results.json")
    if analysis_file.exists():
        with open(analysis_file) as f:
            analysis_data = json.load(f)
        
        stage7_files = {item['file_path'] for item in analysis_data.get('file_analyses', [])}
        
        print(f"\nStage 7 analyzed {len(stage7_files)} files:")
        for f in sorted(stage7_files):
            print(f"  - {f}")
        
        # Check for missing files
        missing_files = stage1_files - stage7_files
        if missing_files:
            print(f"\n❌ MISSING FILES ({len(missing_files)}):")
            for f in sorted(missing_files):
                print(f"  - {f}")
        else:
            print("\n✅ All files accounted for!")
            
        # Test validation method
        print("\n🔧 Testing validation method...")
        validated_analysis = engine._ensure_all_files_analyzed(analysis_data, files_array)
        validated_files = {item['file_path'] for item in validated_analysis.get('file_analyses', [])}
        
        if len(validated_files) > len(stage7_files):
            print(f"✅ Validation added {len(validated_files) - len(stage7_files)} missing files")
            newly_added = validated_files - stage7_files
            for f in sorted(newly_added):
                print(f"  + {f}")
        else:
            print("⚠️ Validation didn't add any files")
            
        return len(missing_files) == 0
    else:
        print(f"\n❌ No analysis file found at {analysis_file}")
        return False

if __name__ == "__main__":
    success = test_file_coverage()
    sys.exit(0 if success else 1)
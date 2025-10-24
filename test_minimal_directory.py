#!/usr/bin/env python3
"""
Minimal test of directory mode using just the git analyzer
"""

import os
import sys
from pathlib import Path

# Add the analyzer source to Python path
analyzer_src = Path(__file__).parent / "agents" / "pr_analyzer" / "src"
sys.path.insert(0, str(analyzer_src))

# Set test mode
os.environ['PR_ANALYZER_TEST_MODE'] = 'true'

try:
    # Import just the git analyzer which has the test mode logic
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "git_analyzer", 
        analyzer_src / "core" / "git_analyzer.py"
    )
    git_analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(git_analyzer)
    
    print("✅ Successfully imported git_analyzer")
    
    # Test the test file changes functionality
    test_dir = Path(__file__).parent / "test_projects"
    analyzer = git_analyzer.GitAnalyzer(str(test_dir))
    
    print("✅ GitAnalyzer initialized")
    
    # Get test file changes (this is what directory mode uses)
    changes = analyzer._get_test_file_changes()
    
    print(f"📁 Found {len(changes)} files for analysis:")
    for change in changes[:5]:  # Show first 5
        print(f"   - {change.file_path}")
    
    if len(changes) > 5:
        print(f"   ... and {len(changes) - 5} more files")
        
    print("✅ Directory mode test successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
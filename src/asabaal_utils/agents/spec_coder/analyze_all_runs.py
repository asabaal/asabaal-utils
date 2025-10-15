#!/usr/bin/env python3
"""Analyze all generated test files from all reproducibility runs."""

import json
import shutil
from pathlib import Path
try:
    from .analyze_tests import TestAnalyzer
except ImportError:
    from analyze_tests import TestAnalyzer

def main():
    """Analyze all runs and combine results."""
    analyzer = TestAnalyzer()
    
    # Create a temporary directory to collect all test files
    temp_dir = Path("/tmp/all_generated_tests")
    temp_dir.mkdir(exist_ok=True)
    
    # Collect test files from all runs
    all_test_files = []
    for run_num in range(3):  # run_0, run_1, run_2
        run_dir = Path(f"../reproducibility_output/run_{run_num}/scaffolds/tests/scaffolds/tests")
        if run_dir.exists():
            for test_file in run_dir.glob("*.py"):
                # Copy to temp directory with run prefix
                dest_file = temp_dir / f"run_{run_num}_{test_file.name}"
                shutil.copy2(test_file, dest_file)
                all_test_files.append(dest_file)
    
    print(f"Found {len(all_test_files)} test files across all runs")
    
    # Analyze all collected files
    if all_test_files:
        analyzer.analyze_directory(str(temp_dir))
        print("Analysis complete for all runs")
    else:
        print("No test files found to analyze")
    
    # Clean up
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
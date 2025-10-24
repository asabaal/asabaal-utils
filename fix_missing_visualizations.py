#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import flowscope
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.scanner import scan_file
from asabaal_utils.flowscope.visualize import create_pyvis_graph
from asabaal_utils.flowscope.snapshot import save_graph

def fix_missing_visualizations():
    """Generate HTML visualizations for modules that are missing them."""
    
    modules_dir = Path("src/asabaal_utils/agents/spec_coder/analysis_output/modules_by_file")
    
    if not modules_dir.exists():
        print(f"Error: {modules_dir} does not exist")
        return
    
    # Find all .txt report files
    report_files = list(modules_dir.glob("*_report.txt"))
    
    print(f"Found {len(report_files)} report files")
    
    fixed_count = 0
    
    for report_file in report_files:
        # Extract module name from filename
        module_name = report_file.stem.replace("_report", "")
        
        # Check if HTML visualization already exists
        html_file = modules_dir / f"{module_name}_graph.html"
        json_file = modules_dir / f"{module_name}_graph.json"
        
        if html_file.exists():
            print(f"✓ {module_name}: HTML already exists")
            continue
            
        # Check if JSON graph exists
        if not json_file.exists():
            print(f"✗ {module_name}: No JSON graph found")
            continue
            
        print(f"→ {module_name}: Generating HTML visualization...")
        
        try:
            # Find the corresponding Python file
            py_file = None
            possible_names = [
                f"{module_name}.py",
                f"test_{module_name}.py",
                f"{module_name.replace('test_', '')}.py"
            ]
            
            # Look in the spec_coder directory
            spec_coder_dir = Path("src/asabaal_utils/agents/spec_coder")
            for name in possible_names:
                candidate = spec_coder_dir / name
                if candidate.exists():
                    py_file = candidate
                    break
                    
            # Also check in subdirectories
            if not py_file:
                for candidate in spec_coder_dir.rglob("*.py"):
                    if candidate.stem == module_name or candidate.stem == f"test_{module_name}":
                        py_file = candidate
                        break
            
            if not py_file:
                print(f"  ✗ Could not find Python file for {module_name}")
                continue
                
            # Scan the file and create visualization
            print(f"  Scanning {py_file}")
            graph = scan_file(py_file)
            
            if graph.number_of_nodes() == 0:
                print(f"  ✗ No functions found in {py_file}")
                continue
                
            # Create HTML visualization
            print(f"  Creating visualization with {graph.number_of_nodes()} functions, {graph.number_of_edges()} calls")
            create_pyvis_graph(graph, html_file, title=f"Call Graph: {module_name}")
            
            print(f"  ✓ Saved to {html_file}")
            fixed_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
    print(f"\nSummary: Fixed {fixed_count} missing visualizations")

if __name__ == "__main__":
    fix_missing_visualizations()
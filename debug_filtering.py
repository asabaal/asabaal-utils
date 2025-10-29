#!/usr/bin/env python3
"""Debug why calls are being filtered out."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.scanner import scan_file, _is_external_function

def debug_filtering():
    # Scan the generator file
    generator_path = Path("src/asabaal_utils/agents/spec_coder/generator.py")
    graph = scan_file(generator_path)
    
    # Find generate_from_spec function
    target_node = "generator.generate_from_spec"
    
    print(f"Analyzing calls for {target_node}:")
    
    # Get all nodes and check what _is_external_function returns for each
    local_modules = {"generator"}
    
    for node in graph.nodes():
        if node != target_node:
            is_external = _is_external_function(node, local_modules)
            print(f"  {node}: external={is_external}")
    
    # Check what calls would be detected without filtering
    print(f"\nOutgoing edges from {target_node}:")
    for src, dst, data in graph.out_edges(target_node, data=True):
        print(f"  -> {dst} (line {data.get('line', 'unknown')})")

if __name__ == "__main__":
    debug_filtering()
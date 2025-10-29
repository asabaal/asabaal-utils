#!/usr/bin/env python3
"""Debug script to test scanner on generator.py specifically."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.scanner import scan_file

def test_generator_scanning():
    # Scan just the generator file
    generator_path = Path("src/asabaal_utils/agents/spec_coder/generator.py")
    if not generator_path.exists():
        print(f"ERROR: {generator_path} not found!")
        return
    
    print(f"Scanning {generator_path}...")
    graph = scan_file(generator_path)
    
    # Find generate_from_spec function
    target_node = None
    for node in graph.nodes():
        if "generate_from_spec" in node:
            target_node = node
            break
    
    if not target_node:
        print("ERROR: generate_from_spec function not found!")
        print("Available nodes:")
        for node in graph.nodes():
            print(f"  - {node}")
        return
    
    print(f"\nFound generate_from_spec function:")
    print(f"  - Node: {target_node}")
    
    # Get outgoing edges (calls made by this function)
    outgoing_edges = list(graph.out_edges(target_node, data=True))
    print(f"  - Calls: {len(outgoing_edges)}")
    
    if outgoing_edges:
        print("  - Called functions:")
        for src, dst, data in outgoing_edges:
            print(f"    * {dst} (line {data.get('line', 'unknown')})")
    else:
        print("  - NO CALLS DETECTED (this is the problem!)")
    
    # Also check what functions were found in total
    print(f"\nTotal functions found in file: {graph.number_of_nodes()}")
    for node in graph.nodes():
        print(f"  - {node}")

if __name__ == "__main__":
    test_generator_scanning()
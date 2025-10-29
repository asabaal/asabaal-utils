#!/usr/bin/env python3
"""Test the graph layout optimizer script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import networkx as nx
from graph_layout_optimizer import optimize_graph_layout

def test_layout_optimizer():
    print("Testing graph layout optimizer...")
    
    # Create a test graph similar to function flow graphs
    G = nx.DiGraph()
    
    # Add nodes (like functions)
    nodes = [
        "main_func", "helper1", "helper2", "helper3", 
        "subhelper1", "subhelper2", "leaf1", "leaf2", "leaf3"
    ]
    for node in nodes:
        G.add_node(node)
    
    # Add edges (like function calls)
    edges = [
        ("main_func", "helper1"),
        ("main_func", "helper2"), 
        ("main_func", "helper3"),
        ("helper1", "subhelper1"),
        ("helper1", "subhelper2"),
        ("helper2", "leaf1"),
        ("helper3", "leaf2"),
        ("helper3", "leaf3")
    ]
    for edge in edges:
        G.add_edge(*edge)
    
    print(f"Created test graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Test the optimizer
    try:
        pos, crossings = optimize_graph_layout(G, return_crossings=True)
        print(f"✓ Layout optimization successful!")
        print(f"  Final crossings: {crossings}")
        print(f"  Node positions: {len(pos)}")
        
        # Show some sample positions
        for i, (node, (x, y)) in enumerate(pos.items()):
            if i < 5:  # Show first 5
                print(f"    {node}: ({x:.2f}, {y:.2f})")
            if i == 4 and len(pos) > 5:
                print(f"    ... and {len(pos) - 5} more nodes")
        
        return True
        
    except Exception as e:
        print(f"✗ Layout optimization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_layout_optimizer()
    if success:
        print("\n✅ Layout optimizer test PASSED")
    else:
        print("\n❌ Layout optimizer test FAILED")
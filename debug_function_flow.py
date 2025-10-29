#!/usr/bin/env python3
"""Debug why Function Flow Graph shows single nodes."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.snapshot import load_graph

def debug_function_flow():
    # Load the graph
    graph = load_graph(Path("spec_coder_graph_fixed.json"))
    
    # Test generator.generate_from_spec
    function_name = "generator.generate_from_spec"
    
    print(f"Debugging {function_name}:")
    print(f"  Function exists in graph: {function_name in graph.nodes}")
    
    if function_name in graph.nodes:
        successors = list(graph.successors(function_name))
        predecessors = list(graph.predecessors(function_name))
        print(f"  Successors (outgoing edges): {len(successors)}")
        for succ in successors:
            print(f"    - {succ}")
        print(f"  Predecessors (incoming edges): {len(predecessors)}")
        for pred in predecessors:
            print(f"    - {pred}")
    else:
        print("  Available functions containing 'generate_from_spec':")
        for node in graph.nodes():
            if "generate_from_spec" in node:
                print(f"    - {node}")
    
    # Test orchestrator._stage1_spec_to_scaffold
    function_name2 = "orchestrator._stage1_spec_to_scaffold"
    print(f"\nDebugging {function_name2}:")
    print(f"  Function exists in graph: {function_name2 in graph.nodes}")
    
    if function_name2 in graph.nodes:
        successors2 = list(graph.successors(function_name2))
        predecessors2 = list(graph.predecessors(function_name2))
        print(f"  Successors (outgoing edges): {len(successors2)}")
        for succ in successors2:
            print(f"    - {succ}")
        print(f"  Predecessors (incoming edges): {len(predecessors2)}")
        for pred in predecessors2:
            print(f"    - {pred}")
    else:
        print("  Available functions containing '_stage1_spec_to_scaffold':")
        for node in graph.nodes():
            if "_stage1_spec_to_scaffold" in node:
                print(f"    - {node}")
    
    # Check some stats
    print(f"\nGraph statistics:")
    print(f"  Total nodes: {graph.number_of_nodes()}")
    print(f"  Total edges: {graph.number_of_edges()}")
    
    # Check generator functions
    print(f"\nGenerator functions:")
    for node in graph.nodes():
        if node.startswith("generator."):
            out_edges = list(graph.successors(node))
            if out_edges:
                print(f"  {node}: {len(out_edges)} outgoing edges")

if __name__ == "__main__":
    debug_function_flow()
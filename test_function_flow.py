#!/usr/bin/env python3
"""Test if the Function Flow Graph is working correctly."""

import sys
from pathlib import Path
import networkx as nx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.visualize import create_function_flow_data
from asabaal_utils.flowscope.snapshot import load_graph

def test_function_flow_graph():
    # Load the graph data as NetworkX graph
    graph = load_graph(Path("spec_coder_graph_fixed.json"))
    
    # Test generator.generate_from_spec
    function_name = "generator.generate_from_spec"
    module_name = "generator"
    
    print(f"Testing Function Flow Graph for {function_name}:")
    
    # Create the function flow graph data
    flow_data = create_function_flow_data(graph, function_name)
    
    print(f"  Nodes: {len(flow_data['nodes'])}")
    print(f"  Edges: {len(flow_data['edges'])}")
    
    if flow_data['nodes']:
        print("  Node details:")
        for node in flow_data['nodes']:
            print(f"    - {node['id']} ({node['label']})")
    
    if flow_data['edges']:
        print("  Edge details:")
        for edge in flow_data['edges']:
            print(f"    - {edge['from']} -> {edge['to']}")
    
    # Test orchestrator._stage1_spec_to_scaffold
    print(f"\nTesting Function Flow Graph for orchestrator._stage1_spec_to_scaffold:")
    function_name2 = "orchestrator._stage1_spec_to_scaffold"
    module_name2 = "orchestrator"
    
    flow_data2 = create_function_flow_data(graph, function_name2)
    
    print(f"  Nodes: {len(flow_data2['nodes'])}")
    print(f"  Edges: {len(flow_data2['edges'])}")
    
    if flow_data2['nodes']:
        print("  Node details:")
        for node in flow_data2['nodes']:
            print(f"    - {node['id']} ({node['label']})")
    
    if flow_data2['edges']:
        print("  Edge details:")
        for edge in flow_data2['edges']:
            print(f"    - {edge['from']} -> {edge['to']}")

if __name__ == "__main__":
    test_function_flow_graph()
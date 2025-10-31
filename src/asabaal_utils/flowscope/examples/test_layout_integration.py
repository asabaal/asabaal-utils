#!/usr/bin/env python3
"""
Test integration of layout relaxer with structure examples
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append('..')

def create_simple_test_graph():
    """Create a simple test graph from structure examples"""
    
    # Import layout relaxer
    try:
        from layout_relaxer import GraphLayout
    except ImportError as e:
        print(f"Could not import layout_relaxer: {e}")
        return None
    
    G = GraphLayout()
    
    # Conservative physics parameters
    G.k_spring = 0.08
    G.k_repel = 30.0
    G.k_barrier = 60.0
    G.L0 = 2.0
    G.step = 0.01
    G.damping = 0.95
    G.edge_radius = 0.5
    
    # Node styles
    STYLES = {
        "entry": {"shape": "ellipse", "color": "#90ee90"},
        "exit": {"shape": "ellipse", "color": "#ff6b6b"},
        "assignment": {"shape": "box", "color": "#ffd700"},
        "conditional": {"shape": "diamond", "color": "#ffa500"},
        "loop": {"shape": "diamond", "color": "#ff9999"},
        "statement": {"shape": "box", "color": "#97c2fc"},
        "return": {"shape": "box", "color": "#90ee90"},
        "merge": {"shape": "circle", "color": "#d3d3d3"},
    }
    
    # Create a binary branching structure (like binary_6_lines)
    G.add_node("n0", "entry", **STYLES["entry"], width=1.8, height=1.2, pos=(0.0, 0.0))
    G.add_node("n1", "x > 5", **STYLES["conditional"], width=2.2, height=1.6, pos=(0.0, 2.0))
    G.add_node("n2", "result = x * 2", **STYLES["assignment"], width=2.5, height=1.2, pos=(-3.0, 4.0))
    G.add_node("n3", "result = x + 10", **STYLES["assignment"], width=2.5, height=1.2, pos=(3.0, 4.0))
    G.add_node("n4", "return result", **STYLES["return"], width=2.0, height=1.2, pos=(0.0, 6.0))
    G.add_node("n5", "exit", **STYLES["exit"], width=1.8, height=1.2, pos=(0.0, 8.0))
    
    # Add edges
    G.add_edge("n0", "n1")
    G.add_edge("n1", "n2")  # true branch
    G.add_edge("n1", "n3")  # false branch
    G.add_edge("n2", "n4")
    G.add_edge("n3", "n4")
    G.add_edge("n4", "n5")
    
    return G

def run_simulation_test():
    """Run a test simulation"""
    print("Testing layout relaxer integration...")
    
    # Create test graph
    G = create_simple_test_graph()
    if G is None:
        print("Failed to create test graph")
        return
    
    print(f"Created graph with {len(G.nodes)} nodes and {len(G.edges)} edges")
    
    # Import simulation visualizer
    try:
        from layout_simulation_visualizer import LayoutSimulationVisualizer
    except ImportError as e:
        print(f"Could not import LayoutSimulationVisualizer: {e}")
        return
    
    # Create visualizer
    visualizer = LayoutSimulationVisualizer(max_frames_in_memory=20)
    
    # Run simulation
    output_dir = Path(".")
    frames_file = output_dir / "test_simulation_frames.json"
    
    print("Running layout relaxation simulation...")
    visualizer.run_simulation(
        G,
        iterations=100,
        capture_interval=2,
        output_file=str(frames_file)
    )
    
    # Load frames and generate HTML
    visualizer.load_frames(str(frames_file))
    html_file = output_dir / "test_layout_simulation.html"
    visualizer.generate_html_visualizer(str(html_file))
    
    print(f"✓ Test simulation complete!")
    print(f"  Frames: {frames_file}")
    print(f"  HTML: {html_file}")
    
    # Show final positions
    print(f"\nFinal node positions:")
    for name in G.nodes:
        n = G.nodes[name]
        print(f"  {name:>3} ({n.x:8.3f}, {n.y:8.3f})")

def create_multiple_structure_tests():
    """Create tests for different structure types"""
    
    structure_types = {
        "linear": {
            "description": "Simple linear flow",
            "nodes": [
                ("n0", "entry", "entry", (0.0, 0.0)),
                ("n1", "x = x + 1", "assignment", (0.0, 2.0)),
                ("n2", "y = x * 2", "assignment", (0.0, 4.0)),
                ("n3", "return y", "return", (0.0, 6.0)),
                ("n4", "exit", "exit", (0.0, 8.0)),
            ],
            "edges": [("n0", "n1"), ("n1", "n2"), ("n2", "n3"), ("n3", "n4")]
        },
        "loop": {
            "description": "Loop structure",
            "nodes": [
                ("n0", "entry", "entry", (0.0, 0.0)),
                ("n1", "i = 0", "assignment", (0.0, 2.0)),
                ("n2", "i < 10", "loop", (0.0, 4.0)),
                ("n3", "process(i)", "statement", (3.0, 6.0)),
                ("n4", "i += 1", "assignment", (3.0, 8.0)),
                ("n5", "return", "return", (0.0, 10.0)),
                ("n6", "exit", "exit", (0.0, 12.0)),
            ],
            "edges": [("n0", "n1"), ("n1", "n2"), ("n2", "n3"), ("n3", "n4"), 
                     ("n4", "n2"), ("n2", "n5"), ("n5", "n6")]
        },
        "nested": {
            "description": "Nested conditional structure",
            "nodes": [
                ("n0", "entry", "entry", (0.0, 0.0)),
                ("n1", "x > 0", "conditional", (0.0, 2.0)),
                ("n2", "y > 0", "conditional", (-3.0, 4.0)),
                ("n3", "result = x + y", "assignment", (-5.0, 6.0)),
                ("n4", "result = x - y", "assignment", (-1.0, 6.0)),
                ("n5", "result = -x", "assignment", (3.0, 4.0)),
                ("n6", "return result", "return", (0.0, 8.0)),
                ("n7", "exit", "exit", (0.0, 10.0)),
            ],
            "edges": [("n0", "n1"), ("n1", "n2"), ("n1", "n5"), ("n2", "n3"), 
                     ("n2", "n4"), ("n3", "n6"), ("n4", "n6"), ("n5", "n6"), ("n6", "n7")]
        }
    }
    
    try:
        from layout_relaxer import GraphLayout
        from layout_simulation_visualizer import LayoutSimulationVisualizer
    except ImportError as e:
        print(f"Import error: {e}")
        return
    
    STYLES = {
        "entry": {"shape": "ellipse", "color": "#90ee90"},
        "exit": {"shape": "ellipse", "color": "#ff6b6b"},
        "assignment": {"shape": "box", "color": "#ffd700"},
        "conditional": {"shape": "diamond", "color": "#ffa500"},
        "loop": {"shape": "diamond", "color": "#ff9999"},
        "statement": {"shape": "box", "color": "#97c2fc"},
        "return": {"shape": "box", "color": "#90ee90"},
        "merge": {"shape": "circle", "color": "#d3d3d3"},
    }
    
    print("Creating multiple structure tests...")
    
    for struct_type, config in structure_types.items():
        print(f"\n--- {struct_type.title()} Structure ---")
        print(f"Description: {config['description']}")
        
        # Create graph
        G = GraphLayout()
        G.k_spring = 0.08
        G.k_repel = 30.0
        G.k_barrier = 60.0
        G.L0 = 2.0
        G.step = 0.01
        G.damping = 0.95
        G.edge_radius = 0.5
        
        # Add nodes
        for node_id, label, node_type, pos in config["nodes"]:
            style = STYLES.get(node_type, STYLES["statement"])
            width = 2.0 if node_type in ["entry", "exit"] else 2.5
            height = 1.2 if node_type in ["entry", "exit"] else 1.0
            
            G.add_node(node_id, label, **style, width=width, height=height, pos=pos)
        
        # Add edges
        for from_node, to_node in config["edges"]:
            G.add_edge(from_node, to_node)
        
        print(f"Created graph with {len(G.nodes)} nodes and {len(G.edges)} edges")
        
        # Run simulation
        visualizer = LayoutSimulationVisualizer(max_frames_in_memory=20)
        frames_file = f"{struct_type}_structure_frames.json"
        
        visualizer.run_simulation(
            G,
            iterations=80,
            capture_interval=2,
            output_file=frames_file
        )
        
        # Generate HTML
        visualizer.load_frames(frames_file)
        html_file = f"{struct_type}_structure_simulation.html"
        visualizer.generate_html_visualizer(html_file)
        
        print(f"✓ Generated: {html_file}")

if __name__ == "__main__":
    # Run single test
    run_simulation_test()
    
    print("\n" + "="*50 + "\n")
    
    # Run multiple structure tests
    create_multiple_structure_tests()
    
    print("\n✓ All integration tests complete!")
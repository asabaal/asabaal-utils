#!/usr/bin/env python3
"""
Test script for the layout relaxer with stable parameters
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from layout_relaxer import GraphLayout, Node, Edge

def create_test_graph():
    """Create a simple test graph with stable parameters"""
    G = GraphLayout()
    
    # More conservative physics parameters
    G.k_spring = 0.1      # Reduced spring constant
    G.k_repel = 50.0      # Much lower repulsion
    G.k_barrier = 100.0   # Much lower barrier force
    G.L0 = 2.0            # Larger rest length
    G.step = 0.01         # Smaller time step
    G.damping = 0.95      # More damping
    G.edge_radius = 0.5   # Larger edge radius
    
    # Legend-based styles
    STYLES = {
        "Entry":       dict(shape="ellipse", color="#90ee90"),
        "Exit":        dict(shape="ellipse", color="#ff6b6b"),
        "Assignment":  dict(shape="box",     color="#ffd700"),
        "Conditional": dict(shape="diamond", color="#ffa500"),
        "Loop":        dict(shape="diamond", color="#ff9999"),
        "Statement":   dict(shape="box",     color="#97c2fc"),
        "Return":      dict(shape="box",     color="#90ee90"),
        "Try":         dict(shape="box",     color="#dda0dd"),
        "Except":      dict(shape="box",     color="#f0e68c"),
        "Merge":       dict(shape="circle",  color="#d3d3d3"),
    }
    
    # Create a simple test graph
    G.add_node("n0", "entry",    **STYLES["Entry"],      width=1.8, height=1.2, pos=(0.0, 0.0))
    G.add_node("n1", "cond",     **STYLES["Conditional"],width=2.2, height=1.6, pos=(2.0, 2.0))
    G.add_node("n2", "assign A", **STYLES["Assignment"], width=2.8, height=1.2, pos=(-2.0, 4.0))
    G.add_node("n3", "assign B", **STYLES["Assignment"], width=2.0, height=1.2, pos=( 2.0, 4.0))
    G.add_node("n4", "merge",    **STYLES["Merge"],      width=1.2, height=1.2, pos=(0.0, 6.0))
    G.add_node("n5", "return",   **STYLES["Return"],     width=2.2, height=1.2, pos=(0.0, 8.0))
    G.add_node("n6", "exit",     **STYLES["Exit"],       width=1.8, height=1.2, pos=(0.0, 10.0))

    G.add_edge("n0", "n1")
    G.add_edge("n1", "n2")
    G.add_edge("n1", "n3")
    G.add_edge("n2", "n4")
    G.add_edge("n3", "n4")
    G.add_edge("n4", "n5")
    G.add_edge("n5", "n6")
    
    return G

def test_relaxation():
    """Test the relaxation with frame capture"""
    print("Testing layout relaxer with frame capture...")
    
    G = create_test_graph()
    
    # Capture frames for visualization
    frames = []
    capture_interval = 10  # Capture every 10 iterations
    
    print("Initial positions:")
    for name in G.nodes:
        n = G.nodes[name]
        print(f"  {name:>3} ({n.x:.3f}, {n.y:.3f})")
    
    # Run relaxation with frame capture
    iterations = 200
    for it in range(iterations):
        # Linear cooling
        t = it / max(1, iterations - 1)
        step = 0.01 * (1.0 - t) + 0.001 * t
        G.step = step
        
        # Capture frame
        if it % capture_interval == 0:
            frame = {}
            for name, node in G.nodes.items():
                frame[name] = {
                    'x': node.x,
                    'y': node.y,
                    'label': node.label,
                    'shape': node.shape,
                    'color': node.color,
                    'width': node.width,
                    'height': node.height
                }
            frames.append({
                'iteration': it,
                'step': step,
                'nodes': frame
            })
        
        # Run one iteration (we need to modify the relaxer to support single steps)
        from layout_relaxer import _relax_iteration
        _relax_iteration(G)
    
    print(f"\nFinal positions after {iterations} iterations:")
    for name in G.nodes:
        n = G.nodes[name]
        print(f"  {name:>3} ({n.x:.3f}, {n.y:.3f})")
    
    print(f"\nCaptured {len(frames)} frames for visualization")
    return frames

if __name__ == "__main__":
    frames = test_relaxation()
    
    # Save frames to JSON for visualization
    import json
    with open("relaxation_frames.json", "w") as f:
        json.dump(frames, f, indent=2)
    
    print("Frames saved to relaxation_frames.json")
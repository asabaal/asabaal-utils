#!/usr/bin/env python3
"""
3-Node Triangle Repulsion Simulation

This script recreates the exact test scenario from test_3_node_triangle_repulsion
where shape repulsion dominates and triangle expands.

Physics Setup:
- k_spring: 0.1 (weak attraction)
- k_repel: 10.0 (strong repulsion)
- Small triangle with large nodes: (0,0), (1,0), (0.5,0.866) with 2.5x2.5 nodes
- Expected: Triangle expands, nodes push apart
"""

import sys
import json
import math
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from layout_relaxer import GraphLayout


def triangle_area(p1, p2, p3):
    """Calculate triangle area using cross product."""
    return abs((p1[0]*(p2[1]-p3[1]) + p2[0]*(p3[1]-p1[1]) + p3[0]*(p1[1]-p2[1])) / 2)


def main():
    """Run 3-node triangle repulsion simulation."""
    print("=== 3-Node Triangle Repulsion Simulation ===")
    
    # Recreate exact test scenario from test_3_node_triangle_repulsion
    G = GraphLayout()
    G.step = 0.01
    G.damping = 0.9
    G.k_spring = 0.1    # Weak attraction
    G.k_repel = 10.0    # Strong repulsion
    G.k_barrier = 1.0
    G.L0 = 3.0          # Large rest length
    
    # Create small triangle with large nodes (maximize repulsion)
    G.add_node("a", "A", "box", "#ff0000", 2.5, 2.5, pos=(0.0, 0.0))
    G.add_node("b", "B", "box", "#00ff00", 2.5, 2.5, pos=(1.0, 0.0))
    G.add_node("c", "C", "box", "#0000ff", 2.5, 2.5, pos=(0.5, 0.866))  # Equilateral triangle
    
    # Add edges to form triangle
    G.add_edge("a", "b")
    G.add_edge("b", "c")
    G.add_edge("c", "a")
    
    # Store initial positions and area
    initial_pos = {
        "a": (G.nodes["a"].x, G.nodes["a"].y),
        "b": (G.nodes["b"].x, G.nodes["b"].y),
        "c": (G.nodes["c"].x, G.nodes["c"].y)
    }
    
    initial_area = triangle_area(initial_pos["a"], initial_pos["b"], initial_pos["c"])
    
    print(f"Initial positions: A={initial_pos['a']}, B={initial_pos['b']}, C={initial_pos['c']}")
    print(f"Initial triangle area: {initial_area:.3f}")
    
    # Run simulation with frame capture
    print("\nRunning simulation...")
    frames = G.run_simulation_with_capture(iterations=100, capture_interval=2)
    
    print(f"Captured {len(frames)} frames")
    
    # Calculate final positions and area
    final_pos = {
        "a": (G.nodes["a"].x, G.nodes["a"].y),
        "b": (G.nodes["b"].x, G.nodes["b"].y),
        "c": (G.nodes["c"].x, G.nodes["c"].y)
    }
    
    final_area = triangle_area(final_pos["a"], final_pos["b"], final_pos["c"])
    
    print(f"Final positions: A={final_pos['a']}, B={final_pos['b']}, C={final_pos['c']}")
    print(f"Final triangle area: {final_area:.3f}")
    print(f"Area increase: {final_area - initial_area:.3f} ({(final_area - initial_area)/initial_area*100:.1f}%)")
    
    # Save trajectory data
    trajectory_data = {
        "scenario": "3_node_triangle_repulsion",
        "parameters": {
            "k_spring": G.k_spring,
            "k_repel": G.k_repel,
            "k_barrier": G.k_barrier,
            "L0": G.L0,
            "step": G.step,
            "damping": G.damping
        },
        "initial_positions": initial_pos,
        "initial_area": initial_area,
        "final_positions": final_pos,
        "final_area": final_area,
        "frames": frames
    }
    
    # Save to file
    output_file = Path(__file__).parent / "3_node_triangle_repulsion_trajectory.json"
    with open(output_file, 'w') as f:
        json.dump(trajectory_data, f, indent=2)
    
    print(f"Trajectory saved to: {output_file}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
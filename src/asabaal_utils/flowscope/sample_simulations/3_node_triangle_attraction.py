#!/usr/bin/env python3
"""
3-Node Triangle Attraction Simulation

This script recreates the exact test scenario from test_3_node_triangle_attraction
where spring attraction dominates and triangle contracts.

Physics Setup:
- k_spring: 10.0 (strong attraction)
- k_repel: 0.1 (weak repulsion)
- Large triangle: nodes at (0,0), (6,0), (3,5)
- Expected: Triangle contracts, all nodes move toward center
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
    """Run 3-node triangle attraction simulation."""
    print("=== 3-Node Triangle Attraction Simulation ===")
    
    # Recreate exact test scenario from test_3_node_triangle_attraction
    G = GraphLayout()
    G.step = 0.01
    G.damping = 0.9
    G.k_spring = 10.0  # Strong attraction
    G.k_repel = 0.1    # Weak repulsion
    G.k_barrier = 1.0
    G.L0 = 1.0
    
    # Create large triangle (nodes far apart)
    G.add_node("a", "A", "box", "#ff0000", 1.0, 1.0, pos=(0.0, 0.0))
    G.add_node("b", "B", "box", "#00ff00", 1.0, 1.0, pos=(6.0, 0.0))
    G.add_node("c", "C", "box", "#0000ff", 1.0, 1.0, pos=(3.0, 5.0))
    
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
    
    # Calculate center of triangle
    center_x = (initial_pos["a"][0] + initial_pos["b"][0] + initial_pos["c"][0]) / 3
    center_y = (initial_pos["a"][1] + initial_pos["b"][1] + initial_pos["c"][1]) / 3
    
    print(f"Triangle center: ({center_x:.3f}, {center_y:.3f})")
    
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
    print(f"Area reduction: {initial_area - final_area:.3f} ({(initial_area - final_area)/initial_area*100:.1f}%)")
    
    # Save trajectory data
    trajectory_data = {
        "scenario": "3_node_triangle_attraction",
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
    output_file = Path(__file__).parent / "3_node_triangle_attraction_trajectory.json"
    with open(output_file, 'w') as f:
        json.dump(trajectory_data, f, indent=2)
    
    print(f"Trajectory saved to: {output_file}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
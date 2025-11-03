#!/usr/bin/env python3
"""
3-Node Edge Barrier Forces Simulation

This script recreates the exact test scenario from test_3_node_edge_barrier_forces
where edge barrier forces push non-incident node away.

Physics Setup:
- k_spring: 1.0 (moderate attraction)
- k_repel: 1.0 (moderate repulsion)
- k_barrier: 50.0 (strong edge barriers)
- Edge A-B with non-incident node C nearby at (2,0.5)
- Expected: Edge barrier force pushes C upward
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from layout_relaxer import GraphLayout


def main():
    """Run 3-node edge barrier forces simulation."""
    print("=== 3-Node Edge Barrier Forces Simulation ===")
    
    # Recreate exact test scenario from test_3_node_edge_barrier_forces
    G = GraphLayout()
    G.step = 0.01
    G.damping = 0.9
    G.k_spring = 1.0
    G.k_repel = 1.0
    G.k_barrier = 50.0   # Strong edge barriers
    G.L0 = 2.0
    G.edge_radius = 2.0   # Large edge barrier radius
    
    # Create edge A-B and non-incident node C near edge
    G.add_node("a", "A", "box", "#ff0000", 1.0, 1.0, pos=(0.0, 0.0))
    G.add_node("b", "B", "box", "#00ff00", 1.0, 1.0, pos=(4.0, 0.0))
    G.add_node("c", "C", "box", "#0000ff", 1.0, 1.0, pos=(2.0, 0.5))  # Close to edge A-B
    
    # Add only edge A-B (C is non-incident)
    G.add_edge("a", "b")
    
    # Store initial positions
    initial_c_pos = (G.nodes["c"].x, G.nodes["c"].y)
    
    print(f"Initial positions: A=({G.nodes['a'].x:.3f}, {G.nodes['a'].y:.3f}), "
          f"B=({G.nodes['b'].x:.3f}, {G.nodes['b'].y:.3f}), C=({G.nodes['c'].x:.3f}, {G.nodes['c'].y:.3f})")
    
    # Calculate expected edge barrier force on C
    from layout_relaxer import _edge_barrier_force_for_rect
    
    c_node = G.nodes["c"]
    a_node = G.nodes["a"]
    b_node = G.nodes["b"]
    
    barrier_fx, barrier_fy = _edge_barrier_force_for_rect(
        c_node, a_node.x, a_node.y, b_node.x, b_node.y, 
        G.edge_radius, G.k_barrier
    )
    
    print(f"Edge barrier force on C: ({barrier_fx:.3f}, {barrier_fy:.3f})")
    print(f"Barrier force magnitude: {math.sqrt(barrier_fx**2 + barrier_fy**2):.3f}")
    
    # Edge barrier should push C away from edge
    if barrier_fy > 0:
        expected_direction = "upward (away from edge)"
    elif barrier_fy < 0:
        expected_direction = "downward (toward edge)"
    else:
        expected_direction = "no vertical force"
        
    print(f"Expected C movement: {expected_direction}")
    
    # Run simulation with frame capture
    print("\nRunning simulation...")
    frames = G.run_simulation_with_capture(iterations=100, capture_interval=2)
    
    print(f"Captured {len(frames)} frames")
    
    # Get final position of C
    final_c_pos = (G.nodes["c"].x, G.nodes["c"].y)
    
    print(f"Final C position: ({final_c_pos[0]:.3f}, {final_c_pos[1]:.3f})")
    
    # Calculate movement
    x_movement = final_c_pos[0] - initial_c_pos[0]
    y_movement = final_c_pos[1] - initial_c_pos[1]
    total_movement = math.sqrt(x_movement**2 + y_movement**2)
    
    print(f"C movement: x={x_movement:.6f}, y={y_movement:.6f}, total={total_movement:.6f}")
    
    # Validate expected behavior
    if y_movement > 0:
        actual_direction = "upward (away from edge)"
    elif y_movement < 0:
        actual_direction = "downward (toward edge)"
    else:
        actual_direction = "no vertical movement"
        
    print(f"Actual C movement: {actual_direction}")
    
    # Save trajectory data
    trajectory_data = {
        "scenario": "3_node_edge_barrier_forces",
        "parameters": {
            "k_spring": G.k_spring,
            "k_repel": G.k_repel,
            "k_barrier": G.k_barrier,
            "L0": G.L0,
            "step": G.step,
            "damping": G.damping,
            "edge_radius": G.edge_radius
        },
        "initial_positions": {
            "a": [0.0, 0.0],
            "b": [4.0, 0.0],
            "c": [2.0, 0.5]
        },
        "final_positions": {
            "a": [G.nodes["a"].x, G.nodes["a"].y],
            "b": [G.nodes["b"].x, G.nodes["b"].y],
            "c": [final_c_pos[0], final_c_pos[1]]
        },
        "edge_barrier_force": {
            "c": [barrier_fx, barrier_fy]
        },
        "movements": {
            "c": {
                "x": x_movement,
                "y": y_movement,
                "total": total_movement
            }
        },
        "frames": frames
    }
    
    # Save to file
    output_file = Path(__file__).parent / "3_node_edge_barrier_forces_trajectory.json"
    with open(output_file, 'w') as f:
        json.dump(trajectory_data, f, indent=2)
    
    print(f"Trajectory saved to: {output_file}")
    
    return True


if __name__ == "__main__":
    import math
    success = main()
    sys.exit(0 if success else 1)
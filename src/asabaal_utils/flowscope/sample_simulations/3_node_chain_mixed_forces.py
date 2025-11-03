#!/usr/bin/env python3
"""
3-Node Chain Mixed Forces Simulation

This script recreates the exact test scenario from test_3_node_chain_mixed_forces
where middle node experiences competing forces.

Physics Setup:
- k_spring: 2.0 (moderate attraction)
- k_repel: 2.0 (moderate repulsion)
- Linear chain: A--B--C at positions (0,0), (3,0), (6,0)
- Expected: A moves right, C moves left, B minimal movement (balanced forces)
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from layout_relaxer import GraphLayout


def main():
    """Run 3-node chain mixed forces simulation."""
    print("=== 3-Node Chain Mixed Forces Simulation ===")
    
    # Recreate exact test scenario from test_3_node_chain_mixed_forces
    G = GraphLayout()
    G.step = 0.01
    G.damping = 0.9
    G.k_spring = 2.0    # Moderate attraction
    G.k_repel = 2.0     # Moderate repulsion
    G.k_barrier = 1.0
    G.L0 = 2.0
    
    # Create linear chain: A -- B -- C
    G.add_node("a", "A", "box", "#ff0000", 1.5, 1.5, pos=(0.0, 0.0))
    G.add_node("b", "B", "box", "#00ff00", 1.5, 1.5, pos=(3.0, 0.0))
    G.add_node("c", "C", "box", "#0000ff", 1.5, 1.5, pos=(6.0, 0.0))
    
    # Add edges to form chain
    G.add_edge("a", "b")
    G.add_edge("b", "c")
    
    # Store initial positions
    initial_pos = {
        "a": (G.nodes["a"].x, G.nodes["a"].y),
        "b": (G.nodes["b"].x, G.nodes["b"].y),
        "c": (G.nodes["c"].x, G.nodes["c"].y)
    }
    
    print(f"Initial chain: A={initial_pos['a']}, B={initial_pos['b']}, C={initial_pos['c']}")
    
    # Calculate chain center
    chain_center_x = (initial_pos["a"][0] + initial_pos["c"][0]) / 2
    print(f"Chain center: ({chain_center_x:.3f}, 0.0)")
    
    # Run simulation with frame capture
    print("\nRunning simulation...")
    frames = G.run_simulation_with_capture(iterations=100, capture_interval=2)
    
    print(f"Captured {len(frames)} frames")
    
    # Calculate final positions
    final_pos = {
        "a": (G.nodes["a"].x, G.nodes["a"].y),
        "b": (G.nodes["b"].x, G.nodes["b"].y),
        "c": (G.nodes["c"].x, G.nodes["c"].y)
    }
    
    print(f"Final chain:   A={final_pos['a']}, B={final_pos['b']}, C={final_pos['c']}")
    
    # Analyze movement
    a_movement = final_pos["a"][0] - initial_pos["a"][0]
    b_movement = final_pos["b"][0] - initial_pos["b"][0]
    c_movement = final_pos["c"][0] - initial_pos["c"][0]
    
    print(f"Movement: A={a_movement:.6f}, B={b_movement:.6f}, C={c_movement:.6f}")
    
    # Validate expected behavior
    if a_movement > 0:
        a_direction = "right (toward B)"
    elif a_movement < 0:
        a_direction = "left (away from B)"
    else:
        a_direction = "none"
        
    if c_movement > 0:
        c_direction = "right (away from B)"
    elif c_movement < 0:
        c_direction = "left (toward B)"
    else:
        c_direction = "none"
        
    print(f"A movement: {a_direction}")
    print(f"C movement: {c_direction}")
    print(f"B movement magnitude: {abs(b_movement):.6f} (should be minimal)")
    
    # Save trajectory data
    trajectory_data = {
        "scenario": "3_node_chain_mixed_forces",
        "parameters": {
            "k_spring": G.k_spring,
            "k_repel": G.k_repel,
            "k_barrier": G.k_barrier,
            "L0": G.L0,
            "step": G.step,
            "damping": G.damping
        },
        "initial_positions": initial_pos,
        "final_positions": final_pos,
        "movements": {
            "a": a_movement,
            "b": b_movement,
            "c": c_movement
        },
        "frames": frames
    }
    
    # Save to file
    output_file = Path(__file__).parent / "3_node_chain_mixed_forces_trajectory.json"
    with open(output_file, 'w') as f:
        json.dump(trajectory_data, f, indent=2)
    
    print(f"Trajectory saved to: {output_file}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
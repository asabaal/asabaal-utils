#!/usr/bin/env python3
"""
2-Node Equilibrium Simulation

This script recreates the exact test scenario from test_2_node_equilibrium
where nodes are at optimal distance with near-zero net forces.

Physics Setup:
- k_spring: 1.0 (moderate attraction)
- k_repel: 1.0 (moderate repulsion)
- Nodes at optimal distance: (0,0) and (2,0)
- Expected: Minimal movement, near-equilibrium
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from layout_relaxer import GraphLayout


def main():
    """Run 2-node equilibrium simulation."""
    print("=== 2-Node Equilibrium Simulation ===")
    
    # Recreate exact test scenario from test_2_node_equilibrium
    G = GraphLayout()
    G.step = 0.01
    G.damping = 0.9
    G.k_spring = 1.0
    G.k_repel = 1.0
    G.k_barrier = 1.0
    G.L0 = 2.0
    
    # Place nodes at optimal distance for equilibrium
    G.add_node("a", "A", "box", "#ff0000", 1.0, 1.0, pos=(0.0, 0.0))
    G.add_node("b", "B", "box", "#00ff00", 1.0, 1.0, pos=(2.0, 0.0))
    G.add_edge("a", "b")
    
    print(f"Initial positions: A=({G.nodes['a'].x:.3f}, {G.nodes['a'].y:.3f}), B=({G.nodes['b'].x:.3f}, {G.nodes['b'].y:.3f})")
    
    # Calculate initial forces
    from layout_relaxer import _dist_dxdy, _effective_L0, _shape_repulsion
    
    a_node = G.nodes["a"]
    b_node = G.nodes["b"]
    d, dx, dy = _dist_dxdy(a_node.x, a_node.y, b_node.x, b_node.y)
    effective_L0 = _effective_L0(G, a_node, b_node)
    delta = d - effective_L0
    
    spring_fx_a = (dx / d) * (G.k_spring * delta)
    spring_fy_a = (dy / d) * (G.k_spring * delta)
    repel_fx_a, repel_fy_a, repel_fx_b, repel_fy_b = _shape_repulsion(a_node, b_node, G.k_repel)
    total_fx_a = spring_fx_a + repel_fx_a
    
    print(f"Initial distance: {d:.3f}, L0_effective: {effective_L0:.3f}")
    print(f"Spring force: {spring_fx_a:.3f}, Repulsion: {repel_fx_a:.3f}")
    print(f"Total force on A: {total_fx_a:.3f}")
    print(f"Net force magnitude: {abs(total_fx_a):.3f} (should be small at equilibrium)")
    
    # Run simulation with frame capture
    print("\nRunning simulation...")
    frames = G.run_simulation_with_capture(iterations=100, capture_interval=2)
    
    print(f"Captured {len(frames)} frames")
    
    # Save trajectory data
    trajectory_data = {
        "scenario": "2_node_equilibrium",
        "parameters": {
            "k_spring": G.k_spring,
            "k_repel": G.k_repel,
            "k_barrier": G.k_barrier,
            "L0": G.L0,
            "step": G.step,
            "damping": G.damping
        },
        "initial_positions": {
            "a": [0.0, 0.0],
            "b": [2.0, 0.0]
        },
        "frames": frames
    }
    
    # Save to file
    output_file = Path(__file__).parent / "2_node_equilibrium_trajectory.json"
    with open(output_file, 'w') as f:
        json.dump(trajectory_data, f, indent=2)
    
    print(f"Trajectory saved to: {output_file}")
    
    # Print final state
    print(f"\nFinal positions: A=({G.nodes['a'].x:.3f}, {G.nodes['a'].y:.3f}), B=({G.nodes['b'].x:.3f}, {G.nodes['b'].y:.3f})")
    
    # Calculate movement
    movement_a = math.sqrt((G.nodes['a'].x - 0.0)**2 + (G.nodes['a'].y - 0.0)**2)
    movement_b = math.sqrt((G.nodes['b'].x - 2.0)**2 + (G.nodes['b'].y - 0.0)**2)
    print(f"Movement: A={movement_a:.6f}, B={movement_b:.6f} (should be minimal)")
    
    return True


if __name__ == "__main__":
    import math
    success = main()
    sys.exit(0 if success else 1)
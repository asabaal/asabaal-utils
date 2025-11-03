#!/usr/bin/env python3
"""
Two Node Simulation using Native GraphLayout Methods

This script demonstrates basic two-node physics simulation
using the native GraphLayout testing methods from layout_relaxer.py.
No custom utilities or parallel infrastructure are used.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from layout_relaxer import GraphLayout


def main():
    """Run two-node simulation demonstration."""
    print("=== Two Node Simulation ===")
    
    # Create test graph using native GraphLayout method
    layout = GraphLayout()
    layout.create_test_graph("two_node")
    
    # Print initial state
    print("\nInitial State:")
    layout.print_state()
    
    # Validate physics
    print("\nPhysics Validation:")
    layout.validate_physics()
    
    # Run simulation with frame capture
    print("\nRunning simulation...")
    frames = layout.run_simulation_with_capture(iterations=50, capture_interval=5)
    
    print(f"Captured {len(frames)} frames")
    
    # Print final state
    print("\nFinal State:")
    layout.print_state()
    
    # Calculate final energy
    energy = layout.calculate_energy()
    print(f"\nFinal Energy: {energy}")
    
    # For now, just report the final positions
    print(f"\nFinal node positions:")
    for node_id, node in layout.nodes.items():
        print(f"  {node_id}: ({node.x:.2f}, {node.y:.2f})")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Physics Investigation using Native GraphLayout Methods

This script demonstrates parameter sensitivity analysis and physics
investigation using the native GraphLayout testing methods from layout_relaxer.py.
No custom utilities or parallel infrastructure are used.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from layout_relaxer import GraphLayout


def main():
    """Run physics investigation demonstration."""
    print("=== Physics Investigation ===")
    
    # Test parameter sensitivity on spring constant
    print(f"\n--- Testing Spring Constant Sensitivity ---")
    layout = GraphLayout()
    
    spring_values = [0.1, 0.5, 1.0, 2.0, 5.0]
    results = layout.test_parameter_sensitivity("k_spring", spring_values)
    
    # Print results summary
    print("Spring constant results:")
    for value, result in results.items():
        print(f"  k_spring={value}: {result}")
    
    # Test parameter sensitivity on repulsion constant
    print(f"\n--- Testing Repulsion Constant Sensitivity ---")
    layout = GraphLayout()
    
    repulsion_values = [50.0, 100.0, 200.0, 500.0, 1000.0]
    results = layout.test_parameter_sensitivity("k_repel", repulsion_values)
    
    # Print results summary
    print("Repulsion constant results:")
    for value, result in results.items():
        print(f"  k_repel={value}: {result}")
    
    # Detailed physics validation on a three_node graph
    print(f"\n--- Detailed Physics Validation ---")
    layout = GraphLayout()
    layout.create_test_graph("three_node")
    
    print("Initial physics validation:")
    layout.validate_physics()
    
    print("\nRunning simulation...")
    layout.run_simulation_with_capture(iterations=50)
    
    print("\nFinal physics validation:")
    layout.validate_physics()
    
    # Energy breakdown
    energy = layout.calculate_energy()
    print(f"\nFinal energy breakdown: {energy}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
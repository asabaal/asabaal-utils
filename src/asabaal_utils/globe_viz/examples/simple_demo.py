#!/usr/bin/env python3
"""
Simple demonstration of the 3D Globe Visualization system.

This script shows how to load data, set up the visualization, and interact
with the globe.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from asabaal_utils.globe_viz import GlobeVisualizationManager


def main():
    """Run a simple demonstration of the 3D Globe Visualization system."""
    # Create the visualization manager
    viz_manager = GlobeVisualizationManager(
        width=1200,
        height=800,
        # You can provide a custom globe image here if desired
        # globe_image_path="path/to/globe_image.png"
    )
    
    # Get the sample data directory
    sample_data_dir = Path(__file__).parent.parent / "sample_data"
    
    # Load entity and metric definitions
    viz_manager.load_data(
        entities_file=sample_data_dir / "entities.json",
        metrics_file=sample_data_dir / "metrics.json"
    )
    
    # Set the initial metric to visualize
    viz_manager.set_current_metric("life_expectancy")
    
    print("3D Globe Visualization Demo")
    print("---------------------------")
    print("Controls:")
    print("  - Click and drag to rotate the globe")
    print("  - +/- keys to zoom in/out")
    print("  - 'h' key to toggle UI visibility")
    print("  - 's' key to take a snapshot")
    print("  - 'r' key to reset the view")
    print("  - 'v' key to create a rotation video")
    print("  - Space to pause/resume")
    print("  - ESC to exit")
    print("---------------------------")
    
    # Run the visualization
    viz_manager.run(interactive=True)


if __name__ == "__main__":
    main()
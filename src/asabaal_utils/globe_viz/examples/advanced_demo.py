#!/usr/bin/env python3
"""
Advanced demonstration of the 3D Globe Visualization system.

This script shows more advanced features of the visualization system,
including derived metrics, custom rendering, and data export.
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from asabaal_utils.globe_viz import (
    GlobeVisualizationManager, Entity, Metric, MetricData, MetricType
)
from asabaal_utils.globe_viz.renderers import ColorMapType, MarkerStyle


def create_synthetic_metric(viz_manager):
    """Create a synthetic metric combining GDP and life expectancy."""
    # Register a custom transformer function
    viz_manager.data_manager.register_transformer(
        "weighted_score", 
        lambda gdp, life: (gdp / 100000) * 0.5 + (life / 90) * 0.5
    )
    
    # Compute derived metric
    viz_manager.derive_metric(
        "development_score",
        ["gdp_per_capita", "life_expectancy"],
        "weighted_score"
    )
    
    # Create a proper metric definition
    development_score = Metric(
        id="development_score",
        name="Development Score",
        description="Combined score of GDP per capita and life expectancy",
        metric_type=MetricType.SCALAR,
        range=(0, 1),
        color_scale=["#d73027", "#fc8d59", "#fee090", "#e0f3f8", "#91bfdb", "#4575b4"]
    )
    
    # Add to metrics dictionary
    viz_manager.data_manager.metrics["development_score"] = development_score


def customize_globe_renderer(viz_manager):
    """Customize the globe renderer appearance."""
    # Get the renderer
    renderer = viz_manager.renderer
    
    # Customize data layer
    data_layer = renderer.layers.get("data")
    if data_layer:
        data_layer.style.update({
            "marker_style": MarkerStyle.DIAMOND.value,
            "marker_size": 10,
            "color_map_type": ColorMapType.SEQUENTIAL.value
        })
    
    # Customize outlines layer
    outlines_layer = renderer.layers.get("outlines")
    if outlines_layer:
        outlines_layer.style.update({
            "line_color": (200, 200, 255),
            "line_thickness": 1,
            "alpha": 180
        })
    
    # Customize highlight layer
    highlight_layer = renderer.layers.get("highlights")
    if highlight_layer:
        highlight_layer.style.update({
            "marker_style": MarkerStyle.STAR.value,
            "marker_size": 15,
            "marker_color": (255, 215, 0),  # Gold
            "line_thickness": 2
        })


def main():
    """Run an advanced demonstration of the 3D Globe Visualization system."""
    # Create the visualization manager
    viz_manager = GlobeVisualizationManager(
        width=1200,
        height=800
    )
    
    # Get the sample data directory
    sample_data_dir = Path(__file__).parent.parent / "sample_data"
    
    # Load entity and metric definitions
    viz_manager.load_data(
        entities_file=sample_data_dir / "entities.json",
        metrics_file=sample_data_dir / "metrics.json"
    )
    
    # Create a synthetic derived metric
    create_synthetic_metric(viz_manager)
    
    # Customize renderer appearance
    customize_globe_renderer(viz_manager)
    
    # Select and highlight some entities
    viz_manager.select_entity("USA")
    viz_manager.select_entity("CHN")
    viz_manager.select_entity("DEU")
    
    # Set the initial metric to visualize
    viz_manager.set_current_metric("development_score")
    
    # Initial rotation
    viz_manager.set_rotation(20.0, 15.0)
    
    print("Advanced 3D Globe Visualization Demo")
    print("------------------------------------")
    print("This demo shows:")
    print("  - Custom derived metrics")
    print("  - Customized visualization appearance")
    print("  - Pre-selected entities")
    print("  - Initial rotation and view settings")
    print("------------------------------------")
    print("Controls:")
    print("  - Click and drag to rotate the globe")
    print("  - +/- keys to zoom in/out")
    print("  - 'h' key to toggle UI visibility")
    print("  - 's' key to take a snapshot")
    print("  - 'r' key to reset the view")
    print("  - 'v' key to create a rotation video")
    print("  - Space to pause/resume")
    print("  - ESC to exit")
    print("------------------------------------")
    
    # Run the visualization
    viz_manager.run(interactive=True)
    
    # Export the data at the end
    output_path = viz_manager.export_data("globe_data_export")
    print(f"Data exported to: {output_path}")


if __name__ == "__main__":
    main()
# 3D Globe Visualization System

A flexible, interactive 3D globe visualization system capable of displaying various global metrics. The system allows users to easily switch between different datasets, customize visualization parameters, and explore geographic patterns through an intuitive interface.

## Features

- **Interactive 3D Globe**: Rotate, zoom, and pan to explore global data
- **Multiple Metrics Support**: Easily switch between different global datasets
- **Customizable Visualizations**: Configure colors, markers, and display options
- **Data Management**: Load data from various sources and formats
- **UI Controls**: Interactive interface for controlling the visualization
- **Snapshot & Video Export**: Capture images and create videos of the visualization
- **Entity Selection**: Select and highlight countries or regions
- **Derived Metrics**: Create new metrics from combinations of existing ones

## Installation

```bash
# Clone the repository
git clone https://github.com/asabaal/asabaal-utils.git

# Navigate to the directory
cd asabaal-utils

# Install requirements
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Getting Started

The system includes simple demo examples to help you get started:

```bash
# Run the simple demo
python -m asabaal_utils.globe_viz.examples.simple_demo

# Run the advanced demo with more features
python -m asabaal_utils.globe_viz.examples.advanced_demo
```

## Usage

### Basic Usage

```python
from asabaal_utils.globe_viz import GlobeVisualizationManager

# Create the visualization manager
viz_manager = GlobeVisualizationManager(width=1200, height=800)

# Load data
viz_manager.load_data(
    entities_file="path/to/entities.json",
    metrics_file="path/to/metrics.json"
)

# Set the initial metric to visualize
viz_manager.set_current_metric("gdp_per_capita")

# Run the visualization
viz_manager.run(interactive=True)
```

### Creating Custom Metrics

```python
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
```

### Customizing the Visualization

```python
# Customize data markers
viz_manager.renderer.layers["data"].style.update({
    "marker_style": "diamond",
    "marker_size": 10,
    "color_map_type": "sequential"
})

# Select entities
viz_manager.select_entity("USA")
viz_manager.select_entity("CHN")

# Set rotation and zoom
viz_manager.set_rotation(20.0, 15.0)
viz_manager.set_zoom(1.2)
```

### Exporting

```python
# Take a snapshot
viz_manager.take_snapshot()

# Create a rotation video
viz_manager.save_video("globe_rotation", rotation_speed=1.0, duration=10.0)

# Export data
viz_manager.export_data("globe_data_export")
```

## Data Format

The system uses JSON files for entity and metric definitions. 

### Metrics JSON

```json
{
  "metrics": [
    {
      "id": "gdp_per_capita",
      "name": "GDP per Capita",
      "description": "Gross Domestic Product (GDP) per capita in USD",
      "unit": "USD",
      "source": "World Bank (2022)",
      "metric_type": "scalar",
      "range": {"min": 0, "max": 120000},
      "colorScale": ["#313695", "#4575b4", "#74add1", "#abd9e9", 
                    "#fee090", "#fdae61", "#f46d43", "#d73027"]
    },
    ...
  ]
}
```

### Entities JSON

```json
{
  "entities": [
    {
      "id": "USA",
      "name": "United States",
      "type": "country",
      "location": {
        "lat": 37.0902,
        "lon": -95.7129
      },
      "metrics": {
        "gdp_per_capita": {
          "value": 69288
        },
        "life_expectancy": {
          "value": 78.79
        }
      }
    },
    ...
  ]
}
```

## Controls

- **Mouse Drag**: Rotate the globe
- **+/- Keys**: Zoom in/out
- **h Key**: Toggle UI visibility
- **s Key**: Take a snapshot
- **r Key**: Reset view
- **v Key**: Create rotation video
- **Space**: Pause/resume
- **ESC**: Exit

## Requirements

- Python 3.8+
- OpenCV
- NumPy
- Additional dependencies in requirements.txt

## License

MIT License. See the LICENSE file for details.
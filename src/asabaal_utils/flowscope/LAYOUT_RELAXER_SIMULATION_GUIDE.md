# Layout Relaxer Simulation Guide

This guide covers the new layout relaxer and step-by-step simulation visualizer for FlowScope function flows.

## Overview

The layout relaxer provides physics-based layout optimization for function flow graphs, while the simulation visualizer offers interactive controls to step through the relaxation process frame by frame.

## Features

### Layout Relaxer
- **Shape-aware collision detection**: Different node shapes (box, diamond, ellipse, circle) with accurate overlap detection
- **Edge barrier fields**: Prevents nodes from crossing edges using infinite-well potentials
- **Rigid-body physics**: Realistic spring forces and repulsion between nodes
- **Configurable parameters**: Tunable physics constants for different graph types

### Simulation Visualizer
- **Step-by-step navigation**: Move forward/backward through simulation frames
- **Auto-play with FPS control**: Adjustable playback speed from 0.5 to 10 FPS
- **Memory optimization**: Configurable frame buffer to handle large simulations
- **Interactive controls**: Play/pause, reset, speed control, progress bar
- **Real-time information**: Display current iteration, step size, node count

## Quick Start

### Basic Usage

```python
from layout_relaxer import GraphLayout
from layout_simulation_visualizer import LayoutSimulationVisualizer

# Create a graph
G = GraphLayout()
G.add_node("n0", "entry", shape="ellipse", color="#90ee90", width=1.8, height=1.2)
G.add_node("n1", "condition", shape="diamond", color="#ffa500", width=2.2, height=1.6)
G.add_edge("n0", "n1")

# Configure physics parameters
G.k_spring = 0.1      # Spring attraction
G.k_repel = 50.0      # Node repulsion
G.k_barrier = 100.0   # Edge barrier strength
G.L0 = 2.0            # Rest length
G.step = 0.01         # Time step
G.damping = 0.95      # Velocity damping

# Run simulation
visualizer = LayoutSimulationVisualizer(max_frames_in_memory=100)
visualizer.run_simulation(G, iterations=200, capture_interval=5)
visualizer.generate_html_visualizer("simulation.html")
```

### Command Line Usage

```bash
# Run simulation with default parameters
python layout_simulation_visualizer.py --iterations 300 --capture-interval 5

# Load existing frames
python layout_simulation_visualizer.py --load-frames simulation_frames.json

# Adjust memory usage
python layout_simulation_visualizer.py --max-memory-frames 50
```

## Physics Parameters

### Core Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `k_spring` | 0.25 | Attraction force between connected nodes |
| `k_repel` | 220.0 | Repulsion force between overlapping nodes |
| `k_barrier` | 9000.0 | Edge barrier field strength |
| `L0` | 0.5 | Spring rest length |
| `step` | 0.05 | Integration time step |
| `damping` | 0.90 | Velocity damping factor |
| `edge_radius` | 0.30 | Edge corridor thickness |

### Recommended Settings

#### Small Graphs (< 10 nodes)
```python
G.k_spring = 0.1
G.k_repel = 30.0
G.k_barrier = 60.0
G.L0 = 2.0
G.step = 0.01
G.damping = 0.95
```

#### Medium Graphs (10-25 nodes)
```python
G.k_spring = 0.08
G.k_repel = 40.0
G.k_barrier = 80.0
G.L0 = 2.5
G.step = 0.008
G.damping = 0.96
```

#### Large Graphs (> 25 nodes)
```python
G.k_spring = 0.05
G.k_repel = 50.0
G.k_barrier = 100.0
G.L0 = 3.0
G.step = 0.005
G.damping = 0.97
```

## Node Types and Styling

### Supported Shapes

| Shape | Usage | Color Example |
|-------|-------|--------------|
| `ellipse` | Entry/Exit points | `#90ee90` (entry), `#ff6b6b` (exit) |
| `box` | Statements, assignments | `#ffd700` (assignment), `#97c2fc` (statement) |
| `diamond` | Conditionals, loops | `#ffa500` (conditional), `#ff9999` (loop) |
| `circle` | Merge points | `#d3d3d3` |

### Node Size Guidelines

```python
# Entry/Exit nodes
width, height = 1.8, 1.2

# Assignment/Statement nodes
width = max(1.5, min(3.0, len(label) * 0.15 + 1.5))
height = 1.0

# Conditional/Loop nodes
width, height = 2.2, 1.6

# Merge nodes
width, height = 1.2, 1.2
```

## Simulation Controls

### HTML Visualizer Controls

1. **Play/Pause Button**: Start or stop automatic playback
2. **Step Forward/Backward**: Navigate one frame at a time
3. **Reset Button**: Return to the first frame
4. **FPS Slider**: Adjust playback speed (0.5 - 10 FPS)
5. **Speed Input**: Skip multiple frames per step (1-50)
6. **Progress Bar**: Visual indication of current position

### Keyboard Shortcuts

The HTML visualizer supports keyboard shortcuts for quick navigation:

- **Space**: Play/Pause
- **→**: Step Forward
- **←**: Step Backward
- **R**: Reset
- **↑/↓**: Adjust FPS

## Memory Optimization

### Frame Buffer Management

The visualizer uses a circular buffer to limit memory usage:

```python
# Keep only 50 frames in memory at once
visualizer = LayoutSimulationVisualizer(max_frames_in_memory=50)

# For very large simulations, use disk storage
visualizer.run_simulation(
    G, 
    iterations=1000, 
    capture_interval=10,
    output_file="large_simulation_frames.json"
)
```

### Performance Tips

1. **Reduce capture interval** for long simulations
2. **Lower FPS** for smooth playback on slower machines
3. **Use disk storage** for simulations with >500 frames
4. **Adjust physics parameters** to reduce required iterations

## Integration with Structure Examples

### Converting Function Flow Data

```python
def convert_function_flow_to_layout_graph(function_flow_data):
    G = GraphLayout()
    
    # Map node types to styles
    style_map = {
        "entry": {"shape": "ellipse", "color": "#90ee90"},
        "exit": {"shape": "ellipse", "color": "#ff6b6b"},
        "assignment": {"shape": "box", "color": "#ffd700"},
        "conditional": {"shape": "diamond", "color": "#ffa500"},
        # ... more mappings
    }
    
    # Add nodes
    for node_data in function_flow_data["nodes"]:
        node_type = node_data["type"]
        style = style_map[node_type]
        G.add_node(
            node_data["id"],
            node_data["label"],
            **style,
            width=calculate_width(node_data),
            height=calculate_height(node_type),
            pos=(node_data.get("x", 0) / 50.0, node_data.get("y", 0) / 50.0)
        )
    
    # Add edges
    for edge_data in function_flow_data["edges"]:
        G.add_edge(edge_data["from"], edge_data["to"])
    
    return G
```

### Batch Processing

```python
# Generate simulations for all structure examples
python examples/generate_structure_visualizations_with_simulation.py

# This creates:
# - Static visualizations: *_flow.html
# - Layout simulations: *_layout_simulation.html
# - Summary: enhanced_visualization_summary.md
# - Index: simulations/index.html
```

## Troubleshooting

### Common Issues

#### Unstable Layouts
**Problem**: Nodes fly off to infinity
**Solution**: 
- Reduce `k_spring` and `k_repel`
- Increase `damping`
- Use smaller `step` size
- Increase `L0` (rest length)

#### Slow Convergence
**Problem**: Layout takes too long to stabilize
**Solution**:
- Increase `k_spring`
- Decrease `damping` slightly
- Use larger `step` size
- Check for conflicting constraints

#### Memory Issues
**Problem**: Out of memory for large simulations
**Solution**:
- Reduce `max_frames_in_memory`
- Increase `capture_interval`
- Use disk storage with `output_file`
- Lower total iterations

#### Edge Crossings
**Problem**: Edges still cross after relaxation
**Solution**:
- Increase `k_barrier`
- Increase `edge_radius`
- Add more iterations
- Check initial node placement

### Debug Mode

Enable debug output to monitor simulation progress:

```python
# Add debug prints to layout_relaxer.py
def _relax_iteration(G):
    forces = {name: [0.0, 0.0] for name in G.nodes}
    
    # ... force calculations ...
    
    # Debug output
    if hasattr(G, 'debug') and G.debug:
        max_force = max((f[0]**2 + f[1]**2)**0.5 for f in forces.values())
        print(f"Iteration {getattr(G, 'iteration', 0)}: Max force = {max_force:.4f}")
    
    # ... integration ...
```

## Examples

### Simple Binary Branch

```python
# Create binary branching structure
G = GraphLayout()
G.add_node("entry", "entry", shape="ellipse", color="#90ee90", width=1.8, height=1.2)
G.add_node("cond", "x > 5", shape="diamond", color="#ffa500", width=2.2, height=1.6)
G.add_node("true_branch", "x * 2", shape="box", color="#ffd700", width=2.0, height=1.0)
G.add_node("false_branch", "x + 10", shape="box", color="#ffd700", width=2.0, height=1.0)
G.add_node("merge", "merge", shape="circle", color="#d3d3d3", width=1.2, height=1.2)
G.add_node("exit", "exit", shape="ellipse", color="#ff6b6b", width=1.8, height=1.2)

G.add_edge("entry", "cond")
G.add_edge("cond", "true_branch")
G.add_edge("cond", "false_branch")
G.add_edge("true_branch", "merge")
G.add_edge("false_branch", "merge")
G.add_edge("merge", "exit")
```

### Loop Structure

```python
# Create loop structure
G = GraphLayout()
G.add_node("entry", "entry", shape="ellipse", color="#90ee90", width=1.8, height=1.2)
G.add_node("init", "i = 0", shape="box", color="#ffd700", width=2.0, height=1.0)
G.add_node("loop", "i < 10", shape="diamond", color="#ff9999", width=2.2, height=1.6)
G.add_node("body", "process(i)", shape="box", color="#97c2fc", width=2.5, height=1.0)
G.add_node("increment", "i += 1", shape="box", color="#ffd700", width=2.0, height=1.0)
G.add_node("exit", "exit", shape="ellipse", color="#ff6b6b", width=1.8, height=1.2)

G.add_edge("entry", "init")
G.add_edge("init", "loop")
G.add_edge("loop", "body")
G.add_edge("body", "increment")
G.add_edge("increment", "loop")  # Loop back edge
G.add_edge("loop", "exit")      # Loop exit edge
```

## File Structure

```
flowscope/
├── layout_relaxer.py                    # Core physics engine
├── layout_simulation_visualizer.py       # HTML visualizer generator
├── examples/
│   ├── test_layout_integration.py        # Integration tests
│   ├── generate_structure_visualizations_with_simulation.py
│   └── structure_visualizations/
│       ├── simulations/                  # Generated simulations
│       │   ├── index.html              # Simulation index
│       │   └── *_layout_simulation.html
│       └── enhanced_visualization_summary.md
└── LAYOUT_RELAXER_SIMULATION_GUIDE.md   # This guide
```

## Contributing

When contributing to the layout relaxer:

1. **Test with different graph sizes** - Ensure stability across scales
2. **Validate physics parameters** - Document parameter ranges
3. **Check memory usage** - Profile with large simulations
4. **Update documentation** - Include new features and examples
5. **Add integration tests** - Cover new functionality

## License

This layout relaxer and simulation visualizer are part of the FlowScope project and follow the same license terms.
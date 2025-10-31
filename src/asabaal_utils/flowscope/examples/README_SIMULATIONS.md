# FlowScope Layout Relaxer Simulations

This directory contains interactive layout relaxation simulations for various control flow structures.

## Quick Start

### View Simulations
```bash
# Open the main index page
open structure_visualizations/simulations/index.html
```

### Generate New Simulations
```bash
# Generate all structure simulations
python generate_structure_simulations_standalone.py

# Test individual components
python test_layout_integration.py
python test_all_simulations.py
```

## Available Simulations

### Linear Structure
- **File**: `linear_5_lines_layout_simulation.html`
- **Description**: Simple linear control flow with sequential execution
- **Nodes**: 5 (entry → statement → statement → return → exit)
- **Features**: Straight-line execution path

### Binary Branching
- **File**: `binary_6_lines_layout_simulation.html`
- **Description**: Conditional branching with true/false paths
- **Nodes**: 7 (entry → conditional → two branches → merge → return → exit)
- **Features**: Diamond-shaped decision node with parallel paths

### Loop Structure
- **File**: `loop_8_lines_layout_simulation.html`
- **Description**: Iterative loop with back edge
- **Nodes**: 7 (entry → init → loop → body → increment → return → exit)
- **Features**: Loop back edge showing iteration

### Nested Structure
- **File**: `nested_12_lines_layout_simulation.html`
- **Description**: Nested conditional statements
- **Nodes**: 9 (entry → outer conditional → inner conditional → multiple branches → merge → return → exit)
- **Features**: Multi-level decision making

## Simulation Controls

### Interactive Controls
- **Play/Pause**: Start or stop automatic playback
- **Step Forward**: Move to next simulation frame
- **Step Backward**: Move to previous frame
- **Reset**: Return to initial state
- **FPS Slider**: Adjust playback speed (0.5 - 10 FPS)
- **Speed Control**: Skip multiple frames per step (1-50)

### Information Display
- **Current Frame**: Shows current frame number and total frames
- **Iteration**: Physics iteration count
- **Step Size**: Current integration step size
- **Node Count**: Number of nodes in the graph
- **Playing Status**: Whether auto-play is active

### Progress Bar
Visual indicator showing current position in the simulation timeline.

## Physics Parameters

The simulations use these physics parameters:

| Parameter | Value | Description |
|-----------|--------|-------------|
| Spring Constant | 0.08 | Attraction between connected nodes |
| Repulsion Constant | 40.0 | Node-to-node repulsion force |
| Barrier Constant | 80.0 | Edge barrier field strength |
| Rest Length | 2.5 | Preferred edge length |
| Time Step | 0.008 | Integration step size |
| Damping | 0.96 | Velocity damping factor |
| Edge Radius | 0.6 | Edge corridor thickness |

## Node Types and Colors

| Node Type | Shape | Color | Usage |
|-----------|--------|--------|---------|
| Entry | Ellipse | Light Green (#90ee90) | Function entry point |
| Exit | Ellipse | Red (#ff6b6b) | Function exit point |
| Assignment | Box | Gold (#ffd700) | Variable assignments |
| Conditional | Diamond | Orange (#ffa500) | If/elif/else statements |
| Loop | Diamond | Light Red (#ff9999) | For/while loops |
| Statement | Box | Light Blue (#97c2fc) | Generic statements |
| Return | Box | Light Green (#90ee90) | Return statements |
| Merge | Circle | Light Gray (#d3d3d3) | Control flow merge points |

## Memory Optimization

The simulations use memory-efficient frame management:

- **Frame Buffer**: Keeps only 50 frames in memory by default
- **Disk Storage**: Large simulations write frames to JSON files
- **Capture Interval**: Records every 2-3 iterations to reduce storage
- **Lazy Loading**: Loads frames on demand during playback

## File Structure

```
structure_visualizations/simulations/
├── index.html                           # Main simulation index
├── linear_5_lines_layout_simulation.html  # Linear structure simulation
├── binary_6_lines_layout_simulation.html  # Binary branching simulation
├── loop_8_lines_layout_simulation.html    # Loop structure simulation
├── nested_12_lines_layout_simulation.html # Nested structure simulation
├── linear_5_lines_simulation_frames.json  # Linear simulation data
├── binary_6_lines_simulation_frames.json  # Binary simulation data
├── loop_8_lines_simulation_frames.json    # Loop simulation data
└── nested_12_lines_simulation_frames.json # Nested simulation data
```

## Usage Examples

### Basic Simulation Viewing
1. Open `index.html` in your web browser
2. Click on any simulation link
3. Use the control panel to navigate
4. Adjust FPS for comfortable viewing speed

### Step-by-Step Analysis
1. Open a specific simulation
2. Click "Step Forward" to advance one frame
3. Observe how nodes move and settle
4. Watch edge barrier forces prevent crossings
5. Use "Step Backward" to review changes

### Performance Analysis
1. Set FPS to maximum (10) for quick overview
2. Observe convergence behavior
3. Reduce FPS for detailed analysis
4. Monitor iteration count and step size
5. Watch how physics parameters affect stability

## Troubleshooting

### Common Issues

**Simulation doesn't load**
- Check that all JSON frame files exist
- Verify HTML file has correct paths
- Ensure browser supports JavaScript

**Playback is choppy**
- Reduce FPS setting
- Close other browser tabs
- Check available memory

**Nodes fly off screen**
- Physics parameters may be too aggressive
- Reload simulation from beginning
- Check for corrupted frame data

**Controls don't respond**
- Refresh the page
- Check browser console for errors
- Verify JavaScript is enabled

### Performance Tips

1. **For Large Graphs**: Use lower FPS (1-2)
2. **For Detailed Analysis**: Use step-by-step navigation
3. **For Overview**: Use higher FPS (5-10) with speed control
4. **Memory Issues**: Close other tabs, reduce frame buffer size

## Advanced Features

### Custom Simulation Parameters
Edit the physics parameters in `generate_structure_simulations_standalone.py`:

```python
# Conservative parameters for stability
G.k_spring = 0.08      # Reduce for gentler attraction
G.k_repel = 40.0        # Reduce for less repulsion
G.k_barrier = 80.0       # Reduce for weaker edge barriers
G.step = 0.008          # Reduce for more stable integration
G.damping = 0.96         # Increase for more damping
```

### Adding New Structures
1. Define the structure in `create_simple_structure_examples()`
2. Specify nodes with types, positions, and connections
3. Add to the examples list
4. Regenerate simulations

### Exporting Simulation Data
Frame data is stored in JSON format:
```json
{
  "iteration": 0,
  "step": 0.008,
  "nodes": {
    "n0": {
      "x": 0.0,
      "y": 0.0,
      "label": "entry",
      "shape": "ellipse",
      "color": "#90ee90"
    }
  }
}
```

## Integration with FlowScope

These simulations integrate seamlessly with the broader FlowScope ecosystem:

- **Function Flow Parser**: Extracts control flow from Python code
- **Layout Calculator**: Provides initial positioning
- **Layout Relaxer**: Optimizes layout using physics simulation
- **HTML Renderer**: Creates interactive visualizations
- **Simulation Visualizer**: Adds step-by-step playback

## Contributing

To contribute new simulation features:

1. **Test thoroughly**: Ensure simulations work across browsers
2. **Document parameters**: Explain physics parameter effects
3. **Optimize performance**: Monitor memory usage and frame rate
4. **Add examples**: Include new structure types
5. **Update documentation**: Keep this README current

## License

These simulations are part of the FlowScope project and follow the same licensing terms.
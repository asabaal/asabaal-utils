# Enhanced Control Flow Structure Visualization Summary

This document summarizes all generated control flow visualizations with layout relaxation simulations.

## Features

- **Static Visualizations**: Traditional function flow diagrams
- **Layout Relaxation Simulations**: Step-by-step physics-based layout optimization
- **Interactive Controls**: Play, pause, step forward/backward, adjustable frame rate
- **Memory Optimization**: Efficient handling of large simulations

## Simulation Controls

- **Play/Pause**: Auto-play the simulation
- **Step Forward/Backward**: Navigate frame by frame
- **FPS Control**: Adjust playback speed (0.5 - 10 FPS)
- **Speed Control**: Skip multiple frames per step (1-50 frames)
- **Progress Bar**: Visual indication of simulation progress

## Linear Structures

## Linear Structures\n\n### linear_3_lines
- **Description**: 3 lines - 3 lines - Simple linear
- **Nodes**: 3
- **Edges**: 2
- **Static Visualization**: [linear_3_lines_flow.html](linear_3_lines_flow.html)
- **Layout Simulation**: [linear_3_lines_layout_simulation.html](linear_3_lines_layout_simulation.html)

### linear_5_lines
- **Description**: 5 lines - 5 lines - Basic linear
- **Nodes**: 5
- **Edges**: 4
- **Static Visualization**: [linear_5_lines_flow.html](linear_5_lines_flow.html)
- **Layout Simulation**: [linear_5_lines_layout_simulation.html](linear_5_lines_layout_simulation.html)

### linear_8_lines
- **Description**: 8 lines - 8 lines - Medium linear
- **Nodes**: 6
- **Edges**: 5
- **Static Visualization**: [linear_8_lines_flow.html](linear_8_lines_flow.html)
- **Layout Simulation**: [linear_8_lines_layout_simulation.html](linear_8_lines_layout_simulation.html)

### linear_10_lines
- **Description**: 10 lines - 10 lines - Complex linear
- **Nodes**: 6
- **Edges**: 5
- **Static Visualization**: [linear_10_lines_flow.html](linear_10_lines_flow.html)
- **Layout Simulation**: [linear_10_lines_layout_simulation.html](linear_10_lines_layout_simulation.html)

## Simulation Statistics

- **Total Functions with Simulations**: 25
- **Average Iterations per Simulation**: 150
- **Frame Capture Interval**: Every 3 iterations
- **Memory Management**: 50 frames max in memory

## Physics Parameters

The layout relaxation uses the following physics parameters:

- **Spring Constant**: 0.08 (attraction between connected nodes)
- **Repulsion Constant**: 40.0 (node-to-node repulsion)
- **Barrier Constant**: 80.0 (edge barrier strength)
- **Rest Length**: 2.5 (preferred edge length)
- **Damping**: 0.96 (velocity damping factor)
- **Time Step**: 0.008 (integration step size)

## Usage Instructions

1. **Static View**: Open the `_flow.html` files for traditional diagrams
2. **Simulation View**: Open the `_layout_simulation.html` files for interactive simulations
3. **Controls**: Use the control panel to navigate through the simulation
4. **Performance**: For large graphs, reduce FPS or increase capture interval


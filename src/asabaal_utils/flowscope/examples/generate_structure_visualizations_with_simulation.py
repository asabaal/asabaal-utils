#!/usr/bin/env python3
"""
Enhanced structure visualization generator with layout relaxation simulation
Integrates the new layout relaxer with step-by-step simulation capabilities
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_structure_visualizations import VISUALIZATION_EXAMPLES, generate_visualizations
from layout_simulation_visualizer import LayoutSimulationVisualizer

def convert_function_flow_to_layout_graph(function_flow_data: Dict[str, Any]) -> 'GraphLayout':
    """Convert function flow data to layout relaxer graph format"""
    try:
        from layout_relaxer import GraphLayout
    except ImportError:
        print("Warning: layout_relaxer not available, using fallback")
        return None
    
    G = GraphLayout()
    
    # Conservative physics parameters for stable simulation
    G.k_spring = 0.08
    G.k_repel = 40.0
    G.k_barrier = 80.0
    G.L0 = 2.5
    G.step = 0.008
    G.damping = 0.96
    G.edge_radius = 0.6
    
    # Node style mapping
    style_map = {
        "entry": {"shape": "ellipse", "color": "#90ee90"},
        "exit": {"shape": "ellipse", "color": "#ff6b6b"},
        "assignment": {"shape": "box", "color": "#ffd700"},
        "conditional": {"shape": "diamond", "color": "#ffa500"},
        "loop": {"shape": "diamond", "color": "#ff9999"},
        "statement": {"shape": "box", "color": "#97c2fc"},
        "return": {"shape": "box", "color": "#90ee90"},
        "try": {"shape": "box", "color": "#dda0dd"},
        "except": {"shape": "box", "color": "#f0e68c"},
        "merge": {"shape": "circle", "color": "#d3d3d3"},
    }
    
    # Add nodes
    for node_data in function_flow_data.get("nodes", []):
        node_type = node_data.get("type", "statement")
        style = style_map.get(node_type, style_map["statement"])
        
        # Calculate node size based on label length
        label = node_data.get("label", "")
        width = max(1.5, min(3.0, len(label) * 0.15 + 1.5))
        height = 1.2 if node_type in ["entry", "exit"] else 1.0
        
        # Initial position based on existing layout if available
        x = node_data.get("x", 0.0) / 50.0  # Convert from pixels to layout units
        y = node_data.get("y", 0.0) / 50.0
        
        G.add_node(
            node_data["id"],
            label,
            **style,
            width=width,
            height=height,
            pos=(x, y)
        )
    
    # Add edges
    for edge_data in function_flow_data.get("edges", []):
        G.add_edge(edge_data["from"], edge_data["to"])
    
    return G

def generate_simulation_for_function(function_flow_data: Dict[str, Any], 
                                  function_name: str,
                                  output_dir: Path,
                                  iterations: int = 150,
                                  capture_interval: int = 3) -> Optional[str]:
    """Generate layout relaxation simulation for a single function"""
    
    # Convert to layout graph
    G = convert_function_flow_to_layout_graph(function_flow_data)
    if G is None:
        return None
    
    # Create visualizer
    visualizer = LayoutSimulationVisualizer(max_frames_in_memory=50)
    
    # Run simulation
    frames_file = output_dir / f"{function_name}_simulation_frames.json"
    visualizer.run_simulation(
        G,
        iterations=iterations,
        capture_interval=capture_interval,
        output_file=str(frames_file)
    )
    
    # Generate HTML visualizer
    html_file = output_dir / f"{function_name}_layout_simulation.html"
    visualizer.load_frames(str(frames_file))
    visualizer.generate_html_visualizer(str(html_file))
    
    return str(html_file)

def create_enhanced_visualization_summary(simulations: List[Dict[str, Any]], 
                                        output_dir: Path):
    """Create enhanced summary with simulation links"""
    
    summary_content = """# Enhanced Control Flow Structure Visualization Summary

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

"""
    
    # Group simulations by type
    by_type = {}
    for sim in simulations:
        struct_type = sim["type"]
        if struct_type not in by_type:
            by_type[struct_type] = []
        by_type[struct_type].append(sim)
    
    # Generate content for each type
    type_order = ["linear", "binary", "multi", "loop", "nested", "exception", "multi_return", "complex"]
    
    for struct_type in type_order:
        if struct_type not in by_type:
            continue
            
        summary_content += f"## {struct_type.title()} Structures\\n\\n"
        
        for sim in sorted(by_type[struct_type], key=lambda x: x["lines"]):
            name = sim["name"]
            lines = sim["lines"]
            nodes = sim["nodes"]
            edges = sim["edges"]
            
            static_link = f"{name}_flow.html"
            simulation_link = f"{name}_layout_simulation.html"
            
            summary_content += f"""### {name}
- **Description**: {lines} lines - {sim.get('description', 'Control flow structure')}
- **Nodes**: {nodes}
- **Edges**: {edges}
- **Static Visualization**: [{static_link}]({static_link})
- **Layout Simulation**: [{simulation_link}]({simulation_link})

"""
    
    summary_content += """## Simulation Statistics

- **Total Functions with Simulations**: {total_sims}
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

""".format(total_sims=len(simulations))
    
    # Write summary
    summary_file = output_dir / "enhanced_visualization_summary.md"
    with open(summary_file, 'w') as f:
        f.write(summary_content)
    
    return summary_file

def generate_structure_examples_with_flow_data():
    """Generate structure examples with flow data using existing generator"""
    
    # Setup paths
    examples_dir = Path(__file__).parent
    structure_examples_file = examples_dir / 'structure_examples.py'
    
    # Read source code
    with open(structure_examples_file, 'r') as f:
        source_code = f.read()
    
    # Import required modules
    sys.path.insert(0, str(examples_dir.parent.parent))
    try:
        from asabaal_utils.flowscope.function_flow_builder import generate_function_flow
    except ImportError:
        from ..function_flow_builder import generate_function_flow
    
    examples = []
    
    for function_name, structure_type, description in VISUALIZATION_EXAMPLES:
        try:
            # Generate function flow
            function_flow = generate_function_flow(source_code, function_name)
            
            if function_flow is None:
                print(f"  ❌ Failed to generate function flow for {function_name}")
                continue
            
            # Extract line count from function name or description
            lines = int([x for x in description.split() if x.isdigit()][0]) if any(x.isdigit() for x in description.split()) else 0
            
            examples.append({
                "name": function_name,
                "type": structure_type.lower().replace(" ", "_").replace("-", "_"),
                "lines": lines,
                "description": description,
                "flow_data": function_flow
            })
            
        except Exception as e:
            print(f"  ❌ Error processing {function_name}: {e}")
            continue
    
    return examples

def main():
    """Main function to generate enhanced structure visualizations"""
    
    print("Generating enhanced structure visualizations with layout relaxation simulations...")
    
    # Setup directories
    base_dir = Path(__file__).parent
    output_dir = base_dir / "structure_visualizations"
    simulation_dir = output_dir / "simulations"
    simulation_dir.mkdir(exist_ok=True)
    
    # Generate structure examples with flow data
    print("1. Generating base structure examples...")
    structure_examples = generate_structure_examples_with_flow_data()
    
    if not structure_examples:
        print("❌ No structure examples generated. Exiting.")
        return
    
    print(f"   Generated {len(structure_examples)} structure examples")
    
    simulations = []
    
    # Generate simulations for each function
    print("2. Generating layout relaxation simulations...")
    for i, example in enumerate(structure_examples):
        function_name = example["name"]
        function_flow_data = example["flow_data"]
        
        print(f"   Processing {function_name} ({i+1}/{len(structure_examples)})...")
        
        # Generate simulation
        sim_file = generate_simulation_for_function(
            function_flow_data,
            function_name,
            simulation_dir,
            iterations=150,
            capture_interval=3
        )
        
        if sim_file:
            simulations.append({
                "name": function_name,
                "type": example["type"],
                "lines": example["lines"],
                "nodes": len(function_flow_data.get("nodes", [])),
                "edges": len(function_flow_data.get("edges", [])),
                "description": example.get("description", ""),
                "simulation_file": sim_file
            })
            print(f"     ✓ Simulation generated: {sim_file}")
        else:
            print(f"     ✗ Failed to generate simulation for {function_name}")
    
    # Create enhanced summary
    print("3. Creating enhanced visualization summary...")
    summary_file = create_enhanced_visualization_summary(simulations, output_dir)
    
    # Create index page with links to all simulations
    print("4. Creating simulation index page...")
    create_simulation_index_page(simulations, simulation_dir)
    
    print(f"\\n✓ Enhanced structure visualizations complete!")
    print(f"  - Static visualizations: {output_dir}")
    print(f"  - Layout simulations: {simulation_dir}")
    print(f"  - Summary: {summary_file}")
    print(f"  - Simulation index: {simulation_dir}/index.html")

def create_simulation_index_page(simulations: List[Dict[str, Any]], output_dir: Path):
    """Create an index page with all simulations"""
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Layout Relaxation Simulations</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .controls {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .filter-group {
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }
        .filter-group label {
            font-weight: bold;
            margin-right: 5px;
        }
        select, input {
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .simulations {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .simulation-card {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            background: #fff;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .simulation-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .simulation-title {
            font-size: 18px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
        }
        .simulation-meta {
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
        }
        .simulation-links {
            display: flex;
            gap: 10px;
        }
        .simulation-links a {
            padding: 6px 12px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }
        .static-link {
            background: #28a745;
            color: white;
        }
        .simulation-link {
            background: #007bff;
            color: white;
        }
        .type-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 5px;
        }
        .linear { background: #e3f2fd; color: #1976d2; }
        .binary { background: #f3e5f5; color: #7b1fa2; }
        .multi { background: #e8f5e8; color: #388e3c; }
        .loop { background: #fff3e0; color: #f57c00; }
        .nested { background: #fce4ec; color: #c2185b; }
        .exception { background: #f3e5f5; color: #7b1fa2; }
        .multi_return { background: #e0f2f1; color: #00796b; }
        .complex { background: #ffebee; color: #d32f2f; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Layout Relaxation Simulations</h1>
        
        <div class="controls">
            <div class="filter-group">
                <label>Filter by type:</label>
                <select id="typeFilter" onchange="filterSimulations()">
                    <option value="">All Types</option>
                    <option value="linear">Linear</option>
                    <option value="binary">Binary</option>
                    <option value="multi">Multi-way</option>
                    <option value="loop">Loop</option>
                    <option value="nested">Nested</option>
                    <option value="exception">Exception</option>
                    <option value="multi_return">Multi-return</option>
                    <option value="complex">Complex</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Min nodes:</label>
                <input type="number" id="minNodes" value="0" onchange="filterSimulations()">
            </div>
            
            <div class="filter-group">
                <label>Max nodes:</label>
                <input type="number" id="maxNodes" value="100" onchange="filterSimulations()">
            </div>
        </div>
        
        <div class="simulations" id="simulationsContainer">
"""
    
    # Add simulation cards
    for sim in simulations:
        type_class = sim["type"]
        html_content += f"""
            <div class="simulation-card" data-type="{type_class}" data-nodes="{sim['nodes']}">
                <div class="simulation-title">
                    <span class="type-badge {type_class}">{type_class.title()}</span>
                    {sim['name']}
                </div>
                <div class="simulation-meta">
                    Lines: {sim['lines']} | Nodes: {sim['nodes']} | Edges: {sim['edges']}
                </div>
                <div class="simulation-links">
                    <a href="{sim['name']}_flow.html" class="static-link">Static</a>
                    <a href="{sim['name']}_layout_simulation.html" class="simulation-link">Simulation</a>
                </div>
            </div>
        """
    
    html_content += """
        </div>
    </div>
    
    <script>
        function filterSimulations() {
            const typeFilter = document.getElementById('typeFilter').value;
            const minNodes = parseInt(document.getElementById('minNodes').value);
            const maxNodes = parseInt(document.getElementById('maxNodes').value);
            
            const cards = document.querySelectorAll('.simulation-card');
            
            cards.forEach(card => {
                const cardType = card.dataset.type;
                const cardNodes = parseInt(card.dataset.nodes);
                
                const typeMatch = !typeFilter || cardType === typeFilter;
                const nodesMatch = cardNodes >= minNodes && cardNodes <= maxNodes;
                
                card.style.display = typeMatch && nodesMatch ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>
    """
    
    with open(output_dir / "index.html", 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
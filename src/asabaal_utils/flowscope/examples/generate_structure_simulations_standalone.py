#!/usr/bin/env python3
"""
Standalone structure visualization generator with layout relaxation simulation
Fixed version with proper imports and error handling
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append('..')
sys.path.append(str(Path(__file__).parent.parent.parent))

def create_all_structure_examples():
    """Create all 25 structure examples from the original specification"""
    
    # Complete examples list - all 25 functions
    VISUALIZATION_EXAMPLES = [
            # Linear functions (1-10 lines)
            ('linear_3_lines', 'Linear', '3 lines - Simple linear'),
            ('linear_5_lines', 'Linear', '5 lines - Basic linear'),
            ('linear_8_lines', 'Linear', '8 lines - Medium linear'),
            ('linear_10_lines', 'Linear', '10 lines - Complex linear'),
            
            # Binary branching (5-15 lines)
            ('binary_6_lines', 'Binary Branching', '6 lines - Simple binary'),
            ('binary_9_lines', 'Binary Branching', '9 lines - Medium binary'),
            ('binary_14_lines', 'Binary Branching', '14 lines - Complex binary'),
            ('binary_18_lines', 'Binary Branching', '18 lines - Advanced binary'),
            
            # Multi-way branching (8-25 lines)
            ('multi_10_lines', 'Multi-way Branching', '10 lines - Simple multi-way'),
            ('multi_14_lines', 'Multi-way Branching', '14 lines - Medium multi-way'),
            ('multi_22_lines', 'Multi-way Branching', '22 lines - Complex multi-way'),
            
            # Loop structures (6-20 lines)
            ('loop_8_lines', 'Loop Structures', '8 lines - Simple loop'),
            ('loop_11_lines', 'Loop Structures', '11 lines - Medium loop'),
            ('loop_16_lines', 'Loop Structures', '16 lines - Complex loop'),
            ('loop_19_lines', 'Loop Structures', '19 lines - Advanced loop'),
            
            # Nested structures (10-30 lines)
            ('nested_12_lines', 'Nested Structures', '12 lines - Simple nesting'),
            ('nested_18_lines', 'Nested Structures', '18 lines - Medium nesting'),
            ('nested_25_lines', 'Nested Structures', '25 lines - Complex nesting'),
            
            # Exception handling (8-25 lines)
            ('exception_10_lines', 'Exception Handling', '10 lines - Simple exception'),
            ('exception_14_lines', 'Exception Handling', '14 lines - Medium exception'),
            ('exception_20_lines', 'Exception Handling', '20 lines - Complex exception'),
            
            # Multiple returns (5-20 lines)
            ('multi_return_7_lines', 'Multiple Returns', '7 lines - Simple multi-return'),
            ('multi_return_11_lines', 'Multiple Returns', '11 lines - Medium multi-return'),
            ('multi_return_16_lines', 'Multiple Returns', '16 lines - Complex multi-return'),
            
            # Complex combination
            ('complex_25_lines', 'Complex Mixed', '25 lines - Mixed structures'),
        ]
    
    examples = []
    
    for function_name, structure_type, description in VISUALIZATION_EXAMPLES:
        # Generate flow data based on structure type
        flow_data = generate_flow_data_for_type(function_name, structure_type)
        
        if flow_data:
            # Extract line count from description
            lines = int([x for x in description.split() if x.isdigit()][0]) if any(x.isdigit() for x in description.split()) else 0
            
            examples.append({
                "name": function_name,
                "type": structure_type.lower().replace(" ", "_").replace("-", "_"),
                "lines": lines,
                "description": description,
                "flow_data": flow_data
            })
    
    return examples

def generate_flow_data_for_type(function_name: str, structure_type: str):
    """Generate appropriate flow data for each structure type"""
    
    if "linear" in structure_type.lower():
        return generate_linear_flow(function_name)
    elif "binary" in structure_type.lower():
        return generate_binary_flow(function_name)
    elif "multi" in structure_type.lower():
        return generate_multi_flow(function_name)
    elif "loop" in structure_type.lower():
        return generate_loop_flow(function_name)
    elif "nested" in structure_type.lower():
        return generate_nested_flow(function_name)
    elif "exception" in structure_type.lower():
        return generate_exception_flow(function_name)
    elif "multi_return" in structure_type.lower():
        return generate_multi_return_flow(function_name)
    elif "complex" in structure_type.lower():
        return generate_complex_flow(function_name)
    else:
        return generate_linear_flow(function_name)  # Default

def generate_linear_flow(function_name: str):
    """Generate linear flow structure"""
    # Determine complexity based on line count
    if "3_lines" in function_name:
        node_count = 3
    elif "5_lines" in function_name:
        node_count = 4
    elif "8_lines" in function_name:
        node_count = 5
    elif "10_lines" in function_name:
        node_count = 6
    else:
        node_count = 4
    
    nodes = []
    edges = []
    
    # Create linear chain
    for i in range(node_count):
        node_type = "entry" if i == 0 else ("exit" if i == node_count - 1 else "statement" if i < node_count - 2 else "return")
        label = "entry" if i == 0 else ("exit" if i == node_count - 1 else f"statement_{i}" if i < node_count - 2 else "return")
        
        nodes.append({
            "id": f"n{i}",
            "type": node_type,
            "label": label,
            "x": 0,
            "y": i * 100
        })
        
        if i > 0:
            edges.append({"from": f"n{i-1}", "to": f"n{i}"})
    
    return {"nodes": nodes, "edges": edges}

def generate_binary_flow(function_name: str):
    """Generate binary branching flow structure"""
    # Determine complexity
    if "6_lines" in function_name:
        complexity = "simple"
    elif "9_lines" in function_name:
        complexity = "medium"
    elif "14_lines" in function_name:
        complexity = "complex"
    elif "18_lines" in function_name:
        complexity = "advanced"
    else:
        complexity = "simple"
    
    nodes = [
        {"id": "n0", "type": "entry", "label": "entry", "x": 0, "y": 0},
        {"id": "n1", "type": "conditional", "label": "condition", "x": 0, "y": 100},
        {"id": "n2", "type": "assignment", "label": "true_branch", "x": -150, "y": 200},
        {"id": "n3", "type": "assignment", "label": "false_branch", "x": 150, "y": 200},
    ]
    
    edges = [
        {"from": "n0", "to": "n1"},
        {"from": "n1", "to": "n2", "label": "true"},
        {"from": "n1", "to": "n3", "label": "false"},
    ]
    
    # Add complexity-specific nodes
    if complexity in ["medium", "complex", "advanced"]:
        nodes.extend([
            {"id": "n4", "type": "statement", "label": "process_true", "x": -150, "y": 300},
            {"id": "n5", "type": "statement", "label": "process_false", "x": 150, "y": 300},
        ])
        edges.extend([
            {"from": "n2", "to": "n4"},
            {"from": "n3", "to": "n5"},
        ])
        last_nodes = ["n4", "n5"]
    else:
        last_nodes = ["n2", "n3"]
    
    # Add merge and exit
    merge_id = f"n{len(nodes)}"
    exit_id = f"n{len(nodes) + 1}"
    
    nodes.extend([
        {"id": merge_id, "type": "merge", "label": "merge", "x": 0, "y": 400},
        {"id": exit_id, "type": "exit", "label": "exit", "x": 0, "y": 500},
    ])
    
    for node in last_nodes:
        edges.append({"from": node, "to": merge_id})
    
    edges.append({"from": merge_id, "to": exit_id})
    
    return {"nodes": nodes, "edges": edges}

def generate_loop_flow(function_name: str):
    """Generate loop flow structure"""
    nodes = [
        {"id": "n0", "type": "entry", "label": "entry", "x": 0, "y": 0},
        {"id": "n1", "type": "assignment", "label": "init", "x": 0, "y": 100},
        {"id": "n2", "type": "loop", "label": "condition", "x": 0, "y": 200},
        {"id": "n3", "type": "statement", "label": "loop_body", "x": 200, "y": 300},
        {"id": "n4", "type": "assignment", "label": "increment", "x": 200, "y": 400},
    ]
    
    edges = [
        {"from": "n0", "to": "n1"},
        {"from": "n1", "to": "n2"},
        {"from": "n2", "to": "n3", "label": "iterate"},
        {"from": "n3", "to": "n4"},
        {"from": "n4", "to": "n2", "label": "loop_back"},  # Loop back edge
    ]
    
    # Add exit
    exit_id = f"n{len(nodes)}"
    nodes.append({"id": exit_id, "type": "exit", "label": "exit", "x": 0, "y": 500})
    edges.append({"from": "n2", "to": exit_id, "label": "exit_condition"})
    
    return {"nodes": nodes, "edges": edges}

def generate_nested_flow(function_name: str):
    """Generate nested conditional flow structure"""
    nodes = [
        {"id": "n0", "type": "entry", "label": "entry", "x": 0, "y": 0},
        {"id": "n1", "type": "conditional", "label": "outer_cond", "x": 0, "y": 100},
        {"id": "n2", "type": "conditional", "label": "inner_cond", "x": -150, "y": 200},
        {"id": "n3", "type": "assignment", "label": "inner_true", "x": -250, "y": 300},
        {"id": "n4", "type": "assignment", "label": "inner_false", "x": -50, "y": 300},
        {"id": "n5", "type": "assignment", "label": "outer_false", "x": 150, "y": 200},
    ]
    
    edges = [
        {"from": "n0", "to": "n1"},
        {"from": "n1", "to": "n2", "label": "true"},
        {"from": "n1", "to": "n5", "label": "false"},
        {"from": "n2", "to": "n3", "label": "true"},
        {"from": "n2", "to": "n4", "label": "false"},
    ]
    
    # Add merge and exit
    merge_id = f"n{len(nodes)}"
    exit_id = f"n{len(nodes) + 1}"
    
    nodes.extend([
        {"id": merge_id, "type": "merge", "label": "merge", "x": 0, "y": 400},
        {"id": exit_id, "type": "exit", "label": "exit", "x": 0, "y": 500},
    ])
    
    edges.extend([
        {"from": "n3", "to": merge_id},
        {"from": "n4", "to": merge_id},
        {"from": "n5", "to": merge_id},
        {"from": merge_id, "to": exit_id},
    ])
    
    return {"nodes": nodes, "edges": edges}

def generate_multi_flow(function_name: str):
    """Generate multi-way branching flow structure"""
    nodes = [
        {"id": "n0", "type": "entry", "label": "entry", "x": 0, "y": 0},
        {"id": "n1", "type": "conditional", "label": "multi_cond", "x": 0, "y": 100},
        {"id": "n2", "type": "assignment", "label": "case_1", "x": -200, "y": 200},
        {"id": "n3", "type": "assignment", "label": "case_2", "x": -67, "y": 200},
        {"id": "n4", "type": "assignment", "label": "case_3", "x": 67, "y": 200},
        {"id": "n5", "type": "assignment", "label": "default_case", "x": 200, "y": 200},
    ]
    
    edges = [
        {"from": "n0", "to": "n1"},
        {"from": "n1", "to": "n2", "label": "case_1"},
        {"from": "n1", "to": "n3", "label": "case_2"},
        {"from": "n1", "to": "n4", "label": "case_3"},
        {"from": "n1", "to": "n5", "label": "default"},
    ]
    
    # Add merge and exit
    merge_id = f"n{len(nodes)}"
    exit_id = f"n{len(nodes) + 1}"
    
    nodes.extend([
        {"id": merge_id, "type": "merge", "label": "merge", "x": 0, "y": 300},
        {"id": exit_id, "type": "exit", "label": "exit", "x": 0, "y": 400},
    ])
    
    for i in range(2, 6):  # Connect all cases to merge
        edges.append({"from": f"n{i}", "to": merge_id})
    
    edges.append({"from": merge_id, "to": exit_id})
    
    return {"nodes": nodes, "edges": edges}

def generate_exception_flow(function_name: str):
    """Generate exception handling flow structure"""
    nodes = [
        {"id": "n0", "type": "entry", "label": "entry", "x": 0, "y": 0},
        {"id": "n1", "type": "try", "label": "try_block", "x": 0, "y": 100},
        {"id": "n2", "type": "statement", "label": "risky_operation", "x": 0, "y": 200},
        {"id": "n3", "type": "except", "label": "except_handler", "x": 150, "y": 300},
        {"id": "n4", "type": "statement", "label": "cleanup", "x": 0, "y": 400},
    ]
    
    edges = [
        {"from": "n0", "to": "n1"},
        {"from": "n1", "to": "n2"},
        {"from": "n1", "to": "n3", "label": "exception"},
        {"from": "n2", "to": "n4"},
        {"from": "n3", "to": "n4"},
    ]
    
    # Add exit
    exit_id = f"n{len(nodes)}"
    nodes.append({"id": exit_id, "type": "exit", "label": "exit", "x": 0, "y": 500})
    edges.append({"from": "n4", "to": exit_id})
    
    return {"nodes": nodes, "edges": edges}

def generate_multi_return_flow(function_name: str):
    """Generate multiple returns flow structure"""
    nodes = [
        {"id": "n0", "type": "entry", "label": "entry", "x": 0, "y": 0},
        {"id": "n1", "type": "conditional", "label": "cond_1", "x": 0, "y": 100},
        {"id": "n2", "type": "return", "label": "return_1", "x": -150, "y": 200},
        {"id": "n3", "type": "conditional", "label": "cond_2", "x": 150, "y": 200},
        {"id": "n4", "type": "return", "label": "return_2", "x": 50, "y": 300},
        {"id": "n5", "type": "return", "label": "return_3", "x": 250, "y": 300},
    ]
    
    edges = [
        {"from": "n0", "to": "n1"},
        {"from": "n1", "to": "n2", "label": "true"},
        {"from": "n1", "to": "n3", "label": "false"},
        {"from": "n3", "to": "n4", "label": "true"},
        {"from": "n3", "to": "n5", "label": "false"},
    ]
    
    # Add final exit
    exit_id = f"n{len(nodes)}"
    nodes.append({"id": exit_id, "type": "exit", "label": "exit", "x": 0, "y": 400})
    
    # Connect all returns to exit
    for i in range(2, 6):
        if f"n{i}" in nodes:
            edges.append({"from": f"n{i}", "to": exit_id})
    
    return {"nodes": nodes, "edges": edges}

def generate_complex_flow(function_name: str):
    """Generate complex mixed flow structure"""
    nodes = [
        {"id": "n0", "type": "entry", "label": "entry", "x": 0, "y": 0},
        {"id": "n1", "type": "conditional", "label": "main_cond", "x": 0, "y": 100},
        {"id": "n2", "type": "loop", "label": "process_loop", "x": -150, "y": 200},
        {"id": "n3", "type": "statement", "label": "loop_body", "x": -150, "y": 300},
        {"id": "n4", "type": "assignment", "label": "increment", "x": -150, "y": 400},
        {"id": "n5", "type": "try", "label": "error_handling", "x": 150, "y": 200},
        {"id": "n6", "type": "statement", "label": "risky_op", "x": 150, "y": 300},
        {"id": "n7", "type": "except", "label": "except_block", "x": 150, "y": 400},
    ]
    
    edges = [
        {"from": "n0", "to": "n1"},
        {"from": "n1", "to": "n2", "label": "true"},
        {"from": "n1", "to": "n5", "label": "false"},
        {"from": "n2", "to": "n3"},
        {"from": "n3", "to": "n4"},
        {"from": "n4", "to": "n2", "label": "loop_back"},
        {"from": "n2", "to": "n8", "label": "loop_exit"},  # Will add n8
        {"from": "n5", "to": "n6"},
        {"from": "n5", "to": "n7", "label": "exception"},
        {"from": "n6", "to": "n8"},
        {"from": "n7", "to": "n8"},
    ]
    
    # Add merge and exit
    merge_id = f"n{len(nodes)}"
    exit_id = f"n{len(nodes) + 1}"
    
    nodes.extend([
        {"id": merge_id, "type": "merge", "label": "final_merge", "x": 0, "y": 500},
        {"id": exit_id, "type": "exit", "label": "exit", "x": 0, "y": 600},
    ])
    
    edges.extend([
        {"from": "n2", "to": merge_id},
        {"from": "n5", "to": merge_id},
        {"from": merge_id, "to": exit_id},
    ])
    
    return {"nodes": nodes, "edges": edges}

def convert_function_flow_to_layout_graph(function_flow_data: Dict[str, Any]):
    """Convert function flow data to layout relaxer graph format"""
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from layout_relaxer import GraphLayout
    except ImportError:
        print("Warning: layout_relaxer not available, using fallback")
        return None
    
    G = GraphLayout()
    
    # Balanced physics parameters for convergence
    G.k_spring = 0.28
    G.k_repel = 12.0  # Much smaller for stability
    G.k_barrier = 500.0  # Much smaller for stability
    G.L0 = 0.45
    G.step = 0.045
    G.damping = 0.92
    G.edge_radius = 0.30
    
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
    try:
        from layout_simulation_visualizer import LayoutSimulationVisualizer
    except ImportError:
        print("Warning: layout_simulation_visualizer not available")
        return None
    
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

def create_summary_page(simulations: List[Dict[str, Any]], output_dir: Path):
    """Create summary page with all simulations"""
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Structure Layout Simulations</title>
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
        .simulation-link {
            display: inline-block;
            padding: 8px 16px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }
        .simulation-link:hover {
            background: #0056b3;
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
        .binary_branching { background: #f3e5f5; color: #7b1fa2; }
        .loop { background: #fff3e0; color: #f57c00; }
        .nested { background: #fce4ec; color: #c2185b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Structure Layout Simulations</h1>
        
        <div class="simulations">
"""
    
    # Add simulation cards
    for sim in simulations:
        type_class = sim["type"]
        html_content += f"""
            <div class="simulation-card">
                <div class="simulation-title">
                    <span class="type-badge {type_class}">{type_class.replace('_', ' ').title()}</span>
                    {sim['name']}
                </div>
                <div class="simulation-meta">
                    Lines: {sim['lines']} | Nodes: {sim['nodes']} | Edges: {sim['edges']}
                </div>
                <div>
                    <a href="{sim['name']}_layout_simulation.html" class="simulation-link">View Simulation</a>
                </div>
            </div>
        """
    
    html_content += """
        </div>
    </div>
</body>
</html>
    """
    
    summary_file = output_dir / "index.html"
    with open(summary_file, 'w') as f:
        f.write(html_content)
    
    return summary_file

def main():
    """Main function to generate structure simulations"""
    
    print("Generating structure layout simulations...")
    
    # Setup directories
    base_dir = Path(__file__).parent
    output_dir = base_dir / "structure_visualizations"
    simulation_dir = output_dir / "simulations"
    simulation_dir.mkdir(exist_ok=True)
    
    # Create all structure examples
    print("1. Creating structure examples...")
    structure_examples = create_all_structure_examples()
    
    print(f"   Created {len(structure_examples)} structure examples")
    
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
            iterations=100,
            capture_interval=2
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
    
    # Create summary page
    print("3. Creating summary page...")
    summary_file = create_summary_page(simulations, simulation_dir)
    
    print(f"\\n✓ Structure simulations complete!")
    print(f"  - Simulations: {simulation_dir}")
    print(f"  - Summary: {summary_file}")
    print(f"  - Total simulations: {len(simulations)}")

if __name__ == "__main__":
    main()
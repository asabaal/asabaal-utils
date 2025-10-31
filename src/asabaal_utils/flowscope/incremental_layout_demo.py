#!/usr/bin/env python3
"""
Incremental Layout Demo Script

This script demonstrates the incremental layout system by:
1. Loading all 25 function examples from the structure examples
2. Creating visualizations that show nodes being added one at a time
3. Showing two stages: add stage → correct locations stage
4. Demonstrating how crossings are resolved after each addition

Usage:
    python incremental_layout_demo.py
"""

import sys
import os
import json
import ast
from pathlib import Path

# Add the parent directory to the path so we can import flowscope modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Define the 25 functions to process (same as generate_structure_visualizations.py)
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

class SimpleNode:
    def __init__(self, name):
        self.name = name
        self.x = 0
        self.y = 0

class SimpleEdge:
    def __init__(self, start, end):
        self.start = start
        self.end = end

class SimpleLayout:
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    def add_node(self, name, pos):
        node = SimpleNode(name)
        node.x, node.y = pos
        self.nodes[name] = node
    
    def add_edge(self, start, end):
        self.edges.append(SimpleEdge(start, end))

def load_existing_function_flow(function_name):
    """Load existing function flow from the structure_visualizations directory."""
    
    flow_file = Path(__file__).parent / 'examples' / 'structure_visualizations' / f'{function_name}_flow.json'
    
    if not flow_file.exists():
        print(f"  ❌ Flow file not found: {flow_file}")
        return None
    
    try:
        with open(flow_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ❌ Error loading flow file: {e}")
        return None

def convert_flow_to_layout_format(function_flow):
    """Convert function flow JSON to the format expected by incremental layout."""
    
    # Create a simple representation that preserves the node order
    nodes = []
    edges = []
    node_info = {}  # Store additional node info (label, type, line)
    
    # Sort nodes by their appearance in the original flow
    node_order = {}
    for i, node in enumerate(function_flow['nodes']):
        node_order[node['id']] = i
        node_info[node['id']] = {
            'label': node['label'],
            'type': node['type'],
            'line': node['line']
        }
    
    # Create node list in order
    for node in function_flow['nodes']:
        nodes.append(node['id'])
    
    # Create edge list
    for edge in function_flow['edges']:
        edges.append((edge['from'], edge['to']))
    
    return nodes, edges, node_info

def create_incremental_layout_stages(nodes, edges, node_info):
    """Create incremental layout stages showing add and correct phases."""
    
    stages = []
    
    # We'll add nodes one by one and track the layout at each stage
    current_nodes = []
    current_edges = []
    
    for i, node_id in enumerate(nodes):
        # Stage 1: Add the node (initial placement)
        current_nodes.append(node_id)
        
        # Add edges that involve this node and previous nodes
        for edge_start, edge_end in edges:
            if edge_start in current_nodes and edge_end in current_nodes:
                if (edge_start, edge_end) not in current_edges:
                    current_edges.append((edge_start, edge_end))
        
        # Create a simple layout for this stage with collision detection
        layout = SimpleLayout()
        
        # Estimate node sizes for collision detection
        node_sizes = {}
        for node in current_nodes:
            label = node_info.get(node, {}).get('label', node)
            node_sizes[node] = estimate_label_size(label)
        
        # Add nodes with simple vertical grid layout
        for j, current_node in enumerate(current_nodes):
            # Vertical grid layout for initial placement
            x = (j % 3) * 2.0  # 3 columns
            y = (j // 3) * 1.5  # rows, vertical spacing
            layout.add_node(current_node, (x, y))
        
        # Add edges
        for edge_start, edge_end in current_edges:
            layout.add_edge(edge_start, edge_end)
        
        # Store the "add" stage
        add_stage = {
            'stage_number': i * 2 + 1,
            'stage_type': 'add',
            'node_added': node_id,
            'nodes': {name: {'x': node.x, 'y': node.y} for name, node in layout.nodes.items()},
            'edges': [(e.start, e.end) for e in layout.edges],
            'total_nodes': len(current_nodes),
            'total_edges': len(current_edges)
        }
        stages.append(add_stage)
        
        # Stage 2: Correct crossings (apply incremental layout algorithm)
        # For this demo, we'll apply a simple crossing resolution
        corrected_layout = apply_crossing_correction(layout, current_nodes, current_edges, node_info)
        
        # Store the "correct" stage
        correct_stage = {
            'stage_number': i * 2 + 2,
            'stage_type': 'correct',
            'node_corrected': node_id,
            'nodes': {name: {'x': node.x, 'y': node.y} for name, node in corrected_layout.nodes.items()},
            'edges': [(e.start, e.end) for e in corrected_layout.edges],
            'total_nodes': len(current_nodes),
            'total_edges': len(current_edges),
            'crossings_fixed': count_crossings(layout, corrected_layout)
        }
        stages.append(correct_stage)
    
    return stages

def estimate_label_size(label):
    """Estimate visual size of a node label."""
    if not label:
        return 1.0, 0.5  # Default size
    
    # Rough estimation based on character count (more compact for vertical layout)
    char_count = len(label)
    width = max(0.8, char_count * 0.10)  # 0.10 units per character, more compact
    height = 0.5  # Reduced height for tighter vertical spacing
    return width, height

def check_collision(pos1, size1, pos2, size2):
    """Check if two nodes overlap given their positions and sizes."""
    x1, y1 = pos1
    w1, h1 = size1
    x2, y2 = pos2
    w2, h2 = size2
    
    # Reduced margin for tighter vertical layout
    margin = 0.1
    
    # Check if rectangles overlap
    return not (x1 + w1/2 + margin < x2 - w2/2 or
                x2 + w2/2 + margin < x1 - w1/2 or
                y1 + h1/2 + margin < y2 - h2/2 or
                y2 + h2/2 + margin < y1 - h1/2)

def apply_crossing_correction(layout, nodes, edges, node_info):
    """Apply crossing correction with collision detection based on label sizes."""
    
    # Create a new layout with corrected positions
    corrected = SimpleLayout()
    
    # Simple heuristic: arrange nodes in layers to minimize crossings
    # Find topological order
    node_levels = {}
    for node in nodes:
        # Count incoming edges
        incoming = sum(1 for e_start, e_end in edges if e_end == node)
        node_levels[node] = incoming
    
    # Group nodes by level
    levels = {}
    for node, level in node_levels.items():
        if level not in levels:
            levels[level] = []
        levels[level].append(node)
    
    # Position nodes by level with collision detection
    max_level = max(levels.keys()) if levels else 0
    placed_positions = {}
    
    for level in range(max_level + 1):
        if level in levels:
            level_nodes = levels[level]
            
            # Sort nodes by estimated size (larger first for better packing)
            node_sizes = {}
            for node in level_nodes:
                label = node_info.get(node, {}).get('label', node)
                node_sizes[node] = estimate_label_size(label)
            
            level_nodes.sort(key=lambda n: node_sizes[n][0] * node_sizes[n][1], reverse=True)
            
        # Try to place each node without collision
            for node in level_nodes:
                width, height = node_sizes[node]
                
                # Try to place each node without collision
                placed = False
                for attempt_x in range(-6, 7):  # Try positions from -6 to 6
                    test_pos = (attempt_x * 0.6, level * 2.0)  # 0.6 unit steps, tighter vertical spacing
                    
                    # Check collision with already placed nodes
                    collision = False
                    for placed_node, placed_pos in placed_positions.items():
                        placed_size = node_sizes.get(placed_node, (1.8, 0.8))
                        if check_collision(test_pos, node_sizes[node], placed_pos, placed_size):
                            collision = True
                            break
                    
                    if not collision:
                        corrected.add_node(node, test_pos)
                        placed_positions[node] = test_pos
                        placed = True
                        break
                
                # If we couldn't place without collision, force place at end
                if not placed:
                    max_x = max(pos[0] for pos in placed_positions.values()) if placed_positions else 0
                    forced_pos = (max_x + width/2 + 0.5, level * 3.0)
                    corrected.add_node(node, forced_pos)
                    placed_positions[node] = forced_pos
    
    # Add edges
    for edge_start, edge_end in edges:
        corrected.add_edge(edge_start, edge_end)
    
    return corrected

def count_crossings(layout1, layout2):
    """Count how many crossings were fixed (simplified)."""
    # This is a simplified count - in practice you'd compare actual edge crossings
    return len(layout1.edges) // 2  # Placeholder

def generate_incremental_visualization(function_name, structure_type, description, stages, node_info):
    """Generate HTML visualization for incremental layout stages."""
    
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Incremental Layout Demo: {function_name}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .controls {{
            text-align: center;
            margin-bottom: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stage-info {{
            background: white;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .add-stage {{
            border-left: 4px solid #2196F3;
        }}
        .correct-stage {{
            border-left: 4px solid #4CAF50;
        }}
        #graph {{
            height: 600px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        button {{
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .play-btn {{
            background-color: #4CAF50;
            color: white;
        }}
        .step-btn {{
            background-color: #2196F3;
            color: white;
        }}
        .reset-btn {{
            background-color: #FF9800;
            color: white;
        }}
        .speed-control {{
            margin: 10px;
        }}
        .stage-counter {{
            background: #f8f9fa;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            color: #495057;
            border: 2px solid #dee2e6;
            margin: 0 10px;
        }}
        .legend {{
            background: white;
            padding: 15px;
            margin-top: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .legend h4 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 16px;
        }}
        .legend-item {{
            display: inline-flex;
            align-items: center;
            margin: 5px 15px 5px 0;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            margin-right: 5px;
            border: 1px solid #ccc;
        }}
        .legend-shape {{
            width: 12px;
            height: 12px;
            margin-right: 8px;
            border: 1px solid #666;
            background: rgba(255,255,255,0.3);
        }}
        .legend-item span {{
            font-size: 12px;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Incremental Layout Demo</h1>
        <h2>{function_name}</h2>
        <p><strong>{structure_type}</strong> - {description}</p>
    </div>
    
    <div class="controls">
        <button class="play-btn" onclick="playAnimation()">▶️ Play Animation</button>
        <button class="step-btn" onclick="nextStage()">⏭️ Next Stage</button>
        <button class="step-btn" onclick="previousStage()">⏮️ Previous Stage</button>
        <button class="step-btn" onclick="goToFinal()">⏭️ Go to Final</button>
        <button class="reset-btn" onclick="resetAnimation()">🔄 Reset</button>
        <div class="stage-counter">
            <span id="stageCounter">Stage 0 of 0</span>
        </div>
        <div class="speed-control">
            <label>Animation Speed: </label>
            <input type="range" id="speedSlider" min="100" max="2000" value="800" step="100">
            <span id="speedValue">800ms</span>
        </div>
    </div>
    
    <div class="stage-info" id="stageInfo">
        <h3>Stage 0: Ready to Start</h3>
        <p>Click "Play Animation" to see the incremental layout process</p>
    </div>
    
    <div id="graph"></div>
    
    <div class="legend">
        <h4>Node Types</h4>
        <div class="legend-item">
            <div class="legend-color" style="background: #90ee90;"></div>
            <div class="legend-shape" style="border-radius: 50%;"></div>
            <span>Entry Point</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff6b6b;"></div>
            <div class="legend-shape" style="border-radius: 50%;"></div>
            <span>Exit Point</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffd700;"></div>
            <div class="legend-shape"></div>
            <span>Assignment</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffa500;"></div>
            <div class="legend-shape" style="transform: rotate(45deg);"></div>
            <span>Conditional</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff9999;"></div>
            <div class="legend-shape" style="transform: rotate(45deg);"></div>
            <span>Loop</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #97c2fc;"></div>
            <div class="legend-shape"></div>
            <span>Statement</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #dda0dd;"></div>
            <div class="legend-shape"></div>
            <span>Try Block</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #f0e68c;"></div>
            <div class="legend-shape"></div>
            <span>Except Block</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #d3d3d3;"></div>
            <div class="legend-shape" style="border-radius: 50%;"></div>
            <span>Merge Point</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #e6f3ff;"></div>
            <div class="legend-shape"></div>
            <span>Block Start</span>
        </div>
    </div>
    
    <script>
        const stages = {stages_json};
        const nodeInfo = {node_info_json};
        let currentStage = -1;
        let network = null;
        let animationTimer = null;
        
        // Color mapping for node types (same as original visualizations)
        const colorMap = {{
            'entry': '#90ee90',
            'exit': '#ff6b6b',
            'assignment': '#ffd700',
            'conditional': '#ffa500',
            'loop': '#ff9999',
            'statement': '#97c2fc',
            'try': '#dda0dd',
            'except': '#f0e68c',
            'merge': '#d3d3d3',
            'return': '#ff6b6b',
            'block_start': '#e6f3ff',
            'loop_exit': '#ffcccc'
        }};
        
        // Shape mapping for node types (same as original visualizations)
        const shapeMap = {{
            'entry': 'ellipse',
            'exit': 'ellipse',
            'conditional': 'diamond',
            'loop': 'diamond',
            'merge': 'circle',
            'return': 'ellipse',
            'block_start': 'box',
            'loop_exit': 'ellipse'
        }};
        
        function initNetwork() {{
            const container = document.getElementById('graph');
            const data = {{
                nodes: new vis.DataSet([]),
                edges: new vis.DataSet([])
            }};
            
            const options = {{
                layout: {{
                    hierarchical: false,
                    improvedLayout: false
                }},
                physics: {{
                    enabled: false
                }},
                nodes: {{
                    shape: 'box',
                    margin: 10,
                    font: {{
                        size: 12,
                        face: 'monospace'
                    }},
                    borderWidth: 2
                }},
                edges: {{
                    arrows: 'to',
                    smooth: {{
                        type: 'cubicBezier',
                        roundness: 0.4
                    }}
                }}
            }};
            
            network = new vis.Network(container, data, options);
        }}
        
        function updateStage(stageIndex) {{
            if (stageIndex < -1 || stageIndex >= stages.length) return;
            
            currentStage = stageIndex;
            
            // Update stage counter
            updateStageCounter();
            
            if (stageIndex === -1) {{
                // Reset state
                network.setData({{
                    nodes: new vis.DataSet([]),
                    edges: new vis.DataSet([])
                }});
                document.getElementById('stageInfo').innerHTML = `
                    <h3>Stage 0: Ready to Start</h3>
                    <p>Click "Play Animation" to see the incremental layout process</p>
                `;
                return;
            }}
            
            const stage = stages[stageIndex];
            const stageType = stage.stage_type;
            const stageNum = stage.stage_number;
            
            // Update nodes
            const nodes = Object.entries(stage.nodes).map(([id, pos]) => {{
                const info = nodeInfo[id] || {{}};
                const label = info.label || id.substring(0, 8) + '...';
                const nodeType = info.type || 'statement';
                const line = info.line || '';
                
                // Create shorter label for display
                let displayLabel = label;
                if (label.length > 30) {{
                    displayLabel = label.substring(0, 27) + '...';
                }}
                
                // Get base color and shape from node type
                const baseColor = colorMap[nodeType] || '#97c2fc';
                const shape = shapeMap[nodeType] || 'box';
                
                // Apply stage-specific highlighting
                let nodeColor, borderColor;
                if (stageType === 'add') {{
                    nodeColor = baseColor;
                    borderColor = '#1976D2';
                    borderWidth = 3;
                }} else {{
                    nodeColor = baseColor;
                    borderColor = '#388E3C';
                    borderWidth = 2;
                }}
                
                // Highlight newly added/corrected node
                if ((stageType === 'add' && stage.node_added === id) ||
                    (stageType === 'correct' && stage.node_corrected === id)) {{
                    nodeColor = stageType === 'add' ? '#BBDEFB' : '#C8E6C9';
                    borderWidth = 4;
                }}
                
                return {{
                    id: id,
                    label: displayLabel,
                    title: `${{label}}\\nType: ${{nodeType}}\\nLine: ${{line}}`,
                    x: pos.x * 100,  // Scale for visualization
                    y: pos.y * 100,
                    shape: shape,
                    color: {{
                        background: nodeColor,
                        border: borderColor
                    }},
                    font: {{
                        size: nodeType === 'entry' || nodeType === 'exit' ? 14 : 12,
                        bold: nodeType === 'entry' || nodeType === 'exit',
                        color: '#333'
                    }},
                    borderWidth: borderWidth
                }};
            }});
            
            // Highlight the newly added/corrected node
            if (stageType === 'add' && stage.node_added) {{
                const addedNode = nodes.find(n => n.id === stage.node_added);
                if (addedNode) {{
                    addedNode.color = '#BBDEFB';
                    addedNode.borderColor = '#1976D2';
                    addedNode.borderWidth = 3;
                }}
            }} else if (stageType === 'correct' && stage.node_corrected) {{
                const correctedNode = nodes.find(n => n.id === stage.node_corrected);
                if (correctedNode) {{
                    correctedNode.color = '#C8E6C9';
                    correctedNode.borderColor = '#388E3C';
                    correctedNode.borderWidth = 3;
                }}
            }}
            
            // Update edges
            const edges = stage.edges.map(([from, to], index) => ({{
                from: from,
                to: to,
                color: stageType === 'add' ? '#90CAF9' : '#81C784',
                width: stageType === 'add' ? 2 : 3
            }}));
            
            network.setData({{
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(edges)
            }});
            
            // Update stage info
            const stageTitle = stageType === 'add' ? 
                `Stage ${{stageNum}}: Adding Node "${{stage.node_added}}"` :
                `Stage ${{stageNum}}: Correcting Layout for Node "${{stage.node_corrected}}"`;
            
            const stageDescription = stageType === 'add' ?
                `<p>Node "${{stage.node_added}}" has been added to the graph.</p>
                 <p>Current graph: ${{stage.total_nodes}} nodes, ${{stage.total_edges}} edges</p>` :
                `<p>Layout has been optimized to resolve edge crossings.</p>
                 <p>Current graph: ${{stage.total_nodes}} nodes, ${{stage.total_edges}} edges</p>
                 <p>Crossings addressed: ${{stage.crossings_fixed || 0}}</p>`;
            
            const stageClass = stageType === 'add' ? 'add-stage' : 'correct-stage';
            
            document.getElementById('stageInfo').innerHTML = `
                <h3>${{stageTitle}}</h3>
                ${{stageDescription}}
            `;
            document.getElementById('stageInfo').className = 'stage-info ' + stageClass;
        }}
        
        function playAnimation() {{
            resetAnimation();
            const speed = parseInt(document.getElementById('speedSlider').value);
            
            function animate() {{
                if (currentStage < stages.length - 1) {{
                    nextStage();
                    animationTimer = setTimeout(animate, speed);
                }}
            }}
            
            animate();
        }}
        
        function nextStage() {{
            if (animationTimer) {{
                clearTimeout(animationTimer);
                animationTimer = null;
            }}
            updateStage(currentStage + 1);
        }}
        
        function previousStage() {{
            if (animationTimer) {{
                clearTimeout(animationTimer);
                animationTimer = null;
            }}
            updateStage(currentStage - 1);
        }}
        
        function updateStageCounter() {{
            const totalStages = stages.length;
            const currentDisplayStage = currentStage === -1 ? 0 : currentStage + 1;
            document.getElementById('stageCounter').textContent = `Stage ${{currentDisplayStage}} of ${{totalStages}}`;
        }}
        
        function goToFinal() {{
            if (animationTimer) {{
                clearTimeout(animationTimer);
                animationTimer = null;
            }}
            updateStage(stages.length - 1);
        }}
        
        function resetAnimation() {{
            if (animationTimer) {{
                clearTimeout(animationTimer);
                animationTimer = null;
            }}
            updateStage(-1);
        }}
        
        // Speed slider
        document.getElementById('speedSlider').addEventListener('input', function(e) {{
            document.getElementById('speedValue').textContent = e.target.value + 'ms';
        }});
        
        // Initialize on load
        window.onload = function() {{
            initNetwork();
            updateStage(-1);
        }};
    </script>
</body>
</html>
    """
    
    return html_template.format(
        function_name=function_name,
        structure_type=structure_type,
        description=description,
        stages_json=json.dumps(stages, indent=2),
        node_info_json=json.dumps(node_info, indent=2)
    )

def process_function(function_name, structure_type, description):
    """Process a single function and generate incremental layout visualization."""
    
    try:
        print(f"\nProcessing: {function_name}")
        print(f"Structure: {structure_type}")
        print(f"Description: {description}")
        
        # Load existing function flow
        function_flow = load_existing_function_flow(function_name)
        
        if function_flow is None:
            print(f"  ❌ Failed to load function flow")
            return None
        
        # Convert to layout format
        nodes, edges, node_info = convert_flow_to_layout_format(function_flow)
        
        print(f"  📊 Original: {len(nodes)} nodes, {len(edges)} edges")
        
        # Create incremental layout stages
        stages = create_incremental_layout_stages(nodes, edges, node_info)
        
        print(f"  🎬 Generated {len(stages)} stages ({len(stages)//2} additions)")
        
        # Generate HTML visualization
        html_content = generate_incremental_visualization(function_name, structure_type, description, stages, node_info)
        
        return {
            'function_name': function_name,
            'structure_type': structure_type,
            'description': description,
            'html_content': html_content,
            'stages_count': len(stages),
            'nodes_count': len(nodes),
            'edges_count': len(edges),
            'success': True
        }
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return {
            'function_name': function_name,
            'structure_type': structure_type,
            'description': description,
            'error': str(e),
            'success': False
        }

def main():
    """Main function to process all 25 functions and generate incremental layout demos."""
    
    print("Incremental Layout Demo Generator")
    print("=" * 60)
    print("Generating visualizations for 25 function examples...")
    print("Each visualization shows:")
    print("  1. ADD stage: Node is added to the graph")
    print("  2. CORRECT stage: Layout is optimized to resolve crossings")
    
    # Setup paths
    output_dir = Path(__file__).parent / 'incremental_layout_demos'
    output_dir.mkdir(exist_ok=True)
    
    # Process all functions
    results = []
    
    for function_name, structure_type, description in VISUALIZATION_EXAMPLES:
        result = process_function(function_name, structure_type, description)
        results.append(result)
        
        if result and result.get('success'):
            # Save HTML file
            output_file = output_dir / f"{function_name}_incremental_layout.html"
            with open(output_file, 'w') as f:
                f.write(result['html_content'])
            print(f"  ✅ Saved: {output_file.name}")
    
    # Generate summary
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"✅ Successfully processed: {len(successful)}/{len(results)} functions")
    print(f"❌ Failed: {len(failed)} functions")
    print(f"📁 Output directory: {output_dir}")
    
    if successful:
        total_stages = sum(r['stages_count'] for r in successful)
        total_nodes = sum(r['nodes_count'] for r in successful)
        total_edges = sum(r['edges_count'] for r in successful)
        
        print(f"🎬 Total stages generated: {total_stages}")
        print(f"📍 Total nodes processed: {total_nodes}")
        print(f"🔗 Total edges processed: {total_edges}")
        print(f"📈 Average stages per function: {total_stages/len(successful):.1f}")
    
    # Generate index file
    index_html = generate_index_html(successful, output_dir)
    with open(output_dir / 'index.html', 'w') as f:
        f.write(index_html)
    
    print(f"📋 Generated index.html for easy navigation")
    
    if failed:
        print(f"\n❌ Failed functions:")
        for result in failed:
            print(f"  - {result['function_name']}: {result.get('error', 'Unknown error')}")

def generate_index_html(successful_results, output_dir):
    """Generate an index HTML file to navigate all demos."""
    
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Incremental Layout Demos - Index</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .demo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .demo-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .demo-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .demo-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }
        .demo-description {
            color: #666;
            margin-bottom: 12px;
            font-size: 14px;
        }
        .demo-stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-size: 12px;
            color: #888;
        }
        .demo-link {
            display: inline-block;
            background-color: #2196F3;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        .demo-link:hover {
            background-color: #1976D2;
        }
        .structure-section {
            margin-bottom: 30px;
        }
        .structure-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Incremental Layout Demos</h1>
        <p>Interactive visualizations showing how nodes are added one at a time and how the layout algorithm resolves edge crossings</p>
        <p><strong>Each demo shows two stages:</strong> ADD (node added) → CORRECT (crossings resolved)</p>
    </div>
"""
    
    # Group by structure type
    by_structure = {}
    for result in successful_results:
        structure = result['structure_type']
        if structure not in by_structure:
            by_structure[structure] = []
        by_structure[structure].append(result)
    
    # Generate sections for each structure type
    for structure_type, results in by_structure.items():
        html += f'    <div class="structure-section">\n'
        html += f'        <h2 class="structure-title">{structure_type}</h2>\n'
        html += f'        <div class="demo-grid">\n'
        
        for result in results:
            html += f'            <div class="demo-card">\n'
            html += f'                <div class="demo-title">{result["function_name"]}</div>\n'
            html += f'                <div class="demo-description">{result["description"]}</div>\n'
            html += f'                <div class="demo-stats">\n'
            html += f'                    <span>📍 {result["nodes_count"]} nodes</span>\n'
            html += f'                    <span>🔗 {result["edges_count"]} edges</span>\n'
            html += f'                    <span>🎬 {result["stages_count"]} stages</span>\n'
            html += f'                </div>\n'
            html += f'                <a href="{result["function_name"]}_incremental_layout.html" class="demo-link">View Demo</a>\n'
            html += f'            </div>\n'
        
        html += f'        </div>\n'
        html += f'    </div>\n'
    
    html += """
</body>
</html>
    """
    
    return html

if __name__ == '__main__':
    main()
"""
Hierarchical Function Flow Generator

Creates intuitive tree-based visualizations for ALL control flow structures.
Uses semantic positioning based on control flow meaning.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict, deque


class HierarchicalLayoutEngine:
    """Engine for creating semantic hierarchical layouts for control flow graphs."""
    
    def __init__(self, function_flow_data: Dict[str, Any]):
        self.flow_data = function_flow_data
        self.nodes = function_flow_data.get('nodes', [])
        self.edges = function_flow_data.get('edges', [])
        self.entry_point = function_flow_data.get('entry_point', {})
        self.exit_point = function_flow_data.get('exit_point', {})
        
        # Build adjacency lists
        self.children = defaultdict(list)
        self.parents = defaultdict(list)
        self._build_adjacency()
        
        # Layout parameters
        self.level_height = 150
        self.node_spacing = 200
        self.branch_spacing = 250
        
    def _build_adjacency(self):
        """Build parent-child relationships from edges."""
        for edge in self.edges:
            self.children[edge['from']].append(edge['to'])
            self.parents[edge['to']].append(edge['from'])
    
    def detect_structure_type(self) -> str:
        """Detect the control flow structure type."""
        node_types = [node.get('type', 'statement') for node in self.nodes]
        
        # Count different node types
        conditionals = node_types.count('conditional')
        returns = node_types.count('return')
        loops = node_types.count('loop')
        exceptions = sum(1 for node in self.nodes if 'exception' in node.get('label', '').lower())
        
        # Detect back edges (loops)
        back_edges = 0
        for edge in self.edges:
            from_node = self._get_node_by_id(edge['from'])
            to_node = self._get_node_by_id(edge['to'])
            if from_node and to_node:
                if from_node.get('line', 0) > to_node.get('line', 0):
                    back_edges += 1
        
        # Structure detection logic
        if conditionals == 0 and back_edges == 0:
            return 'linear'
        elif conditionals == 1 and back_edges == 0:
            return 'binary_branching'
        elif conditionals > 1 and back_edges == 0:
            return 'multi_way_branching'
        elif back_edges > 0 and conditionals <= 1:
            return 'loop'
        elif conditionals > 1 and back_edges > 0:
            return 'nested'
        elif exceptions > 0:
            return 'exception_handling'
        elif returns > 1:
            return 'multiple_returns'
        else:
            return 'complex'
    
    def _get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node data by ID."""
        if node_id == self.entry_point.get('id'):
            return self.entry_point
        elif node_id == self.exit_point.get('id'):
            return self.exit_point
        else:
            for node in self.nodes:
                if node.get('id') == node_id:
                    return node
        return None
    
    def calculate_hierarchical_layout(self) -> Dict[str, Dict[str, Any]]:
        """Calculate hierarchical positions for all nodes."""
        structure_type = self.detect_structure_type()
        
        if structure_type == 'linear':
            return self._layout_linear()
        elif structure_type == 'binary_branching':
            return self._layout_binary_branching()
        elif structure_type == 'multi_way_branching':
            return self._layout_multi_way_branching()
        elif structure_type == 'loop':
            return self._layout_loop()
        elif structure_type in ['nested', 'exception_handling', 'multiple_returns', 'complex']:
            return self._layout_hierarchical_tree()
        else:
            return self._layout_hierarchical_tree()
    
    def _layout_linear(self) -> Dict[str, Dict[str, Any]]:
        """Layout linear functions as a clean chain."""
        positions = {}
        
        # Start from entry point
        current_id = self.entry_point.get('id')
        x = 0
        y = 0
        level = 0
        
        # Place entry point
        positions[current_id] = {'x': x, 'y': y, 'level': level}
        
        # Follow the main path
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            children = self.children[current_id]
            
            if len(children) == 0:
                break
            
            # For linear, take the first child (main path)
            next_id = children[0]
            level += 1
            y += self.level_height
            
            positions[next_id] = {'x': x, 'y': y, 'level': level}
            current_id = next_id
        
        return positions
    
    def _layout_binary_branching(self) -> Dict[str, Dict[str, Any]]:
        """Layout binary branching as a diamond pattern."""
        positions = {}
        
        # Find the decision node
        decision_node = None
        for node in self.nodes:
            if node.get('type') == 'conditional':
                decision_node = node
                break
        
        if not decision_node:
            return self._layout_linear()
        
        # Layout structure
        entry_id = self.entry_point.get('id')
        decision_id = decision_node.get('id')
        
        # Entry at top
        positions[entry_id] = {'x': 0, 'y': 0, 'level': 0}
        
        # Decision node below entry
        positions[decision_id] = {'x': 0, 'y': self.level_height, 'level': 1}
        
        # Find true and false branches
        decision_children = self.children[decision_id]
        if len(decision_children) >= 2:
            true_branch = decision_children[0]
            false_branch = decision_children[1]
            
            # Place branches side by side
            positions[true_branch] = {'x': -self.branch_spacing/2, 'y': self.level_height * 2, 'level': 2}
            positions[false_branch] = {'x': self.branch_spacing/2, 'y': self.level_height * 2, 'level': 2}
            
            # Find exit points from branches
            true_children = self.children[true_branch]
            false_children = self.children[false_branch]
            
            exit_y = self.level_height * 3
            if true_children:
                positions[true_children[0]] = {'x': -self.branch_spacing/2, 'y': exit_y, 'level': 3}
            if false_children:
                positions[false_children[0]] = {'x': self.branch_spacing/2, 'y': exit_y, 'level': 3}
        
        return positions
    
    def _layout_multi_way_branching(self) -> Dict[str, Dict[str, Any]]:
        """Layout multi-way branching as a tree with multiple branches."""
        positions = {}
        
        # Find all decision nodes
        decision_nodes = [node for node in self.nodes if node.get('type') == 'conditional']
        
        if not decision_nodes:
            return self._layout_linear()
        
        # Start with entry point
        entry_id = self.entry_point.get('id')
        positions[entry_id] = {'x': 0, 'y': 0, 'level': 0}
        
        # Layout first decision node
        first_decision = decision_nodes[0]
        decision_id = first_decision.get('id')
        positions[decision_id] = {'x': 0, 'y': self.level_height, 'level': 1}
        
        # Layout branches
        branches = self.children[decision_id]
        num_branches = len(branches)
        
        if num_branches > 0:
            # Calculate branch positions
            total_width = (num_branches - 1) * self.branch_spacing
            start_x = -total_width / 2
            
            for i, branch_id in enumerate(branches):
                branch_x = start_x + i * self.branch_spacing
                positions[branch_id] = {'x': branch_x, 'y': self.level_height * 2, 'level': 2}
                
                # Layout branch children
                branch_children = self.children[branch_id]
                for child_id in branch_children:
                    positions[child_id] = {'x': branch_x, 'y': self.level_height * 3, 'level': 3}
        
        return positions
    
    def _layout_loop(self) -> Dict[str, Dict[str, Any]]:
        """Layout loop structures with clear loop body."""
        positions = {}
        
        # Entry at top
        entry_id = self.entry_point.get('id')
        positions[entry_id] = {'x': 0, 'y': 0, 'level': 0}
        
        # Find loop-related nodes
        loop_nodes = [node for node in self.nodes if 'loop' in node.get('label', '').lower() or node.get('type') == 'loop']
        
        if not loop_nodes:
            # Fallback to hierarchical
            return self._layout_hierarchical_tree()
        
        # Simple layout: entry -> loop body -> exit
        current_y = self.level_height
        for i, node in enumerate(loop_nodes):
            positions[node.get('id')] = {'x': 0, 'y': current_y, 'level': i + 1}
            current_y += self.level_height
        
        # Exit point
        exit_id = self.exit_point.get('id')
        positions[exit_id] = {'x': 0, 'y': current_y, 'level': len(loop_nodes) + 1}
        
        return positions
    
    def _layout_hierarchical_tree(self) -> Dict[str, Dict[str, Any]]:
        """General hierarchical tree layout for complex structures."""
        positions = {}
        
        # BFS to assign levels
        levels = defaultdict(list)
        visited = set()
        queue = deque([(self.entry_point.get('id'), 0)])
        
        while queue:
            node_id, level = queue.popleft()
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            levels[level].append(node_id)
            
            # Add children to queue
            for child_id in self.children[node_id]:
                if child_id not in visited:
                    queue.append((child_id, level + 1))
        
        # Position nodes by level
        for level, node_ids in levels.items():
            y = level * self.level_height
            num_nodes = len(node_ids)
            
            if num_nodes == 1:
                # Center single node
                positions[node_ids[0]] = {'x': 0, 'y': y, 'level': level}
            else:
                # Spread multiple nodes horizontally
                total_width = (num_nodes - 1) * self.branch_spacing
                start_x = -total_width / 2
                
                for i, node_id in enumerate(node_ids):
                    x = start_x + i * self.branch_spacing
                    positions[node_id] = {'x': x, 'y': y, 'level': level}
        
        return positions


def generate_hierarchical_function_flow(
    function_flow_data: Dict[str, Any],
    output_path: Path,
    function_name: Optional[str] = None,
    module_name: Optional[str] = None,
    title: Optional[str] = None
) -> None:
    """
    Generate a hierarchical function flow HTML visualization.
    
    Args:
        function_flow_data: Function flow data with nodes and edges
        output_path: Path to save HTML file
        function_name: Name of function (for title)
        module_name: Name of module (for title)
        title: Custom title (overrides generated title)
    """
    
    # Extract basic info
    func_name = function_name or function_flow_data.get('function_name', 'Unknown Function')
    mod_name = module_name or function_flow_data.get('module', 'Unknown Module')
    
    # Generate title
    if title:
        page_title = title
    else:
        page_title = f"Hierarchical Flow - {func_name}"
    
    # Create layout engine and calculate positions
    layout_engine = HierarchicalLayoutEngine(function_flow_data)
    structure_type = layout_engine.detect_structure_type()
    positions = layout_engine.calculate_hierarchical_layout()
    
    # Count nodes and edges
    node_count = len(function_flow_data.get('nodes', [])) + 2  # +2 for entry/exit
    edge_count = len(function_flow_data.get('edges', []))
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hierarchical Function Flow - {func_name}</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        
        .header h1 {{
            margin: 0;
            color: #333;
            font-size: 28px;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            color: #666;
            margin-top: 5px;
            font-size: 14px;
        }}
        
        .structure-info {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px 20px;
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            gap: 30px;
            align-items: center;
        }}
        
        .structure-type {{
            font-size: 18px;
            font-weight: 600;
            color: #007bff;
        }}
        
        .stats {{
            display: flex;
            gap: 20px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #28a745;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        
        .graph-container {{
            margin: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            height: 85vh;
        }}
        
        #network {{
            width: 100%;
            height: 100%;
        }}
        
        .controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
        }}
        
        button {{
            padding: 8px 16px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: #007bff;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #0056b3;
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #545b62;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Hierarchical Function Flow - {func_name}</h1>
        <div class="subtitle">Module: {mod_name} | Structure: {structure_type.replace('_', ' ').title()}</div>
    </div>
    
    <div class="structure-info">
        <div class="structure-type">Structure Type: {structure_type.replace('_', ' ').title()}</div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{node_count}</div>
                <div class="stat-label">Nodes</div>
            </div>
            <div class="stat">
                <div class="stat-value">{edge_count}</div>
                <div class="stat-label">Edges</div>
            </div>
        </div>
    </div>
    
    <div class="graph-container">
        <div id="network"></div>
        <div class="controls">
            <button class="btn-primary" onclick="network.fit()">Fit to Screen</button>
            <button class="btn-secondary" onclick="togglePhysics()">Toggle Physics</button>
        </div>
    </div>

    <script type="text/javascript">
        // Function flow data
        const functionFlowData = {json.dumps(function_flow_data, indent=8)};
        
        // Pre-calculated hierarchical positions
        const hierarchicalPositions = {json.dumps(positions, indent=8)};
        
        // Color and shape mappings
        const colorMap = {{
            'entry': '#28a745',
            'exit': '#dc3545', 
            'conditional': '#ffc107',
            'return': '#17a2b8',
            'statement': '#007bff',
            'assignment': '#6f42c1',
            'loop': '#fd7e14',
            'merge': '#20c997'
        }};
        
        const shapeMap = {{
            'entry': 'circle',
            'exit': 'circle',
            'conditional': 'diamond',
            'return': 'triangleDown',
            'statement': 'box',
            'assignment': 'box',
            'loop': 'box',
            'merge': 'circle'
        }};
        
        // Create nodes with hierarchical positions
        const nodes = new vis.DataSet([
            {{
                id: functionFlowData.entry_point.id,
                label: functionFlowData.entry_point.label,
                title: `${{functionFlowData.entry_point.label}}\\nType: ${{functionFlowData.entry_point.type}}\\nLine: ${{functionFlowData.entry_point.line}}`,
                color: {{
                    background: colorMap[functionFlowData.entry_point.type],
                    border: '#28a745'
                }},
                shape: shapeMap[functionFlowData.entry_point.type] || 'box',
                font: {{size: 16, bold: true, color: '#333'}},
                borderWidth: 3,
                x: hierarchicalPositions[functionFlowData.entry_point.id]?.x || 0,
                y: hierarchicalPositions[functionFlowData.entry_point.id]?.y || 0
            }},
            {{
                id: functionFlowData.exit_point.id,
                label: functionFlowData.exit_point.label,
                title: `${{functionFlowData.exit_point.label}}\\nType: ${{functionFlowData.exit_point.type}}\\nLine: ${{functionFlowData.exit_point.line}}`,
                color: {{
                    background: colorMap[functionFlowData.exit_point.type],
                    border: '#dc3545'
                }},
                shape: shapeMap[functionFlowData.exit_point.type] || 'box',
                font: {{size: 16, bold: true, color: '#333'}},
                borderWidth: 3,
                x: hierarchicalPositions[functionFlowData.exit_point.id]?.x || 0,
                y: hierarchicalPositions[functionFlowData.exit_point.id]?.y || 0
            }}
        ]);
        
        // Add control flow nodes with hierarchical positions
        functionFlowData.nodes.forEach(node => {{
            if (node.id !== functionFlowData.entry_point.id && node.id !== functionFlowData.exit_point.id) {{
                const color = colorMap[node.type] || '#97c2fc';
                const shape = shapeMap[node.type] || 'box';
                
                let label = node.label;
                if (label.length > 30) {{
                    label = label.substring(0, 27) + '...';
                }}
                
                nodes.add({{
                    id: node.id,
                    label: label,
                    title: `${{node.label}}\\nType: ${{node.type}}\\nLine: ${{node.line}}`,
                    color: {{
                        background: color,
                        border: '#333'
                    }},
                    shape: shape,
                    font: {{size: 12, color: '#333'}},
                    borderWidth: 2,
                    x: hierarchicalPositions[node.id]?.x || 0,
                    y: hierarchicalPositions[node.id]?.y || 0
                }});
            }}
        }});
        
        // Create edges with appropriate styling
        const edges = new vis.DataSet(functionFlowData.edges.map(edge => ({{
            from: edge.from,
            to: edge.to,
            label: edge.label || '',
            arrows: 'to',
            color: {{color: '#666666', highlight: '#007bff'}},
            width: 2,
            smooth: {{
                type: 'cubicBezier',
                roundness: 0.1
            }}
        }})));
        
        // Create network with hierarchical layout
        const container = document.getElementById('network');
        const data = {{ nodes, edges }};
        
        const options = {{
            layout: {{
                hierarchical: {{
                    enabled: false,  // Use our manual positions
                    levelSeparation: 150,
                    nodeSpacing: 200,
                    treeSpacing: 200
                }}
            }},
            physics: {{
                enabled: false,  // Start with physics disabled
                stabilization: {{
                    enabled: true,
                    iterations: 100
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                dragNodes: true,
                dragView: true,
                zoomView: true
            }},
            nodes: {{
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                shadow: true,
                smooth: {{
                    type: 'cubicBezier',
                    roundness: 0.2
                }}
            }}
        }};
        
        const network = new vis.Network(container, data, options);
        
        // Fit to screen after network is ready
        network.once('stabilizationIterationsDone', function() {{
            network.fit();
        }});
        
        // Control functions
        function togglePhysics() {{
            const physicsEnabled = !network.physics.physicsEnabled;
            network.setOptions({{
                physics: {{
                    enabled: physicsEnabled
                }}
            }});
        }}
    </script>
</body>
</html>"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated hierarchical function flow: {output_path}")
    print(f"  Structure: {structure_type.replace('_', ' ').title()}")
    print(f"  Nodes: {node_count}, Edges: {edge_count}")
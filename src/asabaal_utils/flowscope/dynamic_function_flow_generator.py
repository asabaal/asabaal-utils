"""
Dynamic Function Flow Generator

Creates standalone HTML visualizations for function flow graphs with the same
look and feel as FlowScope, but with fully interactive dynamic graphs.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def generate_dynamic_function_flow(
    function_flow_data: Dict[str, Any],
    output_path: Path,
    function_name: Optional[str] = None,
    module_name: Optional[str] = None,
    title: Optional[str] = None
) -> None:
    """
    Generate a standalone dynamic function flow HTML visualization.
    
    Args:
        function_flow_data: Function flow data with nodes and edges
        output_path: Path to save the HTML file
        function_name: Name of the function (for title)
        module_name: Name of the module (for title)
        title: Custom title (overrides generated title)
    """
    
    # Extract basic info
    func_name = function_name or function_flow_data.get('function_name', 'Unknown Function')
    mod_name = module_name or function_flow_data.get('module', 'Unknown Module')
    
    # Generate title
    if title:
        page_title = title
    else:
        page_title = f"{func_name} function from {mod_name} module"
    
    # Count nodes and edges
    node_count = len(function_flow_data.get('nodes', [])) + 2  # +2 for entry/exit
    edge_count = len(function_flow_data.get('edges', []))
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic Function Flow - {func_name}</title>
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
        
        .controls {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px 20px;
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .control-group label {{
            font-size: 12px;
            color: #555;
            font-weight: 500;
        }}
        
        button {{
            padding: 8px 16px;
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
        
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #1e7e34;
        }}
        
        select {{
            padding: 6px 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        .graph-container {{
            margin: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        
        .graph-header {{
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }}
        
        .graph-title {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin: 0;
        }}
        
        .graph-metadata {{
            display: flex;
            gap: 20px;
            align-items: center;
            font-size: 14px;
            color: #666;
        }}
        
        .metadata-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .metadata-label {{
            font-weight: 500;
        }}
        
        .metadata-value {{
            color: #007bff;
            font-weight: 600;
        }}
        
        .toggle-button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.2s;
        }}
        
        .toggle-button:hover {{
            background: #0056b3;
        }}
        
        .toggle-button.collapsed {{
            background: #6c757d;
        }}
        
        .resize-handle {{
            background: #e9ecef;
            border: 1px solid #dee2e6;
            height: 10px;
            cursor: ns-resize;
            position: relative;
            flex-shrink: 0;
        }}
        
        .resize-handle::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 2px;
            background: #6c757d;
            border-radius: 1px;
        }}
        
        .resize-handle:hover {{
            background: #dee2e6;
        }}
        
        #network {{
            height: 60vh;
            min-height: 400px;
            flex: 1;
            position: relative;
        }}
        
        .info-panel {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px 20px;
            margin: 0 20px 20px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        
        .legend {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #ccc;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            max-width: 250px;
        }}
        
        .legend h4 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 14px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 6px;
            font-size: 12px;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            margin-right: 8px;
            border: 1px solid #666;
        }}
        
        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 400px;
            font-size: 18px;
            color: #666;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 10000;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dynamic Function Flow Visualization</h1>
        <div class="subtitle">{func_name} function from {mod_name} module • FlowScope Analysis</div>
    </div>
    
    <div class="controls">
        <div class="control-group">
            <label>Layout:</label>
            <select id="layoutSelect">
                <option value="free">Free Form (Default)</option>
                <option value="hierarchical">Hierarchical</option>
                <option value="physics">Physics-based</option>
                <option value="circular">Circular</option>
            </select>
        </div>
        
        <div class="control-group">
            <button class="btn-primary" onclick="changeLayout()">Apply Layout</button>
            <button class="btn-secondary" onclick="resetZoom()">Reset Zoom</button>
            <button class="btn-success" onclick="togglePhysics()">Toggle Physics</button>
        </div>
        
        <div class="control-group">
            <label>Node Size:</label>
            <select id="nodeSizeSelect">
                <option value="small">Small</option>
                <option value="medium" selected>Medium</option>
                <option value="large">Large</option>
            </select>
        </div>
        
        <div class="control-group">
            <button class="btn-secondary" onclick="exportImage()">Export Image</button>
        </div>
    </div>
    
    <div class="info-panel">
        <h3 style="margin: 0; color: #333;">Function Information</h3>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{node_count}</div>
                <div class="stat-label">Control Flow Nodes</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{edge_count}</div>
                <div class="stat-label">Flow Edges</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{function_flow_data.get('file_path', 'Unknown').split('/')[-1]}</div>
                <div class="stat-label">Source File</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{mod_name}</div>
                <div class="stat-label">Module</div>
            </div>
        </div>
    </div>
    
    <div class="graph-container">
        <div class="graph-header">
            <h2 class="graph-title" id="graph-title">{func_name} Function Flow</h2>
            <div class="graph-metadata" id="graph-metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Module:</span>
                    <span class="metadata-value">{mod_name}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Nodes:</span>
                    <span class="metadata-value" id="node-count">{node_count}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Edges:</span>
                    <span class="metadata-value" id="edge-count">{edge_count}</span>
                </div>
                <button class="toggle-button" id="toggle-metadata" onclick="toggleMetadata()">Hide Info</button>
            </div>
        </div>
        <div class="resize-handle" id="resize-handle"></div>
        <div id="network" class="loading">Loading function flow graph...</div>
    </div>
    
    <div class="legend">
        <h4>Node Types</h4>
        <div class="legend-item">
            <div class="legend-color" style="background: #90ee90;"></div>
            <span>Entry Point</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff6b6b;"></div>
            <span>Exit Point</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffd700;"></div>
            <span>Assignment</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffa500;"></div>
            <span>Conditional</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff9999;"></div>
            <span>Loop</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #97c2fc;"></div>
            <span>Statement</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #dda0dd;"></div>
            <span>Try Block</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #f0e68c;"></div>
            <span>Except Block</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #d3d3d3;"></div>
            <span>Merge Point</span>
        </div>
    </div>
    
    <script>
        // Function flow data for {func_name} function
        const functionFlowData = {json.dumps(function_flow_data, indent=8)};
        
        let network = null;
        let physicsEnabled = false;
        
        // Color mapping for node types
        const colorMap = {{
            'entry': '#90ee90',
            'exit': '#ff6b6b',
            'assignment': '#ffd700',
            'conditional': '#ffa500',
            'loop': '#ff9999',
            'statement': '#97c2fc',
            'return': '#90ee90',
            'try': '#dda0dd',
            'except': '#f0e68c',
            'merge': '#d3d3d3'
        }};
        
        // Shape mapping for node types
        const shapeMap = {{
            'entry': 'ellipse',
            'exit': 'ellipse',
            'conditional': 'diamond',
            'loop': 'diamond',
            'merge': 'circle'
        }};
        
        function initializeNetwork() {{
            const container = document.getElementById('network');
            
            // Create nodes
            const nodes = new vis.DataSet([
                {{
                    id: functionFlowData.entry_point.id,
                    label: functionFlowData.entry_point.label,
                    title: `${{functionFlowData.entry_point.label}}\\nType: ${{functionFlowData.entry_point.type}}\\nLine: ${{functionFlowData.entry_point.line}}`,
                    color: colorMap[functionFlowData.entry_point.type],
                    shape: shapeMap[functionFlowData.entry_point.type] || 'box',
                    font: {{size: 16, bold: true, color: '#333'}},
                    borderWidth: 3,
                    borderColor: '#28a745'
                }},
                {{
                    id: functionFlowData.exit_point.id,
                    label: functionFlowData.exit_point.label,
                    title: `${{functionFlowData.exit_point.label}}\\nType: ${{functionFlowData.exit_point.type}}\\nLine: ${{functionFlowData.exit_point.line}}`,
                    color: colorMap[functionFlowData.exit_point.type],
                    shape: shapeMap[functionFlowData.exit_point.type] || 'box',
                    font: {{size: 16, bold: true, color: '#333'}},
                    borderWidth: 3,
                    borderColor: '#dc3545'
                }}
            ]);
            
            // Add control flow nodes
            functionFlowData.nodes.forEach(node => {{
                if (node.id !== functionFlowData.entry_point.id && node.id !== functionFlowData.exit_point.id) {{
                    const color = colorMap[node.type] || '#97c2fc';
                    const shape = shapeMap[node.type] || 'box';
                    
                    let label = node.label;
                    if (label.length > 50) {{
                        label = label.substring(0, 47) + '...';
                    }}
                    
                    nodes.add({{
                        id: node.id,
                        label: label,
                        title: `${{node.label}}\\nType: ${{node.type}}\\nLine: ${{node.line}}`,
                        color: color,
                        shape: shape,
                        font: {{size: 12, color: '#333'}},
                        borderWidth: 1,
                        borderColor: '#666666'
                    }});
                }}
            }});
            
            // Create edges
            const edges = new vis.DataSet(functionFlowData.edges.map(edge => ({{
                from: edge.from,
                to: edge.to,
                label: edge.label || '',
                arrows: 'to',
                color: {{color: '#666666', highlight: '#007bff'}},
                width: 2,
                smooth: {{
                    type: 'cubicBezier',
                    roundness: 0.2
                }}
            }})));
            
            // Create network
            const data = {{ nodes: nodes, edges: edges }};
            
            const options = {{
                layout: {{
                    randomSeed: 42,
                    improvedLayout: true
                }},
                physics: {{
                    enabled: false
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 200,
                    zoomView: true,
                    dragView: true,
                    navigationButtons: true,
                    keyboard: true
                }},
                nodes: {{
                    borderWidth: 1,
                    borderColor: '#666666',
                    font: {{color: '#333'}},
                    shadow: {{
                        enabled: true,
                        color: 'rgba(0,0,0,0.1)',
                        size: 5,
                        x: 2,
                        y: 2
                    }}
                }},
                edges: {{
                    smooth: {{
                        type: 'cubicBezier',
                        roundness: 0.2
                    }},
                    shadow: {{
                        enabled: true,
                        color: 'rgba(0,0,0,0.1)',
                        size: 3,
                        x: 1,
                        y: 1
                    }}
                }}
            }};
            
            network = new vis.Network(container, data, options);
            
            // Make network globally accessible
            window.network = network;
            
            // Fit network after stabilization
            network.once('stabilized', function() {{
                network.fit({{
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }});
            
            // Add click event for node details
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    const nodeId = params.nodes[0];
                    const node = nodes.get(nodeId);
                    console.log('Clicked node:', node);
                }}
            }});
        }}
        
        function changeLayout() {{
            const layoutType = document.getElementById('layoutSelect').value;
            const nodeSize = document.getElementById('nodeSizeSelect').value;
            
            let nodeSizeValue = 20;
            if (nodeSize === 'small') nodeSizeValue = 15;
            else if (nodeSize === 'large') nodeSizeValue = 30;
            
            const options = {{
                layout: {{
                    randomSeed: 42,
                    improvedLayout: true
                }},
                physics: {{ enabled: physicsEnabled }},
                nodes: {{ size: nodeSizeValue }}
            }};
            
            if (layoutType === 'hierarchical') {{
                options.layout = {{
                    hierarchical: {{
                        direction: 'UD',
                        sortMethod: 'directed',
                        levelSeparation: 150,
                        nodeSpacing: 200
                    }}
                }};
                options.physics = {{ enabled: false }};
            }} else if (layoutType === 'physics') {{
                options.physics = {{
                    enabled: true,
                    stabilization: {{ iterations: 100 }}
                }};
            }} else if (layoutType === 'circular') {{
                options.physics = {{ enabled: false }};
                
                // Manually arrange nodes in a circle
                const nodeIds = network.body.data.nodes.getIds();
                const radius = 300;
                const center = {{ x: 0, y: 0 }};
                
                nodeIds.forEach((id, index) => {{
                    const angle = (2 * Math.PI * index) / nodeIds.length;
                    const x = center.x + radius * Math.cos(angle);
                    const y = center.y + radius * Math.sin(angle);
                    network.moveNode(id, x, y);
                }});
            }}
            
            network.setOptions(options);
        }}
        
        function resetZoom() {{
            network.fit({{
                animation: {{
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
        }}
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{
                physics: {{
                    enabled: physicsEnabled,
                    stabilization: {{ iterations: physicsEnabled ? 100 : 0 }}
                }}
            }});
        }}
        
        function toggleMetadata() {{
            const metadata = document.getElementById('graph-metadata');
            const button = document.getElementById('toggle-metadata');
            const network = document.getElementById('network');
            
            if (metadata.style.display === 'none') {{
                metadata.style.display = 'flex';
                button.textContent = 'Hide Info';
                button.classList.remove('collapsed');
                network.style.height = '60vh';
            }} else {{
                metadata.style.display = 'none';
                button.textContent = 'Show Info';
                button.classList.add('collapsed');
                network.style.height = '75vh';
            }}
            
            // Trigger network resize
            if (window.network) {{
                window.network.redraw();
                window.network.fit();
            }}
        }}
        
        function exportImage() {{
            // Create a canvas element
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Get network canvas
            const networkCanvas = network.canvas.frame.canvas;
            
            // Set canvas size
            canvas.width = networkCanvas.width;
            canvas.height = networkCanvas.height;
            
            // Draw network canvas to our canvas
            ctx.drawImage(networkCanvas, 0, 0);
            
            // Convert to blob and download
            canvas.toBlob(function(blob) {{
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '{func_name}_function_flow.png';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }});
        }}
        
        function makeResizable() {{
            const resizeHandle = document.getElementById('resize-handle');
            const networkContainer = document.getElementById('network');
            const graphContainer = document.querySelector('.graph-container');
            let isResizing = false;
            let startY = 0;
            let startHeight = 0;
            
            resizeHandle.addEventListener('mousedown', (e) => {{
                isResizing = true;
                startY = e.clientY;
                startHeight = networkContainer.offsetHeight;
                document.body.style.cursor = 'ns-resize';
                document.body.style.userSelect = 'none';
                e.preventDefault();
            }});
            
            document.addEventListener('mousemove', (e) => {{
                if (!isResizing) return;
                
                const deltaY = e.clientY - startY;
                const newHeight = Math.max(200, startHeight + deltaY); // Minimum 200px height
                const containerHeight = graphContainer.offsetHeight;
                const headerHeight = graphContainer.querySelector('.graph-header').offsetHeight;
                const handleHeight = resizeHandle.offsetHeight;
                const availableHeight = containerHeight - headerHeight - handleHeight;
                
                if (newHeight <= availableHeight) {{
                    networkContainer.style.height = newHeight + 'px';
                    if (window.network) {{
                        window.network.redraw();
                    }}
                }}
            }});
            
            document.addEventListener('mouseup', () => {{
                if (isResizing) {{
                    isResizing = false;
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                    if (window.network) {{
                        window.network.fit();
                    }}
                }}
            }});
            
            // Touch support for mobile
            resizeHandle.addEventListener('touchstart', (e) => {{
                isResizing = true;
                startY = e.touches[0].clientY;
                startHeight = networkContainer.offsetHeight;
                e.preventDefault();
            }});
            
            document.addEventListener('touchmove', (e) => {{
                if (!isResizing) return;
                
                const deltaY = e.touches[0].clientY - startY;
                const newHeight = Math.max(200, startHeight + deltaY);
                const containerHeight = graphContainer.offsetHeight;
                const headerHeight = graphContainer.querySelector('.graph-header').offsetHeight;
                const handleHeight = resizeHandle.offsetHeight;
                const availableHeight = containerHeight - headerHeight - handleHeight;
                
                if (newHeight <= availableHeight) {{
                    networkContainer.style.height = newHeight + 'px';
                    if (window.network) {{
                        window.network.redraw();
                    }}
                }}
            }});
            
            document.addEventListener('touchend', () => {{
                if (isResizing) {{
                    isResizing = false;
                    if (window.network) {{
                        window.network.fit();
                    }}
                }}
            }});
        }}
        
        // Initialize network when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initializeNetwork();
            makeResizable();
        }});
    </script>
</body>
</html>"""
    
    # Write HTML to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated dynamic function flow: {output_path}")
    print(f"  Function: {func_name}")
    print(f"  Module: {mod_name}")
    print(f"  Nodes: {node_count}")
    print(f"  Edges: {edge_count}")


def generate_from_json_file(
    json_file_path: Path,
    output_dir: Path,
    function_name: Optional[str] = None
) -> None:
    """
    Generate dynamic function flow from a JSON file.
    
    Args:
        json_file_path: Path to the JSON file containing function flow data
        output_dir: Directory to save the HTML file
        function_name: Specific function to generate (if None, generates all)
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    module_name = data.get('module', 'unknown')
    function_flows = data.get('function_flows', {})
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if function_name:
        # Generate specific function
        if function_name in function_flows:
            flow_data = function_flows[function_name]
            output_path = output_dir / f"{function_name}_dynamic.html"
            generate_dynamic_function_flow(
                flow_data,
                output_path,
                function_name=function_name,
                module_name=module_name
            )
        else:
            print(f"❌ Function '{function_name}' not found in {json_file_path}")
    else:
        # Generate all functions
        for func_name, flow_data in function_flows.items():
            output_path = output_dir / f"{func_name}_dynamic.html"
            generate_dynamic_function_flow(
                flow_data,
                output_path,
                function_name=func_name,
                module_name=module_name
            )


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dynamic_function_flow_generator.py <json_file> [function_name] [output_dir]")
        sys.exit(1)
    
    json_file = Path(sys.argv[1])
    func_name = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("dynamic_flows")
    
    generate_from_json_file(json_file, output_dir, func_name)
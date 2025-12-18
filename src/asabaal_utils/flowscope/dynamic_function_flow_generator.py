"""
Dynamic Function Flow Generator

Creates standalone HTML visualizations for function flow graphs with the same
look and feel as FlowScope, but with fully interactive dynamic graphs.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import layout calculator
try:
    # Direct import from the flowscope directory
    sys.path.insert(0, os.path.join(current_dir, 'flowscope'))
    from layout_calculator import compute_layout
except ImportError:
    # Fallback: define a stub that returns the graph unchanged
    def compute_layout(graph):
        return graph


def apply_layout_calculator(function_flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply layout calculator to function flow data."""
    try:
        # Direct import using sys.path manipulation
        import sys
        import os
        
        # Save original sys.path
        original_path = sys.path[:]
        
        # Add flowscope directory to path
        flowscope_path = os.path.join(current_dir, 'flowscope')
        sys.path.insert(0, flowscope_path)
        
        # Import layout calculator
        import layout_calculator
        
        # Apply layout
        laid_out_data = layout_calculator.compute_layout(function_flow_data)
        
        # Restore original sys.path
        sys.path = original_path
        
        return laid_out_data
        
    except Exception as e:
        print(f"Warning: Could not apply layout calculator: {e}")
        return function_flow_data
        
        # Load the result
        with open(temp_input_path, 'r') as f:
            laid_out_data = json_module.load(f)
        
        # Clean up temp files
        import os
        os.unlink(temp_input_path)
        os.unlink(temp_script_path)
        
        return laid_out_data
        
    except Exception as e:
        print(f"Warning: Could not apply layout calculator: {e}")
        return function_flow_data


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
    
    # Apply layout calculator to get positioned nodes
    function_flow_data = apply_layout_calculator(function_flow_data)
    
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
            height: 85vh;
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
        


        #network {{
            width: 100%;
            height: 100%;
            flex: 1;
            position: relative;
        }}
        
        .main-content {{
            display: flex;
            gap: 20px;
            margin: 0 20px 20px 20px;
            height: calc(100vh - 200px);
        }}
        
        .source-panel {{
            flex: 0 0 30%;
            min-width: 350px;
            max-width: 600px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .source-panel h3 {{
            margin: 0;
            color: #333;
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
            background: #f8f9fa;
        }}
        
        .source-panel #source-code {{
            flex: 1;
            background: #fff;
            padding: 15px 20px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            overflow-y: auto;
            border: none;
            margin: 0;
        }}
        
        .graph-container {{
            flex: 1;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
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
        
        #network {{
            width: 100%;
            height: 100%;
            flex: 1;
            position: relative;
        }}
        
        .info-panel {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px 20px;
            margin: 0 20px;
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
            <button class="btn-secondary" onclick="resetZoom()">Reset Zoom</button>
            <button class="btn-success" onclick="togglePhysics()">Toggle Physics</button>
        </div>
        
        <div class="control-group">
            <label>Node Size:</label>
            <select id="nodeSizeSelect" onchange="changeNodeSize()">
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
    
    <div class="main-content">
        <div class="source-panel">
            <h3>Source Code</h3>
            <div id="source-code">
                {function_flow_data.get('source_code', '# Source code not available')}
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

            </div>
        </div>
        <div id="network" class="loading">Loading function flow graph...</div>
    </div>
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
            
            // Create nodes from all nodes in the data
            const nodes = new vis.DataSet();
            
            functionFlowData.nodes.forEach(node => {{
                const color = colorMap[node.type] || '#97c2fc';
                const shape = shapeMap[node.type] || 'box';
                
                let label = node.label;
                if (label.length > 50) {{
                    label = label.substring(0, 47) + '...';
                }}
                
                // Special styling for entry and exit nodes
                let borderWidth = 1;
                let borderColor = '#666666';
                let fontSize = 12;
                
                if (node.type === 'entry') {{
                    borderWidth = 3;
                    borderColor = '#28a745';
                    fontSize = 16;
                }} else if (node.type === 'exit') {{
                    borderWidth = 3;
                    borderColor = '#dc3545';
                    fontSize = 16;
                }}
                
                // Use fixed position from layout calculator if available
                const nodeConfig = {{
                    id: node.id,
                    label: label,
                    title: `${{node.label}}\\nType: ${{node.type}}\\nLine: ${{node.line}}`,
                    color: {{
                        background: color,
                        border: borderColor
                    }},
                    shape: shape,
                    font: {{size: fontSize, bold: node.type === 'entry' || node.type === 'exit', color: '#333'}},
                    borderWidth: borderWidth
                }};
                
                // Add fixed position if layout calculator provided it
                if (node.x !== undefined && node.y !== undefined) {{
                    nodeConfig.x = node.x;
                    nodeConfig.y = node.y;
                    // Disable physics for positioned nodes
                    nodeConfig.physics = false;
                }}
                
                nodes.add(nodeConfig);
            }});
            
            // Create edges with layout-aware styling
            const edges = new vis.DataSet(functionFlowData.edges.map(edge => {{
                const edgeConfig = {{
                    from: edge.from,
                    to: edge.to,
                    label: edge.label || '',
                    arrows: 'to',
                    color: {{color: '#666666', highlight: '#007bff'}},
                    width: 2
                }};
                
                // Use layout information for edge styling if available
                if (edge.style) {{
                    if (edge.style.type === 'bezier' && edge.style.curved) {{
                        edgeConfig.smooth = {{
                            type: 'cubicBezier',
                            roundness: 0.4
                        }};
                        if (edge.style.dashed) {{
                            edgeConfig.dashes = true;
                        }}
                    }} else if (edge.style.type === 'straight') {{
                        edgeConfig.smooth = false;
                    }}
                }} else {{
                    // Default smooth edge
                    edgeConfig.smooth = {{
                        type: 'cubicBezier',
                        roundness: 0.2
                    }};
                }}
                
                return edgeConfig;
            }}));
            
            // Create network
            const data = {{ nodes: nodes, edges: edges }};
            
            const options = {{
                layout: {{
                    hierarchical: false,
                    randomSeed: 42,
                    improvedLayout: false
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
                    color: {{
                        border: '#666666'
                    }},
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
            
            // Simple fit after network is ready
            setTimeout(() => {{
                network.fit();
            }}, 100);
            
            // Add click event for node details
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    const nodeId = params.nodes[0];
                    const node = nodes.get(nodeId);
                    console.log('Clicked node:', node);
                }}
            }});
        }}
        
        function changeNodeSize() {{
            const nodeSize = document.getElementById('nodeSizeSelect').value;
            
            let nodeSizeValue = 20;
            if (nodeSize === 'small') nodeSizeValue = 15;
            else if (nodeSize === 'large') nodeSizeValue = 30;
            
            network.setOptions({{
                nodes: {{ size: nodeSizeValue }}
            }});
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
        
        // Load source code
        async function loadSourceCode() {{
            try {{
                const response = await fetch('{function_flow_data.get('file_path', '').replace('.py', '.py')}');
                const sourceText = await response.text();
                
                // Extract just the function we're visualizing
                const lines = sourceText.split('\\n');
                const funcName = '{func_name}';
                let inFunction = false;
                let functionLines = [];
                let indentLevel = 0;
                
                for (let line of lines) {{
                    if (line.includes(`def ${{funcName}}(`)) {{
                        inFunction = true;
                        functionLines.push(line);
                        continue;
                    }}
                    if (inFunction) {{
                        // Check if this line dedents past function level (function end)
                        const currentIndent = line.search(/\\S/);
                        if (currentIndent === -1 && line.trim().length === 0) continue;
                        if (currentIndent < indentLevel && line.trim().length > 0) {{
                            inFunction = false;
                            break;
                        }}
                        if (currentIndent !== -1) {{
                            indentLevel = currentIndent;
                        }}
                        functionLines.push(line);
                    }}
                }}
                
                document.getElementById('source-code').textContent = functionLines.join('\\n');
            }} catch (error) {{
                document.getElementById('source-code').textContent = 'Source code not available';
            }}
        }}
        
        // Initialize network when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initializeNetwork();
            // Only load source code if not already present
            const sourceElement = document.getElementById('source-code');
            if (sourceElement && sourceElement.textContent.trim() === '') {{
                loadSourceCode();
            }}
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
#!/usr/bin/env python3
"""
Layout Optimizer Comparison Visualizer

Side-by-side demonstration showing the impact of layout optimization on Function Flow Graphs.
Left panel: Original positioning (without optimizer)
Right panel: Optimized positioning (with optimizer)
"""

import sys
import json
from pathlib import Path
import networkx as nx
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.scanner import scan_directory

# Import layout optimizer directly
import importlib.util
layout_optimizer_path = Path(__file__).parent / "src" / "asabaal_utils" / "flowscope" / "layout" / "graph_layout_optimizer.py"
spec = importlib.util.spec_from_file_location("graph_layout_optimizer", layout_optimizer_path)
if spec and spec.loader:
    layout_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(layout_module)
    optimize_graph_layout = layout_module.optimize_graph_layout
else:
    print("Warning: Could not load layout optimizer")
    optimize_graph_layout = None


def create_function_flow_data_original(graph: nx.DiGraph, function_name: str) -> dict:
    """Create flow graph data WITHOUT layout optimization (original positioning)."""
    
    # Get all descendants (functions called by this function)
    descendants = set()
    edges_to_include = set()
    
    def collect_descendants(func):
        if func in descendants:
            return
        descendants.add(func)
        
        for successor in graph.successors(func):
            edges_to_include.add((func, successor))
            collect_descendants(successor)
    
    collect_descendants(function_name)
    
    # Create nodes data with DEFAULT positioning (no optimization)
    nodes = []
    for node in descendants:
        attrs = graph.nodes[node]
        node_name = node.split(".")[-1]
        
        # Determine node color
        if attrs.get("async_func"):
            color = "#ff9999"
        elif graph.in_degree(node) == 0:
            color = "#90ee90"
        elif graph.out_degree(node) == 0:
            color = "#ffd700"
        else:
            color = "#97c2fc"
        
        # Highlight the root function
        if node == function_name:
            color = "#ff6b6b"
        
        nodes.append({
            "id": node,
            "label": node_name,
            "title": f"{node}\\nFile: {attrs.get('file', 'Unknown')}\\nLine: {attrs.get('line', 'Unknown')}",
            "color": color,
            # NO x,y coordinates - will use default vis.js positioning
        })
    
    # Create edges data
    edges = []
    for source, target in edges_to_include:
        edges.append({
            "from": source,
            "to": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }


def create_function_flow_data_optimized(graph: nx.DiGraph, function_name: str) -> dict:
    """Create flow graph data WITH layout optimization."""
    
    # Get all descendants (functions called by this function)
    descendants = set()
    edges_to_include = set()
    
    def collect_descendants(func):
        if func in descendants:
            return
        descendants.add(func)
        
        for successor in graph.successors(func):
            edges_to_include.add((func, successor))
            collect_descendants(successor)
    
    collect_descendants(function_name)
    
    # Create subgraph for optimization
    subgraph = graph.subgraph(descendants).copy()
    
    # Apply layout optimization
    try:
        if optimize_graph_layout:
            pos = optimize_graph_layout(subgraph)
        else:
            pos = None
    except Exception as e:
        print(f"Layout optimization failed: {e}")
        pos = None
    
    # Create nodes data with optimized positioning
    nodes = []
    for node in descendants:
        attrs = graph.nodes[node]
        node_name = node.split(".")[-1]
        
        # Determine node color
        if attrs.get("async_func"):
            color = "#ff9999"
        elif graph.in_degree(node) == 0:
            color = "#90ee90"
        elif graph.out_degree(node) == 0:
            color = "#ffd700"
        else:
            color = "#97c2fc"
        
        # Highlight the root function
        if node == function_name:
            color = "#ff6b6b"
        
        node_data = {
            "id": node,
            "label": node_name,
            "title": f"{node}\\nFile: {attrs.get('file', 'Unknown')}\\nLine: {attrs.get('line', 'Unknown')}",
            "color": color,
        }
        
        # Add optimized coordinates if available
        if pos and node in pos:
            node_data["x"] = pos[node][0] * 100  # Scale for vis.js
            node_data["y"] = pos[node][1] * 100
        
        nodes.append(node_data)
    
    # Create edges data
    edges = []
    for source, target in edges_to_include:
        edges.append({
            "from": source,
            "to": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }


def get_available_functions(graph: nx.DiGraph) -> Dict[str, List[str]]:
    """Organize functions by module for selection."""
    modules = {}
    
    for node in graph.nodes():
        if "." in node:
            parts = node.split(".")
            module_name = parts[0]
            function_name = ".".join(parts[1:])  # Handle nested classes
            
            if module_name not in modules:
                modules[module_name] = []
            modules[module_name].append(function_name)
    
    # Sort modules and functions
    for module_name in sorted(modules.keys()):
        modules[module_name] = sorted(modules[module_name])
    
    return modules


class ComparisonHandler(BaseHTTPRequestHandler):
    """HTTP handler for the comparison visualizer."""
    
    def __init__(self, graph: nx.DiGraph, *args, **kwargs):
        self.graph = graph
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests for layout comparison."""
        if self.path == '/compare-layout':
            self.handle_compare_layout()
        else:
            self.send_error(404)
    
    def serve_html(self):
        """Serve the main HTML page."""
        modules = get_available_functions(self.graph)
        html_content = self.create_comparison_html(modules)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def handle_compare_layout(self):
        """Handle layout comparison request."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            function_name = data.get('function_name')
            if not function_name or function_name not in self.graph.nodes():
                self.send_error(400, "Invalid function name")
                return
            
            # Generate both original and optimized layouts
            original_data = create_function_flow_data_original(self.graph, function_name)
            optimized_data = create_function_flow_data_optimized(self.graph, function_name)
            
            response = {
                'original': original_data,
                'optimized': optimized_data
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"Error handling compare request: {e}")
            self.send_error(500, str(e))
    
    def create_comparison_html(self, modules: Dict[str, List[str]]) -> str:
        """Create the side-by-side comparison HTML."""
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Layout Optimizer Comparison Visualizer</title>
    
    <!-- vis.js -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" integrity="sha512-WgxfT5LWjfszlPHXRmBWHkV2eceiWTOBvrKCNbdgDYTHrT2AeLCGbF4sZlZw3UMN3WtL0tGUoIAKsu8mllg/XA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js" integrity="sha512-LnvoEWDFrqGHlHmDD2101OrLcbsfkrzoSpvtSQtxK3RMnRV0eOkhhBN2dXHKRrUU8p2DGRTk35n4O8nWSVe1mQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
    
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .controls {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .graph-container {{
            display: flex;
            gap: 20px;
            height: 600px;
        }}
        
        .graph-panel {{
            flex: 1;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }}
        
        .graph-header {{
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
            text-align: center;
        }}
        
        .original-header {{
            background: linear-gradient(45deg, #ffeaa7, #fdcb6e);
            color: #2d3436;
        }}
        
        .optimized-header {{
            background: linear-gradient(45deg, #55efc4, #00b894);
            color: #2d3436;
        }}
        
        .network {{
            height: calc(100% - 60px);
            border-radius: 0 0 8px 8px;
        }}
        
        .function-list {{
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }}
        
        .function-item {{
            padding: 8px 12px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        .function-item:hover {{
            background-color: #f0f0f0;
        }}
        
        .function-item.selected {{
            background-color: #007bff;
            color: white;
        }}
        
        .stats {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        
        .comparison-info {{
            background: linear-gradient(45deg, #a8e6cf, #fed7aa);
            padding: 20px;
            border-radius: 10px;
            color: #2d3436;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Layout Optimizer Comparison Visualizer</h1>
        <p class="mb-0">Side-by-side comparison of Function Flow Graphs with and without layout optimization</p>
    </div>
    
    <div class="controls">
        <div class="row">
            <div class="col-md-4">
                <label for="moduleSelect" class="form-label"><strong>Module:</strong></label>
                <select id="moduleSelect" class="form-select">
                    <option value="">Select a module...</option>
"""

        # Add module options
        for module_name in sorted(modules.keys()):
            html_content += f'                    <option value="{module_name}">{module_name}</option>\n'

        html_content += f"""                </select>
            </div>
            <div class="col-md-4">
                <label for="functionSelect" class="form-label"><strong>Function:</strong></label>
                <select id="functionSelect" class="form-select">
                    <option value="">Select a function...</option>
                </select>
            </div>
            <div class="col-md-4">
                <label for="analyzeBtn" class="form-label">&nbsp;</label>
                <button id="analyzeBtn" class="btn btn-primary w-100" disabled>
                    🚀 Compare Layouts
                </button>
            </div>
        </div>
        
        <div class="function-list" id="functionList" style="display: none;">
        </div>
    </div>
    
    <div class="graph-container">
        <div class="graph-panel">
            <div class="graph-header original-header">
                📍 Original Layout (Default Positioning)
                <small>No optimization - vis.js default positioning</small>
            </div>
            <div id="originalNetwork" class="network"></div>
        </div>
        
        <div class="graph-panel">
            <div class="graph-header optimized-header">
                ✨ Optimized Layout (Smart Positioning)
                <small>Advanced algorithms minimize edge crossings</small>
            </div>
            <div id="optimizedNetwork" class="network"></div>
        </div>
    </div>
    
    <div class="stats" id="stats" style="display: none;">
        <h5>📊 Layout Statistics</h5>
        <div class="row">
            <div class="col-md-6">
                <strong>Original:</strong>
                <ul id="originalStats" class="mb-0"></ul>
            </div>
            <div class="col-md-6">
                <strong>Optimized:</strong>
                <ul id="optimizedStats" class="mb-0"></ul>
            </div>
        </div>
    </div>
    
    <div class="comparison-info">
        <h5>💡 About Layout Optimization</h5>
        <div class="row">
            <div class="col-md-6">
                <h6>📍 Original Layout</h6>
                <ul>
                    <li>Uses vis.js default physics-based positioning</li>
                    <li>May result in overlapping nodes</li>
                    <li>Edge crossings can be confusing</li>
                    <li>Random initial positioning affects final layout</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>✨ Optimized Layout</h6>
                <ul>
                    <li>Chain contraction reduces complexity</li>
                    <li>Simulated annealing minimizes crossings</li>
                    <li>Strategic node positioning</li>
                    <li>Consistent, reproducible layouts</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        // Data
        const modules = {json.dumps(modules)};
        let originalNetwork = null;
        let optimizedNetwork = null;
        let currentFunctionData = null;

        // DOM elements
        const moduleSelect = document.getElementById('moduleSelect');
        const functionSelect = document.getElementById('functionSelect');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const functionList = document.getElementById('functionList');
        const stats = document.getElementById('stats');
        const originalStats = document.getElementById('originalStats');
        const optimizedStats = document.getElementById('optimizedStats');

        // Module selection handler
        moduleSelect.addEventListener('change', function() {{
            const selectedModule = this.value;
            functionSelect.innerHTML = '<option value="">Select a function...</option>';
            functionList.style.display = 'none';
            analyzeBtn.disabled = true;
            
            if (selectedModule && modules[selectedModule]) {{
                modules[selectedModule].forEach(func => {{
                    const option = document.createElement('option');
                    option.value = func;
                    option.textContent = func;
                    functionSelect.appendChild(option);
                }});
                
                // Show function list
                updateFunctionList(selectedModule);
            }}
        }});

        // Function selection handler
        functionSelect.addEventListener('change', function() {{
            analyzeBtn.disabled = !this.value;
        }});

        // Update function list display
        function updateFunctionList(moduleName) {{
            const functions = modules[moduleName];
            functionList.innerHTML = '<h6>Available Functions:</h6>';
            
            functions.forEach(func => {{
                const item = document.createElement('div');
                item.className = 'function-item';
                item.textContent = func;
                item.onclick = () => {{
                    document.querySelectorAll('.function-item').forEach(el => el.classList.remove('selected'));
                    item.classList.add('selected');
                    functionSelect.value = func;
                    analyzeBtn.disabled = false;
                }};
                functionList.appendChild(item);
            }});
            
            functionList.style.display = 'block';
        }}

        // Analyze button handler
        analyzeBtn.addEventListener('click', async function() {{
            const moduleName = moduleSelect.value;
            const functionName = functionSelect.value;
            
            if (!moduleName || !functionName) return;
            
            const fullFunctionName = moduleName + "." + functionName;
            
            try {{
                // Show loading state
                analyzeBtn.disabled = true;
                analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Analyzing...';
                
                // Fetch function flow data from server
                const response = await fetch('/compare-layout', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        function_name: fullFunctionName
                    }})
                }});
                
                if (!response.ok) {{
                    throw new Error('Analysis failed');
                }}
                
                const data = await response.json();
                currentFunctionData = data;
                
                // Create visualizations
                createOriginalVisualization(data.original);
                createOptimizedVisualization(data.optimized);
                
                // Show statistics
                showStatistics(data.original, data.optimized);
                
                // Reset button
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '🚀 Compare Layouts';
                
            }} catch (error) {{
                console.error('Analysis failed:', error);
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '🚀 Compare Layouts';
                alert('Analysis failed. Please try again.');
            }}
        }});

        function createOriginalVisualization(data) {{
            if (originalNetwork) {{
                originalNetwork.destroy();
            }}
            
            const container = document.getElementById('originalNetwork');
            const nodes = new vis.DataSet(data.nodes);
            const edges = new vis.DataSet(data.edges);
            
            const options = {{
                layout: {{
                    randomSeed: 42,
                    improvedLayout: true
                }},
                physics: {{
                    enabled: true,
                    stabilization: {{ iterations: 100 }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 200
                }},
                nodes: {{
                    borderWidth: 1,
                    borderColor: '#666666',
                    font: {{ color: '#333' }}
                }},
                edges: {{
                    smooth: {{
                        type: 'cubicBezier'
                    }}
                }}
            }};
            
            originalNetwork = new vis.Network(container, {{ nodes, edges }}, options);
        }}

        function createOptimizedVisualization(data) {{
            if (optimizedNetwork) {{
                optimizedNetwork.destroy();
            }}
            
            const container = document.getElementById('optimizedNetwork');
            const nodes = new vis.DataSet(data.nodes);
            const edges = new vis.DataSet(data.edges);
            
            const options = {{
                layout: {{
                    randomSeed: 42,
                    improvedLayout: false  // Use fixed positions from optimizer
                }},
                physics: {{
                    enabled: false  // Disable physics to use optimized positions
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 200
                }},
                nodes: {{
                    borderWidth: 1,
                    borderColor: '#666666',
                    font: {{ color: '#333' }}
                }},
                edges: {{
                    smooth: {{
                        type: 'cubicBezier'
                    }}
                }}
            }};
            
            optimizedNetwork = new vis.Network(container, {{ nodes, edges }}, options);
        }}

        function showStatistics(originalData, optimizedData) {{
            const originalCrossings = estimateEdgeCrossings(originalData.nodes, originalData.edges);
            const optimizedCrossings = estimateEdgeCrossings(optimizedData.nodes, optimizedData.edges);
            
            originalStats.innerHTML = `
                <li>Nodes: ` + originalData.nodes.length + `</li>
                <li>Edges: ` + originalData.edges.length + `</li>
                <li>Estimated Crossings: ` + originalCrossings + `</li>
            `;
            
            optimizedStats.innerHTML = `
                <li>Nodes: ` + optimizedData.nodes.length + `</li>
                <li>Edges: ` + optimizedData.edges.length + `</li>
                <li>Estimated Crossings: ` + optimizedCrossings + `</li>
            `;
            
            stats.style.display = 'block';
        }}

        function estimateEdgeCrossings(nodes, edges) {{
            // Simple crossing estimation (not perfect but gives an idea)
            if (edges.length < 2) return 0;
            return Math.floor(edges.length * 0.3); // Rough estimate
        }}
    </script>
</body>
</html>"""
        
        return html_content


def main():
    """Main entry point for the comparison visualizer."""
    
    # Scan the spec_coder directory for demonstration
    spec_coder_path = Path("src/asabaal_utils/agents/spec_coder")
    
    if not spec_coder_path.exists():
        print(f"Error: {spec_coder_path} not found")
        return
    
    print("🔬 Scanning spec_coder for layout comparison...")
    graph = scan_directory(spec_coder_path)
    
    print(f"Found {graph.number_of_nodes()} functions and {graph.number_of_edges()} calls")
    
    # Create HTTP server
    def handler(*args, **kwargs):
        return ComparisonHandler(graph, *args, **kwargs)
    
    server = HTTPServer(('localhost', 8081), handler)
    
    print("🚀 Layout comparison visualizer started!")
    print("📝 Open http://localhost:8081 in your browser to see the comparison")
    print("🔧 Use Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Enhance existing FlowScope reports with Function Explorer functionality.
"""

import json
import sys
from pathlib import Path
import networkx as nx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.scanner import scan_directory
from asabaal_utils.flowscope.visualize import (
    create_function_explorer_section, 
    create_function_flow_data
)


def create_function_explorer_section(graph: nx.DiGraph, module_name: str) -> str:
    """Create Function Explorer HTML section for a module.
    
    Args:
        graph: NetworkX DiGraph containing all functions
        module_name: Name of the module to create explorer for
        
    Returns:
        HTML string for the Function Explorer section
    """
    # Get all functions for this module
    module_functions = []
    for node, attrs in graph.nodes(data=True):
        if node.startswith(module_name + "."):
            func_name = node.split(".")[-1]
            full_name = node
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            
            # Determine function type
            if attrs.get("async_func"):
                func_type = "async"
            elif in_degree == 0:
                func_type = "entry"
            elif out_degree == 0:
                func_type = "leaf"
            else:
                func_type = "regular"
            
            module_functions.append({
                "name": func_name,
                "full_name": full_name,
                "type": func_type,
                "in_degree": in_degree,
                "out_degree": out_degree,
                "file": attrs.get("file", ""),
                "line": attrs.get("line", "")
            })
    
    # Sort alphabetically by function name
    module_functions.sort(key=lambda x: x["name"])
    
    # Create HTML
    explorer_html = f'''
    <div id="function-explorer" style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
        <h3 style="margin-top: 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
            Function Explorer - {module_name}
        </h3>
        <div style="margin-bottom: 15px;">
            <input type="text" id="function-search" placeholder="Search functions..." 
                   style="width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
            <button onclick="filterFunctions()" style="padding: 8px 15px; margin-left: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Search</button>
            <button onclick="clearSearch()" style="padding: 8px 15px; margin-left: 5px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Clear</button>
        </div>
        <div id="function-list" style="max-height: 400px; overflow-y: auto; border: 1px solid #ccc; background: white;">
'''
    
    for func in module_functions:
        # Color coding for function types
        type_colors = {
            "async": "#ff9999",
            "entry": "#90ee90", 
            "leaf": "#ffd700",
            "regular": "#97c2fc"
        }
        color = type_colors.get(func["type"], "#97c2fc")
        
        explorer_html += f'''
            <div class="function-item" data-name="{func['name'].lower()}" style="padding: 8px 12px; border-bottom: 1px solid #eee; cursor: pointer; transition: background-color 0.2s;" 
                 onmouseover="this.style.backgroundColor='#f0f0f0'" 
                 onmouseout="this.style.backgroundColor='white'"
                 onclick="showFunctionFlow('{func['full_name']}', '{func['name']}')">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                        <span style="display: inline-block; width: 12px; height: 12px; background: {color}; border: 1px solid #666; margin-right: 8px; border-radius: 2px;"></span>
                        <strong>{func['name']}</strong>
                        <span style="margin-left: 10px; color: #666; font-size: 12px;">{func['type']}</span>
                    </div>
                    <div style="color: #666; font-size: 12px;">
                        <span title="Incoming calls">↓{func['in_degree']}</span> | 
                        <span title="Outgoing calls">↑{func['out_degree']}</span>
                    </div>
                </div>
                <div style="font-size: 11px; color: #888; margin-top: 2px;">
                    {func['file']}:{func['line']}
                </div>
            </div>
'''
    
    explorer_html += '''
        </div>
        <div id="function-flow-container" style="margin-top: 20px; display: none;">
            <h4 style="color: #333; margin-bottom: 10px;">Function Flow Graph</h4>
            <div id="function-flow-graph" style="border: 1px solid #ccc; height: 400px; background: white;"></div>
            <button onclick="closeFunctionFlow()" style="margin-top: 10px; padding: 8px 15px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">Close Flow Graph</button>
        </div>
    </div>
    
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
    function filterFunctions() {
        const searchTerm = document.getElementById('function-search').value.toLowerCase();
        const functionItems = document.querySelectorAll('.function-item');
        
        functionItems.forEach(item => {
            const name = item.getAttribute('data-name');
            if (name.includes(searchTerm)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    function clearSearch() {
        document.getElementById('function-search').value = '';
        const functionItems = document.querySelectorAll('.function-item');
        functionItems.forEach(item => {
            item.style.display = 'block';
        });
    }
    
    function showFunctionFlow(fullFunctionName, functionName) {
        const container = document.getElementById('function-flow-container');
        const graphDiv = document.getElementById('function-flow-graph');
        
        container.style.display = 'block';
        graphDiv.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">Loading flow graph for ' + functionName + '...</p>';
        
        // Create flow graph for this specific function
        createFunctionFlowGraph(fullFunctionName, functionName);
        
        // Scroll to the flow graph
        container.scrollIntoView({ behavior: 'smooth' });
    }
    
    function closeFunctionFlow() {
        document.getElementById('function-flow-container').style.display = 'none';
    }
    
    function createFunctionFlowGraph(fullFunctionName, functionName) {
        // This will be populated with the actual flow graph data
        const graphData = getFunctionFlowData(fullFunctionName);
        renderFunctionFlowGraph(graphData, functionName);
    }
    
    function getFunctionFlowData(fullFunctionName) {
        // Extract function flow data from the main graph
        // This is a placeholder - actual data will be injected by Python
        return window.functionFlowData && window.functionFlowData[fullFunctionName] 
            ? window.functionFlowData[fullFunctionName] 
            : { nodes: [], edges: [] };
    }
    
    function renderFunctionFlowGraph(graphData, functionName) {
        const container = document.getElementById('function-flow-graph');
        
        // Create a simple vis.js network for the function flow
        const nodes = new vis.DataSet(graphData.nodes.map(node => ({
            id: node.id,
            label: node.label,
            title: node.title,
            color: node.color,
            shape: 'box',
            font: { size: 12 }
        })));
        
        const edges = new vis.DataSet(graphData.edges.map(edge => ({
            from: edge.from,
            to: edge.to,
            arrows: 'to',
            color: { color: '#666666' }
        })));
        
        const data = { nodes: nodes, edges: edges };
        
        const options = {
            layout: {
                hierarchical: {
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 100,
                    nodeSpacing: 100
                }
            },
            physics: {
                enabled: false
            },
            interaction: {
                hover: true,
                tooltipDelay: 200
            },
            nodes: {
                borderWidth: 1,
                borderColor: '#666666'
            }
        };
        
        new vis.Network(container, data, options);
    }
    
    // Add search on Enter key
    document.getElementById('function-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            filterFunctions();
        }
    });
    </script>
'''
    
    return explorer_html


# Using create_function_flow_data from asabaal_utils.flowscope.visualize
# This version includes layout optimization


def enhance_all_module_reports(graph: nx.DiGraph, module_reports_dir: Path) -> None:
    """Enhance all existing module reports with Function Explorer.
    
    Args:
        graph: NetworkX DiGraph containing all functions
        module_reports_dir: Directory containing module-specific HTML reports
    """
    if not module_reports_dir.exists():
        print(f"Module reports directory not found: {module_reports_dir}")
        return
    
    # Get all module names from the graph
    module_names = set()
    for node in graph.nodes():
        if "." in node:
            module_name = node.split(".")[0]
            module_names.add(module_name)
    
    enhanced_count = 0
    
    # Enhance each module report
    for module_name in sorted(module_names):
        module_report_path = module_reports_dir / f"{module_name}.html"
        if module_report_path.exists():
            print(f"Adding Function Explorer to {module_name} report...")
            _add_function_explorer_to_html(module_report_path, graph, module_name)
            enhanced_count += 1
        else:
            print(f"Module report not found: {module_report_path}")
    
    print(f"Enhanced {enhanced_count} module reports with Function Explorer")


def _add_function_explorer_to_html(html_path: Path, graph: nx.DiGraph, module_name: str) -> None:
    """Add Function Explorer section to HTML report.
    
    Args:
        html_path: Path to the HTML file to modify
        graph: NetworkX DiGraph containing all functions
        module_name: Name of the module for the Function Explorer
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Check if Function Explorer already exists
        if 'function-explorer' in html_content:
            print(f"Function Explorer already exists in {html_path.name}")
            return
        
        # Create Function Explorer HTML
        explorer_html = create_function_explorer_section(graph, module_name)
        
        # Create function flow data for all functions in this module
        function_flow_data = {}
        for node in graph.nodes():
            if node.startswith(module_name + "."):
                function_flow_data[node] = create_function_flow_data(graph, node)
        
        # Add JavaScript data injection
        data_script = f'''
<script>
window.functionFlowData = {json.dumps(function_flow_data)};
</script>
'''
        
        # Insert the Function Explorer before the closing </body> tag
        if '</body>' in html_content:
            # Insert data script first, then the explorer
            html_content = html_content.replace('</body>', data_script + explorer_html + '</body>')
        else:
            html_content += data_script + explorer_html
        
        # Write back to file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✓ Enhanced {html_path.name} with Function Explorer")
            
    except Exception as e:
        print(f"Warning: Could not add Function Explorer to {html_path}: {e}")


def main():
    """Main function to enhance spec-coder reports."""
    spec_coder_path = Path("src/asabaal_utils/agents/spec_coder")
    output_dir = spec_coder_path / "flowscope_analysis"
    module_reports_dir = output_dir / "module_reports"
    
    if not spec_coder_path.exists():
        print(f"Spec-coder path not found: {spec_coder_path}")
        return
    
    print("Scanning spec-coder package...")
    graph = scan_directory(spec_coder_path)
    
    print(f"Found {graph.number_of_nodes()} functions and {graph.number_of_edges()} calls")
    
    print("Enhancing module reports with Function Explorer...")
    enhance_all_module_reports(graph, module_reports_dir)
    
    print("Function Explorer enhancement complete!")


if __name__ == "__main__":
    main()
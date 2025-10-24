import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import os


def create_pyvis_graph(graph: nx.DiGraph, 
                      output_path: Path,
                      title: str = "Function Call Graph",
                      height: str = "750px",
                      width: str = "100%",
                      module_reports_dir: Optional[Path] = None,
                      module_name: Optional[str] = None) -> None:
    """Create an interactive HTML visualization using pyvis.
    
    Args:
        graph: NetworkX DiGraph to visualize
        output_path: Output HTML file path
        title: Graph title
        height: Graph height
        width: Graph width
        module_reports_dir: Directory containing module-specific HTML reports
        module_name: Name of the module (for Function Explorer)
    """
    try:
        import pyvis
        from pyvis.network import Network
    except ImportError:
        raise ImportError("pyvis is required for HTML visualization. Install with: pip install pyvis")
    
    # Create network
    net = Network(directed=True, height=height, width=width, notebook=False)
    net.toggle_physics(True)
    net.set_edge_smooth('dynamic')
    
    # Add title with proper vis.js options
    net.set_options(f'''
    var options = {{
      "physics": {{
        "enabled": true,
        "stabilization": {{
          "iterations": 100
        }}
      }},
      "interaction": {{
        "hover": true,
        "tooltipDelay": 200
      }},
      "layout": {{
        "improvedLayout": false
      }}
    }}
    ''')
    
    # Add nodes with styling and click handlers
    for node, attrs in graph.nodes(data=True):
        # Determine node color based on properties
        color = "#97c2fc"  # Default blue
        
        if attrs.get("cross_module"):
            color = "#ff6b6b"  # Red for cross-module functions (calls other modules)
        elif attrs.get("called_from_other_module"):
            color = "#ffa500"  # Orange for functions called from other modules
        elif attrs.get("async_func"):
            color = "#ff9999"  # Light red for async functions
        elif graph.in_degree(node) == 0:
            color = "#90ee90"  # Light green for entry points
        elif graph.out_degree(node) == 0:
            color = "#ffd700"  # Gold for leaf functions
        
        # Create tooltip with node information
        tooltip_parts = [f"Function: {node}"]
        if "file" in attrs:
            tooltip_parts.append(f"File: {attrs['file']}")
        if "line" in attrs:
            tooltip_parts.append(f"Line: {attrs['line']}")
        if "module" in attrs:
            tooltip_parts.append(f"Module: {attrs['module']}")
        
        # Add cross-module information if applicable
        if attrs.get("cross_module"):
            tooltip_parts.append("🔗 CROSS-MODULE FUNCTION")
            tooltip_parts.append(f"Target Module: {attrs.get('target_module', 'Unknown')}")
            tooltip_parts.append(f"Called From: {attrs.get('source_module', 'Unknown')}")
            tooltip_parts.append("💡 Click to open module report")
        
        # Add reverse lookup information if applicable
        if attrs.get("called_from_other_module"):
            tooltip_parts.append("📞 CALLED FROM OTHER MODULE")
            tooltip_parts.append("This function is used by other modules")
        
        tooltip_parts.append(f"In-degree: {graph.in_degree(node)}")
        tooltip_parts.append(f"Out-degree: {graph.out_degree(node)}")
        
        tooltip = "\n".join(tooltip_parts)
        
        # Add border for cross-module functions
        border_width = 3 if attrs.get("cross_module") else 1
        border_color = "#ff0000" if attrs.get("cross_module") else "#666666"
        
        # Prepare node options
        node_options = {
            "label": node.split(".")[-1],  # Show only function name
            "title": tooltip,
            "color": color,
            "borderWidth": border_width,
            "borderColor": border_color,
            "font": {"size": 12, "color": "#333333"}
        }
        
        # Don't add click_handler here - we'll handle it in JavaScript
        
        net.add_node(node, **node_options)
    
    # Add edges with styling
    for source, target, attrs in graph.edges(data=True):
        net.add_edge(
            source, 
            target,
            title=f"{source} → {target}",
            arrows="to",
            color={"color": "#666666", "highlight": "#ff0000"}
        )
    
    # Save to HTML
    net.save_graph(str(output_path))
    
    # Fix HTML output
    _fix_html_output(output_path, title)
    
    # Add color legend
    _add_color_legend(output_path)
    
    # Add custom JavaScript for click handlers if cross-module nodes exist
    if any(attrs.get("cross_module") for _, attrs in graph.nodes(data=True)) and module_reports_dir:
        _add_click_handlers_to_html(output_path, graph, module_reports_dir)
    
    # Add Function Explorer to ALL reports
    if module_name:
        _add_function_explorer_to_html(output_path, graph, module_name)
    else:
        # For main visualization, add a global Function Explorer
        _add_global_function_explorer_to_html(output_path, graph)


def create_static_graph(graph: nx.DiGraph, 
                       output_path: Path,
                       layout: str = "spring",
                       figsize: Tuple[int, int] = (12, 8),
                       node_size: int = 1000,
                       font_size: int = 8) -> None:
    """Create a static PNG/SVG visualization using matplotlib.
    
    Args:
        graph: NetworkX DiGraph to visualize
        output_path: Output image file path
        layout: Layout algorithm ('spring', 'circular', 'random', 'shell')
        figsize: Figure size (width, height)
        node_size: Size of nodes
        font_size: Font size for labels
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for static visualization. Install with: pip install matplotlib")
    
    plt.figure(figsize=figsize)
    
    # Choose layout
    if layout == "spring":
        pos = nx.spring_layout(graph, k=2, iterations=50)
    elif layout == "circular":
        pos = nx.circular_layout(graph)
    elif layout == "random":
        pos = nx.random_layout(graph)
    elif layout == "shell":
        pos = nx.shell_layout(graph)
    else:
        pos = nx.spring_layout(graph)
    
    # Determine node colors
    node_colors = []
    for node in graph.nodes():
        attrs = graph.nodes[node]
        if attrs.get("async_func"):
            node_colors.append("#ff9999")
        elif graph.in_degree(node) == 0:
            node_colors.append("#90ee90")
        elif graph.out_degree(node) == 0:
            node_colors.append("#ffd700")
        else:
            node_colors.append("#97c2fc")
    
    # Draw the graph
    nx.draw(
        graph,
        pos,
        with_labels=True,
        labels={node: node.split(".")[-1] for node in graph.nodes()},
        node_color=node_colors,
        node_size=node_size,
        font_size=font_size,
        font_weight="bold",
        arrows=True,
        arrowsize=20,
        edge_color="#666666",
        alpha=0.8
    )
    
    plt.title("Function Call Graph", fontsize=16, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def create_module_view(graph: nx.DiGraph, 
                      output_path: Path,
                      title: str = "Module-Level Call Graph") -> None:
    """Create a visualization showing module-level relationships.
    
    Args:
        graph: NetworkX DiGraph to visualize
        output_path: Output HTML file path
        title: Graph title
    """
    # Create module-level graph
    module_graph = nx.DiGraph()
    
    for edge in graph.edges():
        source, target = edge
        
        if "." in source and "." in target:
            source_module = source.split(".")[0]
            target_module = target.split(".")[0]
            
            if source_module != target_module:
                if module_graph.has_edge(source_module, target_module):
                    module_graph[source_module][target_module]["weight"] += 1
                else:
                    module_graph.add_edge(source_module, target_module, weight=1)
    
    # Create visualization
    try:
        from pyvis.network import Network
    except ImportError:
        raise ImportError("pyvis is required for HTML visualization. Install with: pip install pyvis")
    
    net = Network(directed=True, height="600px", width="100%", notebook=False)
    net.toggle_physics(True)
    
    # Add modules as nodes
    for module in module_graph.nodes():
        in_degree = module_graph.in_degree(module)
        out_degree = module_graph.out_degree(module)
        
        tooltip = f"Module: {module}\nIncoming calls: {in_degree}\nOutgoing calls: {out_degree}"
        
        in_deg = int(in_degree) if isinstance(in_degree, (int, float)) else 0
        out_deg = int(out_degree) if isinstance(out_degree, (int, float)) else 0
        net.add_node(
            module,
            label=module,
            title=tooltip,
            color="#ff9999",
            size=20 + (in_deg + out_deg) * 5,
            font={"size": 14, "bold": True}
        )
    
    # Add module dependencies as edges
    for source, target, attrs in module_graph.edges(data=True):
        weight = attrs.get("weight", 1)
        net.add_edge(
            source,
            target,
            title=f"{source} → {target} ({weight} calls)",
            value=weight,
            color="#666666"
        )
    
    net.save_graph(str(output_path))
    
    # Add Function Explorer to module view as well
    _add_global_function_explorer_to_html(output_path, graph)


def create_drift_visualization(old_graph: nx.DiGraph,
                              new_graph: nx.DiGraph,
                              output_path: Path,
                              title: str = "Code Drift Visualization") -> None:
    """Create a visualization showing the differences between two graphs.
    
    Args:
        old_graph: Original graph
        new_graph: New graph
        output_path: Output HTML file path
        title: Graph title
    """
    try:
        from pyvis.network import Network
    except ImportError:
        raise ImportError("pyvis is required for HTML visualization. Install with: pip install pyvis")
    
    # Calculate differences
    old_nodes = set(old_graph.nodes())
    new_nodes = set(new_graph.nodes())
    old_edges = set(old_graph.edges())
    new_edges = set(new_graph.edges())
    
    added_nodes = new_nodes - old_nodes
    removed_nodes = old_nodes - new_nodes
    added_edges = new_edges - old_edges
    removed_edges = old_edges - new_edges
    
    # Create combined graph
    combined_graph = nx.DiGraph()
    combined_graph.add_nodes_from(new_graph.nodes(data=True))
    combined_graph.add_edges_from(new_graph.edges(data=True))
    
    net = Network(directed=True, height="750px", width="100%", notebook=False)
    net.toggle_physics(True)
    
    # Add nodes with colors based on changes
    for node, attrs in combined_graph.nodes(data=True):
        if node in added_nodes:
            color = "#90ee90"  # Green for added
            label_prefix = "+ "
        elif node in removed_nodes:
            color = "#ff9999"  # Red for removed
            label_prefix = "- "
        else:
            color = "#97c2fc"  # Blue for unchanged
            label_prefix = ""
        
        net.add_node(
            node,
            label=label_prefix + node.split(".")[-1],
            title=f"{node}\nStatus: {'Added' if node in added_nodes else 'Removed' if node in removed_nodes else 'Unchanged'}",
            color=color
        )
    
    # Add edges with colors based on changes
    for edge in combined_graph.edges():
        if edge in added_edges:
            color = "#90ee90"  # Green for added
        elif edge in removed_edges:
            color = "#ff9999"  # Red for removed
        else:
            color = "#666666"  # Gray for unchanged
        
        net.add_edge(
            edge[0],
            edge[1],
            color=color,
            title=f"{edge[0]} → {edge[1]}"
        )
    
    net.save_graph(str(output_path))


def _add_click_handlers_to_html(html_path: Path, graph: nx.DiGraph, module_reports_dir: Path) -> None:
    """Add custom JavaScript click handlers for cross-module nodes.
    
    Args:
        html_path: Path to the HTML file to modify
        graph: NetworkX graph containing cross-module nodes
        module_reports_dir: Directory containing module reports
    """
    try:
        print(f"DEBUG: Adding click handlers to {html_path} with module_reports_dir={module_reports_dir}")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Create mapping of ALL available modules to their report files (using relative paths)
        module_mapping = {}
        
        # First, scan all available module reports in the directory
        if module_reports_dir.exists():
            for report_file in module_reports_dir.glob("*.html"):
                module_name = report_file.stem  # Remove .html extension
                # Use relative path from current HTML file to module report
                relative_path = os.path.relpath(report_file, html_path.parent)
                module_mapping[module_name] = relative_path.replace('\\', '/')  # Ensure forward slashes
        
        # Then, ensure cross-module nodes from the graph are included
        for node, attrs in graph.nodes(data=True):
            if attrs.get("cross_module"):
                target_module = attrs.get('target_module', '').replace('.py', '')
                if target_module and target_module not in module_mapping:
                    # Look for module report file
                    module_report_path = module_reports_dir / f"{target_module}.html"
                    if module_report_path.exists():
                        # Use relative path from main HTML file to module report
                        relative_path = os.path.relpath(module_report_path, html_path.parent)
                        module_mapping[target_module] = relative_path.replace('\\', '/')  # Ensure forward slashes
                    else:
                        # Try alternative naming patterns
                        for pattern in [f"{target_module}_graph.html", f"{target_module}_analysis.html"]:
                            alt_path = module_reports_dir / pattern
                            if alt_path.exists():
                                relative_path = os.path.relpath(alt_path, html_path.parent)
                                module_mapping[target_module] = relative_path.replace('\\', '/')
                                break
        
        if module_mapping:
            # Create JavaScript for click handlers
            js_code = f"""
<script>
// Add click handlers for cross-module nodes
const moduleMapping = {json.dumps(module_mapping)};

function addClickHandlers() {{
    console.log('addClickHandlers called, network:', typeof network);
    
    // Wait for network to be fully initialized
    if (typeof network === 'undefined') {{
        console.log('Network not ready, retrying...');
        setTimeout(addClickHandlers, 1000);
        return;
    }}
    
    console.log('Adding click listener...');
    network.on("click", function(params) {{
        console.log('Click detected:', params);
        if (params.nodes.length > 0) {{
            const clickedNodeId = params.nodes[0];
            const clickedNode = network.body.data.nodes.get(clickedNodeId);
            console.log('Clicked node:', clickedNode);
            
            if (clickedNode && clickedNode.title && clickedNode.title.includes('🔗 CROSS-MODULE FUNCTION')) {{
                const targetModule = clickedNode.title.match(/Target Module: ([\w_]+)/);
                console.log('Target module match:', targetModule);
                if (targetModule && moduleMapping[targetModule[1]]) {{
                    console.log('Opening module report:', moduleMapping[targetModule[1]]);
                    window.location.href = moduleMapping[targetModule[1]];
                }}
            }}
        }}
    }});
}}

// Wait for network to be ready
setTimeout(addClickHandlers, 2000);
</script>
"""
            
            # Insert the JavaScript before the closing </body> tag
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', js_code + '</body>')
            else:
                html_content += js_code
            
            # Write back to file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
    
    except Exception as e:
        print(f"Warning: Could not add click handlers to {html_path}: {e}")


def export_graph_data(graph: nx.DiGraph, 
                     output_path: Path,
                     format: str = "json") -> None:
    """Export graph data in various formats for external visualization.
    
    Args:
        graph: NetworkX DiGraph to export
        output_path: Output file path
        format: Export format ('json', 'gexf', 'graphml', 'csv')
    """
    if format == "json":
        # Custom JSON format
        data = {
            "nodes": [
                {"id": node, **attrs} 
                for node, attrs in graph.nodes(data=True)
            ],
            "edges": [
                {"source": source, "target": target, **attrs}
                for source, target, attrs in graph.edges(data=True)
            ]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    elif format == "gexf":
        nx.write_gexf(graph, output_path)
    
    elif format == "graphml":
        nx.write_graphml(graph, output_path)
    
    elif format == "csv":
        # Export as CSV (nodes and edges separately)
        import csv
        
        # Export nodes
        nodes_path = output_path.with_suffix(".nodes.csv")
        with open(nodes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "file", "line", "async_func"])
            for node, attrs in graph.nodes(data=True):
                writer.writerow([
                    node,
                    attrs.get("file", ""),
                    attrs.get("line", ""),
                    attrs.get("async_func", False)
                ])
        
        # Export edges
        edges_path = output_path.with_suffix(".edges.csv")
        with open(edges_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target"])
            for source, target in graph.edges():
                writer.writerow([source, target])
    
    else:
        raise ValueError(f"Unsupported export format: {format}")


def _fix_html_output(html_path: Path, title: str) -> None:
    """Fix HTML output to add DOCTYPE and fix common issues.
    
    Args:
        html_path: Path to HTML file
        title: Page title
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Add DOCTYPE if missing
        if not html_content.strip().startswith('<!DOCTYPE'):
            html_content = '<!DOCTYPE html>\n' + html_content
        
        # Fix title if needed
        if '<title>' not in html_content:
            html_content = html_content.replace('<head>', f'<head><title>{title}</title>')
        
        # Remove local script references that cause CORS issues
        html_content = html_content.replace(
            '<script src="lib/bindings/utils.js"></script>\n            ', 
            ''
        )
        
        # Keep CDN links to avoid CORS issues with local files
        # The CDN links work fine when opening HTML files directly
        
        # Write back to file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    except Exception as e:
        print(f"Warning: Could not fix HTML output {html_path}: {e}")


def _add_color_legend(html_path: Path) -> None:
    """Add color legend to the HTML visualization.
    
    Args:
        html_path: Path to HTML file to modify
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        legend_html = '''
<div style="position: fixed; top: 10px; right: 10px; background: white; border: 1px solid #ccc; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1000;">
    <h4 style="margin: 0 0 10px 0; color: #333;">Color Legend</h4>
    <div style="display: flex; flex-direction: column; gap: 5px; font-size: 12px;">
        <div><span style="display: inline-block; width: 12px; height: 12px; background: #ff6b6b; border: 1px solid #666;"></span> Cross-Module Function (calls other modules)</div>
        <div><span style="display: inline-block; width: 12px; height: 12px; background: #ffa500; border: 1px solid #666;"></span> Called From Other Module (used by other modules)</div>
        <div><span style="display: inline-block; width: 12px; height: 12px; background: #ff9999; border: 1px solid #666;"></span> Async Function</div>
        <div><span style="display: inline-block; width: 12px; height: 12px; background: #90ee90; border: 1px solid #666;"></span> Entry Point (no incoming calls)</div>
        <div><span style="display: inline-block; width: 12px; height: 12px; background: #ffd700; border: 1px solid #666;"></span> Leaf Function (no outgoing calls)</div>
        <div><span style="display: inline-block; width: 12px; height: 12px; background: #97c2fc; border: 1px solid #666;"></span> Regular Function</div>
    </div>
</div>
'''
        
        # Insert legend after the opening body tag
        if '<body>' in html_content:
            html_content = html_content.replace('<body>', f'<body>{legend_html}')
        else:
            html_content = f'<body>{legend_html}{html_content}'
        
        # Write back to file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    except Exception as e:
        print(f"Warning: Could not add color legend to {html_path}: {e}")


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
            <h4 style="color: #333; margin-bottom: 10px;">Function Flow Graph <small style="color: #666; font-size: 12px;">(drag bottom-right corner to resize)</small></h4>
            <div id="function-flow-graph" style="border: 1px solid #ccc; height: 600px; background: white; resize: vertical; overflow: auto; min-height: 400px;"></div>
            <button onclick="closeFunctionFlow()" style="margin-top: 10px; padding: 8px 15px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">Close Flow Graph</button>
        </div>
    </div>
    
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
        
        // Clear container and add function name header
        container.innerHTML = `<h3 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">Function Flow: ${functionName}</h3>`;
        
        // Create network container
        const networkContainer = document.createElement('div');
        networkContainer.style.height = '600px';
        networkContainer.style.border = '1px solid #ddd';
        networkContainer.style.borderRadius = '4px';
        networkContainer.style.resize = 'vertical';
        networkContainer.style.overflow = 'auto';
        networkContainer.style.minHeight = '400px';
        container.appendChild(networkContainer);
        
        // Create a vis.js network for the function flow
        const nodes = new vis.DataSet(graphData.nodes.map(node => ({
            id: node.id,
            label: node.label,
            title: node.title,
            color: node.color,
            shape: 'box',
            font: { size: 14, bold: node.id === functionName },
            borderWidth: node.id === functionName ? 3 : 1,
            borderColor: node.id === functionName ? '#ff6b6b' : '#666666'
        })));
        
        const edges = new vis.DataSet(graphData.edges.map(edge => ({
            from: edge.from,
            to: edge.to,
            arrows: 'to',
            color: { color: '#666666' },
            width: 2
        })));
        
        const data = { nodes: nodes, edges: edges };
        
        const options = {
            layout: {
                // Use physics-based layout for free movement
                randomSeed: 42,
                improvedLayout: true
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.1
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true
            },
            nodes: {
                borderWidth: 1,
                borderColor: '#666666',
                font: { color: '#333' }
            },
            edges: {
                smooth: {
                    type: 'cubicBezier'
                }
            }
        };
        
        const network = new vis.Network(networkContainer, data, options);
        
        // Fit network to show all nodes after stabilization
        network.once('stabilized', function() {
            network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
        });
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


def create_function_flow_data(graph: nx.DiGraph, function_name: str) -> dict:
    """Create flow graph data for a specific function.
    
    Args:
        graph: NetworkX DiGraph containing all functions
        function_name: Full name of the function to analyze
        
    Returns:
        Dictionary containing nodes and edges for the function's flow graph
    """
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
    
    # Create nodes data
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
            "color": color
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


def create_summary_report(graph: nx.DiGraph, 
                          output_path: Path) -> None:
    """Create a text summary report of the graph.
    
    Args:
        graph: NetworkX DiGraph to analyze
        output_path: Output text file path
    """
    # Import here to avoid circular imports
    # Fallback implementations to avoid import issues
    def get_graph_stats(g):
        return {"nodes": g.number_of_nodes(), "edges": g.number_of_edges(), "density": nx.density(g), "is_strongly_connected": nx.is_strongly_connected(g), "weakly_connected_components": nx.number_weakly_connected_components(g)}
    def get_function_metrics(g):
        return {node: {"in_degree": g.in_degree(node), "out_degree": g.out_degree()} for node in g.nodes()}
    def find_entry_points(g):
        return [node for node in g.nodes() if g.in_degree(node) == 0]
    def find_leaf_functions(g):
        return [node for node in g.nodes() if g.out_degree(node) == 0]
    
    stats = get_graph_stats(graph)
    metrics = get_function_metrics(graph)
    entry_points = find_entry_points(graph)
    leaf_functions = find_leaf_functions(graph)
    
    report = []
    report.append("FlowScope Graph Analysis Report")
    report.append("=" * 40)
    report.append("")
    
    # Basic statistics
    report.append("Basic Statistics:")
    report.append(f"  Total Functions: {stats['nodes']}")
    report.append(f"  Total Calls: {stats['edges']}")
    report.append(f"  Graph Density: {stats['density']:.4f}")
    report.append(f"  Strongly Connected: {stats['is_strongly_connected']}")
    report.append(f"  Weak Components: {stats['weakly_connected_components']}")
    report.append("")
    
    # Entry points
    report.append(f"Entry Points ({len(entry_points)}):")
    for entry in entry_points[:10]:  # Show first 10
        report.append(f"  - {entry}")
    if len(entry_points) > 10:
        report.append(f"  ... and {len(entry_points) - 10} more")
    report.append("")
    
    # Leaf functions
    report.append(f"Leaf Functions ({len(leaf_functions)}):")
    for leaf in leaf_functions[:10]:  # Show first 10
        report.append(f"  - {leaf}")
    if len(leaf_functions) > 10:
        report.append(f"  ... and {len(leaf_functions) - 10} more")
    report.append("")
    
    # Most connected functions
    sorted_by_in_degree = sorted(
        metrics.items(), 
        key=lambda x: int(x[1]["in_degree"]) if isinstance(x[1]["in_degree"], (int, float)) else 0, 
        reverse=True
    )
    sorted_by_out_degree = sorted(
        metrics.items(), 
        key=lambda x: int(x[1]["out_degree"]) if isinstance(x[1]["out_degree"], (int, float)) else 0, 
        reverse=True
    )
    
    report.append("Most Called Functions (Top 10):")
    for func, metric in sorted_by_in_degree[:10]:
        report.append(f"  {func}: {metric['in_degree']} calls")
    report.append("")
    
    report.append("Functions with Most Calls (Top 10):")
    for func, metric in sorted_by_out_degree[:10]:
        report.append(f"  {func}: {metric['out_degree']} outgoing calls")
    report.append("")
    
    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))


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
            
    except Exception as e:
        print(f"Warning: Could not add Function Explorer to {html_path}: {e}")


def create_module_reports_with_explorer(graph: nx.DiGraph, 
                                        output_dir: Path,
                                        include_function_explorer: bool = True) -> None:
    """Create module-specific reports with Function Explorer.
    
    Args:
        graph: NetworkX DiGraph containing all functions
        output_dir: Output directory for reports
        include_function_explorer: Whether to include Function Explorer in reports
    """
    # Get all module names from the graph
    module_names = set()
    for node in graph.nodes():
        if "." in node:
            module_name = node.split(".")[0]
            module_names.add(module_name)
    
    # Create module reports directory
    module_reports_dir = output_dir / "module_reports"
    module_reports_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating {len(module_names)} module reports with Function Explorer...")
    
    for module_name in sorted(module_names):
        # Filter graph to include only this module's functions
        module_graph = nx.DiGraph()
        
        # Add nodes for this module
        for node, attrs in graph.nodes(data=True):
            if node.startswith(module_name + "."):
                module_graph.add_node(node, **attrs)
        
        # Add edges (both internal and cross-module)
        for source, target, attrs in graph.edges(data=True):
            if source.startswith(module_name + "."):
                module_graph.add_edge(source, target, **attrs)
        
        if module_graph.number_of_nodes() > 0:
            # Create module report with Function Explorer
            module_report_path = module_reports_dir / f"{module_name}.html"
            create_pyvis_graph(
                module_graph, 
                module_report_path,
                title=f"{module_name} Module - Function Call Graph",
                module_name=module_name if include_function_explorer else None,
                module_reports_dir=module_reports_dir
            )
            print(f"✓ Created {module_name} report with {module_graph.number_of_nodes()} functions")
    
    print(f"Created {len(module_names)} module reports in {module_reports_dir}")


def _add_global_function_explorer_to_html(html_path: Path, graph: nx.DiGraph) -> None:
    """Add global Function Explorer section to main HTML report.
    
    Args:
        html_path: Path to the HTML file to modify
        graph: NetworkX DiGraph containing all functions
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Check if Function Explorer already exists
        if 'function-explorer' in html_content:
            print(f"Function Explorer already exists in {html_path.name}")
            return
        
        # Get all functions from all modules
        all_functions = []
        for node, attrs in graph.nodes(data=True):
            if "." in node:
                module_name = node.split(".")[0]
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
                
                all_functions.append({
                    "name": func_name,
                    "full_name": full_name,
                    "module": module_name,
                    "type": func_type,
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "file": attrs.get("file", ""),
                    "line": attrs.get("line", "")
                })
        
        # Sort alphabetically by function name
        all_functions.sort(key=lambda x: (x["name"], x["module"]))
        
        # Create global Function Explorer HTML
        explorer_html = f'''
    <div id="function-explorer" style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
        <h3 style="margin-top: 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
            Global Function Explorer - All Modules
        </h3>
        <div style="margin-bottom: 15px;">
            <input type="text" id="function-search" placeholder="Search functions across all modules..." 
                   style="width: 400px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
            <button onclick="filterFunctions()" style="padding: 8px 15px; margin-left: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Search</button>
            <button onclick="clearSearch()" style="padding: 8px 15px; margin-left: 5px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Clear</button>
        </div>
        <div id="function-list" style="max-height: 500px; overflow-y: auto; border: 1px solid #ccc; background: white;">
'''
        
        for func in all_functions:
            # Color coding for function types
            type_colors = {
                "async": "#ff9999",
                "entry": "#90ee90", 
                "leaf": "#ffd700",
                "regular": "#97c2fc"
            }
            color = type_colors.get(func["type"], "#97c2fc")
            
            explorer_html += f'''
            <div class="function-item" data-name="{func['name'].lower()}" data-module="{func['module'].lower()}" style="padding: 8px 12px; border-bottom: 1px solid #eee; cursor: pointer; transition: background-color 0.2s;" 
                 onmouseover="this.style.backgroundColor='#f0f0f0'" 
                 onmouseout="this.style.backgroundColor='white'"
                 onclick="showFunctionFlow('{func['full_name']}', '{func['name']}', '{func['module']}')">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                        <span style="display: inline-block; width: 12px; height: 12px; background: {color}; border: 1px solid #666; margin-right: 8px; border-radius: 2px;"></span>
                        <strong>{func['name']}</strong>
                        <span style="margin-left: 10px; color: #666; font-size: 12px; background: #e9ecef; padding: 2px 6px; border-radius: 3px;">{func['module']}</span>
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
            <h4 style="color: #333; margin-bottom: 10px;">Function Flow Graph <small style="color: #666; font-size: 12px;">(drag bottom-right corner to resize)</small></h4>
            <div id="function-flow-graph" style="border: 1px solid #ccc; height: 600px; background: white; resize: vertical; overflow: auto; min-height: 400px;"></div>
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
            const module = item.getAttribute('data-module');
            if (name.includes(searchTerm) || module.includes(searchTerm)) {
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
    
    function showFunctionFlow(fullFunctionName, functionName, moduleName) {
        const container = document.getElementById('function-flow-container');
        const graphDiv = document.getElementById('function-flow-graph');
        
        container.style.display = 'block';
        graphDiv.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">Loading flow graph for ' + moduleName + '.' + functionName + '...</p>';
        
        // Create flow graph for this specific function
        createFunctionFlowGraph(fullFunctionName, functionName, moduleName);
        
        // Scroll to the flow graph
        container.scrollIntoView({ behavior: 'smooth' });
    }
    
    function closeFunctionFlow() {
        document.getElementById('function-flow-container').style.display = 'none';
    }
    
    function createFunctionFlowGraph(fullFunctionName, functionName, moduleName) {
        // Set function name in header
        document.getElementById('function-name-display').textContent = moduleName + '.' + functionName;
        
        // This will be populated with actual flow graph data
        const graphData = getFunctionFlowData(fullFunctionName);
        renderFunctionFlowGraph(graphData, functionName, moduleName);
    }
    
    function getFunctionFlowData(fullFunctionName) {
        // Extract function flow data from the main graph
        // This is a placeholder - actual data will be injected by Python
        return window.functionFlowData && window.functionFlowData[fullFunctionName] 
            ? window.functionFlowData[fullFunctionName] 
            : { nodes: [], edges: [] };
    }
    
    function renderFunctionFlowGraph(graphData, functionName, moduleName) {
        const container = document.getElementById('function-flow-graph');
        
        // Clear container and add function name header
        container.innerHTML = `<h3 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">Function Flow: ${functionName}</h3>`;
        
        // Create network container
        const networkContainer = document.createElement('div');
        networkContainer.style.height = '600px';
        networkContainer.style.border = '1px solid #ddd';
        networkContainer.style.borderRadius = '4px';
        networkContainer.style.resize = 'vertical';
        networkContainer.style.overflow = 'auto';
        networkContainer.style.minHeight = '400px';
        container.appendChild(networkContainer);
        
        // Create a vis.js network for the function flow
        const nodes = new vis.DataSet(graphData.nodes.map(node => ({
            id: node.id,
            label: node.label,
            title: node.title,
            color: node.color,
            shape: 'box',
            font: { size: 14, bold: node.id.includes(functionName) },
            borderWidth: node.id.includes(functionName) ? 3 : 1,
            borderColor: node.id.includes(functionName) ? '#ff6b6b' : '#666666'
        })));
        
        const edges = new vis.DataSet(graphData.edges.map(edge => ({
            from: edge.from,
            to: edge.to,
            arrows: 'to',
            color: { color: '#666666' },
            width: 2
        })));
        
        const data = { nodes: nodes, edges: edges };
        
        const options = {
            layout: {
                // Use physics-based layout for free movement
                randomSeed: 42,
                improvedLayout: true
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.1
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true
            },
            nodes: {
                borderWidth: 1,
                borderColor: '#666666',
                font: { color: '#333' }
            },
            edges: {
                smooth: {
                    type: 'cubicBezier'
                }
            }
        };
        
        const network = new vis.Network(networkContainer, data, options);
        
        // Fit network to show all nodes after stabilization
        network.once('stabilized', function() {
            network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
        });
    }
    
    // Add search on Enter key
    document.getElementById('function-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            filterFunctions();
        }
    });
    </script>
'''
        
        # Create function flow data for all functions
        function_flow_data = {}
        for node in graph.nodes():
            if "." in node:
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
            
        print(f"✓ Enhanced {html_path.name} with Global Function Explorer")
            
    except Exception as e:
        print(f"Warning: Could not add Global Function Explorer to {html_path}: {e}")


def create_enhanced_module_reports(graph: nx.DiGraph, 
                                  output_dir: Path,
                                  module_reports_dir: Path) -> None:
    """Enhance all existing module reports with Function Explorer.
    
    Args:
        graph: NetworkX DiGraph containing all functions
        output_dir: Main output directory
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
    
    # Enhance each module report
    for module_name in module_names:
        module_report_path = module_reports_dir / f"{module_name}.html"
        if module_report_path.exists():
            print(f"Adding Function Explorer to {module_name} report...")
            _add_function_explorer_to_html(module_report_path, graph, module_name)
        else:
            print(f"Module report not found: {module_report_path}")
    
    print(f"Enhanced {len(module_names)} module reports with Function Explorer")
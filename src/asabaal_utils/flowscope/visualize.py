import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json


def create_pyvis_graph(graph: nx.DiGraph, 
                      output_path: Path,
                      title: str = "Function Call Graph",
                      height: str = "750px",
                      width: str = "100%") -> None:
    """Create an interactive HTML visualization using pyvis.
    
    Args:
        graph: NetworkX DiGraph to visualize
        output_path: Output HTML file path
        title: Graph title
        height: Graph height
        width: Graph width
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
    
    # Add title
    net.set_options(f'''
    var options = {{
      "title": {{
        "text": "{title}",
        "hierarchical": false
      }}
    }}
    ''')
    
    # Add nodes with styling
    for node, attrs in graph.nodes(data=True):
        # Determine node color based on properties
        color = "#97c2fc"  # Default blue
        
        if attrs.get("cross_module"):
            color = "#ff6b6b"  # Red for cross-module functions
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
        
        tooltip_parts.append(f"In-degree: {graph.in_degree(node)}")
        tooltip_parts.append(f"Out-degree: {graph.out_degree(node)}")
        
        tooltip = "\n".join(tooltip_parts)
        
        # Add border for cross-module functions
        border_width = 3 if attrs.get("cross_module") else 1
        border_color = "#ff0000" if attrs.get("cross_module") else "#666666"
        
        net.add_node(
            node,
            label=node.split(".")[-1],  # Show only function name
            title=tooltip,
            color=color,
            border=border_width,
            borderColor=border_color,
            font={"size": 12, "color": "#333333"}
        )
    
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
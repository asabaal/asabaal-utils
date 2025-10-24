import networkx as nx
from typing import Dict, List, Set, Tuple, Any, Optional
from pathlib import Path


def compare_graphs(old_graph: nx.DiGraph, new_graph: nx.DiGraph) -> Dict[str, Any]:
    """Compare two call graphs and identify differences.
    
    Args:
        old_graph: Original/previous version of the call graph
        new_graph: New/current version of the call graph
        
    Returns:
        Dictionary containing detailed comparison results
    """
    old_nodes = set(old_graph.nodes())
    new_nodes = set(new_graph.nodes())
    old_edges = set(old_graph.edges())
    new_edges = set(new_graph.edges())
    
    # Calculate differences
    added_nodes = new_nodes - old_nodes
    removed_nodes = old_nodes - new_nodes
    common_nodes = old_nodes & new_nodes
    
    added_edges = new_edges - old_edges
    removed_edges = old_edges - new_edges
    common_edges = old_edges & new_edges
    
    # Analyze node changes
    node_changes = {}
    for node in common_nodes:
        old_attrs = dict(old_graph.nodes[node])
        new_attrs = dict(new_graph.nodes[node])
        
        if old_attrs != new_attrs:
            node_changes[node] = {
                "old_attributes": old_attrs,
                "new_attributes": new_attrs,
                "changes": _compare_attributes(old_attrs, new_attrs)
            }
    
    # Analyze edge changes
    edge_changes = {}
    for edge in common_edges:
        old_attrs = dict(old_graph.edges[edge])
        new_attrs = dict(new_graph.edges[edge])
        
        if old_attrs != new_attrs:
            edge_changes[edge] = {
                "old_attributes": old_attrs,
                "new_attributes": new_attrs,
                "changes": _compare_attributes(old_attrs, new_attrs)
            }
    
    return {
        "summary": {
            "added_nodes": len(added_nodes),
            "removed_nodes": len(removed_nodes),
            "added_edges": len(added_edges),
            "removed_edges": len(removed_edges),
            "node_changes": len(node_changes),
            "edge_changes": len(edge_changes)
        },
        "added_nodes": list(added_nodes),
        "removed_nodes": list(removed_nodes),
        "added_edges": [list(edge) for edge in added_edges],
        "removed_edges": [list(edge) for edge in removed_edges],
        "node_changes": node_changes,
        "edge_changes": edge_changes
    }


def _compare_attributes(old_attrs: Dict[str, Any], new_attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Compare attribute dictionaries and identify changes."""
    changes = {}
    
    all_keys = set(old_attrs.keys()) | set(new_attrs.keys())
    
    for key in all_keys:
        old_val = old_attrs.get(key)
        new_val = new_attrs.get(key)
        
        if old_val != new_val:
            changes[key] = {
                "old": old_val,
                "new": new_val
            }
    
    return changes


def analyze_impact(graph_diff: Dict[str, Any], graph: nx.DiGraph) -> Dict[str, Any]:
    """Analyze the impact of changes on the overall graph structure.
    
    Args:
        graph_diff: Result from compare_graphs
        graph: The new graph to analyze impact on
        
    Returns:
        Dictionary containing impact analysis
    """
    impact = {
        "critical_changes": [],
        "affected_modules": set(),
        "breaking_changes": [],
        "api_changes": []
    }
    
    # Analyze removed nodes (potential breaking changes)
    for node in graph_diff["removed_nodes"]:
        # Check if this was a public API function
        if not node.startswith("_") and "." in node:
            impact["breaking_changes"].append({
                "type": "removed_function",
                "function": node,
                "reason": "Public function was removed"
            })
        
        # Track affected modules
        if "." in node:
            module = node.split(".")[0]
            impact["affected_modules"].add(module)
    
    # Analyze added nodes
    for node in graph_diff["added_nodes"]:
        if "." in node:
            module = node.split(".")[0]
            impact["affected_modules"].add(module)
    
    # Analyze removed edges
    for edge in graph_diff["removed_edges"]:
        source, target = edge
        if "." in source:
            module = source.split(".")[0]
            impact["affected_modules"].add(module)
    
    # Convert set to list for JSON serialization
    impact["affected_modules"] = list(impact["affected_modules"])
    
    return impact


def get_drift_timeline(snapshots: List[Path]) -> List[Dict[str, Any]]:
    """Create a timeline of changes across multiple snapshots.
    
    Note: This function requires the caller to handle graph loading.
    
    Args:
        snapshots: List of snapshot file paths in chronological order
        
    Returns:
        List of drift analyses between consecutive snapshots
    """
    # This function is simplified to avoid import issues
    # Users should call this with pre-loaded graphs or handle loading separately
    raise NotImplementedError(
        "get_drift_timeline requires graph loading to be handled by the caller. "
        "Use compare_graphs directly with loaded graphs."
    )
    
    for i in range(len(snapshots) - 1):
        old_graph = load_graph(snapshots[i])
        new_graph = load_graph(snapshots[i + 1])
        
        diff = compare_graphs(old_graph, new_graph)
        impact = analyze_impact(diff, new_graph)
        
        timeline.append({
            "from_snapshot": str(snapshots[i]),
            "to_snapshot": str(snapshots[i + 1]),
            "diff": diff,
            "impact": impact
        })
    
    return timeline


def detect_architecture_drift(graph_diff: Dict[str, Any]) -> Dict[str, Any]:
    """Detect significant architectural changes in the codebase.
    
    Args:
        graph_diff: Result from compare_graphs
        
    Returns:
        Dictionary containing architectural drift analysis
    """
    drift = {
        "module_changes": {},
        "dependency_changes": {},
        "complexity_changes": {}
    }
    
    # Analyze module-level changes
    added_modules = set()
    removed_modules = set()
    
    for node in graph_diff["added_nodes"]:
        if "." in node:
            added_modules.add(node.split(".")[0])
    
    for node in graph_diff["removed_nodes"]:
        if "." in node:
            removed_modules.add(node.split(".")[0])
    
    drift["module_changes"] = {
        "added_modules": list(added_modules),
        "removed_modules": list(removed_modules)
    }
    
    # Analyze dependency changes
    added_edges = graph_diff["added_edges"]
    removed_edges = graph_diff["removed_edges"]
    
    cross_module_added = []
    cross_module_removed = []
    
    for edge in added_edges:
        if len(edge) >= 2:
            source, target = edge[0], edge[1]
            if "." in source and "." in target:
                source_module = source.split(".")[0]
                target_module = target.split(".")[0]
                if source_module != target_module:
                    cross_module_added.append(f"{source_module} -> {target_module}")
    
    for edge in removed_edges:
        if len(edge) >= 2:
            source, target = edge[0], edge[1]
            if "." in source and "." in target:
                source_module = source.split(".")[0]
                target_module = target.split(".")[0]
                if source_module != target_module:
                    cross_module_removed.append(f"{source_module} -> {target_module}")
    
    drift["dependency_changes"] = {
        "added_cross_module_dependencies": cross_module_added,
        "removed_cross_module_dependencies": cross_module_removed
    }
    
    return drift


def generate_drift_report(graph_diff: Dict[str, Any], 
                        old_snapshot: Optional[str] = None,
                        new_snapshot: Optional[str] = None) -> str:
    """Generate a human-readable drift report.
    
    Args:
        graph_diff: Result from compare_graphs
        old_snapshot: Path/name of old snapshot
        new_snapshot: Path/name of new snapshot
        
    Returns:
        Formatted string report
    """
    report = []
    
    if old_snapshot and new_snapshot:
        report.append(f"Drift Analysis: {old_snapshot} → {new_snapshot}")
        report.append("=" * 50)
    else:
        report.append("Drift Analysis Report")
        report.append("=" * 30)
    
    summary = graph_diff["summary"]
    report.append(f"Added Functions: {summary['added_nodes']}")
    report.append(f"Removed Functions: {summary['removed_nodes']}")
    report.append(f"Added Calls: {summary['added_edges']}")
    report.append(f"Removed Calls: {summary['removed_edges']}")
    report.append("")
    
    if graph_diff["added_nodes"]:
        report.append("Added Functions:")
        for node in graph_diff["added_nodes"]:
            report.append(f"  + {node}")
        report.append("")
    
    if graph_diff["removed_nodes"]:
        report.append("Removed Functions:")
        for node in graph_diff["removed_nodes"]:
            report.append(f"  - {node}")
        report.append("")
    
    if graph_diff["added_edges"]:
        report.append("Added Calls:")
        for edge in graph_diff["added_edges"]:
            if len(edge) >= 2:
                report.append(f"  + {edge[0]} → {edge[1]}")
        report.append("")
    
    if graph_diff["removed_edges"]:
        report.append("Removed Calls:")
        for edge in graph_diff["removed_edges"]:
            if len(edge) >= 2:
                report.append(f"  - {edge[0]} → {edge[1]}")
        report.append("")
    
    return "\n".join(report)
"""
FlowScope — Function-Level Code Flow and Drift Analysis Tool

FlowScope analyzes Python codebases to generate and compare function-level call graphs.
It helps track code evolution and understand function relationships across projects.
"""

# Import key functions directly
from .scanner import scan_directory, scan_file
from .graph import (
    get_graph_stats,
    get_function_metrics,
    find_entry_points,
    find_leaf_functions,
    get_call_chains,
    get_module_summary,
    detect_cycles,
    get_critical_path,
    filter_graph_by_module,
    merge_graphs
)
from .snapshot import (
    save_graph,
    load_graph,
    get_snapshot_metadata,
    compare_snapshots,
    create_snapshot_with_context,
    list_snapshots
)
from .drift import (
    compare_graphs,
    analyze_impact,
    detect_architecture_drift,
    generate_drift_report
)
from .visualize import (
    create_pyvis_graph,
    create_static_graph,
    create_module_view,
    create_drift_visualization,
    export_graph_data,
    create_summary_report
)
from .cli import main

__version__ = "1.0.0"
__author__ = "FlowScope Team"

# Export main functions for easy access
__all__ = [
    # Core scanning
    "scan_directory",
    "scan_file",
    
    # Graph analysis
    "get_graph_stats",
    "get_function_metrics", 
    "find_entry_points",
    "find_leaf_functions",
    "get_call_chains",
    "get_module_summary",
    "detect_cycles",
    "get_critical_path",
    "filter_graph_by_module",
    "merge_graphs",
    
    # Snapshot management
    "save_graph",
    "load_graph",
    "get_snapshot_metadata",
    "compare_snapshots",
    "create_snapshot_with_context",
    "list_snapshots",
    
    # Drift analysis
    "compare_graphs",
    "analyze_impact",
    "detect_architecture_drift",
    "generate_drift_report",
    
    # Visualization
    "create_pyvis_graph",
    "create_static_graph",
    "create_module_view",
    "create_drift_visualization",
    "export_graph_data",
    "create_summary_report",
    
    # CLI
    "main"
]

# CLI entry point
def cli():
    """Entry point for command-line interface."""
    main()

# Convenience function for quick analysis
def quick_scan(path, output_file="flow_graph.json", create_viz=False):
    """Quick scan a path and save results.
    
    Args:
        path: Path to scan (file or directory)
        output_file: Output file for the graph snapshot
        create_viz: Whether to create an HTML visualization
        
    Returns:
        NetworkX DiGraph of the scanned code
    """
    from pathlib import Path
    
    path_obj = Path(path)
    
    if path_obj.is_file():
        graph = scan_file(path_obj)
    else:
        graph = scan_directory(path_obj)
    
    # Save graph
    save_graph(graph, Path(output_file))
    
    # Create visualization if requested
    if create_viz:
        viz_path = Path(output_file).with_suffix(".html")
        create_pyvis_graph(graph, viz_path)
    
    return graph
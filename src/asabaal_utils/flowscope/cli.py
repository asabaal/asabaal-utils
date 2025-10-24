#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import Optional
import networkx as nx

# Import flowscope modules
from .scanner import scan_directory, scan_file
from .snapshot import save_graph, load_graph, get_snapshot_metadata
from .drift import compare_graphs, generate_drift_report
from .visualize import (
    create_pyvis_graph, 
    create_static_graph, 
    create_module_view,
    create_drift_visualization,
    create_summary_report,
    export_graph_data
)


def cmd_scan(args) -> None:
    """Scan a directory or file and create a graph snapshot."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning '{path}'...")
    
    try:
        if path.is_file():
            graph = scan_file(path)
        else:
            exclude_patterns = set(args.exclude) if args.exclude else None
            graph = scan_directory(path, exclude_patterns)
        
        print(f"Found {graph.number_of_nodes()} functions and {graph.number_of_edges()} calls")
        
        # Create metadata
        metadata = {
            "source_path": str(path.absolute()),
            "description": args.description,
            "scan_type": "file" if path.is_file() else "directory"
        }
        
        # Save graph
        output_path = Path(args.output)
        save_graph(graph, output_path, metadata)
        
        print(f"Graph saved to '{output_path}'")
        
        # Generate visualization if requested
        if args.visualize:
            viz_path = output_path.with_suffix(".html")
            module_reports_dir = Path(args.module_reports) if args.module_reports else None
            create_pyvis_graph(graph, viz_path, title=f"Call Graph: {path.name}", module_reports_dir=module_reports_dir)
            print(f"Visualization saved to '{viz_path}'")
            if module_reports_dir:
                print(f"Cross-module nodes will link to reports in: {module_reports_dir}")
            
    except Exception as e:
        print(f"Error during scanning: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_compare(args) -> None:
    """Compare two graph snapshots."""
    old_path = Path(args.old)
    new_path = Path(args.new)
    
    if not old_path.exists():
        print(f"Error: Old snapshot '{old_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    if not new_path.exists():
        print(f"Error: New snapshot '{new_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Comparing '{old_path.name}' → '{new_path.name}'...")
    
    try:
        old_graph = load_graph(old_path)
        new_graph = load_graph(new_path)
        
        diff = compare_graphs(old_graph, new_graph)
        
        # Print summary
        summary = diff["summary"]
        print(f"\nSummary:")
        print(f"  Added functions: {summary['added_nodes']}")
        print(f"  Removed functions: {summary['removed_nodes']}")
        print(f"  Added calls: {summary['added_edges']}")
        print(f"  Removed calls: {summary['removed_edges']}")
        
        # Save detailed report
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix == ".json":
                import json
                with open(output_path, "w") as f:
                    json.dump(diff, f, indent=2)
            else:
                report = generate_drift_report(diff, str(old_path), str(new_path))
                with open(output_path, "w") as f:
                    f.write(report)
            print(f"Detailed report saved to '{output_path}'")
        
        # Generate visualization if requested
        if args.visualize:
            viz_path = Path(args.visualize)
            create_drift_visualization(old_graph, new_graph, viz_path)
            print(f"Drift visualization saved to '{viz_path}'")
            
    except Exception as e:
        print(f"Error during comparison: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_visualize(args) -> None:
    """Create visualization from a graph snapshot."""
    graph_path = Path(args.graph)
    
    if not graph_path.exists():
        print(f"Error: Graph file '{graph_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading graph from '{graph_path}'...")
    
    try:
        graph = load_graph(graph_path)
        print(f"Loaded {graph.number_of_nodes()} functions and {graph.number_of_edges()} calls")
        
        output_path = Path(args.output)
        
        if args.type == "interactive":
            module_reports_dir = Path(args.module_reports) if args.module_reports else None
            create_pyvis_graph(graph, output_path, title=args.title, module_reports_dir=module_reports_dir)
        elif args.type == "static":
            create_static_graph(
                graph, 
                output_path, 
                layout=args.layout,
                figsize=(args.width, args.height)
            )
        elif args.type == "modules":
            create_module_view(graph, output_path, title=args.title)
        else:
            print(f"Error: Unknown visualization type '{args.type}'", file=sys.stderr)
            sys.exit(1)
        
        print(f"Visualization saved to '{output_path}'")
        
    except Exception as e:
        print(f"Error during visualization: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_info(args) -> None:
    """Show information about a graph snapshot."""
    graph_path = Path(args.graph)
    
    if not graph_path.exists():
        print(f"Error: Graph file '{graph_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    try:
        metadata = get_snapshot_metadata(graph_path)
        
        print(f"Graph: {graph_path.name}")
        print(f"Version: {metadata['version']}")
        print(f"Created: {metadata['created_at']}")
        print(f"Functions: {metadata['node_count']}")
        print(f"Calls: {metadata['edge_count']}")
        
        if metadata['metadata']:
            print("\nMetadata:")
            for key, value in metadata['metadata'].items():
                print(f"  {key}: {value}")
        
        # Load graph for additional stats if requested
        if args.detailed:
            graph = load_graph(graph_path)
            
            # Calculate basic stats
            entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]
            leaf_functions = [n for n in graph.nodes() if graph.out_degree(n) == 0]
            
            print(f"\nDetailed Statistics:")
            print(f"  Entry points: {len(entry_points)}")
            print(f"  Leaf functions: {len(leaf_functions)}")
            print(f"  Is strongly connected: {nx.is_strongly_connected(graph)}")
            print(f"  Weak components: {nx.number_weakly_connected_components(graph)}")
            
            if entry_points:
                print(f"\nEntry Points (first 10):")
                for entry in entry_points[:10]:
                    print(f"  - {entry}")
        
    except Exception as e:
        print(f"Error reading graph info: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_export(args) -> None:
    """Export graph data in various formats."""
    graph_path = Path(args.graph)
    output_path = Path(args.output)
    
    if not graph_path.exists():
        print(f"Error: Graph file '{graph_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    try:
        graph = load_graph(graph_path)
        export_graph_data(graph, output_path, args.format)
        print(f"Graph exported to '{output_path}' in {args.format} format")
        
    except Exception as e:
        print(f"Error during export: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_report(args) -> None:
    """Generate a summary report for a graph."""
    graph_path = Path(args.graph)
    output_path = Path(args.output)
    
    if not graph_path.exists():
        print(f"Error: Graph file '{graph_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    try:
        graph = load_graph(graph_path)
        create_summary_report(graph, output_path)
        print(f"Summary report saved to '{output_path}'")
        
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FlowScope - Function-Level Code Flow and Drift Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  flowscope scan src/ --output project.json
  flowscope scan main.py --output main.json --visualize
  flowscope compare old.json new.json --output diff.txt --visualize drift.html
  flowscope visualize project.json --output viz.html --type interactive
  flowscope info project.json --detailed
        """
    )
    
    subparsers = parser.add_subparsers(dest="cmd", help="Available commands")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directory or file")
    scan_parser.add_argument("path", help="Path to scan")
    scan_parser.add_argument("--output", "-o", default="flow_graph.json", 
                           help="Output file path (default: flow_graph.json)")
    scan_parser.add_argument("--exclude", nargs="*", 
                           help="Patterns to exclude from scanning")
    scan_parser.add_argument("--description", help="Description for this snapshot")
    scan_parser.add_argument("--visualize", action="store_true",
                           help="Generate HTML visualization")
    scan_parser.add_argument("--module-reports", 
                           help="Directory containing module-specific HTML reports for cross-module linking")
    scan_parser.set_defaults(func=cmd_scan)
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two snapshots")
    compare_parser.add_argument("old", help="Old snapshot file")
    compare_parser.add_argument("new", help="New snapshot file")
    compare_parser.add_argument("--output", "-o", help="Output file for detailed report")
    compare_parser.add_argument("--visualize", help="Generate drift visualization")
    compare_parser.set_defaults(func=cmd_compare)
    
    # Visualize command
    viz_parser = subparsers.add_parser("visualize", help="Create visualization")
    viz_parser.add_argument("graph", help="Graph snapshot file")
    viz_parser.add_argument("--output", "-o", default="flow_graph.html",
                          help="Output file path (default: flow_graph.html)")
    viz_parser.add_argument("--type", choices=["interactive", "static", "modules"],
                           default="interactive", help="Visualization type")
    viz_parser.add_argument("--title", default="Function Call Graph",
                           help="Graph title")
    viz_parser.add_argument("--layout", choices=["spring", "circular", "random", "shell"],
                           default="spring", help="Layout for static visualization")
    viz_parser.add_argument("--width", type=int, default=12, help="Width for static visualization")
    viz_parser.add_argument("--height", type=int, default=8, help="Height for static visualization")
    viz_parser.add_argument("--module-reports", 
                           help="Directory containing module-specific HTML reports for cross-module linking")
    viz_parser.set_defaults(func=cmd_visualize)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show graph information")
    info_parser.add_argument("graph", help="Graph snapshot file")
    info_parser.add_argument("--detailed", action="store_true",
                           help="Show detailed statistics")
    info_parser.set_defaults(func=cmd_info)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export graph data")
    export_parser.add_argument("graph", help="Graph snapshot file")
    export_parser.add_argument("--output", "-o", required=True, help="Output file path")
    export_parser.add_argument("--format", choices=["json", "gexf", "graphml", "csv"],
                              default="json", help="Export format")
    export_parser.set_defaults(func=cmd_export)
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate summary report")
    report_parser.add_argument("graph", help="Graph snapshot file")
    report_parser.add_argument("--output", "-o", default="flow_report.txt",
                             help="Output file path (default: flow_report.txt)")
    report_parser.set_defaults(func=cmd_report)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
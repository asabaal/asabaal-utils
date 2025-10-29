#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import Optional
import networkx as nx

# Import flowscope modules
try:
    from .scanner import scan_directory, scan_file
    from .snapshot import save_graph, load_graph, get_snapshot_metadata
    from .drift import compare_graphs, generate_drift_report
    from .visualize import (
        create_pyvis_graph, 
        create_static_graph, 
        create_module_view,
        create_drift_visualization,
        create_summary_report,
        export_graph_data,
        create_module_reports_with_explorer
    )
except ImportError:
    from scanner import scan_directory, scan_file
    from snapshot import save_graph, load_graph, get_snapshot_metadata
    from drift import compare_graphs, generate_drift_report
    from visualize import (
        create_pyvis_graph, 
        create_static_graph, 
        create_module_view,
        create_drift_visualization,
        create_summary_report,
        export_graph_data,
        create_module_reports_with_explorer
    )


def cmd_scan(args) -> None:
    """Scan a directory or file and create a complete analysis."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning '{path}'...")
    
    try:
        # Always enable all features
        analyze_functions = True
        exclude_patterns = set(args.exclude) if args.exclude else None
        
        # Set up output directory
        if path.is_file():
            output_dir = path.parent / "flowscope_analysis"
            graph = scan_file(path)
        else:
            output_dir = path / "flowscope_analysis"
            graph = scan_directory(path, exclude_patterns, analyze_functions, output_dir)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set output file paths
        graph_file = output_dir / "flowscope.json"
        viz_file = output_dir / "flowscope_visualization.html"
        module_view_path = output_dir / "module_view.html"
        summary_path = output_dir / "flowscope_report.md"
        
        print(f"Found {graph.number_of_nodes()} functions and {graph.number_of_edges()} calls")
        
        # Create metadata
        metadata = {
            "source_path": str(path.absolute()),
            "description": getattr(args, 'description', f"FlowScope analysis of {path.name}"),
            "scan_type": "file" if path.is_file() else "directory"
        }
        
        # Save graph
        save_graph(graph, graph_file, metadata)
        print(f"Graph saved to '{graph_file}'")
        
        # Always generate all visualizations and reports
        # Create module view
        create_module_view(graph, module_view_path, title=f"Module View: {path.name}")
        print(f"Module view saved to '{module_view_path}'")
        
        # Create summary report
        create_summary_report(graph, summary_path)
        print(f"Summary report saved to '{summary_path}'")
        
        # Create main visualization with module reports
        create_pyvis_graph(graph, viz_file, title=f"Call Graph: {path.name}", module_reports_dir=output_dir)
        print(f"Visualization saved to '{viz_file}'")
        print(f"Module reports available in: {output_dir}")
        
        print(f"\nAnalysis complete! Open '{viz_file}' to start exploring.")
            
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


def cmd_analyze(args) -> None:
    """Analyze a directory and create comprehensive reports with Function Explorer."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing '{path}'...")
    
    try:
        # Scan the directory
        exclude_patterns = set(args.exclude) if args.exclude else None
        graph = scan_directory(path, exclude_patterns)
        
        print(f"Found {graph.number_of_nodes()} functions and {graph.number_of_edges()} calls")
        
        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main visualization
        main_viz_path = output_dir / "flowscope_visualization.html"
        module_reports_dir = output_dir / "module_reports"
        create_pyvis_graph(
            graph, 
            main_viz_path, 
            title="FlowScope Analysis - Function Call Graph",
            module_reports_dir=module_reports_dir
        )
        print(f"✓ Created main visualization: {main_viz_path}")
        
        # Create module reports with Function Explorer
        if args.modules:
            create_module_reports_with_explorer(graph, output_dir, include_function_explorer=True)
        
        # Create summary report
        summary_path = output_dir / "flowscope_report.md"
        create_summary_report(graph, summary_path)
        print(f"✓ Created summary report: {summary_path}")
        
        # Create module view if requested
        if args.module_view:
            module_view_path = output_dir / "module_view.html"
            create_module_view(graph, module_view_path)
            print(f"✓ Created module view: {module_view_path}")
        
        print(f"\nAnalysis complete! Reports saved to: {output_dir}")
        print(f"Open {main_viz_path} to start exploring.")
        
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FlowScope - Function-Level Code Flow and Drift Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  flowscope src/
  flowscope . --exclude out node_modules
        """
    )
    
    # Main arguments
    parser.add_argument("path", help="Path to scan")
    parser.add_argument("--exclude", nargs="*", 
                       help="Patterns to exclude from scanning")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up automatic output directory and enable all features
    target_path = Path(args.path)
    if target_path.is_file():
        output_dir = target_path.parent / "flowscope_analysis"
    else:
        output_dir = target_path / "flowscope_analysis"
    
    # Configure args for full analysis
    args.output = output_dir / "flowscope.json"
    args.visualize = True
    args.analyze_functions = True
    args.description = f"FlowScope analysis of {target_path.name}"
    
    # Execute main scan logic
    cmd_scan(args)


if __name__ == "__main__":
    main()
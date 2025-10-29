#!/usr/bin/env python3
"""
Enhance existing FlowScope reports with Function Explorer functionality.
"""

import json
from pathlib import Path
import networkx as nx
from .visualize import create_function_explorer_section, create_function_flow_data


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


def enhance_main_visualization(main_html_path: Path, graph: nx.DiGraph) -> None:
    """Enhance the main visualization with a module overview.
    
    Args:
        main_html_path: Path to the main HTML visualization
        graph: NetworkX DiGraph containing all functions
    """
    try:
        with open(main_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Get module statistics
        module_stats = {}
        for node in graph.nodes():
            if "." in node:
                module_name = node.split(".")[0]
                if module_name not in module_stats:
                    module_stats[module_name] = {
                        "functions": 0,
                        "calls": 0,
                        "entry_points": 0,
                        "leaf_functions": 0
                    }
                
                module_stats[module_name]["functions"] += 1
                module_stats[module_name]["calls"] += graph.out_degree(node)
                
                if graph.in_degree(node) == 0:
                    module_stats[module_name]["entry_points"] += 1
                if graph.out_degree(node) == 0:
                    module_stats[module_name]["leaf_functions"] += 1
        
        # Create module overview HTML
        overview_html = '''
        <div id="module-overview" style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
            <h3 style="margin-top: 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                Module Overview
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
'''
        
        for module_name, stats in sorted(module_stats.items()):
            overview_html += f'''
                <div style="border: 1px solid #ccc; padding: 15px; border-radius: 5px; background: white;">
                    <h4 style="margin: 0 0 10px 0; color: #007bff;">{module_name}</h4>
                    <div style="font-size: 14px; line-height: 1.4;">
                        <div><strong>Functions:</strong> {stats["functions"]}</div>
                        <div><strong>Total Calls:</strong> {stats["calls"]}</div>
                        <div><strong>Entry Points:</strong> {stats["entry_points"]}</div>
                        <div><strong>Leaf Functions:</strong> {stats["leaf_functions"]}</div>
                    </div>
                </div>
'''
        
        overview_html += '''
            </div>
        </div>
'''
        
        # Insert after the opening body tag
        if '<body>' in html_content:
            html_content = html_content.replace('<body>', f'<body>{overview_html}')
        else:
            html_content = f'<body>{overview_html}{html_content}'
        
        # Write back to file
        with open(main_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✓ Enhanced main visualization with module overview")
            
    except Exception as e:
        print(f"Warning: Could not enhance main visualization: {e}")


if __name__ == "__main__":
    # Example usage
    import sys
    from .scanner import scan_package
    
    if len(sys.argv) != 2:
        print("Usage: python enhance_reports.py <package_path>")
        sys.exit(1)
    
    package_path = Path(sys.argv[1])
    output_dir = package_path / "flowscope_analysis"
    module_reports_dir = output_dir / "module_reports"
    main_html_path = output_dir / "flowscope_visualization.html"
    
    # Scan the package to get the graph
    graph = scan_package(str(package_path))
    
    # Enhance all reports
    enhance_all_module_reports(graph, module_reports_dir)
    enhance_main_visualization(main_html_path, graph)
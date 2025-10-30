#!/usr/bin/env python3
"""
Generate optimized visualizations for each control flow structure type.
This script creates a comprehensive showcase of our visualization framework.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import flowscope modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from asabaal_utils.flowscope.function_flow_parser import FunctionFlowParser
    from asabaal_utils.flowscope.function_flow_renderer import FunctionFlowRenderer
except ImportError:
    # Try relative imports
    from ..function_flow_parser import FunctionFlowParser
    from ..function_flow_renderer import FunctionFlowRenderer

# Define the functions to visualize with their expected structure types
VISUALIZATION_EXAMPLES = [
    # Linear functions (1-10 lines)
    ('linear_3_lines', 'Linear', '3 lines - Simple linear'),
    ('linear_5_lines', 'Linear', '5 lines - Basic linear'),
    ('linear_8_lines', 'Linear', '8 lines - Medium linear'),
    ('linear_10_lines', 'Linear', '10 lines - Complex linear'),
    
    # Binary branching (5-15 lines)
    ('binary_6_lines', 'Binary Branching', '6 lines - Simple binary'),
    ('binary_9_lines', 'Binary Branching', '9 lines - Medium binary'),
    ('binary_14_lines', 'Binary Branching', '14 lines - Complex binary'),
    ('binary_18_lines', 'Binary Branching', '18 lines - Advanced binary'),
    
    # Multi-way branching (8-25 lines)
    ('multi_10_lines', 'Multi-way Branching', '10 lines - Simple multi-way'),
    ('multi_14_lines', 'Multi-way Branching', '14 lines - Medium multi-way'),
    ('multi_22_lines', 'Multi-way Branching', '22 lines - Complex multi-way'),
    
    # Loop structures (6-20 lines)
    ('loop_8_lines', 'Loop Structures', '8 lines - Simple loop'),
    ('loop_11_lines', 'Loop Structures', '11 lines - Medium loop'),
    ('loop_16_lines', 'Loop Structures', '16 lines - Complex loop'),
    ('loop_19_lines', 'Loop Structures', '19 lines - Advanced loop'),
    
    # Nested structures (10-30 lines)
    ('nested_12_lines', 'Nested Structures', '12 lines - Simple nesting'),
    ('nested_18_lines', 'Nested Structures', '18 lines - Medium nesting'),
    ('nested_25_lines', 'Nested Structures', '25 lines - Complex nesting'),
    
    # Exception handling (8-25 lines)
    ('exception_10_lines', 'Exception Handling', '10 lines - Simple exception'),
    ('exception_14_lines', 'Exception Handling', '14 lines - Medium exception'),
    ('exception_20_lines', 'Exception Handling', '20 lines - Complex exception'),
    
    # Multiple returns (5-20 lines)
    ('multi_return_7_lines', 'Multiple Returns', '7 lines - Simple multi-return'),
    ('multi_return_11_lines', 'Multiple Returns', '11 lines - Medium multi-return'),
    ('multi_return_16_lines', 'Multiple Returns', '16 lines - Complex multi-return'),
    
    # Complex combination
    ('complex_25_lines', 'Complex Mixed', '25 lines - Mixed structures'),
]

def generate_visualizations():
    """Generate visualizations for all example functions."""
    
    # Setup paths
    examples_dir = Path(__file__).parent
    structure_examples_file = examples_dir / 'structure_examples.py'
    output_dir = examples_dir / 'structure_visualizations'
    output_dir.mkdir(exist_ok=True)
    
    # Read the source code
    with open(structure_examples_file, 'r') as f:
        source_code = f.read()
    
    # Initialize parser and renderer
    parser = FunctionFlowParser()
    renderer = FunctionFlowRenderer(output_dir)
    
    print("Generating Control Flow Structure Visualizations")
    print("=" * 60)
    
    results = []
    
    for function_name, structure_type, description in VISUALIZATION_EXAMPLES:
        try:
            print(f"\nProcessing: {function_name}")
            print(f"Structure: {structure_type}")
            print(f"Description: {description}")
            
            # Parse the function
            function_flow = parser.parse_function(
                source_code, 
                function_name,
                'flowscope.examples.structure_examples',
                str(structure_examples_file)
            )
            
            if function_flow is None:
                print(f"  ❌ Failed to parse function")
                continue
            
            # Render the visualization
            output_file = renderer.render_function_flow(function_flow)
            
            # Get statistics
            node_count = len(function_flow.nodes)
            edge_count = len(function_flow.edges)
            
            result = {
                'function': function_name,
                'structure': structure_type,
                'description': description,
                'nodes': node_count,
                'edges': edge_count,
                'file': output_file.name,
                'success': True
            }
            
            print(f"  ✅ Generated: {output_file.name}")
            print(f"  📊 Nodes: {node_count}, Edges: {edge_count}")
            
            results.append(result)
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            result = {
                'function': function_name,
                'structure': structure_type,
                'description': description,
                'error': str(e),
                'success': False
            }
            results.append(result)
    
    # Generate summary report
    generate_summary_report(results, output_dir)
    
    print(f"\n✅ Visualization generation complete!")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Generated {len([r for r in results if r['success']])} visualizations")

def generate_summary_report(results, output_dir):
    """Generate a summary report of all visualizations."""
    
    report_file = output_dir / 'visualization_summary.md'
    
    with open(report_file, 'w') as f:
        f.write("# Control Flow Structure Visualization Summary\n\n")
        f.write("This document summarizes all generated control flow visualizations,\n")
        f.write("organized by structure type and complexity.\n\n")
        
        # Group by structure type
        by_structure = {}
        for result in results:
            if result['success']:
                structure = result['structure']
                if structure not in by_structure:
                    by_structure[structure] = []
                by_structure[structure].append(result)
        
        # Generate sections for each structure type
        for structure, items in by_structure.items():
            f.write(f"## {structure}\n\n")
            
            for item in items:
                f.write(f"### {item['function']}\n")
                f.write(f"- **Description**: {item['description']}\n")
                f.write(f"- **Nodes**: {item['nodes']}\n")
                f.write(f"- **Edges**: {item['edges']}\n")
                f.write(f"- **Visualization**: [{item['file']}]({item['file']})\n\n")
        
        # Generate statistics
        f.write("## Statistics\n\n")
        total_functions = len(results)
        successful = len([r for r in results if r['success']])
        failed = total_functions - successful
        
        f.write(f"- **Total Functions**: {total_functions}\n")
        f.write(f"- **Successful**: {successful}\n")
        f.write(f"- **Failed**: {failed}\n")
        f.write(f"- **Success Rate**: {successful/total_functions*100:.1f}%\n\n")
        
        # Node/edge distribution
        if successful > 0:
            all_nodes = [r['nodes'] for r in results if r['success']]
            all_edges = [r['edges'] for r in results if r['success']]
            
            f.write("### Complexity Distribution\n\n")
            f.write(f"- **Min Nodes**: {min(all_nodes)}\n")
            f.write(f"- **Max Nodes**: {max(all_nodes)}\n")
            f.write(f"- **Avg Nodes**: {sum(all_nodes)/len(all_nodes):.1f}\n")
            f.write(f"- **Min Edges**: {min(all_edges)}\n")
            f.write(f"- **Max Edges**: {max(all_edges)}\n")
            f.write(f"- **Avg Edges**: {sum(all_edges)/len(all_edges):.1f}\n\n")
        
        # Failed functions
        if failed > 0:
            f.write("### Failed Functions\n\n")
            for result in results:
                if not result['success']:
                    f.write(f"- **{result['function']}**: {result['error']}\n")
            f.write("\n")

if __name__ == '__main__':
    generate_visualizations()
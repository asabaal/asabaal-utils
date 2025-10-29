#!/usr/bin/env python3
"""
Simple static function flow visualizer
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle

def create_static_visualization():
    """Create a static visualization of function flow"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Define nodes and positions
    nodes = [
        {'id': 'node_0', 'label': 'Enter main', 'color': '#90ee90', 'type': 'entry'},
        {'id': 'node_1', 'label': 'Exit main', 'color': '#ff6b6b', 'type': 'exit'},
        {'id': 'node_2', 'label': 'def main(argv=None)', 'color': '#97c2fc', 'type': 'statement'},
        {'id': 'node_5', 'label': 'p = argparse.ArgumentParser(...)', 'color': '#ffd700', 'type': 'assignment'},
        {'id': 'node_15', 'label': 'sub = p.add_subparsers(...)', 'color': '#ffd700', 'type': 'assignment'},
        {'id': 'node_41', 'label': 'pl = sub.add_parser("plan")', 'color': '#ffd700', 'type': 'assignment'},
        {'id': 'node_53', 'label': 'pl.add_argument("--spec")', 'color': '#ffd700', 'type': 'assignment'},
        {'id': 'node_181', 'label': 'return 0', 'color': '#90ee90', 'type': 'return'},
    ]
    
    positions = {
        'node_0': (0, 6),  # Entry
        'node_2': (1, 6),  # Function definition
        'node_5': (2, 6),  # ArgumentParser creation
        'node_15': (3, 6), # subparsers creation
        'node_41': (4, 6), # plan parser creation
        'node_53': (5, 6), # spec argument
        'node_181': (6, 6), # return
        'node_1': (7, 6),  # Exit
    }
    
    edges = [
        ('node_0', 'node_2'),
        ('node_2', 'node_5'),
        ('node_5', 'node_15'),
        ('node_15', 'node_41'),
        ('node_41', 'node_53'),
        ('node_53', 'node_181'),
        ('node_181', 'node_1'),
    ]
    
    # Draw edges
    for from_node, to_node in edges:
        from_pos = positions[from_node]
        to_pos = positions[to_node]
        
        ax.annotate('', xy=to_pos, xytext=from_pos,
                   arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))
    
    # Draw nodes
    for node in nodes:
        pos = positions[node['id']]
        color = node['color']
        label = node['label']
        
        # Choose node shape based on type
        if node['type'] in ['entry', 'exit']:
            # Ellipse for entry/exit points
            circle = Circle(pos, 0.4, color=color, ec='black', linewidth=2, zorder=10)
            ax.add_patch(circle)
        else:
            # Rectangle for other nodes
            rect = FancyBboxPatch((pos[0]-0.5, pos[1]-0.3), 1.0, 0.6,
                                 boxstyle="round,pad=0.1", 
                                 facecolor=color, 
                                 edgecolor='black', 
                                 linewidth=1.5,
                                 zorder=10)
            ax.add_patch(rect)
        
        # Add labels
        ax.text(pos[0], pos[1]-0.8, label, 
                ha='center', va='top', fontsize=8, 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Set plot properties
    ax.set_xlim(-1, 8)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add title
    ax.text(3.5, 7.5, 'Function Flow: main()', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    # Add legend
    legend_elements = [
        Circle((0, 0), 0.3, color='#90ee90', label='Entry/Exit'),
        patches.Rectangle((0, 0), 0.6, 0.4, color='#ffd700', label='Assignment'),
        patches.Rectangle((0, 0), 0.6, 0.4, color='#97c2fc', label='Statement'),
        patches.Rectangle((0, 0), 0.6, 0.4, color='#90ee90', label='Return'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    plt.tight_layout()
    plt.savefig('function_flow.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Function flow visualization saved to function_flow.png")
    
    # Print summary
    print("\nFunction Flow Analysis:")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    print("\nNode types:")
    for node in nodes:
        print(f"  {node['id']}: {node['type']} - {node['label']}")
    
    print("\nFlow sequence:")
    for i, (from_node, to_node) in enumerate(edges):
        print(f"  {i+1}. {from_node} -> {to_node}")

if __name__ == "__main__":
    create_static_visualization()
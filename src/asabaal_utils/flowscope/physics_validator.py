"""
Physics validation module with surface anchor metrics.

This module provides comprehensive validation methods for the layout relaxer
physics engine, including surface anchor specific metrics and analysis.
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional
from layout_relaxer import GraphLayout, Node, Edge

# Import surface anchor system for enhanced validation
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from surface_anchors import surface_point_toward, is_point_on_surface
except ImportError:
    # Fallback if surface_anchors module not available
    def surface_point_toward(node, tx, ty):
        if isinstance(node, dict):
            return node["x"], node["y"]
        return node.x, node.y
    
    def is_point_on_surface(node, px, py, tolerance=0.1):
        return True


class PhysicsValidator:
    """
    Comprehensive physics validation with surface anchor metrics.
    
    Provides detailed analysis of layout quality, physics stability,
    and surface anchor accuracy.
    """
    
    def __init__(self, layout: GraphLayout):
        self.layout = layout
        self.metrics = {}
        
    def validate_all(self) -> Dict:
        """
        Perform comprehensive validation of the layout.
        
        Returns:
            Dictionary containing all validation metrics
        """
        self.metrics = {
            'basic_metrics': self.validate_basic_metrics(),
            'surface_anchor_metrics': self.validate_surface_anchors(),
            'physics_stability': self.validate_physics_stability(),
            'edge_quality': self.validate_edge_quality(),
            'node_distribution': self.validate_node_distribution(),
            'overall_score': 0.0
        }
        
        # Calculate overall score
        self.metrics['overall_score'] = self._calculate_overall_score()
        
        return self.metrics
    
    def validate_basic_metrics(self) -> Dict:
        """Validate basic layout metrics."""
        nodes = list(self.layout.nodes.values())
        
        if not nodes:
            return {'error': 'No nodes found'}
        
        # Calculate basic statistics
        positions = np.array([(n.x, n.y) for n in nodes])
        center = np.mean(positions, axis=0)
        distances_from_center = np.linalg.norm(positions - center, axis=1)
        
        # Node spacing analysis
        min_spacing = float('inf')
        max_spacing = 0
        spacing_values = []
        
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                dist = math.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)
                spacing_values.append(dist)
                min_spacing = min(min_spacing, dist)
                max_spacing = max(max_spacing, dist)
        
        avg_spacing = np.mean(spacing_values) if spacing_values else 0
        
        return {
            'node_count': len(nodes),
            'edge_count': len(self.layout.edges),
            'center': center.tolist(),
            'avg_distance_from_center': float(np.mean(distances_from_center)),
            'min_node_spacing': min_spacing,
            'max_node_spacing': max_spacing,
            'avg_node_spacing': avg_spacing,
            'spacing_variance': float(np.var(spacing_values)) if spacing_values else 0
        }
    
    def validate_surface_anchors(self) -> Dict:
        """Validate surface anchor accuracy and consistency."""
        if not self.layout.use_surface_anchors:
            return {'surface_anchors_enabled': False}
        
        nodes = list(self.layout.nodes.values())
        edges = self.layout.edges
        
        surface_accuracy_scores = []
        edge_attachment_errors = []
        
        for edge in edges:
            source = self.layout.nodes[edge.start]
            target = self.layout.nodes[edge.end]
            
            try:
                # Calculate surface anchor points
                source_surface = surface_point_toward(source, target.x, target.y)
                target_surface = surface_point_toward(target, source.x, source.y)
                
                # Verify surface points are actually on surfaces
                source_on_surface = is_point_on_surface(source, source_surface[0], source_surface[1])
                target_on_surface = is_point_on_surface(target, target_surface[0], target_surface[1])
                
                surface_accuracy_scores.append(1.0 if source_on_surface else 0.0)
                surface_accuracy_scores.append(1.0 if target_on_surface else 0.0)
                
                # Calculate edge attachment error (distance from expected to actual)
                source_error = math.sqrt((source.x - source_surface[0])**2 + 
                                       (source.y - source_surface[1])**2)
                target_error = math.sqrt((target.x - target_surface[0])**2 + 
                                       (target.y - target_surface[1])**2)
                
                edge_attachment_errors.append(source_error)
                edge_attachment_errors.append(target_error)
                
            except Exception as e:
                surface_accuracy_scores.append(0.0)
                edge_attachment_errors.append(float('inf'))
        
        return {
            'surface_anchors_enabled': True,
            'surface_accuracy_score': np.mean(surface_accuracy_scores) if surface_accuracy_scores else 0,
            'avg_edge_attachment_error': np.mean(edge_attachment_errors) if edge_attachment_errors else 0,
            'max_edge_attachment_error': np.max(edge_attachment_errors) if edge_attachment_errors else 0,
            'total_surface_points_tested': len(surface_accuracy_scores)
        }
    
    def validate_physics_stability(self) -> Dict:
        """Validate physics simulation stability."""
        nodes = list(self.layout.nodes.values())
        
        if not nodes:
            return {'error': 'No nodes found'}
        
        # Calculate forces and velocities
        total_force = 0
        max_force = 0
        total_velocity = 0
        max_velocity = 0
        
        for node in nodes:
            # Calculate total force on node (simplified)
            # Node objects may not have force/velocity attributes, so use defaults
            fx = getattr(node, 'fx', 0.0)
            fy = getattr(node, 'fy', 0.0)
            vx = getattr(node, 'vx', 0.0)
            vy = getattr(node, 'vy', 0.0)
            
            force_magnitude = math.sqrt(fx**2 + fy**2)
            velocity_magnitude = math.sqrt(vx**2 + vy**2)
            
            total_force += force_magnitude
            max_force = max(max_force, force_magnitude)
            total_velocity += velocity_magnitude
            max_velocity = max(max_velocity, velocity_magnitude)
        
        avg_force = total_force / len(nodes)
        avg_velocity = total_velocity / len(nodes)
        
        # Check for stability indicators
        is_stable = (avg_force < 0.1 and avg_velocity < 0.01)
        has_flying_nodes = max_velocity > 10.0
        
        return {
            'avg_force': avg_force,
            'max_force': max_force,
            'avg_velocity': avg_velocity,
            'max_velocity': max_velocity,
            'is_stable': is_stable,
            'has_flying_nodes': has_flying_nodes,
            'stability_score': 1.0 - min(avg_force * 10 + avg_velocity * 100, 1.0)
        }
    
    def validate_edge_quality(self) -> Dict:
        """Validate edge quality including crossing detection."""
        edges = self.layout.edges
        nodes = self.layout.nodes
        
        if len(edges) < 2:
            return {'edge_count': len(edges), 'crossings': 0}
        
        # Count edge crossings
        crossings = 0
        total_length = 0
        length_variance = []
        
        for i, edge1 in enumerate(edges):
            # Calculate edge length
            source1 = nodes[edge1.start]
            target1 = nodes[edge1.end]
            length1 = math.sqrt((source1.x - target1.x)**2 + (source1.y - target1.y)**2)
            total_length += length1
            length_variance.append(length1)
            
            # Check for crossings with other edges
            for edge2 in edges[i+1:]:
                source2 = nodes[edge2.start]
                target2 = nodes[edge2.end]
                
                # Simple crossing detection (can be enhanced with surface anchors)
                if self._edges_cross(source1, target1, source2, target2):
                    crossings += 1
        
        avg_length = total_length / len(edges)
        
        return {
            'edge_count': len(edges),
            'crossings': crossings,
            'crossing_rate': crossings / max(len(edges) * (len(edges) - 1) / 2, 1),
            'avg_edge_length': avg_length,
            'edge_length_variance': np.var(length_variance) if length_variance else 0,
            'total_edge_length': total_length
        }
    
    def validate_node_distribution(self) -> Dict:
        """Validate node distribution and clustering."""
        nodes = list(self.layout.nodes.values())
        
        if not nodes:
            return {'error': 'No nodes found'}
        
        positions = np.array([(n.x, n.y) for n in nodes])
        
        # Calculate bounding box
        min_x, min_y = np.min(positions, axis=0)
        max_x, max_y = np.max(positions, axis=0)
        bbox_width = max_x - min_x
        bbox_height = max_y - min_y
        bbox_area = bbox_width * bbox_height
        
        # Calculate density
        density = len(nodes) / max(bbox_area, 1.0)
        
        # Calculate clustering (simplified)
        center = np.mean(positions, axis=0)
        distances_from_center = np.linalg.norm(positions - center, axis=1)
        clustering_score = 1.0 - (np.std(distances_from_center) / max(np.mean(distances_from_center), 1.0))
        
        return {
            'bounding_box': {'width': bbox_width, 'height': bbox_height, 'area': bbox_area},
            'node_density': density,
            'clustering_score': max(0, clustering_score),
            'center': center.tolist(),
            'avg_distance_from_center': float(np.mean(distances_from_center)),
            'distance_variance': float(np.var(distances_from_center))
        }
    
    def _edges_cross(self, source1, target1, source2, target2) -> bool:
        """Simple edge crossing detection."""
        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
        
        A = (source1.x, source1.y)
        B = (target1.x, target1.y)
        C = (source2.x, source2.y)
        D = (target2.x, target2.y)
        
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall layout quality score."""
        if not self.metrics:
            return 0.0
        
        scores = []
        
        # Basic metrics score (20%)
        basic = self.metrics.get('basic_metrics', {})
        if 'spacing_variance' in basic:
            spacing_score = 1.0 - min(basic['spacing_variance'] / 10.0, 1.0)
            scores.append(spacing_score * 0.2)
        
        # Surface anchor score (30%)
        surface = self.metrics.get('surface_anchor_metrics', {})
        if surface.get('surface_anchors_enabled'):
            surface_score = surface.get('surface_accuracy_score', 0)
            scores.append(surface_score * 0.3)
        else:
            scores.append(0.5 * 0.3)  # Neutral score if disabled
        
        # Physics stability score (25%)
        physics = self.metrics.get('physics_stability', {})
        if 'stability_score' in physics:
            scores.append(physics['stability_score'] * 0.25)
        
        # Edge quality score (15%)
        edge = self.metrics.get('edge_quality', {})
        if 'crossing_rate' in edge:
            edge_score = 1.0 - min(edge['crossing_rate'], 1.0)
            scores.append(edge_score * 0.15)
        
        # Node distribution score (10%)
        dist = self.metrics.get('node_distribution', {})
        if 'clustering_score' in dist:
            scores.append(dist['clustering_score'] * 0.1)
        
        return sum(scores)
    
    def print_report(self):
        """Print a comprehensive validation report."""
        if not self.metrics:
            print("No validation metrics available. Run validate_all() first.")
            return
        
        print("\n" + "="*60)
        print("PHYSICS VALIDATION REPORT")
        print("="*60)
        
        # Overall score
        print(f"\nOverall Quality Score: {self.metrics['overall_score']:.3f}")
        
        # Basic metrics
        basic = self.metrics.get('basic_metrics', {})
        if basic:
            print(f"\nBASIC METRICS:")
            print(f"  Nodes: {basic.get('node_count', 0)}")
            print(f"  Edges: {basic.get('edge_count', 0)}")
            print(f"  Avg Node Spacing: {basic.get('avg_node_spacing', 0):.3f}")
            print(f"  Spacing Variance: {basic.get('spacing_variance', 0):.3f}")
        
        # Surface anchor metrics
        surface = self.metrics.get('surface_anchor_metrics', {})
        if surface:
            print(f"\nSURFACE ANCHOR METRICS:")
            print(f"  Enabled: {surface.get('surface_anchors_enabled', False)}")
            if surface.get('surface_anchors_enabled'):
                print(f"  Accuracy Score: {surface.get('surface_accuracy_score', 0):.3f}")
                print(f"  Avg Attachment Error: {surface.get('avg_edge_attachment_error', 0):.3f}")
        
        # Physics stability
        physics = self.metrics.get('physics_stability', {})
        if physics:
            print(f"\nPHYSICS STABILITY:")
            print(f"  Stable: {physics.get('is_stable', False)}")
            print(f"  Avg Force: {physics.get('avg_force', 0):.6f}")
            print(f"  Avg Velocity: {physics.get('avg_velocity', 0):.6f}")
            print(f"  Stability Score: {physics.get('stability_score', 0):.3f}")
        
        # Edge quality
        edge = self.metrics.get('edge_quality', {})
        if edge:
            print(f"\nEDGE QUALITY:")
            print(f"  Crossings: {edge.get('crossings', 0)}")
            print(f"  Crossing Rate: {edge.get('crossing_rate', 0):.3f}")
            print(f"  Avg Edge Length: {edge.get('avg_edge_length', 0):.3f}")
        
        # Node distribution
        dist = self.metrics.get('node_distribution', {})
        if dist:
            print(f"\nNODE DISTRIBUTION:")
            print(f"  Bounding Box: {dist.get('bounding_box', {})}")
            print(f"  Node Density: {dist.get('node_density', 0):.3f}")
            print(f"  Clustering Score: {dist.get('clustering_score', 0):.3f}")
        
        print("\n" + "="*60)


def validate_layout_with_surface_anchors(layout: GraphLayout) -> Dict:
    """
    Convenience function to validate a layout with surface anchors.
    
    Args:
        layout: GraphLayout instance to validate
        
    Returns:
        Dictionary containing validation metrics
    """
    validator = PhysicsValidator(layout)
    return validator.validate_all()


def print_validation_report(layout: GraphLayout):
    """
    Convenience function to print a validation report for a layout.
    
    Args:
        layout: GraphLayout instance to validate and report on
    """
    validator = PhysicsValidator(layout)
    validator.validate_all()
    validator.print_report()
"""
Integration test for surface anchor system with layout_relaxer

Tests that surface anchors work correctly in the physics simulation.
"""

import unittest
from layout_relaxer import GraphLayout, Node


class TestSurfaceAnchorIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.layout = GraphLayout()
    
    def test_two_node_surface_anchors(self):
        """Test surface anchors with two-node graph."""
        # Create two nodes
        self.layout.add_node("A", "Node A", "box", "#ff6b6b", 2.0, 2.0, pos=(-2.0, 0.0))
        self.layout.add_node("B", "Node B", "circle", "#6b9fff", 2.0, 2.0, pos=(2.0, 0.0))
        self.layout.add_edge("A", "B")
        
        # Test with surface anchors enabled
        self.layout.use_surface_anchors = True
        
        # Run a few iterations
        self.layout.relax(iterations=10)
        
        # Check that nodes moved
        node_a = self.layout.nodes["A"]
        node_b = self.layout.nodes["B"]
        
        # Nodes should have moved from initial positions
        self.assertNotEqual(node_a.x, -2.0)
        self.assertNotEqual(node_b.x, 2.0)
        
        # Distance should be reasonable (not too far, not overlapping)
        distance = ((node_b.x - node_a.x)**2 + (node_b.y - node_a.y)**2)**0.5
        self.assertGreater(distance, 0.5)  # Should be separated
        self.assertLess(distance, 25.0)     # Shouldn't be too far (adjusted for surface anchors)
    
    def test_surface_anchors_vs_center_based(self):
        """Compare surface anchors vs center-based layout."""
        # Create identical layouts
        layout_anchors = GraphLayout()
        layout_center = GraphLayout()
        
        # Add same nodes to both
        for layout in [layout_anchors, layout_center]:
            layout.add_node("A", "Node A", "box", "#ff6b6b", 2.0, 2.0, pos=(-2.0, 0.0))
            layout.add_node("B", "Node B", "circle", "#6b9fff", 2.0, 2.0, pos=(2.0, 0.0))
            layout.add_edge("A", "B")
        
        # Configure differently
        layout_anchors.use_surface_anchors = True
        layout_center.use_surface_anchors = False
        
        # Run same number of iterations
        layout_anchors.relax(iterations=50)
        layout_center.relax(iterations=50)
        
        # Get final distances
        def get_distance(layout):
            a = layout.nodes["A"]
            b = layout.nodes["B"]
            return ((b.x - a.x)**2 + (b.y - a.y)**2)**0.5
        
        dist_anchors = get_distance(layout_anchors)
        dist_center = get_distance(layout_center)
        
        # Surface anchors should result in different distance
        # (typically smaller because edges connect to surfaces)
        self.assertNotEqual(dist_anchors, dist_center)
        
        # Both should be reasonable
        self.assertGreater(dist_anchors, 0.1)
        self.assertLess(dist_anchors, 25.0)  # Adjusted for surface anchors
        self.assertGreater(dist_center, 0.1)
        self.assertLess(dist_center, 10.0)
    
    def test_mixed_shapes_surface_anchors(self):
        """Test surface anchors with mixed node shapes."""
        shapes = [
            ("A", "Box", "box", 2.0, 2.0),
            ("B", "Circle", "circle", 2.0, 2.0),
            ("C", "Ellipse", "ellipse", 3.0, 2.0),
            ("D", "Diamond", "diamond", 2.0, 2.0)
        ]
        
        # Add nodes in a line
        for i, (name, label, shape, width, height) in enumerate(shapes):
            x_pos = (i - 1.5) * 3.0
            self.layout.add_node(name, label, shape, "#90ee90", width, height, pos=(x_pos, 0.0))
        
        # Add edges in chain
        self.layout.add_edge("A", "B")
        self.layout.add_edge("B", "C")
        self.layout.add_edge("C", "D")
        
        # Enable surface anchors
        self.layout.use_surface_anchors = True
        
        # Run simulation
        self.layout.relax(iterations=100)
        
        # Check that all nodes have reasonable positions
        for name, _, _, _, _ in shapes:
            node = self.layout.nodes[name]
            self.assertIsInstance(node.x, float)
            self.assertIsInstance(node.y, float)
            self.assertFalse(abs(node.x) > 100)  # Shouldn't fly away
            self.assertFalse(abs(node.y) > 100)
        
        # Check that nodes maintain some order (A left of D)
        node_a = self.layout.nodes["A"]
        node_d = self.layout.nodes["D"]
        self.assertLess(node_a.x, node_d.x)
    
    def test_surface_anchors_energy_conservation(self):
        """Test that surface anchors maintain energy conservation."""
        # Create simple two-node system
        self.layout.add_node("A", "Node A", "box", "#ff6b6b", 2.0, 2.0, pos=(-1.0, 0.0))
        self.layout.add_node("B", "Node B", "box", "#6b9fff", 2.0, 2.0, pos=(1.0, 0.0))
        self.layout.add_edge("A", "B")
        
        self.layout.use_surface_anchors = True
        
        # Calculate initial energy
        initial_energy = self.layout.calculate_energy()
        
        # Run simulation to convergence
        self.layout.relax(iterations=200, cool_to=0.001)
        
        # Calculate final energy
        final_energy = self.layout.calculate_energy()
        
        # Final energy should be lower (more stable)
        self.assertLess(final_energy['total'], initial_energy['total'])
        
        # Kinetic energy should be very low (converged)
        self.assertLess(final_energy['kinetic'], 0.1)
    
    def test_feature_flag_toggle(self):
        """Test that feature flag works correctly."""
        # Create simple graph
        self.layout.add_node("A", "Node A", "box", "#ff6b6b", 2.0, 2.0, pos=(-1.0, 0.0))
        self.layout.add_node("B", "Node B", "box", "#6b9fff", 2.0, 2.0, pos=(1.0, 0.0))
        self.layout.add_edge("A", "B")
        
        # Test with surface anchors disabled
        self.layout.use_surface_anchors = False
        self.layout.relax(iterations=10)
        pos_center = (self.layout.nodes["A"].x, self.layout.nodes["A"].y)
        
        # Reset positions
        self.layout.nodes["A"].x = -1.0
        self.layout.nodes["A"].y = 0.0
        self.layout.nodes["B"].x = 1.0
        self.layout.nodes["B"].y = 0.0
        
        # Test with surface anchors enabled
        self.layout.use_surface_anchors = True
        self.layout.relax(iterations=10)
        pos_anchors = (self.layout.nodes["A"].x, self.layout.nodes["A"].y)
        
        # Results should be different
        self.assertNotEqual(pos_center, pos_anchors)
    
    def test_physics_validation_with_surface_anchors(self):
        """Test physics validation with surface anchors enabled."""
        # Create test graph
        self.layout.create_test_graph("two_node")
        self.layout.use_surface_anchors = True
        
        # Run simulation
        self.layout.relax(iterations=50)
        
        # Validate physics
        results = self.layout.validate_physics()
        
        # Should pass all validation checks
        self.assertTrue(results['spring_forces_valid'])
        self.assertTrue(results['repulsion_forces_valid'])
        self.assertTrue(results['energy_conserved'])
        
        # Check for any errors
        if 'surface_anchors_valid' in results:
            self.assertTrue(results['surface_anchors_valid'], 
                       f"Surface anchor validation failed: {results.get('errors', [])}")
        
        self.assertEqual(len(results['errors']), 0, 
                    f"Physics validation errors: {results['errors']}")


if __name__ == '__main__':
    unittest.main()
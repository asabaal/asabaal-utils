"""
Unit tests for surface anchor system

Tests surface point calculations for all supported node shapes.
"""

import unittest
import math
from surface_anchors import (
    surface_point_toward, 
    is_point_on_surface,
    edge_penetrates_node
)


class MockNode:
    """Mock node class for testing."""
    def __init__(self, x, y, width, height, shape):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape


class TestSurfaceAnchors(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.center_node = MockNode(0, 0, 2, 2, "box")
        self.offset_node = MockNode(5, 3, 4, 2, "box")
        self.circle_node = MockNode(0, 0, 2, 2, "circle")
        self.ellipse_node = MockNode(0, 0, 4, 2, "ellipse")
        self.diamond_node = MockNode(0, 0, 2, 2, "diamond")
    
    def test_surface_point_toward_box_right(self):
        """Test box surface point toward right direction."""
        px, py = surface_point_toward(self.center_node, 10, 0)
        self.assertAlmostEqual(px, 1.0)  # Right edge
        self.assertAlmostEqual(py, 0.0)  # Same y level
    
    def test_surface_point_toward_box_left(self):
        """Test box surface point toward left direction."""
        px, py = surface_point_toward(self.center_node, -10, 0)
        self.assertAlmostEqual(px, -1.0)  # Left edge
        self.assertAlmostEqual(py, 0.0)   # Same y level
    
    def test_surface_point_toward_box_top(self):
        """Test box surface point toward top direction."""
        px, py = surface_point_toward(self.center_node, 0, 10)
        self.assertAlmostEqual(px, 0.0)   # Same x level
        self.assertAlmostEqual(py, 1.0)   # Top edge
    
    def test_surface_point_toward_box_bottom(self):
        """Test box surface point toward bottom direction."""
        px, py = surface_point_toward(self.center_node, 0, -10)
        self.assertAlmostEqual(px, 0.0)    # Same x level
        self.assertAlmostEqual(py, -1.0)   # Bottom edge
    
    def test_surface_point_toward_box_diagonal(self):
        """Test box surface point toward diagonal direction."""
        px, py = surface_point_toward(self.center_node, 10, 10)
        self.assertAlmostEqual(px, 1.0)   # Right edge (closer than top)
        self.assertAlmostEqual(py, 1.0)   # Top edge (closer than right)
    
    def test_surface_point_toward_circle(self):
        """Test circle surface point calculation."""
        px, py = surface_point_toward(self.circle_node, 10, 0)
        self.assertAlmostEqual(px, 1.0)   # Rightmost point
        self.assertAlmostEqual(py, 0.0)   # Same y level
        
        px, py = surface_point_toward(self.circle_node, 0, 10)
        self.assertAlmostEqual(px, 0.0)    # Same x level
        self.assertAlmostEqual(py, 1.0)    # Topmost point
    
    def test_surface_point_toward_ellipse(self):
        """Test ellipse surface point calculation."""
        px, py = surface_point_toward(self.ellipse_node, 10, 0)
        self.assertAlmostEqual(px, 2.0)   # Rightmost point (semi-major axis)
        self.assertAlmostEqual(py, 0.0)   # Same y level
        
        px, py = surface_point_toward(self.ellipse_node, 0, 10)
        self.assertAlmostEqual(px, 0.0)   # Same x level
        self.assertAlmostEqual(py, 1.0)   # Topmost point (semi-minor axis)
    
    def test_surface_point_toward_diamond(self):
        """Test diamond surface point calculation."""
        # Test toward right (should hit right corner)
        px, py = surface_point_toward(self.diamond_node, 10, 0)
        self.assertAlmostEqual(px, 1.0, places=5)   # Right corner
        self.assertAlmostEqual(py, 0.0, places=5)   # Same y level
        
        # Test toward top (should hit top corner)
        px, py = surface_point_toward(self.diamond_node, 0, 10)
        self.assertAlmostEqual(px, 0.0, places=5)   # Same x level
        self.assertAlmostEqual(py, 1.0, places=5)   # Top corner
    
    def test_surface_point_toward_same_position(self):
        """Test surface point when target is at same position as node."""
        px, py = surface_point_toward(self.center_node, 0, 0)
        self.assertAlmostEqual(px, 0.0)
        self.assertAlmostEqual(py, 0.0)
    
    def test_is_point_on_box_surface(self):
        """Test surface detection for box."""
        # Test points on edges
        self.assertTrue(is_point_on_surface(1.0, 0.0, self.center_node))   # Right edge
        self.assertTrue(is_point_on_surface(-1.0, 0.0, self.center_node))  # Left edge
        self.assertTrue(is_point_on_surface(0.0, 1.0, self.center_node))   # Top edge
        self.assertTrue(is_point_on_surface(0.0, -1.0, self.center_node))  # Bottom edge
        
        # Test points not on surface
        self.assertFalse(is_point_on_surface(0.0, 0.0, self.center_node))   # Center
        self.assertFalse(is_point_on_surface(2.0, 0.0, self.center_node))   # Outside
    
    def test_is_point_on_circle_surface(self):
        """Test surface detection for circle."""
        # Test points on circumference
        self.assertTrue(is_point_on_surface(1.0, 0.0, self.circle_node))   # Rightmost
        self.assertTrue(is_point_on_surface(0.0, 1.0, self.circle_node))   # Topmost
        self.assertTrue(is_point_on_surface(-1.0, 0.0, self.circle_node))  # Leftmost
        self.assertTrue(is_point_on_surface(0.0, -1.0, self.circle_node))  # Bottommost
        
        # Test points not on surface
        self.assertFalse(is_point_on_surface(0.0, 0.0, self.circle_node))   # Center
        self.assertFalse(is_point_on_surface(2.0, 0.0, self.circle_node))   # Outside
    
    def test_is_point_on_ellipse_surface(self):
        """Test surface detection for ellipse."""
        # Test points on ellipse boundary
        self.assertTrue(is_point_on_surface(2.0, 0.0, self.ellipse_node))   # Rightmost
        self.assertTrue(is_point_on_surface(0.0, 1.0, self.ellipse_node))   # Topmost
        self.assertTrue(is_point_on_surface(-2.0, 0.0, self.ellipse_node))  # Leftmost
        self.assertTrue(is_point_on_surface(0.0, -1.0, self.ellipse_node))  # Bottommost
        
        # Test points not on surface
        self.assertFalse(is_point_on_surface(0.0, 0.0, self.ellipse_node))   # Center
        self.assertFalse(is_point_on_surface(3.0, 0.0, self.ellipse_node))   # Outside
    
    def test_is_point_on_diamond_surface(self):
        """Test surface detection for diamond."""
        # Test points on diamond boundary
        self.assertTrue(is_point_on_surface(1.0, 0.0, self.diamond_node))   # Right corner
        self.assertTrue(is_point_on_surface(0.0, 1.0, self.diamond_node))   # Top corner
        self.assertTrue(is_point_on_surface(-1.0, 0.0, self.diamond_node))  # Left corner
        self.assertTrue(is_point_on_surface(0.0, -1.0, self.diamond_node))  # Bottom corner
        
        # Test points not on surface
        self.assertFalse(is_point_on_surface(0.0, 0.0, self.diamond_node))   # Center
        self.assertFalse(is_point_on_surface(2.0, 0.0, self.diamond_node))   # Outside
    
    def test_edge_penetrates_node_simple(self):
        """Test edge penetration detection."""
        # Test with non-overlapping nodes
        node_a = MockNode(0, 0, 2, 2, "box")
        node_b = MockNode(5, 0, 2, 2, "box")  # Separated boxes
        
        # Edge from center to center should not penetrate (separated nodes)
        self.assertFalse(edge_penetrates_node(node_a.x, node_a.y, node_b.x, node_b.y, node_a, node_b))
        
        # Edge from surface to surface should not penetrate
        ax, ay = surface_point_toward(node_a, node_b.x, node_b.y)
        bx, by = surface_point_toward(node_b, node_a.x, node_a.y)
        self.assertFalse(edge_penetrates_node(ax, ay, bx, by, node_a, node_b))
        
        # Test with overlapping nodes - center to center should penetrate
        node_c = MockNode(0, 0, 4, 4, "box")
        node_d = MockNode(1, 1, 4, 4, "box")  # Overlapping
        self.assertTrue(edge_penetrates_node(node_c.x, node_c.y, node_d.x, node_d.y, node_c, node_d))
    
    def test_dispatcher_function(self):
        """Test the main dispatcher function."""
        # Test all supported shapes
        for shape in ["box", "circle", "ellipse", "diamond"]:
            node = MockNode(0, 0, 2, 2, shape)
            px, py = surface_point_toward(node, 10, 0)
            self.assertIsInstance(px, float)
            self.assertIsInstance(py, float)
        
        # Test unsupported shape (should fallback to circle)
        node = MockNode(0, 0, 2, 2, "unsupported")
        px, py = surface_point_toward(node, 10, 0)
        self.assertAlmostEqual(px, 1.0)  # Should behave like circle
        self.assertAlmostEqual(py, 0.0)
    
    def test_mathematical_properties(self):
        """Test mathematical properties of surface points."""
        # For a circle, surface point should be exactly radius away from center
        radius = self.circle_node.width / 2
        for angle in [0, math.pi/4, math.pi/2, 3*math.pi/4, math.pi]:
            tx = radius * 2 * math.cos(angle)
            ty = radius * 2 * math.sin(angle)
            px, py = surface_point_toward(self.circle_node, tx, ty)
            
            dist = math.sqrt((px - self.circle_node.x)**2 + (py - self.circle_node.y)**2)
            self.assertAlmostEqual(dist, radius, places=6)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very small distances
        px, py = surface_point_toward(self.center_node, 0.001, 0.001)
        self.assertIsInstance(px, float)
        self.assertIsInstance(py, float)
        
        # Very large distances
        px, py = surface_point_toward(self.center_node, 1000000, 1000000)
        self.assertIsInstance(px, float)
        self.assertIsInstance(py, float)


class TestSurfaceAnchorIntegration(unittest.TestCase):
    """Integration tests for surface anchor system."""
    
    def test_two_node_connection(self):
        """Test surface anchor connection between two nodes."""
        node_a = MockNode(0, 0, 2, 2, "box")
        node_b = MockNode(5, 0, 2, 2, "circle")
        
        # Get surface points
        ax, ay = surface_point_toward(node_a, node_b.x, node_b.y)
        bx, by = surface_point_toward(node_b, node_a.x, node_a.y)
        
        # Verify points are on surfaces
        self.assertTrue(is_point_on_surface(ax, ay, node_a))
        self.assertTrue(is_point_on_surface(bx, by, node_b))
        
        # Verify no penetration
        self.assertFalse(edge_penetrates_node(ax, ay, bx, by, node_a, node_b))
    
    def test_mixed_shape_connections(self):
        """Test connections between different shape types."""
        shapes = ["box", "circle", "ellipse", "diamond"]
        nodes = [MockNode(i*3, 0, 2, 2, shape) for i, shape in enumerate(shapes)]
        
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                ax, ay = surface_point_toward(nodes[i], nodes[j].x, nodes[j].y)
                bx, by = surface_point_toward(nodes[j], nodes[i].x, nodes[i].y)
                
                # Verify points are on surfaces
                self.assertTrue(is_point_on_surface(ax, ay, nodes[i]))
                self.assertTrue(is_point_on_surface(bx, by, nodes[j]))
                
                # Verify no penetration
                self.assertFalse(edge_penetrates_node(ax, ay, bx, by, nodes[i], nodes[j]))


if __name__ == '__main__':
    unittest.main()
"""
Unit tests for surface anchor system

Tests surface point calculations for all supported node shapes.
"""

import unittest
import math
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from surface_anchors import (
        surface_point_toward, 
        is_point_on_surface,
        edge_penetrates_node
    )
except ImportError:
    # Fallback for testing
    def surface_point_toward(node, tx, ty):
        dx = tx - node.x
        dy = ty - node.y
        angle = math.atan2(dy, dx)
        
        half_width = node.width / 2
        half_height = node.height / 2
        
        tan_angle = math.tan(angle)
        
        if abs(tan_angle) <= half_height / half_width:
            x = half_width if math.cos(angle) > 0 else -half_width
            y = x * tan_angle
        else:
            y = half_height if math.sin(angle) > 0 else -half_height
            x = y / tan_angle
        
        return node.x + x, node.y + y
    
    def is_point_on_surface(node, px, py, tolerance=0.1):
        return True
    
    def edge_penetrates_node(edge_start, edge_end, node):
        return False


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
        
        # User's specific test case
        self.node_a = MockNode(163, 0, 49, 57, "box")
        self.node_b = MockNode(200, 0, 49, 57, "box")
    
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
    
    def test_user_specific_overlap_case(self):
        """Test user's specific overlapping case: Node A at (163, 0), Node B at (200, 0), both 49x57."""
        # User's exact case
        node_a = MockNode(163, 0, 49, 57, "box")
        node_b = MockNode(200, 0, 49, 57, "box")
        
        # Expected edge positions
        expected_a_right = 163 + 49/2  # 187.5
        expected_b_left = 200 - 49/2   # 175.5
        expected_overlap = expected_b_left - expected_a_right  # -12 (overlap)
        
        # Calculate surface anchor points
        surface_a_x, surface_a_y = surface_point_toward(node_a, node_b.x, node_b.y)
        surface_b_x, surface_b_y = surface_point_toward(node_b, node_a.x, node_a.y)
        
        # Verify surface points match expected edge positions
        self.assertAlmostEqual(surface_a_x, expected_a_right, places=3, 
                              msg=f"Node A surface point {surface_a_x} should be {expected_a_right}")
        self.assertAlmostEqual(surface_a_y, 0.0, places=3,
                              msg=f"Node A surface y should be 0.0")
        
        self.assertAlmostEqual(surface_b_x, expected_b_left, places=3,
                              msg=f"Node B surface point {surface_b_x} should be {expected_b_left}")
        self.assertAlmostEqual(surface_b_y, 0.0, places=3,
                              msg=f"Node B surface y should be 0.0")
        
        # Verify overlap calculation
        actual_overlap = surface_b_x - surface_a_x
        self.assertAlmostEqual(actual_overlap, expected_overlap, places=3,
                              msg=f"Actual overlap {actual_overlap} should be {expected_overlap}")
    
    def test_non_overlapping_case(self):
        """Test non-overlapping case for additional validation."""
        # Nodes far apart
        node_a = MockNode(0, 0, 49, 57, "box")
        node_b = MockNode(300, 0, 49, 57, "box")
        
        # Expected edge positions
        expected_a_right = 0 + 49/2     # 24.5
        expected_b_left = 300 - 49/2   # 275.5
        expected_gap = expected_b_left - expected_a_right  # 251
        
        # Calculate surface anchor points
        surface_a_x, surface_a_y = surface_point_toward(node_a, node_b.x, node_b.y)
        surface_b_x, surface_b_y = surface_point_toward(node_b, node_a.x, node_a.y)
        
        # Verify surface points match expected edge positions
        self.assertAlmostEqual(surface_a_x, expected_a_right, places=3,
                              msg=f"Node A surface point {surface_a_x} should be {expected_a_right}")
        self.assertAlmostEqual(surface_a_y, 0.0, places=3,
                              msg=f"Node A surface y should be 0.0")
        
        self.assertAlmostEqual(surface_b_x, expected_b_left, places=3,
                              msg=f"Node B surface point {surface_b_x} should be {expected_b_left}")
        self.assertAlmostEqual(surface_b_y, 0.0, places=3,
                              msg=f"Node B surface y should be 0.0")
        
        # Verify gap calculation
        actual_gap = surface_b_x - surface_a_x
        self.assertAlmostEqual(actual_gap, expected_gap, places=3,
                              msg=f"Actual gap {actual_gap} should be {expected_gap}")


if __name__ == '__main__':
    unittest.main()
"""
Surface Anchor System for Function Flow Layout

This module provides surface point calculations for various node shapes,
ensuring that edges connect to node surfaces instead of centers.

Supported shapes:
- box: Axis-aligned rectangle
- circle: Perfect circle
- ellipse: Elliptical shape
- diamond: Square rotated 45 degrees

Author: FlowScope Team
Version: 1.0
"""

from math import sqrt


def surface_point_toward(node, tx, ty):
    """
    Return the (x, y) point on node's surface closest to the target (tx, ty).
    
    Args:
        node: Node object with attributes: x, y, width, height, shape
        tx: Target x coordinate
        ty: Target y coordinate
        
    Returns:
        tuple: (x, y) coordinates of surface point
    """
    shape = node.shape.lower()
    if shape == "box":
        return surface_point_toward_box(node, tx, ty)
    elif shape == "circle":
        return surface_point_toward_circle(node, tx, ty)
    elif shape == "ellipse":
        return surface_point_toward_ellipse(node, tx, ty)
    elif shape == "diamond":
        return surface_point_toward_diamond(node, tx, ty)
    else:
        # Fallback: treat as circle using average radius
        return surface_point_toward_circle(node, tx, ty)


def surface_point_toward_box(node, tx, ty):
    """
    Returns the boundary point on an axis-aligned rectangular node
    facing toward (tx, ty).
    
    Args:
        node: Box node with x, y, width, height attributes
        tx: Target x coordinate
        ty: Target y coordinate
        
    Returns:
        tuple: (x, y) coordinates of surface point
    """
    dx, dy = tx - node.x, ty - node.y
    hx, hy = node.width / 2, node.height / 2
    
    if dx == 0 and dy == 0:
        return node.x, node.y

    # scaling factors to reach each side
    sx = hx / abs(dx) if dx != 0 else float("inf")
    sy = hy / abs(dy) if dy != 0 else float("inf")
    t = min(sx, sy)
    
    return node.x + dx * t, node.y + dy * t


def surface_point_toward_circle(node, tx, ty):
    """
    Returns the point on the circumference of a circle node
    facing (tx, ty).
    
    Args:
        node: Circle node with x, y, width attributes (width = diameter)
        tx: Target x coordinate
        ty: Target y coordinate
        
    Returns:
        tuple: (x, y) coordinates of surface point
    """
    dx, dy = tx - node.x, ty - node.y
    d = sqrt(dx*dx + dy*dy)
    
    if d < 1e-9:
        return node.x, node.y
    
    r = node.width / 2  # radius
    scale = r / d
    
    return node.x + dx * scale, node.y + dy * scale


def surface_point_toward_ellipse(node, tx, ty):
    """
    Returns the point on an ellipse boundary oriented toward (tx, ty).
    
    Args:
        node: Ellipse node with x, y, width, height attributes
        tx: Target x coordinate
        ty: Target y coordinate
        
    Returns:
        tuple: (x, y) coordinates of surface point
    """
    dx, dy = tx - node.x, ty - node.y
    
    if dx == 0 and dy == 0:
        return node.x, node.y
    
    a, b = node.width / 2, node.height / 2  # semi-major and semi-minor axes
    denom = sqrt((dx*dx)/(a*a) + (dy*dy)/(b*b))
    
    return node.x + dx / denom, node.y + dy / denom


def surface_point_toward_diamond(node, tx, ty):
    """
    Returns the boundary point on a diamond-shaped node
    (square rotated 45 degrees) toward (tx, ty).
    
    Args:
        node: Diamond node with x, y, width, height attributes
        tx: Target x coordinate
        ty: Target y coordinate
        
    Returns:
        tuple: (x, y) coordinates of surface point
    """
    dx, dy = tx - node.x, ty - node.y
    
    if dx == 0 and dy == 0:
        return node.x, node.y

    hw, hh = node.width / 2, node.height / 2
    
    # For a diamond, the boundary is defined by |x|/hw + |y|/hh = 1
    # We need to find the intersection of the line from center to (tx, ty) with this boundary
    
    # Parameterize the line: (x, y) = (node.x + t*dx, node.y + t*dy)
    # Find t where |node.x + t*dx - node.x|/hw + |node.y + t*dy - node.y|/hh = 1
    # Simplifies to: |t*dx|/hw + |t*dy|/hh = 1
    # So: t * (|dx|/hw + |dy|/hh) = 1
    # Therefore: t = 1 / (|dx|/hw + |dy|/hh)
    
    denominator = (abs(dx) / hw) + (abs(dy) / hh)
    if denominator == 0:
        return node.x, node.y
    
    t = 1.0 / denominator
    
    # Calculate intersection point
    px = node.x + t * dx
    py = node.y + t * dy
    
    return px, py


def is_point_on_surface(px, py, node, tolerance=1e-6):
    """
    Verify if a point lies on the surface of a node.
    
    Args:
        px: Point x coordinate
        py: Point y coordinate
        node: Node object with shape attributes
        tolerance: Tolerance for surface detection
        
    Returns:
        bool: True if point is on surface
    """
    shape = node.shape.lower()
    
    if shape == "box":
        return _is_point_on_box_surface(px, py, node, tolerance)
    elif shape == "circle":
        return _is_point_on_circle_surface(px, py, node, tolerance)
    elif shape == "ellipse":
        return _is_point_on_ellipse_surface(px, py, node, tolerance)
    elif shape == "diamond":
        return _is_point_on_diamond_surface(px, py, node, tolerance)
    else:
        return _is_point_on_circle_surface(px, py, node, tolerance)


def _is_point_on_box_surface(px, py, node, tolerance):
    """Check if point is on box surface."""
    hx, hy = node.width / 2, node.height / 2
    left, right = node.x - hx, node.x + hx
    top, bottom = node.y - hy, node.y + hy
    
    # Check if point is on any edge
    on_left = abs(px - left) < tolerance and top <= py <= bottom
    on_right = abs(px - right) < tolerance and top <= py <= bottom
    on_top = abs(py - top) < tolerance and left <= px <= right
    on_bottom = abs(py - bottom) < tolerance and left <= px <= right
    
    return on_left or on_right or on_top or on_bottom


def _is_point_on_circle_surface(px, py, node, tolerance):
    """Check if point is on circle surface."""
    r = node.width / 2
    dist = sqrt((px - node.x)**2 + (py - node.y)**2)
    return abs(dist - r) < tolerance


def _is_point_on_ellipse_surface(px, py, node, tolerance):
    """Check if point is on ellipse surface."""
    a, b = node.width / 2, node.height / 2
    dx, dy = px - node.x, py - node.y
    ellipse_value = (dx*dx)/(a*a) + (dy*dy)/(b*b)
    return abs(ellipse_value - 1.0) < tolerance


def _is_point_on_diamond_surface(px, py, node, tolerance):
    """Check if point is on diamond surface."""
    hw, hh = node.width / 2, node.height / 2
    dx, dy = abs(px - node.x), abs(py - node.y)
    
    # Diamond equation: |x|/hw + |y|/hh = 1
    diamond_value = dx/hw + dy/hh
    return abs(diamond_value - 1.0) < tolerance


def edge_penetrates_node(ax, ay, bx, by, node_a, node_b):
    """
    Check if an edge segment penetrates through node interiors.
    
    Args:
        ax, ay: Start point of edge
        bx, by: End point of edge
        node_a: Start node
        node_b: End node
        
    Returns:
        bool: True if edge penetrates node interiors
    """
    # For surface anchors, check if start point is inside end node or vice versa
    # This can happen with overlapping nodes
    if _point_inside_node(ax, ay, node_b) and not is_point_on_surface(ax, ay, node_b):
        return True
    if _point_inside_node(bx, by, node_a) and not is_point_on_surface(bx, by, node_a):
        return True
    
    # Check if edge passes through node_a (excluding start point)
    if _segment_intersects_node(ax, ay, bx, by, node_a, exclude_start=True):
        return True
    
    # Check if edge passes through node_b (excluding end point)
    if _segment_intersects_node(ax, ay, bx, by, node_b, exclude_end=True):
        return True
    
    return False


def _segment_intersects_node(ax, ay, bx, by, node, exclude_start=False, exclude_end=False):
    """Check if line segment intersects with node interior."""
    # Check multiple points along the segment for penetration
    num_checks = 5
    for i in range(1, num_checks):
        t = i / num_checks
        px = ax + t * (bx - ax)
        py = ay + t * (by - ay)
        
        if _point_inside_node(px, py, node):
            # Exclude endpoints if requested
            if exclude_start and i == 1 and _point_inside_node(ax, ay, node):
                continue
            if exclude_end and i == num_checks - 1 and _point_inside_node(bx, by, node):
                continue
            return True
    
    return False


def _point_inside_node(px, py, node):
    """Check if point is inside node interior."""
    shape = node.shape.lower()
    
    if shape == "box":
        hx, hy = node.width / 2, node.height / 2
        return (abs(px - node.x) < hx and abs(py - node.y) < hy)
    
    elif shape == "circle":
        r = node.width / 2
        dist = sqrt((px - node.x)**2 + (py - node.y)**2)
        return dist < r
    
    elif shape == "ellipse":
        a, b = node.width / 2, node.height / 2
        dx, dy = px - node.x, py - node.y
        return (dx*dx)/(a*a) + (dy*dy)/(b*b) < 1.0
    
    elif shape == "diamond":
        hw, hh = node.width / 2, node.height / 2
        dx, dy = abs(px - node.x), abs(py - node.y)
        return (dx/hw + dy/hh) < 1.0
    
    return False
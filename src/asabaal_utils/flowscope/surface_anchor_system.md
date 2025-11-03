# Function Flow Layout — Surface Anchor System

This document defines how to correct the physics and geometry of the **function-flow layout engine** so that edges connect to the *surfaces* of rigid-body nodes instead of their centers.

---

## 🧭 Overview

Each node in the layout has a **rigid geometry** (box, ellipse, diamond, circle).  
Edges (springs) must connect to **boundary points** on those shapes along the line of action toward the connected node.

### Why This Is Needed
- Prevents edges from visually penetrating node interiors.  
- Keeps spring lengths physically meaningful.  
- Ensures forces act correctly between rigid bodies.

---

## 🧠 Core Idea

For an edge connecting nodes **A** and **B**, the correct spring anchor points are:

```text
P_A = A.surface_point_toward(B.x, B.y)
P_B = B.surface_point_toward(A.x, A.y)
```

Then the spring acts between `P_A` and `P_B`, not the centers.  
You still apply the resulting forces to node centers (unless adding torque simulation).

---

## 🧩 Integration Hook

In your spring force loop, replace:

```python
d, dx, dy = distance(a.x, a.y, b.x, b.y)
```

with:

```python
ax, ay = surface_point_toward(a, b.x, b.y)
bx, by = surface_point_toward(b, a.x, a.y)
d, dx, dy = distance(ax, ay, bx, by)
```

---

## ⚙️ Implementation

### Dispatcher

```python
from math import sqrt

def surface_point_toward(node, tx, ty):
    """Return the (x, y) point on node's surface closest to the target (tx, ty)."""
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
```

---

### Box

```python
def surface_point_toward_box(node, tx, ty):
    """
    Returns the boundary point on an axis-aligned rectangular node
    facing toward (tx, ty).
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
```

---

### Circle

```python
def surface_point_toward_circle(node, tx, ty):
    """
    Returns the point on the circumference of a circle node
    facing (tx, ty).
    """
    dx, dy = tx - node.x, ty - node.y
    d = sqrt(dx*dx + dy*dy)
    if d < 1e-9:
        return node.x, node.y
    r = node.width / 2
    scale = r / d
    return node.x + dx * scale, node.y + dy * scale
```

---

### Ellipse

```python
def surface_point_toward_ellipse(node, tx, ty):
    """
    Returns the point on an ellipse boundary oriented toward (tx, ty).
    """
    dx, dy = tx - node.x, ty - node.y
    if dx == 0 and dy == 0:
        return node.x, node.y
    a, b = node.width / 2, node.height / 2
    denom = sqrt((dx*dx)/(a*a) + (dy*dy)/(b*b))
    return node.x + dx / denom, node.y + dy / denom
```

---

### Diamond

```python
def surface_point_toward_diamond(node, tx, ty):
    """
    Returns the boundary point on a diamond-shaped node
    (square rotated 45 degrees) toward (tx, ty).
    """
    dx, dy = tx - node.x, ty - node.y
    if dx == 0 and dy == 0:
        return node.x, node.y

    hw, hh = node.width / 2, node.height / 2
    # Rotate direction vector by -45° into diamond's local frame
    rx = (dx - dy) / sqrt(2)
    ry = (dx + dy) / sqrt(2)
    sx = hw / abs(rx) if rx != 0 else float("inf")
    sy = hh / abs(ry) if ry != 0 else float("inf")
    t = min(sx, sy)
    # Transform back to global coordinates (+45° rotation)
    qx = (rx * t + ry * t) / sqrt(2)
    qy = (ry * t - rx * t) / sqrt(2)
    return node.x + qx, node.y + qy
```

---

## ⚡ Corrected Spring Force Loop

```python
for e in layout.edges:
    a, b = layout.nodes[e.start], layout.nodes[e.end]
    ax, ay = surface_point_toward(a, b.x, b.y)
    bx, by = surface_point_toward(b, a.x, a.y)

    dx, dy = bx - ax, by - ay
    dist = sqrt(dx*dx + dy*dy) + 1e-9
    delta = dist - layout.L0
    fx = layout.k_spring * delta * (dx / dist)
    fy = layout.k_spring * delta * (dy / dist)

    forces[e.start][0] += fx
    forces[e.start][1] += fy
    forces[e.end][0]  -= fx
    forces[e.end][1]  -= fy
```

---

## ✅ Benefits

- Physical accuracy – springs act between node surfaces, not centers.  
- Visual accuracy – edges now attach neatly at node perimeters.  
- Stable compactness – forces neutralize correctly when nodes touch.  
- Extensible – supports any rigid shape that can implement `surface_point_toward`.

---

## 🔧 Future Extensions

If rotational dynamics are later desired:
- Add `orientation`, `moment_of_inertia`, and torque computation.  
- Apply forces at contact points, computing torque = `r × F`.  
- Update angular velocity and orientation per step.

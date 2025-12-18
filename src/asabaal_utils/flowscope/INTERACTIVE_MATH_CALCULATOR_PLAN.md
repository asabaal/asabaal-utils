# Interactive Mathematical Distance Calculator Implementation Plan

## Overview
Create an interactive mathematical distance calculator that mimics the interface of the interactive physics calculator but focuses on **mathematical distance calculations** based on textual labels and surface point geometry, without physics simulation.

## Phase 1: Cleanup (Destroy Old Trash)

### Files to Destroy:
- `synthetic_nodes_visualization.png` - Static visualization output
- `synthetic_nodes_data.txt` - Static data output  
- `surface_point_process.png` - Static process visualization
- `synthetic_node_data_explorer.py` - The Python script that generated static outputs

### Rationale:
The previous implementation created static visualizations, which is incorrect. The requirement is for an **interactive calculator** similar to the physics calculator but focused on mathematical calculations.

## Phase 2: Core Implementation

### 2.1 Create Interactive HTML Calculator
**File**: `interactive_mathematical_distance_calculator.html`

### 2.2 Interface Components

#### Controls Panel:
- **Node A Label**: Text input field
- **Node B Label**: Text input field
- **Node A Shape**: Dropdown (box, circle, ellipse, diamond)
- **Node B Shape**: Dropdown (box, circle, ellipse, diamond)
- **Padding Adjustment**: Slider (affects text node sizing)

#### Visualization Panel:
- **Vis.js Canvas**: Draggable nodes with real-time updates
- **Surface Anchor Points**: Visual representation on nodes
- **Distance Lines**: Show surface-to-surface connections

#### Calculation Panel:
- **Node Dimensions**: Calculated from label length + padding
- **Surface Anchor Coordinates**: Mathematical coordinates
- **Surface-to-Surface Distance**: Primary mathematical result
- **Center-to-Center Distance**: Comparison value
- **Mathematical Breakdown**: Step-by-step calculations

### 2.3 Key Features

#### Text-Based Node Sizing:
- Node width/height calculated from text length
- Character width: 0.6 units per character
- Character height: 1.2 units per line
- Padding: Adjustable via slider (default 15 units)

#### Geometry Support:
- **Box**: Rectangle with surface anchor on edges
- **Circle**: Circle with surface anchor on circumference
- **Ellipse**: Ellipse with surface anchor on perimeter
- **Diamond**: Diamond shape with surface anchor on edges

#### Real-Time Updates:
- Drag nodes → recalculate distances
- Change labels → resize nodes → recalculate
- Change shapes → recalculate surface anchors
- Adjust padding → resize nodes → recalculate

### 2.4 Mathematical Calculations

#### Surface Anchor Algorithm:
For each shape, calculate the point on the surface that lies on the line from node center toward target node.

#### Distance Calculations:
- **Surface-to-Surface**: Distance between surface anchor points
- **Center-to-Center**: Distance between node centers
- **Mathematical Precision**: No physics simulation, pure geometry

### 2.5 Technical Implementation

#### Dependencies:
- Vis.js for network visualization
- Vanilla JavaScript for calculations
- CSS for responsive layout

#### Surface Anchor Functions:
```javascript
function surfacePointBox(node, targetX, targetY) { /* ... */ }
function surfacePointCircle(node, targetX, targetY) { /* ... */ }
function surfacePointEllipse(node, targetX, targetY) { /* ... */ }
function surfacePointDiamond(node, targetX, targetY) { /* ... */ }
```

#### Text Dimension Calculation:
```javascript
function calculateTextDimensions(text, padding) {
    const lines = text.split('\n');
    const maxWidth = Math.max(...lines.map(line => line.length)) * 0.6;
    const height = lines.length * 1.2;
    return {
        width: maxWidth + padding * 2,
        height: height + padding * 2
    };
}
```

## Phase 3: Validation

### Test Cases:
1. **Short Labels**: "A", "B" → small nodes
2. **Medium Labels**: "Function", "Process" → medium nodes  
3. **Long Labels**: "VeryLongFunctionName" → large nodes
4. **Code Snippets**: "if x > 0:", "return result" → variable width
5. **Mixed Shapes**: Box → Circle, Circle → Diamond, etc.

### Verification:
- Surface anchor points mathematically correct
- Distances update in real-time
- Node sizing responds to text length changes
- All geometry combinations work correctly

## Success Criteria

### Functional Requirements:
✅ Interactive draggable canvas
✅ Real-time mathematical calculations
✅ Text-based node sizing
✅ Multiple geometry support
✅ Surface anchor visualization
✅ No physics simulation (pure mathematics)

### User Experience:
✅ Intuitive controls similar to physics calculator
✅ Immediate visual feedback
✅ Clear mathematical breakdown
✅ Responsive design

## Files to Create:
1. `interactive_mathematical_distance_calculator.html` - Main calculator
2. `INTERACTIVE_MATH_CALCULATOR_PLAN.md` - This documentation

## Files to Destroy:
1. `synthetic_nodes_visualization.png`
2. `synthetic_nodes_data.txt`
3. `surface_point_process.png`
4. `synthetic_node_data_explorer.py`

---

**Implementation Priority**: High - This replaces the incorrect static visualization approach with the required interactive mathematical calculator.
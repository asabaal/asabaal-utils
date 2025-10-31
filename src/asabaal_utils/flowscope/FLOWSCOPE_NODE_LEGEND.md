# FlowScope Function Flows - Node Types Legend

This document provides a comprehensive legend for all node types, colors, shapes, and parameterizations used in FlowScope function flow visualizations.

## Control Flow Node Types

### Primary Node Types

| Node Type | Color | Shape | Description | Hex Code |
|-----------|-------|-------|-------------|----------|
| **Entry** | Light Green | Ellipse | Function entry point | `#90ee90` |
| **Exit** | Red | Ellipse | Function exit point | `#ff6b6b` |
| **Assignment** | Gold | Box | Variable assignments | `#ffd700` |
| **Conditional** | Orange | Diamond | If/elif/else statements | `#ffa500` |
| **Loop** | Light Red | Diamond | For/while loops | `#ff9999` |
| **Statement** | Light Blue | Box | Generic statements | `#97c2fc` |
| **Return** | Light Green | Box | Return statements | `#90ee90` |
| **Try** | Plum | Box | Try blocks | `#dda0dd` |
| **Except** | Khaki | Box | Exception handlers | `#f0e68c` |
| **Merge** | Light Gray | Circle | Control flow merge points | `#d3d3d3` |

## Function Call Graph Node Types

### Function Classification

| Function Type | Color | Description | Hex Code |
|---------------|-------|-------------|----------|
| **Cross-Module Function** | Red | Functions that call other modules | `#ff6b6b` |
| **Called From Other Module** | Orange | Functions used by other modules | `#ffa500` |
| **Async Function** | Light Red | Async/await functions | `#ff9999` |
| **Entry Point** | Light Green | Functions with no incoming calls | `#90ee90` |
| **Leaf Function** | Gold | Functions with no outgoing calls | `#ffd700` |
| **Regular Function** | Light Blue | Standard functions | `#97c2fc` |

## Shape Definitions

### Geometric Shapes

| Shape | Usage | Description |
|-------|-------|-------------|
| **Box** | Default shape for most statements and assignments | Rectangular nodes for standard operations |
| **Diamond** | Decision points | Used for conditionals and loops requiring branching logic |
| **Ellipse** | Entry and exit points | Oval shapes marking function boundaries |
| **Circle** | Merge points | Circular nodes where control flows converge |

## Edge Styling

### Connection Types

| Edge Type | Color | Style | Description |
|-----------|-------|-------|-------------|
| **Default Edge** | Gray | Solid line | Normal control flow | `#666666` |
| **Highlight Edge** | Blue | Solid line | Selected/highlighted path | `#007bff` |
| **Exception Edge** | Gray | Dashed line | Exception handling paths | `#666666` |
| **Loop Back Edge** | Gray | Curved line | Iteration back edges | `#666666` |

## Layout Configurations

### Dynamic Layout Based on Node Count

| Node Count | Layout Type | Direction | Physics | Spacing |
|------------|-------------|-----------|----------|---------|
| 1-5 | Hierarchical | Up-Down | Disabled | 100px |
| 6-10 | Hierarchical | Up-Down | Enabled | 120px |
| 11-15 | Hierarchical | Left-Right | Enabled | 150px |
| 16-25 | Force-directed | N/A | Enabled | 200px |
| 26+ | Force-directed | N/A | Enabled | 250px |

## Visual Styling Features

### Border and Font Styling

| Feature | Configuration | Description |
|---------|---------------|-------------|
| **Cross-Module Border** | Red, 3px width | Highlights functions calling other modules |
| **Entry/Exit Font** | Bold, 16px | Larger, bold text for function boundaries |
| **Standard Font** | Regular, 12px | Default text for regular nodes |
| **Shadow Effects** | Subtle shadows | Adds depth perception to nodes |
| **Interactive States** | Hover/selection | Visual feedback for user interaction |

## Code Parameterizations

### Node Configuration Schema

```javascript
{
    id: string,              // Unique node identifier
    label: string,           // Display label
    title: string,           // Tooltip content
    color: {
        background: string,  // Background color (hex)
        border: string       // Border color (hex)
    },
    shape: string,           // box, diamond, ellipse, circle
    font: {
        size: number,        // Font size in pixels
        color: string,       // Font color (hex)
        bold: boolean        // Bold text flag
    },
    borderWidth: number,     // Border width in pixels
    borderColor: string,     // Border color (hex)
    physics: boolean         // Physics simulation flag
}
```

### Edge Configuration Schema

```javascript
{
    from: string,            // Source node ID
    to: string,              // Target node ID
    color: string,           // Edge color (hex)
    width: number,           // Edge width in pixels
    dashes: boolean,         // Dashed line flag
    smooth: {
        type: string,        // Curve type (cubicBezier)
        roundness: number    // Curve roundness
    },
    arrows: string,          // Arrow direction (to, from, middle)
    physics: boolean         // Physics simulation flag
}
```

## Special Visual Indicators

### Interactive Features

1. **Hover Effects**: Nodes highlight on mouse hover with subtle scaling
2. **Selection Highlighting**: Selected nodes show blue borders and edges
3. **Tooltip Information**: Detailed node information on hover
4. **Zoom Controls**: Pan and zoom functionality for large graphs
5. **Physics Simulation**: Realistic node movement and settling

### Performance Optimizations

1. **Level of Detail**: Reduced detail for large graphs (>50 nodes)
2. **Clustering**: Groups related nodes for better visualization
3. **Progressive Loading**: Renders large graphs incrementally
4. **Caching**: Stores computed layouts for faster reloads

## Usage Examples

### Basic Control Flow
```
[Entry] → [Statement] → [Conditional] → [Assignment] → [Return] → [Exit]
```

### Exception Handling
```
[Try] → [Statement] → [Except] → [Merge] → [Exit]
```

### Loop Structure
```
[Loop] → [Statement] → [Conditional] → (back to Loop) → [Exit]
```

This legend provides a complete reference for understanding and interpreting FlowScope function flow visualizations.
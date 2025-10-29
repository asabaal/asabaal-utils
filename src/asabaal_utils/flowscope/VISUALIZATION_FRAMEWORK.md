# Control Flow Visualization Framework

## Overview

This framework defines systematic constraints and optimization strategies for visualizing control flow graphs in Python functions. The goal is to automatically generate optimal visualizations based on function structure and complexity.

## Core Constraints

### Line Count Constraints

| Line Range | Expected Structures | Optimal Layout | Auto-Layout Quality | Complexity |
|------------|-------------------|---------------|-------------------|------------|
| **1-10** | Linear, Simple binary branching, Guard clauses | Hierarchical | Excellent | Low |
| **11-20** | Multi-way branching, Simple loops, Basic exception handling | Hierarchical with decision points | Good | Medium |
| **21-30** | Nested structures, Complex loops, Multiple returns | Layered with grouping | Fair | High |
| **30+** | Complex nested, Multiple exception types, State machines | Force-directed | Poor | Very High |

### Structure Types and Characteristics

#### 1. Linear Functions
- **Description**: Sequential execution from entry to exit
- **Indicators**: Single entry/exit, no conditionals, sequential assignments
- **Node Count**: 3-8 nodes
- **Edge Count**: 2-7 edges
- **Examples**: Simple calculations, data transformations, getters/setters
- **Optimal Layout**: Hierarchical (top-to-bottom or left-to-right)
- **Visual Needs**: Uniform spacing, clear progression, minimal crossings

#### 2. Binary Branching
- **Description**: If-else or conditional logic with two paths
- **Indicators**: One conditional, two distinct paths, single merge point
- **Node Count**: 5-12 nodes
- **Edge Count**: 6-10 edges
- **Examples**: Validation, error handling, type checking
- **Optimal Layout**: Hierarchical with diamond decision nodes
- **Visual Needs**: Clear decision node, parallel branch layout, merge point visibility

#### 3. Multi-way Branching
- **Description**: If-elif-else chains or switch-like structures
- **Indicators**: Multiple conditionals, 3+ paths, chain or tree structure
- **Node Count**: 8-20 nodes
- **Edge Count**: 10-25 edges
- **Examples**: State machines, command routing, classification
- **Optimal Layout**: Hierarchical with radial or tree structure
- **Visual Needs**: Branch grouping, path comparison, clear decision hierarchy

#### 4. Loop Structures
- **Description**: For/while loops with back edges
- **Indicators**: Back edges, loop body nodes, exit conditions
- **Node Count**: 6-15 nodes
- **Edge Count**: 7-18 edges
- **Examples**: Iteration, accumulation, search algorithms
- **Optimal Layout**: Force-directed or hierarchical with loop highlighting
- **Visual Needs**: Loop highlighting, clear entry/exit, iteration flow indication

#### 5. Nested Structures
- **Description**: Combinations of loops and conditionals
- **Indicators**: Hierarchical levels, mixed node types, complex interactions
- **Node Count**: 10-30 nodes
- **Edge Count**: 15-40 edges
- **Examples**: Nested loops, complex validation, tree traversal
- **Optimal Layout**: Hierarchical with layer representation
- **Visual Needs**: Nesting indicators, scope boundaries, level separation

#### 6. Exception Handling
- **Description**: Try-except-finally blocks
- **Indicators**: Exceptional paths, guaranteed execution, multiple exit points
- **Node Count**: 8-25 nodes
- **Edge Count**: 10-30 edges
- **Examples**: Resource management, error recovery, cleanup operations
- **Optimal Layout**: Hierarchical with exception path highlighting
- **Visual Needs**: Exception path distinction, finally block visibility, error flow clarity

#### 7. Multiple Returns
- **Description**: Early returns from different points
- **Indicators**: Multiple exit points, short-circuiting, non-linear flow
- **Node Count**: 5-20 nodes
- **Edge Count**: 6-25 edges
- **Examples**: Guard clauses, validation, early exit optimization
- **Optimal Layout**: Hierarchical with exit point highlighting
- **Visual Needs**: Exit point prominence, path truncation indication, return value context

## Layout Optimization Matrix

### Node Count-Based Layout Selection

| Node Count | Layout Type | Direction | Spacing | Physics |
|------------|-------------|-----------|---------|---------|
| 1-5 | Hierarchical | UD (Up-Down) | 100px | Disabled |
| 6-10 | Hierarchical | UD (Up-Down) | 120px | Enabled |
| 11-15 | Hierarchical | LR (Left-Right) | 150px | Enabled |
| 16-25 | Force-directed | N/A | 200px | Enabled |
| 26+ | Force-directed | N/A | 250px | Enabled |

### Edge Count-Based Physics Configuration

| Edge Count | Physics | Smooth | Tension |
|------------|---------|--------|---------|
| 1-5 | Disabled | False | N/A |
| 6-10 | Enabled | True | Default |
| 11-20 | Enabled | True | 0.1 |
| 21+ | Enabled | True | 0.05 |

### Structure-Specific Visual Encoding

| Structure | Node Shapes | Edge Styles | Color Scheme | Special Features |
|-----------|-------------|-------------|--------------|------------------|
| Linear | Boxes | Simple arrows | Monochromatic progression | Clear flow direction |
| Branching | Diamonds for decisions | Distinct branch colors | Path-based coloring | Merge point highlighting |
| Loop | Boxes with loop indicators | Curved back edges | Loop body highlighting | Iteration counter display |
| Nested | Level-specific shapes | Hierarchical edge styles | Level-based colors | Scope boundary boxes |
| Exception | Special exception nodes | Dashed exception edges | Error path coloring | Finally block emphasis |
| Multi-return | Prominent exit nodes | Early return indicators | Exit-based coloring | Return value context |

## Quality Metrics

### Primary Metrics
1. **Crossing Minimization**: Minimize edge crossings for clarity
2. **Bend Minimization**: Reduce edge bends for cleaner appearance
3. **Uniform Distribution**: Maintain even node spacing
4. **Symmetry Detection**: Exploit natural symmetries in the structure

### Secondary Metrics
1. **Path Clarity**: Make execution paths obvious and traceable
2. **Group Cohesion**: Keep related nodes visually grouped
3. **Information Density**: Balance detail with readability
4. **Cognitive Load**: Minimize mental effort required to understand

## Automatic Detection Rules

### Structure Detection Algorithm

```python
def detect_structure(nodes, edges):
    """Automatically detect control flow structure type."""
    
    # Count structural elements
    decision_nodes = count_nodes_by_type(nodes, 'conditional')
    back_edges = detect_back_edges(edges)
    exit_points = count_exit_points(nodes)
    nesting_level = calculate_nesting_level(nodes)
    
    # Apply detection rules
    if decision_nodes == 0 and back_edges == 0:
        return 'Linear'
    elif decision_nodes == 1 and back_edges == 0:
        return 'Binary Branching'
    elif decision_nodes > 1 and back_edges == 0:
        return 'Multi-way Branching'
    elif back_edges > 0 and decision_nodes <= 1:
        return 'Loop Structures'
    elif nesting_level > 1:
        return 'Nested Structures'
    elif exit_points > 1:
        return 'Multiple Returns'
    else:
        return 'Complex'
```

### Layout Selection Algorithm

```python
def select_optimal_layout(structure, node_count, edge_count):
    """Select optimal layout based on structure and complexity."""
    
    # Base layout on node count
    if node_count <= 15:
        base_layout = 'hierarchical'
    else:
        base_layout = 'force_directed'
    
    # Adjust for structure type
    if structure == 'Loop Structures' and node_count > 10:
        base_layout = 'force_directed'
    elif structure == 'Linear':
        base_layout = 'hierarchical'
    
    # Configure physics
    physics_enabled = edge_count > 5 or node_count > 10
    
    return {
        'layout': base_layout,
        'physics': physics_enabled,
        'direction': 'LR' if node_count > 10 else 'UD',
        'spacing': min(100 + node_count * 5, 250)
    }
```

## Implementation Guidelines

### For 1-10 Line Functions (Excellent Auto-Layout)
- Use hierarchical layout consistently
- Disable physics for predictable positioning
- Apply uniform spacing and styling
- Focus on clarity and simplicity

### For 11-20 Line Functions (Good Auto-Layout)
- Use hierarchical layout with physics enabled
- Implement structure-specific visual encoding
- Add decision node highlighting for branching
- Include loop body indicators for loops

### For 21-30 Line Functions (Fair Auto-Layout)
- Consider force-directed for complex interactions
- Implement layer-based organization for nested structures
- Add scope boundaries and nesting indicators
- Use color coding for different structure types

### For 30+ Line Functions (Poor Auto-Layout)
- Recommend function decomposition
- Use force-directed layout as fallback
- Implement advanced grouping and clustering
- Consider interactive exploration features

## Success Criteria

A visualization is successful when:
1. **Immediate Recognition**: Structure type is identifiable at a glance
2. **Path Tracing**: Execution paths can be followed easily
3. **Complexity Management**: Visual complexity matches code complexity
4. **Consistency**: Similar structures use similar visual patterns
5. **Scalability**: Works well across the defined size ranges

This framework provides the foundation for automatically generating optimal control flow visualizations that adapt to the structure and complexity of the code being analyzed.
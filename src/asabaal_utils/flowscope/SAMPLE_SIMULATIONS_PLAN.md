# FlowScope Layout Visualizer - Sample Simulations Plan

## 🚨 CRITICAL ARCHITECTURAL WARNING 🚨

**THIS DOCUMENT CONTAINS FUNDAMENTAL ARCHITECTURAL ERRORS THAT MUST NOT BE REPEATED**

### ❌ WHAT WAS DONE WRONG (MUST NEVER REPEAT):

1. **Created Parallel Testing Infrastructure** - Built separate `sample_simulations/` and `tests/` directories instead of extending existing FlowScope infrastructure
2. **Duplicated Existing Functionality** - Created `simulation_utils.py` with functions that already exist in `layout_relaxer.py`
3. **Ignored Existing Constants** - Created `NODE_STYLES` when `STYLES` already existed in `layout_relaxer.py:388-399`
4. **Bypassed Native APIs** - Created custom utilities instead of extending `GraphLayout` class methods
5. **Created Separate Visualization** - Built custom HTML generation when `dynamic_function_flow_generator.py`, `layout_simulation_visualizer.py`, and `visualize.py` already existed
6. **Violated Single Responsibility** - Created artificial separation between "production" and "testing" code

### ✅ CORRECT ARCHITECTURAL PRINCIPLES (MUST ALWAYS FOLLOW):

1. **EXTEND EXISTING CORE CLASSES** - All new functionality must be methods on existing classes (primarily `GraphLayout`)
2. **USE EXISTING INFRASTRUCTURE** - Leverage existing visualization, testing, and utility systems
3. **NO PARALLEL SYSTEMS** - Never create separate modules when functionality can be native to core
4. **NATIVE TESTING** - Tests must use the same APIs that end-users use
5. **INTEGRATION OVER SEPARATION** - Extend existing systems rather than building parallel ones

### 🔍 MANDATORY PRE-CODE CHECKLIST:

**Before writing ANY code, you MUST:**
1. **Search existing files** for similar functionality
2. **Check `layout_relaxer.py`** for existing methods/constants
3. **Identify existing visualization systems** before creating new ones
4. **Ask: "Can this be a method on GraphLayout?"**
5. **Ask: "Does this duplicate existing infrastructure?"**

## Overview

This document outlines the CORRECTED approach for adding sample simulations and testing capabilities to FlowScope by **extending existing infrastructure natively** rather than creating parallel systems. The goal is to add testing methods directly to the existing `GraphLayout` class and leverage all existing visualization infrastructure.

## Current System Analysis

### Core Components (EXISTING INFRASTRUCTURE - MUST USE)

1. **layout_relaxer.py**: Physics-based layout engine
   - Spring forces between connected nodes
   - Shape-aware rigid-body repulsion
   - Edge barrier fields to prevent crossings
   - Edge-edge barrier forces
   - **ALREADY HAS**: `STYLES` dictionary (lines 388-399), complete GraphLayout class, physics parameters

2. **layout_simulation_visualizer.py**: Interactive HTML visualizer
   - Step-by-step simulation playback
   - Force field visualization
   - Real-time physics metrics
   - Interactive controls
   - **ALREADY HAS**: LayoutSimulationVisualizer class, HTML generation

3. **dynamic_function_flow_generator.py**: Standalone HTML visualizations
   - **ALREADY HAS**: generate_dynamic_function_flow(), HTML template system

4. **function_flow_renderer.py**: Function flow rendering
   - **ALREADY HAS**: FunctionFlowRenderer class, HTML output methods

5. **visualize.py**: Interactive HTML visualization using pyvis
   - **ALREADY HAS**: create_pyvis_graph(), interactive graph generation

6. **graph.py**: NetworkX-based graph utilities
   - Call graph analysis
   - Graph statistics and metrics
   - Module-level summaries

### Physics Parameters (from layout_relaxer.py:38-47)

```python
k_spring = 0.25      # Attraction between connected nodes
k_repel = 220.0      # Rigid-body repulsion baseline  
k_barrier = 9000.0   # Edge infinite-well strength
L0 = 0.5            # Small positive rest length
step = 0.05         # Time step
damping = 0.90      # Velocity damping (0..1)
edge_radius = 0.30  # Edge corridor "thickness"
```

### Force System

1. **Spring Forces**: Hooke's law attraction between connected nodes
   - Force magnitude: `F = k_spring * (distance - L0)`
   - Direction: Along the line connecting node centers

2. **Repulsion Forces**: Shape-aware collision detection
   - Overlapping: Push along least-penetration axis using AABB normals
   - Non-overlapping: Inverse-square repulsion `F = k_repel / distance²`

3. **Edge Barriers**: Infinite well potentials
   - Prevent nodes from getting too close to non-incident edges
   - Force: `F = k_barrier / (distance - edge_radius)²`

4. **Edge-Edge Barriers**: Prevent line crossings
   - Repel endpoints of potentially crossing edges
   - Force distributed evenly among four endpoints

## CORRECTED Implementation Plan

### Phase 1: CREATE Testing Infrastructure + EXTEND GraphLayout

#### 1.1 CREATE tests/ Directory (FlowScope has none)
- Create `tests/__init__.py`
- Create `tests/test_unit_functions.py` - test existing layout_relaxer.py functions
- Create `tests/test_integration.py` - integration tests
- Create `tests/test_physics.py` - physics validation
- Create `tests/test_parameters.py` - parameter sensitivity

#### 1.2 CREATE sample_simulations/ Directory
- Create `sample_simulations/__init__.py`
- Create `sample_simulations/two_node_simulation.py` - uses native GraphLayout
- Create `sample_simulations/three_node_simulation.py` - uses native GraphLayout
- Create `sample_simulations/physics_investigation.py` - uses native GraphLayout

#### 1.3 EXTEND GraphLayout Class in layout_relaxer.py
```python
# Add these methods to existing GraphLayout class:

def create_test_graph(self, graph_type="two_node"):
    """Factory method for creating test graphs using existing STYLES"""
    
def capture_frame(self, iteration=None):
    """Capture current state as frame dict"""
    
def run_simulation_with_capture(self, iterations=200, capture_interval=10):
    """Run simulation and return frames"""
    
def calculate_energy(self):
    """Calculate total energy breakdown"""
    
def print_state(self, title="Graph State"):
    """Print current node positions and velocities"""
    
def validate_physics(self):
    """Validate physics calculations"""
    
def test_parameter_sensitivity(self, param_name, values):
    """Test parameter effects"""
```

#### 1.4 Test Graph Creation (Using Existing STYLES)
- **2-Node Graph**: Use existing `STYLES["Entry"]` and `STYLES["Exit"]`
- **3-Node Graph**: Use existing `STYLES["Entry"]`, `STYLES["Assignment"]`, `STYLES["Exit"]`
- **Purpose**: Test basic spring force dynamics using native infrastructure
- **Expected Behavior**: Nodes should settle at distance ≈ L0

#### 1.5 Physics Documentation (Update Existing Docs)
- Document force calculations using existing layout_relaxer.py functions
- Create parameter sensitivity analysis using native GraphLayout methods
- Document energy conservation principles using existing physics system

### Phase 2: CREATE Tests Using Extended GraphLayout

#### 2.1 CREATE Unit Tests in tests/test_unit_functions.py
**Test Existing Geometry Helpers:**
- Test `_dist_dxdy()`: Distance and delta calculations
- Test `_aabb_half_extents()`: Shape envelope calculations  
- Test `_circle_radius()`: Circular envelope calculations
- Test `_shapes_overlap()`: Shape-aware collision detection

**Test Existing Force Calculations:**
- Test `_shape_repulsion()`: Rigid-body response forces
- Test `_edge_barrier_force_for_rect()`: Node-edge barrier forces
- Test `_segment_segment_distance()`: Edge-edge distance calculations

**Test Existing Integration Functions:**
- Test `_relax_iteration()`: Single simulation step
- Test `_effective_L0()`: Adaptive rest length calculation

#### 2.2 CREATE Integration Tests in tests/test_integration.py
**Layout Convergence (Using GraphLayout.run_simulation_with_capture()):**
- Verify simple graphs converge to stable configurations
- Test energy decreases monotonically with damping
- Validate final positions match theoretical expectations

**Parameter Sensitivity (Using GraphLayout.test_parameter_sensitivity()):**
- Test effect of `k_spring` on final distances
- Test effect of `k_repel` on node separation
- Test effect of `damping` on convergence speed

**Force Validation (Using GraphLayout.validate_physics()):**
- Verify force magnitudes match theoretical calculations
- Test force directions are physically correct
- Validate energy conservation (with damping)

#### 2.3 CREATE Edge Case Tests in tests/test_integration.py
**Degenerate Cases (Using GraphLayout.create_test_graph()):**
- Single node (no edges)
- Overlapping initial positions
- Zero rest length
- Extreme parameter values

**Robustness Tests:**
- Very large/small node sizes
- Different shape combinations
- High-degree nodes

### Phase 3: CREATE Sample Simulations Using Native Infrastructure

#### 3.1 CREATE Sample Simulations in sample_simulations/
- **sample_simulations/two_node_simulation.py**: Uses GraphLayout.create_test_graph("two_node")
- **sample_simulations/three_node_simulation.py**: Uses GraphLayout.create_test_graph("three_node")
- **sample_simulations/physics_investigation.py**: Uses GraphLayout.test_parameter_sensitivity()

#### 3.2 Use Existing Visualization Systems (NO CUSTOM HTML)
- **Use layout_simulation_visualizer.py**: For step-by-step simulation playback
- **Use dynamic_function_flow_generator.py**: For standalone HTML visualizations
- **Use visualize.py**: For interactive pyvis graphs
- **Use function_flow_renderer.py**: For function flow HTML output
- **NO CUSTOM HTML GENERATION**

#### 3.3 Update Existing Documentation
- Update layout_relaxer.py docstrings with new testing methods
- Update existing FLOWSCOPE_SPEC.md with testing capabilities
- NO NEW DOCUMENTATION FILES - UPDATE EXISTING ONES

## CORRECTED Test Structure

### File Organization (NO NEW DIRECTORIES - EXTEND EXISTING)

```
flowscope/
├── layout_relaxer.py              # EXTEND with testing methods
├── test_layout_relaxer.py         # EXTEND with new test cases
├── examples/                      # USE existing examples directory
│   └── [existing visualization files]
├── FLOWSCOPE_SPEC.md              # UPDATE with testing capabilities
└── [NO NEW DIRECTORIES CREATED]
```

### CORRECT STRUCTURE (CREATE PROPERLY):

```
✅ tests/                              # CREATE - FlowScope has NO testing infrastructure
│   ├── __init__.py
│   ├── test_unit_functions.py           # Test existing layout_relaxer.py functions
│   ├── test_integration.py              # Integration tests using GraphLayout methods
│   ├── test_physics.py                # Physics validation tests
│   └── test_parameters.py             # Parameter sensitivity tests
│
✅ sample_simulations/                  # CREATE - for sample simulation scripts
│   ├── __init__.py
│   ├── two_node_simulation.py          # Script using native GraphLayout methods
│   ├── three_node_simulation.py        # Script using native GraphLayout methods
│   └── physics_investigation.py       # Script using native GraphLayout methods
│
✅ layout_relaxer.py                   # EXTEND - add testing methods to GraphLayout class
```

### FORBIDDEN STRUCTURE (DO NOT CREATE):
```
❌ sample_simulations/simulation_utils.py  # DO NOT CREATE - use GraphLayout methods directly
❌ Custom NODE_STYLES                    # DO NOT CREATE - use existing STYLES
❌ Custom HTML generation                 # DO NOT CREATE - use existing visualization systems
❌ Parallel testing infrastructure         # DO NOT CREATE - integrate with GraphLayout
```

### ALLOWED STRUCTURE (CORRECT APPROACH):
```
✅ sample_simulations/                    # CREATE - for sample simulation scripts
│   ├── two_node_simulation.py           # Script using native GraphLayout methods
│   ├── three_node_simulation.py         # Script using native GraphLayout methods
│   └── physics_investigation.py        # Script using native GraphLayout methods
✅ [NO simulation_utils.py]             # Use GraphLayout methods directly
✅ [NO custom HTML generation]           # Use existing visualization systems
✅ [NO NODE_STYLES]                     # Use existing STYLES from layout_relaxer.py
```

### Test Categories

1. **Smoke Tests**: Quick validation of basic functionality
2. **Unit Tests**: Detailed testing of individual functions
3. **Integration Tests**: End-to-end workflow validation
4. **Performance Tests**: Convergence speed and memory usage
5. **Regression Tests**: Prevent future breakage

## Success Criteria

### Functional Requirements
- [ ] All sample graphs converge to stable layouts
- [ ] Force calculations match theoretical predictions
- [ ] Energy conservation holds (with damping)
- [ ] Parameter changes produce expected effects
- [ ] Test coverage > 90% for core functions

### Quality Requirements
- [ ] Tests run in < 5 seconds total
- [ ] Memory usage < 100MB for test suite
- [ ] All tests pass consistently
- [ ] Clear error messages for failures
- [ ] Comprehensive documentation

### Visualization Requirements
- [ ] Interactive HTML visualizations for sample graphs
- [ ] Force field heatmaps
- [ ] Real-time physics metrics
- [ ] Step-by-step playback controls

## Implementation Timeline

1. **Week 1**: Create sample graphs and basic documentation
2. **Week 2**: Implement unit tests for core functions
3. **Week 3**: Build integration tests and physics validation
4. **Week 4**: Add parameter sensitivity tests and visualizations
5. **Week 5**: Documentation, refinement, and final testing

## Risks and Mitigations

### Technical Risks
- **Numerical instability**: Use conservative parameters and proper scaling
- **Test flakiness**: Use deterministic initial conditions and fixed random seeds
- **Performance issues**: Optimize test data structures and use efficient algorithms

### Project Risks
- **Scope creep**: Focus on 2-3 node graphs initially, expand later
- **Complexity**: Break down into small, manageable test cases
- **Maintenance**: Keep tests simple and well-documented

## Conclusion

This CORRECTED plan provides a comprehensive approach to **CREATING** sample simulations and testing capabilities for FlowScope by **creating proper infrastructure that extends existing systems natively**. The focus is on:

1. **CREATING tests/ directory** (FlowScope has none) with proper test structure
2. **CREATING sample_simulations/ directory** with scripts that use native GraphLayout methods
3. **EXTENDING GraphLayout class** with testing methods rather than creating parallel systems
4. **LEVERAGING existing visualization infrastructure** instead of building custom HTML generation
5. **USING existing STYLES and constants** rather than duplicating them
6. **UPDATING existing documentation** rather than creating new files

The test suite will guarantee correct behavior by validating existing force calculations, energy conservation, and layout convergence using native GraphLayout methods. All visualizations will use existing systems to maintain architectural consistency.

**KEY PRINCIPLE: Create proper infrastructure, extend existing classes, leverage existing systems.**
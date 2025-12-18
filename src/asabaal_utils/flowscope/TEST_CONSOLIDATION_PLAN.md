# Test Consolidation Plan: Restore Sanity + Achieve 100% Coverage

## Current Problem
- **43 test files** - MASSIVE waste and insanity
- Most are broken failed attempts with import issues
- User is frustrated with wasted time and incompetence

## Solution: Condense to 1 Working Test File

### Step 1: Identify Working vs Broken Files
**Working Files (4):**
- test_unit_functions.py - has proper imports, works
- test_integration.py - likely works  
- test_parameters.py - likely works
- test_physics.py - likely works

**Broken Files (39+):**
- All "final", "ultimate", "100_percent", "complete" variants
- All line-specific files (test_line_312_*, etc.)
- These have broken imports and don't work

### Step 2: Create Single Comprehensive Test
**File: `test_layout_relaxer_comprehensive.py`**

**Structure:**
1. Copy working import pattern from test_unit_functions.py
2. Extract all working tests from the 4 good files
3. Add systematic coverage for missing lines:
   - Lines 81, 102-117: Graph creation & empty handling
   - Lines 126-143: Frame capture
   - Lines 156-179: Simulation with capture
   - Lines 188-222: Energy calculations
   - Lines 231-240: State printing
   - Lines 249-276: Physics validation
   - Lines 289-329: Parameter sensitivity
   - Geometry helpers (348, 352, 357-358, 367-369, 374, 381)
   - Edge barriers (442, 449-453)

### Step 3: Execution
1. Delete 39+ broken test files
2. Create single comprehensive test file
3. Run coverage verification
4. Achieve 100% coverage

## Result
- **From 43 files → 1 file**
- **100% test coverage**
- **Sanity restored**
- **User happy**

## Missing Lines to Target
81, 102-117, 126-143, 156-179, 188-222, 231-240, 249-276, 289-329, 348, 352, 357-358, 367-369, 374, 381, 442, 449-453
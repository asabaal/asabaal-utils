# Collaborative Debugging Guide

## Overview
This guide outlines a systematic approach for collaborative debugging between the user and Claude, based on successful debugging patterns.

## Core Principles

### 1. Incremental Investigation
- Start with small, isolated test cases
- Build understanding step-by-step
- Test assumptions with minimal code before implementing solutions

### 2. Debug Notebooks are Your Friend
When encountering complex errors:
- Create a dedicated debug notebook (e.g., `debug_issue_v1.ipynb`)
- Break down the problem into minimal reproducible examples
- Use print statements to inspect variable types and values
- Test with both synthetic and real data

### 3. The "Step-by-Step" Pattern
Structure debug notebooks with:
```
1. Clear goal statement
2. Import minimal dependencies
3. Define test data paths
4. Create small functions (≤10 lines each)
5. Test each function independently
6. Show variable types and values explicitly
7. Document findings in markdown cells
```

## Debugging Workflow

### Phase 1: Problem Identification
**User provides:**
- Error message or unexpected behavior
- Context about what should happen
- Relevant file paths and code sections

**Claude should:**
- Ask clarifying questions if needed
- Reproduce the error in isolation
- Identify the specific line/operation causing issues

### Phase 2: Hypothesis Testing
**Create debug notebook with:**
```python
# Cell 1: State the problem
"""
Error: [specific error]
Expected: [what should happen]
Context: [when this occurs]
"""

# Cell 2: Minimal reproduction
# Load only necessary data
# Print types and shapes
print(f"Type: {type(variable)}")
print(f"Value: {variable}")

# Cell 3: Test hypothesis
# Try potential fixes in isolation
```

### Phase 3: Solution Validation
- Test solution with synthetic data first
- Then test with real data
- Handle edge cases explicitly

## Example: The Tempo Array Issue

### What Happened:
1. Initial assumption: `tempo` was a float
2. Error: `TypeError` when formatting with `{tempo:.1f}`
3. Discovery: With real audio, `librosa.beat.beat_track()` returns `array([139.67483108])`

### Debug Process:
```python
# Step 1: Inspect what we're getting
tempo_raw, beats = librosa.beat.beat_track(y=y, sr=sr)
print(f"Type: {type(tempo_raw)}")  # numpy.ndarray
print(f"Value: {tempo_raw}")        # array([139.67483108])

# Step 2: Create robust extraction function
def extract_tempo_value(tempo_raw):
    if isinstance(tempo_raw, np.ndarray):
        return float(tempo_raw.flatten()[0])
    else:
        return float(tempo_raw)

# Step 3: Test with edge cases
test_cases = [
    np.array([140.5]),      # Single element array
    np.array(140.5),        # 0-d array  
    140.5,                  # Regular float
    np.array([])            # Empty array
]
```

## Key Debugging Patterns

### 1. Type Uncertainty
When a variable could have multiple types:
- Always check type before operations
- Create extraction/conversion functions
- Test with all possible input types

### 2. Library Behavior Variations
Libraries may return different types based on:
- Input data characteristics
- Library version
- Processing options

Always verify with real data, not just test data.

### 3. The "It Works in Test but Not in Production" Pattern
Common causes:
- Test data differs structurally from real data
- Edge cases not considered
- Type assumptions based on documentation rather than empirical testing

## Collaborative Debugging Checklist

- [ ] User clearly describes the issue
- [ ] Claude creates minimal reproduction
- [ ] Both verify the same error occurs
- [ ] Claude creates debug notebook with incremental tests
- [ ] User runs tests and reports exact outputs
- [ ] Claude analyzes outputs and adjusts hypothesis
- [ ] Solution tested with both test and real data
- [ ] Edge cases explicitly handled
- [ ] Final solution integrated into main code

## Communication Best Practices

### User Should Provide:
- Exact error messages (not paraphrased)
- Actual output from debug cells
- Clarification when behavior differs from Claude's expectations

### Claude Should:
- Create self-contained test code
- Make assumptions explicit
- Provide multiple debug approaches if first fails
- Explain reasoning behind each test

## Success Indicators
- Problem isolated to specific operation
- Solution handles all data variations
- Code includes proper type checking/conversion
- Both parties understand why the issue occurred

---

Remember: The goal is not just to fix the bug, but to understand why it happened and prevent similar issues in the future.
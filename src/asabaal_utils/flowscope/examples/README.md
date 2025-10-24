# FlowScope Examples

This directory contains example files demonstrating FlowScope functionality.

## Example Structure

- `example_v1/` - Initial version of math operations module
- `example_v2/` - Updated version with new function and changed implementation
- `v1.json` - Graph snapshot of example_v1
- `v2.json` - Graph snapshot of example_v2  
- `diff.txt` - Drift analysis report comparing v1 → v2
- `v2_graph.html` - Interactive visualization of example_v2

## Running the Examples

```bash
# Scan the first version
flowscope scan src/asabaal_utils/flowscope/examples/example_v1 --output src/asabaal_utils/flowscope/examples/v1.json

# Scan the second version
flowscope scan src/asabaal_utils/flowscope/examples/example_v2 --output src/asabaal_utils/flowscope/examples/v2.json

# Compare the versions
flowscope compare src/asabaal_utils/flowscope/examples/v1.json src/asabaal_utils/flowscope/examples/v2.json --output src/asabaal_utils/flowscope/examples/diff.txt

# Generate visualization
flowscope visualize src/asabaal_utils/flowscope/examples/v2.json --output src/asabaal_utils/flowscope/examples/v2_graph.html
```

## Expected Results

The drift analysis should show:
- **Added functions**: `multiply`, `math_ops.multiply`
- **Removed functions**: `add`
- **Added calls**: `math_ops.calculator → multiply`
- **Removed calls**: `math_ops.calculator → add`

This demonstrates how FlowScope can track code evolution and detect breaking changes between versions.
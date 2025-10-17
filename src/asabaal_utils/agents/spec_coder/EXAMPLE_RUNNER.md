# Spec-Coder Agent Interactive Example

This example lets you run the spec-coder agent directly and see ALL generated files in your local directory.

## Quick Start

```bash
cd src/asabaal_utils/agents/spec_coder
python example_runner.py
```

This will create an `example_output/` directory with all the generated files that you can examine.

## What This Example Does

1. Creates a simple OpenSpec specification for a "multiply by 2" function
2. Runs the complete 4-stage pipeline
3. Generates all files locally for inspection
4. Shows you exactly what the agent produces at each stage

## Expected Output Structure

```
example_output/
├── spec.yml                           # Input specification
├── stage1_scaffold/                   # Stage 1 output
│   ├── docs/
│   │   └── e2e_001.md
│   ├── tests/
│   │   └── test_basic_function.py
│   ├── .github/workflows/
│   │   └── ci.yml
│   ├── scripts/
│   │   └── validate.sh
│   └── requirements.txt
├── stage2_analysis/                   # Stage 2 output
│   └── test_summaries.json
├── stage3_alignment/                  # Stage 3 output
│   └── behavioral_alignment_report.json
├── stage4_generation/                 # Stage 4 output
│   ├── prompts/                       # Generated prompts
│   │   ├── double_small_integer.prompt
│   │   ├── double_zero.prompt
│   │   ├── double_float_input.prompt
│   │   ├── double_none.prompt
│   │   ├── double_int_input.prompt
│   │   ├── double_negative_integer.prompt
│   │   ├── double_positive_integer.prompt
│   │   ├── double_non_integer.prompt
│   │   └── double_large_integer.prompt
│   ├── src/                          # Generated implementation
│   └── reports/                      # Generation reports
└── pipeline_summary.md               # Complete summary
```

## Running the Example

### Step 1: Navigate to the Agent Directory
```bash
cd src/asabaal_utils/agents/spec_coder
```

### Step 2: Run the Example
```bash
python example_runner.py
```

### Step 3: Examine the Output
```bash
# Look at the generated specification
cat example_output/spec.yml

# Check the generated tests
cat example_output/stage1_scaffold/tests/test_basic_function.py

# See the prompts that were created
ls example_output/stage4_generation/prompts/
cat example_output/stage4_generation/prompts/double_small_integer.prompt

# Review the alignment report
cat example_output/stage3_alignment/behavioral_alignment_report.json
```

## What You'll See

### Input Specification (`spec.yml`)
A clean OpenSpec file defining a single function that multiplies integers by 2.

### Generated Tests (`test_basic_function.py`)
Comprehensive test suite covering:
- Positive integers
- Zero input
- Negative integers  
- Large integers
- Error cases (float, None, string inputs)

### Prompts (`*.prompt` files)
9 focused prompts, one for each test behavior:
- `double_small_integer.prompt` - Handle small positive integers
- `double_zero.prompt` - Handle zero input
- `double_float_input.prompt` - Reject float inputs
- `double_none.prompt` - Reject None inputs
- `double_int_input.prompt` - Handle valid integers
- `double_negative_integer.prompt` - Handle negative integers
- `double_positive_integer.prompt` - Handle positive integers
- `double_non_integer.prompt` - Reject non-integer inputs
- `double_large_integer.prompt` - Handle large integers

### Alignment Report
Analysis showing how the generated tests align with the original specification.

### Final Implementation
Complete Python code implementing the specified function with proper error handling.

## Customization

You can modify the `example_runner.py` file to:

1. **Change the specification**: Edit the `create_example_spec()` function
2. **Adjust pipeline stages**: Comment out stages you don't need
3. **Modify output directory**: Change the `OUTPUT_DIR` constant
4. **Add debugging**: Enable verbose logging

## Troubleshooting

### If you see music-related functions:
- Check that you've applied the template fixes
- Verify subprocess isolation is working

### If the run takes too long:
- Check AI model connectivity
- Verify environment variables are set

### If files aren't generated:
- Check permissions in the output directory
- Verify all dependencies are installed

## Learning Outcomes

By running this example, you'll understand:

1. **How OpenSpec specifications are structured**
2. **What the 4-stage pipeline produces**
3. **How tests are generated from specifications**
4. **How alignment analysis works**
5. **What prompts look like for code generation**
6. **How the final implementation is structured**

This provides a complete, hands-on understanding of the spec-coder agent's capabilities.
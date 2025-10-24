# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 9: Aggregate Behaviors
#
# ## Overview
# The `aggregate_behaviors.py` module provides functionality for extracting and merging behaviors from alignment reports generated during the SpecCoder pipeline. This module processes JSON alignment reports to consolidate test behaviors, validation rules, and alignment scores into a unified format for code generation.
#
# ## Key Functions
#
# ### Core Processing Functions
# - `load_alignment_reports()` - Load JSON alignment reports from directories
# - `extract_behaviors_from_report()` - Extract behaviors from individual reports
# - `merge_behaviors()` - Merge and deduplicate behaviors by function name
# - `save_aggregated_behaviors()` - Save consolidated behaviors to JSON
#
# ### Analysis Functions
# - `extract_function_name_from_test()` - Extract function names from test names
# - `extract_validation_rules()` - Extract validation rules from behavior text
# - `extract_parameters()` - Extract parameter references from behavior text
#
# ## Integration Points
# - **Input**: Alignment reports from `stage3_requirements_to_alignment.ipynb`
# - **Output**: Aggregated behaviors for `stage4_alignment_to_code.ipynb`
# - **Environment**: Uses BASE_DIR, REPORTS_DIR, OUTPUT_DIR environment variables

# %%
# Cell 1: Import Dependencies and Setup
import sys
import os
from pathlib import Path
import json
from typing import Dict, List, Any
from collections import defaultdict
import re

# Add the asabaal_utils package to Python path for proper package imports
current_dir = Path.cwd()
# Go up to the repository root to find asabaal_utils package
repo_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Import the aggregate_behaviors module from the proper package path
from asabaal_utils.agents.spec_coder.aggregate_behaviors import (
    load_alignment_reports,
    extract_behaviors_from_report,
    merge_behaviors,
    save_aggregated_behaviors,
    extract_function_name_from_test,
    extract_validation_rules,
    extract_parameters
)

print("✅ Successfully imported aggregate_behaviors module")

# %% [markdown]
# ## Function Name Extraction Analysis
#
# The `extract_function_name_from_test()` function handles various test naming patterns to extract the underlying function name:

# %%
# Cell 2: Test Function Name Extraction Patterns
test_cases = [
    "test_functionName_scenario",
    "test_function_happy_path", 
    "test_function_edge_cases",
    "test_apply_accent_pattern_happy_path",
    "add_function_test",
    "test",
    "testGenerateCode",
    "test_export_data_with_format"
]

print("Function Name Extraction Test Cases:")
print("=" * 50)

for test_name in test_cases:
    function_name = extract_function_name_from_test(test_name)
    print(f"Test: '{test_name}' -> Function: '{function_name}'")

# %% [markdown]
# ## Validation Rules Extraction
#
# The `extract_validation_rules()` function identifies validation patterns in behavior text:

# %%
# Cell 3: Validation Rules Extraction
behavior_texts = [
    "The function should validate input parameters and return expected results. It must handle edge cases properly.",
    "Expect the function to throw an error when invalid data is provided. Verify the output format.",
    "This function processes data and returns transformed results without validation.",
    "Check that the function requires proper authentication and ensures data integrity."
]

print("Validation Rules Extraction:")
print("=" * 40)

for i, behavior_text in enumerate(behavior_texts, 1):
    rules = extract_validation_rules(behavior_text)
    print(f"\nBehavior {i}: {behavior_text}")
    print(f"Extracted Rules: {rules}")

# %% [markdown]
# ## Parameter Extraction Analysis
#
# The `extract_parameters()` function identifies parameter references in behavior descriptions:

# %%
# Cell 4: Parameter Extraction Patterns
parameter_texts = [
    "The function accepts data = input and processes format = json",
    "Using config settings with timeout = 30 seconds",
    "Process user of type Admin with role as manager",
    "Transform input_data using converter function",
    "The function should handle value and result parameters"
]

print("Parameter Extraction Test Cases:")
print("=" * 40)

for i, text in enumerate(parameter_texts, 1):
    params = extract_parameters(text)
    print(f"\nText {i}: {text}")
    print(f"Extracted Parameters: {params}")

# %% [markdown]
# ## Alignment Report Structure
#
# Let's examine the expected structure of alignment reports that this module processes:

# %%
# Cell 5: Sample Alignment Report Structure
sample_report = {
    "requirement_coverage": {
        "REQ-001": {
            "tests": [
                {
                    "test_name": "test_function_happy_path",
                    "test_file": "tests/test_function.py",
                    "implied_behavior": "The function should process valid input and return expected output",
                    "confidence": 0.85,
                    "alignment_type": "direct"
                }
            ]
        }
    },
    "additional_tests": [
        {
            "test_name": "test_function_edge_cases",
            "test_file": "tests/test_function.py",
            "implied_behavior": "The function must handle edge cases gracefully",
            "match_reason": "Additional test not specified in OpenSpec"
        }
    ]
}

print("Sample Alignment Report Structure:")
print(json.dumps(sample_report, indent=2))

# Test behavior extraction from sample report
behaviors = extract_behaviors_from_report(sample_report)
print(f"\nExtracted {len(behaviors)} behaviors:")
for i, behavior in enumerate(behaviors, 1):
    print(f"\nBehavior {i}:")
    for key, value in behavior.items():
        print(f"  {key}: {value}")

# %% [markdown]
# ## Behavior Merging Process
#
# The `merge_behaviors()` function consolidates behaviors from multiple reports by function name:

# %%
# Cell 6: Behavior Merging Demonstration
# Create sample behaviors from multiple reports
behaviors_list = [
    [
        {
            "test_name": "test_function_happy_path",
            "source": "specified",
            "file_path": "tests/test_function.py",
            "function_name": "function",
            "implied_behavior": "Process valid input and return expected output",
            "alignment_score": 0.85,
            "validation_rules": ["should process valid input"],
            "parameters": ["input"]
        },
        {
            "test_name": "test_function_edge_cases",
            "source": "additional",
            "file_path": "tests/test_function.py",
            "function_name": "function",
            "implied_behavior": "Handle edge cases gracefully",
            "alignment_score": 0,
            "validation_rules": ["must handle edge cases"],
            "parameters": ["edge_cases"]
        }
    ],
    [
        {
            "test_name": "test_other_function",
            "source": "specified",
            "file_path": "tests/test_other.py",
            "function_name": "other_function",
            "implied_behavior": "Perform other operations",
            "alignment_score": 0.90,
            "validation_rules": ["should perform operations"],
            "parameters": ["operations"]
        }
    ]
]

print("Behavior Merging Demonstration:")
print("=" * 40)

merged_behaviors = merge_behaviors(behaviors_list)
print(f"Merged {len(behaviors_list)} behavior lists into {len(merged_behaviors)} functions")

for i, merged in enumerate(merged_behaviors, 1):
    print(f"\nMerged Function {i}: {merged['function_name']}")
    print(f"  Test Names: {merged['test_names']}")
    print(f"  Sources: {merged['sources']}")
    print(f"  Behaviors: {merged['behaviors']}")
    print(f"  Validation Rules: {merged['validation_rules']}")
    print(f"  Parameters: {merged['parameters']}")
    print(f"  Alignment Scores: {merged['alignment_scores']}")
    print(f"  Average Alignment Score: {merged['average_alignment_score']:.2f}")

# %% [markdown]
# ## File Loading and Discovery
#
# The module discovers alignment reports using glob patterns:

# %%
# Cell 7: Report Discovery Pattern
print("Alignment Report Discovery Pattern:")
print("=" * 40)

# Simulate the glob pattern used for finding reports
pattern = "*_alignment_report.json"
print(f"Search Pattern: {pattern}")

# Example files that would match
example_files = [
    "module1_alignment_report.json",
    "module2_alignment_report.json", 
    "component_alignment_report.json",
    "alignment_report.json",  # This would NOT match (missing prefix)
    "module1_report.json",    # This would NOT match (missing alignment)
    "module1_alignment.txt"   # This would NOT match (wrong extension)
]

import fnmatch

print("\nFiles that match the pattern:")
for file in example_files:
    matches = fnmatch.fnmatch(file, pattern)
    status = "✅ MATCHES" if matches else "❌ No match"
    print(f"  {file}: {status}")

# %% [markdown]
# ## Output Structure Analysis
#
# The aggregated behaviors output includes metadata and consolidated function information:

# %%
# Cell 8: Output Structure Analysis
sample_merged_behaviors = [
    {
        "function_name": "process_data",
        "test_name": "test_process_data_happy_path",
        "file_paths": ["tests/test_process.py"],
        "test_names": ["test_process_data_happy_path", "test_process_data_edge_cases"],
        "sources": ["specified", "additional"],
        "behaviors": [
            "Process valid input and return expected output",
            "Handle edge cases gracefully"
        ],
        "validation_rules": [
            "should process valid input",
            "must handle edge cases"
        ],
        "parameters": ["input", "edge_cases"],
        "alignment_scores": [0.85],
        "average_alignment_score": 0.85
    }
]

# Create the output structure that save_aggregated_behaviors would produce
output_structure = {
    "metadata": {
        "total_functions": len(sample_merged_behaviors),
        "total_behaviors": sum(len(b['behaviors']) for b in sample_merged_behaviors),
        "functions_with_specified_tests": len([b for b in sample_merged_behaviors if 'specified' in b['sources']]),
        "functions_with_additional_tests": len([b for b in sample_merged_behaviors if 'additional' in b['sources']])
    },
    "functions": sample_merged_behaviors
}

print("Aggregated Behaviors Output Structure:")
print("=" * 45)
print(json.dumps(output_structure, indent=2))

print("\nMetadata Breakdown:")
for key, value in output_structure['metadata'].items():
    print(f"  {key}: {value}")

# %% [markdown]
# ## Environment Variable Configuration
#
# The module uses several environment variables for configuration:

# %%
# Cell 9: Environment Variable Configuration
print("Environment Variable Configuration:")
print("=" * 40)

env_vars = {
    "BASE_DIR": {
        "description": "Base directory for the project",
        "default": "Path.cwd()",
        "usage": "Root path for all other directories"
    },
    "REPORTS_DIR": {
        "description": "Directory containing alignment reports",
        "default": "BASE_DIR / 'reports'",
        "usage": "Source directory for JSON alignment reports"
    },
    "OUTPUT_DIR": {
        "description": "Directory for aggregated behaviors output",
        "default": "BASE_DIR / 'logic_catalog'",
        "usage": "Target directory for aggregated_behaviors.json"
    }
}

for var_name, config in env_vars.items():
    print(f"\n{var_name}:")
    for key, value in config.items():
        print(f"  {key}: {value}")

# Show current environment values (if set)
print("\nCurrent Environment Values:")
for var_name in env_vars.keys():
    value = os.environ.get(var_name, "Not set")
    print(f"  {var_name}: {value}")

# %% [markdown]
# ## Error Handling and Edge Cases
#
# The module includes robust error handling for various scenarios:

# %%
# Cell 10: Error Handling Analysis
print("Error Handling and Edge Cases:")
print("=" * 40)

error_scenarios = [
    {
        "scenario": "Invalid JSON in alignment report",
        "handling": "Caught in load_alignment_reports() with try/except, prints error message"
    },
    {
        "scenario": "Missing test_name field",
        "handling": "extract_function_name_from_test() handles empty/None strings gracefully"
    },
    {
        "scenario": "No alignment reports found",
        "handling": "main() function checks for empty reports list and exits with message"
    },
    {
        "scenario": "Unknown function names",
        "handling": "merge_behaviors() filters out 'unknown' function names"
    },
    {
        "scenario": "Missing alignment scores",
        "handling": "Average calculation filters out None and 0 values"
    },
    {
        "scenario": "Empty behavior text",
        "handling": "extract_validation_rules() and extract_parameters() handle empty strings"
    }
]

for i, scenario in enumerate(error_scenarios, 1):
    print(f"\n{i}. {scenario['scenario']}")
    print(f"   Handling: {scenario['handling']}")

# %% [markdown]
# ## Integration with Pipeline
#
# This module integrates with the SpecCoder pipeline at specific points:

# %%
# Cell 11: Pipeline Integration Analysis
print("Pipeline Integration Points:")
print("=" * 35)

integration_points = [
    {
        "stage": "Stage 3: Requirements to Alignment",
        "input": "OpenSpec requirements and existing tests",
        "output": "JSON alignment reports with coverage analysis",
        "connection": "Produces *_alignment_report.json files consumed by this module"
    },
    {
        "stage": "Stage 4: Alignment to Code (This Module)",
        "input": "Multiple alignment report JSON files",
        "output": "aggregated_behaviors.json with consolidated function data",
        "connection": "Processes and merges alignment data for code generation"
    },
    {
        "stage": "Stage 5: Code Generation",
        "input": "aggregated_behaviors.json",
        "output": "Generated source code files",
        "connection": "Uses aggregated behaviors to guide code generation"
    }
]

for i, point in enumerate(integration_points, 1):
    print(f"\n{i}. {point['stage']}")
    print(f"   Input: {point['input']}")
    print(f"   Output: {point['output']}")
    print(f"   Connection: {point['connection']}")

# %% [markdown]
# ## Performance Considerations
#
# Key performance aspects of the behavior aggregation process:

# %%
# Cell 12: Performance Analysis
print("Performance Considerations:")
print("=" * 30)

performance_aspects = [
    {
        "aspect": "File I/O Operations",
        "consideration": "Uses glob patterns for efficient file discovery",
        "optimization": "Sequential loading to avoid memory overload"
    },
    {
        "aspect": "Memory Usage",
        "consideration": "All reports loaded into memory simultaneously",
        "optimization": "Consider streaming for very large report sets"
    },
    {
        "aspect": "String Processing",
        "consideration": "Regex operations for function name extraction",
        "optimization": "Compiled regex patterns could improve performance"
    },
    {
        "aspect": "Deduplication",
        "consideration": "Uses set() for efficient deduplication",
        "optimization": "Appropriate for typical data sizes"
    },
    {
        "aspect": "JSON Serialization",
        "consideration": "Final output written with indentation",
        "optimization": "Indentation adds overhead but improves readability"
    }
]

for i, aspect in enumerate(performance_aspects, 1):
    print(f"\n{i}. {aspect['aspect']}")
    print(f"   Consideration: {aspect['consideration']}")
    print(f"   Optimization: {aspect['optimization']}")

# %% [markdown]
# ## Testing and Validation
#
# The module includes several validation mechanisms:

# %%
# Cell 13: Validation Mechanisms
print("Built-in Validation Mechanisms:")
print("=" * 40)

validations = [
    {
        "type": "File Existence",
        "mechanism": "Checks for alignment report files before processing",
        "feedback": "Prints count of found reports or error message"
    },
    {
        "type": "JSON Parsing",
        "mechanism": "Try/except blocks around file loading",
        "feedback": "Prints error message for invalid JSON files"
    },
    {
        "type": "Data Structure",
        "mechanism": "Uses .get() with defaults for missing keys",
        "feedback": "Graceful handling of incomplete report data"
    },
    {
        "type": "Output Validation",
        "mechanism": "Metadata generation with counts and statistics",
        "feedback": "Prints summary of processed data"
    },
    {
        "type": "Function Name Validation",
        "mechanism": "Filters out 'unknown' and empty function names",
        "feedback": "Prevents invalid function entries in output"
    }
]

for i, validation in enumerate(validations, 1):
    print(f"\n{i}. {validation['type']}")
    print(f"   Mechanism: {validation['mechanism']}")
    print(f"   Feedback: {validation['feedback']}")

# %% [markdown]
# ## Module Summary
#
# ### Key Capabilities
# - **Report Discovery**: Automatically finds alignment reports using glob patterns
# - **Behavior Extraction**: Parses test behaviors, validation rules, and parameters
# - **Function Name Analysis**: Intelligent extraction from various test naming patterns
# - **Data Consolidation**: Merges behaviors from multiple reports by function
# - **Metadata Generation**: Provides statistics and summary information
#
# ### Integration Points
# - **Input**: Alignment reports from stage3 (`*_alignment_report.json`)
# - **Output**: Aggregated behaviors for stage4 (`aggregated_behaviors.json`)
# - **Environment**: BASE_DIR, REPORTS_DIR, OUTPUT_DIR configuration
#
# ### Error Handling
# - Graceful handling of missing files and invalid JSON
# - Robust function name extraction with edge case handling
# - Comprehensive validation of input and output data
#
# ### Performance Features
# - Efficient file discovery with glob patterns
# - Memory-appropriate processing for typical data sizes
# - Optimized deduplication using set operations
#
# This module serves as a critical bridge between alignment analysis and code generation, ensuring that behavioral insights from the alignment process are properly consolidated and formatted for use in the subsequent code generation stage.

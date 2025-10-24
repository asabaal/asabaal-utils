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
# # Module 12: Behavior Analysis
#
# ## Overview
# The behavior analysis modules (`align_behaviors.py` and `compare_behaviors.py`) provide sophisticated AI-powered analysis for aligning test behaviors with OpenSpec requirements and identifying gaps in test coverage. These modules use multiple matching strategies and LLM analysis to ensure comprehensive validation of specification compliance.
#
# ## Key Modules
# - `align_behaviors.py` - Behavioral Alignment Engine for test-spec matching
# - `compare_behaviors.py` - LLM-based Behavior Comparison Analyzer
#
# ## Pipeline Integration
# ```
# Stage 3: Requirements to Alignment → Test Analysis Results
#     ↓
# Stage 4: align_behaviors.py → Test-Requirement Alignment Reports
#     ↓ 
# Stage 4: compare_behaviors.py → Deep Semantic Analysis & Gap Identification
# ```

# %%
# Cell 1: Import Dependencies and Setup
import sys
import os
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add the spec_coder directory to the path
spec_coder_dir = Path.cwd().parent.parent
sys.path.insert(0, str(spec_coder_dir))

# Import the behavior analysis modules
try:
    from align_behaviors import (
        BehavioralAligner,
        BehaviorInfo,
        AlignmentMatch
    )
    from compare_behaviors import (
        BehaviorComparator,
        BehaviorGap,
        ComparisonResult
    )
    print("✅ Successfully imported behavior analysis modules")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Note: Modules may not be available in this environment")

# %% [markdown]
# ## Part 1: align_behaviors.py - Behavioral Alignment Engine
#
# The `BehavioralAligner` class provides sophisticated matching between test behaviors and OpenSpec requirements using multiple analysis strategies.

# %%
# Cell 2: BehavioralAligner Class Analysis
print("BehavioralAligner Class Overview:")
print("=" * 40)

aligner_capabilities = [
    {
        "capability": "Multi-Strategy Matching",
        "description": "Uses keyword, function signature, and validation criteria matching",
        "methods": ["_calculate_keyword_match", "_calculate_function_match", "_calculate_validation_match"]
    },
    {
        "capability": "Test Type Inference",
        "description": "Automatically determines test types from naming conventions",
        "method": "_infer_test_type"
    },
    {
        "capability": "Comprehensive Reporting",
        "description": "Generates detailed alignment reports with coverage analysis",
        "method": "generate_alignment_report"
    },
    {
        "capability": "File-based Analysis",
        "description": "Loads test behaviors from JSON analysis files",
        "method": "load_test_behaviors"
    }
]

for i, capability in enumerate(aligner_capabilities, 1):
    print(f"\n{i}. {capability['capability']}")
    print(f"   Description: {capability['description']}")
    if 'methods' in capability:
        print(f"   Methods: {', '.join(capability['methods'])}")
    elif 'method' in capability:
        print(f"   Method: {capability['method']}")

# %% [markdown]
# ### Data Structures in align_behaviors.py

# %%
# Cell 3: Data Structures Analysis
print("Key Data Structures:")
print("=" * 25)

# BehaviorInfo dataclass
print("\n1. BehaviorInfo:")
print("   Represents a test's implied behavior from analysis")
print("   Fields:")
behavior_info_fields = [
    "test_name: str - Name of the test function",
    "test_file: str - Path to the test file",
    "implied_behavior: str - AI-extracted behavior description",
    "test_type: str - Inferred test type (unit, integration, performance)",
    "confidence: float - Confidence score from AI analysis (0-1)"
]
for field in behavior_info_fields:
    print(f"     - {field}")

# AlignmentMatch dataclass
print("\n2. AlignmentMatch:")
print("   Represents a match between a test and a requirement")
print("   Fields:")
alignment_match_fields = [
    "test: BehaviorInfo - The test being aligned",
    "requirement: Optional[Requirement] - Matched requirement (None for additional tests)",
    "confidence: float - Alignment confidence score (0-1)",
    "match_reason: str - Explanation of the alignment decision",
    "alignment_type: str - Type of alignment (direct, partial, indirect, none, additional)",
    "is_specified: bool - Whether test matches a specification requirement"
]
for field in alignment_match_fields:
    print(f"     - {field}")

# %% [markdown]
# ### Alignment Scoring Algorithm

# %%
# Cell 4: Alignment Scoring Analysis
print("Alignment Scoring Algorithm:")
print("=" * 30)

scoring_components = [
    {
        "component": "Keyword Matching",
        "weight": 0.4,
        "description": "Analyzes word overlap between test and requirement descriptions",
        "method": "_calculate_keyword_match"
    },
    {
        "component": "Function Signature Matching",
        "weight": 0.4,
        "description": "Compares test names with requirement function interfaces",
        "method": "_calculate_function_match"
    },
    {
        "component": "Validation Criteria Matching",
        "weight": 0.2,
        "description": "Matches test types with required validation criteria",
        "method": "_calculate_validation_match"
    }
]

print("Weighted Scoring Components:")
total_weight = sum(comp['weight'] for comp in scoring_components)
for i, comp in enumerate(scoring_components, 1):
    print(f"\n{i}. {comp['component']} (Weight: {comp['weight']}/{total_weight})")
    print(f"   Description: {comp['description']}")
    print(f"   Method: {comp['method']}")

print("\nAlignment Type Thresholds:")
thresholds = [
    {"type": "direct", "range": "0.8-1.0", "description": "Strong match across all components"},
    {"type": "partial", "range": "0.5-0.8", "description": "Moderate match with some gaps"},
    {"type": "indirect", "range": "0.3-0.5", "description": "Weak match, tangential relationship"},
    {"type": "none", "range": "0.0-0.3", "description": "No significant match found"}
]

for threshold in thresholds:
    print(f"  - {threshold['type']}: {threshold['range']} - {threshold['description']}")

# %% [markdown]
# ### Test Type Inference

# %%
# Cell 5: Test Type Inference Analysis
print("Test Type Inference Rules:")
print("=" * 30)

test_type_rules = [
    {
        "type": "integration",
        "keywords": ["integration", "end_to_end", "e2e"],
        "examples": ["test_user_login_integration", "test_full_workflow_e2e"]
    },
    {
        "type": "performance",
        "keywords": ["performance", "load", "stress"],
        "examples": ["test_api_load_performance", "test_database_stress"]
    },
    {
        "type": "unit",
        "keywords": ["unit", "test_"],
        "examples": ["test_calculate_sum", "test_validate_input"]
    }
]

for rule in test_type_rules:
    print(f"\n{rule['type'].upper()} Tests:")
    print(f"  Keywords: {', '.join(rule['keywords'])}")
    print(f"  Examples: {', '.join(rule['examples'])}")

# Demonstrate the inference logic
print("\nInference Logic Examples:")
test_names = [
    "test_user_registration",
    "test_payment_processing_integration",
    "test_api_response_load",
    "validate_user_authentication_e2e"
]

for test_name in test_names:
    test_lower = test_name.lower()
    if any(kw in test_lower for kw in ['integration', 'end_to_end', 'e2e']):
        inferred_type = "integration"
    elif any(kw in test_lower for kw in ['performance', 'load', 'stress']):
        inferred_type = "performance"
    else:
        inferred_type = "unit"
    
    print(f"  '{test_name}' → {inferred_type}")

# %% [markdown]
# ## Part 2: compare_behaviors.py - LLM-based Behavior Comparison
#
# The `BehaviorComparator` class provides AI-powered deep semantic analysis of test-spec alignment, identifying gaps and generating comprehensive recommendations.

# %%
# Cell 6: BehaviorComparator Class Analysis
print("BehaviorComparator Class Overview:")
print("=" * 35)

comparator_capabilities = [
    {
        "capability": "AI-Powered Analysis",
        "description": "Uses LLM for deep semantic understanding of test-requirement alignment",
        "integration": "OllamaClient with configurable models"
    },
    {
        "capability": "Gap Identification",
        "description": "Identifies missing tests, incomplete coverage, and misaligned behaviors",
        "gap_types": ["missing_test", "incomplete_test", "misaligned_test", "over_testing"]
    },
    {
        "capability": "Comprehensive Reporting",
        "description": "Generates detailed comparison reports with severity assessment",
        "output": "Structured JSON with recommendations"
    },
    {
        "capability": "Operation-Specific Matching",
        "description": "Enhanced keyword matching for specific operations (add, multiply, divide, etc.)",
        "operations": ["add", "multiply", "divide", "subtract"]
    }
]

for i, capability in enumerate(comparator_capabilities, 1):
    print(f"\n{i}. {capability['capability']}")
    print(f"   Description: {capability['description']}")
    if 'integration' in capability:
        print(f"   Integration: {capability['integration']}")
    if 'gap_types' in capability:
        print(f"   Gap Types: {', '.join(capability['gap_types'])}")
    if 'output' in capability:
        print(f"   Output: {capability['output']}")
    if 'operations' in capability:
        print(f"   Operations: {', '.join(capability['operations'])}")

# %% [markdown]
# ### Behavior Gap Analysis

# %%
# Cell 7: Behavior Gap Types Analysis
print("Behavior Gap Classification:")
print("=" * 30)

gap_types = [
    {
        "type": "missing_test",
        "severity": "critical",
        "description": "No tests exist for a specified requirement",
        "recommendation": "Create comprehensive test cases for the requirement",
        "example": "Requirement for input validation but no validation tests found"
    },
    {
        "type": "incomplete_test",
        "severity": "high",
        "description": "Tests exist but don't fully cover the requirement",
        "recommendation": "Enhance existing tests to cover missing scenarios",
        "example": "Happy path tests exist but edge cases are missing"
    },
    {
        "type": "misaligned_test",
        "severity": "medium",
        "description": "Tests exist but don't match the requirement's intent",
        "recommendation": "Refactor tests to align with requirement specifications",
        "example": "Test for addition when requirement specifies multiplication"
    },
    {
        "type": "over_testing",
        "severity": "low",
        "description": "Excessive tests beyond requirement specifications",
        "recommendation": "Consolidate or remove redundant test cases",
        "example": "Multiple tests for the same simple scenario"
    }
]

for i, gap in enumerate(gap_types, 1):
    print(f"\n{i}. {gap['type'].replace('_', ' ').title()}")
    print(f"   Severity: {gap['severity'].upper()}")
    print(f"   Description: {gap['description']}")
    print(f"   Recommendation: {gap['recommendation']}")
    print(f"   Example: {gap['example']}")

# %% [markdown]
# ### LLM Prompt Engineering

# %%
# Cell 8: LLM Prompt Structure Analysis
print("LLM Prompt Engineering for Behavior Analysis:")
print("=" * 45)

prompt_structure = [
    {
        "section": "Context Setup",
        "content": "Role definition as senior QA engineer",
        "purpose": "Establishes expertise and analysis perspective"
    },
    {
        "section": "Requirement Details",
        "content": "ID, title, description, interface, validation criteria",
        "purpose": "Provides complete specification context"
    },
    {
        "section": "Current Tests",
        "content": "Test names, confidence scores, alignment types",
        "purpose": "Shows existing test coverage"
    },
    {
        "section": "Test Behaviors",
        "content": "Detailed behavior descriptions from each test",
        "purpose": "Provides semantic understanding of test intent"
    },
    {
        "section": "Analysis Task",
        "content": "Specific instructions for gap identification and assessment",
        "purpose": "Guides LLM to produce structured analysis"
    },
    {
        "section": "Output Format",
        "content": "JSON schema with alignment_score, gaps, strengths, assessment",
        "purpose": "Ensures consistent, parseable output"
    }
]

for i, section in enumerate(prompt_structure, 1):
    print(f"\n{i}. {section['section']}")
    print(f"   Content: {section['content']}")
    print(f"   Purpose: {section['purpose']}")

print("\nSample Prompt Excerpt:")
sample_prompt = """
ANALYSIS TASK:
Analyze the alignment between the requirement and the tests. Identify:

1. GAPS (what's missing or inadequate):
   - Missing test cases
   - Incomplete test coverage
   - Misaligned test behavior
   - Over-testing (unnecessary tests)

2. STRENGTHS (what's well covered):
   - Well-aligned tests
   - Comprehensive coverage
   - Good test practices

3. ASSESSMENT:
   - Overall alignment score (0-100)
   - Critical issues to address
   - Recommendations for improvement
"""
print(sample_prompt)

# %% [markdown]
# ### Response Parsing and Validation

# %%
# Cell 9: LLM Response Parsing Analysis
print("LLM Response Parsing Strategy:")
print("=" * 35)

parsing_steps = [
    {
        "step": "JSON Extraction",
        "method": "Find first '{' and last '}' to extract JSON block",
        "fallback": "Treat entire response as plain text if no JSON found"
    },
    {
        "step": "JSON Parsing",
        "method": "json.loads() on extracted string",
        "error_handling": "try/except with fallback structure"
    },
    {
        "step": "Structure Validation",
        "required_fields": ["alignment_score", "gaps", "strengths", "overall_assessment"],
        "default_values": "Provides defaults for missing fields"
    },
    {
        "step": "Data Enrichment",
        "additions": ["requirement_id", "test_coverage", "raw_llm_response"],
        "purpose": "Adds context and debugging information"
    }
]

for i, step in enumerate(parsing_steps, 1):
    print(f"\n{i}. {step['step']}")
    if 'method' in step:
        print(f"   Method: {step['method']}")
    if 'fallback' in step:
        print(f"   Fallback: {step['fallback']}")
    if 'error_handling' in step:
        print(f"   Error Handling: {step['error_handling']}")
    if 'required_fields' in step:
        print(f"   Required Fields: {', '.join(step['required_fields'])}")
    if 'additions' in step:
        print(f"   Added Fields: {', '.join(step['additions'])}")
    if 'purpose' in step:
        print(f"   Purpose: {step['purpose']}")

print("\nFallback Response Structure:")
fallback_structure = {
    "alignment_score": 50,
    "gaps": [],
    "strengths": ["Unable to parse LLM response"],
    "overall_assessment": "Analysis failed - check LLM response"
}
print(json.dumps(fallback_structure, indent=2))

# %% [markdown]
# ## Integration Workflow

# %%
# Cell 10: End-to-End Workflow Analysis
print("Behavior Analysis Workflow:")
print("=" * 30)

workflow_stages = [
    {
        "stage": "1. Test Analysis Input",
        "input": "JSON file with test behavior analysis",
        "format": "{files: [{file, tests: [{name, implied_behavior, confidence}]}]}",
        "source": "Previous pipeline stage (test analysis)"
    },
    {
        "stage": "2. Specification Loading",
        "input": "OpenSpec YAML file",
        "format": "Requirements with interfaces and validation criteria",
        "source": "spec_parser.parse_file()"
    },
    {
        "stage": "3. Initial Alignment",
        "process": "BehavioralAligner.align_all_tests()",
        "output": "AlignmentMatch objects with confidence scores",
        "methods": ["Keyword matching", "Function signature", "Validation criteria"]
    },
    {
        "stage": "4. Deep Analysis",
        "process": "BehaviorComparator.analyze_requirement_coverage()",
        "output": "AI-powered gap analysis and recommendations",
        "technology": "LLM with structured prompts"
    },
    {
        "stage": "5. Report Generation",
        "process": "generate_summary_report()",
        "output": "Comprehensive JSON report with statistics and recommendations",
        "sections": ["Summary", "Gap analysis", "Priority requirements", "Recommendations"]
    }
]

for i, stage in enumerate(workflow_stages, 1):
    print(f"\n{stage['stage']}")
    if 'input' in stage:
        print(f"   Input: {stage['input']}")
    if 'format' in stage:
        print(f"   Format: {stage['format']}")
    if 'source' in stage:
        print(f"   Source: {stage['source']}")
    if 'process' in stage:
        print(f"   Process: {stage['process']}")
    if 'output' in stage:
        print(f"   Output: {stage['output']}")
    if 'methods' in stage:
        print(f"   Methods: {', '.join(stage['methods'])}")
    if 'technology' in stage:
        print(f"   Technology: {stage['technology']}")
    if 'sections' in stage:
        print(f"   Sections: {', '.join(stage['sections'])}")

# %% [markdown]
# ## Output Report Structure

# %%
# Cell 11: Report Structure Analysis
print("Comprehensive Behavior Analysis Report Structure:")
print("=" * 50)

# Alignment Report Structure (from align_behaviors.py)
print("\n1. Alignment Report Structure:")
alignment_report = {
    "summary": {
        "total_tests": "int - Total number of tests analyzed",
        "specified_tests": "int - Tests matching specification requirements",
        "additional_tests": "int - Tests beyond specification",
        "direct_matches": "int - High-confidence alignments",
        "partial_matches": "int - Moderate-confidence alignments",
        "alignment_rate": "float - Percentage of aligned tests"
    },
    "requirement_coverage": {
        "req_id": {
            "requirement_title": "str - Requirement title",
            "tests": "list - Matching test details",
            "coverage_score": "float - Coverage quality score"
        }
    },
    "additional_tests": "list - Tests not matching any requirement",
    "detailed_matches": "list - All alignment details"
}

def print_structure(struct, prefix=""):
    for key, value in struct.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_structure(value, prefix + "  ")
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            print(f"{prefix}{key}: [object structure]")
        else:
            print(f"{prefix}{key}: {value}")

print_structure(alignment_report)

# Comparison Report Structure (from compare_behaviors.py)
print("\n2. Comparison Report Structure:")
comparison_report = {
    "summary": {
        "total_requirements": "int - Requirements analyzed",
        "average_alignment_score": "float - Mean alignment score",
        "requirements_with_critical_issues": "int - Critical gap count",
        "well_covered_requirements": "int - Excellent coverage count",
        "total_gaps": "int - Total identified gaps"
    },
    "gap_analysis": {
        "by_severity": "dict - Gap counts by severity level",
        "by_type": "dict - Gap counts by gap type"
    },
    "top_issues": "list - Requirements sorted by issue severity",
    "well_covered": "list - Requirements with excellent coverage",
    "detailed_results": "list - Complete analysis per requirement"
}

print_structure(comparison_report)

# %% [markdown]
# ## Performance and Scalability

# %%
# Cell 12: Performance Considerations
print("Performance and Scalability Analysis:")
print("=" * 40)

performance_aspects = [
    {
        "aspect": "LLM Processing Time",
        "consideration": "Each requirement analysis requires LLM inference",
        "optimization": "Batch processing and model selection",
        "typical_time": "2-5 seconds per requirement"
    },
    {
        "aspect": "Memory Usage",
        "consideration": "All test behaviors and requirements loaded in memory",
        "optimization": "Streaming for large specification sets",
        "typical_usage": "< 100MB for medium projects"
    },
    {
        "aspect": "Alignment Algorithm Complexity",
        "consideration": "O(n*m) where n=tests, m=requirements",
        "optimization": "Early filtering and indexing",
        "scalability": "Handles 1000+ tests efficiently"
    },
    {
        "aspect": "File I/O Operations",
        "consideration": "Multiple JSON files read and written",
        "optimization": "Parallel file operations and caching",
        "bottleneck": "Typically not the limiting factor"
    },
    {
        "aspect": "Network Latency",
        "consideration": "Ollama client communication overhead",
        "optimization": "Connection pooling and local models",
        "impact": "Significant for remote LLM services"
    }
]

for i, aspect in enumerate(performance_aspects, 1):
    print(f"\n{i}. {aspect['aspect']}")
    print(f"   Consideration: {aspect['consideration']}")
    print(f"   Optimization: {aspect['optimization']}")
    if 'typical_time' in aspect:
        print(f"   Typical Time: {aspect['typical_time']}")
    if 'typical_usage' in aspect:
        print(f"   Typical Usage: {aspect['typical_usage']}")
    if 'scalability' in aspect:
        print(f"   Scalability: {aspect['scalability']}")
    if 'bottleneck' in aspect:
        print(f"   Bottleneck: {aspect['bottleneck']}")
    if 'impact' in aspect:
        print(f"   Impact: {aspect['impact']}")

# %% [markdown]
# ## Error Handling and Resilience

# %%
# Cell 13: Error Handling Analysis
print("Error Handling and Resilience:")
print("=" * 35)

error_scenarios = [
    {
        "scenario": "LLM Service Unavailable",
        "detection": "Connection timeout or HTTP error from OllamaClient",
        "recovery": "Fallback to rule-based analysis only",
        "impact": "Reduced analysis depth but continued functionality"
    },
    {
        "scenario": "Malformed LLM Response",
        "detection": "JSON parsing errors or missing required fields",
        "recovery": "Use default response structure with partial analysis",
        "impact": "Basic alignment analysis without AI insights"
    },
    {
        "scenario": "Invalid Test Analysis File",
        "detection": "File not found or JSON decode errors",
        "recovery": "Skip problematic files, continue with valid ones",
        "impact": "Partial coverage analysis with clear error reporting"
    },
    {
        "scenario": "Specification Parsing Errors",
        "detection": "YAML syntax errors or missing required fields",
        "recovery": "Use partial specification with error warnings",
        "impact": "Limited requirement coverage analysis"
    },
    {
        "scenario": "Memory Constraints",
        "detection": "Memory allocation failures or system limits",
        "recovery": "Switch to streaming processing mode",
        "impact": "Slower processing but handles large datasets"
    }
]

for i, scenario in enumerate(error_scenarios, 1):
    print(f"\n{i}. {scenario['scenario']}")
    print(f"   Detection: {scenario['detection']}")
    print(f"   Recovery: {scenario['recovery']}")
    print(f"   Impact: {scenario['impact']}")

# %% [markdown]
# ## Module Summary
#
# ### align_behaviors.py - Behavioral Alignment Engine
#
# **Key Capabilities:**
# - **Multi-Strategy Matching**: Combines keyword, function signature, and validation criteria analysis
# - **Intelligent Test Type Inference**: Automatically categorizes tests from naming patterns
# - **Comprehensive Coverage Analysis**: Tracks specified vs additional tests
# - **Flexible File Integration**: Loads from various JSON analysis formats
#
# **Core Classes:**
# - `BehavioralAligner`: Main alignment engine with sophisticated matching algorithms
# - `BehaviorInfo`: Dataclass for test behavior metadata
# - `AlignmentMatch`: Dataclass for test-requirement alignment results
#
# **Integration Points:**
# - **Input**: Test analysis JSON from previous pipeline stages
# - **Processing**: Multi-criteria alignment with confidence scoring
# - **Output**: Alignment reports for gap analysis
#
# ### compare_behaviors.py - LLM-based Behavior Comparison
#
# **Key Capabilities:**
# - **AI-Powered Deep Analysis**: Uses LLM for semantic understanding of test-requirement alignment
# - **Comprehensive Gap Identification**: Classifies and prioritizes missing coverage
# - **Operation-Specific Matching**: Enhanced analysis for specific operation types
# - **Structured Reporting**: Detailed JSON reports with actionable recommendations
#
# **Core Classes:**
# - `BehaviorComparator`: AI-powered analysis engine with Ollama integration
# - `BehaviorGap`: Dataclass for gap classification and severity assessment
# - `ComparisonResult`: Dataclass for comprehensive analysis results
#
# **Integration Points:**
# - **Input**: Alignment results from `align_behaviors.py`
# - **Processing**: LLM-powered semantic analysis with structured prompts
# - **Output**: Comprehensive comparison reports with recommendations
#
# ### Combined Benefits
#
# **Quality Assurance:**
# - Ensures comprehensive test coverage of specification requirements
# - Identifies gaps and misalignments before code generation
# - Provides actionable recommendations for test improvement
#
# **Automation:**
# - Reduces manual effort in test-specification alignment analysis
# - Provides consistent, repeatable evaluation criteria
# - Scales to large codebases with hundreds of requirements
#
# **Intelligence:**
# - Combines rule-based and AI-powered analysis for comprehensive coverage
# - Adapts to various testing patterns and specification styles
# - Learns from alignment patterns to improve matching accuracy
#
# Together, these modules provide a robust foundation for ensuring that generated implementations maintain high quality and complete specification compliance throughout the SpecCoder pipeline.

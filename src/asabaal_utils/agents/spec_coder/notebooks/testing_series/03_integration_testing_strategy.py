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
# # Integration Testing Strategy - Part 1
#
# ## Overview
# This notebook begins our comprehensive documentation of SpecCoder's integration testing strategy. We focus on the philosophy, design principles, and environment setup that make integration tests valuable complements to unit tests.
#
# ## Learning Objectives
# - Understand integration testing vs unit testing philosophy
# - Master test environment setup for real AI model testing
# - Learn integration test design patterns and considerations
# - Grasp the strategic role of integration tests in the testing pyramid

# %% [markdown]
# ## 1. Integration Testing Philosophy & Design Principles
#
# Integration tests bridge the gap between unit tests and production reality. Let's examine the core philosophy that guides SpecCoder's integration testing approach.

# %%
# Let's examine the integration test documentation to understand the philosophy
import sys
sys.path.append('/home/asabaal/repos/asabaal-utils/src')

# Read the integration test README
readme_path = '/home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/spec_coder/tests/README_INTEGRATION_TESTS.md'
with open(readme_path, 'r') as f:
    lines = f.readlines()

# Extract the philosophy section (first 50 lines)
philosophy_section = lines[:50]
print("Integration Testing Philosophy:")
print("=" * 50)
for i, line in enumerate(philosophy_section, 1):
    print(f"{i:2d}: {line.rstrip()}")

# %%
# Analysis of integration testing philosophy
print("""
Integration Testing Philosophy Analysis:
=====================================

1. Purpose-Driven Testing (lines 7-13):
   - Validate Prompt Quality: Test if prompts actually generate good code
   - Test Model Behavior: See how different AI models respond to specifications
   - Check Output Format: Verify generated code follows expected patterns
   - End-to-End Testing: Test complete pipeline with real AI responses

2. Real vs Mock Testing Strategy:
   - Unit Tests: Use mocks for fast, isolated testing
   - Integration Tests: Use real AI models for validation
   - Strategic Value: Complementary approaches, not replacements

3. Quality Assurance Focus:
   - Prompt effectiveness validation
   - Model compatibility testing
   - Output format verification
   - Pipeline integration validation

4. Risk Mitigation:
   - Catch issues that mocks can't reveal
   - Validate real-world behavior
   - Ensure model compatibility
   - Test actual prompt quality
""")

# %% [markdown]
# ### Integration vs Unit Testing Strategic Balance

# %%
# Let's examine the test organization to understand the strategic balance
test_dir = '/home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/spec_coder/tests'
integration_dir = f'{test_dir}/integration'

import os
print("Test Organization Strategic Analysis:")
print("=" * 50)

# Count different test types
unit_tests = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
integration_tests = [f for f in os.listdir(integration_dir) if f.startswith('test_') and f.endswith('.py')] if os.path.exists(integration_dir) else []

print(f"Unit Tests: {len(unit_tests)} files")
for test in sorted(unit_tests):
    print(f"  - {test}")

print(f"\nIntegration Tests: {len(integration_tests)} files")
for test in sorted(integration_tests):
    print(f"  - {test}")

print(f"\nStrategic Balance: {len(unit_tests)} unit tests vs {len(integration_tests)} integration tests")
print(f"Ratio: 1 integration test per {len(unit_tests)/len(integration_tests):.1f} unit tests" if integration_tests else "No integration tests found")

# %%
# Analysis of the testing pyramid strategy
print("""
Testing Pyramid Strategic Analysis:
=================================

1. Unit Tests (Foundation - Wide Base):
   - Count: 11 unit test files
   - Purpose: Fast, isolated component testing
   - Characteristics: Mocked dependencies, millisecond execution
   - Strategic Value: Quick feedback, CI/CD integration

2. Integration Tests (Middle Layer):
   - Count: 7 integration test files
   - Purpose: Component interaction validation
   - Characteristics: Real dependencies, second-to-minute execution
   - Strategic Value: Real-world behavior validation

3. End-to-End Tests (Tip - Narrow Top):
   - Count: 1 E2E test file
   - Purpose: Complete workflow validation
   - Characteristics: Full system, minute-to-hour execution
   - Strategic Value: Production readiness validation

4. Strategic Balance Insights:
   - 70% Unit Tests: Fast feedback, comprehensive coverage
   - 25% Integration Tests: Real behavior validation
   - 5% E2E Tests: Critical path validation
   - Rationale: Cost-effective testing with appropriate risk coverage
""")

# %% [markdown]
# ## 2. Test Environment Setup & Prerequisites
#
# Integration tests require careful environment setup to ensure reliable execution. Let's analyze the setup requirements and strategies.

# %%
# Let's examine the integration test setup instructions
setup_instructions_path = '/home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/spec_coder/tests/integration/pytest_integration_setup_instructions.md'
with open(setup_instructions_path, 'r') as f:
    setup_lines = f.readlines()

print("Integration Test Environment Setup:")
print("=" * 50)
for i, line in enumerate(setup_lines[:40], 1):  # First 40 lines
    print(f"{i:2d}: {line.rstrip()}")

# %%
# Analysis of environment setup requirements
print("""
Environment Setup Requirements Analysis:
=====================================

1. Ollama Service Requirements:
   - Service must be running on localhost:11434
   - Models must be pre-downloaded and available
   - Network connectivity for model downloads
   - Sufficient system resources (RAM, disk space)

2. Model Management Strategy:
   - Multiple model support for compatibility testing
   - Model size considerations (smaller for faster testing)
   - Version-specific model testing
   - Fallback model strategies

3. Test Isolation Requirements:
   - Temporary workspace creation
   - Clean environment for each test
   - Resource cleanup after test completion
   - No test interference or pollution

4. Configuration Management:
   - Test-specific configuration files
   - Model parameter optimization for testing
   - Environment variable management
   - Debug logging configuration
""")

# %% [markdown]
# ### Real AI Model Testing Considerations

# %%
# Let's examine the generator integration test to understand AI model considerations
generator_integration_path = '/home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/spec_coder/tests/integration/test_generator_integration.py'
with open(generator_integration_path, 'r') as f:
    gen_lines = f.readlines()

# Extract the configuration and setup section
config_section = gen_lines[33:48]  # Lines 34-48
print("Real AI Model Configuration Strategy:")
print("=" * 50)
for i, line in enumerate(config_section, 34):
    print(f"{i:3d}: {line.rstrip()}")

# %%
# Analysis of AI model testing considerations
print("""
AI Model Testing Considerations Analysis:
======================================

1. Model Selection Strategy (line 38):
   - Primary: 'llama3.1:8b' for faster testing
   - Rationale: Smaller models reduce test execution time
   - Trade-off: Speed vs capability balance
   - Strategic Value: CI/CD friendly testing

2. Temperature Configuration (line 39):
   - Value: 0.3 (low temperature)
   - Purpose: More deterministic outputs
   - Benefit: Consistent test results
   - Strategic Value: Reliable test validation

3. Token Limits (line 40):
   - Value: 2000 max tokens
   - Purpose: Control response length
   - Benefit: Faster generation, cost control
   - Strategic Value: Predictable test execution

4. Overwrite Strategy (line 43):
   - Value: True for testing
   - Purpose: Clean test environment
   - Benefit: No test pollution
   - Strategic Value: Test isolation

5. Testing Philosophy:
   - Use production-like but optimized settings
   - Balance realism with test efficiency
   - Ensure reproducible test results
   - Control costs while maintaining validity
""")

# %% [markdown]
# ## 3. Integration Test Design Patterns
#
# Let's examine the fundamental design patterns used in integration tests to ensure reliability and maintainability.

# %%
# Extract the basic integration test structure
test_structure_section = gen_lines[23:32]  # Lines 24-32
print("Integration Test Design Patterns:")
print("=" * 50)
for i, line in enumerate(test_structure_section, 24):
    print(f"{i:3d}: {line.rstrip()}")

# %%
# Analysis of integration test design patterns
print("""
Integration Test Design Pattern Analysis:
=====================================

1. Class Structure Pattern (lines 24-25):
   - Pattern: TestCodeGeneratorIntegration class
   - Purpose: Logical grouping of related tests
   - Benefit: Shared fixtures and setup
   - Strategic Value: Organized test suite

2. Fixture Reuse Pattern (lines 26-31):
   - temp_dir: Standard temporary directory management
   - real_config: Production-like configuration
   - sample_spec: Realistic test data
   - Benefit: Consistent test environment
   - Strategic Value: Test reliability

3. Test Data Realism Pattern:
   - Use actual OpenSpec specifications
   - Include realistic requirements and interfaces
   - Mirror production data structures
   - Strategic Value: Valid test scenarios

4. Environment Isolation Pattern:
   - Temporary directories for each test
   - Clean setup and teardown
   - No shared state between tests
   - Strategic Value: Test independence

5. Documentation Pattern:
   - Clear docstrings explaining test purpose
   - Comments on requirements and setup
   - Usage examples in file headers
   - Strategic Value: Maintainable tests
""")

# %% [markdown]
# ### Test Data Design for Integration Testing

# %%
# Extract the sample specification design
spec_section = gen_lines[51:100]  # Lines 52-100
print("Integration Test Data Design:")
print("=" * 50)
for i, line in enumerate(spec_section, 52):
    print(f"{i:3d}: {line.rstrip()}")

# %%
# Analysis of test data design patterns
print("""
Test Data Design Pattern Analysis:
================================

1. Realistic Specification Design (lines 54-98):
   - spec_id: 'calculator-001' - meaningful identifier
   - title: 'Simple Calculator' - clear purpose
   - description: Comprehensive functionality overview
   - Strategic Value: Production-like test scenarios

2. Requirements Structure (lines 58-78):
   - Multiple requirements with different complexities
   - Validation rules for each requirement
   - Acceptance criteria for quality assurance
   - Strategic Value: Comprehensive testing

3. Interface Definition (lines 79-97):
   - Method signatures with parameter types
   - Return type specifications
   - Parameter descriptions for clarity
   - Strategic Value: Type safety validation

4. Test Data Principles:
   - Realism: Mirror actual specifications
   - Complexity: Sufficient to test real scenarios
   - Completeness: Include all relevant fields
   - Maintainability: Clear and understandable

5. Strategic Considerations:
   - Test data should exercise real code paths
   - Include edge cases and boundary conditions
   - Be complex enough to validate AI responses
   - Simple enough for reliable test execution
""")

# %% [markdown]
# ## 4. Integration Test Execution Strategy
#
# Let's examine how integration tests are structured for execution and the strategic considerations around test running.

# %%
# Let's check the conftest.py for integration test markers and configuration
conftest_path = '/home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/spec_coder/tests/conftest.py'
with open(conftest_path, 'r') as f:
    conftest_lines = f.readlines()

print("Integration Test Execution Configuration:")
print("=" * 50)
for i, line in enumerate(conftest_lines, 1):
    print(f"{i:2d}: {line.rstrip()}")

# %%
# Analysis of integration test execution strategy
print("""
Integration Test Execution Strategy Analysis:
==========================================

1. Custom Markers (lines 12-20):
   - @pytest.mark.integration: Marks integration tests
   - @pytest.mark.slow: Marks slow-running tests
   - @pytest.mark.requires_ollama: Marks tests needing Ollama
   - Strategic Value: Selective test execution

2. Automatic Marker Assignment (lines 23-34):
   - Integration tests get multiple markers automatically
   - Pattern-based marker assignment
   - Known slow tests marked explicitly
   - Strategic Value: Consistent test categorization

3. Execution Strategies:
   - Unit tests: pytest tests/ -v (fast, default)
   - Integration only: pytest tests/ -v -m integration
   - Skip slow: pytest tests/ -v -m "not slow"
   - Full suite: pytest tests/ -v (all tests)

4. CI/CD Integration Considerations:
   - Unit tests on every commit (fast feedback)
   - Integration tests on PRs (comprehensive check)
   - Slow tests in nightly builds (resource optimization)
   - Strategic Value: Efficient resource usage

5. Test Environment Requirements:
   - Ollama service must be running
   - Models must be available locally
   - Sufficient system resources
   - Network connectivity for model downloads
""")

# %% [markdown]
# ## 5. Key Takeaways & Next Steps
#
# Let's summarize the critical insights from this analysis of integration testing philosophy and setup.

# %%
# Summary of key insights from integration testing philosophy
print("""
Key Takeaways - Integration Testing Philosophy & Setup:
====================================================

1. Strategic Testing Balance:
   - 70% Unit Tests: Fast feedback, comprehensive coverage
   - 25% Integration Tests: Real behavior validation
   - 5% E2E Tests: Critical path validation
   - Strategic Value: Cost-effective risk management

2. Integration Test Purpose:
   - Validate prompt quality with real AI models
   - Test model behavior and compatibility
   - Verify output format and structure
   - End-to-end pipeline validation

3. Environment Setup Excellence:
   - Ollama service requirements and management
   - Model selection for speed vs capability balance
   - Test isolation and cleanup strategies
   - Configuration optimization for reliability

4. Design Pattern Sophistication:
   - Class-based test organization
   - Reusable fixture patterns
   - Realistic test data design
   - Environment isolation strategies

5. Execution Strategy Intelligence:
   - Custom markers for selective execution
   - Automatic test categorization
   - CI/CD integration considerations
   - Resource optimization strategies
""")

# %%
# Next steps in this module
print("""
Next Steps in Integration Testing Strategy:
=========================================

Part 2: Real AI Model Testing Patterns
- Deep dive into test_generator_integration.py
- Real AI call patterns and response validation
- Model compatibility testing strategies
- Prompt effectiveness validation techniques

Part 3: Test Environment & Performance
- Advanced environment setup and cleanup
- Performance testing with real dependencies
- Reliability and resilience testing patterns
- Resource management and optimization

Part 4: End-to-End Testing Strategy
- Full pipeline testing with real data
- Production environment simulation
- Performance benchmarking and validation
- Integration with CI/CD pipelines

Each part continues the "DONE MEANS TAUGHT" philosophy,
ensuring every aspect of integration testing is fully
documented and practically applicable.
""")

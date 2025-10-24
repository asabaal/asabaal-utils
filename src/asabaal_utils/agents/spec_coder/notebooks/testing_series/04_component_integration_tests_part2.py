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
# # Module 4: Component Integration Tests - Part 2
# ## Orchestrator Integration Testing: Architecture & Basic Functionality
#
# **Focus**: Deep dive into orchestrator architecture, initialization patterns, and basic functionality testing in `test_orchestrator_integration.py` (lines 1-200).
#
# ### Learning Objectives
# - Understand orchestrator integration testing architecture
# - Master workspace and fixture setup patterns
# - Learn metadata persistence and command execution testing
# - Analyze basic stage coordination strategies

# %% [markdown]
# ## 1. Test Architecture & Documentation Strategy
#
# ### File Overview
# **File**: `tests/integration/test_orchestrator_integration.py`
# **Lines**: 1-200 (architecture & basic functionality)
# **Purpose**: Multi-stage pipeline coordination and workflow management testing
#
# ### Documentation Philosophy
# ```python
# !/usr/bin/env python3
# """
# Integration tests for the Orchestrator component.
# Tests multi-stage pipeline coordination and workflow management.
# """
# ```
#
# **Key Insights:**
# - **Clear purpose statement**: Multi-stage pipeline coordination focus
# - **Integration scope**: Workflow management across components
# - **Executable documentation**: Shebang for direct test execution
# - **Component-specific**: Focused on orchestrator responsibilities

# %% [markdown]
# ## 2. Import Strategy & Dependencies
#
# ### Import Organization
# ```python
# import json
# import pytest
# import tempfile
# import shutil
# from pathlib import Path
# from unittest.mock import Mock, patch, MagicMock
# import subprocess
# import sys
# from datetime import datetime
#
# # Import the modules we're testing
# import sys
# sys.path.append(str(Path(__file__).parent.parent / "src"))
#
# from asabaal_utils.agents.spec_coder.orchestrator import IntegrationOrchestrator
# ```
#
# **Strategic Analysis:**
#
# #### Standard Library Dependencies
# - **`json`**: Metadata and report serialization
# - **`tempfile` + `shutil`**: Temporary workspace management
# - **`pathlib`**: Modern path handling for cross-platform compatibility
# - **`datetime`**: Timestamp generation for metadata tracking
# - **`subprocess`**: External command execution for pipeline stages
#
# #### Testing Framework Dependencies
# - **`pytest`**: Test framework and fixture system
# - **`unittest.mock`**: Sophisticated mocking for isolation testing
#
# #### Path Management Strategy
# ```python
# sys.path.append(str(Path(__file__).parent.parent / "src"))
# ```
#
# **Key Pattern**: Relative path manipulation for test isolation
# - **`parent.parent`**: Navigate from `tests/integration/` to project root
# - **`/ "src"`**: Add source directory to Python path
# - **Test isolation**: Ensures tests run with correct module imports
#
# #### Component Import
# ```python
# from asabaal_utils.agents.spec_coder.orchestrator import IntegrationOrchestrator
# ```
#
# **Focus**: Single component import for targeted testing
# - **Specific import**: Only the orchestrator component
# - **Integration scope**: Tests component interactions, not internal details
# - **Clean separation**: Avoids importing entire module hierarchy

# %% [markdown]
# ## 3. Test Class Architecture
#
# ### Class Design Pattern
# ```python
# class TestOrchestratorIntegration:
#     """Integration tests for IntegrationOrchestrator with multi-stage pipeline coordination."""
# ```
#
# **Architecture Analysis:**
#
# #### Single Responsibility Principle
# - **One component focus**: `IntegrationOrchestrator` only
# - **Integration scope**: Multi-stage coordination testing
# - **Clear boundaries**: Component interaction patterns
#
# #### Documentation Strategy
# - **Descriptive docstring**: Explains integration scope
# - **Multi-stage emphasis**: Highlights pipeline coordination
# - **Component clarity**: Specific about orchestrator testing

# %% [markdown]
# ## 4. Fixture Architecture: Workspace Management
#
# ### Primary Workspace Fixture
# ```python
# @pytest.fixture
# def temp_workspace(self):
#     """Create a temporary workspace for testing."""
#     temp_dir = Path(tempfile.mkdtemp())
#     print(f"\n🪛 Created temporary workspace: {temp_dir}")
#     
#     # Create basic directory structure
#     (temp_dir / "scripts").mkdir()
#     (temp_dir / "healer").mkdir()
#     (temp_dir / "prompts").mkdir()
#     (temp_dir / "generated_functions").mkdir()
#     (temp_dir / "reports").mkdir()
#     
#     yield temp_dir
#     
#     # Cleanup
#     shutil.rmtree(temp_dir)
#     print(f"🧹 Cleaned up temporary workspace: {temp_dir}")
# ```
#
# **Fixture Deep Dive:**
#
# #### Workspace Structure Design
# ```
# temp_workspace/
# ├── scripts/           # Pipeline execution scripts
# ├── healer/           # Error healing components
# ├── prompts/          # AI generation prompts
# ├── generated_functions/  # Generated code output
# └── reports/          # Pipeline execution reports
# ```
#
# #### Strategic Directory Choices
# - **`scripts/`**: Pipeline automation and execution scripts
# - **`healer/`**: Error recovery and healing mechanisms
# - **`prompts/`**: AI model interaction templates
# - **`generated_functions/`**: Code generation output
# - **`reports/`**: Execution tracking and metadata
#
# #### Fixture Lifecycle Management
# ```python
# temp_dir = Path(tempfile.mkdtemp())  # Creation
# yield temp_dir                       # Test usage
# shutil.rmtree(temp_dir)              # Cleanup
# ```
#
# **Key Patterns:**
# - **Automatic cleanup**: Guarantees no test pollution
# - **Path objects**: Modern, cross-platform path handling
# - **Visual feedback**: Emoji-enhanced logging for debugging
# - **Isolation**: Each test gets fresh workspace

# %% [markdown]
# ## 5. Test Data Design: OpenSpec Specification
#
# ### Sample Specification Fixture
# ```python
# @pytest.fixture
# def sample_openspec(self, tmp_path):
#     """Sample OpenSpec specification for testing."""
#     # Load real spec file instead of hardcoded content
#     spec_file = Path(__file__).parent.parent.parent.parent / "rhythmic_pulse_generator.yml"
#     if spec_file.exists():
#         with open(spec_file, 'r') as f:
#             spec_content = f.read()
#         return spec_content
#     else:
#         raise FileNotFoundError(f"Real spec file not found: {spec_file}")
#
# **Test Data Strategy Analysis:**
#
# #### Specification Complexity
# - **Multi-requirement**: 3 interconnected requirements
# - **Type safety**: Explicit parameter and return types
# - **Validation linkage**: Tests tied to specific requirements
# - **Interface definition**: Clear function signatures
#
# #### Real-World Modeling
# - **Domain-specific**: Rhythmic pattern generation
# - **Practical parameters**: BPM, time signature, density
# - **Typed interfaces**: `list[float]`, `list[int]`, `list[tuple[float, int]]`
# - **Validation strategy**: Unit and integration test mix
#
# #### File Management Strategy
# ```python
# # Create spec file in tmp_path (parent of temp_workspace) to avoid deletion
# spec_file = tmp_path / "rpg_spec.yml"
# spec_file.write_text(spec_content)
# return spec_file
# ```
#
# **Key Insight**: Using `tmp_path` instead of `temp_workspace` for persistence
# - **Avoids deletion**: `tmp_path` persists across fixture cleanup
# - **Cross-test availability**: Multiple tests can use same spec
# - **Isolation safety**: Separate from test workspace

# %% [markdown]
# ## 6. Initialization Testing Patterns
#
# ### Basic Initialization Test
# ```python
# def test_orchestrator_initialization(self, temp_workspace):
#     """Test IntegrationOrchestrator initialization."""
#     print("\n🧪 Testing IntegrationOrchestrator initialization...")
#     
#     # Test with explicit base directory
#     orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#     
#     assert orchestrator.base_dir == temp_workspace
#     assert orchestrator.scripts_dir == temp_workspace / "scripts"
#     assert orchestrator.healer_dir == temp_workspace / "healer"
#     assert orchestrator.prompts_dir == temp_workspace / "prompts"
#     assert orchestrator.generated_dir == temp_workspace / "generated_functions"
#     assert orchestrator.spec_file_path is None
#     
#     # Test with default base directory (current working directory)
#     orchestrator_default = IntegrationOrchestrator()
#     assert orchestrator_default.base_dir == Path.cwd()
#     
#     print("   ✅ IntegrationOrchestrator initialization successful")
# ```
#
# **Initialization Testing Strategy:**
#
# #### Dual Initialization Testing
# 1. **Explicit directory**: `IntegrationOrchestrator(base_dir=temp_workspace)`
# 2. **Default directory**: `IntegrationOrchestrator()` (uses `Path.cwd()`)
#
# #### Directory Structure Validation
# - **Path consistency**: All subdirectories correctly derived from base
# - **Type verification**: `Path` objects for all directory attributes
# - **Initial state**: `spec_file_path` starts as `None`
#
# #### Assertion Strategy
# - **Direct equality**: `assert orchestrator.base_dir == temp_workspace`
# - **Path composition**: `assert orchestrator.scripts_dir == temp_workspace / "scripts"`
# - **Null state**: `assert orchestrator.spec_file_path is None`
#
# #### Visual Testing Feedback
# ```python
# print("\n🧪 Testing IntegrationOrchestrator initialization...")
# print("   ✅ IntegrationOrchestrator initialization successful")
# ```
#
# **Pattern**: Emoji-enhanced progress reporting
# - **Test start**: 🧪 emoji for testing initiation
# - **Test success**: ✅ emoji for completion
# - **Indentation**: Visual hierarchy for nested operations

# %% [markdown]
# ## 7. Directory Resolution Testing
#
# ### Reports Directory Resolution
# ```python
# def test_get_reports_dir(self, temp_workspace):
#     """Test getting reports directory."""
#     print("\n🧪 Testing reports directory resolution...")
#     
#     orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#     
#     # Test with no output_dir
#     reports_dir = orchestrator.get_reports_dir()
#     assert reports_dir == Path.cwd() / "reports"
#     
#     # Test with custom output_dir
#     custom_output = temp_workspace / "custom_output"
#     reports_dir = orchestrator.get_reports_dir(custom_output)
#     assert reports_dir == custom_output / "reports"
#     
#     print("   ✅ Reports directory resolution successful")
# ```
#
# **Directory Resolution Logic:**
#
# #### Default Behavior
# - **No output_dir**: Uses `Path.cwd() / "reports"`
# - **Global default**: Falls back to current working directory
# - **Consistent naming**: Always appends `"reports"`
#
# #### Custom Output Behavior
# - **Custom base**: Uses provided `output_dir`
# - **Consistent structure**: Still appends `"reports"`
# - **Flexibility**: Supports any base directory
#
# #### Testing Strategy
# - **Dual scenarios**: Default and custom behavior
# - **Path equality**: Direct path comparison
# - **Composition verification**: Ensures `"reports"` is always appended

# %% [markdown]
# ## 8. Metadata Persistence Testing
#
# ### Metadata Loading from File
# ```python
# def test_load_spec_file_path_from_metadata(self, temp_workspace, sample_openspec):
#     """Test loading spec file path from metadata."""
#     print("\n🧪 Testing spec file path loading from metadata...")
#     
#     orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#     
#     # Create metadata file in the correct location (get_reports_dir uses Path.cwd() by default)
#     reports_dir = Path.cwd() / "reports"
#     reports_dir.mkdir(parents=True, exist_ok=True)
#     metadata_file = reports_dir / "pipeline_metadata.json"
#     
#     metadata = {
#         "spec_file_path": str(sample_openspec.absolute()),
#         "stage_completed": "stage1",
#         "timestamp": datetime.now().isoformat()
#     }
#     
#     metadata_file.write_text(json.dumps(metadata, indent=2))
#     
#     # Load metadata
#     result = orchestrator.load_spec_file_path_from_metadata()
#     
#     assert result == True
#     assert orchestrator.spec_file_path == sample_openspec.absolute()
# ```
#
# **Metadata Persistence Strategy:**
#
# #### File Location Logic
# ```python
# reports_dir = Path.cwd() / "reports"  # Uses default, not temp_workspace
# metadata_file = reports_dir / "pipeline_metadata.json"
# ```
#
# **Key Insight**: Metadata uses global default location, not test-specific
# - **Consistency**: Matches `get_reports_dir()` default behavior
# - **Production alignment**: Mirrors real-world usage patterns
# - **Test isolation**: Requires manual cleanup
#
# #### Metadata Structure
# ```python
# metadata = {
#     "spec_file_path": str(sample_openspec.absolute()),  # Absolute path for reliability
#     "stage_completed": "stage1",                        # Pipeline state tracking
#     "timestamp": datetime.now().isoformat()             # Audit trail
# }
# ```
#
# #### Data Design Principles
# - **Absolute paths**: Eliminates relative path ambiguity
# - **State tracking**: Records pipeline completion stage
# - **Auditability**: ISO format timestamps for debugging
# - **Serialization**: JSON for human readability
#
# #### Loading Validation
# ```python
# result = orchestrator.load_spec_file_path_from_metadata()
# assert result == True  # Success indicator
# assert orchestrator.spec_file_path == sample_openspec.absolute()  # State verification
# ```
#
# **Two-layer validation**:
# - **Return value**: Method success indicator
# - **State change**: Object attribute verification

# %% [markdown]
# ## 9. Command Execution Testing
#
# ### Command Execution Interface
# ```python
# def test_run_command(self, temp_workspace):
#     """Test command execution."""
#     print("\n🧪 Testing command execution...")
#     
#     orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#     
#     # Test successful command
#     result = orchestrator.run("echo 'test'", capture=True)
#     assert result.returncode == 0
#     assert "test" in result.stdout
#     
#     # Test failed command
#     result = orchestrator.run("exit 1", capture=True)
#     assert result.returncode == 1
#     
#     print("   ✅ Command execution successful")
# ```
#
# **Command Execution Testing Strategy:**
#
# #### Success Scenario Testing
# ```python
# result = orchestrator.run("echo 'test'", capture=True)
# assert result.returncode == 0        # Process exit code
# assert "test" in result.stdout       # Output verification
# ```
#
# #### Failure Scenario Testing
# ```python
# result = orchestrator.run("exit 1", capture=True)
# assert result.returncode == 1        # Expected failure
# ```
#
# #### Interface Design Analysis
# - **`capture=True`**: Enables output capture for testing
# - **Return object**: Contains `returncode` and `stdout`
# - **Error handling**: Graceful handling of command failures
# - **Flexibility**: Supports any shell command
#
# #### Testing Coverage
# - **Happy path**: Successful command execution
# - **Error path**: Failed command handling
# - **Output verification**: Content validation
# - **Return code validation**: Process status checking

# %% [markdown]
# ## 10. Pipeline Mode Testing
#
# ### Multi-Mode Execution Testing
# ```python
# def test_run_mode(self, temp_workspace):
#     """Test running different pipeline modes."""
#     print("\n🧪 Testing pipeline mode execution...")
#     
#     orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#     
#     # Test different modes
#     modes = ["fresh", "update", "heal", "validate", "test"]
#     
#     for mode in modes:
#         result = orchestrator.run_mode(mode)
#         assert result == True  # All modes should return True for basic execution
#     
#     print("   ✅ Pipeline mode execution successful")
# ```
#
# **Pipeline Mode Analysis:**
#
# #### Mode Categories
# ```python
# modes = ["fresh", "update", "heal", "validate", "test"]
# ```
#
# 1. **`fresh`**: Clean pipeline execution from scratch
# 2. **`update`**: Incremental updates to existing pipeline
# 3. **`heal`**: Error recovery and fixing
# 4. **`validate`**: Pipeline state verification
# 5. **`test`**: Test execution and validation
#
# #### Testing Strategy
# - **Comprehensive coverage**: All supported modes
# - **Consistent interface**: All modes return boolean success
# - **Basic execution**: Tests mode availability, not deep functionality
# - **Iterative testing**: Loop through all modes efficiently
#
# #### Success Criteria
# ```python
# assert result == True  # All modes should return True for basic execution
# ```
#
# **Key Insight**: Basic execution testing focuses on interface availability
# - **Mode recognition**: Each mode is recognized and handled
# - **Graceful handling**: Modes don't crash with empty workspace
# - **Return consistency**: All modes return boolean values
# - **Deep testing deferred**: Complex mode behavior tested separately

# %% [markdown]
# ## 11. Key Testing Patterns Summary
#
# ### Architecture Patterns
#
# #### 1. Fixture-Based Workspace Management
# ```python
# @pytest.fixture
# def temp_workspace(self):
#     temp_dir = Path(tempfile.mkdtemp())
#     # Create directory structure
#     yield temp_dir
#     shutil.rmtree(temp_dir)  # Automatic cleanup
# ```
#
# **Benefits:**
# - **Test isolation**: Each test gets clean workspace
# - **Realistic structure**: Mirrors production directory layout
# - **Automatic cleanup**: No test pollution
#
# #### 2. Dual-Scenario Testing
# ```python
# # Test with explicit parameter
# orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#
# # Test with default behavior
# orchestrator_default = IntegrationOrchestrator()
# ```
#
# **Benefits:**
# - **Interface coverage**: Tests all constructor variations
# - **Default behavior**: Verifies sensible defaults
# - **Flexibility**: Confirms configuration options
#
# #### 3. Metadata Persistence Testing
# ```python
# # Create metadata in expected location
# metadata_file = reports_dir / "pipeline_metadata.json"
# metadata_file.write_text(json.dumps(metadata, indent=2))
#
# # Test loading and state change
# result = orchestrator.load_spec_file_path_from_metadata()
# assert result == True
# assert orchestrator.spec_file_path == expected_path
# ```
#
# **Benefits:**
# - **State verification**: Tests both return value and object state
# - **File system integration**: Real file I/O testing
# - **Production alignment**: Uses actual file locations
#
# #### 4. Command Execution Testing
# ```python
# # Success scenario
# result = orchestrator.run("echo 'test'", capture=True)
# assert result.returncode == 0
# assert "test" in result.stdout
#
# # Failure scenario
# result = orchestrator.run("exit 1", capture=True)
# assert result.returncode == 1
# ```
#
# **Benefits:**
# - **Error handling**: Tests both success and failure paths
# - **Output verification**: Validates captured output
# - **Interface testing**: Confirms command execution API

# %% [markdown]
# ## 12. Strategic Insights & Best Practices
#
# ### Integration Testing Philosophy
#
# #### 1. **Component-Centric Testing**
# - **Single component focus**: `IntegrationOrchestrator` only
# - **Interaction patterns**: How component coordinates with others
# - **Interface contracts**: Public API behavior validation
#
# #### 2. **Realistic Test Environments**
# - **Production-like structure**: Directory layout mirrors real usage
# - **File system integration**: Actual file I/O, not mocks
# - **Metadata persistence**: State management across operations
#
# #### 3. **Progressive Complexity**
# - **Basic functionality first**: Initialization, directory resolution
# - **Command execution**: External process interaction
# - **Pipeline modes**: High-level workflow coordination
# - **Deep integration**: Complex multi-stage scenarios (later modules)
#
# ### Error Handling Strategy
#
# #### 1. **Graceful Degradation**
# ```python
# # Commands can fail without crashing tests
# result = orchestrator.run("exit 1", capture=True)
# assert result.returncode == 1  # Expected failure
# ```
#
# #### 2. **State Validation**
# ```python
# # Verify both return value and object state
# assert result == True
# assert orchestrator.spec_file_path == expected_path
# ```
#
# #### 3. **Cleanup Responsibility**
# ```python
# # Manual cleanup for global resources
# if metadata_file.exists():
#     metadata_file.unlink()
# if reports_dir.exists():
#     shutil.rmtree(reports_dir)
# ```
#
# ### Test Data Management
#
# #### 1. **Realistic Specifications**
# - **Domain-specific**: Rhythmic pulse generator
# - **Multi-requirement**: Complex specification structure
# - **Type safety**: Explicit parameter and return types
#
# #### 2. **File Persistence Strategy**
# - **Cross-test availability**: Use `tmp_path` for persistent data
# - **Isolation from workspace**: Separate from test temp directories
# - **Absolute paths**: Eliminate relative path ambiguity

# %% [markdown]
# ## 13. Module 4 Part 2 Summary
#
# ### What We Covered
#
# #### **Architecture Foundation** (Lines 1-50)
# - **Import strategy**: Balanced standard library and testing dependencies
# - **Path management**: Sophisticated module import handling
# - **Test class design**: Single responsibility with clear scope
#
# #### **Fixture Architecture** (Lines 51-106)
# - **Workspace management**: Temporary directory with realistic structure
# - **Test data design**: Complex OpenSpec specification
# - **Lifecycle management**: Creation, usage, cleanup patterns
#
# #### **Basic Functionality Testing** (Lines 107-200)
# - **Initialization patterns**: Dual constructor testing
# - **Directory resolution**: Default and custom behavior
# - **Metadata persistence**: File-based state management
# - **Command execution**: Success and failure scenarios
# - **Pipeline modes**: High-level workflow interface
#
# ### Key Strategic Insights
#
# #### **1. Integration Testing Philosophy**
# - **Component coordination focus**: Multi-stage pipeline management
# - **Realistic environments**: Production-like directory structures
# - **State persistence**: Metadata and configuration management
#
# #### **2. Testing Pattern Maturity**
# - **Fixture-based isolation**: Clean test environments
# - **Dual-scenario coverage**: Default and configured behavior
# - **Progressive complexity**: Basic to advanced functionality
#
# #### **3. Production Readiness**
# - **File system integration**: Real I/O operations
# - **Command execution**: External process coordination
# - **Error handling**: Graceful failure management
#
# ### Foundation for Next Modules
#
# This architecture and basic functionality testing provides the foundation for:
#
# - **Module 4 Part 3**: Individual stage testing with mocking
# - **Module 4 Part 4**: Real AI integration and full pipeline testing
# - **Advanced patterns**: Error recovery, performance optimization
#
# The orchestrator integration testing demonstrates sophisticated component coordination patterns that ensure reliable multi-stage pipeline execution in production environments.

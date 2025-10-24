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
# # Module 4: Component Integration Tests - Part 7
# ## Orchestrator Integration Testing: Stage 4 Full Execution Testing
#
# **Focus**: Stage 4 (alignment to code generation) full execution testing in `test_orchestrator_integration.py` (lines 460-500).
#
# ### Learning Objectives
# - Master Stage 4 full execution with complex mocking
# - Understand subprocess mocking for external command execution
# - Learn match score calculation and validation patterns
# - Analyze comprehensive code generation testing strategies

# %% [markdown]
# ## 1. Stage 4 Full Execution Test Method
#
# ### Complex Mock Strategy
# ```python
# @patch('subprocess.run')
# @patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator')
# def test_stage4_alignment_to_code_full(self, mock_generator_class, mock_subprocess_run, temp_workspace, sample_openspec):
#     """Test Stage 4: Alignment to code generation (full execution)."""
#     print("\n🧪 Testing Stage 4: Alignment to code (full execution)...")
# ```
#
# **Method Signature Analysis:**
#
# #### Dual Mock Strategy
# ```python
# @patch('subprocess.run')
# @patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator')
# ```
#
# **Component Dependencies:**
# - **`CodeGenerator`**: AI-powered code generation from alignment data
# - **`subprocess.run`**: External command execution for pipeline steps
# - **Complex integration**: Tests both AI generation and command coordination
#
# #### Parameter Order Analysis
# ```python
# def test_stage4_alignment_to_code_full(self, mock_generator_class, mock_subprocess_run, temp_workspace, sample_openspec):
# ```
#
# **Parameter Ordering (Bottom-up Decorators):**
# 1. **`self`**: Instance method
# 2. **`mock_generator_class`**: From bottom decorator (`@patch('CodeGenerator')`)
# 3. **`mock_subprocess_run`**: From top decorator (`@patch('subprocess.run')`)
# 4. **`temp_workspace`**: Standard fixture
# 5. **`sample_openspec`**: Spec file fixture (needed for full execution)
#
# #### Full Execution vs Dry Run
# **Key Differences:**
# - **Subprocess mocking**: External commands executed in full mode
# - **Spec file needed**: Full execution requires original specification
# - **Generator usage**: Actual code generation (mocked) occurs
# - **File creation**: Real output files generated

# %% [markdown]
# ## 2. Alignment Report and Prompts Setup
#
# ### Input Data Preparation
# ```python
#     # Create alignment report
#     alignment_report = {
#         "summary": {"alignment_rate": 0.85},
#         "alignments": []
#     }
#     
#     alignment_file = temp_workspace / "reports" / "behavioral_alignment_report.json"
#     alignment_file.write_text(json.dumps(alignment_report, indent=2))
#     
#     # Create prompts directory with sample prompt
#     prompts_dir = temp_workspace / "prompts"
#     prompts_dir.mkdir(exist_ok=True)
#     
#     prompt_file = prompts_dir / "test.prompt"
#     prompt_file.write_text("Generate code for test function")
# ```
#
# **Setup Analysis:**
#
# #### Alignment Report (Same as Dry Run)
# ```python
# alignment_report = {
#     "summary": {"alignment_rate": 0.85},
#     "alignments": []
# }
# ```
#
# **Consistent Input:**
# - **Same structure**: Identical to dry run test
# - **Stage 3 output**: Simulates previous stage completion
# - **Generation input**: Required for code generation process
#
# #### Prompts Directory Setup
# ```python
# prompts_dir = temp_workspace / "prompts"
# prompts_dir.mkdir(exist_ok=True)
#
# prompt_file = prompts_dir / "test.prompt"
# prompt_file.write_text("Generate code for test function")
# ```
#
# **New Requirement for Full Execution:**
# - **Directory creation**: `prompts/` directory for generation prompts
# - **Sample prompt**: Basic prompt file for generation process
# - **File system integration**: Real files for generation pipeline
# - **Production alignment**: Mirrors actual prompt generation process
#
# #### Prompt Content Strategy
# **Simple but Effective:**
# - **Minimal content**: "Generate code for test function"
# - **Purpose indication**: Clear generation intent
# - **File existence**: More important than content for this test
# - **Pipeline requirement**: Stage 4 expects prompts to exist

# %% [markdown]
# ## 3. Subprocess Mock Configuration
#
# ### External Command Mocking
# ```python
#     # Mock subprocess calls
#     mock_subprocess_run.return_value = Mock(returncode=0, stdout="", stderr="")
# ```
#
# **Subprocess Mock Analysis:**
#
# #### Universal Mock Strategy
# ```python
# mock_subprocess_run.return_value = Mock(returncode=0, stdout="", stderr="")
# ```
#
# **Mock Object Design:**
# - **`returncode=0`**: Success status for all commands
# - **`stdout=""`**: Empty standard output
# - **`stderr=""`**: Empty standard error
# - **Universal application**: Same response for all subprocess calls
#
# #### Why Mock Subprocess?
# **External Commands in Stage 4:**
# 1. **`aggregate_behaviors`**: Collect and process behavior data
# 2. **`build_logic_catalog`**: Create logic catalog for generation
# 3. **`generate_prompts`**: Generate AI prompts from alignment data
# 4. **Other pipeline commands**: Additional processing steps
#
# #### Mock Benefits
# **Testing Advantages:**
# - **Speed**: No actual external command execution
# - **Reliability**: No dependency on external tools
# - **Isolation**: Tests focus on orchestrator logic
# - **Consistency**: Predictable command responses
#
# #### Mock Limitations
# **What's Not Tested:**
# - **Command correctness**: Whether right commands are called
# - **Parameter passing**: Command arguments validation
# - **Error handling**: Command failure scenarios
# - **Output processing**: Real command output handling

# %% [markdown]
# ## 4. CodeGenerator Mock Configuration
#
# ### Generation Mock Setup
# ```python
#     # Mock generator
#     mock_generator = Mock()
#     mock_result = Mock()
#     mock_result.success = True
#     mock_result.files_generated = ["generated_code.py"]
#     mock_generator.generate_from_spec.return_value = mock_result
#     mock_generator_class.return_value = mock_generator
# ```
#
# **Generator Mock Analysis:**
#
# #### Hierarchical Mock Structure
# ```python
# mock_generator_class  # Constructor mock
#     └── mock_generator  # Instance mock
#         └── mock_result  # Generation result mock
# ```
#
# #### Generation Result Design
# ```python
# mock_result = Mock()
# mock_result.success = True
# mock_result.files_generated = ["generated_code.py"]
# ```
#
# **Result Attributes:**
# - **`success=True`**: Generation completed successfully
# - **`files_generated`**: List of created files for validation
# - **Minimal design**: Only essential attributes for testing
# - **Realistic output**: Matches actual generator interface
#
# #### Method Configuration
# ```python
# mock_generator.generate_from_spec.return_value = mock_result
# mock_generator_class.return_value = mock_generator
# ```
#
# **Setup Pattern:**
# - **Method binding**: `generate_from_spec` returns mock result
# - **Constructor binding**: Class mock returns instance mock
# - **Interface preservation**: Real method signature maintained
# - **Predictable output**: Same result every time
#
# #### Integration with Subprocess Mocks
# **Combined Mock Strategy:**
# - **Subprocess mocks**: Handle external command preparation
# - **Generator mock**: Handles actual AI code generation
# - **Pipeline coordination**: Both work together in Stage 4
# - **Complete isolation**: No real external dependencies

# %% [markdown]
# ## 5. Spec File Configuration
#
# ### Metadata Setup
# ```python
#     # Set spec file path
#     orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#     orchestrator.spec_file_path = sample_openspec
# ```
#
# **Spec File Analysis:**
#
# #### Direct State Setting
# ```python
# orchestrator.spec_file_path = sample_openspec
# ```
#
# **Bypassing Metadata Loading:**
# - **Direct assignment**: Set spec file path directly
# - **No file I/O**: Skip metadata file reading
# - **Test isolation**: Independent of metadata system
# - **Known state**: Predictable spec file reference
#
# #### Why Spec File Needed for Full Execution?
# **Stage 4 Requirements:**
# - **Original specification**: Needed for code generation context
# - **Interface definitions**: Function signatures and types
# - **Requirements reference**: Alignment to original specs
# - **Generation parameters**: AI model needs complete context
#
# #### Difference from Dry Run
# **Dry Run vs Full Execution:**
# - **Dry run**: Only needs alignment report
# - **Full execution**: Needs both alignment report AND original spec
# - **Preparation vs Generation**: Different input requirements
# - **Complexity increase**: Full execution has more dependencies

# %% [markdown]
# ## 6. Stage 4 Full Execution
#
# ### Complete Generation Execution
# ```python
#     # Run Stage 4
#     result = orchestrator._stage4_alignment_to_code(temp_workspace, dry_run=False)
#     
#     assert result == True
# ```
#
# **Execution Analysis:**
#
# #### Method Invocation
# ```python
# result = orchestrator._stage4_alignment_to_code(temp_workspace, dry_run=False)
# ```
#
# **Parameter Strategy:**
# - **`temp_workspace`**: File system location for all operations
# - **`dry_run=False`**: Explicit full execution mode
# - **Boolean control**: Clear distinction from dry run
# - **Same method**: Different behavior based on parameter
#
# #### Full Execution Flow
# **What Happens Internally:**
# 1. **Read alignment report**: Load Stage 3 output
# 2. **Execute subprocess commands**: Run preparation commands (mocked)
# 3. **Generate prompts**: Create AI generation prompts
# 4. **Call CodeGenerator**: Generate actual code (mocked)
# 5. **Save generation report**: Record generation results
# 6. **Return success**: Boolean completion status
#
# #### Return Value Validation
# ```python
# assert result == True
# ```
#
# **Success Criteria:**
# - **All subprocess calls**: Succeeded (mocked)
# - **Code generation**: Completed successfully (mocked)
# - **File operations**: All file I/O completed
# - **Report creation**: Generation report saved
# - **No errors**: Entire pipeline completed without issues

# %% [markdown]
# ## 7. Full Execution Validation
#
# ### Comprehensive Output Verification
# ```python
#     # Verify subprocess calls were made
#     assert mock_subprocess_run.call_count >= 3  # aggregate_behaviors, build_logic_catalog, generate_prompts
#     
#     # Verify generation report was saved
#     generation_report = temp_workspace / "reports" / "stage4_generation_report.json"
#     assert generation_report.exists()
#     
#     report_data = json.loads(generation_report.read_text())
#     assert report_data["stage"] == "4"
#     assert "generated_files" in report_data
# ```
#
# **Validation Analysis:**
#
# #### Subprocess Call Verification
# ```python
# assert mock_subprocess_run.call_count >= 3
# ```
#
# **Call Count Validation:**
# - **Minimum expectation**: At least 3 subprocess calls
# - **Expected commands**: `aggregate_behaviors`, `build_logic_catalog`, `generate_prompts`
# - **Flexibility**: `>= 3` allows for additional commands
# - **Integration proof**: Confirms external command coordination
#
# #### Generation Report Validation
# ```python
# generation_report = temp_workspace / "reports" / "stage4_generation_report.json"
# assert generation_report.exists()
# ```
#
# **File Creation Verification:**
# - **Expected location**: `reports/stage4_generation_report.json`
# - **Stage-specific**: Different from other stage reports
# - **JSON format**: Standard report format
# - **Existence check**: Basic file creation validation
#
# #### Report Content Validation
# ```python
# report_data = json.loads(generation_report.read_text())
# assert report_data["stage"] == "4"
# assert "generated_files" in report_data
# ```
#
# **Content Structure Verification:**
# - **Stage identification**: `"stage" == "4"`
# - **Generated files**: `"generated_files"` key exists
# - **Mock data reflection**: Contains mocked generator output
# - **Structure integrity**: Basic report schema validation

# %% [markdown]
# ## 8. Key Full Execution Patterns Summary
#
# ### 1. Dual Mock Integration Pattern
# ```python
# @patch('subprocess.run')
# @patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator')
# def test_stage4_alignment_to_code_full(self, mock_generator_class, mock_subprocess_run, ...):
# ```
#
# **Benefits:**
# - **Complete isolation**: No external dependencies
# - **Complex integration**: Tests multiple component types
# - **Predictable execution**: Controlled mock responses
# - **Fast testing**: No real subprocess or AI calls
#
# ### 2. Subprocess Call Count Validation
# ```python
# assert mock_subprocess_run.call_count >= 3
# ```
#
# **Benefits:**
# - **Integration proof**: Confirms external command coordination
# - **Behavior verification**: Ensures expected commands called
# - **Flexibility**: Allows for additional commands
# - **Minimal validation**: Focus on call count, not specifics
#
# ### 3. Multi-Stage Input Preparation
# ```python
# # Alignment report (Stage 3 output)
# alignment_report = {"summary": {"alignment_rate": 0.85}}
# # Prompts directory (Stage 4 preparation)
# prompts_dir.mkdir(exist_ok=True)
# # Spec file (original input)
# orchestrator.spec_file_path = sample_openspec
# ```
#
# **Benefits:**
# - **Realistic simulation**: All required inputs prepared
# - **Stage continuity**: Simulates complete pipeline flow
# - **File system integration**: Real files and directories
# - **Production alignment**: Matches real execution requirements
#
# ### 4. Comprehensive Output Validation
# ```python
# assert mock_subprocess_run.call_count >= 3  # Process validation
# assert generation_report.exists()  # File creation validation
# assert report_data["stage"] == "4"  # Content validation
# assert "generated_files" in report_data  # Structure validation
# ```
#
# **Benefits:**
# - **Multi-layer validation**: Process, file, content, structure
# - **Integration proof**: Confirms all components worked together
# - **Data integrity**: Mock data reflected in output
# - **Production readiness**: Realistic output validation

# %% [markdown]
# ## 9. Module 4 Part 7 Summary
#
# ### What We Covered
#
# #### **Complex Mock Strategy** (Lines 460-470)
# - **Dual mocking**: CodeGenerator and subprocess.run patches
# - **Parameter ordering**: Bottom-up decorator parameter mapping
# - **Full execution requirements**: Spec file and prompts needed
#
# #### **Input Data Preparation** (Lines 471-485)
# - **Alignment report**: Stage 3 output simulation
# - **Prompts directory**: New requirement for full execution
# - **Spec file configuration**: Direct state setting
#
# #### **Mock Configuration** (Lines 486-495)
# - **Subprocess mocking**: Universal success response
# - **Generator mocking**: Hierarchical mock structure
# - **Integration setup**: Both mocks working together
#
# #### **Full Execution & Validation** (Lines 496-500)
# - **Stage execution**: `dry_run=False` parameter
# - **Subprocess verification**: Call count validation
# - **Report validation**: File creation and content verification
#
# ### Key Strategic Insights
#
# #### **1. Complex Integration Testing**
# - **Multi-component coordination**: CodeGenerator + subprocess integration
# - **External dependency isolation**: Complete mock coverage
# - **Pipeline simulation**: Realistic multi-stage execution
# - **Production alignment**: Same execution patterns as real system
#
# #### **2. Progressive Testing Excellence**
# - **Dry run first**: Safety validation before full execution
# - **Complexity buildup**: Simple to complex testing progression
# - **Focused validation**: Each aspect tested appropriately
# - **Error isolation**: Separate concerns for easier debugging
#
# #### **3. Mock Strategy Maturity**
# - **Hierarchical design**: Multi-level mock object structure
# - **Universal responses**: Consistent mock behavior
# - **Integration verification**: Call count and output validation
# - **Data flow proof**: Mock data reflected in final output
#
# ### Completion of Stage Testing
#
# This completes the individual stage testing for the orchestrator:
#
# - **Stage 1**: OpenSpec to scaffold (Parts 2-3)
# - **Stage 2**: Scaffold to requirements (Part 3)
# - **Stage 3**: Requirements to alignment (Parts 4-5)
# - **Stage 4**: Alignment to code generation (Parts 6-7)
#
# The sophisticated testing patterns demonstrate comprehensive integration testing that ensures reliable multi-stage pipeline execution while maintaining complete test isolation and production realism.

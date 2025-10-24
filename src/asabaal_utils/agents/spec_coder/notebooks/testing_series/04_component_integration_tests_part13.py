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
# # Module 4: Component Integration Tests - Part 13
# ## Orchestrator Integration Testing: Real AI Integration - Stage 1+2 Testing
#
# **Focus**: Real AI integration testing for Stage 1+2 in `test_orchestrator_integration.py` (lines 700-750).
#
# ### Learning Objectives
# - Master real AI model integration testing with @pytest.mark.integration
# - Understand production AI configuration and optimization
# - Learn real test file generation and validation strategies
# - Analyze multi-stage integration with actual AI execution

# %% [markdown]
# ## 1. Real AI Integration Test Architecture
#
# ### Production AI Testing Strategy
# ```python
#     @pytest.mark.integration
#     def test_stage1_plus_stage2_integration(self, temp_workspace, sample_openspec):
#         """Test Stage 1 + 2 integration (Spec → Scaffold → Requirements) with real AI."""
#         print("\n🧪 Testing Stage 1 + 2 integration with real AI...")
# ```
#
# **Integration Test Analysis:**
#
# #### Integration Test Marker
# ```python
# @pytest.mark.integration
# ```
#
# **Special Test Category:**
# - **Integration marker**: Distinguishes from unit tests
# - **Real AI usage**: Actually calls AI models (no mocks)
# - **Longer execution**: Requires network and AI processing time
# - **Optional running**: Can be skipped in fast test suites
#
# #### Multi-Stage Integration Focus
# ```python
# def test_stage1_plus_stage2_integration(self, temp_workspace, sample_openspec):
# ```
#
# **Stage Combination Testing:**
# - **Stage 1**: OpenSpec to scaffold generation with real AI
# - **Stage 2**: Scaffold to requirements extraction with real analysis
# - **Integration focus**: How real AI output flows between stages
# - **Production simulation**: Actual AI model behavior
#
# #### No Mocking Philosophy
# **Real AI Testing Benefits:**
# - **Production confidence**: Real AI model behavior
# - **Integration validation**: Actual component interaction
# - **End-to-end testing**: Complete data flow with real processing
# - **Performance testing**: Real AI execution time and resource usage

# %% [markdown]
# ## 2. Spec File Validation and Setup
#
# ### Real Specification Verification
# ```python
#         orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
#         
#         # Verify spec file exists and show content
#         assert sample_openspec.exists(), f"Spec file should exist: {sample_openspec}"
#         print(f"📋 Using spec file: {sample_openspec}")
#         print(f"📋 Spec file content preview:\n{sample_openspec.read_text()[:200]}...")
#         print(f"📋 Current working directory: {Path.cwd()}")
#         print(f"📋 Spec file absolute path: {sample_openspec.absolute()}")
#         print(f"📋 Spec file readable: {sample_openspec.is_file()}")
# ```
#
# **Spec File Analysis:**
#
# #### Comprehensive Spec Validation
# ```python
# assert sample_openspec.exists(), f"Spec file should exist: {sample_openspec}"
# ```
#
# **File Existence Verification:**
# - **Absolute certainty**: Spec file must exist for AI processing
# - **Detailed error**: Clear message if file missing
# - **Path debugging**: Shows exact path being checked
# - **Early failure**: Fail fast if input not available
#
# #### Debug Information Output
# ```python
# print(f"📋 Using spec file: {sample_openspec}")
# print(f"📋 Spec file content preview:\n{sample_openspec.read_text()[:200]}...")
# print(f"📋 Current working directory: {Path.cwd()}")
# print(f"📋 Spec file absolute path: {sample_openspec.absolute()}")
# print(f"📋 Spec file readable: {sample_openspec.is_file()}")
# ```
#
# **Production Debugging Strategy:**
# - **File path clarity**: Show exact file being used
# - **Content preview**: Verify spec content is correct
# - **Environment context**: Current directory and absolute paths
# - **Accessibility check**: Confirm file is readable
# - **Visual debugging**: Emoji-enhanced output for clarity
#
# #### Spec Content Preview
# **Why Show Content Preview?**
# - **Input verification**: Confirm spec contains expected content
# - **Debugging aid**: Help diagnose AI processing issues
# - **Test documentation**: Show what data AI receives
# - **Truncation safety**: Only show first 200 characters

# %% [markdown]
# ## 3. Stage 1 Real AI Execution
#
# ### Real AI Scaffold Generation
# ```python
#         # Run Stage 1 - Real AI call to generate test scaffolds
#         print("🔧 Running Stage 1: OpenSpec → Tests/Scaffold")
#         # Use absolute path to ensure generator can find the spec file
#         absolute_spec_path = sample_openspec.absolute()
#         print(f"📋 Using absolute spec path: {absolute_spec_path}")
#         stage1_success = orchestrator._stage1_spec_to_scaffold(absolute_spec_path, temp_workspace)
#         assert stage1_success, "Stage 1 should succeed with real AI"
# ```
#
# **Stage 1 Execution Analysis:**
#
# #### Real AI Invocation
# ```python
# stage1_success = orchestrator._stage1_spec_to_scaffold(absolute_spec_path, temp_workspace)
# ```
#
# **Production Execution:**
# - **No mocks**: Actual AI model called
# - **Real processing**: AI generates test scaffolds from specification
# - **Network dependency**: Requires AI model access
# - **Variable timing**: Execution time depends on AI response
#
# #### Absolute Path Strategy
# ```python
# absolute_spec_path = sample_openspec.absolute()
# print(f"📋 Using absolute spec path: {absolute_spec_path}")
# ```
#
# **Path Resolution Benefits:**
# - **Reliability**: Eliminates relative path ambiguity
# - **AI model access**: Ensures AI can find specification file
# - **Cross-environment**: Works regardless of current directory
# - **Debugging clarity**: Shows exact path used by AI
#
# #### Success Validation
# ```python
# assert stage1_success, "Stage 1 should succeed with real AI"
# ```
#
# **Real AI Success Criteria:**
# - **AI model response**: AI successfully processes specification
# - **File generation**: Test scaffold files created
# - **No network errors**: AI model accessible and responsive
# - **Valid output**: Generated content is usable
#
# #### Execution Logging
# ```python
# print("🔧 Running Stage 1: OpenSpec → Tests/Scaffold")
# ```
#
# **Progress Tracking:**
# - **Stage identification**: Clear indication of current stage
# - **Process description**: What transformation is occurring
# - **Visual marker**: Emoji for easy scanning
# - **Debugging support**: Track execution progress

# %% [markdown]
# ## 4. Stage 1 Output Validation
#
# ### Real AI Generation Verification
# ```python
#         # Verify Stage 1 output
#         stage1_report = temp_workspace / "reports" / "stage1_report.json"
#         assert stage1_report.exists(), "Stage 1 report should exist"
#         
#         # Verify that test scaffolds were actually created
#         scaffolds_dir = temp_workspace / "scaffolds"
#         tests_dir = scaffolds_dir / "tests"
#         assert tests_dir.exists(), "Tests directory should be created"
#         
#         test_files = list(tests_dir.glob("*.py"))
#         assert len(test_files) > 0, "Should have generated test files"
#         print(f"📝 Generated {len(test_files)} test files: {[f.name for f in test_files]}")
# ```
#
# **Stage 1 Validation Analysis:**
#
# #### Report File Verification
# ```python
# stage1_report = temp_workspace / "reports" / "stage1_report.json"
# assert stage1_report.exists(), "Stage 1 report should exist"
# ```
#
# **Generation Report Validation:**
# - **File creation**: AI generation process documented
# - **Expected location**: Consistent with other stages
# - **Success indication**: Report should indicate successful generation
# - **Debugging value**: Contains AI execution details
#
# #### Directory Structure Validation
# ```python
# scaffolds_dir = temp_workspace / "scaffolds"
# tests_dir = scaffolds_dir / "tests"
# assert tests_dir.exists(), "Tests directory should be created"
# ```
#
# **Expected Directory Structure:**
# - **`scaffolds/`**: Main scaffold output directory
# - **`scaffolds/tests/`**: Generated test files location
# - **Automatic creation**: Directory created by Stage 1
# - **Production alignment**: Matches expected pipeline structure
#
# #### Test File Generation Validation
# ```python
# test_files = list(tests_dir.glob("*.py"))
# assert len(test_files) > 0, "Should have generated test files"
# print(f"📝 Generated {len(test_files)} test files: {[f.name for f in test_files]}")
# ```
#
# **Real AI Output Verification:**
# - **File existence**: At least one test file generated
# - **File counting**: Verify multiple files may be generated
# - **File naming**: Show actual generated file names
# - **Content validation**: Files are Python files (`.py` extension)
#
# #### Generation Success Indicators
# **What This Proves:**
# - **AI model functionality**: AI successfully generated test code
# - **File system integration**: Generated files saved correctly
# - **Specification understanding**: AI interpreted OpenSpec correctly
# - **Output quality**: Generated files are valid Python files

# %% [markdown]
# ## 5. Stage 2 Real AI Execution
#
# ### Real AI Requirements Extraction
# ```python
#         # Run Stage 2 - Real analysis of generated test files
#         print("🧠 Running Stage 2: Tests/Scaffold → Logical Requirements")
#         stage2_success = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
#         assert stage2_success, "Stage 2 should succeed"
# ```
#
# **Stage 2 Execution Analysis:**
#
# #### Real AI Analysis
# ```python
# stage2_success = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
# ```
#
# **Stage 2 Processing:**
# - **Input**: Real test files generated by Stage 1 AI
# - **Analysis**: AI analyzes test code to extract requirements
# - **No mocks**: Actual AI analysis of generated content
# - **Integration**: Uses real AI-generated test scaffolds
#
# #### Process Description
# ```python
# print("🧠 Running Stage 2: Tests/Scaffold → Logical Requirements")
# ```
#
# **Stage 2 Purpose:**
# - **Test analysis**: Extract logical requirements from test code
# - **Behavior identification**: Understand what tests are checking
# - **Requirement synthesis**: Create requirement descriptions
# - **AI processing**: Natural language analysis of code
#
# #### Success Validation
# ```python
# assert stage2_success, "Stage 2 should succeed"
# ```
#
# **Stage 2 Success Criteria:**
# - **File reading**: Successfully reads AI-generated test files
# - **Code analysis**: AI analyzes test code structure
# - **Requirement extraction**: Logical requirements identified
# - **Output generation**: Requirement summaries created
#
# #### Integration Validation
# **What This Tests:**
# - **Stage continuity**: Output from Stage 1 feeds into Stage 2
# - **AI coordination**: Two AI processes work together
# - **Data flow**: Real AI-generated content flows between stages
# - **Quality consistency**: Stage 2 can understand Stage 1 output

# %% [markdown]
# ## 6. Stage 2 Output Validation
#
# ### Real AI Analysis Verification
# ```python
#         # Verify Stage 2 output
#         stage2_summary = temp_workspace / "reports" / "stage2_test_summaries" / "test_summary_tests.json"
#         assert stage2_summary.exists(), "Stage 2 summary should exist"
#         
#         # Verify Stage 2 content
#         stage2_content = json.loads(stage2_summary.read_text())
#         assert len(stage2_content) > 0, "Should have extracted test behaviors"
#         print(f"📊 Analyzed {len(stage2_content)} test behaviors")
# ```
#
# **Stage 2 Validation Analysis:**
#
# #### Summary File Verification
# ```python
# stage2_summary = temp_workspace / "reports" / "stage2_test_summaries" / "test_summary_tests.json"
# assert stage2_summary.exists(), "Stage 2 summary should exist"
# ```
#
# **Expected Output Structure:**
# - **Directory**: `stage2_test_summaries/` subdirectory
# - **File**: `test_summary_tests.json` summary file
# - **Creation**: Generated by Stage 2 analysis
# - **Content**: AI analysis results
#
# #### Content Validation
# ```python
# stage2_content = json.loads(stage2_summary.read_text())
# assert len(stage2_content) > 0, "Should have extracted test behaviors"
# ```
#
# **Analysis Results Verification:**
# - **JSON parsing**: File contains valid JSON
# - **Content existence**: Analysis results present
# - **Data extraction**: Test behaviors successfully extracted
# - **Non-empty**: AI found meaningful content to analyze
#
# #### Analysis Reporting
# ```python
# print(f"📊 Analyzed {len(stage2_content)} test behaviors")
# ```
#
# **Quantitative Feedback:**
# - **Behavior count**: Number of test behaviors analyzed
# - **Success indicator**: Non-zero count means successful analysis
# - **Scale awareness**: Shows scope of AI analysis
# - **Debugging value**: Helps understand analysis scope
#
# #### Integration Success Proof
# **What This Validates:**
# - **Stage 1 quality**: Generated tests were analyzable
# - **Stage 2 capability**: AI successfully analyzed test code
# - **Data flow**: Real AI-generated content processed successfully
# - **Pipeline integration**: Two AI stages work together

# %% [markdown]
# ## 7. Metadata Persistence Validation
#
# ### Cross-Stage State Management
# ```python
#         # Verify metadata persistence
#         assert orchestrator.spec_file_path == sample_openspec.absolute()
#         
#         print("   ✅ Stage 1 + 2 integration successful with real AI")
# ```
#
# **Metadata Validation Analysis:**
#
# #### State Persistence Check
# ```python
# assert orchestrator.spec_file_path == sample_openspec.absolute()
# ```
#
# **Cross-Stage Continuity:**
# - **State retention**: Spec file path preserved across stages
# - **Metadata consistency**: Orchestrator maintains correct state
# - **Pipeline context**: Original specification still accessible
# - **Integration proof**: Stages share common context
#
# #### Success Confirmation
# ```python
# print("   ✅ Stage 1 + 2 integration successful with real AI")
# ```
#
# **Integration Success Indicators:**
# - **Stage 1 success**: Real AI generated test scaffolds
# - **Stage 2 success**: Real AI analyzed generated tests
# - **Data flow**: AI-generated content successfully processed
# - **Pipeline completion**: Both stages completed successfully
#
# #### Real AI Integration Value
# **What This Test Proves:**
# - **Production readiness**: Real AI models work in pipeline
# - **Quality assurance**: AI-generated content is usable
# - **Integration reliability**: Stages work with real AI output
# - **Performance validation**: Acceptable execution time and quality

# %% [markdown]
# ## 8. Key Real AI Integration Patterns Summary
#
# ### 1. Integration Test Marking
# ```python
# @pytest.mark.integration
# def test_stage1_plus_stage2_integration(self, temp_workspace, sample_openspec):
#     # Real AI execution, no mocks
# ```
#
# **Benefits:**
# - **Test categorization**: Distinguishes integration from unit tests
# - **Optional execution**: Can be skipped in fast test suites
# - **Production confidence**: Real AI model behavior validation
# - **Performance testing**: Actual AI execution time
#
# ### 2. Comprehensive Input Validation
# ```python
# assert sample_openspec.exists()
# print(f"📋 Spec file content preview:\n{sample_openspec.read_text()[:200]}...")
# print(f"📋 Using absolute spec path: {absolute_spec_path}")
# ```
#
# **Benefits:**
# - **Input verification**: Confirm AI receives correct data
# - **Debugging support**: Clear visibility into test inputs
# - **Path reliability**: Absolute paths prevent access issues
# - **Test documentation**: Shows what AI processes
#
# ### 3. Real AI Output Validation
# ```python
# test_files = list(tests_dir.glob("*.py"))
# assert len(test_files) > 0, "Should have generated test files"
# print(f"📝 Generated {len(test_files)} test files: {[f.name for f in test_files]}")
# ```
#
# **Benefits:**
# - **Tangible results**: Verify AI actually generated files
# - **Quality assessment**: Files are valid Python code
# - **Quantitative feedback**: Count and names of generated files
# - **Production simulation**: Real AI output validation
#
# ### 4. Multi-Stage Integration Testing
# ```python
# # Stage 1: Real AI generation
# stage1_success = orchestrator._stage1_spec_to_scaffold(absolute_spec_path, temp_workspace)
# # Stage 2: Real AI analysis of Stage 1 output
# stage2_success = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
# ```
#
# **Benefits:**
# - **End-to-end validation**: Complete AI pipeline testing
# - **Data flow verification**: Real AI output feeds next stage
# - **Quality consistency**: Stage 2 can understand Stage 1 output
# - **Integration reliability**: AI components work together
#
# ### 5. Production-Ready Debugging
# ```python
# print("🔧 Running Stage 1: OpenSpec → Tests/Scaffold")
# print("🧠 Running Stage 2: Tests/Scaffold → Logical Requirements")
# print(f"📊 Analyzed {len(stage2_content)} test behaviors")
# print("   ✅ Stage 1 + 2 integration successful with real AI")
# ```
#
# **Benefits:**
# - **Progress tracking**: Clear execution visibility
# - **Quantitative feedback**: Measurable results
# - **Success confirmation**: Clear completion indicators
# - **Debugging support**: Rich execution information

# %% [markdown]
# ## 9. Module 4 Part 13 Summary
#
# ### What We Covered
#
# #### **Real AI Integration Architecture** (Lines 700-710)
# - **@pytest.mark.integration**: Special test category for real AI
# - **Multi-stage testing**: Stage 1+2 integration with real AI
# - **No mocking philosophy**: Production AI behavior validation
#
# #### **Comprehensive Input Validation** (Lines 711-725)
# - **Spec file verification**: Existence and content validation
# - **Debugging output**: Path and content visibility
# - **Absolute path strategy**: Reliable AI file access
#
# #### **Stage 1 Real AI Execution** (Lines 726-740)
# - **Real AI invocation**: Actual scaffold generation
# - **Success validation**: AI processing confirmation
# - **Progress tracking**: Clear execution logging
#
# #### **Stage 1 Output Validation** (Lines 741-755)
# - **Report verification**: Generation documentation
# - **File generation**: Real test file creation validation
# - **Quantitative feedback**: File count and naming
#
# #### **Stage 2 Real AI Execution** (Lines 756-765)
# - **Real AI analysis**: Processing of Stage 1 output
# - **Integration testing**: AI-to-AI data flow
# - **Success validation**: Analysis completion
#
# #### **Stage 2 Output Validation** (Lines 766-780)
# - **Summary verification**: Analysis results validation
# - **Content validation**: Non-empty analysis results
# - **Quantitative reporting**: Behavior count feedback
#
# ### Key Strategic Insights
#
# #### **1. Production AI Testing Philosophy**
# - **Real model validation**: Actual AI behavior, not mocks
# - **Integration confidence**: AI components work together
# - **Quality assurance**: AI-generated content is usable
# - **Performance validation**: Acceptable execution time
#
# #### **2. Multi-Stage AI Integration**
# - **Data flow verification**: Real AI output feeds next stage
# - **Quality consistency**: Stage 2 understands Stage 1 output
# - **End-to-end testing**: Complete AI pipeline validation
# - **Production simulation**: Real-world execution patterns
#
# #### **3. Comprehensive Validation Strategy**
# - **Input verification**: Confirm AI receives correct data
# - **Output validation**: Verify AI generates usable results
# - **Integration proof**: Stages work with real AI content
# - **Debugging support**: Rich execution visibility
#
# ### Foundation for Production Deployment
#
# This real AI integration testing provides the foundation for:
#
# - **Production confidence**: Real AI models work in pipeline
# - **Quality assurance**: AI-generated content meets standards
# - **Performance validation**: Acceptable execution characteristics
# - **Integration reliability**: Multi-stage AI coordination
#
# The sophisticated real AI integration patterns demonstrate production-ready testing that ensures actual AI model behavior and multi-stage coordination work reliably in real-world scenarios.

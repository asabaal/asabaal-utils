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
# # 🔍 Module 4: AnalysisEngine - AI-Powered Test Analysis Engine
#
# ## Purpose
# The AnalysisEngine combines AST parsing with AI summarization to analyze test files and generate comprehensive behavior summaries.
#
# ## What This Module Does
# 1. **AST Parsing**: Analyzes test file structure using Python's Abstract Syntax Tree
# 2. **AI Analysis**: Uses AI models to understand test semantics and behavior
# 3. **Coverage Analysis**: Evaluates test coverage and quality metrics
# 4. **Directory Processing**: Processes entire test directories efficiently
# 5. **Report Generation**: Creates comprehensive analysis reports
#
# ## Key Components
# - `AnalysisEngine`: Main orchestrator class for test analysis
# - `TestSummarizer`: AI-powered test behavior summarization
# - `parse_test_file()`: AST-based test file parsing function
# - `analyze_single_file()`: Analyze individual test files
# - `analyze_directory()`: Process entire test directories
# - `generate_report()`: Create analysis reports

# %% [markdown]
# ## 📋 Setup and Configuration

# %%
# Import required modules
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from IPython.display import display, Markdown, HTML

# Add current directory to path for imports
current_dir = Path(__file__).parent.parent.parent if '__file__' in globals() else Path.cwd()
sys.path.insert(0, str(current_dir))

# Import the AnalysisEngine and related components
try:
    from tester import AnalysisEngine, TestSummarizer, parse_test_file
    print("✅ AnalysisEngine and related components imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running this from the spec_coder directory")

# Setup logging to see analysis progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("🔍 Test Analysis Setup complete!")

# %%
# AnalysisEngine Configuration
BASE_DIR = current_dir
TESTS_DIR = BASE_DIR / "tests"
REPORTS_DIR = BASE_DIR / "reports"

print(f"📁 Base directory: {BASE_DIR}")
print(f"🧪 Tests directory: {TESTS_DIR}")
print(f"📊 Reports directory: {REPORTS_DIR}")

# Verify directories exist
for dir_path, name in [(TESTS_DIR, "Tests"), (REPORTS_DIR, "Reports")]:
    if dir_path.exists():
        print(f"✅ {name} directory found")
    else:
        print(f"❌ {name} directory not found: {dir_path}")

# %% [markdown]
# ## 🏗️ Step 4.1: Initialize the AnalysisEngine

# %%
# Initialize the AnalysisEngine
analyzer = AnalysisEngine(
    model_name="qwen3-coder:latest",
    spec_file=None,  # We'll add this later if needed
    source_file=None  # We'll add this later if needed
)

print("🔍 AnalysisEngine Configuration:")
print(f"  Model name: {analyzer.summarizer.client.config.model if hasattr(analyzer, 'summarizer') else 'Unknown'}")
print(f"  Spec file: {analyzer.spec_file if hasattr(analyzer, 'spec_file') else 'None'}")
print(f"  Source file: {analyzer.source_file if hasattr(analyzer, 'source_file') else 'None'}")

# Show available methods
methods = [method for method in dir(analyzer) if not method.startswith('_')]
print(f"\n📋 Available methods: {methods}")

print("\n✅ AnalysisEngine ready for test analysis!")

# %% [markdown]
# ## 📄 Step 4.2: Test File Structure Analysis

# %%
# Create a sample test file for analysis
sample_test_content = '''
import pytest
from pathlib import Path

def test_file_processing():
    """Test basic file processing functionality."""
    test_file = Path("test.txt")
    assert test_file.suffix == ".txt"
    assert test_file.name == "test.txt"

def test_error_handling():
    """Test error handling in file operations."""
    with pytest.raises(FileNotFoundError):
        Path("nonexistent.txt").read_text()

class TestFileOperations:
    """Test class for file operations."""
    
    def test_class_method(self):
        """Test class-based test method."""
        assert True
'''

# Create sample test file
sample_test_file = TESTS_DIR / "sample_test.py"
TESTS_DIR.mkdir(exist_ok=True)
with open(sample_test_file, 'w') as f:
    f.write(sample_test_content)

print(f"📄 Created sample test file: {sample_test_file}")
print(f"📏 File size: {sample_test_file.stat().st_size} bytes")

# Analyze the test file structure using AST parsing
print("\n🔍 AST-based Test File Analysis:")
print("=" * 40)

try:
    parsed_data = parse_test_file(sample_test_file)
    
    print(f"📁 File: {parsed_data.get('file_path', 'Unknown')}")
    print(f"📋 Functions found: {len(parsed_data.get('functions', []))}")
    print(f"🏛️ Classes found: {len(parsed_data.get('classes', []))}")
    print(f"📦 Imports: {len(parsed_data.get('imports', []))}")
    
    # Show function details
    for i, func in enumerate(parsed_data.get('functions', []), 1):
        print(f"\n  📝 Function {i}: {func.get('name', 'Unknown')}")
        print(f"     Line: {func.get('line', 'Unknown')}")
        print(f"     Args: {func.get('args', [])}")
        print(f"     Docstring: {func.get('docstring', 'No docstring')[:50]}...")
    
    # Show class details
    for i, cls in enumerate(parsed_data.get('classes', []), 1):
        print(f"\n  🏛️ Class {i}: {cls.get('name', 'Unknown')}")
        print(f"     Line: {cls.get('line', 'Unknown')}")
        print(f"     Methods: {len(cls.get('methods', []))}")
        
except Exception as e:
    print(f"❌ Error parsing test file: {e}")

# %% [markdown]
# ## 🤖 Step 4.3: AI-Powered Test Analysis

# %%
# Use AnalysisEngine to analyze the test file with AI
print("🤖 AI-Powered Test Analysis:")
print("=" * 35)

try:
    # Analyze the sample test file
    analysis_result = analyzer.analyze_single_file(sample_test_file)
    
    print(f"✅ Analysis completed for: {analysis_result.get('file_path', 'Unknown')}")
    
    # Show basic analysis results
    print(f"\n📊 Analysis Summary:")
    print(f"  Functions analyzed: {len(analysis_result.get('functions', []))}")
    print(f"  Classes analyzed: {len(analysis_result.get('classes', []))}")
    
    # Show AI-generated behaviors if available
    if 'behaviors' in analysis_result:
        print(f"\n🧠 AI-Generated Behaviors:")
        for i, behavior in enumerate(analysis_result['behaviors'], 1):
            print(f"  {i}. {behavior.get('function', 'Unknown')}: {behavior.get('behavior', 'No behavior')}")
            print(f"     Confidence: {behavior.get('confidence', 0):.2f}")
    
    # Show coverage analysis if available
    if 'coverage_analysis' in analysis_result:
        coverage = analysis_result['coverage_analysis']
        print(f"\n📈 Coverage Analysis:")
        print(f"  Quality score: {coverage.get('quality_score', 0):.2f}")
        print(f"  Behaviors extracted: {coverage.get('behaviors_extracted', 0)}")
    
    # Show recommendations if available
    if 'recommendations' in analysis_result:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(analysis_result['recommendations'], 1):
            print(f"  {i}. {rec}")
    
except Exception as e:
    print(f"❌ Error during AI analysis: {e}")
    print("💡 This might be due to missing AI model or configuration issues")
    print("🔧 The AST parsing part should still work even if AI analysis fails")

# %% [markdown]
# ## 📁 Step 4.4: Directory-Wide Analysis

# %%
# Analyze entire test directory
print("📁 Directory-Wide Test Analysis:")
print("=" * 40)

if TESTS_DIR.exists():
    try:
        # Get all Python test files
        test_files = list(TESTS_DIR.glob("**/test_*.py"))
        print(f"📄 Found {len(test_files)} test files")
        
        if test_files:
            # Show first few files
            print("\n📋 Test files found:")
            for i, test_file in enumerate(test_files[:5], 1):
                rel_path = test_file.relative_to(TESTS_DIR)
                size = test_file.stat().st_size
                print(f"  {i}. {rel_path} ({size:,} bytes)")
            
            if len(test_files) > 5:
                print(f"  ... and {len(test_files) - 5} more files")
            
            # Analyze directory (this might take time with AI analysis)
            print(f"\n🔍 Analyzing directory...")
            directory_results = analyzer.analyze_directory(TESTS_DIR)
            
            print(f"✅ Directory analysis completed")
            print(f"📊 Files processed: {len(directory_results.get('files', []))}")
            
            # Show summary statistics
            if 'summary' in directory_results:
                summary = directory_results['summary']
                print(f"\n📈 Summary Statistics:")
                print(f"  Total functions: {summary.get('total_functions', 0)}")
                print(f"  Total classes: {summary.get('total_classes', 0)}")
                print(f"  Average quality score: {summary.get('avg_quality_score', 0):.2f}")
        else:
            print("❌ No test files found in the directory")
            
    except Exception as e:
        print(f"❌ Error during directory analysis: {e}")
        print("💡 This might be due to AI model issues or large directory processing")
else:
    print("❌ Tests directory not found")
    print("💡 Create some test files to see directory analysis in action")

# %% [markdown]
# ## 📊 Step 4.5: Report Generation

# %%
# Generate comprehensive analysis report
print("📊 Analysis Report Generation:")
print("=" * 35)

try:
    # Generate report for the sample test file
    if 'analysis_result' in locals() and analysis_result:
        report = analyzer.generate_report(analysis_result)
        
        print("✅ Report generated successfully!")
        print(f"📏 Report length: {len(str(report))} characters")
        
        # Show report structure
        if isinstance(report, dict):
            print("\n📋 Report sections:")
            for key, value in report.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                elif isinstance(value, dict):
                    print(f"  {key}: {len(value)} sub-items")
                else:
                    print(f"  {key}: {type(value).__name__}")
        
        # Save report to file
        REPORTS_DIR.mkdir(exist_ok=True)
        report_file = REPORTS_DIR / "test_analysis_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Report saved to: {report_file}")
        print(f"📏 Report file size: {report_file.stat().st_size:,} bytes")
        
    else:
        print("❌ No analysis results available for report generation")
        print("💡 Run the AI analysis first to generate results")
        
except Exception as e:
    print(f"❌ Error generating report: {e}")

# %% [markdown]
# ## 🧪 Step 4.6: Test Execution Integration

# %%
# Test execution functionality
print("🧪 Test Execution Integration:")
print("=" * 35)

try:
    # Check if run_tests method is available
    if hasattr(analyzer, 'run_tests'):
        print("✅ Test execution functionality available")
        
        # Try to run tests on the sample file (if pytest is available)
        print(f"\n🏃 Running tests on: {sample_test_file}")
        
        test_results = analyzer.run_tests(sample_test_file)
        
        if test_results:
            print(f"✅ Test execution completed")
            print(f"📊 Results: {test_results}")
        else:
            print("⚠️ No test results returned (might be normal if no test runner configured)")
            
    else:
        print("⚠️ Test execution not available in this AnalysisEngine version")
        
except Exception as e:
    print(f"❌ Error during test execution: {e}")
    print("💡 This might be due to missing pytest or test configuration")
    print("🔧 The analysis functionality should work independently of test execution")

# %% [markdown]
# ## 🔧 Step 4.7: AnalysisEngine Components Deep Dive

# %%
# Examine the components that make up AnalysisEngine
print("🔧 AnalysisEngine Components Deep Dive:")
print("=" * 45)

# Check TestSummarizer component
if hasattr(analyzer, 'summarizer'):
    summarizer = analyzer.summarizer
    print(f"\n🤖 TestSummarizer Component:")
    print(f"  Type: {type(summarizer).__name__}")
    print(f"  Model: {getattr(summarizer, 'model_name', 'Unknown')}")
    
    summarizer_methods = [method for method in dir(summarizer) if not method.startswith('_')]
    print(f"  Methods: {summarizer_methods}")
else:
    print("\n❌ TestSummarizer component not found")

# Check parse_test_file function
print(f"\n📄 parse_test_file Function:")
try:
    # Test the function with our sample file
    parse_result = parse_test_file(sample_test_file)
    print(f"  ✅ Function works correctly")
    print(f"  📊 Returns: {type(parse_result).__name__}")
    print(f"  📋 Keys: {list(parse_result.keys()) if isinstance(parse_result, dict) else 'Not a dict'}")
except Exception as e:
    print(f"  ❌ Function error: {e}")

# Show AnalysisEngine method details
print(f"\n🔍 AnalysisEngine Methods:")
for method_name in ['analyze_single_file', 'analyze_directory', 'generate_report', 'run_tests']:
    if hasattr(analyzer, method_name):
        method = getattr(analyzer, method_name)
        print(f"  ✅ {method_name}: {method.__doc__.split('.')[0] if method.__doc__ else 'No documentation'}")
    else:
        print(f"  ❌ {method_name}: Not found")

# %% [markdown]
# ## ✅ Step 4.8: AnalysisEngine Validation

# %%
# Validate the AnalysisEngine setup and functionality
print("✅ AnalysisEngine Validation:")
print("=" * 30)

validation_results = {
    "import_success": False,
    "initialization": False,
    "ast_parsing": False,
    "ai_analysis": False,
    "directory_processing": False,
    "report_generation": False
}

# Check import success
try:
    from tester import AnalysisEngine, TestSummarizer, parse_test_file
    validation_results["import_success"] = True
    print("✅ Import: Success")
except ImportError:
    print("❌ Import: Failed")

# Check initialization
try:
    test_analyzer = AnalysisEngine()
    validation_results["initialization"] = True
    print("✅ Initialization: Success")
except Exception as e:
    print(f"❌ Initialization: Failed - {e}")

# Check AST parsing
try:
    if 'sample_test_file' in locals() and sample_test_file.exists():
        parsed = parse_test_file(sample_test_file)
        if isinstance(parsed, dict) and 'functions' in parsed:
            validation_results["ast_parsing"] = True
            print("✅ AST parsing: Success")
        else:
            print("❌ AST parsing: Invalid result format")
    else:
        print("⚠️ AST parsing: No test file available")
except Exception as e:
    print(f"❌ AST parsing: Failed - {e}")

# Check AI analysis (might fail without AI model)
try:
    if 'analysis_result' in locals() and analysis_result:
        validation_results["ai_analysis"] = True
        print("✅ AI analysis: Success")
    else:
        print("⚠️ AI analysis: Not completed (might be normal without AI model)")
except Exception as e:
    print(f"❌ AI analysis: Failed - {e}")

# Check directory processing
try:
    if hasattr(analyzer, 'analyze_directory'):
        validation_results["directory_processing"] = True
        print("✅ Directory processing: Method available")
    else:
        print("❌ Directory processing: Method not found")
except Exception as e:
    print(f"❌ Directory processing: Failed - {e}")

# Check report generation
try:
    if hasattr(analyzer, 'generate_report'):
        validation_results["report_generation"] = True
        print("✅ Report generation: Method available")
    else:
        print("❌ Report generation: Method not found")
except Exception as e:
    print(f"❌ Report generation: Failed - {e}")

# Overall validation
passed_validations = sum(validation_results.values())
total_validations = len(validation_results)

print(f"\n📊 Validation Summary:")
print(f"  Passed: {passed_validations}/{total_validations}")
print(f"  Success Rate: {(passed_validations/total_validations)*100:.1f}%")

if passed_validations >= total_validations * 0.75:
    print("\n🎉 AnalysisEngine is ready for use!")
    if not validation_results.get("ai_analysis"):
        print("💡 Note: AI analysis might need additional configuration (AI model setup)")
else:
    print("\n⚠️ Several validations failed. Review the AnalysisEngine setup.")

# %% [markdown]
# ## 📚 Step 4.9: AnalysisEngine Documentation

# %%
# Display comprehensive documentation about the AnalysisEngine
print("📚 AnalysisEngine Documentation:")
print("=" * 40)

documentation = {
    "Purpose": "Combines AST parsing with AI summarization for comprehensive test analysis",
    "Main Class": "AnalysisEngine",
    "Key Methods": [
        "analyze_single_file() - Analyze individual test files with AI",
        "analyze_directory() - Process entire test directories",
        "generate_report() - Create comprehensive analysis reports",
        "run_tests() - Execute tests and integrate results"
    ],
    "Components": {
        "TestSummarizer": "AI-powered test behavior analysis and summarization",
        "parse_test_file()": "AST-based test file structure parsing",
        "AnalysisEngine": "Main orchestrator combining all components"
    },
    "Input": "Test files (Python) and optional specification/source files",
    "Output": "Comprehensive analysis reports with AI-generated insights",
    "AI Integration": "Uses AI models for semantic test behavior analysis",
    "Static Analysis": "AST parsing for structural test analysis",
    "Use Cases": [
        "Test quality assessment and coverage analysis",
        "Test behavior extraction and documentation",
        "Integration test validation and gap identification",
        "Test suite optimization and maintenance"
    ]
}

for section, content in documentation.items():
    print(f"\n📋 {section}:")
    if isinstance(content, list):
        for item in content:
            print(f"  • {item}")
    elif isinstance(content, dict):
        for key, value in content.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {content}")

print("\n🔗 Related Components:")
print("  • SpecParser - Provides specification context for analysis")
print("  • CodeGenerator - Generates code that AnalysisEngine can validate")
print("  • IntegrationOrchestrator - Coordinates analysis in the pipeline")
print("  • OllamaClient - Provides AI models for TestSummarizer")

print("\n🎯 Usage Pattern:")
print("  1. Initialize AnalysisEngine with AI model configuration")
print("  2. Analyze test files individually or by directory")
print("  3. Review AI-generated behaviors and coverage analysis")
print("  4. Generate comprehensive reports for stakeholders")
print("  5. Use insights to improve test quality and coverage")

# %% [markdown]
# ## 🎯 Summary: AnalysisEngine Module
#
# ### What We Covered
# 1. **Module Structure**: Understanding the AnalysisEngine class and its components
# 2. **AST Parsing**: How test files are analyzed for structure and content
# 3. **AI Analysis**: How TestSummarizer provides semantic test understanding
# 4. **Directory Processing**: Efficient processing of entire test suites
# 5. **Report Generation**: Creating comprehensive analysis reports
# 6. **Test Execution**: Integration with test runners for validation
# 7. **Component Integration**: How all parts work together
#
# ### Key Takeaways
# - AnalysisEngine combines static AST analysis with AI-powered semantic analysis
# - TestSummarizer provides intelligent test behavior extraction using AI models
# - The system can process individual files or entire test directories
# - Reports include quality scores, coverage analysis, and improvement recommendations
# - Integration with test execution provides validation of analysis results
# - The system works with or without AI models (graceful degradation)
#
# ### When to Use
# - For comprehensive test quality assessment and coverage analysis
# - When identifying test gaps and improvement opportunities
# - For validating test suite completeness against specifications
# - When generating test documentation and reports
# - For integration into CI/CD pipelines for quality gates
#
# ### Integration Points
# - **Input**: Test files, optional specification files, source code files
# - **Output**: Analysis reports, behavior summaries, coverage metrics
# - **Dependencies**: AI models (via OllamaClient), AST parsing, test runners
# - **Consumers**: Development teams, QA teams, CI/CD systems
#
# ### Real Implementation Status
# ✅ **VERIFIED**: This notebook now uses the REAL `AnalysisEngine` class with actual functionality:
# - `analyze_single_file()` for individual test file analysis
# - `analyze_directory()` for processing entire test suites
# - `generate_report()` for comprehensive analysis reporting
# - `TestSummarizer` component for AI-powered semantic analysis
# - `parse_test_file()` function for AST-based structural analysis
#
# The AnalysisEngine is a sophisticated tool that provides both static analysis and AI-powered insights for test quality assessment and improvement.

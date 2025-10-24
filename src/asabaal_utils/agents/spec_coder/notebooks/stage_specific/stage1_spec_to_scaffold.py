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
#     display_name: basic_audio_env
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 🔧 Stage 1: OpenSpec → Test/Scaffold
#
# ## Purpose
# Transform an OpenSpec YAML specification into:
# - **Source code scaffold** (basic function signatures)
# - **Comprehensive tests** (pytest with examples)
# - **Documentation** (markdown with usage examples)
#
# ## What This Stage Does
# 1. **Parses** the OpenSpec specification
# 2. **Generates** function signatures based on interfaces
# 3. **Creates** tests using the example inputs/outputs from the spec
# 4. **Builds** documentation with concrete examples
#
# ## Key Components
# - `CodeGenerator`: Main orchestrator for this stage
# - `SpecParser`: Extracts requirements and interfaces
# - `PromptTemplates`: AI prompts for code/test/doc generation
# - `OllamaClient`: AI model interface

# %% [markdown]
# ## 📋 Setup and Configuration

# %%
# Import required modules
import sys
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from IPython.display import display, Markdown, HTML

# Add the asabaal_utils package to Python path for proper package imports
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
# Go up to the repository root to find asabaal_utils package
repo_root = current_dir.parent
sys.path.insert(0, str(repo_root))

# Import Stage 1 specific components from proper package paths
try:
    from asabaal_utils.agents.spec_coder.generator import CodeGenerator
    from asabaal_utils.agents.spec_coder.spec_parser import SpecParser
    from asabaal_utils.agents.spec_coder.ollama_client import OllamaClient
    from asabaal_utils.agents.spec_coder.templates import PromptTemplates
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running this from the spec_coder directory")
    print(f"📁 Current directory: {current_dir}")
    print(f"📁 Python path: {sys.path[:3]}")  # Show first 3 entries

# Setup logging to see detailed AI interactions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("🔧 Stage 1 Setup complete!")

# %%
# Stage 1 Configuration
current_dir = Path(__file__).parent.parent.parent if '__file__' in globals() else Path.cwd().parent.parent
SPEC_FILE = current_dir / "rhythmic_pulse_generator.yml"
STAGE1_OUTPUT = current_dir / "stage1_output"
STAGE1_OUTPUT.mkdir(exist_ok=True)

print(f"📁 Current directory: {current_dir}")
print(f"📁 Input spec: {SPEC_FILE}")
print(f"📁 Stage 1 output: {STAGE1_OUTPUT}")

# Verify spec file exists
if SPEC_FILE.exists():
    print("✅ Spec file found!")
    print(f"📏 Spec file size: {SPEC_FILE.stat().st_size:,} bytes")
else:
    print(f"❌ Spec file not found: {SPEC_FILE}")
    print("💡 Available example files:")
    examples_dir = current_dir / "examples"
    if examples_dir.exists():
        for example_file in examples_dir.glob("*.yml"):
            print(f"  - {example_file.name}")

# %% [markdown]
# ## 🔍 Step 1.1: Examine the Input Specification

# %%
# Load and display the raw specification
with open(SPEC_FILE, 'r') as f:
    raw_spec = f.read()

print("📋 Raw OpenSpec YAML:")
print("=" * 50)
print(raw_spec)

# %%
# Parse the specification using SpecParser
parser = SpecParser()
spec = parser.parse_file(SPEC_FILE)

print("🏗️ Parsed Specification Structure:")
print(f"Spec ID: {spec.spec_id}")
print(f"Title: {spec.title}")
print(f"Version: {spec.version}")
print(f"Requirements: {len(spec.requirements)}")

print("\n📋 Detailed Requirements Analysis:")
for i, req in enumerate(spec.requirements, 1):
    print(f"\n--- Requirement {i}: {req.id} ---")
    print(f"Title: {req.title}")
    print(f"Description: {req.description}")
    
    if req.interface:
        print(f"\n🔧 Function Interface:")
        print(f"  Function: {req.interface.function}")
        print(f"  Parameters: {req.interface.parameters}")
        print(f"  Returns: {req.interface.returns}")
        
        if req.interface.example:
            print(f"\n💡 Example (CRITICAL for test generation):")
            print(f"  Input: {req.interface.example.get('input', 'N/A')}")
            print(f"  Output: {req.interface.example.get('output', 'N/A')}")
    
    if req.validation:
        print(f"\n✅ Validation Criteria:")
        for val in req.validation:
            print(f"  Type: {val.type}, File: {val.file}, Target: {val.target}")

# %% [markdown]
# ## 🤖 Step 1.2: Examine the AI Prompts for Stage 1

# %%
# Load and examine the prompt templates
templates = PromptTemplates()

print("📝 Stage 1 Prompt Templates:")
print("=" * 40)

# Code generation prompt
print("\n🔧 Code Generation Prompt:")
print("-" * 30)
code_prompt = templates.source_code_prompt
print(code_prompt[:1000] + "..." if len(code_prompt) > 1000 else code_prompt)

print("\n" + "=" * 50)

# Test generation prompt  
print("\n🧪 Test Generation Prompt:")
print("-" * 30)
test_prompt = templates.test_prompt
print(test_prompt[:1000] + "..." if len(test_prompt) > 1000 else test_prompt)

print("\n" + "=" * 50)

# Documentation generation prompt
print("\n📚 Documentation Generation Prompt:")
print("-" * 30)
doc_prompt = templates.documentation_prompt
print(doc_prompt[:1000] + "..." if len(doc_prompt) > 1000 else doc_prompt)

# %% [markdown]
# ## 🏭 Step 1.3: Initialize the Code Generator

# %%
# Initialize the CodeGenerator with detailed configuration
generator = CodeGenerator()

print("🏭 CodeGenerator Configuration:")
print(f"  Output directory: {STAGE1_OUTPUT}")
print(f"  Spec file: {SPEC_FILE}")
print(f"  AI Model: {generator.ollama_client.config.model if hasattr(generator, 'ollama_client') else 'Unknown'}")

# Show generator internals
if hasattr(generator, 'templates'):
    print(f"  Templates loaded: {type(generator.templates).__name__}")
if hasattr(generator, 'ollama_client'):
    print(f"  Ollama client: {type(generator.ollama_client).__name__}")

print("\n✅ CodeGenerator ready for Stage 1 execution!")

# %% [markdown]
# ## ⚡ Step 1.4: Execute Stage 1 - Generate Scaffold

# %%
# Execute Stage 1 generation
print("🚀 Starting Stage 1: OpenSpec → Test/Scaffold")
print(f"📁 Input: {SPEC_FILE}")
print(f"📁 Output: {STAGE1_OUTPUT}")
print("\n⏳ This may take a few minutes as it calls AI models...\n")

# Run the generation
result = generator.generate_from_spec(SPEC_FILE, STAGE1_OUTPUT)

print("\n📊 Stage 1 Results:")
print(f"  Success: {result.success}")
print(f"  Files generated: {len(result.files_generated)}")
print(f"  Execution time: {result.execution_time:.2f}s")
print(f"  Errors: {len(result.errors)}")
print(f"  Warnings: {len(result.warnings)}")

if result.errors:
    print("\n❌ Errors:")
    for error in result.errors:
        print(f"  - {error}")

if result.warnings:
    print("\n⚠️ Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")

if result.success:
    print("\n✅ Stage 1 completed successfully!")
else:
    print("\n❌ Stage 1 failed!")

# %% [markdown]
# ## 📁 Step 1.5: Examine Generated Files

# %%
# List all generated files
print("📁 Stage 1 Generated Files:")
print("=" * 40)

if STAGE1_OUTPUT.exists():
    for file_path in sorted(STAGE1_OUTPUT.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(STAGE1_OUTPUT)
            size = file_path.stat().st_size
            print(f"📄 {rel_path} ({size:,} bytes)")
else:
    print("❌ No output directory found")

# %% [markdown]
# ## 💻 Step 1.6: Analyze Generated Source Code

# %%
# Examine the generated source code scaffold
src_files = list(STAGE1_OUTPUT.rglob("*.py"))
src_files = [f for f in src_files if "test_" not in f.name]

for src_file in src_files:
    rel_path = src_file.relative_to(STAGE1_OUTPUT)
    print(f"\n💻 Source Code: {rel_path}")
    print("=" * 50)
    
    with open(src_file, 'r') as f:
        content = f.read()
    
    print(content)
    
    # Analysis
    lines = content.split('\n')
    functions = [line.strip() for line in lines if line.strip().startswith('def ')]
    imports = [line.strip() for line in lines if line.strip().startswith('import') or line.strip().startswith('from')]
    
    print(f"\n📊 Analysis:")
    print(f"  Total lines: {len(lines)}")
    print(f"  Functions: {len(functions)}")
    for func in functions:
        print(f"    - {func}")
    print(f"  Imports: {len(imports)}")
    for imp in imports:
        print(f"    - {imp}")

# %% [markdown]
# ## 🧪 Step 1.7: Analyze Generated Tests

# %%
# Examine the generated test files
test_files = list(STAGE1_OUTPUT.rglob("test_*.py"))

for test_file in test_files:
    rel_path = test_file.relative_to(STAGE1_OUTPUT)
    print(f"\n🧪 Test File: {rel_path}")
    print("=" * 50)
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    print(content)
    
    # Test analysis
    lines = content.split('\n')
    test_functions = [line.strip() for line in lines if line.strip().startswith('def test_')]
    assertions = [line.strip() for line in lines if 'assert' in line]
    
    print(f"\n📊 Test Analysis:")
    print(f"  Total lines: {len(lines)}")
    print(f"  Test functions: {len(test_functions)}")
    for test_func in test_functions:
        print(f"    - {test_func}")
    print(f"  Assertions: {len(assertions)}")
    for i, assertion in enumerate(assertions[:5], 1):  # Show first 5
        print(f"    {i}. {assertion}")
    if len(assertions) > 5:
        print(f"    ... and {len(assertions) - 5} more")
    
    # Check if examples from spec are included
    spec_examples = []
    for req in spec.requirements:
        if req.interface and req.interface.example:
            spec_examples.append(req.interface.example)
    
    print(f"\n🎯 Spec Examples in Tests:")
    for i, example in enumerate(spec_examples, 1):
        example_str = str(example)
        if example_str in content:
            print(f"  ✅ Example {i} found in tests")
        else:
            print(f"  ❌ Example {i} NOT found in tests")
            print(f"     Expected: {example_str}")

# %% [markdown]
# ## 📚 Step 1.8: Analyze Generated Documentation

# %%
# Examine the generated documentation
doc_files = list(STAGE1_OUTPUT.rglob("*.md"))

for doc_file in doc_files:
    rel_path = doc_file.relative_to(STAGE1_OUTPUT)
    print(f"\n📚 Documentation: {rel_path}")
    print("=" * 50)
    
    with open(doc_file, 'r') as f:
        content = f.read()
    
    print(content)
    
    # Documentation analysis
    lines = content.split('\n')
    code_blocks = [line.strip() for line in lines if line.strip().startswith('```')]
    headers = [line.strip() for line in lines if line.strip().startswith('#')]
    
    print(f"\n📊 Documentation Analysis:")
    print(f"  Total lines: {len(lines)}")
    print(f"  Headers: {len(headers)}")
    for header in headers:
        print(f"    - {header}")
    print(f"  Code blocks: {len(code_blocks) // 2}")  # Each block has opening and closing
    
    # Check for expected outputs in examples
    print(f"\n🎯 Expected Outputs in Documentation:")
    has_expected_outputs = False
    for req in spec.requirements:
        if req.interface and req.interface.example:
            example_output = str(req.interface.example.get('output', ''))
            if example_output and example_output in content:
                print(f"  ✅ {req.id}: Expected output found")
                has_expected_outputs = True
            elif example_output:
                print(f"  ❌ {req.id}: Expected output NOT found")
                print(f"     Expected: {example_output}")
    
    if not has_expected_outputs:
        print("  ⚠️ No expected outputs found in documentation examples")
        print("  💡 This is what we're trying to fix with the enhanced prompt!")


# %% [markdown]
# ## 🔍 Step 1.9: Interactive File Explorer

# %%
# Interactive file viewer for Stage 1 output
def view_stage1_file(file_path):
    """View any Stage 1 generated file"""
    full_path = STAGE1_OUTPUT / file_path
    if full_path.exists():
        print(f"📄 Viewing: {file_path}")
        print("=" * 60)
        with open(full_path, 'r') as f:
            content = f.read()
        print(content)
        
        # File stats
        stats = full_path.stat()
        print(f"\n📊 File Stats:")
        print(f"  Size: {stats.st_size:,} bytes")
        print(f"  Lines: {len(content.splitlines())}")
        print(f"  Modified: {datetime.fromtimestamp(stats.st_mtime)}")
    else:
        print(f"❌ File not found: {file_path}")

# List all available files
print("🔍 Interactive File Explorer:")
print("Use view_stage1_file('path/to/file') to examine any generated file")
print("\nAvailable files:")

if STAGE1_OUTPUT.exists():
    for file_path in sorted(STAGE1_OUTPUT.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(STAGE1_OUTPUT)
            print(f"  view_stage1_file('{rel_path}')")
else:
    print("  ❌ No files available")

# Example usage (uncomment to use):
# view_stage1_file('src/rhythmic_pulse_generator.py')
# view_stage1_file('tests/test_rhythmic_pulse_generator.py')
# view_stage1_file('docs/rhythmic_pulse_generator.md')

# %% [markdown]
# ## 🧪 Step 1.10: Run Generated Tests

# %%
# Try to run the generated tests to see if they work
import subprocess
import sys
import os

test_files = list(STAGE1_OUTPUT.rglob("test_*.py"))

if test_files:
    print("🧪 Running Generated Tests:")
    print("=" * 40)
    
    for test_file in test_files:
        rel_path = test_file.relative_to(STAGE1_OUTPUT)
        print(f"\n🔬 Testing: {rel_path}")
        print("-" * 30)
        
        # Change to the output directory to run tests
        original_cwd = Path.cwd().parent.parent
        try:
            # We need to run from the directory containing the source code
            test_dir = test_file.parent
            os.chdir(test_dir)
            
            # Run pytest
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file.name,
                "-v", "--tb=short", "--no-header"
            ], capture_output=True, text=True, timeout=30)
            
            print("STDOUT:")
            if result.stdout:
                print(result.stdout)
            else:
                print("(no output)")
            
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
            
            print(f"\nReturn code: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ Tests passed!")
            else:
                print("❌ Tests failed!")
                
        except subprocess.TimeoutExpired:
            print("⏰ Tests timed out (30s limit)")
        except Exception as e:
            print(f"💥 Error running tests: {e}")
        finally:
            os.chdir(original_cwd)
else:
    print("❌ No test files found")

# %% [markdown]
# ## 📊 Stage 1 Summary and Analysis

# %%
# Comprehensive Stage 1 analysis
print("📊 Stage 1 Summary: OpenSpec → Test/Scaffold")
print("=" * 60)

# Count files by type
src_files = list(STAGE1_OUTPUT.rglob("*.py"))
src_files = [f for f in src_files if "test_" not in f.name]
test_files = list(STAGE1_OUTPUT.rglob("test_*.py"))
doc_files = list(STAGE1_OUTPUT.rglob("*.md"))

print(f"📁 Generated Files:")
print(f"  Source files: {len(src_files)}")
print(f"  Test files: {len(test_files)}")
print(f"  Documentation files: {len(doc_files)}")
print(f"  Total files: {len(src_files) + len(test_files) + len(doc_files)}")

# Analyze requirements coverage
print(f"\n🎯 Requirements Coverage:")
print(f"  Spec requirements: {len(spec.requirements)}")

if src_files:
    total_functions = 0
    for src_file in src_files:
        with open(src_file, 'r') as f:
            content = f.read()
        functions = [line for line in content.split('\n') if line.strip().startswith('def ')]
        total_functions += len(functions)
    print(f"  Generated functions: {total_functions}")

if test_files:
    total_tests = 0
    for test_file in test_files:
        with open(test_file, 'r') as f:
            content = f.read()
        tests = [line for line in content.split('\n') if line.strip().startswith('def test_')]
        total_tests += len(tests)
    print(f"  Generated tests: {total_tests}")

# Check for examples in documentation
if doc_files:
    docs_with_examples = 0
    for doc_file in doc_files:
        with open(doc_file, 'r') as f:
            content = f.read()
        if '```' in content:
            docs_with_examples += 1
    print(f"  Docs with code examples: {docs_with_examples}/{len(doc_files)}")

# Quality assessment
print(f"\n🔍 Quality Assessment:")

# Check if examples from spec are properly used
spec_examples_used = 0
total_spec_examples = 0
for req in spec.requirements:
    if req.interface and req.interface.example:
        total_spec_examples += 1
        example_str = str(req.interface.example)
        
        # Check if example appears in any generated file
        found_in_files = 0
        for file_list in [src_files, test_files, doc_files]:
            for file_path in file_list:
                with open(file_path, 'r') as f:
                    content = f.read()
                if example_str in content:
                    found_in_files += 1
                    break
        
        if found_in_files > 0:
            spec_examples_used += 1

print(f"  Spec examples used: {spec_examples_used}/{total_spec_examples}")
print(f"  Example usage rate: {spec_examples_used/total_spec_examples*100:.1f}%" if total_spec_examples > 0 else "  No examples in spec")

# Stage 1 success criteria
print(f"\n✅ Stage 1 Success Criteria:")
success_criteria = [
    (len(src_files) > 0, "Source code generated"),
    (len(test_files) > 0, "Tests generated"),
    (len(doc_files) > 0, "Documentation generated"),
    (spec_examples_used == total_spec_examples, "All spec examples used")
]

for criterion, description in success_criteria:
    status = "✅" if criterion else "❌"
    print(f"  {status} {description}")

all_passed = all(criterion for criterion, _ in success_criteria)
print(f"\n🏆 Stage 1 Overall: {'✅ SUCCESS' if all_passed else '⚠️ NEEDS IMPROVEMENT'}")

if not all_passed:
    print("\n💡 Recommendations:")
    if not spec_examples_used == total_spec_examples:
        print("  - Check prompt templates to ensure spec examples are used")
        print("  - Verify the enhanced documentation prompt is working")
    if len(doc_files) == 0:
        print("  - Check documentation generation in CodeGenerator")
    if len(test_files) == 0:
        print("  - Check test generation logic")


# %% [markdown]
# ## 🔄 Stage 1 Debug Tools

# %%
# Debug tools for Stage 1
def debug_prompt_usage():
    """Debug how spec examples are used in prompts"""
    print("🔍 Debugging Prompt Usage:")
    print("=" * 40)
    
    templates = PromptTemplates()
    
    # Check each prompt type
    prompts = {
        "Code": templates.get_code_generation_prompt(spec),
        "Test": templates.get_test_generation_prompt(spec),
        "Documentation": templates.get_documentation_prompt(spec)
    }
    
    for prompt_type, prompt in prompts.items():
        print(f"\n{prompt_type} Prompt:")
        print("-" * 20)
        
        # Check for spec examples in prompt
        examples_found = 0
        for req in spec.requirements:
            if req.interface and req.interface.example:
                example_str = str(req.interface.example)
                if example_str in prompt:
                    examples_found += 1
                    print(f"  ✅ Found example for {req.id}")
                else:
                    print(f"  ❌ Missing example for {req.id}")
        
        print(f"  Examples in prompt: {examples_found}/{total_spec_examples}")
        
        # Check for enhanced documentation instructions
        if prompt_type == "Documentation":
            if "expected output" in prompt.lower():
                print("  ✅ Enhanced documentation instructions found")
            else:
                print("  ❌ Enhanced documentation instructions MISSING")

def regenerate_stage1():
    """Regenerate Stage 1 output"""
    import shutil
    
    print("🔄 Regenerating Stage 1...")
    
    # Backup existing output
    if STAGE1_OUTPUT.exists():
        backup_dir = STAGE1_OUTPUT.parent / f"{STAGE1_OUTPUT.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(STAGE1_OUTPUT, backup_dir)
        print(f"  📦 Backed up to: {backup_dir}")
    
    # Recreate output directory
    STAGE1_OUTPUT.mkdir(exist_ok=True)
    
    # Regenerate
    result = generator.generate_from_spec(SPEC_FILE, STAGE1_OUTPUT)
    
    print(f"  ✅ Regeneration complete: {result.success}")
    return result

# Export debug functions
print("🔧 Debug Tools Available:")
print("  debug_prompt_usage() - Check how spec examples are used in prompts")
print("  regenerate_stage1() - Regenerate Stage 1 output")
print("  view_stage1_file(path) - View any generated file")

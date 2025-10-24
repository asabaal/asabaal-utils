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
# # 🚀 OpenSpec Pipeline Interactive Notebook
#
# This notebook runs the complete OpenSpec-to-Code pipeline step by step with full interactive control.
#
# ## Pipeline Stages:
# 1. **Stage 1**: OpenSpec → Test/Scaffold 
# 2. **Stage 2**: Test/Scaffold → Logical Requirements
# 3. **Stage 3**: Logical Requirements → Behavioral Alignment
# 4. **Stage 4**: Behavioral Alignment → Final Code
#
# Each stage shows inputs, outputs, and all generated content for full visibility.

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

# Add current directory to path for imports
sys.path.insert(0, str(Path.cwd()))

# Import pipeline components
try:
    from orchestrator import IntegrationOrchestrator
    from generator import CodeGenerator
    from spec_parser import SpecParser
    from ollama_client import OllamaClient
    from templates import PromptTemplates
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the spec_coder directory")

# Setup logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("✅ Setup complete!")

# %%
# Configuration
SPEC_FILE = Path("examples/rhythmic_pulse_generator.yml")
OUTPUT_DIR = Path("notebook_output")
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📁 Spec file: {SPEC_FILE}")
print(f"📁 Output directory: {OUTPUT_DIR}")
print(f"📁 Working directory: {Path.cwd()}")

# Verify spec file exists
if not SPEC_FILE.exists():
    print(f"❌ Spec file not found: {SPEC_FILE}")
    print("Available files in examples:")
    if Path("examples").exists():
        for f in Path("examples").glob("*.yml"):
            print(f"  - {f}")
else:
    print("✅ Spec file found!")

# %% [markdown]
# ## 🔍 Step 0: Examine the Input Specification

# %%
# Load and display the specification
with open(SPEC_FILE, 'r') as f:
    spec_content = f.read()

print("📋 Raw Specification Content:")
print("=" * 50)
print(spec_content)

# Parse as YAML to show structure
spec_data = yaml.safe_load(spec_content)
print("\n🏗️ Parsed Specification Structure:")
print("=" * 50)
print(json.dumps(spec_data, indent=2))

# %%
# Parse specification using SpecParser
parser = SpecParser()
parsed_spec = parser.parse_file(SPEC_FILE)

print(f"📝 Spec ID: {parsed_spec.spec_id}")
print(f"📝 Title: {parsed_spec.title}")
print(f"📝 Version: {parsed_spec.version}")
print(f"📝 Number of Requirements: {len(parsed_spec.requirements)}")

print("\n📋 Requirements Details:")
for i, req in enumerate(parsed_spec.requirements, 1):
    print(f"\n--- Requirement {i}: {req.id} ---")
    print(f"Title: {req.title}")
    print(f"Description: {req.description}")
    if req.interface:
        print(f"Function: {req.interface.function}")
        print(f"Parameters: {req.interface.parameters}")
        print(f"Returns: {req.interface.returns}")
        if req.interface.example:
            print(f"Example: {req.interface.example}")
    if req.validation:
        print(f"Validation: {req.validation}")

# %% [markdown]
# ## 🚀 Stage 1: OpenSpec → Test/Scaffold

# %%
# Initialize orchestrator for Stage 1
orchestrator = IntegrationOrchestrator(base_dir=Path.cwd())

print("🔧 Starting Stage 1: OpenSpec → Test/Scaffold")
print(f"📁 Input spec: {SPEC_FILE}")
print(f"📁 Output dir: {OUTPUT_DIR}")

# Run Stage 1
stage1_success = orchestrator._stage1_spec_to_scaffold(SPEC_FILE, OUTPUT_DIR)

if stage1_success:
    print("\n✅ Stage 1 completed successfully!")
else:
    print("\n❌ Stage 1 failed!")

# %%
# Examine Stage 1 outputs
print("📁 Stage 1 Generated Files:")
print("=" * 40)

scaffolds_dir = OUTPUT_DIR / "scaffolds"
if scaffolds_dir.exists():
    for file_path in scaffolds_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(OUTPUT_DIR)
            print(f"📄 {rel_path}")
else:
    print("❌ No scaffolds directory found")

# %%
# Display generated test file
test_file = scaffolds_dir / "src" / "test_rhythmic_pulse_generator.py"
if test_file.exists():
    print("🧪 Generated Test File:")
    print("=" * 40)
    with open(test_file, 'r') as f:
        test_content = f.read()
    print(test_content)
else:
    print(f"❌ Test file not found: {test_file}")

# %%
# Display generated documentation
doc_file = scaffolds_dir / "docs" / "rhythmic_pulse_generator.md"
if doc_file.exists():
    print("📚 Generated Documentation:")
    print("=" * 40)
    with open(doc_file, 'r') as f:
        doc_content = f.read()
    print(doc_content)
else:
    print(f"❌ Documentation file not found: {doc_file}")

# %%
# Display generated source code scaffold
src_file = scaffolds_dir / "src" / "rhythmic_pulse_generator.py"
if src_file.exists():
    print("💻 Generated Source Code Scaffold:")
    print("=" * 40)
    with open(src_file, 'r') as f:
        src_content = f.read()
    print(src_content)
else:
    print(f"❌ Source file not found: {src_file}")

# %% [markdown]
# ## 🧠 Stage 2: Test/Scaffold → Logical Requirements

# %%
# Run Stage 2
print("🧠 Starting Stage 2: Test/Scaffold → Logical Requirements")
print(f"📁 Input dir: {OUTPUT_DIR}")

stage2_success = orchestrator._stage2_scaffold_to_requirements(OUTPUT_DIR)

if stage2_success:
    print("\n✅ Stage 2 completed successfully!")
else:
    print("\n❌ Stage 2 failed!")

# %%
# Examine Stage 2 outputs
print("📁 Stage 2 Generated Files:")
print("=" * 40)

reports_dir = OUTPUT_DIR / "reports"
if reports_dir.exists():
    for file_path in reports_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(OUTPUT_DIR)
            print(f"📄 {rel_path}")
else:
    print("❌ No reports directory found")

# %%
# Display logical requirements analysis
requirements_file = reports_dir / "logical_requirements.json"
if requirements_file.exists():
    print("🧠 Logical Requirements Analysis:")
    print("=" * 40)
    with open(requirements_file, 'r') as f:
        req_data = json.load(f)
    print(json.dumps(req_data, indent=2))
else:
    print(f"❌ Requirements file not found: {requirements_file}")

# %%
# Display test analysis
test_analysis_file = reports_dir / "test_analysis.json"
if test_analysis_file.exists():
    print("🧪 Test Analysis:")
    print("=" * 40)
    with open(test_analysis_file, 'r') as f:
        test_data = json.load(f)
    print(json.dumps(test_data, indent=2))
else:
    print(f"❌ Test analysis file not found: {test_analysis_file}")

# %% [markdown]
# ## 🎯 Stage 3: Logical Requirements → Behavioral Alignment

# %%
# Run Stage 3
print("🎯 Starting Stage 3: Logical Requirements → Behavioral Alignment")
print(f"📁 Input dir: {OUTPUT_DIR}")

stage3_success = orchestrator._stage3_requirements_to_alignment(OUTPUT_DIR)

if stage3_success:
    print("\n✅ Stage 3 completed successfully!")
else:
    print("\n❌ Stage 3 failed!")

# %%
# Examine Stage 3 outputs
print("📁 Stage 3 Generated Files:")
print("=" * 40)

alignment_dir = OUTPUT_DIR / "alignment"
if alignment_dir.exists():
    for file_path in alignment_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(OUTPUT_DIR)
            print(f"📄 {rel_path}")
else:
    print("❌ No alignment directory found")

# %%
# Display behavioral alignment report
alignment_report = alignment_dir / "behavioral_alignment.json"
if alignment_report.exists():
    print("🎯 Behavioral Alignment Report:")
    print("=" * 40)
    with open(alignment_report, 'r') as f:
        alignment_data = json.load(f)
    print(json.dumps(alignment_data, indent=2))
else:
    print(f"❌ Alignment report not found: {alignment_report}")

# %%
# Display aligned tests
aligned_tests_file = alignment_dir / "aligned_tests.py"
if aligned_tests_file.exists():
    print("🧪 Aligned Tests:")
    print("=" * 40)
    with open(aligned_tests_file, 'r') as f:
        aligned_tests = f.read()
    print(aligned_tests)
else:
    print(f"❌ Aligned tests file not found: {aligned_tests_file}")

# %% [markdown]
# ## ⚡ Stage 4: Behavioral Alignment → Final Code

# %%
# Run Stage 4 (dry run first to check setup)
print("⚡ Starting Stage 4: Behavioral Alignment → Final Code")
print(f"📁 Input dir: {OUTPUT_DIR}")
print("🔍 Running in dry-run mode first...")

stage4_dry_success = orchestrator._stage4_alignment_to_code(OUTPUT_DIR, dry_run=True)

if stage4_dry_success:
    print("\n✅ Stage 4 dry-run successful! Ready for full execution.")
    
    # Ask for confirmation before full run
    print("\n🚀 Running full Stage 4...")
    stage4_success = orchestrator._stage4_alignment_to_code(OUTPUT_DIR, dry_run=False)
    
    if stage4_success:
        print("\n✅ Stage 4 completed successfully!")
    else:
        print("\n❌ Stage 4 failed!")
else:
    print("\n❌ Stage 4 dry-run failed!")

# %%
# Examine Stage 4 final outputs
print("📁 Stage 4 Final Generated Files:")
print("=" * 40)

final_dir = OUTPUT_DIR / "final"
if final_dir.exists():
    for file_path in final_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(OUTPUT_DIR)
            print(f"📄 {rel_path}")
else:
    print("❌ No final directory found")

# %%
# Display final implementation
final_impl_file = final_dir / "rhythmic_pulse_generator.py"
if final_impl_file.exists():
    print("💻 Final Implementation:")
    print("=" * 40)
    with open(final_impl_file, 'r') as f:
        final_impl = f.read()
    print(final_impl)
else:
    print(f"❌ Final implementation file not found: {final_impl_file}")

# %%
# Display final tests
final_tests_file = final_dir / "test_rhythmic_pulse_generator.py"
if final_tests_file.exists():
    print("🧪 Final Tests:")
    print("=" * 40)
    with open(final_tests_file, 'r') as f:
        final_tests = f.read()
    print(final_tests)
else:
    print(f"❌ Final tests file not found: {final_tests_file}")

# %%
# Display final documentation
final_doc_file = final_dir / "rhythmic_pulse_generator.md"
if final_doc_file.exists():
    print("📚 Final Documentation:")
    print("=" * 40)
    with open(final_doc_file, 'r') as f:
        final_doc = f.read()
    print(final_doc)
else:
    print(f"❌ Final documentation file not found: {final_doc_file}")

# %% [markdown]
# ## 🧪 Test the Final Implementation

# %%
# Run the final tests
import subprocess
import sys

if final_tests_file and final_tests_file.exists():
    print("🧪 Running Final Tests:")
    print("=" * 40)
    
    # Change to final directory and run tests
    original_cwd = Path.cwd()
    try:
        os.chdir(final_dir.parent)
        
        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(final_tests_file.relative_to(final_dir.parent)),
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"\nReturn code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
    finally:
        os.chdir(original_cwd)
else:
    print("❌ No final tests to run")

# %% [markdown]
# ## 📊 Pipeline Summary

# %%
# Display pipeline summary
print("📊 Pipeline Execution Summary")
print("=" * 50)

stages = [
    ("Stage 1: OpenSpec → Scaffold", stage1_success),
    ("Stage 2: Scaffold → Requirements", stage2_success),
    ("Stage 3: Requirements → Alignment", stage3_success),
    ("Stage 4: Alignment → Final Code", stage4_success if 'stage4_success' in locals() else False)
]

for stage_name, success in stages:
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{stage_name}: {status}")

# Count total files generated
total_files = 0
if OUTPUT_DIR.exists():
    total_files = len(list(OUTPUT_DIR.rglob("*")))
    total_files = len([f for f in OUTPUT_DIR.rglob("*") if f.is_file()])

print(f"\n📁 Total files generated: {total_files}")
print(f"📁 Output directory: {OUTPUT_DIR}")

# Show directory structure
print("\n📂 Generated Directory Structure:")
if OUTPUT_DIR.exists():
    for item in OUTPUT_DIR.rglob("*"):
        if item.is_dir():
            rel_path = item.relative_to(OUTPUT_DIR)
            print(f"📁 {rel_path}/")
        elif item.is_file():
            rel_path = item.relative_to(OUTPUT_DIR)
            print(f"📄 {rel_path}")


# %% [markdown]
# ## 🔍 Interactive Exploration
#
# You can now explore any of the generated files in detail. Use the cells below to examine specific aspects of the pipeline output.

# %%
# Interactive file viewer
def view_file(file_path):
    """View any generated file"""
    full_path = OUTPUT_DIR / file_path
    if full_path.exists():
        print(f"📄 Viewing: {file_path}")
        print("=" * 50)
        with open(full_path, 'r') as f:
            content = f.read()
        print(content)
    else:
        print(f"❌ File not found: {file_path}")

# Example usage:
# view_file("scaffolds/src/rhythmic_pulse_generator.py")
# view_file("final/rhythmic_pulse_generator.md")
# view_file("reports/logical_requirements.json")

print("🔍 Use view_file(path) to examine any generated file")
print("Example: view_file('final/rhythmic_pulse_generator.py')")

# %%
# List all available files for exploration
print("📋 All Generated Files (for view_file()):")
print("=" * 40)

if OUTPUT_DIR.exists():
    for file_path in sorted(OUTPUT_DIR.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(OUTPUT_DIR)
            print(f"view_file('{rel_path}')")
else:
    print("❌ No output directory found")

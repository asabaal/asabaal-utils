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
# # 🧠 Stage 2: Test/Scaffold → Logical Requirements
#
# ## Purpose
# Analyze the generated scaffold and tests to extract logical requirements and identify gaps.

# %%
# Setup
import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
sys.path.insert(0, str(current_dir.parent.parent.parent))

# %%
# Configuration
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
STAGE1_OUTPUT = current_dir / "stage1_output"
STAGE2_OUTPUT = current_dir / "stage2_output"
STAGE2_OUTPUT.mkdir(exist_ok=True)

# Configuration for compatibility with existing code
config = {
    'working_dir': str(STAGE1_OUTPUT),
    'spec_file': str(current_dir / "../rhythmic_pulse_generator.yml")
}

print(f"📁 Current directory: {current_dir}")
print(f"📁 Stage 1 input: {STAGE1_OUTPUT}")
print(f"📁 Stage 2 output: {STAGE2_OUTPUT}")

# %%
# Check Stage 1 output exists
if STAGE1_OUTPUT.exists():
    print("✅ Stage 1 output found")
    files = list(STAGE1_OUTPUT.rglob("*"))
    files = [f for f in files if f.is_file()]
    print(f"📄 Found {len(files)} files")
else:
    print("❌ Stage 1 output not found - run Stage 1 first!")

# %% [markdown]
# ## 📋 Step 2.1: Examine Stage 1 Generated Files

# %%
print("\n" + "="*80)
print("STAGE 2: SCAFFOLD TO REQUIREMENTS ANALYSIS")
print("="*80)
print("\n🎯 OBJECTIVE: Analyze scaffold code to extract requirements")
print("📁 Working Directory:", config['working_dir'])
print("📋 Spec File:", config['spec_file'])
print("\n🔄 Ready to analyze scaffold output from Stage 1...")

# %% [markdown]
# ## Step 2.1 List Scaffold Output Files

# %%
print("📂 Listing scaffold output files...")

# List all files in the working directory
scaffold_files = []
for root, dirs, files in os.walk(config['working_dir']):
    for file in files:
        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, config['working_dir'])
        scaffold_files.append(rel_path)

print(f"\n📋 Found {len(scaffold_files)} files:")
for i, file_path in enumerate(scaffold_files, 1):
    print(f"  {i:2d}. {file_path}")

print(f"\n✅ Scaffold files listed successfully")

# %% [markdown]
# ## Step 2.2 Analyze Source Code Structure

# %%
print("🔍 Analyzing source code structure...")

# Filter for Python source files
source_files = [f for f in scaffold_files if f.endswith('.py')]

print(f"\n🐍 Found {len(source_files)} Python source files:")
for file_path in source_files:
    print(f"\n📄 Analyzing: {file_path}")
    
    full_path = os.path.join(config['working_dir'], file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count lines
        lines = content.split('\n')
        print(f"   📏 Lines: {len(lines)}")
        
        # Find functions
        functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
        print(f"   🔧 Functions: {len(functions)} - {', '.join(functions[:5])}{'...' if len(functions) > 5 else ''}")
        
        # Find classes
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        print(f"   🏗️  Classes: {len(classes)} - {', '.join(classes)}")
        
        # Find imports
        imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+[^\n]+', content, re.MULTILINE)
        print(f"   📦 Imports: {len(imports)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n✅ Source code analysis completed")

# %% [markdown]
# ## Step 2.3 Analyze Test Files

# %%
print("🧪 Analyzing test files...")

# Filter for test files
test_files = [f for f in scaffold_files if 'test' in f.lower() and f.endswith('.py')]

print(f"\n🧪 Found {len(test_files)} test files:")
for file_path in test_files:
    print(f"\n📄 Analyzing: {file_path}")
    
    full_path = os.path.join(config['working_dir'], file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count lines
        lines = content.split('\n')
        print(f"   📏 Lines: {len(lines)}")
        
        # Find test functions
        test_functions = re.findall(r'^def\s+(test_\w+)\s*\(', content, re.MULTILINE)
        print(f"   🧪 Test Functions: {len(test_functions)} - {', '.join(test_functions)}")
        
        # Find assertions
        assertions = re.findall(r'assert\s+', content)
        print(f"   ✅ Assertions: {len(assertions)}")
        
        # Find test imports
        test_imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+(?:unittest|pytest|test)', content, re.MULTILINE)
        print(f"   📦 Test Imports: {len(test_imports)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n✅ Test analysis completed")

# %% [markdown]
# ## Step 2.4 Analyze Documentation Files

# %%
print("📚 Analyzing documentation files...")

# Filter for documentation files
doc_files = [f for f in scaffold_files if any(f.endswith(ext) for ext in ['.md', '.rst', '.txt', '.doc'])]

print(f"\n📚 Found {len(doc_files)} documentation files:")
for file_path in doc_files:
    print(f"\n📄 Analyzing: {file_path}")
    
    full_path = os.path.join(config['working_dir'], file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count lines and words
        lines = content.split('\n')
        words = content.split()
        print(f"   📏 Lines: {len(lines)}, Words: {len(words)}")
        
        # Find sections (markdown headers)
        if file_path.endswith('.md'):
            sections = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            print(f"   📑 Sections: {len(sections)} - {', '.join(sections[:3])}{'...' if len(sections) > 3 else ''}")
        
        # Find TODO/FIXME comments
        todos = re.findall(r'(?i)(?:TODO|FIXME|XXX):\s*(.+)', content)
        print(f"   📝 TODOs: {len(todos)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n✅ Documentation analysis completed")

# %% [markdown]
# ## Step 2.5 Extract Logical Requirements

# %%
print("🧠 Extracting logical requirements from scaffold...")

requirements = {
    'functional': [],
    'technical': [],
    'testing': [],
    'documentation': []
}

# Analyze all Python files for requirements
for file_path in source_files:
    full_path = os.path.join(config['working_dir'], file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract functional requirements from function names and docstrings
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):\s*"""([^"""]*(?:"""[^"""]*)*?)"""', content, re.DOTALL)
        for func_name, docstring in functions:
            if docstring.strip():
                requirements['functional'].append(f"Function '{func_name}': {docstring.strip()}")
        
        # Extract technical requirements from imports and class definitions
        imports = re.findall(r'import\s+(\S+)', content)
        for imp in imports:
            requirements['technical'].append(f"Dependency: {imp}")
            
        classes = re.findall(r'class\s+(\w+).*?:\s*"""([^"""]*(?:"""[^"""]*)*?)"""', content, re.DOTALL)
        for class_name, docstring in classes:
            if docstring.strip():
                requirements['technical'].append(f"Class '{class_name}': {docstring.strip()}")
        
    except Exception as e:
        print(f"   ❌ Error analyzing {file_path}: {e}")

# Analyze test files for testing requirements
for file_path in test_files:
    full_path = os.path.join(config['working_dir'], file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        test_functions = re.findall(r'def\s+(test_\w+)\s*\(', content)
        for test_func in test_functions:
            requirements['testing'].append(f"Test case: {test_func}")
            
    except Exception as e:
        print(f"   ❌ Error analyzing {file_path}: {e}")

print(f"\n📋 Requirements Summary:")
for category, items in requirements.items():
    print(f"   {category.title()}: {len(items)} items")
    for item in items[:3]:  # Show first 3 items
        print(f"     - {item[:80]}{'...' if len(item) > 80 else ''}")
    if len(items) > 3:
        print(f"     ... and {len(items) - 3} more")

print(f"\n✅ Requirements extraction completed")

# %% [markdown]
# ## Step 2.6 Identify Gaps and Missing Elements

# %%
print("🔍 Identifying gaps and missing elements...")

gaps = []

# Check for common missing elements
if not any('README' in f.upper() for f in scaffold_files):
    gaps.append("Missing README.md file")

if not any('requirements.txt' in f or 'pyproject.toml' in f or 'setup.py' in f for f in scaffold_files):
    gaps.append("Missing dependency specification file (requirements.txt, pyproject.toml, or setup.py)")

if not test_files:
    gaps.append("No test files found")

if not doc_files:
    gaps.append("No documentation files found")

# Check for error handling in source files
error_handling_patterns = [r'try:', r'except', r'raise', r'Exception']
has_error_handling = False

for file_path in source_files:
    full_path = os.path.join(config['working_dir'], file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for pattern in error_handling_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                has_error_handling = True
                break
        
        if has_error_handling:
            break
            
    except Exception:
        pass

if not has_error_handling:
    gaps.append("Limited or no error handling in source code")

# Check for logging
logging_patterns = [r'import logging', r'print\(', r'log\.']
has_logging = False

for file_path in source_files:
    full_path = os.path.join(config['working_dir'], file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for pattern in logging_patterns:
            if re.search(pattern, content):
                has_logging = True
                break
        
        if has_logging:
            break
            
    except Exception:
        pass

if not has_logging:
    gaps.append("No logging mechanism found")

print(f"\n⚠️  Identified {len(gaps)} potential gaps:")
for i, gap in enumerate(gaps, 1):
    print(f"   {i}. {gap}")

# %% [markdown]
# ## Step 2.7 Generate Requirements Report

# %%
print("📊 Generating comprehensive requirements report...")

# Create requirements report
report = []
report.append("# SCAFFOLD TO REQUIREMENTS ANALYSIS REPORT")
report.append("=" * 50)
report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"Working Directory: {config['working_dir']}")
report.append(f"Spec File: {config['spec_file']}")
report.append("")

report.append("## FILE SUMMARY")
report.append("-" * 20)
report.append(f"Total Files: {len(scaffold_files)}")
report.append(f"Source Files: {len(source_files)}")
report.append(f"Test Files: {len(test_files)}")
report.append(f"Documentation Files: {len(doc_files)}")
report.append("")

report.append("## FUNCTIONAL REQUIREMENTS")
report.append("-" * 30)
for i, req in enumerate(requirements['functional'], 1):
    report.append(f"{i}. {req}")
report.append("")

report.append("## TECHNICAL REQUIREMENTS")
report.append("-" * 30)
for i, req in enumerate(requirements['technical'], 1):
    report.append(f"{i}. {req}")
report.append("")

report.append("## TESTING REQUIREMENTS")
report.append("-" * 30)
for i, req in enumerate(requirements['testing'], 1):
    report.append(f"{i}. {req}")
report.append("")

report.append("## DOCUMENTATION REQUIREMENTS")
report.append("-" * 30)
for i, req in enumerate(requirements['documentation'], 1):
    report.append(f"{i}. {req}")
report.append("")

if gaps:
    report.append("## IDENTIFIED GAPS")
    report.append("-" * 20)
    for i, gap in enumerate(gaps, 1):
        report.append(f"{i}. {gap}")
    report.append("")

report.append("## RECOMMENDATIONS")
report.append("-" * 25)
recommendations = []

if not any('README' in f.upper() for f in scaffold_files):
    recommendations.append("Create a comprehensive README.md with usage examples")

if not test_files:
    recommendations.append("Add unit tests to ensure code reliability")

if not doc_files:
    recommendations.append("Add documentation to improve code maintainability")

if not has_error_handling:
    recommendations.append("Implement proper error handling in source code")

if not has_logging:
    recommendations.append("Add logging mechanism for debugging and monitoring")

for i, rec in enumerate(recommendations, 1):
    report.append(f"{i}. {rec}")

# Save requirements report
report_content = "\n".join(report)
requirements_report_file = os.path.join(STAGE2_OUTPUT, 'requirements_report.md')

with open(requirements_report_file, 'w', encoding='utf-8') as f:
    f.write(report_content)

print(f"\n📄 Requirements report saved to: {requirements_report_file}")
print(f"📊 Report contains {len(report)} lines")
print(f"\n📋 Analysis Summary:")
print(f"   - Total files analyzed: {len(scaffold_files)}")
print(f"   - Functional requirements: {len(requirements['functional'])}")
print(f"   - Technical requirements: {len(requirements['technical'])}")
print(f"   - Testing requirements: {len(requirements['testing'])}")
print(f"   - Identified gaps: {len(gaps)}")
print(f"   - Recommendations: {len(recommendations)}")

print(f"\n✅ Stage 2 requirements analysis completed successfully!")
print(f"🎯 Ready for Stage 3: Requirements to Alignment Analysis")

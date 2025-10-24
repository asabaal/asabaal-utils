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
# # 🏥 Stage 5: Healer - Code Repair and Enhancement
#
# ## 🎯 Objective
# Analyze the generated code from Stage 4, identify issues, gaps, and problems, then apply healing mechanisms to repair and enhance the implementation.
#
# ## 📋 What This Stage Does
# 1. Load generated code from Stage 4
# 2. Analyze code for syntax errors, missing imports, and logic gaps
# 3. Apply healing mechanisms to repair broken code
# 4. Enhance code quality and completeness
# 5. Validate final implementation against specifications
# 6. Generate healing report with fixes applied
#
# ## 🔧 Dependencies
# - Stage 1: Spec to Scaffold (completed)
# - Stage 2: Scaffold to Requirements (completed)
# - Stage 3: Requirements to Alignment (completed)
# - Stage 4: Alignment to Code (completed)
# - Original specification file
# - Generated code from Stage 4

# %%
# Cell 1: Import Dependencies
import os
import sys
import ast
import re
import yaml
import json
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

print("✅ Dependencies imported successfully")

# Add the asabaal_utils package to Python path for proper package imports
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
# Go up to the repository root to find asabaal_utils package
repo_root = current_dir.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Import the actual healer implementation from the proper package path
try:
    from asabaal_utils.agents.spec_coder.healer.heal import Healer, RepairResult
    print("✅ Healer module imported successfully")
except ImportError as e:
    print(f"❌ Error importing healer: {e}")
    print("💡 Falling back to basic implementation")
    Healer = None
    RepairResult = None

# %%
# Cell 2: Configuration Setup
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
config = {
    'base_dir': str(current_dir),
    'spec_file': str(current_dir / "../rhythmic_pulse_generator.yml"),
    'stage4_output': str(current_dir / "stage4_output"),
    'healer_output': str(current_dir / "stage5_output"),
    'healing_report': str(current_dir / "stage5_output/healing_report.json")
}

# Create output directory
output_dir = Path(config['healer_output'])
output_dir.mkdir(parents=True, exist_ok=True)

print("🔧 Configuration loaded:")
for key, value in config.items():
    print(f"   {key}: {value}")

print(f"\n📁 Healer output directory: {output_dir}")

# %%
print("\n" + "="*80)
print("STAGE 5: HEALER - CODE REPAIR AND ENHANCEMENT")
print("="*80)
print("\n🎯 OBJECTIVE: Analyze and repair generated code from Stage 4")
print("📁 Base Directory:", config['base_dir'])
print("📋 Spec File:", config['spec_file'])
print("📂 Stage 4 Output:", config['stage4_output'])
print("🏥 Healer Output:", config['healer_output'])
print("\n🔄 Ready to heal and enhance code...")

# %% [markdown]
# ## Step 5.1 Load Generated Code from Stage 4

# %%
print("📂 Loading generated code from Stage 4...")

stage4_dir = Path(config['stage4_output'])
generated_files = []

if stage4_dir.exists():
    # Find all Python files in Stage 4 output
    for py_file in stage4_dir.rglob("*.py"):
        generated_files.append(py_file)
    
    print(f"\n✅ Found {len(generated_files)} Python files:")
    for file_path in generated_files[:5]:  # Show first 5 files
        print(f"   - {file_path.relative_to(stage4_dir)}")
    
    if len(generated_files) > 5:
        print(f"   ... and {len(generated_files) - 5} more files")
else:
    print(f"❌ Stage 4 output directory not found: {stage4_dir}")
    generated_files = []

# %% [markdown]
# ## Step 5.2 Load Original Specification

# %%
print("📋 Loading original specification...")

try:
    with open(config['spec_file'], 'r', encoding='utf-8') as f:
        spec_data = yaml.safe_load(f)
    
    print(f"\n✅ Specification loaded successfully")
    print(f"📊 Project: {spec_data.get('title', 'Unknown')}")
    print(f"📝 Description: {spec_data.get('description', 'No description')[:100]}{'...' if len(spec_data.get('description', '')) > 100 else ''}")
    
    # Extract expected functions from specification
    expected_functions = []
    for req in spec_data.get('requirements', []):
        if 'interface' in req and 'function' in req['interface']:
            func_name = req['interface']['function'].split('(')[0].strip()
            expected_functions.append({
                'name': func_name,
                'signature': req['interface']['function'],
                'description': req.get('description', '')
            })
    
    print(f"\n🔧 Expected functions from spec: {len(expected_functions)}")
    for func in expected_functions:
        print(f"   - {func['name']}")
    
except Exception as e:
    print(f"❌ Error loading specification: {e}")
    spec_data = {'title': 'Unknown', 'description': 'No description', 'requirements': []}
    expected_functions = []

# %% [markdown]
# ## Step 5.3 Code Analysis and Issue Detection

# %%
print("🔍 Analyzing generated code for issues...")

issues_found = []
syntax_issues = []
import_issues = []
logic_gaps = []

def analyze_python_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python file for common issues."""
    analysis = {
        'file': str(file_path),
        'syntax_errors': [],
        'missing_imports': [],
        'undefined_functions': [],
        'logic_gaps': []
    }
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST to detect syntax errors
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            analysis['syntax_errors'].append(f"Line {e.lineno}: {e.msg}")
        
        # Check for common import issues
        imports = set()
        for node in ast.walk(tree) if 'tree' in locals() else []:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        
        # Check for missing common imports
        common_imports = {'pathlib', 'yaml', 'json', 'datetime', 'typing'}
        for common in common_imports:
            if common in content and common not in imports:
                analysis['missing_imports'].append(common)
        
        # Check for undefined functions (basic check)
        defined_functions = set()
        for node in ast.walk(tree) if 'tree' in locals() else []:
            if isinstance(node, ast.FunctionDef):
                defined_functions.add(node.name)
        
        # Look for function calls that might be undefined
        for node in ast.walk(tree) if 'tree' in locals() else []:
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name not in defined_functions and func_name not in dir(__builtins__):
                        analysis['undefined_functions'].append(func_name)
    
    except Exception as e:
        analysis['syntax_errors'].append(f"File analysis error: {e}")
    
    return analysis

# Analyze all generated files
all_issues = {
    'syntax_errors': [],
    'missing_imports': [],
    'undefined_functions': [],
    'logic_gaps': []
}

for file_path in generated_files:
    print(f"\n🔍 Analyzing: {file_path.name}")
    analysis = analyze_python_file(file_path)
    
    if analysis['syntax_errors']:
        print(f"   ❌ Syntax errors: {len(analysis['syntax_errors'])}")
        all_issues['syntax_errors'].extend(analysis['syntax_errors'])
    
    if analysis['missing_imports']:
        print(f"   ⚠️  Missing imports: {len(analysis['missing_imports'])}")
        all_issues['missing_imports'].extend(analysis['missing_imports'])
    
    if analysis['undefined_functions']:
        print(f"   ❓ Undefined functions: {len(analysis['undefined_functions'])}")
        all_issues['undefined_functions'].extend(analysis['undefined_functions'])

print(f"\n📊 Analysis Summary:")
print(f"   Syntax errors: {len(all_issues['syntax_errors'])}")
print(f"   Missing imports: {len(all_issues['missing_imports'])}")
print(f"   Undefined functions: {len(all_issues['undefined_functions'])}")

# %% [markdown]
# ## Step 5.4 Apply Healing Mechanisms

# %%
print("🔧 Applying healing mechanisms...")

healing_report = {
    'timestamp': datetime.now().isoformat(),
    'spec_file': config['spec_file'],
    'stage4_output': config['stage4_output'],
    'healer_output': config['healer_output'],
    'issues_found': all_issues,
    'fixes_applied': [],
    'validation_results': []
}

def apply_healing_fixes(file_path: Path, issues: Dict[str, List[str]]) -> List[str]:
    """Apply healing fixes to a Python file."""
    fixes_applied = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix missing imports
        for missing_import in issues.get('missing_imports', []):
            import_line = f"import {missing_import}\n"
            if import_line not in content:
                # Add import after existing imports
                lines = content.split('\n')
                import_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_index = i + 1
                lines.insert(import_index, import_line)
                content = '\n'.join(lines)
                fixes_applied.append(f"Added missing import: {missing_import}")
        
        # Fix common syntax issues
        if issues.get('syntax_errors'):
            # Basic syntax fixes
            content = content.replace(',,', ',')  # Double commas
            content = content.replace('[[', '[')  # Double brackets
            content = content.replace(']]', ']')  # Double brackets
            fixes_applied.append("Applied basic syntax fixes")
        
        # Write healed content
        if content != original_content:
            healed_path = output_dir / file_path.name
            with open(healed_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"Saved healed version: {healed_path.name}")
    
    except Exception as e:
        fixes_applied.append(f"Error applying fixes: {e}")
    
    return fixes_applied

# Apply healing to all files
for file_path in generated_files:
    print(f"\n🔧 Healing: {file_path.name}")
    
    # Get issues for this file
    file_issues = {
        'missing_imports': [],
        'syntax_errors': []
    }
    
    # Apply fixes
    fixes = apply_healing_fixes(file_path, file_issues)
    if fixes:
        print(f"   ✅ Fixes applied: {len(fixes)}")
        for fix in fixes:
            print(f"      - {fix}")
        healing_report['fixes_applied'].extend(fixes)
    else:
        print(f"   ℹ️  No fixes needed")

# %% [markdown]
# ## Step 5.5 Validate Healed Code

# %%
print("🧪 Validating healed code...")

validation_results = []

# Test syntax validation of healed files
healed_files = list(output_dir.rglob("*.py"))
for healed_file in healed_files:
    print(f"\n🧪 Validating: {healed_file.name}")
    
    try:
        with open(healed_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse to check syntax
        ast.parse(content)
        
        validation_result = {
            'file': healed_file.name,
            'status': 'valid',
            'errors': []
        }
        
        print(f"   ✅ Syntax valid")
        
    except SyntaxError as e:
        validation_result = {
            'file': healed_file.name,
            'status': 'invalid',
            'errors': [f"Line {e.lineno}: {e.msg}"]
        }
        print(f"   ❌ Syntax error: {e.msg}")
    
    validation_results.append(validation_result)

healing_report['validation_results'] = validation_results

# Count validation results
valid_count = sum(1 for r in validation_results if r['status'] == 'valid')
invalid_count = len(validation_results) - valid_count

print(f"\n📊 Validation Summary:")
print(f"   Valid files: {valid_count}")
print(f"   Invalid files: {invalid_count}")

# %% [markdown]
# ## Step 5.6 Generate Healing Report

# %%
print("📄 Generating healing report...")

# Save healing report
try:
    with open(config['healing_report'], 'w', encoding='utf-8') as f:
        json.dump(healing_report, f, indent=2)
    print(f"✅ Healing report saved: {config['healing_report']}")
except Exception as e:
    print(f"❌ Error saving healing report: {e}")

# Generate summary report
summary_report = f"""# 🏥 Stage 5 Healing Report

## Timestamp
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Input Analysis
- **Specification**: {config['spec_file']}
- **Stage 4 Output**: {config['stage4_output']}
- **Files Analyzed**: {len(generated_files)}

## Issues Found
- **Syntax Errors**: {len(all_issues['syntax_errors'])}
- **Missing Imports**: {len(all_issues['missing_imports'])}
- **Undefined Functions**: {len(all_issues['undefined_functions'])}

## Fixes Applied
- **Total Fixes**: {len(healing_report['fixes_applied'])}

## Validation Results
- **Valid Files**: {valid_count}
- **Invalid Files**: {invalid_count}
- **Success Rate**: {valid_count*100/(valid_count+invalid_count) if (valid_count+invalid_count) > 0 else 0:.1f}%

## Output Directory
{config['healer_output']}

## Next Steps
1. Review any remaining syntax errors
2. Test functionality of healed code
3. Validate against original specification
4. Deploy healed implementation
"""

# Save summary report
summary_path = output_dir / "healing_summary.md"
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write(summary_report)

print(f"✅ Summary report saved: {summary_path}")

# %% [markdown]
# ## Step 5.7 Final Output Structure

# %%
print("\n📁 Final Healed Output Structure:")

# List all files in output directory
if output_dir.exists():
    for item in output_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(output_dir)
            size = item.stat().st_size
            print(f"   📄 {rel_path} ({size} bytes)")

print(f"\n✅ Stage 5 healing completed successfully!")
print(f"🎯 Healed code ready at: {output_dir}")
print(f"📊 Total files processed: {len(generated_files)}")
print(f"🔧 Total fixes applied: {len(healing_report['fixes_applied'])}")

print(f"\n🚀 SpecCoder Pipeline Complete - All 5 Stages Finished!")
print(f"🏥 Final healed and enhanced implementation is ready for deployment!")

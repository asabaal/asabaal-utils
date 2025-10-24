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
# # 📊 Stage 3: Requirements to Alignment Analysis
#
# ## 🎯 Objective
# Compare extracted requirements against original specification to identify alignment gaps and inconsistencies.
#
# ## 📋 What This Stage Does
# 1. Load original specification
# 2. Load requirements from Stage 2
# 3. Compare spec vs requirements
# 4. Identify alignment gaps
# 5. Generate alignment report
#
# ## 🔧 Dependencies
# - Stage 1: Spec to Scaffold (completed)
# - Stage 2: Scaffold to Requirements (completed)
# - Original specification file

# %%
# Cell 1: Import Dependencies
import os
import re
import yaml
import json
from datetime import datetime
from pathlib import Path

print("✅ Dependencies imported successfully")

# %%
# Cell 2: Configuration Setup
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
config = {
    'working_dir': str(current_dir / "stage1_output"),
    'spec_file': str(current_dir / "../rhythmic_pulse_generator.yml"),
    'requirements_report': str(current_dir / "stage2_output/requirements_report.md")
}

print("🔧 Configuration loaded:")
for key, value in config.items():
    print(f"   {key}: {value}")

# Verify paths exist
spec_path = Path(config['spec_file'])
if spec_path.exists():
    print(f"\n✅ Spec file found: {spec_path}")
else:
    print(f"\n❌ Spec file not found: {spec_path}")

# %%
print("\n" + "="*80)
print("STAGE 3: REQUIREMENTS TO ALIGNMENT ANALYSIS")
print("="*80)
print("\n🎯 OBJECTIVE: Compare requirements against original specification")
print("📁 Working Directory:", config['working_dir'])
print("📋 Spec File:", config['spec_file'])
print("📄 Requirements Report:", config['requirements_report'])
print("\n🔄 Ready to analyze alignment...")

# %% [markdown]
# ## Step 3.1 Load Original Specification

# %%
print("📋 Loading original specification...")

try:
    with open(config['spec_file'], 'r', encoding='utf-8') as f:
        spec_content = f.read()
    
    # Parse YAML specification
    spec_data = yaml.safe_load(spec_content)
    
    print(f"\n✅ Specification loaded successfully")
    print(f"📊 Spec keys: {list(spec_data.keys())}")
    
    # Extract key specification elements
    spec_elements = {
        'name': spec_data.get('name', 'Unknown'),
        'description': spec_data.get('description', ''),
        'functions': spec_data.get('functions', []),
        'classes': spec_data.get('classes', []),
        'dependencies': spec_data.get('dependencies', []),
        'tests': spec_data.get('tests', [])
    }
    
    print(f"\n📋 Specification Summary:")
    print(f"   Name: {spec_elements['name']}")
    print(f"   Description: {spec_elements['description'][:100]}{'...' if len(spec_elements['description']) > 100 else ''}")
    print(f"   Functions: {len(spec_elements['functions'])}")
    print(f"   Classes: {len(spec_elements['classes'])}")
    print(f"   Dependencies: {len(spec_elements['dependencies'])}")
    print(f"   Tests: {len(spec_elements['tests'])}")
    
except Exception as e:
    print(f"❌ Error loading specification: {e}")
    spec_data = {}
    spec_elements = {}

# %% [markdown]
# ## Step 3.2 Load Requirements from Stage 2

# %% [markdown]
# ## Step 3.3 Compare Specification vs RequirementsNow we'll compare the original specification with the extracted requirements to identify:- Missing requirements that weren't captured in the scaffold- Incorrect interpretations that need correction- Additional requirements implied by the implementationThis comparison ensures our final implementation stays true to the original intent.

# %%
print("📄 Loading requirements report from Stage 2...")

try:
    with open(config['requirements_report'], 'r', encoding='utf-8') as f:
        requirements_content = f.read()
    
    print(f"\n✅ Requirements report loaded successfully")
    print(f"📊 Report size: {len(requirements_content)} characters")
    
    # Parse requirements from report
    requirements = {
        'functional': [],
        'technical': [],
        'testing': [],
        'documentation': []
    }
    
    lines = requirements_content.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('## FUNCTIONAL REQUIREMENTS'):
            current_section = 'functional'
        elif line.startswith('## TECHNICAL REQUIREMENTS'):
            current_section = 'technical'
        elif line.startswith('## TESTING REQUIREMENTS'):
            current_section = 'testing'
        elif line.startswith('## DOCUMENTATION REQUIREMENTS'):
            current_section = 'documentation'
        elif current_section and line.startswith(tuple(str(i) + '.' for i in range(1, 100))):
            # This is a requirement item
            req_text = line[line.find('.') + 1:].strip()
            if req_text:
                requirements[current_section].append(req_text)
    
    print(f"\n📋 Parsed Requirements:")
    for category, items in requirements.items():
        print(f"   {category.title()}: {len(items)} items")
    
except Exception as e:
    print(f"❌ Error loading requirements report: {e}")
    requirements = {
        'functional': [],
        'technical': [],
        'testing': [],
        'documentation': []
    }

    # %%
    # Extract key specification elements from OpenSpec format
    spec_elements = {
        'spec_id': spec_data.get('spec_id', 'Unknown'),
        'title': spec_data.get('title', 'Unknown'),
        'description': spec_data.get('description', ''),
        'functions': [],
        'classes': [],
        'dependencies': [],
        'tests': []
    }
    
    # Extract functions from requirements
    for req in spec_data.get('requirements', []):
        if 'interface' in req and 'function' in req['interface']:
            func_name = req['interface']['function'].split('(')[0].strip()
            spec_elements['functions'].append(func_name)
    
    print(f"\n📋 Specification Summary:")
    print(f"   ID: {spec_elements['spec_id']}")
    print(f"   Title: {spec_elements['title']}")
    print(f"   Description: {spec_elements['description'][:100]}{'...' if len(spec_elements['description']) > 100 else ''}")
    print(f"   Functions: {len(spec_elements['functions'])}")
    print(f"   Classes: {len(spec_elements['classes'])}")
    print(f"   Dependencies: {len(spec_elements['dependencies'])}")
    print(f"   Tests: {len(spec_elements['tests'])}")
    
    print(f"\n🔧 Extracted Functions: {spec_elements['functions']}")

# %%
print("🔍 Comparing specification against requirements...")

alignment_analysis = {
    'matched_functions': [],
    'missing_functions': [],
    'extra_functions': [],
    'matched_classes': [],
    'missing_classes': [],
    'extra_classes': [],
    'matched_dependencies': [],
    'missing_dependencies': [],
    'extra_dependencies': []
}

# Extract function names from requirements
req_functions = []
for req in requirements['functional']:
    # Look for function names in requirements
    func_match = re.search(r"Function '([^']+)'", req)
    if func_match:
        req_functions.append(func_match.group(1))

# Compare functions
spec_functions = [func.get('name', '') for func in spec_elements.get('functions', []) if isinstance(func, dict)]
if isinstance(spec_elements.get('functions'), list):
    spec_functions = [f if isinstance(f, str) else f.get('name', '') for f in spec_elements['functions']]

print(f"\n🔧 Function Comparison:")
print(f"   Spec functions: {spec_functions}")
print(f"   Req functions: {req_functions}")

for func in spec_functions:
    if func in req_functions:
        alignment_analysis['matched_functions'].append(func)
    else:
        alignment_analysis['missing_functions'].append(func)

for func in req_functions:
    if func not in spec_functions:
        alignment_analysis['extra_functions'].append(func)

# Compare classes
req_classes = []
for req in requirements['technical']:
    class_match = re.search(r"Class '([^']+)'", req)
    if class_match:
        req_classes.append(class_match.group(1))

spec_classes = spec_elements.get('classes', [])
if isinstance(spec_elements.get('classes'), list):
    spec_classes = [c if isinstance(c, str) else c.get('name', '') for c in spec_elements['classes']]

print(f"\n🏗️  Class Comparison:")
print(f"   Spec classes: {spec_classes}")
print(f"   Req classes: {req_classes}")

for cls in spec_classes:
    if cls in req_classes:
        alignment_analysis['matched_classes'].append(cls)
    else:
        alignment_analysis['missing_classes'].append(cls)

for cls in req_classes:
    if cls not in spec_classes:
        alignment_analysis['extra_classes'].append(cls)

# Compare dependencies
req_dependencies = []
for req in requirements['technical']:
    dep_match = re.search(r"Dependency: ([^\s]+)", req)
    if dep_match:
        req_dependencies.append(dep_match.group(1))

spec_dependencies = spec_elements.get('dependencies', [])

print(f"\n📦 Dependency Comparison:")
print(f"   Spec dependencies: {spec_dependencies}")
print(f"   Req dependencies: {req_dependencies}")

for dep in spec_dependencies:
    if dep in req_dependencies:
        alignment_analysis['matched_dependencies'].append(dep)
    else:
        alignment_analysis['missing_dependencies'].append(dep)

for dep in req_dependencies:
    if dep not in spec_dependencies:
        alignment_analysis['extra_dependencies'].append(dep)

print(f"\n✅ Comparison completed")

# %% [markdown]
# ## Step 3.4 Identify Alignment Gaps

# %%
print("🚨 Identifying alignment gaps...")

gaps = []
alignment_score = 100

# Calculate alignment score and identify gaps
total_spec_items = len(spec_functions) + len(spec_classes) + len(spec_dependencies)
total_matched = (len(alignment_analysis['matched_functions']) + 
                len(alignment_analysis['matched_classes']) + 
                len(alignment_analysis['matched_dependencies']))

if total_spec_items > 0:
    alignment_score = (total_matched / total_spec_items) * 100

# Function gaps
if alignment_analysis['missing_functions']:
    gaps.append(f"Missing functions: {', '.join(alignment_analysis['missing_functions'])}")
    alignment_score -= len(alignment_analysis['missing_functions']) * 5

if alignment_analysis['extra_functions']:
    gaps.append(f"Extra functions not in spec: {', '.join(alignment_analysis['extra_functions'])}")
    alignment_score -= len(alignment_analysis['extra_functions']) * 2

# Class gaps
if alignment_analysis['missing_classes']:
    gaps.append(f"Missing classes: {', '.join(alignment_analysis['missing_classes'])}")
    alignment_score -= len(alignment_analysis['missing_classes']) * 5

if alignment_analysis['extra_classes']:
    gaps.append(f"Extra classes not in spec: {', '.join(alignment_analysis['extra_classes'])}")
    alignment_score -= len(alignment_analysis['extra_classes']) * 2

# Dependency gaps
if alignment_analysis['missing_dependencies']:
    gaps.append(f"Missing dependencies: {', '.join(alignment_analysis['missing_dependencies'])}")
    alignment_score -= len(alignment_analysis['missing_dependencies']) * 3

if alignment_analysis['extra_dependencies']:
    gaps.append(f"Extra dependencies not in spec: {', '.join(alignment_analysis['extra_dependencies'])}")
    alignment_score -= len(alignment_analysis['extra_dependencies']) * 1

# Ensure score doesn't go below 0
alignment_score = max(0, alignment_score)

print(f"\n📊 Alignment Score: {alignment_score:.1f}%")

if gaps:
    print(f"\n⚠️  Identified {len(gaps)} alignment gaps:")
    for i, gap in enumerate(gaps, 1):
        print(f"   {i}. {gap}")
else:
    print("\n✅ No alignment gaps identified - perfect alignment!")

# Determine alignment quality
if alignment_score >= 90:
    quality = "Excellent"
    emoji = "🟢"
elif alignment_score >= 75:
    quality = "Good"
    emoji = "🟡"
elif alignment_score >= 60:
    quality = "Fair"
    emoji = "🟠"
else:
    quality = "Poor"
    emoji = "🔴"

print(f"\n{emoji} Alignment Quality: {quality}")

# %% [markdown]
# ## Step 3.5 Generate Alignment Report

# %%
print("📊 Generating alignment analysis report...")

# Create alignment report
report = []
report.append("# REQUIREMENTS TO SPECIFICATION ALIGNMENT REPORT")
report.append("=" * 55)
report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"Working Directory: {config['working_dir']}")
report.append(f"Specification File: {config['spec_file']}")
report.append(f"Requirements Report: {config['requirements_report']}")
report.append("")

report.append("## ALIGNMENT SUMMARY")
report.append("-" * 25)
report.append(f"Overall Alignment Score: {alignment_score:.1f}%")
report.append(f"Alignment Quality: {quality} {emoji}")
report.append(f"Total Gaps Identified: {len(gaps)}")
report.append("")

report.append("## FUNCTION ALIGNMENT")
report.append("-" * 25)
report.append(f"Matched Functions: {len(alignment_analysis['matched_functions'])}")
if alignment_analysis['matched_functions']:
    for func in alignment_analysis['matched_functions']:
        report.append(f"  ✅ {func}")

report.append(f"Missing Functions: {len(alignment_analysis['missing_functions'])}")
if alignment_analysis['missing_functions']:
    for func in alignment_analysis['missing_functions']:
        report.append(f"  ❌ {func}")

report.append(f"Extra Functions: {len(alignment_analysis['extra_functions'])}")
if alignment_analysis['extra_functions']:
    for func in alignment_analysis['extra_functions']:
        report.append(f"  ⚠️  {func}")
report.append("")

report.append("## CLASS ALIGNMENT")
report.append("-" * 20)
report.append(f"Matched Classes: {len(alignment_analysis['matched_classes'])}")
if alignment_analysis['matched_classes']:
    for cls in alignment_analysis['matched_classes']:
        report.append(f"  ✅ {cls}")

report.append(f"Missing Classes: {len(alignment_analysis['missing_classes'])}")
if alignment_analysis['missing_classes']:
    for cls in alignment_analysis['missing_classes']:
        report.append(f"  ❌ {cls}")

report.append(f"Extra Classes: {len(alignment_analysis['extra_classes'])}")
if alignment_analysis['extra_classes']:
    for cls in alignment_analysis['extra_classes']:
        report.append(f"  ⚠️  {cls}")
report.append("")

report.append("## DEPENDENCY ALIGNMENT")
report.append("-" * 28)
report.append(f"Matched Dependencies: {len(alignment_analysis['matched_dependencies'])}")
if alignment_analysis['matched_dependencies']:
    for dep in alignment_analysis['matched_dependencies']:
        report.append(f"  ✅ {dep}")

report.append(f"Missing Dependencies: {len(alignment_analysis['missing_dependencies'])}")
if alignment_analysis['missing_dependencies']:
    for dep in alignment_analysis['missing_dependencies']:
        report.append(f"  ❌ {dep}")

report.append(f"Extra Dependencies: {len(alignment_analysis['extra_dependencies'])}")
if alignment_analysis['extra_dependencies']:
    for dep in alignment_analysis['extra_dependencies']:
        report.append(f"  ⚠️  {dep}")
report.append("")

if gaps:
    report.append("## ALIGNMENT GAPS")
    report.append("-" * 20)
    for i, gap in enumerate(gaps, 1):
        report.append(f"{i}. {gap}")
    report.append("")

report.append("## RECOMMENDATIONS")
report.append("-" * 20)
recommendations = []

if alignment_analysis['missing_functions']:
    recommendations.append(f"Implement missing functions: {', '.join(alignment_analysis['missing_functions'])}")

if alignment_analysis['missing_classes']:
    recommendations.append(f"Implement missing classes: {', '.join(alignment_analysis['missing_classes'])}")

if alignment_analysis['missing_dependencies']:
    recommendations.append(f"Add missing dependencies: {', '.join(alignment_analysis['missing_dependencies'])}")

if alignment_analysis['extra_functions']:
    recommendations.append(f"Review extra functions: {', '.join(alignment_analysis['extra_functions'])}")

if alignment_score < 75:
    recommendations.append("Significant alignment issues detected - consider reviewing the entire implementation")
elif alignment_score < 90:
    recommendations.append("Minor alignment issues - address gaps before proceeding to final implementation")
else:
    recommendations.append("Good alignment - ready for final implementation stage")

for i, rec in enumerate(recommendations, 1):
    report.append(f"{i}. {rec}")

# Save alignment report
report_content = "\n".join(report)
alignment_report_file = os.path.join(config['working_dir'], 'alignment_report.md')

with open(alignment_report_file, 'w', encoding='utf-8') as f:
    f.write(report_content)

print(f"\n📄 Alignment report saved to: {alignment_report_file}")
print(f"📊 Report contains {len(report)} lines")
print(f"\n📋 Alignment Summary:")
print(f"   - Alignment Score: {alignment_score:.1f}%")
print(f"   - Quality: {quality} {emoji}")
print(f"   - Total Gaps: {len(gaps)}")
print(f"   - Recommendations: {len(recommendations)}")

print(f"\n✅ Stage 3 alignment analysis completed successfully!")
print(f"🎯 Ready for Stage 4: Alignment to Code Implementation")

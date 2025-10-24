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
# # Module 7: Templates - Part 1
#
# ## 🎯 **Module Overview**
# This module documents the `templates.py` file - the prompt template system for the SpecCoder agent. The PromptTemplates class provides structured templates for generating different types of content from OpenSpec specifications.
#
# ## 📋 **What We'll Learn**
# - Template-based prompt engineering
# - Dataclass structure for template management
# - Source code scaffolding templates
# - Test generation templates
# - Documentation generation templates
# - System prompt configuration
#
# ## 🔧 **Key Components**
# - **PromptTemplates**: Dataclass containing all prompt templates
# - **source_code_prompt**: Template for generating Python scaffolding
# - **test_prompt**: Template for generating pytest tests
# - **documentation_prompt**: Template for generating markdown documentation
# - **system_prompt**: System-level instructions for AI behavior

# %%
# Cell 1: Setup and Dependencies
from dataclasses import dataclass
from typing import Dict, Any
import inspect

print("✅ Template system setup complete")
print(f"📦 Dataclass imported: {dataclass}")
print(f"🔍 Inspection tools ready")

# %%
# Cell 2: PromptTemplates Dataclass Structure
"""
Lines 10-13: PromptTemplates dataclass definition

The PromptTemplates class uses the @dataclass decorator to create a container
for all prompt templates used in the SpecCoder system. This provides a clean,
type-safe way to manage templates.
"""

@dataclass
class PromptTemplates:
    """Container for prompt templates used in code generation."""
    
    # Template fields will be added in subsequent cells
    pass

# Test the dataclass structure
print("🧪 Testing PromptTemplates dataclass:")

# Create an instance
templates = PromptTemplates()
print(f"📦 Templates instance: {templates}")
print(f"🏷️  Dataclass fields: {templates.__dataclass_fields__}")
print(f"🔍 Is dataclass: {templates.__class__.__dataclass_params__}")

# Check dataclass properties
print(f"\n📋 Dataclass properties:")
print(f"   - Frozen: {templates.__class__.__dataclass_params__.frozen}")
print(f"   - Init: {templates.__class__.__dataclass_params__.init}")
print(f"   - Repr: {templates.__class__.__dataclass_params__.repr}")
print(f"   - Order: {templates.__class__.__dataclass_params__.order}")
print(f"   - Eq: {templates.__class__.__dataclass_params__.eq}")

# %%
# Cell 3: Source Code Prompt Template
"""
Lines 14-30: Source code generation prompt template

The source_code_prompt template is used to generate Python scaffolding code
from OpenSpec specifications. It emphasizes exact function interface compliance
and proper code structure.
"""

source_code_prompt = """Generate Python scaffolding code using the EXACT function interfaces provided.

For specification {spec_id}, create a file with:
- Module docstring: "{title}\nVersion {version}"
- Import appropriate modules based on function requirements
- Function stubs with TODO comments and pass statements
- Use the EXACT function signatures provided below
- Single-line docstrings format: \"\"\"TODO {spec_id}: description.\"\"\"

FUNCTION INTERFACES (USE EXACTLY AS SPECIFIED):
{interfaces}

REQUIREMENTS:
{requirements}

IMPORTANT: Use the exact function names, parameter names, and types from the interfaces above.
Do not infer or modify the signatures - use them exactly as provided."""

# Test the source code template
print("🧪 Testing source code prompt template:")
print(f"📝 Template length: {len(source_code_prompt)} characters")
print(f"🔍 Placeholders: {[p for p in ['{spec_id}', '{title}', '{version}', '{interfaces}', '{requirements}'] if p in source_code_prompt]}")

# Test template formatting
test_data = {
    'spec_id': 'SPEC-001',
    'title': 'Test Specification',
    'version': '1.0.0',
    'interfaces': 'def test_function(param: str) -> bool:',
    'requirements': '- Must handle string input\n- Return boolean result'
}

formatted_prompt = source_code_prompt.format(**test_data)
print(f"\n📄 Formatted prompt (first 200 chars):")
print(f"   {formatted_prompt[:200]}...")

# Analyze template structure
print(f"\n🔍 Template analysis:")
print(f"   - Lines: {len(source_code_prompt.splitlines())}")
print(f"   - Emphasizes 'EXACT': {source_code_prompt.upper().count('EXACT')} times")
print(f"   - Contains 'TODO': {'TODO' in source_code_prompt}")
print(f"   - Contains 'pass': {'pass' in source_code_prompt}")

# %%
# Cell 4: Test Generation Prompt Template
"""
Lines 32-47: Test generation prompt template

The test_prompt template is used to generate comprehensive pytest tests
for individual requirements. It focuses on thorough testing coverage.
"""

test_prompt = """
Generate comprehensive pytest tests for the following requirement:

Requirement ID: {req_id}
Title: {req_title}
Description: {req_description}
Validation: {validation}

Generate tests that verify:
- Correct functionality
- Edge cases
- Error conditions
- Type safety

Return only the test code without explanations.
"""

# Test the test prompt template
print("🧪 Testing test prompt template:")
print(f"📝 Template length: {len(test_prompt)} characters")
print(f"🔍 Placeholders: {[p for p in ['{req_id}', '{req_title}', '{req_description}', '{validation}'] if p in test_prompt]}")

# Test template formatting
test_data = {
    'req_id': 'REQ-001',
    'req_title': 'String Validation',
    'req_description': 'Validate input string format',
    'validation': 'Check for non-empty string, proper format'
}

formatted_prompt = test_prompt.format(**test_data)
print(f"\n📄 Formatted test prompt:")
print(formatted_prompt)

# Analyze test coverage areas
coverage_areas = [
    'Correct functionality',
    'Edge cases', 
    'Error conditions',
    'Type safety'
]

print(f"\n🎯 Test coverage areas specified:")
for area in coverage_areas:
    included = area in formatted_prompt
    print(f"   {'✅' if included else '❌'} {area}")

print(f"\n🔍 Test template analysis:")
print(f"   - Lines: {len(test_prompt.splitlines())}")
print(f"   - Mentions 'pytest': {'pytest' in test_prompt.lower()}")
print(f"   - Requests code only: {'only the test code' in test_prompt.lower()}")

# %%
# Cell 5: Documentation Generation Prompt Template
"""
Lines 49-75: Documentation generation prompt template

The documentation_prompt template generates comprehensive markdown documentation
from specifications, with emphasis on practical examples and expected outputs.
"""

documentation_prompt = """
Generate markdown documentation for the following specification:

Specification ID: {spec_id}
Title: {title}
Requirements: {requirements}

Include:
- Project overview
- Installation instructions
- Usage examples with EXPECTED OUTPUTS for each example
- API documentation
- Requirements traceability

For each usage example, include:
1. The code example in a code block
2. A separate code block showing the expected output
3. A brief explanation of what the example demonstrates

IMPORTANT: Use the exact example inputs and outputs provided in each requirement of the spec file. 
Each requirement contains concrete example data - use these specific input/output pairs in your documentation examples.
Format them with separate code blocks for the code and the expected output.

Make the examples practical and realistic, showing what users would actually see when running the code.

Return only the markdown documentation without explanations.
"""

# Test the documentation prompt template
print("🧪 Testing documentation prompt template:")
print(f"📝 Template length: {len(documentation_prompt)} characters")
print(f"🔍 Placeholders: {[p for p in ['{spec_id}', '{title}', '{requirements}'] if p in documentation_prompt]}")

# Test template formatting
test_data = {
    'spec_id': 'SPEC-001',
    'title': 'String Processor',
    'requirements': '- Process strings\n- Handle edge cases\n- Example: input="hello" → output="HELLO"'
}

formatted_prompt = documentation_prompt.format(**test_data)
print(f"\n📄 Formatted documentation prompt (first 300 chars):")
print(f"   {formatted_prompt[:300]}...")

# Analyze documentation requirements
doc_sections = [
    'Project overview',
    'Installation instructions',
    'Usage examples with EXPECTED OUTPUTS',
    'API documentation',
    'Requirements traceability'
]

print(f"\n📚 Documentation sections required:")
for section in doc_sections:
    included = section in formatted_prompt
    print(f"   {'✅' if included else '❌'} {section}")

# Check example formatting requirements
example_requirements = [
    'code example in a code block',
    'separate code block showing the expected output',
    'brief explanation'
]

print(f"\n💡 Example formatting requirements:")
for req in example_requirements:
    included = req in formatted_prompt.lower()
    print(f"   {'✅' if included else '❌'} {req}")

print(f"\n🔍 Documentation template analysis:")
print(f"   - Lines: {len(documentation_prompt.splitlines())}")
print(f"   - Emphasizes 'EXPECTED OUTPUTS': {documentation_prompt.upper().count('EXPECTED OUTPUTS')}")
print(f"   - Mentions 'markdown': {'markdown' in documentation_prompt.lower()}")
print(f"   - Requests concrete examples: {'concrete example data' in documentation_prompt.lower()}")

# %%
# Cell 6: System Prompt Template
"""
Lines 77-82: System prompt template

The system_prompt provides high-level instructions for the AI's behavior
when generating code. It emphasizes scaffolding over implementation.
"""

system_prompt = """
You are generating Python scaffolding code that matches reference implementations exactly.
Create function stubs with TODO comments and pass statements.
Do NOT implement actual functionality - only create the structure.
Match the reference format precisely.
"""

# Test the system prompt template
print("🧪 Testing system prompt template:")
print(f"📝 Template length: {len(system_prompt)} characters")
print(f"🔍 Placeholders: {len([p for p in ['{', '}'] if p in system_prompt])} (should be 0)")

print(f"\n📄 System prompt content:")
print(system_prompt)

# Analyze system prompt instructions
instructions = [
    'scaffolding code',
    'matches reference implementations exactly',
    'TODO comments',
    'pass statements',
    'Do NOT implement actual functionality',
    'only create the structure',
    'Match the reference format precisely'
]

print(f"\n🎯 System prompt instructions:")
for instruction in instructions:
    included = instruction in system_prompt.lower()
    print(f"   {'✅' if included else '❌'} {instruction}")

print(f"\n🔍 System prompt analysis:")
print(f"   - Lines: {len(system_prompt.splitlines())}")
print(f"   - Emphasizes 'NOT implement': {'NOT implement' in system_prompt}")
print(f"   - Mentions 'scaffolding': {'scaffolding' in system_prompt.lower()}")
print(f"   - Mentions 'TODO': {'TODO' in system_prompt}")
print(f"   - Mentions 'pass': {'pass' in system_prompt}")

# %%
# Cell 7: Complete PromptTemplates Class Assembly
"""
Complete assembly of the PromptTemplates dataclass with all templates.
This brings together all the template components into a single, cohesive class.
"""

@dataclass
class PromptTemplates:
    """Container for prompt templates used in code generation."""
    
    source_code_prompt: str = """Generate Python scaffolding code using the EXACT function interfaces provided.

For specification {spec_id}, create a file with:
- Module docstring: "{title}\nVersion {version}"
- Import appropriate modules based on function requirements
- Function stubs with TODO comments and pass statements
- Use the EXACT function signatures provided below
- Single-line docstrings format: \"\"\"TODO {spec_id}: description.\"\"\"

FUNCTION INTERFACES (USE EXACTLY AS SPECIFIED):
{interfaces}

REQUIREMENTS:
{requirements}

IMPORTANT: Use the exact function names, parameter names, and types from the interfaces above.
Do not infer or modify the signatures - use them exactly as provided."""

    test_prompt: str = """
Generate comprehensive pytest tests for the following requirement:

Requirement ID: {req_id}
Title: {req_title}
Description: {req_description}
Validation: {validation}

Generate tests that verify:
- Correct functionality
- Edge cases
- Error conditions
- Type safety

Return only the test code without explanations.
"""

    documentation_prompt: str = """
Generate markdown documentation for the following specification:

Specification ID: {spec_id}
Title: {title}
Requirements: {requirements}

Include:
- Project overview
- Installation instructions
- Usage examples with EXPECTED OUTPUTS for each example
- API documentation
- Requirements traceability

For each usage example, include:
1. The code example in a code block
2. A separate code block showing the expected output
3. A brief explanation of what the example demonstrates

IMPORTANT: Use the exact example inputs and outputs provided in each requirement of the spec file. 
Each requirement contains concrete example data - use these specific input/output pairs in your documentation examples.
Format them with separate code blocks for the code and the expected output.

Make the examples practical and realistic, showing what users would actually see when running the code.

Return only the markdown documentation without explanations.
"""

    system_prompt: str = """
You are generating Python scaffolding code that matches reference implementations exactly.
Create function stubs with TODO comments and pass statements.
Do NOT implement actual functionality - only create the structure.
Match the reference format precisely.
"""

# Test the complete PromptTemplates class
print("🧪 Testing complete PromptTemplates class:")

# Create instance with default values
templates = PromptTemplates()
print(f"📦 Templates instance created: {type(templates).__name__}")

# Check all fields are present
expected_fields = ['source_code_prompt', 'test_prompt', 'documentation_prompt', 'system_prompt']
actual_fields = list(templates.__dataclass_fields__.keys())

print(f"\n📋 Field validation:")
print(f"   Expected fields: {expected_fields}")
print(f"   Actual fields: {actual_fields}")
print(f"   All present: {set(expected_fields) == set(actual_fields)}")

# Test field values
print(f"\n📝 Field values:")
for field_name in expected_fields:
    field_value = getattr(templates, field_name)
    print(f"   {field_name}: {len(field_value)} chars, {len(field_value.splitlines())} lines")

# Test template formatting
print(f"\n🔧 Template formatting test:")
test_formats = [
    ('source_code_prompt', {'spec_id': 'TEST', 'title': 'Test', 'version': '1.0', 'interfaces': 'def test():', 'requirements': 'Test req'}),
    ('test_prompt', {'req_id': 'REQ-001', 'req_title': 'Test', 'req_description': 'Test desc', 'validation': 'Test val'}),
    ('documentation_prompt', {'spec_id': 'DOC-001', 'title': 'Doc Test', 'requirements': 'Doc req'})
]

for template_name, format_data in test_formats:
    try:
        template = getattr(templates, template_name)
        formatted = template.format(**format_data)
        print(f"   ✅ {template_name}: Formatted successfully ({len(formatted)} chars)")
    except Exception as e:
        print(f"   ❌ {template_name}: {e}")

# %%
# Cell 8: Template Usage and Integration Testing
"""
Comprehensive testing of template usage patterns and integration scenarios.

This cell demonstrates how the templates would be used in practice
within the SpecCoder system.
"""

# Create templates instance
templates = PromptTemplates()

print("🧪 Template Usage and Integration Testing:")
print("=" * 50)

# Scenario 1: Source code generation
print("\n🔧 Scenario 1: Source Code Generation")
print("-" * 30)

spec_data = {
    'spec_id': 'MUSIC-001',
    'title': 'Music Generation Library',
    'version': '1.0.0',
    'interfaces': '''def generate_melody(key: str, tempo: int) -> List[str]:
def apply_rhythm(pattern: str, notes: List[str]) -> List[str]:''',
    'requirements': '''- Generate melodies in specified key
- Apply rhythmic patterns
- Handle tempo variations'''
}

source_prompt = templates.source_code_prompt.format(**spec_data)
print(f"📝 Source prompt generated: {len(source_prompt)} characters")
print(f"📄 Contains function signatures: {'def generate_melody' in source_prompt}")
print(f"📄 Contains TODO instruction: {'TODO' in source_prompt}")

# Scenario 2: Test generation
print("\n🧪 Scenario 2: Test Generation")
print("-" * 25)

req_data = {
    'req_id': 'REQ-001',
    'req_title': 'Melody Generation',
    'req_description': 'Generate musical melodies in specified keys',
    'validation': 'Check output is valid list of notes'
}

test_prompt = templates.test_prompt.format(**req_data)
print(f"📝 Test prompt generated: {len(test_prompt)} characters")
print(f"📄 Contains pytest instruction: {'pytest' in test_prompt.lower()}")
print(f"📄 Contains edge cases: {'Edge cases' in test_prompt}")

# Scenario 3: Documentation generation
print("\n📚 Scenario 3: Documentation Generation")
print("-" * 35)

doc_data = {
    'spec_id': 'MUSIC-001',
    'title': 'Music Generation Library',
    'requirements': '''- Generate melodies: input="C major", tempo=120 → output=["C", "E", "G"]
- Apply rhythms: input="rock", notes=["C", "E"] → output=["C", "C", "E", "E"]'''
}

doc_prompt = templates.documentation_prompt.format(**doc_data)
print(f"📝 Documentation prompt generated: {len(doc_prompt)} characters")
print(f"📄 Contains expected outputs: {'EXPECTED OUTPUTS' in doc_prompt}")
print(f"📄 Contains example data: {'concrete example data' in doc_prompt.lower()}")

# Scenario 4: System prompt usage
print("\n🤖 Scenario 4: System Prompt Usage")
print("-" * 30)

print(f"📝 System prompt: {len(templates.system_prompt)} characters")
print(f"📄 Emphasizes scaffolding: {'scaffolding' in templates.system_prompt.lower()}")
print(f"📄 Warns against implementation: {'Do NOT implement' in templates.system_prompt}")

# Template integration analysis
print("\n🔍 Template Integration Analysis:")
print("-" * 35)

# Check template consistency
all_templates = [
    ('Source Code', templates.source_code_prompt),
    ('Test', templates.test_prompt),
    ('Documentation', templates.documentation_prompt),
    ('System', templates.system_prompt)
]

for name, template in all_templates:
    lines = len(template.splitlines())
    chars = len(template)
    placeholders = len([p for p in ['{', '}'] if p in template]) // 2  # Each placeholder has { and }
    
    print(f"   {name:12} | {lines:3} lines | {chars:4} chars | {placeholders:2} placeholders")

# Template usage patterns
print("\n💡 Template Usage Patterns:")
print("   📝 Source Code: Used for initial code scaffolding from OpenSpec")
print("   🧪 Test: Used for generating pytest tests per requirement")
print("   📚 Documentation: Used for creating user-facing documentation")
print("   🤖 System: Used as AI behavior instructions for all operations")

print("\n🎉 Template System Testing Complete!")
print("\n📊 Summary:")
print(f"   - Total templates: {len(all_templates)}")
print(f"   - Total characters: {sum(len(t) for _, t in all_templates)}")
print(f"   - Dataclass structure: ✅")
print(f"   - Template formatting: ✅")
print(f"   - Integration readiness: ✅")

print("\n🔍 Template Features Documented:")
print("   📦 Dataclass-based organization")
print("   🔧 Placeholder-based formatting")
print("   📝 Structured prompt engineering")
print("   🎯 Task-specific templates")
print("   🚫 Implementation restrictions (scaffolding only)")
print("   📚 Documentation with expected outputs")
print("   🧪 Comprehensive test coverage requirements")
print("   🤖 System-level behavior control")
print("   ✅ Exact interface compliance emphasis")
print("   📋 Requirements traceability support")

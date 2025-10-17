"""
Prompt Templates

Contains templates for generating different types of content from OpenSpec specifications.
"""

from dataclasses import dataclass


@dataclass
class PromptTemplates:
    """Container for prompt templates used in code generation."""
    
    source_code_prompt: str = """Generate Python scaffolding code using the EXACT function interfaces provided.

For specification {spec_id}, create a file with:
- Module docstring: "{title}\\nVersion {version}"
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
- Usage examples
- API documentation
- Requirements traceability

Return only the markdown documentation without explanations.
"""

    system_prompt: str = """
You are generating Python scaffolding code that matches reference implementations exactly.
Create function stubs with TODO comments and pass statements.
Do NOT implement actual functionality - only create the structure.
Match the reference format precisely.
"""
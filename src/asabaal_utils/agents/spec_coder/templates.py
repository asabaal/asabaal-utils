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

    def get_test_generation_prompt(self, spec) -> str:
        """
        Generate a test generation prompt for the given specification.
        
        Args:
            spec: OpenSpec object containing requirements and interfaces
            
        Returns:
            Formatted prompt string for test generation
        """
        # Format requirements for the prompt
        requirements_text = ""
        for req in spec.requirements:
            requirements_text += f"- {req.id}: {req.description}\n"
            if req.interface and req.interface.example:
                requirements_text += f"  Example: {req.interface.example}\n"
        
        # Format interfaces for the prompt
        interfaces_text = ""
        for interface in spec.interfaces:
            if interface.type == 'class':
                interfaces_text += f"class {interface.name}:\n"
                for method in interface.methods:
                    interfaces_text += f"  {method.signature}\n"
            elif interface.type == 'function':
                interfaces_text += f"{interface.signature}\n"
        
        return self.test_prompt.format(
            req_id=spec.spec_id,
            req_title=spec.title,
            req_description=requirements_text,
            validation="Functional testing based on specification requirements",
            interfaces=interfaces_text
        )
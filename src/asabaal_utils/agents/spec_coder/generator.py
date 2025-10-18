"""
OpenSpec-to-Code Generator

Main orchestrator for converting OpenSpec specifications into complete
code implementations using AI models.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    from .spec_parser import SpecParser, OpenSpec, Requirement
    from .ollama_client import OllamaClient, GenerationConfig
    from .templates import PromptTemplates
except ImportError:
    from spec_parser import SpecParser, OpenSpec, Requirement
    from ollama_client import OllamaClient, GenerationConfig
    from templates import PromptTemplates

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of a generation operation."""
    success: bool
    files_generated: List[str]
    errors: List[str]
    warnings: List[str]
    execution_time: float


class CodeGenerator:
    """Main generator class that orchestrates the code generation process."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the generator with configuration."""
        self.config = self._load_config(config_path)
        self.spec_parser = SpecParser()
        self.ollama_client = OllamaClient(GenerationConfig(**self.config['model']))
        self.templates = PromptTemplates()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert spec_id to consistent filename format."""
        # Always use underscores for consistency
        return name.replace('-', '_').replace(' ', '_')
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml
        
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "config.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_from_spec(self, spec_path: Path, output_dir: Optional[Path] = None) -> GenerationResult:
        """Generate complete implementation from an OpenSpec specification."""
        import time
        start_time = time.time()
        
        # Setup paths - use the provided output_dir, or fall back to current directory
        if output_dir is None:
            output_dir = Path.cwd() / "output"
        else:
            output_dir = Path(output_dir)
        
        errors = []
        warnings = []
        
        # Clean output directory to prevent mixing old/new formats
        if output_dir.exists() and any(output_dir.iterdir()):
            if not self.config.get('generation', {}).get('overwrite', False):
                warnings.append("Output directory exists and is not empty. Use overwrite=True to clean it.")
                return GenerationResult(
                    success=False,
                    files_generated=[],
                    errors=["Output directory exists and overwrite=False"],
                    warnings=warnings,
                    execution_time=0
                )
            shutil.rmtree(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        files_generated = []
        
        try:
            # Parse the specification
            logger.info(f"Parsing specification: {spec_path}")
            spec = self.spec_parser.parse_file(spec_path)
            
            # Validate the specification
            validation_issues = self.spec_parser.validate_spec(spec)
            if validation_issues:
                warnings.extend(f"Spec validation issue: {issue}" for issue in validation_issues)
            
            # Test Ollama connection
            if not self.ollama_client.test_connection():
                raise RuntimeError("Failed to connect to Ollama. Please ensure Ollama is running and the model is available.")
            
            # Generate files
            logger.info("Starting code generation...")
            
            # 1. Generate main source code
            source_file = self._generate_source_code(spec, output_dir)
            if source_file:
                files_generated.append(source_file)
            
            # 2. Generate documentation
            doc_file = self._generate_documentation(spec, output_dir)
            if doc_file:
                files_generated.append(doc_file)
            
            # 3. Generate tests for each requirement
            test_files = self._generate_tests(spec, output_dir)
            files_generated.extend(test_files)
            
            # 4. Generate CI/CD configuration
            ci_files = self._generate_ci_config(spec, output_dir)
            files_generated.extend(ci_files)
            
            # 5. Generate validation script
            validation_file = self._generate_validation_script(output_dir)
            if validation_file:
                files_generated.append(validation_file)
            
            # 6. Generate requirements file
            requirements_file = self._generate_requirements_file(output_dir)
            if requirements_file:
                files_generated.append(requirements_file)
            
            logger.info(f"Generation complete. Generated {len(files_generated)} files.")
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            errors.append(str(e))
        
        execution_time = time.time() - start_time
        
        return GenerationResult(
            success=len(errors) == 0,
            files_generated=files_generated,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time
        )
    
    def _generate_source_code(self, spec: OpenSpec, output_dir: Path) -> Optional[str]:
        """Generate the main source code file."""
        try:
            # Prepare the prompt
            requirements_text = self.spec_parser.format_requirements_for_prompt(spec)
            interfaces_text = self.spec_parser.format_interfaces_for_prompt(spec)
            prompt = self.templates.source_code_prompt.format(
                spec_id=spec.spec_id,
                title=spec.title,
                version=spec.version,
                requirements=requirements_text,
                interfaces=interfaces_text
            )
            
            # Generate code
            logger.info("Generating source code...")
            generated_code = self.ollama_client.generate_code(prompt)
            
            # Write to file
            filename = self._sanitize_filename(spec.spec_id)
            output_file = output_dir / "scaffolds" / "src" / f"{filename}.py"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                f.write(generated_code)
            
            logger.info(f"Source code written to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate source code: {e}")
            return None
    
    def _generate_documentation(self, spec: OpenSpec, output_dir: Path) -> Optional[str]:
        """Generate documentation file."""
        try:
            requirements_text = self.spec_parser.format_requirements_for_prompt(spec)
            prompt = self.templates.documentation_prompt.format(
                spec_id=spec.spec_id,
                title=spec.title,
                requirements=requirements_text
            )
            
            logger.info("Generating documentation...")
            generated_doc = self.ollama_client.generate(prompt)
            
            filename = self._sanitize_filename(spec.spec_id)
            output_file = output_dir / "scaffolds" / "docs" / f"{filename}.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                f.write(generated_doc)
            
            logger.info(f"Documentation written to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate documentation: {e}")
            return None
    
    def _generate_tests(self, spec: OpenSpec, output_dir: Path) -> List[str]:
        """Generate test files for each requirement."""
        test_files = []
        
        try:
            # First generate the source code to have it available for test generation
            filename = self._sanitize_filename(spec.spec_id)
            source_file = output_dir / "scaffolds" / "src" / f"{filename}.py"
            if not source_file.exists():
                logger.warning("Source code file not found, generating tests without code context")
                source_code = ""
            else:
                with open(source_file, 'r') as f:
                    source_code = f.read()
            
            for requirement in spec.requirements:
                if not requirement.validation:
                    continue
                for validation in requirement.validation:
                    if validation.type == 'unit':
                        test_file = self._generate_unit_test(
                            requirement, source_code, output_dir
                        )
                        if test_file:
                            test_files.append(test_file)
                    elif validation.type == 'integration':
                        test_file = self._generate_integration_test(
                            requirement, source_code, output_dir
                        )
                        if test_file:
                            test_files.append(test_file)
            
            logger.info(f"Generated {len(test_files)} test files")
            
        except Exception as e:
            logger.error(f"Failed to generate tests: {e}")
        
        return test_files
    
    def _strip_markdown_code_blocks(self, content: str) -> str:
        """Strip markdown code block formatting and other non-Python content from generated content."""
        import re
        
        # Remove ```python and ``` markers
        content = re.sub(r'```python\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
        
        # Remove common AI-generated comments and notes
        lines = content.split('\n')
        cleaned_lines = []
        in_python_code = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip lines that look like AI instructions or notes
            if (stripped.startswith('Note:') or 
                stripped.startswith('TODO:') or
                stripped.startswith('Replace') or
                stripped.startswith('your_module') or
                'actual name of your module' in stripped.lower() or
                stripped.startswith('# Note:') or
                stripped.startswith('# TODO:') or
                stripped.startswith('pytest test code only') or
                stripped.startswith('The test code must be complete') or
                stripped.startswith('Generate comprehensive pytest tests') or
                not stripped or
                stripped.lower().startswith('here is') or
                stripped.lower().startswith('this is') or
                stripped.lower().startswith('the following')):
                continue
            
            # Skip lines that are clearly instructions
            if any(keyword in stripped.lower() for keyword in [
                'generate tests', 'test code', 'pytest file', 'executable', 
                'complete and executable', 'single pytest file', 'instruction',
                'requirement:', 'code to test:', 'verify:'
            ]):
                continue
            
            cleaned_lines.append(line)
        
        # Remove any remaining empty lines at the beginning or end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        # Fix indentation issues by removing leading spaces only from the first few lines
        # that might have been incorrectly indented by AI generation
        for i, line in enumerate(cleaned_lines):
            if i < 5 and line.strip() and not line.startswith(' ' * 4):  # Not properly indented
                # Remove leading spaces from lines that should start at column 0
                if line.strip().startswith(('def ', 'class ', 'import ', 'from ', '@')):
                    cleaned_lines[i] = line.lstrip()
        
        content = '\n'.join(cleaned_lines)
        
        return content
    
    def _generate_unit_test(self, requirement: Requirement, source_code: str, output_dir: Path) -> Optional[str]:
        """Generate a unit test for a specific requirement."""
        try:
            validation_file = requirement.validation[0].file if requirement.validation else "unknown"
            prompt = self.templates.test_prompt.format(
                req_id=requirement.id,
                req_title=requirement.title,
                req_description=requirement.description,
                validation=f"unit test in {validation_file}"
            )
            
            generated_test = self.ollama_client.generate_tests(source_code, requirement.description)
            
            # Strip markdown code blocks if present
            generated_test = self._strip_markdown_code_blocks(generated_test)
            
            # Extract filename from validation or create one
            if requirement.validation:
                # Get just the filename, not the full path
                test_filename = Path(requirement.validation[0].file).name
            else:
                test_filename = f"test_{requirement.id.lower()}.py"
            output_file = output_dir / "scaffolds" / "tests" / test_filename
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                f.write(generated_test)
            
            logger.debug(f"Unit test written to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate unit test for {requirement.id}: {e}")
            return None
    
    def _generate_integration_test(self, requirement: Requirement, source_code: str, output_dir: Path) -> Optional[str]:
        """Generate an integration test for a specific requirement."""
        # Similar to unit test but with integration focus
        return self._generate_unit_test(requirement, source_code, output_dir)
    
    def _generate_ci_config(self, spec: OpenSpec, output_dir: Path) -> List[str]:
        """Generate CI/CD configuration files."""
        ci_files = []
        
        try:
            # Generate GitHub Actions workflow
            workflow_content = self._generate_github_workflow(spec)
            workflow_file = output_dir / ".github" / "workflows" / "ci.yml"
            workflow_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(workflow_file, 'w') as f:
                f.write(workflow_content)
            
            ci_files.append(str(workflow_file))
            logger.info(f"CI workflow written to: {workflow_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate CI config: {e}")
        
        return ci_files
    
    def _generate_github_workflow(self, spec: OpenSpec) -> str:
        """Generate GitHub Actions workflow content."""
        return f"""name: CI
on:
  push:
  pull_request:
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          pip install pytest ruff || true
      - name: Run validation
        run: bash scripts/validate.sh
"""
    
    def _generate_validation_script(self, output_dir: Path) -> Optional[str]:
        """Generate validation script."""
        try:
            script_content = """#!/usr/bin/env bash
set -euo pipefail
echo "▶ Running validation..."
ruff check . || true
pytest -q
echo "✅ Validation complete."
"""
            
            script_file = output_dir / "scripts" / "validate.sh"
            script_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_file, 0o755)
            
            logger.info(f"Validation script written to: {script_file}")
            return str(script_file)
            
        except Exception as e:
            logger.error(f"Failed to generate validation script: {e}")
            return None
    
    def _generate_requirements_file(self, output_dir: Path) -> Optional[str]:
        """Generate requirements.txt file."""
        try:
            requirements_content = """pytest>=7.4.0
ruff>=0.1.0
"""
            
            requirements_file = output_dir / "requirements.txt"
            with open(requirements_file, 'w') as f:
                f.write(requirements_content)
            
            logger.info(f"Requirements file written to: {requirements_file}")
            return str(requirements_file)
            
        except Exception as e:
            logger.error(f"Failed to generate requirements file: {e}")
            return None
    
    def _generate_unit_test_with_retry(self, requirement: Requirement, source_code: str, max_retries: int = 3) -> str:
        """Generate a unit test with retry logic when AI generation fails."""
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    # First attempt - normal generation
                    generated_test = self.ollama_client.generate_tests(source_code, requirement.description)
                else:
                    # Retry attempts - with feedback about previous failure
                    retry_prompt = f"""Generate pytest tests for the following requirement. 
Your previous attempt had syntax errors or was incomplete. Please ensure the code is valid, complete Python.

Requirement: {requirement.description}

Code to test:
```python
{source_code}
```

Generate complete, syntactically valid pytest code. Return ONLY the Python code without explanations."""
                    generated_test = self.ollama_client.generate(retry_prompt, 
                        "You are an expert Python test developer. Generate complete, valid pytest code.")
                
                # Strip markdown code blocks if present
                cleaned_test = self._clean_generated_code(generated_test)
                
                # Validate that the generated code is syntactically valid
                if self._validate_python_code(cleaned_test):
                    logger.info(f"Successfully generated valid test for {requirement.id} on attempt {attempt + 1}")
                    return cleaned_test
                else:
                    logger.warning(f"Attempt {attempt + 1} failed for {requirement.id} - invalid Python syntax")
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {requirement.id} with error: {e}")
        
        # All retries failed - use fallback
        logger.error(f"All {max_retries} attempts failed for {requirement.id}, using fallback test")
        return self._generate_fallback_test(requirement)
    
    def _clean_generated_code(self, generated_code: str) -> str:
        """Clean generated code by removing markdown formatting and fixing truncation."""
        if not generated_code:
            return ""
        
        # Remove markdown code blocks
        lines = generated_code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip markdown code block markers
            if line.strip() in ['```python', '```']:
                continue
            cleaned_lines.append(line)
        
        cleaned_code = '\n'.join(cleaned_lines)
        
        # Fix common truncation issues
        if cleaned_code.strip():
            # Check if the last line is incomplete (common truncation pattern)
            last_line = cleaned_lines[-1] if cleaned_lines else ""
            
            # If the last line looks like it was cut off mid-function, remove it
            if (last_line.strip().startswith('def ') and 
                '(' in last_line and ':' not in last_line):
                cleaned_lines = cleaned_lines[:-1]
                cleaned_code = '\n'.join(cleaned_lines)
            
            # Ensure the file ends properly
            if cleaned_code.strip() and not cleaned_code.rstrip().endswith('\n'):
                cleaned_code += '\n'
        
        return cleaned_code
    
    def _validate_python_code(self, code: str) -> bool:
        """Validate that the generated code is syntactically valid Python."""
        if not code.strip():
            return False
        
        try:
            import ast
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _generate_fallback_test(self, requirement: Requirement) -> str:
        """Generate a basic fallback test when AI generation fails."""
        test_name = f"test_{requirement.id.lower().replace('-', '_')}"
        
        fallback_test = f'''import pytest

def {test_name}():
    """Fallback test for requirement: {requirement.title}"""
    # TODO: Implement proper test for: {requirement.description}
    # This is a placeholder generated due to AI generation failure
    # FAIL the test to indicate that proper implementation is needed
    pytest.fail(f"AI generation failed for requirement {{requirement.id}}. Manual test implementation required for: {{requirement.description}}")
'''
        return fallback_test
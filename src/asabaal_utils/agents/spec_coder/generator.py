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
    """
    Main generator class that orchestrates AI-powered code generation from OpenSpec specifications.
    
    This class serves as the primary interface for converting OpenSpec YAML specifications
    into complete, working code implementations. It coordinates multiple AI models and
    generation strategies to produce source code, tests, documentation, and configuration
    files based on specification requirements.
    
    The generator supports:
    - Source code generation from function specifications
    - Automated test generation with coverage analysis
    - Documentation generation
    - CI/CD configuration generation
    - Code validation and cleanup
    
    Attributes:
        config: Configuration dictionary for model settings and generation options
        spec_parser: SpecParser instance for processing OpenSpec files
        ollama_client: OllamaClient instance for AI model interactions
        templates: PromptTemplates instance for generation prompts
    
    Example:
        >>> generator = CodeGenerator()
        >>> result = generator.generate_from_spec(Path("api_spec.yaml"))
        >>> if result.success:
        ...     print(f"Generated {len(result.files_generated)} files")
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the CodeGenerator with configuration.
        
        Args:
            config_path: Optional path to configuration file. If None, uses default
                        configuration settings for model parameters and generation options.
        
        Raises:
            FileNotFoundError: If config_path is specified but file doesn't exist
            ValueError: If configuration file contains invalid settings
        
        Example:
            >>> # Use default configuration
            >>> generator = CodeGenerator()
            >>> # Use custom configuration
            >>> generator = CodeGenerator(Path("config.json"))
        """
        self.config = self._load_config(config_path)
        self.spec_parser = SpecParser()
        self.ollama_client = OllamaClient(GenerationConfig(**self.config['model']))
        self.templates = PromptTemplates()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Convert a name to a consistent, filesystem-safe filename format.
        
        This private method ensures that generated filenames are consistent across
        different platforms and filesystems by replacing problematic characters
        with safe alternatives. It handles spaces, hyphens, and other characters
        that might cause issues in different operating systems.
        
        Args:
            name: Original name string that may contain spaces, hyphens, or other
                  filesystem-unsafe characters.
        
        Returns:
            Sanitized filename string using only underscores as separators.
            All spaces and hyphens are replaced with underscores for consistency.
        
        Note:
            This method is conservative in its approach - it only replaces the most
            common problematic characters to preserve readability while ensuring
            filesystem compatibility.
        
        Example:
            >>> generator._sanitize_filename("my-api-spec")
            'my_api_spec'
            >>> generator._sanitize_filename("test file name")
            'test_file_name'
            >>> generator._sanitize_filename("complex_name-v2.0")
            'complex_name_v2.0'
        """
        # Always use underscores for consistency
        return name.replace('-', '_').replace(' ', '_')
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """
        Load generator configuration from a YAML file with fallback to default.
        
        This private method handles configuration loading for the code generator,
        supporting both custom configuration files and a default configuration.
        It loads model settings, generation parameters, and other options that
        control the code generation process.
        
        Args:
            config_path: Optional path to custom configuration YAML file. If None,
                        uses the default configuration file in the config directory.
        
        Returns:
            Dictionary containing configuration settings with the following structure:
            {
                'model': {
                    'model': str - Model name,
                    'base_url': str - Ollama server URL,
                    'temperature': float - Generation temperature,
                    'max_tokens': int - Maximum tokens to generate
                },
                'generation': {
                    'overwrite': bool - Whether to overwrite existing files,
                    'retry_attempts': int - Number of retry attempts for failed generations
                }
            }
        
        Raises:
            FileNotFoundError: If neither custom nor default config file exists
            yaml.YAMLError: If configuration file contains invalid YAML
        
        Example:
            >>> # Use default configuration
            >>> config = generator._load_config(None)
            >>> # Use custom configuration
            >>> config = generator._load_config(Path("my_config.yaml"))
            >>> print(f"Model: {config['model']['model']}")
        """
        import yaml
        
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "config.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_from_spec(self, spec_path: Path, output_dir: Optional[Path] = None) -> GenerationResult:
        """
        Generate complete code implementation from an OpenSpec specification file.
        
        This is the main entry point for code generation. It processes an OpenSpec
        YAML file and generates a complete project structure including source code,
        tests, documentation, and configuration files. The generation process uses
        AI models to create implementations that match the specification requirements.
        
        Args:
            spec_path: Path to the OpenSpec YAML specification file containing
                      requirements, function interfaces, validation criteria, and metadata.
            output_dir: Directory where generated code will be written. If None,
                       creates a 'generated_functions' directory in the current location.
        
        Returns:
            GenerationResult object containing:
            - success: Boolean indicating if generation completed successfully
            - files_generated: List of paths to generated files
            - errors: List of error messages encountered during generation
            - warnings: List of warnings about potential issues
            - execution_time: Time taken for generation in seconds
        
        Raises:
            FileNotFoundError: If spec_path does not exist
            ValueError: If spec_path contains invalid OpenSpec format
            OSError: If output_dir cannot be created or written to
            RuntimeError: If AI model generation fails
        
        Example:
            >>> generator = CodeGenerator()
            >>> result = generator.generate_from_spec(
            ...     Path("calculator_spec.yaml"),
            ...     Path("generated_calculator")
            ... )
            >>> if result.success:
            ...     print(f"Generated {len(result.files_generated)} files")
            ...     for file_path in result.files_generated:
            ...         print(f"  - {file_path}")
            >>> else:
            ...     print("Generation failed:")
            ...     for error in result.errors:
            ...         print(f"  - {error}")
        """
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
        """
        Generate source code implementations for all requirements in the specification.
        
        This method uses AI models to generate complete, working implementations
        for each function specified in the OpenSpec file. It considers function
        signatures, requirements descriptions, and validation criteria to create
        appropriate implementations.
        
        Args:
            spec: Parsed OpenSpec object containing requirements and interfaces.
            output_dir: Directory where source code files will be written.
        
        Returns:
            Path to the main generated source file, or None if generation failed.
        
        Raises:
            RuntimeError: If AI model fails to generate valid code
            OSError: If source code files cannot be written
        
        Example:
            >>> generator = CodeGenerator()
            >>> spec = generator.spec_parser.parse_file(Path("spec.yaml"))
            >>> source_file = generator._generate_source_code(spec, Path("output"))
            >>> if source_file:
            ...     print(f"Generated source: {source_file}")
        """
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
            
            # Clean up markdown formatting from generated code
            cleaned_code = self._strip_markdown_code_blocks(generated_code)
            
            # Write to file
            filename = self._sanitize_filename(spec.spec_id)
            output_file = output_dir / "scaffolds" / "src" / f"{filename}.py"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                f.write(cleaned_code)
            
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
            
            # Clean up markdown formatting issues
            cleaned_doc = self._clean_documentation_markdown(generated_doc)
            
            with open(output_file, 'w') as f:
                f.write(cleaned_doc)
            
            logger.info(f"Documentation written to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate documentation: {e}")
            return None
    
    def _generate_tests(self, spec: OpenSpec, output_dir: Path) -> List[str]:
        """
        Generate comprehensive test suites for all requirements in the specification.
        
        This method creates both unit tests and integration tests for each requirement
        in the specification. It uses AI to generate tests that cover normal operation,
        edge cases, error conditions, and validation criteria specified in the OpenSpec.
        
        Args:
            spec: Parsed OpenSpec object containing requirements and validation criteria.
            output_dir: Directory where test files will be written.
        
        Returns:
            List of paths to generated test files. Empty list if generation failed.
        
        Raises:
            RuntimeError: If AI model fails to generate valid tests
            OSError: If test files cannot be written
        
        Example:
            >>> generator = CodeGenerator()
            >>> spec = generator.spec_parser.parse_file(Path("spec.yaml"))
            >>> test_files = generator._generate_tests(spec, Path("output"))
            >>> print(f"Generated {len(test_files)} test files")
            >>> for test_file in test_files:
            ...     print(f"  - {test_file}")
        """
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
                # Generate tests for all requirements, even if no validation is specified
                if not requirement.validation:
                    # No validation specified - generate a basic functional test
                    logger.info(f"No validation specified for {requirement.id}, generating basic functional test")
                    test_file = self._generate_unit_test(
                        requirement, source_code, output_dir
                    )
                    if test_file:
                        test_files.append(test_file)
                else:
                    # Validation specified - generate tests based on validation type
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
                        elif validation.type == 'functional':
                            # Functional validation - generate both unit and integration tests
                            unit_test = self._generate_unit_test(
                                requirement, source_code, output_dir
                            )
                            if unit_test:
                                test_files.append(unit_test)
                            
                            integration_test = self._generate_integration_test(
                                requirement, source_code, output_dir
                            )
                            if integration_test:
                                test_files.append(integration_test)
                        else:
                            # Unknown validation type - generate a basic unit test
                            logger.warning(f"Unknown validation type '{validation.type}' for {requirement.id}, generating basic unit test")
                            test_file = self._generate_unit_test(
                                requirement, source_code, output_dir
                            )
                            if test_file:
                                test_files.append(test_file)
            
            logger.info(f"Generated {len(test_files)} test files")
            
        except Exception as e:
            logger.error(f"Failed to generate tests: {e}")
        
        return test_files
    
    def _strip_markdown_code_blocks(self, content: str) -> str:
        """
        Remove markdown code block markers from AI-generated content.
        
        This private method processes AI-generated text to remove markdown code block
        delimiters (```python, ```, etc.) that are commonly included in model responses
        but would cause syntax errors if left in the generated code files.
        
        Args:
            content: Raw text content from AI model that may contain markdown code
                    block markers and other formatting artifacts.
        
        Returns:
            Clean code string with markdown markers removed, suitable for writing
            directly to Python files. The method preserves the actual code content
            while removing only the formatting markers.
        
        Note:
            This method handles various markdown code block formats:
            - ```python
            - ```
            - Language-specific markers (```javascript, etc.)
            - Multiple code blocks in the same content
        
        Example:
            >>> content = '''
            ... ```python
            ... def hello_world():
            ...     print("Hello, World!")
            ... ```
            ... '''
            >>> clean_code = generator._strip_markdown_code_blocks(content)
            >>> assert '```python' not in clean_code
            >>> assert 'def hello_world():' in clean_code
        """
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
                stripped.lower().startswith('the following') or
                'do not add extra parameters' in stripped.lower() or
                'do not modify existing ones' in stripped.lower()):
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
    
    def _clean_documentation_markdown(self, content: str) -> str:
        """
        Clean up markdown formatting issues in AI-generated documentation.
        
        This method fixes common issues with AI-generated markdown:
        1. Removes extra plain text lines between code blocks
        2. Fixes incorrect code block language markers for output
        3. Removes redundant empty lines
        4. Cleans up AI-generated artifacts
        
        Args:
            content: Raw markdown content from AI model
            
        Returns:
            Cleaned markdown content with proper formatting
        """
        import re
        
        lines = content.split('\n')
        cleaned_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip AI-generated artifacts and notes
            if (stripped.startswith('Note:') or 
                stripped.startswith('TODO:') or
                stripped.startswith('Replace') or
                'actual name of your module' in stripped.lower() or
                stripped.startswith('# Note:') or
                stripped.startswith('# TODO:') or
                'Return only the markdown documentation' in stripped or
                'without explanations' in stripped):
                i += 1
                continue
            
            # Fix code block language for output blocks
            if stripped.startswith('```python') and i > 0:
                # Look at previous lines to determine if this is output
                prev_lines = [lines[j].strip() for j in range(max(0, i-3), i) if lines[j].strip()]
                if any('print(' in prev_line or 'output:' in prev_line.lower() or 'result:' in prev_line.lower() 
                      for prev_line in prev_lines):
                    # This looks like output, change to plain code block
                    cleaned_lines.append('```')
                    i += 1
                    continue
            
            # Remove extra empty lines between code blocks
            if stripped == '' and i > 0 and i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                prev_line = lines[i - 1].strip()
                
                # If we're between two code blocks or after a code block, keep only one empty line
                if (prev_line.startswith('```') and next_line.startswith('```')) or \
                   (prev_line.startswith('```') and next_line == ''):
                    # Skip this empty line
                    i += 1
                    continue
            
            # Remove consecutive empty lines
            if stripped == '' and cleaned_lines and cleaned_lines[-1].strip() == '':
                i += 1
                continue
            
            cleaned_lines.append(line)
            i += 1
        
        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    

    
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
    
    def _generate_unit_test(self, requirement: Requirement, source_code: str, output_dir: Path) -> Optional[str]:
        """
        Generate a unit test for a specific requirement.
        
        Args:
            requirement: The requirement to generate tests for
            source_code: The generated source code (for context)
            output_dir: Directory to write the test file
            
        Returns:
            Path to the generated test file, or None if generation failed
        """
        try:
            # Prepare the prompt for unit test generation
            # Create a simple prompt for this specific requirement
            prompt = f"""
Generate comprehensive pytest tests for the following requirement:

Requirement ID: {requirement.id}
Title: {requirement.title}
Description: {requirement.description}

Generate tests that verify:
- Correct functionality
- Edge cases
- Error conditions
- Type safety

Return only the test code without explanations.
"""
            
            # Generate test code
            logger.info(f"Generating unit test for requirement: {requirement.id}")
            test_code = self.ollama_client.generate_code(prompt)
            
            # Clean up markdown formatting
            test_code = self._strip_markdown_code_blocks(test_code)
            
            # Validate the generated test code
            if not self._validate_python_code(test_code):
                logger.warning(f"Generated unit test for {requirement.id} failed syntax validation, using fallback")
                test_code = self._generate_fallback_test(requirement)
            
            # Write test file
            test_dir = output_dir / "tests"
            test_dir.mkdir(exist_ok=True)
            
            test_filename = f"test_{requirement.id.lower().replace('-', '_')}.py"
            test_file = test_dir / test_filename
            
            with open(test_file, 'w') as f:
                f.write(test_code)
            
            logger.info(f"Generated unit test: {test_file}")
            return str(test_file)
            
        except Exception as e:
            logger.error(f"Failed to generate unit test for {requirement.id}: {e}")
            return None
    
    def _generate_integration_test(self, requirement: Requirement, source_code: str, output_dir: Path) -> Optional[str]:
        """
        Generate an integration test for a specific requirement.
        
        Args:
            requirement: The requirement to generate tests for
            source_code: The generated source code (for context)
            output_dir: Directory to write the test file
            
        Returns:
            Path to the generated test file, or None if generation failed
        """
        try:
            # Prepare the prompt for integration test generation
            prompt = f"""
Generate comprehensive pytest integration tests for the following requirement:

Requirement ID: {requirement.id}
Title: {requirement.title}
Description: {requirement.description}

IMPORTANT: This is an INTEGRATION test. The test should:
1. Test multiple components working together
2. Verify end-to-end functionality
3. Use realistic data and scenarios
4. Test the complete workflow described in the requirement

Generate tests that verify:
- Correct functionality
- Edge cases
- Error conditions
- Type safety
- Integration between components

Return only the test code without explanations.
"""
            
            # Generate test code
            logger.info(f"Generating integration test for requirement: {requirement.id}")
            test_code = self.ollama_client.generate_code(prompt)
            
            # Clean up markdown formatting
            test_code = self._strip_markdown_code_blocks(test_code)
            
            # Validate the generated test code
            if not self._validate_python_code(test_code):
                logger.warning(f"Generated integration test for {requirement.id} failed syntax validation, using fallback")
                test_code = self._generate_fallback_test(requirement)
            
            # Write test file
            test_dir = output_dir / "tests"
            test_dir.mkdir(exist_ok=True)
            
            test_filename = f"test_{requirement.id.lower().replace('-', '_')}_integration.py"
            test_file = test_dir / test_filename
            
            with open(test_file, 'w') as f:
                f.write(test_code)
            
            logger.info(f"Generated integration test: {test_file}")
            return str(test_file)
            
        except Exception as e:
            logger.error(f"Failed to generate integration test for {requirement.id}: {e}")
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
        """
        Clean and validate AI-generated code to ensure it's executable and well-formatted.
        
        This private method processes raw AI-generated code to fix common issues,
        remove problematic content, and ensure the code is syntactically correct.
        It handles various artifacts that AI models might introduce during generation.
        
        Args:
            generated_code: Raw code string from AI model that may contain formatting
                           issues, instructional text, or other problematic elements.
        
        Returns:
            Cleaned code string that is syntactically valid and ready for execution.
            The method removes problematic elements while preserving functional code.
        
        Note:
            The cleaning process includes:
            - Removing instructional comments and notes
            - Fixing indentation issues
            - Removing template placeholders
            - Ensuring proper function structure
            - Validating Python syntax
        
        Example:
            >>> raw_code = '''
            ... # TODO: Implement this function
            ... def example():
            ...     # Replace with your implementation
            ...     pass
            ... '''
            >>> clean_code = generator._clean_generated_code(raw_code)
            >>> assert 'TODO:' not in clean_code
            >>> assert 'def example():' in clean_code
        """
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
        """
        Validate that generated Python code is syntactically correct.
        
        This private method performs syntax validation on generated code to ensure
        it can be executed without Python syntax errors. It uses the built-in
        compile() function to check syntax without actually executing the code.
        
        Args:
            code: Python code string to validate for syntax correctness.
        
        Returns:
            True if the code is syntactically valid Python, False otherwise.
        
        Note:
            This method only checks syntax, not runtime errors or logical issues.
            It's a fast way to catch obvious generation problems before writing
            code to files.
        
        Example:
            >>> valid_code = "def hello():\n    print('Hello')"
            >>> invalid_code = "def hello()\n    print('Hello')"  # Missing colon
            >>> generator._validate_python_code(valid_code)
            True
            >>> generator._validate_python_code(invalid_code)
            False
        """
        """Validate that the generated code is syntactically valid Python."""
        if not code.strip():
            return False
        
        try:
            import ast
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
            
            test_filename = f"test_{requirement.id.lower().replace('-', '_')}_integration.py"
            test_file = test_dir / test_filename
            
            with open(test_file, 'w') as f:
                f.write(test_code)
            
            logger.info(f"Generated integration test: {test_file}")
            return str(test_file)
            
        except Exception as e:
            logger.error(f"Failed to generate integration test for {requirement.id}: {e}")
            return None
    
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
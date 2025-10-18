"""
Comprehensive test suite for the CodeGenerator class.
"""

import pytest
import json
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime

from ..generator import CodeGenerator, GenerationResult


class TestCodeGenerator:
    """Test cases for CodeGenerator class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a mock configuration file."""
        config = {
            'model': {
                'model': 'test-model',
                'temperature': 0.7,
                'max_tokens': 1000
            },
            'generation': {
                'overwrite': True
            }
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))
        return config_file
    
    @pytest.fixture
    def sample_spec_file(self, temp_dir):
        """Create a sample OpenSpec YAML file for testing."""
        spec_content = """
spec_id: "test-001"
title: "Test Specification"
version: "1.0.0"
description: "A test specification for testing purposes"
requirements:
  - id: "req-001"
    title: "Test Requirement"
    description: "A test requirement"
    validation:
      - type: "unit"
        target: "test_function"
"""
        spec_file = temp_dir / "test_spec.yml"
        spec_file.write_text(spec_content)
        return spec_file
    
    def test_init_with_config(self, mock_config):
        """Test generator initialization with custom config."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            generator = CodeGenerator(config_path=mock_config)
            
            assert generator.config['model']['model'] == 'test-model'
            assert generator.config['generation']['overwrite'] is True
            mock_parser_class.assert_called_once()
            mock_ollama_class.assert_called_once()
            mock_templates_class.assert_called_once()
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        with patch('generator.SpecParser'), \
             patch('generator.OllamaClient'), \
             patch('generator.PromptTemplates'):
            
            generator = CodeGenerator()
            
            # Test various filename formats
            assert generator._sanitize_filename("test-spec") == "test_spec"
            assert generator._sanitize_filename("test spec") == "test_spec"
            assert generator._sanitize_filename("Test-Spec With Spaces") == "Test_Spec_With_Spaces"
            assert generator._sanitize_filename("already_good") == "already_good"
    
    def test_load_config_default_path(self):
        """Test loading config from default path."""
        with patch('generator.SpecParser'), \
             patch('generator.OllamaClient'), \
             patch('generator.PromptTemplates'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump({'model': {'model': 'default'}}))):
            
            generator = CodeGenerator(config_path=None)
            
            assert 'model' in generator.config
    
    def test_generate_from_spec_success(self, mock_config, sample_spec_file, temp_dir):
        """Test successful generation from spec."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            
            # Mock spec parsing
            mock_spec = Mock()
            mock_spec.spec_id = "test-001"
            mock_spec.title = "Test Specification"
            mock_spec.version = "1.0.0"
            mock_spec.requirements = []
            mock_parser.parse_file.return_value = mock_spec
            mock_parser.validate_spec.return_value = []
            
            # Mock Ollama response
            mock_ollama.generate.return_value = "def test_function():\n    return True"
            
            # Mock templates
            mock_templates.get_generation_prompt.return_value = "Generate code"
            
            # Create generator and run generation
            generator = CodeGenerator(config_path=mock_config)
            output_dir = temp_dir / "output"
            result = generator.generate_from_spec(sample_spec_file, output_dir)
            
            # Verify success
            assert result.success
            assert len(result.files_generated) > 0
            assert result.execution_time > 0
    
    def test_generate_from_spec_overwrite_disabled(self, mock_config, sample_spec_file, temp_dir):
        """Test generation when overwrite is disabled and directory exists."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Create config with overwrite disabled
            config_content = {
                'model': {'model': 'test-model'},
                'generation': {'overwrite': False}
            }
            config_file = temp_dir / "config_no_overwrite.yaml"
            config_file.write_text(yaml.dump(config_content))
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            
            # Create generator
            generator = CodeGenerator(config_path=config_file)
            output_dir = temp_dir / "output"
            
            # Create existing output directory with files
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "existing_file.py").write_text("existing code")
            
            # Run generation
            result = generator.generate_from_spec(sample_spec_file, output_dir)
            
            # Verify failure due to overwrite disabled
            assert not result.success
            assert "overwrite=False" in result.errors[0]
    
    def test_generate_from_spec_overwrite_enabled(self, mock_config, sample_spec_file, temp_dir):
        """Test generation when overwrite is enabled and directory exists."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            
            # Mock spec parsing
            mock_spec = Mock()
            mock_spec.spec_id = "test-001"
            mock_spec.title = "Test Specification"
            mock_spec.version = "1.0.0"
            mock_spec.requirements = []
            mock_parser.parse_file.return_value = mock_spec
            mock_parser.validate_spec.return_value = []
            
            # Mock Ollama response
            mock_ollama.generate.return_value = "def new_function():\n    return True"
            
            # Mock templates
            mock_templates.get_generation_prompt.return_value = "Generate code"
            
            # Create generator and run generation
            generator = CodeGenerator(config_path=mock_config)
            output_dir = temp_dir / "output"
            
            # Create existing output directory with files
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "existing_file.py").write_text("existing code")
            
            result = generator.generate_from_spec(sample_spec_file, output_dir)
            
            # Verify success and that old files were removed
            assert result.success
            assert len(result.files_generated) > 0
    
    def test_generate_from_spec_validation_errors(self, mock_config, sample_spec_file, temp_dir):
        """Test generation when spec validation fails."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            
            # Create generator
            generator = CodeGenerator(config_path=mock_config)
            output_dir = temp_dir / "output"
            
            # Mock spec parsing with validation errors
            mock_spec = Mock()
            mock_parser.parse_file.return_value = mock_spec
            mock_parser.validate_spec.return_value = ["Validation error 1", "Validation error 2"]
            
            # Run generation
            result = generator.generate_from_spec(sample_spec_file, output_dir)
            
            # Verify success but with warnings for validation issues
            assert result.success
            assert len(result.errors) == 0
            assert len(result.warnings) == 2
            assert "Spec validation issue: Validation error 1" in result.warnings
            assert "Spec validation issue: Validation error 2" in result.warnings
    
    def test_generate_from_spec_parse_error(self, mock_config, sample_spec_file, temp_dir):
        """Test generation when spec parsing fails."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            
            # Create generator
            generator = CodeGenerator(config_path=mock_config)
            output_dir = temp_dir / "output"
            
            # Mock spec parsing to raise exception
            mock_parser.parse_file.side_effect = Exception("Parse error")
            
            # Run generation
            result = generator.generate_from_spec(sample_spec_file, output_dir)
            
            # Verify failure due to parse error
            assert not result.success
            assert len(result.errors) > 0
            assert "Parse error" in result.errors[0]
    
    def test_generate_from_spec_default_output_dir(self, mock_config, sample_spec_file, temp_dir):
        """Test generation with default output directory."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            
            # Mock spec parsing
            mock_spec = Mock()
            mock_spec.spec_id = "test-001"
            mock_spec.title = "Test Specification"
            mock_spec.version = "1.0.0"
            mock_spec.requirements = []
            mock_parser.parse_file.return_value = mock_spec
            mock_parser.validate_spec.return_value = []
            
            # Mock Ollama response
            mock_ollama.generate.return_value = "def default_test():\n    return 'default'"
            
            # Mock templates
            mock_templates.get_generation_prompt.return_value = "Generate code"
            
            # Create generator and run generation without output_dir
            generator = CodeGenerator(config_path=mock_config)
            result = generator.generate_from_spec(sample_spec_file)
            
            # Verify success and default output directory
            assert result.success
            assert len(result.files_generated) > 0
    
    def test_generate_from_spec_ollama_error(self, mock_config, sample_spec_file, temp_dir):
        """Test generation when Ollama client fails."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            
            # Mock spec parsing
            mock_spec = Mock()
            mock_spec.spec_id = "test-001"
            mock_spec.title = "Test Specification"
            mock_spec.version = "1.0.0"
            mock_spec.requirements = []
            mock_parser.parse_file.return_value = mock_spec
            mock_parser.validate_spec.return_value = []
            
            # Mock Ollama to raise exception
            mock_ollama.generate.side_effect = Exception("Ollama error")
            
            # Mock templates
            mock_templates.get_generation_prompt.return_value = "Generate code"
            
            # Create generator and run generation
            generator = CodeGenerator(config_path=mock_config)
            output_dir = temp_dir / "output"
            
            result = generator.generate_from_spec(sample_spec_file, output_dir)
            
            # Verify partial success - some files generated despite Ollama error
            assert result.success
            assert len(result.files_generated) > 0
            # Should have CI config, validation script, and requirements but no source or docs
            file_types = [f for f in result.files_generated if any(x in f for x in ['ci.yml', 'validate.sh', 'requirements.txt'])]
            assert len(file_types) >= 2  # At least CI and validation


class TestCodeGeneratorPrivateMethods:
    """Test cases for CodeGenerator private methods."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a mock configuration file."""
        config = {
            'model': {
                'model': 'test-model',
                'temperature': 0.7,
                'max_tokens': 1000
            },
            'generation': {
                'overwrite': True
            }
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))
        return config_file
    
    def test_generate_source_code_success(self, mock_config, temp_dir):
        """Test successful source code generation."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.format_requirements_for_prompt.return_value = "req1, req2"
            mock_parser.format_interfaces_for_prompt.return_value = "interface1, interface2"
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.generate_code.return_value = "def test_function():\n    return True"
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            mock_templates.source_code_prompt.format.return_value = "Generated prompt"
            
            # Create generator
            generator = CodeGenerator(config_path=mock_config)
            
            # Create mock spec
            mock_spec = Mock()
            mock_spec.spec_id = "test-001"
            mock_spec.title = "Test Specification"
            mock_spec.version = "1.0.0"
            
            # Test source code generation
            output_dir = temp_dir / "output"
            result = generator._generate_source_code(mock_spec, output_dir)
            
            # Verify success
            assert result is not None
            assert result.endswith("test_001.py")  # Note: sanitized filename
            assert Path(result).exists()
            assert "def test_function():" in Path(result).read_text()
    
    def test_generate_source_code_ollama_failure(self, mock_config, temp_dir):
        """Test source code generation when Ollama fails."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.format_requirements_for_prompt.return_value = "req1, req2"
            mock_parser.format_interfaces_for_prompt.return_value = "interface1, interface2"
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.generate_code.side_effect = Exception("Ollama error")
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            mock_templates.source_code_prompt.format.return_value = "Generated prompt"
            
            # Create generator
            generator = CodeGenerator(config_path=mock_config)
            
            # Create mock spec
            mock_spec = Mock()
            mock_spec.spec_id = "test-001"
            mock_spec.title = "Test Specification"
            mock_spec.version = "1.0.0"
            
            # Test source code generation
            output_dir = temp_dir / "output"
            result = generator._generate_source_code(mock_spec, output_dir)
            
            # Verify failure returns None
            assert result is None
    
    def test_generate_documentation_success(self, mock_config, temp_dir):
        """Test successful documentation generation."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Setup mocks
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.format_requirements_for_prompt.return_value = "req1, req2"
            
            mock_ollama = Mock()
            mock_ollama_class.return_value = mock_ollama
            mock_ollama.generate.return_value = "# Test Documentation\n\nThis is test documentation."
            
            mock_templates = Mock()
            mock_templates_class.return_value = mock_templates
            mock_templates.documentation_prompt.format.return_value = "Generated doc prompt"
            
            # Create generator
            generator = CodeGenerator(config_path=mock_config)
            
            # Create mock spec
            mock_spec = Mock()
            mock_spec.spec_id = "test-001"
            mock_spec.title = "Test Specification"
            mock_spec.version = "1.0.0"
            
            # Test documentation generation
            output_dir = temp_dir / "output"
            result = generator._generate_documentation(mock_spec, output_dir)
            
            # Verify success
            assert result is not None
            assert result.endswith("test_001.md")  # Note: sanitized filename in docs folder
            assert Path(result).exists()
            content = Path(result).read_text()
            assert "# Test Documentation" in content
    
    def test_generate_validation_script_success(self, temp_dir):
        """Test successful validation script generation."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Create generator
            generator = CodeGenerator()
            
            # Test validation script generation
            output_dir = temp_dir / "output"
            result = generator._generate_validation_script(output_dir)
            
            # Verify success
            assert result is not None
            assert result.endswith("validate.sh")
            assert Path(result).exists()
            content = Path(result).read_text()
            assert "#!/usr/bin/env bash" in content  # Actual shebang used
            assert "pytest" in content.lower()
    
    def test_generate_requirements_file_success(self, temp_dir):
        """Test successful requirements file generation."""
        with patch('src.asabaal_utils.agents.spec_coder.generator.SpecParser') as mock_parser_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.OllamaClient') as mock_ollama_class, \
             patch('src.asabaal_utils.agents.spec_coder.generator.PromptTemplates') as mock_templates_class:
            
            # Create generator
            generator = CodeGenerator()
            
            # Test requirements file generation
            output_dir = temp_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)  # Create directory first
            result = generator._generate_requirements_file(output_dir)
            
            # Verify success
            assert result is not None
            assert result.endswith("requirements.txt")
            assert Path(result).exists()
            content = Path(result).read_text()
            assert "pytest" in content and "ruff" in content  # Actual dependencies


class TestGenerationResult:
    """Test cases for GenerationResult class."""
    
    def test_generation_result_creation(self):
        """Test creating a successful GenerationResult."""
        result = GenerationResult(
            success=True,
            files_generated=["file1.py", "file2.py"],
            errors=[],
            warnings=["Minor warning"],
            execution_time=1.5
        )
        
        assert result.success is True
        assert len(result.files_generated) == 2
        assert "file1.py" in result.files_generated
        assert "file2.py" in result.files_generated
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Minor warning"
        assert result.execution_time == 1.5
    
    def test_generation_result_failure(self):
        """Test creating a failed GenerationResult."""
        result = GenerationResult(
            success=False,
            files_generated=[],
            errors=["Major error", "Another error"],
            warnings=[],
            execution_time=0.5
        )
        
        assert result.success is False
        assert len(result.files_generated) == 0
        assert len(result.errors) == 2
        assert "Major error" in result.errors
        assert "Another error" in result.errors
        assert len(result.warnings) == 0
        assert result.execution_time == 0.5


    def test_strip_markdown_code_blocks_basic(self):
        """Test basic markdown code block stripping."""
        generator = CodeGenerator()
        
        # Test with ```python wrapper
        content = "```python\ndef test_function():\n    return True\n```"
        result = generator._strip_markdown_code_blocks(content)
        expected = "def test_function():\n    return True"
        assert result == expected
    
    def test_strip_markdown_code_blocks_with_instructions(self):
        """Test stripping instructional text that causes IndentationError."""
        generator = CodeGenerator()
        
        # Test content that would cause IndentationError
        content = """ pytest test code only.

import pytest
from unittest.mock import patch, MagicMock

def test_generate_time_grid_happy_path():
    result = generate_time_grid(120, 4)
    assert len(result) > 0"""
        
        result = generator._strip_markdown_code_blocks(content)
        
        # Should remove the instructional line
        lines = result.split('\n')
        assert not any('pytest test code only' in line for line in lines)
        assert 'import pytest' in result
        assert 'def test_generate_time_grid_happy_path' in result
        
        # Should be valid Python that can be parsed
        import ast
        try:
            ast.parse(result)
        except SyntaxError:
            pytest.fail("Stripped content should be valid Python")
    
    def test_strip_markdown_code_blocks_various_instructions(self):
        """Test stripping various types of instructional text."""
        generator = CodeGenerator()
        
        test_cases = [
            ("The test code must be complete and executable as a single pytest file.\nimport pytest", "import pytest"),
            ("Generate comprehensive pytest tests for the following:\nimport pytest", "import pytest"),
            ("Note: This is a test file\nimport pytest", "import pytest"),
            ("TODO: Add more tests\nimport pytest", "import pytest"),
            ("Here is the test code:\nimport pytest", "import pytest"),
            ("The following code implements:\nimport pytest", "import pytest"),
        ]
        
        for input_content, expected_start in test_cases:
            result = generator._strip_markdown_code_blocks(input_content)
            assert result.strip().startswith(expected_start.strip()), f"Failed on: {input_content}"
            
            # Should be valid Python
            import ast
            try:
                ast.parse(result)
            except SyntaxError:
                pytest.fail(f"Stripped content should be valid Python: {result}")
    
    def test_strip_markdown_code_blocks_preserve_valid_code(self):
        """Test that valid code is preserved while stripping instructions."""
        generator = CodeGenerator()
        
        content = """```python
import pytest
from unittest.mock import patch, MagicMock

def test_function_happy_path():
    result = some_function(1, 2)
    assert result == 3

def test_function_edge_case():
    with pytest.raises(ValueError):
        some_function(-1, 0)
```"""
        
        result = generator._strip_markdown_code_blocks(content)
        
        # Should preserve all valid code
        assert 'import pytest' in result
        assert 'def test_function_happy_path' in result
        assert 'def test_function_edge_case' in result
        assert 'assert result == 3' in result
        assert 'pytest.raises(ValueError)' in result
        
        # Should be valid Python
        import ast
        try:
            ast.parse(result)
        except SyntaxError:
            pytest.fail("Stripped content should be valid Python")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
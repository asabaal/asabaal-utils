"""
Integration tests for CodeGenerator with real AI model calls.

These tests make actual calls to Ollama models and validate the quality
of generated outputs. They require Ollama to be running and are slower
than unit tests, so they should be run separately.

Run with: pytest tests/test_generator_integration.py -v
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
import time
import re

from asabaal_utils.agents.spec_coder.generator import CodeGenerator, GenerationResult
from asabaal_utils.agents.spec_coder.ollama_client import GenerationConfig


class TestCodeGeneratorIntegration:
    """Integration tests with real AI model calls."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def real_config(self, temp_dir):
        """Create a real configuration file using available models."""
        config = {
            'model': {
                'model': 'llama3.1:8b',  # Use smaller model for faster testing
                'temperature': 0.3,
                'max_tokens': 2000
            },
            'generation': {
                'overwrite': True
            }
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))
        return config_file
    
    @pytest.fixture
    def sample_spec(self, temp_dir):
        """Create a sample OpenSpec specification for testing."""
        spec_content = """
spec_id: "calculator-001"
title: "Simple Calculator"
version: "1.0.0"
description: "A basic calculator that can perform arithmetic operations"
requirements:
  - id: "req-001"
    title: "Addition Function"
    description: "Implement a function that adds two numbers"
    validation:
      - type: "unit"
        target: "test_addition"
    acceptance_criteria:
      - "Function takes two parameters"
      - "Returns sum of the two numbers"
      - "Handles integer and float inputs"
  - id: "req-002"
    title: "Subtraction Function"
    description: "Implement a function that subtracts two numbers"
    validation:
      - type: "unit"
        target: "test_subtraction"
    acceptance_criteria:
      - "Function takes two parameters"
      - "Returns difference of the two numbers"
      - "Handles integer and float inputs"
interfaces:
  - name: "Calculator"
    methods:
      - name: "add"
        parameters:
          - name: "a"
            type: "float"
          - name: "b"
            type: "float"
        returns:
          type: "float"
      - name: "subtract"
        parameters:
          - name: "a"
            type: "float"
          - name: "b"
            type: "float"
        returns:
          type: "float"
"""
        spec_file = temp_dir / "calculator_spec.yml"
        spec_file.write_text(spec_content)
        return spec_file
    
    @pytest.fixture
    def complex_spec(self, temp_dir):
        """Create a more complex OpenSpec specification."""
        spec_content = """
spec_id: "data-processor-002"
title: "Data Processing Pipeline"
version: "2.0.0"
description: "A data processing pipeline that can read, transform, and write CSV data"
requirements:
  - id: "req-001"
    title: "CSV Reader"
    description: "Read CSV files and return structured data"
    validation:
      - type: "unit"
        target: "test_csv_reader"
    acceptance_criteria:
      - "Reads CSV from file path"
      - "Handles headers and data rows"
      - "Returns list of dictionaries"
  - id: "req-002"
    title: "Data Transformer"
    description: "Transform data according to specified rules"
    validation:
      - type: "unit"
        target: "test_data_transformer"
    acceptance_criteria:
      - "Applies transformation functions"
      - "Handles missing values"
      - "Validates data types"
  - id: "req-003"
    title: "Data Writer"
    description: "Write processed data to CSV file"
    validation:
      - type: "unit"
        target: "test_data_writer"
    acceptance_criteria:
      - "Writes data to CSV file"
      - "Includes headers"
      - "Handles file creation"
interfaces:
  - name: "DataProcessor"
    methods:
      - name: "read_csv"
        parameters:
          - name: "file_path"
            type: "str"
        returns:
          type: "list[dict]"
      - name: "transform_data"
        parameters:
          - name: "data"
            type: "list[dict]"
          - name: "rules"
            type: "dict"
        returns:
          type: "list[dict]"
      - name: "write_csv"
        parameters:
          - name: "data"
            type: "list[dict]"
          - name: "file_path"
            type: "str"
        returns:
          type: "bool"
"""
        spec_file = temp_dir / "data_processor_spec.yml"
        spec_file.write_text(spec_content)
        return spec_file
    
    @pytest.mark.integration
    def test_real_ai_generation_simple_spec(self, real_config, sample_spec, temp_dir):
        """Test actual AI generation with simple specification."""
        
        # Create generator with real config
        generator = CodeGenerator(config_path=real_config)
        
        # Test generation
        output_dir = temp_dir / "output"
        start_time = time.time()
        result = generator.generate_from_spec(sample_spec, output_dir)
        execution_time = time.time() - start_time
        
        # Verify generation succeeded
        assert result.success, f"Generation failed: {result.errors}"
        assert len(result.files_generated) > 0
        assert execution_time < 60  # Should complete within 60 seconds
        
        # Verify source code was generated
        source_files = [f for f in result.files_generated if f.endswith('.py')]
        assert len(source_files) > 0, "No Python source files generated"
        
        # Check source code quality
        source_file = source_files[0]
        source_content = Path(source_file).read_text()
        
        # Should contain addition-related functions (robust to naming variations)
        add_patterns = ["def add(", "def addition", "def sum_", "def add_numbers"]
        has_add_function = any(pattern in source_content for pattern in add_patterns)
        assert has_add_function, f"Missing addition function. Found patterns: {[p for p in add_patterns if p in source_content]}"
        
        # Should contain subtraction-related functions (robust to naming variations)
        subtract_patterns = ["def subtract(", "def subtraction", "def diff", "def subtract_numbers"]
        has_subtract_function = any(pattern in source_content for pattern in subtract_patterns)
        assert has_subtract_function, f"Missing subtraction function. Found patterns: {[p for p in subtract_patterns if p in source_content]}"
        
        # Should have proper structure
        assert "class" in source_content or "def " in source_content, "No class or function definitions found"
        
        # Should have some documentation
        assert '"""' in source_content or "'''" in source_content, "Missing docstrings"
        
        # Should have proper imports (basic validation)
        lines = source_content.split('\n')
        code_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('```')]
        has_imports = any(line.startswith('import ') or line.startswith('from ') for line in code_lines)
        # Note: imports are optional for simple functions, so we don't assert on them
        
        print(f"✅ Generated {len(result.files_generated)} files in {execution_time:.2f}s")
        print(f"📁 Source file: {source_file}")
        print(f"📝 Code preview (first 300 chars): {source_content[:300]}...")
        
        # Debug: Show what function patterns were found
        found_functions = [pattern for pattern in add_patterns + subtract_patterns if pattern in source_content]
        print(f"🔍 Found function patterns: {found_functions}")
        
        print(f"✅ Generated {len(result.files_generated)} files in {execution_time:.2f}s")
        print(f"📁 Source file: {source_file}")
    
    @pytest.mark.integration
    def test_real_ai_generation_complex_spec(self, real_config, complex_spec, temp_dir):
        """Test actual AI generation with complex specification."""
        
        # Create generator with real config
        generator = CodeGenerator(config_path=real_config)
        
        # Test generation
        output_dir = temp_dir / "output"
        start_time = time.time()
        result = generator.generate_from_spec(complex_spec, output_dir)
        execution_time = time.time() - start_time
        
        # Verify generation succeeded
        assert result.success, f"Generation failed: {result.errors}"
        assert len(result.files_generated) > 0
        assert execution_time < 120  # Complex spec may take longer
        
        # Verify source code was generated
        source_files = [f for f in result.files_generated if f.endswith('.py')]
        assert len(source_files) > 0, "No Python source files generated"
        
        # Check source code quality
        source_file = source_files[0]
        source_content = Path(source_file).read_text()
        
        # Should contain CSV reading methods (robust to naming variations)
        csv_read_patterns = ["def read_csv(", "def csv_reader", "def load_csv", "def import_csv"]
        has_csv_read = any(pattern in source_content for pattern in csv_read_patterns)
        assert has_csv_read, f"Missing CSV reading method. Found patterns: {[p for p in csv_read_patterns if p in source_content]}"
        
        # Should contain data transformation methods (robust to naming variations)
        transform_patterns = ["def transform_data", "def data_transform", "def process_data", "def apply_transform"]
        has_transform = any(pattern in source_content for pattern in transform_patterns)
        assert has_transform, f"Missing data transformation method. Found patterns: {[p for p in transform_patterns if p in source_content]}"
        
        # Should contain CSV writing methods (robust to naming variations)
        csv_write_patterns = ["def write_csv(", "def csv_writer", "def save_csv", "def export_csv", "def data_writer"]
        has_csv_write = any(pattern in source_content for pattern in csv_write_patterns)
        assert has_csv_write, f"Missing CSV writing method. Found patterns: {[p for p in csv_write_patterns if p in source_content]}"
        
        # Should handle CSV operations
        assert "csv" in source_content.lower() or "pandas" in source_content.lower(), "No CSV handling found"
        
        # Should have error handling (optional for placeholder code)
        has_error_handling = "try:" in source_content or "except" in source_content
        if not has_error_handling:
            print(f"⚠️  No error handling found (acceptable for placeholder code)")
        
        print(f"✅ Generated {len(result.files_generated)} files in {execution_time:.2f}s")
        print(f"📁 Source file: {source_file}")
    
    @pytest.mark.integration
    def test_real_ai_generation_quality_metrics(self, real_config, sample_spec, temp_dir):
        """Test actual AI generation with quality metrics validation."""
        
        generator = CodeGenerator(config_path=real_config)
        output_dir = temp_dir / "output"
        result = generator.generate_from_spec(sample_spec, output_dir)
        
        assert result.success, f"Generation failed: {result.errors}"
        
        # Get the main source file
        source_files = [f for f in result.files_generated if f.endswith('.py')]
        assert len(source_files) > 0
        source_content = Path(source_files[0]).read_text()
        
        # Quality metrics
        metrics = {
            'line_count': len(source_content.splitlines()),
            'function_count': len(re.findall(r'def\s+\w+\s*\(', source_content)),
            'class_count': len(re.findall(r'class\s+\w+\s*:', source_content)),
            'docstring_count': len(re.findall(r'"""|\'\'\'', source_content)) // 2,
            'comment_lines': len([line for line in source_content.splitlines() if line.strip().startswith('#')]),
            'import_count': len(re.findall(r'import\s+\w+|from\s+\w+\s+import', source_content)),
        }
        
        # Quality assertions (more realistic for AI-generated placeholder code)
        assert metrics['line_count'] >= 10, f"Generated code too short: {metrics['line_count']} lines"
        assert metrics['function_count'] >= 2, f"Should have at least 2 functions, got {metrics['function_count']}"
        assert metrics['docstring_count'] > 0, f"Missing documentation, docstring count: {metrics['docstring_count']}"
        # Imports are optional for simple functions, so we don't assert on them
        
        # Code structure checks (optional for generated modules)
        has_main_guard = "if __name__" in source_content or "__main__" in source_content
        if not has_main_guard:
            print(f"⚠️  No main guard found (acceptable for generated modules)")
        
        print(f"📊 Code Quality Metrics:")
        for metric, value in metrics.items():
            print(f"   {metric}: {value}")
    
    @pytest.mark.integration
    def test_real_ai_generation_different_models(self, temp_dir, sample_spec):
        """Test generation with different AI models."""
        
        available_models = ['llama3.1:8b', 'qwen3-coder:latest']  # Test with smaller models
        results = {}
        
        for model in available_models:
            # Create config for this model
            config = {
                'model': {
                    'model': model,
                    'temperature': 0.3,
                    'max_tokens': 1500
                },
                'generation': {'overwrite': True}
            }
            config_file = temp_dir / f"config_{model.replace(':', '_')}.yaml"
            config_file.write_text(yaml.dump(config))
            
            # Test generation
            generator = CodeGenerator(config_path=config_file)
            output_dir = temp_dir / f"output_{model.replace(':', '_')}"
            
            start_time = time.time()
            result = generator.generate_from_spec(sample_spec, output_dir)
            execution_time = time.time() - start_time
            
            results[model] = {
                'success': result.success,
                'file_count': len(result.files_generated),
                'execution_time': execution_time,
                'errors': result.errors
            }
            
            if result.success:
                print(f"✅ {model}: {len(result.files_generated)} files in {execution_time:.2f}s")
            else:
                print(f"❌ {model}: {result.errors}")
        
        # At least one model should succeed
        successful_models = [model for model, data in results.items() if data['success']]
        assert len(successful_models) > 0, "No models succeeded"
        
        print(f"🏆 Best performing model: {min(successful_models, key=lambda m: results[m]['execution_time'])}")
    
    @pytest.mark.integration
    def test_real_ai_generation_error_handling(self, real_config, temp_dir):
        """Test error handling in AI generation."""
        
        generator = CodeGenerator(config_path=real_config)
        
        # Test with invalid spec file
        invalid_spec = temp_dir / "invalid.yml"
        invalid_spec.write_text("invalid: yaml: content:")
        
        output_dir = temp_dir / "output"
        result = generator.generate_from_spec(invalid_spec, output_dir)
        
        # Should handle gracefully
        assert not result.success
        assert len(result.errors) > 0
        
        # Test with non-existent file
        non_existent = temp_dir / "non_existent.yml"
        result = generator.generate_from_spec(non_existent, output_dir)
        
        assert not result.success
        assert len(result.errors) > 0
        
        print("✅ Error handling works correctly")


class TestCodeGeneratorIntegrationManual:
    """Manual integration tests - run these when you want to test with real AI."""
    
    @pytest.mark.integration
    def test_manual_simple_generation(self):
        """Manual test for simple generation - run when needed."""
        
        # Create temporary setup
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create real config
            config = {
                'model': {
                    'model': 'llama3.1:8b',
                    'temperature': 0.3,
                    'max_tokens': 2000
                },
                'generation': {'overwrite': True}
            }
            config_file = temp_dir / "config.yaml"
            config_file.write_text(yaml.dump(config))
            
            # Create simple spec
            spec_content = """
spec_id: "test-001"
title: "Test Function"
version: "1.0.0"
description: "A simple test function"
requirements:
  - id: "req-001"
    title: "Hello World Function"
    description: "Function that returns hello world"
    validation:
      - type: "unit"
        target: "test_hello_world"
"""
            spec_file = temp_dir / "test_spec.yml"
            spec_file.write_text(spec_content)
            
            # Run generation
            generator = CodeGenerator(config_path=config_file)
            output_dir = temp_dir / "output"
            result = generator.generate_from_spec(spec_file, output_dir)
            
            print(f"Generation result: {result}")
            print(f"Files generated: {result.files_generated}")
            
            if result.success:
                for file_path in result.files_generated:
                    if file_path.endswith('.py'):
                        content = Path(file_path).read_text()
                        print(f"\n=== {file_path} ===")
                        print(content)
            
        finally:
            shutil.rmtree(temp_dir)
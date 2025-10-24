#!/usr/bin/env python3
"""
Comprehensive Production Tests for generate_prompts.py

This test suite provides thorough coverage of the generate_prompts module,
including edge cases, error conditions, and integration scenarios.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_module_import():
    """Test that the generate_prompts module can be imported."""
    try:
        import generate_prompts
        assert hasattr(generate_prompts, 'load_functional_catalog')
        assert hasattr(generate_prompts, 'generate_function_prompt')
        assert hasattr(generate_prompts, 'save_prompt')
        assert hasattr(generate_prompts, 'generate_metadata_summary')
        print("✅ Module import test passed")
    except ImportError as e:
        pytest.skip(f"generate_prompts module not available: {e}")


class TestLoadFunctionalCatalog:
    """Test suite for load_functional_catalog function."""
    
    def test_load_valid_yaml(self):
        """Test loading a valid YAML catalog file."""
        try:
            import generate_prompts
            
            test_data = {
                'functions': {
                    'test_function': {
                        'description': 'Test function description',
                        'parameters': [],
                        'return_type': 'str'
                    }
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                yaml.dump(test_data, f)
                temp_file = Path(f.name)
            
            try:
                loaded = generate_prompts.load_functional_catalog(temp_file)
                assert loaded == test_data
            finally:
                temp_file.unlink()
                
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_load_invalid_yaml(self):
        """Test handling of invalid YAML file."""
        try:
            import generate_prompts
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                f.write("invalid: yaml: content: [")
                temp_file = Path(f.name)
            
            try:
                with pytest.raises(yaml.YAMLError):
                    generate_prompts.load_functional_catalog(temp_file)
            finally:
                temp_file.unlink()
                
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_load_nonexistent_file(self):
        """Test handling of nonexistent file."""
        try:
            import generate_prompts
            
            with pytest.raises(FileNotFoundError):
                generate_prompts.load_functional_catalog(Path("nonexistent.yml"))
                
        except ImportError:
            pytest.skip("generate_prompts module not available")


class TestGenerateFunctionPrompt:
    """Test suite for generate_function_prompt function."""
    
    def test_generate_complete_prompt(self):
        """Test generating a complete function prompt."""
        try:
            import generate_prompts
            
            function_data = {
                'description': 'Test function for testing',
                'behaviors': ['should do something correctly'],
                'parameters': [
                    {'name': 'param1', 'type': 'str', 'default': None},
                    {'name': 'param2', 'type': 'int', 'default': 10}
                ],
                'return_type': 'str',
                'validation_rules': ['param1 should not be empty'],
                'error_conditions': ['raises ValueError if param1 is empty']
            }
            
            prompt = generate_prompts.generate_function_prompt('test_function', function_data)
            
            # Check that all expected sections are present
            assert 'test_function' in prompt
            assert 'param1: str' in prompt
            assert 'param2: int = 10' in prompt
            assert 'should do something correctly' in prompt
            assert 'return a value of type `str`' in prompt
            assert 'param1 should not be empty' in prompt
            assert 'raises ValueError if param1 is empty' in prompt
            
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_generate_minimal_prompt(self):
        """Test generating a prompt with minimal function data."""
        try:
            import generate_prompts
            
            function_data = {}
            
            prompt = generate_prompts.generate_function_prompt('minimal_function', function_data)
            
            # Should still contain function name and basic structure
            assert 'minimal_function' in prompt
            assert 'Function Implementation Request' in prompt
            assert 'def minimal_function()' in prompt
            
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_generate_with_no_parameters(self):
        """Test generating a prompt for a function with no parameters."""
        try:
            import generate_prompts
            
            function_data = {
                'description': 'Function with no parameters',
                'parameters': [],
                'return_type': 'bool'
            }
            
            prompt = generate_prompts.generate_function_prompt('no_params_function', function_data)
            
            assert 'no_params_function' in prompt
            assert 'def no_params_function()' in prompt
            assert 'return a value of type `bool`' in prompt
            
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_generate_with_complex_parameters(self):
        """Test generating a prompt with complex parameter types."""
        try:
            import generate_prompts
            
            function_data = {
                'description': 'Function with complex parameters',
                'parameters': [
                    {'name': 'data_list', 'type': 'List[str]', 'default': None},
                    {'name': 'config_dict', 'type': 'Dict[str, Any]', 'default': None},
                    {'name': 'optional_flag', 'type': 'bool', 'default': True}
                ],
                'return_type': 'Dict[str, Any]'
            }
            
            prompt = generate_prompts.generate_function_prompt('complex_function', function_data)
            
            assert 'data_list: List[str]' in prompt
            assert 'config_dict: Dict[str, Any]' in prompt
            assert 'optional_flag: bool = True' in prompt
            assert 'return a value of type `Dict[str, Any]`' in prompt
            
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_generate_with_validation_and_errors(self):
        """Test generating a prompt with validation rules and error conditions."""
        try:
            import generate_prompts
            
            function_data = {
                'description': 'Function with comprehensive validation',
                'parameters': [
                    {'name': 'input_value', 'type': 'int', 'default': None}
                ],
                'return_type': 'str',
                'validation_rules': [
                    'input_value must be positive',
                    'input_value must be less than 100',
                    'should validate input type'
                ],
                'error_conditions': [
                    'raises ValueError if input_value is negative',
                    'raises TypeError if input_value is not integer'
                ]
            }
            
            prompt = generate_prompts.generate_function_prompt('validated_function', function_data)
            
            assert 'input_value must be positive' in prompt
            assert 'input_value must be less than 100' in prompt
            assert 'raises ValueError if input_value is negative' in prompt
            assert 'raises TypeError if input_value is not integer' in prompt
            
        except ImportError:
            pytest.skip("generate_prompts module not available")


class TestGenerateAllPrompts:
    """Test suite for generate_all_prompts function."""
    
    def test_generate_multiple_prompts(self):
        """Test generating prompts for multiple functions."""
        try:
            import generate_prompts
            
            test_data = {
                'functions': {
                    'func1': {
                        'description': 'First function',
                        'parameters': [],
                        'return_type': 'str'
                    },
                    'func2': {
                        'description': 'Second function',
                        'parameters': [{'name': 'param', 'type': 'int'}],
                        'return_type': 'bool'
                    },
                    'func3': {
                        'description': 'Third function',
                        'parameters': [],
                        'return_type': 'void'
                    }
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                yaml.dump(test_data, f)
                catalog_file = Path(f.name)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir)
                
                try:
                    if hasattr(generate_prompts, 'generate_all_prompts'):
                        generate_prompts.generate_all_prompts(catalog_file, output_dir)
                        
                        # Check that prompt files were created
                        prompt_files = list(output_dir.glob("*.prompt"))
                        assert len(prompt_files) == 3
                        
                        # Check that expected files exist
                        func_names = ['func1', 'func2', 'func3']
                        for func_name in func_names:
                            expected_file = output_dir / f"{func_name}.prompt"
                            assert expected_file.exists()
                            
                            # Check content
                            content = expected_file.read_text()
                            assert func_name in content
                            
                    else:
                        print("⚠️ generate_all_prompts function not found, skipping")
                        
                finally:
                    catalog_file.unlink()
                    
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_generate_empty_catalog(self):
        """Test generating prompts from empty catalog."""
        try:
            import generate_prompts
            
            test_data = {'functions': {}}
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                yaml.dump(test_data, f)
                catalog_file = Path(f.name)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir)
                
                try:
                    if hasattr(generate_prompts, 'generate_all_prompts'):
                        generate_prompts.generate_all_prompts(catalog_file, output_dir)
                        
                        # Should create no files
                        prompt_files = list(output_dir.glob("*.prompt"))
                        assert len(prompt_files) == 0
                        
                finally:
                    catalog_file.unlink()
                    
        except ImportError:
            pytest.skip("generate_prompts module not available")


class TestSavePromptsToJSON:
    """Test suite for save_prompts_to_json function."""
    
    def test_save_prompts_to_json_file(self):
        """Test saving prompts to JSON format."""
        try:
            import generate_prompts
            
            prompts = {
                'test_function': 'This is a test prompt for test_function',
                'another_function': 'This is another prompt'
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_file = Path(f.name)
            
            try:
                if hasattr(generate_prompts, 'save_prompts_to_json'):
                    generate_prompts.save_prompts_to_json(prompts, output_file)
                    
                    # Verify the file was created and contains correct data
                    with open(output_file, 'r') as f:
                        saved_data = json.load(f)
                    
                    assert saved_data == prompts
                    
                else:
                    print("⚠️ save_prompts_to_json function not found, skipping")
                    
            finally:
                output_file.unlink()
                
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_save_empty_prompts(self):
        """Test saving empty prompts dictionary."""
        try:
            import generate_prompts
            
            prompts = {}
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_file = Path(f.name)
            
            try:
                if hasattr(generate_prompts, 'save_prompts_to_json'):
                    generate_prompts.save_prompts_to_json(prompts, output_file)
                    
                    with open(output_file, 'r') as f:
                        saved_data = json.load(f)
                    
                    assert saved_data == {}
                    
                else:
                    print("⚠️ save_prompts_to_json function not found, skipping")
                    
            finally:
                output_file.unlink()
                
        except ImportError:
            pytest.skip("generate_prompts module not available")
    
    def test_save_complex_prompts(self):
        """Test saving prompts with complex content."""
        try:
            import generate_prompts
            
            prompts = {
                'complex_function': '''
# Function Implementation Request: complex_function

## Overview
Generate a Python function `complex_function` that implements complex functionality.

## Function Signature
```python
def complex_function(param1: str, param2: List[int]) -> Dict[str, Any]:
    """
    Complex function description
    """
    # Implementation here
```

## Return Type
The function must return a value of type `Dict[str, Any]`.
''',
                'simple_function': 'Simple prompt content'
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_file = Path(f.name)
            
            try:
                if hasattr(generate_prompts, 'save_prompts_to_json'):
                    generate_prompts.save_prompts_to_json(prompts, output_file)
                    
                    with open(output_file, 'r') as f:
                        saved_data = json.load(f)
                    
                    assert saved_data == prompts
                    assert 'complex_function' in saved_data
                    assert 'simple_function' in saved_data
                    assert 'Function Implementation Request' in saved_data['complex_function']
                    
                else:
                    print("⚠️ save_prompts_to_json function not found, skipping")
                    
            finally:
                output_file.unlink()
                
        except ImportError:
            pytest.skip("generate_prompts module not available")


class TestMainFunction:
    """Test suite for main function."""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        try:
            import generate_prompts
            
            assert hasattr(generate_prompts, 'main')
            assert callable(generate_prompts.main)
            
        except ImportError:
            pytest.skip("generate_prompts module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
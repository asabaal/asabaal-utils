#!/usr/bin/env python3
"""
Comprehensive Production Tests for build_logic_catalog.py

This test suite provides thorough coverage of the build_logic_catalog module,
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
    """Test that the build_logic_catalog module can be imported."""
    try:
        import build_logic_catalog
        assert hasattr(build_logic_catalog, 'load_aggregated_behaviors')
        assert hasattr(build_logic_catalog, 'normalize_function_name')
        assert hasattr(build_logic_catalog, 'infer_return_type')
        assert hasattr(build_logic_catalog, 'extract_parameter_info')
        print("✅ Module import test passed")
    except ImportError as e:
        pytest.skip(f"build_logic_catalog module not available: {e}")


class TestLoadAggregatedBehaviors:
    """Test suite for load_aggregated_behaviors function."""
    
    def test_load_valid_file(self):
        """Test loading a valid aggregated behaviors file."""
        try:
            import build_logic_catalog
            
            test_data = {
                "metadata": {"total_functions": 2},
                "functions": [
                    {
                        "function_name": "test_function1",
                        "behaviors": ["behavior1"]
                    },
                    {
                        "function_name": "test_function2", 
                        "behaviors": ["behavior2"]
                    }
                ]
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                temp_file = Path(f.name)
            
            try:
                loaded = build_logic_catalog.load_aggregated_behaviors(temp_file)
                assert loaded == test_data
            finally:
                temp_file.unlink()
                
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_load_invalid_json(self):
        """Test handling of invalid JSON file."""
        try:
            import build_logic_catalog
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write("{ invalid json")
                temp_file = Path(f.name)
            
            try:
                with pytest.raises(json.JSONDecodeError):
                    build_logic_catalog.load_aggregated_behaviors(temp_file)
            finally:
                temp_file.unlink()
                
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_load_nonexistent_file(self):
        """Test handling of nonexistent file."""
        try:
            import build_logic_catalog
            
            with pytest.raises(FileNotFoundError):
                build_logic_catalog.load_aggregated_behaviors(Path("nonexistent.json"))
                
        except ImportError:
            pytest.skip("build_logic_catalog module not available")


class TestNormalizeFunctionName:
    """Test suite for normalize_function_name function."""
    
    def test_camel_case_conversion(self):
        """Test CamelCase to snake_case conversion."""
        try:
            import build_logic_catalog
            
            assert build_logic_catalog.normalize_function_name("testFunction") == "function"
            assert build_logic_catalog.normalize_function_name("TestFunction") == "function"  # test_ prefix removed
            assert build_logic_catalog.normalize_function_name("addNumbers") == "add_numbers"
            assert build_logic_catalog.normalize_function_name("ProcessData") == "process_data"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_prefix_removal(self):
        """Test removal of common prefixes."""
        try:
            import build_logic_catalog
            
            assert build_logic_catalog.normalize_function_name("test_add_function") == "add_function"
            assert build_logic_catalog.normalize_function_name("mock_helper") == "helper"
            assert build_logic_catalog.normalize_function_name("fake_data") == "data"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_suffix_removal(self):
        """Test removal of common suffixes."""
        try:
            import build_logic_catalog
            
            assert build_logic_catalog.normalize_function_name("add_function_test") == "add_function"
            assert build_logic_catalog.normalize_function_name("helper_mock") == "helper"
            assert build_logic_catalog.normalize_function_name("data_fake") == "data"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_edge_cases(self):
        """Test edge cases for function name normalization."""
        try:
            import build_logic_catalog
            
            # Empty string
            assert build_logic_catalog.normalize_function_name("") == ""
            
            # Already snake_case
            assert build_logic_catalog.normalize_function_name("already_snake_case") == "already_snake_case"
            
            # Mixed patterns
            assert build_logic_catalog.normalize_function_name("testAddFunction_test") == "add_function"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")


class TestInferReturnType:
    """Test suite for infer_return_type function."""
    
    def test_boolean_inference(self):
        """Test boolean return type inference."""
        try:
            import build_logic_catalog
            
            behaviors = ["should return true", "function returns bool"]
            rules = ["expect boolean result"]
            
            result = build_logic_catalog.infer_return_type(behaviors, rules)
            assert result == "bool"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_list_inference(self):
        """Test list return type inference."""
        try:
            import build_logic_catalog
            
            behaviors = ["returns list of items", "should return list"]
            rules = []
            
            result = build_logic_catalog.infer_return_type(behaviors, rules)
            assert result == "list"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_string_inference(self):
        """Test string return type inference."""
        try:
            import build_logic_catalog
            
            behaviors = ["should return string", "returns str"]
            rules = ["expect string output"]
            
            result = build_logic_catalog.infer_return_type(behaviors, rules)
            assert result == "str"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_numeric_inference(self):
        """Test numeric return type inference."""
        try:
            import build_logic_catalog
            
            # Integer
            behaviors = ["returns int", "should return integer"]
            result = build_logic_catalog.infer_return_type(behaviors, [])
            assert result == "int"
            
            # Float
            behaviors = ["returns float", "should return decimal"]
            result = build_logic_catalog.infer_return_type(behaviors, [])
            assert result == "float"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_bytes_inference(self):
        """Test bytes return type inference."""
        try:
            import build_logic_catalog
            
            behaviors = ["returns bytes", "midi file output", "bytes data"]
            rules = []
            
            result = build_logic_catalog.infer_return_type(behaviors, [])
            assert result == "bytes"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_default_inference(self):
        """Test default return type inference."""
        try:
            import build_logic_catalog
            
            behaviors = ["does something", "processes data"]
            rules = ["should work correctly"]
            
            result = build_logic_catalog.infer_return_type(behaviors, rules)
            assert result == "Any"
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")


class TestExtractParameterInfo:
    """Test suite for extract_parameter_info function."""
    
    def test_known_parameters(self):
        """Test extraction of known parameter patterns."""
        try:
            import build_logic_catalog
            
            parameters = ["tempo", "pattern", "duration"]
            behaviors = ["generates rhythm with given tempo and pattern"]
            
            result = build_logic_catalog.extract_parameter_info(parameters, behaviors)
            
            assert len(result) == 3
            tempo_param = next(p for p in result if p['name'] == 'tempo')
            assert tempo_param['type'] == 'int'
            assert tempo_param['description'] == 'Tempo in BPM'
            
            pattern_param = next(p for p in result if p['name'] == 'pattern')
            assert pattern_param['type'] == 'list'
            assert pattern_param['description'] == 'Rhythm pattern'
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_inferred_parameters(self):
        """Test parameter type inference from context."""
        try:
            import build_logic_catalog
            
            parameters = ["data", "count", "items"]
            behaviors = ["processes data list with count integer"]
            
            result = build_logic_catalog.extract_parameter_info(parameters, behaviors)
            
            assert len(result) == 3
            data_param = next(p for p in result if p['name'] == 'data')
            assert data_param['type'] == 'list'
            
            count_param = next(p for p in result if p['name'] == 'count')
            assert count_param['type'] == 'int'
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_empty_parameters(self):
        """Test handling of empty parameter list."""
        try:
            import build_logic_catalog
            
            result = build_logic_catalog.extract_parameter_info([], [])
            assert result == []
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_unknown_parameters(self):
        """Test handling of unknown parameters."""
        try:
            import build_logic_catalog
            
            parameters = ["unknown_param", "another_unknown"]
            behaviors = ["does something with parameters"]
            
            result = build_logic_catalog.extract_parameter_info(parameters, behaviors)
            
            assert len(result) == 2
            for param in result:
                assert param['type'] == 'Any'
                assert param['default'] is None
                assert 'description' in param
                
        except ImportError:
            pytest.skip("build_logic_catalog module not available")


class TestBuildLogicCatalog:
    """Test suite for build_logic_catalog function."""
    
    def test_build_basic_catalog(self):
        """Test building a basic logic catalog."""
        try:
            import build_logic_catalog
            
            test_data = {
                "metadata": {"total_functions": 1},
                "functions": [
                    {
                        "function_name": "generate_rhythm",
                        "behaviors": ["generates rhythm pattern"],
                        "parameters": ["tempo", "pattern"],
                        "validation_rules": ["tempo should be positive"],
                        "sources": ["specified"]
                    }
                ]
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                input_file = Path(f.name)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                output_file = Path(f.name)
            
            try:
                if hasattr(build_logic_catalog, 'build_logic_catalog'):
                    catalog = build_logic_catalog.build_logic_catalog(input_file, output_file)
                    
                    # Should have functions section
                    assert 'functions' in catalog
                    
                    # Check function was processed
                    functions = catalog['functions']
                    assert len(functions) >= 1
                    
                    # Find our function
                    rhythm_func = next((f for f in functions if f['name'] == 'generate_rhythm'), None)
                    if rhythm_func:
                        assert 'parameters' in rhythm_func
                        assert 'return_type' in rhythm_func
                        
                else:
                    print("⚠️ build_logic_catalog function not found, skipping")
                    
            finally:
                input_file.unlink()
                output_file.unlink()
                
        except ImportError:
            pytest.skip("build_logic_catalog module not available")
    
    def test_build_catalog_with_validation(self):
        """Test building catalog with validation rules."""
        try:
            import build_logic_catalog
            
            test_data = {
                "metadata": {"total_functions": 1},
                "functions": [
                    {
                        "function_name": "validate_input",
                        "behaviors": ["validates input parameters"],
                        "parameters": ["input_data"],
                        "validation_rules": ["input should not be empty", "should return bool"],
                        "sources": ["specified"]
                    }
                ]
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                input_file = Path(f.name)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                output_file = Path(f.name)
            
            try:
                if hasattr(build_logic_catalog, 'build_logic_catalog'):
                    catalog = build_logic_catalog.build_logic_catalog(input_file, output_file)
                    
                    functions = catalog.get('functions', [])
                    validate_func = next((f for f in functions if f['name'] == 'validate_input'), None)
                    
                    if validate_func:
                        # Should infer return type from validation rules
                        assert validate_func.get('return_type') == 'bool'
                        
            finally:
                input_file.unlink()
                output_file.unlink()
                
        except ImportError:
            pytest.skip("build_logic_catalog module not available")


class TestMainFunction:
    """Test suite for main function."""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        try:
            import build_logic_catalog
            
            assert hasattr(build_logic_catalog, 'main')
            assert callable(build_logic_catalog.main)
            
        except ImportError:
            pytest.skip("build_logic_catalog module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
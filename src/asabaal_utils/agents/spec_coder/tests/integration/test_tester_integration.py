"""
Integration tests for TestAnalyzer/TestSummarizer with real AI model calls.

These tests make actual calls to Ollama models to validate the complete
test analysis workflow: AST parsing + AI summarization.

Run with: pytest tests/test_tester_integration.py -v

Requires:
- Ollama service running on localhost:11434
- Models: qwen3-coder:latest (or other available models)
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path
import time

from asabaal_utils.agents.spec_coder.tester import TestAnalyzer
from asabaal_utils.agents.spec_coder.summarize_tests import TestSummarizer


class TestTestAnalyzerIntegration:
    """Integration tests for TestAnalyzer with real AI calls."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_test_file(self, temp_dir):
        """Create a realistic test file for analysis."""
        test_content = '''
import pytest
import math
from calculator import Calculator

class TestCalculator:
    """Test suite for Calculator class."""
    
    def test_addition_positive_numbers(self):
        """Test adding two positive numbers."""
        calc = Calculator()
        result = calc.add(5, 3)
        assert result == 8
        assert isinstance(result, (int, float))
    
    def test_addition_negative_numbers(self):
        """Test adding two negative numbers."""
        calc = Calculator()
        result = calc.add(-5, -3)
        assert result == -8
    
    def test_addition_mixed_numbers(self):
        """Test adding positive and negative numbers."""
        calc = Calculator()
        result = calc.add(10, -4)
        assert result == 6
    
    def test_addition_with_floats(self):
        """Test adding floating point numbers."""
        calc = Calculator()
        result = calc.add(2.5, 3.7)
        assert abs(result - 6.2) < 0.001
    
    def test_division_by_zero(self):
        """Test that division by zero raises appropriate error."""
        calc = Calculator()
        with pytest.raises(ZeroDivisionError):
            calc.divide(5, 0)
    
    def test_square_root_negative(self):
        """Test square root of negative number."""
        calc = Calculator()
        with pytest.raises(ValueError):
            calc.square_root(-4)
    
    def test_complex_calculation(self):
        """Test complex calculation involving multiple operations."""
        calc = Calculator()
        numbers = [1, 2, 3, 4, 5]
        result = calc.sum_of_squares(numbers)
        expected = 1 + 4 + 9 + 16 + 25  # 55
        assert result == expected
'''
        test_file = temp_dir / "test_calculator.py"
        test_file.write_text(test_content)
        return test_file
    
    @pytest.fixture
    def sample_spec_file(self, temp_dir):
        """Create a sample OpenSpec specification for context."""
        spec_content = {
            'spec_id': 'calculator-001',
            'title': 'Advanced Calculator',
            'version': '1.0.0',
            'description': 'A calculator that performs basic and advanced mathematical operations',
            'requirements': [
                {
                    'id': 'req-001',
                    'title': 'Basic Arithmetic Operations',
                    'description': 'Implement addition, subtraction, multiplication, and division',
                    'validation': [
                        {'type': 'unit', 'target': 'test_addition_positive_numbers'},
                        {'type': 'unit', 'target': 'test_division_by_zero'}
                    ],
                    'interface': {
                        'function': 'add',
                        'parameters': {'a': 'float', 'b': 'float'},
                        'returns': 'float'
                    }
                },
                {
                    'id': 'req-002', 
                    'title': 'Advanced Mathematical Functions',
                    'description': 'Implement square root and power functions',
                    'validation': [
                        {'type': 'unit', 'target': 'test_square_root_negative'}
                    ],
                    'interface': {
                        'function': 'square_root',
                        'parameters': {'x': 'float'},
                        'returns': 'float'
                    }
                }
            ]
        }
        spec_file = temp_dir / "calculator_spec.yml"
        spec_file.write_text(yaml.dump(spec_content))
        return spec_file
    
    @pytest.fixture
    def sample_source_file(self, temp_dir):
        """Create a sample source file for context."""
        source_content = '''
"""
Advanced Calculator Module
Implements basic and advanced mathematical operations.
"""

import math

class Calculator:
    """A calculator that performs various mathematical operations."""
    
    def add(self, a, b):
        """TODO RPG-001: Add two numbers and return the result."""
        pass
    
    def subtract(self, a, b):
        """TODO RPG-001: Subtract b from a and return the result."""
        pass
    
    def multiply(self, a, b):
        """TODO RPG-001: Multiply two numbers and return the result."""
        pass
    
    def divide(self, a, b):
        """TODO RPG-001: Divide a by b and handle division by zero."""
        pass
    
    def square_root(self, x):
        """TODO RPG-002: Calculate square root and handle negative inputs."""
        pass
    
    def sum_of_squares(self, numbers):
        """TODO RPG-002: Calculate sum of squares of a list of numbers."""
        pass
'''
        source_file = temp_dir / "calculator.py"
        source_file.write_text(source_content)
        return source_file
    
    @pytest.mark.integration
    def test_real_ai_single_file_analysis(self, sample_test_file, sample_spec_file, sample_source_file):
        """Test complete analysis of a single test file with real AI."""
        
        # Create analyzer with real context
        analyzer = TestAnalyzer(
            model_name="qwen3-coder:latest",
            spec_file=sample_spec_file,
            source_file=sample_source_file
        )
        
        # Analyze the test file
        start_time = time.time()
        result = analyzer.analyze_single_file(sample_test_file)
        analysis_time = time.time() - start_time
        
        # Verify analysis succeeded
        assert 'error' not in result, f"Analysis failed: {result.get('error', 'Unknown error')}"
        assert 'tests' in result
        assert len(result['tests']) > 0
        assert analysis_time < 30  # Should complete within 30 seconds
        
        # Verify each test has AI-generated summary
        for test in result['tests']:
            assert 'implied_behavior' in test
            assert len(test['implied_behavior']) > 10, "Behavior summary too short"
            assert test['implied_behavior'] != "Error generating summary", "AI generation failed"
            
            # Verify test structure is preserved
            assert 'name' in test
            assert 'target_function' in test
            assert 'inputs' in test
            assert 'assertions' in test
            # Note: Some tests (like pytest.raises) may not have direct assertions
        
        print(f"✅ Analyzed {len(result['tests'])} tests in {analysis_time:.2f}s")
        
        # Print some example summaries for verification
        for i, test in enumerate(result['tests'][:3]):  # Show first 3
            print(f"📝 Test {i+1}: {test['name']}")
            print(f"   Target: {test.get('target_function', 'Unknown')}")
            print(f"   Behavior: {test['implied_behavior']}")
    
    @pytest.mark.integration
    def test_real_ai_directory_analysis(self, temp_dir, sample_spec_file, sample_source_file):
        """Test analysis of multiple test files in directory."""
        
        # Create multiple test files
        test_files = {
            "test_basic_operations.py": '''
import pytest
from calculator import Calculator

def test_add_basic():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_subtract_basic():
    calc = Calculator()
    assert calc.subtract(10, 4) == 6
''',
            "test_advanced_operations.py": '''
import pytest
import math
from calculator import Calculator

def test_square_root_positive():
    calc = Calculator()
    assert calc.square_root(9) == 3.0

def test_power_operation():
    calc = Calculator()
    assert calc.power(2, 3) == 8
''',
            "test_edge_cases.py": '''
import pytest
from calculator import Calculator

def test_large_numbers():
    calc = Calculator()
    result = calc.add(1_000_000, 2_000_000)
    assert result == 3_000_000

def test_precision_floats():
    calc = Calculator()
    result = calc.add(0.1, 0.2)
    assert abs(result - 0.3) < 1e-10
'''
        }
        
        # Write test files
        for filename, content in test_files.items():
            (temp_dir / filename).write_text(content)
        
        # Create analyzer and analyze directory
        analyzer = TestAnalyzer(
            model_name="qwen3-coder:latest",
            spec_file=sample_spec_file,
            source_file=sample_source_file
        )
        
        output_dir = temp_dir / "analysis_output"
        start_time = time.time()
        results = analyzer.analyze_directory(temp_dir, output_dir)
        analysis_time = time.time() - start_time
        
        # Verify analysis succeeded
        assert len(results) == len(test_files), f"Expected {len(test_files)} results, got {len(results)}"
        assert analysis_time < 60  # Should complete within 60 seconds
        
        # Verify output files were created
        assert output_dir.exists()
        summary_files = list(output_dir.glob("test_summary_*.json"))
        assert len(summary_files) == len(test_files)
        
        # Verify combined summary was created
        combined_file = output_dir / "combined_test_summary.json"
        assert combined_file.exists()
        
        # Verify each result has AI summaries
        total_tests = 0
        for result in results:
            assert 'error' not in result
            assert 'tests' in result
            total_tests += len(result['tests'])
            
            for test in result['tests']:
                assert 'implied_behavior' in test
                assert len(test['implied_behavior']) > 10
        
        print(f"✅ Analyzed {total_tests} tests across {len(results)} files in {analysis_time:.2f}s")
    
    @pytest.mark.integration
    def test_real_ai_quality_validation(self, sample_test_file, sample_spec_file, sample_source_file):
        """Test AI-based quality validation of test coverage."""
        
        analyzer = TestAnalyzer(
            model_name="qwen3-coder:latest",
            spec_file=sample_spec_file,
            source_file=sample_source_file
        )
        
        result = analyzer.analyze_single_file(sample_test_file)
        
        # Quality metrics for AI summaries
        total_tests = len(result['tests'])
        quality_metrics = {
            'avg_summary_length': 0,
            'has_function_references': 0,
            'has_behavioral_language': 0,
            'has_error_handling': 0,
            'has_edge_case_mentions': 0
        }
        
        summary_lengths = []
        
        for test in result['tests']:
            behavior = test['implied_behavior']
            summary_lengths.append(len(behavior))
            
            # Check for function references
            if any(word in behavior.lower() for word in ['add', 'divide', 'square_root', 'calculate']):
                quality_metrics['has_function_references'] += 1
            
            # Check for behavioral language
            if any(word in behavior.lower() for word in ['should', 'must', 'expect', 'require', 'handle']):
                quality_metrics['has_behavioral_language'] += 1
            
            # Check for error handling mentions
            if any(word in behavior.lower() for word in ['error', 'exception', 'raise', 'invalid']):
                quality_metrics['has_error_handling'] += 1
            
            # Check for edge case mentions
            if any(word in behavior.lower() for word in ['edge', 'boundary', 'limit', 'zero', 'negative']):
                quality_metrics['has_edge_case_mentions'] += 1
        
        quality_metrics['avg_summary_length'] = sum(summary_lengths) / len(summary_lengths)
        
        # Quality assertions
        assert quality_metrics['avg_summary_length'] > 50, "Summaries too short on average"
        assert quality_metrics['avg_summary_length'] < 300, "Summaries too long on average"
        assert quality_metrics['has_function_references'] > total_tests * 0.5, "Too few function references"
        assert quality_metrics['has_behavioral_language'] > total_tests * 0.7, "Too little behavioral language"
        
        print(f"📊 Quality Metrics:")
        for metric, value in quality_metrics.items():
            if isinstance(value, float):
                print(f"   {metric}: {value:.1f}")
            else:
                print(f"   {metric}: {value}/{total_tests}")
    
    @pytest.mark.integration
    def test_real_ai_error_handling(self, temp_dir):
        """Test error handling with malformed test files."""
        
        # Test with malformed test file
        malformed_test = temp_dir / "test_malformed.py"
        malformed_test.write_text("def test_broken()\n    assert True  # Missing colon")
        
        analyzer = TestAnalyzer()
        result = analyzer.analyze_single_file(malformed_test)
        
        # Should handle parsing errors gracefully
        assert 'error' in result
        assert 'syntax' in result['error'].lower() or 'parse' in result['error'].lower()
        
        # Test with empty test file
        empty_test = temp_dir / "test_empty.py"
        empty_test.write_text("")
        
        result = analyzer.analyze_single_file(empty_test)
        assert 'error' not in result  # Should not have parsing errors
        assert 'tests' in result
        assert len(result['tests']) == 0  # Empty file should have no tests
        
        print("✅ Error handling works correctly")


class TestTestSummarizerIntegration:
    """Integration tests for TestSummarizer component specifically."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.integration
    def test_real_ai_summarizer_with_context(self, temp_dir):
        """Test TestSummarizer with context files."""
        
        # Create context files
        spec_file = temp_dir / "spec.yml"
        spec_file.write_text(yaml.dump({
            'spec_id': 'test-001',
            'requirements': [
                {
                    'id': 'req-001',
                    'title': 'Test Requirement',
                    'description': 'A test requirement for validation',
                    'interface': {
                        'function': 'test_func',
                        'parameters': {'x': 'int'},
                        'returns': 'bool'
                    }
                }
            ]
        }))
        
        source_file = temp_dir / "source.py"
        source_file.write_text('''
def test_func(x):
    """TODO RPG-001: Test function implementation."""
    pass
''')
        
        # Create summarizer with context
        summarizer = TestSummarizer(
            model_name="qwen3-coder:latest",
            spec_file=spec_file,
            source_file=source_file
        )
        
        # Test data
        test_data = {
            'name': 'test_functionality',
            'target_function': 'test_func',
            'inputs': {'x': 5},
            'assertions': ['assert test_func(5) is True']
        }
        
        # Generate summary
        start_time = time.time()
        summary = summarizer.summarize_test(test_data)
        summary_time = time.time() - start_time
        
        # Verify summary quality
        assert summary is not None
        assert len(summary) > 20
        assert summary_time < 30  # Should complete within reasonable time
        assert "Error generating summary" not in summary
        
        # Check that context influenced the summary
        assert any(word in summary.lower() for word in ['test_func', 'requirement', 'validation'])
        
        print(f"✅ Generated summary in {summary_time:.2f}s: {summary}")
    
    @pytest.mark.integration
    def test_real_ai_summarizer_without_context(self):
        """Test TestSummarizer without context files."""
        
        summarizer = TestSummarizer(model_name="qwen3-coder:latest")
        
        test_data = {
            'name': 'test_addition',
            'target_function': 'add',
            'inputs': {'a': 2, 'b': 3},
            'assertions': ['assert add(2, 3) == 5']
        }
        
        summary = summarizer.summarize_test(test_data)
        
        assert summary is not None
        assert len(summary) > 20
        assert "Error generating summary" not in summary
        
        # Should still generate meaningful summary without context
        assert any(word in summary.lower() for word in ['add', 'sum', 'result'])
        
        print(f"✅ Context-free summary: {summary}")
    
    @pytest.mark.integration
    def test_real_ai_summarizer_batch_processing(self):
        """Test batch processing of multiple test files."""
        
        summarizer = TestSummarizer(model_name="qwen3-coder:latest")
        
        # Create test data for multiple tests
        parsed_data = {
            'file': 'test_multiple.py',
            'tests': [
                {
                    'name': 'test_add_positive',
                    'target_function': 'add',
                    'inputs': {'a': 5, 'b': 3},
                    'assertions': ['assert add(5, 3) == 8']
                },
                {
                    'name': 'test_add_negative',
                    'target_function': 'add', 
                    'inputs': {'a': -5, 'b': -3},
                    'assertions': ['assert add(-5, -3) == -8']
                },
                {
                    'name': 'test_divide_by_zero',
                    'target_function': 'divide',
                    'inputs': {'a': 5, 'b': 0},
                    'assertions': ['with pytest.raises(ZeroDivisionError): divide(5, 0)']
                }
            ]
        }
        
        # Process all tests
        start_time = time.time()
        result = summarizer.summarize_test_file(parsed_data)
        processing_time = time.time() - start_time
        
        # Verify results
        assert len(result['tests']) == 3
        assert processing_time < 30  # Should complete within reasonable time
        
        for test in result['tests']:
            assert 'implied_behavior' in test
            assert len(test['implied_behavior']) > 20
        
        print(f"✅ Processed {len(result['tests'])} tests in {processing_time:.2f}s")
        
        # Verify different behaviors are detected
        behaviors = [test['implied_behavior'].lower() for test in result['tests']]
        assert any('positive' in behavior or 'add' in behavior for behavior in behaviors)
        assert any('zero' in behavior or 'error' in behavior for behavior in behaviors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
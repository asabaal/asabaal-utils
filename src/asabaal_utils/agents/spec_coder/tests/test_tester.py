"""
Comprehensive test suite for the Tester class.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from subprocess import CompletedProcess

from ..tester import TestAnalyzer


class TestTestAnalyzer:
    """Test cases for TestAnalyzer class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def analyzer(self):
        """Create a TestAnalyzer instance."""
        with patch('src.asabaal_utils.agents.spec_coder.summarize_tests.OllamaClient') as mock_client:
            mock_client.return_value.test_connection.return_value = True
            # Mock the summarize_test_file method to avoid actual AI calls
            mock_client.return_value.generate.return_value = {"summary": "Mock summary"}
            return TestAnalyzer()
    
    @pytest.fixture
    def sample_test_file(self, temp_dir):
        """Create a sample test file."""
        test_content = '''
import pytest

def test_addition():
    """Test basic addition."""
    assert 1 + 1 == 2

def test_subtraction():
    """Test basic subtraction."""
    assert 5 - 3 == 2

def test_failing():
    """Test that fails."""
    assert False
'''
        test_file = temp_dir / "test_sample.py"
        test_file.write_text(test_content)
        return test_file
    
    def test_init_default(self):
        """Test analyzer initialization with defaults."""
        with patch('src.asabaal_utils.agents.spec_coder.summarize_tests.OllamaClient') as mock_client:
            mock_client.return_value.test_connection.return_value = True
            
            analyzer = TestAnalyzer()
            assert hasattr(analyzer, 'summarizer')
            mock_client.assert_called_once()
    
    def test_init_custom_model(self):
        """Test analyzer initialization with custom model."""
        with patch('src.asabaal_utils.agents.spec_coder.summarize_tests.OllamaClient') as mock_client:
            mock_client.return_value.test_connection.return_value = True
            
            analyzer = TestAnalyzer(model_name="custom-model")
            
            # Check that OllamaClient was called with custom model
            call_args = mock_client.call_args
            config = call_args[0][0]
            assert config.model == "custom-model"
    
    def test_init_connection_failure(self):
        """Test analyzer initialization when Ollama connection fails."""
        with patch('src.asabaal_utils.agents.spec_coder.summarize_tests.OllamaClient') as mock_client:
            mock_client.return_value.test_connection.return_value = False
            
            with pytest.raises(RuntimeError, match="Failed to connect to Ollama"):
                TestAnalyzer()
    
    def test_analyze_single_file_success(self, analyzer, temp_dir):
        """Test successful analysis of a single test file."""
        # Create a test file
        test_file = temp_dir / "test_sample.py"
        test_file.write_text("def test_addition(): assert 1 + 1 == 2")
        
        # Mock the parse_test_file function
        mock_parsed_data = {
            'functions': ['test_addition'],
            'imports': [],
            'assertions': ['assert 1 + 1 == 2']
        }
        
        # Mock the summarizer
        mock_summary = {
            'file_path': str(test_file),
            'summary': 'Test verifies addition functionality',
            'behaviors': ['adds numbers correctly']
        }
        
        with patch('asabaal_utils.agents.spec_coder.parse_tests.parse_test_file', return_value=mock_parsed_data), \
             patch.object(analyzer.summarizer, 'summarize_test_file', return_value=mock_summary):
            
            result = analyzer.analyze_single_file(test_file)
            
            assert result['summary'] == 'Test verifies addition functionality'
            assert 'behaviors' in result
    
    def test_analyze_single_file_parse_error(self, analyzer, temp_dir):
        """Test analysis when parsing fails."""
        test_file = temp_dir / "test_broken.py"
        test_file.write_text("invalid python syntax")
        
        # Mock parse error
        mock_parsed_data = {'success': False, 'error': 'Syntax error: invalid syntax (<unknown>, line 1)', 'tests': []}
        
        with patch('src.asabaal_utils.agents.spec_coder.parse_tests.parse_test_file', return_value=mock_parsed_data):
            result = analyzer.analyze_single_file(test_file)
            
            assert 'error' in result
            assert 'Syntax error' in result['error']
    
    def test_analyze_directory(self, analyzer, temp_dir):
        """Test analysis of a directory of test files."""
        # Create test files
        (temp_dir / "test_sample1.py").write_text("def test_1(): pass")
        (temp_dir / "test_sample2.py").write_text("def test_2(): pass")
        (temp_dir / "not_test.py").write_text("def regular(): pass")
        
        # Mock analysis results
        mock_results = [
            {'file': 'test_sample1.py', 'summary': 'Test 1 summary'},
            {'file': 'test_sample2.py', 'summary': 'Test 2 summary'}
        ]
        
        with patch.object(analyzer, 'analyze_single_file', side_effect=mock_results):
            results = analyzer.analyze_directory(temp_dir, temp_dir / "output")
            
            assert len(results) == 2
            assert results[0]['summary'] == 'Test 1 summary'
            assert results[1]['summary'] == 'Test 2 summary'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
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
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from tester import AnalysisEngine
except ImportError:
    pytest.skip("tester module not available", allow_module_level=True)


class TestAnalysisEngine:
    """Test cases for AnalysisEngine class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_summarizer(self):
        """Create a mock TestSummarizer."""
        mock_summ = Mock()
        mock_summ.summarize_test_file.return_value = {
            "summary": "Mock test summary",
            "behaviors": ["Mock behavior"],
            "confidence": 0.8
        }
        return mock_summ
    
    def test_init_default(self, mock_summarizer):
        """Test analyzer initialization with defaults."""
        with patch('tester.TestSummarizer', return_value=mock_summarizer):
            analyzer = AnalysisEngine()
            assert hasattr(analyzer, 'summarizer')
            assert analyzer.summarizer == mock_summarizer
    
    def test_init_custom_model(self, mock_summarizer):
        """Test analyzer initialization with custom model."""
        with patch('tester.TestSummarizer', return_value=mock_summarizer) as mock_summ_class:
            analyzer = AnalysisEngine(model_name="custom-model")
            assert hasattr(analyzer, 'summarizer')
            mock_summ_class.assert_called_once_with("custom-model", None, None)
    
    def test_init_with_files(self, mock_summarizer):
        """Test analyzer initialization with spec and source files."""
        with patch('tester.TestSummarizer', return_value=mock_summarizer) as mock_summ_class:
            spec_file = Path("test_spec.yaml")
            source_file = Path("test_source.py")
            
            analyzer = AnalysisEngine(
                model_name="custom-model",
                spec_file=spec_file,
                source_file=source_file
            )
            assert hasattr(analyzer, 'summarizer')
            mock_summ_class.assert_called_once_with("custom-model", spec_file, source_file)
    
    def test_analyze_single_file_success(self, mock_summarizer, temp_dir):
        """Test successful analysis of a single test file."""
        with patch('tester.TestSummarizer', return_value=mock_summarizer):
            # Create a test file
            test_file = temp_dir / "test_sample.py"
            test_file.write_text("def test_addition(): assert 1 + 1 == 2")
            
            # Mock the parse_test_file function
            mock_parsed_data = {
                "functions": [
                    {
                        "name": "test_addition",
                        "line": 1,
                        "args": [],
                        "docstring": None,
                        "imports": [],
                        "assertions": ["assert 1 + 1 == 2"]
                    }
                ]
            }
            
            # Mock the summarizer to return proper structure
            mock_summarizer.summarize_test_file.return_value = {
                "file_path": str(test_file),
                "functions": mock_parsed_data["functions"],
                "summary": "Mock test summary",
                "behaviors": ["Mock behavior"],
                "confidence": 0.8
            }
            
            with patch('tester.parse_test_file', return_value=mock_parsed_data):
                analyzer = AnalysisEngine()
                result = analyzer.analyze_single_file(test_file)
                
                assert "file_path" in result
                assert "functions" in result
                assert "summary" in result
                assert len(result["functions"]) == 1
                assert result["functions"][0]["name"] == "test_addition"
    
    def test_analyze_single_file_parse_error(self, mock_summarizer, temp_dir):
        """Test analysis when file parsing fails."""
        with patch('tester.TestSummarizer', return_value=mock_summarizer):
            # Create an invalid test file
            test_file = temp_dir / "test_invalid.py"
            test_file.write_text("def test_addition(: assert 1 + 1 == 2")  # Syntax error
            
            # Mock parse_test_file to return error structure
            mock_parsed_data = {"error": "Parse error"}
            
            with patch('tester.parse_test_file', return_value=mock_parsed_data):
                analyzer = AnalysisEngine()
                result = analyzer.analyze_single_file(test_file)
                
                assert "error" in result
                assert "Parse error" in result["error"]
    
    def test_analyze_directory(self, mock_summarizer, temp_dir):
        """Test analysis of a directory containing test files."""
        with patch('tester.TestSummarizer', return_value=mock_summarizer):
            # Create multiple test files
            test_file1 = temp_dir / "test_file1.py"
            test_file2 = temp_dir / "test_file2.py"
            non_test_file = temp_dir / "helper.py"
            
            test_file1.write_text("def test_one(): assert True")
            test_file2.write_text("def test_two(): assert False")
            non_test_file.write_text("def helper(): pass")
            
            # Create output directory
            output_dir = temp_dir / "output"
            output_dir.mkdir()
            
            # Mock parse_test_file
            mock_parsed_data = {
                "functions": [{"name": "test_func", "line": 1, "args": [], "docstring": None, "imports": [], "assertions": []}]
            }
            
            # Mock the summarizer to return proper structure
            mock_summarizer.summarize_test_file.return_value = {
                "file_path": "mock_path",
                "functions": mock_parsed_data["functions"],
                "summary": "Mock summary",
                "behaviors": ["Mock behavior"],
                "confidence": 0.8
            }
            
            with patch('tester.parse_test_file', return_value=mock_parsed_data):
                analyzer = AnalysisEngine()
                results = analyzer.analyze_directory(temp_dir, output_dir)
                
                assert len(results) == 2  # Only test files, not helper.py
    
    def test_analyze_directory_empty(self, mock_summarizer, temp_dir):
        """Test analysis of an empty directory."""
        with patch('tester.TestSummarizer', return_value=mock_summarizer):
            # Create output directory
            output_dir = temp_dir / "output"
            output_dir.mkdir()
            
            analyzer = AnalysisEngine()
            results = analyzer.analyze_directory(temp_dir, output_dir)
            assert results == []
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        with patch('tester.TestSummarizer'):
            analyzer = AnalysisEngine()
            assert hasattr(analyzer, 'analyze_single_file')
            assert hasattr(analyzer, 'analyze_directory')
            assert callable(analyzer.analyze_single_file)
            assert callable(analyzer.analyze_directory)
"""
Test suite for the analyze_tests module.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from asabaal_utils.agents.spec_coder.analyze_tests import AnalysisEngine


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
        mock_summarizer = Mock()
        mock_summarizer.summarize_test_file.return_value = {
            "file": "test_example.py",
            "tests": [
                {
                    "name": "test_example",
                    "target_function": "example_function",
                    "inputs": {"arg1": "value1"},
                    "assertions": ["assert result == expected"],
                    "implied_behavior": "Tests the example function"
                }
            ]
        }
        return mock_summarizer
    
    @pytest.fixture
    def engine(self, mock_summarizer):
        """Create an AnalysisEngine instance with mocked summarizer."""
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.TestSummarizer', return_value=mock_summarizer):
            return AnalysisEngine()
    
    @pytest.fixture
    def sample_test_file(self, temp_dir):
        """Create a sample test file."""
        test_content = '''
def test_example():
    result = example_function("test")
    assert result == "expected"
'''
        test_file = temp_dir / "test_example.py"
        test_file.write_text(test_content)
        return test_file
    
    def test_init_default(self):
        """Test AnalysisEngine initialization with default parameters."""
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.TestSummarizer') as mock_summarizer_class:
            engine = AnalysisEngine()
            mock_summarizer_class.assert_called_once_with("qwen3-coder:latest", None, None)
    
    def test_init_custom_parameters(self):
        """Test AnalysisEngine initialization with custom parameters."""
        spec_file = Path("test_spec.yml")
        source_file = Path("test_source.py")
        
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.TestSummarizer') as mock_summarizer_class:
            engine = AnalysisEngine("custom-model", spec_file, source_file)
            mock_summarizer_class.assert_called_once_with("custom-model", spec_file, source_file)
    
    def test_analyze_single_file_success(self, engine, sample_test_file, mock_summarizer):
        """Test successful analysis of a single test file."""
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.parse_test_file') as mock_parse:
            mock_parse.return_value = {
                "file": str(sample_test_file),
                "tests": [{"name": "test_example"}]
            }
            
            result = engine.analyze_single_file(sample_test_file)
            
            mock_parse.assert_called_once_with(sample_test_file)
            mock_summarizer.summarize_test_file.assert_called_once()
            assert "tests" in result
            assert result["file"] == "test_example.py"
    
    def test_analyze_single_file_parse_error(self, engine, sample_test_file):
        """Test analysis when parsing fails."""
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.parse_test_file') as mock_parse:
            mock_parse.return_value = {
                "file": str(sample_test_file),
                "error": "Parse error"
            }
            
            result = engine.analyze_single_file(sample_test_file)
            
            assert "error" in result
            assert result["error"] == "Parse error"
    
    def test_analyze_directory_success(self, engine, temp_dir, mock_summarizer):
        """Test successful analysis of a directory with test files."""
        # Create test files
        (temp_dir / "test_file1.py").write_text("def test1(): pass")
        (temp_dir / "test_file2.py").write_text("def test2(): pass")
        (temp_dir / "not_a_test.py").write_text("def helper(): pass")
        
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.parse_test_file') as mock_parse:
            mock_parse.return_value = {
                "file": "test_file.py",
                "tests": [{"name": "test_example"}]
            }
            
            results = engine.analyze_directory(temp_dir, output_dir)
            
            assert len(results) == 2  # Only test_*.py files
            assert (output_dir / "test_summary_test_file1.py.json").exists()
            assert (output_dir / "test_summary_test_file2.py.json").exists()
            assert (output_dir / "combined_test_summary.json").exists()
    
    def test_analyze_directory_no_test_files(self, engine, temp_dir):
        """Test analysis of directory with no test files."""
        # Create non-test files
        (temp_dir / "helper.py").write_text("def helper(): pass")
        (temp_dir / "config.py").write_text("CONFIG = {}")
        
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        results = engine.analyze_directory(temp_dir, output_dir)
        
        assert len(results) == 0
    
    def test_analyze_directory_with_errors(self, engine, temp_dir, mock_summarizer):
        """Test analysis directory with some files causing errors."""
        # Create test files
        (temp_dir / "test_good.py").write_text("def test_good(): pass")
        (temp_dir / "test_bad.py").write_text("def test_bad(): pass")
        
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.parse_test_file') as mock_parse:
            # First call succeeds, second fails
            mock_parse.side_effect = [
                {"file": "test_good.py", "tests": [{"name": "test_good"}]},
                {"file": "test_bad.py", "error": "Parse error"}
            ]
            
            results = engine.analyze_directory(temp_dir, output_dir)
            
            assert len(results) == 2
            assert "tests" in results[0]  # Success case
            assert "error" in results[1]   # Error case
    
    def test_generate_report_success(self, engine, temp_dir):
        """Test successful generation of analysis report."""
        analyzed_data = [
            {
                "file": "test_file1.py",
                "tests": [
                    {
                        "name": "test_example1",
                        "target_function": "function1",
                        "inputs": {"arg": "value"},
                        "assertions": ["assert result"],
                        "implied_behavior": "Tests function1"
                    }
                ]
            },
            {
                "file": "test_file2.py",
                "error": "Parse error"
            }
        ]
        
        output_path = temp_dir / "report.md"
        engine.generate_report(analyzed_data, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "# Test Analysis Report" in content
        assert "Total test files analyzed: 2" in content
        assert "Total tests found: 1" in content
        assert "test_example1" in content
        assert "Parse error" in content
    
    def test_generate_report_no_tests(self, engine, temp_dir):
        """Test report generation with no tests found."""
        analyzed_data = [
            {
                "file": "test_empty.py",
                "tests": []
            }
        ]
        
        output_path = temp_dir / "report.md"
        engine.generate_report(analyzed_data, output_path)
        
        content = output_path.read_text()
        assert "No tests found" in content
    
    def test_generate_report_empty_data(self, engine, temp_dir):
        """Test report generation with empty analyzed data."""
        output_path = temp_dir / "report.md"
        engine.generate_report([], output_path)
        
        content = output_path.read_text()
        assert "# Test Analysis Report" in content
        assert "Total test files analyzed: 0" in content
        assert "Total tests found: 0" in content


class TestMainFunction:
    """Test cases for the main function."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_main_function_exists(self):
        """Test that the main function exists and is callable."""
        from asabaal_utils.agents.spec_coder.analyze_tests import main
        assert callable(main)
    
    @patch('sys.argv', ['analyze_tests.py', 'test_file.py'])
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.mkdir')
    def test_main_single_file_analysis(self, mock_mkdir, mock_is_file, mock_exists, temp_dir):
        """Test main function with single file analysis."""
        mock_is_file.return_value = True
        mock_exists.return_value = False
        
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.AnalysisEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine.analyze_single_file.return_value = {"tests": []}
            mock_engine_class.return_value = mock_engine
            
            from asabaal_utils.agents.spec_coder.analyze_tests import main
            
            # Should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected when script completes
    
    @patch('sys.argv', ['analyze_tests.py', 'test_dir'])
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.mkdir')
    def test_main_directory_analysis(self, mock_mkdir, mock_is_dir, mock_exists, temp_dir):
        """Test main function with directory analysis."""
        mock_is_dir.return_value = True
        mock_exists.return_value = False
        
        with patch('asabaal_utils.agents.spec_coder.analyze_tests.AnalysisEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine.analyze_directory.return_value = []
            mock_engine_class.return_value = mock_engine
            
            from asabaal_utils.agents.spec_coder.analyze_tests import main
            
            try:
                main()
            except SystemExit:
                pass  # Expected when script completes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
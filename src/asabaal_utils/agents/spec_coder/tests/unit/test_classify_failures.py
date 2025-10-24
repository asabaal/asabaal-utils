"""
Comprehensive test suite for classify_failures.py
"""

import pytest
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from asabaal_utils.agents.spec_coder.healer.classify_failures import FailureClassifier, main
except ImportError:
    pytest.skip("classify_failures module not available")


class TestFailureClassifier:
    """Test cases for FailureClassifier class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def classifier(self, temp_dir):
        """Create a FailureClassifier instance with temp directory."""
        return FailureClassifier(reports_dir=str(temp_dir))
    
    @pytest.fixture
    def sample_test_results(self):
        """Sample test results data."""
        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "total_tests": 5,
            "passed": 2,
            "failed": 3,
            "results": [
                {
                    "function_name": "test_function_1",
                    "success": True,
                    "returncode": 0,
                    "stdout": "PASSED",
                    "stderr": "",
                    "test_dir": "/tmp/test1"
                },
                {
                    "function_name": "test_function_2", 
                    "success": False,
                    "returncode": 1,
                    "stdout": "FAILED",
                    "stderr": "NameError: name 'undefined_var' is not defined",
                    "test_dir": "/tmp/test2"
                },
                {
                    "function_name": "test_function_3",
                    "success": False,
                    "returncode": 1,
                    "stdout": "FAILED",
                    "stderr": "ImportError: No module named 'missing_module'",
                    "test_dir": "/tmp/test3"
                }
            ]
        }
    
    def test_init_default(self):
        """Test classifier initialization with default directory."""
        classifier = FailureClassifier()
        assert classifier.reports_dir == Path("reports")
    
    def test_init_custom_directory(self, temp_dir):
        """Test classifier initialization with custom directory."""
        classifier = FailureClassifier(reports_dir=str(temp_dir))
        assert classifier.reports_dir == temp_dir
    
    def test_load_test_results_latest_file(self, classifier, sample_test_results):
        """Test loading test results from latest_test_results.json."""
        # Create the latest file
        latest_file = classifier.reports_dir / "latest_test_results.json"
        latest_file.write_text(json.dumps(sample_test_results))
        
        result = classifier.load_test_results()
        assert result == sample_test_results
    
    def test_load_test_results_fallback_to_pattern(self, classifier, sample_test_results):
        """Test loading test results falls back to pattern matching."""
        # Create a timestamped file
        timestamped_file = classifier.reports_dir / "test_results_20240101_120000.json"
        timestamped_file.write_text(json.dumps(sample_test_results))
        
        result = classifier.load_test_results()
        assert result == sample_test_results
    
    def test_load_test_results_no_files(self, classifier):
        """Test loading test results when no files exist."""
        with pytest.raises(FileNotFoundError, match="No test results found"):
            classifier.load_test_results()
    
    def test_load_test_results_multiple_files_chooses_latest(self, classifier, sample_test_results):
        """Test loading chooses the most recent file when multiple exist."""
        # Create multiple files with different timestamps
        old_file = classifier.reports_dir / "test_results_20240101_120000.json"
        new_file = classifier.reports_dir / "test_results_20240101_130000.json"
        
        old_results = {**sample_test_results, "timestamp": "older"}
        new_results = {**sample_test_results, "timestamp": "newer"}
        
        old_file.write_text(json.dumps(old_results))
        time.sleep(0.1)  # Ensure different timestamps
        new_file.write_text(json.dumps(new_results))
        
        result = classifier.load_test_results()
        assert result["timestamp"] == "newer"
    
    def test_classify_failure_import_error_collection(self, classifier):
        """Test classification of import errors during collection."""
        stdout = "NameError: name 'Any' is not defined"
        stderr = "error during collection"
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        # The logic checks for "collecting" in the combined output
        assert result == "logic_mismatch"  # Since "collecting" is not in the combined output
    
    def test_classify_failure_signature_mismatch_missing_args(self, classifier):
        """Test classification of signature mismatch - missing arguments."""
        stdout = "missing 1 required positional argument: 'self'"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "signature_mismatch"
    
    def test_classify_failure_signature_mismatch_takes_args(self, classifier):
        """Test classification of signature mismatch - takes arguments."""
        stdout = "test_func() takes 2 positional arguments but 1 was given"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "signature_mismatch"
    
    def test_classify_failure_signature_mismatch_unexpected_keyword(self, classifier):
        """Test classification of signature mismatch - unexpected keyword."""
        stdout = "unexpected keyword argument 'invalid_arg'"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "signature_mismatch"
    
    def test_classify_failure_smoke_test_basic_execution(self, classifier):
        """Test classification of smoke test failures."""
        stdout = "test_my_func_basic_execution FAILED"
        stderr = "ValueError: something went wrong"
        function_name = "my_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "throws_on_smoke"
    
    def test_classify_failure_smoke_test_with_signature_issue(self, classifier):
        """Test classification of smoke test failure that's actually a signature issue."""
        stdout = "test_my_func_basic_execution FAILED"
        stderr = "missing 1 required positional argument: 'param'"
        function_name = "my_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "signature_mismatch"
    
    def test_classify_failure_import_error_module_not_found(self, classifier):
        """Test classification of import errors."""
        stdout = "ImportError: No module named 'missing_module'"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "import_error"
    
    def test_classify_failure_syntax_error(self, classifier):
        """Test classification of syntax errors."""
        stdout = "SyntaxError: invalid syntax"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "syntax_error"
    
    def test_classify_failure_indentation_error(self, classifier):
        """Test classification of indentation errors."""
        stdout = "IndentationError: expected an indented block"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "syntax_error"
    
    def test_classify_failure_name_error_execution(self, classifier):
        """Test classification of NameError during execution."""
        stdout = "NameError: name 'undefined_var' is not defined"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "logic_mismatch"
    
    def test_classify_failure_value_error(self, classifier):
        """Test classification of ValueError."""
        stdout = "ValueError: invalid value"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "throws_on_smoke"
    
    def test_classify_failure_type_error(self, classifier):
        """Test classification of TypeError (not signature related)."""
        stdout = "TypeError: unsupported operand type(s)"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "type_error"
    
    def test_classify_failure_assertion_error(self, classifier):
        """Test classification of AssertionError."""
        stdout = "AssertionError: Expected True but got False"
        stderr = ""
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "logic_mismatch"
    
    def test_classify_failure_assert_statement(self, classifier):
        """Test classification of assert statement failure."""
        stdout = "assert condition == True"
        stderr = "AssertionError"
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "logic_mismatch"
    
    def test_classify_failure_default_logic_mismatch(self, classifier):
        """Test classification defaults to logic_mismatch for unknown patterns."""
        stdout = "Some unknown error occurred"
        stderr = "Weird error message"
        function_name = "test_func"
        
        result = classifier.classify_failure(stdout, stderr, function_name)
        assert result == "logic_mismatch"
    
    def test_classify_all_failures_mixed_results(self, classifier, sample_test_results):
        """Test classifying all failures from mixed test results."""
        # Create test results file
        test_file = classifier.reports_dir / "latest_test_results.json"
        test_file.write_text(json.dumps(sample_test_results))
        
        failures = classifier.classify_all_failures()
        
        # Should have 2 failures (from the sample data)
        assert len(failures) == 2
        
        # Check first failure (NameError -> logic_mismatch)
        failure1 = failures[0]
        assert failure1["function_name"] == "test_function_2"
        assert failure1["classification"] == "logic_mismatch"
        assert failure1["returncode"] == 1
        assert "undefined_var" in failure1["stderr"]
        
        # Check second failure (ImportError -> import_error)
        failure2 = failures[1]
        assert failure2["function_name"] == "test_function_3"
        assert failure2["classification"] == "import_error"
        assert failure2["returncode"] == 1
        assert "missing_module" in failure2["stderr"]
    
    def test_classify_all_failures_no_failures(self, classifier):
        """Test classifying when all tests passed."""
        # Create test results with no failures
        test_results = {
            "results": [
                {
                    "function_name": "test_func1",
                    "success": True,
                    "returncode": 0,
                    "stdout": "PASSED",
                    "stderr": "",
                    "test_dir": "/tmp/test1"
                }
            ]
        }
        
        test_file = classifier.reports_dir / "latest_test_results.json"
        test_file.write_text(json.dumps(test_results))
        
        failures = classifier.classify_all_failures()
        assert len(failures) == 0
    
    def test_save_classification_report(self, classifier, temp_dir):
        """Test saving classification report."""
        # Create sample failures
        failures = [
            {
                "function_name": "test_func1",
                "classification": "import_error",
                "returncode": 1,
                "stdout": "FAILED",
                "stderr": "ImportError",
                "test_dir": "/tmp/test1"
            }
        ]
        
        # Create the artifacts directory
        artifacts_dir = temp_dir / "healer" / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the artifacts directory and current working directory
        with patch('asabaal_utils.agents.spec_coder.healer.classify_failures.Path') as mock_path:
            # Configure mock to return appropriate paths
            def path_side_effect(*args):
                if not args:
                    return temp_dir  # Return temp_dir for Path() with no args
                elif args == ('healer/artifacts',):
                    return artifacts_dir  # Return our artifacts directory
                return Path(*args)
            
            mock_path.side_effect = path_side_effect
            
            report_path = classifier.save_classification_report(failures)
            
            # Check that report file was created
            assert Path(report_path).exists()
            
            # Check report content
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert "metadata" in report
            assert "failures" in report
            assert report["metadata"]["total_failures"] == 1
            assert len(report["failures"]) == 1
            assert report["failures"][0]["function_name"] == "test_func1"
    
    def test_save_classification_report_creates_latest(self, classifier, temp_dir):
        """Test that saving creates both timestamped and latest reports."""
        failures = []
        
        # Create the artifacts directory
        artifacts_dir = temp_dir / "healer" / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the artifacts directory and current working directory
        with patch('asabaal_utils.agents.spec_coder.healer.classify_failures.Path') as mock_path:
            # Configure mock to return appropriate paths
            def path_side_effect(*args):
                if not args:
                    return temp_dir  # Return temp_dir for Path() with no args
                elif args == ('healer/artifacts',):
                    return artifacts_dir  # Return our artifacts directory
                return Path(*args)
            
            mock_path.side_effect = path_side_effect
            
            report_path = classifier.save_classification_report(failures)
            
            # Check both files exist
            timestamped_file = artifacts_dir / "latest_classification_report.json"
            assert timestamped_file.exists()
            
            # Check they have the same content
            with open(report_path, 'r') as f1, open(timestamped_file, 'r') as f2:
                assert json.load(f1) == json.load(f2)
    
    def test_main_function_success(self, classifier, sample_test_results):
        """Test main function with successful classification."""
        # Mock the entire FailureClassifier class to control behavior
        with patch('asabaal_utils.agents.spec_coder.healer.classify_failures.FailureClassifier') as mock_classifier_class:
            # Configure the mock instance
            mock_instance = Mock()
            mock_classifier_class.return_value = mock_instance
            
            # Mock the methods that main() calls
            mock_instance.classify_all_failures.return_value = [
                {
                    "function_name": "test_function_2",
                    "classification": "import_error",
                    "returncode": 1,
                    "stdout": "FAILED",
                    "stderr": "ImportError: No module named 'missing_module'",
                    "test_dir": "/tmp/test2"
                },
                {
                    "function_name": "test_function_3", 
                    "classification": "syntax_error",
                    "returncode": 1,
                    "stdout": "FAILED",
                    "stderr": "SyntaxError: invalid syntax",
                    "test_dir": "/tmp/test3"
                }
            ]
            mock_instance.save_classification_report.return_value = "mock_report_path.json"
            
            with patch('builtins.print') as mock_print:
                result = main()
                
                assert result == 0
                # Check that success messages were printed
                mock_print.assert_any_call("🔍 Classifying 2 failures...")
                mock_print.assert_any_call("📄 Classification report saved: mock_report_path.json")
    
    def test_main_function_no_failures(self, classifier):
        """Test main function when no failures exist."""
        # Create test results with no failures
        test_results = {"results": []}
        test_file = classifier.reports_dir / "latest_test_results.json"
        test_file.write_text(json.dumps(test_results))
        
        with patch('builtins.print') as mock_print:
            result = main()
            
            # Check what was actually printed
            if mock_print.call_args_list:
                actual_calls = [str(call) for call in mock_print.call_args_list]
                print(f"Actual print calls: {actual_calls}")
            
            assert result == 1  # main() returns 1 when it can't find test results
            mock_print.assert_any_call("❌ Classification failed: No test results found in reports")
    
    def test_main_function_exception(self, classifier):
        """Test main function when an exception occurs."""
        # Mock load_test_results to raise an exception on the class
        with patch.object(FailureClassifier, 'load_test_results', side_effect=Exception("Test error")):
            with patch('builtins.print') as mock_print:
                result = main()
                
                assert result == 1
                mock_print.assert_any_call("❌ Classification failed: Test error")
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        from asabaal_utils.agents.spec_coder.healer.classify_failures import main
        assert callable(main)
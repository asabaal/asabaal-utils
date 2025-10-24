#!/usr/bin/env python3
"""
Comprehensive Production Tests for aggregate_behaviors.py

This test suite provides thorough coverage of the aggregate_behaviors module,
including edge cases, error conditions, and integration scenarios.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_module_import():
    """Test that the aggregate_behaviors module can be imported."""
    try:
        import aggregate_behaviors
        assert hasattr(aggregate_behaviors, 'load_alignment_reports')
        assert hasattr(aggregate_behaviors, 'extract_behaviors_from_report')
        assert hasattr(aggregate_behaviors, 'merge_behaviors')
        print("✅ Module import test passed")
    except ImportError as e:
        pytest.skip(f"aggregate_behaviors module not available: {e}")


class TestLoadAlignmentReports:
    """Test suite for load_alignment_reports function."""
    
    def test_load_empty_directory(self):
        """Test loading from an empty directory."""
        try:
            import aggregate_behaviors
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                reports = aggregate_behaviors.load_alignment_reports(temp_path)
                assert reports == []
                
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_load_valid_reports(self):
        """Test loading valid alignment reports."""
        try:
            import aggregate_behaviors
            
            # Create test reports
            report1 = {
                "requirement_coverage": {"req-001": {"tests": []}},
                "additional_tests": []
            }
            report2 = {
                "requirement_coverage": {"req-002": {"tests": []}},
                "additional_tests": []
            }
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create report files
                (temp_path / "report1_alignment_report.json").write_text(json.dumps(report1))
                (temp_path / "report2_alignment_report.json").write_text(json.dumps(report2))
                
                reports = aggregate_behaviors.load_alignment_reports(temp_path)
                assert len(reports) == 2
                assert reports[0]["requirement_coverage"]["req-001"] is not None
                assert reports[1]["requirement_coverage"]["req-002"] is not None
                
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_load_mixed_files(self):
        """Test loading from directory with mixed file types."""
        try:
            import aggregate_behaviors
            
            report = {
                "requirement_coverage": {"req-001": {"tests": []}},
                "additional_tests": []
            }
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create mixed files
                (temp_path / "valid_alignment_report.json").write_text(json.dumps(report))
                (temp_path / "invalid.txt").write_text("not json")
                (temp_path / "other.json").write_text('{"not": "alignment report"}')
                
                reports = aggregate_behaviors.load_alignment_reports(temp_path)
                assert len(reports) == 1
                
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_load_invalid_json(self):
        """Test handling of invalid JSON files."""
        try:
            import aggregate_behaviors
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create invalid JSON file
                (temp_path / "invalid_alignment_report.json").write_text("{ invalid json")
                
                # Should not crash, just skip invalid file
                reports = aggregate_behaviors.load_alignment_reports(temp_path)
                assert reports == []
                
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")


class TestExtractFunctionName:
    """Test suite for extract_function_name_from_test function."""
    
    def test_basic_test_names(self):
        """Test basic test name extraction."""
        try:
            import aggregate_behaviors
            
            # Standard test_ prefix
            assert aggregate_behaviors.extract_function_name_from_test("test_add_function") == "add_function"
            assert aggregate_behaviors.extract_function_name_from_test("test_multiply") == "multiply"
            assert aggregate_behaviors.extract_function_name_from_test("test_divide_by_zero") == "divide_by_zero"
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_suffix_test_names(self):
        """Test test names with _test suffix."""
        try:
            import aggregate_behaviors
            
            assert aggregate_behaviors.extract_function_name_from_test("add_function_test") == "add_function"
            assert aggregate_behaviors.extract_function_name_from_test("multiply_test") == "multiply"
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_edge_cases(self):
        """Test edge cases for function name extraction."""
        try:
            import aggregate_behaviors
            
            # Empty and single word
            assert aggregate_behaviors.extract_function_name_from_test("") == ""
            assert aggregate_behaviors.extract_function_name_from_test("test") == ""
            
            # CamelCase conversion
            assert aggregate_behaviors.extract_function_name_from_test("testAddFunction") == "test_add_function"  # test_ prefix not removed
            assert aggregate_behaviors.extract_function_name_from_test("TestFunction") == "test_function"
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_common_patterns(self):
        """Test common test naming patterns."""
        try:
            import aggregate_behaviors
            
            # Happy path patterns
            assert aggregate_behaviors.extract_function_name_from_test("test_function_happy_path") == "function"
            assert aggregate_behaviors.extract_function_name_from_test("test_function_edge_cases") == "function"
            assert aggregate_behaviors.extract_function_name_from_test("test_function_invalid_inputs") == "function"
            
            # With prefixes
            assert aggregate_behaviors.extract_function_name_from_test("test_generate_rhythm") == "generate_rhythm"
            assert aggregate_behaviors.extract_function_name_from_test("test_apply_accent_pattern") == "apply_accent_pattern"
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")


class TestExtractBehaviorsFromReport:
    """Test suite for extract_behaviors_from_report function."""
    
    def test_extract_requirement_coverage(self):
        """Test extracting behaviors from requirement coverage."""
        try:
            import aggregate_behaviors
            
            report = {
                "requirement_coverage": {
                    "req-001": {
                        "tests": [
                            {
                                "test_name": "test_add_function",
                                "test_file": "test_math.py",
                                "implied_behavior": "Tests addition functionality",
                                "confidence": 0.9,
                                "alignment_type": "direct"
                            }
                        ]
                    }
                },
                "additional_tests": []
            }
            
            behaviors = aggregate_behaviors.extract_behaviors_from_report(report)
            
            assert len(behaviors) == 1
            assert behaviors[0]["test_name"] == "test_add_function"
            assert behaviors[0]["source"] == "specified"
            assert behaviors[0]["function_name"] == "add_function"
            assert behaviors[0]["alignment_score"] == 0.9
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_extract_additional_tests(self):
        """Test extracting behaviors from additional tests."""
        try:
            import aggregate_behaviors
            
            report = {
                "requirement_coverage": {},
                "additional_tests": [
                    {
                        "test_name": "test_helper_function",
                        "test_file": "test_utils.py",
                        "implied_behavior": "Tests helper functionality",
                        "match_reason": "Additional test not in spec"
                    }
                ]
            }
            
            behaviors = aggregate_behaviors.extract_behaviors_from_report(report)
            
            assert len(behaviors) == 1
            assert behaviors[0]["test_name"] == "test_helper_function"
            assert behaviors[0]["source"] == "additional"
            assert behaviors[0]["function_name"] == "helper_function"
            assert behaviors[0]["alignment_score"] == 0
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_extract_mixed_report(self):
        """Test extracting from mixed report with both types."""
        try:
            import aggregate_behaviors
            
            report = {
                "requirement_coverage": {
                    "req-001": {
                        "tests": [
                            {
                                "test_name": "test_main_function",
                                "test_file": "test_main.py",
                                "implied_behavior": "Tests main functionality",
                                "confidence": 0.85
                            }
                        ]
                    }
                },
                "additional_tests": [
                    {
                        "test_name": "test_utility_function",
                        "test_file": "test_utils.py",
                        "implied_behavior": "Tests utility functionality"
                    }
                ]
            }
            
            behaviors = aggregate_behaviors.extract_behaviors_from_report(report)
            
            assert len(behaviors) == 2
            specified = [b for b in behaviors if b["source"] == "specified"]
            additional = [b for b in behaviors if b["source"] == "additional"]
            
            assert len(specified) == 1
            assert len(additional) == 1
            assert specified[0]["test_name"] == "test_main_function"
            assert additional[0]["test_name"] == "test_utility_function"
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")


class TestMergeBehaviors:
    """Test suite for merge_behaviors function."""
    
    def test_merge_single_list(self):
        """Test merging a single behavior list."""
        try:
            import aggregate_behaviors
            
            behaviors_list = [[
                {
                    "test_name": "test_function",
                    "source": "specified",
                    "function_name": "function",
                    "alignment_score": 0.9
                }
            ]]
            
            merged = aggregate_behaviors.merge_behaviors(behaviors_list)
            
            assert len(merged) == 1
            assert merged[0]["function_name"] == "function"
            assert merged[0]["test_names"] == ["test_function"]
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_merge_multiple_lists(self):
        """Test merging multiple behavior lists."""
        try:
            import aggregate_behaviors
            
            behaviors_list = [
                [
                    {
                        "test_name": "test_function",
                        "source": "specified",
                        "function_name": "function",
                        "alignment_score": 0.9
                    }
                ],
                [
                    {
                        "test_name": "test_function_additional",
                        "source": "additional", 
                        "function_name": "function",
                        "alignment_score": None
                    }
                ]
            ]
            
            merged = aggregate_behaviors.merge_behaviors(behaviors_list)
            
            assert len(merged) == 1
            assert merged[0]["function_name"] == "function"
            assert len(merged[0]["test_names"]) == 2
            assert "test_function" in merged[0]["test_names"]
            assert "test_function_additional" in merged[0]["test_names"]
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_merge_different_functions(self):
        """Test merging behaviors for different functions."""
        try:
            import aggregate_behaviors
            
            behaviors_list = [
                [
                    {
                        "test_name": "test_add",
                        "source": "specified",
                        "function_name": "add",
                        "alignment_score": 0.9
                    }
                ],
                [
                    {
                        "test_name": "test_multiply",
                        "source": "specified",
                        "function_name": "multiply", 
                        "alignment_score": 0.85
                    }
                ]
            ]
            
            merged = aggregate_behaviors.merge_behaviors(behaviors_list)
            
            assert len(merged) == 2
            function_names = [m["function_name"] for m in merged]
            assert "add" in function_names
            assert "multiply" in function_names
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_merge_with_validation_rules(self):
        """Test merging behaviors with validation rules."""
        try:
            import aggregate_behaviors
            
            behaviors_list = [[
                {
                    "test_name": "test_function",
                    "source": "specified",
                    "function_name": "function",
                    "validation_rules": ["should return correct value", "should handle errors"],
                    "parameters": ["param1", "param2"]
                }
            ]]
            
            merged = aggregate_behaviors.merge_behaviors(behaviors_list)
            
            assert len(merged) == 1
            assert len(merged[0]["validation_rules"]) == 2
            assert "should return correct value" in merged[0]["validation_rules"]
            assert len(merged[0]["parameters"]) == 2
            assert "param1" in merged[0]["parameters"]
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")
    
    def test_merge_average_alignment_score(self):
        """Test calculation of average alignment scores."""
        try:
            import aggregate_behaviors
            
            behaviors_list = [
                [
                    {
                        "test_name": "test_function1",
                        "source": "specified",
                        "function_name": "function",
                        "alignment_score": 0.8
                    }
                ],
                [
                    {
                        "test_name": "test_function2",
                        "source": "specified",
                        "function_name": "function",
                        "alignment_score": 0.9
                    }
                ]
            ]
            
            merged = aggregate_behaviors.merge_behaviors(behaviors_list)
            
            assert len(merged) == 1
            assert abs(merged[0]["average_alignment_score"] - 0.85) < 0.0001
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")


class TestSaveAggregatedBehaviors:
    """Test suite for save_aggregated_behaviors function."""
    
    def test_save_behaviors(self):
        """Test saving aggregated behaviors to file."""
        try:
            import aggregate_behaviors
            
            behaviors = [
                {
                    "function_name": "test_function",
                    "test_names": ["test_test_function"],
                    "sources": ["specified"],
                    "behaviors": ["Tests functionality"],
                    "validation_rules": ["should return correct value"],
                    "parameters": ["param1"]
                }
            ]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_file = Path(f.name)
            
            try:
                aggregate_behaviors.save_aggregated_behaviors(behaviors, output_file)
                
                # Verify file was created and contains correct data
                with open(output_file, 'r') as f:
                    saved_data = json.load(f)
                
                assert 'metadata' in saved_data
                assert 'functions' in saved_data
                assert saved_data['metadata']['total_functions'] == 1
                assert len(saved_data['functions']) == 1
                assert saved_data['functions'][0]['function_name'] == 'test_function'
                
            finally:
                output_file.unlink()
                
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")


class TestMainFunction:
    """Test suite for main function."""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        try:
            import aggregate_behaviors
            
            assert hasattr(aggregate_behaviors, 'main')
            assert callable(aggregate_behaviors.main)
            
        except ImportError:
            pytest.skip("aggregate_behaviors module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
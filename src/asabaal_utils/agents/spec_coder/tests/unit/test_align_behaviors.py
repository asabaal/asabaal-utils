#!/usr/bin/env python3
"""
Comprehensive Production Tests for align_behaviors.py

This test suite provides thorough coverage of the align_behaviors module,
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
    """Test that the align_behaviors module can be imported."""
    try:
        import align_behaviors
        assert hasattr(align_behaviors, 'BehaviorInfo')
        assert hasattr(align_behaviors, 'AlignmentMatch')
        assert hasattr(align_behaviors, 'BehavioralAligner')
        assert hasattr(align_behaviors, 'main')
        print("✅ Module import test passed")
    except ImportError as e:
        pytest.skip(f"align_behaviors module not available: {e}")


class TestTestBehavior:
    """Test suite for TestBehavior dataclass."""
    
    def test_test_behavior_creation(self):
        """Test TestBehavior dataclass creation."""
        try:
            from align_behaviors import TestBehavior
            
            behavior = TestBehavior(
                test_name="test_function",
                test_file="test_file.py",
                implied_behavior="Tests function functionality",
                test_type="unit",
                confidence=0.9
            )
            
            assert behavior.test_name == "test_function"
            assert behavior.test_file == "test_file.py"
            assert behavior.implied_behavior == "Tests function functionality"
            assert behavior.test_type == "unit"
            assert behavior.confidence == 0.9
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_test_behavior_defaults(self):
        """Test TestBehavior with default values."""
        try:
            from align_behaviors import TestBehavior
            
            # Test with minimal required fields
            behavior = TestBehavior(
                test_name="test_minimal",
                test_file="test.py",
                implied_behavior="Minimal test",
                test_type="unit",
                confidence=0.5
            )
            
            assert behavior.test_name == "test_minimal"
            assert behavior.confidence == 0.5
            
        except ImportError:
            pytest.skip("align_behaviors module not available")


class TestAlignmentMatch:
    """Test suite for AlignmentMatch dataclass."""
    
    def test_alignment_match_creation(self):
        """Test AlignmentMatch dataclass creation."""
        try:
            from align_behaviors import AlignmentMatch, TestBehavior
            
            test_behavior = TestBehavior(
                test_name="test_function",
                test_file="test_file.py",
                implied_behavior="Tests function",
                test_type="unit",
                confidence=0.9
            )
            
            match = AlignmentMatch(
                test=test_behavior,
                requirement=None,  # For additional test
                confidence=0.8,
                match_reason="Good match",
                alignment_type="direct",
                is_specified=False
            )
            
            assert match.test == test_behavior
            assert match.requirement is None
            assert match.confidence == 0.8
            assert match.match_reason == "Good match"
            assert match.alignment_type == "direct"
            assert match.is_specified is False
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_alignment_match_types(self):
        """Test AlignmentMatch with different alignment types."""
        try:
            from align_behaviors import AlignmentMatch, TestBehavior
            
            test_behavior = TestBehavior(
                test_name="test_function",
                test_file="test_file.py",
                implied_behavior="Tests function",
                test_type="unit",
                confidence=0.9
            )
            
            # Test all alignment types
            alignment_types = ['direct', 'partial', 'indirect', 'none', 'additional']
            
            for alignment_type in alignment_types:
                match = AlignmentMatch(
                    test=test_behavior,
                    requirement=None,
                    confidence=0.7,
                    match_reason=f"Test {alignment_type}",
                    alignment_type=alignment_type,
                    is_specified=(alignment_type != 'additional')
                )
                
                assert match.alignment_type == alignment_type
                assert match.is_specified == (alignment_type != 'additional')
                
        except ImportError:
            pytest.skip("align_behaviors module not available")


class TestBehavioralAligner:
    """Test suite for BehavioralAligner class."""
    
    def test_aligner_initialization(self):
        """Test BehavioralAligner initialization."""
        try:
            from align_behaviors import BehavioralAligner
            
            aligner = BehavioralAligner()
            assert hasattr(aligner, 'spec_parser')
            assert aligner.spec_parser is not None
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_load_test_behaviors_single_file(self):
        """Test loading test behaviors from single file format."""
        try:
            from align_behaviors import BehavioralAligner
            
            test_data = {
                "file": "test_math.py",
                "tests": [
                    {
                        "name": "test_add_function",
                        "implied_behavior": "Tests addition functionality"
                    },
                    {
                        "name": "test_multiply_function",
                        "implied_behavior": "Tests multiplication functionality"
                    }
                ]
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                temp_file = Path(f.name)
            
            try:
                aligner = BehavioralAligner()
                behaviors = aligner.load_test_behaviors(temp_file)
                
                assert len(behaviors) == 2
                assert behaviors[0].test_name == "test_add_function"
                assert behaviors[0].implied_behavior == "Tests addition functionality"
                assert behaviors[1].test_name == "test_multiply_function"
                assert behaviors[1].confidence == 0.8  # Default confidence
                
            finally:
                temp_file.unlink()
                
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_load_test_behaviors_combined_format(self):
        """Test loading test behaviors from combined format."""
        try:
            from align_behaviors import BehavioralAligner
            
            test_data = {
                "files": [
                    {
                        "file": "test_math.py",
                        "tests": [
                            {
                                "name": "test_add_function",
                                "implied_behavior": "Tests addition functionality"
                            }
                        ]
                    },
                    {
                        "file": "test_utils.py",
                        "tests": [
                            {
                                "name": "test_helper_function",
                                "implied_behavior": "Tests helper functionality"
                            }
                        ]
                    }
                ]
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                temp_file = Path(f.name)
            
            try:
                aligner = BehavioralAligner()
                behaviors = aligner.load_test_behaviors(temp_file)
                
                assert len(behaviors) == 2
                assert behaviors[0].test_file == "test_math.py"
                assert behaviors[1].test_file == "test_utils.py"
                
            finally:
                temp_file.unlink()
                
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_load_test_behaviors_invalid_json(self):
        """Test handling of invalid JSON file."""
        try:
            from align_behaviors import BehavioralAligner
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write("{ invalid json")
                temp_file = Path(f.name)
            
            try:
                aligner = BehavioralAligner()
                with pytest.raises(json.JSONDecodeError):
                    aligner.load_test_behaviors(temp_file)
            finally:
                temp_file.unlink()
                
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_infer_test_type_comprehensive(self):
        """Test test type inference with comprehensive patterns."""
        try:
            from align_behaviors import BehavioralAligner
            
            aligner = BehavioralAligner()
            
            # Integration tests
            assert aligner._infer_test_type("test_integration_flow") == "integration"
            assert aligner._infer_test_type("test_end_to_end_process") == "integration"
            assert aligner._infer_test_type("test_e2e_user_journey") == "integration"
            
            # Performance tests
            assert aligner._infer_test_type("performance_load_test") == "performance"
            assert aligner._infer_test_type("stress_testing") == "performance"
            assert aligner._infer_test_type("benchmark_test") == "unit"  # 'benchmark' not in performance keywords
            
            # Unit tests (default)
            assert aligner._infer_test_type("test_function") == "unit"
            assert aligner._infer_test_type("test_helper_method") == "unit"
            assert aligner._infer_test_type("unknown_test_pattern") == "unit"
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_calculate_keyword_match(self):
        """Test keyword matching calculation."""
        try:
            from align_behaviors import BehavioralAligner, TestBehavior, Requirement
            
            aligner = BehavioralAligner()
            
            test_behavior = TestBehavior(
                test_name="test_add_function",
                test_file="test_math.py",
                implied_behavior="Tests addition of two numbers and returns sum",
                test_type="unit",
                confidence=0.9
            )
            
            requirement = Requirement(
                id="req-001",
                title="Add Function",
                description="Function should add two numbers together and return the sum"
            )
            
            # Test keyword matching
            match_score = aligner._calculate_keyword_match(test_behavior, requirement)
            assert isinstance(match_score, float)
            assert 0.0 <= match_score <= 1.0
            
            # Test with no matching keywords
            test_behavior_no_match = TestBehavior(
                test_name="test_subtract_function",
                test_file="test_math.py",
                implied_behavior="Tests subtraction operation",
                test_type="unit",
                confidence=0.9
            )
            
            match_score_no_match = aligner._calculate_keyword_match(test_behavior_no_match, requirement)
            assert isinstance(match_score_no_match, float)
            assert 0.0 <= match_score_no_match <= 1.0
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_calculate_function_match(self):
        """Test function name matching calculation."""
        try:
            from align_behaviors import BehavioralAligner, TestBehavior, Requirement
            
            aligner = BehavioralAligner()
            
            # Direct function name match
            test_behavior = TestBehavior(
                test_name="test_add_numbers",
                test_file="test_math.py",
                implied_behavior="Tests addition functionality",
                test_type="unit",
                confidence=0.9
            )
            
            requirement = Requirement(
                id="req-001",
                title="Add Function",
                description="Function add_numbers should add two numbers"
            )
            
            match_score = aligner._calculate_function_match(test_behavior, requirement)
            assert isinstance(match_score, float)
            assert 0.0 <= match_score <= 1.0
            
            # Partial function name match
            test_behavior_partial = TestBehavior(
                test_name="test_add",
                test_file="test_math.py",
                implied_behavior="Tests add functionality",
                test_type="unit",
                confidence=0.9
            )
            
            match_score_partial = aligner._calculate_function_match(test_behavior_partial, requirement)
            assert isinstance(match_score_partial, float)
            assert 0.0 <= match_score_partial <= 1.0
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_calculate_validation_match(self):
        """Test validation criteria matching calculation."""
        try:
            from align_behaviors import BehavioralAligner, TestBehavior, Requirement
            
            aligner = BehavioralAligner()
            
            test_behavior = TestBehavior(
                test_name="test_add_function",
                test_file="test_math.py",
                implied_behavior="Tests that add function returns correct sum and validates inputs",
                test_type="unit",
                confidence=0.9
            )
            
            requirement = Requirement(
                id="req-001",
                title="Add Function",
                description="Function should add two numbers"
            )
            
            # Test validation matching
            match_score = aligner._calculate_validation_match(test_behavior, requirement)
            assert isinstance(match_score, float)
            assert 0.0 <= match_score <= 1.0
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_align_test_to_requirement_comprehensive(self):
        """Test aligning a test to a requirement with comprehensive scenarios."""
        try:
            from align_behaviors import BehavioralAligner, TestBehavior, Requirement
            
            aligner = BehavioralAligner()
            
            test_behavior = TestBehavior(
                test_name="test_add_function",
                test_file="test_math.py",
                implied_behavior="Tests addition of two numbers",
                test_type="unit",
                confidence=0.9
            )
            
            requirement = Requirement(
                id="req-001",
                title="Add Function",
                description="Function should add two numbers together"
            )
            
            # Test alignment
            match = aligner.align_test_to_requirement(test_behavior, requirement)
            
            assert match.test == test_behavior
            assert match.requirement == requirement
            assert isinstance(match.confidence, float)
            assert 0.0 <= match.confidence <= 1.0
            assert match.alignment_type in ['direct', 'partial', 'indirect', 'none']
            assert match.is_specified is True
            assert len(match.match_reason) > 0
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_align_all_tests(self):
        """Test aligning multiple tests to multiple requirements."""
        try:
            from align_behaviors import BehavioralAligner, TestBehavior, Requirement, OpenSpec
            
            aligner = BehavioralAligner()
            
            # Create test behaviors
            test_behaviors = [
                TestBehavior(
                    test_name="test_add_function",
                    test_file="test_math.py",
                    implied_behavior="Tests addition functionality",
                    test_type="unit",
                    confidence=0.9
                ),
                TestBehavior(
                    test_name="test_helper_function",
                    test_file="test_utils.py",
                    implied_behavior="Tests helper functionality",
                    test_type="unit",
                    confidence=0.8
                )
            ]
            
            # Create requirements
            requirements = [
                Requirement(
                    id="req-001",
                    title="Add Function",
                    description="Function should add two numbers"
                )
            ]
            
            # Create OpenSpec
            spec = OpenSpec(
                spec_id="test-spec",
                title="Test Specification",
                version="1.0",
                requirements=requirements,
                raw_data={}
            )
            
            # Align all tests
            matches = aligner.align_all_tests(test_behaviors, spec)
            
            assert len(matches) == 2
            assert all(isinstance(match.confidence, float) for match in matches)
            assert all(0.0 <= match.confidence <= 1.0 for match in matches)
            
        except ImportError:
            pytest.skip("align_behaviors module not available")
    
    def test_generate_alignment_report(self):
        """Test generating comprehensive alignment report."""
        try:
            from align_behaviors import BehavioralAligner, TestBehavior, AlignmentMatch
            
            aligner = BehavioralAligner()
            
            # Create test matches
            test_behavior1 = TestBehavior(
                test_name="test_specified_function",
                test_file="test_specified.py",
                implied_behavior="Tests specified functionality",
                test_type="unit",
                confidence=0.9
            )
            
            test_behavior2 = TestBehavior(
                test_name="test_additional_function",
                test_file="test_additional.py",
                implied_behavior="Tests additional functionality",
                test_type="unit",
                confidence=0.8
            )
            
            matches = [
                AlignmentMatch(
                    test=test_behavior1,
                    requirement=None,  # Mock requirement
                    confidence=0.85,
                    match_reason="Direct match to requirement",
                    alignment_type="direct",
                    is_specified=True
                ),
                AlignmentMatch(
                    test=test_behavior2,
                    requirement=None,
                    confidence=0.7,
                    match_reason="Additional test not in spec",
                    alignment_type="additional",
                    is_specified=False
                )
            ]
            
            # Generate report
            report = aligner.generate_alignment_report(matches)
            
            # Check report structure
            assert 'summary' in report
            assert 'requirement_coverage' in report
            assert 'additional_tests' in report
            assert 'detailed_matches' in report
            
            # Check summary
            summary = report['summary']
            assert summary['total_tests'] == 2
            assert summary['specified_tests'] == 1
            assert summary['additional_tests'] == 1
            assert 'alignment_rate' in summary
            
            # Check additional tests section
            additional_tests = report['additional_tests']
            assert len(additional_tests) == 1
            assert additional_tests[0]['test_name'] == "test_additional_function"
            
        except ImportError:
            pytest.skip("align_behaviors module not available")


class TestMainFunction:
    """Test suite for main function."""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        try:
            import align_behaviors
            
            assert hasattr(align_behaviors, 'main')
            assert callable(align_behaviors.main)
            
        except ImportError:
            pytest.skip("align_behaviors module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
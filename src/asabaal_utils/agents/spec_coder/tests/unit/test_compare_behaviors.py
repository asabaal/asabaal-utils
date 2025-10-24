"""
Tests for the compare_behaviors module.

This module tests the BehaviorComparator class which is critical for
the alignment stage of the spec-coder pipeline.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from asabaal_utils.agents.spec_coder.compare_behaviors import (
    BehaviorComparator, 
    BehaviorGap, 
    ComparisonResult
)
from asabaal_utils.agents.spec_coder.align_behaviors import BehaviorInfo
from asabaal_utils.agents.spec_coder.spec_parser import OpenSpec, Requirement


class TestBehaviorComparator:
    """Test cases for BehaviorComparator class."""
    
    @pytest.fixture
    def comparator(self):
        """Create a BehaviorComparator instance for testing."""
        with patch('asabaal_utils.agents.spec_coder.compare_behaviors.OllamaClient') as mock_ollama, \
             patch('asabaal_utils.agents.spec_coder.compare_behaviors.BehavioralAligner') as mock_aligner, \
             patch('asabaal_utils.agents.spec_coder.compare_behaviors.SpecParser') as mock_parser:
            comparator = BehaviorComparator()
            comparator.aligner = mock_aligner.return_value
            comparator.ollama = mock_ollama.return_value
            comparator.spec_parser = mock_parser.return_value
            return comparator
    
    @pytest.fixture
    def sample_test_behaviors(self):
        """Create sample test behaviors for testing."""
        return [
            BehaviorInfo(
                test_name="test_add_positive_numbers",
                test_file="test_calculator.py",
                implied_behavior="Tests addition of positive numbers",
                test_type="unit",
                confidence=0.9
            ),
            BehaviorInfo(
                test_name="test_add_negative_numbers", 
                test_file="test_calculator.py",
                implied_behavior="Tests addition with negative numbers",
                test_type="unit",
                confidence=0.85
            ),
            BehaviorInfo(
                test_name="test_multiply_numbers",
                test_file="test_calculator.py", 
                implied_behavior="Tests multiplication functionality",
                test_type="unit",
                confidence=0.95
            )
        ]
    
    @pytest.fixture
    def sample_spec_behaviors(self):
        """Create sample specification behaviors for testing."""
        return [
            {
                "id": "REQ-001",
                "description": "Add two positive numbers and return the result",
                "type": "functional",
                "priority": "high"
            },
            {
                "id": "REQ-002", 
                "description": "Handle negative number inputs for addition",
                "type": "functional",
                "priority": "medium"
            },
            {
                "id": "REQ-003",
                "description": "Multiply two numbers together", 
                "type": "functional",
                "priority": "high"
            },
            {
                "id": "REQ-004",
                "description": "Divide numbers and handle division by zero",
                "type": "functional", 
                "priority": "critical"
            }
        ]
    
    def test_init(self, comparator):
        """Test BehaviorComparator initialization."""
        assert comparator.ollama is not None
        assert comparator.aligner is not None
        assert comparator.spec_parser is not None
    
    def test_load_test_behaviors(self, comparator):
        """Test loading test behaviors from file."""
        # Mock the aligner's load_test_behaviors method
        expected_behaviors = [
            BehaviorInfo("test1", "file1.py", "behavior1", "unit", 0.8)
        ]
        comparator.aligner.load_test_behaviors = Mock(return_value=expected_behaviors)
        
        # Test the method
        result = comparator.load_test_behaviors(Path("test_file.json"))
        
        # Verify
        comparator.aligner.load_test_behaviors.assert_called_once_with(Path("test_file.json"))
        assert result == expected_behaviors
    
    def test_compare_behaviors_basic(self, comparator, sample_spec_behaviors, sample_test_behaviors):
        """Test basic compare_behaviors functionality."""
        # Test the comparison
        result = comparator.compare_spec_and_test_behaviors(sample_spec_behaviors, sample_test_behaviors)
        
        # Verify structure
        assert 'spec_behaviors' in result
        assert 'test_behaviors' in result
        assert 'alignment_analysis' in result
        assert 'gaps' in result
        assert 'strengths' in result
        assert 'recommendations' in result
        
        # Verify data
        assert len(result['spec_behaviors']) == 4
        assert len(result['test_behaviors']) == 3
        assert result['alignment_analysis']['total_spec_behaviors'] == 4
    
    def test_compare_behaviors_coverage_analysis(self, comparator, sample_spec_behaviors, sample_test_behaviors):
        """Test that compare_behaviors correctly analyzes coverage."""
        result = comparator.compare_spec_and_test_behaviors(sample_spec_behaviors, sample_test_behaviors)
        
        # Should find coverage for addition and multiplication behaviors
        # Should identify gap for division behavior
        analysis = result['alignment_analysis']
        
        assert analysis['total_spec_behaviors'] == 4
        assert analysis['covered_behaviors'] >= 2  # At least addition and multiplication
        assert analysis['total_gaps'] >= 1  # At least division
        assert 0 <= analysis['overall_score'] <= 1
    
    def test_compare_behaviors_identifies_gaps(self, comparator, sample_spec_behaviors, sample_test_behaviors):
        """Test that compare_behaviors correctly identifies missing test coverage."""
        result = comparator.compare_spec_and_test_behaviors(sample_spec_behaviors, sample_test_behaviors)
        
        # Should identify gap for division functionality
        gaps = result['gaps']
        division_gaps = [gap for gap in gaps if 'division' in gap['description'].lower()]
        
        assert len(division_gaps) >= 1
        assert division_gaps[0]['type'] == 'missing_test'
        assert division_gaps[0]['severity'] == 'high'
    
    def test_compare_behaviors_identifies_strengths(self, comparator, sample_spec_behaviors, sample_test_behaviors):
        """Test that compare_behaviors correctly identifies well-covered behaviors."""
        result = comparator.compare_spec_and_test_behaviors(sample_spec_behaviors, sample_test_behaviors)
        
        # Should identify strengths for covered behaviors
        strengths = result['strengths']
        assert len(strengths) >= 2  # At least addition and multiplication
        
        for strength in strengths:
            assert 'behavior_id' in strength
            assert 'description' in strength
            assert 'tests' in strength
            assert len(strength['tests']) >= 1
    
    def test_compare_behaviors_empty_inputs(self, comparator):
        """Test compare_behaviors with empty inputs."""
        result = comparator.compare_spec_and_test_behaviors([], [])
        
        assert result['alignment_analysis']['total_spec_behaviors'] == 0
        assert result['alignment_analysis']['covered_behaviors'] == 0
        assert result['alignment_analysis']['overall_score'] == 0
        assert len(result['gaps']) == 0
        assert len(result['strengths']) == 0
    
    def test_compare_behaviors_no_test_coverage(self, comparator, sample_spec_behaviors):
        """Test compare_behaviors when no tests cover the behaviors."""
        result = comparator.compare_spec_and_test_behaviors(sample_spec_behaviors, [])
        
        # Should identify gaps for all spec behaviors
        assert len(result['gaps']) == len(sample_spec_behaviors)
        assert len(result['strengths']) == 0
        assert result['alignment_analysis']['overall_score'] == 0
    
    def test_compare_behaviors_perfect_coverage(self, comparator, sample_spec_behaviors):
        """Test compare_behaviors with perfect test coverage."""
        # Create test behaviors that perfectly match spec behaviors
        perfect_test_behaviors = []
        for spec in sample_spec_behaviors:
            test_behavior = BehaviorInfo(
                test_name=f"test_{spec['id'].lower()}",
                test_file="test_file.py",
                implied_behavior=spec['description'],
                test_type="unit",
                confidence=0.9
            )
            perfect_test_behaviors.append(test_behavior)
        
        result = comparator.compare_spec_and_test_behaviors(sample_spec_behaviors, perfect_test_behaviors)
        
        # Should have high coverage and no gaps
        assert result['alignment_analysis']['overall_score'] > 0.8
        assert len(result['gaps']) == 0
        assert len(result['strengths']) == len(sample_spec_behaviors)
    
    @patch('asabaal_utils.agents.spec_coder.compare_behaviors.OllamaClient')
    @patch('asabaal_utils.agents.spec_coder.compare_behaviors.BehavioralAligner')
    @patch('asabaal_utils.agents.spec_coder.compare_behaviors.SpecParser')
    def test_analyze_requirement_coverage(self, mock_spec_parser, mock_aligner, mock_ollama):
        """Test the analyze_requirement_coverage method."""
        # Setup mocks
        mock_ollama_instance = Mock()
        mock_ollama_instance.generate.return_value = '{"alignment_score": 85, "gaps": [], "strengths": ["Good coverage"], "overall_assessment": "Well covered"}'
        mock_ollama.return_value = mock_ollama_instance
        
        mock_aligner_instance = Mock()
        mock_aligner.return_value = mock_aligner_instance
        
        comparator = BehaviorComparator()
        
        # Create test requirement
        requirement = Requirement(
            id="REQ-001",
            title="Add Numbers",
            description="Add two numbers together",
            interface=None,
            validation=[]
        )
        
        # Create test behaviors
        test_behaviors = [
            BehaviorInfo("test_add", "test.py", "Tests addition", "unit", 0.9)
        ]
        
        # Mock the aligner response
        mock_aligner_instance.align_test_to_requirement.return_value = Mock(confidence=0.8)
        
        # Test the method
        result = comparator.analyze_requirement_coverage(requirement, test_behaviors)
        
        # Verify
        assert 'requirement_id' in result
        assert 'alignment_score' in result
        assert 'gaps' in result
        assert 'strengths' in result
        assert result['requirement_id'] == "REQ-001"
    
    def test_generate_summary_report(self, comparator):
        """Test the generate_summary_report method."""
        # Create sample comparison results
        results = [
            ComparisonResult(
                requirement_id="REQ-001",
                requirement_title="Add Numbers",
                alignment_score=0.9,
                gaps=[],
                strengths=["Good coverage"],
                overall_assessment="Well covered",
                test_coverage={}
            ),
            ComparisonResult(
                requirement_id="REQ-002",
                requirement_title="Subtract Numbers", 
                alignment_score=0.5,
                gaps=[
                    BehaviorGap(
                        gap_type="missing_test",
                        severity="high",
                        description="Missing edge case tests",
                        recommendation="Add edge case tests"
                    )
                ],
                strengths=[],
                overall_assessment="Needs improvement",
                test_coverage={}
            )
        ]
        
        # Generate summary
        summary = comparator.generate_summary_report(results)
        
        # Verify structure
        assert 'summary' in summary
        assert 'gap_analysis' in summary
        assert 'top_issues' in summary
        assert 'well_covered' in summary
        assert 'detailed_results' in summary
        
        # Verify summary data
        assert summary['summary']['total_requirements'] == 2
        assert summary['summary']['average_alignment_score'] == 0.7
        assert summary['summary']['requirements_with_critical_issues'] == 0
        assert summary['summary']['well_covered_requirements'] == 1


class TestBehaviorGap:
    """Test cases for BehaviorGap dataclass."""
    
    def test_behavior_gap_creation(self):
        """Test creating a BehaviorGap."""
        gap = BehaviorGap(
            gap_type="missing_test",
            severity="high", 
            description="Missing test for edge case",
            recommendation="Add edge case test",
            test_name="test_function",
            requirement_id="REQ-001"
        )
        
        assert gap.gap_type == "missing_test"
        assert gap.severity == "high"
        assert gap.description == "Missing test for edge case"
        assert gap.recommendation == "Add edge case test"
        assert gap.test_name == "test_function"
        assert gap.requirement_id == "REQ-001"


class TestComparisonResult:
    """Test cases for ComparisonResult dataclass."""
    
    def test_comparison_result_creation(self):
        """Test creating a ComparisonResult."""
        result = ComparisonResult(
            requirement_id="REQ-001",
            requirement_title="Add Numbers",
            alignment_score=0.85,
            gaps=[],
            strengths=["Good coverage"],
            overall_assessment="Well covered",
            test_coverage={"test_add": {"confidence": 0.9}}
        )
        
        assert result.requirement_id == "REQ-001"
        assert result.requirement_title == "Add Numbers"
        assert result.alignment_score == 0.85
        assert len(result.gaps) == 0
        assert len(result.strengths) == 1
        assert result.overall_assessment == "Well covered"
        assert len(result.test_coverage) == 1


if __name__ == "__main__":
    pytest.main([__file__])
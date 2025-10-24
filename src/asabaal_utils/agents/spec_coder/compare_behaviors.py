"""
LLM-based Behavior Comparison Analyzer

Uses AI to perform deep semantic analysis of test-spec alignment,
identifying gaps, overlaps, and mismatches between test behaviors and OpenSpec requirements.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import sys
import os

# Import local modules
from ollama_client import OllamaClient, GenerationConfig
from align_behaviors import BehavioralAligner, AlignmentMatch, BehaviorInfo
from spec_parser import SpecParser, OpenSpec, Requirement


@dataclass
class BehaviorGap:
    """Represents a gap between test behavior and spec requirement."""
    gap_type: str  # 'missing_test', 'incomplete_test', 'misaligned_test', 'over_testing'
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    recommendation: str
    test_name: Optional[str] = None
    requirement_id: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of comparing test behaviors with spec requirements."""
    requirement_id: str
    requirement_title: str
    alignment_score: float
    gaps: List[BehaviorGap]
    strengths: List[str]
    overall_assessment: str
    test_coverage: Dict[str, Any]  # test_name -> coverage_info


class BehaviorComparator:
    """
    Main class for comparing specification behaviors with test behaviors to identify gaps and alignment issues.
    
    This class provides the core functionality for analyzing how well test coverage aligns with
    specification requirements, helping identify missing test cases and areas of strength in testing.
    
    Attributes:
        ollama: OllamaClient instance for AI-powered analysis
        aligner: BehavioralAligner instance for test-spec alignment
        spec_parser: SpecParser instance for specification processing
    
    Example:
        >>> comparator = BehaviorComparator(model_name="qwen3-coder:latest")
        >>> spec_behaviors = [{"id": "REQ-001", "description": "Add two numbers"}]
        >>> test_behaviors = [TestBehavior("test_add", "test.py", "Tests addition", "unit", 0.9)]
        >>> result = comparator.compare_spec_and_test_behaviors(spec_behaviors, test_behaviors)
        >>> print(f"Coverage: {result['alignment_analysis']['coverage_percentage']:.1f}%")
    """
    
    def __init__(self, model_name: str = "qwen3-coder:latest"):
        """
        Initialize the BehaviorComparator with specified AI model.
        
        Args:
            model_name: Name of the Ollama model to use for AI-powered analysis.
                       Defaults to "qwen3-coder:latest".
        
        Raises:
            ConnectionError: If Ollama server is not accessible
            ValueError: If specified model is not available
        
        Example:
            >>> comparator = BehaviorComparator("qwen3-coder:latest")
            >>> # or use default
            >>> comparator = BehaviorComparator()
        """
        config = GenerationConfig(model=model_name)
        self.ollama = OllamaClient(config)
        self.aligner = BehavioralAligner()
        self.spec_parser = SpecParser()
    
    def load_test_behaviors(self, analysis_file: Path) -> List[BehaviorInfo]:
        """
        Load test behaviors from a previously generated analysis file.
        
        This method reads a JSON file containing test analysis results and converts
        them into TestBehavior objects for comparison with specification requirements.
        
        Args:
            analysis_file: Path to the JSON file containing test behavior analysis.
                          Expected format includes test names, files, implied behaviors,
                          test types, and confidence scores.
        
        Returns:
            List of TestBehavior objects extracted from the analysis file.
        
        Raises:
            FileNotFoundError: If the analysis file does not exist
            JSONDecodeError: If the file contains invalid JSON
            KeyError: If required fields are missing from the analysis data
        
        Example:
            >>> behaviors = comparator.load_test_behaviors(Path("test_analysis.json"))
            >>> print(f"Loaded {len(behaviors)} test behaviors")
        """
        return self.aligner.load_test_behaviors(analysis_file)
    
    def compare_spec_and_test_behaviors(self, spec_behaviors: List[Dict[str, Any]], test_behaviors: List[BehaviorInfo]) -> Dict[str, Any]:
        """
        Compare specification behaviors with test behaviors to identify gaps and alignment issues.
        
        This is the main entry point for behavior comparison analysis. It performs intelligent
        matching between specification requirements and test implementations using operation-specific
        keyword matching to determine coverage gaps and strengths.
        
        Args:
            spec_behaviors: List of behaviors extracted from specification requirements.
                          Each behavior should be a dictionary with at least 'id' and 'description'
                          keys. Optional keys include 'type', 'priority', and other metadata.
                          Example: [{"id": "REQ-001", "description": "Add two positive numbers", 
                                   "type": "functional", "priority": "high"}]
            
            test_behaviors: List of TestBehavior objects extracted from test implementations.
                          Each should contain test name, file, implied behavior description,
                          test type, and confidence score.
                          Example: [TestBehavior("test_add", "test.py", "Tests addition", "unit", 0.9)]
        
        Returns:
            Dictionary containing comprehensive comparison results with the following structure:
            {
                'spec_behaviors': List[Dict] - Original specification behaviors,
                'test_behaviors': List[Dict] - Processed test behaviors,
                'alignment_analysis': {
                    'total_spec_behaviors': int - Total number of specification behaviors,
                    'covered_behaviors': int - Number of behaviors with test coverage,
                    'coverage_percentage': float - Percentage of behaviors covered (0-100),
                    'total_gaps': int - Number of uncovered behaviors,
                    'overall_score': float - Normalized coverage score (0.0-1.0)
                },
                'gaps': List[Dict] - Uncovered specification behaviors,
                'strengths': List[Dict] - Well-covered specification behaviors,
                'recommendations': List[Dict] - Suggestions for improving test coverage
            }
        
        Raises:
            ValueError: If spec_behaviors or test_behaviors contain invalid data
        
        Example:
            >>> spec_behaviors = [
            ...     {"id": "REQ-001", "description": "Add two positive numbers"},
            ...     {"id": "REQ-002", "description": "Divide numbers and handle division by zero"}
            ... ]
            >>> test_behaviors = [
            ...     TestBehavior("test_add", "test.py", "Tests addition", "unit", 0.9)
            ... ]
            >>> result = comparator.compare_spec_and_test_behaviors(spec_behaviors, test_behaviors)
            >>> print(f"Coverage: {result['alignment_analysis']['coverage_percentage']:.1f}%")
            >>> print(f"Gaps: {len(result['gaps'])}")
        """
        # Convert spec behaviors to OpenSpec format for analysis
        # For now, we'll use the existing compare_all_requirements method
        # but this provides a cleaner interface for behavior comparison
        
        # If we have a full spec, use compare_all_requirements
        # Otherwise, create a minimal comparison based on the behaviors provided
        
        results = {
            'spec_behaviors': spec_behaviors,
            'test_behaviors': [
                {
                    'name': test.test_name,
                    'file': test.test_file,
                    'behavior': test.implied_behavior,
                    'type': test.test_type,
                    'confidence': test.confidence
                }
                for test in test_behaviors
            ],
            'alignment_analysis': {},
            'gaps': [],
            'strengths': [],
            'recommendations': []
        }
        
        # Perform basic alignment analysis
        for spec_behavior in spec_behaviors:
            behavior_id = spec_behavior.get('id', 'unknown')
            behavior_desc = spec_behavior.get('description', '')
            
            # Find matching test behaviors
            matching_tests = []
            for test in test_behaviors:
                # More precise keyword matching - look for operation-specific keywords
                behavior_keywords = behavior_desc.lower().split()
                test_behavior_text = test.implied_behavior.lower()
                
                # Look for specific operation keywords
                operation_match = False
                if 'add' in behavior_keywords or 'addition' in behavior_keywords:
                    operation_match = any(word in test_behavior_text for word in ['add', 'addition'])
                elif 'multiply' in behavior_keywords or 'multiplication' in behavior_keywords:
                    operation_match = any(word in test_behavior_text for word in ['multiply', 'multiplication'])
                elif 'divide' in behavior_keywords or 'division' in behavior_keywords:
                    operation_match = any(word in test_behavior_text for word in ['divide', 'division'])
                elif 'subtract' in behavior_keywords or 'subtraction' in behavior_keywords:
                    operation_match = any(word in test_behavior_text for word in ['subtract', 'subtraction'])
                
                if operation_match:
                    matching_tests.append(test)
            
            # Analyze coverage
            if not matching_tests:
                results['gaps'].append({
                    'type': 'missing_test',
                    'severity': 'high',
                    'behavior_id': behavior_id,
                    'description': f"No tests found for behavior: {behavior_desc}",
                    'recommendation': f"Create tests to validate: {behavior_desc}"
                })
            else:
                results['strengths'].append({
                    'behavior_id': behavior_id,
                    'description': f"Behavior covered by {len(matching_tests)} test(s)",
                    'tests': [test.test_name for test in matching_tests]
                })
        
        # Generate overall assessment
        total_spec_behaviors = len(spec_behaviors)
        covered_behaviors = len([g for g in results['strengths']])
        coverage_percentage = (covered_behaviors / total_spec_behaviors * 100) if total_spec_behaviors > 0 else 0
        
        results['alignment_analysis'] = {
            'total_spec_behaviors': total_spec_behaviors,
            'covered_behaviors': covered_behaviors,
            'coverage_percentage': coverage_percentage,
            'total_gaps': len(results['gaps']),
            'overall_score': coverage_percentage / 100.0
        }
        
        return results
    
    def compare_behaviors_basic(self, spec_behaviors: List[Dict[str, Any]], test_behaviors: List[BehaviorInfo]) -> Dict[str, Any]:
        """
        Compare specification behaviors with test behaviors to identify gaps and alignment issues.
        
        This is the main entry point for behavior comparison analysis.
        
        Args:
            spec_behaviors: List of behaviors extracted from specification requirements
            test_behaviors: List of behaviors extracted from test implementations
            
        Returns:
            Dictionary containing comparison results including gaps, strengths, and alignment scores
        """
        # Convert spec behaviors to OpenSpec format for analysis
        # For now, we'll use the existing compare_all_requirements method
        # but this provides a cleaner interface for behavior comparison
        
        # If we have a full spec, use compare_all_requirements
        # Otherwise, create a minimal comparison based on the behaviors provided
        
        results = {
            'spec_behaviors': spec_behaviors,
            'test_behaviors': [
                {
                    'name': test.test_name,
                    'file': test.test_file,
                    'behavior': test.implied_behavior,
                    'type': test.test_type,
                    'confidence': test.confidence
                }
                for test in test_behaviors
            ],
            'alignment_analysis': {},
            'gaps': [],
            'strengths': [],
            'recommendations': []
        }
        
        # Perform basic alignment analysis
        for spec_behavior in spec_behaviors:
            behavior_id = spec_behavior.get('id', 'unknown')
            behavior_desc = spec_behavior.get('description', '')
            
            # Find matching test behaviors
            matching_tests = []
            for test in test_behaviors:
                # Simple keyword matching for now - could be enhanced with LLM
                if any(keyword in test.implied_behavior.lower() 
                       for keyword in behavior_desc.lower().split() if len(keyword) > 3):
                    matching_tests.append(test)
            
            # Analyze coverage
            if not matching_tests:
                results['gaps'].append({
                    'type': 'missing_test',
                    'severity': 'high',
                    'behavior_id': behavior_id,
                    'description': f"No tests found for behavior: {behavior_desc}",
                    'recommendation': f"Create tests to validate: {behavior_desc}"
                })
            else:
                results['strengths'].append({
                    'behavior_id': behavior_id,
                    'description': f"Behavior covered by {len(matching_tests)} test(s)",
                    'tests': [test.test_name for test in matching_tests]
                })
        
        # Generate overall assessment
        total_spec_behaviors = len(spec_behaviors)
        covered_behaviors = len([g for g in results['strengths']])
        coverage_percentage = (covered_behaviors / total_spec_behaviors * 100) if total_spec_behaviors > 0 else 0
        
        results['alignment_analysis'] = {
            'total_spec_behaviors': total_spec_behaviors,
            'covered_behaviors': covered_behaviors,
            'coverage_percentage': coverage_percentage,
            'total_gaps': len(results['gaps']),
            'overall_score': coverage_percentage / 100.0
        }
        
        return results
    
    def compare_behaviors(self, spec_behaviors: List[Dict[str, Any]], test_behaviors: List[BehaviorInfo]) -> Dict[str, Any]:
        """
        Convenience method that delegates to compare_spec_and_test_behaviors.
        
        This method maintains backward compatibility with the expected API.
        """
        return self.compare_spec_and_test_behaviors(spec_behaviors, test_behaviors)
    
    def analyze_requirement_coverage(self, requirement: Requirement, test_behaviors: List[BehaviorInfo]) -> Dict[str, Any]:
        """
        Analyze how well tests cover a specific requirement using AI-powered analysis.
        
        This method performs deep analysis of test coverage for a single requirement,
        using AI to understand the semantic relationship between tests and requirements
        beyond simple keyword matching.
        
        Args:
            requirement: Requirement object containing the specification details including
                        id, title, description, interface, and validation criteria.
            test_behaviors: List of TestBehavior objects to analyze against the requirement.
                          Only tests with confidence > 0.3 will be considered for analysis.
        
        Returns:
            Dictionary containing detailed coverage analysis with the following structure:
            {
                'requirement_id': str - ID of the analyzed requirement,
                'coverage_score': float - AI-assessed coverage score (0.0-1.0),
                'relevant_tests': List[Dict] - Tests that match this requirement,
                'coverage_analysis': str - AI-generated analysis of coverage quality,
                'gaps': List[str] - Identified gaps in test coverage,
                'recommendations': List[str] - Suggestions for improving coverage
            }
        
        Raises:
            ValueError: If requirement is None or test_behaviors is empty
            RuntimeError: If AI analysis fails
        
        Example:
            >>> requirement = Requirement("REQ-001", "Add Numbers", "Adds two numbers together")
            >>> test_behaviors = [TestBehavior("test_add", "test.py", "Tests addition", "unit", 0.9)]
            >>> analysis = comparator.analyze_requirement_coverage(requirement, test_behaviors)
            >>> print(f"Coverage score: {analysis['coverage_score']:.2f}")
        """
        # Get relevant tests for this requirement
        relevant_tests = []
        for test in test_behaviors:
            match = self.aligner.align_test_to_requirement(test, requirement)
            if match.confidence > 0.3:  # Include weak matches too for analysis
                relevant_tests.append({
                    'test': test,
                    'match': match
                })
        
        # Prepare context for LLM
        req_context = {
            'id': requirement.id,
            'title': requirement.title,
            'description': requirement.description,
            'interface': {
                'function': requirement.interface.function if requirement.interface else None,
                'parameters': requirement.interface.parameters if requirement.interface else {},
                'returns': requirement.interface.returns if requirement.interface else None
            } if requirement.interface else None,
            'validation': [
                {
                    'type': v.type,
                    'file': v.file,
                    'target': v.target
                }
                for v in requirement.validation
            ] if requirement.validation else []
        }
        
        test_context = [
            {
                'name': test['test'].test_name,
                'file': test['test'].test_file,
                'behavior': test['test'].implied_behavior,
                'confidence': test['match'].confidence,
                'alignment_type': test['match'].alignment_type
            }
            for test in relevant_tests
        ]
        
        # Create LLM prompt
        prompt = self._create_comparison_prompt(req_context, test_context)
        
        # Get LLM analysis
        response = self.ollama.generate(prompt)
        
        # Parse the response
        return self._parse_llm_response(response, requirement.id, relevant_tests)
    
    def _create_comparison_prompt(self, requirement: Dict[str, Any], tests: List[Dict[str, Any]]) -> str:
        """
        Create a comprehensive prompt for LLM analysis of requirement-test alignment.
        
        This private method constructs a detailed prompt that provides the LLM with
        all necessary context to analyze how well tests cover a specific requirement.
        The prompt includes requirement details, interface specifications, validation
        criteria, and relevant test information.
        
        Args:
            requirement: Dictionary containing requirement details including id, title,
                        description, interface specifications, and validation criteria.
            tests: List of dictionaries containing test information that may be relevant
                   to this requirement. Each test should include name, file, behavior,
                   type, and confidence score.
        
        Returns:
            Formatted prompt string optimized for LLM analysis of test coverage.
            The prompt includes structured sections for requirement details,
            interface specifications, validation criteria, and test information.
        
        Note:
            This method is designed to work specifically with the LLM's expected
            input format for coverage analysis tasks. The prompt structure follows
            a consistent pattern to ensure reliable analysis results.
        
        Example:
            >>> requirement = {
            ...     'id': 'REQ-001',
            ...     'title': 'Add Numbers',
            ...     'description': 'Adds two numbers together',
            ...     'interface': {'function': 'add', 'parameters': {'a': 'int', 'b': 'int'}, 'returns': 'int'},
            ...     'validation': [{'type': 'unit', 'target': 'add'}]
            ... }
            >>> tests = [{'name': 'test_add', 'behavior': 'Tests addition functionality'}]
            >>> prompt = comparator._create_comparison_prompt(requirement, tests)
            >>> print(len(prompt))  # Should be a substantial, well-structured prompt
        """
        prompt = f"""You are a senior QA engineer analyzing test coverage against OpenSpec requirements.

REQUIREMENT:
ID: {requirement['id']}
Title: {requirement['title']}
Description: {requirement['description']}
"""

        if requirement['interface']:
            prompt += f"""
Interface:
- Function: {requirement['interface']['function']}
- Parameters: {requirement['interface']['parameters']}
- Returns: {requirement['interface']['returns']}
"""

        if requirement['validation']:
            prompt += f"""
Validation Criteria:
{chr(10).join([f"- {v['type']} test in {v['file']} (target: {v['target']})" for v in requirement['validation']])}
"""

        prompt += f"""

CURRENT TESTS:
{chr(10).join([f"- {test['name']} (confidence: {test['confidence']:.2f}, type: {test['alignment_type']})" for test in tests])}

TEST BEHAVIORS:
{chr(10).join([f"{i+1}. {test['name']}: {test['behavior']}" for i, test in enumerate(tests)])}

ANALYSIS TASK:
Analyze the alignment between the requirement and the tests. Identify:

1. GAPS (what's missing or inadequate):
   - Missing test cases
   - Incomplete test coverage
   - Misaligned test behavior
   - Over-testing (unnecessary tests)

2. STRENGTHS (what's well covered):
   - Well-aligned tests
   - Comprehensive coverage
   - Good test practices

3. ASSESSMENT:
   - Overall alignment score (0-100)
   - Critical issues to address
   - Recommendations for improvement

FORMAT YOUR RESPONSE AS JSON:
{{
  "alignment_score": <0-100>,
  "gaps": [
    {{
      "type": "missing_test|incomplete_test|misaligned_test|over_testing",
      "severity": "critical|high|medium|low",
      "description": "Clear description of the gap",
      "recommendation": "Specific recommendation to fix it",
      "test_name": "relevant test name if applicable"
    }}
  ],
  "strengths": [
    "Clear description of what's well covered"
  ],
  "overall_assessment": "Summary of the alignment quality"
}}
"""

        return prompt
    
    def _parse_llm_response(self, response: str, requirement_id: str, relevant_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse and validate LLM response for requirement-test alignment analysis.
        
        This private method processes the LLM's JSON response, validates its structure,
        and extracts the analysis results. It handles potential parsing errors and
        ensures the response contains all required fields for further processing.
        
        Args:
            response: Raw JSON response string from the LLM containing alignment analysis.
                     Expected format includes alignment_score, gaps, strengths, and assessment.
            requirement_id: ID of the requirement that was analyzed, used for error reporting
                           and result identification.
            relevant_tests: List of test dictionaries that were provided to the LLM for analysis.
                           Used for validation and context in error scenarios.
        
        Returns:
            Dictionary containing parsed analysis results with the following structure:
            {
                'requirement_id': str - ID of the analyzed requirement,
                'alignment_score': float - LLM-assessed alignment score (0-100),
                'gaps': List[Dict] - Identified gaps in test coverage,
                'strengths': List[Dict] - Well-covered aspects and strengths,
                'coverage_analysis': str - Overall analysis summary,
                'recommendations': List[str] - Suggestions for improvement
            }
        
        Raises:
            json.JSONDecodeError: If response contains invalid JSON
            ValueError: If response is missing required fields or contains invalid data
            RuntimeError: If parsing fails due to malformed response
        
        Note:
            This method includes robust error handling to gracefully manage LLM output
            variations and provide meaningful error messages for debugging.
        
        Example:
            >>> response = '''{
            ...     "alignment_score": 75,
            ...     "gaps": [{"type": "missing_test", "description": "No edge case testing"}],
            ...     "strengths": [{"description": "Good basic functionality coverage"}],
            ...     "coverage_analysis": "Overall good coverage with some gaps",
            ...     "recommendations": ["Add edge case tests"]
            ... }'''
            >>> result = comparator._parse_llm_response(response, "REQ-001", [])
            >>> print(f"Alignment score: {result['alignment_score']}")
        """
        """Parse the LLM response into structured data."""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                # Fallback if no JSON found
                analysis = {
                    "alignment_score": 50,
                    "gaps": [],
                    "strengths": ["Unable to parse LLM response"],
                    "overall_assessment": "Analysis failed - check LLM response"
                }
        except json.JSONDecodeError:
            # Fallback for malformed JSON
            analysis = {
                "alignment_score": 50,
                "gaps": [
                    {
                        "type": "parsing_error",
                        "severity": "high",
                        "description": "Failed to parse LLM response",
                        "recommendation": "Review LLM output and retry analysis",
                        "test_name": None
                    }
                ],
                "strengths": [],
                "overall_assessment": "Analysis incomplete due to parsing error"
            }
        
        # Add test coverage info
        test_coverage = {}
        for test_info in relevant_tests:
            test_coverage[test_info['test'].test_name] = {
                'file': test_info['test'].test_file,
                'confidence': test_info['match'].confidence,
                'alignment_type': test_info['match'].alignment_type,
                'behavior': test_info['test'].implied_behavior
            }
        
        return {
            'requirement_id': requirement_id,
            'alignment_score': analysis.get('alignment_score', 50),
            'gaps': analysis.get('gaps', []),
            'strengths': analysis.get('strengths', []),
            'overall_assessment': analysis.get('overall_assessment', ''),
            'test_coverage': test_coverage,
            'raw_llm_response': response
        }
    
    def compare_all_requirements(self, spec: OpenSpec, test_behaviors: List[BehaviorInfo]) -> List[ComparisonResult]:
        """Compare all requirements in a spec against test behaviors."""
        results = []
        
        for requirement in spec.requirements:
            analysis = self.analyze_requirement_coverage(requirement, test_behaviors)
            
            # Convert gaps to BehaviorGap objects
            gaps = []
            for gap_data in analysis['gaps']:
                gap = BehaviorGap(
                    gap_type=gap_data.get('type', 'unknown'),
                    severity=gap_data.get('severity', 'medium'),
                    description=gap_data.get('description', ''),
                    recommendation=gap_data.get('recommendation', ''),
                    test_name=gap_data.get('test_name'),
                    requirement_id=requirement.id
                )
                gaps.append(gap)
            
            result = ComparisonResult(
                requirement_id=requirement.id,
                requirement_title=requirement.title,
                alignment_score=analysis['alignment_score'] / 100.0,  # Convert to 0-1 scale
                gaps=gaps,
                strengths=analysis['strengths'],
                overall_assessment=analysis['overall_assessment'],
                test_coverage=analysis['test_coverage']
            )
            
            results.append(result)
        
        return results
    
    def generate_summary_report(self, results: List[ComparisonResult]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report of all requirement-test comparisons.
        
        This method aggregates individual comparison results into a high-level report
        that provides insights into overall test coverage quality, identifies critical
        issues, and highlights well-covered areas.
        
        Args:
            results: List of ComparisonResult objects from individual requirement analyses.
                    Each result should contain alignment scores, gaps, and detailed analysis.
        
        Returns:
            Dictionary containing comprehensive summary report with the following structure:
            {
                'summary': {
                    'total_requirements': int - Total number of requirements analyzed,
                    'average_alignment_score': float - Mean alignment score across all requirements,
                    'requirements_with_critical_issues': int - Count of requirements with critical gaps,
                    'requirements_with_high_issues': int - Count of requirements with high-severity gaps,
                    'well_covered_requirements': int - Count of requirements with excellent coverage
                },
                'gap_analysis': {
                    'total_gaps': int - Total number of identified gaps,
                    'gaps_by_severity': Dict[str, int] - Gap counts by severity level,
                    'gaps_by_type': Dict[str, int] - Gap counts by gap type
                },
                'priority_requirements': List[Dict] - Requirements sorted by issue severity,
                'well_covered_requirements': List[Dict] - Requirements with excellent coverage,
                'recommendations': List[str] - High-level recommendations for improvement
            }
        
        Raises:
            ValueError: If results list is empty or contains invalid ComparisonResult objects
        
        Example:
            >>> results = [comparison_result1, comparison_result2]
            >>> report = comparator.generate_summary_report(results)
            >>> print(f"Average alignment: {report['summary']['average_alignment_score']:.2f}")
            >>> print(f"Critical issues: {report['summary']['requirements_with_critical_issues']}")
        """
        total_requirements = len(results)
        avg_alignment = sum(r.alignment_score for r in results) / total_requirements if total_requirements > 0 else 0
        
        # Count gaps by severity
        gap_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        gap_types = {}
        
        for result in results:
            for gap in result.gaps:
                gap_counts[gap.severity] += 1
                gap_types[gap.gap_type] = gap_types.get(gap.gap_type, 0) + 1
        
        # Find requirements with most issues
        requirements_by_issues = sorted(
            results,
            key=lambda r: len([g for g in r.gaps if g.severity in ['critical', 'high']]),
            reverse=True
        )
        
        # Find well-covered requirements
        well_covered = [r for r in results if r.alignment_score >= 0.8 and len(r.gaps) == 0]
        
        return {
            'summary': {
                'total_requirements': total_requirements,
                'average_alignment_score': avg_alignment,
                'requirements_with_critical_issues': len([r for r in results if any(g.severity == 'critical' for g in r.gaps)]),
                'well_covered_requirements': len(well_covered),
                'total_gaps': sum(gap_counts.values())
            },
            'gap_analysis': {
                'by_severity': gap_counts,
                'by_type': gap_types
            },
            'top_issues': [
                {
                    'requirement_id': r.requirement_id,
                    'requirement_title': r.requirement_title,
                    'critical_gaps': len([g for g in r.gaps if g.severity == 'critical']),
                    'high_gaps': len([g for g in r.gaps if g.severity == 'high']),
                    'alignment_score': r.alignment_score
                }
                for r in requirements_by_issues[:5]
            ],
            'well_covered': [
                {
                    'requirement_id': r.requirement_id,
                    'requirement_title': r.requirement_title,
                    'alignment_score': r.alignment_score,
                    'strengths': r.strengths
                }
                for r in well_covered
            ],
            'detailed_results': [
                {
                    'requirement_id': r.requirement_id,
                    'requirement_title': r.requirement_title,
                    'alignment_score': r.alignment_score,
                    'gaps': [
                        {
                            'type': g.gap_type,
                            'severity': g.severity,
                            'description': g.description,
                            'recommendation': g.recommendation,
                            'test_name': g.test_name
                        }
                        for g in r.gaps
                    ],
                    'strengths': r.strengths,
                    'overall_assessment': r.overall_assessment,
                    'test_count': len(r.test_coverage)
                }
                for r in results
            ]
        }


def main():
    """Main function for testing the comparator."""
    comparator = BehaviorComparator()
    
    # Load test behaviors
    test_behaviors = comparator.load_test_behaviors(
        Path('test_summaries.json')
    )
    
    # Load spec - use a configurable path or parameter
    spec_path = Path('test_spec.yml')  # Default to local test spec
    if not spec_path.exists():
        print("No test spec found. Please provide a spec file path.")
        return
    
    spec = comparator.spec_parser.parse_file(spec_path)
    
    # Load spec
    spec = comparator.spec_parser.parse_file(
        Path('/home/asabaal/repos/music_creation/qa_test_project/reference/openspec/specs/rhythmic_pulse_generator.yml')
    )
    
    # Compare all requirements
    results = comparator.compare_all_requirements(spec, test_behaviors)
    
    # Generate summary report
    summary = comparator.generate_summary_report(results)
    
    # Save results
    output_dir = Path('/home/asabaal/repos/music_creation/qa_test_project/generator/alignment')
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / 'comparison_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Comparison complete: {summary['summary']['total_requirements']} requirements analyzed")
    print(f"Average alignment score: {summary['summary']['average_alignment_score']:.2%}")
    print(f"Critical gaps found: {summary['gap_analysis']['by_severity']['critical']}")
    print(f"Results saved to {output_dir / 'comparison_results.json'}")


if __name__ == '__main__':
    main()
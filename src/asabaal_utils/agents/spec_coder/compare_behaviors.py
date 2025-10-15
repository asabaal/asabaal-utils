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

try:
    from .ollama_client import OllamaClient, GenerationConfig
    from .align_behaviors import BehavioralAligner, AlignmentMatch, TestBehavior
    from .spec_parser import SpecParser, OpenSpec, Requirement
except ImportError:
    # Add parent directory to path for imports
    sys.path.append(str(Path(__file__).parent))
    from ollama_client import OllamaClient, GenerationConfig
    from align_behaviors import BehavioralAligner, AlignmentMatch, TestBehavior
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
    """Compares test behaviors with OpenSpec requirements using LLM analysis."""
    
    def __init__(self, model_name: str = "qwen3-coder:latest"):
        config = GenerationConfig(model=model_name)
        self.ollama = OllamaClient(config)
        self.aligner = BehavioralAligner()
        self.spec_parser = SpecParser()
    
    def analyze_requirement_coverage(self, requirement: Requirement, test_behaviors: List[TestBehavior]) -> Dict[str, Any]:
        """Analyze how well tests cover a specific requirement."""
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
        """Create a prompt for LLM to analyze requirement-test alignment."""
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
    
    def compare_all_requirements(self, spec: OpenSpec, test_behaviors: List[TestBehavior]) -> List[ComparisonResult]:
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
        """Generate a summary report of all comparisons."""
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
    test_behaviors = comparator.aligner.load_test_behaviors(
        Path('/home/asabaal/repos/music_creation/qa_test_project/generator/analysis/combined_analysis.json')
    )
    
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
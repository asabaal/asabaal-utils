"""
Behavioral Alignment Engine

Matches test behaviors with OpenSpec requirements to identify what each test validates.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
try:
    from .spec_parser import SpecParser, OpenSpec, Requirement
except ImportError:
    from spec_parser import SpecParser, OpenSpec, Requirement


@dataclass
class TestBehavior:
    """Represents a test's implied behavior from analysis."""
    test_name: str
    test_file: str
    implied_behavior: str
    test_type: str  # 'unit', 'integration', etc.
    confidence: float  # 0-1 confidence score from AI


@dataclass
class AlignmentMatch:
    """Represents a match between a test and a requirement."""
    test: TestBehavior
    requirement: Optional[Requirement]  # None for additional tests
    confidence: float
    match_reason: str
    alignment_type: str  # 'direct', 'partial', 'indirect', 'none', 'additional'
    is_specified: bool  # True if test is for a requirement in OpenSpec


class BehavioralAligner:
    """Aligns test behaviors with OpenSpec requirements."""
    
    def __init__(self):
        self.spec_parser = SpecParser()
    
    def load_test_behaviors(self, analysis_file: Path) -> List[TestBehavior]:
        """Load test behaviors from the analysis output."""
        with open(analysis_file, 'r') as f:
            data = json.load(f)
        
        behaviors = []
        # Handle both combined and individual file formats
        if 'files' in data:
            # Combined format
            for file_data in data['files']:
                file_path = file_data.get('file', file_data.get('file_path', 'unknown'))
                for test_data in file_data['tests']:
                    behavior = TestBehavior(
                        test_name=test_data['name'],  # Changed from 'test_name' to 'name'
                        test_file=file_path,
                        implied_behavior=test_data['implied_behavior'],
                        test_type=self._infer_test_type(test_data['name']),
                        confidence=0.8  # Default confidence
                    )
                    behaviors.append(behavior)
        elif 'tests' in data:
            # Single file format
            file_path = data.get('file', data.get('file_path', 'unknown'))
            for test_data in data['tests']:
                behavior = TestBehavior(
                    test_name=test_data['name'],  # Changed from 'test_name' to 'name'
                    test_file=file_path,
                    implied_behavior=test_data['implied_behavior'],
                    test_type=self._infer_test_type(test_data['name']),
                    confidence=0.8  # Default confidence
                )
                behaviors.append(behavior)
        
        return behaviors
    
    def load_spec(self, spec_file: Path) -> OpenSpec:
        """Load OpenSpec from file."""
        return self.spec_parser.parse_file(spec_file)
    
    def _infer_test_type(self, test_name: str) -> str:
        """Infer test type from test name."""
        test_name_lower = test_name.lower()
        
        if any(keyword in test_name_lower for keyword in ['integration', 'end_to_end', 'e2e']):
            return 'integration'
        elif any(keyword in test_name_lower for keyword in ['unit', 'test_']):
            return 'unit'
        elif any(keyword in test_name_lower for keyword in ['performance', 'load', 'stress']):
            return 'performance'
        else:
            return 'unit'
    
    def _calculate_keyword_match(self, test_behavior: TestBehavior, requirement: Requirement) -> float:
        """Calculate keyword-based match score."""
        test_text = f"{test_behavior.test_name} {test_behavior.implied_behavior}".lower()
        req_text = f"{requirement.title} {requirement.description}".lower()
        
        # Extract keywords from requirement
        req_keywords = set(re.findall(r'\b\w+\b', req_text))
        req_keywords.discard('the')
        req_keywords.discard('a')
        req_keywords.discard('an')
        req_keywords.discard('and')
        req_keywords.discard('or')
        req_keywords.discard('but')
        
        # Count matches
        matches = sum(1 for keyword in req_keywords if keyword in test_text)
        
        if len(req_keywords) == 0:
            return 0.0
        
        return matches / len(req_keywords)
    
    def _calculate_function_match(self, test_behavior: TestBehavior, requirement: Requirement) -> float:
        """Calculate function name match score."""
        if not requirement.interface:
            return 0.0
        
        func_name = requirement.interface.function.lower()
        test_text = f"{test_behavior.test_name} {test_behavior.implied_behavior}".lower()
        
        # Direct function name match
        if func_name in test_text:
            return 1.0
        
        # Partial match
        func_parts = func_name.split('_')
        matches = sum(1 for part in func_parts if part in test_text)
        
        return matches / len(func_parts) if func_parts else 0.0
    
    def _calculate_validation_match(self, test_behavior: TestBehavior, requirement: Requirement) -> float:
        """Calculate validation criteria match score."""
        if not requirement.validation:
            return 0.0
        
        test_type = test_behavior.test_type
        validation_types = [v.type for v in requirement.validation]
        
        # Direct type match
        if test_type in validation_types:
            return 1.0
        
        # Partial match (unit tests can validate integration criteria, etc.)
        if test_type == 'unit' and 'integration' in validation_types:
            return 0.5
        elif test_type == 'integration' and 'unit' in validation_types:
            return 0.7
        
        return 0.0
    
    def align_test_to_requirement(self, test_behavior: TestBehavior, requirement: Requirement) -> AlignmentMatch:
        """Align a single test to a requirement."""
        keyword_score = self._calculate_keyword_match(test_behavior, requirement)
        function_score = self._calculate_function_match(test_behavior, requirement)
        validation_score = self._calculate_validation_match(test_behavior, requirement)
        
        # Weighted average
        total_score = (keyword_score * 0.4 + function_score * 0.4 + validation_score * 0.2)
        
        # Determine alignment type and reason
        if total_score >= 0.8:
            alignment_type = 'direct'
            match_reason = f"Strong match: keywords ({keyword_score:.2f}), function ({function_score:.2f}), validation ({validation_score:.2f})"
        elif total_score >= 0.5:
            alignment_type = 'partial'
            match_reason = f"Partial match: keywords ({keyword_score:.2f}), function ({function_score:.2f}), validation ({validation_score:.2f})"
        elif total_score >= 0.3:
            alignment_type = 'indirect'
            match_reason = f"Weak match: keywords ({keyword_score:.2f}), function ({function_score:.2f}), validation ({validation_score:.2f})"
        else:
            alignment_type = 'none'
            match_reason = f"No significant match: keywords ({keyword_score:.2f}), function ({function_score:.2f}), validation ({validation_score:.2f})"
        
        return AlignmentMatch(
            test=test_behavior,
            requirement=requirement,
            confidence=total_score,
            match_reason=match_reason,
            alignment_type=alignment_type,
            is_specified=True  # Will be set properly in align_all_tests
        )
    
    def align_all_tests(self, test_behaviors: List[TestBehavior], spec: OpenSpec) -> List[AlignmentMatch]:
        """Align all tests to all requirements."""
        matches = []
        
        # Group tests by file to track expected vs actual test counts
        tests_by_file = {}
        for test_behavior in test_behaviors:
            file_name = Path(test_behavior.test_file).name
            if file_name not in tests_by_file:
                tests_by_file[file_name] = []
            tests_by_file[file_name].append(test_behavior)
        
        # Count expected tests per file from OpenSpec
        expected_tests_per_file = {}
        for requirement in spec.requirements:
            if requirement.validation:
                for validation in requirement.validation:
                    if validation.file:
                        expected_tests_per_file[validation.file] = 1  # OpenSpec expects 1 test per file
        
        # Create a mapping from actual files to expected files
        file_mapping = {}
        for file_name in tests_by_file.keys():
            # Try to find a matching expected file
            for expected_file in expected_tests_per_file.keys():
                # Strip extensions and compare base names
                actual_base = file_name.replace('.py', '')
                expected_base = expected_file.replace('.py', '')
                if actual_base.startswith(expected_base) or expected_base.startswith(actual_base):
                    file_mapping[file_name] = expected_file
                    break
            else:
                file_mapping[file_name] = None
        
        for test_behavior in test_behaviors:
            best_match = None
            best_score = 0.0
            
            for requirement in spec.requirements:
                match = self.align_test_to_requirement(test_behavior, requirement)
                
                # Keep the best match for each test
                if match.confidence > best_score:
                    best_match = match
                    best_score = match.confidence
            
            file_name = Path(test_behavior.test_file).name
            expected_file = file_mapping.get(file_name)
            
            if best_match and best_score >= 0.3:  # Threshold for considering it a real match
                # Check if this test is within the expected count for this file
                file_tests = [t for t in matches if Path(t.test.test_file).name == file_name and t.is_specified]
                expected_count = expected_tests_per_file.get(expected_file, 0) if expected_file else 0
                
                if len(file_tests) < expected_count:
                    # This test is within the expected count
                    best_match.is_specified = True
                else:
                    # This test exceeds the expected count, mark as additional
                    best_match.is_specified = False
                    best_match.alignment_type = "additional"
                    best_match.match_reason = f"Additional test - OpenSpec expects {expected_count} test(s) for {expected_file or file_name}"
                
                matches.append(best_match)
            else:
                # Create an "additional" test entry for tests not matching any requirement
                additional_match = AlignmentMatch(
                    test=test_behavior,
                    requirement=None,
                    confidence=0.0,
                    match_reason="No matching requirement found in OpenSpec",
                    alignment_type="additional",
                    is_specified=False
                )
                matches.append(additional_match)
        
        return matches
    
    def generate_alignment_report(self, matches: List[AlignmentMatch]) -> Dict[str, Any]:
        """Generate a summary report of alignments."""
        total_tests = len(matches)
        specified_tests = [m for m in matches if m.is_specified]
        additional_tests = [m for m in matches if not m.is_specified]
        
        direct_matches = sum(1 for m in specified_tests if m.alignment_type == 'direct')
        partial_matches = sum(1 for m in specified_tests if m.alignment_type == 'partial')
        indirect_matches = sum(1 for m in specified_tests if m.alignment_type == 'indirect')
        no_matches = sum(1 for m in specified_tests if m.alignment_type == 'none')
        
        # Group by requirement (only for specified tests)
        req_coverage = {}
        for match in specified_tests:
            if match.requirement:  # Should always be true for specified tests
                req_id = match.requirement.id
                if req_id not in req_coverage:
                    req_coverage[req_id] = {
                        'requirement_title': match.requirement.title,
                        'tests': [],
                        'coverage_score': 0.0
                    }
                req_coverage[req_id]['tests'].append({
                    'test_name': match.test.test_name,
                    'test_file': match.test.test_file,
                    'confidence': match.confidence,
                    'alignment_type': match.alignment_type,
                    'implied_behavior': match.test.implied_behavior
                })
        
        # Calculate coverage scores
        for req_id, data in req_coverage.items():
            if data['tests']:
                data['coverage_score'] = sum(t['confidence'] for t in data['tests']) / len(data['tests'])
        
        return {
            'summary': {
                'total_tests': total_tests,
                'specified_tests': len(specified_tests),
                'additional_tests': len(additional_tests),
                'direct_matches': direct_matches,
                'partial_matches': partial_matches,
                'indirect_matches': indirect_matches,
                'no_matches': no_matches,
                'alignment_rate': (direct_matches + partial_matches) / len(specified_tests) if specified_tests else 0
            },
            'requirement_coverage': req_coverage,
            'additional_tests': [
                {
                    'test_name': m.test.test_name,
                    'test_file': m.test.test_file,
                    'test_type': m.test.test_type,
                    'implied_behavior': m.test.implied_behavior,
                    'match_reason': m.match_reason
                }
                for m in additional_tests
            ],
            'detailed_matches': [
                {
                    'test_name': m.test.test_name,
                    'test_file': m.test.test_file,
                    'requirement_id': m.requirement.id if m.requirement else None,
                    'requirement_title': m.requirement.title if m.requirement else None,
                    'confidence': m.confidence,
                    'alignment_type': m.alignment_type,
                    'match_reason': m.match_reason,
                    'is_specified': m.is_specified,
                    'implied_behavior': m.test.implied_behavior
                }
                for m in matches
            ]
        }


def main():
    """Main function for testing the aligner."""
    aligner = BehavioralAligner()
    
    # Load test behaviors
    test_behaviors = aligner.load_test_behaviors(
        Path('/home/asabaal/repos/music_creation/qa_test_project/generator/analysis/combined_test_summary.json')
    )
    
    # Load spec
    spec = aligner.load_spec(
        Path('/home/asabaal/repos/music_creation/qa_test_project/reference/openspec/specs/rhythmic_pulse_generator.yml')
    )
    
    # Align
    matches = aligner.align_all_tests(test_behaviors, spec)
    
    # Generate report
    report = aligner.generate_alignment_report(matches)
    
    # Save report
    output_dir = Path('/home/asabaal/repos/music_creation/qa_test_project/generator/alignment')
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / 'alignment_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Alignment complete: {report['summary']['total_tests']} tests analyzed")
    print(f"Direct matches: {report['summary']['direct_matches']}")
    print(f"Partial matches: {report['summary']['partial_matches']}")
    print(f"Alignment rate: {report['summary']['alignment_rate']:.2%}")


if __name__ == '__main__':
    main()
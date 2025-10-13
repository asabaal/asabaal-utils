#!/usr/bin/env python3
"""
Stage 5: Issue Extraction with Validation
Validate parsed issues, remove duplicates, apply business logic, and prepare final results
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import from Stage 4
from .stage4_response_parsing import QualityIssue, IssueType, Priority


class ValidationResult(Enum):
    """Issue validation results"""
    VALID = "valid"
    DUPLICATE = "duplicate"
    LOW_CONFIDENCE = "low_confidence"
    INSUFFICIENT_DETAIL = "insufficient_detail"
    FALSE_POSITIVE = "false_positive"


@dataclass
class ValidatedIssue:
    """Validated quality issue with additional metadata"""
    original_issue: QualityIssue
    validation_result: ValidationResult
    validation_notes: str
    business_impact_score: float  # 0.0 to 10.0
    action_required: bool
    duplicate_of: Optional[str] = None  # ID of original issue if this is a duplicate


class IssueValidator:
    """Validate and filter quality issues"""
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.test_output_dir = Path(output_dir) / "debug_outputs" / "stage5"
            self.stage4_dir = Path(output_dir) / "debug_outputs" / "stage4"
        else:
            self.test_output_dir = Path(__file__).parent / "debug_outputs" / "stage5"
            self.stage4_dir = Path(__file__).parent / "debug_outputs" / "stage4"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔧 Issue Validator initialized:")
        print(f"   Loading issues from: {self.stage4_dir}")
        print(f"   Debug outputs to: {self.test_output_dir}")
        
        # Validation rules configuration
        self.min_confidence_threshold = 0.4
        self.duplicate_similarity_threshold = 0.8
        
        # Business impact scoring weights
        self.impact_weights = {
            IssueType.DUPLICATE: 7.0,       # High impact - wastes developer time
            IssueType.MERGE_BLOCKER: 9.0,   # Critical - blocks deployment
            IssueType.MERGE_WARNING: 6.0,   # Medium-high - affects deployment safety
            IssueType.PATTERN_ISSUE: 4.0,   # Medium - affects maintainability
            IssueType.ORGANIZATION: 3.0,    # Low-medium - affects developer experience
            IssueType.CODE_QUALITY: 5.0     # Medium - affects code health
        }
    
    def load_stage4_issues(self) -> List[QualityIssue]:
        """Load quality issues from Stage 4"""
        print("\n📂 Loading Stage 4 issues...")
        
        issues_file = self.stage4_dir / "all_issues.json"
        
        if not issues_file.exists():
            raise RuntimeError("Stage 4 issues not found - run Stage 4 first!")
        
        with open(issues_file, 'r') as f:
            issues_data = json.load(f)
        
        # Convert back to QualityIssue objects
        issues = []
        for issue_dict in issues_data:
            issue = QualityIssue(
                id=issue_dict['id'],
                type=IssueType(issue_dict['type']),
                priority=Priority(issue_dict['priority']),
                title=issue_dict['title'],
                description=issue_dict['description'],
                files_affected=issue_dict['files_affected'],
                recommendation=issue_dict['recommendation'],
                source_agent=issue_dict['source_agent'],
                raw_text=issue_dict['raw_text'],
                confidence=issue_dict['confidence']
            )
            issues.append(issue)
        
        print(f"   ✅ Loaded {len(issues)} issues from Stage 4")
        return issues
    
    def validate_individual_issue(self, issue: QualityIssue) -> ValidatedIssue:
        """Validate an individual issue"""
        validation_notes = []
        
        # Check 1: Confidence threshold
        if issue.confidence < self.min_confidence_threshold:
            return ValidatedIssue(
                original_issue=issue,
                validation_result=ValidationResult.LOW_CONFIDENCE,
                validation_notes=f"Confidence {issue.confidence:.2f} below threshold {self.min_confidence_threshold}",
                business_impact_score=0.0,
                action_required=False
            )
        
        validation_notes.append(f"Confidence {issue.confidence:.2f} acceptable")
        
        # Check 2: Sufficient detail
        has_detail = bool(issue.description.strip() and len(issue.description) > 10)
        has_recommendation = bool(issue.recommendation.strip() and len(issue.recommendation) > 5)
        
        if not (has_detail and has_recommendation):
            return ValidatedIssue(
                original_issue=issue,
                validation_result=ValidationResult.INSUFFICIENT_DETAIL,
                validation_notes=f"Missing detail: description={has_detail}, recommendation={has_recommendation}",
                business_impact_score=0.0,
                action_required=False
            )
        
        validation_notes.append("Sufficient detail provided")
        
        # Check 3: False positive detection
        false_positive_patterns = [
            r"placeholder",
            r"todo",
            r"test.*test",
            r"example.*example"
        ]
        
        combined_text = f"{issue.title} {issue.description}".lower()
        
        for pattern in false_positive_patterns:
            if re.search(pattern, combined_text):
                return ValidatedIssue(
                    original_issue=issue,
                    validation_result=ValidationResult.FALSE_POSITIVE,
                    validation_notes=f"Matches false positive pattern: {pattern}",
                    business_impact_score=0.0,
                    action_required=False
                )
        
        validation_notes.append("No false positive patterns detected")
        
        # Calculate business impact score
        base_impact = self.impact_weights.get(issue.type, 5.0)
        
        # Priority multiplier
        priority_multiplier = {
            Priority.CRITICAL: 1.5,
            Priority.HIGH: 1.2,
            Priority.MEDIUM: 1.0,
            Priority.LOW: 0.7
        }[issue.priority]
        
        # File count multiplier (more files = higher impact)
        file_multiplier = min(1.5, 1.0 + len(issue.files_affected) * 0.1)
        
        # Confidence multiplier
        confidence_multiplier = 0.5 + (issue.confidence * 0.5)
        
        business_impact_score = base_impact * priority_multiplier * file_multiplier * confidence_multiplier
        business_impact_score = min(10.0, business_impact_score)  # Cap at 10
        
        validation_notes.append(f"Business impact: {business_impact_score:.1f}/10.0")
        
        # Determine if action is required
        action_required = (
            business_impact_score >= 3.0 and
            issue.priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM]
        )
        
        validation_notes.append(f"Action required: {action_required}")
        
        return ValidatedIssue(
            original_issue=issue,
            validation_result=ValidationResult.VALID,
            validation_notes=" | ".join(validation_notes),
            business_impact_score=business_impact_score,
            action_required=action_required
        )
    
    def find_duplicate_issues(self, validated_issues: List[ValidatedIssue]) -> List[ValidatedIssue]:
        """Find and mark duplicate issues"""
        print("\n🔍 Finding duplicate issues...")
        
        # Group issues by type and similarity
        type_groups = defaultdict(list)
        
        for validated_issue in validated_issues:
            if validated_issue.validation_result == ValidationResult.VALID:
                issue_type = validated_issue.original_issue.type
                type_groups[issue_type].append(validated_issue)
        
        # Find duplicates within each type
        duplicates_found = 0
        
        for issue_type, group in type_groups.items():
            print(f"   Checking {len(group)} {issue_type.value} issues for duplicates...")
            
            for i in range(len(group)):
                if group[i].validation_result != ValidationResult.VALID:
                    continue
                    
                for j in range(i + 1, len(group)):
                    if group[j].validation_result != ValidationResult.VALID:
                        continue
                    
                    # Calculate similarity
                    similarity = self._calculate_issue_similarity(
                        group[i].original_issue, 
                        group[j].original_issue
                    )
                    
                    if similarity >= self.duplicate_similarity_threshold:
                        # Mark the lower confidence one as duplicate
                        if group[i].original_issue.confidence >= group[j].original_issue.confidence:
                            group[j].validation_result = ValidationResult.DUPLICATE
                            group[j].duplicate_of = group[i].original_issue.id
                            group[j].validation_notes += f" | Duplicate of {group[i].original_issue.id} (similarity: {similarity:.2f})"
                        else:
                            group[i].validation_result = ValidationResult.DUPLICATE
                            group[i].duplicate_of = group[j].original_issue.id
                            group[i].validation_notes += f" | Duplicate of {group[j].original_issue.id} (similarity: {similarity:.2f})"
                        
                        duplicates_found += 1
        
        print(f"   Found {duplicates_found} duplicate issues")
        return validated_issues
    
    def _calculate_issue_similarity(self, issue1: QualityIssue, issue2: QualityIssue) -> float:
        """Calculate similarity between two issues"""
        
        # Title similarity
        title1_words = set(issue1.title.lower().split())
        title2_words = set(issue2.title.lower().split())
        
        if title1_words and title2_words:
            title_similarity = len(title1_words & title2_words) / len(title1_words | title2_words)
        else:
            title_similarity = 0.0
        
        # Files overlap
        files1 = set(issue1.files_affected)
        files2 = set(issue2.files_affected)
        
        if files1 and files2:
            files_similarity = len(files1 & files2) / len(files1 | files2)
        else:
            files_similarity = 0.0
        
        # Description similarity (simple word overlap)
        desc1_words = set(issue1.description.lower().split())
        desc2_words = set(issue2.description.lower().split())
        
        if desc1_words and desc2_words:
            desc_similarity = len(desc1_words & desc2_words) / len(desc1_words | desc2_words)
        else:
            desc_similarity = 0.0
        
        # Weighted average
        similarity = (
            title_similarity * 0.4 +
            files_similarity * 0.4 +
            desc_similarity * 0.2
        )
        
        return similarity
    
    def test_validation_rules(self, issues: List[QualityIssue]) -> Dict[str, Any]:
        """Test validation rules on all issues"""
        print("\n🧪 Testing validation rules...")
        
        validation_results = {
            'total_issues': len(issues),
            'validation_counts': defaultdict(int),
            'sample_validations': [],
            'business_impact_distribution': defaultdict(int),
            'action_required_count': 0
        }
        
        validated_issues = []
        
        for issue in issues:
            validated = self.validate_individual_issue(issue)
            validated_issues.append(validated)
            
            # Count validation results
            validation_results['validation_counts'][validated.validation_result.value] += 1
            
            # Count business impact distribution
            impact_bucket = f"{int(validated.business_impact_score)}-{int(validated.business_impact_score)+1}"
            validation_results['business_impact_distribution'][impact_bucket] += 1
            
            if validated.action_required:
                validation_results['action_required_count'] += 1
            
            # Sample for debugging
            if len(validation_results['sample_validations']) < 5:
                validation_results['sample_validations'].append({
                    'issue_id': issue.id,
                    'validation_result': validated.validation_result.value,
                    'business_impact': validated.business_impact_score,
                    'action_required': validated.action_required,
                    'notes': validated.validation_notes[:100]
                })
        
        # Convert defaultdict to regular dict for JSON serialization
        validation_results['validation_counts'] = dict(validation_results['validation_counts'])
        validation_results['business_impact_distribution'] = dict(validation_results['business_impact_distribution'])
        
        # Save validation test results
        with open(self.test_output_dir / "validation_test_results.json", 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        print(f"   Total issues validated: {len(issues)}")
        print(f"   Validation results:")
        for result_type, count in validation_results['validation_counts'].items():
            print(f"     • {result_type}: {count}")
        print(f"   Action required: {validation_results['action_required_count']}")
        
        return validation_results, validated_issues
    
    def test_duplicate_detection(self, validated_issues: List[ValidatedIssue]) -> List[ValidatedIssue]:
        """Test duplicate detection with full debugging"""
        print("\n🧪 Testing duplicate detection...")
        
        initial_valid_count = sum(1 for v in validated_issues if v.validation_result == ValidationResult.VALID)
        
        # Find duplicates
        updated_issues = self.find_duplicate_issues(validated_issues)
        
        final_valid_count = sum(1 for v in updated_issues if v.validation_result == ValidationResult.VALID)
        duplicates_found = sum(1 for v in updated_issues if v.validation_result == ValidationResult.DUPLICATE)
        
        duplicate_analysis = {
            'initial_valid_issues': initial_valid_count,
            'final_valid_issues': final_valid_count,
            'duplicates_found': duplicates_found,
            'duplicate_pairs': []
        }
        
        # Collect duplicate pairs for analysis
        for issue in updated_issues:
            if issue.validation_result == ValidationResult.DUPLICATE and issue.duplicate_of:
                duplicate_analysis['duplicate_pairs'].append({
                    'duplicate_issue': issue.original_issue.id,
                    'original_issue': issue.duplicate_of,
                    'duplicate_title': issue.original_issue.title[:50],
                    'similarity_note': issue.validation_notes.split('similarity: ')[-1] if 'similarity:' in issue.validation_notes else 'N/A'
                })
        
        with open(self.test_output_dir / "duplicate_detection_results.json", 'w') as f:
            json.dump(duplicate_analysis, f, indent=2)
        
        print(f"   Valid issues: {initial_valid_count} → {final_valid_count}")
        print(f"   Duplicates found: {duplicates_found}")
        
        return updated_issues
    
    def create_final_issue_list(self, validated_issues: List[ValidatedIssue]) -> List[ValidatedIssue]:
        """Create final filtered and prioritized issue list"""
        print("\n📋 Creating final issue list...")
        
        # Filter to valid, actionable issues
        final_issues = [
            v for v in validated_issues 
            if v.validation_result == ValidationResult.VALID and v.action_required
        ]
        
        # Sort by business impact score (descending) then by priority
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        
        final_issues.sort(key=lambda x: (-x.business_impact_score, priority_order[x.original_issue.priority]))
        
        print(f"   Final actionable issues: {len(final_issues)}")
        
        # Create summary by category
        category_summary = defaultdict(int)
        impact_summary = defaultdict(list)
        
        for issue in final_issues:
            category_summary[issue.original_issue.type.value] += 1
            impact_bucket = f"{int(issue.business_impact_score)}-{int(issue.business_impact_score)+0.9:.0f}"
            impact_summary[impact_bucket].append(issue.original_issue.id)
        
        summary = {
            'total_actionable_issues': len(final_issues),
            'issues_by_type': dict(category_summary),
            'business_impact_distribution': {k: len(v) for k, v in impact_summary.items()},
            'top_5_issues': [
                {
                    'id': issue.original_issue.id,
                    'title': issue.original_issue.title,
                    'type': issue.original_issue.type.value,
                    'priority': issue.original_issue.priority.value,
                    'business_impact': issue.business_impact_score,
                    'files_count': len(issue.original_issue.files_affected)
                }
                for issue in final_issues[:5]
            ]
        }
        
        with open(self.test_output_dir / "final_issue_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   Issues by type:")
        for issue_type, count in category_summary.items():
            print(f"     • {issue_type}: {count}")
        
        return final_issues
    
    def analyze_extraction_results(self, 
                                 original_issues: List[QualityIssue],
                                 validated_issues: List[ValidatedIssue],
                                 final_issues: List[ValidatedIssue]) -> Dict[str, Any]:
        """Analyze the complete extraction process"""
        print("\n📊 Analyzing extraction results...")
        
        analysis = {
            'stage5_success': True,
            'original_issues_count': len(original_issues),
            'validated_issues_count': len(validated_issues),
            'final_actionable_count': len(final_issues),
            'filtering_efficiency': 0.0,
            'validation_breakdown': defaultdict(int),
            'average_business_impact': 0.0,
            'recommendations': []
        }
        
        # Count validation results
        for validated in validated_issues:
            analysis['validation_breakdown'][validated.validation_result.value] += 1
        
        # Calculate filtering efficiency
        if original_issues:
            analysis['filtering_efficiency'] = len(final_issues) / len(original_issues)
        
        # Calculate average business impact of final issues
        if final_issues:
            total_impact = sum(issue.business_impact_score for issue in final_issues)
            analysis['average_business_impact'] = total_impact / len(final_issues)
        
        # Generate recommendations
        if len(final_issues) == 0:
            analysis['recommendations'].append("❌ No actionable issues - check validation rules")
            analysis['stage5_success'] = False
        elif len(final_issues) < 3:
            analysis['recommendations'].append("⚠️ Very few actionable issues - validation may be too strict")
        else:
            analysis['recommendations'].append(f"✅ {len(final_issues)} actionable issues identified")
        
        if analysis['average_business_impact'] > 6.0:
            analysis['recommendations'].append("🔥 High average business impact - prioritize these issues")
        elif analysis['average_business_impact'] < 3.0:
            analysis['recommendations'].append("💡 Lower impact issues - consider as nice-to-have improvements")
        
        duplicates_count = analysis['validation_breakdown'].get('duplicate', 0)
        if duplicates_count > 0:
            analysis['recommendations'].append(f"🔍 Removed {duplicates_count} duplicate issues")
        
        # Convert defaultdict for JSON serialization
        analysis['validation_breakdown'] = dict(analysis['validation_breakdown'])
        
        print(f"   Original → Validated → Final: {len(original_issues)} → {len(validated_issues)} → {len(final_issues)}")
        print(f"   Filtering efficiency: {analysis['filtering_efficiency']:.1%}")
        print(f"   Average business impact: {analysis['average_business_impact']:.1f}/10.0")
        print(f"   Validation breakdown:")
        for result_type, count in analysis['validation_breakdown'].items():
            print(f"     • {result_type}: {count}")
        
        print(f"   Recommendations:")
        for rec in analysis['recommendations']:
            print(f"     • {rec}")
        
        return analysis
    
    def save_final_results(self, final_issues: List[ValidatedIssue], analysis: Dict[str, Any]):
        """Save final extraction results"""
        print("\n💾 Saving final extraction results...")
        
        # Save final issues in multiple formats
        
        # 1. Full validated issues with all metadata
        validated_issues_data = []
        for validated in final_issues:
            issue_data = {
                'issue': asdict(validated.original_issue),
                'validation': {
                    'result': validated.validation_result.value,
                    'notes': validated.validation_notes,
                    'business_impact_score': validated.business_impact_score,
                    'action_required': validated.action_required
                }
            }
            # Convert enums to strings
            issue_data['issue']['type'] = validated.original_issue.type.value
            issue_data['issue']['priority'] = validated.original_issue.priority.value
            validated_issues_data.append(issue_data)
        
        with open(self.test_output_dir / "final_validated_issues.json", 'w') as f:
            json.dump(validated_issues_data, f, indent=2)
        
        # 2. Simple issue list for downstream processing
        simple_issues = []
        for validated in final_issues:
            simple_issue = asdict(validated.original_issue)
            simple_issue['type'] = validated.original_issue.type.value
            simple_issue['priority'] = validated.original_issue.priority.value
            simple_issue['business_impact_score'] = validated.business_impact_score
            simple_issues.append(simple_issue)
        
        with open(self.test_output_dir / "final_issues_simple.json", 'w') as f:
            json.dump(simple_issues, f, indent=2)
        
        # 3. Human-readable report
        report_lines = [
            "STAGE 5: ISSUE EXTRACTION RESULTS",
            "=" * 50,
            f"Final Actionable Issues: {len(final_issues)}",
            f"Average Business Impact: {analysis['average_business_impact']:.1f}/10.0",
            f"Filtering Efficiency: {analysis['filtering_efficiency']:.1%}",
            "",
            "TOP PRIORITY ISSUES:",
            "-" * 25,
        ]
        
        for i, validated in enumerate(final_issues[:10], 1):
            issue = validated.original_issue
            report_lines.extend([
                f"{i}. [{issue.priority.value}] {issue.title}",
                f"   Impact: {validated.business_impact_score:.1f}/10 | Files: {len(issue.files_affected)} | Agent: {issue.source_agent}",
                f"   Recommendation: {issue.recommendation[:100]}...",
                ""
            ])
        
        if len(final_issues) > 10:
            report_lines.append(f"... and {len(final_issues) - 10} more issues")
        
        with open(self.test_output_dir / "extraction_report.txt", 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"   Final issues saved to: {self.test_output_dir}/final_validated_issues.json")
        print(f"   Simple format saved to: {self.test_output_dir}/final_issues_simple.json")
        print(f"   Human report saved to: {self.test_output_dir}/extraction_report.txt")
    
    def run_full_stage5_test(self) -> Dict[str, Any]:
        """Run complete Stage 5 testing pipeline"""
        print("=" * 60)
        print("🧪 STAGE 5: ISSUE EXTRACTION WITH VALIDATION")
        print("=" * 60)
        
        # Step 1: Load Stage 4 issues
        original_issues = self.load_stage4_issues()
        
        # Step 2: Test validation rules
        validation_results, validated_issues = self.test_validation_rules(original_issues)
        
        # Step 3: Test duplicate detection
        validated_issues = self.test_duplicate_detection(validated_issues)
        
        # Step 4: Create final issue list
        final_issues = self.create_final_issue_list(validated_issues)
        
        # Step 5: Analyze results
        analysis = self.analyze_extraction_results(original_issues, validated_issues, final_issues)
        
        # Step 6: Save results
        self.save_final_results(final_issues, analysis)
        
        # Create stage summary
        stage5_summary = {
            'stage': 'Issue Extraction with Validation',
            'success': analysis['stage5_success'],
            'original_issues': len(original_issues),
            'final_actionable_issues': len(final_issues),
            'filtering_efficiency': analysis['filtering_efficiency'],
            'average_business_impact': analysis['average_business_impact'],
            'validation_results': validation_results,
            'analysis': analysis,
            'ready_for_stage6': analysis['stage5_success'] and len(final_issues) > 0
        }
        
        with open(self.test_output_dir / "stage5_test_summary.json", 'w') as f:
            json.dump(stage5_summary, f, indent=2)
        
        print(f"\n✅ STAGE 5 COMPLETE:")
        print(f"   Extraction successful: {analysis['stage5_success']}")
        print(f"   Final actionable issues: {len(final_issues)}")
        print(f"   Filtering efficiency: {analysis['filtering_efficiency']:.1%}")
        print(f"   Average business impact: {analysis['average_business_impact']:.1f}/10.0")
        print(f"   Debug outputs saved to: {self.test_output_dir}")
        
        return stage5_summary


def main():
    """Test Stage 5: Issue Extraction with Validation"""
    try:
        validator = IssueValidator()
        results = validator.run_full_stage5_test()
        
        if results['ready_for_stage6']:
            print(f"\n🎉 Stage 5 successful!")
            print(f"Ready to proceed to Stage 6: Filtering and Result Combination")
            print(f"Extracted {results['final_actionable_issues']} actionable issues for final processing")
        else:
            print(f"\n❌ Stage 5 failed - issue extraction not working")
            print(f"Check validation rules and business logic")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Stage 5 testing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
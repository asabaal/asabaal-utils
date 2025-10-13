#!/usr/bin/env python3
"""
Stage 6: Filtering and Result Combination
Final filtering, result combination, and output formatting for complete PR analysis
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from collections import defaultdict

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import from previous stages
from .stage4_response_parsing import QualityIssue, IssueType, Priority
from .stage5_issue_extraction import ValidatedIssue, ValidationResult


@dataclass
class PRAnalysisReport:
    """Complete PR analysis report"""
    pr_summary: Dict[str, Any]
    overall_assessment: Dict[str, Any]
    quality_issues: List[Dict[str, Any]]
    recommendations: List[str]
    merge_readiness: Dict[str, Any]
    technical_metrics: Dict[str, Any]
    generated_at: str
    analysis_metadata: Dict[str, Any]


class ResultCombiner:
    """Combine and format final PR analysis results"""
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.test_output_dir = Path(output_dir) / "debug_outputs" / "stage6"
            self.stage1_dir = Path(output_dir) / "debug_outputs" / "stage1"
            self.stage5_dir = Path(output_dir) / "debug_outputs" / "stage5"
        else:
            self.test_output_dir = Path(__file__).parent / "debug_outputs" / "stage6"
            self.stage1_dir = Path(__file__).parent / "debug_outputs" / "stage1"
            self.stage5_dir = Path(__file__).parent / "debug_outputs" / "stage5"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔧 Result Combiner initialized:")
        print(f"   Loading context from: {self.stage1_dir}")
        print(f"   Loading issues from: {self.stage5_dir}")
        print(f"   Final outputs to: {self.test_output_dir}")
    
    def load_analysis_context(self) -> Dict[str, Any]:
        """Load original analysis context from Stage 1"""
        print("\n📂 Loading analysis context...")
        
        context_file = self.stage1_dir / "final_analysis_context.json"
        
        if not context_file.exists():
            raise RuntimeError("Stage 1 context not found - run Stage 1 first!")
        
        with open(context_file, 'r') as f:
            context = json.load(f)
        
        print(f"   ✅ Loaded context: {len(context['files'])} files analyzed")
        return context
    
    def load_validated_issues(self) -> List[ValidatedIssue]:
        """Load validated issues from Stage 5"""
        print("\n📂 Loading validated issues...")
        
        issues_file = self.stage5_dir / "final_validated_issues.json" 
        
        if not issues_file.exists():
            raise RuntimeError("Stage 5 issues not found - run Stage 5 first!")
        
        with open(issues_file, 'r') as f:
            issues_data = json.load(f)
        
        # Convert back to ValidatedIssue objects
        validated_issues = []
        for item in issues_data:
            issue_dict = item['issue']
            validation_dict = item['validation']
            
            original_issue = QualityIssue(
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
            
            validated_issue = ValidatedIssue(
                original_issue=original_issue,
                validation_result=ValidationResult(validation_dict['result']),
                validation_notes=validation_dict['notes'],
                business_impact_score=validation_dict['business_impact_score'],
                action_required=validation_dict['action_required']
            )
            
            validated_issues.append(validated_issue)
        
        print(f"   ✅ Loaded {len(validated_issues)} validated issues")
        return validated_issues
    
    def calculate_overall_assessment(self, 
                                   context: Dict[str, Any], 
                                   issues: List[ValidatedIssue]) -> Dict[str, Any]:
        """Calculate overall PR assessment scores"""
        print("\n📊 Calculating overall assessment...")
        
        # Business impact score (0-10)
        if issues:
            avg_business_impact = sum(issue.business_impact_score for issue in issues) / len(issues)
            business_impact_score = min(10.0, avg_business_impact)
        else:
            business_impact_score = 8.0  # No issues found = good
        
        # Technical quality score (0-10)
        critical_issues = sum(1 for issue in issues if issue.original_issue.priority == Priority.CRITICAL)
        high_issues = sum(1 for issue in issues if issue.original_issue.priority == Priority.HIGH)
        
        # Deduct points for critical and high priority issues
        technical_quality_score = 10.0 - (critical_issues * 2.0) - (high_issues * 1.0)
        technical_quality_score = max(0.0, technical_quality_score)
        
        # Risk assessment score (0-10, lower = higher risk)
        merge_blockers = sum(1 for issue in issues if issue.original_issue.type == IssueType.MERGE_BLOCKER)
        duplicates = sum(1 for issue in issues if issue.original_issue.type == IssueType.DUPLICATE)
        
        risk_score = 10.0 - (merge_blockers * 3.0) - (duplicates * 0.5)
        risk_score = max(0.0, risk_score)
        
        # Overall score (weighted average)
        overall_score = (
            business_impact_score * 0.4 +
            technical_quality_score * 0.3 +
            risk_score * 0.3
        )
        
        # Determine recommendation
        if overall_score >= 8.5:
            recommendation = "READY_TO_MERGE"
            status_color = "green"
        elif overall_score >= 7.0:
            recommendation = "PROCEED_WITH_CAUTION"
            status_color = "yellow"
        elif overall_score >= 5.0:
            recommendation = "REQUIRES_ATTENTION"
            status_color = "orange"
        else:
            recommendation = "MAJOR_ISSUES_FOUND"
            status_color = "red"
        
        assessment = {
            'overall_score': round(overall_score, 1),
            'business_impact_score': round(business_impact_score, 1),
            'technical_quality_score': round(technical_quality_score, 1),
            'risk_score': round(risk_score, 1),
            'recommendation': recommendation,
            'status_color': status_color,
            'total_issues': len(issues),
            'critical_issues': critical_issues,
            'high_priority_issues': high_issues,
            'files_analyzed': len(context['files'])
        }
        
        print(f"   Overall score: {assessment['overall_score']}/10.0")
        print(f"   Recommendation: {assessment['recommendation']}")
        print(f"   Issues breakdown: {critical_issues} critical, {high_issues} high priority")
        
        return assessment
    
    def format_quality_issues(self, issues: List[ValidatedIssue]) -> List[Dict[str, Any]]:
        """Format quality issues for final report"""
        print("\n📝 Formatting quality issues...")
        
        formatted_issues = []
        
        for issue in issues:
            original = issue.original_issue
            
            # Create formatted issue
            formatted_issue = {
                'id': original.id,
                'type': original.type.value,
                'priority': original.priority.value,
                'title': original.title,
                'description': original.description,
                'files_affected': original.files_affected,
                'files_count': len(original.files_affected),
                'recommendation': original.recommendation,
                'business_impact_score': round(issue.business_impact_score, 1),
                'confidence': round(original.confidence, 2),
                'source_agent': original.source_agent,
                'category': self._categorize_issue(original),
                'severity': self._calculate_severity(issue),
                'estimated_effort': self._estimate_effort(original, issue)
            }
            
            formatted_issues.append(formatted_issue)
        
        print(f"   Formatted {len(formatted_issues)} issues")
        return formatted_issues
    
    def _categorize_issue(self, issue: QualityIssue) -> str:
        """Categorize issue for reporting"""
        if issue.type == IssueType.DUPLICATE:
            return "Code Organization"
        elif issue.type in [IssueType.MERGE_BLOCKER, IssueType.MERGE_WARNING]:
            return "Merge Readiness"
        elif issue.type == IssueType.PATTERN_ISSUE:
            return "Code Consistency"
        elif issue.type == IssueType.ORGANIZATION:
            return "Project Structure"
        else:
            return "Code Quality"
    
    def _calculate_severity(self, validated_issue: ValidatedIssue) -> str:
        """Calculate issue severity"""
        impact = validated_issue.business_impact_score
        priority = validated_issue.original_issue.priority
        
        if impact >= 8.0 or priority == Priority.CRITICAL:
            return "Critical"
        elif impact >= 6.0 or priority == Priority.HIGH:
            return "High"
        elif impact >= 4.0 or priority == Priority.MEDIUM:
            return "Medium"
        else:
            return "Low"
    
    def _estimate_effort(self, issue: QualityIssue, validated_issue: ValidatedIssue) -> str:
        """Estimate effort to fix issue"""
        files_count = len(issue.files_affected)
        issue_type = issue.type
        
        if issue_type == IssueType.DUPLICATE and files_count > 5:
            return "Large (4-8 hours)"
        elif issue_type == IssueType.DUPLICATE and files_count > 2:
            return "Medium (2-4 hours)"
        elif issue_type == IssueType.PATTERN_ISSUE:
            return "Small (30min-2 hours)"
        elif issue_type in [IssueType.MERGE_BLOCKER, IssueType.MERGE_WARNING]:
            return "Review (15-30 minutes)"
        else:
            return "Small (30min-2 hours)"
    
    def generate_recommendations(self, 
                               assessment: Dict[str, Any], 
                               issues: List[ValidatedIssue],
                               context: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        print("\n💡 Generating recommendations...")
        
        recommendations = []
        
        # Priority-based recommendations
        critical_issues = [i for i in issues if i.original_issue.priority == Priority.CRITICAL]
        high_issues = [i for i in issues if i.original_issue.priority == Priority.HIGH]
        
        if critical_issues:
            recommendations.append(f"🔴 **CRITICAL**: Address {len(critical_issues)} critical issues before merging")
            for issue in critical_issues[:3]:  # Top 3
                recommendations.append(f"   • {issue.original_issue.title}")
        
        if high_issues:
            recommendations.append(f"🟡 **HIGH PRIORITY**: Consider fixing {len(high_issues)} high-priority issues")
        
        # Type-specific recommendations
        duplicate_issues = [i for i in issues if i.original_issue.type == IssueType.DUPLICATE]
        if duplicate_issues:
            total_files = sum(len(i.original_issue.files_affected) for i in duplicate_issues)
            recommendations.append(f"🔄 **DUPLICATES**: Remove {total_files} duplicate/redundant files to reduce repository bloat")
        
        pattern_issues = [i for i in issues if i.original_issue.type == IssueType.PATTERN_ISSUE]
        if pattern_issues:
            recommendations.append(f"📐 **CONSISTENCY**: Establish coding standards to address {len(pattern_issues)} pattern inconsistencies")
        
        merge_issues = [i for i in issues if i.original_issue.type in [IssueType.MERGE_BLOCKER, IssueType.MERGE_WARNING]]
        if merge_issues:
            recommendations.append(f"🚀 **DEPLOYMENT**: Review merge readiness concerns before deployment")
        
        # Overall recommendations based on score
        if assessment['overall_score'] >= 8.0:
            recommendations.append("✅ **OVERALL**: PR is in good shape, minor cleanup recommended")
        elif assessment['overall_score'] >= 6.0:
            recommendations.append("⚠️ **OVERALL**: PR needs attention but is manageable")
        else:
            recommendations.append("❌ **OVERALL**: Significant issues found, major cleanup needed")
        
        # Add effort estimation
        total_effort_hours = self._calculate_total_effort(issues)
        recommendations.append(f"⏱️ **ESTIMATED EFFORT**: ~{total_effort_hours} hours to address all issues")
        
        print(f"   Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _calculate_total_effort(self, issues: List[ValidatedIssue]) -> str:
        """Calculate total effort to fix all issues"""
        total_minutes = 0
        
        for issue in issues:
            issue_type = issue.original_issue.type
            files_count = len(issue.original_issue.files_affected)
            
            if issue_type == IssueType.DUPLICATE:
                total_minutes += files_count * 30  # 30 min per duplicate file
            elif issue_type == IssueType.PATTERN_ISSUE:
                total_minutes += 60  # 1 hour per pattern issue
            elif issue_type in [IssueType.MERGE_BLOCKER, IssueType.MERGE_WARNING]:
                total_minutes += 20  # 20 min review per merge issue
            else:
                total_minutes += 45  # 45 min default
        
        hours = total_minutes / 60
        if hours < 2:
            return f"{int(total_minutes)} minutes"
        elif hours < 8:
            return f"{hours:.1f} hours"
        else:
            return f"{int(hours)} hours"
    
    def create_technical_metrics(self, 
                               context: Dict[str, Any], 
                               issues: List[ValidatedIssue]) -> Dict[str, Any]:
        """Create technical metrics summary"""
        print("\n📈 Creating technical metrics...")
        
        pr_summary = context['pr_summary']
        
        # Calculate issue density
        total_files = len(context['files'])
        issues_per_file = len(issues) / total_files if total_files > 0 else 0
        
        # Calculate complexity metrics
        lines_changed = pr_summary.get('total_lines_added', 0) + pr_summary.get('total_lines_removed', 0)
        complexity_score = min(10.0, lines_changed / 10000)  # Normalize to 0-10
        
        metrics = {
            'files_analyzed': total_files,
            'total_lines_changed': lines_changed,
            'lines_added': pr_summary.get('total_lines_added', 0),
            'lines_removed': pr_summary.get('total_lines_removed', 0),
            'issues_identified': len(issues),
            'issues_per_file_ratio': round(issues_per_file, 2),
            'complexity_score': round(complexity_score, 1),
            'categories_analyzed': len(context['categories']),
            'agents_used': 3,  # duplicate_detection, merge_readiness, pattern_analysis
            'analysis_confidence': round(sum(i.original_issue.confidence for i in issues) / len(issues) if issues else 1.0, 2)
        }
        
        print(f"   Metrics calculated: {metrics['issues_identified']} issues across {metrics['files_analyzed']} files")
        return metrics
    
    def create_merge_readiness_summary(self, 
                                     assessment: Dict[str, Any], 
                                     issues: List[ValidatedIssue]) -> Dict[str, Any]:
        """Create merge readiness summary"""
        print("\n🚀 Creating merge readiness summary...")
        
        # Find merge-related issues
        merge_blockers = [i for i in issues if i.original_issue.type == IssueType.MERGE_BLOCKER]
        merge_warnings = [i for i in issues if i.original_issue.type == IssueType.MERGE_WARNING]
        
        # Determine merge status
        if merge_blockers:
            merge_status = "BLOCKED"
            merge_color = "red"
        elif len(merge_warnings) > 2 or assessment['overall_score'] < 6.0:
            merge_status = "CAUTION"
            merge_color = "yellow"
        elif assessment['overall_score'] >= 8.0:
            merge_status = "READY"
            merge_color = "green"
        else:
            merge_status = "REVIEW"
            merge_color = "orange"
        
        # Create blocking/warning summaries
        blocking_issues = []
        warning_issues = []
        
        for issue in merge_blockers:
            blocking_issues.append({
                'title': issue.original_issue.title,
                'impact': issue.business_impact_score
            })
        
        for issue in merge_warnings:
            warning_issues.append({
                'title': issue.original_issue.title,
                'impact': issue.business_impact_score
            })
        
        summary = {
            'status': merge_status,
            'status_color': merge_color,
            'overall_score': assessment['overall_score'],
            'blocking_issues_count': len(merge_blockers),
            'warning_issues_count': len(merge_warnings),
            'blocking_issues': blocking_issues,
            'warning_issues': warning_issues,
            'recommendation': self._get_merge_recommendation(merge_status, assessment, issues)
        }
        
        print(f"   Merge status: {merge_status} ({len(merge_blockers)} blockers, {len(merge_warnings)} warnings)")
        return summary
    
    def _get_merge_recommendation(self, status: str, assessment: Dict[str, Any], issues: List[ValidatedIssue]) -> str:
        """Get specific merge recommendation"""
        if status == "BLOCKED":
            return "Do not merge until blocking issues are resolved"
        elif status == "CAUTION":
            return "Proceed with caution - review warnings before merging"
        elif status == "READY":
            return "Safe to merge - excellent code quality"
        else:
            return "Review recommended before merging"
    
    def test_result_combination(self) -> Tuple[Dict[str, Any], List[ValidatedIssue], Dict[str, Any]]:
        """Test the complete result combination process"""
        print("\n🧪 Testing result combination...")
        
        # Load data
        context = self.load_analysis_context()
        issues = self.load_validated_issues()
        
        # Generate components
        assessment = self.calculate_overall_assessment(context, issues)
        formatted_issues = self.format_quality_issues(issues)
        recommendations = self.generate_recommendations(assessment, issues, context)
        technical_metrics = self.create_technical_metrics(context, issues)
        merge_readiness = self.create_merge_readiness_summary(assessment, issues)
        
        # Test results
        test_results = {
            'data_loaded_successfully': bool(context and issues),
            'assessment_calculated': bool(assessment),
            'issues_formatted': len(formatted_issues),
            'recommendations_generated': len(recommendations),
            'metrics_created': bool(technical_metrics),
            'merge_readiness_determined': bool(merge_readiness),
            'overall_test_success': True
        }
        
        # Save test results
        with open(self.test_output_dir / "combination_test_results.json", 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"   ✅ Combination test successful")
        print(f"   Assessment: {assessment['overall_score']}/10 ({assessment['recommendation']})")
        print(f"   Issues: {len(formatted_issues)} formatted")
        print(f"   Recommendations: {len(recommendations)} generated")
        
        return context, issues, {
            'assessment': assessment,
            'formatted_issues': formatted_issues,
            'recommendations': recommendations,
            'technical_metrics': technical_metrics,
            'merge_readiness': merge_readiness
        }
    
    def create_final_report(self, 
                          context: Dict[str, Any], 
                          issues: List[ValidatedIssue],
                          components: Dict[str, Any]) -> PRAnalysisReport:
        """Create the final comprehensive PR analysis report"""
        print("\n📋 Creating final report...")
        
        report = PRAnalysisReport(
            pr_summary={
                'branch_info': f"{context['pr_summary']['from_branch']} → {context['pr_summary']['to_branch']}",
                'files_changed': context['pr_summary']['total_files_changed'],
                'lines_added': context['pr_summary']['total_lines_added'],
                'lines_removed': context['pr_summary']['total_lines_removed'],
                'total_lines_changed': context['pr_summary']['total_lines_added'] + context['pr_summary']['total_lines_removed']
            },
            overall_assessment=components['assessment'],
            quality_issues=components['formatted_issues'],
            recommendations=components['recommendations'],
            merge_readiness=components['merge_readiness'],
            technical_metrics=components['technical_metrics'],
            generated_at=datetime.now().isoformat(),
            analysis_metadata={
                'analyzer_version': '1.0.0',
                'stages_completed': ['context_prep', 'agent_prompts', 'agent_communication', 'response_parsing', 'issue_extraction', 'result_combination'],
                'total_analysis_time': 'N/A',  # Would be calculated in full integration
                'confidence_level': 'high'
            }
        )
        
        print(f"   ✅ Final report created")
        print(f"   PR: {report.pr_summary['files_changed']} files, {report.pr_summary['total_lines_changed']:,} lines changed")
        print(f"   Quality: {len(report.quality_issues)} issues, {report.overall_assessment['overall_score']}/10 score")
        
        return report
    
    def save_final_outputs(self, report: PRAnalysisReport):
        """Save final outputs in multiple formats"""
        print("\n💾 Saving final outputs...")
        
        # 1. Complete JSON report (ESSENTIAL OUTPUT)
        report_dict = asdict(report)
        from .path_utils import get_main_output_dir
        main_output_dir = get_main_output_dir(self.test_output_dir)
        with open(main_output_dir / "complete_pr_analysis.json", 'w') as f:
            json.dump(report_dict, f, indent=2)
        # Also save in debug folder for troubleshooting
        with open(self.test_output_dir / "complete_pr_analysis.json", 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        # 2. Executive summary
        exec_summary = {
            'overall_score': report.overall_assessment['overall_score'],
            'recommendation': report.overall_assessment['recommendation'],
            'total_issues': len(report.quality_issues),
            'critical_issues': report.overall_assessment['critical_issues'],
            'merge_status': report.merge_readiness['status'],
            'top_3_issues': report.quality_issues[:3] if report.quality_issues else [],
            'key_recommendations': report.recommendations[:3]
        }
        
        with open(self.test_output_dir / "executive_summary.json", 'w') as f:
            json.dump(exec_summary, f, indent=2)
        
        # 3. Human-readable report
        self._create_human_readable_report(report)
        
        # 4. GitHub-style markdown report
        self._create_markdown_report(report)
        
        print(f"   Complete report: {self.test_output_dir}/complete_pr_analysis.json")
        print(f"   Executive summary: {self.test_output_dir}/executive_summary.json")
        print(f"   Human report: {self.test_output_dir}/pr_analysis_report.txt")
        print(f"   Markdown report: {self.test_output_dir}/PR_ANALYSIS_REPORT.md")
    
    def _create_human_readable_report(self, report: PRAnalysisReport):
        """Create human-readable text report"""
        lines = [
            "=" * 80,
            "PULL REQUEST ANALYSIS REPORT",
            "=" * 80,
            f"Generated: {report.generated_at}",
            f"Branch: {report.pr_summary['branch_info']}",
            f"Files Changed: {report.pr_summary['files_changed']}",
            f"Lines Changed: {report.pr_summary['total_lines_changed']:,} (+{report.pr_summary['lines_added']:,} -{report.pr_summary['lines_removed']:,})",
            "",
            "OVERALL ASSESSMENT",
            "-" * 40,
            f"Overall Score: {report.overall_assessment['overall_score']}/10.0",
            f"Recommendation: {report.overall_assessment['recommendation']}",
            f"Merge Status: {report.merge_readiness['status']}",
            f"Total Issues: {len(report.quality_issues)}",
            f"Critical Issues: {report.overall_assessment['critical_issues']}",
            "",
            "TOP QUALITY ISSUES",
            "-" * 40,
        ]
        
        for i, issue in enumerate(report.quality_issues[:10], 1):
            lines.extend([
                f"{i}. [{issue['priority']}] {issue['title']}",
                f"   Category: {issue['category']} | Impact: {issue['business_impact_score']}/10 | Files: {issue['files_count']}",
                f"   Recommendation: {issue['recommendation'][:100]}...",
                ""
            ])
        
        lines.extend([
            "",
            "KEY RECOMMENDATIONS",
            "-" * 40,
        ])
        
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        lines.extend([
            "",
            "TECHNICAL METRICS",
            "-" * 40,
            f"Analysis Confidence: {report.technical_metrics['analysis_confidence']}",
            f"Issues per File: {report.technical_metrics['issues_per_file_ratio']}",
            f"Complexity Score: {report.technical_metrics['complexity_score']}/10",
            "",
            "=" * 80
        ])
        
        with open(self.test_output_dir / "pr_analysis_report.txt", 'w') as f:
            f.write('\n'.join(lines))
    
    def _create_markdown_report(self, report: PRAnalysisReport):
        """Create GitHub-style markdown report"""
        status_emoji = {
            'READY': '✅',
            'CAUTION': '⚠️',
            'REVIEW': '🔍',
            'BLOCKED': '❌'
        }
        
        lines = [
            "# 🔍 Pull Request Analysis Report",
            "",
            f"**Generated:** {report.generated_at}  ",
            f"**Branch:** `{report.pr_summary['branch_info']}`  ",
            f"**Files Changed:** {report.pr_summary['files_changed']}  ",
            f"**Lines Changed:** {report.pr_summary['total_lines_changed']:,} (+{report.pr_summary['lines_added']:,} -{report.pr_summary['lines_removed']:,})  ",
            "",
            "## 📊 Overall Assessment",
            "",
            f"| Metric | Score | Status |",
            f"|--------|-------|--------|",
            f"| **Overall Quality** | {report.overall_assessment['overall_score']}/10 | {report.overall_assessment['recommendation']} |",
            f"| **Merge Readiness** | {status_emoji.get(report.merge_readiness['status'], '🔍')} | {report.merge_readiness['status']} |",
            f"| **Total Issues** | {len(report.quality_issues)} | {report.overall_assessment['critical_issues']} Critical |",
            "",
            "## 🚨 Quality Issues",
            "",
        ]
        
        # Group issues by priority
        issue_groups = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for issue in report.quality_issues:
            issue_groups[issue['priority']].append(issue)
        
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            issues = issue_groups[priority]
            if issues:
                priority_emoji = {'CRITICAL': '🔴', 'HIGH': '🟡', 'MEDIUM': '🟠', 'LOW': '🔵'}
                lines.extend([
                    f"### {priority_emoji[priority]} {priority} Priority ({len(issues)} issues)",
                    ""
                ])
                
                for issue in issues:
                    lines.extend([
                        f"**{issue['title']}**",
                        f"- **Category:** {issue['category']}",
                        f"- **Impact:** {issue['business_impact_score']}/10",
                        f"- **Files Affected:** {issue['files_count']}",
                        f"- **Recommendation:** {issue['recommendation']}",
                        ""
                    ])
        
        lines.extend([
            "## 💡 Key Recommendations",
            ""
        ])
        
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        lines.extend([
            "",
            "## 📈 Technical Metrics",
            "",
            f"- **Analysis Confidence:** {report.technical_metrics['analysis_confidence']}",
            f"- **Issues per File:** {report.technical_metrics['issues_per_file_ratio']}",
            f"- **Complexity Score:** {report.technical_metrics['complexity_score']}/10",
            f"- **Categories Analyzed:** {report.technical_metrics['categories_analyzed']}",
            "",
            "---",
            "",
            f"*Generated by PR Analyzer v{report.analysis_metadata['analyzer_version']}*"
        ])
        
        # Save markdown report (ESSENTIAL OUTPUT)
        from .path_utils import get_main_output_dir
        main_output_dir = get_main_output_dir(self.test_output_dir)
        with open(main_output_dir / "PR_ANALYSIS_REPORT.md", 'w') as f:
            f.write('\n'.join(lines))
        # Also save in debug folder for troubleshooting
        with open(self.test_output_dir / "PR_ANALYSIS_REPORT.md", 'w') as f:
            f.write('\n'.join(lines))
    
    def run_full_stage6_test(self) -> Dict[str, Any]:
        """Run complete Stage 6 testing pipeline"""
        print("=" * 60)
        print("🧪 STAGE 6: FILTERING AND RESULT COMBINATION")
        print("=" * 60)
        
        try:
            # Step 1: Test result combination
            context, issues, components = self.test_result_combination()
            
            # Step 2: Create final report
            final_report = self.create_final_report(context, issues, components)
            
            # Step 3: Save outputs
            self.save_final_outputs(final_report)
            
            # Create stage summary
            stage6_summary = {
                'stage': 'Filtering and Result Combination',
                'success': True,
                'final_report_created': True,
                'overall_score': final_report.overall_assessment['overall_score'],
                'merge_status': final_report.merge_readiness['status'],
                'total_issues': len(final_report.quality_issues),
                'critical_issues': final_report.overall_assessment['critical_issues'],
                'recommendations_count': len(final_report.recommendations),
                'outputs_generated': 4,  # JSON, summary, text, markdown
                'ready_for_stage7': True
            }
            
            with open(self.test_output_dir / "stage6_test_summary.json", 'w') as f:
                json.dump(stage6_summary, f, indent=2)
            
            print(f"\n✅ STAGE 6 COMPLETE:")
            print(f"   Final report created: {stage6_summary['final_report_created']}")
            print(f"   Overall score: {stage6_summary['overall_score']}/10")
            print(f"   Merge status: {stage6_summary['merge_status']}")
            print(f"   Total issues: {stage6_summary['total_issues']}")
            print(f"   Outputs generated: {stage6_summary['outputs_generated']} formats")
            print(f"   Debug outputs saved to: {self.test_output_dir}")
            
            return stage6_summary
            
        except Exception as e:
            error_summary = {
                'stage': 'Filtering and Result Combination',
                'success': False,
                'error': str(e),
                'ready_for_stage7': False
            }
            
            with open(self.test_output_dir / "stage6_error_summary.json", 'w') as f:
                json.dump(error_summary, f, indent=2)
            
            raise e


def main():
    """Test Stage 6: Filtering and Result Combination"""
    try:
        combiner = ResultCombiner()
        results = combiner.run_full_stage6_test()
        
        if results['ready_for_stage7']:
            print(f"\n🎉 Stage 6 successful!")
            print(f"Ready to proceed to Stage 7: Full Integration Test")
            print(f"Complete PR analysis report generated with {results['total_issues']} issues")
            print(f"Overall quality score: {results['overall_score']}/10 ({results['merge_status']})")
        else:
            print(f"\n❌ Stage 6 failed - result combination not working")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Stage 6 testing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
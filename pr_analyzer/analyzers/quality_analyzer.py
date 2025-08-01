"""
Quality Analysis Module

Detects duplicate files, incomplete implementations, inconsistent patterns,
and other quality issues that indicate a PR may not be ready for merge.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class QualityIssue:
    """Represents a quality issue found in the PR."""
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    category: str  # 'DUPLICATE', 'INCOMPLETE', 'INCONSISTENT', 'ABANDONED'
    title: str
    description: str
    affected_files: List[str]
    recommendation: str


@dataclass
class DuplicateGroup:
    """Group of files that appear to be duplicates or variations."""
    similarity_score: float
    files: List[str]
    duplicate_type: str  # 'EXACT', 'PARTIAL', 'TEMPLATE_VARIATION'
    common_patterns: List[str]


class QualityAnalyzer:
    """Analyzes PR quality and detects potential issues."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize quality analyzer with configuration."""
        self.config = config
        self.similarity_threshold = 0.7  # Files with >70% similarity flagged as duplicates
        self.partial_threshold = 0.4     # Files with >40% similarity flagged as partials
        
    def analyze_pr_quality(self, pr_analysis, classified_files, repo_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive quality analysis of the PR.
        
        Returns:
            Dictionary containing quality analysis results
        """
        issues = []
        
        # 1. Detect duplicate and similar files
        duplicate_issues = self._detect_duplicates(classified_files, repo_path)
        issues.extend(duplicate_issues)
        
        # 2. Detect incomplete implementations
        incomplete_issues = self._detect_incomplete_implementations(classified_files, repo_path)
        issues.extend(incomplete_issues)
        
        # 3. Detect inconsistent patterns
        inconsistent_issues = self._detect_inconsistent_patterns(classified_files, repo_path)
        issues.extend(inconsistent_issues)
        
        # 4. Detect abandoned experiments
        abandoned_issues = self._detect_abandoned_experiments(classified_files, pr_analysis)
        issues.extend(abandoned_issues)
        
        # 5. Check for mixed concerns
        mixed_concern_issues = self._detect_mixed_concerns(classified_files, pr_analysis)
        issues.extend(mixed_concern_issues)
        
        # Calculate merge readiness score
        merge_readiness = self._calculate_merge_readiness(issues)
        
        return {
            'issues': issues,
            'merge_readiness': merge_readiness,
            'quality_score': self._calculate_quality_score(issues),
            'recommendations': self._generate_quality_recommendations(issues),
            'issue_summary': self._summarize_issues(issues)
        }
    
    def _detect_duplicates(self, classified_files, repo_path: str) -> List[QualityIssue]:
        """Detect duplicate and similar files."""
        issues = []
        
        # Group files by category for targeted duplicate detection
        category_groups = {}
        for file in classified_files:
            category = file.category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(file)
        
        # Check each category for duplicates
        for category, files in category_groups.items():
            if len(files) < 2:
                continue
                
            duplicate_groups = self._find_duplicate_groups(files, repo_path)
            
            for group in duplicate_groups:
                if group.similarity_score > self.similarity_threshold:
                    severity = 'CRITICAL' if group.duplicate_type == 'EXACT' else 'HIGH'
                    issues.append(QualityIssue(
                        severity=severity,
                        category='DUPLICATE',
                        title=f'Duplicate {category.lower()} files detected',
                        description=f'Found {len(group.files)} files with {group.similarity_score:.1%} similarity',
                        affected_files=group.files,
                        recommendation=f'Consolidate duplicate files or remove unnecessary copies. Consider using a single source of truth.'
                    ))
                elif group.similarity_score > self.partial_threshold:
                    issues.append(QualityIssue(
                        severity='MEDIUM',
                        category='DUPLICATE',
                        title=f'Partially similar {category.lower()} files',
                        description=f'Found files with {group.similarity_score:.1%} similarity - may indicate incomplete refactoring',
                        affected_files=group.files,
                        recommendation='Review files for common code that could be extracted or consolidated.'
                    ))
        
        return issues
    
    def _find_duplicate_groups(self, files: List, repo_path: str) -> List[DuplicateGroup]:
        """Find groups of duplicate or similar files."""
        groups = []
        processed = set()
        
        for i, file1 in enumerate(files):
            if file1.file_path in processed:
                continue
                
            similar_files = [file1.file_path]
            
            for j, file2 in enumerate(files[i+1:], i+1):
                if file2.file_path in processed:
                    continue
                    
                similarity = self._calculate_file_similarity(
                    file1.file_path, file2.file_path, repo_path
                )
                
                if similarity > self.partial_threshold:
                    similar_files.append(file2.file_path)
                    processed.add(file2.file_path)
            
            if len(similar_files) > 1:
                # Calculate average similarity for the group
                avg_similarity = self._calculate_group_similarity(similar_files, repo_path)
                
                duplicate_type = 'EXACT' if avg_similarity > 0.95 else 'PARTIAL'
                
                groups.append(DuplicateGroup(
                    similarity_score=avg_similarity,
                    files=similar_files,
                    duplicate_type=duplicate_type,
                    common_patterns=self._extract_common_patterns(similar_files, repo_path)
                ))
                
                for file_path in similar_files:
                    processed.add(file_path)
        
        return groups
    
    def _calculate_file_similarity(self, file1: str, file2: str, repo_path: str) -> float:
        """Calculate similarity between two files."""
        try:
            path1 = Path(repo_path) / file1
            path2 = Path(repo_path) / file2
            
            # Check if files exist
            if not path1.exists() or not path2.exists():
                return 0.0
            
            # Skip large files for performance (>100KB)
            if path1.stat().st_size > 100000 or path2.stat().st_size > 100000:
                return 0.0
            
            # Read file contents
            with open(path1, 'r', encoding='utf-8', errors='ignore') as f:
                content1 = f.read()
            with open(path2, 'r', encoding='utf-8', errors='ignore') as f:
                content2 = f.read()
            
            # Skip very large content comparisons
            if len(content1) > 50000 or len(content2) > 50000:
                return 0.0
            
            # Quick filename similarity check first
            filename_similarity = SequenceMatcher(
                None, Path(file1).name, Path(file2).name
            ).ratio()
            
            # Only do expensive content comparison if filenames are somewhat similar
            if filename_similarity < 0.3:
                return filename_similarity * 0.2
            
            # Calculate similarity using SequenceMatcher
            similarity = SequenceMatcher(None, content1, content2).ratio()
            
            # Weight content similarity higher than filename similarity
            return (similarity * 0.8) + (filename_similarity * 0.2)
            
        except Exception:
            return 0.0
    
    def _calculate_group_similarity(self, files: List[str], repo_path: str) -> float:
        """Calculate average similarity within a group of files."""
        if len(files) < 2:
            return 0.0
        
        similarities = []
        for i in range(len(files)):
            for j in range(i+1, len(files)):
                sim = self._calculate_file_similarity(files[i], files[j], repo_path)
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _extract_common_patterns(self, files: List[str], repo_path: str) -> List[str]:
        """Extract common patterns from a group of similar files."""
        patterns = []
        
        # Check for common file naming patterns
        filenames = [Path(f).name for f in files]
        
        # Find common prefixes/suffixes
        if len(filenames) > 1:
            # Common prefix
            prefix = os.path.commonprefix(filenames)
            if len(prefix) > 3:
                patterns.append(f'Common prefix: {prefix}')
            
            # Common suffix (excluding extension)
            stems = [Path(f).stem for f in filenames]
            reversed_stems = [s[::-1] for s in stems]
            suffix = os.path.commonprefix(reversed_stems)[::-1]
            if len(suffix) > 3:
                patterns.append(f'Common suffix: {suffix}')
        
        # Check for common directory structures
        dirs = [str(Path(f).parent) for f in files]
        if len(set(dirs)) == 1 and dirs[0] != '.':
            patterns.append(f'Same directory: {dirs[0]}')
        
        return patterns
    
    def _detect_incomplete_implementations(self, classified_files, repo_path: str) -> List[QualityIssue]:
        """Detect incomplete implementations and TODO markers."""
        issues = []
        
        todo_files = []
        placeholder_files = []
        
        for file in classified_files:
            try:
                file_path = Path(repo_path) / file.file_path
                if not file_path.exists():
                    continue
                    
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                
                # Check for TODO markers
                todo_patterns = [
                    r'todo\b', r'fixme\b', r'hack\b', r'temp\b', r'temporary\b',
                    r'placeholder\b', r'coming soon\b', r'not implemented\b'
                ]
                
                todo_matches = []
                for pattern in todo_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    todo_matches.extend(matches)
                
                if todo_matches:
                    todo_files.append((file.file_path, len(todo_matches)))
                
                # Check for placeholder content
                placeholder_patterns = [
                    r'lorem ipsum', r'placeholder', r'example\.com',
                    r'your-.*-here', r'replace.*with', r'update.*this'
                ]
                
                for pattern in placeholder_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        placeholder_files.append(file.file_path)
                        break
                        
            except Exception:
                continue
        
        # Report TODO issues
        if todo_files:
            high_todo_files = [f for f, count in todo_files if count > 5]
            if high_todo_files:
                issues.append(QualityIssue(
                    severity='HIGH',
                    category='INCOMPLETE',
                    title='Multiple TODO markers found',
                    description=f'Found {len(high_todo_files)} files with many TODO/FIXME markers',
                    affected_files=high_todo_files,
                    recommendation='Complete pending tasks or remove TODO markers before merging.'
                ))
            elif len(todo_files) > 10:
                issues.append(QualityIssue(
                    severity='MEDIUM',
                    category='INCOMPLETE',
                    title='Many files with TODO markers',
                    description=f'Found TODO markers in {len(todo_files)} files',
                    affected_files=[f for f, _ in todo_files],
                    recommendation='Review and address TODO items before merging.'
                ))
        
        # Report placeholder content
        if placeholder_files:
            issues.append(QualityIssue(
                severity='HIGH',
                category='INCOMPLETE',
                title='Placeholder content detected',
                description=f'Found placeholder content in {len(placeholder_files)} files',
                affected_files=placeholder_files,
                recommendation='Replace placeholder content with actual implementation.'
            ))
        
        return issues
    
    def _detect_inconsistent_patterns(self, classified_files, repo_path: str) -> List[QualityIssue]:
        """Detect inconsistent naming patterns and structures."""
        issues = []
        
        # Check for inconsistent naming patterns within categories
        category_files = {}
        for file in classified_files:
            category = file.category
            if category not in category_files:
                category_files[category] = []
            category_files[category].append(file.file_path)
        
        for category, files in category_files.items():
            if len(files) < 3:  # Need at least 3 files to detect patterns
                continue
            
            # Check naming consistency
            filenames = [Path(f).name for f in files]
            
            # Check for mixed naming conventions
            kebab_case = sum(1 for f in filenames if '-' in f and '_' not in f)
            snake_case = sum(1 for f in filenames if '_' in f and '-' not in f)
            camel_case = sum(1 for f in filenames if any(c.isupper() for c in f) and '-' not in f and '_' not in f)
            
            total_files = len(filenames)
            if kebab_case > 0 and snake_case > 0 and (kebab_case + snake_case) > total_files * 0.5:
                issues.append(QualityIssue(
                    severity='MEDIUM',
                    category='INCONSISTENT',
                    title=f'Mixed naming conventions in {category.lower()} files',
                    description=f'Found both kebab-case ({kebab_case}) and snake_case ({snake_case}) naming',
                    affected_files=files,
                    recommendation='Standardize on a single naming convention for consistency.'
                ))
        
        return issues
    
    def _detect_abandoned_experiments(self, classified_files, pr_analysis) -> List[QualityIssue]:
        """Detect abandoned experiments and unused files."""
        issues = []
        
        # Look for files that were added then deleted
        added_files = set()
        deleted_files = set()
        
        for file_change in pr_analysis.file_changes:
            if file_change.change_type == 'A':
                added_files.add(file_change.file_path)
            elif file_change.change_type == 'D':
                deleted_files.add(file_change.file_path)
        
        # Find files with similar names that were added/deleted (potential renaming experiments)
        potential_experiments = []
        for added_file in added_files:
            for deleted_file in deleted_files:
                similarity = SequenceMatcher(None, added_file, deleted_file).ratio()
                if similarity > 0.6:  # High similarity suggests renaming experiment
                    potential_experiments.append((added_file, deleted_file, similarity))
        
        if potential_experiments:
            issues.append(QualityIssue(
                severity='MEDIUM',
                category='ABANDONED',
                title='Potential abandoned renaming experiments',
                description=f'Found {len(potential_experiments)} pairs of similar added/deleted files',
                affected_files=[f[0] for f in potential_experiments] + [f[1] for f in potential_experiments],
                recommendation='Clean up abandoned experiments or clarify intentional file restructuring.'
            ))
        
        return issues
    
    def _detect_mixed_concerns(self, classified_files, pr_analysis) -> List[QualityIssue]:
        """Detect PRs that mix multiple unrelated concerns."""
        issues = []
        
        # Count files in each category
        category_counts = {}
        for file in classified_files:
            category = file.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Identify high-impact categories
        high_impact_categories = [
            'CORE_BUSINESS_LOGIC', 'DATABASE', 'API_INTEGRATION', 'USER_INTERFACE'
        ]
        
        affected_high_impact = sum(1 for cat in high_impact_categories if category_counts.get(cat, 0) > 0)
        
        # Flag PRs that touch too many high-impact areas
        if affected_high_impact >= 3:
            total_high_impact_files = sum(category_counts.get(cat, 0) for cat in high_impact_categories)
            if total_high_impact_files > 20:
                issues.append(QualityIssue(
                    severity='HIGH',
                    category='MIXED_CONCERNS',
                    title='PR touches multiple high-impact areas',
                    description=f'Changes affect {affected_high_impact} critical system areas with {total_high_impact_files} files',
                    affected_files=[f.file_path for f in classified_files if f.category in high_impact_categories],
                    recommendation='Consider breaking this PR into smaller, focused changes for easier review and safer deployment.'
                ))
        
        return issues
    
    def _calculate_merge_readiness(self, issues: List[QualityIssue]) -> Dict[str, Any]:
        """Calculate overall merge readiness based on issues."""
        critical_issues = [i for i in issues if i.severity == 'CRITICAL']
        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']
        
        # Calculate readiness score (0-100)
        penalty = 0
        penalty += len(critical_issues) * 40  # Critical issues heavily penalize
        penalty += len(high_issues) * 20      # High issues moderately penalize
        penalty += len(medium_issues) * 5     # Medium issues lightly penalize
        
        readiness_score = max(0, 100 - penalty)
        
        # Determine readiness status
        if critical_issues:
            status = 'NOT_READY'
            recommendation = 'Critical issues must be resolved before merge'
        elif readiness_score < 60:
            status = 'NEEDS_WORK'
            recommendation = 'Address high-priority issues before merge'
        elif readiness_score < 80:
            status = 'REVIEW_NEEDED'
            recommendation = 'Consider addressing issues for better code quality'
        else:
            status = 'READY'
            recommendation = 'PR appears ready for merge'
        
        return {
            'score': readiness_score,
            'status': status,
            'recommendation': recommendation,
            'blocking_issues': len(critical_issues),
            'warning_issues': len(high_issues),
            'info_issues': len(medium_issues)
        }
    
    def _calculate_quality_score(self, issues: List[QualityIssue]) -> float:
        """Calculate overall quality score."""
        if not issues:
            return 10.0
        
        penalty = 0
        for issue in issues:
            if issue.severity == 'CRITICAL':
                penalty += 3.0
            elif issue.severity == 'HIGH':
                penalty += 2.0
            elif issue.severity == 'MEDIUM':
                penalty += 1.0
            else:
                penalty += 0.5
        
        return max(0.0, 10.0 - penalty)
    
    def _generate_quality_recommendations(self, issues: List[QualityIssue]) -> List[str]:
        """Generate actionable recommendations based on issues."""
        recommendations = []
        
        # Group issues by category
        issue_categories = {}
        for issue in issues:
            category = issue.category
            if category not in issue_categories:
                issue_categories[category] = []
            issue_categories[category].append(issue)
        
        # Generate category-specific recommendations
        if 'DUPLICATE' in issue_categories:
            recommendations.append('🔍 Review duplicate files and consolidate similar implementations')
        
        if 'INCOMPLETE' in issue_categories:
            recommendations.append('✅ Complete TODO items and replace placeholder content')
        
        if 'INCONSISTENT' in issue_categories:
            recommendations.append('📏 Standardize naming conventions and code patterns')
        
        if 'ABANDONED' in issue_categories:
            recommendations.append('🧹 Clean up abandoned experiments and unused files')
        
        if 'MIXED_CONCERNS' in issue_categories:
            recommendations.append('🎯 Consider splitting large PRs into focused, single-purpose changes')
        
        return recommendations
    
    def _summarize_issues(self, issues: List[QualityIssue]) -> Dict[str, Any]:
        """Summarize issues for display."""
        summary = {
            'total_issues': len(issues),
            'by_severity': {},
            'by_category': {},
            'most_common_category': None,
            'most_severe_issue': None
        }
        
        # Count by severity
        for issue in issues:
            severity = issue.severity
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
        
        # Count by category
        for issue in issues:
            category = issue.category
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
        
        # Find most common category
        if summary['by_category']:
            summary['most_common_category'] = max(summary['by_category'], key=summary['by_category'].get)
        
        # Find most severe issue
        severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        if issues:
            summary['most_severe_issue'] = max(issues, key=lambda x: severity_order.get(x.severity, 0))
        
        return summary
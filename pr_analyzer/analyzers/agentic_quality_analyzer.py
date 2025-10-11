"""
Agentic Quality Analysis Module

Uses AI agents to intelligently analyze PR quality, detect duplicates,
and assess merge readiness through intelligent reasoning rather than algorithms.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass

# Import OpenRouter client
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from analyzers.openrouter_client import OpenRouterClient
    OPENROUTER_AVAILABLE = True
except ImportError:
    try:
        # Fallback for direct execution
        from openrouter_client import OpenRouterClient
        OPENROUTER_AVAILABLE = True
    except ImportError:
        OpenRouterClient = None
        OPENROUTER_AVAILABLE = False

# Import json for response parsing
import json


@dataclass
class QualityIssue:
    """Represents a quality issue found by the AI agent."""
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    category: str  # 'DUPLICATE', 'INCOMPLETE', 'INCONSISTENT', 'ABANDONED'
    title: str
    description: str
    affected_files: List[str]
    recommendation: str
    agent_reasoning: str  # The agent's reasoning for this issue


class AgenticQualityAnalyzer:
    """Uses AI agents to analyze PR quality and detect issues."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize agentic quality analyzer."""
        self.config = config
        
        # Initialize agentic backend
        self.agentic_backend = config.get('agentic_backend', {})
        self.provider = self.agentic_backend.get('provider', 'openrouter')
        self.model = self.agentic_backend.get('model') or os.getenv('OPENROUTER_MODEL', 'qwen/qwen-2.5-coder-32b-instruct')
        
        # Initialize appropriate client
        if self.provider == 'openrouter' and OpenRouterClient:
            try:
                self.openrouter_client = OpenRouterClient(model=self.model)
                print(f"🤖 Using OpenRouter with model: {self.model}")
            except Exception as e:
                print(f"⚠️  Failed to initialize OpenRouter client: {e}")
                self.openrouter_client = None
        else:
            # Fallback to Claude CLI
            self.oauth_token = os.getenv('CLAUDE_CODE_OAUTH_TOKEN')
            if not self.oauth_token:
                print("⚠️  CLAUDE_CODE_OAUTH_TOKEN not set - agentic analysis will use fallback")
            self.openrouter_client = None
        
        self.load_exceptions()
        
    def analyze_pr_quality(self, pr_analysis, classified_files, repo_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive quality analysis using AI agents.
        
        Returns:
            Dictionary containing quality analysis results
        """
        print("🤖 Launching AI agents for quality analysis...")
        
        # Prepare data for the agents
        analysis_context = self._prepare_analysis_context(pr_analysis, classified_files, repo_path)
        
        # Launch specialized agents for different types of analysis
        duplicate_analysis = self._launch_duplicate_detection_agent(analysis_context, repo_path)
        merge_readiness_analysis = self._launch_merge_readiness_agent(analysis_context, repo_path)
        pattern_analysis = self._launch_pattern_analysis_agent(analysis_context, repo_path)
        
        # Combine results from all agents
        all_issues = []
        all_issues.extend(duplicate_analysis.get('issues', []))
        all_issues.extend(merge_readiness_analysis.get('issues', []))
        all_issues.extend(pattern_analysis.get('issues', []))
        
        # Filter out suppressed issues based on user exceptions
        all_issues = self.filter_suppressed_issues(all_issues)
        
        # Calculate overall metrics
        merge_readiness = self._calculate_merge_readiness(all_issues, merge_readiness_analysis)
        quality_score = self._calculate_quality_score(all_issues)
        
        return {
            'issues': all_issues,
            'merge_readiness': merge_readiness,
            'quality_score': quality_score,
            'recommendations': self._extract_recommendations(all_issues),
            'issue_summary': self._summarize_issues(all_issues),
            'agent_insights': {
                'duplicate_analysis': duplicate_analysis,
                'merge_readiness_analysis': merge_readiness_analysis,
                'pattern_analysis': pattern_analysis
            }
        }
    
    def _prepare_analysis_context(self, pr_analysis, classified_files, repo_path: str) -> Dict[str, Any]:
        """Prepare context data for AI agents."""
        
        # Collect file information with content samples
        file_info = []
        for classified_file in classified_files:
            file_path = Path(repo_path) / classified_file.file_path
            
            # Get file change info
            file_change = None
            for fc in pr_analysis.file_changes:
                if fc.file_path == classified_file.file_path:
                    file_change = fc
                    break
            
            file_data = {
                'path': classified_file.file_path,
                'category': classified_file.category,
                'importance': classified_file.importance,
                'icon': classified_file.icon,
                'description': classified_file.description,
                'change_type': file_change.change_type if file_change else 'UNKNOWN',
                'lines_added': file_change.lines_added if file_change else 0,
                'lines_removed': file_change.lines_removed if file_change else 0,
                'exists': file_path.exists(),
                'size': file_path.stat().st_size if file_path.exists() else 0
            }
            
            # Add content sample for small files
            if file_path.exists() and file_path.stat().st_size < 50000:  # < 50KB
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Clean content to avoid null bytes that break subprocess
                        clean_content = content.replace('\x00', '').replace('\r\n', '\n')
                        # Include first 1000 chars as sample
                        file_data['content_sample'] = clean_content[:1000] if len(clean_content) > 1000 else clean_content
                        file_data['total_lines'] = len(content.split('\n'))
                except Exception:
                    file_data['content_sample'] = '[Error reading file]'
                    file_data['total_lines'] = 0
            else:
                file_data['content_sample'] = '[File too large or missing]'
                file_data['total_lines'] = 0
            
            file_info.append(file_data)
        
        return {
            'pr_summary': {
                'from_branch': pr_analysis.from_branch,
                'to_branch': pr_analysis.to_branch,
                'total_files_changed': pr_analysis.total_files_changed,
                'total_lines_added': pr_analysis.total_lines_added,
                'total_lines_removed': pr_analysis.total_lines_removed,
                'commit_messages': pr_analysis.commit_messages[:10]  # First 10 commits
            },
            'files': file_info,
            'categories': self._group_files_by_category(file_info),
            'repo_path': repo_path
        }
    
    def _group_files_by_category(self, file_info: List[Dict]) -> Dict[str, List[Dict]]:
        """Group files by category for easier agent analysis."""
        categories = {}
        for file_data in file_info:
            category = file_data['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(file_data)
        return categories
    
    def _launch_duplicate_detection_agent(self, context: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Launch AI agent to detect duplicate and similar files using Task tool."""
        
        # Prepare detailed file information for the agent
        files_for_analysis = self._prepare_files_for_content_analysis(context, repo_path)
        
        agent_prompt = f"""
You are a senior software architect with expertise in detecting duplicate implementations by analyzing actual code content and functional purpose. Your task is to DISCOVER duplicate or similar files by reading and understanding what each file actually does.

## PR Context
- Analyzing: {context['pr_summary']['total_files_changed']} files (+{context['pr_summary']['total_lines_added']}/-{context['pr_summary']['total_lines_removed']})
- Branch: {context['pr_summary']['from_branch']} → {context['pr_summary']['to_branch']}

## File Content & Functional Analysis
{files_for_analysis}

## DISCOVERY OBJECTIVES

**Find files that serve similar/identical purposes by analyzing their actual functionality:**

### 1. **FUNCTIONAL DUPLICATES**
Look for files that accomplish the same goal through similar or different approaches:
- Scripts that process the same type of data (e.g., blog posts, configurations)
- Functions with similar logic but different implementations
- Components that render similar UI elements
- Multiple solutions to the same business problem

### 2. **VERSION VARIATIONS** 
Identify files that appear to be different versions of the same functionality:
- Scripts with suffixes like "_verbose", "_simple", "_v2", etc.
- Files with similar core functionality but different levels of detail
- Experimental vs production versions of the same feature

### 3. **PARTIAL IMPLEMENTATIONS**
Find incomplete or abandoned implementations:
- Files that seem to be early versions of functionality found elsewhere
- Partial migrations or refactoring attempts
- Template files that were customized but not fully completed

### 4. **CONFIGURATION REDUNDANCY**
Discover multiple config files serving similar purposes:
- Database setup scripts with overlapping functionality
- Environment configurations with similar variables
- Build/deployment files that configure the same systems

## ANALYSIS METHOD
1. **Read the actual code content** - don't just look at filenames
2. **Understand what each file DOES** - what problem does it solve?
3. **Compare functional purposes** - which files solve similar problems?
4. **Identify relationships** - are some files variations of others?
5. **Provide evidence** - quote specific code/content that shows similarity

## OUTPUT REQUIREMENTS
For each discovered duplicate/similar relationship, provide:
- **Files involved** (specific paths)
- **Functional similarity** (what they both do)
- **Evidence** (specific code quotes showing similarity)
- **Recommendation** (consolidate, remove, or clarify differences)

Focus on DISCOVERING actual content-based duplicates, not generic observations.
"""

        print("🧠 Launching intelligent content analysis agent...")
        
        # Use subprocess to call claude CLI directly (following your blog automation pattern)
        # Call the agent - this is an agentic system, no fallbacks
        agent_result = self._call_agent(agent_prompt)
        if not agent_result:
            raise RuntimeError("Agent call failed - agentic system requires working agent")
        
        return self._parse_agent_content_analysis(agent_result, context)
    
    def _call_agent(self, prompt):
        """Call agent using configured backend (OpenRouter API)"""
        # Clean prompt to avoid null bytes and other problematic characters
        clean_prompt = prompt.replace('\x00', '').replace('\r\n', '\n').encode('utf-8', errors='ignore').decode('utf-8')
        
        # Check OpenRouter availability
        if self.provider != 'openrouter' or not self.openrouter_client:
            print("❌ OpenRouter client not available")
            return None
        
        # Use OpenRouter API
        try:
            response = self.openrouter_client.ask(clean_prompt)
            return response.content
        except Exception as e:
            print(f"❌ OpenRouter API error: {e}")
            return None
    
    def _launch_merge_readiness_agent(self, context: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Launch AI agent to assess merge readiness."""
        
        agent_prompt = f"""
You are a senior engineering manager evaluating whether this PR is ready to merge. Consider code quality, completeness, and potential risks.

## PR Overview
- Scope: {context['pr_summary']['total_files_changed']} files, +{context['pr_summary']['total_lines_added']}/-{context['pr_summary']['total_lines_removed']} lines
- Categories affected: {len(context['categories'])} different types of files

## Recent Commit Messages
{chr(10).join(context['pr_summary']['commit_messages'])}

## File Categories Analysis
{self._format_categories_for_agent(context['categories'])}

## Sample Files (First 20 for review)
{self._format_files_for_agent(context['files'][:20])}

## Merge Readiness Assessment

Evaluate this PR across these dimensions:

1. **COMPLETENESS**: Are there signs of unfinished work?
   - TODO comments, placeholder text
   - Incomplete implementations
   - Missing corresponding changes (e.g., CSS without HTML updates)

2. **CODE QUALITY**: Does this meet merge standards?
   - Consistent patterns and conventions
   - No obvious bugs or issues
   - Appropriate scope (not mixing unrelated changes)

3. **RISK ASSESSMENT**: What are the deployment risks?
   - Large-scale changes to critical systems
   - Changes to multiple high-impact areas
   - Potential breaking changes

4. **ORGANIZATIONAL ISSUES**: Are there process problems?
   - Mixed concerns in single PR
   - Experimental code left in
   - Poor commit organization

## Response Format
```json
{{
    "merge_readiness_score": 85,  // 0-100
    "status": "READY|REVIEW_NEEDED|NEEDS_WORK|NOT_READY",
    "blocking_issues": 0,
    "warning_issues": 2,
    "info_issues": 1,
    "recommendation": "Specific recommendation for next steps",
    "issues": [
        {{
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "category": "INCOMPLETE|MIXED_CONCERNS|RISK",
            "title": "Issue title",
            "description": "Detailed description",
            "affected_files": ["file1", "file2"],
            "recommendation": "How to fix this",
            "agent_reasoning": "Why this is an issue"
        }}
    ],
    "confidence": "HIGH|MEDIUM|LOW",
    "analysis_notes": "Key observations about this PR"
}}
```

Be thorough but practical - focus on issues that genuinely impact merge safety.
"""

        print("🤖 Launching merge readiness assessment agent...")
        
        # Call the agent - agentic system, no fallbacks
        agent_result = self._call_agent(agent_prompt)
        if not agent_result:
            raise RuntimeError("Merge readiness agent call failed - agentic system requires working agent")
        
        return self._parse_merge_readiness_response(agent_result, context)
    
    def _launch_pattern_analysis_agent(self, context: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Launch AI agent to analyze code patterns and consistency."""
        
        # For now, just return empty - this is an agentic system, implement agent or nothing
        return {'issues': [], 'insights': {}}
    
    def _intelligent_duplicate_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform intelligent duplicate analysis using heuristics and patterns."""
        issues = []
        
        # 1. Analyze filename patterns for potential duplicates
        filename_groups = {}
        for file_data in context['files']:
            name = Path(file_data['path']).name
            stem = Path(file_data['path']).stem.lower()
            
            # Group by similar stems (ignoring case and common suffixes)
            clean_stem = stem.replace('-copy', '').replace('_copy', '').replace('2', '').replace('old', '').replace('new', '')
            
            if clean_stem not in filename_groups:
                filename_groups[clean_stem] = []
            filename_groups[clean_stem].append(file_data)
        
        # Find potential duplicates
        for stem, files in filename_groups.items():
            if len(files) > 1:
                # Check if they're in the same category (higher chance of being duplicates)
                categories = set(f['category'] for f in files)
                if len(categories) == 1:  # Same category
                    severity = 'HIGH' if any('copy' in f['path'].lower() for f in files) else 'MEDIUM'
                    
                    issue = QualityIssue(
                        severity=severity,
                        category='DUPLICATE',
                        title=f'Potential duplicate files: {stem}',
                        description=f'Found {len(files)} files with similar names in {list(categories)[0]} category',
                        affected_files=[f['path'] for f in files],
                        recommendation='Review files for duplication and consolidate if necessary',
                        agent_reasoning=f'Files have similar stems "{stem}" and are in the same category, suggesting potential duplication'
                    )
                    issues.append(issue)
        
        # 2. Look for content-based duplicates in small files
        content_groups = {}
        for file_data in context['files']:
            if file_data.get('content_sample') and len(file_data['content_sample']) > 100:
                content_hash = hash(file_data['content_sample'][:500])  # Hash first 500 chars
                if content_hash not in content_groups:
                    content_groups[content_hash] = []
                content_groups[content_hash].append(file_data)
        
        for content_hash, files in content_groups.items():
            if len(files) > 1:
                issue = QualityIssue(
                    severity='CRITICAL',
                    category='DUPLICATE',
                    title='Files with identical content detected',
                    description=f'Found {len(files)} files with identical or very similar content',
                    affected_files=[f['path'] for f in files],
                    recommendation='Remove duplicate files or ensure they serve different purposes',
                    agent_reasoning='Files have identical content samples, indicating exact or near-exact duplication'
                )
                issues.append(issue)
        
        # 3. Look for incomplete refactoring patterns
        refactoring_patterns = [
            ('old', 'new'), ('v1', 'v2'), ('temp', 'final'), ('backup', 'current')
        ]
        
        for old_pattern, new_pattern in refactoring_patterns:
            old_files = [f for f in context['files'] if old_pattern in f['path'].lower()]
            new_files = [f for f in context['files'] if new_pattern in f['path'].lower()]
            
            if old_files and new_files:
                issue = QualityIssue(
                    severity='MEDIUM',
                    category='INCOMPLETE',
                    title=f'Potential incomplete refactoring: {old_pattern}/{new_pattern} pattern',
                    description=f'Found both {old_pattern} and {new_pattern} files, suggesting incomplete refactoring',
                    affected_files=[f['path'] for f in old_files + new_files],
                    recommendation='Complete refactoring by removing old files or clarifying purpose',
                    agent_reasoning=f'Presence of both {old_pattern} and {new_pattern} patterns suggests incomplete migration'
                )
                issues.append(issue)
        
        return {
            'issues': issues,
            'insights': {
                'total_potential_duplicates': len([i for i in issues if i.category == 'DUPLICATE']),
                'confidence_level': 'MEDIUM',
                'analysis_summary': f'Analyzed {len(context["files"])} files for duplication patterns'
            }
        }
    
    def _format_categories_for_agent(self, categories: Dict[str, List[Dict]]) -> str:
        """Format category information for agent consumption."""
        lines = []
        for category, files in categories.items():
            lines.append(f"- {category}: {len(files)} files")
            if len(files) <= 5:
                for file in files:
                    lines.append(f"  • {file['path']} ({file['change_type']}, +{file['lines_added']}/-{file['lines_removed']})")
            else:
                for file in files[:3]:
                    lines.append(f"  • {file['path']} ({file['change_type']}, +{file['lines_added']}/-{file['lines_removed']})")
                lines.append(f"  • ... and {len(files) - 3} more files")
        return '\n'.join(lines)
    
    def _format_files_for_agent(self, files: List[Dict]) -> str:
        """Format file information for agent analysis."""
        lines = []
        for file in files:
            lines.append(f"## {file['path']}")
            lines.append(f"- Category: {file['category']} ({file['importance']})")
            lines.append(f"- Change: {file['change_type']} (+{file['lines_added']}/-{file['lines_removed']})")
            lines.append(f"- Size: {file['size']} bytes, {file['total_lines']} lines")
            
            if file.get('content_sample'):
                lines.append(f"- Content sample:")
                lines.append(f"```")
                lines.append(file['content_sample'][:500])  # Limit sample size
                if len(file['content_sample']) > 500:
                    lines.append("... [truncated]")
                lines.append(f"```")
            lines.append("")
        return '\n'.join(lines)
    
    def _convert_agent_response_to_issues(self, agent_response: Dict) -> Dict[str, Any]:
        """Convert agent JSON response to our issue format."""
        issues = []
        
        for issue_data in agent_response.get('issues', []):
            issue = QualityIssue(
                severity=issue_data.get('severity', 'MEDIUM'),
                category=issue_data.get('category', 'UNKNOWN'),
                title=issue_data.get('title', ''),
                description=issue_data.get('description', ''),
                affected_files=issue_data.get('affected_files', []),
                recommendation=issue_data.get('recommendation', ''),
                agent_reasoning=issue_data.get('agent_reasoning', '')
            )
            issues.append(issue)
        
        return {
            'issues': issues,
            'insights': agent_response.get('insights', {}),
            'agent_response': agent_response
        }
    
    def _parse_text_response(self, text_response: str, category: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails."""
        # Simple fallback - create a single issue from the text response
        issue = QualityIssue(
            severity='MEDIUM',
            category=category,
            title='Agent analysis results',
            description=text_response[:500],  # Truncate long responses
            affected_files=[],
            recommendation='Review agent analysis for details',
            agent_reasoning=text_response
        )
        
        return {
            'issues': [issue],
            'insights': {'confidence_level': 'LOW', 'analysis_summary': 'Text-based analysis'}
        }
    
    def _fallback_duplicate_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback duplicate analysis when agent fails."""
        issues = []
        
        # Simple filename-based duplicate detection
        filenames = {}
        for file_data in context['files']:
            name = Path(file_data['path']).name
            if name not in filenames:
                filenames[name] = []
            filenames[name].append(file_data['path'])
        
        # Find exact filename duplicates
        for name, paths in filenames.items():
            if len(paths) > 1:
                issue = QualityIssue(
                    severity='HIGH',
                    category='DUPLICATE',
                    title=f'Duplicate filename: {name}',
                    description=f'Found {len(paths)} files with the same name in different locations',
                    affected_files=paths,
                    recommendation='Consolidate duplicate files or ensure they serve different purposes',
                    agent_reasoning='Fallback analysis: detected identical filenames'
                )
                issues.append(issue)
        
        return {'issues': issues, 'insights': {}}
    
    def _fallback_merge_readiness_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback merge readiness analysis when agent fails."""
        issues = []
        total_files = len(context['files'])
        
        # Check for large PR
        if total_files > 100:
            issue = QualityIssue(
                severity='HIGH',
                category='MIXED_CONCERNS',
                title='Large PR with many files',
                description=f'PR affects {total_files} files, which may be difficult to review thoroughly',
                affected_files=[f['path'] for f in context['files'][:10]],
                recommendation='Consider breaking this PR into smaller, focused changes',
                agent_reasoning='Fallback analysis: large PR detected'
            )
            issues.append(issue)
        
        # Calculate basic readiness score
        score = max(0, 100 - (total_files // 10) * 5)  # Reduce score for large PRs
        
        status = 'READY' if score > 80 else 'REVIEW_NEEDED' if score > 60 else 'NEEDS_WORK'
        
        return {
            'issues': issues,
            'merge_readiness_score': score,
            'status': status,
            'recommendation': 'Basic analysis completed - consider manual review'
        }
    
    def _fallback_pattern_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback pattern analysis when agent fails."""
        return {'issues': [], 'insights': {}}
    
    def _calculate_merge_readiness(self, issues: List[QualityIssue], merge_analysis: Dict) -> Dict[str, Any]:
        """Calculate merge readiness based on all issues."""
        critical_issues = len([i for i in issues if i.severity == 'CRITICAL'])
        high_issues = len([i for i in issues if i.severity == 'HIGH'])
        medium_issues = len([i for i in issues if i.severity == 'MEDIUM'])
        
        # Use agent's score if available, otherwise calculate
        score = merge_analysis.get('merge_readiness_score', 100)
        if 'merge_readiness_score' not in merge_analysis:
            penalty = critical_issues * 40 + high_issues * 20 + medium_issues * 5
            score = max(0, 100 - penalty)
        
        if critical_issues > 0:
            status = 'NOT_READY'
            recommendation = 'Critical issues must be resolved before merge'
        elif score < 60:
            status = 'NEEDS_WORK'
            recommendation = 'Address high-priority issues before merge'
        elif score < 80:
            status = 'REVIEW_NEEDED'
            recommendation = 'Consider addressing issues for better code quality'
        else:
            status = 'READY'
            recommendation = 'PR appears ready for merge'
        
        return {
            'score': score,
            'status': status,
            'recommendation': recommendation,
            'blocking_issues': critical_issues,
            'warning_issues': high_issues,
            'info_issues': medium_issues
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
    
    def _extract_recommendations(self, issues: List[QualityIssue]) -> List[str]:
        """Extract unique recommendations from all issues."""
        recommendations = set()
        for issue in issues:
            if issue.recommendation:
                recommendations.add(issue.recommendation)
        return list(recommendations)
    
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
    
    def load_exceptions(self):
        """Load quality issue exceptions from config."""
        config_dir = Path.cwd() / "config"
        exceptions_file = config_dir / "quality_exceptions.json"
        
        self.exceptions = []
        if exceptions_file.exists():
            try:
                with open(exceptions_file, 'r') as f:
                    data = json.load(f)
                    self.exceptions = data
                print(f"📋 Loaded {len(self.exceptions)} quality exceptions")
            except Exception as e:
                print(f"⚠️  Warning: Could not load exceptions: {e}")
    
    def is_issue_suppressed(self, issue: QualityIssue) -> bool:
        """Check if a quality issue should be suppressed based on exceptions."""
        for exception in self.exceptions:
            if not exception.get('active', True):
                continue
                
            pattern = exception.get('pattern', '').lower()
            
            # More flexible pattern matching
            issue_title_lower = issue.title.lower()
            issue_category_lower = issue.category.lower()
            
            # Check if pattern matches issue title, category, or affected files
            pattern_matches = (
                pattern in issue_title_lower or 
                pattern in issue_category_lower or
                # Also check if all words in pattern appear in title (order doesn't matter)
                all(word in issue_title_lower for word in pattern.split() if len(word) > 2) or
                any(pattern in file_path.lower() for file_path in issue.affected_files)
            )
            
            if pattern_matches:
                print(f"🔇 Suppressing issue: {issue.title} (matches pattern: {exception.get('pattern', '')})")
                return True
        
        return False
    
    def filter_suppressed_issues(self, issues: List[QualityIssue]) -> List[QualityIssue]:
        """Filter out suppressed issues based on user exceptions."""
        return [issue for issue in issues if not self.is_issue_suppressed(issue)]
    
    def _prepare_files_for_content_analysis(self, context: Dict[str, Any], repo_path: str) -> str:
        """Prepare detailed file content for intelligent analysis."""
        analysis_sections = []
        
        # Group files by category for focused analysis
        for category, files in context['categories'].items():
            if not files:
                continue
                
            analysis_sections.append(f"\n### {category} FILES ({len(files)} files)")
            
            # Analyze up to 10 files per category for performance
            for file_data in files[:10]:
                file_path = Path(repo_path) / file_data['path']
                
                analysis_sections.append(f"\n#### {file_data['path']}")
                analysis_sections.append(f"- Change: {file_data['change_type']} (+{file_data['lines_added']}/-{file_data['lines_removed']})")
                analysis_sections.append(f"- Size: {file_data['size']} bytes")
                
                # Get fuller content for analysis
                if file_path.exists() and file_path.stat().st_size < 100000:  # <100KB
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Clean content to avoid null bytes
                        content = content.replace('\x00', '').replace('\r\n', '\n')
                        
                        # Extract functional summary for duplicate detection
                        lines = content.split('\n')
                        
                        # Build functional analysis instead of random snippets
                        functional_analysis = []
                        
                        # 1. File header/purpose (first 10 lines)
                        functional_analysis.append("=== FILE PURPOSE & HEADER ===")
                        functional_analysis.extend(lines[:10])
                        
                        # 2. Function/class definitions (complete signatures)
                        functional_analysis.append("\n=== FUNCTIONS & CLASSES ===")
                        for i, line in enumerate(lines):
                            if any(pattern in line for pattern in ['def ', 'function ', 'class ', 'const ', 'let ', 'var ']):
                                # Include the full function definition
                                start = i
                                end = min(len(lines), i + 15)  # Get function body context
                                functional_analysis.extend(lines[start:end])
                                functional_analysis.append("---")
                        
                        # 3. Main execution/workflow (if exists)
                        functional_analysis.append("\n=== MAIN WORKFLOW ===")
                        for i, line in enumerate(lines):
                            if any(pattern in line.lower() for pattern in ['if __name__', 'main()', 'export default', 'module.exports']):
                                start = max(0, i - 5)
                                end = min(len(lines), i + 20)
                                functional_analysis.extend(lines[start:end])
                                break
                        
                        # 4. Key imports/dependencies 
                        functional_analysis.append("\n=== IMPORTS & DEPENDENCIES ===")
                        for line in lines[:50]:  # Check first 50 lines for imports
                            if any(pattern in line for pattern in ['import ', 'from ', 'require(', 'include ', '#include']):
                                functional_analysis.append(line)
                        
                        content_sample = '\n'.join(functional_analysis[:200])  # Limit total lines but focus on functionality
                        
                        analysis_sections.append(f"- Content analysis:")
                        analysis_sections.append("```")
                        analysis_sections.append(content_sample[:3000])  # Limit to 3KB
                        if len(content_sample) > 3000:
                            analysis_sections.append("... [truncated for analysis]")
                        analysis_sections.append("```")
                        
                    except Exception as e:
                        analysis_sections.append(f"- Content: [Error reading file: {e}]")
                else:
                    analysis_sections.append(f"- Content: [File too large or missing]")
        
        return '\n'.join(analysis_sections)
    
    def _parse_agent_content_analysis(self, agent_result: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the agent's content analysis response."""
        issues = []
        
        # Try to extract structured information from agent response
        lines = agent_result.split('\n')
        current_issue = None
        
        for line in lines:
            line = line.strip()
            
            # Look for severity indicators
            if any(severity in line.upper() for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']):
                if current_issue:
                    issues.append(current_issue)
                
                # Extract severity
                severity = 'MEDIUM'
                for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    if sev in line.upper():
                        severity = sev
                        break
                
                current_issue = QualityIssue(
                    severity=severity,
                    category='DUPLICATE',  # Default, may be updated
                    title=line,
                    description='',
                    affected_files=[],
                    recommendation='',
                    agent_reasoning=''
                )
            
            elif current_issue:
                # Accumulate information for current issue
                if line.startswith('Files:') or line.startswith('Affected:'):
                    # Extract file names
                    file_text = line.split(':', 1)[1].strip()
                    current_issue.affected_files = [f.strip() for f in file_text.split(',')]
                elif line.startswith('Problem:') or line.startswith('Description:'):
                    current_issue.description = line.split(':', 1)[1].strip()
                elif line.startswith('Recommendation:'):
                    current_issue.recommendation = line.split(':', 1)[1].strip()
                elif line.startswith('Reasoning:') or line.startswith('Evidence:'):
                    current_issue.agent_reasoning = line.split(':', 1)[1].strip()
        
        # Add the last issue if exists
        if current_issue:
            issues.append(current_issue)
        
        # If no structured issues found, create a general analysis issue
        if not issues:
            issue = QualityIssue(
                severity='MEDIUM',
                category='ANALYSIS',
                title='Agent Content Analysis Results',
                description='Detailed content analysis completed',
                affected_files=[],
                recommendation='Review agent analysis for specific recommendations',
                agent_reasoning=agent_result[:1000]  # First 1000 chars
            )
            issues.append(issue)
        
        return {
            'issues': issues,
            'insights': {
                'agent_analysis': agent_result,
                'confidence_level': 'HIGH',
                'analysis_summary': f'AI agent analyzed file contents and purposes'
            }
        }
    
    def _parse_merge_readiness_response(self, agent_result: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the merge readiness agent's JSON response."""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON block in the response
            json_match = re.search(r'```json\s*({.*?})\s*```', agent_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                response_data = json.loads(json_str)
                
                # Convert to our issue format
                issues = []
                for issue_data in response_data.get('issues', []):
                    issue = QualityIssue(
                        severity=issue_data.get('severity', 'MEDIUM'),
                        category=issue_data.get('category', 'MERGE_READINESS'),
                        title=issue_data.get('title', ''),
                        description=issue_data.get('description', ''),
                        affected_files=issue_data.get('affected_files', []),
                        recommendation=issue_data.get('recommendation', ''),
                        agent_reasoning=issue_data.get('agent_reasoning', '')
                    )
                    issues.append(issue)
                
                return {
                    'issues': issues,
                    'merge_readiness_score': response_data.get('merge_readiness_score', 50),
                    'status': response_data.get('status', 'REVIEW_NEEDED'),
                    'recommendation': response_data.get('recommendation', ''),
                    'confidence': response_data.get('confidence', 'MEDIUM'),
                    'analysis_notes': response_data.get('analysis_notes', ''),
                    'blocking_issues': response_data.get('blocking_issues', 0),
                    'warning_issues': response_data.get('warning_issues', 0),
                    'info_issues': response_data.get('info_issues', 0)
                }
            else:
                # No JSON found, parse as text
                return self._parse_text_merge_readiness(agent_result, context)
                
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON response: {e}")
            return self._parse_text_merge_readiness(agent_result, context)
        except Exception as e:
            print(f"⚠️  Error parsing merge readiness response: {e}")
            return self._fallback_merge_readiness_analysis(context)
    
    def _parse_text_merge_readiness(self, agent_result: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse text-based merge readiness response."""
        # Create a general issue from the agent's analysis
        issue = QualityIssue(
            severity='MEDIUM',
            category='MERGE_READINESS',
            title='Merge Readiness Analysis',
            description='AI agent analysis of merge readiness',
            affected_files=[],
            recommendation='Review detailed analysis for merge recommendations',
            agent_reasoning=agent_result[:1000]  # First 1000 chars
        )
        
        # Try to extract a score from text
        import re
        score_match = re.search(r'score[:\s]*(\d+)', agent_result.lower())
        score = int(score_match.group(1)) if score_match else 70
        
        status = 'READY' if score > 80 else 'REVIEW_NEEDED' if score > 60 else 'NEEDS_WORK'
        
        return {
            'issues': [issue],
            'merge_readiness_score': score,
            'status': status,
            'recommendation': 'Review agent analysis for detailed recommendations',
            'confidence': 'MEDIUM'
        }
    
    def _enhanced_content_analysis(self, context: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Enhanced content analysis as fallback when agent fails."""
        issues = []
        
        # Content-based analysis by reading actual files
        content_analysis = {}
        
        for file_data in context['files'][:50]:  # Limit for performance
            file_path = Path(repo_path) / file_data['path']
            
            if not file_path.exists() or file_path.stat().st_size > 50000:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Analyze content characteristics
                analysis = {
                    'path': file_data['path'],
                    'category': file_data['category'],
                    'has_todos': 'todo' in content.lower() or 'fixme' in content.lower(),
                    'has_placeholders': any(p in content.lower() for p in ['placeholder', 'lorem ipsum', 'replace this']),
                    'function_count': len(re.findall(r'function\s+\w+|def\s+\w+|const\s+\w+\s*=', content)),
                    'class_count': len(re.findall(r'class\s+\w+|<.*class=', content)),
                    'content_hash': hash(content[:1000]),  # Hash of first 1KB
                    'key_identifiers': re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{4,}', content)[:20]  # First 20 identifiers
                }
                
                content_analysis[file_data['path']] = analysis
                
            except Exception:
                continue
        
        # Find content duplicates by hash
        hash_groups = {}
        for path, analysis in content_analysis.items():
            content_hash = analysis['content_hash']
            if content_hash not in hash_groups:
                hash_groups[content_hash] = []
            hash_groups[content_hash].append((path, analysis))
        
        for content_hash, files in hash_groups.items():
            if len(files) > 1:
                issue = QualityIssue(
                    severity='HIGH',
                    category='DUPLICATE',
                    title='Files with very similar content detected',
                    description=f'Found {len(files)} files with similar content structure',
                    affected_files=[f[0] for f in files],
                    recommendation='Review files for actual duplication and consolidate if needed',
                    agent_reasoning='Files have similar content hashes indicating potential duplication'
                )
                issues.append(issue)
        
        # Find incomplete work
        incomplete_files = [
            path for path, analysis in content_analysis.items() 
            if analysis['has_todos'] or analysis['has_placeholders']
        ]
        
        if incomplete_files:
            issue = QualityIssue(
                severity='MEDIUM',
                category='INCOMPLETE',
                title='Files with TODO markers or placeholder content',
                description=f'Found {len(incomplete_files)} files with incomplete implementations',
                affected_files=incomplete_files,
                recommendation='Complete TODO items and replace placeholder content before merge',
                agent_reasoning='Files contain TODO markers or placeholder text indicating incomplete work'
            )
            issues.append(issue)
        
        return {
            'issues': issues,
            'insights': {
                'content_analysis_performed': True,
                'files_analyzed': len(content_analysis),
                'confidence_level': 'MEDIUM'
            }
        }
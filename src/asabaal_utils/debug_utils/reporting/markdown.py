"""Markdown report generation for Debug Session Tracker.

This module provides classes for generating Markdown reports from debug sessions.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, TextIO

from ..session.session import DebugSession


class MarkdownReport:
    """Markdown report generator for debug sessions.

    This class generates Markdown reports from debug sessions, including
    diagnostics, issues, fixes, and other session information.

    Attributes:
        session: The debug session to generate a report for
    """

    def __init__(self, session: DebugSession):
        """Initialize the Markdown report generator.

        Args:
            session: The debug session to generate a report for
        """
        self.session = session

    def generate(self) -> str:
        """Generate a Markdown report.

        Returns:
            Markdown report as a string
        """
        # Build the report sections
        sections = [
            self._generate_header(),
            self._generate_summary(),
            self._generate_diagnostics(),
            self._generate_issues(),
            self._generate_fixes(),
            self._generate_metrics()
        ]
        
        # Join the sections with double newlines
        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        """Generate the report header.

        Returns:
            Report header as Markdown
        """
        return (
            f"# Debug Session Report: {self.session.name}\n\n"
            f"- **Project:** {self.session.project}\n"
            f"- **Session ID:** {self.session.id}\n"
            f"- **Status:** {self.session.status.capitalize()}\n"
            f"- **Created:** {self.session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- **Last Updated:** {self.session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

    def _generate_summary(self) -> str:
        """Generate the session summary.

        Returns:
            Session summary as Markdown
        """
        # Calculate session duration
        duration_seconds = (self.session.updated_at - self.session.created_at).total_seconds()
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Count diagnostics, issues, and fixes
        total_diagnostics = len(self.session.diagnostics)
        total_issues = sum(len(d.issues_found) for d in self.session.diagnostics)
        fixed_issues = sum(len(f.resolved_issues) for f in self.session.fixes)
        total_fixes = len(self.session.fixes)
        successful_fixes = sum(1 for f in self.session.fixes if f.successful)
        
        summary = [
            "## Summary\n",
            f"- **Duration:** {duration_str}",
            f"- **Diagnostics Run:** {total_diagnostics}",
            f"- **Issues Found:** {total_issues}",
            f"- **Issues Fixed:** {fixed_issues} ({fixed_issues / total_issues * 100:.1f}% of total)" if total_issues > 0 else "- **Issues Fixed:** 0",
            f"- **Fixes Applied:** {total_fixes}",
            f"- **Successful Fixes:** {successful_fixes} ({successful_fixes / total_fixes * 100:.1f}% of total)" if total_fixes > 0 else "- **Successful Fixes:** 0"
        ]
        
        # Add session completion summary or abandonment reason
        if self.session.status == "completed" and self.session.summary:
            summary.append("\n### Session Summary\n")
            summary.append(self.session.summary)
        elif self.session.status == "abandoned" and self.session.abandonment_reason:
            summary.append("\n### Abandonment Reason\n")
            summary.append(self.session.abandonment_reason)
            
        return "\n".join(summary)

    def _generate_diagnostics(self) -> str:
        """Generate the diagnostics section.

        Returns:
            Diagnostics section as Markdown
        """
        if not self.session.diagnostics:
            return "## Diagnostics\n\nNo diagnostics were run in this session."
            
        diagnostics = ["## Diagnostics\n"]
        
        for i, diagnostic in enumerate(self.session.diagnostics):
            # Calculate duration
            duration = diagnostic.duration()
            duration_str = f"{duration:.2f}s" if duration is not None else "N/A"
            
            # Count issues by severity
            issue_counts = diagnostic.count_issues_by_severity()
            
            diagnostics.extend([
                f"### {i+1}. {diagnostic.tool} on {diagnostic.target}\n",
                f"- **ID:** {diagnostic.id}",
                f"- **Time:** {diagnostic.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **Duration:** {duration_str}",
                f"- **Issues Found:** {len(diagnostic.issues_found)}"
            ])
            
            # Add issue severity breakdown
            if any(issue_counts.values()):
                diagnostics.append("- **Issues by Severity:**")
                for severity, count in issue_counts.items():
                    if count > 0:
                        diagnostics.append(f"  - {severity.capitalize()}: {count}")
            
            # Add parameters if any
            if diagnostic.parameters:
                diagnostics.append("- **Parameters:**")
                for key, value in diagnostic.parameters.items():
                    diagnostics.append(f"  - {key}: {value}")
            
            # Add a sample of issues if any
            if diagnostic.issues_found:
                diagnostics.append("\n#### Sample Issues\n")
                
                # Show up to 5 issues
                for j, issue in enumerate(diagnostic.issues_found[:5]):
                    diagnostics.append(f"1. **{issue.severity.capitalize()}:** {issue.description} ({issue.location})")
                    
                # Indicate if there are more issues
                if len(diagnostic.issues_found) > 5:
                    diagnostics.append(f"\n*{len(diagnostic.issues_found) - 5} more issues not shown.*")
            
        return "\n".join(diagnostics)

    def _generate_issues(self) -> str:
        """Generate the issues section.

        Returns:
            Issues section as Markdown
        """
        # Collect all issues from all diagnostics
        all_issues = []
        for diagnostic in self.session.diagnostics:
            all_issues.extend(diagnostic.issues_found)
            
        if not all_issues:
            return "## Issues\n\nNo issues were found in this session."
            
        # Group issues by severity
        issues_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for issue in all_issues:
            severity = issue.severity.lower()
            if severity in issues_by_severity:
                issues_by_severity[severity].append(issue)
                
        # Build the issues section
        issues = ["## Issues\n"]
        
        for severity in ["critical", "high", "medium", "low"]:
            severity_issues = issues_by_severity[severity]
            if severity_issues:
                issues.append(f"### {severity.capitalize()} Severity Issues ({len(severity_issues)})\n")
                
                for i, issue in enumerate(severity_issues):
                    status = "Fixed" if issue.is_fixed() else "Unfixed"
                    issues.append(f"1. **{status}:** {issue.description} ({issue.location})")
                    
                    # Add fix reference if the issue is fixed
                    if issue.is_fixed():
                        issues.append(f"   - Fixed by: {issue.fixed_by}")
                        
                issues.append("")  # Add a blank line between severity sections
                
        return "\n".join(issues)

    def _generate_fixes(self) -> str:
        """Generate the fixes section.

        Returns:
            Fixes section as Markdown
        """
        if not self.session.fixes:
            return "## Fixes\n\nNo fixes were applied in this session."
            
        fixes = ["## Fixes\n"]
        
        for i, fix in enumerate(self.session.fixes):
            status = "Successful" if fix.successful else "Failed"
            fixes.extend([
                f"### {i+1}. {fix.script} on {fix.target} ({status})\n",
                f"- **ID:** {fix.id}",
                f"- **Time:** {fix.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **Status:** {status}",
                f"- **Issues Resolved:** {len(fix.resolved_issues)}"
            ])
            
            # Add parameters if any
            if fix.parameters:
                fixes.append("- **Parameters:**")
                for key, value in fix.parameters.items():
                    fixes.append(f"  - {key}: {value}")
            
            # Add resolved issues if any
            if fix.resolved_issues:
                fixes.append("\n#### Resolved Issues\n")
                
                for issue_id in fix.resolved_issues:
                    fixes.append(f"- {issue_id}")
            
            # Add file changes if any
            if fix.changes:
                fixes.append("\n#### File Changes\n")
                
                for change in fix.changes:
                    summary = change.summarize_changes()
                    fixes.append(f"- **{summary['file_path']}**")
                    fixes.append(f"  - Lines before: {summary['lines_before']}, after: {summary['lines_after']}")
                    fixes.append(f"  - Added: {summary['lines_added']}, Removed: {summary['lines_removed']}, Modified: {summary['lines_modified']}")
                    fixes.append(f"  - Change percentage: {summary['change_percentage']}%")
                    
                    # Add modified functions if available
                    changed_functions = change.get_changed_functions()
                    if changed_functions:
                        fixes.append("  - Modified functions:")
                        for func in changed_functions:
                            fixes.append(f"    - `{func}`")
            
        return "\n".join(fixes)

    def _generate_metrics(self) -> str:
        """Generate the metrics section.

        Returns:
            Metrics section as Markdown
        """
        # Calculate session duration
        duration_seconds = (self.session.updated_at - self.session.created_at).total_seconds()
        
        # Count diagnostics and issues by tool
        diagnostics_by_tool = {}
        issues_by_tool = {}
        
        for diagnostic in self.session.diagnostics:
            tool = diagnostic.tool
            
            if tool not in diagnostics_by_tool:
                diagnostics_by_tool[tool] = 0
                issues_by_tool[tool] = 0
                
            diagnostics_by_tool[tool] += 1
            issues_by_tool[tool] += len(diagnostic.issues_found)
            
        # Count fixes and success rate
        total_fixes = len(self.session.fixes)
        successful_fixes = sum(1 for f in self.session.fixes if f.successful)
        success_rate = (successful_fixes / total_fixes * 100) if total_fixes > 0 else 0
        
        # Generate the metrics section
        metrics = [
            "## Metrics\n",
            "### Session Metrics",
            f"- **Total Duration:** {int(duration_seconds)} seconds",
            f"- **Issues per Diagnostic:** {sum(len(d.issues_found) for d in self.session.diagnostics) / len(self.session.diagnostics):.2f}" if self.session.diagnostics else "- **Issues per Diagnostic:** N/A",
            f"- **Fix Success Rate:** {success_rate:.1f}%"
        ]
        
        # Add diagnostics by tool
        if diagnostics_by_tool:
            metrics.append("\n### Diagnostics by Tool")
            for tool, count in diagnostics_by_tool.items():
                metrics.append(f"- **{tool}:** {count} runs, {issues_by_tool[tool]} issues")
        
        return "\n".join(metrics)

    def save(self, file_path: str) -> bool:
        """Save the report to a file.

        Args:
            file_path: Path where the report will be saved

        Returns:
            True if the report was saved successfully, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                f.write(self.generate())
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False

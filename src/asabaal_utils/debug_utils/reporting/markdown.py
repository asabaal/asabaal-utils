"""Markdown report generation for Debug Session Tracker.

This module provides classes for generating Markdown reports from debug sessions.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, TextIO, Union

from ..session.session import DebugSession
from ..tracking.diagnostics import DiagnosticRun, Issue
from ..tracking.fixes import AppliedFix


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
        
        # Safely count issues
        total_issues = 0
        fixed_issues = 0
        
        for diag in self.session.diagnostics:
            # Handle both DiagnosticRun objects and dictionaries
            if isinstance(diag, DiagnosticRun):
                total_issues += len(diag.issues_found)
            elif isinstance(diag, dict) and 'issues_found' in diag:
                total_issues += len(diag['issues_found'])
            
        # Safely count fixed issues
        total_fixes = len(self.session.fixes)
        successful_fixes = 0
        
        for fix in self.session.fixes:
            # Handle both AppliedFix objects and dictionaries
            if isinstance(fix, AppliedFix):
                fixed_issues += len(fix.resolved_issues)
                if fix.successful:
                    successful_fixes += 1
            elif isinstance(fix, dict):
                if 'resolved_issues' in fix:
                    fixed_issues += len(fix['resolved_issues'])
                if fix.get('successful', False):
                    successful_fixes += 1
        
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
            # Handle both DiagnosticRun objects and dictionaries
            if isinstance(diagnostic, dict):
                # Create a DiagnosticRun from the dictionary
                from ..tracking.diagnostics import DiagnosticRun
                try:
                    diagnostic = DiagnosticRun.from_dict(diagnostic)
                except Exception as e:
                    # If conversion fails, work with the dictionary directly
                    start_time = diagnostic.get('start_time')
                    if isinstance(start_time, str):
                        try:
                            start_time = datetime.fromisoformat(start_time)
                        except:
                            start_time = datetime.now()
                    
                    end_time = diagnostic.get('end_time')
                    if isinstance(end_time, str):
                        try:
                            end_time = datetime.fromisoformat(end_time)
                        except:
                            end_time = start_time
                    
                    # Calculate duration
                    if start_time and end_time:
                        duration = (end_time - start_time).total_seconds()
                        duration_str = f"{duration:.2f}s"
                    else:
                        duration_str = "N/A"
                    
                    # Count issues
                    issues_found = diagnostic.get('issues_found', [])
                    num_issues = len(issues_found)
                    
                    diagnostics.extend([
                        f"### {i+1}. {diagnostic.get('tool', 'Unknown Tool')} on {diagnostic.get('target', 'Unknown Target')}\n",
                        f"- **ID:** {diagnostic.get('id', 'Unknown ID')}",
                        f"- **Time:** {start_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(start_time, datetime) else 'Unknown'}",
                        f"- **Duration:** {duration_str}",
                        f"- **Issues Found:** {num_issues}"
                    ])
                    
                    # Add a sample of issues if any
                    if issues_found:
                        diagnostics.append("\n#### Sample Issues\n")
                        
                        # Show up to 5 issues
                        for j, issue in enumerate(issues_found[:5]):
                            if isinstance(issue, dict):
                                severity = issue.get('severity', 'unknown').capitalize()
                                description = issue.get('description', 'Unknown issue')
                                location = issue.get('location', 'Unknown location')
                                diagnostics.append(f"1. **{severity}:** {description} ({location})")
                            else:
                                diagnostics.append(f"1. Issue {j+1}")
                        
                        # Indicate if there are more issues
                        if len(issues_found) > 5:
                            diagnostics.append(f"\n*{len(issues_found) - 5} more issues not shown.*")
                    
                    continue
            
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
            # Handle both DiagnosticRun objects and dictionaries
            if isinstance(diagnostic, DiagnosticRun):
                all_issues.extend(diagnostic.issues_found)
            elif isinstance(diagnostic, dict) and 'issues_found' in diagnostic:
                # Convert dictionaries to Issue objects
                from ..tracking.diagnostics import Issue
                for issue_data in diagnostic['issues_found']:
                    if isinstance(issue_data, dict):
                        try:
                            issue = Issue.from_dict(issue_data)
                            all_issues.append(issue)
                        except Exception as e:
                            # If conversion fails, create a simple representation
                            severity = issue_data.get('severity', 'unknown')
                            description = issue_data.get('description', 'Unknown issue')
                            location = issue_data.get('location', 'Unknown location')
                            fixed_by = issue_data.get('fixed_by')
                            
                            # Create a minimal issue object
                            issue = Issue(
                                id=issue_data.get('id', 'unknown_id'),
                                type=issue_data.get('type', 'unknown'),
                                severity=severity,
                                location=location,
                                description=description,
                                fixed_by=fixed_by
                            )
                            all_issues.append(issue)
            
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
            # Handle both AppliedFix objects and dictionaries
            if isinstance(fix, dict):
                # Create an AppliedFix from the dictionary
                from ..tracking.fixes import AppliedFix
                try:
                    fix = AppliedFix.from_dict(fix)
                except Exception as e:
                    # If conversion fails, work with the dictionary directly
                    timestamp = fix.get('timestamp')
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp)
                        except:
                            timestamp = datetime.now()
                    
                    status = "Successful" if fix.get('successful', False) else "Failed"
                    script = fix.get('script', 'Unknown script')
                    target = fix.get('target', 'Unknown target')
                    fix_id = fix.get('id', 'Unknown ID')
                    resolved_issues = fix.get('resolved_issues', [])
                    changes = fix.get('changes', [])
                    
                    fixes.extend([
                        f"### {i+1}. {script} on {target} ({status})\n",
                        f"- **ID:** {fix_id}",
                        f"- **Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp, datetime) else 'Unknown'}",
                        f"- **Status:** {status}",
                        f"- **Issues Resolved:** {len(resolved_issues)}"
                    ])
                    
                    # Add parameters if any
                    if 'parameters' in fix and fix['parameters']:
                        fixes.append("- **Parameters:**")
                        for key, value in fix['parameters'].items():
                            fixes.append(f"  - {key}: {value}")
                    
                    # Add resolved issues if any
                    if resolved_issues:
                        fixes.append("\n#### Resolved Issues\n")
                        
                        for issue_id in resolved_issues:
                            fixes.append(f"- {issue_id}")
                    
                    # Add file changes if any
                    if changes:
                        fixes.append("\n#### File Changes\n")
                        
                        for change in changes:
                            if isinstance(change, dict):
                                file_path = change.get('file_path', 'Unknown file')
                                fixes.append(f"- **{file_path}**")
                                
                                # Add change details if available
                                if 'before_state' in change and 'after_state' in change:
                                    before_lines = len(change['before_state'].splitlines()) if isinstance(change['before_state'], str) else 0
                                    after_lines = len(change['after_state'].splitlines()) if isinstance(change['after_state'], str) else 0
                                    fixes.append(f"  - Lines before: {before_lines}, after: {after_lines}")
                            else:
                                fixes.append(f"- File change {i+1}")
                    
                    continue
            
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
            # Handle both DiagnosticRun objects and dictionaries
            if isinstance(diagnostic, DiagnosticRun):
                tool = diagnostic.tool
                issues_count = len(diagnostic.issues_found)
            elif isinstance(diagnostic, dict):
                tool = diagnostic.get('tool', 'Unknown')
                issues_count = len(diagnostic.get('issues_found', []))
            else:
                continue
            
            if tool not in diagnostics_by_tool:
                diagnostics_by_tool[tool] = 0
                issues_by_tool[tool] = 0
                
            diagnostics_by_tool[tool] += 1
            issues_by_tool[tool] += issues_count
            
        # Count fixes and success rate
        total_fixes = len(self.session.fixes)
        successful_fixes = 0
        for fix in self.session.fixes:
            # Handle both AppliedFix objects and dictionaries
            if isinstance(fix, AppliedFix):
                if fix.successful:
                    successful_fixes += 1
            elif isinstance(fix, dict):
                if fix.get('successful', False):
                    successful_fixes += 1
        
        success_rate = (successful_fixes / total_fixes * 100) if total_fixes > 0 else 0
        
        # Generate the metrics section
        metrics = [
            "## Metrics\n",
            "### Session Metrics",
            f"- **Total Duration:** {int(duration_seconds)} seconds",
            f"- **Issues per Diagnostic:** {sum(issues_by_tool.values()) / sum(diagnostics_by_tool.values()):.2f}" if sum(diagnostics_by_tool.values()) > 0 else "- **Issues per Diagnostic:** N/A",
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

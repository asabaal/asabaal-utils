"""
HTML Report Generation Module

Generates comprehensive HTML reports with interactive visualizations
for PR analysis results.
"""

import json
from typing import Dict, Any
from pathlib import Path


class HTMLGenerator:
    """Generates HTML reports from PR analysis data."""
    
    def __init__(self):
        """Initialize HTML generator."""
        pass
    
    def generate_report_html(self, report_data: Dict[str, Any]) -> str:
        """Generate complete HTML report from analysis data."""
        
        # Extract key data
        pr_analysis = report_data['pr_analysis']
        classified_files = report_data['classified_files'] 
        category_summary = report_data['category_summary']
        impact_analysis = report_data.get('impact_analysis', {})
        executive_summary = report_data.get('executive_summary', {})
        visualizations = report_data.get('visualizations', {})
        
        # Generate HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR Analysis: {pr_analysis.from_branch} → {pr_analysis.to_branch}</title>
    
    <!-- External Libraries -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <style>
        {self._generate_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header(pr_analysis)}
        {self._generate_executive_summary(executive_summary)}
        {self._generate_merge_readiness_section(report_data.get('quality_analysis', {}))}
        {self._generate_impact_dashboard(impact_analysis)}
        {self._generate_quality_issues_section(report_data.get('quality_analysis', {}))}
        {self._generate_category_overview(category_summary)}
        {self._generate_file_explorer(classified_files, pr_analysis)}
        {self._generate_visualizations_section(visualizations)}
        {self._generate_detailed_analysis(pr_analysis, classified_files)}
        {self._generate_footer(report_data.get('report_metadata', {}))}
    </div>
    
    <script>
        // Category file data for interactive exploration
        window.categoryFileData = {self._generate_category_file_data(classified_files, pr_analysis)};
        
        {self._generate_javascript(visualizations)}
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_css(self) -> str:
        """Generate CSS styles for the report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #e2e8f0;
            background: #0f172a;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .section {
            background: #1e293b;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid #334155;
        }
        
        .section h2 {
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #f1f5f9;
            border-bottom: 2px solid #334155;
            padding-bottom: 10px;
        }
        
        .section h3 {
            color: #cbd5e1;
            margin-bottom: 15px;
        }
        
        .section p {
            color: #cbd5e1;
            margin-bottom: 15px;
        }
        
        .section ul {
            color: #cbd5e1;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: #374151;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #60a5fa;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #f1f5f9;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #9ca3af;
            font-size: 0.9rem;
        }
        
        .impact-score {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        
        .impact-high { background: #dc2626; color: #fca5a5; }
        .impact-medium { background: #d97706; color: #fed7aa; }
        .impact-low { background: #059669; color: #86efac; }
        
        .category-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .category-card {
            background: #374151;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #60a5fa;
        }
        
        .category-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .category-icon {
            font-size: 1.5rem;
            margin-right: 10px;
        }
        
        .category-name {
            font-weight: bold;
            color: #f1f5f9;
        }
        
        .category-count {
            background: #60a5fa;
            color: #0f172a;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-left: auto;
            font-weight: bold;
        }
        
        .file-explorer {
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #334155;
            border-radius: 8px;
            background: #1e293b;
        }
        
        .file-item {
            padding: 10px 15px;
            border-bottom: 1px solid #334155;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .file-item:hover {
            background: #374151;
        }
        
        .file-path {
            font-family: 'Monaco', 'Menlo', 'SF Mono', 'Consolas', monospace;
            font-size: 0.9rem;
            color: #cbd5e1;
        }
        
        .change-type {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .change-added { background: #059669; color: #86efac; }
        .change-modified { background: #d97706; color: #fed7aa; }
        .change-deleted { background: #dc2626; color: #fca5a5; }
        
        .chart-container {
            margin: 20px 0;
            min-height: 400px;
            background: #374151;
            border-radius: 8px;
            padding: 10px;
        }
        
        .recommendations {
            background: #1e293b;
            border-left: 4px solid #60a5fa;
            padding: 20px;
            border-radius: 0 8px 8px 0;
            border: 1px solid #334155;
        }
        
        .recommendations h3 {
            color: #f1f5f9;
            margin-bottom: 15px;
        }
        
        .recommendations ul {
            list-style: none;
            padding-left: 0;
        }
        
        .recommendations li {
            margin: 10px 0;
            padding-left: 30px;
            position: relative;
            color: #cbd5e1;
        }
        
        .recommendations li:before {
            content: "💡";
            position: absolute;
            left: 0;
        }
        
        .footer {
            text-align: center;
            color: #6b7280;
            font-size: 0.9rem;
            padding: 30px;
            border-top: 1px solid #334155;
            margin-top: 40px;
        }
        
        /* Scrollbar styling for dark theme */
        .file-explorer::-webkit-scrollbar {
            width: 8px;
        }
        
        .file-explorer::-webkit-scrollbar-track {
            background: #1e293b;
        }
        
        .file-explorer::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 4px;
        }
        
        .file-explorer::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }
        
        /* Modal styles */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .modal-content {
            background: #1e293b;
            border-radius: 12px;
            max-width: 800px;
            max-height: 80vh;
            width: 90%;
            border: 1px solid #334155;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            border-bottom: 1px solid #334155;
        }
        
        .modal-header h2 {
            color: #f1f5f9;
            margin: 0;
            font-size: 1.5rem;
        }
        
        .modal-close {
            background: none;
            border: none;
            color: #9ca3af;
            font-size: 2rem;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-close:hover {
            color: #f1f5f9;
        }
        
        .modal-body {
            padding: 20px 30px;
            max-height: 60vh;
            overflow-y: auto;
        }
        
        .category-stats {
            display: flex;
            gap: 30px;
            margin-bottom: 20px;
            padding: 20px;
            background: #374151;
            border-radius: 8px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            display: block;
            font-size: 1.8rem;
            font-weight: bold;
            color: #f1f5f9;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #9ca3af;
            font-size: 0.9rem;
        }
        
        .category-file-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .category-file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            border-bottom: 1px solid #334155;
            background: #374151;
            margin-bottom: 5px;
            border-radius: 6px;
        }
        
        .category-file-item:hover {
            background: #475569;
        }
        
        .file-info {
            display: flex;
            align-items: center;
            flex: 1;
        }
        
        .file-icon {
            margin-right: 10px;
            font-size: 1.1rem;
        }
        
        .file-name {
            font-family: 'Monaco', 'Menlo', 'SF Mono', 'Consolas', monospace;
            font-size: 0.9rem;
            color: #cbd5e1;
        }
        
        .file-changes {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .line-changes {
            font-family: 'Monaco', 'Menlo', 'SF Mono', 'Consolas', monospace;
            font-size: 0.8rem;
            color: #9ca3af;
        }
        
        /* Merge Readiness Styles */
        .merge-readiness-section {
            border-left: 4px solid #60a5fa;
        }
        
        .readiness-overview {
            display: flex;
            align-items: center;
            gap: 30px;
        }
        
        .readiness-score {
            flex-shrink: 0;
        }
        
        .score-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            border: 4px solid;
        }
        
        .score-circle.status-ready { border-color: #059669; background: rgba(5, 150, 105, 0.1); }
        .score-circle.status-review { border-color: #d97706; background: rgba(217, 119, 6, 0.1); }
        .score-circle.status-needs-work { border-color: #dc2626; background: rgba(220, 38, 38, 0.1); }
        .score-circle.status-not-ready { border-color: #dc2626; background: rgba(220, 38, 38, 0.2); }
        
        .score-value {
            font-size: 2.5rem;
            color: #f1f5f9;
        }
        
        .score-label {
            font-size: 0.9rem;
            color: #9ca3af;
        }
        
        .readiness-details {
            flex: 1;
        }
        
        .readiness-status {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .status-icon {
            font-size: 1.5rem;
        }
        
        .status-text {
            font-size: 1.3rem;
            font-weight: bold;
        }
        
        .status-text.status-ready { color: #86efac; }
        .status-text.status-review { color: #fed7aa; }
        .status-text.status-needs-work { color: #fca5a5; }
        .status-text.status-not-ready { color: #fca5a5; }
        
        .readiness-recommendation {
            color: #cbd5e1;
            margin-bottom: 20px;
            font-size: 1.1rem;
        }
        
        .readiness-metrics {
            display: flex;
            gap: 30px;
        }
        
        .readiness-metrics .metric-item {
            text-align: center;
        }
        
        .readiness-metrics .metric-value {
            display: block;
            font-size: 1.5rem;
            font-weight: bold;
            color: #f1f5f9;
        }
        
        .readiness-metrics .metric-label {
            color: #9ca3af;
            font-size: 0.9rem;
        }
        
        /* Quality Issues Styles */
        .quality-issues-section {
            border-left: 4px solid #f59e0b;
        }
        
        .issues-summary {
            margin-bottom: 25px;
            padding: 15px;
            background: #374151;
            border-radius: 8px;
        }
        
        .quality-category {
            margin-bottom: 25px;
        }
        
        .quality-category h3 {
            color: #f1f5f9;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .category-issues {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .quality-issue {
            background: #374151;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid;
        }
        
        .quality-issue.severity-critical { border-left-color: #dc2626; }
        .quality-issue.severity-high { border-left-color: #f59e0b; }
        .quality-issue.severity-medium { border-left-color: #3b82f6; }
        .quality-issue.severity-low { border-left-color: #6b7280; }
        
        .issue-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        
        .issue-severity {
            font-size: 0.9rem;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.1);
        }
        
        .issue-title {
            font-weight: bold;
            color: #f1f5f9;
            font-size: 1.1rem;
        }
        
        .issue-description {
            color: #cbd5e1;
            margin-bottom: 10px;
        }
        
        .issue-files {
            color: #9ca3af;
            font-size: 0.9rem;
            margin-bottom: 10px;
            font-family: 'Monaco', 'Menlo', 'SF Mono', 'Consolas', monospace;
        }
        
        .issue-recommendation {
            color: #cbd5e1;
            font-size: 0.95rem;
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 6px;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .category-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _generate_header(self, pr_analysis) -> str:
        """Generate report header section."""
        return f"""
        <div class="header">
            <h1>🔍 PR Analysis Report</h1>
            <p class="subtitle">{pr_analysis.from_branch} → {pr_analysis.to_branch}</p>
            <p style="margin-top: 10px; opacity: 0.8;">
                📊 {pr_analysis.total_files_changed} files changed • 
                ➕ {pr_analysis.total_lines_added:,} additions • 
                ➖ {pr_analysis.total_lines_removed:,} deletions
            </p>
        </div>
        """
    
    def _generate_executive_summary(self, executive_summary: Dict[str, Any]) -> str:
        """Generate executive summary section."""
        if not executive_summary:
            return ""
        
        key_metrics = executive_summary.get('key_metrics', {})
        
        return f"""
        <div class="section">
            <h2>📋 Executive Summary</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{executive_summary.get('scale', 'Unknown')}</div>
                    <div class="metric-label">PR Scale</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{executive_summary.get('impact_score', 0)}/10</div>
                    <div class="metric-label">Impact Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{executive_summary.get('risk_level', 'Unknown')}</div>
                    <div class="metric-label">Risk Level</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{executive_summary.get('transformation_type', 'Mixed')}</div>
                    <div class="metric-label">Transformation Type</div>
                </div>
            </div>
            
            <h3>🎯 Primary Changes</h3>
            <p style="margin-bottom: 20px;">This PR represents a <strong>{executive_summary.get('transformation_type', 'development update')}</strong> 
            with <strong>{executive_summary.get('scale', 'standard').lower()}</strong> scope affecting 
            <strong>{key_metrics.get('files_changed', 0)} files</strong>.</p>
        </div>
        """
    
    def _generate_impact_dashboard(self, impact_analysis: Dict[str, Any]) -> str:
        """Generate impact analysis dashboard."""
        if not impact_analysis:
            return ""
        
        breakdown = impact_analysis.get('impact_breakdown', {})
        recommendations = impact_analysis.get('recommendations', [])
        
        dashboard_html = f"""
        <div class="section">
            <h2>📈 Impact Analysis</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{impact_analysis.get('overall_score', 0)}/10</div>
                    <div class="metric-label">Overall Impact Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{impact_analysis.get('business_impact', 0)}/10</div>
                    <div class="metric-label">Business Impact</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{impact_analysis.get('technical_impact', 0)}/10</div>
                    <div class="metric-label">Technical Impact</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{impact_analysis.get('risk_score', 0)}/10</div>
                    <div class="metric-label">Risk Score</div>
                </div>
            </div>
        """
        
        if recommendations:
            dashboard_html += f"""
            <div class="recommendations">
                <h3>💡 Recommendations</h3>
                <ul>
                    {''.join(f'<li>{rec}</li>' for rec in recommendations)}
                </ul>
            </div>
            """
        
        dashboard_html += "</div>"
        return dashboard_html
    
    def _generate_category_overview(self, category_summary: Dict[str, Any]) -> str:
        """Generate category overview section."""
        if not category_summary:
            return ""
        
        categories_html = ""
        for category, info in category_summary.items():
            if info['count'] > 0:  # Only show categories with files
                categories_html += f"""
                <div class="category-card">
                    <div class="category-header">
                        <span class="category-icon">{info.get('icon', '📁')}</span>
                        <span class="category-name">{category.replace('_', ' ').title()}</span>
                        <span class="category-count">{info['count']}</span>
                    </div>
                    <p style="color: #718096; font-size: 0.9rem;">{info.get('description', '')}</p>
                </div>
                """
        
        return f"""
        <div class="section">
            <h2>📂 File Categories</h2>
            <div class="category-grid">
                {categories_html}
            </div>
        </div>
        """
    
    def _generate_file_explorer(self, classified_files, pr_analysis) -> str:
        """Generate file explorer section."""
        files_html = ""
        
        # Create a mapping of file paths to change info
        change_info = {fc.file_path: fc for fc in pr_analysis.file_changes}
        
        for classified_file in classified_files:
            file_change = change_info.get(classified_file.file_path)
            if not file_change:
                continue
                
            change_type_class = {
                'A': 'change-added',
                'M': 'change-modified', 
                'D': 'change-deleted',
                'R': 'change-modified'
            }.get(file_change.change_type, 'change-modified')
            
            change_type_text = {
                'A': 'Added',
                'M': 'Modified',
                'D': 'Deleted', 
                'R': 'Renamed'
            }.get(file_change.change_type, 'Changed')
            
            files_html += f"""
            <div class="file-item">
                <div>
                    <span class="category-icon">{classified_file.icon}</span>
                    <span class="file-path">{classified_file.file_path}</span>
                </div>
                <div>
                    <span class="change-type {change_type_class}">{change_type_text}</span>
                    <span style="margin-left: 10px; color: #718096; font-size: 0.8rem;">
                        +{file_change.lines_added} -{file_change.lines_removed}
                    </span>
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>📄 File Changes</h2>
            <div class="file-explorer">
                {files_html}
            </div>
        </div>
        """
    
    def _generate_visualizations_section(self, visualizations: Dict[str, Any]) -> str:
        """Generate visualizations section with charts."""
        return f"""
        <div class="section">
            <h2>📊 Visualizations</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                <div>
                    <h3>Category Distribution</h3>
                    <div id="categoryChart" class="chart-container"></div>
                </div>
                <div>
                    <h3>Lines of Code Changes</h3>
                    <div id="linesChart" class="chart-container"></div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                <div>
                    <h3>Change Types</h3>
                    <div id="changeTypesChart" class="chart-container"></div>
                </div>
                <div>
                    <h3>File Size Distribution</h3>
                    <div id="fileSizeChart" class="chart-container"></div>
                </div>
            </div>
        </div>
        """
    
    def _generate_detailed_analysis(self, pr_analysis, classified_files) -> str:
        """Generate detailed analysis section."""
        return f"""
        <div class="section">
            <h2>🔬 Detailed Analysis</h2>
            
            <h3>📈 Change Statistics</h3>
            <ul style="margin-bottom: 20px;">
                <li><strong>Total Files Changed:</strong> {pr_analysis.total_files_changed}</li>
                <li><strong>Lines Added:</strong> {pr_analysis.total_lines_added:,}</li>
                <li><strong>Lines Removed:</strong> {pr_analysis.total_lines_removed:,}</li>
                <li><strong>Net Change:</strong> {pr_analysis.total_lines_added - pr_analysis.total_lines_removed:+,}</li>
            </ul>
            
            <h3>📝 Commit Messages</h3>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace;">
                {'<br>'.join(pr_analysis.commit_messages[:10]) if pr_analysis.commit_messages else 'No commit messages available'}
            </div>
        </div>
        """
    
    def _generate_footer(self, metadata: Dict[str, Any]) -> str:
        """Generate report footer."""
        generated_at = metadata.get('generated_at', 'Unknown')
        return f"""
        <div class="footer">
            <p>🤖 Generated by PR Analyzer v{metadata.get('generator_version', '1.0.0')} at {generated_at}</p>
            <p>Made with ❤️ by Asabaal Ventures</p>
        </div>
        """
    
    def _generate_javascript(self, visualizations: Dict[str, Any]) -> str:
        """Generate JavaScript for interactive charts."""
        return f"""
        // Initialize charts when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initializeCharts();
            initializeCategoryExploration();
        }});
        
        function initializeCharts() {{
            {self._generate_category_chart_js(visualizations)}
            {self._generate_lines_chart_js(visualizations)}
            {self._generate_change_types_chart_js(visualizations)}
            {self._generate_file_size_chart_js(visualizations)}
        }}
        
        function initializeCategoryExploration() {{
            // Add click handlers to category cards
            document.querySelectorAll('.category-card').forEach(card => {{
                card.style.cursor = 'pointer';
                card.addEventListener('click', function() {{
                    const categoryName = this.querySelector('.category-name').textContent;
                    showCategoryDetails(categoryName.toUpperCase().replace(/ /g, '_'));
                }});
            }});
        }}
        
        function showCategoryDetails(category) {{
            // Create modal for category details
            const modal = createModal();
            const categoryFiles = getCategoryFiles(category);
            
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>${{category.replace(/_/g, ' ')}} Files</h2>
                        <button class="modal-close" onclick="closeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="category-details">
                            <div class="category-stats">
                                <div class="stat-item">
                                    <span class="stat-value">${{categoryFiles.length}}</span>
                                    <span class="stat-label">Files</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">${{categoryFiles.reduce((sum, f) => sum + f.linesAdded, 0)}}</span>
                                    <span class="stat-label">Lines Added</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">${{categoryFiles.reduce((sum, f) => sum + f.linesRemoved, 0)}}</span>
                                    <span class="stat-label">Lines Removed</span>
                                </div>
                            </div>
                            <div class="category-file-list">
                                ${{categoryFiles.map(file => `
                                    <div class="category-file-item">
                                        <div class="file-info">
                                            <span class="file-icon">${{file.icon}}</span>
                                            <span class="file-name">${{file.path}}</span>
                                        </div>
                                        <div class="file-changes">
                                            <span class="change-type ${{getChangeTypeClass(file.changeType)}}">${{file.changeType}}</span>
                                            <span class="line-changes">+${{file.linesAdded}} -${{file.linesRemoved}}</span>
                                        </div>
                                    </div>
                                `).join('')}}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            modal.style.display = 'flex';
        }}
        
        function createModal() {{
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            `;
            return modal;
        }}
        
        function closeModal() {{
            const modal = document.querySelector('.modal-overlay');
            if (modal) {{
                modal.remove();
            }}
        }}
        
        function getCategoryFiles(category) {{
            // This would be populated with actual file data
            return window.categoryFileData[category] || [];
        }}
        
        function getChangeTypeClass(changeType) {{
            switch(changeType) {{
                case 'A': return 'change-added';
                case 'M': return 'change-modified';
                case 'D': return 'change-deleted';
                case 'R': return 'change-modified';
                default: return 'change-modified';
            }}
        }}
        
        // Close modal on outside click
        document.addEventListener('click', function(e) {{
            if (e.target.classList.contains('modal-overlay')) {{
                closeModal();
            }}
        }});
        
        // Close modal on escape key
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeModal();
            }}
        }});
        """
    
    def _generate_category_chart_js(self, visualizations: Dict[str, Any]) -> str:
        """Generate JavaScript for category distribution chart."""
        category_data = visualizations.get('category_distribution', {})
        if not category_data:
            return ""
        
        return f"""
        // Category Distribution Chart
        var categoryData = [{{
            values: {json.dumps(category_data.get('data', []))},
            labels: {json.dumps(category_data.get('labels', []))},
            type: 'pie',
            marker: {{
                colors: {json.dumps(category_data.get('colors', []))}
            }},
            textfont: {{
                color: '#e2e8f0'
            }}
        }}];
        
        var categoryLayout = {{
            title: '',
            showlegend: true,
            margin: {{ t: 20, b: 20, l: 20, r: 20 }},
            paper_bgcolor: '#374151',
            plot_bgcolor: '#374151',
            font: {{
                color: '#e2e8f0'
            }},
            legend: {{
                font: {{
                    color: '#e2e8f0'
                }}
            }}
        }};
        
        Plotly.newPlot('categoryChart', categoryData, categoryLayout, {{responsive: true}});
        
        // Add click handler for category exploration
        document.getElementById('categoryChart').on('plotly_click', function(data) {{
            var category = data.points[0].label;
            showCategoryDetails(category);
        }});
        """
    
    def _generate_lines_chart_js(self, visualizations: Dict[str, Any]) -> str:
        """Generate JavaScript for lines changed chart."""
        lines_data = visualizations.get('lines_changed_data', {})
        if not lines_data:
            return ""
        
        return f"""
        // Lines Changed Chart
        var linesData = [{{
            x: ['Added', 'Removed', 'Net Change'],
            y: [{lines_data.get('added', 0)}, {lines_data.get('removed', 0)}, {lines_data.get('net', 0)}],
            type: 'bar',
            marker: {{
                color: ['#22c55e', '#ef4444', '#3b82f6']
            }}
        }}];
        
        var linesLayout = {{
            title: '',
            margin: {{ t: 20, b: 40, l: 50, r: 20 }},
            paper_bgcolor: '#374151',
            plot_bgcolor: '#374151',
            font: {{
                color: '#e2e8f0'
            }},
            xaxis: {{
                color: '#e2e8f0',
                gridcolor: '#475569'
            }},
            yaxis: {{
                color: '#e2e8f0',
                gridcolor: '#475569'
            }}
        }};
        
        Plotly.newPlot('linesChart', linesData, linesLayout, {{responsive: true}});
        """
    
    def _generate_change_types_chart_js(self, visualizations: Dict[str, Any]) -> str:
        """Generate JavaScript for change types chart."""
        change_data = visualizations.get('change_type_distribution', {})
        if not change_data:
            return ""
        
        return f"""
        // Change Types Chart
        var changeTypesData = [{{
            values: {json.dumps(list(change_data.values()))},
            labels: {json.dumps(['Added', 'Modified', 'Deleted', 'Renamed'])},
            type: 'pie',
            marker: {{
                colors: ['#22c55e', '#f59e0b', '#ef4444', '#8b5cf6']
            }},
            textfont: {{
                color: '#e2e8f0'
            }}
        }}];
        
        var changeTypesLayout = {{
            title: '',
            showlegend: true,
            margin: {{ t: 20, b: 20, l: 20, r: 20 }},
            paper_bgcolor: '#374151',
            plot_bgcolor: '#374151',
            font: {{
                color: '#e2e8f0'
            }},
            legend: {{
                font: {{
                    color: '#e2e8f0'
                }}
            }}
        }};
        
        Plotly.newPlot('changeTypesChart', changeTypesData, changeTypesLayout, {{responsive: true}});
        """
    
    def _generate_file_size_chart_js(self, visualizations: Dict[str, Any]) -> str:
        """Generate JavaScript for file size distribution chart."""
        size_data = visualizations.get('file_size_distribution', {})
        if not size_data:
            return ""
        
        return f"""
        // File Size Distribution Chart
        var fileSizeData = [{{
            x: {json.dumps(list(size_data.keys()))},
            y: {json.dumps(list(size_data.values()))},
            type: 'bar',
            marker: {{
                color: '#6366f1'
            }}
        }}];
        
        var fileSizeLayout = {{
            title: '',
            xaxis: {{ 
                title: 'Change Size Category',
                color: '#e2e8f0',
                gridcolor: '#475569'
            }},
            yaxis: {{ 
                title: 'Number of Files',
                color: '#e2e8f0',
                gridcolor: '#475569'
            }},
            margin: {{ t: 20, b: 60, l: 50, r: 20 }},
            paper_bgcolor: '#374151',
            plot_bgcolor: '#374151',
            font: {{
                color: '#e2e8f0'
            }}
        }};
        
        Plotly.newPlot('fileSizeChart', fileSizeData, fileSizeLayout, {{responsive: true}});
        """
    
    def _generate_category_file_data(self, classified_files, pr_analysis) -> str:
        """Generate JavaScript object with category file data for interactive exploration."""
        # Create a mapping of file paths to change info
        change_info = {fc.file_path: fc for fc in pr_analysis.file_changes}
        
        # Group files by category
        category_data = {}
        for classified_file in classified_files:
            category = classified_file.category
            if category not in category_data:
                category_data[category] = []
            
            file_change = change_info.get(classified_file.file_path)
            if file_change:
                category_data[category].append({
                    'path': classified_file.file_path,
                    'icon': classified_file.icon,
                    'changeType': file_change.change_type,
                    'linesAdded': file_change.lines_added,
                    'linesRemoved': file_change.lines_removed,
                    'description': classified_file.description
                })
        
        return json.dumps(category_data)
    
    def _generate_merge_readiness_section(self, quality_analysis: Dict[str, Any]) -> str:
        """Generate merge readiness assessment section."""
        if not quality_analysis:
            return ""
        
        merge_readiness = quality_analysis.get('merge_readiness', {})
        status = merge_readiness.get('status', 'UNKNOWN')
        score = merge_readiness.get('score', 0)
        recommendation = merge_readiness.get('recommendation', '')
        
        # Determine status styling
        status_class = {
            'READY': 'status-ready',
            'REVIEW_NEEDED': 'status-review',
            'NEEDS_WORK': 'status-needs-work',
            'NOT_READY': 'status-not-ready'
        }.get(status, 'status-unknown')
        
        status_icon = {
            'READY': '✅',
            'REVIEW_NEEDED': '⚠️',
            'NEEDS_WORK': '🔧',
            'NOT_READY': '❌'
        }.get(status, '❓')
        
        return f"""
        <div class="section merge-readiness-section">
            <h2>🚀 Merge Readiness Assessment</h2>
            
            <div class="readiness-overview">
                <div class="readiness-score">
                    <div class="score-circle {status_class}">
                        <div class="score-value">{score}</div>
                        <div class="score-label">/ 100</div>
                    </div>
                </div>
                
                <div class="readiness-details">
                    <div class="readiness-status">
                        <span class="status-icon">{status_icon}</span>
                        <span class="status-text {status_class}">{status.replace('_', ' ').title()}</span>
                    </div>
                    <div class="readiness-recommendation">
                        {recommendation}
                    </div>
                    
                    <div class="readiness-metrics">
                        <div class="metric-item">
                            <span class="metric-value">{merge_readiness.get('blocking_issues', 0)}</span>
                            <span class="metric-label">Blocking Issues</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">{merge_readiness.get('warning_issues', 0)}</span>
                            <span class="metric-label">Warning Issues</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">{merge_readiness.get('info_issues', 0)}</span>
                            <span class="metric-label">Info Issues</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_quality_issues_section(self, quality_analysis: Dict[str, Any]) -> str:
        """Generate quality issues section."""
        if not quality_analysis or not quality_analysis.get('issues'):
            return ""
        
        issues = quality_analysis.get('issues', [])
        issue_summary = quality_analysis.get('issue_summary', {})
        
        # Group issues by category
        issues_by_category = {}
        for issue in issues:
            category = issue.category
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)
        
        issues_html = ""
        for category, category_issues in issues_by_category.items():
            category_icon = {
                'DUPLICATE': '👥',
                'INCOMPLETE': '⚠️',
                'INCONSISTENT': '📏',
                'ABANDONED': '🗑️',
                'MIXED_CONCERNS': '🎯'
            }.get(category, '❓')
            
            issues_html += f"""
            <div class="quality-category">
                <h3>{category_icon} {category.replace('_', ' ').title()}</h3>
                <div class="category-issues">
            """
            
            for issue in category_issues:
                severity_class = f"severity-{issue.severity.lower()}"
                severity_icon = {
                    'CRITICAL': '🚨',
                    'HIGH': '⚠️',
                    'MEDIUM': '💡',
                    'LOW': 'ℹ️'
                }.get(issue.severity, '❓')
                
                affected_files_text = ""
                if len(issue.affected_files) <= 3:
                    affected_files_text = ", ".join(issue.affected_files)
                else:
                    affected_files_text = f"{', '.join(issue.affected_files[:3])} and {len(issue.affected_files) - 3} more"
                
                issues_html += f"""
                <div class="quality-issue {severity_class}">
                    <div class="issue-header">
                        <span class="issue-severity">{severity_icon} {issue.severity}</span>
                        <span class="issue-title">{issue.title}</span>
                    </div>
                    <div class="issue-description">{issue.description}</div>
                    <div class="issue-files">
                        <strong>Affected files:</strong> {affected_files_text}
                    </div>
                    <div class="issue-recommendation">
                        <strong>Recommendation:</strong> {issue.recommendation}
                    </div>
                </div>
                """
            
            issues_html += "</div></div>"
        
        return f"""
        <div class="section quality-issues-section">
            <h2>🔍 Quality Issues</h2>
            <div class="issues-summary">
                <p>Found <strong>{issue_summary.get('total_issues', 0)} quality issues</strong> that should be addressed before merging.</p>
            </div>
            <div class="quality-issues">
                {issues_html}
            </div>
        </div>
        """
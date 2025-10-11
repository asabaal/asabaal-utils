#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Pure deterministic HTML generation - no agentic toolkit needed

class Stage9HTMLGenerator:
    def __init__(self, target_repo_path: str = None, output_dir: str = None):
        # Use current working directory as target repo if not specified
        self.target_repo = Path(target_repo_path) if target_repo_path else Path.cwd()
        
        # Set analyzer root to local output directory if provided, otherwise target repo output directory
        if output_dir:
            self.analyzer_root = Path(output_dir)
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.target_repo / "pr_analysis_output"
            self.analyzer_root = self.output_dir  # Use same directory for consistency
        
        self.output_dir.mkdir(exist_ok=True)
        
        self.debug_dir = self.output_dir / "debug_outputs" / "stage8_agentic"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        self.prompt_data_dir = self.output_dir / "prompt_data"
        self.prompt_data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_analysis_data(self) -> Dict[str, Any]:
        """Load all analysis data from previous stages"""
        print("📊 Loading analysis data...")
        
        analysis_data = {}
        
        # Load Stage 1: Context and file analysis
        stage1_files = self.analyzer_root / "debug_outputs" / "stage1"
        if (stage1_files / "file_analysis_results.json").exists():
            with open(stage1_files / "file_analysis_results.json", 'r') as f:
                analysis_data['file_analysis'] = json.load(f)
                
        # Load Stage 3: Agent responses with detailed findings
        stage3_files = self.analyzer_root / "debug_outputs" / "stage3"
        analysis_data['agent_responses'] = {}
        
        response_files = [
            'duplicate_detection_full_response.txt',
            'merge_readiness_full_response.txt', 
            'pattern_analysis_full_response.txt',
            'quality_assessment_full_response.txt',
            'security_review_full_response.txt'
        ]
        
        for response_file in response_files:
            file_path = stage3_files / response_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    agent_name = response_file.replace('_full_response.txt', '')
                    analysis_data['agent_responses'][agent_name] = f.read()
        
        # Load Stage 6: Final combined results from MAIN output directory
        complete_analysis_file = self.analyzer_root / "complete_pr_analysis.json"
        if complete_analysis_file.exists():
            with open(complete_analysis_file, 'r') as f:
                analysis_data['complete_analysis'] = json.load(f)
                
        # Load markdown report for reference from MAIN output directory
        markdown_file = self.analyzer_root / "PR_ANALYSIS_REPORT.md"
        if markdown_file.exists():
            with open(markdown_file, 'r') as f:
                analysis_data['markdown_report'] = f.read()
        
        # Load Stage 8: File-level merge readiness assessment results from MAIN output directory
        file_assessment_file = self.analyzer_root / "file_assessment_results.json"
        if file_assessment_file.exists():
            with open(file_assessment_file, 'r') as f:
                assessment_data = json.load(f)
                analysis_data['file_assessment'] = assessment_data
                total_files = assessment_data.get('assessment_summary', {}).get('total_files', 0)
                print(f"✅ Loaded Stage 8 file assessment: {total_files} files assessed")
        else:
            print("⚠️  Stage 8 file assessment results not found - using Stage 7 as fallback")
            # Fallback to Stage 7 if Stage 8 not available
            detailed_analysis_file = self.analyzer_root / "detailed_analysis_results.json"
            if detailed_analysis_file.exists():
                with open(detailed_analysis_file, 'r') as f:
                    analysis_data['detailed_analysis'] = json.load(f)
                    print(f"✅ Loaded Stage 7 detailed analysis (fallback): {analysis_data['detailed_analysis']['analysis_summary']['total_files_analyzed']} files analyzed")
        
        # Load Stage 7 summary for reference
        detailed_summary_file = self.analyzer_root / "detailed_analysis_summary.txt"
        if detailed_summary_file.exists():
            with open(detailed_summary_file, 'r') as f:
                analysis_data['detailed_summary'] = f.read()
        
        print(f"✅ Loaded analysis data with {len(analysis_data)} sections")
        return analysis_data
    
    
    def generate_complete_file_data_js(self, file_assessments: list) -> str:
        """Generate complete JavaScript fileData array from assessment data"""
        print(f"🔧 Generating JavaScript for {len(file_assessments)} files...")
        
        js_lines = ["        const fileData = ["]
        
        for i, file_data in enumerate(file_assessments):
            # Convert to JavaScript object format
            js_obj = {
                "file_path": file_data.get('file_path', ''),
                "merge_readiness": file_data.get('merge_readiness', 'unknown'),
                "business_impact_score": file_data.get('business_impact_score', 5),
                "technical_risk_score": file_data.get('technical_risk_score', 5),
                "overall_assessment": file_data.get('overall_assessment', {}),
                "detailed_feedback": file_data.get('detailed_feedback', ''),
                "recommendations": file_data.get('recommendations', [])
            }
            
            # Convert to JSON string with proper indentation
            js_string = json.dumps(js_obj, indent=12)
            
            # Add comma except for last item
            if i < len(file_assessments) - 1:
                js_string += ","
            
            js_lines.append(js_string)
        
        js_lines.append("        ];")
        js_lines.append("")
        js_lines.append("        // Initialize variables after fileData is defined")
        js_lines.append("        let filteredFiles = [...fileData];")
        js_lines.append("        let currentFilter = 'all';")
        js_lines.append("")
        js_lines.append("        // Function to render files into the DOM")
        js_lines.append("        function renderFileTree() {")
        js_lines.append("            const fileTree = document.getElementById('fileTree');")
        js_lines.append("            fileTree.innerHTML = '';")
        js_lines.append("")
        js_lines.append("            filteredFiles.forEach(file => {")
        js_lines.append("                const fileItem = document.createElement('div');")
        js_lines.append("                fileItem.className = `file-item ${file.merge_readiness}`;")
        js_lines.append("")
        js_lines.append("                const statusColor = file.merge_readiness === 'ready' ? '#00ff88' : ")
        js_lines.append("                                   file.merge_readiness === 'conditional' ? '#ffa500' : '#ff6b6b';")
        js_lines.append("")
        js_lines.append("                fileItem.innerHTML = `")
        js_lines.append("                    <div class='file-header'>")
        js_lines.append("                        <div class='file-path'>${file.file_path}</div>")
        js_lines.append("                        <div class='file-status' style='color: ${statusColor}'>${file.merge_readiness.toUpperCase()}</div>")
        js_lines.append("                    </div>")
        js_lines.append("                    <div class='file-details'>")
        js_lines.append("                        <div class='score-grid'>")
        js_lines.append("                            <div class='score-item'>")
        js_lines.append("                                <span class='score-label'>Business Impact:</span>")
        js_lines.append("                                <span class='score-value'>${file.business_impact_score}/10</span>")
        js_lines.append("                            </div>")
        js_lines.append("                            <div class='score-item'>")
        js_lines.append("                                <span class='score-label'>Technical Risk:</span>")
        js_lines.append("                                <span class='score-value'>${file.technical_risk_score}/10</span>")
        js_lines.append("                            </div>")
        js_lines.append("                        </div>")
        js_lines.append("                        <div class='file-purpose'>")
        js_lines.append("                            <strong>Purpose:</strong> ${file.overall_assessment.purpose || 'Not specified'}")
        js_lines.append("                        </div>")
        js_lines.append("                        <div class='file-recommendations'>")
        js_lines.append("                            <strong>Recommendations:</strong>")
        js_lines.append("                            <ul>${file.recommendations.map(rec => `<li>${rec}</li>`).join('')}</ul>")
        js_lines.append("                        </div>")
        js_lines.append("                    </div>")
        js_lines.append("                `;")
        js_lines.append("")
        js_lines.append("                fileTree.appendChild(fileItem);")
        js_lines.append("            });")
        js_lines.append("        }")
        js_lines.append("")
        js_lines.append("        // Function to filter files - replaces any existing filterFiles function")
        js_lines.append("        function filterFiles() {")
        js_lines.append("            const searchTerm = document.getElementById('fileSearch').value.toLowerCase();")
        js_lines.append("            const statusFilter = document.getElementById('statusFilter').value;")
        js_lines.append("")
        js_lines.append("            console.log('Filtering files:', { searchTerm, statusFilter, totalFiles: fileData.length });")
        js_lines.append("")
        js_lines.append("            // Filter the data first")
        js_lines.append("            filteredFiles = fileData.filter(file => {")
        js_lines.append("                const matchesSearch = file.file_path.toLowerCase().includes(searchTerm);")
        js_lines.append("                const matchesStatus = statusFilter === 'all' || file.merge_readiness === statusFilter;")
        js_lines.append("                return matchesSearch && matchesStatus;")
        js_lines.append("            });")
        js_lines.append("")
        js_lines.append("            console.log('Filtered to:', filteredFiles.length, 'files');")
        js_lines.append("")
        js_lines.append("            // Update filter stats")
        js_lines.append("            updateFilterStats();")
        js_lines.append("")
        js_lines.append("            // Re-render the tree")
        js_lines.append("            renderFileTree();")
        js_lines.append("        }")
        js_lines.append("")
        js_lines.append("        function updateFilterStats() {")
        js_lines.append("            const statsEl = document.getElementById('filterStats');")
        js_lines.append("            const total = fileData.length;")
        js_lines.append("            const filtered = filteredFiles.length;")
        js_lines.append("            const ready = filteredFiles.filter(f => f.merge_readiness === 'ready').length;")
        js_lines.append("            const conditional = filteredFiles.filter(f => f.merge_readiness === 'conditional').length;")
        js_lines.append("            const notReady = filteredFiles.filter(f => f.merge_readiness === 'not_ready').length;")
        js_lines.append("")
        js_lines.append("            if (filtered === total) {")
        js_lines.append("                statsEl.innerHTML = `Showing all ${total} files (${ready} ready, ${conditional} conditional, ${notReady} not ready)`;")
        js_lines.append("            } else {")
        js_lines.append("                statsEl.innerHTML = `Showing ${filtered} of ${total} files (${ready} ready, ${conditional} conditional, ${notReady} not ready)`;")
        js_lines.append("            }")
        js_lines.append("        }")
        js_lines.append("")
        js_lines.append("        // Add some additional filtering capabilities")
        js_lines.append("        function clearFilters() {")
        js_lines.append("            document.getElementById('fileSearch').value = '';")
        js_lines.append("            document.getElementById('statusFilter').value = 'all';")
        js_lines.append("            filterFiles();")
        js_lines.append("        }")
        js_lines.append("")
        js_lines.append("        function showOnlyProblems() {")
        js_lines.append("            document.getElementById('statusFilter').value = 'not_ready';")
        js_lines.append("            filterFiles();")
        js_lines.append("        }")
        js_lines.append("")
        js_lines.append("        function showOnlyReady() {")
        js_lines.append("            document.getElementById('statusFilter').value = 'ready';")
        js_lines.append("            filterFiles();")
        js_lines.append("        }")
        js_lines.append("")
        js_lines.append("        // Initial render when page loads")
        js_lines.append("        document.addEventListener('DOMContentLoaded', function() {")
        js_lines.append("            renderFileTree();")
        js_lines.append("            updateFilterStats();")
        js_lines.append("        });")
        
        return "\n".join(js_lines)
    
    def inject_complete_file_data(self, html_template: str, analysis_data: Dict[str, Any]) -> str:
        """Inject complete file data into HTML template"""
        
        print("🔍 Debugging HTML template injection...")
        print(f"🔍 Template contains '// FILE_DATA_INJECTION_POINT': {'// FILE_DATA_INJECTION_POINT' in html_template}")
        print(f"🔍 Template contains 'const fileData': {'const fileData' in html_template}")
        
        # Get file assessments from Stage 8 data
        file_assessment = analysis_data.get('file_assessment', {})
        file_assessments = file_assessment.get('file_assessments', [])
        
        # Fallback to Stage 7 if Stage 8 not available
        if not file_assessments:
            detailed_analysis = analysis_data.get('detailed_analysis', {})
            file_assessments = detailed_analysis.get('file_analyses', [])
            print(f"⚠️  Using Stage 7 fallback data: {len(file_assessments)} files")
        else:
            print(f"✅ Using Stage 8 assessment data: {len(file_assessments)} files")
        
        if not file_assessments:
            print("❌ No file assessment data available")
            return html_template
        
        # Generate complete JavaScript file data
        complete_js = self.generate_complete_file_data_js(file_assessments)
        
        # Replace placeholder with complete data
        if '// FILE_DATA_INJECTION_POINT' in html_template:
            updated_html = html_template.replace('// FILE_DATA_INJECTION_POINT', complete_js)
            print(f"✅ Injected complete file data ({len(file_assessments)} files)")
            return updated_html
        else:
            print("❌ FILE_DATA_INJECTION_POINT placeholder not found in template")
            return html_template
    
    def replace_template_variables(self, html_template: str, analysis_data: Dict[str, Any], called_from_stage10: bool = False) -> str:
        """Replace all template variables with real data"""
        print("🔧 Replacing template variables with real data...")
        
        # Get data from analysis
        complete_analysis = analysis_data.get('complete_analysis', {})
        pr_summary = complete_analysis.get('pr_summary', {})
        overall_assessment = complete_analysis.get('overall_assessment', {})
        file_assessment = analysis_data.get('file_assessment', {})
        assessment_summary = file_assessment.get('assessment_summary', {})
        
        # Branch information
        branch_info = pr_summary.get('branch_info', 'unknown → unknown')
        if ' → ' in branch_info:
            branch_from, branch_to = branch_info.split(' → ')
        else:
            branch_from, branch_to = 'unknown', 'unknown'
        
        # Template variable replacements - only include placeholders that exist in template
        replacements = {
            '{{BRANCH_FROM}}': branch_from,
            '{{BRANCH_TO}}': branch_to,
            '{{TOTAL_FILES}}': str(assessment_summary.get('total_files', pr_summary.get('files_changed', 0))),
            '{{READY_FILES}}': str(assessment_summary.get('ready_files', 0)),
            '{{QUALITY_SCORE}}': str(overall_assessment.get('overall_score', 0)),
            '{{TOTAL_ISSUES}}': str(overall_assessment.get('total_issues', 0)),
            # Content sections
            '{{OVERVIEW_CONTENT}}': self.generate_overview_content(complete_analysis, analysis_data.get('file_assessment', {}), called_from_stage10),
            '{{FILE_ANALYSIS_CONTENT}}': self.generate_enhanced_search_container(),
            '{{QUALITY_ISSUES_CONTENT}}': self.generate_quality_issues_content(complete_analysis), 
            '{{DUPLICATES_CONTENT}}': self.generate_duplicates_content(analysis_data.get('agent_responses', {})),
            '{{RECOMMENDATIONS_CONTENT}}': self.generate_recommendations_content(complete_analysis)
        }
        
        # Apply all replacements
        result = html_template
        replacements_made = 0
        for placeholder, value in replacements.items():
            old_result = result
            result = result.replace(placeholder, value)
            if old_result != result:
                replacements_made += 1
            
        print(f"✅ Made {replacements_made}/{len(replacements)} template variable replacements")
        return result
    
    def generate_overview_content(self, complete_analysis, file_assessment={}, called_from_stage10: bool = False):
        """Generate overview content section"""
        pr_summary = complete_analysis.get('pr_summary', {})
        overall_assessment = complete_analysis.get('overall_assessment', {})
        
        overview_html = f"""
        <div class="overview-section">
            <div class="pr-stats">
                <div class="stat-item">
                    <h4>{pr_summary.get('files_changed', 0)}</h4>
                    <p>Files Changed</p>
                </div>
                <div class="stat-item">
                    <h4>{pr_summary.get('lines_added', 0):,}</h4>
                    <p>Lines Added</p>
                </div>
                <div class="stat-item">
                    <h4>{pr_summary.get('lines_removed', 0):,}</h4>
                    <p>Lines Removed</p>
                </div>
                <div class="stat-item">
                    <h4>{overall_assessment.get('overall_score', 0)}/10</h4>
                    <p>Quality Score</p>
                </div>
            </div>
            <div class="recommendation-box">
                <h4>Recommendation: {overall_assessment.get('recommendation', 'UNKNOWN')}</h4>
                <p>Overall assessment based on code quality, merge readiness, and potential issues.</p>
            </div>
        </div>
        """
        
        # Add feedback history section if called from Stage 10
        if called_from_stage10:
            feedback_history = self._generate_feedback_history_section(file_assessment)
            overview_html += feedback_history
        
        return overview_html
        return overview_html
    
    def _generate_feedback_history_section(self, file_assessment):
        """Generate feedback history section for overview tab"""
        
        # Get feedback history from file assessment data
        feedback_history = file_assessment.get('feedback_history', [])
        
        if not feedback_history:
            return ""
        
        history_html = """
        <div class="feedback-history-section">
            <h3>📋 Feedback History</h3>
            <div class="feedback-timeline">
        """
        
        for entry in reversed(feedback_history):  # Show newest first
            timestamp = entry.get('timestamp', 'Unknown time')
            feedback_summary = entry.get('feedback_summary', 'No summary')
            metrics_changes = entry.get('metrics_changes', {})
            
            # Format timestamp
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = timestamp
            
            history_html += f"""
            <div class="feedback-entry">
                <div class="feedback-header">
                    <span class="feedback-time">{formatted_time}</span>
                    <span class="feedback-summary">{feedback_summary}</span>
                </div>
                <div class="feedback-metrics">
                    <div class="metric-change">
                        <span class="metric-label">Ready Files:</span>
                        <span class="metric-value {'positive' if metrics_changes.get('ready_files_change', 0) > 0 else 'neutral'}">
                            {metrics_changes.get('ready_files_change', 0):+d}
                        </span>
                    </div>
                    <div class="metric-change">
                        <span class="metric-label">Confidence:</span>
                        <span class="metric-value {'positive' if metrics_changes.get('confidence_change', 0) > 0 else 'neutral'}">
                            {metrics_changes.get('confidence_change', 0):+.1%}
                        </span>
                    </div>
                    <div class="metric-change">
                        <span class="metric-label">Quality Score:</span>
                        <span class="metric-value {'positive' if metrics_changes.get('quality_score_change', 0) > 0 else 'neutral'}">
                            {metrics_changes.get('quality_score_change', 0):+.1f}
                        </span>
                    </div>
                    <div class="metric-change">
                        <span class="metric-label">Issues:</span>
                        <span class="metric-value {'positive' if metrics_changes.get('not_ready_files_change', 0) < 0 else 'neutral'}">
                            {entry.get('quality_issues_count', 0)} total
                        </span>
                    </div>
                </div>
            </div>
            """
        
        history_html += """
            </div>
        </div>
        
        <style>
        .feedback-history-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .feedback-history-section h3 {
            color: #00ff88;
            margin-bottom: 15px;
        }
        
        .feedback-timeline {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .feedback-entry {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 15px;
            border-left: 4px solid #00ff88;
        }
        
        .feedback-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .feedback-time {
            color: #888;
            font-size: 0.9rem;
        }
        
        .feedback-summary {
            color: #e0e0e0;
            font-weight: bold;
        }
        
        .feedback-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }
        
        .metric-change {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .metric-label {
            color: #888;
            font-size: 0.9rem;
        }
        
        .metric-value.positive {
            color: #00ff88;
        }
        
        .metric-value.negative {
            color: #ff4444;
        }
        
        .metric-value.neutral {
            color: #e0e0e0;
        }
        </style>
        """
        
        return history_html
    
    def generate_quality_issues_content(self, complete_analysis):
        """Generate quality issues content section"""
        quality_issues = complete_analysis.get('quality_issues', [])
        
        if not quality_issues:
            return "<div class='no-issues'><p>No quality issues identified.</p></div>"
        
        issues_html = "<div class='quality-issues-list'>"
        
        # Group issues by priority
        priority_groups = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for issue in quality_issues:
            priority = issue.get('priority', 'LOW')
            priority_groups[priority].append(issue)
        
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            issues = priority_groups[priority]
            if issues:
                issues_html += f"<h4 class='priority-{priority.lower()}'>{priority} Priority ({len(issues)} issues)</h4>"
                for issue in issues:
                    issues_html += f"""
                    <div class='issue-item priority-{priority.lower()}'>
                        <h5>{issue.get('title', 'Unknown Issue')}</h5>
                        <p><strong>Impact:</strong> {issue.get('business_impact_score', 0)}/10</p>
                        <p><strong>Files:</strong> {issue.get('files_count', 0)}</p>
                        <p><strong>Recommendation:</strong> {issue.get('recommendation', 'No recommendation')}</p>
                    </div>
                    """
        
        issues_html += "</div>"
        return issues_html
    
    def generate_duplicates_content(self, agent_responses):
        """Generate duplicates detection content section"""
        duplicate_response = agent_responses.get('duplicate_detection', '')
        
        if not duplicate_response:
            return "<div class='duplicate-item'><h3>No Duplicates Found</h3><p>No duplicate analysis available.</p></div>"
        
        # Parse the response into structured sections
        sections = self._parse_duplicate_response(duplicate_response)
        
        duplicates_html = ""
        for section in sections:
            duplicates_html += f"""
            <div class='duplicate-item'>
                <h3>{section['title']}</h3>
                <div class='duplicate-details'>
                    {section['content']}
                </div>
            </div>
            """
        
        return duplicates_html
    
    def _parse_duplicate_response(self, response_text):
        """Parse duplicate detection response into structured sections"""
        sections = []
        
        # Split by major sections (look for patterns like ## or ### or numbered sections)
        lines = response_text.split('\n')
        current_section = {'title': 'Duplicate Analysis Summary', 'content': ''}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a header line
            is_numbered = any(line.startswith(str(i) + '.') for i in range(1, 10))
            if (line.startswith('##') or line.startswith('###') or 
                (line.startswith('**') and line.endswith('**')) or
                is_numbered):
                
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                title = line.replace('#', '').replace('**', '').strip()
                if any(title.startswith(str(i) + '.') for i in range(1, 10)):
                    title = title.split('.', 1)[1].strip() if '.' in title else title
                    
                current_section = {'title': title[:100], 'content': ''}
            else:
                # Add to current section content
                if line:
                    current_section['content'] += f"<p>{line}</p>\n"
        
        # Don't forget the last section
        if current_section['content'].strip():
            sections.append(current_section)
        
        # If no sections were found, create a single section with the first part of the response
        if not sections:
            sections = [{
                'title': 'Duplicate Detection Results',
                'content': f"<p>{response_text[:800]}{'...' if len(response_text) > 800 else ''}</p>"
            }]
        
        return sections[:5]  # Limit to 5 sections to avoid too much content
    
    def generate_recommendations_content(self, complete_analysis):
        """Generate recommendations content section"""
        recommendations = complete_analysis.get('recommendations', [])
        
        if not recommendations:
            return "<div class='no-recommendations'><p>No specific recommendations available.</p></div>"
        
        rec_html = "<div class='recommendations-list'>"
        for i, rec in enumerate(recommendations, 1):
            rec_html += f"""
            <div class='recommendation-item'>
                <h5>{i}. Recommendation</h5>
                <p>{rec}</p>
            </div>
            """
        rec_html += "</div>"
        return rec_html
    
    def generate_enhanced_search_container(self):
        """Generate enhanced search container with quick filter buttons"""
        return """
        <div class="search-container">
            <input type="text" class="search-input" id="fileSearch" placeholder="Search files..." onkeyup="filterFiles()">
            <select class="filter-select" id="statusFilter" onchange="filterFiles()">
                <option value="all">All Files</option>
                <option value="ready">Ready</option>
                <option value="conditional">Conditional</option>
                <option value="not_ready">Not Ready</option>
            </select>
        </div>
        <div class="quick-filters">
            <button class="quick-filter-btn" onclick="clearFilters()">Show All</button>
            <button class="quick-filter-btn" onclick="showOnlyProblems()">Problems Only</button>
            <button class="quick-filter-btn" onclick="showOnlyReady()">Ready Files</button>
        </div>
        <div class="filter-stats" id="filterStats">
            Showing all files
        </div>
        <!-- Files will be rendered here by JavaScript -->
        """
    
    def save_html_report(self, html_content: str) -> Path:
        """Save generated HTML report"""
        
        # Check if response contains HTML at all
        if not any(tag in html_content.lower() for tag in ['<html', '<div', '<body', '<!doctype']):
            print(f"❌ Response doesn't contain HTML content. Response preview: {html_content[:200]}...")
            # Save raw response for debugging
            debug_file = self.debug_dir / "invalid_html_response.txt"
            with open(debug_file, 'w') as f:
                f.write(html_content)
            print(f"💾 Saved invalid response for debugging: {debug_file}")
            raise Exception("Agent response doesn't contain valid HTML content")
        
        # Extract just the HTML if there's extra text
        html_start = html_content.find('<!DOCTYPE html>')
        if html_start == -1:
            html_start = html_content.find('<html>')
        if html_start == -1:
            # Look for any HTML-like content
            html_start = html_content.find('<')
            
        if html_start > 0:
            html_content = html_content[html_start:]
            
        html_end = html_content.rfind('</html>')
        if html_end != -1:
            html_content = html_content[:html_end + 7]
        
        # Save to target repository output directory
        html_file = self.output_dir / "pr_analysis_interactive.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        file_size = html_file.stat().st_size
        print(f"💾 Saved interactive HTML report: {html_file} ({file_size:,} bytes)")
        
        return html_file
    
    
    def _generate_standard_html(self, analysis_data: Dict[str, Any], called_from_stage10: bool = False) -> Path:
        """Generate HTML using deterministic approach - pure Python template replacement"""
        
        print("🔄 Using deterministic approach: Python template replacement with complete file data...")
        
        # Step 1: Load working template directly  
        repo_root = Path(__file__).parent.parent.parent.parent  # Go up to asabaal-utils root
        template_file = repo_root / "templates" / "working_html_template.html"
        if not template_file.exists():
            raise Exception(f"Working HTML template not found: {template_file}")
        
        with open(template_file, 'r') as f:
            html_template = f.read()
        print(f"✅ Loaded working HTML template: {template_file}")
        
        # Step 2: Replace all template variables with real data
        complete_html = self.replace_template_variables(html_template, analysis_data, called_from_stage10)
        
        # Step 3: Inject complete file data
        complete_html = self.inject_complete_file_data(complete_html, analysis_data)
        
        # Step 4: Save final HTML
        return self.save_html_report(complete_html)
    
    def run_stage9_html_generation(self):
        """Run complete Stage 9 HTML report generation"""
        print("=" * 80)
        print("🚀 STAGE 9: HTML REPORT GENERATION")
        print("=" * 80)
        
        try:
            # Step 1: Load all analysis data
            analysis_data = self.load_analysis_data()
            
            # Step 2: Determine processing approach based on dataset size
            # First check Stage 8 file assessment results
            file_assessment = analysis_data.get('file_assessment', {})
            file_count = len(file_assessment.get('file_assessments', []))
            
            # Fallback to Stage 7 if Stage 8 not available
            if file_count == 0:
                detailed_analysis = analysis_data.get('detailed_analysis', {})
                file_count = len(detailed_analysis.get('file_analyses', []))
            
            # Use deterministic template approach  
            print(f"📊 Dataset size: {file_count} files - using deterministic template approach")
            html_file = self._generate_standard_html(analysis_data)
            
            # Step 5: Validation
            if html_file.exists() and html_file.stat().st_size > 10000:  # At least 10KB
                print("✅ STAGE 9: SUCCESS")
                print(f"📊 Generated interactive HTML report: {html_file}")
                print(f"🔗 Open in browser: file://{html_file.absolute()}")
                return True
            else:
                print("❌ STAGE 9: FAILED - HTML file too small or missing")
                return False
                
        except Exception as e:
            print(f"❌ STAGE 9: FAILED with error: {e}")
            return False

def main():
    generator = Stage9HTMLGenerator()
    success = generator.run_stage9_html_generation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
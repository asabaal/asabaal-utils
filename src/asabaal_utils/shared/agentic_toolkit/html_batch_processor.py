#!/usr/bin/env python3
"""
HTML Batch Processor - Specialized processor for generating HTML from large datasets

Uses the Agentic Batch Processing Toolkit to handle large file analysis datasets
and generate complete HTML visualizations without being limited by agent context windows.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from .batch_processor import BatchProcessor, BatchProcessingConfig


class HTMLBatchProcessor(BatchProcessor):
    """
    Specialized batch processor for HTML generation from analysis data.
    
    Handles large file analysis datasets by:
    1. Processing files in manageable batches
    2. Generating HTML sections for each batch  
    3. Combining into complete interactive dashboard
    4. Verifying all files are included
    """
    
    def __init__(self, 
                 output_dir: str,
                 html_template_path: str,
                 instructions_path: str,
                 config: Optional[BatchProcessingConfig] = None):
        
        super().__init__(output_dir, config)
        
        self.html_template_path = Path(html_template_path)
        self.instructions_path = Path(instructions_path)
        
        # Load HTML template and instructions
        self.html_template = self._load_html_template()
        self.instructions = self._load_instructions()
    
    def _load_html_template(self) -> str:
        """Load HTML template if it exists"""
        if self.html_template_path.exists():
            with open(self.html_template_path, 'r') as f:
                return f.read()
        return ""
    
    def _load_instructions(self) -> str:
        """Load processing instructions"""
        if self.instructions_path.exists():
            with open(self.instructions_path, 'r') as f:
                return f.read()
        return "Generate HTML for the provided data."
    
    def process_batch(self, batch_items: List[Dict], context: Dict[str, Any]) -> List[str]:
        """
        Process a batch of Stage 7 analysis results into HTML sections.
        
        Args:
            batch_items: List of Stage 7 analysis result objects (not raw files!)
            context: Contains template, instructions, and previous HTML sections
            
        Returns:
            List of HTML section strings
        """
        
        # Verify we're processing analysis results, not raw files
        processing_mode = context.get('processing_mode', 'unknown')
        if processing_mode != 'analysis_results':
            if self.config.debug_mode:
                print("⚠️  Warning: Expected analysis results but processing mode not set")
        
        # Create batch-specific prompt for analysis results
        prompt = self._create_html_batch_prompt_for_analysis(batch_items, context)
        
        try:
            # Call agent to generate HTML sections
            response = self.call_agent(prompt)
            
            # Parse response into HTML sections
            html_sections = self._parse_html_response(response, batch_items)
            
            # For single-pass processing of many items, we return one section but it represents all items
            if len(batch_items) > 50 and len(html_sections) == 1:
                # Store metadata about how many items this section represents
                self._single_pass_item_count = len(batch_items)
            
            if self.config.debug_mode:
                if len(batch_items) > 50 and len(html_sections) == 1:
                    print(f"✅ Generated complete HTML for {len(batch_items)} analysis results (single-pass)")
                else:
                    print(f"✅ Generated HTML for {len(html_sections)} analysis results")
            
            return html_sections
            
        except Exception as e:
            error_msg = str(e)
            if self.config.debug_mode:
                print(f"❌ HTML batch generation failed: {error_msg}")
            
            return []
    
    def process_single_item(self, item: Dict, context: Dict[str, Any]) -> Optional[str]:
        """
        Process a single Stage 7 analysis result into HTML.
        
        Args:
            item: Single Stage 7 analysis result object
            context: Processing context
            
        Returns:
            HTML string for this analysis result or None if failed
        """
        
        try:
            prompt = self._create_single_analysis_html_prompt(item, context)
            response = self.call_agent(prompt)
            
            html_section = self._parse_single_html_response(response, item)
            
            if self.config.debug_mode and html_section:
                print(f"✅ Generated HTML for analysis: {item.get('file_path', 'unknown')}")
            
            return html_section
            
        except Exception as e:
            if self.config.debug_mode:
                print(f"❌ Single analysis HTML generation failed: {e}")
            return None
    
    def get_item_identifier(self, item: Dict) -> str:
        """Get unique identifier for a Stage 7 analysis result"""
        return item.get('file_path', str(hash(str(item))))
    
    def combine_results(self, all_html_sections: List[str]) -> Dict[str, Any]:
        """
        Combine all HTML sections into complete dashboard.
        
        Args:
            all_html_sections: List of HTML section strings
            
        Returns:
            Complete HTML dashboard data
        """
        
        # Combine all HTML sections
        combined_html_content = "\n".join(all_html_sections)
        
        # For single-pass processing, the HTML content is already complete
        if len(all_html_sections) == 1 and len(combined_html_content) > 10000:
            # This looks like a complete HTML document from single-pass processing
            if self.config.debug_mode:
                print(f"🔍 Debug: Using complete HTML from single-pass (length: {len(combined_html_content)})")
                print(f"🔍 Debug: Content starts with: {combined_html_content[:200]}...")
            complete_html = combined_html_content
        else:
            # Build dashboard from individual sections
            if self.config.debug_mode:
                print(f"🔍 Debug: Building dashboard from {len(all_html_sections)} sections")
                print(f"🔍 Debug: Combined length: {len(combined_html_content)}")
            complete_html = self._build_complete_dashboard(combined_html_content)
        
        # Determine actual item count - for single-pass, use stored count
        actual_item_count = getattr(self, '_single_pass_item_count', len(all_html_sections))
        
        return {
            "complete_html": complete_html,
            "section_count": len(all_html_sections),
            "actual_item_count": actual_item_count,  # True number of items processed
            "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_sections": len(all_html_sections)
        }
    
    def _create_html_batch_prompt(self, batch_items: List[Dict], context: Dict[str, Any]) -> str:
        """DEPRECATED: Use _create_html_batch_prompt_for_analysis instead"""
        
        if self.config.debug_mode:
            print("⚠️  WARNING: Using deprecated _create_html_batch_prompt - should use analysis results")
        
        # Check if these look like analysis results or raw files
        first_item = batch_items[0] if batch_items else {}
        if 'merge_readiness' in first_item and 'overall_assessment' in first_item:
            # These are analysis results, redirect to correct method
            return self._create_html_batch_prompt_for_analysis(batch_items, context)
        
        # Legacy behavior for raw files (deprecated)
        file_list = "\n".join([f"- {item.get('file_path', item.get('path', 'unknown'))}" for item in batch_items])
        
        batch_data = {
            "files": batch_items,
            "batch_size": len(batch_items),
            "context": context.get("previous_sections_count", 0)
        }
        
        # Save batch data for agent to read
        batch_file = self.output_dir / f"legacy_batch_data_{int(time.time())}.json"
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        prompt = f"""You are generating HTML file tree sections for an interactive dashboard.

{self.instructions}

BATCH DATA: Read from {batch_file}

FILES IN THIS BATCH ({len(batch_items)}):
{file_list}

REQUIREMENTS:
1. Generate HTML sections for EVERY file in the batch
2. Use the file tree structure specified in instructions
3. Include all file analysis data (purpose, business impact, risk assessment)
4. Return ONLY the HTML sections (no explanations)
5. Each file should be a complete <div class="file-item"> section

Return the HTML sections for all {len(batch_items)} files."""

        return prompt
    
    def _create_single_file_html_prompt(self, item: Dict, context: Dict[str, Any]) -> str:
        """DEPRECATED: Use _create_single_analysis_html_prompt instead"""
        
        if self.config.debug_mode:
            print("⚠️  WARNING: Using deprecated _create_single_file_html_prompt - should use analysis results")
        
        # Check if this looks like an analysis result
        if 'merge_readiness' in item and 'overall_assessment' in item:
            return self._create_single_analysis_html_prompt(item, context)
        
        # Legacy behavior for raw files (deprecated)
        file_path = item.get('file_path', item.get('path', 'unknown'))
        
        prompt = f"""Generate HTML section for a single file that was missed in batch processing.

{self.instructions}

FILE: {file_path}
DATA: {json.dumps(item, indent=2)}

Return ONLY the HTML section for this file (complete <div class="file-item"> structure)."""

        return prompt
    
    def _parse_html_response(self, response: str, batch_items: List[Dict]) -> List[str]:
        """Parse agent response into individual HTML sections"""
        
        # For single-pass processing of many items, return the whole response as one section
        # The agent generates a complete HTML structure, not individual sections
        if len(batch_items) > 50:  # Large single-pass processing
            if response.strip():
                if self.config.debug_mode:
                    print(f"🔍 Debug: Single-pass response length: {len(response)} chars")
                    print(f"🔍 Debug: Response starts with: {response[:100]}...")
                return [response]  # Return entire response as single section
            else:
                return []
        
        # For smaller batches, try to parse individual file-item divs
        sections = []
        
        # Split by file-item divs (this is a simple approach)
        if '<div class="file-item"' in response:
            parts = response.split('<div class="file-item"')
            for i, part in enumerate(parts[1:], 1):  # Skip first empty part
                # Find the closing div (simple approach)
                if '</div>' in part:
                    end_pos = part.rfind('</div>') + 6
                    section = '<div class="file-item"' + part[:end_pos]
                    sections.append(section)
        
        # Fallback: if parsing failed, return whole response as one section
        if not sections and response.strip():
            sections = [response]
        
        return sections
    
    def _parse_single_html_response(self, response: str, item: Dict) -> Optional[str]:
        """Parse single file HTML response"""
        
        response = response.strip()
        
        # Look for file-item div
        if '<div class="file-item"' in response:
            start = response.find('<div class="file-item"')
            end = response.rfind('</div>') + 6
            if start != -1 and end != -1:
                return response[start:end]
        
        # Return response if it looks like HTML
        if '<div' in response or '<span' in response:
            return response
        
        return None
    
    def _build_complete_dashboard(self, file_sections_html: str) -> str:
        """Build complete HTML dashboard with all file sections"""
        
        # This is a simplified version - in practice, you'd use the full template
        complete_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete PR Analysis Dashboard</title>
    <!-- Include all CSS styles here -->
</head>
<body>
    <div class="container">
        <!-- Header and other sections -->
        
        <div id="hierarchy" class="tab-content">
            <h2>🌳 Complete Hierarchical File Analysis</h2>
            <div class="search-container">
                <input type="text" class="search-input" id="fileSearch" placeholder="Search files...">
                <select class="filter-select" id="statusFilter">
                    <option value="all">All Files</option>
                    <option value="ready">Ready</option>
                    <option value="conditional">Conditional</option>
                    <option value="not_ready">Not Ready</option>
                </select>
            </div>
            <div class="file-tree" id="fileTree">
                {file_sections_html}
            </div>
        </div>
        
        <!-- Other sections -->
    </div>
    
    <!-- Include all JavaScript here -->
</body>
</html>"""
        
        return complete_html
    
    def _create_html_batch_prompt_for_analysis(self, batch_analysis_results: List[Dict], context: Dict[str, Any]) -> str:
        """Create prompt for batch HTML generation from Stage 7 analysis results"""
        
        analysis_list = "\n".join([
            f"- {result.get('file_path', 'unknown')}: {result.get('merge_readiness', 'unknown')} - {result.get('overall_assessment', {}).get('purpose', 'No purpose')[:100]}"
            for result in batch_analysis_results
        ])
        
        batch_data = {
            "analysis_results": batch_analysis_results,
            "batch_size": len(batch_analysis_results),
            "context": context.get("previous_sections_count", 0),
            "processing_mode": "analysis_results"
        }
        
        # Save batch data for agent to read
        batch_file = self.output_dir / f"analysis_batch_data_{int(time.time())}.json"
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        prompt = f"""You are generating HTML file tree sections from Stage 7 detailed analysis results.

{self.instructions}

IMPORTANT: You are processing ANALYSIS RESULTS, not raw files. Each item contains:
- file_path: The file path
- merge_readiness: "ready" | "conditional" | "not_ready"  
- overall_assessment: {{purpose, business_impact, risk_assessment}}
- feedback: Detailed feedback (only if conditional/not_ready)
- code_elements: {{classes: [...], functions: [...]}}

BATCH DATA: Read analysis results from {batch_file}

ANALYSIS RESULTS IN THIS BATCH ({len(batch_analysis_results)}):
{analysis_list}

REQUIREMENTS:
1. Generate HTML sections for EVERY analysis result in the batch
2. Use the file tree structure specified in instructions
3. Display the ANALYSIS DATA (merge readiness, assessments, feedback)
4. Show code elements (classes/functions) if available
5. Return ONLY the HTML sections (no explanations)
6. Each result should be a complete <div class="file-item"> section

Return the HTML sections for all {len(batch_analysis_results)} analysis results."""

        return prompt
    
    def _create_single_analysis_html_prompt(self, analysis_result: Dict, context: Dict[str, Any]) -> str:
        """Create prompt for single analysis result HTML generation"""
        
        file_path = analysis_result.get('file_path', 'unknown')
        merge_readiness = analysis_result.get('merge_readiness', 'unknown')
        
        prompt = f"""Generate HTML section for a single Stage 7 analysis result.

{self.instructions}

ANALYSIS RESULT: {file_path}
MERGE READINESS: {merge_readiness}
DATA: {json.dumps(analysis_result, indent=2)}

Generate HTML displaying this analysis data (merge readiness, assessments, feedback, code elements).
Return ONLY the HTML section for this analysis result (complete <div class="file-item"> structure)."""

        return prompt


def create_html_batch_processor(output_dir: str,
                               html_template_path: str,
                               instructions_path: str,
                               batch_size: int = 25,
                               debug_mode: bool = False) -> HTMLBatchProcessor:
    """
    Factory function to create HTML batch processor.
    
    Args:
        output_dir: Directory for output files
        html_template_path: Path to HTML template
        instructions_path: Path to processing instructions
        batch_size: Number of files per batch
        debug_mode: Enable debug output
        
    Returns:
        Configured HTML batch processor
    """
    
    config = BatchProcessingConfig(
        batch_size=batch_size,
        debug_mode=debug_mode,
        verify_completeness=True,
        save_progress=True
    )
    
    return HTMLBatchProcessor(output_dir, html_template_path, instructions_path, config)
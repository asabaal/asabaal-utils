#!/usr/bin/env python3
"""
Detailed Analysis Processor - Specialized batch processor for Stage 7 file analysis

Uses the Agentic Batch Processing Toolkit to analyze large numbers of files
at the class/function level for merge readiness assessment.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from .batch_processor import BatchProcessor, BatchProcessingConfig


class DetailedAnalysisProcessor(BatchProcessor):
    """
    Specialized batch processor for detailed file-level analysis.
    
    Processes large numbers of files to provide:
    - File-level purpose and business impact analysis
    - Class/function level code quality assessment
    - File-type specific review criteria
    - Merge readiness decisions with detailed feedback
    """
    
    def __init__(self, 
                 repo_path: str,
                 output_dir: str,
                 instructions_path: str,
                 output_format_path: str,
                 config: Optional[BatchProcessingConfig] = None):
        
        super().__init__(output_dir, config)
        
        self.repo_path = Path(repo_path)
        self.instructions_path = Path(instructions_path)
        self.output_format_path = Path(output_format_path)
        
        # Load instructions and output format
        self.instructions = self._load_instructions()
        self.output_format = self._load_output_format()
    
    def _load_instructions(self) -> str:
        """Load detailed analysis instructions"""
        if self.instructions_path.exists():
            with open(self.instructions_path, 'r') as f:
                return f.read()
        return "Analyze files for merge readiness at class/function level."
    
    def _load_output_format(self) -> str:
        """Load output format template"""
        if self.output_format_path.exists():
            with open(self.output_format_path, 'r') as f:
                return f.read()
        return "{}"
    
    def process_batch(self, batch_items: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        Process a batch of files for detailed analysis.
        
        Args:
            batch_items: List of file data objects to analyze
            context: Contains previous analyses for context
            
        Returns:
            List of detailed analysis results
        """
        
        # Format batch files for analysis
        formatted_batch = []
        for file_data in batch_items:
            formatted_file = {
                "file_path": file_data.get('path', ''),
                "category": file_data.get('category', ''),
                "importance": file_data.get('importance', ''),
                "change_type": file_data.get('change_type', ''),
                "lines_added": file_data.get('lines_added', 0),
                "lines_removed": file_data.get('lines_removed', 0),
                "content_sample": file_data.get('content_sample', ''),
                "total_lines": file_data.get('total_lines', 0),
                "has_functions": file_data.get('has_functions', False),
                "has_classes": file_data.get('has_classes', False)
            }
            formatted_batch.append(formatted_file)
        
        # Create batch analysis prompt
        prompt = self._create_batch_analysis_prompt(formatted_batch, context.get('previous_analyses', []))
        
        try:
            # Call agent for batch analysis
            response = self.call_agent(prompt)
            
            # Parse batch response
            batch_analyses = self._parse_batch_response(response)
            
            if self.config.debug_mode:
                print(f"✅ Analyzed batch: {len(batch_analyses)} results returned")
                
            return batch_analyses
            
        except Exception as e:
            if self.config.debug_mode:
                print(f"❌ Batch analysis failed: {e}")
            return []
    
    def process_single_item(self, item: Dict, context: Dict[str, Any]) -> Optional[Dict]:
        """
        Process a single file for detailed analysis (fallback for missed files).
        
        Args:
            item: Single file data object
            context: Context from previous analyses
            
        Returns:
            Detailed analysis result or None if failed
        """
        
        # Format single file data
        formatted_file = {
            "file_path": item.get('path', ''),
            "category": item.get('category', ''),
            "importance": item.get('importance', ''),
            "change_type": item.get('change_type', ''),
            "lines_added": item.get('lines_added', 0),
            "lines_removed": item.get('lines_removed', 0),
            "content_sample": item.get('content_sample', ''),
            "total_lines": item.get('total_lines', 0),
            "has_functions": item.get('has_functions', False),
            "has_classes": item.get('has_classes', False)
        }
        
        # Create single file prompt
        prompt = self._create_single_file_prompt(formatted_file, context.get('previous_analyses', []))
        
        try:
            response = self.call_agent(prompt)
            analysis = self._parse_single_file_response(response, item['path'])
            
            if self.config.debug_mode and analysis:
                print(f"✅ Analyzed single file: {item['path']}")
                
            return analysis
        except Exception as e:
            if self.config.debug_mode:
                print(f"❌ Single file analysis failed for {item['path']}: {e}")
            return None
    
    def get_item_identifier(self, item: Dict) -> str:
        """Get unique identifier for a file"""
        return item.get('path', str(hash(str(item))))
    
    def combine_results(self, all_analyses: List[Dict]) -> Dict[str, Any]:
        """
        Combine all individual analyses into final detailed analysis report.
        
        Args:
            all_analyses: List of all file analysis results
            
        Returns:
            Complete detailed analysis report
        """
        
        # Filter out None values from failed analyses
        valid_analyses = [a for a in all_analyses if a is not None]
        
        # Count merge readiness statuses
        ready_count = len([a for a in valid_analyses if a.get('merge_readiness') == 'ready'])
        conditional_count = len([a for a in valid_analyses if a.get('merge_readiness') == 'conditional'])  
        not_ready_count = len([a for a in valid_analyses if a.get('merge_readiness') == 'not_ready'])
        
        # Determine overall readiness
        if not_ready_count > 0:
            overall_readiness = "not_ready"
        elif conditional_count > 0:
            overall_readiness = "conditional"
        else:
            overall_readiness = "ready"
        
        return {
            "analysis_summary": {
                "total_files_analyzed": len(valid_analyses),
                "total_files_in_pr": len(all_analyses),  # Include failed attempts in total
                "merge_ready_files": ready_count,
                "conditional_files": conditional_count,
                "not_ready_files": not_ready_count,
                "overall_merge_readiness": overall_readiness,
                "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "file_analyses": valid_analyses,
            "recommendations": self._generate_overall_recommendations(valid_analyses),
            "blocking_issues": [
                analysis.get('feedback', '') 
                for analysis in valid_analyses 
                if analysis and analysis.get('merge_readiness') == 'not_ready'
            ]
        }
    
    def _create_batch_analysis_prompt(self, batch_files: List[Dict], previous_analyses: List[Dict]) -> str:
        """Create prompt for batch analysis"""
        
        batch_files_info = "\n".join([
            f"- {f['file_path']} ({f.get('category', 'Unknown')} - {f.get('lines_added', 0)} lines added)"
            for f in batch_files
        ])
        
        previous_context = ""
        if previous_analyses:
            recent_analyses = previous_analyses[-10:]  # Last 10 for context
            previous_context = f"""
CONTEXT FROM PREVIOUS ANALYSES:
You have already analyzed {len(previous_analyses)} files. Recent findings:
{chr(10).join([f"- {a.get('file_path', '')}: {a.get('merge_readiness', 'unknown')} - {(a.get('feedback', '') or 'No issues')[:100]}" for a in recent_analyses])}
"""
        
        prompt = f"""You are analyzing a batch of {len(batch_files)} files for merge readiness.

{self.instructions}

{previous_context}

FILES IN THIS BATCH:
{batch_files_info}

CRITICAL: Analyze EVERY file in this batch. Return a JSON array where each element follows this structure:
{{
  "file_path": "exact/file/path.ext",
  "merge_readiness": "ready|conditional|not_ready", 
  "overall_assessment": {{
    "purpose": "...",
    "business_impact": "...",
    "risk_assessment": "..."
  }},
  "feedback": "only if conditional or not_ready",
  "code_elements": {{
    "classes": [...],
    "functions": [...] 
  }}
}}

Return ONLY the JSON array with an analysis object for each of the {len(batch_files)} files."""

        return prompt
    
    def _create_single_file_prompt(self, file_data: Dict, previous_analyses: List[Dict]) -> str:
        """Create prompt for single file analysis"""
        
        context_info = ""
        if previous_analyses:
            context_info = f"CONTEXT: You've already analyzed {len(previous_analyses)} other files."
        
        prompt = f"""You are analyzing a single file that was missed in batch processing: {file_data['file_path']}

{context_info}

{self.instructions[:1000]}  # Truncate for single file

FILE DETAILS:
- Path: {file_data['file_path']}
- Category: {file_data.get('category', 'Unknown')}
- Lines added: {file_data.get('lines_added', 0)}
- Content sample: {file_data.get('content_sample', '')[:1000]}...

Return a single JSON object analyzing this file:
{{
  "file_path": "{file_data['file_path']}",
  "merge_readiness": "ready|conditional|not_ready",
  "overall_assessment": {{
    "purpose": "...",
    "business_impact": "...",
    "risk_assessment": "..."
  }},
  "feedback": "only if conditional or not_ready",
  "code_elements": {{
    "classes": [...],
    "functions": [...]
  }}
}}"""

        return prompt
    
    def _parse_batch_response(self, response: str) -> List[Dict]:
        """Parse batch analysis response"""
        try:
            # Extract JSON from response
            json_str = response.strip()
            if '```json' in json_str:
                start = json_str.find('```json') + 7
                end = json_str.find('```', start)
                if end != -1:
                    json_str = json_str[start:end].strip()
            
            # Try to parse as array
            if json_str.startswith('['):
                return json.loads(json_str)
            else:
                # If single object, wrap in array
                return [json.loads(json_str)]
                
        except Exception as e:
            if self.config.debug_mode:
                print(f"❌ Failed to parse batch response: {e}")
            return []
    
    def _parse_single_file_response(self, response: str, file_path: str) -> Optional[Dict]:
        """Parse single file analysis response"""
        try:
            json_str = response.strip()
            if '```json' in json_str:
                start = json_str.find('```json') + 7
                end = json_str.find('```', start)
                if end != -1:
                    json_str = json_str[start:end].strip()
            
            analysis = json.loads(json_str)
            analysis['file_path'] = file_path  # Ensure correct path
            return analysis
        except Exception as e:
            if self.config.debug_mode:
                print(f"❌ Failed to parse single file response: {e}")
            return None
    
    def _generate_overall_recommendations(self, analyses: List[Dict]) -> List[str]:
        """Generate recommendations based on all analyses"""
        recommendations = []
        
        # Filter out None values
        valid_analyses = [a for a in analyses if a is not None]
        
        # Count common issues
        conditional_files = [a for a in valid_analyses if a.get('merge_readiness') == 'conditional']
        
        if len(conditional_files) > 5:
            recommendations.append("Multiple files need minor improvements - consider addressing common patterns")
            
        if any('console.log' in (a.get('feedback', '') or '') for a in valid_analyses):
            recommendations.append("Remove debug console.log statements from production code")
            
        if any('CSS' in (a.get('feedback', '') or '') for a in valid_analyses):
            recommendations.append("Consider extracting inline CSS to separate files for better maintainability")
            
        return recommendations


def create_detailed_analysis_processor(repo_path: str,
                                     output_dir: str,
                                     instructions_path: str,
                                     output_format_path: str,
                                     batch_size: int = 12,
                                     max_files: Optional[int] = None,
                                     debug_mode: bool = False) -> DetailedAnalysisProcessor:
    """
    Factory function to create detailed analysis processor.
    
    Args:
        repo_path: Path to repository being analyzed
        output_dir: Directory for output files
        instructions_path: Path to analysis instructions
        output_format_path: Path to output format template
        batch_size: Number of files per batch
        max_files: Optional limit on total files to process
        debug_mode: Enable debug output
        
    Returns:
        Configured detailed analysis processor
    """
    
    config = BatchProcessingConfig(
        batch_size=batch_size,
        debug_mode=debug_mode,
        verify_completeness=True,
        save_progress=True,
        max_retries=3
    )
    
    processor = DetailedAnalysisProcessor(
        repo_path, output_dir, instructions_path, output_format_path, config
    )
    
    # Store max_files limit if provided
    if max_files:
        processor.max_files = max_files
    
    return processor
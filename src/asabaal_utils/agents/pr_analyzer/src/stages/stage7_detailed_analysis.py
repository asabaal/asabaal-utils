#!/usr/bin/env python3
"""
Stage 7: Detailed File-Level Analysis
Comprehensive code review at file, class, and function levels for merge readiness
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add shared utilities to path
shared_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "asabaal_utils" / "shared"
sys.path.insert(0, str(shared_path))

from api_confirmation import require_paid_api_confirmation

# Import backend manager
BACKEND_MANAGER_AVAILABLE = False
BackendManager = None
BackendConfig = None
BackendType = None

try:
    from agentic_toolkit.backend_config import BackendManager, BackendConfig, BackendType
    BACKEND_MANAGER_AVAILABLE = True
except ImportError:
    BACKEND_MANAGER_AVAILABLE = False
    BackendManager = None  # type: ignore
    BackendConfig = None  # type: ignore
    BackendType = None  # type: ignore


class DetailedAnalysisEngine:
    """Detailed file-level analysis for merge readiness assessment"""
    
    def __init__(self, repo_path: str, output_dir: Optional[str] = None, debug_mode: bool = False, max_files: Optional[int] = None, config: Optional[Dict[str, Any]] = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else self.repo_path / "pr_analysis_output"
        self.debug_mode = debug_mode
        self.max_files = max_files  # File count filter for debug mode
        
        # Main outputs go to root of output directory
        # Debug outputs only created in debug mode
        if self.debug_mode:
            self.debug_dir = self.output_dir / "debug_outputs" / "stage7"
            self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        self.prompt_data_dir = self.output_dir / "prompt_data"
        
        # Resume capability - track progress
        self.progress_file = self.output_dir / "stage7_progress.json"
        self.partial_results_file = self.output_dir / "stage7_partial_results.json"
        
        # Package directory for templates
        self.package_dir = Path(__file__).parent
        
        # Initialize backend manager
        self.backend_manager = None
        if BACKEND_MANAGER_AVAILABLE:
            try:
                # Create backend config from provided config or auto-detect
                backend_config = None
                if config and 'agentic_backend' in config:
                    backend_cfg = config['agentic_backend']
                    provider = backend_cfg.get('provider', 'ollama')
                    model = backend_cfg.get('model', 'anthropic/claude-3.5-sonnet')
                    
                    if provider == 'ollama' and BackendType is not None and BackendConfig is not None:
                        backend_config = BackendConfig(
                            backend_type=BackendType.OLLAMA,
                            model=model,
                            base_url='http://localhost:11434'
                        )
                    elif provider == 'openrouter' and BackendType is not None and BackendConfig is not None:
                        backend_config = BackendConfig(
                            backend_type=BackendType.OPENROUTER,
                            model=model,
                            api_key=os.getenv('OPENROUTER_API_KEY')
                        )
                    elif provider == 'claude' and BackendType is not None and BackendConfig is not None:
                        backend_config = BackendConfig(
                            backend_type=BackendType.CLAUDE,
                            model=model,
                            api_key=os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
                        )
                
                if BackendManager is not None and backend_config is not None:
                    self.backend_manager = BackendManager(backend_config)
                else:
                    self.backend_manager = None
                if self.backend_manager is not None:
                    backend_info = self.backend_manager.get_backend_info()
                    print(f"🔧 Backend manager initialized for detailed analysis")
                    print(f"   Using {backend_info['backend_type']} backend with model {backend_info.get('model', 'unknown')}")
                else:
                    print("⚠️  Backend manager not available")
            except Exception as e:
                print(f"⚠️  Backend manager initialization failed: {e}")
                self.backend_manager = None
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_analysis_context(self) -> Dict[str, Any]:
        """Load all previous analysis data for detailed review"""
        if self.debug_mode:
            print("🔍 Loading previous analysis data...")
        context = {}
        
        # Load Stage 1: File classifications and content
        stage1_files = self.output_dir / "debug_outputs" / "stage1"
        context_file = stage1_files / "final_analysis_context.json"
        
        if context_file.exists():
            if self.debug_mode:
                print(f"✅ Found Stage 1 context: {context_file}")
            with open(context_file, 'r') as f:
                context = json.load(f)
                if self.debug_mode:
                    print(f"   Files classified: {len(context.get('file_classifications', {}))}")
                    print(f"   Files with content: {len(context.get('file_contents', {}))}")
        else:
            if self.debug_mode:
                print(f"❌ Stage 1 context not found: {context_file}")
            
        # Load Stage 6: Combined analysis results
        stage6_files = self.output_dir / "debug_outputs" / "stage6"
        complete_analysis_file = stage6_files / "complete_pr_analysis.json"
        
        if complete_analysis_file.exists():
            if self.debug_mode:
                print(f"✅ Found Stage 6 results: {complete_analysis_file}")
            with open(complete_analysis_file, 'r') as f:
                stage6_data = json.load(f)
                context['previous_analysis'] = stage6_data
        else:
            if self.debug_mode:
                print(f"❌ Stage 6 results not found: {complete_analysis_file}")
                
        return context
        
    def prepare_detailed_analysis_data(self) -> Path:
        """Prepare comprehensive data file for detailed analysis agent"""
        
        # Load all context
        analysis_context = self.load_analysis_context()
        
        # Process files array into classifications and contents
        files_array = analysis_context.get('files', [])
        file_classifications = {}
        file_contents = {}
        
        for file_data in files_array:
            file_path = file_data.get('path', '')
            file_classifications[file_path] = {
                'category': file_data.get('category', ''),
                'importance': file_data.get('importance', ''),
                'change_type': file_data.get('change_type', ''),
                'lines_added': file_data.get('lines_added', 0),
                'lines_removed': file_data.get('lines_removed', 0)
            }
            file_contents[file_path] = {
                'content_sample': file_data.get('content_sample', ''),
                'total_lines': file_data.get('total_lines', 0),
                'has_functions': file_data.get('has_functions', False),
                'has_classes': file_data.get('has_classes', False)
            }
        
        # Create detailed analysis data structure
        detailed_data = {
            "repository_info": {
                "repo_path": str(self.repo_path),
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_files": len(files_array)
            },
            "file_classifications": file_classifications,
            "file_contents": file_contents,
            "git_analysis": analysis_context.get('pr_summary', {}),
            "previous_findings": analysis_context.get('previous_analysis', {}),
            "analysis_instructions": {
                "focus_areas": [
                    "File-level purpose and business impact",
                    "Class/function level code quality",
                    "File-type specific review criteria",
                    "Merge readiness assessment with feedback"
                ],
                "output_requirements": "Hierarchical analysis with merge decisions at all levels"
            }
        }
        
        # Save detailed analysis data
        data_file = self.prompt_data_dir / "detailed_analysis_data.json"
        with open(data_file, 'w') as f:
            json.dump(detailed_data, f, indent=2)
            
        if self.debug_mode:
            print(f"📊 Prepared detailed analysis data: {data_file}")
            print(f"   Files to analyze: {detailed_data['repository_info']['total_files']}")
        
        return data_file
        
    def create_detailed_analysis_prompt(self) -> str:
        """Create detailed analysis prompt with file references"""
        
        # Copy instruction files to prompt_data directory (like other stages do)
        instructions_source = self.package_dir / "detailed_analysis_instructions.txt"
        output_format_source = self.package_dir / "detailed_analysis_output_format.json"
        
        instructions_file = self.prompt_data_dir / "detailed_analysis_instructions.txt"
        output_format_file = self.prompt_data_dir / "detailed_analysis_output_format.json"
        data_file = self.prompt_data_dir / "detailed_analysis_data.json"
        
        # Copy files to prompt_data (following the same pattern as other stages)
        if instructions_source.exists():
            import shutil
            shutil.copy2(instructions_source, instructions_file)
        if output_format_source.exists():
            import shutil
            shutil.copy2(output_format_source, output_format_file)
        
        prompt = f"""You are a senior code reviewer conducting detailed file-level analysis for merge readiness assessment.

Read the detailed analysis instructions from {instructions_file} and the analysis data from {data_file}.

Reference the output format template at {output_format_file} for your response structure.

Instructions:
1. Analyze each file at the class/function level for merge readiness
2. Apply file-type specific review criteria based on classifications  
3. Provide hierarchical assessment: file → class → function levels
4. Give merge readiness decisions with feedback only when issues found

Return ONLY valid JSON in the exact format specified in the output format template."""

        return prompt
        
    def call_detailed_analysis_agent(self, prompt: str) -> str:
        """Call agent for detailed file analysis using OpenRouter API"""
        print("🤖 Calling detailed analysis agent...")
        
        # Save prompt to file only in debug mode
        if self.debug_mode:
            prompt_file = self.debug_dir / "detailed_analysis_prompt.txt"
            with open(prompt_file, 'w') as f:
                f.write(prompt)
            print(f"💾 Saved prompt to {prompt_file}")
        
        # Check backend availability
        if not self.backend_manager:
            raise Exception("AI backend manager not available - check appropriate configuration")
        
        # Use AI backend API
        try:
            backend_info = self.backend_manager.get_backend_info()
            backend_type = backend_info['backend_type']
            backend_model = backend_info.get('model', 'unknown')
            print(f"🔄 Using {backend_type} API with model {backend_model} (prompt length: {len(prompt):,} chars)")
            
            # Require confirmation for paid APIs
            if not require_paid_api_confirmation(backend_type):
                raise Exception("Paid API usage not confirmed by user")
            
            response = self.backend_manager.call_agent(prompt, timeout=300)
            
            # Save full response only in debug mode
            if self.debug_mode:
                response_file = self.debug_dir / "detailed_analysis_full_response.txt"
                with open(response_file, 'w') as f:
                    f.write(response)
                print(f"✅ {backend_type} agent call successful ({len(response):,} chars)")
            
            return response
            
        except Exception as e:
            backend_info = self.backend_manager.get_backend_info() if self.backend_manager else {'backend_type': 'AI Backend'}
            backend_type = backend_info['backend_type']
            if self.debug_mode:
                print(f"❌ {backend_type} API error: {e}")
            raise Exception(f"{backend_type} API call failed: {str(e)}")
            
    def save_detailed_analysis(self, analysis_response: str) -> Path:
        """Save and validate detailed analysis results"""
        
        try:
            # Extract JSON from response (handle cases where agent includes extra text)
            json_str = analysis_response.strip()
            
            # Look for JSON block if response contains other text
            if '```json' in json_str:
                start = json_str.find('```json') + 7
                end = json_str.find('```', start)
                if end != -1:
                    json_str = json_str[start:end].strip()
            elif json_str.startswith('Based on') or json_str.startswith('The analysis'):
                # Find the JSON part
                json_start = json_str.find('{')
                if json_start != -1:
                    json_str = json_str[json_start:]
            
            # Parse JSON response
            analysis_data = json.loads(json_str)
            
            # VALIDATION: Ensure all files from Stage 1 are included
            analysis_data = self._ensure_all_files_analyzed(analysis_data)
            
            # Save main analysis result to root output directory
            analysis_file = self.output_dir / "detailed_analysis_results.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2)
                
            print(f"📊 Detailed analysis saved: {analysis_file}")
            
            # Generate summary (main output)
            summary = self.generate_analysis_summary(analysis_data)
            summary_file = self.output_dir / "detailed_analysis_summary.txt"
            with open(summary_file, 'w') as f:
                f.write(summary)
                
            return analysis_file
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse analysis response as JSON: {e}")
            print(f"❌ Response preview: {analysis_response[:200]}...")
            # Save raw response for debugging only in debug mode
            if self.debug_mode:
                raw_file = self.debug_dir / "detailed_analysis_raw_response.txt"
                with open(raw_file, 'w') as f:
                    f.write(analysis_response)
                print(f"💾 Raw response saved for debugging: {raw_file}")
            raise
    
    def _ensure_all_files_analyzed(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all files from Stage 1 are included in the analysis"""
        
        # Load Stage 1 context to get the complete file list
        try:
            context_file = self.output_dir / "final_analysis_context.json"
            if not context_file.exists():
                print("⚠️  Cannot validate file completeness - Stage 1 context not found")
                return analysis_data
                
            with open(context_file, 'r') as f:
                stage1_context = json.load(f)
            
            # Get all files from Stage 1
            stage1_files = set()
            for file_data in stage1_context.get('files', []):
                stage1_files.add(file_data.get('path', ''))
            
            # Get files analyzed by Stage 7
            file_analyses = analysis_data.get('file_analyses', [])
            if isinstance(file_analyses, dict):
                analyzed_files = set(file_analyses.keys())
            else:
                analyzed_files = set(f.get('file_path', '') for f in file_analyses)
            
            # Find missing files
            missing_files = stage1_files - analyzed_files
            
            if missing_files:
                print(f"⚠️  AI agent missed {len(missing_files)} files - adding default analysis")
                for missing_file in missing_files:
                    print(f"   Adding missing file: {missing_file}")
                    
                    # Create default analysis for missing files
                    default_analysis = {
                        "merge_readiness": "conditional",
                        "overall_assessment": {
                            "purpose": "File requires manual review - AI analysis missed",
                            "business_impact": "Unknown - requires assessment",
                            "risk_assessment": "Unknown - requires assessment"
                        },
                        "feedback": "This file was not analyzed by the AI agent and requires manual review.",
                        "code_elements": {
                            "classes": [],
                            "functions": []
                        }
                    }
                    
                    # Add to analysis data
                    if isinstance(file_analyses, dict):
                        file_analyses[missing_file] = default_analysis
                    else:
                        file_analyses.append({
                            "file_path": missing_file,
                            **default_analysis
                        })
                
                # Update the analysis data
                analysis_data['file_analyses'] = file_analyses
                
                # Update metadata
                if 'analysis_metadata' in analysis_data:
                    analysis_data['analysis_metadata']['total_files_analyzed'] = len(stage1_files)
                
                print(f"✅ Added {len(missing_files)} missing files to analysis")
            
        except Exception as e:
            print(f"⚠️  Error validating file completeness: {e}")
            
        return analysis_data
            
    def generate_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Generate human-readable summary of detailed analysis"""
        
        # Handle both expected and actual response formats
        metadata = analysis_data.get('analysis_metadata', {})
        summary = analysis_data.get('analysis_summary', analysis_data.get('overall_assessment', {}))
        file_analyses = analysis_data.get('file_analyses', {})
        
        # Convert file_analyses dict to list if needed
        if isinstance(file_analyses, dict):
            file_list = [{'file_path': k, **v} for k, v in file_analyses.items()]
        else:
            file_list = file_analyses if isinstance(file_analyses, list) else []
        
        total_files = metadata.get('total_files_analyzed', len(file_list))
        
        report = f"""DETAILED FILE-LEVEL ANALYSIS SUMMARY
{'=' * 50}

OVERALL RESULTS:
- Total files analyzed: {total_files}
- Analysis timestamp: {metadata.get('timestamp', 'Unknown')}
- Overall merge readiness: {summary.get('merge_readiness', 'Unknown').upper()}

"""

        # Count files by status
        ready_count = len([f for f in file_list if f.get('merge_readiness') == 'MERGE_READY'])
        conditional_count = len([f for f in file_list if f.get('merge_readiness') == 'conditional'])
        not_ready_count = len([f for f in file_list if f.get('merge_readiness') == 'not_ready'])
        insufficient_data_count = len([f for f in file_list if f.get('merge_readiness') == 'INSUFFICIENT_DATA'])
        
        report += f"""FILE STATUS BREAKDOWN:
- Ready for merge: {ready_count}
- Conditional: {conditional_count}  
- Not ready: {not_ready_count}
- Insufficient data: {insufficient_data_count}

"""

        # Files needing attention
        conditional_files = [f for f in file_list if f.get('merge_readiness') == 'conditional']
        not_ready_files = [f for f in file_list if f.get('merge_readiness') == 'not_ready']
        
        if conditional_files:
            report += f"\nCONDITIONAL FILES ({len(conditional_files)}):\n"
            for file_data in conditional_files:
                report += f"- {file_data.get('file_path', 'Unknown')}: {file_data.get('feedback', 'No specific feedback')}\n"
                
        if not_ready_files:
            report += f"\nNOT READY FILES ({len(not_ready_files)}):\n"
            for file_data in not_ready_files:
                report += f"- {file_data.get('file_path', 'Unknown')}: {file_data.get('feedback', 'No specific feedback')}\n"
                
        # Overall recommendations from summary
        summary_obj = analysis_data.get('summary', {})
        if summary_obj and isinstance(summary_obj, dict):
            key_concerns = summary_obj.get('key_concerns', [])
            next_steps = summary_obj.get('next_steps', [])
            
            if key_concerns:
                report += f"\nKEY CONCERNS:\n"
                for i, concern in enumerate(key_concerns, 1):
                    report += f"{i}. {concern}\n"
                    
            if next_steps:
                report += f"\nRECOMMENDED NEXT STEPS:\n"
                for i, step in enumerate(next_steps, 1):
                    report += f"{i}. {step}\n"
                
        return report
        
    def process_file_batch(self, batch_files: List[Dict], previous_analyses: List[Dict]) -> List[Dict]:
        """Process a batch of files with context from previous analyses"""
        
        # Convert file data format (from files array to individual file data)
        formatted_batch = []
        for file_data in batch_files:
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
        
        # Create batch-specific prompt
        prompt = self.create_batch_analysis_prompt(formatted_batch, previous_analyses)
        
        try:
            # Call agent for this batch
            response = self.call_detailed_analysis_agent(prompt)
            
            # Parse batch response
            batch_analyses = self.parse_batch_response(response)
            
            if self.debug_mode:
                print(f"✅ Batch processed: {len(batch_analyses)} analyses returned")
                
            return batch_analyses
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ Batch processing failed: {e}")
            return []
    
    def process_single_file(self, file_data: Dict, previous_analyses: List[Dict]) -> Optional[Dict]:
        """Process a single file with full context from previous analyses"""
        
        # Format the single file data
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
        
        # Create single file prompt
        prompt = self.create_single_file_prompt(formatted_file, previous_analyses)
        
        try:
            response = self.call_detailed_analysis_agent(prompt)
            analysis = self.parse_single_file_response(response, file_data['path'])
            
            if self.debug_mode and analysis:
                print(f"✅ Single file processed: {file_data['path']}")
                
            return analysis
        except Exception as e:
            if self.debug_mode:
                print(f"❌ Single file processing failed for {file_data['path']}: {e}")
            return None
    
    def create_batch_analysis_prompt(self, batch_files: List[Dict], previous_analyses: List[Dict]) -> str:
        """Create prompt for batch analysis"""
        
        instructions_content = ""
        instructions_source = self.package_dir / "detailed_analysis_instructions.txt"
        if instructions_source.exists():
            with open(instructions_source, 'r') as f:
                instructions_content = f.read()
        
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

{instructions_content}

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
    
    def create_single_file_prompt(self, file_data: Dict, previous_analyses: List[Dict]) -> str:
        """Create prompt for single file analysis"""
        
        instructions_content = ""
        instructions_source = self.package_dir / "detailed_analysis_instructions.txt"
        if instructions_source.exists():
            with open(instructions_source, 'r') as f:
                instructions_content = f.read()[:1000]  # Truncate for single file
        
        context_info = ""
        if previous_analyses:
            context_info = f"CONTEXT: You've already analyzed {len(previous_analyses)} other files."
        
        prompt = f"""You are analyzing a single file that was missed in batch processing: {file_data['file_path']}

{context_info}

{instructions_content}

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
    
    def parse_batch_response(self, response: str) -> List[Dict]:
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
                
        except:
            return []
    
    def parse_single_file_response(self, response: str, file_path: str) -> Optional[Dict]:
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
        except:
            return None
    
    def combine_all_analyses(self, all_analyses: List[Dict], total_files: int) -> Dict:
        """Combine all individual analyses into final report"""
        
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
                "total_files_in_pr": total_files,
                "merge_ready_files": ready_count,
                "conditional_files": conditional_count,
                "not_ready_files": not_ready_count,
                "overall_merge_readiness": overall_readiness,
                "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "file_analyses": valid_analyses,
            "recommendations": self.generate_overall_recommendations(valid_analyses),
            "blocking_issues": [
                analysis.get('feedback', '') 
                for analysis in valid_analyses 
                if analysis and analysis.get('merge_readiness') == 'not_ready'
            ]
        }
    
    def generate_overall_recommendations(self, analyses: List[Dict]) -> List[str]:
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
    
    def save_final_analysis(self, final_analysis: Dict) -> Path:
        """Save the complete analysis results"""
        
        # Save main analysis result
        analysis_file = self.output_dir / "detailed_analysis_results.json"
        with open(analysis_file, 'w') as f:
            json.dump(final_analysis, f, indent=2)
            
        # Generate and save summary
        summary = self.generate_analysis_summary(final_analysis)
        summary_file = self.output_dir / "detailed_analysis_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)
            
        return analysis_file
    
    def load_previous_progress(self) -> Dict[str, Any]:
        """Load previous analysis progress for resume capability"""
        progress = {
            "completed_files": set(),
            "partial_analyses": []
        }
        
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    saved_progress = json.load(f)
                    progress["completed_files"] = set(saved_progress.get("completed_files", []))
                    
                if self.debug_mode:
                    print(f"📋 Resumed: Found {len(progress['completed_files'])} previously analyzed files")
            except:
                if self.debug_mode:
                    print("⚠️  Could not load previous progress")
        
        if self.partial_results_file.exists():
            try:
                with open(self.partial_results_file, 'r') as f:
                    progress["partial_analyses"] = json.load(f)
                    
                if self.debug_mode:
                    print(f"📋 Resumed: Found {len(progress['partial_analyses'])} partial analyses")
            except:
                if self.debug_mode:
                    print("⚠️  Could not load partial results")
        
        return progress
    
    def save_progress(self, completed_files: set, partial_analyses: List[Dict]):
        """Save current progress for resume capability"""
        try:
            # Save progress
            progress = {
                "completed_files": list(completed_files),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_completed": len(completed_files)
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            
            # Save partial results
            with open(self.partial_results_file, 'w') as f:
                json.dump(partial_analyses, f, indent=2)
                
            if self.debug_mode:
                print(f"💾 Progress saved: {len(completed_files)} files completed")
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️  Could not save progress: {e}")
        
    def run_detailed_analysis(self) -> bool:
        """Execute complete detailed file-level analysis using smart batch processing"""
        
        print("=" * 80)
        print("🔍 STAGE 7: DETAILED FILE-LEVEL ANALYSIS")
        print("=" * 80)
        
        try:
            # Step 1: Load context and previous progress
            analysis_context = self.load_analysis_context()
            files_array = analysis_context.get('files', [])
            
            # Apply file count filter if specified
            if self.max_files and len(files_array) > self.max_files:
                files_array = files_array[:self.max_files]
                if self.debug_mode:
                    print(f"🔢 File count filter applied: Processing {self.max_files} files (of {len(analysis_context.get('files', []))} total)")
            
            total_files = len(files_array)
            
            # Load previous progress for resume capability
            progress = self.load_previous_progress()
            previously_completed = progress["completed_files"]
            all_analyses = progress["partial_analyses"]
            
            # Filter out already completed files
            remaining_files = [f for f in files_array if f['path'] not in previously_completed]
            
            if previously_completed:
                print(f"📋 Resuming: {len(previously_completed)} files already analyzed")
                print(f"📊 Processing {len(remaining_files)} remaining files of {total_files} total")
            else:
                print(f"📊 Processing {total_files} files using smart batch analysis")
            
            # Step 2: Batch processing with accumulating context
            batch_size = 12  # Process 12 files at a time
            analyzed_files = set(previously_completed)
            
            for batch_start in range(0, len(remaining_files), batch_size):
                batch_end = min(batch_start + batch_size, len(remaining_files))
                batch_files = remaining_files[batch_start:batch_end]
                
                batch_num = batch_start//batch_size + 1
                print(f"🔄 Analyzing batch {batch_num}: files {batch_start+1}-{batch_end} of remaining")
                
                batch_analyses = self.process_file_batch(batch_files, all_analyses)
                if batch_analyses:
                    all_analyses.extend(batch_analyses)
                    analyzed_files.update([f.get('file_path') for f in batch_analyses if f])
                    
                    # Save progress after each batch
                    self.save_progress(analyzed_files, all_analyses)
            
            # Step 3: Verification - check for missed files
            all_file_paths = {f['path'] for f in files_array}
            missed_files = all_file_paths - analyzed_files
            
            if missed_files:
                print(f"⚠️  Found {len(missed_files)} files missed in batch processing")
                print("🔄 Processing missed files individually...")
                
                for file_path in missed_files:
                    file_data = next((f for f in files_array if f['path'] == file_path), None)
                    if file_data:
                        individual_analysis = self.process_single_file(file_data, all_analyses)
                        if individual_analysis:
                            all_analyses.append(individual_analysis)
                            analyzed_files.add(file_path)
                            
                            # Save progress after each individual file
                            self.save_progress(analyzed_files, all_analyses)
            
            # Step 4: Combine all analyses and save
            final_analysis = self.combine_all_analyses(all_analyses, total_files)
            analysis_file = self.save_final_analysis(final_analysis)
            
            # Clean up progress files on successful completion
            if self.progress_file.exists():
                self.progress_file.unlink()
            if self.partial_results_file.exists():
                self.partial_results_file.unlink()
            
            print(f"✅ STAGE 7 DETAILED ANALYSIS: SUCCESS")
            print(f"📊 Analyzed {len(analyzed_files)} of {total_files} files")
            print(f"📊 Generated detailed analysis: {analysis_file}")
            
            if self.debug_mode:
                self.create_test_summary(True, f"Analyzed {len(analyzed_files)}/{total_files} files successfully")
            return True
                
        except Exception as e:
            print(f"❌ STAGE 7 DETAILED ANALYSIS: FAILED - {e}")
            if self.debug_mode:
                self.create_test_summary(False, str(e))
            return False
            
    def create_test_summary(self, success: bool, message: str):
        """Create test summary for this stage (debug mode only)"""
        if not self.debug_mode:
            return
            
        summary = {
            "stage": "7_detailed_analysis",
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "output_files": [
                str(self.output_dir / "detailed_analysis_results.json"),
                str(self.output_dir / "detailed_analysis_summary.txt")
            ]
        }
        
        if self.debug_mode:
            summary["debug_files"] = [
                str(self.debug_dir / "detailed_analysis_prompt.txt"),
                str(self.debug_dir / "detailed_analysis_full_response.txt")
            ]
        
        summary_file = self.debug_dir / "stage7_test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)


def main():
    """Main execution for Stage 7"""
    if len(sys.argv) < 2:
        print("Usage: python stage7_detailed_analysis.py <repo_path> [output_dir]")
        sys.exit(1)
        
    repo_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyzer = DetailedAnalysisEngine(repo_path, output_dir)
    success = analyzer.run_detailed_analysis()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
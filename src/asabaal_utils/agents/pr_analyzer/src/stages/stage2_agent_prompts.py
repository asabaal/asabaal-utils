#!/usr/bin/env python3
"""
Stage 2: Agent Prompt Generation Testing
Test prompt generation for each specialized agent with full visibility
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class PromptTestResult:
    """Results from prompt generation testing"""
    agent_name: str
    prompt_length: int
    context_size_kb: float
    file_count: int
    category_count: int
    generated_successfully: bool
    validation_errors: List[str]
    performance_ms: float


class AgentPromptTester:
    """Test Stage 2: Agent Prompt Generation with full visibility"""
    
    def __init__(self, output_dir: str | None = None):
        if output_dir is not None:
            self.test_output_dir = Path(output_dir) / "debug_outputs" / "stage2"
            # Load context from Stage 1 in the provided output directory
            stage1_dir = Path(output_dir) / "debug_outputs" / "stage1"
        else:
            self.test_output_dir = Path(__file__).parent / "debug_outputs" / "stage2"
            # Load context from Stage 1 in the default location
            stage1_dir = Path(__file__).parent / "debug_outputs" / "stage1"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        context_file = stage1_dir / "final_analysis_context.json"
        
        if not context_file.exists():
            raise RuntimeError("Stage 1 context not found - run Stage 1 first!")
        
        with open(context_file, 'r') as f:
            self.analysis_context = json.load(f)
        
        print(f"📋 Loaded Stage 1 context:")
        print(f"   Files: {len(self.analysis_context['files'])}")
        print(f"   Categories: {len(self.analysis_context['categories'])}")
        print(f"   PR: {self.analysis_context['pr_summary']['from_branch']} → {self.analysis_context['pr_summary']['to_branch']}")
    
    def test_duplicate_detection_prompt(self) -> PromptTestResult:
        """Test Duplicate Detection Agent prompt generation"""
        print("\n🔍 Testing Duplicate Detection Agent Prompt...")
        
        start_time = time.time()
        
        try:
            # Prepare detailed file information for content analysis
            files_for_analysis = self._prepare_files_for_content_analysis()
            
            # Build the duplicate detection prompt (same as original but with debugging)
            prompt = f"""You are a senior software architect with expertise in detecting duplicate implementations by analyzing actual code content and functional purpose. Your task is to DISCOVER duplicate or similar files by reading and understanding what each file actually does.

## PR Context
- Analyzing: {self.analysis_context['pr_summary']['total_files_changed']} files (+{self.analysis_context['pr_summary']['total_lines_added']}/-{self.analysis_context['pr_summary']['total_lines_removed']})
- Branch: {self.analysis_context['pr_summary']['from_branch']} → {self.analysis_context['pr_summary']['to_branch']}

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
Respond with specific discoveries in this format:

### CRITICAL Issues (Exact duplicates or abandoned implementations)
**Issue:** [Brief title]
**Files:** file1.py, file2.py, file3.py
**Evidence:** [Specific code quotes showing similarity]
**Recommendation:** [Specific action needed]

### HIGH Issues (Functional duplicates with different implementations)
**Issue:** [Brief title]  
**Files:** file1.py, file2.py
**Evidence:** [Specific code quotes showing similarity]
**Recommendation:** [Specific action needed]

### MEDIUM Issues (Similar purpose, potentially consolidatable)
**Issue:** [Brief title]
**Files:** file1.py, file2.py
**Evidence:** [Specific code quotes showing similarity]
**Recommendation:** [Specific action needed]

Focus on DISCOVERING actual content-based duplicates, not generic observations.
"""
            
            end_time = time.time()
            
            # Analyze prompt characteristics
            prompt_stats = {
                'total_length': len(prompt),
                'total_lines': len(prompt.split('\n')),
                'context_section_length': len(files_for_analysis),
                'file_samples_included': files_for_analysis.count('####'),
                'categories_included': len(self.analysis_context['categories']),
                'estimated_tokens': len(prompt.split()) * 1.3,  # Rough estimate
                'performance_ms': (end_time - start_time) * 1000
            }
            
            # Validate prompt structure
            validation_errors = []
            
            if len(prompt) > 100000:  # 100KB limit
                validation_errors.append(f"Prompt too large: {len(prompt)} chars")
            
            if '## PR Context' not in prompt:
                validation_errors.append("Missing PR Context section")
            
            if '## File Content & Functional Analysis' not in prompt:
                validation_errors.append("Missing file analysis section")
                
            if '## OUTPUT REQUIREMENTS' not in prompt:
                validation_errors.append("Missing output requirements section")
            
            if files_for_analysis.count('####') < 5:
                validation_errors.append(f"Too few file samples: {files_for_analysis.count('####')}")
            
            # Save prompt and analysis
            prompt_debug = {
                'agent': 'duplicate_detection',
                'prompt_stats': prompt_stats,
                'validation_errors': validation_errors,
                'context_summary': {
                    'total_files': len(self.analysis_context['files']),
                    'files_with_content': len([f for f in self.analysis_context['files'] if f.get('content_sample', '').strip()]),
                    'categories': list(self.analysis_context['categories'].keys())
                },
                'expected_discoveries': [
                    "Should find blog processing script duplicates",
                    "Should find database setup redundancy", 
                    "Should find nested content directories"
                ]
            }
            
            with open(self.test_output_dir / "duplicate_detection_prompt_debug.json", 'w') as f:
                json.dump(prompt_debug, f, indent=2)
            
            with open(self.test_output_dir / "duplicate_detection_prompt.txt", 'w') as f:
                f.write(prompt)
            
            print(f"✅ Duplicate Detection prompt generated:")
            print(f"   Length: {prompt_stats['total_length']:,} chars ({prompt_stats['estimated_tokens']:.0f} tokens)")
            print(f"   File samples: {prompt_stats['file_samples_included']}")
            print(f"   Categories: {prompt_stats['categories_included']}")
            print(f"   Performance: {prompt_stats['performance_ms']:.1f}ms")
            
            if validation_errors:
                print(f"   Validation errors: {len(validation_errors)}")
                for error in validation_errors:
                    print(f"     • {error}")
            
            return PromptTestResult(
                agent_name="duplicate_detection",
                prompt_length=prompt_stats['total_length'],
                context_size_kb=prompt_stats['context_section_length'] / 1024,
                file_count=prompt_stats['file_samples_included'],
                category_count=prompt_stats['categories_included'],
                generated_successfully=len(validation_errors) == 0,
                validation_errors=validation_errors,
                performance_ms=prompt_stats['performance_ms']
            )
            
        except Exception as e:
            print(f"❌ Duplicate detection prompt generation failed: {e}")
            return PromptTestResult(
                agent_name="duplicate_detection",
                prompt_length=0,
                context_size_kb=0,
                file_count=0,
                category_count=0,
                generated_successfully=False,
                validation_errors=[str(e)],
                performance_ms=0
            )
    
    def test_merge_readiness_prompt(self) -> PromptTestResult:
        """Test Merge Readiness Agent prompt generation"""
        print("\n🤖 Testing Merge Readiness Agent Prompt...")
        
        start_time = time.time()
        
        try:
            # Format categories and files for readiness analysis
            categories_formatted = self._format_categories_for_agent()
            files_formatted = self._format_files_for_agent(self.analysis_context['files'][:20])
            
            prompt = f"""You are a senior engineering manager evaluating whether this PR is ready to merge. Consider code quality, completeness, and potential risks.

## PR Overview
- Scope: {self.analysis_context['pr_summary']['total_files_changed']} files, +{self.analysis_context['pr_summary']['total_lines_added']}/-{self.analysis_context['pr_summary']['total_lines_removed']} lines
- Categories affected: {len(self.analysis_context['categories'])} different types of files

## Recent Commit Messages
{chr(10).join(self.analysis_context['pr_summary']['commit_messages'])}

## File Categories Analysis
{categories_formatted}

## Sample Files (First 20 for review)
{files_formatted}

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
            
            end_time = time.time()
            
            # Analyze prompt characteristics
            prompt_stats = {
                'total_length': len(prompt),
                'total_lines': len(prompt.split('\n')),
                'categories_section_length': len(categories_formatted),
                'files_section_length': len(files_formatted),
                'commit_messages_count': len(self.analysis_context['pr_summary']['commit_messages']),
                'estimated_tokens': len(prompt.split()) * 1.3,
                'performance_ms': (end_time - start_time) * 1000
            }
            
            # Validate prompt structure
            validation_errors = []
            
            if len(prompt) > 50000:  # 50KB limit for readiness
                validation_errors.append(f"Prompt too large: {len(prompt)} chars")
            
            if '"merge_readiness_score"' not in prompt:
                validation_errors.append("Missing JSON response format")
            
            if '## PR Overview' not in prompt:
                validation_errors.append("Missing PR overview section")
            
            if files_formatted.count('##') < 5:
                validation_errors.append(f"Too few file samples: {files_formatted.count('##')}")
            
            # Save prompt and analysis
            prompt_debug = {
                'agent': 'merge_readiness',
                'prompt_stats': prompt_stats,
                'validation_errors': validation_errors,
                'expected_outcomes': {
                    'score_range': '60-80 (REVIEW_NEEDED)',
                    'key_issues': ['Large PR size', 'Mixed concerns', 'Configuration redundancy'],
                    'should_flag': ['Incomplete refactoring', 'Multiple similar files']
                }
            }
            
            with open(self.test_output_dir / "merge_readiness_prompt_debug.json", 'w') as f:
                json.dump(prompt_debug, f, indent=2)
            
            with open(self.test_output_dir / "merge_readiness_prompt.txt", 'w') as f:
                f.write(prompt)
            
            print(f"✅ Merge Readiness prompt generated:")
            print(f"   Length: {prompt_stats['total_length']:,} chars ({prompt_stats['estimated_tokens']:.0f} tokens)")
            print(f"   Commit messages: {prompt_stats['commit_messages_count']}")
            print(f"   Categories section: {prompt_stats['categories_section_length']:,} chars")
            print(f"   Performance: {prompt_stats['performance_ms']:.1f}ms")
            
            if validation_errors:
                print(f"   Validation errors: {len(validation_errors)}")
                for error in validation_errors:
                    print(f"     • {error}")
            
            return PromptTestResult(
                agent_name="merge_readiness",
                prompt_length=prompt_stats['total_length'],
                context_size_kb=(prompt_stats['categories_section_length'] + prompt_stats['files_section_length']) / 1024,
                file_count=20,  # Fixed sample size
                category_count=len(self.analysis_context['categories']),
                generated_successfully=len(validation_errors) == 0,
                validation_errors=validation_errors,
                performance_ms=prompt_stats['performance_ms']
            )
            
        except Exception as e:
            print(f"❌ Merge readiness prompt generation failed: {e}")
            return PromptTestResult(
                agent_name="merge_readiness",
                prompt_length=0,
                context_size_kb=0,
                file_count=0,
                category_count=0,
                generated_successfully=False,
                validation_errors=[str(e)],
                performance_ms=0
            )
    
    def test_pattern_analysis_prompt(self) -> PromptTestResult:
        """Test Pattern Analysis Agent prompt generation"""
        print("\n📐 Testing Pattern Analysis Agent Prompt...")
        
        start_time = time.time()
        
        try:
            # For now, create a basic pattern analysis prompt
            prompt = f"""You are a senior software architect analyzing code patterns and consistency across this PR.

## PR Context
- Analyzing: {self.analysis_context['pr_summary']['total_files_changed']} files
- Categories: {len(self.analysis_context['categories'])} different types

## Analysis Focus
Look for patterns and consistency issues:

1. **Naming Conventions**
   - File naming patterns
   - Variable and function naming
   - Directory structure consistency

2. **Architecture Patterns**
   - Similar functionality implemented differently
   - Inconsistent approaches to the same problems
   - Missing architectural patterns

3. **Code Style**
   - Formatting inconsistencies
   - Different coding patterns for similar tasks
   - Inconsistent error handling approaches

## Sample File Analysis
{self._format_files_for_agent(self.analysis_context['files'][:10])}

## Output Format
Identify specific pattern issues with recommendations for improvement.
"""
            
            end_time = time.time()
            
            prompt_stats = {
                'total_length': len(prompt),
                'performance_ms': (end_time - start_time) * 1000
            }
            
            # Save prompt
            with open(self.test_output_dir / "pattern_analysis_prompt.txt", 'w') as f:
                f.write(prompt)
            
            print(f"✅ Pattern Analysis prompt generated:")
            print(f"   Length: {prompt_stats['total_length']:,} chars")
            print(f"   Performance: {prompt_stats['performance_ms']:.1f}ms")
            print(f"   Note: Basic implementation - can be enhanced later")
            
            return PromptTestResult(
                agent_name="pattern_analysis",
                prompt_length=prompt_stats['total_length'],
                context_size_kb=len(prompt) / 1024,
                file_count=10,
                category_count=len(self.analysis_context['categories']),
                generated_successfully=True,
                validation_errors=[],
                performance_ms=prompt_stats['performance_ms']
            )
            
        except Exception as e:
            print(f"❌ Pattern analysis prompt generation failed: {e}")
            return PromptTestResult(
                agent_name="pattern_analysis",
                prompt_length=0,
                context_size_kb=0,
                file_count=0,
                category_count=0,
                generated_successfully=False,
                validation_errors=[str(e)],
                performance_ms=0
            )
    
    def _prepare_files_for_content_analysis(self) -> str:
        """Prepare detailed file content for intelligent analysis (from original code)"""
        analysis_sections = []
        
        # Group files by category for focused analysis
        for category, files in self.analysis_context['categories'].items():
            if not files or category == 'GENERATED_IRRELEVANT':
                continue
                
            analysis_sections.append(f"\n### {category} FILES ({len(files)} files)")
            
            # Analyze up to 10 files per category for performance
            for file_data in files[:10]:
                analysis_sections.append(f"\n#### {file_data['path']}")
                analysis_sections.append(f"- Change: {file_data['change_type']} (+{file_data['lines_added']}/-{file_data['lines_removed']})")
                analysis_sections.append(f"- Size: {file_data['size']} bytes")
                
                # Add content sample if available
                if file_data.get('content_sample'):
                    analysis_sections.append(f"- Content analysis:")
                    analysis_sections.append("```")
                    analysis_sections.append(file_data['content_sample'][:1000])  # Limit to 1KB
                    if len(file_data['content_sample']) > 1000:
                        analysis_sections.append("... [truncated for analysis]")
                    analysis_sections.append("```")
                else:
                    analysis_sections.append(f"- Content: [No content sample available]")
        
        return '\n'.join(analysis_sections)
    
    def _format_categories_for_agent(self) -> str:
        """Format category information for agent consumption"""
        lines = []
        for category, files in self.analysis_context['categories'].items():
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
        """Format file information for agent analysis"""
        lines = []
        for file in files:
            lines.append(f"## {file['path']}")
            lines.append(f"- Category: {file['category']} ({file.get('importance', 'UNKNOWN')})")
            lines.append(f"- Change: {file['change_type']} (+{file['lines_added']}/-{file['lines_removed']})")
            lines.append(f"- Size: {file['size']} bytes, {file.get('total_lines', 0)} lines")
            
            if file.get('content_sample'):
                lines.append(f"- Content sample:")
                lines.append(f"```")
                lines.append(file['content_sample'][:500])  # Limit sample size
                if len(file['content_sample']) > 500:
                    lines.append("... [truncated]")
                lines.append(f"```")
            lines.append("")
        return '\n'.join(lines)
    
    def run_full_stage2_test(self) -> Dict[str, PromptTestResult]:
        """Run complete Stage 2 testing pipeline"""
        print("=" * 60)
        print("🧪 STAGE 2: AGENT PROMPT GENERATION TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test all three agent prompts
        results['duplicate_detection'] = self.test_duplicate_detection_prompt()
        results['merge_readiness'] = self.test_merge_readiness_prompt()
        results['pattern_analysis'] = self.test_pattern_analysis_prompt()
        
        # Generate overall statistics
        total_prompt_size = sum(r.prompt_length for r in results.values())
        successful_prompts = sum(1 for r in results.values() if r.generated_successfully)
        total_validation_errors = sum(len(r.validation_errors) for r in results.values())
        total_performance = sum(r.performance_ms for r in results.values())
        
        stage2_summary = {
            'stage': 'Agent Prompt Generation',
            'agents_tested': len(results),
            'successful_prompts': successful_prompts,
            'total_prompt_size': total_prompt_size,
            'total_validation_errors': total_validation_errors,
            'total_performance_ms': total_performance,
            'results_by_agent': {name: {
                'success': result.generated_successfully,
                'prompt_length': result.prompt_length,
                'validation_errors': len(result.validation_errors)
            } for name, result in results.items()},
            'ready_for_stage3': successful_prompts == len(results) and total_validation_errors == 0
        }
        
        with open(self.test_output_dir / "stage2_test_summary.json", 'w') as f:
            json.dump(stage2_summary, f, indent=2)
        
        print(f"\n✅ STAGE 2 COMPLETE:")
        print(f"   Agents tested: {len(results)}")
        print(f"   Successful: {successful_prompts}")
        print(f"   Total prompt size: {total_prompt_size:,} chars")
        print(f"   Validation errors: {total_validation_errors}")
        print(f"   Total time: {total_performance:.1f}ms")
        print(f"   Debug outputs saved to: {self.test_output_dir}")
        
        if stage2_summary['ready_for_stage3']:
            print(f"\n🎉 Stage 2 successful! Ready for Stage 3: Agent Communication")
        else:
            print(f"\n⚠️  Stage 2 has issues - check validation errors before proceeding")
        
        return results


def main():
    """Test Stage 2: Agent Prompt Generation"""
    try:
        tester = AgentPromptTester()
        results = tester.run_full_stage2_test()
        
        # Check if ready to proceed
        all_successful = all(r.generated_successfully for r in results.values())
        
        if all_successful:
            print(f"\n🎉 Stage 2 testing successful!")
            print(f"Ready to proceed to Stage 3: Agent Communication")
        else:
            print(f"\n❌ Stage 2 testing had issues:")
            for name, result in results.items():
                if not result.generated_successfully:
                    print(f"   • {name}: {result.validation_errors}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Stage 2 testing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
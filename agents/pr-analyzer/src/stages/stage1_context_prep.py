#!/usr/bin/env python3
"""
Stage 1: Context Preparation Testing
Test the context preparation stage with full visibility and debugging
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ..core.git_analyzer import GitAnalyzer
from ..classifiers.file_classifier import FileClassifier


@dataclass
class ContextTestResult:
    """Results from context preparation testing"""
    success: bool
    total_files: int
    files_with_content: int
    files_by_category: Dict[str, int]
    sample_files: List[Dict]
    errors: List[str]
    performance_ms: float


class ContextPreparationTester:
    """Test Stage 1: Context Preparation with full visibility"""
    
    def __init__(self, repo_path: str, output_dir: str = None):
        self.repo_path = Path(repo_path).resolve()
        if output_dir:
            self.test_output_dir = Path(output_dir) / "debug_outputs" / "stage1"
        else:
            self.test_output_dir = Path(__file__).parent / "debug_outputs" / "stage1"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        config_dir = Path(__file__).parent / 'config'
        self.config = self._load_config(config_dir)
        
        # Initialize components
        self.git_analyzer = GitAnalyzer(str(self.repo_path))
        self.file_classifier = FileClassifier(self.config)
    
    def _load_config(self, config_dir: Path) -> Dict[str, Any]:
        """Load configuration files"""
        config = {}
        
        # Load categories
        categories_file = config_dir / 'categories.json'
        if categories_file.exists():
            with open(categories_file, 'r') as f:
                config['categories'] = json.load(f)
        else:
            print(f"⚠️  Categories config not found at {categories_file}")
            config['categories'] = {}
        
        return config
    
    def test_git_analysis(self, from_branch: str, to_branch: str) -> Dict[str, Any]:
        """Test Stage 1a: Git Analysis"""
        print("🔍 Testing Git Analysis...")
        
        try:
            import time
            start_time = time.time()
            
            pr_analysis = self.git_analyzer.analyze_pr(from_branch, to_branch, include_diffs=False)
            
            # Define analysis files early for use in debug output
            analysis_files = pr_analysis.file_changes_excluding_analysis or pr_analysis.file_changes
            # Filter out deleted files - they shouldn't be analyzed for duplicates since they're being removed
            analysis_files = [fc for fc in analysis_files if fc.change_type != 'D']
            
            end_time = time.time()
            
            # Debug output
            git_debug = {
                'from_branch': pr_analysis.from_branch,
                'to_branch': pr_analysis.to_branch,
                # All files (including PR analysis outputs)
                'total_files_changed': pr_analysis.total_files_changed,
                'total_lines_added': pr_analysis.total_lines_added,
                'total_lines_removed': pr_analysis.total_lines_removed,
                # Filtered files (excluding PR analysis outputs) - used for recommendations
                'total_files_changed_excluding_analysis': pr_analysis.total_files_changed_excluding_analysis,
                'total_lines_added_excluding_analysis': pr_analysis.total_lines_added_excluding_analysis,
                'total_lines_removed_excluding_analysis': pr_analysis.total_lines_removed_excluding_analysis,
                'file_changes_sample': [
                    {
                        'file_path': fc.file_path,
                        'change_type': fc.change_type,
                        'lines_added': fc.lines_added,
                        'lines_removed': fc.lines_removed
                    }
                    for fc in pr_analysis.file_changes[:10]  # First 10 files
                ],
                'analysis_files_sample': [
                    {
                        'file_path': fc.file_path,
                        'change_type': fc.change_type,
                        'lines_added': fc.lines_added,
                        'lines_removed': fc.lines_removed
                    }
                    for fc in analysis_files[:10]  # First 10 analysis files
                ],
                'commit_messages_sample': pr_analysis.commit_messages[:5],
                'performance_ms': (end_time - start_time) * 1000
            }
            
            # Save debug output
            with open(self.test_output_dir / "git_analysis_debug.json", 'w') as f:
                json.dump(git_debug, f, indent=2)
            
            print(f"✅ Git analysis completed:")
            print(f"   All files: {pr_analysis.total_files_changed} files, +{pr_analysis.total_lines_added}/-{pr_analysis.total_lines_removed} lines")
            print(f"   For analysis: {pr_analysis.total_files_changed_excluding_analysis} files, +{pr_analysis.total_lines_added_excluding_analysis}/-{pr_analysis.total_lines_removed_excluding_analysis} lines")
            print(f"   Performance: {git_debug['performance_ms']:.1f}ms")
            
            return {
                'success': True,
                'pr_analysis': pr_analysis,
                'debug_info': git_debug
            }
            
        except Exception as e:
            print(f"❌ Git analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_file_classification(self, pr_analysis) -> Dict[str, Any]:
        """Test Stage 1b: File Classification"""
        print("📂 Testing File Classification...")
        
        try:
            import time
            start_time = time.time()
            
            # Define analysis files for this method
            analysis_files = pr_analysis.file_changes_excluding_analysis or pr_analysis.file_changes
            
            # Filter out deleted files - they shouldn't be analyzed for duplicates since they're being removed
            analysis_files = [fc for fc in analysis_files if fc.change_type != 'D']
            
            classified_files = []
            classification_debug = {
                'categories': {},
                'classification_errors': [],
                'deleted_files_filtered': len((pr_analysis.file_changes_excluding_analysis or pr_analysis.file_changes)) - len(analysis_files)
            }
            
            for file_change in analysis_files:
                try:
                    classified_file = self.file_classifier.classify_file(file_change.file_path)
                    classified_files.append(classified_file)
                    
                    # Track categories
                    category = classified_file.category
                    if category not in classification_debug['categories']:
                        classification_debug['categories'][category] = 0
                    classification_debug['categories'][category] += 1
                    
                except Exception as e:
                    classification_debug['classification_errors'].append({
                        'file': file_change.file_path,
                        'error': str(e)
                    })
            
            # Generate category summary
            category_summary = self.file_classifier.generate_category_summary(classified_files)
            
            end_time = time.time()
            classification_debug['performance_ms'] = (end_time - start_time) * 1000
            classification_debug['total_files_classified'] = len(classified_files)
            classification_debug['category_summary'] = category_summary
            
            # Sample classified files for debugging
            classification_debug['sample_classified_files'] = [
                {
                    'file_path': cf.file_path,
                    'category': cf.category,
                    'importance': cf.importance,
                    'icon': cf.icon,
                    'description': cf.description
                }
                for cf in classified_files[:15]  # First 15 files
            ]
            
            # Save debug output
            with open(self.test_output_dir / "file_classification_debug.json", 'w') as f:
                json.dump(classification_debug, f, indent=2)
            
            print(f"✅ File classification completed:")
            print(f"   Files classified: {len(classified_files)}")
            print(f"   Categories found: {len(classification_debug['categories'])}")
            print(f"   Performance: {classification_debug['performance_ms']:.1f}ms")
            
            # Show category breakdown
            for category, count in classification_debug['categories'].items():
                print(f"   {category}: {count} files")
            
            return {
                'success': True,
                'classified_files': classified_files,
                'category_summary': category_summary,
                'debug_info': classification_debug
            }
            
        except Exception as e:
            print(f"❌ File classification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_content_analysis(self, classified_files, pr_analysis) -> Dict[str, Any]:
        """Test Stage 1c: Content Analysis (most critical for agents)"""
        print("📖 Testing Content Analysis...")
        
        try:
            import time
            start_time = time.time()
            
            content_debug = {
                'files_analyzed': 0,
                'files_with_content': 0,
                'files_too_large': 0,
                'files_missing': 0,
                'content_errors': [],
                'category_content_samples': {}
            }
            
            # Analyze file contents (this is what agents need)
            file_info = []
            for classified_file in classified_files:  # Analyze ALL files - no artificial limits
                file_path = Path(self.repo_path) / classified_file.file_path
                
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
                
                content_debug['files_analyzed'] += 1
                
                # Read content for analysis
                if file_path.exists() and file_path.stat().st_size < 50000:  # < 50KB
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Clean content
                        clean_content = content.replace('\x00', '').replace('\r\n', '\n')
                        
                        # Add content sample
                        file_data['content_sample'] = clean_content[:1000] if len(clean_content) > 1000 else clean_content
                        file_data['total_lines'] = len(content.split('\n'))
                        file_data['has_functions'] = 'def ' in content or 'function ' in content
                        file_data['has_classes'] = 'class ' in content or 'className=' in content
                        file_data['has_imports'] = 'import ' in content or 'require(' in content
                        
                        content_debug['files_with_content'] += 1
                        
                        # Store category samples for agent debugging
                        category = classified_file.category
                        if category not in content_debug['category_content_samples']:
                            content_debug['category_content_samples'][category] = []
                        
                        if len(content_debug['category_content_samples'][category]) < 3:  # Max 3 samples per category
                            content_debug['category_content_samples'][category].append({
                                'file': classified_file.file_path,
                                'sample': file_data['content_sample'][:200],  # First 200 chars
                                'has_functions': file_data['has_functions'],
                                'has_classes': file_data['has_classes']
                            })
                        
                    except Exception as e:
                        file_data['content_sample'] = '[Error reading file]'
                        file_data['total_lines'] = 0
                        content_debug['content_errors'].append({
                            'file': classified_file.file_path,
                            'error': str(e)
                        })
                        
                elif file_path.exists():
                    file_data['content_sample'] = '[File too large]'
                    file_data['total_lines'] = 0
                    content_debug['files_too_large'] += 1
                else:
                    file_data['content_sample'] = '[File missing]'
                    file_data['total_lines'] = 0
                    content_debug['files_missing'] += 1
                
                file_info.append(file_data)
            
            end_time = time.time()
            content_debug['performance_ms'] = (end_time - start_time) * 1000
            
            # Save detailed debug output
            with open(self.test_output_dir / "content_analysis_debug.json", 'w') as f:
                json.dump(content_debug, f, indent=2)
            
            # Save file info for agent testing
            with open(self.test_output_dir / "file_info_for_agents.json", 'w') as f:
                json.dump(file_info[:10], f, indent=2)  # First 10 files with full content
            
            print(f"✅ Content analysis completed:")
            print(f"   Files analyzed: {content_debug['files_analyzed']}")
            print(f"   Files with content: {content_debug['files_with_content']}")
            print(f"   Files too large: {content_debug['files_too_large']}")
            print(f"   Files missing: {content_debug['files_missing']}")
            print(f"   Content errors: {len(content_debug['content_errors'])}")
            print(f"   Performance: {content_debug['performance_ms']:.1f}ms")
            
            return {
                'success': True,
                'file_info': file_info,
                'debug_info': content_debug
            }
            
        except Exception as e:
            print(f"❌ Content analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_context_assembly(self, pr_analysis, file_info) -> Dict[str, Any]:
        """Test Stage 1d: Final Context Assembly"""
        print("🔧 Testing Context Assembly...")
        
        try:
            import time
            start_time = time.time()
            
            # Group files by category for agent consumption
            categories = {}
            for file_data in file_info:
                category = file_data['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(file_data)
            
            # Build final analysis context (what gets passed to agents)
            analysis_context = {
                'pr_summary': {
                    'from_branch': pr_analysis.from_branch,
                    'to_branch': pr_analysis.to_branch,
                    # Use filtered statistics for agent analysis (excluding PR analysis files)
                    'total_files_changed': pr_analysis.total_files_changed_excluding_analysis,
                    'total_lines_added': pr_analysis.total_lines_added_excluding_analysis,
                    'total_lines_removed': pr_analysis.total_lines_removed_excluding_analysis,
                    # Also include full stats for transparency
                    'total_files_changed_all': pr_analysis.total_files_changed,
                    'total_lines_added_all': pr_analysis.total_lines_added,
                    'total_lines_removed_all': pr_analysis.total_lines_removed,
                    'commit_messages': pr_analysis.commit_messages[:10]  # First 10 commits
                },
                'files': file_info,
                'categories': categories,
                'repo_path': str(self.repo_path)
            }
            
            end_time = time.time()
            
            # Generate assembly statistics
            assembly_debug = {
                'total_files_in_context': len(file_info),
                'categories_found': len(categories),
                'category_breakdown': {cat: len(files) for cat, files in categories.items()},
                'context_size_kb': len(json.dumps(analysis_context)) / 1024,
                'performance_ms': (end_time - start_time) * 1000
            }
            
            # Save the full context that would be passed to agents (ESSENTIAL OUTPUT)
            from ..utils.path_utils import get_main_output_dir
            main_output_dir = get_main_output_dir(self.test_output_dir)
            with open(main_output_dir / "final_analysis_context.json", 'w') as f:
                json.dump(analysis_context, f, indent=2)
            # Also save in debug folder for troubleshooting
            with open(self.test_output_dir / "final_analysis_context.json", 'w') as f:
                json.dump(analysis_context, f, indent=2)
            
            # Save assembly debug info
            with open(self.test_output_dir / "context_assembly_debug.json", 'w') as f:
                json.dump(assembly_debug, f, indent=2)
            
            print(f"✅ Context assembly completed:")
            print(f"   Files in context: {assembly_debug['total_files_in_context']}")
            print(f"   Categories: {assembly_debug['categories_found']}")
            print(f"   Context size: {assembly_debug['context_size_kb']:.1f} KB")
            print(f"   Performance: {assembly_debug['performance_ms']:.1f}ms")
            
            # Show category breakdown
            for category, count in assembly_debug['category_breakdown'].items():
                print(f"   {category}: {count} files")
            
            return {
                'success': True,
                'analysis_context': analysis_context,
                'debug_info': assembly_debug
            }
            
        except Exception as e:
            print(f"❌ Context assembly failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_full_stage1_test(self, from_branch: str = "feature/image_transcription", to_branch: str = "main") -> ContextTestResult:
        """Run complete Stage 1 testing pipeline"""
        print("=" * 60)
        print("🧪 STAGE 1: CONTEXT PREPARATION TESTING")
        print("=" * 60)
        
        errors = []
        start_time = time.time()
        
        # Test 1a: Git Analysis
        git_result = self.test_git_analysis(from_branch, to_branch)
        if not git_result['success']:
            errors.append(f"Git analysis: {git_result['error']}")
            return ContextTestResult(False, 0, 0, {}, [], errors, 0)
        
        pr_analysis = git_result['pr_analysis']
        
        # Test 1b: File Classification
        classification_result = self.test_file_classification(pr_analysis)
        if not classification_result['success']:
            errors.append(f"File classification: {classification_result['error']}")
            return ContextTestResult(False, 0, 0, {}, [], errors, 0)
        
        classified_files = classification_result['classified_files']
        
        # Test 1c: Content Analysis
        content_result = self.test_content_analysis(classified_files, pr_analysis)
        if not content_result['success']:
            errors.append(f"Content analysis: {content_result['error']}")
            return ContextTestResult(False, 0, 0, {}, [], errors, 0)
        
        file_info = content_result['file_info']
        
        # Test 1d: Context Assembly
        assembly_result = self.test_context_assembly(pr_analysis, file_info)
        if not assembly_result['success']:
            errors.append(f"Context assembly: {assembly_result['error']}")
            return ContextTestResult(False, 0, 0, {}, [], errors, 0)
        
        end_time = time.time()
        
        # Generate final test results
        files_by_category = {}
        files_with_content = 0
        
        for file_data in file_info:
            category = file_data['category']
            files_by_category[category] = files_by_category.get(category, 0) + 1
            
            if file_data.get('content_sample') and '[Error' not in file_data['content_sample']:
                files_with_content += 1
        
        # Compare against manual analysis
        print("\n🔍 COMPARISON WITH MANUAL ANALYSIS:")
        expected_duplicates = [
            'content/auto_blog_processor.py',
            'content/automated_blog_processor.py',
            'content/batch_process_all_posts.py'
        ]
        
        found_blog_files = [
            f['path'] for f in file_info 
            if 'blog' in f['path'].lower() and f['path'].endswith('.py')
        ]
        
        print(f"   Expected blog processors: {len(expected_duplicates)}")
        print(f"   Found blog processors: {len(found_blog_files)}")
        print(f"   Blog files found: {found_blog_files[:5]}...")  # First 5
        
        # Save comprehensive test results
        test_summary = {
            'stage': 'Context Preparation',
            'success': True,
            'total_files': len(file_info),
            'files_with_content': files_with_content,
            'files_by_category': files_by_category,
            'performance_ms': (end_time - start_time) * 1000,
            'comparison_with_manual': {
                'expected_blog_processors': expected_duplicates,
                'found_blog_files': found_blog_files,
                'match_rate': len(found_blog_files) / len(expected_duplicates) if expected_duplicates else 0
            }
        }
        
        with open(self.test_output_dir / "stage1_test_summary.json", 'w') as f:
            json.dump(test_summary, f, indent=2)
        
        print(f"\n✅ STAGE 1 COMPLETE:")
        print(f"   Total files processed: {len(file_info)}")
        print(f"   Files with content: {files_with_content}")
        print(f"   Categories identified: {len(files_by_category)}")
        print(f"   Total time: {test_summary['performance_ms']:.1f}ms")
        print(f"   Debug outputs saved to: {self.test_output_dir}")
        
        return ContextTestResult(
            success=True,
            total_files=len(file_info),
            files_with_content=files_with_content,
            files_by_category=files_by_category,
            sample_files=file_info[:5],
            errors=errors,
            performance_ms=test_summary['performance_ms']
        )


def main():
    """Test Stage 1: Context Preparation"""
    # Test with the website repo
    repo_path = "/home/asabaal/asabaal_ventures/repos/multisensory-experience-website"
    
    tester = ContextPreparationTester(repo_path)
    result = tester.run_full_stage1_test()
    
    if result.success:
        print(f"\n🎉 Stage 1 testing successful!")
        print(f"Ready to proceed to Stage 2: Agent Prompt Generation")
    else:
        print(f"\n❌ Stage 1 testing failed:")
        for error in result.errors:
            print(f"   • {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
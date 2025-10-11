#!/usr/bin/env python3
"""
Test the duplicate detection agent in isolation
Compare its output against our manual reference analysis
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.agentic_quality_analyzer import AgenticQualityAnalyzer

def test_duplicate_detection_agent():
    """Test the agent with our brand-integration PR data"""
    
    print("🧪 Testing Duplicate Detection Agent")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = AgenticQualityAnalyzer({})
    
    # Prepare test context (simplified version of what main system does)
    repo_path = "/home/asabaal/asabaal_ventures/repos/multisensory-experience-website"
    
    # Simulate the context data the agent receives
    test_context = {
        'pr_summary': {
            'from_branch': 'brand-integration',
            'to_branch': 'main', 
            'total_files_changed': 257,
            'total_lines_added': 48149,
            'total_lines_removed': 3543,
            'commit_messages': ['blog post preparer tested and working', 'blog post convupgrader agent pipeline functional']
        },
        'files': [
            # Focus on the Python files we know are duplicates
            {'path': 'content/batch_process_all_posts.py', 'category': 'AUTOMATION', 'importance': 'HIGH', 'icon': '🤖', 'description': 'Blog processing automation', 'change_type': 'A', 'lines_added': 150, 'lines_removed': 0, 'exists': True, 'size': 5000},
            {'path': 'content/batch_process_all_posts_verbose.py', 'category': 'AUTOMATION', 'importance': 'HIGH', 'icon': '🤖', 'description': 'Blog processing automation', 'change_type': 'A', 'lines_added': 180, 'lines_removed': 0, 'exists': True, 'size': 6000},
            {'path': 'content/batch_process_simple.py', 'category': 'AUTOMATION', 'importance': 'MEDIUM', 'icon': '🤖', 'description': 'Blog processing automation', 'change_type': 'A', 'lines_added': 80, 'lines_removed': 0, 'exists': True, 'size': 3000},
            {'path': 'content/automated_claude_processor.py', 'category': 'AUTOMATION', 'importance': 'HIGH', 'icon': '🤖', 'description': 'Claude automation core', 'change_type': 'A', 'lines_added': 200, 'lines_removed': 0, 'exists': True, 'size': 8000},
            {'path': 'content/claude_blog_processor.py', 'category': 'AUTOMATION', 'importance': 'MEDIUM', 'icon': '🤖', 'description': 'Claude blog wrapper', 'change_type': 'A', 'lines_added': 120, 'lines_removed': 0, 'exists': True, 'size': 4000},
            {'path': 'content/simple_blog_processor.py', 'category': 'AUTOMATION', 'importance': 'LOW', 'icon': '🤖', 'description': 'Simple blog processor', 'change_type': 'A', 'lines_added': 60, 'lines_removed': 0, 'exists': True, 'size': 2000},
        ],
        'categories': {
            'AUTOMATION': [
                {'path': 'content/batch_process_all_posts.py', 'category': 'AUTOMATION', 'change_type': 'A'},
                {'path': 'content/batch_process_all_posts_verbose.py', 'category': 'AUTOMATION', 'change_type': 'A'},
                {'path': 'content/batch_process_simple.py', 'category': 'AUTOMATION', 'change_type': 'A'},
                {'path': 'content/automated_claude_processor.py', 'category': 'AUTOMATION', 'change_type': 'A'},
                {'path': 'content/claude_blog_processor.py', 'category': 'AUTOMATION', 'change_type': 'A'},
                {'path': 'content/simple_blog_processor.py', 'category': 'AUTOMATION', 'change_type': 'A'},
            ]
        },
        'repo_path': repo_path
    }
    
    print("📋 Test Context Prepared")
    print(f"   Repository: {repo_path}")
    print(f"   Files to analyze: {len(test_context['files'])}")
    print(f"   Categories: {list(test_context['categories'].keys())}")
    
    print("\n🤖 Launching Duplicate Detection Agent...")
    
    # Call the agent directly
    try:
        import traceback
        result = analyzer._launch_duplicate_detection_agent(test_context, repo_path)
        
        print(f"\n📊 Agent Results:")
        print(f"   Issues found: {len(result.get('issues', []))}")
        
        for i, issue in enumerate(result.get('issues', []), 1):
            print(f"\n   Issue {i}:")
            print(f"   ├─ Severity: {issue.severity}")
            print(f"   ├─ Category: {issue.category}")
            print(f"   ├─ Title: {issue.title}")
            print(f"   ├─ Description: {issue.description[:100]}...")
            print(f"   ├─ Affected Files: {len(issue.affected_files)} files")
            print(f"   └─ Recommendation: {issue.recommendation[:100]}...")
        
        insights = result.get('insights', {})
        if insights:
            print(f"\n🔍 Agent Insights:")
            for key, value in insights.items():
                print(f"   {key}: {value}")
        
        return result
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        traceback.print_exc()
        return None

def compare_with_manual_analysis():
    """Compare agent results with our manual reference"""
    
    print("\n" + "=" * 50)
    print("📊 COMPARISON WITH MANUAL ANALYSIS")
    print("=" * 50)
    
    print("\n🎯 EXPECTED (Manual Analysis):")
    print("   ├─ Should find: Blog processing script cluster (6 files)")
    print("   ├─ Should identify: batch_process_all_posts.py variations")
    print("   ├─ Should detect: Claude processor wrappers")
    print("   ├─ Should provide: Specific code evidence")
    print("   └─ Should recommend: Consolidation strategies")
    
    print("\n🤖 ACTUAL (Agent Output):")
    print("   └─ [Results from agent test above]")
    
    print("\n📋 EVALUATION CRITERIA:")
    print("   ✅ Does it find the blog processing duplicates?")
    print("   ✅ Does it identify functional similarity (not just filename)?") 
    print("   ✅ Does it provide specific code evidence?")
    print("   ✅ Does it recommend consolidation?")
    print("   ✅ Is the analysis actionable and useful?")

if __name__ == "__main__":
    # Run the test
    result = test_duplicate_detection_agent()
    
    # Compare with manual analysis  
    compare_with_manual_analysis()
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Examine agent output quality")
    print(f"   2. Debug any issues with Claude CLI calls")
    print(f"   3. Improve prompts/parsing if needed")
    print(f"   4. Iterate until agent matches manual analysis")
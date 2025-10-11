#!/usr/bin/env python3
"""Test ONLY the duplicate detection agent"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.agentic_quality_analyzer import AgenticQualityAnalyzer

def test_duplicate_agent_only():
    """Test just the duplicate detection agent in isolation"""
    
    print("🧪 Testing DUPLICATE DETECTION AGENT Only")
    print("=" * 50)
    
    analyzer = AgenticQualityAnalyzer({})
    
    # Simple test context with known duplicates
    test_context = {
        'pr_summary': {
            'from_branch': 'brand-integration',
            'to_branch': 'main',
            'total_files_changed': 6,
            'total_lines_added': 1000,
            'total_lines_removed': 100,
            'commit_messages': ['blog automation']
        },
        'files': [
            {'path': 'content/batch_process_all_posts.py', 'category': 'AUTOMATION', 'importance': 'HIGH', 'icon': '🤖', 'description': 'Blog processing', 'change_type': 'A', 'lines_added': 150, 'lines_removed': 0, 'exists': True, 'size': 5000, 'total_lines': 100},
            {'path': 'content/batch_process_all_posts_verbose.py', 'category': 'AUTOMATION', 'importance': 'HIGH', 'icon': '🤖', 'description': 'Blog processing verbose', 'change_type': 'A', 'lines_added': 180, 'lines_removed': 0, 'exists': True, 'size': 6000, 'total_lines': 120},
        ],
        'categories': {
            'AUTOMATION': [
                {'path': 'content/batch_process_all_posts.py', 'category': 'AUTOMATION'},
                {'path': 'content/batch_process_all_posts_verbose.py', 'category': 'AUTOMATION'},
            ]
        }
    }
    
    repo_path = "/home/asabaal/asabaal_ventures/repos/multisensory-experience-website"
    
    print("🤖 Testing duplicate detection agent...")
    
    try:
        result = analyzer._launch_duplicate_detection_agent(test_context, repo_path)
        print("✅ Agent completed successfully")
        print(f"📊 Issues found: {len(result.get('issues', []))}")
        
        for issue in result.get('issues', []):
            print(f"   - {issue.severity}: {issue.title}")
            print(f"     Files: {issue.affected_files}")
            
    except Exception as e:
        print(f"❌ Agent failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duplicate_agent_only()
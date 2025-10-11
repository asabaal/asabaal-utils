#!/usr/bin/env python3
"""
Simple test - just test the agent call directly
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.agentic_quality_analyzer import AgenticQualityAnalyzer

def test_agent_call():
    """Test the agent call directly with a simple prompt"""
    
    print("🧪 Testing Agent Call Directly")
    print("=" * 50)
    
    analyzer = AgenticQualityAnalyzer({})
    
    # Simple test prompt
    test_prompt = """
You are testing the OpenRouter API integration. 

Analyze these duplicate files:

## File 1: batch_process_all_posts.py
- Purpose: Process all blog posts in batch
- Main function: Calls subprocess to run automated_claude_processor.py
- Key code: subprocess.run([sys.executable, "automated_claude_processor.py", post])

## File 2: batch_process_all_posts_verbose.py  
- Purpose: Process all blog posts in batch with verbose output
- Main function: Calls subprocess to run automated_claude_processor.py
- Key code: subprocess.run([sys.executable, "automated_claude_processor.py", post])

## File 3: batch_process_simple.py
- Purpose: Simple batch processing of blog posts
- Main function: Calls subprocess to run automated_claude_processor.py  
- Key code: subprocess.run([sys.executable, "automated_claude_processor.py", post])

TASK: Identify that these three files are functional duplicates that all batch process blog posts using the same underlying mechanism.

Provide a clear analysis of their similarity and recommend consolidation.
"""
    
    print("📋 Test Prompt Prepared")
    print(f"   Length: {len(test_prompt)} characters")
    
    print("\n🤖 Calling Agent via OpenRouter API...")
    
    try:
        # Test the agent call directly
        result = analyzer._call_agent(test_prompt)
        
        if result:
            print(f"✅ Agent Call Success!")
            print(f"   Response length: {len(result)} characters")
            print(f"\n📄 Agent Response:")
            print("-" * 50)
            print(result)
            print("-" * 50)
            
            # Check if it found the duplicates
            if "duplicate" in result.lower() or "similar" in result.lower():
                print(f"\n✅ Response mentions duplicates/similarity")
            else:
                print(f"\n❌ Response doesn't mention duplicates")
                
            if "batch_process" in result:
                print(f"✅ Response mentions our test files")
            else:
                print(f"❌ Response doesn't mention our test files")
                
        else:
            print(f"❌ Agent Call returned None")
            
    except Exception as e:
        print(f"❌ Agent call failed: {e}")
        import traceback
        traceback.print_exc()

def test_parsing():
    """Test how the response gets parsed"""
    
    print(f"\n" + "=" * 50)
    print("🔍 Testing Response Parsing")
    print("=" * 50)
    
    # Mock a good agent response
    mock_response = """
I can see these files are functional duplicates:

HIGH SEVERITY: Blog Processing Script Duplicates

Files: batch_process_all_posts.py, batch_process_all_posts_verbose.py, batch_process_simple.py

Problem: All three files accomplish the same core function - batch processing blog posts through automated_claude_processor.py

Evidence: Each contains identical subprocess calls:
subprocess.run([sys.executable, "automated_claude_processor.py", post])

Recommendation: Consolidate into single script, keeping the verbose version as it has the most features

Reasoning: Having three scripts that do essentially the same thing creates maintenance overhead and confusion
"""
    
    analyzer = AgenticQualityAnalyzer({})
    
    print("📋 Testing with mock agent response...")
    
    try:
        # Test the parsing logic
        result = analyzer._parse_agent_content_analysis(mock_response, {})
        
        print(f"✅ Parsing Success!")
        print(f"   Issues extracted: {len(result.get('issues', []))}")
        
        for i, issue in enumerate(result.get('issues', []), 1):
            print(f"\n   Issue {i}:")
            print(f"   ├─ Severity: {issue.severity}")
            print(f"   ├─ Title: {issue.title}")
            print(f"   ├─ Files: {issue.affected_files}")
            print(f"   └─ Recommendation: {issue.recommendation}")
            
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test agent call
    test_agent_call()
    
    # Test response parsing
    test_parsing()
    
    print(f"\n🎯 Summary:")
    print(f"   This tests the core OpenRouter API integration")
    print(f"   If this works, the agent should find duplicates")
    print(f"   If this fails, we know where the problem is")
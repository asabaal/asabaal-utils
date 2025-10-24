#!/usr/bin/env python3
"""
Simple test of directory mode functionality
"""

import os
import sys
from pathlib import Path

# Add the analyzer source to Python path
analyzer_src = Path(__file__).parent / "agents" / "pr_analyzer" / "src"
sys.path.insert(0, str(analyzer_src))

# Set test mode
os.environ['PR_ANALYZER_TEST_MODE'] = 'true'

# Test basic functionality
try:
    from stages.stage1_context_prep import ContextPreparationTester
    from stages.stage2_agent_prompts import AgentPromptTester
    
    print("✅ Successfully imported stage modules")
    
    # Test context preparation
    test_dir = Path(__file__).parent / "test_projects"
    context_tester = ContextPreparationTester(str(test_dir))
    
    print("✅ ContextPreparationTester initialized")
    
    # Run the test
    result = context_tester.test_context_preparation()
    print(f"📊 Context preparation result: {result}")
    
    if result and 'file_changes' in result:
        file_count = len(result['file_changes'])
        print(f"📁 Found {file_count} files for analysis")
        
        # Test prompt generation
        prompt_tester = AgentPromptTester(str(test_dir))
        prompts = prompt_tester.test_prompt_generation()
        
        if prompts:
            print(f"✅ Generated {len(prompts)} AI prompts")
            for i, prompt in enumerate(prompts[:2]):  # Show first 2
                print(f"   Prompt {i+1}: {len(prompt.get('prompt', ''))} characters")
        else:
            print("❌ No prompts generated")
    else:
        print("❌ No file changes found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
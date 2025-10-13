#!/usr/bin/env python3
"""
Test script to fix Stage 3 prompt creation with inline JSON content
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_duplicate_detection_prompt_inline(analysis_context, prompt_data_dir):
    """Create duplicate detection prompt with inline JSON content"""
    
    # Create the data structure
    file_analysis_data = {
        'pr_summary': analysis_context['pr_summary'],
        'categories': {},
        'file_details': []
    }
    
    # Organize files by category with content
    for category, files in analysis_context['categories'].items():
        if not files or category == 'GENERATED_IRRELEVANT':
            continue
            
        file_analysis_data['categories'][category] = len(files)
        
        # Add detailed file info for analysis
        for file_data in files[:10]:  # Limit per category
            file_details = {
                'path': file_data['path'],
                'category': category,
                'change_type': file_data['change_type'],
                'lines_added': file_data['lines_added'],
                'lines_removed': file_data['lines_removed'],
                'size': file_data['size'],
                'content_sample': file_data.get('content_sample', ''),
                'has_functions': file_data.get('has_functions', False),
                'has_classes': file_data.get('has_classes', False)
            }
            file_analysis_data['file_details'].append(file_details)
    
    # Save data file (for debugging)
    prompt_data_dir = Path(prompt_data_dir)
    prompt_data_dir.mkdir(exist_ok=True)
    data_file = prompt_data_dir / "duplicate_analysis_data.json"
    with open(data_file, 'w') as f:
        json.dump(file_analysis_data, f, indent=2)
    
    # Create prompt with inline JSON content
    json_content = json.dumps(file_analysis_data, indent=2)
    prompt = f"""You are a senior software architect detecting duplicate files.

Here is the detailed file analysis data:

```json
{json_content}
```

Instructions:
1. Analyze the JSON data above which contains PR summary, file categories, and detailed file information
2. Analyze file content samples and purposes to find duplicates
3. Focus on functional duplicates - files that solve the same problems

Expected duplicates based on manual analysis:
- Blog processing scripts in content/ directory
- Database setup files (supabase-setup.sql, etc.) 
- Deployment guides (VERCEL-DEPLOY.md variants)

Provide your analysis in this exact format:

## CRITICAL:
[Exact duplicates or abandoned implementations with specific file paths and evidence]

## HIGH:
[Functional duplicates with different implementations and specific file paths]

## MEDIUM:
[Similar purpose files that could be consolidated with specific file paths]

## Summary:
[Brief summary of findings and recommendations]

Be specific about which files and provide evidence from the content samples."""

    return prompt

def test_prompt_creation():
    """Test the fixed prompt creation"""
    
    # Load context from Stage 1
    stage1_dir = Path("src/asabaal_utils/pr_analyzer/debug_outputs/stage1")
    context_file = stage1_dir / "final_analysis_context.json"
    
    if not context_file.exists():
        print("❌ Stage 1 context not found")
        return
    
    with open(context_file, 'r') as f:
        analysis_context = json.load(f)
    
    # Create prompt with inline JSON
    prompt_data_dir = Path("src/asabaal_utils/pr_analyzer/debug_outputs/stage3/prompt_data")
    prompt = create_duplicate_detection_prompt_inline(analysis_context, prompt_data_dir)
    
    print("✅ Fixed prompt created successfully!")
    print(f"Prompt length: {len(prompt)} characters")
    print("\n--- PROMPT PREVIEW ---")
    print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
    print("\n--- END PREVIEW ---")
    
    # Save the fixed prompt
    prompt_file = prompt_data_dir / "duplicate_detection_prompt_fixed.txt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    print(f"✅ Fixed prompt saved to: {prompt_file}")

if __name__ == '__main__':
    test_prompt_creation()
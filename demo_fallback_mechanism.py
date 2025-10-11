#!/usr/bin/env python3
"""
Demonstration of the deleted files fallback mechanism in action.
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def demo_fallback_mechanism():
    """Demonstrate the fallback mechanism with simulated deleted files"""
    
    print("🎯 Deleted Files Fallback Mechanism Demonstration")
    print("=" * 55)
    
    try:
        from asabaal_utils.pr_analyzer.file_existence_utils import validate_and_create_feedback
        
        # Load real project data
        multisensory_project = Path("/home/asabaal/repos/multisensory-experience-website")
        with open(multisensory_project / "pr_analysis_output" / "file_assessment_results.json", 'r') as f:
            real_data = json.load(f)
        
        print("📊 Current Project State:")
        summary = real_data['assessment_summary']
        print(f"   Total Files: {summary['total_files']}")
        print(f"   Ready Files: {summary['ready_files']}")
        print(f"   Not Ready Files: {summary['not_ready_files']}")
        
        # Simulate deleted files by modifying the data
        simulated_data = json.loads(json.dumps(real_data))  # Deep copy
        
        # Mark some existing files as deleted (simulate the original problem)
        files_to_simulate_deleted = [
            "database-archive/supabase-keys.prod.js",
            "database-archive/supabase-setup.sql"
        ]
        
        print(f"\n🔧 Simulating deleted files: {len(files_to_simulate_deleted)} files")
        for file_path in files_to_simulate_deleted:
            # Find and mark as not_ready to simulate the original issue
            for assessment in simulated_data['file_assessments']:
                if assessment['file_path'] == file_path:
                    assessment['merge_readiness'] = 'not_ready'
                    assessment['recommendations'] = ['File needs review']
                    break
        
        # Recount simulated not_ready files
        simulated_not_ready = sum(1 for f in simulated_data['file_assessments'] 
                                if f['merge_readiness'] == 'not_ready')
        print(f"   Simulated Not Ready Files: {simulated_not_ready}")
        
        # Test the fallback mechanism
        print("\n🤖 Applying Fallback Mechanism...")
        feedback, prompt_addition = validate_and_create_feedback(
            str(multisensory_project), simulated_data['file_assessments']
        )
        
        print(f"📝 Feedback Results:")
        print(f"   Type: {feedback['type']}")
        print(f"   Files Detected: {len(feedback.get('files', []))}")
        
        if feedback['type'] != 'no_deleted_files':
            print(f"\n🔄 Files that would be auto-reclassified:")
            for file_info in feedback['files']:
                print(f"   - {file_info['file_path']}")
                print(f"     Current Status: {file_info['current_status']}")
                print(f"     Existence: {file_info['existence_status']}")
                print(f"     Recommended: {file_info['recommended_status']}")
            
            print(f"\n📄 Generated Prompt Addition: {len(prompt_addition)} characters")
            if prompt_addition:
                print("   Preview:")
                preview = prompt_addition[:200] + "..." if len(prompt_addition) > 200 else prompt_addition
                print(f"   {preview}")
        
        print("\n✅ Demonstration completed successfully!")
        print("\n💡 Key Benefits of the Fallback Mechanism:")
        print("   1. Automatically detects deleted/moved files")
        print("   2. Generates appropriate feedback for agents")
        print("   3. Provides prompt additions for clear instructions")
        print("   4. Handles edge cases gracefully without manual intervention")
        print("   5. Maintains accuracy of merge readiness assessments")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_fallback_mechanism()
    sys.exit(0 if success else 1)
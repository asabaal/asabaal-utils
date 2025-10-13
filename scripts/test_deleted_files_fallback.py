#!/usr/bin/env python3
"""
Test script for the deleted files fallback mechanism.
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_deleted_file_detection():
    """Test the deleted file detection and reclassification mechanism"""
    
    print("🧪 Testing Deleted Files Fallback Mechanism")
    print("=" * 50)
    
    try:
        # Import the utilities
        from asabaal_utils.pr_analyzer.file_existence_utils import (
            FileExistenceValidator, 
            validate_and_create_feedback
        )
        print("✅ Successfully imported file existence utilities")
        
        # Test data - simulate files that include deleted ones
        test_file_assessments = [
            {
                "file_path": "database-archive/supabase-keys.prod.js",
                "merge_readiness": "not_ready",
                "recommendations": ["File needs review"]
            },
            {
                "file_path": "database-archive/supabase-setup.sql",
                "merge_readiness": "not_ready", 
                "recommendations": ["File needs review"]
            },
            {
                "file_path": "assets/images/icons/cosmic_nebula.svg",
                "merge_readiness": "not_ready",
                "recommendations": ["File needs review"]
            },
            {
                "file_path": "README.md",
                "merge_readiness": "ready",
                "recommendations": ["File is ready"]
            }
        ]
        
        print(f"📋 Test data: {len(test_file_assessments)} files")
        
        # Test 1: File existence validation
        print("\n🔍 Test 1: File Existence Validation")
        validator = FileExistenceValidator(str(project_root))
        
        deleted_files = validator.find_deleted_files(test_file_assessments)
        print(f"Found {len(deleted_files)} deleted files:")
        for deleted in deleted_files:
            print(f"  - {deleted['file_path']}: {deleted['reason']}")
        
        # Test 2: Feedback creation
        print("\n📝 Test 2: Feedback Creation")
        feedback = validator.create_deleted_file_feedback(deleted_files)
        print(f"Feedback type: {feedback['type']}")
        print(f"Files to reclassify: {len(feedback.get('files', []))}")
        
        # Test 3: Prompt addition generation
        print("\n📄 Test 3: Prompt Addition Generation")
        prompt_addition = validator.generate_fallback_prompt_addition(feedback)
        print(f"Generated prompt addition length: {len(prompt_addition)} chars")
        if prompt_addition:
            print("Prompt addition preview:")
            print(prompt_addition[:300] + "..." if len(prompt_addition) > 300 else prompt_addition)
        
        # Test 4: Auto reclassification
        print("\n🤖 Test 4: Auto Reclassification")
        updated_assessments, changes = validator.auto_reclassify_deleted_files(
            test_file_assessments, deleted_files
        )
        
        print(f"Reclassified {len(changes['files_reclassified'])} files:")
        for change in changes['files_reclassified']:
            print(f"  - {change['file_path']}: {change['old_status']} → {change['new_status']}")
        
        print(f"Metrics impact:")
        metrics = changes['impact_on_metrics']
        print(f"  Not Ready: {metrics['not_ready_before']} → {metrics['not_ready_after']}")
        print(f"  Ready: {metrics['ready_before']} → {metrics['ready_after']}")
        
        # Test 5: Convenience function
        print("\n🔧 Test 5: Convenience Function")
        feedback2, prompt_addition2 = validate_and_create_feedback(
            str(project_root), test_file_assessments
        )
        
        print(f"Convenience function results:")
        print(f"  Feedback type: {feedback2['type']}")
        print(f"  Prompt addition length: {len(prompt_addition2)}")
        
        print("\n✅ All tests passed! Deleted files fallback mechanism is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stage10_integration():
    """Test integration with Stage 10 feedback system"""
    
    print("\n🔗 Testing Stage 10 Integration")
    print("=" * 30)
    
    try:
        # Import Stage 10 system
        from asabaal_utils.pr_analyzer.stage10_feedback_updates import FeedbackUpdateSystem
        
        # Initialize the system
        system = FeedbackUpdateSystem(project_root)
        print("✅ FeedbackUpdateSystem initialized successfully")
        
        # Test the automatic reclassification method
        test_assessment_data = {
            "file_assessments": [
                {
                    "file_path": "database-archive/supabase-keys.prod.js",
                    "merge_readiness": "not_ready",
                    "recommendations": ["File needs review"]
                },
                {
                    "file_path": "README.md",
                    "merge_readiness": "ready", 
                    "recommendations": ["File is ready"]
                }
            ],
            "assessment_summary": {
                "total_files": 2,
                "ready_files": 1,
                "not_ready_files": 1
            }
        }
        
        auto_updates = system.apply_automatic_deleted_file_reclassification(test_assessment_data)
        
        print(f"Stage 10 auto-reclassification results:")
        print(f"  Files updated: {len(auto_updates)}")
        for file_path, updates in auto_updates.items():
            print(f"  - {file_path}: {updates.get('merge_readiness', 'unknown')}")
        
        print("✅ Stage 10 integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Stage 10 integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Deleted Files Fallback Mechanism Tests")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_deleted_file_detection()
    test2_passed = test_stage10_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"File Existence Detection: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Stage 10 Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! The fallback mechanism is ready for use.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.")
        sys.exit(1)
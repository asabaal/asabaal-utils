#!/usr/bin/env python3
"""
Test: Stage 8 Architecture Fix

This test verifies that Stage 8 now correctly processes Stage 7 analysis results
instead of re-processing raw files.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_html_processor_architecture():
    """Test that HTML processor correctly handles analysis results"""
    print("🧪 Testing HTML processor architecture fix...")
    
    from asabaal_utils.agentic_toolkit.html_batch_processor import HTMLBatchProcessor
    from asabaal_utils.agentic_toolkit import BatchProcessingConfig
    
    # Sample Stage 7 analysis results (what Stage 8 should process)
    analysis_results = [
        {
            "file_path": "src/main.py",
            "merge_readiness": "ready",
            "overall_assessment": {
                "purpose": "Main application entry point with CLI interface",
                "business_impact": "Critical - core application functionality",
                "risk_assessment": "Low risk - well-structured with proper error handling"
            },
            "feedback": None,
            "code_elements": {
                "classes": ["Application", "CLIParser"],
                "functions": ["main", "parse_args", "run_app"]
            }
        },
        {
            "file_path": "src/utils.py", 
            "merge_readiness": "conditional",
            "overall_assessment": {
                "purpose": "Utility functions for data processing and validation",
                "business_impact": "Medium - supports core functionality",
                "risk_assessment": "Medium risk - needs input validation improvements"
            },
            "feedback": "Add rate limiting and enhance input validation for production use",
            "code_elements": {
                "classes": [],
                "functions": ["validate_input", "process_data", "format_output"]
            }
        }
    ]
    
    # Create processor
    config = BatchProcessingConfig(batch_size=2, debug_mode=True)
    processor = HTMLBatchProcessor(
        output_dir="./test_html_output",
        html_template_path="./test_template.html",
        instructions_path="./test_instructions.txt",
        config=config
    )
    
    print(f"✅ Created HTMLBatchProcessor")
    
    # Test the new prompt generation
    context = {"processing_mode": "analysis_results"}
    prompt = processor._create_html_batch_prompt_for_analysis(analysis_results, context)
    
    print(f"✅ Generated analysis-based prompt ({len(prompt)} chars)")
    
    # Verify prompt contains analysis data, not raw file data
    assert "merge_readiness" in prompt, "Prompt should contain merge readiness data"
    assert "overall_assessment" in prompt, "Prompt should contain assessment data" 
    assert "ANALYSIS RESULTS" in prompt, "Prompt should clearly indicate processing analysis results"
    assert "analysis_batch_data_" in prompt, "Should use analysis batch data file naming"
    
    print(f"✅ Prompt correctly references analysis results")
    
    # Test item identification
    identifier = processor.get_item_identifier(analysis_results[0])
    assert identifier == "src/main.py", "Should identify analysis result by file_path"
    
    print(f"✅ Item identification works correctly")
    
    # Test single analysis prompt
    single_prompt = processor._create_single_analysis_html_prompt(analysis_results[0], context)
    assert "ANALYSIS RESULT: src/main.py" in single_prompt, "Single prompt should reference analysis result"
    assert "MERGE READINESS: ready" in single_prompt, "Single prompt should show merge readiness"
    
    print(f"✅ Single analysis prompt works correctly")
    
    return True

def test_backward_compatibility():
    """Test that the old methods still work but show deprecation warnings"""
    print("🧪 Testing backward compatibility...")
    
    from asabaal_utils.agentic_toolkit.html_batch_processor import HTMLBatchProcessor
    from asabaal_utils.agentic_toolkit import BatchProcessingConfig
    
    # Sample raw file data (old format)
    raw_files = [
        {
            "path": "src/main.py",
            "category": "python", 
            "lines_added": 150,
            "content_sample": "#!/usr/bin/env python3\nimport sys..."
        }
    ]
    
    # Sample analysis results (new format)  
    analysis_results = [
        {
            "file_path": "src/main.py",
            "merge_readiness": "ready",
            "overall_assessment": {"purpose": "Main app"}
        }
    ]
    
    config = BatchProcessingConfig(debug_mode=True)
    processor = HTMLBatchProcessor(
        output_dir="./test_html_output",
        html_template_path="./test_template.html", 
        instructions_path="./test_instructions.txt",
        config=config
    )
    
    # Test deprecated method with raw files
    print("   Testing deprecated method with raw files...")
    old_prompt = processor._create_html_batch_prompt(raw_files, {})
    assert "legacy_batch_data_" in old_prompt, "Should use legacy file naming for raw files"
    
    # Test deprecated method with analysis results (should redirect)
    print("   Testing deprecated method with analysis results...")
    redirected_prompt = processor._create_html_batch_prompt(analysis_results, {})
    assert "analysis_batch_data_" in redirected_prompt, "Should redirect to analysis method"
    
    print(f"✅ Backward compatibility works with proper redirects")
    
    return True

def main():
    """Run architecture tests"""
    print("🚀 Testing Stage 8 Architecture Fix")
    print("=" * 50)
    
    tests = [
        ("HTML Processor Architecture", test_html_processor_architecture),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Test: {name}")
        try:
            result = test_func()
            results.append((name, result))
            if result:
                print(f"✅ {name}: PASSED")
            else:
                print(f"❌ {name}: FAILED")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 ARCHITECTURE TEST RESULTS:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Stage 8 architecture fix is working correctly!")
        print("📊 Stage 8 now processes Stage 7 analysis results (not raw files)")
        return True
    else:
        print("⚠️  Some architecture tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
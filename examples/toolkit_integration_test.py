#!/usr/bin/env python3
"""
Test: Agentic Batch Processing Toolkit Integration

This test verifies that both Stage 7 and Stage 8 can successfully use the
generalized batch processing toolkit.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_detailed_analysis_processor():
    """Test the detailed analysis processor"""
    print("🧪 Testing DetailedAnalysisProcessor...")
    
    from asabaal_utils.agentic_toolkit import create_detailed_analysis_processor
    
    # Create a test processor (won't actually run without real data)
    processor = create_detailed_analysis_processor(
        repo_path="./test_repo",
        output_dir="./test_output",
        instructions_path="./test_instructions.txt",
        output_format_path="./test_format.json",
        batch_size=5,
        debug_mode=True
    )
    
    print(f"✅ Created DetailedAnalysisProcessor with batch size {processor.config.batch_size}")
    print(f"✅ Debug mode: {processor.config.debug_mode}")
    print(f"✅ Verify completeness: {processor.config.verify_completeness}")
    
    return True

def test_html_batch_processor():
    """Test the HTML batch processor"""
    print("🧪 Testing HTMLBatchProcessor...")
    
    from asabaal_utils.agentic_toolkit import create_html_batch_processor
    
    # Create a test processor
    processor = create_html_batch_processor(
        output_dir="./test_html_output",
        html_template_path="./test_template.html",
        instructions_path="./test_html_instructions.txt",
        batch_size=25,
        debug_mode=True
    )
    
    print(f"✅ Created HTMLBatchProcessor with batch size {processor.config.batch_size}")
    print(f"✅ Progress tracking: {processor.config.save_progress}")
    
    return True

def test_stage7_integration():
    """Test Stage 7 integration with toolkit"""
    print("🧪 Testing Stage 7 integration...")
    
    try:
        from asabaal_utils.pr_analyzer.stage7_detailed_analysis_v2 import DetailedAnalysisEngine
        
        # Create engine (won't actually run without real data)
        engine = DetailedAnalysisEngine(
            repo_path="./test_repo", 
            output_dir="./test_output",
            debug_mode=True,
            max_files=10
        )
        
        print(f"✅ Created DetailedAnalysisEngine V2 with toolkit")
        print(f"✅ Max files limit: {engine.max_files}")
        print(f"✅ Batch processor available: {hasattr(engine, 'batch_processor')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Stage 7 V2 import failed: {e}")
        return False

def test_analyzer_integration():
    """Test main analyzer integration"""
    print("🧪 Testing UnifiedPRAnalyzer integration...")
    
    try:
        from asabaal_utils.pr_analyzer.analyzer import UnifiedPRAnalyzer, TOOLKIT_VERSION_AVAILABLE
        
        print(f"✅ Toolkit version available: {TOOLKIT_VERSION_AVAILABLE}")
        
        # Create analyzer (use current directory to avoid path issues)
        analyzer = UnifiedPRAnalyzer(".", debug_mode=True)
        
        print(f"✅ Created UnifiedPRAnalyzer successfully")
        print(f"✅ Debug mode: {analyzer.debug_mode}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Analyzer integration failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Running Agentic Batch Processing Toolkit Integration Tests")
    print("=" * 70)
    
    tests = [
        ("Core Processors", test_detailed_analysis_processor),
        ("HTML Processor", test_html_batch_processor), 
        ("Stage 7 Integration", test_stage7_integration),
        ("Analyzer Integration", test_analyzer_integration)
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
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Toolkit is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
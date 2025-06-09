#!/usr/bin/env python3
"""
Comprehensive test of MoviePy integration and dependency resolution.

This script tests all video processing tools to ensure they work with the current
MoviePy installation and don't have conflicting dependencies.
"""

import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all video processing imports."""
    print("🔍 Testing imports...")
    
    tests = [
        ("Basic video processing", lambda: __import__("asabaal_utils.video_processing", fromlist=["*"])),
        ("MoviePy imports", lambda: __import__("asabaal_utils.video_processing.moviepy_imports", fromlist=["*"])),
        ("Silence detector", lambda: __import__("asabaal_utils.video_processing.silence_detector", fromlist=["SilenceDetector"])),
        ("Video summarizer", lambda: __import__("asabaal_utils.video_processing.video_summarizer", fromlist=["VideoSummarizer"])),
        ("Jump cut detector", lambda: __import__("asabaal_utils.video_processing.jump_cut_detector", fromlist=["JumpCutDetector"])),
        ("Church service analyzer", lambda: __import__("asabaal_utils.video_processing.church_service_analyzer", fromlist=["ChurchServiceAnalyzer"])),
        ("Lyric video generator", lambda: __import__("asabaal_utils.video_processing.lyric_video", fromlist=["LyricVideoGenerator"])),
        ("CLI commands", lambda: __import__("asabaal_utils.video_processing.cli", fromlist=["*"])),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            test_func()
            print(f"  ✅ {name}")
            results.append((name, True, None))
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            results.append((name, False, str(e)))
    
    return results

def test_moviepy_diagnostics():
    """Test MoviePy diagnostics and version detection."""
    print("\n🔍 Testing MoviePy diagnostics...")
    
    try:
        from asabaal_utils.video_processing.moviepy_imports import check_moviepy_import, get_moviepy_version
        
        version = get_moviepy_version()
        print(f"  📦 Detected MoviePy version: {version}")
        
        diagnostics = check_moviepy_import()
        print(f"  📊 Import diagnostics:")
        for module, status in diagnostics['modules'].items():
            status_icon = "✅" if status else "❌"
            print(f"    {status_icon} {module}")
        
        return True, diagnostics
    except Exception as e:
        print(f"  ❌ MoviePy diagnostics failed: {e}")
        return False, str(e)

def test_core_functionality():
    """Test core functionality with actual MoviePy usage."""
    print("\n🔍 Testing core functionality...")
    
    tests = [
        ("SilenceDetector creation", lambda: __import__("asabaal_utils.video_processing.silence_detector", fromlist=["SilenceDetector"]).SilenceDetector()),
        ("VideoSummarizer creation", lambda: __import__("asabaal_utils.video_processing.video_summarizer", fromlist=["VideoSummarizer"]).VideoSummarizer()),
        ("ChurchServiceAnalyzer creation", lambda: __import__("asabaal_utils.video_processing.church_service_analyzer", fromlist=["ChurchServiceAnalyzer"]).ChurchServiceAnalyzer()),
        ("LyricVideoGenerator creation", lambda: __import__("asabaal_utils.video_processing.lyric_video", fromlist=["LyricVideoGenerator"]).LyricVideoGenerator()),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            test_func()
            print(f"  ✅ {name}")
            results.append((name, True, None))
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            results.append((name, False, str(e)))
    
    return results

def test_cli_availability():
    """Test CLI command availability."""
    print("\n🔍 Testing CLI command availability...")
    
    import subprocess
    
    commands = [
        "remove-silence",
        "create-lyric-video", 
        "analyze-transcript",
        "generate-thumbnails",
        "analyze-colors",
        "detect-jump-cuts",
        "create-summary",
    ]
    
    results = []
    for cmd in commands:
        try:
            result = subprocess.run([cmd, "--help"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ {cmd}")
                results.append((cmd, True, None))
            else:
                print(f"  ❌ {cmd}: Exit code {result.returncode}")
                results.append((cmd, False, f"Exit code {result.returncode}"))
        except Exception as e:
            print(f"  ❌ {cmd}: {e}")
            results.append((cmd, False, str(e)))
    
    return results

def main():
    """Run all tests and provide summary."""
    print("🎬 MoviePy Integration Test Suite")
    print("=" * 50)
    
    try:
        # Test imports
        import_results = test_imports()
        
        # Test MoviePy diagnostics
        moviepy_success, moviepy_info = test_moviepy_diagnostics()
        
        # Test core functionality
        func_results = test_core_functionality()
        
        # Test CLI availability
        cli_results = test_cli_availability()
        
        # Summary
        print("\n📊 SUMMARY")
        print("=" * 50)
        
        import_success = sum(1 for _, success, _ in import_results if success)
        func_success = sum(1 for _, success, _ in func_results if success)
        cli_success = sum(1 for _, success, _ in cli_results if success)
        
        total_tests = len(import_results) + len(func_results) + len(cli_results) + (1 if moviepy_success else 0)
        total_success = import_success + func_success + cli_success + (1 if moviepy_success else 0)
        
        print(f"📦 Imports: {import_success}/{len(import_results)} successful")
        print(f"🔧 Core functionality: {func_success}/{len(func_results)} successful")
        print(f"💻 CLI commands: {cli_success}/{len(cli_results)} successful")
        print(f"📊 MoviePy diagnostics: {'✅' if moviepy_success else '❌'}")
        print(f"\n🎯 Overall: {total_success}/{total_tests} tests passed ({total_success/total_tests*100:.1f}%)")
        
        if total_success == total_tests:
            print("\n🎉 All tests passed! MoviePy integration is working correctly.")
            print("All video processing tools should work simultaneously without conflicts.")
            return 0
        else:
            print(f"\n⚠️  {total_tests - total_success} test(s) failed. Check the output above for details.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
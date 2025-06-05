#!/usr/bin/env python3
"""
Test script for AsaBaal Utils MCP Server

This script tests the MCP server functionality without requiring a full MCP client.
It directly imports and tests the tools to ensure they work correctly.
"""

import sys
import os
import json

# Add tools directory to path
tools_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tools_dir)

# Import the MCP server module
from asabaal_mcp_server import (
    analyze_document, convert_format, validate_format, 
    get_supported_conversions, analyze_and_convert,
    quick_csv_to_json, markdown_to_html
)

def test_document_analysis():
    """Test document analysis functionality."""
    print("🔍 Testing Document Analysis...")
    
    sample_text = """
    # Sample Document for Testing
    
    This is a comprehensive test document that contains multiple elements for analysis.
    
    ## Features Being Tested
    
    The document analyzer should detect:
    - Multiple paragraphs and sentences
    - Markdown formatting elements
    - Contact information like email@example.com
    - Phone numbers such as 555-123-4567
    - URLs like https://example.com
    
    This text has varying sentence lengths. Some are short! Others are much longer and contain more complex vocabulary that should affect readability calculations.
    
    ```python
    def example_code():
        return "Code blocks should be detected"
    ```
    
    The analyzer calculates reading time, lexical diversity, and structural patterns.
    """
    
    result = analyze_document(sample_text, "md")
    
    if result["success"]:
        data = result["data"]
        print(f"✅ Analysis completed successfully")
        print(f"   Word count: {data['basic_stats']['word_count']}")
        print(f"   Reading level: {data['readability']['reading_level']}")
        print(f"   Emails found: {data['content_analysis']['emails_found']}")
        print(f"   Has markdown: {data['content_analysis']['has_markdown']}")
        print(f"   Estimated reading time: {data['structure']['estimated_reading_time_minutes']} minutes")
    else:
        print(f"❌ Analysis failed: {result['error']}")
    
    return result["success"]

def test_format_conversion():
    """Test format conversion functionality."""
    print("\n🔄 Testing Format Conversion...")
    
    # Test CSV to JSON
    sample_csv = """name,age,city,occupation
John Doe,28,New York,Engineer
Jane Smith,32,London,Designer
Bob Johnson,45,Tokyo,Manager"""
    
    print("   Testing CSV → JSON conversion...")
    result = convert_format(sample_csv, "csv", "json")
    
    if result["success"]:
        print("✅ CSV to JSON conversion successful")
        converted_data = json.loads(result["converted_content"])
        print(f"   Converted {len(converted_data)} records")
    else:
        print(f"❌ CSV to JSON failed: {result['error']}")
        return False
    
    # Test JSON to CSV (using the result from above)
    print("   Testing JSON → CSV conversion...")
    json_content = result["converted_content"]
    result2 = convert_format(json_content, "json", "csv")
    
    if result2["success"]:
        print("✅ JSON to CSV conversion successful")
        lines = result2["converted_content"].strip().split('\n')
        print(f"   Generated {len(lines)} CSV lines")
    else:
        print(f"❌ JSON to CSV failed: {result2['error']}")
        return False
    
    return True

def test_markdown_conversion():
    """Test Markdown to HTML conversion."""
    print("\n📝 Testing Markdown Conversion...")
    
    sample_markdown = """# Hello World

This is a **sample** document with:

- List item 1
- List item 2
- *Emphasized* text

## Code Example

```python
def greet(name):
    return f"Hello, {name}!"
```

Visit [OpenAI](https://openai.com) for more information."""
    
    result = markdown_to_html(sample_markdown, complete_document=True)
    
    if result["success"]:
        print("✅ Markdown to HTML conversion successful")
        html_length = len(result["converted_content"])
        print(f"   Generated {html_length} characters of HTML")
        
        # Check if it's a complete document
        html_content = result["converted_content"]
        if "<!DOCTYPE html>" in html_content and "<html>" in html_content:
            print("   ✅ Complete HTML document generated")
        else:
            print("   ⚠️  HTML fragment generated (not complete document)")
    else:
        print(f"❌ Markdown to HTML failed: {result['error']}")
        return False
    
    return True

def test_format_validation():
    """Test format validation functionality."""
    print("\n✅ Testing Format Validation...")
    
    # Test valid JSON
    valid_json = '{"name": "John", "age": 30, "active": true}'
    result = validate_format(valid_json, "json")
    
    if result["success"] and result["data"]["valid"]:
        print("✅ Valid JSON correctly identified")
    else:
        print("❌ Valid JSON validation failed")
        return False
    
    # Test invalid JSON
    invalid_json = '{"name": "John", "age": 30, "active": true'  # Missing closing brace
    result = validate_format(invalid_json, "json")
    
    if result["success"] and not result["data"]["valid"]:
        print("✅ Invalid JSON correctly identified")
    else:
        print("❌ Invalid JSON validation failed")
        return False
    
    return True

def test_combined_workflow():
    """Test the combined analysis and conversion workflow."""
    print("\n🔄 Testing Combined Workflow...")
    
    sample_data = """product,price,category
Laptop,999.99,Electronics
Phone,599.99,Electronics
Book,19.99,Literature"""
    
    result = analyze_and_convert(
        sample_data,
        from_format="csv",
        to_format="json",
        analyze_original=True,
        analyze_converted=True
    )
    
    if result["success"]:
        data = result["data"]
        print("✅ Combined workflow completed successfully")
        
        if "original_analysis" in data:
            original_stats = data["original_analysis"]["data"]["basic_stats"]
            print(f"   Original: {original_stats['word_count']} words, {original_stats['line_count']} lines")
        
        if "conversion" in data and data["conversion"]["success"]:
            print("   ✅ Format conversion successful")
        
        if "converted_analysis" in data:
            converted_stats = data["converted_analysis"]["data"]["basic_stats"]
            print(f"   Converted: {converted_stats['word_count']} words, {converted_stats['line_count']} lines")
    else:
        print(f"❌ Combined workflow failed: {result['error']}")
        return False
    
    return True

def test_quick_tools():
    """Test the quick conversion tools."""
    print("\n⚡ Testing Quick Tools...")
    
    # Test quick CSV to JSON
    simple_csv = "name,value\ntest,123\nexample,456"
    result = quick_csv_to_json(simple_csv)
    
    if result["success"]:
        print("✅ Quick CSV to JSON successful")
    else:
        print(f"❌ Quick CSV to JSON failed: {result['error']}")
        return False
    
    return True

def test_supported_conversions():
    """Test getting supported conversions info."""
    print("\n📋 Testing Supported Conversions Info...")
    
    result = get_supported_conversions()
    
    if result["success"]:
        conversions = result["data"]["supported_conversions"]
        print(f"✅ Retrieved {len(conversions)} supported conversions")
        print(f"   Available: {', '.join(list(conversions.keys())[:3])}...")
    else:
        print(f"❌ Failed to get conversions: {result['error']}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🧪 AsaBaal Utils MCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Document Analysis", test_document_analysis),
        ("Format Conversion", test_format_conversion),
        ("Markdown Conversion", test_markdown_conversion),
        ("Format Validation", test_format_validation),
        ("Combined Workflow", test_combined_workflow),
        ("Quick Tools", test_quick_tools),
        ("Supported Conversions", test_supported_conversions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ❌ {test_name} test failed")
        except Exception as e:
            print(f"   💥 {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP server is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
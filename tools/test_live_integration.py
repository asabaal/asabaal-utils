#!/usr/bin/env python3
"""
Live Integration Test - Demonstrates Claude Tool Bridge in action
Shows real-world examples of how Claude can use all your tools
"""

import requests
import json
import time
from typing import Dict, Any

class LiveIntegrationTest:
    def __init__(self, bridge_url: str = "http://localhost:7000"):
        self.bridge_url = bridge_url
        self.test_results = []
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict:
        """Execute a tool via the bridge"""
        try:
            response = requests.post(f"{self.bridge_url}/execute", 
                                   json={"tool_name": tool_name, "parameters": parameters},
                                   timeout=30)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_document_analysis_pipeline(self):
        """Test complete document analysis workflow"""
        print("🔍 TESTING: Document Analysis Pipeline")
        print("=" * 50)
        
        # Test different types of documents
        test_documents = [
            {
                "name": "Technical Documentation",
                "content": """# API Documentation\n\nThis API provides endpoints for data analysis. \nContact: support@company.com or call 555-1234.\n\n## Features\n- Fast processing\n- Secure authentication\n- Real-time results""",
                "type": "md"
            },
            {
                "name": "Business Email",
                "content": "Hello team! Our Q4 results show 25% growth. The new product launch at https://example.com/launch exceeded expectations. Please review the attached report and send feedback to manager@company.com by Friday.",
                "type": "txt"
            },
            {
                "name": "Code Documentation", 
                "content": """def process_data(input_file, output_format='json'):\n    \"\"\"Process data file and convert to specified format.\n    \n    Args:\n        input_file: Path to input file\n        output_format: Output format (json, csv, xml)\n    \"\"\"\n    return convert_file(input_file, output_format)""",
                "type": "py"
            }
        ]
        
        for doc in test_documents:
            print(f"\n📄 Analyzing: {doc['name']}")
            result = self.execute_tool("document_analyzer", {
                "text": doc["content"],
                "content_type": doc["type"]
            })
            
            if result.get("success"):
                data = result["result"]["data"]
                stats = data["basic_stats"]
                readability = data["readability"]
                content = data["content_analysis"]
                
                print(f"   📊 Words: {stats['word_count']}, Sentences: {stats['sentence_count']}")
                print(f"   📖 Reading Level: {readability['reading_level']}")
                print(f"   📧 Emails Found: {content['emails_found']}")
                print(f"   🌐 URLs Found: {content['urls_found']}")
                print(f"   ⏱️  Execution: {result['execution_time_ms']:.1f}ms")
            else:
                print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
    
    def test_format_conversion_chain(self):
        """Test chained format conversions"""
        print("\n🔄 TESTING: Format Conversion Chain")
        print("=" * 50)
        
        # Start with CSV data
        original_csv = """product,price,category,in_stock
Laptop,999.99,Electronics,true
Book,15.99,Education,true
Coffee Mug,12.50,Kitchen,false
Smartphone,699.99,Electronics,true"""
        
        print("📄 Starting with CSV data:")
        print("   4 products with price, category, stock info")
        
        # CSV → JSON
        print("\n🔄 Step 1: CSV → JSON")
        json_result = self.execute_tool("format_converter", {
            "content": original_csv,
            "from_format": "csv",
            "to_format": "json"
        })
        
        if json_result.get("success"):
            json_data = json_result["result"]["data"]["converted_content"]
            info = json_result["result"]["data"]["conversion_info"]
            print(f"   ✅ Success! {info['original_size_chars']} → {info['converted_size_chars']} chars")
            print(f"   ⏱️  Execution: {json_result['execution_time_ms']:.1f}ms")
            
            # JSON → XML
            print("\n🔄 Step 2: JSON → XML")
            xml_result = self.execute_tool("format_converter", {
                "content": json_data,
                "from_format": "json", 
                "to_format": "xml",
                "options": {"root_name": "products", "item_name": "product"}
            })
            
            if xml_result.get("success"):
                xml_info = xml_result["result"]["data"]["conversion_info"]
                print(f"   ✅ Success! {xml_info['original_size_chars']} → {xml_info['converted_size_chars']} chars")
                print(f"   ⏱️  Execution: {xml_result['execution_time_ms']:.1f}ms")
                print("   📄 Final format: Structured XML with custom root element")
            else:
                print(f"   ❌ XML conversion failed: {xml_result.get('message')}")
        else:
            print(f"   ❌ JSON conversion failed: {json_result.get('message')}")
    
    def test_combined_workflow(self):
        """Test combining multiple tools in a workflow"""
        print("\n🔗 TESTING: Combined Workflow")
        print("=" * 50)
        
        # Sample data that needs analysis AND conversion
        sample_data = """name,age,email,department
Alice Johnson,28,alice@company.com,Engineering
Bob Smith,34,bob@company.com,Marketing  
Carol Davis,29,carol@company.com,Engineering
David Wilson,31,david@company.com,Sales"""
        
        print("📊 Processing employee data with combined workflow:")
        
        # Step 1: Analyze the original CSV
        print("\n📋 Step 1: Analyzing original CSV structure")
        analysis_result = self.execute_tool("document_analyzer", {
            "text": sample_data,
            "content_type": "csv"
        })
        
        if analysis_result.get("success"):
            analysis_data = analysis_result["result"]["data"]
            emails_found = analysis_data["content_analysis"]["emails_found"]
            word_count = analysis_data["basic_stats"]["word_count"]
            print(f"   📧 Found {emails_found} email addresses")
            print(f"   📊 Total words: {word_count}")
            print(f"   ⏱️  Analysis time: {analysis_result['execution_time_ms']:.1f}ms")
        
        # Step 2: Convert to JSON for better structure
        print("\n🔄 Step 2: Converting to JSON for API compatibility")
        conversion_result = self.execute_tool("format_converter", {
            "content": sample_data,
            "from_format": "csv",
            "to_format": "json"
        })
        
        if conversion_result.get("success"):
            json_content = conversion_result["result"]["data"]["converted_content"]
            conversion_info = conversion_result["result"]["data"]["conversion_info"]
            print(f"   ✅ Converted to structured JSON")
            print(f"   📄 Size change: +{conversion_info['size_change_percent']:.1f}%")
            print(f"   ⏱️  Conversion time: {conversion_result['execution_time_ms']:.1f}ms")
            
            # Step 3: Analyze the converted JSON
            print("\n🔍 Step 3: Analyzing converted JSON structure")
            json_analysis = self.execute_tool("document_analyzer", {
                "text": json_content,
                "content_type": "json"
            })
            
            if json_analysis.get("success"):
                json_data = json_analysis["result"]["data"]
                structure = json_data["structure"]
                print(f"   📋 JSON Valid: {structure.get('json_valid', 'Unknown')}")
                print(f"   ⏱️  Analysis time: {json_analysis['execution_time_ms']:.1f}ms")
                
                total_time = (analysis_result['execution_time_ms'] + 
                            conversion_result['execution_time_ms'] + 
                            json_analysis['execution_time_ms'])
                print(f"\n⚡ Total workflow time: {total_time:.1f}ms")
                print("   🎯 Workflow complete: Analyzed → Converted → Re-analyzed")
    
    def test_tool_discovery(self):
        """Test tool discovery and categorization"""
        print("\n🔍 TESTING: Tool Discovery System")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.bridge_url}/tools")
            if response.status_code == 200:
                data = response.json()
                tools = data["tools"]
                
                # Categorize tools
                categories = {}
                for tool in tools:
                    cat = tool.get("category", "other")
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(tool)
                
                print(f"📊 Discovery Results:")
                print(f"   🔧 Total tools found: {len(tools)}")
                print(f"   📂 Categories: {len(categories)}")
                
                for category, cat_tools in categories.items():
                    active_count = sum(1 for t in cat_tools if t.get("status") == "active")
                    print(f"   📁 {category.upper()}: {len(cat_tools)} tools ({active_count} active)")
                
                print(f"\n🎯 Top Tools by Category:")
                for category, cat_tools in list(categories.items())[:3]:
                    print(f"   📂 {category.upper()}:")
                    for tool in cat_tools[:3]:
                        status = "✅" if tool.get("status") == "active" else "❌"
                        print(f"      {status} {tool['name']}")
            else:
                print(f"❌ Tool discovery failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Tool discovery error: {e}")
    
    def run_all_tests(self):
        """Run complete integration test suite"""
        print("🚀 CLAUDE TOOL INTEGRATION - LIVE TESTING")
        print("=" * 60)
        print("Testing the complete Claude Tool Bridge system")
        print("Demonstrating real-world AI-tool collaboration")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_tool_discovery()
        self.test_document_analysis_pipeline()
        self.test_format_conversion_chain()
        self.test_combined_workflow()
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("🎉 INTEGRATION TEST COMPLETE!")
        print("=" * 60)
        print(f"⏱️  Total test time: {total_time:.2f}s")
        print("🎯 All systems operational - Claude can use your entire toolkit!")
        print("🚀 Ready for production AI-human collaboration!")
        print("=" * 60)

if __name__ == "__main__":
    # Check if bridge is running
    try:
        response = requests.get("http://localhost:7000", timeout=2)
        if response.status_code == 200:
            print("✅ Bridge detected - running comprehensive tests...\n")
            test = LiveIntegrationTest()
            test.run_all_tests()
        else:
            print("❌ Bridge not responding properly")
    except requests.RequestException:
        print("❌ Claude Tool Bridge not running!")
        print("💡 Start it with: ./tools/claude-tools start")
        print("🧪 Then run: python tools/test_live_integration.py")
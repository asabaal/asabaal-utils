#!/usr/bin/env python3
"""
Claude Client for Tool Bridge
Simple interface for Claude to discover and use tools
"""

import requests
import json
from typing import Dict, List, Any, Optional

class ClaudeToolClient:
    """Client interface for Claude to interact with the tool bridge"""
    
    def __init__(self, bridge_url: str = "http://localhost:7000"):
        self.bridge_url = bridge_url
        self.available_tools = {}
        self.load_tools()
    
    def load_tools(self):
        """Load available tools from the bridge"""
        try:
            response = requests.get(f"{self.bridge_url}/tools")
            if response.status_code == 200:
                data = response.json()
                self.available_tools = {tool["name"]: tool for tool in data["tools"]}
                print(f"✅ Loaded {len(self.available_tools)} tools from bridge")
            else:
                print(f"❌ Failed to load tools: {response.status_code}")
        except requests.RequestException as e:
            print(f"❌ Cannot connect to tool bridge: {e}")
            print(f"💡 Make sure the bridge is running at {self.bridge_url}")
    
    def list_tools(self) -> List[str]:
        """Get list of all available tool names"""
        return list(self.available_tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Get detailed information about a specific tool"""
        return self.available_tools.get(tool_name)
    
    def use_tool(self, tool_name: str, **parameters) -> Dict[str, Any]:
        """
        Use a tool with given parameters
        
        Args:
            tool_name: Name of the tool to use
            **parameters: Tool parameters as keyword arguments
            
        Returns:
            Dict with tool execution results
        """
        if tool_name not in self.available_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not available",
                "available_tools": self.list_tools()
            }
        
        try:
            payload = {
                "tool_name": tool_name,
                "parameters": parameters
            }
            
            response = requests.post(f"{self.bridge_url}/execute", json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"Tool execution failed: {response.status_code}",
                    "details": response.text
                }
        
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
    
    def analyze_document(self, text: str, content_type: str = "txt") -> Dict:
        """Convenience method to analyze a document"""
        return self.use_tool("document_analyzer", text=text, content_type=content_type)
    
    def convert_format(self, content: str, from_format: str, to_format: str, **options) -> Dict:
        """Convenience method to convert between formats"""
        return self.use_tool("format_converter", 
                           content=content, 
                           from_format=from_format, 
                           to_format=to_format, 
                           options=options)
    
    def run_cli_tool(self, tool_name: str, *args) -> Dict:
        """Convenience method to run a CLI tool"""
        return self.use_tool(tool_name, args=list(args))
    
    def discover_new_tools(self) -> Dict:
        """Trigger discovery of new tools"""
        try:
            response = requests.post(f"{self.bridge_url}/discover")
            if response.status_code == 200:
                self.load_tools()  # Reload tools after discovery
                return response.json()
            else:
                return {"success": False, "error": f"Discovery failed: {response.status_code}"}
        except requests.RequestException as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    def health_check(self) -> Dict:
        """Check health of all tools"""
        try:
            response = requests.get(f"{self.bridge_url}/health")
            return response.json() if response.status_code == 200 else {"error": "Health check failed"}
        except requests.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def show_tools(self):
        """Display all available tools in a nice format"""
        if not self.available_tools:
            print("❌ No tools available. Make sure the bridge is running.")
            return
        
        print(f"\n🔧 Available Tools ({len(self.available_tools)})")
        print("=" * 60)
        
        categories = {}
        for tool in self.available_tools.values():
            category = tool.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        for category, tools in categories.items():
            print(f"\n📂 {category.upper()}")
            print("-" * 40)
            for tool in tools:
                status = "✅" if tool["status"] == "active" else "❌"
                print(f"  {status} {tool['name']:<20} - {tool['description']}")
    
    def get_claude_schema(self) -> Dict:
        """Get tools in Claude-compatible schema format"""
        try:
            response = requests.get(f"{self.bridge_url}/claude/tools.json")
            return response.json() if response.status_code == 200 else {}
        except requests.RequestException:
            return {}

# Convenience function for Claude to use
def create_tool_client(bridge_url: str = "http://localhost:7000") -> ClaudeToolClient:
    """Create a tool client instance"""
    return ClaudeToolClient(bridge_url)

# Example usage for testing
if __name__ == "__main__":
    print("🔧 Claude Tool Client - Testing Interface")
    print("=" * 50)
    
    # Create client
    client = ClaudeToolClient()
    
    # Show available tools
    client.show_tools()
    
    # Test document analysis
    print("\n🧪 Testing Document Analysis...")
    result = client.analyze_document(
        "This is a test document. It has multiple sentences! How will it analyze?",
        "txt"
    )
    if result.get("success"):
        print("✅ Document analysis successful!")
        analysis = result["result"]["data"]
        print(f"📊 Word count: {analysis['basic_stats']['word_count']}")
        print(f"📖 Reading level: {analysis['readability']['reading_level']}")
    else:
        print(f"❌ Document analysis failed: {result.get('message', 'Unknown error')}")
    
    # Test format conversion
    print("\n🔄 Testing Format Conversion...")
    result = client.convert_format(
        "name,age\nAlice,25\nBob,30",
        "csv",
        "json"
    )
    if result.get("success"):
        print("✅ Format conversion successful!")
        print(f"📄 Converted: CSV → JSON")
    else:
        print(f"❌ Format conversion failed: {result.get('message', 'Unknown error')}")
    
    # Test CLI tool (if any available)
    cli_tools = [name for name, tool in client.available_tools.items() 
                 if tool.get("endpoint") == "cli"]
    if cli_tools:
        print(f"\n⚡ Testing CLI Tool: {cli_tools[0]}")
        result = client.run_cli_tool(cli_tools[0], "--help")
        if result.get("success"):
            print("✅ CLI tool execution successful!")
        else:
            print(f"❌ CLI tool failed: {result.get('message', 'Unknown error')}")
    
    # Health check
    print("\n🏥 Running Health Check...")
    health = client.health_check()
    if "overall_health" in health:
        print(f"🌡️ Overall health: {health['overall_health']}")
        print(f"✅ Healthy tools: {health['healthy_tools']}")
        print(f"❌ Unhealthy tools: {health['unhealthy_tools']}")
    else:
        print("❌ Health check failed")
    
    print("\n✨ Testing complete!")
    print("💡 Now Claude can use client.use_tool() to access any tool!")
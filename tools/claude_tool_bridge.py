#!/usr/bin/env python3
"""
Claude Tool Integration Bridge
A system that makes all your tools accessible to Claude through a unified interface
"""

import os
import json
import asyncio
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

@dataclass
class ToolDefinition:
    """Definition of a tool that Claude can use"""
    name: str
    description: str
    endpoint: str
    method: str
    parameters: Dict[str, Any]
    examples: List[Dict[str, Any]]
    category: str
    version: str
    status: str  # "active", "inactive", "error"

class ToolRequest(BaseModel):
    """Request format for tool execution"""
    tool_name: str
    parameters: Dict[str, Any]
    context: Optional[str] = None

class ToolResponse(BaseModel):
    """Standardized response format for all tools"""
    success: bool
    tool_name: str
    result: Any
    message: str
    execution_time_ms: float
    context: Optional[str] = None

class ClaudeToolBridge:
    """Main bridge class that manages tool discovery and execution"""
    
    def __init__(self, tools_directory: str = None):
        self.tools_directory = Path(tools_directory or os.getcwd())
        self.tools_registry: Dict[str, ToolDefinition] = {}
        self.active_services: Dict[str, str] = {}  # service_name -> url
        self.app = FastAPI(
            title="Claude Tool Bridge",
            description="Unified interface for Claude to access all your tools",
            version="1.0.0"
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Claude Tool Bridge",
                "status": "active",
                "available_tools": len(self.tools_registry),
                "active_services": list(self.active_services.keys())
            }
        
        @self.app.get("/tools")
        async def list_tools():
            """Get all available tools for Claude"""
            return {
                "tools": [asdict(tool) for tool in self.tools_registry.values()],
                "categories": self.get_tool_categories(),
                "total_count": len(self.tools_registry)
            }
        
        @self.app.get("/tools/{tool_name}")
        async def get_tool_info(tool_name: str):
            """Get detailed information about a specific tool"""
            if tool_name not in self.tools_registry:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            return asdict(self.tools_registry[tool_name])
        
        @self.app.post("/execute")
        async def execute_tool(request: ToolRequest) -> ToolResponse:
            """Execute a tool with given parameters"""
            return await self.execute_tool_async(request.tool_name, request.parameters, request.context)
        
        @self.app.get("/claude/tools.json")
        async def claude_tool_schema():
            """Get tools in Claude-compatible JSON schema format"""
            return self.generate_claude_schema()
        
        @self.app.post("/discover")
        async def discover_tools():
            """Scan for new tools and update registry"""
            discovered = await self.discover_tools()
            return {
                "discovered_count": len(discovered),
                "tools": discovered,
                "total_tools": len(self.tools_registry)
            }
        
        @self.app.get("/health")
        async def health_check():
            """Check health of all registered tools"""
            health_status = await self.check_tools_health()
            return health_status
    
    async def discover_tools(self) -> List[str]:
        """Discover tools from multiple sources"""
        discovered = []
        
        # 1. Discover from existing API services
        discovered.extend(await self.discover_api_tools())
        
        # 2. Discover from command-line tools using toolmgr
        discovered.extend(await self.discover_cli_tools())
        
        # 3. Discover from Python modules
        discovered.extend(await self.discover_python_tools())
        
        return discovered
    
    async def discover_api_tools(self) -> List[str]:
        """Discover tools from running API services"""
        discovered = []
        
        # Check for converter API
        try:
            response = requests.get("http://localhost:8000/tools/list", timeout=2)
            if response.status_code == 200:
                api_tools = response.json()
                for tool_name, tool_info in api_tools["tools"].items():
                    self.register_api_tool(tool_name, tool_info)
                    discovered.append(tool_name)
                    self.active_services["converter_api"] = "http://localhost:8000"
        except requests.RequestException:
            pass  # Service not available
        
        return discovered
    
    async def discover_cli_tools(self) -> List[str]:
        """Discover command-line tools using toolmgr"""
        discovered = []
        
        try:
            # Use toolmgr to list installed tools
            result = subprocess.run(
                [str(self.tools_directory / "toolmgr"), "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse toolmgr output and register CLI tools
                cli_tools = self.parse_toolmgr_output(result.stdout)
                for tool_info in cli_tools:
                    self.register_cli_tool(tool_info)
                    discovered.append(tool_info["name"])
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # toolmgr not available
        
        return discovered
    
    async def discover_python_tools(self) -> List[str]:
        """Discover Python-based tools"""
        discovered = []
        
        # Look for Python files that look like tools
        for py_file in self.tools_directory.glob("**/*.py"):
            if self.is_python_tool(py_file):
                tool_info = self.extract_python_tool_info(py_file)
                if tool_info:
                    self.register_python_tool(tool_info)
                    discovered.append(tool_info["name"])
        
        return discovered
    
    def register_api_tool(self, tool_name: str, tool_info: Dict):
        """Register a tool from an API service"""
        # Convert API tool info to our standard format
        endpoints = tool_info.get("endpoints", [])
        main_endpoint = endpoints[0] if endpoints else "/unknown"
        
        self.tools_registry[tool_name] = ToolDefinition(
            name=tool_name,
            description=tool_info.get("description", ""),
            endpoint=f"http://localhost:8000{main_endpoint}",
            method="POST",
            parameters=self.extract_api_parameters(tool_info),
            examples=self.generate_api_examples(tool_name, tool_info),
            category=tool_info.get("category", "api"),
            version="1.0.0",
            status="active"
        )
    
    def register_cli_tool(self, tool_info: Dict):
        """Register a command-line tool"""
        self.tools_registry[tool_info["name"]] = ToolDefinition(
            name=tool_info["name"],
            description=tool_info.get("description", "Command-line tool"),
            endpoint="cli",  # Special endpoint for CLI tools
            method="EXEC",
            parameters={
                "args": {
                    "type": "array",
                    "description": "Command line arguments",
                    "items": {"type": "string"}
                }
            },
            examples=[{
                "description": f"Run {tool_info['name']}",
                "parameters": {"args": ["--help"]}
            }],
            category=tool_info.get("category", "cli"),
            version=tool_info.get("version", "1.0.0"),
            status="active"
        )
    
    def register_python_tool(self, tool_info: Dict):
        """Register a Python-based tool"""
        self.tools_registry[tool_info["name"]] = ToolDefinition(
            name=tool_info["name"],
            description=tool_info.get("description", "Python tool"),
            endpoint="python",  # Special endpoint for Python tools
            method="EXEC",
            parameters=tool_info.get("parameters", {}),
            examples=tool_info.get("examples", []),
            category=tool_info.get("category", "python"),
            version=tool_info.get("version", "1.0.0"),
            status="active"
        )
    
    async def execute_tool_async(self, tool_name: str, parameters: Dict, context: str = None) -> ToolResponse:
        """Execute a tool and return standardized response"""
        import time
        start_time = time.time()
        
        if tool_name not in self.tools_registry:
            return ToolResponse(
                success=False,
                tool_name=tool_name,
                result=None,
                message=f"Tool '{tool_name}' not found",
                execution_time_ms=0,
                context=context
            )
        
        tool = self.tools_registry[tool_name]
        
        try:
            if tool.endpoint.startswith("http"):
                # API tool
                result = await self.execute_api_tool(tool, parameters)
            elif tool.endpoint == "cli":
                # CLI tool
                result = await self.execute_cli_tool(tool, parameters)
            elif tool.endpoint == "python":
                # Python tool
                result = await self.execute_python_tool(tool, parameters)
            else:
                raise ValueError(f"Unknown tool endpoint type: {tool.endpoint}")
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResponse(
                success=True,
                tool_name=tool_name,
                result=result,
                message="Tool executed successfully",
                execution_time_ms=execution_time,
                context=context
            )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResponse(
                success=False,
                tool_name=tool_name,
                result=None,
                message=f"Tool execution failed: {str(e)}",
                execution_time_ms=execution_time,
                context=context
            )
    
    async def execute_api_tool(self, tool: ToolDefinition, parameters: Dict) -> Any:
        """Execute an API-based tool"""
        response = requests.post(tool.endpoint, json=parameters, timeout=30)
        response.raise_for_status()
        return response.json()
    
    async def execute_cli_tool(self, tool: ToolDefinition, parameters: Dict) -> Any:
        """Execute a CLI tool"""
        args = parameters.get("args", [])
        cmd = [str(self.tools_directory / tool.name)] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    
    async def execute_python_tool(self, tool: ToolDefinition, parameters: Dict) -> Any:
        """Execute a Python-based tool"""
        # For now, treat Python tools as CLI tools
        return await self.execute_cli_tool(tool, parameters)
    
    def generate_claude_schema(self) -> Dict:
        """Generate Claude-compatible tool schema"""
        claude_tools = []
        
        for tool_name, tool in self.tools_registry.items():
            claude_tool = {
                "name": tool_name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": list(tool.parameters.keys())
                }
            }
            claude_tools.append(claude_tool)
        
        return {
            "tools": claude_tools,
            "metadata": {
                "bridge_version": "1.0.0",
                "total_tools": len(claude_tools),
                "categories": self.get_tool_categories()
            }
        }
    
    def get_tool_categories(self) -> Dict[str, int]:
        """Get tool counts by category"""
        categories = {}
        for tool in self.tools_registry.values():
            categories[tool.category] = categories.get(tool.category, 0) + 1
        return categories
    
    async def check_tools_health(self) -> Dict:
        """Check health status of all tools"""
        health_status = {
            "overall_health": "healthy",
            "total_tools": len(self.tools_registry),
            "healthy_tools": 0,
            "unhealthy_tools": 0,
            "tool_status": {}
        }
        
        for tool_name, tool in self.tools_registry.items():
            try:
                # Quick health check based on tool type
                if tool.endpoint.startswith("http"):
                    # Check if API is responding
                    response = requests.get(tool.endpoint.split("/tools/")[0] + "/", timeout=2)
                    status = "healthy" if response.status_code == 200 else "unhealthy"
                else:
                    # For CLI tools, check if the executable exists
                    tool_path = self.tools_directory / tool_name
                    status = "healthy" if tool_path.exists() else "unhealthy"
                
                health_status["tool_status"][tool_name] = status
                if status == "healthy":
                    health_status["healthy_tools"] += 1
                else:
                    health_status["unhealthy_tools"] += 1
            
            except Exception:
                health_status["tool_status"][tool_name] = "unhealthy"
                health_status["unhealthy_tools"] += 1
        
        if health_status["unhealthy_tools"] > 0:
            health_status["overall_health"] = "degraded"
        
        return health_status
    
    # Helper methods
    def parse_toolmgr_output(self, output: str) -> List[Dict]:
        """Parse toolmgr list output"""
        tools = []
        # This is a simplified parser - you might need to enhance based on actual toolmgr output
        lines = output.split('\n')
        for line in lines:
            if '✅' in line or '❌' in line:
                # Extract tool info from toolmgr output format
                parts = line.split()
                if len(parts) >= 3:
                    tools.append({
                        "name": parts[1],
                        "version": parts[2].replace('v', ''),
                        "description": ' '.join(parts[3:]) if len(parts) > 3 else ""
                    })
        return tools
    
    def is_python_tool(self, file_path: Path) -> bool:
        """Check if a Python file is a tool"""
        try:
            with open(file_path, 'r') as f:
                content = f.read(200)  # Read first 200 chars
                return any(marker in content for marker in [
                    '#!/usr/bin/env python',
                    '# description:',
                    'class Tool',
                    'def main('
                ])
        except Exception:
            return False
    
    def extract_python_tool_info(self, file_path: Path) -> Optional[Dict]:
        """Extract tool information from Python file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract metadata from comments
            import re
            desc_match = re.search(r'# description:\s*(.+)', content)
            version_match = re.search(r'# version:\s*(.+)', content)
            
            return {
                "name": file_path.stem,
                "description": desc_match.group(1).strip() if desc_match else f"Python tool: {file_path.name}",
                "version": version_match.group(1).strip() if version_match else "1.0.0",
                "parameters": {},
                "examples": []
            }
        except Exception:
            return None
    
    def extract_api_parameters(self, tool_info: Dict) -> Dict:
        """Extract parameters from API tool info"""
        # This would be enhanced based on your specific API structure
        return {
            "content": {
                "type": "string",
                "description": "Content to process"
            }
        }
    
    def generate_api_examples(self, tool_name: str, tool_info: Dict) -> List[Dict]:
        """Generate examples for API tools"""
        return [{
            "description": f"Use {tool_name}",
            "parameters": {"content": "Sample content"}
        }]

# Global bridge instance
bridge = ClaudeToolBridge()

# FastAPI app
app = bridge.app

async def startup():
    """Initialize the bridge on startup"""
    print("🔧 Starting Claude Tool Bridge...")
    discovered = await bridge.discover_tools()
    print(f"📊 Discovered {len(discovered)} tools: {', '.join(discovered)}")
    print(f"🌐 Bridge running at: http://localhost:7000")
    print(f"🔗 Claude schema at: http://localhost:7000/claude/tools.json")

@app.on_event("startup")
async def startup_event():
    await startup()

if __name__ == "__main__":
    print("🚀 Initializing Claude Tool Bridge...")
    uvicorn.run(app, host="0.0.0.0", port=7000)
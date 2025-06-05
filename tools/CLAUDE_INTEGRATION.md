# 🤖 Claude Tool Integration System

**The game-changer is here!** This system allows Claude to easily discover and use all your tools through a unified interface.

## 🚀 Quick Start (30 seconds)

```bash
# Start the complete system
./start_claude_bridge.sh

# Test it works
curl http://localhost:7000/tools

# Let Claude use it
python claude_client.py
```

## 🎯 What This Does

**🔧 Tool Discovery**: Automatically finds all your tools from:
- ✅ Running API services (like your converter API)
- ✅ Command-line tools (managed by toolmgr)
- ✅ Python scripts and modules
- ✅ Custom tools you build

**🌉 Unified Bridge**: Single endpoint for Claude to access everything:
- ✅ Standardized request/response format
- ✅ Automatic error handling and retries
- ✅ Health monitoring and status checking
- ✅ Tool categorization and discovery

**🤖 Claude Interface**: Dead-simple Python client for Claude:
- ✅ `client.use_tool("tool_name", param1="value")`
- ✅ Automatic tool discovery and registration
- ✅ Built-in convenience methods
- ✅ Error handling and fallbacks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Claude      │───▶│  Tool Bridge    │───▶│   Your Tools    │
│                 │    │   Port 7000     │    │  APIs/CLI/etc   │
│ claude_client.py│    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Tool Registry  │
                       │ Auto-Discovery  │
                       └─────────────────┘
```

## 📊 What Claude Gets Access To

After running the system, Claude can instantly use:

### 🔄 **Format Converter Tools**
```python
# Convert CSV to JSON
client.convert_format("name,age\nJohn,25", "csv", "json")

# Convert Markdown to HTML
client.convert_format("# Hello\n**Bold text**", "markdown", "html")

# Convert JSON to XML
client.convert_format('{"name": "test"}', "json", "xml")
```

### 📊 **Document Analyzer Tools**
```python
# Analyze any text
client.analyze_document("Your document text here", "txt")

# Get readability scores, word counts, pattern detection
# Find emails, URLs, phone numbers automatically
```

### ⚡ **Command-Line Tools**
```python
# Run any CLI tool you've installed
client.run_cli_tool("file-organizer", "/path/to/directory")
client.run_cli_tool("quick-backup", "important-file.txt")
client.run_cli_tool("system-info")
```

### 🎯 **Custom Tools**
Any tool you create automatically becomes available to Claude!

## 🧪 Testing Your Setup

**1. Start Everything:**
```bash
./start_claude_bridge.sh
```

**2. Check Status:**
```bash
# See all discovered tools
curl http://localhost:7000/tools

# Health check
curl http://localhost:7000/health

# Get Claude-compatible schema
curl http://localhost:7000/claude/tools.json
```

**3. Test Python Interface:**
```bash
python claude_client.py
```

**4. Test Manual Tool Execution:**
```bash
curl -X POST http://localhost:7000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "document_analyzer",
    "parameters": {
      "text": "Test document",
      "content_type": "txt"
    }
  }'
```

## 🎪 Example Claude Usage

Once this is running, Claude can do things like:

```python
from claude_client import create_tool_client

client = create_tool_client()

# Analyze a document
result = client.analyze_document("""
# Project Report
This is our quarterly analysis. We've achieved great results!
Contact: info@company.com or call 555-1234.
""", "md")

print(f"Word count: {result['result']['data']['basic_stats']['word_count']}")
print(f"Emails found: {result['result']['data']['content_analysis']['emails_found']}")

# Convert formats
csv_data = "product,sales\nLaptops,1000\nPhones,1500"
json_result = client.convert_format(csv_data, "csv", "json")
print("Converted to JSON:", json_result['result']['converted_content'])

# Use CLI tools
client.run_cli_tool("system-info")
client.run_cli_tool("text-counter", "document.txt")
```

## 🔧 Adding New Tools

**For API Tools:**
1. Create a FastAPI service (like converter_api.py)
2. Start it on any port
3. The bridge auto-discovers it

**For CLI Tools:**
1. Install with toolmgr: `./toolmgr install my-script.sh`
2. Bridge automatically finds it
3. Claude can use it via `client.run_cli_tool()`

**For Python Tools:**
1. Add metadata comments to your Python file:
   ```python
   # description: What this tool does
   # version: 1.0.0
   # category: analysis
   ```
2. Make it executable
3. Bridge discovers it automatically

## 🛠️ Bridge API Endpoints

**Discovery & Info:**
- `GET /tools` - List all available tools
- `GET /tools/{tool_name}` - Get tool details
- `POST /discover` - Scan for new tools
- `GET /health` - Check tool health

**Execution:**
- `POST /execute` - Execute any tool
- `GET /claude/tools.json` - Claude-compatible schema

**Management:**
- `GET /` - Bridge status
- `GET /health` - System health

## 🎯 Benefits for You

**🚀 Instant Tool Access**: Claude can use any tool you build immediately
**🔄 Auto-Discovery**: New tools automatically become available  
**🛡️ Error Handling**: Robust error handling and recovery
**📊 Monitoring**: Health checks and status monitoring
**🎨 Flexibility**: Support for any type of tool (API, CLI, Python)
**⚡ Performance**: Async execution and proper resource management

## 🧩 Integration Examples

**Document Processing Pipeline:**
```python
# Claude can now do complex workflows like:
# 1. Analyze original document
analysis = client.analyze_document(text, "md")

# 2. Convert to different format
html_version = client.convert_format(text, "markdown", "html")

# 3. Run additional processing
processed = client.run_cli_tool("text-enhancer", "--input", "doc.html")
```

**Data Processing:**
```python
# 1. Convert CSV to JSON
json_data = client.convert_format(csv_content, "csv", "json")

# 2. Analyze the structure
analysis = client.analyze_document(json_data['result']['converted_content'], "json")

# 3. Generate report
report = client.run_cli_tool("data-reporter", "--json", "data.json")
```

## 🔍 Troubleshooting

**Bridge won't start:**
```bash
# Check if ports are free
lsof -i :7000 -i :8000

# Install missing dependencies
pip install fastapi uvicorn requests
```

**Tools not discovered:**
```bash
# Manual discovery trigger
curl -X POST http://localhost:7000/discover

# Check tool paths
./toolmgr list
```

**Tool execution fails:**
```bash
# Check tool health
curl http://localhost:7000/health

# Test individual tool
curl -X POST http://localhost:7000/execute -d '{"tool_name":"test","parameters":{}}'
```

## 🚀 Next Steps

1. **Start the system**: `./start_claude_bridge.sh`
2. **Test with Claude**: `python claude_client.py` 
3. **Add your tools**: Build new tools and they'll auto-register
4. **Expand capabilities**: Add file upload, batch processing, etc.

---

## 🎉 **This Is the Game-Changer!**

Now Claude can instantly access **any tool you create** through a simple, unified interface. No more manual integrations or complex setups - just build tools and Claude can use them immediately!

**🚀 Ready to revolutionize your workflow? Start the bridge and let Claude access your entire toolbox!**
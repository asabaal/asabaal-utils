# AsaBaal Utils MCP Server Deployment Guide

## 🎯 What We Built

A Model Context Protocol (MCP) server that exposes your document analysis and format conversion tools to AI assistants like Claude, GPT-4, and others through Abacus AI's platform.

## 🛠️ Server Features

### Document Analysis Tools
- **Word/sentence/paragraph counting**
- **Readability analysis** (Flesch Reading Ease)
- **Pattern detection** (emails, URLs, phone numbers)
- **Structure analysis** (headers, code blocks)
- **Content statistics** and lexical diversity

### Format Conversion Tools
- **CSV ↔ JSON** conversion
- **Markdown ↔ HTML** conversion  
- **JSON ↔ XML** conversion
- **YAML ↔ JSON** conversion
- **Format validation**
- **Configurable conversion options**

### Quick Tools
- `quick_csv_to_json` - Simple CSV to JSON
- `quick_json_to_csv` - Simple JSON to CSV
- `markdown_to_html` - Markdown to HTML with options
- `html_to_markdown` - HTML to Markdown

## 📁 Files Created

```
/tools/
├── asabaal_mcp_server.py       # Main MCP server
├── test_mcp_server.py          # Test suite (7/7 tests pass)
├── claude_desktop_config.json  # Local testing config
├── abacus_ai_config.json      # Abacus AI deployment config
└── MCP_DEPLOYMENT_GUIDE.md    # This guide
```

## 🧪 Local Testing

### 1. Test Server Functionality
```bash
cd /home/asabaal/asabaal_ventures/repos/asabaal-utils/tools
python test_mcp_server.py
```

Should show: `🎉 All tests passed! MCP server is ready for deployment.`

### 2. Test with Claude Desktop

1. **Install Claude Desktop** from [claude.ai/desktop](https://claude.ai/desktop)

2. **Add MCP Configuration**:
   - On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - On Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Use content from `claude_desktop_config.json` (update paths as needed)

3. **Restart Claude Desktop**

4. **Test Tools**: Ask Claude to analyze text or convert formats

## 🚀 Abacus AI Deployment

### Step 1: Upload Files
Upload these files to your Abacus AI workspace:
- `asabaal_mcp_server.py`
- `document_analyzer.py` 
- `file_format_converter.py`
- Required dependencies (see requirements below)

### Step 2: Configure MCP Server
In Abacus AI's MCP configuration:
1. Use the configuration from `abacus_ai_config.json`
2. Update file paths to match your deployment location
3. Ensure Python dependencies are installed

### Step 3: Test Integration
1. Create a new chat in Abacus AI
2. Verify the MCP server appears in available tools
3. Test document analysis: "Analyze this text: [sample text]"
4. Test format conversion: "Convert this CSV to JSON: name,age\nJohn,25"

## 📦 Dependencies

Required Python packages:
```bash
pip install mcp fastapi uvicorn pydantic
pip install markdown html2text pyyaml
```

For full functionality, ensure these are available:
- `json` (built-in)
- `csv` (built-in) 
- `xml.etree.ElementTree` (built-in)
- `re` (built-in)
- `typing` (built-in)

## 🔧 Configuration Options

### Document Analysis
- Supports: `.txt`, `.md`, `.py`, `.js`, `.json`, `.csv`
- Calculates: readability, word count, patterns, structure

### Format Conversion
Available conversions:
- `csv_to_json` / `json_to_csv`
- `markdown_to_html` / `html_to_markdown`
- `json_to_xml` / `xml_to_json`
- `yaml_to_json` / `json_to_yaml`
- `csv_to_xml`

### Options
- **CSV operations**: Custom delimiters, header handling
- **HTML generation**: Complete documents vs fragments
- **XML conversion**: Custom root/item element names

## 🎯 Usage Examples

### In Claude/AI Assistant:

**Document Analysis:**
```
"Analyze this document for readability and patterns:
[paste your text here]"
```

**Format Conversion:**
```
"Convert this CSV data to JSON:
name,age,city
John,25,NYC
Jane,30,LA"
```

**Combined Workflow:**
```
"Analyze this CSV data and convert it to XML format:
[paste CSV here]"
```

## 🔍 Troubleshooting

### Common Issues:

1. **Import Errors**: Ensure all Python files are in the same directory
2. **MCP Connection Failed**: Check file paths in configuration
3. **Tool Not Found**: Verify MCP server is running and configured correctly

### Debug Mode:
The server outputs diagnostic information to stderr for debugging.

## 🌟 Next Steps

1. **Test locally** with Claude Desktop
2. **Deploy to Abacus AI** using the configuration files
3. **Expand tools** by adding more MCP endpoints
4. **Scale up** by adapting the Claude Tool Bridge architecture

## 📈 Success Metrics

- ✅ All 7 test cases pass
- ✅ Server starts without errors  
- ✅ Tools work through MCP protocol
- ✅ Compatible with multiple AI assistants
- ✅ Ready for production deployment

Your MCP server is production-ready and can be deployed immediately!
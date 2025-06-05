# File Format Converter Setup & Testing Guide

## Quick Setup (5 minutes!)

### 1. Install Dependencies
Create a `requirements.txt` file:
```txt
fastapi
uvicorn[standard]
python-multipart
markdown
html2text
PyYAML
```

Install everything:
```bash
pip install -r requirements.txt
```

### 2. Save the Files
You need these 3 files in the same directory:

- `document_analyzer.py` (from previous artifact)
- `file_format_converter.py` (first artifact above)  
- `converter_api.py` (second artifact above)

### 3. Run the API
```bash
python converter_api.py
```

You'll see:
```
🚀 Starting AI Utility Tools API...
📊 Available tools: Document Analyzer, Format Converter
🔗 API docs will be available at: http://localhost:8000/docs
🧪 Test endpoints at: /tools/test/converter and /tools/test/analyzer
```

## Instant Testing

### Test 1: Quick Converter Test
```bash
curl http://localhost:8000/tools/test/converter
```

### Test 2: Quick Analyzer Test  
```bash
curl http://localhost:8000/tools/test/analyzer
```

### Test 3: CSV to JSON Conversion
```bash
curl -X POST "http://localhost:8000/tools/convert_format" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "name,age,city\nAlice,25,NYC\nBob,30,LA",
    "from_format": "csv", 
    "to_format": "json"
  }'
```

Expected output:
```json
{
  "success": true,
  "data": {
    "success": true,
    "original_format": "csv",
    "target_format": "json", 
    "converted_content": "[\n  {\n    \"name\": \"Alice\",\n    \"age\": \"25\",\n    \"city\": \"NYC\"\n  },\n  {\n    \"name\": \"Bob\",\n    \"age\": \"30\",\n    \"city\": \"LA\"\n  }\n]",
    "conversion_info": {
      "original_size_chars": 32,
      "converted_size_chars": 134,
      "size_change_percent": 318.75
    }
  }
}
```

### Test 4: Markdown to HTML
```bash
curl -X POST "http://localhost:8000/tools/convert_format" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Hello World\n\nThis is **bold** text with a [link](https://example.com).",
    "from_format": "markdown",
    "to_format": "html"
  }'
```

### Test 5: Combined Analysis + Conversion
```bash
curl -X POST "http://localhost:8000/tools/analyze_and_convert" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "name,email,phone\nJohn,john@email.com,555-1234\nJane,jane@email.com,555-5678",
    "from_format": "csv",
    "to_format": "json",
    "analyze_original": true,
    "analyze_converted": true
  }'
```

## Interactive API Documentation

Visit `http://localhost:8000/docs` in your browser for:
- **Interactive API testing**
- **Complete endpoint documentation** 
- **Request/response examples**
- **Try it out** buttons for each endpoint

## Real-World Usage Examples

### Example 1: Clean CSV Data and Convert
```python
import requests

# Messy CSV data
csv_data = """name,age,city
John Doe,25,"New York, NY"
Jane Smith,30,London
"Bob Johnson",35,"Paris, France" """

# Convert to clean JSON
response = requests.post("http://localhost:8000/tools/convert_format", json={
    "content": csv_data,
    "from_format": "csv", 
    "to_format": "json"
})

print("Clean JSON:", response.json()["data"]["converted_content"])
```

### Example 2: Documentation Pipeline
```python
# Convert README.md to HTML for website
markdown_content = """
# My Project

## Features
- Fast processing
- Easy to use  
- Well documented

## Installation
```bash
pip install my-project
```

Visit our [website](https://example.com) for more info.
"""

response = requests.post("http://localhost:8000/tools/convert_format", json={
    "content": markdown_content,
    "from_format": "markdown",
    "to_format": "html",
    "options": {
        "full_html": True,
        "title": "My Project Documentation"
    }
})

html_output = response.json()["data"]["converted_content"]
```

### Example 3: Data Analysis Workflow
```python
# 1. Analyze original CSV
# 2. Convert to JSON 
# 3. Analyze the JSON structure
response = requests.post("http://localhost:8000/tools/analyze_and_convert", json={
    "content": "product,price,category\nLaptop,999,Electronics\nBook,15,Education",
    "from_format": "csv",
    "to_format": "json", 
    "analyze_original": True,
    "analyze_converted": True
})

workflow_results = response.json()["data"]
print("Original analysis:", workflow_results["original_analysis"])
print("Conversion result:", workflow_results["conversion"])
print("Converted analysis:", workflow_results["converted_analysis"])
```

## Available Conversion Options

### CSV ↔ JSON
```json
{
  "delimiter": ",",           // Field separator
  "include_headers": true     // Use first row as headers
}
```

### Markdown ↔ HTML  
```json
{
  "full_html": false,         // Generate complete HTML document
  "title": "My Document",     // Title for full HTML
  "extensions": ["extra"]     // Markdown extensions
}
```

### JSON ↔ XML
```json
{
  "root_name": "root",        // XML root element name
  "item_name": "item"         // List item element name  
}
```

## File Upload Examples

### Upload and Convert a File
```bash
curl -X POST "http://localhost:8000/tools/convert_file" \
  -F "file=@data.csv" \
  -F "to_format=json" \
  -F "options={\"delimiter\": \",\"}"
```

### Upload and Analyze a File
```bash
curl -X POST "http://localhost:8000/tools/analyze_document_file" \
  -F "file=@document.txt"
```

## What You Can Build Next

This foundation lets you easily add:

1. **More formats**: Add Excel, PDF, Word doc support
2. **Data transformations**: Add data cleaning, filtering, sorting
3. **Batch processing**: Process multiple files at once
4. **Custom workflows**: Chain multiple operations together
5. **Scheduled jobs**: Automate regular conversions

The architecture makes it super easy to add new capabilities while keeping everything organized and testable!

## Troubleshooting

**Port already in use?**
```bash
python converter_api.py --port 8001
```

**Missing dependencies?**
```bash
pip install --upgrade -r requirements.txt
```

**File encoding issues?**
Save files with UTF-8 encoding, especially if you have non-ASCII characters.

**Large files timing out?**
For production, add file size limits and async processing for large files.
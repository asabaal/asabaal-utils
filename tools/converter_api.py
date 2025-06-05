# converter_api.py - Updated tool_api.py with File Format Converter
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
import json

# Import our tools
from document_analyzer import DocumentAnalyzer
from file_format_converter import FileFormatConverter

app = FastAPI(title="AI Utility Tools API", version="2.0.0")

# Initialize our tools
doc_analyzer = DocumentAnalyzer()
format_converter = FileFormatConverter()

# Request Models
class TextAnalysisRequest(BaseModel):
    text: str
    content_type: str = "txt"

class FormatConversionRequest(BaseModel):
    content: str
    from_format: str
    to_format: str
    options: Optional[Dict] = None

class ToolResponse(BaseModel):
    success: bool
    data: dict = None
    message: str
    tool_name: str

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Utility Tools API", 
        "version": "2.0.0",
        "available_tools": ["document_analyzer", "format_converter"]
    }

# Document Analyzer endpoints (existing)
@app.post("/tools/analyze_document", response_model=ToolResponse)
async def analyze_document_text(request: TextAnalysisRequest):
    """Analyze text content and return comprehensive statistics"""
    try:
        result = doc_analyzer.analyze_document(request.text, f".{request.content_type}")
        
        return ToolResponse(
            success=result["success"],
            data=result.get("data"),
            message=result["message"],
            tool_name="document_analyzer"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/analyze_document_file")
async def analyze_document_file(file: UploadFile = File(...)):
    """Analyze an uploaded file"""
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        result = doc_analyzer.analyze_document(text_content, file.filename.split('.')[-1])
        
        return ToolResponse(
            success=result["success"],
            data=result.get("data"),
            message=f"Analyzed file: {file.filename}",
            tool_name="document_analyzer"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Format Converter endpoints (new)
@app.post("/tools/convert_format", response_model=ToolResponse)
async def convert_format(request: FormatConversionRequest):
    """Convert content between different formats"""
    try:
        result = format_converter.convert(
            request.content, 
            request.from_format, 
            request.to_format, 
            request.options or {}
        )
        
        return ToolResponse(
            success=result["success"],
            data=result if result["success"] else {"error": result.get("error")},
            message=result.get("message", "Conversion completed"),
            tool_name="format_converter"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/convert_file")
async def convert_file(
    file: UploadFile = File(...),
    to_format: str = "json",
    options: str = "{}"
):
    """Convert an uploaded file to a different format"""
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Determine source format from filename
        from_format = file.filename.split('.')[-1].lower()
        
        # Parse options
        parsed_options = json.loads(options) if options != "{}" else {}
        
        result = format_converter.convert(text_content, from_format, to_format, parsed_options)
        
        return ToolResponse(
            success=result["success"],
            data=result if result["success"] else {"error": result.get("error")},
            message=f"Converted {file.filename} from {from_format} to {to_format}",
            tool_name="format_converter"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/conversion_options")
async def get_conversion_options():
    """Get all supported format conversions and their options"""
    return {
        "supported_conversions": format_converter.supported_conversions,
        "supported_formats": format_converter.get_supported_formats(),
        "conversion_options": {
            "csv_to_json": {
                "delimiter": "Field delimiter (default: ',')",
                "include_headers": "Include headers in output (default: true)"
            },
            "json_to_csv": {
                "delimiter": "Field delimiter (default: ',')"
            },
            "markdown_to_html": {
                "extensions": "Markdown extensions to use (default: ['extra', 'codehilite', 'toc'])",
                "full_html": "Generate complete HTML document (default: false)",
                "title": "Title for full HTML document"
            },
            "html_to_markdown": {
                "ignore_links": "Ignore links in conversion (default: false)",
                "ignore_images": "Ignore images in conversion (default: false)",
                "body_width": "Text wrapping width (default: 0 = no wrapping)"
            },
            "json_to_xml": {
                "root_name": "Name for XML root element (default: 'root')",
                "item_name": "Name for list item elements (default: 'item')"
            },
            "csv_to_xml": {
                "root_name": "Name for XML root element (default: 'data')",
                "item_name": "Name for row elements (default: 'row')",
                "delimiter": "CSV field delimiter (default: ',')"
            }
        }
    }

@app.post("/tools/validate_format")
async def validate_format(content: str, format_type: str):
    """Validate that content matches the expected format"""
    try:
        result = format_converter.validate_format(content, format_type)
        
        return ToolResponse(
            success=True,
            data=result,
            message=f"Validation completed for {format_type}",
            tool_name="format_converter"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Combined workflow endpoints
@app.post("/tools/analyze_and_convert")
async def analyze_and_convert(
    content: str,
    from_format: str = "txt",
    to_format: str = "json",
    analyze_original: bool = True,
    analyze_converted: bool = False,
    conversion_options: Optional[Dict] = None
):
    """Analyze a document and optionally convert it to another format"""
    try:
        results = {}
        
        # Analyze original content
        if analyze_original:
            analysis_result = doc_analyzer.analyze_document(content, f".{from_format}")
            results["original_analysis"] = analysis_result
        
        # Convert format
        conversion_result = format_converter.convert(
            content, from_format, to_format, conversion_options or {}
        )
        results["conversion"] = conversion_result
        
        # Analyze converted content
        if analyze_converted and conversion_result["success"]:
            converted_analysis = doc_analyzer.analyze_document(
                conversion_result["converted_content"], f".{to_format}"
            )
            results["converted_analysis"] = converted_analysis
        
        return ToolResponse(
            success=True,
            data=results,
            message=f"Completed analysis and conversion workflow",
            tool_name="combined_workflow"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# List all tools and capabilities
@app.get("/tools/list")
async def list_tools():
    """List all available tools and their capabilities"""
    return {
        "tools": {
            "document_analyzer": {
                "name": "Document Analyzer",
                "description": "Analyzes text documents for statistics, readability, and patterns",
                "endpoints": ["/tools/analyze_document", "/tools/analyze_document_file"],
                "supported_formats": [".txt", ".md", ".py", ".js", ".json", ".csv"],
                "capabilities": [
                    "Word/sentence/paragraph counting",
                    "Readability analysis", 
                    "Pattern detection (emails, URLs, phone numbers)",
                    "Structure analysis",
                    "Content statistics"
                ]
            },
            "format_converter": {
                "name": "File Format Converter",
                "description": "Converts content between different file formats",
                "endpoints": [
                    "/tools/convert_format", 
                    "/tools/convert_file",
                    "/tools/validate_format",
                    "/tools/conversion_options"
                ],
                "supported_conversions": list(format_converter.supported_conversions.keys()),
                "capabilities": [
                    "CSV ↔ JSON conversion",
                    "Markdown ↔ HTML conversion", 
                    "JSON ↔ XML conversion",
                    "YAML ↔ JSON conversion",
                    "Format validation",
                    "Configurable conversion options"
                ]
            },
            "combined_workflows": {
                "name": "Combined Workflows",
                "description": "Combines multiple tools for complex operations",
                "endpoints": ["/tools/analyze_and_convert"],
                "capabilities": [
                    "Analyze then convert documents",
                    "Compare before/after analysis",
                    "Batch processing workflows"
                ]
            }
        }
    }

# Quick test endpoints
@app.get("/tools/test/converter")
async def test_converter():
    """Quick test of the format converter"""
    test_csv = "name,age\nJohn,25\nJane,30"
    
    result = format_converter.convert(test_csv, 'csv', 'json')
    
    return {
        "test": "CSV to JSON conversion",
        "input": test_csv,
        "output": result
    }

@app.get("/tools/test/analyzer")
async def test_analyzer():
    """Quick test of the document analyzer"""
    test_text = "This is a sample document. It has multiple sentences! How does it analyze?"
    
    result = doc_analyzer.analyze_document(test_text, '.txt')
    
    return {
        "test": "Document analysis",
        "input": test_text,
        "output": result
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting AI Utility Tools API...")
    print("📊 Available tools: Document Analyzer, Format Converter")
    print("🔗 API docs will be available at: http://localhost:8000/docs")
    print("🧪 Test endpoints at: /tools/test/converter and /tools/test/analyzer")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
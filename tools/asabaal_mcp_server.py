#!/usr/bin/env python3
"""
AsaBaal Utils MCP Server

Model Context Protocol server that exposes document analysis and format conversion tools
to AI assistants like Claude, GPT-4, etc.

Features:
- Document analysis (word count, readability, patterns)
- Format conversion (CSV, JSON, XML, YAML, Markdown, HTML)
- Content validation
- Combined workflows

Usage:
    python asabaal_mcp_server.py

For local testing with Claude Desktop, add to your config:
    {
      "mcpServers": {
        "asabaal-utils": {
          "command": "python",
          "args": ["/path/to/asabaal_mcp_server.py"],
          "env": {}
        }
      }
    }
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional

# Add tools directory to path so we can import our modules
tools_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tools_dir)

from mcp.server.fastmcp import FastMCP
from mcp.server.models import *

# Import our tools
from document_analyzer import DocumentAnalyzer
from file_format_converter import FileFormatConverter

# Initialize our tools
doc_analyzer = DocumentAnalyzer()
format_converter = FileFormatConverter()

# Create MCP server
mcp = FastMCP("AsaBaal Utils")

@mcp.tool()
def analyze_document(
    content: str,
    content_type: str = "txt"
) -> dict:
    """
    Analyze text content and return comprehensive statistics including word count, 
    readability scores, patterns, and structure analysis.
    
    Args:
        content: The text content to analyze
        content_type: File type/extension (txt, md, py, js, json, csv)
    
    Returns:
        Dictionary with analysis results including basic stats, readability, 
        content patterns, and structure information
    """
    try:
        result = doc_analyzer.analyze_document(content, f".{content_type}")
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to analyze document"
        }

@mcp.tool()
def convert_format(
    content: str,
    from_format: str,
    to_format: str,
    delimiter: str = ",",
    include_headers: bool = True,
    full_html: bool = False,
    root_name: str = "root",
    item_name: str = "item"
) -> dict:
    """
    Convert content between different file formats (CSV, JSON, XML, YAML, Markdown, HTML).
    
    Args:
        content: The content to convert
        from_format: Source format (csv, json, xml, yaml, markdown, html)
        to_format: Target format (csv, json, xml, yaml, markdown, html)
        delimiter: Field delimiter for CSV operations (default: ",")
        include_headers: Include headers in CSV output (default: True)
        full_html: Generate complete HTML document when converting to HTML (default: False)
        root_name: XML root element name (default: "root")
        item_name: XML list item element name (default: "item")
    
    Returns:
        Dictionary with conversion results including the converted content and conversion info
    """
    try:
        # Build options dictionary
        options = {
            "delimiter": delimiter,
            "include_headers": include_headers,
            "full_html": full_html,
            "root_name": root_name,
            "item_name": item_name
        }
        
        result = format_converter.convert(content, from_format, to_format, options)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to convert from {from_format} to {to_format}"
        }

@mcp.tool()
def validate_format(content: str, format_type: str) -> dict:
    """
    Validate that content matches the expected format.
    
    Args:
        content: The content to validate
        format_type: Expected format (json, csv, xml, yaml, markdown, html)
    
    Returns:
        Dictionary with validation results indicating if content is valid
    """
    try:
        result = format_converter.validate_format(content, format_type)
        return {
            "success": True,
            "data": result,
            "message": f"Validation completed for {format_type}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to validate {format_type} format"
        }

@mcp.tool()
def get_supported_conversions() -> dict:
    """
    Get list of all supported format conversions and available options.
    
    Returns:
        Dictionary containing supported conversions, formats, and detailed options
    """
    try:
        return {
            "success": True,
            "data": {
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
                        "full_html": "Generate complete HTML document (default: false)"
                    },
                    "html_to_markdown": {
                        "ignore_links": "Ignore links in conversion (default: false)",
                        "ignore_images": "Ignore images in conversion (default: false)"
                    },
                    "json_to_xml": {
                        "root_name": "Name for XML root element (default: 'root')",
                        "item_name": "Name for list item elements (default: 'item')"
                    }
                }
            },
            "message": "Retrieved supported conversions and options"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get supported conversions"
        }

@mcp.tool()
def analyze_and_convert(
    content: str,
    from_format: str = "txt",
    to_format: str = "json",
    analyze_original: bool = True,
    analyze_converted: bool = False,
    delimiter: str = ",",
    include_headers: bool = True,
    full_html: bool = False
) -> dict:
    """
    Combined workflow: analyze a document and optionally convert it to another format.
    
    Args:
        content: The content to process
        from_format: Source format (default: "txt")
        to_format: Target format (default: "json")
        analyze_original: Whether to analyze the original content (default: True)
        analyze_converted: Whether to analyze the converted content (default: False)
        delimiter: Field delimiter for CSV operations (default: ",")
        include_headers: Include headers in CSV output (default: True)
        full_html: Generate complete HTML document (default: False)
    
    Returns:
        Dictionary with analysis and conversion results
    """
    try:
        results = {}
        
        # Analyze original content
        if analyze_original:
            analysis_result = doc_analyzer.analyze_document(content, f".{from_format}")
            results["original_analysis"] = analysis_result
        
        # Convert format
        conversion_options = {
            "delimiter": delimiter,
            "include_headers": include_headers,
            "full_html": full_html
        }
        
        conversion_result = format_converter.convert(
            content, from_format, to_format, conversion_options
        )
        results["conversion"] = conversion_result
        
        # Analyze converted content
        if analyze_converted and conversion_result.get("success"):
            converted_analysis = doc_analyzer.analyze_document(
                conversion_result["converted_content"], f".{to_format}"
            )
            results["converted_analysis"] = converted_analysis
        
        return {
            "success": True,
            "data": results,
            "message": f"Completed analysis and conversion workflow from {from_format} to {to_format}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to complete analysis and conversion workflow"
        }

@mcp.tool()
def quick_csv_to_json(csv_content: str, has_headers: bool = True) -> dict:
    """
    Quick CSV to JSON conversion with simple options.
    
    Args:
        csv_content: CSV content to convert
        has_headers: Whether CSV has headers (default: True)
    
    Returns:
        Dictionary with JSON conversion result
    """
    try:
        options = {"include_headers": has_headers}
        result = format_converter.convert(csv_content, "csv", "json", options)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to convert CSV to JSON"
        }

@mcp.tool()
def quick_json_to_csv(json_content: str) -> dict:
    """
    Quick JSON to CSV conversion.
    
    Args:
        json_content: JSON content to convert
    
    Returns:
        Dictionary with CSV conversion result
    """
    try:
        result = format_converter.convert(json_content, "json", "csv", {})
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to convert JSON to CSV"
        }

@mcp.tool()
def markdown_to_html(markdown_content: str, complete_document: bool = False) -> dict:
    """
    Convert Markdown to HTML.
    
    Args:
        markdown_content: Markdown content to convert
        complete_document: Generate complete HTML document with head/body tags (default: False)
    
    Returns:
        Dictionary with HTML conversion result
    """
    try:
        options = {"full_html": complete_document}
        result = format_converter.convert(markdown_content, "markdown", "html", options)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to convert Markdown to HTML"
        }

@mcp.tool()
def html_to_markdown(html_content: str) -> dict:
    """
    Convert HTML to Markdown.
    
    Args:
        html_content: HTML content to convert
    
    Returns:
        Dictionary with Markdown conversion result
    """
    try:
        result = format_converter.convert(html_content, "html", "markdown", {})
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to convert HTML to Markdown"
        }

# Resource endpoint for getting tool information
@mcp.resource("asabaal://tools/info")
def get_tool_info() -> str:
    """Get information about available tools and their capabilities."""
    info = {
        "server_name": "AsaBaal Utils MCP Server",
        "version": "1.0.0",
        "description": "Document analysis and format conversion tools for AI assistants",
        "tools": {
            "analyze_document": {
                "description": "Comprehensive document analysis including statistics, readability, and patterns",
                "supported_formats": [".txt", ".md", ".py", ".js", ".json", ".csv"]
            },
            "convert_format": {
                "description": "Convert between various file formats",
                "supported_conversions": list(format_converter.supported_conversions.keys())
            },
            "validate_format": {
                "description": "Validate content against expected format"
            },
            "analyze_and_convert": {
                "description": "Combined workflow for analysis and conversion"
            }
        },
        "quick_tools": [
            "quick_csv_to_json",
            "quick_json_to_csv", 
            "markdown_to_html",
            "html_to_markdown"
        ]
    }
    return json.dumps(info, indent=2)

async def main():
    """Run the MCP server."""
    # Import here to avoid issues if mcp modules aren't available
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options()
        )

if __name__ == "__main__":
    print("🚀 Starting AsaBaal Utils MCP Server...", file=sys.stderr)
    print("📊 Available tools: Document Analyzer, Format Converter", file=sys.stderr)
    print("🔗 Ready for AI assistant connections", file=sys.stderr)
    
    asyncio.run(main())
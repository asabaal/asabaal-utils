# file_format_converter.py
import json
import csv
import xml.etree.ElementTree as ET
import yaml
import markdown
import html2text
from io import StringIO
from typing import Dict, Any, List, Union
import re

class FileFormatConverter:
    def __init__(self):
        self.supported_conversions = {
            'csv_to_json': 'Convert CSV data to JSON format',
            'json_to_csv': 'Convert JSON data to CSV format',
            'markdown_to_html': 'Convert Markdown to HTML',
            'html_to_markdown': 'Convert HTML to Markdown',
            'json_to_xml': 'Convert JSON to XML format',
            'xml_to_json': 'Convert XML to JSON format',
            'csv_to_xml': 'Convert CSV to XML format',
            'yaml_to_json': 'Convert YAML to JSON format',
            'json_to_yaml': 'Convert JSON to YAML format'
        }
    
    def convert(self, content: str, from_format: str, to_format: str, options: Dict = None) -> Dict[str, Any]:
        """
        Main conversion method that routes to specific converters
        """
        options = options or {}
        conversion_key = f"{from_format}_to_{to_format}"
        
        if conversion_key not in self.supported_conversions:
            return {
                "success": False,
                "error": f"Conversion from {from_format} to {to_format} not supported",
                "supported_conversions": list(self.supported_conversions.keys())
            }
        
        try:
            # Route to appropriate conversion method
            method_name = f"_{conversion_key}"
            if hasattr(self, method_name):
                result = getattr(self, method_name)(content, options)
                return {
                    "success": True,
                    "original_format": from_format,
                    "target_format": to_format,
                    "converted_content": result,
                    "conversion_info": self._get_conversion_info(content, result, from_format, to_format),
                    "message": f"Successfully converted from {from_format} to {to_format}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Conversion method not implemented: {conversion_key}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to convert from {from_format} to {to_format}"
            }
    
    def _csv_to_json(self, content: str, options: Dict) -> str:
        """Convert CSV to JSON"""
        delimiter = options.get('delimiter', ',')
        include_headers = options.get('include_headers', True)
        
        # Handle different line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        if include_headers:
            reader = csv.DictReader(StringIO(content), delimiter=delimiter)
            data = list(reader)
        else:
            reader = csv.reader(StringIO(content), delimiter=delimiter)
            data = [list(row) for row in reader]
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _json_to_csv(self, content: str, options: Dict) -> str:
        """Convert JSON to CSV"""
        delimiter = options.get('delimiter', ',')
        
        data = json.loads(content)
        
        if not data:
            return ""
        
        output = StringIO()
        
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                # List of dictionaries - use DictWriter
                fieldnames = set()
                for item in data:
                    if isinstance(item, dict):
                        fieldnames.update(item.keys())
                fieldnames = list(fieldnames)
                
                writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
            else:
                # List of simple values
                writer = csv.writer(output, delimiter=delimiter)
                for item in data:
                    writer.writerow([item] if not isinstance(item, (list, tuple)) else item)
        elif isinstance(data, dict):
            # Single dictionary - convert to single row CSV
            writer = csv.DictWriter(output, fieldnames=data.keys(), delimiter=delimiter)
            writer.writeheader()
            writer.writerow(data)
        else:
            # Simple value
            writer = csv.writer(output, delimiter=delimiter)
            writer.writerow([data])
        
        return output.getvalue()
    
    def _markdown_to_html(self, content: str, options: Dict) -> str:
        """Convert Markdown to HTML"""
        extensions = options.get('extensions', ['extra', 'codehilite', 'toc'])
        
        md = markdown.Markdown(extensions=extensions)
        html_content = md.convert(content)
        
        # Add basic HTML structure if requested
        if options.get('full_html', False):
            title = options.get('title', 'Converted Document')
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        return html_content
    
    def _html_to_markdown(self, content: str, options: Dict) -> str:
        """Convert HTML to Markdown"""
        h = html2text.HTML2Text()
        h.ignore_links = options.get('ignore_links', False)
        h.ignore_images = options.get('ignore_images', False)
        h.body_width = options.get('body_width', 0)  # 0 = no wrapping
        
        return h.handle(content)
    
    def _json_to_xml(self, content: str, options: Dict) -> str:
        """Convert JSON to XML"""
        root_name = options.get('root_name', 'root')
        item_name = options.get('item_name', 'item')
        
        data = json.loads(content)
        
        def dict_to_xml(data, parent_name):
            if isinstance(data, dict):
                element = ET.Element(parent_name)
                for key, value in data.items():
                    child = dict_to_xml(value, key)
                    element.append(child)
                return element
            elif isinstance(data, list):
                element = ET.Element(parent_name)
                for item in data:
                    child = dict_to_xml(item, item_name)
                    element.append(child)
                return element
            else:
                element = ET.Element(parent_name)
                element.text = str(data)
                return element
        
        root = dict_to_xml(data, root_name)
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    def _xml_to_json(self, content: str, options: Dict) -> str:
        """Convert XML to JSON"""
        def xml_to_dict(element):
            result = {}
            
            # Add attributes
            if element.attrib:
                result.update(element.attrib)
            
            # Add text content
            if element.text and element.text.strip():
                if len(element) == 0:  # No children, just text
                    return element.text.strip()
                else:
                    result['text'] = element.text.strip()
            
            # Add children
            for child in element:
                child_data = xml_to_dict(child)
                if child.tag in result:
                    # Convert to list if multiple children with same tag
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            
            return result or element.text
        
        root = ET.fromstring(content)
        data = {root.tag: xml_to_dict(root)}
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _csv_to_xml(self, content: str, options: Dict) -> str:
        """Convert CSV to XML (via JSON intermediate)"""
        # First convert to JSON, then to XML
        json_content = self._csv_to_json(content, options)
        xml_options = {
            'root_name': options.get('root_name', 'data'),
            'item_name': options.get('item_name', 'row')
        }
        return self._json_to_xml(json_content, xml_options)
    
    def _yaml_to_json(self, content: str, options: Dict) -> str:
        """Convert YAML to JSON"""
        data = yaml.safe_load(content)
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _json_to_yaml(self, content: str, options: Dict) -> str:
        """Convert JSON to YAML"""
        data = json.loads(content)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    def _get_conversion_info(self, original: str, converted: str, from_format: str, to_format: str) -> Dict:
        """Generate information about the conversion"""
        return {
            "original_size_chars": len(original),
            "converted_size_chars": len(converted),
            "original_lines": len(original.splitlines()),
            "converted_lines": len(converted.splitlines()),
            "size_change_percent": round(((len(converted) - len(original)) / len(original)) * 100, 2) if original else 0
        }
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Return supported input and output formats"""
        formats = {}
        for conversion in self.supported_conversions:
            from_fmt, to_fmt = conversion.split('_to_')
            if from_fmt not in formats:
                formats[from_fmt] = []
            formats[from_fmt].append(to_fmt)
        
        return formats
    
    def validate_format(self, content: str, format_type: str) -> Dict[str, Any]:
        """Validate that content matches the expected format"""
        try:
            if format_type == 'json':
                json.loads(content)
                return {"valid": True, "message": "Valid JSON"}
            
            elif format_type == 'csv':
                reader = csv.reader(StringIO(content))
                rows = list(reader)
                return {"valid": True, "message": f"Valid CSV with {len(rows)} rows"}
            
            elif format_type == 'xml':
                ET.fromstring(content)
                return {"valid": True, "message": "Valid XML"}
            
            elif format_type == 'yaml':
                yaml.safe_load(content)
                return {"valid": True, "message": "Valid YAML"}
            
            elif format_type in ['markdown', 'html']:
                # Basic validation - just check it's text
                return {"valid": True, "message": f"Valid {format_type}"}
            
            else:
                return {"valid": False, "message": f"Unknown format: {format_type}"}
        
        except Exception as e:
            return {"valid": False, "message": f"Invalid {format_type}: {str(e)}"}


# Example usage and testing
def test_converter():
    """Test the converter with sample data"""
    converter = FileFormatConverter()
    
    # Test CSV to JSON
    sample_csv = """name,age,city
John,25,New York
Jane,30,London
Bob,35,Paris"""
    
    print("=== CSV to JSON ===")
    result = converter.convert(sample_csv, 'csv', 'json')
    if result['success']:
        print(result['converted_content'])
        print(f"Conversion info: {result['conversion_info']}")
    
    # Test JSON to CSV
    sample_json = '''[
        {"name": "Alice", "age": 28, "city": "Tokyo"},
        {"name": "Charlie", "age": 32, "city": "Sydney"}
    ]'''
    
    print("\n=== JSON to CSV ===")
    result = converter.convert(sample_json, 'json', 'csv')
    if result['success']:
        print(result['converted_content'])
    
    # Test Markdown to HTML
    sample_markdown = """# Hello World

This is a **sample** document with:

- List item 1
- List item 2

```python
def hello():
    print("Hello, World!")
```

Visit [Google](https://google.com) for more info."""
    
    print("\n=== Markdown to HTML ===")
    result = converter.convert(sample_markdown, 'markdown', 'html')
    if result['success']:
        print(result['converted_content'][:200] + "...")
    
    return converter

if __name__ == "__main__":
    test_converter()
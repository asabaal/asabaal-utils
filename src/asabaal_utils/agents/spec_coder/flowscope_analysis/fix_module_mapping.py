#!/usr/bin/env python3
"""
Script to extract duplicated moduleMapping from HTML files and replace with shared JS file.
"""

import os
import re
from pathlib import Path

def fix_html_files():
    """Replace inline moduleMapping with script tag to shared JS file."""
    
    reports_dir = Path("module_reports")
    if not reports_dir.exists():
        print(f"Directory {reports_dir} not found")
        return
    
    # Pattern to match the moduleMapping declaration
    pattern = r'const moduleMapping = \{[^}]+\};'
    
    updated_files = 0
    
    for html_file in reports_dir.glob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file contains the moduleMapping
            if re.search(pattern, content):
                # Replace the inline moduleMapping with script tag
                updated_content = re.sub(
                    pattern,
                    '// Module mapping loaded from shared file',
                    content
                )
                
                # Add script tag for shared module mapping if not already present
                if 'module_mapping.js' not in updated_content:
                    # Find where to insert the script tag (after the first </script> tag)
                    script_tag = '\n<script src="module_mapping.js"></script>\n'
                    updated_content = updated_content.replace('</script>', f'</script>{script_tag}', 1)
                
                # Write back the updated content
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                updated_files += 1
                print(f"Updated: {html_file.name}")
            
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    print(f"\nUpdated {updated_files} HTML files")

if __name__ == "__main__":
    fix_html_files()
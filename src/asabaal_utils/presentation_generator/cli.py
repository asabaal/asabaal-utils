"""
Command-line interface for presentation generator.

This module provides a CLI tool for converting JSON presentation data to HTML.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from .presentation_html import generate_presentation_html, save_presentation_html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def generate_presentation_cli():
    """CLI entry point for presentation generation."""
    parser = argparse.ArgumentParser(description="Generate HTML presentations from JSON data")
    parser.add_argument("input_file", help="Path to JSON input file with presentation data")
    parser.add_argument("--output-file", help="Path to output HTML file (default: based on input filename)")
    parser.add_argument("--theme", choices=["professional_blue", "dark", "minimal"], 
                        help="Presentation theme (default: use theme from JSON or professional_blue)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Read the JSON input file
        with open(args.input_file, 'r', encoding='utf-8') as f:
            try:
                presentation_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {e}")
                return 1
        
        # Override theme if specified
        if args.theme:
            presentation_data["theme"] = args.theme
        
        # Determine output file path if not specified
        if not args.output_file:
            input_path = Path(args.input_file)
            output_path = input_path.with_suffix('.html')
            args.output_file = str(output_path)
        
        # Generate and save the HTML presentation
        output_path = save_presentation_html(presentation_data, args.output_file)
        
        print(f"\nPresentation generation complete:")
        print(f"- Generated presentation from: {os.path.basename(args.input_file)}")
        print(f"- Saved HTML to: {os.path.abspath(output_path)}")
        print(f"- Theme: {presentation_data.get('theme', 'professional_blue')}")
        print(f"- Number of slides: {len(presentation_data.get('slides', []))}")
        print("\nOpen the HTML file in any web browser to view the presentation.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating presentation: {e}", exc_info=True)
        return 1

def main():
    """Main entry point for CLI."""
    sys.exit(generate_presentation_cli())

if __name__ == "__main__":
    main()

"""
SVG generation utilities for presentation slides.

This module provides functions to generate simple SVG graphics
for use in presentations instead of relying on textual descriptions.
"""

import html
import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any


def generate_svg_for_slide(slide_type: str, slide_content: Dict[str, Any], width: int = 400, height: int = 300) -> str:
    """
    Generate an appropriate SVG graphic based on slide type and content.
    
    Args:
        slide_type: Type of slide ('title', 'content', 'closing', etc.)
        slide_content: Content of the slide
        width: Width of the SVG in pixels
        height: Height of the SVG in pixels
    
    Returns:
        str: SVG markup as a string
    """
    # Generate color palette based on slide content
    colors = generate_color_palette(slide_content)
    
    if slide_type == "title":
        return generate_title_svg(slide_content, colors, width, height)
    elif slide_type == "closing":
        return generate_closing_svg(slide_content, colors, width, height)
    else:  # content slide
        title = slide_content.get('title', '')
        
        # Generate different types of graphics based on the content
        if any(keyword in title.lower() for keyword in ['executive', 'summary', 'overview']):
            return generate_executive_summary_svg(slide_content, colors, width, height)
        elif any(keyword in title.lower() for keyword in ['analysis', 'data', 'metrics', 'statistics']):
            return generate_data_analysis_svg(slide_content, colors, width, height)
        elif any(keyword in title.lower() for keyword in ['strategy', 'plan', 'recommendation']):
            return generate_strategy_svg(slide_content, colors, width, height)
        else:
            return generate_generic_content_svg(slide_content, colors, width, height)


def generate_color_palette(content: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate a color palette based on the content.
    
    Args:
        content: Slide content dictionary
    
    Returns:
        Dict[str, str]: Dictionary of color values
    """
    # Default colors for professional_blue theme
    colors = {
        'primary': '#1a73e8',
        'secondary': '#4285f4',
        'accent': '#fbbc04',
        'background': '#f8f9fa',
        'text': '#202124',
        'light': '#e8eaed',
    }
    
    # Generate a consistent but semi-random accent color based on content
    if 'title' in content:
        # Create a hash from the title for consistency
        title_hash = hashlib.md5(content['title'].encode()).hexdigest()
        
        # Use the first 6 characters of the hash as a color
        # But ensure it's in a good range for visibility
        r = min(240, max(40, int(title_hash[0:2], 16)))
        g = min(240, max(40, int(title_hash[2:4], 16)))
        b = min(240, max(40, int(title_hash[4:6], 16)))
        
        # Override accent color
        colors['accent'] = f'#{r:02x}{g:02x}{b:02x}'
    
    return colors


def generate_title_svg(content: Dict[str, Any], colors: Dict[str, str], width: int, height: int) -> str:
    """Generate SVG for title slides."""
    # Create a modern abstract background with shapes
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{colors['primary']};stop-opacity:0.2" />
                <stop offset="100%" style="stop-color:{colors['secondary']};stop-opacity:0.1" />
            </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="{colors['background']}" />
        <rect x="0" y="0" width="{width}" height="{height}" fill="url(#grad1)" />
        
        <!-- Abstract shapes -->
        <circle cx="{width * 0.8}" cy="{height * 0.2}" r="{width * 0.15}" fill="{colors['primary']}" opacity="0.1" />
        <circle cx="{width * 0.7}" cy="{height * 0.3}" r="{width * 0.1}" fill="{colors['secondary']}" opacity="0.1" />
        <rect x="{width * 0.05}" y="{height * 0.7}" width="{width * 0.2}" height="{height * 0.2}" fill="{colors['accent']}" opacity="0.1" />
        
        <!-- Decorative line -->
        <line x1="{width * 0.1}" y1="{height * 0.6}" x2="{width * 0.9}" y2="{height * 0.6}" stroke="{colors['primary']}" stroke-width="2" opacity="0.3" />
    </svg>"""
    
    return svg


def generate_closing_svg(content: Dict[str, Any], colors: Dict[str, str], width: int, height: int) -> str:
    """Generate SVG for closing slides."""
    # Create a simple "thank you" graphic
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <rect width="100%" height="100%" fill="{colors['background']}" />
        
        <!-- Decorative circular pattern -->
        <circle cx="{width/2}" cy="{height/2}" r="{min(width, height) * 0.3}" fill="none" stroke="{colors['primary']}" stroke-width="2" opacity="0.7" />
        <circle cx="{width/2}" cy="{height/2}" r="{min(width, height) * 0.25}" fill="none" stroke="{colors['secondary']}" stroke-width="1.5" opacity="0.5" />
        <circle cx="{width/2}" cy="{height/2}" r="{min(width, height) * 0.2}" fill="none" stroke="{colors['accent']}" stroke-width="1" opacity="0.3" />
        
        <!-- Center point -->
        <circle cx="{width/2}" cy="{height/2}" r="5" fill="{colors['primary']}" />
    </svg>"""
    
    return svg


def generate_executive_summary_svg(content: Dict[str, Any], colors: Dict[str, str], width: int, height: int) -> str:
    """Generate SVG for executive summary slides."""
    # Create a business chart graphic
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <rect width="100%" height="100%" fill="{colors['background']}" />
        
        <!-- Background grid -->
        <g opacity="0.1">
            <!-- Horizontal lines -->
            <line x1="{width * 0.1}" y1="{height * 0.2}" x2="{width * 0.9}" y2="{height * 0.2}" stroke="{colors['text']}" />
            <line x1="{width * 0.1}" y1="{height * 0.4}" x2="{width * 0.9}" y2="{height * 0.4}" stroke="{colors['text']}" />
            <line x1="{width * 0.1}" y1="{height * 0.6}" x2="{width * 0.9}" y2="{height * 0.6}" stroke="{colors['text']}" />
            <line x1="{width * 0.1}" y1="{height * 0.8}" x2="{width * 0.9}" y2="{height * 0.8}" stroke="{colors['text']}" />
            
            <!-- Vertical lines -->
            <line x1="{width * 0.1}" y1="{height * 0.2}" x2="{width * 0.1}" y2="{height * 0.8}" stroke="{colors['text']}" />
            <line x1="{width * 0.3}" y1="{height * 0.2}" x2="{width * 0.3}" y2="{height * 0.8}" stroke="{colors['text']}" />
            <line x1="{width * 0.5}" y1="{height * 0.2}" x2="{width * 0.5}" y2="{height * 0.8}" stroke="{colors['text']}" />
            <line x1="{width * 0.7}" y1="{height * 0.2}" x2="{width * 0.7}" y2="{height * 0.8}" stroke="{colors['text']}" />
            <line x1="{width * 0.9}" y1="{height * 0.2}" x2="{width * 0.9}" y2="{height * 0.8}" stroke="{colors['text']}" />
        </g>
        
        <!-- Line chart -->
        <polyline points="{width * 0.1},{height * 0.7} 
                           {width * 0.3},{height * 0.5} 
                           {width * 0.5},{height * 0.6} 
                           {width * 0.7},{height * 0.35} 
                           {width * 0.9},{height * 0.3}" 
                  fill="none" stroke="{colors['primary']}" stroke-width="3" />
        
        <!-- Data points -->
        <circle cx="{width * 0.1}" cy="{height * 0.7}" r="5" fill="{colors['primary']}" />
        <circle cx="{width * 0.3}" cy="{height * 0.5}" r="5" fill="{colors['primary']}" />
        <circle cx="{width * 0.5}" cy="{height * 0.6}" r="5" fill="{colors['primary']}" />
        <circle cx="{width * 0.7}" cy="{height * 0.35}" r="5" fill="{colors['primary']}" />
        <circle cx="{width * 0.9}" cy="{height * 0.3}" r="5" fill="{colors['primary']}" />
        
        <!-- Bar chart in background -->
        <rect x="{width * 0.15}" y="{height * 0.6}" width="{width * 0.1}" height="{height * 0.2}" fill="{colors['secondary']}" opacity="0.3" />
        <rect x="{width * 0.35}" y="{height * 0.5}" width="{width * 0.1}" height="{height * 0.3}" fill="{colors['secondary']}" opacity="0.3" />
        <rect x="{width * 0.55}" y="{height * 0.45}" width="{width * 0.1}" height="{height * 0.35}" fill="{colors['secondary']}" opacity="0.3" />
        <rect x="{width * 0.75}" y="{height * 0.4}" width="{width * 0.1}" height="{height * 0.4}" fill="{colors['secondary']}" opacity="0.3" />
        
        <!-- Magnifying glass icon -->
        <circle cx="{width * 0.8}" cy="{height * 0.25}" r="{width * 0.06}" fill="none" stroke="{colors['accent']}" stroke-width="2" />
        <line x1="{width * 0.85}" y1="{height * 0.3}" x2="{width * 0.9}" y2="{height * 0.35}" stroke="{colors['accent']}" stroke-width="2" />
    </svg>"""
    
    return svg


def generate_data_analysis_svg(content: Dict[str, Any], colors: Dict[str, str], width: int, height: int) -> str:
    """Generate SVG for data analysis slides."""
    # Create a chart with data points
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <rect width="100%" height="100%" fill="{colors['background']}" />
        
        <!-- Coordinate system -->
        <line x1="{width * 0.1}" y1="{height * 0.1}" x2="{width * 0.1}" y2="{height * 0.9}" stroke="{colors['text']}" stroke-width="2" />
        <line x1="{width * 0.1}" y1="{height * 0.9}" x2="{width * 0.9}" y2="{height * 0.9}" stroke="{colors['text']}" stroke-width="2" />
        
        <!-- Scatter plot points -->
        <circle cx="{width * 0.2}" cy="{height * 0.7}" r="6" fill="{colors['primary']}" opacity="0.8" />
        <circle cx="{width * 0.3}" cy="{height * 0.5}" r="8" fill="{colors['primary']}" opacity="0.8" />
        <circle cx="{width * 0.4}" cy="{height * 0.6}" r="5" fill="{colors['primary']}" opacity="0.8" />
        <circle cx="{width * 0.5}" cy="{height * 0.3}" r="9" fill="{colors['primary']}" opacity="0.8" />
        <circle cx="{width * 0.6}" cy="{height * 0.4}" r="7" fill="{colors['primary']}" opacity="0.8" />
        <circle cx="{width * 0.7}" cy="{height * 0.2}" r="6" fill="{colors['primary']}" opacity="0.8" />
        <circle cx="{width * 0.8}" cy="{height * 0.35}" r="8" fill="{colors['primary']}" opacity="0.8" />
        
        <!-- Trend line -->
        <line x1="{width * 0.15}" y1="{height * 0.7}" x2="{width * 0.85}" y2="{height * 0.3}" stroke="{colors['accent']}" stroke-width="2" stroke-dasharray="5,5" />
        
        <!-- Axis markers -->
        <line x1="{width * 0.1}" y1="{height * 0.7}" x2="{width * 0.12}" y2="{height * 0.7}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.1}" y1="{height * 0.5}" x2="{width * 0.12}" y2="{height * 0.5}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.1}" y1="{height * 0.3}" x2="{width * 0.12}" y2="{height * 0.3}" stroke="{colors['text']}" stroke-width="1" />
        
        <line x1="{width * 0.3}" y1="{height * 0.9}" x2="{width * 0.3}" y2="{height * 0.92}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.5}" y1="{height * 0.9}" x2="{width * 0.5}" y2="{height * 0.92}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.7}" y1="{height * 0.9}" x2="{width * 0.7}" y2="{height * 0.92}" stroke="{colors['text']}" stroke-width="1" />
    </svg>"""
    
    return svg


def generate_strategy_svg(content: Dict[str, Any], colors: Dict[str, str], width: int, height: int) -> str:
    """Generate SVG for strategy slides."""
    # Create a diagram with connected elements
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <rect width="100%" height="100%" fill="{colors['background']}" />
        
        <!-- Central node -->
        <circle cx="{width/2}" cy="{height/2}" r="{min(width, height) * 0.15}" fill="{colors['primary']}" opacity="0.7" />
        
        <!-- Satellite nodes -->
        <circle cx="{width * 0.25}" cy="{height * 0.25}" r="{min(width, height) * 0.08}" fill="{colors['secondary']}" opacity="0.7" />
        <circle cx="{width * 0.75}" cy="{height * 0.25}" r="{min(width, height) * 0.08}" fill="{colors['secondary']}" opacity="0.7" />
        <circle cx="{width * 0.25}" cy="{height * 0.75}" r="{min(width, height) * 0.08}" fill="{colors['secondary']}" opacity="0.7" />
        <circle cx="{width * 0.75}" cy="{height * 0.75}" r="{min(width, height) * 0.08}" fill="{colors['secondary']}" opacity="0.7" />
        
        <!-- Connecting lines -->
        <line x1="{width/2}" y1="{height/2}" x2="{width * 0.25}" y2="{height * 0.25}" stroke="{colors['text']}" stroke-width="2" />
        <line x1="{width/2}" y1="{height/2}" x2="{width * 0.75}" y2="{height * 0.25}" stroke="{colors['text']}" stroke-width="2" />
        <line x1="{width/2}" y1="{height/2}" x2="{width * 0.25}" y2="{height * 0.75}" stroke="{colors['text']}" stroke-width="2" />
        <line x1="{width/2}" y1="{height/2}" x2="{width * 0.75}" y2="{height * 0.75}" stroke="{colors['text']}" stroke-width="2" />
        
        <!-- Arrow markers for direction -->
        <polygon points="{width * 0.25 + 10},{height * 0.25 + 10} {width * 0.25},{height * 0.25} {width * 0.25 + 15},{height * 0.25 + 5}" fill="{colors['text']}" />
        <polygon points="{width * 0.75 - 10},{height * 0.25 + 10} {width * 0.75},{height * 0.25} {width * 0.75 - 15},{height * 0.25 + 5}" fill="{colors['text']}" />
        <polygon points="{width * 0.25 + 10},{height * 0.75 - 10} {width * 0.25},{height * 0.75} {width * 0.25 + 15},{height * 0.75 - 5}" fill="{colors['text']}" />
        <polygon points="{width * 0.75 - 10},{height * 0.75 - 10} {width * 0.75},{height * 0.75} {width * 0.75 - 15},{height * 0.75 - 5}" fill="{colors['text']}" />
    </svg>"""
    
    return svg


def generate_generic_content_svg(content: Dict[str, Any], colors: Dict[str, str], width: int, height: int) -> str:
    """Generate SVG for generic content slides."""
    # Create a simple visual with abstract shapes
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <rect width="100%" height="100%" fill="{colors['background']}" />
        
        <!-- Decorative elements -->
        <circle cx="{width * 0.8}" cy="{height * 0.8}" r="{width * 0.15}" fill="{colors['primary']}" opacity="0.1" />
        <circle cx="{width * 0.65}" cy="{height * 0.85}" r="{width * 0.1}" fill="{colors['secondary']}" opacity="0.1" />
        
        <!-- Abstract document representation -->
        <rect x="{width * 0.2}" y="{height * 0.2}" width="{width * 0.4}" height="{height * 0.6}" fill="white" stroke="{colors['text']}" stroke-width="1" />
        
        <!-- Document lines -->
        <line x1="{width * 0.25}" y1="{height * 0.3}" x2="{width * 0.55}" y2="{height * 0.3}" stroke="{colors['primary']}" stroke-width="2" />
        <line x1="{width * 0.25}" y1="{height * 0.4}" x2="{width * 0.55}" y2="{height * 0.4}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.25}" y1="{height * 0.45}" x2="{width * 0.45}" y2="{height * 0.45}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.25}" y1="{height * 0.5}" x2="{width * 0.55}" y2="{height * 0.5}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.25}" y1="{height * 0.55}" x2="{width * 0.5}" y2="{height * 0.55}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.25}" y1="{height * 0.6}" x2="{width * 0.55}" y2="{height * 0.6}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.25}" y1="{height * 0.65}" x2="{width * 0.45}" y2="{height * 0.65}" stroke="{colors['text']}" stroke-width="1" />
        <line x1="{width * 0.25}" y1="{height * 0.7}" x2="{width * 0.55}" y2="{height * 0.7}" stroke="{colors['accent']}" stroke-width="2" />
        
        <!-- Decorative icon -->
        <circle cx="{width * 0.7}" cy="{height * 0.4}" r="{width * 0.06}" fill="{colors['secondary']}" opacity="0.7" />
        <polygon points="{width * 0.7},{height * 0.33} {width * 0.76},{height * 0.4} {width * 0.7},{height * 0.47} {width * 0.64},{height * 0.4}" fill="{colors['primary']}" />
    </svg>"""
    
    return svg

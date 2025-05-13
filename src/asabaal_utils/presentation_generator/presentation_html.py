"""
HTML presentation generator module.

This module converts structured JSON presentation data into interactive HTML presentations.
"""

import json
import os
import re
import html
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional, Any

def generate_presentation_html(presentation_data: Dict[str, Any]) -> str:
    """
    Generate an HTML presentation from structured JSON data.
    
    Args:
        presentation_data: Dictionary containing presentation structure with:
            - title: Presentation title
            - theme: Theme name (optional, defaults to "professional_blue")
            - slides: List of slide objects containing:
                - type: Type of slide (title, content, closing)
                - content: Content of the slide (depends on type)
                - image: Optional image information (for content slides)
    
    Returns:
        str: Complete HTML string for the presentation
    """
    # Extract presentation metadata
    title = presentation_data.get("title", "Presentation")
    theme = presentation_data.get("theme", "professional_blue")
    slides = presentation_data.get("slides", [])
    
    if not slides:
        return _create_error_html("No slides found in presentation data")
    
    # Define CSS styles based on theme
    styles = _get_theme_styles(theme)
    
    # Add general styles
    styles += _get_general_styles()
    
    # Generate HTML for each slide
    slides_html = []
    for index, slide in enumerate(slides):
        slide_type = slide.get("type", "content")
        slide_content = slide.get("content", {})
        slide_image = slide.get("image", {})
        
        if slide_type == "title":
            slides_html.append(_create_title_slide_html(index, slide_content))
        elif slide_type == "closing":
            slides_html.append(_create_closing_slide_html(index, slide_content))
        else:  # content slide
            slides_html.append(_create_content_slide_html(index, slide_content, slide_image))
    
    # JavaScript for navigation
    javascript = _get_navigation_javascript()
    
    # Combine everything into the final HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{html.escape(title)}</title>
        <style>
            {styles}
            /* Print styles for PDF export */
            @media print {{
                .controls, .slide:not(.active) {{
                    display: none !important;
                }}
                .slide.active {{
                    display: flex !important;
                    page-break-after: always;
                    height: 100vh;
                }}
                body, html {{
                    overflow: visible;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="presentation-container">
            <div class="slides-container">
                {"".join(slides_html)}
            </div>
            <div class="controls">
                <button id="prev-button">Previous</button>
                <span id="slide-counter" class="slide-number">1 / {len(slides)}</span>
                <button id="next-button">Next</button>
                <button onclick="exportToPDF()">Export to PDF</button>
                <button id="copy-html-button">Copy HTML</button>
            </div>
        </div>
        <script>
            {javascript}
            
            // Add export to PDF function
            function exportToPDF() {{
                window.print();
            }}
            
            // Add copy HTML function
            document.getElementById('copy-html-button').addEventListener('click', function() {{
                // Create a temporary textarea element to hold the HTML
                const textarea = document.createElement('textarea');
                textarea.value = document.documentElement.outerHTML;
                document.body.appendChild(textarea);
                textarea.select();
                
                try {{
                    // Execute copy command
                    document.execCommand('copy');
                    alert('HTML copied to clipboard! Now you can paste it into a text editor and save it as an .html file.');
                }} catch (err) {{
                    console.error('Failed to copy HTML: ', err);
                    alert('Failed to copy HTML to clipboard. Please try again or save manually.');
                }} finally {{
                    // Remove the temporary textarea
                    document.body.removeChild(textarea);
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html_content

def _get_theme_styles(theme: str) -> str:
    """Get the CSS styles for the specified theme."""
    if theme == "professional_blue":
        return """
        :root {
            --primary-color: #1a73e8;
            --secondary-color: #4285f4;
            --accent-color: #fbbc04;
            --text-color: #202124;
            --background-color: #ffffff;
            --slide-background: #f8f9fa;
            --header-color: #1a73e8;
        }
        """
    elif theme == "dark":
        return """
        :root {
            --primary-color: #4285f4;
            --secondary-color: #5e97f6;
            --accent-color: #fbbc04;
            --text-color: #e8eaed;
            --background-color: #202124;
            --slide-background: #2d2e30;
            --header-color: #8ab4f8;
        }
        """
    elif theme == "minimal":
        return """
        :root {
            --primary-color: #202124;
            --secondary-color: #5f6368;
            --accent-color: #ea4335;
            --text-color: #202124;
            --background-color: #ffffff;
            --slide-background: #ffffff;
            --header-color: #202124;
        }
        """
    else:  # Default to professional_blue
        return """
        :root {
            --primary-color: #1a73e8;
            --secondary-color: #4285f4;
            --accent-color: #fbbc04;
            --text-color: #202124;
            --background-color: #ffffff;
            --slide-background: #f8f9fa;
            --header-color: #1a73e8;
        }
        """

def _get_general_styles() -> str:
    """Get the general CSS styles for the presentation."""
    return """
    body, html {
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        color: var(--text-color);
        background-color: var(--background-color);
        height: 100%;
        overflow: hidden;
    }
    
    .presentation-container {
        width: 100%;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
    
    .slides-container {
        flex: 1;
        position: relative;
        overflow: hidden;
    }
    
    .slide {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: var(--slide-background);
        display: none;
        flex-direction: column;
        padding: 40px;
        box-sizing: border-box;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .slide.active {
        display: flex;
    }
    
    .slide-content {
        flex: 1;
        display: flex;
    }
    
    .slide-text {
        flex: 1;
        padding-right: 20px;
    }
    
    .slide-image {
        width: 40%;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: rgba(0, 0, 0, 0.03);
        border-radius: 8px;
        padding: 20px;
        box-sizing: border-box;
    }
    
    .slide-image-description {
        font-size: 14px;
        color: #666;
        font-style: italic;
        text-align: center;
        max-height: 100%;
        overflow-y: auto;
    }
    
    h1 {
        color: var(--header-color);
        font-size: 42px;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    h2 {
        color: var(--secondary-color);
        font-size: 28px;
        margin-bottom: 30px;
        font-weight: 400;
    }
    
    ul {
        list-style-type: none;
        padding-left: 0;
    }
    
    li {
        position: relative;
        padding-left: 30px;
        margin-bottom: 20px;
        font-size: 22px;
        line-height: 1.5;
    }
    
    li:before {
        content: '';
        position: absolute;
        left: 0;
        top: 10px;
        width: 10px;
        height: 10px;
        background-color: var(--primary-color);
        border-radius: 50%;
    }
    
    .controls {
        display: flex;
        justify-content: center;
        padding: 15px;
        background-color: var(--slide-background);
        border-top: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 8px 16px;
        margin: 0 5px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        transition: background-color 0.3s;
    }
    
    button:hover {
        background-color: var(--secondary-color);
    }
    
    button:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
    }
    
    .slide-number {
        padding: 8px 16px;
        font-size: 16px;
    }
    
    /* Title slide specific */
    .title-slide {
        text-align: center;
        justify-content: center;
    }
    
    .title-slide h1 {
        font-size: 56px;
        margin-bottom: 20px;
    }
    
    .title-slide h2 {
        font-size: 32px;
        margin-bottom: 0;
    }
    
    /* Closing slide specific */
    .closing-slide {
        text-align: center;
        justify-content: center;
    }
    
    /* Make content responsive */
    @media (max-width: 768px) {
        .slide-content {
            flex-direction: column;
        }
        .slide-text {
            padding-right: 0;
            padding-bottom: 20px;
        }
        .slide-image {
            width: 100%;
            max-height: 200px;
        }
        h1 {
            font-size: 32px;
        }
        h2 {
            font-size: 24px;
        }
        li {
            font-size: 18px;
        }
    }
    """

def _get_navigation_javascript() -> str:
    """Get the JavaScript for presentation navigation."""
    return """
    document.addEventListener('DOMContentLoaded', function() {
        const slides = document.querySelectorAll('.slide');
        const prevButton = document.getElementById('prev-button');
        const nextButton = document.getElementById('next-button');
        const slideCounter = document.getElementById('slide-counter');
        let currentSlide = 0;
        
        // Initialize
        updateSlideVisibility();
        
        // Event listeners
        prevButton.addEventListener('click', showPreviousSlide);
        nextButton.addEventListener('click', showNextSlide);
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft') {
                showPreviousSlide();
            } else if (e.key === 'ArrowRight') {
                showNextSlide();
            }
        });
        
        function showPreviousSlide() {
            if (currentSlide > 0) {
                currentSlide--;
                updateSlideVisibility();
            }
        }
        
        function showNextSlide() {
            if (currentSlide < slides.length - 1) {
                currentSlide++;
                updateSlideVisibility();
            }
        }
        
        function updateSlideVisibility() {
            // Hide all slides
            slides.forEach(slide => {
                slide.classList.remove('active');
            });
            
            // Show current slide
            slides[currentSlide].classList.add('active');
            
            // Update counter
            slideCounter.textContent = `${currentSlide + 1} / ${slides.length}`;
            
            // Update button states
            prevButton.disabled = currentSlide === 0;
            nextButton.disabled = currentSlide === slides.length - 1;
        }
    });
    """

def _create_title_slide_html(index: int, content: Dict[str, str]) -> str:
    """Create HTML for a title slide."""
    title = content.get('title', '')
    subtitle = content.get('subtitle', '')
    return f"""
    <div id="slide-{index}" class="slide title-slide">
        <h1>{html.escape(title)}</h1>
        <h2>{html.escape(subtitle)}</h2>
    </div>
    """

def _create_closing_slide_html(index: int, content: Dict[str, str]) -> str:
    """Create HTML for a closing slide."""
    title = content.get('title', '')
    subtitle = content.get('subtitle', '')
    return f"""
    <div id="slide-{index}" class="slide closing-slide">
        <h1>{html.escape(title)}</h1>
        <h2>{html.escape(subtitle)}</h2>
    </div>
    """

def _create_content_slide_html(index: int, content: Dict[str, Any], image: Dict[str, str]) -> str:
    """Create HTML for a content slide."""
    title = content.get('title', '')
    bullets = content.get('bullets', [])
    bullets_html = ""
    
    if bullets:
        bullets_html = "<ul>"
        for bullet in bullets:
            # Enable bold markdown in bullets
            bullet_text = html.escape(bullet)
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bullet_text)
            bullets_html += f"<li>{bullet_text}</li>"
        bullets_html += "</ul>"
    
    # Process image if available
    image_html = ""
    if image:
        image_type = image.get('type', '')
        if image_type == 'description':
            description = html.escape(image.get('description', ''))
            image_html = f"""
            <div class="slide-image">
                <div class="slide-image-description">{description}</div>
            </div>
            """
    
    return f"""
    <div id="slide-{index}" class="slide">
        <h1>{html.escape(title)}</h1>
        <div class="slide-content">
            <div class="slide-text">
                {bullets_html}
            </div>
            {image_html}
        </div>
    </div>
    """

def _create_error_html(error_message: str) -> str:
    """Create a simple HTML page with an error message."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }}
            .error-box {{
                background-color: #ffebee;
                border-left: 4px solid #f44336;
                padding: 20px;
                margin: 20px 0;
            }}
            h1 {{
                color: #d32f2f;
            }}
        </style>
    </head>
    <body>
        <div class="error-box">
            <h1>Error</h1>
            <p>{html.escape(error_message)}</p>
        </div>
    </body>
    </html>
    """

def save_presentation_html(presentation_data: Dict[str, Any], output_path: str) -> str:
    """
    Generate an HTML presentation and save it to a file.
    
    Args:
        presentation_data: Dictionary containing presentation structure
        output_path: Path to save the HTML file
    
    Returns:
        str: Path to the saved HTML file
    """
    # Generate the HTML content
    html_content = generate_presentation_html(presentation_data)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path

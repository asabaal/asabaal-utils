#!/usr/bin/env python3
"""
Comprehensive Text Rendering Debugging Tool
This creates a visual report showing every step of the text rendering pipeline
to identify where text cutoff occurs.
"""

import numpy as np
import cv2
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import json

# Set dark theme for matplotlib
plt.style.use('dark_background')

# Import our components
from src.asabaal_utils.video_processing.lyric_video.text.renderer import TextRenderer, TextStyle, AnimationConfig
from src.asabaal_utils.video_processing.lyric_video.text.fonts import FontManager
from src.asabaal_utils.video_processing.lyric_video.compositor import VideoCompositor, CompositeLayer
from src.asabaal_utils.video_processing.lyric_video.lyrics.parser import LyricWord

class TextRenderingDebugger:
    """Debug text rendering pipeline with visual output."""
    
    def __init__(self, resolution=(1920, 1080)):
        self.resolution = resolution
        self.renderer = TextRenderer(resolution)
        self.compositor = VideoCompositor(resolution, 30.0)
        self.font_manager = FontManager()
        self.debug_output_dir = Path("text_debug_output")
        self.debug_output_dir.mkdir(exist_ok=True)
        
        # Debug data collection
        self.debug_data = {
            "timestamp": datetime.now().isoformat(),
            "resolution": resolution,
            "steps": []
        }
        
    def create_debug_report(self):
        """Create comprehensive debugging report with visualizations."""
        print("🔍 Starting Text Rendering Debug Analysis...")
        print("=" * 60)
        
        # Test text samples
        test_texts = [
            "Short text",
            "Medium length text with more words",
            "Very long text that might extend beyond the screen width and cause clipping issues",
            "Text with g j p q y letters that extend below baseline"
        ]
        
        # Test different styles
        test_styles = [
            TextStyle(font_size=48, vertical_position="top"),
            TextStyle(font_size=72, vertical_position="center"),
            TextStyle(font_size=96, vertical_position="bottom"),
            TextStyle(font_size=120, vertical_position="center", glow_radius=20),
        ]
        
        # Create debug visualizations for each combination
        for i, text in enumerate(test_texts):
            for j, style in enumerate(test_styles):
                self.debug_single_render(text, style, f"test_{i}_{j}")
        
        # Create summary visualization
        self.create_summary_visualization()
        
        # Save debug data
        with open(self.debug_output_dir / "debug_data.json", "w") as f:
            json.dump(self.debug_data, f, indent=2)
            
        print("\n✅ Debug report complete!")
        print(f"📁 Output saved to: {self.debug_output_dir}")
        
    def debug_single_render(self, text, style, test_id):
        """Debug a single text rendering with detailed visualization."""
        print(f"\n🔧 Debugging: '{text[:30]}...' with size {style.font_size}")
        
        debug_step = {
            "test_id": test_id,
            "text": text,
            "font_size": style.font_size,
            "position": style.vertical_position,
            "measurements": {},
            "issues": []
        }
        
        # Step 1: Actually render the text using our renderer
        try:
            # Create fake words for rendering
            words = [LyricWord(word, i*0.5, (i+1)*0.5) for i, word in enumerate(text.split())]
            
            # Render using our actual renderer
            rendered_frame = self.renderer.render_lyric_line(
                words=words,
                current_time=0.5,  # Middle of animation
                style=style,
                animation_config=self.renderer.animation_presets['subtle'],
                line_start=0.0,
                line_end=len(words) * 0.5
            )
            
            # Get actual text bounds from rendered image
            alpha_channel = rendered_frame[:, :, 3]
            rows_with_text = np.where(alpha_channel.any(axis=1))[0]
            cols_with_text = np.where(alpha_channel.any(axis=0))[0]
            
            if len(rows_with_text) > 0 and len(cols_with_text) > 0:
                actual_top = rows_with_text[0]
                actual_bottom = rows_with_text[-1]
                actual_left = cols_with_text[0]
                actual_right = cols_with_text[-1]
                actual_height = actual_bottom - actual_top + 1
                actual_width = actual_right - actual_left + 1
            else:
                actual_top = actual_bottom = actual_left = actual_right = 0
                actual_height = actual_width = 0
                
        except Exception as e:
            print(f"  ❌ Rendering error: {e}")
            rendered_frame = np.zeros((self.resolution[1], self.resolution[0], 4), dtype=np.uint8)
            actual_top = actual_bottom = actual_left = actual_right = 0
            actual_height = actual_width = 0
        
        # Step 2: Font measurements for comparison
        font = self.font_manager.get_font(style.font_family, style.font_size)
        text_surface = self.font_manager.render_text(text, font, style.color, style.stroke_width, style.stroke_color)
        text_h, text_w = text_surface.shape[:2]
        
        debug_step["measurements"]["text_dimensions"] = {"width": int(text_w), "height": int(text_h)}
        debug_step["measurements"]["actual_bounds"] = {
            "top": int(actual_top), "bottom": int(actual_bottom),
            "left": int(actual_left), "right": int(actual_right),
            "width": int(actual_width), "height": int(actual_height)
        }
        print(f"  📏 Font dimensions: {text_w}x{text_h}")
        print(f"  📏 Actual rendered bounds: ({actual_left},{actual_top}) to ({actual_right},{actual_bottom})")
        
        # Step 3: Calculate expected position using actual renderer logic
        y_pos = self.renderer._calculate_vertical_position(text_h, style, 0.0, None)
        
        # Use the same horizontal positioning logic as the actual renderer
        CANVAS_PADDING = 200
        SAFE_LEFT_MARGIN = 50
        SAFE_RIGHT_MARGIN = 50
        available_width = self.resolution[0] - SAFE_LEFT_MARGIN - SAFE_RIGHT_MARGIN
        
        if text_w <= available_width:
            # Text fits: center it normally
            x_pos = (self.resolution[0] - text_w) // 2 + CANVAS_PADDING
        else:
            # Text too wide: start from safe left margin
            x_pos = SAFE_LEFT_MARGIN + CANVAS_PADDING
        
        debug_step["measurements"]["calculated_position"] = {"x": int(x_pos), "y": int(y_pos)}
        print(f"  📍 Calculated position: ({x_pos}, {y_pos})")
        
        # Step 4: Check bounds
        bottom_y = y_pos + text_h
        if actual_bottom >= self.resolution[1] - 1:
            debug_step["issues"].append(f"Text ACTUALLY cut off at bottom: {actual_bottom} >= {self.resolution[1]-1}")
            print(f"  ⚠️  TEXT IS CUT OFF! Bottom pixel at {actual_bottom}")
        elif bottom_y > self.resolution[1]:
            debug_step["issues"].append(f"Text WOULD extend below screen: {bottom_y} > {self.resolution[1]}")
            print(f"  ⚠️  TEXT WOULD EXTEND BELOW SCREEN: {bottom_y} > {self.resolution[1]}")
        
        if y_pos < 0:
            debug_step["issues"].append(f"Text extends above screen: {y_pos} < 0")
            print(f"  ⚠️  TEXT EXTENDS ABOVE SCREEN: {y_pos} < 0")
            
        # Step 5: Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12), facecolor='#1a1a1a')
        fig.suptitle(f"Debug: {test_id} - '{text[:30]}...'", fontsize=16, color='white')
        
        # Subplot 1: Screen layout with actual render overlay
        ax1 = axes[0, 0]
        ax1.set_title("Screen Layout & Actual Rendered Text", color='white')
        ax1.set_facecolor('#2a2a2a')
        
        # Show the actual rendered frame as background
        ax1.imshow(rendered_frame, extent=[0, self.resolution[0], self.resolution[1], 0], alpha=0.8)
        
        # Draw screen boundary
        screen_rect = patches.Rectangle((0, 0), self.resolution[0], self.resolution[1], 
                                      linewidth=3, edgecolor='white', facecolor='none')
        ax1.add_patch(screen_rect)
        
        # Draw safe zones
        safe_top = 100
        safe_bottom = 200
        safe_zone = patches.Rectangle((0, safe_top), self.resolution[0], 
                                    self.resolution[1] - safe_top - safe_bottom,
                                    linewidth=2, edgecolor='#00ff00', facecolor='none', linestyle='--')
        ax1.add_patch(safe_zone)
        ax1.text(50, safe_top - 10, "Safe Zone Top (100px)", fontsize=10, color='#00ff00')
        ax1.text(50, self.resolution[1] - safe_bottom + 20, "Safe Zone Bottom (200px)", fontsize=10, color='#00ff00')
        
        # Draw expected text rectangle
        text_color = '#ff4444' if debug_step["issues"] else '#4444ff'
        expected_rect = patches.Rectangle((x_pos, y_pos), text_w, text_h,
                                        linewidth=2, edgecolor=text_color, facecolor='none', linestyle=':')
        ax1.add_patch(expected_rect)
        ax1.text(x_pos, y_pos - 10, "Expected", fontsize=9, color=text_color)
        
        # Draw actual text bounds if found
        if actual_width > 0:
            actual_rect = patches.Rectangle((actual_left, actual_top), actual_width, actual_height,
                                          linewidth=3, edgecolor='#ffff00', facecolor='none')
            ax1.add_patch(actual_rect)
            ax1.text(actual_left, actual_top - 10, "Actual", fontsize=9, color='#ffff00')
        
        # Draw important lines
        ax1.axhline(y=self.resolution[1], color='red', linewidth=3, label='Screen Bottom')
        ax1.axhline(y=actual_bottom, color='yellow', linewidth=2, linestyle='--', label='Actual Text Bottom')
        
        ax1.set_xlim(-50, self.resolution[0] + 50)
        ax1.set_ylim(self.resolution[1] + 50, -50)
        ax1.set_xlabel("X Position (pixels)", color='white')
        ax1.set_ylabel("Y Position (pixels)", color='white')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.2)
        
        # Subplot 2: Zoomed view of bottom area
        ax2 = axes[0, 1]
        ax2.set_title("Zoomed: Bottom Area (Critical Region)", color='white')
        ax2.set_facecolor('#2a2a2a')
        
        # Show zoomed rendered area
        zoom_top = max(0, self.resolution[1] - 400)
        zoom_region = rendered_frame[zoom_top:, :]
        ax2.imshow(zoom_region, extent=[0, self.resolution[0], self.resolution[1], zoom_top], aspect='auto')
        
        # Draw screen bottom line prominently
        ax2.axhline(y=self.resolution[1], color='red', linewidth=4, label='Screen Edge (1080)')
        ax2.axhline(y=self.resolution[1] - safe_bottom, color='#00ff00', linewidth=2, linestyle='--', label='Safe Zone')
        
        if actual_bottom > 0:
            ax2.axhline(y=actual_bottom, color='yellow', linewidth=3, label=f'Text Bottom ({actual_bottom})')
            
            # Show overflow amount if any
            if actual_bottom >= self.resolution[1] - 1:
                overflow = actual_bottom - (self.resolution[1] - 1)
                ax2.text(self.resolution[0]//2, self.resolution[1] - 50, 
                        f"WARNING: CUTOFF DETECTED! Overflow: {overflow}px", 
                        fontsize=14, color='red', ha='center', 
                        bbox=dict(boxstyle="round,pad=0.5", facecolor="black", alpha=0.8))
        
        ax2.set_xlim(0, self.resolution[0])
        ax2.set_ylim(self.resolution[1] + 20, zoom_top)
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.2)
        
        # Subplot 3: Detailed measurements
        ax3 = axes[1, 0]
        ax3.set_title("Measurements & Analysis", color='white')
        ax3.set_facecolor('#2a2a2a')
        ax3.axis('off')
        
        measurements_text = f"""Text: '{text[:40]}...'
Font Size: {style.font_size}px
Position Mode: {style.vertical_position}

EXPECTED (from font metrics):
  Dimensions: {text_w} x {text_h} pixels
  Position: ({x_pos}, {y_pos})
  Bottom would be: {bottom_y}

ACTUAL (from rendered frame):
  Bounds: ({actual_left},{actual_top}) to ({actual_right},{actual_bottom})
  Dimensions: {actual_width} x {actual_height} pixels
  Bottom pixel: {actual_bottom}
  
SCREEN:
  Height: {self.resolution[1]}
  Safe bottom: {self.resolution[1] - safe_bottom}
  
MARGIN:
  Expected: {self.resolution[1] - bottom_y}px
  Actual: {self.resolution[1] - actual_bottom}px if actual_bottom > 0 else 'N/A'

STATUS: {'WARNING: CUT OFF!' if actual_bottom >= self.resolution[1] - 1 else 'OK'}"""
        
        ax3.text(0.05, 0.95, measurements_text, fontsize=11, verticalalignment='top',
                fontfamily='monospace', transform=ax3.transAxes, color='white',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#333333", alpha=0.8))
        
        # Subplot 4: Actual text rendering close-up
        ax4 = axes[1, 1]
        ax4.set_title("Text Rendering Close-up", color='white')
        ax4.set_facecolor('#2a2a2a')
        
        # Show just the text area with some padding
        if actual_width > 0 and actual_height > 0:
            padding = 50
            y1 = max(0, actual_top - padding)
            y2 = min(self.resolution[1], actual_bottom + padding)
            x1 = max(0, actual_left - padding)
            x2 = min(self.resolution[0], actual_right + padding)
            
            text_region = rendered_frame[y1:y2, x1:x2]
            ax4.imshow(text_region, extent=[x1, x2, y2, y1])
            
            # Draw bounds
            ax4.axhline(y=actual_top, color='yellow', linewidth=1, linestyle='--', alpha=0.5)
            ax4.axhline(y=actual_bottom, color='yellow', linewidth=2, label='Text Bottom')
            ax4.axvline(x=actual_left, color='yellow', linewidth=1, linestyle='--', alpha=0.5)
            ax4.axvline(x=actual_right, color='yellow', linewidth=1, linestyle='--', alpha=0.5)
            
            # Show screen bottom if in view
            if self.resolution[1] >= y1 and self.resolution[1] <= y2:
                ax4.axhline(y=self.resolution[1], color='red', linewidth=3, label='Screen Bottom')
            
            ax4.set_xlim(x1, x2)
            ax4.set_ylim(y2, y1)
            ax4.legend()
        else:
            ax4.text(0.5, 0.5, "No text detected in render", 
                    transform=ax4.transAxes, ha='center', va='center',
                    fontsize=14, color='red')
        
        # Adjust layout and save
        plt.tight_layout()
        fig.savefig(self.debug_output_dir / f"{test_id}_debug.png", dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close(fig)
        
        # Add to debug data
        self.debug_data["steps"].append(debug_step)
        
    def create_summary_visualization(self):
        """Create a summary visualization of all tests."""
        fig, ax = plt.subplots(figsize=(14, 10))
        fig.suptitle("Text Rendering Debug Summary", fontsize=18, weight='bold')
        
        # Collect all issues
        all_issues = []
        for step in self.debug_data["steps"]:
            if step["issues"]:
                all_issues.append({
                    "test_id": step["test_id"],
                    "text": step["text"][:30] + "...",
                    "font_size": step["font_size"],
                    "issues": step["issues"]
                })
        
        # Create summary table
        if all_issues:
            ax.text(0.5, 0.9, f"WARNING: Found {len(all_issues)} text configurations with issues:",
                   fontsize=14, weight='bold', ha='center', transform=ax.transAxes, color='orange')
            
            table_text = "Test ID | Font Size | Issue\n" + "-"*60 + "\n"
            for issue in all_issues:
                table_text += f"{issue['test_id']} | {issue['font_size']}px | {issue['issues'][0]}\n"
            
            ax.text(0.1, 0.7, table_text, fontsize=10, fontfamily='monospace',
                   verticalalignment='top', transform=ax.transAxes, color='white')
        else:
            ax.text(0.5, 0.5, "SUCCESS: No text clipping issues detected!",
                   fontsize=20, weight='bold', ha='center', va='center',
                   color='green', transform=ax.transAxes)
        
        # Add recommendations
        recommendations = """
RECOMMENDATIONS:
1. Check if text effects (glow, shadow) extend beyond calculated height
2. Verify canvas padding is working correctly  
3. Check compositor clipping logic
4. Test with actual SRT file to see word-by-word rendering
5. Enable debug logging: export LOG_LEVEL=DEBUG
"""
        ax.text(0.1, 0.3, recommendations, fontsize=11, fontfamily='monospace',
               verticalalignment='top', transform=ax.transAxes,
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow"))
        
        ax.axis('off')
        fig.tight_layout()
        fig.savefig(self.debug_output_dir / "summary.png", dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Create HTML report
        self.create_html_report()
        
    def create_html_report(self):
        """Create an interactive HTML report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Text Rendering Debug Report</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: linear-gradient(145deg, #2a2a2a, #1f1f1f); 
            padding: 30px; 
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
            border-radius: 15px;
            border: 1px solid #444;
        }}
        h1 {{ 
            color: #00ff88; 
            border-bottom: 3px solid #00ff88; 
            padding-bottom: 15px; 
            text-shadow: 0 0 10px rgba(0,255,136,0.3);
            font-size: 2.5em;
            margin-bottom: 30px;
        }}
        h2 {{ 
            color: #88ddff; 
            margin-top: 40px;
            font-size: 1.8em;
            text-shadow: 0 0 5px rgba(136,221,255,0.3);
        }}
        h3 {{
            color: #ffaa44;
            margin-top: 25px;
            font-size: 1.3em;
        }}
        .test-case {{ 
            margin: 25px 0; 
            padding: 20px; 
            border: 1px solid #555; 
            border-radius: 10px; 
            background: linear-gradient(145deg, #333, #2a2a2a);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        .issue {{ 
            background: linear-gradient(145deg, #3a1f1f, #2a1515); 
            border-left: 5px solid #ff4444; 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 5px;
            color: #ffcccc;
        }}
        .success {{ 
            background: linear-gradient(145deg, #1f3a1f, #15251a); 
            border-left: 5px solid #44ff44; 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 5px;
            color: #ccffcc;
        }}
        .code {{ 
            background: #1a1a1a; 
            padding: 15px; 
            font-family: 'Consolas', 'Monaco', monospace; 
            border-radius: 8px; 
            overflow-x: auto; 
            border: 1px solid #444;
            color: #88ff88;
            font-size: 0.9em;
        }}
        img {{ 
            max-width: 100%; 
            height: auto; 
            margin: 15px 0; 
            border: 2px solid #555; 
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}
        .metrics {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px; 
            margin: 20px 0;
        }}
        .metric {{ 
            background: linear-gradient(145deg, #2a4a6a, #1f3a5a); 
            padding: 15px; 
            border-radius: 8px; 
            text-align: center; 
            border: 1px solid #4a6a8a;
            color: #ccddff;
        }}
        .metric strong {{
            color: #88ddff;
            font-size: 1.1em;
        }}
        .recommendation {{ 
            background: linear-gradient(145deg, #4a3a1a, #3a2a0f); 
            border: 1px solid #ffaa44; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 25px 0;
            color: #ffddaa;
        }}
        .status-good {{ color: #44ff44; font-weight: bold; }}
        .status-bad {{ color: #ff4444; font-weight: bold; }}
        .highlight {{ color: #ffff44; font-weight: bold; }}
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{ width: 12px; }}
        ::-webkit-scrollbar-track {{ background: #1a1a1a; }}
        ::-webkit-scrollbar-thumb {{ background: #444; border-radius: 6px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Text Rendering Debug Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Resolution: {self.resolution[0]} x {self.resolution[1]}</p>
        
        <h2>Summary</h2>
        <img src="summary.png" alt="Summary">
        
        <h2>Test Cases</h2>
"""
        
        # Add each test case
        for step in self.debug_data["steps"]:
            status_class = "issue" if step["issues"] else "success"
            status_icon = "⚠️" if step["issues"] else "✅"
            
            html_content += f"""
        <div class="test-case">
            <h3>{status_icon} Test: {step['test_id']}</h3>
            <div class="metrics">
                <div class="metric">
                    <strong>Font Size</strong><br>{step['font_size']}px
                </div>
                <div class="metric">
                    <strong>Text Width</strong><br>{step['measurements']['text_dimensions']['width']}px
                </div>
                <div class="metric">
                    <strong>Text Height</strong><br>{step['measurements']['text_dimensions']['height']}px
                </div>
                <div class="metric">
                    <strong>Y Position</strong><br>{step['measurements']['calculated_position']['y']}px
                </div>
            </div>
            <div class="{status_class}">
                {step['issues'][0] if step['issues'] else 'No issues detected - text fits within screen bounds'}
            </div>
            <img src="{step['test_id']}_debug.png" alt="{step['test_id']}">
        </div>
"""
        
        html_content += """
        <h2>Debugging Code</h2>
        <div class="code">
# Key functions to investigate:
# 1. TextRenderer._calculate_vertical_position()
# 2. TextRenderer.render_lyric_line() 
# 3. TextRenderer._composite_image()
# 4. VideoCompositor._blend_layer()

# Enable detailed logging:
import logging
logging.basicConfig(level=logging.DEBUG)

# Test specific position:
renderer = TextRenderer((1920, 1080))
style = TextStyle(font_size=72, vertical_position="center")
y_pos = renderer._calculate_vertical_position(100, style, 0.0, None)
print(f"Calculated Y position: {y_pos}")
        </div>
        
        <div class="recommendation">
            <h3>🎯 Next Steps</h3>
            <ol>
                <li>Check if the issue happens with specific fonts or all fonts</li>
                <li>Test with different video resolutions (720p, 1080p, 4K)</li>
                <li>Add logging to track exact pixel positions during rendering</li>
                <li>Verify that video encoding isn't cropping the output</li>
                <li>Test with transparent background vs. video background</li>
            </ol>
        </div>
    </div>
</body>
</html>
"""
        
        with open(self.debug_output_dir / "debug_report.html", "w") as f:
            f.write(html_content)
        
        print(f"\n📊 Interactive HTML report: {self.debug_output_dir / 'debug_report.html'}")


if __name__ == "__main__":
    # Run the debugger
    debugger = TextRenderingDebugger()
    debugger.create_debug_report()
    
    print("\n🔧 Additional debugging steps:")
    print("1. Run with debug logging: LOG_LEVEL=DEBUG create-lyric-video ...")
    print("2. Test with a simple 1-line SRT file")
    print("3. Generate frames without video encoding to isolate the issue")
    print("4. Check if specific fonts or effects cause the cutoff")
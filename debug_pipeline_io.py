#!/usr/bin/env python3
"""
Text Rendering Pipeline Input/Output Debugging Tool
Shows exactly what goes in and out of each stage to identify text cutoff.
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
from src.asabaal_utils.video_processing.lyric_video.lyrics.parser import LyricWord

class TextPipelineDebugger:
    """Debug each stage of the text rendering pipeline with input/output visualization."""
    
    def __init__(self, resolution=(1920, 1080)):
        self.resolution = resolution
        self.renderer = TextRenderer(resolution)
        self.font_manager = FontManager()
        self.debug_output_dir = Path("pipeline_debug_output")
        self.debug_output_dir.mkdir(exist_ok=True)
        
    def debug_complete_pipeline(self, text="Text with descenders: gypsy jungle", font_size=120):
        """Debug the complete text rendering pipeline step by step."""
        print("🔍 DEBUGGING COMPLETE TEXT RENDERING PIPELINE")
        print("=" * 80)
        
        # Create style
        style = TextStyle(font_size=font_size, vertical_position="center")
        
        # Step 1: INPUT ANALYSIS
        print("\n📥 STEP 1: INPUT ANALYSIS")
        print(f"  Input text: '{text}'")
        print(f"  Font size: {font_size}px")
        print(f"  Vertical position: {style.vertical_position}")
        print(f"  Target resolution: {self.resolution}")
        
        input_data = {
            "text": text,
            "font_size": font_size,
            "resolution": self.resolution,
            "style": style
        }
        
        # Step 2: FONT METRICS CALCULATION
        print("\n📏 STEP 2: FONT METRICS CALCULATION")
        font = self.font_manager.get_font(style.font_family, style.font_size)
        raw_text_surface = self.font_manager.render_text(text, font, style.color, style.stroke_width, style.stroke_color)
        text_h, text_w = raw_text_surface.shape[:2]
        
        print(f"  INPUT: Font '{style.font_family}', size {style.font_size}px")
        print(f"  OUTPUT: Text surface {text_w}x{text_h} pixels")
        
        font_metrics = {
            "width": text_w,
            "height": text_h,
            "surface_shape": raw_text_surface.shape
        }
        
        # Step 3: POSITION CALCULATION
        print("\n📍 STEP 3: POSITION CALCULATION")
        
        # Use actual renderer logic
        y_pos = self.renderer._calculate_vertical_position(text_h, style, 0.0, None)
        
        # Horizontal position calculation (from renderer.py lines 262-283)
        CANVAS_PADDING = 200
        SAFE_LEFT_MARGIN = 50
        SAFE_RIGHT_MARGIN = 50
        available_width = self.resolution[0] - SAFE_LEFT_MARGIN - SAFE_RIGHT_MARGIN
        
        if text_w <= available_width:
            x_pos = (self.resolution[0] - text_w) // 2 + CANVAS_PADDING
        else:
            x_pos = SAFE_LEFT_MARGIN + CANVAS_PADDING
            
        print(f"  INPUT: Text dimensions {text_w}x{text_h}, screen {self.resolution}")
        print(f"  CALCULATION: Safe zones - left:{SAFE_LEFT_MARGIN}, right:{SAFE_RIGHT_MARGIN}")
        print(f"  CALCULATION: Available width: {available_width}px")
        print(f"  CALCULATION: Canvas padding: {CANVAS_PADDING}px")
        print(f"  OUTPUT: Position ({x_pos}, {y_pos}) in padded canvas coordinates")
        
        position_data = {
            "x_pos": x_pos,
            "y_pos": y_pos,
            "canvas_padding": CANVAS_PADDING,
            "safe_margins": {"left": SAFE_LEFT_MARGIN, "right": SAFE_RIGHT_MARGIN},
            "available_width": available_width
        }
        
        # Step 4: CANVAS CREATION
        print("\n🖼️  STEP 4: CANVAS CREATION")
        canvas_height = self.resolution[1] + CANVAS_PADDING * 2
        canvas_width = self.resolution[0] + CANVAS_PADDING * 2
        canvas = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)
        
        print(f"  INPUT: Screen resolution {self.resolution}")
        print(f"  CALCULATION: Add padding {CANVAS_PADDING}px on all sides")
        print(f"  OUTPUT: Canvas {canvas_width}x{canvas_height} pixels")
        
        canvas_data = {
            "canvas_size": (canvas_width, canvas_height),
            "screen_size": self.resolution,
            "padding": CANVAS_PADDING
        }
        
        # Step 5: TEXT COMPOSITING
        print("\n🎨 STEP 5: TEXT COMPOSITING")
        
        # Create fake words for testing
        words = [LyricWord(word, i*0.5, (i+1)*0.5) for i, word in enumerate(text.split())]
        
        print(f"  INPUT: Words: {[w.text for w in words]}")
        print(f"  INPUT: Canvas position ({x_pos}, {y_pos})")
        print(f"  INPUT: Canvas size {canvas.shape}")
        
        # Manually composite the text onto canvas (simplified version of render_lyric_line)
        try:
            # Simple compositing - just place the raw text surface
            h, w = raw_text_surface.shape[:2]
            
            # Check bounds before compositing
            canvas_h, canvas_w = canvas.shape[:2]
            if (y_pos + h <= canvas_h and x_pos + w <= canvas_w and 
                y_pos >= 0 and x_pos >= 0):
                
                # Composite text onto canvas
                canvas[y_pos:y_pos+h, x_pos:x_pos+w] = raw_text_surface
                composite_success = True
                print(f"  COMPOSITING: SUCCESS - Text placed at ({x_pos}, {y_pos})")
            else:
                composite_success = False
                print(f"  COMPOSITING: FAILED - Text would extend outside canvas")
                print(f"    Text bounds: ({x_pos}, {y_pos}) to ({x_pos+w}, {y_pos+h})")
                print(f"    Canvas bounds: (0, 0) to ({canvas_w}, {canvas_h})")
                
        except Exception as e:
            composite_success = False
            print(f"  COMPOSITING: ERROR - {e}")
        
        composite_data = {
            "success": composite_success,
            "text_bounds": {"x": x_pos, "y": y_pos, "w": w, "h": h},
            "canvas_bounds": {"w": canvas_w, "h": canvas_h}
        }
        
        # Step 6: CANVAS CROPPING
        print("\n✂️  STEP 6: CANVAS CROPPING")
        
        print(f"  INPUT: Canvas {canvas.shape} with padding {CANVAS_PADDING}")
        print(f"  CALCULATION: Crop to [{CANVAS_PADDING}:{CANVAS_PADDING + self.resolution[1]}, {CANVAS_PADDING}:{CANVAS_PADDING + self.resolution[0]}]")
        
        # Crop canvas back to original resolution
        final_canvas = canvas[CANVAS_PADDING:CANVAS_PADDING + self.resolution[1], 
                             CANVAS_PADDING:CANVAS_PADDING + self.resolution[0]]
        
        print(f"  OUTPUT: Final image {final_canvas.shape}")
        
        # Calculate where text appears in final coordinates
        final_x = x_pos - CANVAS_PADDING
        final_y = y_pos - CANVAS_PADDING
        final_bottom = final_y + h
        final_right = final_x + w
        
        print(f"  COORDINATE TRANSLATION: ({x_pos}, {y_pos}) → ({final_x}, {final_y})")
        print(f"  FINAL TEXT BOUNDS: ({final_x}, {final_y}) to ({final_right}, {final_bottom})")
        
        crop_data = {
            "final_position": {"x": final_x, "y": final_y},
            "final_bounds": {"right": final_right, "bottom": final_bottom},
            "final_size": final_canvas.shape
        }
        
        # Step 7: OUTPUT ANALYSIS
        print("\n📤 STEP 7: OUTPUT ANALYSIS")
        
        # Analyze final output
        alpha_channel = final_canvas[:, :, 3]
        rows_with_text = np.where(alpha_channel.any(axis=1))[0]
        cols_with_text = np.where(alpha_channel.any(axis=0))[0]
        
        if len(rows_with_text) > 0 and len(cols_with_text) > 0:
            actual_top = rows_with_text[0]
            actual_bottom = rows_with_text[-1]
            actual_left = cols_with_text[0]
            actual_right = cols_with_text[-1]
            actual_height = actual_bottom - actual_top + 1
            actual_width = actual_right - actual_left + 1
            
            print(f"  DETECTED TEXT BOUNDS: ({actual_left}, {actual_top}) to ({actual_right}, {actual_bottom})")
            print(f"  DETECTED DIMENSIONS: {actual_width}x{actual_height}")
            
            # Check for cutoff
            cutoff_bottom = actual_bottom >= self.resolution[1] - 1
            cutoff_top = actual_top <= 0
            cutoff_left = actual_left <= 0
            cutoff_right = actual_right >= self.resolution[0] - 1
            
            if cutoff_bottom:
                print(f"  ⚠️  BOTTOM CUTOFF DETECTED: Text bottom at {actual_bottom} >= screen bottom {self.resolution[1]-1}")
            if cutoff_top:
                print(f"  ⚠️  TOP CUTOFF DETECTED: Text top at {actual_top} <= 0")
            if cutoff_left:
                print(f"  ⚠️  LEFT CUTOFF DETECTED: Text left at {actual_left} <= 0")
            if cutoff_right:
                print(f"  ⚠️  RIGHT CUTOFF DETECTED: Text right at {actual_right} >= {self.resolution[0]-1}")
                
            if not any([cutoff_bottom, cutoff_top, cutoff_left, cutoff_right]):
                print(f"  ✅ NO CUTOFF DETECTED: Text fully within bounds")
                
        else:
            print(f"  ❌ NO TEXT DETECTED in final output!")
            actual_top = actual_bottom = actual_left = actual_right = 0
            actual_height = actual_width = 0
        
        output_data = {
            "detected_bounds": {
                "top": actual_top, "bottom": actual_bottom,
                "left": actual_left, "right": actual_right,
                "width": actual_width, "height": actual_height
            },
            "cutoff_detected": actual_bottom >= self.resolution[1] - 1
        }
        
        # Create comprehensive visualization
        self.create_pipeline_visualization(
            input_data, font_metrics, position_data, canvas_data, 
            composite_data, crop_data, output_data, 
            raw_text_surface, canvas, final_canvas
        )
        
        return final_canvas
        
    def create_pipeline_visualization(self, input_data, font_metrics, position_data, 
                                    canvas_data, composite_data, crop_data, output_data,
                                    raw_text_surface, canvas, final_canvas):
        """Create comprehensive visualization of the entire pipeline."""
        
        fig = plt.figure(figsize=(20, 24))
        fig.suptitle("Complete Text Rendering Pipeline: Input → Output Analysis", fontsize=20, color='white')
        
        # Create grid layout
        gs = fig.add_gridspec(6, 3, height_ratios=[1, 1, 1, 1, 1, 1], hspace=0.3, wspace=0.2)
        
        # Step 1: Input Analysis
        ax1 = fig.add_subplot(gs[0, :])
        ax1.set_title("STEP 1: INPUT DATA", fontsize=16, color='#00ff88', weight='bold')
        ax1.axis('off')
        
        input_text = f"""
📥 INPUT PARAMETERS:
  • Text: "{input_data['text']}"
  • Font Size: {input_data['font_size']}px
  • Target Resolution: {input_data['resolution'][0]}x{input_data['resolution'][1]}
  • Vertical Position: center
        """
        ax1.text(0.05, 0.5, input_text, fontsize=14, fontfamily='monospace', 
                transform=ax1.transAxes, color='white', va='center',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#2a2a2a", alpha=0.8))
        
        # Step 2: Font Metrics
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.set_title("STEP 2: RAW FONT RENDERING", fontsize=14, color='#88ddff')
        ax2.imshow(raw_text_surface, aspect='auto')
        ax2.text(0.5, -0.1, f"Raw Text: {font_metrics['width']}x{font_metrics['height']}px", 
                transform=ax2.transAxes, ha='center', color='white', fontsize=12)
        
        # Step 3: Position Calculation
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.set_title("STEP 3: POSITION CALCULATION", fontsize=14, color='#88ddff')
        ax3.axis('off')
        
        position_text = f"""
📍 CALCULATIONS:
Canvas Padding: {position_data['canvas_padding']}px
Safe Margins: L:{position_data['safe_margins']['left']} R:{position_data['safe_margins']['right']}
Available Width: {position_data['available_width']}px

RESULT:
Canvas Position: ({position_data['x_pos']}, {position_data['y_pos']})
        """
        ax3.text(0.05, 0.95, position_text, fontsize=10, fontfamily='monospace',
                transform=ax3.transAxes, color='white', va='top',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#2a4a2a", alpha=0.8))
        
        # Step 4: Canvas Creation
        ax4 = fig.add_subplot(gs[1, 2])
        ax4.set_title("STEP 4: CANVAS CREATION", fontsize=14, color='#88ddff')
        ax4.axis('off')
        
        canvas_text = f"""
🖼️ CANVAS SETUP:
Screen: {canvas_data['screen_size'][0]}x{canvas_data['screen_size'][1]}
Padding: {canvas_data['padding']}px all sides
Canvas: {canvas_data['canvas_size'][0]}x{canvas_data['canvas_size'][1]}

PURPOSE:
Prevent edge clipping during effects
        """
        ax4.text(0.05, 0.95, canvas_text, fontsize=10, fontfamily='monospace',
                transform=ax4.transAxes, color='white', va='top',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#2a2a4a", alpha=0.8))
        
        # Step 5: Canvas with Text (scaled down for visualization)
        ax5 = fig.add_subplot(gs[2, :])
        ax5.set_title("STEP 5: TEXT COMPOSITING ON PADDED CANVAS", fontsize=14, color='#ffaa44')
        
        # Scale down canvas for visualization
        scale_factor = 0.3
        canvas_small = cv2.resize(canvas, (int(canvas.shape[1] * scale_factor), int(canvas.shape[0] * scale_factor)))
        ax5.imshow(canvas_small, aspect='auto')
        
        # Draw guides
        canvas_h_small, canvas_w_small = canvas_small.shape[:2]
        padding_scaled = position_data['canvas_padding'] * scale_factor
        
        # Screen area within canvas
        screen_rect = patches.Rectangle((padding_scaled, padding_scaled), 
                                      self.resolution[0] * scale_factor, 
                                      self.resolution[1] * scale_factor,
                                      linewidth=2, edgecolor='white', facecolor='none', linestyle='--')
        ax5.add_patch(screen_rect)
        ax5.text(padding_scaled, padding_scaled - 10, "Final Screen Area", fontsize=10, color='white')
        
        composite_status = "✅ SUCCESS" if composite_data['success'] else "❌ FAILED"
        ax5.text(0.02, 0.98, f"Compositing: {composite_status}", transform=ax5.transAxes, 
                fontsize=12, color='white', va='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="green" if composite_data['success'] else "red", alpha=0.7))
        
        # Step 6: Cropping Process
        ax6 = fig.add_subplot(gs[3, 0])
        ax6.set_title("STEP 6A: BEFORE CROPPING", fontsize=12, color='#ffaa44')
        ax6.imshow(canvas_small, aspect='auto')
        
        # Highlight crop area
        crop_rect = patches.Rectangle((padding_scaled, padding_scaled),
                                    self.resolution[0] * scale_factor,
                                    self.resolution[1] * scale_factor,
                                    linewidth=3, edgecolor='red', facecolor='none')
        ax6.add_patch(crop_rect)
        ax6.text(0.5, -0.05, "Red = Crop Area", transform=ax6.transAxes, ha='center', color='red', fontsize=10)
        
        # Step 7: Final Output
        ax7 = fig.add_subplot(gs[3, 1])
        ax7.set_title("STEP 6B: AFTER CROPPING", fontsize=12, color='#ffaa44')
        ax7.imshow(final_canvas, aspect='auto')
        
        # Draw screen boundaries
        screen_rect = patches.Rectangle((0, 0), self.resolution[0], self.resolution[1],
                                      linewidth=2, edgecolor='white', facecolor='none')
        ax7.add_patch(screen_rect)
        
        # Highlight detected text bounds if any
        if output_data['detected_bounds']['width'] > 0:
            text_rect = patches.Rectangle(
                (output_data['detected_bounds']['left'], output_data['detected_bounds']['top']),
                output_data['detected_bounds']['width'], output_data['detected_bounds']['height'],
                linewidth=2, edgecolor='yellow', facecolor='none'
            )
            ax7.add_patch(text_rect)
            
            # Draw bottom line
            ax7.axhline(y=self.resolution[1]-1, color='red', linewidth=2, label='Screen Bottom')
            ax7.axhline(y=output_data['detected_bounds']['bottom'], color='yellow', linewidth=2, label='Text Bottom')
            ax7.legend(loc='upper right', fontsize=8)
        
        # Step 8: Analysis Results
        ax8 = fig.add_subplot(gs[3, 2])
        ax8.set_title("STEP 7: OUTPUT ANALYSIS", fontsize=12, color='#ffaa44')
        ax8.axis('off')
        
        if output_data['detected_bounds']['width'] > 0:
            cutoff_status = "⚠️ CUTOFF DETECTED" if output_data['cutoff_detected'] else "✅ NO CUTOFF"
            cutoff_color = 'red' if output_data['cutoff_detected'] else 'green'
            
            analysis_text = f"""
📤 FINAL RESULTS:
Status: {cutoff_status}

Detected Bounds:
  Top: {output_data['detected_bounds']['top']}
  Bottom: {output_data['detected_bounds']['bottom']}
  Left: {output_data['detected_bounds']['left']}
  Right: {output_data['detected_bounds']['right']}
  Size: {output_data['detected_bounds']['width']}x{output_data['detected_bounds']['height']}

Screen Height: {self.resolution[1]}
Bottom Margin: {self.resolution[1] - output_data['detected_bounds']['bottom'] - 1}px
            """
        else:
            cutoff_status = "❌ NO TEXT DETECTED"
            cutoff_color = 'red'
            analysis_text = f"""
📤 FINAL RESULTS:
Status: {cutoff_status}

NO TEXT FOUND in final output!
This indicates a critical failure in
the rendering pipeline.
            """
        
        ax8.text(0.05, 0.95, analysis_text, fontsize=10, fontfamily='monospace',
                transform=ax8.transAxes, color='white', va='top',
                bbox=dict(boxstyle="round,pad=0.5", facecolor=cutoff_color, alpha=0.3))
        
        # Data Flow Diagram
        ax9 = fig.add_subplot(gs[4, :])
        ax9.set_title("PIPELINE DATA FLOW", fontsize=16, color='#ff8844', weight='bold')
        ax9.axis('off')
        
        # Create flow diagram
        flow_y = 0.5
        steps = [
            ("Input Text", "#2a2a2a"),
            ("Font Render", "#2a4a2a"), 
            ("Position Calc", "#2a2a4a"),
            ("Canvas Create", "#4a2a2a"),
            ("Composite", "#4a4a2a"),
            ("Crop", "#2a4a4a"),
            ("Output", "#4a2a4a" if not output_data['cutoff_detected'] else "#4a2a2a")
        ]
        
        step_width = 0.12
        for i, (step_name, color) in enumerate(steps):
            x = 0.05 + i * step_width
            
            # Draw box
            box = patches.FancyBboxPatch((x-0.05, flow_y-0.15), 0.1, 0.3,
                                       boxstyle="round,pad=0.01", 
                                       facecolor=color, edgecolor='white', linewidth=1)
            ax9.add_patch(box)
            
            # Add text
            ax9.text(x, flow_y, step_name, ha='center', va='center', fontsize=10, 
                    color='white', weight='bold', transform=ax9.transAxes)
            
            # Add arrow to next step
            if i < len(steps) - 1:
                ax9.annotate('', xy=(x + 0.06, flow_y), xytext=(x + 0.04, flow_y),
                           arrowprops=dict(arrowstyle='->', color='white', lw=2),
                           transform=ax9.transAxes)
        
        # Problem Areas
        ax10 = fig.add_subplot(gs[5, :])
        ax10.set_title("CRITICAL ANALYSIS: WHERE THINGS GO WRONG", fontsize=16, color='#ff4444', weight='bold')
        ax10.axis('off')
        
        problems_text = f"""
🔍 PIPELINE FAILURE POINTS:

1. FONT RENDERING → POSITION CALCULATION:
   • Raw text: {font_metrics['width']}x{font_metrics['height']}px
   • Position calculated: ({position_data['x_pos']}, {position_data['y_pos']}) in canvas coordinates
   • Final position: ({crop_data['final_position']['x']}, {crop_data['final_position']['y']}) in screen coordinates

2. POSITION CALCULATION → COMPOSITING:
   • Canvas bounds: {canvas_data['canvas_size'][0]}x{canvas_data['canvas_size'][1]}
   • Text placement: {'SUCCESS' if composite_data['success'] else 'FAILED'}
   • Text bounds in canvas: ({composite_data['text_bounds']['x']}, {composite_data['text_bounds']['y']}) to ({composite_data['text_bounds']['x'] + composite_data['text_bounds']['w']}, {composite_data['text_bounds']['y'] + composite_data['text_bounds']['h']})

3. COMPOSITING → CROPPING:
   • Crop region: [{position_data['canvas_padding']}:{position_data['canvas_padding'] + self.resolution[1]}, {position_data['canvas_padding']}:{position_data['canvas_padding'] + self.resolution[0]}]
   • Expected final bottom: {crop_data['final_bounds']['bottom']}
   • Actual detected bottom: {output_data['detected_bounds']['bottom']}

4. ROOT CAUSE ANALYSIS:
   • Expected text to end at Y={crop_data['final_bounds']['bottom']}
   • Screen height is {self.resolution[1]}
   • {'Text extends beyond screen!' if crop_data['final_bounds']['bottom'] >= self.resolution[1] else 'Text should fit within screen.'}
   • {'CUTOFF CONFIRMED!' if output_data['cutoff_detected'] else 'No cutoff detected in final output.'}
        """
        
        ax10.text(0.02, 0.98, problems_text, fontsize=11, fontfamily='monospace',
                 transform=ax10.transAxes, color='white', va='top',
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="#2a1a1a", alpha=0.9))
        
        # Save visualization
        plt.tight_layout()
        fig.savefig(self.debug_output_dir / "complete_pipeline_debug.png", 
                   dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close(fig)
        
        print(f"\n📊 Complete pipeline visualization saved to: {self.debug_output_dir / 'complete_pipeline_debug.png'}")


if __name__ == "__main__":
    # Test with problematic text
    debugger = TextPipelineDebugger()
    
    # Test cases that are likely to show cutoff
    test_cases = [
        ("Simple text", 72),
        ("Text with descenders: gypsy jungle", 96),
        ("Long text that might extend beyond boundaries", 120),
        ("Extreme size test", 150)
    ]
    
    for text, size in test_cases:
        print(f"\n{'='*100}")
        print(f"TESTING: '{text}' at {size}px")
        print(f"{'='*100}")
        
        try:
            debugger.debug_complete_pipeline(text, size)
        except Exception as e:
            print(f"❌ ERROR in pipeline: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Pipeline debugging complete! Check {debugger.debug_output_dir} for results.")
#!/usr/bin/env python3
"""
Debug the ACTUAL lyric video rendering to compare with our simplified tests.
This will use the real render_lyric_line function to see the difference.
"""

import numpy as np
import cv2
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set dark theme for matplotlib
plt.style.use('dark_background')

# Import our components
from src.asabaal_utils.video_processing.lyric_video.text.renderer import TextRenderer, TextStyle, AnimationConfig
from src.asabaal_utils.video_processing.lyric_video.lyrics.parser import LyricWord

class ActualRenderDebugger:
    """Debug the actual lyric video rendering using real functions."""
    
    def __init__(self, resolution=(1920, 1080)):
        self.resolution = resolution
        self.renderer = TextRenderer(resolution)
        self.debug_output_dir = Path("actual_render_debug")
        self.debug_output_dir.mkdir(exist_ok=True)
        
    def test_actual_rendering(self):
        """Test actual lyric line rendering with the real functions."""
        print("🎬 TESTING ACTUAL LYRIC VIDEO RENDERING")
        print("=" * 60)
        
        # Test cases that users typically see in lyric videos
        test_cases = [
            {
                "text": "Every breath you take",
                "font_size": 72,
                "description": "Typical lyric line"
            },
            {
                "text": "I'll be watching you",
                "font_size": 96,
                "description": "Larger lyric line"  
            },
            {
                "text": "Can't you see you belong to me",
                "font_size": 120,
                "description": "Long line with descenders"
            },
            {
                "text": "How my poor heart aches with every step you take",
                "font_size": 84,
                "description": "Very long line"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n{'='*50}")
            print(f"TEST {i+1}: {test_case['description']}")
            print(f"Text: '{test_case['text']}'")
            print(f"Font size: {test_case['font_size']}px")
            print(f"{'='*50}")
            
            self.debug_single_actual_render(test_case, f"actual_test_{i+1}")
            
    def debug_single_actual_render(self, test_case, test_id):
        """Debug a single actual render using the real render_lyric_line function."""
        
        text = test_case["text"]
        font_size = test_case["font_size"]
        
        # Create style
        style = TextStyle(
            font_size=font_size, 
            vertical_position="center",
            glow_radius=0,  # Start without effects
            stroke_width=2
        )
        
        # Create animation config
        animation_config = self.renderer.animation_presets['subtle']
        
        # Create words as they would appear in real usage
        words = []
        word_list = text.split()
        current_time = 0.0
        
        for i, word_text in enumerate(word_list):
            word_duration = 0.5  # 500ms per word
            start_time = current_time
            end_time = current_time + word_duration
            
            word = LyricWord(word_text, start_time, end_time)
            words.append(word)
            current_time = end_time
            
        line_start = 0.0
        line_end = current_time
        test_time = line_end / 2  # Middle of the line
        
        print(f"  📝 Created {len(words)} words: {[w.text for w in words]}")
        print(f"  ⏱️  Line timing: {line_start:.1f}s to {line_end:.1f}s, testing at {test_time:.1f}s")
        
        # STEP 1: Render using actual render_lyric_line function
        print(f"  🎨 Rendering using actual render_lyric_line()...")
        
        try:
            actual_rendered = self.renderer.render_lyric_line(
                words=words,
                current_time=test_time,
                style=style,
                animation_config=animation_config,
                line_start=line_start,
                line_end=line_end,
                audio_features=None,  # No audio features for this test
                effects_config=None   # No effects for this test
            )
            
            print(f"  ✅ Render successful: {actual_rendered.shape}")
            
        except Exception as e:
            print(f"  ❌ Render failed: {e}")
            import traceback
            traceback.print_exc()
            return
            
        # STEP 2: Analyze the actual output
        alpha_channel = actual_rendered[:, :, 3]
        rows_with_text = np.where(alpha_channel.any(axis=1))[0]
        cols_with_text = np.where(alpha_channel.any(axis=0))[0]
        
        if len(rows_with_text) > 0 and len(cols_with_text) > 0:
            actual_top = rows_with_text[0]
            actual_bottom = rows_with_text[-1]
            actual_left = cols_with_text[0]
            actual_right = cols_with_text[-1]
            actual_height = actual_bottom - actual_top + 1
            actual_width = actual_right - actual_left + 1
            
            print(f"  📏 Detected text bounds: ({actual_left}, {actual_top}) to ({actual_right}, {actual_bottom})")
            print(f"  📏 Detected dimensions: {actual_width}x{actual_height}")
            
            # Check for cutoff
            margin_bottom = self.resolution[1] - actual_bottom - 1
            margin_top = actual_top
            margin_left = actual_left
            margin_right = self.resolution[0] - actual_right - 1
            
            print(f"  📐 Margins - Top: {margin_top}px, Bottom: {margin_bottom}px, Left: {margin_left}px, Right: {margin_right}px")
            
            # Check for potential issues
            issues = []
            if actual_bottom >= self.resolution[1] - 5:  # Within 5px of bottom
                issues.append(f"Text very close to bottom: {actual_bottom} vs screen {self.resolution[1]}")
            if actual_top <= 5:
                issues.append(f"Text very close to top: {actual_top}")
            if actual_left <= 5:
                issues.append(f"Text very close to left: {actual_left}")
            if actual_right >= self.resolution[0] - 5:
                issues.append(f"Text very close to right: {actual_right}")
                
            if issues:
                print(f"  ⚠️  POTENTIAL ISSUES DETECTED:")
                for issue in issues:
                    print(f"     - {issue}")
            else:
                print(f"  ✅ Text appears to be safely positioned")
                
        else:
            print(f"  ❌ NO TEXT DETECTED in actual render!")
            actual_top = actual_bottom = actual_left = actual_right = 0
            actual_height = actual_width = 0
            issues = ["No text detected"]
            
        # STEP 3: Create visualization
        self.create_actual_render_visualization(
            test_case, test_id, actual_rendered, 
            {
                "bounds": {
                    "top": actual_top, "bottom": actual_bottom,
                    "left": actual_left, "right": actual_right,
                    "width": actual_width, "height": actual_height
                },
                "issues": issues,
                "margins": {
                    "top": margin_top if 'margin_top' in locals() else 0,
                    "bottom": margin_bottom if 'margin_bottom' in locals() else 0,
                    "left": margin_left if 'margin_left' in locals() else 0,
                    "right": margin_right if 'margin_right' in locals() else 0
                }
            }
        )
        
    def create_actual_render_visualization(self, test_case, test_id, rendered_frame, analysis):
        """Create visualization of actual render results."""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"Actual Render Analysis: {test_case['description']}", fontsize=16, color='white')
        
        # Subplot 1: Full frame with overlays
        ax1 = axes[0, 0]
        ax1.set_title("Full Rendered Frame", color='white')
        ax1.imshow(rendered_frame, aspect='auto')
        
        # Draw screen boundary
        screen_rect = patches.Rectangle((0, 0), self.resolution[0], self.resolution[1], 
                                      linewidth=2, edgecolor='white', facecolor='none')
        ax1.add_patch(screen_rect)
        
        # Draw safe zones (from our current implementation)
        SAFE_TOP_MARGIN = 150
        SAFE_BOTTOM_MARGIN = 350
        safe_zone = patches.Rectangle((0, SAFE_TOP_MARGIN), self.resolution[0], 
                                    self.resolution[1] - SAFE_TOP_MARGIN - SAFE_BOTTOM_MARGIN,
                                    linewidth=2, edgecolor='#00ff00', facecolor='none', linestyle='--')
        ax1.add_patch(safe_zone)
        
        # Draw detected text bounds
        if analysis["bounds"]["width"] > 0:
            text_rect = patches.Rectangle(
                (analysis["bounds"]["left"], analysis["bounds"]["top"]),
                analysis["bounds"]["width"], analysis["bounds"]["height"],
                linewidth=2, edgecolor='yellow', facecolor='none'
            )
            ax1.add_patch(text_rect)
            
        ax1.set_xlim(0, self.resolution[0])
        ax1.set_ylim(self.resolution[1], 0)
        
        # Subplot 2: Bottom area zoom
        ax2 = axes[0, 1]
        ax2.set_title("Bottom Area (Critical Zone)", color='white')
        
        # Show bottom 400px
        bottom_region = rendered_frame[-400:, :]
        ax2.imshow(bottom_region, extent=[0, self.resolution[0], self.resolution[1], self.resolution[1]-400], aspect='auto')
        
        # Draw critical lines
        ax2.axhline(y=self.resolution[1], color='red', linewidth=3, label='Screen Bottom')
        ax2.axhline(y=self.resolution[1] - SAFE_BOTTOM_MARGIN, color='#00ff00', linewidth=2, linestyle='--', label='Safe Zone')
        
        if analysis["bounds"]["bottom"] > 0:
            ax2.axhline(y=analysis["bounds"]["bottom"], color='yellow', linewidth=2, label='Text Bottom')
            
        ax2.set_xlim(0, self.resolution[0])
        ax2.set_ylim(self.resolution[1] + 20, self.resolution[1] - 400)
        ax2.legend()
        
        # Subplot 3: Text close-up
        ax3 = axes[1, 0]
        ax3.set_title("Text Close-up", color='white')
        
        if analysis["bounds"]["width"] > 0:
            # Extract text region with padding
            padding = 100
            y1 = max(0, analysis["bounds"]["top"] - padding)
            y2 = min(self.resolution[1], analysis["bounds"]["bottom"] + padding)
            x1 = max(0, analysis["bounds"]["left"] - padding)
            x2 = min(self.resolution[0], analysis["bounds"]["right"] + padding)
            
            text_region = rendered_frame[y1:y2, x1:x2]
            ax3.imshow(text_region, extent=[x1, x2, y2, y1], aspect='auto')
            
            # Draw bounds
            ax3.axhline(y=analysis["bounds"]["top"], color='yellow', linewidth=1, linestyle='--', alpha=0.5)
            ax3.axhline(y=analysis["bounds"]["bottom"], color='yellow', linewidth=2, label='Text Bottom')
            ax3.axvline(x=analysis["bounds"]["left"], color='yellow', linewidth=1, linestyle='--', alpha=0.5)
            ax3.axvline(x=analysis["bounds"]["right"], color='yellow', linewidth=1, linestyle='--', alpha=0.5)
            
            # Show screen bottom if visible
            if self.resolution[1] >= y1 and self.resolution[1] <= y2:
                ax3.axhline(y=self.resolution[1], color='red', linewidth=3, label='Screen Bottom')
                
            ax3.set_xlim(x1, x2)
            ax3.set_ylim(y2, y1)
            ax3.legend()
        else:
            ax3.text(0.5, 0.5, "No text detected", ha='center', va='center', 
                    transform=ax3.transAxes, fontsize=14, color='red')
            
        # Subplot 4: Analysis summary
        ax4 = axes[1, 1]
        ax4.set_title("Analysis Summary", color='white')
        ax4.axis('off')
        
        summary_text = f"""
TEST: {test_case['description']}
Text: "{test_case['text']}"
Font Size: {test_case['font_size']}px

DETECTED BOUNDS:
  Top: {analysis['bounds']['top']}
  Bottom: {analysis['bounds']['bottom']}
  Left: {analysis['bounds']['left']}
  Right: {analysis['bounds']['right']}
  Size: {analysis['bounds']['width']}x{analysis['bounds']['height']}

MARGINS:
  Top: {analysis['margins']['top']}px
  Bottom: {analysis['margins']['bottom']}px
  Left: {analysis['margins']['left']}px
  Right: {analysis['margins']['right']}px

SCREEN:
  Resolution: {self.resolution[0]}x{self.resolution[1]}
  Safe Bottom: {self.resolution[1] - SAFE_BOTTOM_MARGIN}

STATUS:
"""
        
        if analysis["issues"]:
            summary_text += "  ⚠️  ISSUES DETECTED:\n"
            for issue in analysis["issues"]:
                summary_text += f"    - {issue}\n"
        else:
            summary_text += "  ✅ NO ISSUES DETECTED"
            
        ax4.text(0.05, 0.95, summary_text, fontsize=10, fontfamily='monospace',
                transform=ax4.transAxes, color='white', va='top',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#333333", alpha=0.8))
        
        # Save visualization
        plt.tight_layout()
        fig.savefig(self.debug_output_dir / f"{test_id}_analysis.png", 
                   dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close(fig)
        
        print(f"  📊 Visualization saved: {self.debug_output_dir / f'{test_id}_analysis.png'}")


if __name__ == "__main__":
    debugger = ActualRenderDebugger()
    debugger.test_actual_rendering()
    print(f"\n✅ Actual render debugging complete! Check {debugger.debug_output_dir} for results.")
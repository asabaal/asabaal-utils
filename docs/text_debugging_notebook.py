# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 🔍 Text Rendering Debug Notebook
#
# This notebook helps us visually debug the text cutoff issue step by step.

# %%
# Setup and imports
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from IPython.display import display, Image as IPImage
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Import our components
from src.asabaal_utils.video_processing.lyric_video.text.renderer import TextRenderer, TextStyle
from src.asabaal_utils.video_processing.lyric_video.text.fonts import FontManager
from src.asabaal_utils.video_processing.lyric_video.lyrics.parser import LyricWord, LyricLine

print("✅ Imports successful!")

# %% [markdown]
# ## Step 1: Test Basic Text Rendering

# %%
# Initialize components
resolution = (1920, 1080)
renderer = TextRenderer(resolution)
font_manager = FontManager()

# Test text
test_text = "Testing gjpqy letters that drop below baseline"

# Create different styles to test
styles = [
    TextStyle(font_size=48, vertical_position="top"),
    TextStyle(font_size=72, vertical_position="center"),
    TextStyle(font_size=96, vertical_position="bottom"),
    TextStyle(font_size=120, vertical_position="center", glow_radius=20)
]

# Render and visualize each style
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()

for i, style in enumerate(styles):
    # Get font and measure text
    font = font_manager.get_font(style.font_family, style.font_size)
    text_surface = font_manager.render_text(test_text, font, style.color)
    text_h, text_w = text_surface.shape[:2]
    
    # Calculate position
    y_pos = renderer._calculate_vertical_position(text_h, style, 0.0, None)
    
    # Create visualization
    ax = axes[i]
    ax.set_title(f"Font Size: {style.font_size}px, Position: {style.vertical_position}")
    ax.set_xlim(0, resolution[0])
    ax.set_ylim(resolution[1], 0)  # Invert Y
    
    # Draw screen
    screen = patches.Rectangle((0, 0), resolution[0], resolution[1], 
                              linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.2)
    ax.add_patch(screen)
    
    # Draw safe zones
    safe_zone = patches.Rectangle((0, 100), resolution[0], resolution[1] - 300,
                                 linewidth=1, edgecolor='green', facecolor='lightgreen', alpha=0.1)
    ax.add_patch(safe_zone)
    
    # Draw text rectangle
    x_pos = (resolution[0] - text_w) // 2
    text_bottom = y_pos + text_h
    
    # Color based on whether it fits
    color = 'red' if text_bottom > resolution[1] else 'blue'
    text_rect = patches.Rectangle((x_pos, y_pos), text_w, text_h,
                                 linewidth=2, edgecolor=color, facecolor=color, alpha=0.3)
    ax.add_patch(text_rect)
    
    # Add measurements
    ax.text(10, 50, f"Y: {y_pos}, Bottom: {text_bottom}", fontsize=10)
    if text_bottom > resolution[1]:
        ax.text(10, 80, f"⚠️ OVERFLOW: {text_bottom - resolution[1]}px", fontsize=12, color='red')
    
    ax.set_xlabel("X (pixels)")
    ax.set_ylabel("Y (pixels)")
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# %% [markdown]
# ## Step 2: Test Actual Lyric Rendering

# %%
# Create test lyric line
words = [
    LyricWord("Testing", 0.0, 1.0),
    LyricWord("text", 1.0, 2.0),
    LyricWord("rendering", 2.0, 3.0),
    LyricWord("gjpqy", 3.0, 4.0)
]

# Test with different styles
test_style = TextStyle(font_size=96, vertical_position="center")
animation_config = renderer.animation_presets['subtle']

# Render the line
rendered_line = renderer.render_lyric_line(
    words=words,
    current_time=2.0,  # Middle of animation
    style=test_style,
    animation_config=animation_config,
    line_start=0.0,
    line_end=4.0
)

# Visualize the result
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Show rendered line
ax1.set_title("Rendered Lyric Line")
ax1.imshow(rendered_line)
ax1.axhline(y=resolution[1], color='red', linestyle='--', label='Screen Bottom')
ax1.legend()

# Show alpha channel to see if text is cut off
ax2.set_title("Alpha Channel (Text Visibility)")
ax2.imshow(rendered_line[:, :, 3], cmap='gray')
ax2.axhline(y=resolution[1], color='red', linestyle='--', label='Screen Bottom')
ax2.legend()

plt.tight_layout()
plt.show()

# Check for cutoff
last_row_with_text = np.where(rendered_line[:, :, 3].any(axis=1))[0]
if len(last_row_with_text) > 0:
    last_text_y = last_row_with_text[-1]
    print(f"Last row with text: {last_text_y}")
    print(f"Screen height: {resolution[1]}")
    if last_text_y >= resolution[1] - 1:
        print("⚠️ TEXT IS CUT OFF AT BOTTOM!")
    else:
        print(f"✅ Text ends {resolution[1] - last_text_y}px before screen bottom")


# %% [markdown]
# ## Step 3: Test Canvas Padding Fix

# %%
# Let's manually test the canvas padding approach
def test_canvas_padding():
    # Create text that we know extends below
    test_style = TextStyle(font_size=120, vertical_position="bottom", glow_radius=30)
    
    # Render with current method
    rendered = renderer.render_lyric_line(
        words=words,
        current_time=2.0,
        style=test_style,
        animation_config=animation_config,
        line_start=0.0,
        line_end=4.0
    )
    
    # Check dimensions
    print(f"Rendered shape: {rendered.shape}")
    print(f"Expected shape: {resolution[1]} x {resolution[0]} x 4")
    
    # Find text bounds
    alpha = rendered[:, :, 3]
    rows_with_text = np.where(alpha.any(axis=1))[0]
    cols_with_text = np.where(alpha.any(axis=0))[0]
    
    if len(rows_with_text) > 0 and len(cols_with_text) > 0:
        text_top = rows_with_text[0]
        text_bottom = rows_with_text[-1]
        text_left = cols_with_text[0]
        text_right = cols_with_text[-1]
        
        print(f"\nText bounds:")
        print(f"  Top: {text_top}")
        print(f"  Bottom: {text_bottom} (screen height: {resolution[1]})")
        print(f"  Left: {text_left}")
        print(f"  Right: {text_right} (screen width: {resolution[0]})")
        
        if text_bottom >= resolution[1] - 1:
            print("\n⚠️ TEXT IS BEING CUT OFF!")
            print(f"Text extends to row {text_bottom} but screen ends at {resolution[1]-1}")
        else:
            print(f"\n✅ Text has {resolution[1] - text_bottom - 1}px margin from bottom")
    
    return rendered

rendered_test = test_canvas_padding()

# %% [markdown]
# ## Step 4: Test Different Resolutions

# %%
# Test with different resolutions to see if it's resolution-specific
test_resolutions = [
    (1280, 720),   # 720p
    (1920, 1080),  # 1080p 
    (3840, 2160)   # 4K
]

for res in test_resolutions:
    print(f"\nTesting resolution: {res[0]}x{res[1]}")
    test_renderer = TextRenderer(res)
    
    # Test with large text
    style = TextStyle(font_size=int(res[1] * 0.1), vertical_position="center")  # 10% of height
    
    # Calculate position
    text_height = int(res[1] * 0.1)  # Approximate
    y_pos = test_renderer._calculate_vertical_position(text_height, style, 0.0, None)
    
    print(f"  Font size: {style.font_size}px")
    print(f"  Calculated Y: {y_pos}")
    print(f"  Text bottom: {y_pos + text_height}")
    print(f"  Margin: {res[1] - (y_pos + text_height)}px")
    
    if y_pos + text_height > res[1]:
        print("  ⚠️ WOULD BE CUT OFF!")


# %% [markdown]
# ## Step 5: Trace Through Entire Pipeline

# %%
# Let's trace through the entire rendering pipeline step by step
def trace_rendering_pipeline():
    print("=== RENDERING PIPELINE TRACE ===")
    
    # 1. Text style
    style = TextStyle(font_size=96, vertical_position="bottom")
    print(f"1. Style: font_size={style.font_size}, position={style.vertical_position}")
    
    # 2. Font loading
    font = font_manager.get_font(style.font_family, style.font_size)
    print(f"2. Font loaded: {font}")
    
    # 3. Render individual word
    test_word = "Testing"
    word_surface = font_manager.render_text(test_word, font, style.color)
    print(f"3. Word surface shape: {word_surface.shape}")
    
    # 4. Calculate position
    text_height = word_surface.shape[0]
    y_position = renderer._calculate_vertical_position(text_height, style, 0.0, None)
    print(f"4. Calculated Y position: {y_position}")
    print(f"   Text height: {text_height}")
    print(f"   Bottom would be at: {y_position + text_height}")
    print(f"   Screen height: {resolution[1]}")
    
    # 5. Canvas creation (checking current implementation)
    print(f"\n5. Canvas creation:")
    print(f"   Current: Canvas padding = 200px")
    print(f"   Canvas size would be: {resolution[1] + 400} x {resolution[0] + 400}")
    
    # 6. Final check
    if y_position + text_height > resolution[1]:
        overflow = (y_position + text_height) - resolution[1]
        print(f"\n⚠️ TEXT WOULD OVERFLOW BY {overflow}px!")
        print(f"   This should be prevented by:")
        print(f"   - Safe zone bottom margin: 200px")
        print(f"   - Canvas padding: 200px")
        print(f"   - Position clamping")
    else:
        margin = resolution[1] - (y_position + text_height)
        print(f"\n✅ Text fits with {margin}px bottom margin")

trace_rendering_pipeline()


# %% [markdown]
# ## Step 6: Direct Test of Compositing

# %%
# Test the _composite_image function directly
def test_composite_function():
    # Create a test canvas
    canvas = np.zeros((resolution[1], resolution[0], 4), dtype=np.uint8)
    
    # Create test text that extends beyond bottom
    text_height = 200
    text_width = 500
    test_text = np.ones((text_height, text_width, 4), dtype=np.uint8) * 255
    
    # Position that would cause cutoff
    x_pos = (resolution[0] - text_width) // 2
    y_pos = resolution[1] - 100  # Only 100px from bottom, text is 200px tall
    
    print(f"Canvas size: {canvas.shape}")
    print(f"Text size: {test_text.shape}")
    print(f"Position: ({x_pos}, {y_pos})")
    print(f"Text would extend to: y={y_pos + text_height}")
    print(f"Screen bottom: y={resolution[1]}")
    print(f"Overflow: {max(0, y_pos + text_height - resolution[1])}px")
    
    # Test composite
    renderer._composite_image(canvas, test_text, x_pos, y_pos)
    
    # Check what got composited
    composited_region = canvas[y_pos:, x_pos:x_pos+text_width, 3]
    actual_height = np.sum(composited_region.any(axis=1))
    
    print(f"\nActual composited height: {actual_height}px")
    print(f"Expected (without clipping): {text_height}px")
    print(f"Expected (with clipping): {resolution[1] - y_pos}px")
    
    if actual_height < text_height:
        print("\n⚠️ TEXT WAS CLIPPED!")
    
    return canvas

test_canvas = test_composite_function()

# %% [markdown]
# ## Summary & Next Steps
#
# Based on our debugging, here are the key findings and recommendations:

# %%
print("🔍 DEBUGGING SUMMARY")
print("=" * 50)
print("\nPotential causes of text cutoff:")
print("1. ❓ Position calculation placing text too low")
print("2. ❓ Canvas clipping in _composite_image()")
print("3. ❓ Effects (glow, shadow) extending beyond text bounds")
print("4. ❓ Video encoding cropping the output")
print("5. ❓ Compositor layer blending clipping")
print("\nDebugging steps to try:")
print("1. Add print statements in _calculate_vertical_position()")
print("2. Log actual text bounds in render_lyric_line()")
print("3. Save raw frames before video encoding")
print("4. Test with --text-only flag to isolate issue")
print("5. Try different fonts to see if font-specific")
print("\n💡 Quick workaround: Use --font-size with smaller value")

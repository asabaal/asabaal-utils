# 🤝 Text Cutoff Debugging Collaboration Guide

## Overview
We're working together to solve a text cutoff issue in the lyric video generator. This guide provides a systematic approach to identify and fix the issue.

## 🎯 The Problem
- Text is being cut off at the bottom of the video frames
- Multiple positioning fixes haven't resolved the issue
- Need to identify exactly where in the pipeline the cutoff occurs

## 🛠️ Tools We've Created

### 1. **Video Generation Script** (`generate_video_clips.sh`)
Generates multiple video styles for your song:
```bash
# Update AUDIO and LYRICS paths in the script, then:
./generate_video_clips.sh
```
This creates various styles you can use despite the text cutoff issue.

### 2. **Visual Debugging Tool** (`debug_text_rendering.py`)
Creates detailed visualizations of text positioning:
```bash
python debug_text_rendering.py
# Check text_debug_output/ folder for results
```

### 3. **Interactive Debug Notebook** (`text_debugging_notebook.ipynb`)
Step-by-step debugging in Jupyter:
```bash
jupyter notebook text_debugging_notebook.ipynb
```

### 4. **Quick Test Script** (`test_text_cutoff.sh`)
Tests different font sizes to isolate the issue:
```bash
./test_text_cutoff.sh your_audio.mp3 your_lyrics.srt
```

## 🔍 Debugging Strategy

### Step 1: Run Quick Tests
```bash
# Test with different font sizes
./test_text_cutoff.sh your_audio.mp3 your_lyrics.srt

# Look for:
# - At what font size does cutoff start?
# - Does text-only mode have the same issue?
# - Do effects (neon, glow) make it worse?
```

### Step 2: Enable Debug Logging
```bash
# Run with debug logging
LOG_LEVEL=DEBUG create-lyric-video \
  --audio your_song.mp3 \
  --lyrics lyrics.srt \
  --font-size 96 \
  --start-time 0 --duration 10 \
  --output debug_test.mp4 2>&1 | tee debug_log.txt

# Search log for position calculations
grep -i "position\|height\|bottom" debug_log.txt
```

### Step 3: Visual Analysis
```bash
# Generate visual debug report
python debug_text_rendering.py

# Open the HTML report
open text_debug_output/debug_report.html
```

### Step 4: Test Specific Scenarios
```bash
# Test 1: Minimal text
echo -e "1\n00:00:00,000 --> 00:00:04,000\nTest" > minimal.srt
create-lyric-video --audio song.mp3 --lyrics minimal.srt --font-size 120 --output minimal_test.mp4

# Test 2: Letters that drop below baseline
echo -e "1\n00:00:00,000 --> 00:00:04,000\ngjpqy" > dropping.srt
create-lyric-video --audio song.mp3 --lyrics dropping.srt --font-size 96 --output dropping_test.mp4

# Test 3: Different positions
create-lyric-video --audio song.mp3 --lyrics lyrics.srt --font-size 72 --output test_top.mp4
# (Note: We need to add CLI support for vertical position)
```

## 🔧 Potential Fixes to Try

### 1. **Temporary Workaround**
While we debug, use smaller fonts:
```bash
create-lyric-video --audio song.mp3 --lyrics lyrics.srt --font-size 64 --output workaround.mp4
```

### 2. **Test Different Renderers**
```python
# In Python, test if it's PIL/font issue
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Test basic PIL rendering
img = Image.new('RGBA', (1920, 1080), (0,0,0,0))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 96)
draw.text((100, 800), "Test gjpqy", font=font, fill=(255,255,255))
np_img = np.array(img)
# Check if text is cut off in raw PIL render
```

### 3. **Add Debug Prints**
Add these to `renderer.py` temporarily:
```python
def render_lyric_line(self, ...):
    # After line 271
    print(f"DEBUG: Calculated y_pos={y_pos}, text_height={max_height}")
    print(f"DEBUG: Text bottom would be at {y_pos + max_height}")
    print(f"DEBUG: Screen height is {self.resolution[1]}")
```

## 📊 What to Look For

1. **In debug outputs:**
   - Does calculated Y position + text height exceed screen height?
   - Is text being clipped during compositing?
   - Are effects (glow, shadow) extending beyond calculated bounds?

2. **In test videos:**
   - Which font sizes work vs. fail?
   - Does the issue happen with all fonts or specific ones?
   - Is it worse with certain effects?

3. **In logs:**
   - Look for "clip", "bounds", "overflow" warnings
   - Check calculated positions vs. actual rendering

## 🚀 Next Steps Together

1. **Run the test suite** and share which tests show cutoff
2. **Check debug visualizations** - do they show text extending beyond screen?
3. **Try the notebook** - run each cell and see where issue appears
4. **Share findings** - Screenshots of cutoff, debug outputs, log snippets

## 💡 Quick Experiments

```bash
# Experiment 1: Force text higher
# (We'd need to modify the fixed position values in renderer.py)

# Experiment 2: Render without video encoding
# Generate raw frames to see if encoder is cropping

# Experiment 3: Different resolutions
create-lyric-video --audio song.mp3 --lyrics lyrics.srt --resolution 1280x720 --output test_720p.mp4
```

## 🎬 Meanwhile: Generate Your Videos!

Don't let the debugging stop you from creating:
```bash
# Run the full generation script
./generate_video_clips.sh

# Use smaller fonts that work
create-lyric-video --audio song.mp3 --lyrics lyrics.srt \
  --structure-file song_structure.json \
  --font-size 64 \
  --bespoke-style neon \
  --output final_video.mp4
```

---

## Let's Solve This Together! 🤝

This is exactly the kind of human-AI collaboration challenge that pushes the boundaries. By working together systematically, we'll not only fix this issue but also improve the debugging process for future problems.

**Your next steps:**
1. Run `./test_text_cutoff.sh` with your audio/lyrics
2. Share which font sizes show cutoff
3. Run the visual debugger and share any insights
4. Let's iterate on fixes together!

Remember: We have a week, so we can be thorough and systematic. Every debug step teaches us more about the system!
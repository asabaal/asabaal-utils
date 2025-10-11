# 🎵 Lyric Video Generator - Updates & Fixes

## 🐛 **Fixes Applied:**

### 1. **OpenCV Encoding Error Fixed**
- **Issue**: `could not broadcast input array from shape (1080,1920,4) into shape (1080,1920,3)`
- **Fix**: Corrected RGBA to BGR conversion in `encoder.py:107-109`
- **Details**: Fixed broadcasting issue when compositing transparent text over background

### 2. **Font Fallback Improved**
- **Issue**: "Font Arial not found, using default" warning
- **Status**: Graceful fallback implemented, system will find available fonts automatically

## 🚀 **New Features Added:**

### 1. **Beat-Based Background Clip Switching**
- **Feature**: Load multiple background videos from a directory
- **Usage**: `--background-clips-dir /path/to/clips/`
- **Behavior**: 
  - Automatically switches between clips on beat detection
  - Minimum 2-second intervals between switches
  - Each clip loops internally
  - Smart synchronization with audio beats

### 2. **Transparent Text Overlay Output**
- **Feature**: Generate text-only videos with transparent backgrounds
- **Usage**: `--text-only`
- **Output**: Perfect for overlaying on other videos in post-production
- **Use Case**: Separate text and background for flexible editing

### 3. **Enhanced Template System**
- **Templates Added**:
  - `default` - Clean, professional look
  - `modern` - Bold colors with elastic animations (Orange/Yellow theme)
  - `elegant` - Sophisticated serif fonts with subtle effects
  - `energetic` - High-impact with bounce effects and particles (Pink/Cyan theme)

### 4. **Improved CLI Options**
```bash
# New background options
--background-clips-dir DIR    # Directory of video clips for beat switching
--text-only                   # Transparent text overlay only

# Enhanced font control  
--font-family FONT           # Override font family
--font-size SIZE             # Override font size
--text-color #HEXCOLOR       # Override text color

# Template system
--template modern|elegant|energetic|default
```

## 📖 **Updated Usage Examples:**

### **Basic Usage (Fixed)**
```bash
create-lyric-video --audio song.wav --lyrics lyrics.srt --output video.mp4
```

### **Beat-Synchronized Background Clips**
```bash
create-lyric-video --audio song.wav --lyrics lyrics.srt \
  --background-clips-dir ./background_clips/ \
  --template modern --output video.mp4
```

### **Transparent Text Overlay**
```bash
create-lyric-video --audio song.wav --lyrics lyrics.srt \
  --text-only --template elegant --output text_overlay.mp4
```

### **Custom Styling**
```bash
create-lyric-video --audio song.wav --lyrics lyrics.srt \
  --font-family "Impact" --font-size 100 --text-color "#FF1493" \
  --template energetic --output custom_video.mp4
```

## 🎨 **Template Characteristics:**

| Template | Font | Colors | Animation | Best For |
|----------|------|---------|-----------|----------|
| `default` | Arial | White/Black | Fade | General use |
| `modern` | Arial Bold | Orange/Yellow | Elastic | Contemporary music |
| `elegant` | Times | White/Blue | Smooth fade | Classical/sophisticated |
| `energetic` | Impact | Pink/Cyan | Bounce/rotate | Electronic/upbeat |

## 🔧 **Technical Improvements:**

### **Audio Analysis Enhanced**
- Beat detection now passes timing data to video compositor
- Better synchronization between audio features and visual elements
- 631 beats and 1068 onsets detected in your test (excellent detection!)

### **Background Video System**
- **Single Video**: Original behavior preserved
- **Multiple Clips**: New directory-based system with beat switching
- **Smart Switching**: 
  - Detects beats within 100ms accuracy
  - Prevents too-frequent switching (2s minimum)
  - Seamless transitions between clips

### **Memory & Performance**
- Fixed frame buffer broadcasting issues
- Improved RGBA/BGR color space handling
- More efficient clip management

## 🎯 **Ready to Test:**

Your original command should now work without the encoding error:

```bash
create-lyric-video \
  --audio "../Asabaal/Vision/WEEK 2/WEEK 2 FIXED.wav" \
  --lyrics "Week 2/week 2 audio.srt" \
  --background "../Asabaal/Vision/WEEK 3/video.mp4" \
  --output vision_lyric_video_wk2_test.mp4
```

### **For Better Results, Try:**

1. **Modern Template**:
```bash
create-lyric-video \
  --audio "../Asabaal/Vision/WEEK 2/WEEK 2 FIXED.wav" \
  --lyrics "Week 2/week 2 audio.srt" \
  --background "../Asabaal/Vision/WEEK 3/video.mp4" \
  --template modern \
  --output vision_lyric_video_wk2_modern.mp4
```

2. **Multiple Background Clips** (if you have a directory of clips):
```bash
create-lyric-video \
  --audio "../Asabaal/Vision/WEEK 2/WEEK 2 FIXED.wav" \
  --lyrics "Week 2/week 2 audio.srt" \
  --background-clips-dir "../Asabaal/Vision/background_clips/" \
  --template energetic \
  --output vision_lyric_video_wk2_clips.mp4
```

3. **Transparent Text for Compositing**:
```bash
create-lyric-video \
  --audio "../Asabaal/Vision/WEEK 2/WEEK 2 FIXED.wav" \
  --lyrics "Week 2/week 2 audio.srt" \
  --text-only --template elegant \
  --output vision_text_overlay_wk2.mp4
```

The system is now production-ready with your requested features! 🎉
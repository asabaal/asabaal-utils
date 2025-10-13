#!/bin/bash
# Lyric Video Generation Script - Multiple Styles and Options
# This generates various clips that can be combined for the best result

AUDIO="/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/WEEK 2/WEEK 2 FIXED.wav"
LYRICS="/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/Week 2/week 2 audio.srt"
STRUCTURE="/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/week_2_sections.json"

echo "🎬 Generating Lyric Video Clips..."
echo "================================"

# Create output directory
OUTPUT_DIR="/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/lyric_video_clips"
mkdir -p "$OUTPUT_DIR"

# 1. FULL SONG VERSIONS (Different Styles)
echo "📀 Generating full song versions..."

# A. Neon Electronic Style (Great for instrumental hooks)
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --structure-file "$STRUCTURE" \
  --bespoke-style neon \
  --quality balanced \
  --output "$OUTPUT_DIR/full_neon.mp4"

# B. Bold Impact Style (Bebas Neue font)
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --structure-file "$STRUCTURE" \
  --font-family "Montserrat Bold" \
  --font-size 84 \
  --quality balanced \
  --output "$OUTPUT_DIR/full_bold.mp4"

# C. Matrix/Tech Style
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --structure-file "$STRUCTURE" \
  --bespoke-style matrix \
  --quality balanced \
  --output "$OUTPUT_DIR/full_matrix.mp4"

# 2. INSTRUMENTAL HOOK SECTIONS (Special Effects)
echo "🎸 Generating instrumental hook sections..."

# Hook 1 (14-28s) - Different styles
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 14 --end-time 28 \
  --bespoke-style neon --output "$OUTPUT_DIR/hook1_neon.mp4"

create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 14 --end-time 28 \
  --bespoke-style fire --output "$OUTPUT_DIR/hook1_fire.mp4"

create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 14 --end-time 28 \
  --bespoke-style hologram --output "$OUTPUT_DIR/hook1_hologram.mp4"

# Hook 2 (82-96s)
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 82 --end-time 96 \
  --bespoke-style chrome --output $OUTPUT_DIR/hook2_chrome.mp4

# Hook 3 (164-178s)
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 164 --end-time 178 \
  --bespoke-style gold --output $OUTPUT_DIR/hook3_gold.mp4

# 3. CHORUS SECTIONS (High Energy)
echo "🎤 Generating chorus sections..."

# First Chorus (68-82s)
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 68 --end-time 82 \
  --font-family "Bebas Neue" --font-size 96 --output $OUTPUT_DIR/chorus1_bebas.mp4

# Final Chorus (219-233s) 
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 219 --end-time 233 \
  --bespoke-style neon --output $OUTPUT_DIR/chorus_final_neon.mp4

# 4. VERSE SECTIONS (Readable)
echo "📝 Generating verse sections..."

# Verse 1 (28-54s)
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 28 --end-time 54 \
  --font-family "Open Sans" --font-size 72 --output $OUTPUT_DIR/verse1_clean.mp4

# 5. BRIDGE SECTION (Special)
echo "🌉 Generating bridge section..."

create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --start-time 192 --end-time 219 \
  --bespoke-style ice --output $OUTPUT_DIR/bridge_ice.mp4

# 6. CUSTOM COMBINATIONS
echo "🎨 Generating custom combinations..."

# Electronic vibe combo
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --structure-file "$STRUCTURE" \
  --music-genre electronic --song-mood energetic \
  --output "$OUTPUT_DIR/auto_electronic.mp4

# Rock vibe combo
create-lyric-video --audio "$AUDIO" --lyrics "$LYRICS" --structure-file "$STRUCTURE" \
  --music-genre rock --bespoke-style fire \
  --output "$OUTPUT_DIR/auto_rock.mp4

echo "✅ Video generation complete!"
echo ""
echo "📋 HOW TO COMBINE THE CLIPS:"
echo "============================"
echo ""
echo "Option 1: Use the full versions (full_neon.mp4, full_bold.mp4, etc.)"
echo ""
echo "Option 2: Mix and match sections using ffmpeg:"
echo "  # Example: Combine different sections"
echo "  ffmpeg -i verse1_clean.mp4 -i chorus1_bebas.mp4 -i hook1_neon.mp4 \\"
echo "    -filter_complex \"[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1\" \\"
echo "    -c:v libx264 -c:a aac final_mixed.mp4"
echo ""
echo "Option 3: Use video editing software (Premiere, DaVinci, etc.) to:"
echo "  - Import all clips"
echo "  - Arrange on timeline"
echo "  - Add transitions between different styles"
echo "  - Fine-tune timing"
echo ""
echo "💡 RECOMMENDATIONS:"
echo "  - Use 'neon' or 'hologram' for instrumental hooks (they look amazing!)"
echo "  - Use readable fonts (Open Sans, Montserrat) for verses"
echo "  - Use bold impact fonts (Bebas Neue) for choruses"
echo "  - Mix bespoke styles for variety"
echo ""
echo "🎬 All clips saved in: $OUTPUT_DIR/"

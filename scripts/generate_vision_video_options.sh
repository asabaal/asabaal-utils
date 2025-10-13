#!/bin/bash
# 🎬 Vision Week 2 - Lyric Video Options Generator
# Creates multiple style variations for maximum creative flexibility

# ===== CONFIGURATION =====
AUDIO="/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/WEEK 2/WEEK 2 FIXED.wav"
LYRICS="/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/Week 2/week 2 audio.srt"
BG_CLIPS="/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/WEEK 3/bg clips/"
OUTPUT_DIR="/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/vision_week2_video_options"

echo "🎬 VISION WEEK 2 - VIDEO OPTIONS GENERATOR"
echo "=========================================="
echo "Audio: $AUDIO"
echo "Lyrics: $LYRICS"  
echo "Background clips: $BG_CLIPS"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# ===== QUICK TEST FIRST =====
echo "🧪 Step 1: Quick test (first 15 seconds) to verify our fix works..."

create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --start-time 0 --duration 15 \
  --bespoke-style neon \
  --output "$OUTPUT_DIR/00_test_fix.mp4"

echo "✅ Test complete! Check $OUTPUT_DIR/00_test_fix.mp4 to verify text isn't cut off"
echo ""

# ===== STYLE SHOWCASE =====
echo "🎨 Step 2: Generating style showcase (30-second samples)..."

# Test all bespoke styles on a key section (30-60s)
declare -a styles=("neon" "fire" "ice" "gold" "chrome" "hologram" "matrix" "graffiti")

for style in "${styles[@]}"; do
    echo "  Creating $style style sample..."
    create-lyric-video \
      --audio "$AUDIO" \
      --lyrics "$LYRICS" \
      --start-time 30 --duration 30 \
      --bespoke-style "$style" \
      --output "$OUTPUT_DIR/01_style_${style}.mp4"
done

echo "✅ Style showcase complete!"
echo ""

# ===== FONT VARIATIONS =====
echo "📝 Step 3: Generating font variations..."

# Test different font approaches (same 30-60s section)
declare -a fonts=("Bebas Neue" "Montserrat Bold" "Open Sans" "Anton" "Righteous")

for font in "${fonts[@]}"; do
    safe_name=$(echo "$font" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
    echo "  Creating $font font sample..."
    create-lyric-video \
      --audio "$AUDIO" \
      --lyrics "$LYRICS" \
      --start-time 30 --duration 30 \
      --font-family "$font" \
      --font-size 84 \
      --output "$OUTPUT_DIR/02_font_${safe_name}.mp4"
done

echo "✅ Font variations complete!"
echo ""

# ===== BACKGROUND INTEGRATION =====
echo "🎞️ Step 4: Testing background clip integration..."

create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --start-time 60 --duration 30 \
  --background-clips-dir "$BG_CLIPS" \
  --bespoke-style neon \
  --output "$OUTPUT_DIR/03_with_backgrounds.mp4"

echo "✅ Background integration test complete!"
echo ""

# ===== FULL PRODUCTION OPTIONS =====
echo "🎬 Step 5: Creating full-length production options..."

# Option A: Neon Electronic (your original request)
echo "  Creating Option A: Neon Electronic..."
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --background-clips-dir "$BG_CLIPS" \
  --bespoke-style neon \
  --output "$OUTPUT_DIR/OPTION_A_neon_full.mp4" &

# Option B: High Impact Bold
echo "  Creating Option B: High Impact Bold..."
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --background-clips-dir "$BG_CLIPS" \
  --font-family "Bebas Neue" \
  --font-size 96 \
  --output "$OUTPUT_DIR/OPTION_B_bold_full.mp4" &

# Option C: Futuristic Matrix
echo "  Creating Option C: Futuristic Matrix..."
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --background-clips-dir "$BG_CLIPS" \
  --bespoke-style matrix \
  --output "$OUTPUT_DIR/OPTION_C_matrix_full.mp4" &

# Option D: Elegant Gold
echo "  Creating Option D: Elegant Gold..."
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --background-clips-dir "$BG_CLIPS" \
  --bespoke-style gold \
  --output "$OUTPUT_DIR/OPTION_D_gold_full.mp4" &

echo "  ⏳ Full videos generating in background..."
echo ""

# ===== CREATIVE SEGMENTS =====
echo "🎭 Step 6: Creating creative segment samples..."

# Hook sections with special effects (assuming instrumental parts)
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --start-time 90 --duration 20 \
  --bespoke-style hologram \
  --output "$OUTPUT_DIR/04_hook_hologram.mp4"

# Verse with clean readability
create-lyric-video \
  --audio "$AUDIO" \
  --lyrics "$LYRICS" \
  --start-time 120 --duration 30 \
  --font-family "Open Sans" \
  --font-size 72 \
  --output "$OUTPUT_DIR/04_verse_clean.mp4"

echo "✅ Creative segments complete!"
echo ""

# Wait for background processes to finish
echo "⏳ Waiting for full videos to complete..."
wait

echo ""
echo "🎉 ALL VIDEO OPTIONS GENERATED!"
echo "=============================="
echo ""
echo "📁 Check the output directory: $OUTPUT_DIR/"
echo ""
echo "🎬 WHAT YOU'VE GOT:"
echo "📋 Quick Reference Guide"
echo "----------------------"
echo ""
echo "🧪 TESTING:"
echo "   00_test_fix.mp4          - Verify our text cutoff fix worked"
echo ""
echo "🎨 STYLE SAMPLES (30s each):"
echo "   01_style_neon.mp4        - Electric blue glow effect"
echo "   01_style_fire.mp4        - Burning text effect" 
echo "   01_style_ice.mp4         - Cool crystalline effect"
echo "   01_style_gold.mp4        - Luxury metallic effect"
echo "   01_style_chrome.mp4      - Reflective metal effect"
echo "   01_style_hologram.mp4    - Sci-fi projection effect"
echo "   01_style_matrix.mp4      - Digital rain effect"
echo "   01_style_graffiti.mp4    - Street art effect"
echo ""
echo "📝 FONT SAMPLES (30s each):"
echo "   02_font_bebas_neue.mp4   - Bold impact font"
echo "   02_font_montserrat_bold.mp4 - Modern bold font"
echo "   02_font_open_sans.mp4    - Clean readable font"
echo "   02_font_anton.mp4        - Strong display font"
echo "   02_font_righteous.mp4    - Stylish display font"
echo ""
echo "🎞️ INTEGRATION TESTS:"
echo "   03_with_backgrounds.mp4  - Background clips integration"
echo ""
echo "🎬 FULL PRODUCTION OPTIONS:"
echo "   OPTION_A_neon_full.mp4   - Complete video with neon style"
echo "   OPTION_B_bold_full.mp4   - Complete video with bold fonts"
echo "   OPTION_C_matrix_full.mp4 - Complete video with matrix style"
echo "   OPTION_D_gold_full.mp4   - Complete video with gold style"
echo ""
echo "🎭 CREATIVE SEGMENTS:"
echo "   04_hook_hologram.mp4     - Special effect for instrumental"
echo "   04_verse_clean.mp4       - Clean readable for verses"
echo ""
echo "💡 CLAUDE'S RECOMMENDATIONS:"
echo "============================="
echo ""
echo "🏆 TOP PICK: Start with OPTION_A_neon_full.mp4"
echo "   ✨ Neon effects are stunning for electronic music"
echo "   ✨ Great contrast and readability"
echo "   ✨ Perfect for Vision's futuristic vibe"
echo ""
echo "🥈 BACKUP: OPTION_C_matrix_full.mp4"
echo "   ⚡ Matrix style fits tech/AI themes"
echo "   ⚡ Digital effects complement Vision concept"
echo ""
echo "🎯 FOR MIXING & MATCHING:"
echo "   • Use neon/hologram for high-energy sections"
echo "   • Use clean fonts (Open Sans) for storytelling parts"
echo "   • Use bold fonts (Bebas Neue) for impact moments"
echo "   • Mix gold/chrome for premium feel sections"
echo ""
echo "🛠️ POST-PRODUCTION TIPS:"
echo "   1. Preview all 30s samples first"
echo "   2. Pick your favorite style for the full version"
echo "   3. Use video editor to combine different segments if desired"
echo "   4. Add transitions between style changes"
echo "   5. Sync style changes to musical structure"
echo ""
echo "🚀 QUICK START:"
echo "   1. Watch 00_test_fix.mp4 - verify text looks good"
echo "   2. Browse style samples to find your favorite"
echo "   3. Check OPTION_A_neon_full.mp4 for the complete result"
echo "   4. Use that as your base, then enhance as needed!"
echo ""
echo "🎊 Ready to create something amazing! 🎊"

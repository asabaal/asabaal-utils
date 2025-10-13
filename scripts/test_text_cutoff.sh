#!/bin/bash
# Quick test script to diagnose text cutoff issue

echo "🔍 Text Cutoff Diagnostic Test"
echo "=============================="

# Test files
AUDIO="${1:-/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/WEEK 2/WEEK 2 FIXED.wav}"
LYRICS="${2:-/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/Week 2/week 2 audio.srt}"

# Create a simple test SRT if needed
if [ ! -f "$LYRICS" ]; then
    echo "Creating test SRT file..."
    cat > test_lyrics.srt << EOF
1
00:00:00,000 --> 00:00:04,000
Testing text positioning

2
00:00:04,000 --> 00:00:08,000
Letters that drop: g j p q y

3
00:00:08,000 --> 00:00:12,000
VERY LARGE TEXT TO TEST BOUNDS

4
00:00:12,000 --> 00:00:16,000
Bottom margin test line here
EOF
    LYRICS="test_lyrics.srt"
fi

echo ""
echo "Running text cutoff tests..."
echo ""

# Test 1: Small font (should work)
echo "Test 1: Small font (48px)"
create-lyric-video \
    --audio "$AUDIO" \
    --lyrics "$LYRICS" \
    --font-size 48 \
    --start-time 0 --duration 4 \
    --quality fast \
    --output "mnt/d/Work/Asabaal Ventures/The Great Reconciliation/test_cutoff_48px.mp4"

# Test 2: Medium font 
echo -e "\nTest 2: Medium font (72px)"
create-lyric-video \
    --audio "$AUDIO" \
    --lyrics "$LYRICS" \
    --font-size 72 \
    --start-time 0 --duration 4 \
    --quality fast \
    --output "mnt/d/Work/Asabaal Ventures/The Great Reconciliation/test_cutoff_72px.mp4"

# Test 3: Large font (likely to show issue)
echo -e "\nTest 3: Large font (96px)"
create-lyric-video \
    --audio "$AUDIO" \
    --lyrics "$LYRICS" \
    --font-size 96 \
    --start-time 0 --duration 4 \
    --quality fast \
    --output "/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/test_cutoff_96px.mp4"

# Test 4: Very large font
echo -e "\nTest 4: Very large font (120px)"
create-lyric-video \
    --audio "$AUDIO" \
    --lyrics "$LYRICS" \
    --font-size 120 \
    --start-time 0 --duration 4 \
    --quality fast \
    --output test_cutoff_120px.mp4

# Test 5: With effects that might extend bounds
echo -e "\nTest 5: With glow effect"
create-lyric-video \
    --audio "$AUDIO" \
    --lyrics "$LYRICS" \
    --font-size 72 \
    --bespoke-style neon \
    --start-time 0 --duration 4 \
    --quality fast \
    --output "/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/test_cutoff_neon.mp4"

# Test 6: Text-only mode (isolate from compositor)
echo -e "\nTest 6: Text-only mode"
create-lyric-video \
    --audio "$AUDIO" \
    --lyrics "$LYRICS" \
    --font-size 96 \
    --text-only \
    --start-time 0 --duration 4 \
    --quality fast \
    --output "/mnt/d/Work/Asabaal Ventures/The Great Reconciliation/test_cutoff_textonly.mp4"

echo -e "\n✅ Tests complete!"
echo ""
echo "🔍 Check these videos to see where cutoff starts:"
echo "  - test_cutoff_48px.mp4   (should be OK)"
echo "  - test_cutoff_72px.mp4   (might show issue)"
echo "  - test_cutoff_96px.mp4   (likely shows issue)"
echo "  - test_cutoff_120px.mp4  (definitely shows issue?)"
echo "  - test_cutoff_neon.mp4   (effects might cause issue)"
echo "  - test_cutoff_textonly.mp4 (isolates text rendering)"
echo ""
echo "💡 If text-only mode works but others don't, issue is in compositing"
echo "💡 If all show cutoff, issue is in text positioning calculation"

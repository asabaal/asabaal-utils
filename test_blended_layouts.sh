#!/bin/bash

# Test script for blended layout generation
# This version can be run from the utils repo

echo "Testing blended layout generation..."

# Check if the tools are available
if ! command -v gradient-blend &> /dev/null; then
    echo "Error: gradient-blend tool not found. Make sure it's installed."
    exit 1
fi

if ! command -v auto-layout &> /dev/null; then
    echo "Error: auto-layout tool not found. Make sure it's installed."
    exit 1
fi

# Test directory
TEST_DIR="/home/asabaal/Projects/the_ai_series/psalms"

if [ ! -d "$TEST_DIR" ]; then
    echo "Error: Test directory $TEST_DIR not found"
    exit 1
fi

cd "$TEST_DIR"

# Check if required files exist
if [ ! -f "book_of_life_psalms.png" ] || [ ! -f "The AI Series(2).png" ]; then
    echo "Error: Source images not found in $TEST_DIR"
    exit 1
fi

if [ ! -f "layout_config.json" ]; then
    echo "Error: layout_config.json not found in $TEST_DIR"
    exit 1
fi

# 16:9 (1920x1080)
echo "Creating 16:9 layout..."
gradient-blend "book_of_life_psalms.png" "The AI Series(2).png" blended_16x9.png --width 1920 --overlap 0.25
auto-layout blended_16x9.png --layers "asabaal.png" "PSALMS.png" "the_ai_series_text.png" --fixed "0:TC;1:BL;2:BR" --config layout_config.json --outdir . --basename final_16x9

# 9:16 (1080x1920)
echo "Creating 9:16 layout..."
gradient-blend "book_of_life_psalms.png" "The AI Series(2).png" blended_9x16.png --width 1080 --overlap 0.25
auto-layout blended_9x16.png --layers "asabaal.png" "PSALMS.png" "the_ai_series_text.png" --fixed "0:TC;1:BL;2:BR" --config layout_config.json --outdir . --basename final_9x16

# 1:1 (1024x1024)
echo "Creating 1:1 layout..."
gradient-blend "book_of_life_psalms.png" "The AI Series(2).png" blended_1x1.png --width 1024 --overlap 0.25
auto-layout blended_1x1.png --layers "asabaal.png" "PSALMS.png" "the_ai_series_text.png" --fixed "0:TC;1:BL;2:BR" --config layout_config.json --outdir . --basename final_1x1

# 4:5 (1080x1350)
echo "Creating 4:5 layout..."
gradient-blend "book_of_life_psalms.png" "The AI Series(2).png" blended_4x5.png --width 1080 --overlap 0.25
auto-layout blended_4x5.png --layers "asabaal.png" "PSALMS.png" "the_ai_series_text.png" --fixed "0:TC;1:BL;2:BR" --config layout_config.json --outdir . --basename final_4x5

# 5:4 (1350x1080)
echo "Creating 5:4 layout..."
gradient-blend "book_of_life_psalms.png" "The AI Series(2).png" blended_5x4.png --width 1350 --overlap 0.25
auto-layout blended_5x4.png --layers "asabaal.png" "PSALMS.png" "the_ai_series_text.png" --fixed "0:TC;1:BL;2:BR" --config layout_config.json --outdir . --basename final_5x4

echo "Done! Generated files:"
echo "- final_16x9.png"
echo "- final_9x16.png" 
echo "- final_1x1.png"
echo "- final_4x5.png"
echo "- final_5x4.png"
echo "All files saved in $TEST_DIR"
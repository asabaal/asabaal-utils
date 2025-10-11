#!/bin/bash

# Generate all resized variants with logos using smart_fit + auto-layout
# Usage: ./generate_all_resized.sh

echo "Generating all resized variants with logos..."

INPUT_DIR="/home/asabaal/Projects/the_ai_series/psalms"
BASE_IMAGE="$INPUT_DIR/blended.png"
CONFIG_FILE="$INPUT_DIR/layout_config.json"

# Check if files exist
if [ ! -f "$BASE_IMAGE" ]; then
    echo "Error: Base image $BASE_IMAGE not found"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file $CONFIG_FILE not found"
    exit 1
fi

cd "$INPUT_DIR"

# Define target resolutions
declare -A resolutions=(
    ["16x9"]="1920 1080"
    ["9x16"]="1080 1920" 
    ["1x1"]="1024 1024"
    ["4x5"]="1080 1350"
    ["5x4"]="1350 1080"
)

for aspect in "${!resolutions[@]}"; do
    resolution=${resolutions[$aspect]}
    width=$(echo $resolution | cut -d' ' -f1)
    height=$(echo $resolution | cut -d' ' -f2)
    
    echo "Processing $aspect (${width}x${height})..."
    
    # Step 1: Resize the blended image to target resolution
    resized_base="resized_${aspect}.png"
    python /home/asabaal/repos/asabaal-utils/src/asabaal_utils/image_processing/smart_fit.py \
        "$BASE_IMAGE" "$resized_base" \
        --width "$width" --height "$height" \
        --max-stretch 0.05 --gravity center
    
    # Step 2: Apply logos to the resized image
    auto-layout "$resized_base" \
        --layers "asabaal.png" "the_ai_series_text.png" "PSALMS.png" \
        --fixed "0:TC;1:BL;2:BR" \
        --config "$CONFIG_FILE" \
        --outdir . \
        --basename "final_${aspect}"
    
    echo "Created final_${aspect}.png"
done

echo ""
echo "Done! Generated files:"
for aspect in "${!resolutions[@]}"; do
    echo "- final_${aspect}.png"
done
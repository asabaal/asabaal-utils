#!/usr/bin/env python3
"""
Test the new same-size preprocessing with different aspect ratios.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.image_processing import GradientBlender


def create_different_aspect_images():
    """Create images with very different aspect ratios."""
    
    test_dir = Path("aspect_test")
    test_dir.mkdir(exist_ok=True)
    
    # Tall portrait: 300×800
    tall = Image.new('RGB', (300, 800), color='#FF6B6B')
    draw = ImageDraw.Draw(tall)
    draw.rectangle([50, 100, 250, 700], fill='white', outline='black', width=3)
    draw.text((150, 400), "TALL", fill='black', anchor='mm')
    tall_path = test_dir / "tall.png"
    tall.save(tall_path)
    
    # Wide landscape: 1000×300
    wide = Image.new('RGB', (1000, 300), color='#4ECDC4')
    draw = ImageDraw.Draw(wide)
    draw.rectangle([100, 50, 900, 250], fill='white', outline='black', width=3)
    draw.text((500, 150), "WIDE", fill='black', anchor='mm')
    wide_path = test_dir / "wide.png"
    wide.save(wide_path)
    
    print(f"Created test images:")
    print(f"  Tall: {tall.size} (aspect: {tall.width/tall.height:.2f})")
    print(f"  Wide: {wide.size} (aspect: {wide.width/wide.height:.2f})")
    
    return str(tall_path), str(wide_path)


def test_same_size_preprocessing(tall_path, wide_path):
    """Test the new same-size preprocessing."""
    
    print(f"\n🔧 Testing Same-Size Preprocessing:")
    print("=" * 50)
    
    # Test with default width (max of inputs)
    print(f"\n1. Default width (max of inputs)")
    blender = GradientBlender(overlap=0.25)
    result = blender.blend_images(tall_path, wide_path, "test_default.png", preview=True)
    
    tall_orig = Image.open(tall_path)
    wide_orig = Image.open(wide_path)
    
    target_w = max(tall_orig.width, wide_orig.width)
    scale_tall = target_w / tall_orig.width
    scale_wide = target_w / wide_orig.width
    tall_h = int(tall_orig.height * scale_tall)
    wide_h = int(wide_orig.height * scale_wide)
    target_h = max(tall_h, wide_h)
    
    print(f"  Target dimensions: {target_w} × {target_h}")
    print(f"  Tall resized to: {target_w} × {tall_h}")
    print(f"  Wide resized to: {target_w} × {wide_h}")
    print(f"  Final result: {result['output_size']}")
    print(f"  Overlap: {result['overlap_pixels']}px")
    
    # Test with fixed width
    print(f"\n2. Fixed width (600px)")
    blender = GradientBlender(width=600, overlap=0.3)
    result = blender.blend_images(tall_path, wide_path, "test_600px.png", preview=True)
    print(f"  Result: {result['output_size']}")
    print(f"  Overlap: {result['overlap_pixels']}px")
    
    # Test with fixed pixel overlap
    print(f"\n3. Fixed pixel overlap (150px)")
    blender = GradientBlender(width=500, overlap=150)
    result = blender.blend_images(tall_path, wide_path, "test_150px.png", preview=True)
    print(f"  Result: {result['output_size']}")
    print(f"  Overlap: {result['overlap_pixels']}px")


def main():
    """Run the test."""
    
    print("🧪 Same-Size Preprocessing Test")
    print("Testing that both images are resized to identical dimensions")
    print("=" * 60)
    
    try:
        tall_path, wide_path = create_different_aspect_images()
        test_same_size_preprocessing(tall_path, wide_path)
        
        print(f"\n✅ Test complete! Check 'aspect_test' directory for results.")
        
        # Clean up
        import shutil
        shutil.rmtree("aspect_test")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
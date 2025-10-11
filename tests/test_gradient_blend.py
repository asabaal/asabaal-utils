#!/usr/bin/env python3
"""
Test script for gradient blending functionality.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asabaal_utils.image_processing.gradient_blend import GradientBlender, blend_images
from PIL import Image


def create_test_images():
    """Create simple test images for testing."""
    # Create simple test images using existing test images if available
    test_dir = Path(__file__).parent / "test_data" / "gradient_blend_test"
    top_path = test_dir / "The AI Series(2).png"
    bottom_path = test_dir / "book_of_life_psalms.png"
    
    if top_path.exists() and bottom_path.exists():
        return Image.open(top_path), Image.open(bottom_path)
    
    # Fallback: create simple images
    top_img = Image.new('RGB', (100, 100))
    bottom_img = Image.new('RGB', (100, 100))
    return top_img, bottom_img


def test_gradient_blender_class():
    """Test the GradientBlender class."""
    print("Testing GradientBlender class...")
    
    # Create test images
    top_img, bottom_img = create_test_images()
    
    # Save temporary images
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as top_file:
        top_img.save(top_file.name)
        top_path = top_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as bottom_file:
        bottom_img.save(bottom_file.name)
        bottom_path = bottom_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Test basic blending
        blender = GradientBlender(overlap=0.25, ease='cosine')
        result = blender.blend_images(top_path, bottom_path, output_path)
        
        # Verify output
        assert os.path.exists(output_path), "Output file was not created"
        assert result['output_size'][0] > 0, "Output width should be positive"
        assert result['output_size'][1] > 0, "Output height should be positive"
        assert result['overlap_pixels'] > 0, "Overlap should be positive"
        
        # Load and verify output image
        output_img = Image.open(output_path)
        assert output_img.size[0] == result['output_size'][0], "Output size mismatch"
        assert output_img.size[1] == result['output_size'][1], "Output size mismatch"
        
        print("✓ GradientBlender class test passed")
        print(f"  Output size: {result['output_size']}")
        print(f"  Overlap pixels: {result['overlap_pixels']}")
        
    finally:
        # Clean up temporary files
        for path in [top_path, bottom_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_convenience_function():
    """Test the convenience function."""
    print("\nTesting convenience function...")
    
    # Create test images
    top_img, bottom_img = create_test_images()
    
    # Save temporary images
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as top_file:
        top_img.save(top_file.name)
        top_path = top_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as bottom_file:
        bottom_img.save(bottom_file.name)
        bottom_path = bottom_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Test convenience function
        result = blend_images(top_path, bottom_path, output_path, 
                            overlap=0.3, ease='linear', out_height=500)
        
        # Verify output
        assert os.path.exists(output_path), "Output file was not created"
        assert result['final_height'] == 500, "Final height should match requested"
        
        print("✓ Convenience function test passed")
        print(f"  Final height: {result['final_height']}")
        
    finally:
        # Clean up temporary files
        for path in [top_path, bottom_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_real_images():
    """Test with the real images provided."""
    print("\nTesting with real images...")
    
    # Paths to real test images
    test_dir = Path(__file__).parent / "test_data" / "gradient_blend_test"
    top_path = test_dir / "The AI Series(2).png"
    bottom_path = test_dir / "book_of_life_psalms.png"
    output_path = test_dir / "test_real_blend.png"
    
    if not top_path.exists() or not bottom_path.exists():
        print("⚠ Real test images not found, skipping real image test")
        return
    
    try:
        # Test with real images
        blender = GradientBlender(
            width=800,  # Normalize to 800px width
            overlap=0.25,
            ease='cosine',
            out_height=1200,
            pad=True
        )
        
        result = blender.blend_images(str(top_path), str(bottom_path), str(output_path))
        
        # Verify output
        assert os.path.exists(output_path), "Output file was not created"
        assert result['output_size'][0] == 800, "Output width should be 800"
        assert result['output_size'][1] == 1200, "Output height should be 1200"
        
        print("✓ Real image test passed")
        print(f"  Output size: {result['output_size']}")
        print(f"  Original top size: {result['top_original_size']}")
        print(f"  Original bottom size: {result['bottom_original_size']}")
        
    except Exception as e:
        print(f"✗ Real image test failed: {e}")
        raise


def main():
    """Run all tests."""
    print("Running gradient blend tests...\n")
    
    try:
        test_gradient_blender_class()
        test_convenience_function()
        test_real_images()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
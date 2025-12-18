#!/usr/bin/env python3
"""
Simple test invocation for DocumentPhotoOCR
Verifies the updated document photo OCR functionality
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path and import directly
sys.path.insert(0, str(Path(__file__).parent))

from image_processing.ocr import DocumentPhotoOCR, OCRFactory

def test_document_ocr():
    """Test the DocumentPhotoOCR processor"""
    print("🧪 Testing DocumentPhotoOCR...")
    
    # Create processor
    processor = DocumentPhotoOCR(output_dir="test_document_output")
    
    # Check OCR availability
    if not processor.check_ocr_availability():
        print("❌ Tesseract OCR not available!")
        print("   Install with: sudo apt install tesseract-ocr")
        return False
    
    print("✅ OCR engine available")
    
    # Look for test images in parent directory
    parent_dir = Path(__file__).parent.parent.parent
    test_patterns = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    test_images = []
    
    for pattern in test_patterns:
        test_images.extend(list(parent_dir.glob(pattern)))
    
    # If no images found, create a simple test
    if not test_images:
        print("⚠️  No test images found. Creating a simple text image for testing...")
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple test document image
            img = Image.new('RGB', (600, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            # Simple text layout
            text = """This is a test document.

It contains multiple paragraphs to test the OCR functionality.

The DocumentPhotoOCR processor should extract this text faithfully while preserving paragraph structure.

This test verifies that the implementation works correctly for photographed documents."""
            
            try:
                # Try to use a system font
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Draw text
            y_offset = 50
            for line in text.split('\n'):
                draw.text((50, y_offset), line, fill='black', font=font)
                y_offset += 30
            
            # Save test image in parent directory
            test_img_path = parent_dir / "test_document.jpg"
            img.save(test_img_path, "JPEG")
            test_images = [test_img_path]
            print(f"✅ Created test image: {test_img_path}")
            
        except ImportError:
            print("❌ PIL/Pillow not available for creating test image")
            print("   Install with: pip install Pillow")
            return False
        except Exception as e:
            print(f"❌ Failed to create test image: {e}")
            return False
    
    # Test processing
    print(f"📄 Processing {len(test_images)} test image(s)...")
    
    results = []
    for img_path in test_images:
        print(f"   Processing: {img_path.name}")
        
        try:
            result = processor.process_single_item(img_path)
            results.append(result)
            
            print(f"   ✅ Extracted {result['text_length']} characters")
            print(f"   📝 {result.get('paragraph_count', 0)} paragraphs detected")
            
            # Show preview
            preview = result['extracted_text'][:100] + "..." if len(result['extracted_text']) > 100 else result['extracted_text']
            print(f"   Preview: {preview}")
            
        except Exception as e:
            print(f"   ❌ Error processing {img_path.name}: {e}")
    
    # Save results
    if results:
        try:
            processor.save_results(results)
            print(f"✅ Results saved to: {processor.output_dir}")
            
            # Show generated files
            output_files = list(processor.output_dir.glob("*"))
            if output_files:
                print("📁 Generated files:")
                for f in output_files:
                    print(f"   📄 {f.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return False
    
    print("⚠️  No results to save")
    return False

def test_cli_integration():
    """Test that the CLI can access the DocumentPhotoOCR"""
    print("\n🔧 Testing CLI integration...")
    
    try:
        # Import the factory to test document processor creation
        from asabaal_utils.image_processing.ocr import OCRFactory
        
        # Try to create document processor
        processor = OCRFactory.create_processor('document')
        
        if isinstance(processor, DocumentPhotoOCR):
            print("✅ Document OCR processor available via factory")
            return True
        else:
            print("❌ Factory did not return DocumentPhotoOCR instance")
            return False
            
    except Exception as e:
        print(f"❌ Factory integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Document Photo OCR Test Suite")
    print("=" * 40)
    
    # Run tests
    test_passed = test_document_ocr()
    cli_test_passed = test_cli_integration()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST SUMMARY")
    print("=" * 40)
    print(f"Document OCR Processing: {'✅ PASS' if test_passed else '❌ FAIL'}")
    print(f"Factory Integration: {'✅ PASS' if cli_test_passed else '❌ FAIL'}")
    
    if test_passed and cli_test_passed:
        print("\n🎉 All tests passed! Document Photo OCR is ready to use.")
        print("\nUsage examples:")
        print("  python -m asabaal_utils.image_processing.ocr_cli document photo.jpg")
        print("  python -m asabaal_utils.image_processing.ocr_cli document ./documents/")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
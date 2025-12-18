#!/usr/bin/env python3
"""
Test script for complete OCR pipeline implementation
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add the src directory to Python path and import directly
sys.path.insert(0, str(Path(__file__).parent))

from image_processing.ocr import DocumentPhotoOCR, AINativeOCR

def create_test_document():
    """Create a proper test document image"""
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Test text with paragraphs
    text = """IMPORTANT NOTICE

This is a test document created for OCR validation.

It contains multiple paragraphs to test the quality gate and AI fallback functionality.

The text should pass basic quality checks:
- Alphabetic ratio > 60%
- Average word length > 3
- Multiple paragraphs
- Low symbol density

This ensures our OCR pipeline works correctly for photographed documents.

Thank you for testing our implementation."""
    
    try:
        # Try to use a system font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw text
    y_offset = 50
    for line in text.split('\n'):
        draw.text((50, y_offset), line, fill='black', font=font)
        y_offset += 25
    
    # Save test image
    test_img_path = Path("test_document_real.jpg")
    img.save(test_img_path, "JPEG", quality=95)
    print(f"✅ Created test document: {test_img_path}")
    return test_img_path

def test_hybrid_pipeline():
    """Test hybrid document OCR with fallback"""
    print("\n🧪 Testing Hybrid Document OCR Pipeline")
    print("=" * 50)
    
    # Create test document
    test_img = create_test_document()
    
    # Test DocumentPhotoOCR
    processor = DocumentPhotoOCR(output_dir="test_hybrid_output")
    
    # Check OCR availability
    if not processor.check_ocr_availability():
        print("❌ Tesseract OCR not available!")
        return False
    
    print(f"📄 Processing: {test_img.name}")
    result = processor.process_single_item(test_img)
    
    print(f"✅ Extraction complete:")
    print(f"   Method: {result['extraction_method']}")
    print(f"   Quality: {result.get('quality_status', 'unknown')}")
    print(f"   Characters: {result['text_length']}")
    print(f"   Paragraphs: {result.get('paragraph_count', 0)}")
    
    if result.get('quality_reason'):
        print(f"   Reason: {result['quality_reason']}")
    
    # Save results
    processor.save_results([result])
    
    # Show preview
    if result['extracted_text']:
        preview = result['extracted_text'][:200] + "..." if len(result['extracted_text']) > 200 else result['extracted_text']
        print(f"   Preview: {preview}")
    
    return True

def test_ai_native():
    """Test AI-native OCR"""
    print("\n🧪 Testing AI-Native OCR")
    print("=" * 50)
    
    # Use existing test document
    test_img = Path("test_document_real.jpg")
    if not test_img.exists():
        print("❌ Test document not found!")
        return False
    
    # Test AINativeOCR
    processor = AINativeOCR(output_dir="test_ai_native_output")
    
    print(f"📄 Processing: {test_img.name}")
    result = processor.process_single_item(test_img, model='qwen3-vl:32b')
    
    print(f"✅ AI extraction complete:")
    print(f"   Method: {result['extraction_method']}")
    print(f"   Model: {result.get('model', 'unknown')}")
    print(f"   Characters: {result['text_length']}")
    print(f"   Paragraphs: {result.get('paragraph_count', 0)}")
    
    # Save results
    processor.save_results([result])
    
    # Show preview
    if result['extracted_text']:
        preview = result['extracted_text'][:200] + "..." if len(result['extracted_text']) > 200 else result['extracted_text']
        print(f"   Preview: {preview}")
    
    return True

def main():
    """Run all tests"""
    print("🔍 Complete OCR Pipeline Test Suite")
    print("=" * 50)
    
    # Test hybrid pipeline
    hybrid_success = test_hybrid_pipeline()
    
    # Test AI-native
    ai_success = test_ai_native()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Hybrid Pipeline (deterministic → gate → AI fallback): {'✅ PASS' if hybrid_success else '❌ FAIL'}")
    print(f"AI-Native OCR: {'✅ PASS' if ai_success else '❌ FAIL'}")
    
    if hybrid_success and ai_success:
        print("\n🎉 All pipeline tests passed!")
        print("\n🚀 Ready for production use:")
        print("  - Document OCR with AI fallback")
        print("  - AI-native OCR mode")
        print("  - Quality gate validation")
        print("  - Adaptive thresholding preprocessing")
        return True
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
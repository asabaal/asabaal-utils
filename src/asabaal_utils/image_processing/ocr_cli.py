#!/usr/bin/env python3
"""
OCR Command Line Interface
A user-friendly CLI for the modular OCR system
"""
# description: Modular OCR tool for extracting text from images and PDFs
# version: 1.0.0
# category: utility
# usage: ocr [mobile|pdf] <input_path> [options]

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path to allow importing the OCR module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from asabaal_utils.image_processing.ocr import OCRFactory


def check_dependencies():
    """Check if required dependencies are available."""
    issues = []
    
    # Check for Tesseract
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        issues.append("❌ Tesseract OCR not installed. Install with: sudo apt install tesseract-ocr")
    
    # Check for PyMuPDF (only for PDF processing)
    try:
        import fitz
    except ImportError:
        issues.append("⚠️  PyMuPDF not installed (required for PDF processing). Install with: pip install PyMuPDF")
    
    return issues


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Modular OCR System - Extract text from images and PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ocr mobile ./screenshots          # Process mobile screenshots in directory
  ocr pdf book.pdf                  # Extract text from PDF
  ocr mobile screenshot.jpg         # Process single screenshot
  ocr pdf ./books --output ./text  # Process PDFs with custom output dir
        """
    )
    
    # Main arguments
    parser.add_argument(
        "type",
        choices=["mobile", "pdf"],
        help="Type of OCR processing: 'mobile' for screenshots, 'pdf' for books/documents"
    )
    
    parser.add_argument(
        "input_path",
        help="Input file or directory path"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output-dir",
        help="Output directory for results (default: auto-generated based on type)"
    )
    
    parser.add_argument(
        "--language",
        default="eng",
        help="OCR language code (default: eng). Examples: eng, spa, fra, deu"
    )
    
    parser.add_argument(
        "--pattern",
        default=None,
        help="File pattern for batch processing (default: *.jpg for mobile, *.pdf for pdf)"
    )
    
    parser.add_argument(
        "--enhance",
        choices=["light", "moderate", "aggressive"],
        default="moderate",
        help="Image enhancement level (default: moderate)"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies and exit"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    # Check if --check-deps is in args before full parsing
    if "--check-deps" in sys.argv:
        issues = check_dependencies()
        if issues:
            print("Dependency Check Results:")
            for issue in issues:
                print(f"  {issue}")
            sys.exit(1)
        else:
            print("✅ All dependencies are installed!")
            sys.exit(0)
    
    args = parser.parse_args()
    
    # Check dependencies if requested (redundant but kept for completeness)
    if args.check_deps:
        issues = check_dependencies()
        if issues:
            print("Dependency Check Results:")
            for issue in issues:
                print(f"  {issue}")
            sys.exit(1)
        else:
            print("✅ All dependencies are installed!")
            sys.exit(0)
    
    # Check basic dependencies before processing
    issues = check_dependencies()
    critical_issues = [i for i in issues if i.startswith("❌")]
    if critical_issues:
        print("Critical dependency issues found:")
        for issue in critical_issues:
            print(f"  {issue}")
        print("\nRun 'ocr --check-deps' for full dependency check.")
        sys.exit(1)
    
    try:
        # Create OCR processor
        processor = OCRFactory.create_processor(args.type, args.output_dir)
        
        # Check OCR availability
        if not processor.check_ocr_availability():
            print("❌ OCR engine not available! Please install Tesseract OCR.")
            print("   Ubuntu/Debian: sudo apt install tesseract-ocr")
            print("   macOS: brew install tesseract")
            print("   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
            sys.exit(1)
        
        # Process input
        input_path = Path(args.input_path)
        
        if not input_path.exists():
            print(f"❌ Error: Input path '{input_path}' does not exist")
            sys.exit(1)
        
        if args.verbose:
            print(f"🔍 Processing {args.type} OCR on: {input_path}")
            print(f"📁 Output directory: {processor.output_dir}")
        
        if input_path.is_file():
            # Process single file
            if args.verbose:
                print(f"📄 Processing single file: {input_path.name}")
            
            result = processor.process_single_item(input_path)
            processor.save_results([result])
            
            # Print summary for single file
            if args.type == "mobile":
                print(f"\n✅ Extracted {len(result['chat_titles'])} chat titles from {input_path.name}")
                if args.verbose and result['chat_titles']:
                    print("\nExtracted titles:")
                    for title in result['chat_titles'][:5]:
                        print(f"  • {title}")
                    if len(result['chat_titles']) > 5:
                        print(f"  ... and {len(result['chat_titles']) - 5} more")
            else:  # pdf
                print(f"\n✅ Extracted text from {result['total_pages']} pages")
                if 'error' not in result:
                    print(f"   Direct text pages: {len(result['text_pages'])}")
                    print(f"   OCR pages: {len(result['ocr_pages'])}")
        
        else:
            # Process directory
            if args.type == "mobile":
                pattern = args.pattern or "*.jpg"
                if args.verbose:
                    print(f"🔍 Scanning for {pattern} files...")
                results = processor.batch_process_images(str(input_path), pattern)
            else:  # pdf
                pattern = args.pattern or "*.pdf"
                if args.verbose:
                    print(f"🔍 Scanning for {pattern} files...")
                results = processor.batch_process_images(str(input_path), pattern)
            
            if results:
                processor.save_results(results)
                
                # Print summary
                if args.type == "mobile":
                    total_titles = sum(r['title_count'] for r in results)
                    print(f"\n✅ Processed {len(results)} images")
                    print(f"   Total chat titles extracted: {total_titles}")
                else:  # pdf
                    total_pages = sum(r.get('total_pages', 0) for r in results)
                    print(f"\n✅ Processed {len(results)} PDFs")
                    print(f"   Total pages processed: {total_pages}")
            else:
                print("⚠️  No files found to process")
        
        # Show output location
        print(f"\n📁 Results saved to: {processor.output_dir}")
        
        # List output files
        output_files = list(processor.output_dir.glob("*"))
        if output_files and args.verbose:
            print("\nGenerated files:")
            for f in output_files:
                print(f"  📄 {f.name}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    print("\n✨ OCR processing complete!")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Modular OCR System
Base classes and utilities for different OCR use cases
"""

import os
import sys
import re
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from typing import Dict, List, Optional, Union
import json
import csv
from datetime import datetime


class BaseOCRProcessor(ABC):
    """
    Base class for all OCR processors
    Contains shared functionality for image processing and OCR execution
    """
    
    def __init__(self, output_dir: str = "ocr_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.ocr_config = self._get_default_ocr_config()
    
    def _get_default_ocr_config(self) -> str:
        """Default OCR configuration - can be overridden by subclasses"""
        return r'--oem 3 --psm 6'
    
    def enhance_image(self, image: Image.Image, enhancement_level: str = "moderate") -> Image.Image:
        """
        Enhance image quality for better OCR results
        
        Args:
            image: Input PIL Image
            enhancement_level: 'light', 'moderate', 'aggressive'
        
        Returns:
            Enhanced PIL Image
        """
        # Convert to grayscale if needed
        if image.mode != 'L':
            image = image.convert('L')
        
        if enhancement_level == "light":
            # Minimal enhancement for clean images
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
        elif enhancement_level == "moderate":
            # Standard enhancement for most use cases
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
        elif enhancement_level == "aggressive":
            # Heavy enhancement for poor quality images
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.5)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    def extract_text_from_image(self, image: Union[Path, Image.Image], 
                               language: str = 'eng', 
                               enhance: bool = True,
                               enhancement_level: str = "moderate") -> str:
        """
        Extract text from image using OCR
        
        Args:
            image: Path to image file or PIL Image object
            language: OCR language code
            enhance: Whether to enhance image before OCR
            enhancement_level: Level of image enhancement
        
        Returns:
            Extracted text
        """
        try:
            # Load image if path provided
            if isinstance(image, (str, Path)):
                image = Image.open(image)
            
            # Enhance image if requested
            if enhance:
                image = self.enhance_image(image, enhancement_level)
            
            # Configure OCR with language
            config = f"{self.ocr_config} -l {language}"
            
            # Extract text
            text = pytesseract.image_to_string(image, config=config)
            
            # Basic cleanup
            text = self._basic_text_cleanup(text)
            
            return text
            
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def _basic_text_cleanup(self, text: str) -> str:
        """Basic text cleanup - common to all OCR tasks"""
        text = text.strip()
        text = re.sub(r'\n+', '\n', text)  # Remove multiple newlines
        text = re.sub(r'\s+', ' ', text)   # Normalize whitespace
        return text
    
    def batch_process_images(self, image_directory: str, 
                           file_pattern: str = "*.jpg",
                           **kwargs) -> List[Dict]:
        """
        Process multiple images in a directory
        
        Args:
            image_directory: Directory containing images
            file_pattern: File pattern to match
            **kwargs: Additional arguments for processing
        
        Returns:
            List of processing results
        """
        image_dir = Path(image_directory)
        image_files = list(image_dir.glob(file_pattern))
        
        if not image_files:
            print(f"No images found matching {file_pattern} in {image_directory}")
            return []
        
        print(f"Processing {len(image_files)} images...")
        
        results = []
        for i, image_path in enumerate(image_files, 1):
            print(f"[{i}/{len(image_files)}] Processing: {image_path.name}")
            
            result = self.process_single_item(image_path, **kwargs)
            results.append(result)
        
        return results
    
    @abstractmethod
    def process_single_item(self, item_path: Path, **kwargs) -> Dict:
        """Process a single item - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def save_results(self, results: List[Dict], **kwargs) -> None:
        """Save processing results - must be implemented by subclasses"""
        pass
    
    def check_ocr_availability(self) -> bool:
        """Check if OCR engine is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False


class MobileScreenshotOCR(BaseOCRProcessor):
    """
    Specialized OCR processor for mobile screenshots
    Focuses on extracting chat titles and filtering UI elements
    """
    
    def __init__(self, output_dir: str = "chat_ocr_output"):
        super().__init__(output_dir)
        self.ui_elements = [
            'new chat', 'search', 'menu', 'settings', 'profile', 'logout',
            'chats', 'whatever', 'wifi', 'battery', 'today', 'yesterday'
        ]
    
    def _get_default_ocr_config(self) -> str:
        """OCR config optimized for mobile UI"""
        return r'--oem 3 --psm 3'  # PSM 3 is better for lists
    
    def process_single_item(self, image_path: Path, **kwargs) -> Dict:
        """
        Process a single mobile screenshot
        
        Args:
            image_path: Path to screenshot image
        
        Returns:
            Dictionary with extracted chat titles
        """
        # Extract raw text
        raw_text = self.extract_text_from_image(image_path, enhance=True)
        
        # Extract chat titles
        chat_titles = self._extract_chat_titles(raw_text)
        
        return {
            'image_file': image_path.name,
            'raw_text': raw_text,
            'chat_titles': chat_titles,
            'title_count': len(chat_titles)
        }
    
    def _extract_chat_titles(self, text: str) -> List[str]:
        """
        Extract chat titles from OCR text, filtering out UI elements
        
        Args:
            text: Raw OCR text
        
        Returns:
            List of chat titles
        """
        lines = text.split('\n')
        chat_titles = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 5:  # Filter short lines
                # Remove timestamp patterns
                if re.match(r'^\d+\s+(minutes?|hours?|days?)\s+ago$', line.lower()):
                    continue
                
                # Filter UI elements
                if any(ui_element in line.lower() for ui_element in self.ui_elements):
                    continue
                
                # Clean trailing timestamps
                line = re.sub(r'\s*\(\d+\s+(minutes?|hours?|days?)\s+ago\)$', '', line)
                line = re.sub(r'\s*(yesterday|today)$', '', line, flags=re.IGNORECASE)
                line = line.strip()
                
                if line and len(line) > 5:
                    chat_titles.append(line)
        
        return chat_titles
    
    def save_results(self, results: List[Dict], **kwargs) -> None:
        """
        Save mobile screenshot OCR results
        
        Args:
            results: List of processing results
        """
        # Save detailed CSV
        csv_path = self.output_dir / "chat_titles_extracted.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['image_file', 'chat_title', 'raw_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                for title in result['chat_titles']:
                    writer.writerow({
                        'image_file': result['image_file'],
                        'chat_title': title,
                        'raw_text': result['raw_text'][:200] + "..." if len(result['raw_text']) > 200 else result['raw_text']
                    })
        
        # Save summary text
        summary_path = self.output_dir / "chat_titles_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("MOBILE SCREENSHOT OCR RESULTS\n")
            f.write("=" * 40 + "\n")
            f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Images Processed: {len(results)}\n")
            f.write(f"Total Titles Found: {sum(r['title_count'] for r in results)}\n\n")
            
            for result in results:
                f.write(f"\n[{result['image_file']}]\n")
                for title in result['chat_titles']:
                    f.write(f"• {title}\n")
        
        print(f"Results saved to: {csv_path} and {summary_path}")


class PDFBookOCR(BaseOCRProcessor):
    """
    Specialized OCR processor for PDF books
    Handles both text-based and image-based PDFs
    """
    
    def __init__(self, output_dir: str = "book_ocr_output"):
        super().__init__(output_dir)
        # Import here to avoid dependency issues if not needed
        try:
            import fitz  # PyMuPDF
            self.fitz = fitz
        except ImportError:
            raise ImportError("PyMuPDF (fitz) is required for PDF processing: pip install PyMuPDF")
    
    def _get_default_ocr_config(self) -> str:
        """OCR config optimized for book pages"""
        return r'--oem 3 --psm 1'  # PSM 1 is better for full pages
    
    def process_single_item(self, pdf_path: Path, **kwargs) -> Dict:
        """
        Process a single PDF book
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with extracted text and metadata
        """
        results = {
            'source_file': str(pdf_path),
            'total_pages': 0,
            'text_pages': [],
            'ocr_pages': [],
            'full_text': '',
            'extraction_method': 'hybrid'
        }
        
        try:
            doc = self.fitz.open(pdf_path)
            results['total_pages'] = len(doc)
            
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Try direct text extraction first
                direct_text = page.get_text().strip()
                
                if direct_text and len(direct_text) > 50:
                    # Page has extractable text
                    page_text = direct_text
                    results['text_pages'].append({
                        'page': page_num + 1,
                        'method': 'direct',
                        'text_length': len(page_text)
                    })
                else:
                    # Use OCR
                    page_text = self._ocr_pdf_page(page, page_num + 1)
                    if page_text:
                        results['ocr_pages'].append({
                            'page': page_num + 1,
                            'method': 'ocr',
                            'text_length': len(page_text)
                        })
                
                if page_text:
                    full_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                print(f"Page {page_num + 1}/{len(doc)}: {'Direct' if direct_text else 'OCR'}")
            
            results['full_text'] = full_text
            doc.close()
            
        except Exception as e:
            results['error'] = str(e)
            print(f"Error processing PDF: {e}")
        
        return results
    
    def _ocr_pdf_page(self, page, page_num: int) -> str:
        """
        Perform OCR on a single PDF page
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
        
        Returns:
            Extracted text
        """
        try:
            # Convert page to high-resolution image
            mat = self.fitz.Matrix(2, 2)  # 2x zoom
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            import io
            image = Image.open(io.BytesIO(img_data))
            
            # Extract text with book-optimized settings
            text = self.extract_text_from_image(
                image, 
                enhance=True, 
                enhancement_level="moderate"
            )
            
            # Clean book-specific artifacts
            text = self._clean_book_text(text)
            
            return text
            
        except Exception as e:
            print(f"OCR error on page {page_num}: {e}")
            return ""
    
    def _clean_book_text(self, text: str) -> str:
        """
        Clean text specifically for book content
        
        Args:
            text: Raw OCR text
        
        Returns:
            Cleaned text
        """
        # Split into lines and filter
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Remove very short lines (likely artifacts)
        cleaned_lines = [line for line in lines if len(line) > 3]
        
        # Join with proper spacing
        return '\n'.join(cleaned_lines)
    
    def save_results(self, results: List[Dict], **kwargs) -> None:
        """
        Save PDF OCR results
        
        Args:
            results: List of processing results (usually just one PDF)
        """
        for result in results:
            pdf_name = Path(result['source_file']).stem
            
            # Save full text
            txt_path = self.output_dir / f"{pdf_name}_extracted.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"EXTRACTED FROM: {result['source_file']}\n")
                f.write(f"Total Pages: {result['total_pages']}\n")
                f.write(f"Direct Text Pages: {len(result['text_pages'])}\n")
                f.write(f"OCR Pages: {len(result['ocr_pages'])}\n")
                f.write("=" * 50 + "\n\n")
                f.write(result['full_text'])
            
            # Save metadata
            json_path = self.output_dir / f"{pdf_name}_metadata.json"
            metadata = {k: v for k, v in result.items() if k != 'full_text'}
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"Results saved to: {txt_path} and {json_path}")


# Usage Examples and Factory Function
class OCRFactory:
    """Factory class to create appropriate OCR processors"""
    
    @staticmethod
    def create_processor(processor_type: str, output_dir: str = None) -> BaseOCRProcessor:
        """
        Create an OCR processor of the specified type
        
        Args:
            processor_type: 'mobile' or 'pdf'
            output_dir: Output directory (optional)
        
        Returns:
            OCR processor instance
        """
        if processor_type.lower() == 'mobile':
            return MobileScreenshotOCR(output_dir or "mobile_ocr_output")
        elif processor_type.lower() == 'pdf':
            return PDFBookOCR(output_dir or "pdf_ocr_output")
        else:
            raise ValueError(f"Unknown processor type: {processor_type}")


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Modular OCR System")
    parser.add_argument("type", choices=['mobile', 'pdf'], help="OCR processor type")
    parser.add_argument("input_path", help="Input file or directory path")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--language", default="eng", help="OCR language")
    
    args = parser.parse_args()
    
    # Create processor
    processor = OCRFactory.create_processor(args.type, args.output_dir)
    
    # Check OCR availability
    if not processor.check_ocr_availability():
        print("❌ OCR engine not available!")
        sys.exit(1)
    
    # Process input
    input_path = Path(args.input_path)
    
    if input_path.is_file():
        # Process single file
        result = processor.process_single_item(input_path)
        processor.save_results([result])
    else:
        # Process directory
        if args.type == 'mobile':
            results = processor.batch_process_images(str(input_path), "*.jpg")
        else:
            results = processor.batch_process_images(str(input_path), "*.pdf")
        
        processor.save_results(results)
    
    print("✅ Processing complete!")

"""
PDF and Image Text Extraction Utilities
Handles extracting text from various document formats
Uses GPT-4 Vision for OCR (no Tesseract installation needed)
"""

import base64
import io
from pathlib import Path
from typing import Optional, Union

import PyPDF2
from PIL import Image
from pdf2image import convert_from_path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_API_VERSION
)


class PDFExtractor:
    """
    Utility class for extracting text from PDFs and images.
    Uses GPT-4 Vision for OCR - no Tesseract installation required!
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the PDF extractor.
        
        Args:
            llm_client: Optional LLM client for vision capabilities
        """
        self.llm_client = llm_client
    
    @staticmethod
    def extract_from_pdf(file_path: Union[str, Path], llm_client=None) -> str:
        """
        Extract text from a PDF file.
        
        Tries two methods:
        1. Direct text extraction (for PDFs with embedded text)
        2. GPT-4 Vision OCR (for PDFs that are scanned images)
        
        Args:
            file_path: Path to PDF file
            llm_client: LLM client for vision-based extraction
        
        Returns:
            Extracted text as string
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        print(f"📄 Extracting text from PDF: {file_path.name}")
        
        try:
            # Method 1: Try direct text extraction first (faster)
            text = PDFExtractor._extract_text_directly(file_path)
            
            # If we got meaningful text, return it
            if text and len(text.strip()) > 50:
                print(f"✓ Extracted {len(text)} characters using direct method")
                return text
            
            # Method 2: If direct extraction failed, try GPT-4 Vision
            print("⚠️  Direct extraction yielded little text, trying GPT-4 Vision OCR...")
            
            if llm_client is None:
                # Import here to avoid circular dependency
                from utils.llm_client import LLMClient
                llm_client = LLMClient()
            
            text = PDFExtractor._extract_text_via_vision(file_path, llm_client)
            print(f"✓ Extracted {len(text)} characters using GPT-4 Vision")
            return text
        
        except Exception as e:
            print(f"✗ Error extracting from PDF: {e}")
            raise
    
    @staticmethod
    def _extract_text_directly(file_path: Path) -> str:
        """
        Extract text directly from PDF (works for PDFs with embedded text).
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            Extracted text
        """
        text = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"  PDF has {len(pdf_reader.pages)} page(s)")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num} ---\n"
                    text += page_text
        
        return text.strip()
    
    @staticmethod
    def _extract_text_via_vision(file_path: Path, llm_client) -> str:
        """
        Extract text from PDF using GPT-4 Vision (no Tesseract needed!).
        
        Args:
            file_path: Path to PDF file
            llm_client: LLM client with vision capabilities
        
        Returns:
            Extracted text
        """
        text = ""
        
        # Convert PDF pages to images
        try:
            images = convert_from_path(str(file_path))
            print(f"  Converted PDF to {len(images)} image(s)")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not convert PDF to images: {e}")
            print(f"  You may need to install poppler. For now, returning empty text.")
            return ""
        
        # Process each page with GPT-4 Vision
        for page_num, image in enumerate(images, 1):
            print(f"  Processing page {page_num} with GPT-4 Vision...")
            page_text = PDFExtractor._image_to_text_via_vision(image, llm_client)
            if page_text:
                text += f"\n--- Page {page_num} ---\n"
                text += page_text
        
        return text.strip()
    
    @staticmethod
    def extract_from_image(file_path: Union[str, Path], llm_client=None) -> str:
        """
        Extract text from an image file using GPT-4 Vision.
        
        Args:
            file_path: Path to image file (PNG, JPG, etc.)
            llm_client: LLM client for vision capabilities
        
        Returns:
            Extracted text as string
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        print(f"🖼️  Extracting text from image: {file_path.name}")
        
        try:
            if llm_client is None:
                from utils.llm_client import LLMClient
                llm_client = LLMClient()
            
            # Open image
            image = Image.open(file_path)
            
            # Extract text using GPT-4 Vision
            text = PDFExtractor._image_to_text_via_vision(image, llm_client)
            
            print(f"✓ Extracted {len(text)} characters")
            return text.strip()
        
        except Exception as e:
            print(f"✗ Error extracting from image: {e}")
            raise
    
    @staticmethod
    def _image_to_text_via_vision(image: Image.Image, llm_client) -> str:
        """
        Use GPT-4 Vision to extract text from an image.
        
        Args:
            image: PIL Image object
            llm_client: LLM client with vision capabilities
        
        Returns:
            Extracted text
        """
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Use GPT-4 Vision to extract text
        text = llm_client.extract_text_from_image(image_base64)
        
        return text
    
    @staticmethod
    def extract_from_file(file_path: Union[str, Path], llm_client=None) -> str:
        """
        Smart extraction - automatically detects file type and uses appropriate method.
        
        Args:
            file_path: Path to file (PDF or image)
            llm_client: LLM client for vision capabilities
        
        Returns:
            Extracted text as string
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type by extension
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return PDFExtractor.extract_from_pdf(file_path, llm_client)
        elif extension in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
            return PDFExtractor.extract_from_image(file_path, llm_client)
        else:
            raise ValueError(f"Unsupported file type: {extension}")


def main():
    """
    Test the PDF extractor with sample files.
    """
    print("=" * 60)
    print("Testing PDF/Image Extraction (GPT-4 Vision)")
    print("=" * 60)
    
    # Create a sample text schedule for testing
    sample_schedule = """
SAMPLE SCHEDULE - Week of November 25, 2025

Monday, November 25
- 09:00-10:30: Introduction to AI (Room 101)
- 11:00-12:30: Mathematics Lecture (Room 205)
- 14:00-16:00: Lab Session (Computer Lab A)

Tuesday, November 26
- 10:00-11:30: Machine Learning (Room 101)
- 13:00-15:00: Soccer Practice (Sports Field)

Wednesday, November 27
- 09:00-10:30: Data Structures (Room 303)
- 15:00-17:00: Study Group (Library)
"""
    
    print("\n[Test] Sample schedule text:")
    print(sample_schedule)
    print("\nℹ️  To test with real PDFs/images:")
    print("  1. Save a schedule as PDF or image in tests/sample_schedules/")
    print("  2. Update the file path in test_parser.py")
    print("  3. Run: python test_parser.py")
    print("\n✓ No Tesseract installation required!")
    print("  Using GPT-4 Vision for OCR instead.")


if __name__ == "__main__":
    main()
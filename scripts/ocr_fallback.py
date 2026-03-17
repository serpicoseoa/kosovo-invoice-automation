#!/usr/bin/env python3
"""
OCR Fallback for Invoice Automation
Converts files to high-contrast PDF and applies OCR using Tesseract.
"""

import json
import sys
import os
import subprocess
import tempfile
from datetime import datetime

# OCR output directory
OCR_OUTPUT_PATH = '/data/invoices/ocr_temp'


def ensure_directories():
    """Ensure OCR output directory exists."""
    os.makedirs(OCR_OUTPUT_PATH, exist_ok=True)


def check_tesseract():
    """Check if Tesseract is available."""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def convert_to_high_contrast_pdf(input_path):
    """
    Convert input file to a high-contrast, OCR-enhanced PDF.
    Uses ImageMagick for image processing if available.
    """
    ensure_directories()
    
    # Generate output filename
    basename = os.path.basename(input_path)
    name, ext = os.path.splitext(basename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"{name}_ocr_{timestamp}.pdf"
    output_path = os.path.join(OCR_OUTPUT_PATH, output_filename)
    
    ext_lower = ext.lower()
    
    try:
        if ext_lower in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
            # For images: enhance contrast and convert to PDF with OCR layer
            # Using ImageMagick for preprocessing + Tesseract for OCR
            
            # Create temp file for enhanced image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_enhanced = tmp.name
            
            try:
                # Enhance image with ImageMagick (increase contrast, sharpen)
                subprocess.run([
                    'convert', input_path,
                    '-normalize',           # Normalize contrast
                    '-sharpen', '0x1',      # Sharpen
                    '-contrast-stretch', '2%x2%',  # Stretch contrast
                    '-type', 'Grayscale',   # Convert to grayscale
                    temp_enhanced
                ], check=True, timeout=60)
                
                # Apply Tesseract OCR to create searchable PDF
                subprocess.run([
                    'tesseract', temp_enhanced, output_path.replace('.pdf', ''),
                    '-l', 'eng+deu',        # English + German
                    'pdf'
                ], check=True, timeout=120)
                
            finally:
                # Cleanup temp file
                if os.path.exists(temp_enhanced):
                    os.unlink(temp_enhanced)
                    
        elif ext_lower == '.pdf':
            # For PDFs: extract images, enhance, and rebuild with OCR layer
            
            # Simple approach: use pdftoppm + tesseract
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract PDF pages as images
                subprocess.run([
                    'pdftoppm', '-png', '-r', '300',
                    input_path, os.path.join(tmpdir, 'page')
                ], check=True, timeout=120)
                
                # Find extracted images
                images = sorted([f for f in os.listdir(tmpdir) if f.endswith('.png')])
                
                if not images:
                    # Fallback: just copy the original PDF
                    import shutil
                    shutil.copy(input_path, output_path)
                else:
                    # Process first page (most invoices are single page)
                    first_image = os.path.join(tmpdir, images[0])
                    
                    # Enhance and OCR
                    enhanced = os.path.join(tmpdir, 'enhanced.png')
                    subprocess.run([
                        'convert', first_image,
                        '-normalize', '-sharpen', '0x1',
                        '-contrast-stretch', '2%x2%',
                        '-type', 'Grayscale',
                        enhanced
                    ], check=True, timeout=60)
                    
                    # Create PDF with OCR
                    subprocess.run([
                        'tesseract', enhanced, output_path.replace('.pdf', ''),
                        '-l', 'eng+deu', 'pdf'
                    ], check=True, timeout=120)
        else:
            return {
                'success': False,
                'error': f'Unsupported file format: {ext}'
            }
        
        # Verify output exists
        if os.path.exists(output_path):
            return {
                'success': True,
                'enhanced_pdf_path': output_path,
                'original_path': input_path
            }
        else:
            return {
                'success': False,
                'error': 'OCR processing completed but output file not found'
            }
            
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': f'OCR processing failed: {str(e)}'
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'OCR processing timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def simple_ocr_fallback(input_path):
    """
    Simple fallback that just copies the file for re-processing.
    Used when ImageMagick/Tesseract are not available.
    """
    ensure_directories()
    
    basename = os.path.basename(input_path)
    name, ext = os.path.splitext(basename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"{name}_retry_{timestamp}{ext}"
    output_path = os.path.join(OCR_OUTPUT_PATH, output_filename)
    
    import shutil
    shutil.copy(input_path, output_path)
    
    return {
        'success': True,
        'enhanced_pdf_path': output_path,
        'original_path': input_path,
        'note': 'Simple copy - OCR tools not available'
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: ocr_fallback.py <file_path>'
        }))
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(json.dumps({
            'success': False,
            'error': f'File not found: {file_path}'
        }))
        sys.exit(1)
    
    # Check if Tesseract is available
    if check_tesseract():
        result = convert_to_high_contrast_pdf(file_path)
    else:
        # Fallback to simple copy
        result = simple_ocr_fallback(file_path)
    
    print(json.dumps(result))


if __name__ == '__main__':
    main()

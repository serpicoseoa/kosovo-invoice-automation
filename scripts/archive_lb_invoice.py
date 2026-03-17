#!/usr/bin/env python3
"""
Archive script for Kosovo VAT Purchase Book (LB.xlsx) invoices
Specifically handles LB.xlsx field names from Vartex Classification
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)

def sanitize_filename(name):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()

def archive_lb_invoice(source_file, invoice_data_json, archive_dir):
    """
    Archive LB.xlsx invoice file with proper naming convention
    
    Args:
        source_file: Full path to source file
        invoice_data_json: JSON string with invoice_data from Parse Unstract Result
        archive_dir: Directory to archive to
    """
    try:
        # Parse invoice data
        invoice_data = json.loads(invoice_data_json)
        
        # Validate source file exists
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Create archive directory if it doesn't exist
        os.makedirs(archive_dir, exist_ok=True)
        log_message(f"Archive directory: {archive_dir}")
        
        # Get file extension
        file_ext = Path(source_file).suffix.lower()
        
        # Extract fields from LB.xlsx structure
        supplier_name = invoice_data.get('Emri i shitësit', 'UNKNOWN')
        invoice_date = invoice_data.get('Data', 'UNKNOWN')
        invoice_number = invoice_data.get("'Numri i faturës", invoice_data.get("Numri i faturës", 'UNKNOWN'))
        
        # Sanitize components for filename
        safe_supplier = sanitize_filename(supplier_name)
        safe_date = sanitize_filename(invoice_date)
        safe_number = sanitize_filename(invoice_number)
        
        # Build new filename: {supplier_name} - {invoice_date} - {invoice_number}.ext
        new_filename = f"{safe_supplier} - {safe_date} - {safe_number}{file_ext}"
        
        # Full destination path
        dest_path = os.path.join(archive_dir, new_filename)
        
        # Handle duplicate filenames
        if os.path.exists(dest_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{safe_supplier} - {safe_date} - {safe_number}_{timestamp}{file_ext}"
            dest_path = os.path.join(archive_dir, new_filename)
            log_message(f"Duplicate filename detected, added timestamp", "WARNING")
        
        # Move file
        shutil.move(source_file, dest_path)
        
        log_message(f"Successfully archived: {source_file}")
        log_message(f"New location: {dest_path}")
        
        # Return success
        result = {
            "status": "success",
            "original_path": source_file,
            "archived_path": dest_path,
            "filename": new_filename,
            "supplier": supplier_name,
            "date": invoice_date,
            "invoice_number": invoice_number
        }
        
        print(json.dumps(result))
        return 0
        
    except Exception as e:
        log_message(f"Error archiving file: {e}", "ERROR")
        print(json.dumps({
            "status": "error",
            "message": str(e),
            "source_file": source_file
        }))
        return 1

def main():
    """Main execution function"""
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "error",
            "message": "Usage: python archive_lb_invoice.py <source_file> <archive_dir> [invoice_data_json or pipe from stdin]"
        }))
        return 1
    
    source_file = sys.argv[1]
    archive_dir = sys.argv[2]
    
    # Read JSON data from stdin or command line argument
    if len(sys.argv) >= 4:
        invoice_data_json = sys.argv[3]
        log_message("Reading invoice data from command line argument")
    else:
        # Read from stdin
        log_message("Reading invoice data from stdin")
        invoice_data_json = sys.stdin.read().strip()
        if not invoice_data_json:
            print(json.dumps({
                "status": "error",
                "message": "No invoice data received from stdin"
            }))
            return 1
    
    return archive_lb_invoice(source_file, invoice_data_json, archive_dir)

if __name__ == "__main__":
    sys.exit(main())

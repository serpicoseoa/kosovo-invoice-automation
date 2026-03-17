#!/usr/bin/env python3
"""
Validation script for Invoice Automation
Validates extracted invoice data with field name mapping support.
"""

import json
import sys
import re

# Field name mapping from Unstract output to expected fields
FIELD_MAPPING = {
    # Direct mappings
    'invoice_date': 'invoice_date',
    'invoice_number': 'invoice_number',
    'supplier_name': 'supplier_name',
    'supplier_business_number': 'supplier_business_number',
    'supplier_vat': 'supplier_vat',
    'vat_base_amount': 'vat_base_amount',
    'vat_amount': 'vat_amount',
    'total_amount': 'total_amount',
    'vat_rate': 'vat_rate',
    # Alternate field names from Unstract
    'business number': 'supplier_business_number',
    'business_number': 'supplier_business_number',
    'total amount excluding VAT': 'vat_base_amount',
    'total_amount_excluding_vat': 'vat_base_amount',
    'base_amount': 'vat_base_amount',
    'net_amount': 'vat_base_amount',
}

# Required fields for validation
REQUIRED_FIELDS = [
    'invoice_date',
    'invoice_number',
    'supplier_name',
    'vat_base_amount',
    'vat_amount',
    'total_amount'
]

# VAT tolerance for math validation (allows small rounding differences)
VAT_TOLERANCE = 0.10


def normalize_data(data):
    """Normalize field names from Unstract to expected format."""
    normalized = {}
    
    for key, value in data.items():
        # Check if this field has a mapping
        mapped_key = FIELD_MAPPING.get(key, key)
        normalized[mapped_key] = value
    
    return normalized


def is_empty(value):
    """Check if a value is considered empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == '':
        return True
    return False


def is_numeric(value):
    """Check if a value can be converted to a number."""
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def to_number(value):
    """Convert a value to a float, return None if not possible."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def extract_vat_rate(vat_rate_str):
    """Extract numeric VAT rate from string like '18%' or '18%, 8%'."""
    if vat_rate_str is None:
        return None
    
    # Handle string representation
    if isinstance(vat_rate_str, (int, float)):
        return float(vat_rate_str)
    
    # Extract first percentage from string
    match = re.search(r'(\d+(?:\.\d+)?)\s*%?', str(vat_rate_str))
    if match:
        return float(match.group(1))
    
    return None


def validate_vat_math(data):
    """
    Validate VAT math: total ≈ vat_base_amount + vat_amount
    Returns (is_valid, message)
    """
    base = to_number(data.get('vat_base_amount'))
    vat = to_number(data.get('vat_amount'))
    total = to_number(data.get('total_amount'))
    
    if base is None or vat is None or total is None:
        return True, "Cannot validate VAT math - missing numeric values"
    
    expected_total = base + vat
    difference = abs(total - expected_total)
    
    if difference <= VAT_TOLERANCE:
        return True, f"VAT math valid: {base} + {vat} = {expected_total} (total: {total})"
    else:
        return False, f"VAT math invalid: {base} + {vat} = {expected_total}, but total is {total} (diff: {difference:.2f})"


def validate_invoice_data(data):
    """
    Validate extracted invoice data.
    Returns validation result with details.
    """
    # Normalize field names
    normalized = normalize_data(data)
    
    issues = []
    warnings = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        value = normalized.get(field)
        if is_empty(value):
            issues.append(f"Missing or empty field: {field}")
    
    # Check numeric fields
    numeric_fields = ['vat_base_amount', 'vat_amount', 'total_amount']
    for field in numeric_fields:
        value = normalized.get(field)
        if not is_empty(value) and not is_numeric(value):
            issues.append(f"Non-numeric value for {field}: {value}")
    
    # Validate VAT math
    vat_valid, vat_message = validate_vat_math(normalized)
    if not vat_valid:
        # VAT math failure is a warning, not a blocker
        warnings.append(vat_message)
    
    # Check date format (DD.MM.YYYY)
    invoice_date = normalized.get('invoice_date')
    if invoice_date and isinstance(invoice_date, str):
        date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
        if not re.match(date_pattern, invoice_date):
            warnings.append(f"Date format may not be DD.MM.YYYY: {invoice_date}")
    
    # Determine overall validity
    # Valid if no critical issues (warnings are OK)
    is_valid = len(issues) == 0
    
    return {
        'valid': is_valid,
        'issues': issues,
        'warnings': warnings,
        'vat_validation': vat_message,
        'normalized_data': normalized,
        'fields_found': list(normalized.keys()),
        'required_fields_present': sum(1 for f in REQUIRED_FIELDS if not is_empty(normalized.get(f)))
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'valid': False,
            'error': 'Usage: validation.py <json_string_or_file_path>'
        }))
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    try:
        # Try to parse as JSON string first
        if input_arg.strip().startswith('{'):
            data = json.loads(input_arg)
        else:
            # Try to read as file path
            with open(input_arg, 'r') as f:
                data = json.load(f)
        
        # Validate
        result = validate_invoice_data(data)
        print(json.dumps(result))
        
    except FileNotFoundError:
        print(json.dumps({
            'valid': False,
            'error': f'JSON file not found: {input_arg}'
        }))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({
            'valid': False,
            'error': f'Invalid JSON: {str(e)}'
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            'valid': False,
            'error': str(e)
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()

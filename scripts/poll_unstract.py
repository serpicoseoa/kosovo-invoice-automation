#!/usr/bin/env python3
"""
Poll Unstract API for extraction results.
Usage: python3 poll_unstract.py <status_api_path> <original_path> <file_hash>
"""
import sys
import json
import time
import urllib.request
import urllib.error

# Field mapping for Unstract alternate field names
FIELD_MAPPING = {
    'Invoice Date': 'invoice_date',
    'Invoice Number': 'invoice_number',
    'Supplier Name': 'supplier_name',
    'Supplier Business Number': 'supplier_business_number',
    'Supplier VAT': 'supplier_vat',
    'VAT Base Amount': 'vat_base_amount',
    'VAT Amount': 'vat_amount',
    'Total Amount': 'total_amount',
    'VAT Rate': 'vat_rate',
    'invoice_date': 'invoice_date',
    'invoice_number': 'invoice_number',
    'supplier_name': 'supplier_name',
    'supplier_business_number': 'supplier_business_number',
    'supplier_vat': 'supplier_vat',
    'vat_base_amount': 'vat_base_amount',
    'vat_amount': 'vat_amount',
    'total_amount': 'total_amount',
    'vat_rate': 'vat_rate'
}

def normalize_data(data):
    """Normalize field names from Unstract output."""
    if not isinstance(data, dict):
        return data
    
    normalized = {}
    for key, value in data.items():
        mapped_key = FIELD_MAPPING.get(key, key.lower().replace(' ', '_'))
        normalized[mapped_key] = value
    
    return normalized

def poll_status(status_path, api_key, max_attempts=36, interval=5):
    """Poll Unstract status API until completion."""
    url = f"http://unstract-backend:8000{status_path}"
    headers = {'Authorization': f'Bearer {api_key}'}
    
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                
                if data.get('status') == 'COMPLETED':
                    return {'success': True, 'data': data}
                elif data.get('status') == 'FAILED':
                    return {'success': False, 'error': 'Extraction failed', 'data': data}
                
        except urllib.error.URLError as e:
            if attempt == max_attempts - 1:
                return {'success': False, 'error': str(e)}
        except Exception as e:
            if attempt == max_attempts - 1:
                return {'success': False, 'error': str(e)}
        
        time.sleep(interval)
    
    return {'success': False, 'error': 'Timeout waiting for Unstract result'}

def main():
    if len(sys.argv) < 4:
        print(json.dumps({'error': 'Usage: poll_unstract.py <status_api_path> <original_path> <file_hash>'}))
        sys.exit(1)
    
    status_path = sys.argv[1]
    original_path = sys.argv[2]
    file_hash = sys.argv[3]
    
    api_key = '63771165-bf3f-4dbc-bfa1-02d7f353f8d3'
    
    result = poll_status(status_path, api_key)
    
    if result['success']:
        try:
            # Extract the data from Unstract response
            message = result['data'].get('message', [])
            if message and len(message) > 0:
                file_result = message[0]
                output = file_result.get('result', {}).get('output', {})
                
                # Get the first output key
                output_keys = list(output.keys())
                if output_keys:
                    raw_result = output[output_keys[0]]
                    
                    # Parse if string
                    if isinstance(raw_result, str):
                        try:
                            extracted_data = json.loads(raw_result)
                        except:
                            extracted_data = {'raw': raw_result}
                    else:
                        extracted_data = raw_result
                    
                    # Normalize field names
                    extracted_data = normalize_data(extracted_data)
                    
                    print(json.dumps({
                        'extractedData': extracted_data,
                        'originalPath': original_path,
                        'fileHash': file_hash
                    }))
                    return
            
            print(json.dumps({'error': 'No output in Unstract response', 'raw': result['data']}))
        except Exception as e:
            print(json.dumps({'error': str(e), 'raw': str(result)}))
    else:
        print(json.dumps({'error': result.get('error', 'Unknown error')}))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Checksum Manager for Invoice Automation
Handles SHA-256 checksum calculation and duplicate detection.
Registry stored at: /data/invoices/checksums_db.json
"""

import json
import sys
import os
import hashlib
from datetime import datetime
import fcntl

# Checksum registry path
REGISTRY_PATH = '/data/invoices/checksums_db.json'


def calculate_sha256(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b''):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def load_registry():
    """Load the checksum registry from disk."""
    if not os.path.exists(REGISTRY_PATH):
        return {}
    
    try:
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_registry(registry):
    """Save the checksum registry to disk with file locking."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    
    try:
        with open(REGISTRY_PATH, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(registry, f, indent=2)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError):
        # If locking fails, save anyway (Windows compatibility)
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(registry, f, indent=2)


def check_duplicate(file_path):
    """
    Check if a file is a duplicate based on its SHA-256 hash.
    Returns JSON with is_duplicate flag and hash.
    """
    if not os.path.exists(file_path):
        return {
            'is_duplicate': False,
            'hash': None,
            'error': f'File not found: {file_path}'
        }
    
    # Calculate hash
    file_hash = calculate_sha256(file_path)
    
    # Load registry
    registry = load_registry()
    
    # Check if hash exists
    if file_hash in registry:
        existing = registry[file_hash]
        return {
            'is_duplicate': True,
            'hash': file_hash,
            'original_filename': existing.get('filename'),
            'original_processed_at': existing.get('processed_at')
        }
    
    return {
        'is_duplicate': False,
        'hash': file_hash
    }


def register_checksum(file_path, file_hash=None):
    """
    Register a file's checksum in the registry.
    If hash is not provided, it will be calculated.
    """
    if file_hash is None:
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        file_hash = calculate_sha256(file_path)
    
    # Load registry
    registry = load_registry()
    
    # Add entry
    registry[file_hash] = {
        'filename': os.path.basename(file_path),
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save registry
    save_registry(registry)
    
    return {
        'success': True,
        'hash': file_hash,
        'filename': os.path.basename(file_path),
        'registry_path': REGISTRY_PATH
    }


def list_checksums():
    """List all registered checksums."""
    registry = load_registry()
    return {
        'count': len(registry),
        'checksums': registry
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: checksum_manager.py <action> [file_path] [hash]'
        }))
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        if action == 'check':
            if len(sys.argv) < 3:
                print(json.dumps({
                    'is_duplicate': False,
                    'error': 'Missing file path'
                }))
                sys.exit(1)
            result = check_duplicate(sys.argv[2])
            
        elif action == 'register':
            if len(sys.argv) < 3:
                print(json.dumps({
                    'success': False,
                    'error': 'Missing file path'
                }))
                sys.exit(1)
            file_path = sys.argv[2]
            file_hash = sys.argv[3] if len(sys.argv) > 3 else None
            result = register_checksum(file_path, file_hash)
            
        elif action == 'list':
            result = list_checksums()
            
        else:
            result = {
                'success': False,
                'error': f'Unknown action: {action}. Use "check", "register", or "list"'
            }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()

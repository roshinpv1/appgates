#!/usr/bin/env python3
"""
Script to update timeout values from 30 seconds to 300 seconds
"""

import os
import re

def update_timeout_in_file(file_path, old_timeout="30", new_timeout="300"):
    """Update timeout values in a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update timeout values
        updated_content = re.sub(
            rf'timeout={old_timeout}',
            f'timeout={new_timeout}',
            content
        )
        
        # Also update timeout values in min() functions
        updated_content = re.sub(
            rf'min\(config\.timeout,\s*{old_timeout}\)',
            f'min(config.timeout, {new_timeout})',
            updated_content
        )
        
        # Update default timeout values
        updated_content = re.sub(
            rf'timeout=config\.get\("timeout",\s*{old_timeout}\)',
            f'timeout=config.get("timeout", {new_timeout})',
            updated_content
        )
        
        with open(file_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated timeouts in {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all timeout values"""
    files_to_update = [
        "services/llm_service.py",
        "services/embedding_service.py"
    ]
    
    print("🔄 Updating timeout values from 30s to 300s...")
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            update_timeout_in_file(file_path)
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print("✅ Timeout update completed!")

if __name__ == "__main__":
    main()

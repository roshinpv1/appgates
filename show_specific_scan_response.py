#!/usr/bin/env python3
"""
Script to show the full llm_pre_analysis response for a specific scan
"""

import json
import sys
from pathlib import Path

def show_specific_scan_response(scan_id):
    """Show the full llm_pre_analysis response for a specific scan"""
    
    log_dir = Path("src/logs/llm")
    
    if not log_dir.exists():
        print("❌ Log directory not found: src/logs/llm")
        return
    
    # Try different filename patterns
    possible_files = [
        log_dir / f"scan_{scan_id}_llm_log.jsonl",
        log_dir / f"scan_scan_{scan_id}_llm_log.jsonl"
    ]
    
    log_file = None
    for file_path in possible_files:
        if file_path.exists():
            log_file = file_path
            break
    
    if not log_file:
        print(f"❌ No log file found for scan ID: {scan_id}")
        print("Available scan IDs:")
        for file_path in log_dir.glob("scan_*_llm_log.jsonl"):
            scan_id_from_file = file_path.stem.replace('scan_', '').replace('_llm_log', '')
            print(f"  - {scan_id_from_file}")
        return
    
    print(f"🔍 Finding llm_pre_analysis response for scan: {scan_id}")
    print(f"📄 File: {log_file.name}")
    print("=" * 80)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        log_entry = json.loads(line)
                        node_name = log_entry.get('node_name', '')
                        
                        if node_name == 'LLMPreAnalysisNode':
                            print(f"🎯 Scan ID: {scan_id}")
                            print(f"⏰ Timestamp: {log_entry.get('timestamp', 'Unknown')}")
                            print(f"⏱️  Duration: {log_entry.get('duration', 0):.2f}s")
                            print(f"📝 Prompt Length: {log_entry.get('prompt_length', 0):,} chars")
                            print(f"📄 Response Length: {log_entry.get('response_length', 0):,} chars")
                            
                            if log_entry.get('error'):
                                print(f"❌ Error: {log_entry['error']}")
                            else:
                                print("✅ Success")
                            
                            # Show metadata
                            metadata = log_entry.get('metadata', {})
                            if metadata:
                                print(f"\n📊 Metadata:")
                                print(json.dumps(metadata, indent=2))
                            
                            print(f"\n📋 FULL PROMPT:")
                            print("-" * 40)
                            prompt = log_entry.get('prompt', '')
                            print(prompt)
                            
                            print(f"\n🤖 FULL RESPONSE:")
                            print("-" * 40)
                            response = log_entry.get('response', '')
                            print(response)
                            
                            return
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON decode error in line {line_num}: {e}")
                        continue
        
        print(f"❌ No LLMPreAnalysisNode found in {log_file.name}")
        
    except Exception as e:
        print(f"❌ Error reading {log_file}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python show_specific_scan_response.py <scan_id>")
        print("Example: python show_specific_scan_response.py 1756576087")
        sys.exit(1)
    
    scan_id = sys.argv[1]
    show_specific_scan_response(scan_id)

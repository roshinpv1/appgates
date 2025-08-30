#!/usr/bin/env python3
"""
Script to show all llm_pre_analysis responses from LLM logs
"""

import json
import os
from pathlib import Path
from datetime import datetime

def show_latest_pre_analysis_response():
    """Show the most recent llm_pre_analysis response"""
    
    log_dir = Path("src/logs/llm")
    
    if not log_dir.exists():
        print("❌ Log directory not found: src/logs/llm")
        return
    
    print("🔍 Finding latest llm_pre_analysis response...")
    print("=" * 80)
    
    # Find all log files and get their modification times
    log_files = []
    for log_file in log_dir.glob("scan_*_llm_log.jsonl"):
        log_files.append((log_file, log_file.stat().st_mtime))
    
    if not log_files:
        print("❌ No log files found")
        return
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: x[1], reverse=True)
    
    # Find the most recent pre-analysis response
    latest_response = None
    latest_file = None
    
    for log_file, mtime in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            if log_entry.get('node_name') == 'LLMPreAnalysisNode':
                                latest_response = log_entry
                                latest_file = log_file
                                break
                        except json.JSONDecodeError:
                            continue
            if latest_response:
                break
        except Exception:
            continue
    
    if latest_response:
        scan_id = latest_file.stem.replace('scan_', '').replace('_llm_log', '')
        
        print(f"🎯 Latest LLM Pre-Analysis Response")
        print(f"📄 File: {latest_file.name}")
        print(f"🔢 Scan ID: {scan_id}")
        print(f"⏰ Timestamp: {latest_response.get('timestamp', 'Unknown')}")
        print(f"⏱️  Duration: {latest_response.get('duration', 0):.2f}s")
        print(f"📝 Prompt Length: {latest_response.get('prompt_length', 0):,} chars")
        print(f"📄 Response Length: {latest_response.get('response_length', 0):,} chars")
        
        if latest_response.get('error'):
            print(f"❌ Error: {latest_response['error']}")
        else:
            print("✅ Success")
        
        # Show metadata
        metadata = latest_response.get('metadata', {})
        if metadata:
            print(f"\n📊 Metadata:")
            print(json.dumps(metadata, indent=2))
        
        print(f"\n📋 PROMPT:")
        print("-" * 40)
        prompt = latest_response.get('prompt', '')
        print(prompt)
        
        print(f"\n🤖 RESPONSE:")
        print("-" * 40)
        response = latest_response.get('response', '')
        print(response)
        
    else:
        print("❌ No llm_pre_analysis responses found in any log files")

if __name__ == "__main__":
    show_latest_pre_analysis_response()

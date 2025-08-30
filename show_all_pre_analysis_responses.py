#!/usr/bin/env python3
"""
Script to show all llm_pre_analysis responses from LLM logs
"""

import json
import os
from pathlib import Path
from datetime import datetime

def show_all_pre_analysis_responses():
    """Show all llm_pre_analysis responses from LLM logs"""
    
    log_dir = Path("src/logs/llm")
    
    if not log_dir.exists():
        print("❌ Log directory not found: src/logs/llm")
        return
    
    print("🔍 Searching for all llm_pre_analysis responses...")
    print("=" * 80)
    
    # Find all log files
    log_files = list(log_dir.glob("scan_*_llm_log.jsonl"))
    
    if not log_files:
        print("❌ No log files found")
        return
    
    print(f"📁 Found {len(log_files)} log files")
    print()
    
    total_pre_analysis_calls = 0
    all_responses = []
    
    for log_file in sorted(log_files):
        print(f"📄 Processing: {log_file.name}")
        print("-" * 60)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            node_name = log_entry.get('node_name', '')
                            
                            if node_name == 'LLMPreAnalysisNode':
                                total_pre_analysis_calls += 1
                                
                                # Extract scan_id from filename
                                scan_id = log_file.stem.replace('scan_', '').replace('_llm_log', '')
                                
                                response_data = {
                                    'scan_id': scan_id,
                                    'timestamp': log_entry.get('timestamp', 'Unknown'),
                                    'duration': log_entry.get('duration', 0),
                                    'prompt_length': log_entry.get('prompt_length', 0),
                                    'response_length': log_entry.get('response_length', 0),
                                    'error': log_entry.get('error'),
                                    'response': log_entry.get('response', ''),
                                    'metadata': log_entry.get('metadata', {})
                                }
                                
                                all_responses.append(response_data)
                                
                                print(f"🎯 Scan ID: {scan_id}")
                                print(f"⏰ Timestamp: {response_data['timestamp']}")
                                print(f"⏱️  Duration: {response_data['duration']:.2f}s")
                                print(f"📝 Prompt Length: {response_data['prompt_length']:,} chars")
                                print(f"📄 Response Length: {response_data['response_length']:,} chars")
                                
                                if response_data['error']:
                                    print(f"❌ Error: {response_data['error']}")
                                else:
                                    print("✅ Success")
                                
                                # Show a preview of the response
                                response_preview = response_data['response'][:200] + "..." if len(response_data['response']) > 200 else response_data['response']
                                print(f"📋 Response Preview: {response_preview}")
                                
                                print()
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON decode error in line {line_num}: {e}")
                            continue
                            
        except Exception as e:
            print(f"❌ Error reading {log_file}: {e}")
            continue
    
    print(f"📊 SUMMARY:")
    print(f"   Total LLM Pre-Analysis calls found: {total_pre_analysis_calls}")
    print(f"   Total log files processed: {len(log_files)}")
    
    # Save all responses to a file
    if all_responses:
        output_file = "all_llm_pre_analysis_responses.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_responses, f, indent=2, ensure_ascii=False)
        print(f"💾 All responses saved to: {output_file}")

if __name__ == "__main__":
    show_all_pre_analysis_responses()

#!/usr/bin/env python3
"""
Test: Verify API response includes enhanced metadata
"""

import json
import requests
import time
from pathlib import Path

def test_enhanced_metadata_in_api():
    """Test that API response includes enhanced metadata"""
    
    print("🧪 Testing Enhanced Metadata in API Response")
    print("=" * 50)
    
    # Start the API server if not running
    try:
        health_response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
        print("✅ API server is running")
    except:
        print("❌ API server not running. Please start it first with: python -m codegates.api.server")
        return
    
    # Test with a simple repository that should have some patterns
    scan_request = {
        "repository_url": "https://github.com/spring-projects/spring-petclinic",
        "branch": "main"
    }
    
    print(f"📤 Starting scan of: {scan_request['repository_url']}")
    
    # Start scan
    try:
        response = requests.post("http://localhost:8000/api/v1/scan", json=scan_request)
        if response.status_code != 200:
            print(f"❌ Scan request failed: {response.status_code} - {response.text}")
            return
            
        scan_data = response.json()
        scan_id = scan_data.get("scan_id")
        print(f"✅ Scan started with ID: {scan_id}")
        
        # Wait for completion
        print("⏳ Waiting for scan to complete...")
        for i in range(60):  # Wait up to 5 minutes
            time.sleep(5)
            
            status_response = requests.get(f"http://localhost:8000/api/v1/scan/{scan_id}")
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                continue
                
            result = status_response.json()
            status = result.get("status")
            
            print(f"📊 Status: {status} (attempt {i+1}/60)")
            
            if status == "completed":
                print("✅ Scan completed!")
                break
            elif status == "failed":
                print(f"❌ Scan failed: {result.get('message', 'Unknown error')}")
                return
        else:
            print("⏰ Scan timed out")
            return
        
        # Analyze the response for enhanced metadata
        print("\n🔍 Analyzing API Response for Enhanced Metadata")
        print("-" * 50)
        
        gates = result.get("gates", [])
        print(f"📊 Total gates: {len(gates)}")
        
        gates_with_matches = 0
        total_matches = 0
        enhanced_fields_found = set()
        
        for gate in gates:
            gate_name = gate.get("name")
            matches = gate.get("matches", [])
            
            if matches:
                gates_with_matches += 1
                total_matches += len(matches)
                
                print(f"\n🚪 Gate: {gate_name}")
                print(f"   📈 Status: {gate.get('status')}")
                print(f"   🎯 Matches: {len(matches)}")
                
                # Check first match for enhanced metadata fields
                if matches:
                    first_match = matches[0]
                    print(f"   🔍 Sample match metadata:")
                    
                    # Check for enhanced metadata fields
                    enhanced_fields = [
                        'relative_path', 'file_name', 'file_extension', 'file_size',
                        'line_number', 'column_start', 'column_end', 'matched_text',
                        'pattern', 'severity', 'priority', 'category', 'language',
                        'function_context', 'suggested_fix', 'documentation_link'
                    ]
                    
                    found_fields = []
                    for field in enhanced_fields:
                        if field in first_match:
                            found_fields.append(field)
                            enhanced_fields_found.add(field)
                    
                    print(f"      ✅ Enhanced fields: {len(found_fields)}/{len(enhanced_fields)}")
                    print(f"      📁 File: {first_match.get('relative_path', 'N/A')}")
                    print(f"      📍 Location: Line {first_match.get('line_number', 'N/A')}")
                    print(f"      🎯 Match: '{first_match.get('matched_text', 'N/A')}'")
                    print(f"      ⚠️  Severity: {first_match.get('severity', 'N/A')}")
                    print(f"      🔢 Priority: {first_match.get('priority', 'N/A')}")
                    
                    if 'function_context' in first_match:
                        func_ctx = first_match['function_context']
                        print(f"      🔧 Function: {func_ctx.get('function_name', 'N/A')}")
        
        # Summary
        print(f"\n📊 Enhanced Metadata Summary:")
        print(f"   • Gates with matches: {gates_with_matches}")
        print(f"   • Total pattern matches: {total_matches}")
        print(f"   • Enhanced fields found: {len(enhanced_fields_found)}")
        print(f"   • Fields: {', '.join(sorted(enhanced_fields_found))}")
        
        # Verification
        if total_matches > 0 and len(enhanced_fields_found) >= 10:
            print("\n✅ SUCCESS: Enhanced metadata is working!")
            print("   The API response includes detailed pattern match metadata.")
        elif total_matches > 0:
            print(f"\n⚠️  PARTIAL: Found matches but limited metadata ({len(enhanced_fields_found)} fields)")
        else:
            print("\n❌ FAILED: No pattern matches found with enhanced metadata")
        
        # Save sample response
        with open("sample_enhanced_api_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Sample response saved to: sample_enhanced_api_response.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_enhanced_metadata_in_api() 
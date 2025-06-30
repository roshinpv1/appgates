#!/usr/bin/env python3
"""
Example: How to access enhanced metadata from hard gate analysis
"""

import json
import requests
from pathlib import Path

def access_metadata_from_api():
    """Access metadata via API call"""
    
    # Example API call to get scan results
    scan_request = {
        "repository_url": "https://github.com/username/repo",
        "branch": "main"
    }
    
    # Start scan
    response = requests.post("http://localhost:8000/api/v1/scan", json=scan_request)
    scan_data = response.json()
    scan_id = scan_data.get("scan_id")
    
    # Get results (when completed)
    results_response = requests.get(f"http://localhost:8000/api/v1/scan/{scan_id}")
    results = results_response.json()
    
    # Access enhanced metadata
    for gate in results.get("gates", []):
        gate_name = gate.get("gate")
        matches = gate.get("matches", [])
        
        print(f"\n🚪 Gate: {gate_name}")
        print(f"   Found {len(matches)} pattern matches")
        
        for i, match in enumerate(matches[:3], 1):  # Show first 3
            print(f"\n   🔍 Match {i}:")
            print(f"      📁 File: {match['relative_path']}")
            print(f"      📍 Location: Line {match['line_number']}, Column {match['column_start']}-{match['column_end']}")
            print(f"      🎯 Matched: '{match['matched_text']}'")
            print(f"      ⚠️  Severity: {match['severity']}")
            print(f"      🔢 Priority: {match['priority']}/10")
            print(f"      🔧 Function: {match['function_context']['function_name']}")
            print(f"      💡 Fix: {match['suggested_fix']}")


def access_metadata_from_json():
    """Access metadata from saved JSON file"""
    
    # Load the JSON results file
    with open("enhanced_metadata_results.json", "r") as f:
        data = json.load(f)
    
    print("📊 Metadata Summary:")
    print(f"   • Total Matches: {data['summary']['total_matches']}")
    print(f"   • Available Fields: {len(data['summary']['enhanced_metadata_fields'])}")
    
    # Access specific metadata fields
    for i, match in enumerate(data["matches"][:2], 1):
        print(f"\n🔍 Match {i} Metadata:")
        
        # File information
        print(f"   📁 File Info:")
        print(f"      • Path: {match['relative_path']}")
        print(f"      • Size: {match['file_size']} bytes")
        print(f"      • Extension: {match['file_extension']}")
        
        # Pattern match details
        print(f"   🎯 Pattern Match:")
        print(f"      • Line: {match['line_number']}")
        print(f"      • Columns: {match['column_start']}-{match['column_end']}")
        print(f"      • Text: '{match['matched_text']}'")
        print(f"      • Pattern: {match['pattern']}")
        
        # Analysis information
        print(f"   📊 Analysis:")
        print(f"      • Severity: {match['severity']}")
        print(f"      • Priority: {match['priority']}/10")
        print(f"      • Category: {match['category']}")
        print(f"      • Gate Type: {match['gate_type']}")
        
        # Code context
        func_ctx = match['function_context']
        print(f"   🔧 Code Context:")
        print(f"      • Function: {func_ctx['function_name']}")
        print(f"      • Function Line: {func_ctx['function_line']}")
        print(f"      • Distance: {func_ctx['distance_from_function']} lines")
        
        # Remediation
        print(f"   💡 Remediation:")
        print(f"      • Fix: {match['suggested_fix']}")
        print(f"      • Docs: {match['documentation_link']}")


def filter_high_priority_issues():
    """Filter and show only high priority security issues"""
    
    with open("enhanced_metadata_results.json", "r") as f:
        data = json.load(f)
    
    # Filter high priority issues
    high_priority = [
        match for match in data["matches"] 
        if match.get("priority", 0) >= 7 and match.get("severity") == "HIGH"
    ]
    
    print(f"🚨 High Priority Security Issues: {len(high_priority)}")
    
    for i, match in enumerate(high_priority, 1):
        print(f"\n⚠️  Issue {i}:")
        print(f"   📁 {match['relative_path']}:{match['line_number']}")
        print(f"   🎯 {match['matched_text']}")
        print(f"   🔧 In function: {match['function_context']['function_name']}")
        print(f"   💡 {match['suggested_fix']}")


def export_metadata_for_external_tools():
    """Export metadata in format suitable for external tools"""
    
    with open("enhanced_metadata_results.json", "r") as f:
        data = json.load(f)
    
    # Convert to SARIF format (Static Analysis Results Interchange Format)
    sarif_results = {
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "Hard Gate Analyzer",
                    "version": "1.0.0"
                }
            },
            "results": []
        }]
    }
    
    for match in data["matches"]:
        sarif_result = {
            "ruleId": f"{match['gate_type']}_{match['category']}",
            "level": match['severity'].lower(),
            "message": {
                "text": match['suggested_fix']
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": match['relative_path']
                    },
                    "region": {
                        "startLine": match['line_number'],
                        "startColumn": match['column_start'],
                        "endColumn": match['column_end']
                    }
                }
            }],
            "properties": {
                "priority": match['priority'],
                "pattern": match['pattern'],
                "function": match['function_context']['function_name'],
                "documentation": match['documentation_link']
            }
        }
        sarif_results["runs"][0]["results"].append(sarif_result)
    
    # Save SARIF format
    with open("hard_gate_results.sarif", "w") as f:
        json.dump(sarif_results, f, indent=2)
    
    print("📤 Exported metadata to hard_gate_results.sarif for external tools")


if __name__ == "__main__":
    print("🔍 Enhanced Metadata Access Examples")
    print("=" * 50)
    
    # Example 1: Access from saved JSON
    if Path("enhanced_metadata_results.json").exists():
        print("\n1️⃣ Accessing metadata from JSON file:")
        access_metadata_from_json()
        
        print("\n2️⃣ Filtering high priority issues:")
        filter_high_priority_issues()
        
        print("\n3️⃣ Exporting for external tools:")
        export_metadata_for_external_tools()
    else:
        print("❌ No JSON results file found. Run the test first.")
    
    # Example 2: Access via API (commented out - requires running server)
    # print("\n4️⃣ Accessing metadata via API:")
    # access_metadata_from_api() 
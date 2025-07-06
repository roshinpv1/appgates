#!/usr/bin/env python3
"""
Two-Tier Reporting System Demo

This script demonstrates how to use the new two-tier reporting system 
that provides both summary and detailed reports.
"""

import requests
import json
import time
from pathlib import Path


def demo_two_tier_reporting():
    """Demonstrate the two-tier reporting system"""
    
    # API base URL (adjust as needed)
    base_url = "http://localhost:8000/api/v1"
    
    # Example: Start a scan (replace with your repository)
    print("🚀 Starting repository scan...")
    
    scan_request = {
        "repository_url": "https://github.com/example/sample-repo.git",
        "language": "python",
        "target_gates": ["structured_logs", "error_logs", "automated_tests"]
    }
    
    try:
        # Start scan
        response = requests.post(f"{base_url}/scan", json=scan_request)
        response.raise_for_status()
        scan_data = response.json()
        scan_id = scan_data["scan_id"]
        
        print(f"✅ Scan started with ID: {scan_id}")
        
        # Wait for scan completion (in real usage, you'd poll or use webhooks)
        print("⏳ Waiting for scan to complete...")
        time.sleep(30)  # Adjust based on your repository size
        
        # Check scan status
        status_response = requests.get(f"{base_url}/scan/{scan_id}/status")
        status_response.raise_for_status()
        status = status_response.json()
        
        if status["status"] != "completed":
            print(f"⚠️ Scan not yet complete. Status: {status['status']}")
            return
        
        print("✅ Scan completed! Demonstrating two-tier reporting...")
        
        # 1. Get report modes information
        print("\n📋 Getting available report modes...")
        modes_response = requests.get(f"{base_url}/reports/{scan_id}/modes")
        modes_response.raise_for_status()
        modes_info = modes_response.json()
        
        print("Available modes:")
        for mode, info in modes_info["available_modes"].items():
            print(f"  📊 {mode.upper()}: {info['description']}")
            print(f"     Features: {', '.join(info['features'][:3])}...")
        
        # 2. Generate Summary Report (JSON)
        print("\n📄 Generating Summary Report (JSON)...")
        summary_json_response = requests.get(f"{base_url}/reports/{scan_id}/json?report_mode=summary")
        summary_json_response.raise_for_status()
        summary_data = summary_json_response.json()
        
        print(f"Summary report generated:")
        print(f"  - Overall Score: {summary_data['score']:.1f}%")
        print(f"  - Total Gates: {len(summary_data['gates'])}")
        print(f"  - Report Mode: {summary_data['report_mode']}")
        
        # Save summary JSON
        summary_json_file = f"summary_report_{scan_id}.json"
        with open(summary_json_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"  📁 Saved to: {summary_json_file}")
        
        # 3. Generate Detailed Report (JSON)
        print("\n📄 Generating Detailed Report (JSON)...")
        detailed_json_response = requests.get(f"{base_url}/reports/{scan_id}/json?report_mode=detailed")
        detailed_json_response.raise_for_status()
        detailed_data = detailed_json_response.json()
        
        print(f"Detailed report generated:")
        print(f"  - Overall Score: {detailed_data['score']:.1f}%")
        print(f"  - Total Gates: {len(detailed_data['gates'])}")
        print(f"  - Report Mode: {detailed_data['report_mode']}")
        print(f"  - Additional metadata included: {bool(detailed_data.get('scan_metadata'))}")
        
        # Save detailed JSON
        detailed_json_file = f"detailed_report_{scan_id}.json"
        with open(detailed_json_file, 'w') as f:
            json.dump(detailed_data, f, indent=2)
        print(f"  📁 Saved to: {detailed_json_file}")
        
        # 4. Generate Summary HTML Report
        print("\n🌐 Generating Summary HTML Report...")
        summary_html_response = requests.get(f"{base_url}/reports/{scan_id}/summary")
        summary_html_response.raise_for_status()
        summary_html = summary_html_response.text
        
        summary_html_file = f"summary_report_{scan_id}.html"
        with open(summary_html_file, 'w', encoding='utf-8') as f:
            f.write(summary_html)
        print(f"  📁 Summary HTML saved to: {summary_html_file}")
        
        # 5. Generate Detailed HTML Report
        print("\n🌐 Generating Detailed HTML Report...")
        detailed_html_response = requests.get(f"{base_url}/reports/{scan_id}/detailed")
        detailed_html_response.raise_for_status()
        detailed_html = detailed_html_response.text
        
        detailed_html_file = f"detailed_report_{scan_id}.html"
        with open(detailed_html_file, 'w', encoding='utf-8') as f:
            f.write(detailed_html)
        print(f"  📁 Detailed HTML saved to: {detailed_html_file}")
        
        # 6. Demonstrate comments with both reports
        print("\n💬 Adding comments and regenerating reports...")
        comments = {
            "structured_logs": "Need to implement JSON formatting",
            "error_logs": "Exception handling looks good",
            "automated_tests": "Coverage could be improved"
        }
        
        comments_response = requests.post(f"{base_url}/reports/{scan_id}/comments", json=comments)
        comments_response.raise_for_status()
        comments_result = comments_response.json()
        
        print(f"✅ Comments added successfully:")
        print(f"  - Reports generated: {comments_result['reports_generated']}")
        print(f"  - Comments count: {comments_result['comments_count']}")
        
        # 7. Compare report sizes
        print("\n📊 Report Size Comparison:")
        summary_size = len(summary_html) / 1024  # KB
        detailed_size = len(detailed_html) / 1024  # KB
        
        print(f"  - Summary HTML: {summary_size:.1f} KB")
        print(f"  - Detailed HTML: {detailed_size:.1f} KB")
        print(f"  - Size difference: {(detailed_size - summary_size):.1f} KB ({((detailed_size/summary_size - 1) * 100):.1f}% larger)")
        
        print("\n🎉 Two-tier reporting demonstration completed!")
        print("\nGenerated files:")
        print(f"  📄 {summary_json_file} - Summary JSON report")
        print(f"  📄 {detailed_json_file} - Detailed JSON report")
        print(f"  🌐 {summary_html_file} - Summary HTML report")
        print(f"  🌐 {detailed_html_file} - Detailed HTML report")
        
        print("\n💡 Key Benefits:")
        print("  ✅ Summary reports provide quick overview for immediate action")
        print("  ✅ Detailed reports include full metadata for deep analysis")
        print("  ✅ Same API endpoints support both modes")
        print("  ✅ Backward compatibility maintained")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


def show_api_endpoints():
    """Show the available API endpoints for two-tier reporting"""
    
    print("🔌 Two-Tier Reporting API Endpoints:")
    print("=" * 50)
    
    endpoints = [
        {
            "method": "GET",
            "path": "/api/v1/reports/{scan_id}/modes",
            "description": "Get information about available report modes"
        },
        {
            "method": "GET", 
            "path": "/api/v1/reports/{scan_id}/summary",
            "description": "Generate summary HTML report"
        },
        {
            "method": "GET",
            "path": "/api/v1/reports/{scan_id}/detailed", 
            "description": "Generate detailed HTML report"
        },
        {
            "method": "GET",
            "path": "/api/v1/reports/{scan_id}/json?report_mode=summary",
            "description": "Generate summary JSON report"
        },
        {
            "method": "GET",
            "path": "/api/v1/reports/{scan_id}/json?report_mode=detailed",
            "description": "Generate detailed JSON report"
        },
        {
            "method": "GET",
            "path": "/api/v1/reports/{scan_id}",
            "description": "Legacy endpoint (defaults to summary for backward compatibility)"
        },
        {
            "method": "POST",
            "path": "/api/v1/reports/{scan_id}/comments",
            "description": "Update comments and regenerate both summary and detailed reports"
        }
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint['method']:4} {endpoint['path']}")
        print(f"       {endpoint['description']}")
        print()


if __name__ == "__main__":
    print("Two-Tier Reporting System Demo")
    print("=" * 40)
    
    print("\n1. Show API endpoints")
    print("2. Run full demo (requires running CodeGates API server)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        show_api_endpoints()
    elif choice == "2":
        demo_two_tier_reporting()
    else:
        print("Invalid choice. Please run again and select 1 or 2.") 
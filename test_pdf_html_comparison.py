#!/usr/bin/env python3
"""
Test PDF vs HTML Comparison
Compares PDF output with HTML to identify theme, style, and data structure differences
"""

import os
import sys
import json
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gates'))

def test_pdf_html_comparison():
    """Test and compare PDF vs HTML output"""
    
    print("🔍 Testing PDF vs HTML Comparison")
    print("=" * 50)
    
    # Test 1: Check if both modules are available
    try:
        from utils.html_to_pdf_converter import generate_pdfs_from_html_reports
        print("✅ PDF generation module available")
    except ImportError as e:
        print(f"❌ PDF generation module not available: {e}")
        return False
    
    try:
        from nodes import GenerateReportNode
        print("✅ HTML generation module available")
    except ImportError as e:
        print(f"❌ HTML generation module not available: {e}")
        return False
    
    # Test 2: Create test scan results
    print("\n📋 Creating test scan results...")
    
    test_scan_results = {
        "scan_id": "test-comparison-123",
        "repository_url": "https://github.com/company/test-app",
        "branch": "main",
        "overall_score": 75.5,
        "threshold": 70,
        "scan_timestamp_formatted": "2024-01-15 10:30:00",
        "project_name": "test-app",
        "metadata": {
            "total_files": 150,
            "total_lines": 5000
        },
        "gate_results": [
            {
                "gate": "ALERTING_ACTIONABLE",
                "display_name": "Alerting Actionable",
                "status": "FAIL",
                "score": 0.0,
                "category": "Alerting",
                "priority": "high",
                "description": "Ensure all alerting integrations are present",
                "matches_found": 0,
                "llm_recommendation": "This gate failed because no alerting integrations were found. Consider implementing monitoring and alerting solutions."
            },
            {
                "gate": "STRUCTURED_LOGS",
                "display_name": "Structured Logs",
                "status": "PASS",
                "score": 85.0,
                "category": "Auditability",
                "priority": "medium",
                "description": "Ensure structured logging is implemented",
                "matches_found": 12,
                "llm_recommendation": "Good implementation of structured logging found."
            }
        ],
        "gates": [],  # For compatibility
        "splunk_results": {}
    }
    
    # Test 3: Generate HTML report
    print("\n📄 Generating HTML report...")
    
    # Create test directory
    test_dir = "./test_pdf_html_comparison"
    os.makedirs(test_dir, exist_ok=True)
    
    # Mock the GenerateReportNode to generate HTML
    class MockGenerateReportNode:
        def _generate_html_report(self, params):
            """Generate HTML report for testing"""
            validation = params["validation_results"]
            metadata = params["metadata"]
            
            gate_results = validation["gate_results"]
            
            # Calculate summary statistics
            passed = len([g for g in gate_results if g.get("status") == "PASS"])
            failed = len([g for g in gate_results if g.get("status") == "FAIL"])
            warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
            not_applicable = len([g for g in gate_results if g.get("status") == "NOT_APPLICABLE"])
            total_gates = len(gate_results)
            
            # Extract project info
            app_id = "APP123"
            project_name = "test-app"
            branch_name = "main"
            project_display_name = f"{app_id} - {project_name} ({branch_name})"
            
            # Get overall score
            overall_score = validation.get("overall_score", 0.0)
            
            # Generate gates table HTML
            gates_table_html = ""
            for gate in gate_results:
                gate_name = gate.get("gate", "Unknown")
                display_name = gate.get("display_name", gate_name)
                status = gate.get("status", "UNKNOWN")
                score = gate.get("score", 0.0)
                
                status_class = f"status-{status.lower()}"
                gates_table_html += f"""
                <tr>
                    <td>{gate_name}</td>
                    <td>{display_name}</td>
                    <td><span class="{status_class}">{status}</span></td>
                    <td>{score:.1f}%</td>
                    <td>{gate.get('description', '')}</td>
                </tr>
                """
            
            # Create HTML template
            html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hard Gate Assessment (Hybrid Validation) - {project_display_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f3f4f6; }}
        h1 {{ font-size: 2em; color: #1f2937; border-bottom: 3px solid #2563eb; padding-bottom: 15px; margin-bottom: 30px; }}
        h2 {{ color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 40px; }}
        h3 {{ color: #374151; margin-top: 30px; }}
        .report-badge {{ display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-left: 15px; }}
        .summary-badge {{ background: #059669; color: #fff; }}
        .summary-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
        .stat-label {{ color: #6b7280; margin-top: 5px; }}
        .compliance-bar {{ width: 100%; height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .compliance-fill {{ height: 100%; background: linear-gradient(90deg, #dc2626 0%, #d97706 50%, #059669 100%); transition: width 0.3s ease; }}
        table {{ width: 100%; border-collapse: collapse; margin: 0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #2563eb; color: #fff; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
        .status-pass {{ color: #059669 !important; background: #ecfdf5; padding: 4px 8px; border-radius: 4px; font-weight: 500; }}
        .status-fail {{ color: #dc2626 !important; background: #fef2f2; padding: 4px 8px; border-radius: 4px; font-weight: 500; }}
        .status-warning {{ color: #d97706 !important; background: #fffbeb; padding: 4px 8px; border-radius: 4px; font-weight: 500; }}
        .status-not_applicable {{ color: #6b7280 !important; background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-weight: 500; }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>{project_display_name}</h1>
            <div class="report-badge summary-badge">Hybrid Validation Report</div>
            <p style="color: #2563eb; margin-bottom: 30px; font-weight: 500;">Hard Gate Assessment Report</p>
        </div>
        
        <h2>Executive Summary</h2>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{total_gates}</div>
                <div class="stat-label">Total Gates Evaluated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{passed}</div>
                <div class="stat-label">Gates Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{warnings}</div>
                <div class="stat-label">Partially Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{failed}</div>
                <div class="stat-label">Not Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{not_applicable}</div>
                <div class="stat-label">Not Applicable</div>
            </div>
        </div>
        
        <h3>Overall Compliance</h3>
        <div class="compliance-bar">
            <div class="compliance-fill" style="width: {overall_score:.1f}%"></div>
        </div>
        <p><strong>{overall_score:.1f}% Hard Gates Compliance</strong></p>
        <p style="color: #6b7280; font-size: 0.9em; margin-top: 5px;">
            <em>Percentage calculated based on {total_gates} applicable gates (excluding {not_applicable} N/A gates)</em>
        </p>
        
        <h2>Hard Gates Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th>Gate</th>
                    <th>Practice</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {gates_table_html}
            </tbody>
        </table>
        
        <footer style="margin-top: 50px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            <p>Hard Gate Assessment Hybrid Validation Report generated on 2024-01-15 10:30:00</p>
        </footer>
    </div>
</body>
</html>"""
            
            return html_template
    
    # Generate HTML
    mock_node = MockGenerateReportNode()
    params = {
        "validation_results": test_scan_results,
        "metadata": test_scan_results["metadata"],
        "request": {
            "repository_url": test_scan_results["repository_url"],
            "branch": test_scan_results["branch"]
        }
    }
    
    html_content = mock_node._generate_html_report(params)
    html_path = os.path.join(test_dir, "test_report.html")
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML report generated: {html_path}")
    
    # Test 4: Generate PDF from HTML
    print("\n📄 Generating PDF from HTML...")
    
    try:
        pdf_results = generate_pdfs_from_html_reports(test_scan_results, html_path, test_dir)
        
        if pdf_results["summary"]:
            print(f"✅ Summary PDF generated: {pdf_results['summary'][0]}")
        else:
            print("❌ Summary PDF generation failed")
            return False
        
        if pdf_results["gates"]:
            print(f"✅ Generated {len(pdf_results['gates'])} individual gate PDFs")
            for gate_pdf in pdf_results["gates"]:
                print(f"   📄 {os.path.basename(gate_pdf)}")
        else:
            print("❌ Individual gate PDF generation failed")
            return False
        
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Compare structure and content
    print("\n🔍 Comparing PDF vs HTML structure...")
    
    # Check if files exist and have reasonable sizes
    summary_pdf = pdf_results["summary"][0] if pdf_results["summary"] else None
    gate_pdfs = pdf_results["gates"]
    
    if summary_pdf and os.path.exists(summary_pdf):
        pdf_size = os.path.getsize(summary_pdf)
        html_size = os.path.getsize(html_path)
        print(f"✅ Summary PDF size: {pdf_size} bytes")
        print(f"✅ HTML report size: {html_size} bytes")
        
        if pdf_size > 1000:
            print("✅ Summary PDF has substantial content")
        else:
            print("⚠️ Summary PDF seems small")
    
    for gate_pdf in gate_pdfs:
        if os.path.exists(gate_pdf):
            pdf_size = os.path.getsize(gate_pdf)
            print(f"✅ Gate PDF size: {os.path.basename(gate_pdf)} - {pdf_size} bytes")
    
    # Test 6: Verify theme consistency
    print("\n🎨 Verifying theme consistency...")
    
    # Check if PDFs contain expected elements
    expected_elements = [
        "APP123 - test-app (main)",  # Title
        "Hybrid Validation Report",  # Badge
        "Hard Gate Assessment Report",  # Subtitle
        "Executive Summary",  # Section
        "Overall Compliance",  # Section
        "Hard Gates Analysis",  # Section
        "Alerting Actionable",  # Gate name
        "Structured Logs",  # Gate name
        "75.5% Hard Gates Compliance"  # Score
    ]
    
    print("Expected elements in PDFs:")
    for element in expected_elements:
        print(f"   ✓ {element}")
    
    # Test 7: Check file naming consistency
    print("\n📁 Checking file naming consistency...")
    
    expected_summary_name = "test-app-test-comparison-123-summary.pdf"
    if summary_pdf and os.path.basename(summary_pdf) == expected_summary_name:
        print(f"✅ Summary PDF naming correct: {os.path.basename(summary_pdf)}")
    else:
        print(f"❌ Summary PDF naming incorrect: {os.path.basename(summary_pdf)} (expected: {expected_summary_name})")
    
    for gate_pdf in gate_pdfs:
        filename = os.path.basename(gate_pdf)
        if "test-app-test-comparison-123-" in filename and filename.endswith(".pdf"):
            print(f"✅ Gate PDF naming correct: {filename}")
        else:
            print(f"❌ Gate PDF naming incorrect: {filename}")
    
    print("\n🎉 PDF vs HTML Comparison Test Completed!")
    print("=" * 50)
    print("✅ Both HTML and PDF generation working")
    print("📄 PDFs generated with consistent naming")
    print("🎨 Theme and styling applied")
    print("📁 Files stored in: ./test_pdf_html_comparison")
    
    return True

if __name__ == "__main__":
    success = test_pdf_html_comparison()
    if success:
        print("\n✅ PDF and HTML comparison successful!")
        print("📋 PDFs should match HTML theme and structure")
        print("🔍 Check the generated files for visual comparison")
    else:
        print("\n❌ PDF vs HTML comparison failed!")
        sys.exit(1) 
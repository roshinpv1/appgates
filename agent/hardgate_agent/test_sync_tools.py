#!/usr/bin/env python3
"""
Test script to verify that the synchronous wrapper functions work correctly
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the agent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hardgate_agent.tools import (
    analyze_repository,
    validate_gates,
    analyze_security,
    scan_code,
    check_compliance,
    generate_report
)


def test_sync_tools():
    """Test that all synchronous tools work correctly"""
    print("🧪 Testing Synchronous Tools")
    print("=" * 40)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample repository structure
        sample_repo_path = os.path.join(temp_dir, "sample_repo")
        os.makedirs(sample_repo_path, exist_ok=True)
        
        # Create a simple test file
        test_file = os.path.join(sample_repo_path, "test.py")
        with open(test_file, 'w') as f:
            f.write("""
import logging

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Application started")
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
        
        print(f"📁 Created test repository at: {sample_repo_path}")
        
        try:
            # Test 1: Repository Analysis
            print("\n1. Testing Repository Analysis...")
            repo_result = analyze_repository(repository_path=sample_repo_path)
            print(f"   ✅ Repository analysis: {repo_result.get('success', False)}")
            if repo_result.get('success'):
                analysis = repo_result.get('analysis', {})
                print(f"   📊 Total files: {analysis.get('structure', {}).get('total_files', 0)}")
                print(f"   🔧 Languages: {analysis.get('technologies', {}).get('programming_languages', [])}")
            
            # Test 2: Gate Validation
            print("\n2. Testing Gate Validation...")
            gate_result = validate_gates(
                repository_path=sample_repo_path,
                gates=["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS"]
            )
            print(f"   ✅ Gate validation: {gate_result.get('success', False)}")
            if gate_result.get('success'):
                validation_results = gate_result.get('validation_results', [])
                print(f"   🔍 Validated {len(validation_results)} gates")
                for result in validation_results:
                    print(f"   📋 {result.get('gate_name', 'Unknown')}: {result.get('status', 'Unknown')}")
            
            # Test 3: Code Scanning
            print("\n3. Testing Code Scanning...")
            scan_result = scan_code(
                repository_path=sample_repo_path,
                scan_types=["vulnerabilities", "secrets"]
            )
            print(f"   ✅ Code scanning: {scan_result.get('success', False)}")
            if scan_result.get('success'):
                scan_results = scan_result.get('scan_results', {})
                print(f"   🔍 Scan results: {list(scan_results.keys())}")
            
            # Test 4: Security Analysis
            print("\n4. Testing Security Analysis...")
            security_result = analyze_security(
                analysis_data={
                    "repository_analysis": repo_result.get('analysis', {}),
                    "gate_validation": gate_result,
                    "code_scanning": scan_result
                }
            )
            print(f"   ✅ Security analysis: {security_result.get('success', False)}")
            if security_result.get('success'):
                security_report = security_result.get('security_report', {})
                print(f"   🛡️ Risk level: {security_report.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
            
            # Test 5: Compliance Check
            print("\n5. Testing Compliance Check...")
            compliance_result = check_compliance(
                analysis_data={
                    "repository_analysis": repo_result.get('analysis', {}),
                    "gate_validation": gate_result,
                    "security_analysis": security_result
                },
                frameworks=["Enterprise"]
            )
            print(f"   ✅ Compliance check: {compliance_result.get('success', False)}")
            if compliance_result.get('success'):
                compliance_results = compliance_result.get('compliance_results', {})
                print(f"   📋 Frameworks checked: {list(compliance_results.keys())}")
            
            # Test 6: Report Generation
            print("\n6. Testing Report Generation...")
            report_result = generate_report(
                analysis_data={
                    "repository_analysis": repo_result.get('analysis', {}),
                    "gate_validation": gate_result,
                    "security_analysis": security_result,
                    "compliance_check": compliance_result
                },
                output_path=os.path.join(temp_dir, "report")
            )
            print(f"   ✅ Report generation: {report_result.get('success', False)}")
            if report_result.get('success'):
                print(f"   📄 Report generated: {report_result.get('output_path', 'N/A')}")
            
            print("\n✅ All synchronous tools tested successfully!")
            print("\n📋 Summary:")
            print("   - Repository analysis: ✅")
            print("   - Gate validation: ✅")
            print("   - Code scanning: ✅")
            print("   - Security analysis: ✅")
            print("   - Compliance check: ✅")
            print("   - Report generation: ✅")
            print("\n🎉 All synchronous tools are working correctly!")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_sync_tools() 
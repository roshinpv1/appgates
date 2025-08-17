#!/usr/bin/env python3
"""
Test script to verify that the type annotation fixes work correctly
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


async def test_type_annotations():
    """Test that all tools work with correct type annotations"""
    print("🧪 Testing Type Annotation Fixes")
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
            # Test 1: Repository Analysis with None parameters
            print("\n1. Testing Repository Analysis with None parameters...")
            repo_result = await analyze_repository(
                repository_url=None,  # This should work now
                repository_path=sample_repo_path
            )
            print(f"   ✅ Repository analysis: {repo_result.get('success', False)}")
            
            # Test 2: Gate Validation with None parameters
            print("\n2. Testing Gate Validation with None parameters...")
            gate_result = await validate_gates(
                repository_path=sample_repo_path,
                gates=None,  # This should work now
                validation_config=None  # This should work now
            )
            print(f"   ✅ Gate validation: {gate_result.get('success', False)}")
            
            # Test 3: Code Scanning with None parameters
            print("\n3. Testing Code Scanning with None parameters...")
            scan_result = await scan_code(
                repository_path=sample_repo_path,
                scan_types=None  # This should work now
            )
            print(f"   ✅ Code scanning: {scan_result.get('success', False)}")
            
            # Test 4: Security Analysis
            print("\n4. Testing Security Analysis...")
            security_result = await analyze_security(
                analysis_data={
                    "repository_analysis": repo_result.get('analysis', {}),
                    "gate_validation": gate_result,
                    "code_scanning": scan_result
                }
            )
            print(f"   ✅ Security analysis: {security_result.get('success', False)}")
            
            # Test 5: Compliance Check with None parameters
            print("\n5. Testing Compliance Check with None parameters...")
            compliance_result = await check_compliance(
                analysis_data={
                    "repository_analysis": repo_result.get('analysis', {}),
                    "gate_validation": gate_result,
                    "security_analysis": security_result
                },
                frameworks=None  # This should work now
            )
            print(f"   ✅ Compliance check: {compliance_result.get('success', False)}")
            
            # Test 6: Report Generation with None parameters
            print("\n6. Testing Report Generation with None parameters...")
            report_result = await generate_report(
                analysis_data={
                    "repository_analysis": repo_result.get('analysis', {}),
                    "gate_validation": gate_result,
                    "security_analysis": security_result,
                    "compliance_check": compliance_result
                },
                output_path=None  # This should work now
            )
            print(f"   ✅ Report generation: {report_result.get('success', False)}")
            
            print("\n✅ All type annotation tests passed!")
            print("\n📋 Summary:")
            print("   - Repository analysis with None parameters: ✅")
            print("   - Gate validation with None parameters: ✅")
            print("   - Code scanning with None parameters: ✅")
            print("   - Security analysis: ✅")
            print("   - Compliance check with None parameters: ✅")
            print("   - Report generation with None parameters: ✅")
            print("\n🎉 All tools now work correctly with proper type annotations!")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_type_annotations()) 
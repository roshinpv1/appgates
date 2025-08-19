#!/usr/bin/env python3
"""
Example usage of the HardGate Agent
Demonstrates how to use the agent for repository security analysis
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from agent import HardGateAgent

async def main():
    """Example usage of the HardGate Agent"""
    print("🚀 HardGate Agent Example Usage")
    print("=" * 50)
    
    try:
        # Initialize the HardGate Agent
        print("🔧 Initializing HardGate Agent...")
        agent = HardGateAgent()
        
        if not agent.agent:
            print("❌ Agent initialization failed. Please check Google ADK installation.")
            return
        
        print("✅ HardGate Agent initialized successfully!")
        print(f"📊 Agent has {len(agent.agent.tools)} tools configured")
        
        # Example repository analysis
        print("\n🔍 Example: Repository Analysis")
        print("-" * 30)
        
        # You can replace this with your actual repository URL
        repository_url = "https://github.com/example/security-test-repo"
        
        print(f"📁 Analyzing repository: {repository_url}")
        
        # Run complete analysis
        result = await agent.run_complete_analysis(
            repository_url=repository_url,
            branch="main",
            app_id="example-app-123"
        )
        
        if result.get("success"):
            print("✅ Analysis completed successfully!")
            
            # Display summary
            summary = result.get("summary", {})
            print(f"\n📋 Analysis Summary:")
            print(f"   - Repository: {summary.get('repository_url', 'N/A')}")
            print(f"   - Technologies: {summary.get('technologies_detected', [])}")
            print(f"   - Gates Validated: {summary.get('gates_validated', 0)}")
            print(f"   - Security Score: {summary.get('security_score', 0)}%")
            print(f"   - Risk Level: {summary.get('risk_level', 'Unknown')}")
            
            # Display recommendations
            recommendations = result.get("recommendations", [])
            if recommendations:
                print(f"\n💡 Top Recommendations:")
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"   {i}. {rec}")
            
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        
        # Example: Individual tool usage
        print("\n🔧 Example: Individual Tool Usage")
        print("-" * 30)
        
        # Example: Security scanning
        print("🔍 Running security scan...")
        scan_result = await agent.perform_security_scan(
            repository_path="/path/to/repository",
            scan_type="comprehensive"
        )
        
        if scan_result.get("success"):
            print("✅ Security scan completed!")
            scan_summary = scan_result.get("summary", {})
            print(f"   - Total Issues: {scan_summary.get('total_issues', 0)}")
            print(f"   - High Severity: {scan_summary.get('high_severity', 0)}")
            print(f"   - Risk Level: {scan_summary.get('risk_level', 'Unknown')}")
        
        # Example: Gate validation
        print("\n🎯 Running gate validation...")
        gates_result = await agent.validate_gates(
            repository_path="/path/to/repository",
            gates=["STRUCTURED_LOGS", "AUTOMATED_TESTS", "AUTO_SCALE"]
        )
        
        if gates_result.get("success"):
            print("✅ Gate validation completed!")
            validation_summary = gates_result.get("summary", {})
            print(f"   - Total Gates: {validation_summary.get('total_gates', 0)}")
            print(f"   - Passed: {validation_summary.get('passed_gates', 0)}")
            print(f"   - Failed: {validation_summary.get('failed_gates', 0)}")
            print(f"   - Compliance Rate: {validation_summary.get('compliance_rate', 0)}%")
        
        print("\n🎉 Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during example execution: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 
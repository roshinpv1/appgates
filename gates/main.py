#!/usr/bin/env python3
"""
CodeGates - PocketFlow Implementation
Main entry point for the hard gate validation system
"""

import sys
import os
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import create_validation_flow
from utils.hard_gates import HARD_GATES


def main():
    """Main function to run CodeGates validation"""
    
    # Get user input
    print("🚀 CodeGates - Hard Gate Validation System")
    print("=" * 50)
    
    repository_url = input("Enter repository URL: ").strip()
    if not repository_url:
        print("❌ Repository URL is required")
        return
    
    branch = input("Enter branch (default: main): ").strip() or "main"
    github_token = input("Enter GitHub token (optional): ").strip() or None
    threshold = input("Enter quality threshold (default: 70): ").strip()
    
    try:
        threshold = int(threshold) if threshold else 70
    except ValueError:
        threshold = 70
    
    print(f"\n🔍 Starting validation for: {repository_url}")
    print(f"   Branch: {branch}")
    print(f"   Threshold: {threshold}%")
    print(f"   Token: {'✓ Provided' if github_token else '✗ Not provided'}")
    
    # Initialize shared store
    shared = {
        "request": {
            "repository_url": repository_url,
            "branch": branch,
            "github_token": github_token,
            "threshold": threshold,
            "scan_id": str(uuid.uuid4())
        },
        "repository": {
            "local_path": None,
            "metadata": {}
        },
        "config": {
            "build_files": {},
            "config_files": {},
            "dependencies": []
        },
        "llm": {
            "prompt": None,
            "response": None,
            "patterns": {}
        },
        "validation": {
            "gate_results": [],
            "overall_score": 0.0
        },
        "reports": {
            "html_path": None,
            "json_path": None
        },
        "hard_gates": HARD_GATES,
        "temp_dir": tempfile.mkdtemp(prefix="codegates_"),
        "errors": []
    }
    
    try:
        # Create and run the validation flow
        validation_flow = create_validation_flow()
        validation_flow.run(shared)
        
        # Display results
        print("\n" + "=" * 60)
        print("🎯 VALIDATION COMPLETE")
        print("=" * 60)
        
        if shared["validation"]["gate_results"]:
            print(f"📊 Overall Score: {shared['validation']['overall_score']:.1f}%")
            print(f"📁 Total Files: {shared['repository']['metadata'].get('total_files', 0)}")
            print(f"📝 Total Lines: {shared['repository']['metadata'].get('total_lines', 0)}")
            
            # Show gate summary
            passed = len([g for g in shared["validation"]["gate_results"] if g.get("status") == "PASS"])
            failed = len([g for g in shared["validation"]["gate_results"] if g.get("status") == "FAIL"])
            total = len(shared["validation"]["gate_results"])
            
            print(f"✅ Passed Gates: {passed}/{total}")
            print(f"❌ Failed Gates: {failed}/{total}")
            
            # Show report locations
            if shared["reports"]["html_path"]:
                print(f"📄 HTML Report: {shared['reports']['html_path']}")
            if shared["reports"]["json_path"]:
                print(f"📄 JSON Report: {shared['reports']['json_path']}")
        else:
            print("❌ No validation results generated")
            
        # Show any errors
        if shared["errors"]:
            print("\n⚠️ Errors encountered:")
            for error in shared["errors"]:
                print(f"   - {error}")
    
    except Exception as e:
        print(f"\n❌ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup is handled by CleanupNode in the flow
        pass


if __name__ == "__main__":
    main() 
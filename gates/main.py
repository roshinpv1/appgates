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

from flow import create_static_only_flow
from utils.hard_gates import HARD_GATES


def main():
    """Main entry point for the CodeGates validation system"""
    print("🚀 CodeGates - Hard Gate Validation System")
    print("=" * 50)
    
    # For testing the -cd variant functionality, use a repository that might have a -cd variant
    repository_url = "https://github.com/kubernetes/kubernetes"
    branch = "main"
    github_token = ""
    threshold = 70
    
    print(f"🔍 Starting validation for: {repository_url}")
    print(f"   Branch: {branch}")
    print(f"   Threshold: {threshold}%")
    print(f"   Token: {'✓ Provided' if github_token else '✗ Not provided'}")
    
    # Initialize shared context
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
    
    # Create and run validation flow
    validation_flow = create_static_only_flow()
    validation_flow.run(shared) 
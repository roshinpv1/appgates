#!/usr/bin/env python3
"""
CodeGates Repository Scanner

This script makes a scan API call to the CodeGates server, waits for completion,
and saves the results (HTML and JSON reports) to the current directory.

Usage:
    python scan_repository.py <api_endpoint> <repository_url> <branch> <git_token>

Example:
    python scan_repository.py http://localhost:8000 https://github.com/owner/repo main your_github_token
"""

import requests
import json
import time
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, Any


class CodeGatesScanner:
    """CodeGates API Scanner with polling and result saving"""
    
    def __init__(self, api_endpoint: str):
        """Initialize scanner with API endpoint"""
        self.api_endpoint = api_endpoint.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CodeGates-Scanner/1.0'
        })
    
    def test_connection(self) -> bool:
        """Test connection to the API server"""
        try:
            response = self.session.get(f"{self.api_endpoint}/api/v1/health", timeout=10)
            if response.status_code == 200:
                print("✅ Connected to CodeGates API server")
                return True
            else:
                print(f"❌ API server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to API server: {e}")
            return False
    
    def start_scan(self, repository_url: str, branch: str, git_token: Optional[str] = None) -> str:
        """Start a new scan and return scan ID"""
        
        # Prepare request payload
        payload = {
            "repository_url": repository_url,
            "branch": branch,
            "report_format": "both"  # Get both HTML and JSON reports
        }
        
        # Add GitHub token if provided
        if git_token:
            payload["github_token"] = git_token
        
        print(f"🚀 Starting scan for repository: {repository_url}")
        print(f"📋 Branch: {branch}")
        print(f"🔑 Token provided: {'Yes' if git_token else 'No'}")
        
        try:
            response = self.session.post(
                f"{self.api_endpoint}/api/v1/scan",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                scan_id = result.get('scan_id')
                print(f"✅ Scan started successfully")
                print(f"🆔 Scan ID: {scan_id}")
                return scan_id
            else:
                error_detail = response.json().get('detail', 'Unknown error') if response.content else 'Unknown error'
                raise Exception(f"Failed to start scan: {error_detail}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while starting scan: {e}")
    
    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get current scan status"""
        try:
            response = self.session.get(
                f"{self.api_endpoint}/api/v1/scan/{scan_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise Exception(f"Scan {scan_id} not found")
            else:
                raise Exception(f"Failed to get scan status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while getting scan status: {e}")
    
    def wait_for_completion(self, scan_id: str, timeout_minutes: int = 15) -> Dict[str, Any]:
        """Wait for scan completion with progress updates"""
        print(f"⏳ Waiting for scan completion (timeout: {timeout_minutes} minutes)...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while True:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                raise Exception(f"Scan timed out after {timeout_minutes} minutes")
            
            # Get current status
            status_data = self.get_scan_status(scan_id)
            status = status_data.get('status', 'unknown')
            
            # Print progress
            progress = status_data.get('progress_percentage', 0)
            current_step = status_data.get('current_step', 'Unknown')
            step_details = status_data.get('step_details', '')
            
            if progress:
                print(f"📊 Progress: {progress}% - {current_step}")
            if step_details:
                print(f"   📋 {step_details}")
            
            # Check if completed
            if status == 'completed':
                print("✅ Scan completed successfully!")
                return status_data
            elif status == 'failed':
                errors = status_data.get('errors', [])
                error_msg = '; '.join(errors) if errors else 'Unknown error'
                raise Exception(f"Scan failed: {error_msg}")
            elif status == 'running':
                # Wait before next check
                time.sleep(5)
            else:
                raise Exception(f"Unexpected scan status: {status}")
    
    def download_report(self, scan_id: str, report_type: str) -> Optional[str]:
        """Download report content"""
        try:
            response = self.session.get(
                f"{self.api_endpoint}/api/v1/scan/{scan_id}/report/{report_type}",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"⚠️ Failed to download {report_type} report: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error downloading {report_type} report: {e}")
            return None
    
    def save_report(self, content: str, filename: str) -> bool:
        """Save report content to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 Saved report: {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to save {filename}: {e}")
            return False
    
    def scan_and_save(self, repository_url: str, branch: str, git_token: Optional[str] = None) -> bool:
        """Complete scan workflow: start scan, wait for completion, save results"""
        
        # Test connection first
        if not self.test_connection():
            return False
        
        try:
            # Start scan
            scan_id = self.start_scan(repository_url, branch, git_token)
            
            # Wait for completion
            result = self.wait_for_completion(scan_id)
            
            # Print summary
            print("\n📊 Scan Summary:")
            print(f"   Overall Score: {result.get('overall_score', 0):.1f}%")
            print(f"   Total Files: {result.get('total_files', 0)}")
            print(f"   Total Lines: {result.get('total_lines', 0)}")
            print(f"   Passed Gates: {result.get('passed_gates', 0)}")
            print(f"   Failed Gates: {result.get('failed_gates', 0)}")
            print(f"   Total Gates: {result.get('total_gates', 0)}")
            
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_id_short = scan_id[:8]  # Use first 8 characters of scan ID
            
            # Download and save HTML report
            html_content = self.download_report(scan_id, 'html')
            if html_content:
                html_filename = f"codegates_report_{scan_id_short}_{timestamp}.html"
                self.save_report(html_content, html_filename)
            
            # Download and save JSON report
            json_content = self.download_report(scan_id, 'json')
            if json_content:
                json_filename = f"codegates_report_{scan_id_short}_{timestamp}.json"
                self.save_report(json_content, json_filename)
            
            # Save scan summary
            summary_filename = f"codegates_summary_{scan_id_short}_{timestamp}.json"
            self.save_report(json.dumps(result, indent=2), summary_filename)
            
            print(f"\n✅ All reports saved successfully!")
            print(f"   📄 HTML Report: {html_filename if html_content else 'Not available'}")
            print(f"   📄 JSON Report: {json_filename if json_content else 'Not available'}")
            print(f"   📄 Summary: {summary_filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Scan failed: {e}")
            return False


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="CodeGates Repository Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_repository.py http://localhost:8000 https://github.com/owner/repo main
  python scan_repository.py http://localhost:8000 https://github.com/owner/repo main your_github_token
  python scan_repository.py https://api.codegates.com https://github.com/owner/private-repo develop your_token
        """
    )
    
    parser.add_argument(
        "api_endpoint",
        help="CodeGates API endpoint (e.g., http://localhost:8000)"
    )
    
    parser.add_argument(
        "repository_url",
        help="Git repository URL (e.g., https://github.com/owner/repo)"
    )
    
    parser.add_argument(
        "branch",
        help="Branch to scan (e.g., main, develop)"
    )
    
    parser.add_argument(
        "git_token",
        nargs='?',
        default=None,
        help="GitHub token for private repositories (optional for public repos)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Timeout in minutes for scan completion (default: 15)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.api_endpoint.startswith(('http://', 'https://')):
        print("❌ Error: API endpoint must start with http:// or https://")
        sys.exit(1)
    
    if not args.repository_url.startswith(('http://', 'https://')):
        print("❌ Error: Repository URL must start with http:// or https://")
        sys.exit(1)
    
    # Create scanner and run scan
    scanner = CodeGatesScanner(args.api_endpoint)
    
    print("🚀 CodeGates Repository Scanner")
    print("=" * 50)
    print(f"🔗 API Endpoint: {args.api_endpoint}")
    print(f"📁 Repository: {args.repository_url}")
    print(f"🌿 Branch: {args.branch}")
    print(f"⏱️ Timeout: {args.timeout} minutes")
    print("=" * 50)
    
    success = scanner.scan_and_save(
        repository_url=args.repository_url,
        branch=args.branch,
        git_token=args.git_token
    )
    
    if success:
        print("\n🎉 Scan completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Scan failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 
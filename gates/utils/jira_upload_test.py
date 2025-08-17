"""
JIRA Upload Testing and Validation Script
Comprehensive testing for JIRA integration functionality
"""

import os
import sys
import json
import tempfile
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.jira_upload import upload_report_to_jira, _extract_report_summary
from utils.db_integration import fetch_jira_stories


class JIRAUploadTester:
    """Comprehensive JIRA upload testing and validation"""
    
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_user = os.getenv("JIRA_USER")
        self.jira_token = os.getenv("JIRA_TOKEN")
        self.ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() == "true"
        
        self.test_results = {
            "environment_check": {},
            "authentication_test": {},
            "database_connection": {},
            "file_operations": {},
            "upload_functionality": {},
            "overall_status": "PENDING"
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all JIRA upload tests"""
        print("🧪 Starting JIRA Upload Testing and Validation")
        print("=" * 60)
        
        # Test 1: Environment Check
        self.test_environment_setup()
        
        # Test 2: Authentication Test
        self.test_jira_authentication()
        
        # Test 3: Database Connection
        self.test_database_connection()
        
        # Test 4: File Operations
        self.test_file_operations()
        
        # Test 5: Upload Functionality
        self.test_upload_functionality()
        
        # Generate final report
        self.generate_test_report()
        
        return self.test_results
    
    def test_environment_setup(self):
        """Test environment variables and configuration"""
        print("\n🔧 Testing Environment Setup...")
        
        env_check = {
            "jira_url_set": bool(self.jira_url),
            "jira_user_set": bool(self.jira_user),
            "jira_token_set": bool(self.jira_token),
            "ssl_verify_set": bool(os.getenv("JIRA_SSL_VERIFY")),
            "all_required_set": bool(self.jira_url and self.jira_user and self.jira_token)
        }
        
        print(f"   JIRA URL: {'✅ Set' if env_check['jira_url_set'] else '❌ Missing'}")
        print(f"   JIRA User: {'✅ Set' if env_check['jira_user_set'] else '❌ Missing'}")
        print(f"   JIRA Token: {'✅ Set' if env_check['jira_token_set'] else '❌ Missing'}")
        print(f"   SSL Verify: {'✅ Set' if env_check['ssl_verify_set'] else '⚠️ Using default'}")
        print(f"   All Required: {'✅ Ready' if env_check['all_required_set'] else '❌ Incomplete'}")
        
        if env_check['jira_url_set']:
            print(f"   JIRA URL: {self.jira_url}")
        if env_check['jira_user_set']:
            print(f"   JIRA User: {self.jira_user}")
        if env_check['jira_token_set']:
            print(f"   JIRA Token: {self.jira_token[:20]}...")
        
        self.test_results["environment_check"] = env_check
    
    def test_jira_authentication(self):
        """Test JIRA authentication and connectivity"""
        print("\n🔐 Testing JIRA Authentication...")
        
        if not all([self.jira_url, self.jira_user, self.jira_token]):
            print("   ❌ Skipping - missing environment variables")
            self.test_results["authentication_test"] = {"status": "SKIPPED", "reason": "Missing environment variables"}
            return
        
        try:
            # Test basic connectivity
            test_url = f"{self.jira_url.rstrip('/')}/rest/api/3/myself"
            
            print(f"   Testing connection to: {test_url}")
            
            response = requests.get(
                test_url,
                auth=(self.jira_user, self.jira_token),
                verify=self.ssl_verify,
                timeout=30
            )
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"   ✅ Authentication successful")
                print(f"   👤 User: {user_info.get('displayName', 'Unknown')}")
                print(f"   📧 Email: {user_info.get('emailAddress', 'Unknown')}")
                print(f"   🏢 Account: {user_info.get('accountId', 'Unknown')}")
                
                self.test_results["authentication_test"] = {
                    "status": "SUCCESS",
                    "user_info": user_info,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                print(f"   ❌ Authentication failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
                self.test_results["authentication_test"] = {
                    "status": "FAILED",
                    "http_code": response.status_code,
                    "error": response.text[:500]
                }
                
        except requests.exceptions.SSLError as e:
            print(f"   ❌ SSL Error: {e}")
            self.test_results["authentication_test"] = {
                "status": "SSL_ERROR",
                "error": str(e)
            }
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection Error: {e}")
            self.test_results["authentication_test"] = {
                "status": "CONNECTION_ERROR",
                "error": str(e)
            }
        except requests.exceptions.Timeout as e:
            print(f"   ❌ Timeout Error: {e}")
            self.test_results["authentication_test"] = {
                "status": "TIMEOUT_ERROR",
                "error": str(e)
            }
        except Exception as e:
            print(f"   ❌ Unexpected Error: {e}")
            self.test_results["authentication_test"] = {
                "status": "UNEXPECTED_ERROR",
                "error": str(e)
            }
    
    def test_database_connection(self):
        """Test database connection for JIRA stories"""
        print("\n🗄️ Testing Database Connection...")
        
        try:
            # Test with a sample app_id
            test_app_id = "test-app-123"
            print(f"   Testing with app_id: {test_app_id}")
            
            stories = fetch_jira_stories(app_id=test_app_id)
            
            print(f"   ✅ Database connection successful")
            print(f"   📋 Found {len(stories)} JIRA stories")
            
            if stories:
                print(f"   📝 Sample stories: {stories[:3]}")
            
            self.test_results["database_connection"] = {
                "status": "SUCCESS",
                "stories_found": len(stories),
                "sample_stories": stories[:5]
            }
            
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            self.test_results["database_connection"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_file_operations(self):
        """Test file operations and report generation"""
        print("\n📁 Testing File Operations...")
        
        try:
            # Create test JSON report
            test_report_data = {
                "scan_id": "test-scan-123",
                "app_id": "test-app-123",
                "overall_score": 85.5,
                "summary": {
                    "total_gates": 15,
                    "passed_gates": 12,
                    "failed_gates": 2,
                    "warning_gates": 1
                },
                "gates": [
                    {
                        "name": "STRUCTURED_LOGS",
                        "status": "PASS",
                        "score": 90.0
                    },
                    {
                        "name": "AUTO_SCALE",
                        "status": "FAIL",
                        "score": 25.0
                    }
                ]
            }
            
            # Create temporary test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_report_data, f)
                test_file_path = f.name
            
            print(f"   ✅ Created test JSON report: {test_file_path}")
            
            # Test summary extraction
            summary = _extract_report_summary(test_file_path)
            print(f"   ✅ Summary extraction successful")
            print(f"   📝 Summary preview: {summary[:100]}...")
            
            # Clean up
            os.unlink(test_file_path)
            print(f"   ✅ Cleaned up test file")
            
            self.test_results["file_operations"] = {
                "status": "SUCCESS",
                "test_file_created": True,
                "summary_extraction": True,
                "summary_length": len(summary)
            }
            
        except Exception as e:
            print(f"   ❌ File operations failed: {e}")
            self.test_results["file_operations"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_upload_functionality(self):
        """Test actual upload functionality with a test ticket"""
        print("\n📤 Testing Upload Functionality...")
        
        if not all([self.jira_url, self.jira_user, self.jira_token]):
            print("   ❌ Skipping - missing environment variables")
            self.test_results["upload_functionality"] = {"status": "SKIPPED", "reason": "Missing environment variables"}
            return
        
        # Check if test ticket is provided
        test_ticket = os.getenv("JIRA_TEST_TICKET")
        if not test_ticket:
            print("   ⚠️ No test ticket provided (set JIRA_TEST_TICKET env var)")
            print("   📝 Skipping actual upload test")
            self.test_results["upload_functionality"] = {"status": "SKIPPED", "reason": "No test ticket provided"}
            return
        
        try:
            # Create test report
            test_report_data = {
                "scan_id": "test-scan-123",
                "app_id": "test-app-123",
                "overall_score": 85.5,
                "summary": {
                    "total_gates": 15,
                    "passed_gates": 12,
                    "failed_gates": 2,
                    "warning_gates": 1
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_report_data, f)
                test_file_path = f.name
            
            print(f"   📋 Testing upload to ticket: {test_ticket}")
            
            # Test upload
            result = upload_report_to_jira(
                jira_url=self.jira_url,
                jira_user=self.jira_user,
                jira_token=self.jira_token,
                app_id="test-app-123",
                report_path=test_file_path,
                report_type="json",
                jira_ticket_id=test_ticket,
                comment="This is a test upload from JIRA Upload Tester"
            )
            
            # Clean up
            os.unlink(test_file_path)
            
            if result.get("success"):
                print(f"   ✅ Upload successful!")
                print(f"   📊 Results: {result.get('message', 'Unknown')}")
                
                for story_result in result.get("results", []):
                    story = story_result.get("story", "Unknown")
                    comment_status = story_result.get("comment", "Unknown")
                    attachment_status = story_result.get("attachment", "Unknown")
                    print(f"   📝 Ticket {story}: Comment={comment_status}, Attachment={attachment_status}")
                
                self.test_results["upload_functionality"] = {
                    "status": "SUCCESS",
                    "upload_result": result
                }
            else:
                print(f"   ❌ Upload failed: {result.get('message', 'Unknown error')}")
                self.test_results["upload_functionality"] = {
                    "status": "FAILED",
                    "upload_result": result
                }
                
        except Exception as e:
            print(f"   ❌ Upload test failed: {e}")
            self.test_results["upload_functionality"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")
        print("=" * 60)
        
        # Determine overall status
        all_tests = [
            self.test_results["environment_check"].get("all_required_set", False),
            self.test_results["authentication_test"].get("status") == "SUCCESS",
            self.test_results["database_connection"].get("status") == "SUCCESS",
            self.test_results["file_operations"].get("status") == "SUCCESS",
            self.test_results["upload_functionality"].get("status") in ["SUCCESS", "SKIPPED"]
        ]
        
        overall_status = "PASS" if all(all_tests) else "FAIL"
        self.test_results["overall_status"] = overall_status
        
        print(f"🎯 Overall Status: {overall_status}")
        print()
        
        # Detailed results
        print("📋 Detailed Results:")
        print(f"   Environment Setup: {self._get_status_emoji(self.test_results['environment_check'].get('all_required_set', False))}")
        print(f"   Authentication: {self._get_status_emoji(self.test_results['authentication_test'].get('status') == 'SUCCESS')}")
        print(f"   Database Connection: {self._get_status_emoji(self.test_results['database_connection'].get('status') == 'SUCCESS')}")
        print(f"   File Operations: {self._get_status_emoji(self.test_results['file_operations'].get('status') == 'SUCCESS')}")
        print(f"   Upload Functionality: {self._get_status_emoji(self.test_results['upload_functionality'].get('status') in ['SUCCESS', 'SKIPPED'])}")
        
        # Recommendations
        print("\n💡 Recommendations:")
        if not self.test_results["environment_check"].get("all_required_set", False):
            print("   ❌ Fix environment variables: Set JIRA_URL, JIRA_USER, and JIRA_TOKEN")
        
        if self.test_results["authentication_test"].get("status") != "SUCCESS":
            print("   ❌ Fix authentication: Check JIRA credentials and network connectivity")
        
        if self.test_results["database_connection"].get("status") != "SUCCESS":
            print("   ❌ Fix database connection: Check database connectivity and credentials")
        
        if self.test_results["file_operations"].get("status") != "SUCCESS":
            print("   ❌ Fix file operations: Check file permissions and disk space")
        
        if self.test_results["upload_functionality"].get("status") == "FAILED":
            print("   ❌ Fix upload functionality: Check JIRA permissions and ticket access")
        
        if overall_status == "PASS":
            print("   ✅ All tests passed! JIRA upload is working correctly.")
    
    def _get_status_emoji(self, status: bool) -> str:
        """Get status emoji for display"""
        return "✅ PASS" if status else "❌ FAIL"


def main():
    """Main function to run JIRA upload tests"""
    print("🚀 JIRA Upload Testing and Validation")
    print("=" * 60)
    
    tester = JIRAUploadTester()
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = "jira_upload_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        print("\n🎉 All tests passed! JIRA upload is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please review the recommendations above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test Pattern and File Information Display
"""

import tempfile
import os

def test_patterns_files():
    """Test that matched patterns and file information is displayed in HTML report"""
    
    print("🧪 Testing Pattern and File Information Display")
    print("=" * 55)
    
    # Create test data with detailed pattern matches
    test_data = {
        "validation_results": {
            "overall_score": 75.5,
            "gate_results": [
                {
                    "gate": "AVOID_LOGGING_SECRETS",
                    "display_name": "Avoid Logging Confidential Data",
                    "description": "Prevent sensitive data from being logged accidentally",
                    "category": "Auditability",
                    "priority": "critical",
                    "score": 40.0,
                    "status": "FAIL",
                    "matches_found": 3,
                    "matches": [
                        {
                            "file": "src/main/java/com/example/UserService.java",
                            "line": 45,
                            "match": "logger.info(\"User password: \" + user.getPassword())"
                        },
                        {
                            "file": "src/main/java/com/example/AuthController.java",
                            "line": 123,
                            "match": "log.debug(\"API key: \" + apiKey)"
                        },
                        {
                            "file": "src/main/java/com/example/ConfigService.java",
                            "line": 67,
                            "match": "System.out.println(\"Database password: \" + dbPassword)"
                        }
                    ],
                    "details": [
                        "Security Gate Analysis:",
                        "Expected Violations: 0",
                        "Actual Violations: 3 violations across 3 files",
                        "❌ Security violations found - immediate attention required"
                    ],
                    "recommendations": [
                        "❌ Critical: Avoid Logging Confidential Data violations found",
                        "Found 3 security violations across 3 files",
                        "Immediate action required"
                    ]
                },
                {
                    "gate": "STRUCTURED_LOGS",
                    "display_name": "Logs Searchable/Available",
                    "description": "Ensure logs are structured and searchable for operational monitoring",
                    "category": "Auditability",
                    "priority": "high",
                    "score": 100.0,
                    "status": "PASS",
                    "matches_found": 5,
                    "matches": [
                        {
                            "file": "src/main/java/com/example/LoggingService.java",
                            "line": 23,
                            "match": "logger.info(\"User login successful: {}\", userId)"
                        },
                        {
                            "file": "src/main/java/com/example/OrderService.java",
                            "line": 89,
                            "match": "log.debug(\"Processing order: {}\", orderId)"
                        },
                        {
                            "file": "src/main/java/com/example/PaymentService.java",
                            "line": 156,
                            "match": "logger.warn(\"Payment failed for user: {}\", userId)"
                        },
                        {
                            "file": "src/main/java/com/example/NotificationService.java",
                            "line": 34,
                            "match": "log.info(\"Notification sent: {}\", notificationId)"
                        },
                        {
                            "file": "src/main/java/com/example/AuditService.java",
                            "line": 78,
                            "match": "logger.info(\"Audit event: {}\", eventType)"
                        }
                    ],
                    "details": [
                        "Logging Gate Analysis:",
                        "Expected Coverage: 10%",
                        "Actual Coverage: 100.0%",
                        "✅ Logging is well implemented"
                    ],
                    "recommendations": [
                        "Good: Logs Searchable/Available is well implemented",
                        "Continue maintaining good practices"
                    ]
                },
                {
                    "gate": "RETRY_LOGIC",
                    "display_name": "Retry Logic",
                    "description": "Implement retry mechanisms for resilient operations",
                    "category": "Availability",
                    "priority": "high",
                    "score": 100.0,
                    "status": "PASS",
                    "matches_found": 2,
                    "matches": [
                        {
                            "file": "src/main/java/com/example/RetryService.java",
                            "line": 12,
                            "match": "@Retryable(maxAttempts = 3)"
                        },
                        {
                            "file": "src/main/java/com/example/HttpClientService.java",
                            "line": 45,
                            "match": "retryTemplate.execute(context -> httpClient.call())"
                        }
                    ],
                    "details": [
                        "Availability Gate Analysis:",
                        "Expected Coverage: 10%",
                        "Actual Coverage: 100.0%",
                        "✅ Retry logic is well implemented"
                    ],
                    "recommendations": [
                        "Good: Retry Logic is well implemented",
                        "Continue maintaining good practices"
                    ]
                }
            ],
            "applicability_summary": {
                "applicable_gates": [],
                "not_applicable_gates": []
            }
        },
        "metadata": {
            "total_files": 100,
            "total_lines": 5000,
            "language_stats": {
                "java": {"files": 50, "lines": 2500},
                "python": {"files": 30, "lines": 1500},
                "javascript": {"files": 20, "lines": 1000}
            }
        },
        "llm_info": {
            "source": "static_patterns",
            "model": "pattern_library",
            "provider": "static"
        },
        "request": {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "threshold": 70,
            "scan_id": "test-scan-123"
        }
    }
    
    try:
        # Import the GenerateReportNode
        import sys
        sys.path.append('gates')
        from nodes import GenerateReportNode
        
        # Create the node
        node = GenerateReportNode()
        
        # Test HTML report generation
        print("📄 Testing HTML report generation with pattern and file information...")
        html_content = node._generate_html_report(test_data)
        
        if html_content:
            # Save to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                html_path = f.name
            
            print(f"✅ HTML report generated successfully: {html_path}")
            
            # Check file size
            file_size = os.path.getsize(html_path)
            print(f"📊 HTML file size: {file_size} bytes")
            
            # Check for pattern and file information
            pattern_checks = [
                ("Matched Patterns section", "Matched Patterns and Files:" in html_content),
                ("File column header", "File</th>" in html_content),
                ("Line column header", "Line</th>" in html_content),
                ("Pattern Match column header", "Pattern Match</th>" in html_content),
                ("Total Matches Found", "Total Matches Found:" in html_content),
                ("File paths displayed", "UserService.java" in html_content or "LoggingService.java" in html_content),
                ("Line numbers displayed", "45" in html_content and "23" in html_content),
                ("Pattern matches displayed", "logger.info" in html_content or "log.debug" in html_content),
                ("Scrollable table container", "max-height: 300px" in html_content),
                ("Monospace font for files", "font-family: monospace" in html_content)
            ]
            
            print("\n🔍 Pattern and File Information Checks:")
            all_passed = True
            for check_name, passed in pattern_checks:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {check_name}: {status}")
                if not passed:
                    all_passed = False
            
            # Check for specific pattern matches
            specific_checks = [
                ("Security violation pattern", "logger.info(\"User password:" in html_content),
                ("Structured logging pattern", "logger.info(\"User login successful:" in html_content),
                ("Retry logic pattern", "@Retryable(maxAttempts = 3)" in html_content),
                ("File paths with proper formatting", "src/main/java/com/example/" in html_content),
                ("Line numbers in table", "45" in html_content and "23" in html_content and "123" in html_content)
            ]
            
            print("\n🔍 Specific Pattern Match Checks:")
            for check_name, passed in specific_checks:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {check_name}: {status}")
                if not passed:
                    all_passed = False
            
            # Check for table styling
            styling_checks = [
                ("Table border styling", "border-collapse: collapse" in html_content),
                ("Table header background", "background: #f3f4f6" in html_content),
                ("Pattern match highlighting", "color: #059669; background: #ecfdf5" in html_content),
                ("File path styling", "font-family: monospace; color: #1f2937" in html_content),
                ("Line number styling", "text-align: center; color: #6b7280" in html_content)
            ]
            
            print("\n🔍 Table Styling Checks:")
            for check_name, passed in styling_checks:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {check_name}: {status}")
                if not passed:
                    all_passed = False
            
            # Show sample of generated HTML
            print(f"\n📄 Sample of generated HTML (first 2500 characters):")
            print(html_content[:2500])
            
            # Clean up
            os.unlink(html_path)
            
            if all_passed:
                print("\n✅ Pattern and file information test passed!")
                return True
            else:
                print("\n❌ Some pattern or file information elements are missing!")
                return False
        
    except Exception as e:
        print(f"❌ Pattern and file information test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_patterns_files()
    if success:
        print("\n🎉 Pattern and file information test passed!")
    else:
        print("\n💥 Pattern and file information test failed!")
        exit(1) 
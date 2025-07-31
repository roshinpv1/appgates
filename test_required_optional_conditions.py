#!/usr/bin/env python3
"""
Test script to demonstrate required vs optional conditions
"""

import sys
import os
sys.path.append('gates')

from criteria_evaluator import CriteriaEvaluator, PatternMatch

def test_required_optional_conditions():
    """Test required vs optional conditions"""
    
    # Sample codebase files
    codebase_files = [
        "src/main/java/com/example/Controller.java",
        "src/main/java/com/example/Service.java",
        "src/main/java/com/example/Model.java"
    ]
    
    # Test Case 1: All conditions met (required + optional)
    file_contents_1 = {
        "src/main/java/com/example/Controller.java": """
        import org.springframework.http.HttpStatus;
        import org.springframework.http.ResponseEntity;
        
        @RestController
        public class Controller {
            @GetMapping("/users")
            public ResponseEntity<User> getUser() {
                return ResponseEntity.status(HttpStatus.OK).body(new User());
            }
            
            @PostMapping("/users")
            public ResponseEntity<User> createUser() {
                return ResponseEntity.status(HttpStatus.CREATED).body(new User());
            }
        }
        """,
        "src/main/java/com/example/Service.java": """
        public class Service {
            public void process() {
                // No HTTP status codes here
            }
        }
        """,
        "src/main/java/com/example/Model.java": """
        public class User {
            private String name;
        }
        """
    }
    
    # Test Case 2: Only required conditions met (no optional)
    file_contents_2 = {
        "src/main/java/com/example/Controller.java": """
        @RestController
        public class Controller {
            @GetMapping("/users")
            public ResponseEntity<User> getUser() {
                return ResponseEntity.ok(new User());
            }
            
            @PostMapping("/users")
            public ResponseEntity<User> createUser() {
                return ResponseEntity.status(201).body(new User());
            }
        }
        """,
        "src/main/java/com/example/Service.java": """
        public class Service {
            public void process() {
                // No HTTP status codes here
            }
        }
        """,
        "src/main/java/com/example/Model.java": """
        public class User {
            private String name;
        }
        """
    }
    
    # Test Case 3: Missing required condition (should fail)
    file_contents_3 = {
        "src/main/java/com/example/Controller.java": """
        import org.springframework.http.HttpStatus;
        
        @RestController
        public class Controller {
            @GetMapping("/users")
            public ResponseEntity<User> getUser() {
                return ResponseEntity.ok(new User());
            }
        }
        """,
        "src/main/java/com/example/Service.java": """
        public class Service {
            public void process() {
                // No HTTP status codes here
            }
        }
        """,
        "src/main/java/com/example/Model.java": """
        public class User {
            private String name;
        }
        """
    }
    
    # HTTP_CODES_WITH_OPTIONAL_IMPORT criteria
    http_codes_criteria = {
        "operator": "AND",
        "conditions": [
            {
                "name": "required_conditions",
                "type": "criteria",
                "operator": "AND",
                "weight": 8.0,
                "criteria": {
                    "operator": "AND",
                    "conditions": [
                        {
                            "name": "http_status_usage",
                            "type": "pattern",
                            "operator": "OR",
                            "weight": 4.0,
                            "patterns": [
                                {
                                    "pattern": "(HttpStatus|StatusCode)\\s*\\.\\s*(\\w+|\\d{3})",
                                    "weight": 4.0,
                                    "description": "Detects direct references to HTTP status code enums or constants"
                                },
                                {
                                    "pattern": "ResponseEntity\\.status\\(",
                                    "weight": 4.0,
                                    "description": "Detects ResponseEntity status usage"
                                }
                            ]
                        },
                        {
                            "name": "status_code_values",
                            "type": "pattern",
                            "operator": "OR",
                            "weight": 4.0,
                            "patterns": [
                                {
                                    "pattern": "200|201|400|401|403|404|500",
                                    "weight": 4.0,
                                    "description": "Detects HTTP status code values"
                                },
                                {
                                    "pattern": "OK|CREATED|BAD_REQUEST|UNAUTHORIZED|FORBIDDEN|NOT_FOUND|INTERNAL_SERVER_ERROR",
                                    "weight": 4.0,
                                    "description": "Detects HTTP status code constants"
                                }
                            ]
                        }
                    ]
                }
            },
            {
                "name": "optional_import",
                "type": "pattern",
                "operator": "OR",
                "weight": 2.0,
                "patterns": [
                    {
                        "pattern": "(?i)\\bimport\\s+[\\w.]+\\s*\\.\\s*(HttpStatus|StatusCode|HttpStatusCodes)\\s*(?:\\s|;|$)",
                        "weight": 2.0,
                        "description": "Optional: Detects imports of HTTP status code classes"
                    }
                ]
            }
        ]
    }
    
    print("=== Test Case 1: All conditions met (required + optional) ===")
    print("Expected: PASS (both required conditions + optional import)")
    
    evaluator_1 = CriteriaEvaluator(codebase_files, file_contents_1)
    result_1 = evaluator_1.evaluate_criteria(http_codes_criteria)
    
    print(f"Result: {'PASS' if result_1.passed else 'FAIL'}")
    print(f"Matches found: {len(result_1.matches)}")
    
    for condition in result_1.condition_results:
        print(f"  Condition '{condition.condition_name}': {'PASS' if condition.passed else 'FAIL'}")
        print(f"    Matches: {len(condition.matches)}")
        for match in condition.matches[:3]:  # Show first 3 matches
            print(f"      - {match.file}: {match.pattern}")
    
    print()
    
    print("=== Test Case 2: Only required conditions met (no optional) ===")
    print("Expected: PASS (required conditions met, optional missing)")
    
    evaluator_2 = CriteriaEvaluator(codebase_files, file_contents_2)
    result_2 = evaluator_2.evaluate_criteria(http_codes_criteria)
    
    print(f"Result: {'PASS' if result_2.passed else 'FAIL'}")
    print(f"Matches found: {len(result_2.matches)}")
    
    for condition in result_2.condition_results:
        print(f"  Condition '{condition.condition_name}': {'PASS' if condition.passed else 'FAIL'}")
        print(f"    Matches: {len(condition.matches)}")
        for match in condition.matches[:3]:  # Show first 3 matches
            print(f"      - {match.file}: {match.pattern}")
    
    print()
    
    print("=== Test Case 3: Missing required condition ===")
    print("Expected: FAIL (missing required status code values)")
    
    evaluator_3 = CriteriaEvaluator(codebase_files, file_contents_3)
    result_3 = evaluator_3.evaluate_criteria(http_codes_criteria)
    
    print(f"Result: {'PASS' if result_3.passed else 'FAIL'}")
    print(f"Matches found: {len(result_3.matches)}")
    
    for condition in result_3.condition_results:
        print(f"  Condition '{condition.condition_name}': {'PASS' if condition.passed else 'FAIL'}")
        print(f"    Matches: {len(condition.matches)}")
        for match in condition.matches[:3]:  # Show first 3 matches
            print(f"      - {match.file}: {match.pattern}")
    
    print()
    
    # Summary
    print("=== SUMMARY ===")
    print(f"Test 1 (All conditions): {'✅ PASS' if result_1.passed else '❌ FAIL'}")
    print(f"Test 2 (Required only): {'✅ PASS' if result_2.passed else '❌ FAIL'}")
    print(f"Test 3 (Missing required): {'✅ PASS' if result_3.passed else '❌ FAIL'}")
    
    # Expected results
    expected_results = [True, True, False]
    actual_results = [result_1.passed, result_2.passed, result_3.passed]
    
    if actual_results == expected_results:
        print("\n🎉 Required vs Optional conditions are working correctly!")
        print("\n📋 Key Points:")
        print("  • Required conditions (nested AND): Both must pass")
        print("  • Optional conditions: Can be missing and still PASS")
        print("  • Overall result: PASS if required conditions are met")
    else:
        print("\n❌ Required vs Optional conditions have issues!")
        for i, (expected, actual) in enumerate(zip(expected_results, actual_results)):
            if expected != actual:
                print(f"  Test {i+1}: Expected {expected}, Got {actual}")

if __name__ == "__main__":
    test_required_optional_conditions() 
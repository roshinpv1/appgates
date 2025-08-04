#!/usr/bin/env python3
"""
Comprehensive test script to verify file-centric approach works for all gates.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
import time

# Add the gates directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gates'))

def create_test_repository():
    """Create a comprehensive test repository with various file types and patterns"""
    print("📁 Creating comprehensive test repository...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        
        # Create various file types with patterns that should match different gates
        test_files = [
            # JavaScript files with logging patterns
            ("src/app.js", [
                "console.log('User logged in');",
                "console.error('Database connection failed');",
                "logger.info('Request processed');",
                "console.warn('Deprecated function called');",
                "debug('Processing user data');"
            ]),
            
            # Python files with error handling
            ("src/main.py", [
                "try:",
                "    result = process_data()",
                "except Exception as e:",
                "    logger.error(f'Error: {e}')",
                "    raise",
                "finally:",
                "    cleanup()",
                "print('Processing complete')"
            ]),
            
            # Java files with structured logging
            ("src/Service.java", [
                "import org.slf4j.Logger;",
                "import org.slf4j.LoggerFactory;",
                "private static final Logger logger = LoggerFactory.getLogger(Service.class);",
                "logger.info(\"Service started\");",
                "logger.error(\"Failed to process request\", exception);",
                "logger.warn(\"Resource usage high\");"
            ]),
            
            # Configuration files
            ("config/app.config", [
                "log_level=INFO",
                "log_file=/var/log/app.log",
                "correlation_id_header=X-Correlation-ID",
                "structured_logging=true"
            ]),
            
            # Test files
            ("tests/test_app.py", [
                "import unittest",
                "class TestApp(unittest.TestCase):",
                "    def test_user_login(self):",
                "        result = login_user('test', 'password')",
                "        self.assertTrue(result)",
                "    def test_error_handling(self):",
                "        with self.assertRaises(ValueError):",
                "            process_invalid_data()"
            ]),
            
            # Documentation files
            ("docs/README.md", [
                "# Application Documentation",
                "## Error Handling",
                "The application implements comprehensive error handling.",
                "## Logging",
                "Structured logging is used throughout the application."
            ]),
            
            # Docker files
            ("Dockerfile", [
                "FROM node:16",
                "WORKDIR /app",
                "COPY package*.json ./",
                "RUN npm install",
                "COPY . .",
                "EXPOSE 3000",
                "CMD [\"npm\", \"start\"]"
            ]),
            
            # Package files
            ("package.json", [
                "{",
                "  \"name\": \"test-app\",",
                "  \"version\": \"1.0.0\",",
                "  \"scripts\": {",
                "    \"test\": \"jest\",",
                "    \"start\": \"node src/app.js\"",
                "  },",
                "  \"dependencies\": {",
                "    \"express\": \"^4.17.1\",",
                "    \"winston\": \"^3.3.3\"",
                "  }",
                "}"
            ])
        ]
        
        # Create the files
        for file_path, content_lines in test_files:
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                for line in content_lines:
                    f.write(line + '\n')
        
        # Create metadata
        metadata = {
            "total_files": len(test_files),
            "total_lines": sum(len(content) for _, content in test_files),
            "total_size": sum(len('\n'.join(content)) for _, content in test_files),
            "languages": {
                "JavaScript": {"count": 2, "percentage": 25.0},
                "Python": {"count": 2, "percentage": 25.0},
                "Java": {"count": 1, "percentage": 12.5},
                "JSON": {"count": 1, "percentage": 12.5},
                "Markdown": {"count": 1, "percentage": 12.5},
                "Dockerfile": {"count": 1, "percentage": 12.5}
            },
            "file_list": []
        }
        
        for file_path, content_lines in test_files:
            language = "JavaScript" if file_path.endswith('.js') else \
                      "Python" if file_path.endswith('.py') else \
                      "Java" if file_path.endswith('.java') else \
                      "JSON" if file_path.endswith('.json') else \
                      "Markdown" if file_path.endswith('.md') else \
                      "Dockerfile" if file_path == "Dockerfile" else \
                      "Config"
            
            metadata["file_list"].append({
                "relative_path": file_path,
                "language": language,
                "type": "Test Code" if "test" in file_path.lower() else "Source Code",
                "size": len('\n'.join(content_lines)),
                "lines": len(content_lines),
                "is_binary": False
            })
        
        print(f"✅ Created test repository with {len(test_files)} files")
        return repo_path, metadata

def create_test_gates():
    """Create test gates with various patterns"""
    print("🎯 Creating test gates...")
    
    gates = [
        {
            "name": "STRUCTURED_LOGS",
            "display_name": "Structured Logging",
            "description": "Ensure structured logging is implemented",
            "category": "Logging",
            "priority": "High",
            "patterns": [
                r"logger\.(info|error|warn|debug)",
                r"console\.(log|error|warn|debug)",
                r"log\.(info|error|warn|debug)",
                r"LoggerFactory\.getLogger"
            ]
        },
        {
            "name": "ERROR_HANDLING",
            "display_name": "Error Handling",
            "description": "Ensure proper error handling is implemented",
            "category": "Error Handling",
            "priority": "High",
            "patterns": [
                r"try\s*{",
                r"catch\s*\(",
                r"except\s+",
                r"finally\s*{",
                r"throw\s+new",
                r"raise\s+"
            ]
        },
        {
            "name": "AUTOMATED_TESTS",
            "display_name": "Automated Tests",
            "description": "Ensure automated tests are present",
            "category": "Testing",
            "priority": "Medium",
            "patterns": [
                r"test_",
                r"\.test\.",
                r"unittest\.",
                r"jest\.",
                r"describe\(",
                r"it\(",
                r"assert"
            ]
        },
        {
            "name": "SECURITY_VALIDATION",
            "display_name": "Security Validation",
            "description": "Ensure security validations are present",
            "category": "Security",
            "priority": "High",
            "patterns": [
                r"validate",
                r"sanitize",
                r"escape",
                r"encrypt",
                r"hash",
                r"authentication",
                r"authorization"
            ]
        }
    ]
    
    # Create patterns dictionary
    patterns = {gate["name"]: gate["patterns"] for gate in gates}
    
    # Create pattern data
    pattern_data = {
        gate["name"]: {
            "description": gate["description"],
            "significance": f"Important for {gate['category'].lower()}",
            "expected_coverage": {
                "percentage": 25,
                "reasoning": f"Standard expectation for {gate['category'].lower()}",
                "confidence": "medium"
            }
        }
        for gate in gates
    }
    
    print(f"✅ Created {len(gates)} test gates")
    return gates, patterns, pattern_data

def test_file_centric_processing():
    """Test the file-centric processing approach"""
    print("\n🧪 Testing file-centric processing...")
    
    # Create test repository and gates
    repo_path, metadata = create_test_repository()
    gates, patterns, pattern_data = create_test_gates()
    
    # Import the ValidateGatesNode
    from nodes import ValidateGatesNode
    
    # Create test parameters
    params = {
        "repo_path": str(repo_path),
        "patterns": patterns,
        "pattern_data": pattern_data,
        "metadata": metadata,
        "hard_gates": gates,
        "shared": {
            "request": {
                "repository_url": "https://github.com/test/test-repo",
                "branch": "main"
            }
        }
    }
    
    # Create ValidateGatesNode instance
    validator = ValidateGatesNode()
    
    try:
        # Test the file-centric approach
        print("   🔄 Running file-centric processing...")
        start_time = time.time()
        
        # Add debug logging to see what's happening
        print("   🔍 Debug: Checking file processing step by step...")
        
        # Test file processing directly
        config = validator._get_pattern_matching_config(params.get("shared", {}))
        relevant_files = validator._get_improved_relevant_files(metadata, file_type="Source Code", config=config)
        
        print(f"   📁 Debug: Found {len(relevant_files)} relevant files")
        for file_info in relevant_files:
            print(f"      - {file_info['relative_path']} ({file_info['language']})")
        
        # Test pattern compilation
        all_compiled_patterns = {}
        for gate in gates:
            gate_name = gate["name"]
            patterns_list = patterns.get(gate_name, [])
            compiled_patterns = []
            for pattern in patterns_list:
                try:
                    import re
                    compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    compiled_patterns.append((pattern, compiled_pattern))
                except re.error as e:
                    print(f"   ⚠️ Invalid regex pattern for {gate_name}: {pattern} - {e}")
            all_compiled_patterns[gate_name] = compiled_patterns
            print(f"   🔧 Debug: Compiled {len(compiled_patterns)} patterns for {gate_name}")
        
        # Test a single file
        if relevant_files:
            test_file_info = relevant_files[0]
            test_file_path = repo_path / test_file_info["relative_path"]
            print(f"   🧪 Debug: Testing file {test_file_info['relative_path']}")
            
            if test_file_path.exists():
                print(f"   📄 Debug: File exists, size: {test_file_path.stat().st_size} bytes")
                
                # Read first few lines
                with open(test_file_path, 'r') as f:
                    first_lines = [f.readline().strip() for _ in range(5)]
                print(f"   📝 Debug: First lines: {first_lines}")
                
                # Test pattern matching on first line
                if first_lines and first_lines[0]:
                    for gate_name, compiled_patterns in all_compiled_patterns.items():
                        for pattern, compiled_pattern in compiled_patterns:
                            if compiled_pattern.search(first_lines[0]):
                                print(f"   ✅ Debug: Pattern '{pattern}' matches in {gate_name}")
                            else:
                                print(f"   ❌ Debug: Pattern '{pattern}' does not match in {gate_name}")
            else:
                print(f"   ❌ Debug: File does not exist: {test_file_path}")
        
        results = validator._evaluate_with_legacy_system(params)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"   ⏱️  Processing completed in {processing_time:.2f}s")
        
        # Analyze results
        print(f"\n📊 Results Analysis:")
        print(f"   Total gates processed: {len(results)}")
        
        for result in results:
            gate_name = result["gate"]
            status = result["status"]
            matches_found = result["matches_found"]
            patterns_used = result["patterns_used"]
            
            print(f"   🎯 {gate_name}: {status} ({matches_found} matches, {patterns_used} patterns)")
            
            # Verify result structure
            required_fields = [
                "gate", "display_name", "description", "category", "priority",
                "patterns_used", "matches_found", "score", "status", "details",
                "recommendations", "total_files", "relevant_files", "validation_sources"
            ]
            
            for field in required_fields:
                if field not in result:
                    print(f"   ❌ Missing field '{field}' in {gate_name}")
                    return False
            
            # Verify matches structure
            if "matches" in result:
                for match in result["matches"]:
                    match_fields = ["file", "pattern", "match", "line", "language", "source"]
                    for field in match_fields:
                        if field not in match:
                            print(f"   ❌ Missing field '{field}' in match for {gate_name}")
                            return False
        
        print(f"   ✅ All gates processed successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gate_applicability():
    """Test gate applicability functionality"""
    print("\n🎯 Testing gate applicability...")
    
    try:
        from utils.gate_applicability import gate_applicability_analyzer
        
        # Create test metadata
        metadata = {
            "languages": {
                "JavaScript": {"count": 10, "percentage": 50.0},
                "Python": {"count": 5, "percentage": 25.0},
                "Java": {"count": 5, "percentage": 25.0}
            },
            "file_list": [
                {"language": "JavaScript", "type": "Source Code"},
                {"language": "Python", "type": "Source Code"},
                {"language": "Java", "type": "Source Code"}
            ]
        }
        
        # Test applicability analysis
        characteristics = gate_applicability_analyzer.analyze_codebase_type(metadata)
        print(f"   📊 Codebase characteristics: {characteristics}")
        
        # Test specific gates
        test_gates = ["STRUCTURED_LOGS", "ERROR_HANDLING", "AUTOMATED_TESTS", "SECURITY_VALIDATION"]
        
        for gate_name in test_gates:
            applicability = gate_applicability_analyzer._check_gate_applicability(gate_name, characteristics)
            print(f"   🎯 {gate_name}: {'Applicable' if applicability['is_applicable'] else 'Not Applicable'} - {applicability['reason']}")
        
        print(f"   ✅ Gate applicability testing completed")
        return True
        
    except Exception as e:
        print(f"   ❌ Error in gate applicability: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pattern_matching():
    """Test pattern matching functionality"""
    print("\n🔍 Testing pattern matching...")
    
    try:
        from nodes import ValidateGatesNode
        import re
        
        # Create test patterns
        test_patterns = [
            r"console\.log",
            r"try\s*{",
            r"test_",
            r"logger\."
        ]
        
        # Compile patterns
        compiled_patterns = []
        for pattern in test_patterns:
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                compiled_patterns.append((pattern, compiled_pattern))
            except re.error as e:
                print(f"   ❌ Invalid pattern '{pattern}': {e}")
                return False
        
        print(f"   ✅ Compiled {len(compiled_patterns)} patterns")
        
        # Test pattern matching
        test_lines = [
            "console.log('test');",
            "try {",
            "test_function();",
            "logger.info('message');",
            "// This should not match"
        ]
        
        matches = []
        for line_num, line in enumerate(test_lines, 1):
            for pattern, compiled_pattern in compiled_patterns:
                if compiled_pattern.search(line):
                    matches.append({
                        "pattern": pattern,
                        "match": line.strip(),
                        "line": line_num
                    })
        
        print(f"   📊 Found {len(matches)} matches in test lines")
        
        expected_matches = 4  # console.log, try {, test_function, logger.info
        if len(matches) == expected_matches:
            print(f"   ✅ Pattern matching working correctly")
            return True
        else:
            print(f"   ❌ Expected {expected_matches} matches, got {len(matches)}")
            return False
        
    except Exception as e:
        print(f"   ❌ Error in pattern matching: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_processing():
    """Test file processing functionality"""
    print("\n📁 Testing file processing...")
    
    try:
        from nodes import ValidateGatesNode
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("console.log('test')\n")
            f.write("try:\n")
            f.write("    test_function()\n")
            f.write("except Exception as e:\n")
            f.write("    logger.error(e)\n")
            test_file_path = f.name
        
        try:
            # Test file processing
            validator = ValidateGatesNode()
            
            file_info = {
                "relative_path": "test.py",
                "language": "Python",
                "type": "Source Code"
            }
            
            # Test compiled patterns
            import re
            compiled_patterns = [
                ("console.log", re.compile(r"console\.log", re.IGNORECASE)),
                ("try", re.compile(r"try\s*:", re.IGNORECASE)),
                ("except", re.compile(r"except\s+", re.IGNORECASE))
            ]
            
            gates = [{"name": "TEST_GATE"}]
            
            # Test the file processing method
            matches = validator._process_file_for_all_gates(
                Path(test_file_path),
                file_info,
                {"TEST_GATE": compiled_patterns},
                50,
                gates
            )
            
            print(f"   📊 Found {len(matches['TEST_GATE'])} matches in test file")
            
            if len(matches['TEST_GATE']) >= 3:  # console.log, try, except
                print(f"   ✅ File processing working correctly")
                return True
            else:
                print(f"   ❌ Expected at least 3 matches, got {len(matches['TEST_GATE'])}")
                return False
                
        finally:
            # Clean up
            os.unlink(test_file_path)
        
    except Exception as e:
        print(f"   ❌ Error in file processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Comprehensive File-Centric Approach Test")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Pattern Matching", test_pattern_matching),
        ("Gate Applicability", test_gate_applicability),
        ("File Processing", test_file_processing),
        ("File-Centric Processing", test_file_centric_processing)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! File-centric approach is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
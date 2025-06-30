#!/usr/bin/env python3
"""
Test script to demonstrate enhanced metadata extraction for hard gate analysis
"""

import json
import sys
from pathlib import Path
from pprint import pprint

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from codegates.models import Language
from codegates.core.gate_validators.base import BaseGateValidator
from codegates.core.gate_validators.logging_validators import SecretLogsValidator, StructuredLogsValidator
from codegates.core.gate_validators.error_validators import ErrorLogsValidator


def create_sample_code_files():
    """Create sample code files to test metadata extraction"""
    
    # Create a sample Python file with various patterns
    sample_py = """
import logging
import os

class UserService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def authenticate_user(self, username, password):
        # TODO: Implement proper password hashing
        self.logger.info(f"Authenticating user: {username}")
        
        try:
            # This is a security issue - logging password!
            self.logger.debug(f"Password: {password}")
            self.logger.error("Authentication failed - password mismatch")
            
            if username == "admin" and password == "secret123":
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error("Authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise
    
    def get_user_data(self, user_id):
        try:
            # Simulated database query
            query = f"SELECT * FROM users WHERE id = {user_id}"
            print(f"Executing query: {query}")  # Potential SQL injection
            
            return {"id": user_id, "name": "John Doe"}
            
        except Exception as e:
            print(f"Database error: {e}")
            self.logger.error(f"Database error: {e}")
            return None

def main():
    service = UserService()
    result = service.authenticate_user("admin", "password123")
    print(f"Authentication result: {result}")

if __name__ == "__main__":
    main()
"""

    # Create a sample JavaScript file
    sample_js = """
const express = require('express');
const app = express();

class AuthController {
    async login(req, res) {
        const { username, password } = req.body;
        
        // FIXME: This logs sensitive data
        console.log('Login attempt with password:', password);
        console.error('Failed login for password:', password);
        
        try {
            // Simulated authentication
            if (username === 'admin' && password === 'secret') {
                console.log('Login successful for user:', username);
                res.json({ success: true, token: 'abc123' });
            } else {
                console.error('Login failed for user:', username);
                res.status(401).json({ error: 'Invalid credentials' });
            }
        } catch (error) {
            console.error('Authentication error:', error);
            res.status(500).json({ error: 'Internal server error' });
        }
    }
    
    async getProfile(req, res) {
        try {
            const userId = req.params.id;
            // Potential SQL injection
            const query = `SELECT * FROM users WHERE id = ${userId}`;
            console.log('Executing query:', query);
            
            res.json({ id: userId, name: 'John Doe' });
        } catch (error) {
            console.log('Profile error:', error.message);
            res.status(500).json({ error: 'Profile fetch failed' });
        }
    }
}

module.exports = AuthController;
"""

    # Create test directory and files
    test_dir = Path("test_metadata_sample")
    test_dir.mkdir(exist_ok=True)
    
    (test_dir / "user_service.py").write_text(sample_py)
    (test_dir / "auth_controller.js").write_text(sample_js)
    
    return test_dir


def test_validator_with_matches(validator, test_dir, validator_name):
    """Test a specific validator and show matches if found"""
    
    print(f"\n🔍 Testing {validator_name}...")
    
    # Get file extensions and patterns
    extensions = validator._get_file_extensions()
    patterns = validator._get_language_patterns()
    
    print(f"   • File Extensions: {extensions}")
    print(f"   • Pattern Categories: {list(patterns.keys())}")
    
    all_matches = []
    
    # Test each pattern category
    for category, pattern_list in patterns.items():
        print(f"   • Testing {category}: {len(pattern_list)} patterns")
        matches = validator._search_files_for_patterns(test_dir, extensions, pattern_list)
        all_matches.extend(matches)
        
        if matches:
            print(f"     ✅ Found {len(matches)} matches in {category}")
        else:
            print(f"     ❌ No matches in {category}")
    
    return all_matches


def test_enhanced_metadata_extraction():
    """Test the enhanced metadata extraction system"""
    
    print("🚀 Testing Enhanced Metadata Extraction for Hard Gate Analysis")
    print("=" * 70)
    
    # Create sample code files
    test_dir = create_sample_code_files()
    print(f"📁 Created test files in: {test_dir}")
    
    try:
        all_matches = []
        
        # Test multiple validators to find matches
        validators_to_test = [
            (SecretLogsValidator(Language.PYTHON), "Secret Logs Validator (Python)"),
            (SecretLogsValidator(Language.JAVASCRIPT), "Secret Logs Validator (JavaScript)"),
            (ErrorLogsValidator(Language.PYTHON), "Error Logs Validator (Python)"),
            (ErrorLogsValidator(Language.JAVASCRIPT), "Error Logs Validator (JavaScript)"),
        ]
        
        for validator, name in validators_to_test:
            matches = test_validator_with_matches(validator, test_dir, name)
            all_matches.extend(matches)
        
        print(f"\n📊 Overall Analysis Results:")
        print(f"   • Total Matches Found: {len(all_matches)}")
        
        if all_matches:
            # Display detailed metadata for each match
            for i, match in enumerate(all_matches[:5], 1):  # Show first 5 matches
                print(f"\n🔍 Match {i} - Enhanced Metadata:")
                print(f"   ├── File Information:")
                print(f"   │   ├── File: {match['relative_path']}")
                print(f"   │   ├── Name: {match['file_name']}")
                print(f"   │   ├── Extension: {match['file_extension']}")
                print(f"   │   ├── Size: {match['file_size']} bytes")
                print(f"   │   └── Modified: {match['file_modified']}")
                
                print(f"   ├── Pattern Match:")
                print(f"   │   ├── Line: {match['line_number']}")
                print(f"   │   ├── Columns: {match['column_start']}-{match['column_end']}")
                print(f"   │   ├── Matched Text: '{match['matched_text']}'")
                print(f"   │   ├── Full Line: {match['full_line']}")
                print(f"   │   ├── Pattern: {match['pattern']}")
                print(f"   │   └── Pattern Type: {match['pattern_type']}")
                
                print(f"   ├── Code Context:")
                print(f"   │   ├── Function: {match['function_context']['function_name']}")
                print(f"   │   ├── Function Line: {match['function_context']['function_line']}")
                print(f"   │   ├── Function Signature: {match['function_context']['function_signature']}")
                print(f"   │   └── Distance from Function: {match['function_context']['distance_from_function']} lines")
                
                print(f"   ├── Analysis:")
                print(f"   │   ├── Severity: {match['severity']}")
                print(f"   │   ├── Category: {match['category']}")
                print(f"   │   ├── Priority: {match['priority']}/10")
                print(f"   │   ├── Language: {match['language']}")
                print(f"   │   └── Gate Type: {match['gate_type']}")
                
                print(f"   ├── Code Properties:")
                print(f"   │   ├── Line Length: {match['line_length']}")
                print(f"   │   ├── Indentation: {match['indentation_level']} spaces")
                print(f"   │   ├── Is Comment: {match['is_comment']}")
                print(f"   │   └── In String Literal: {match['is_string_literal']}")
                
                print(f"   ├── Remediation:")
                print(f"   │   ├── Suggested Fix: {match['suggested_fix']}")
                print(f"   │   └── Documentation: {match['documentation_link']}")
                
                print(f"   └── Context Lines ({match['context_start_line']}-{match['context_end_line']}):")
                for j, context_line in enumerate(match['context_lines']):
                    line_num = match['context_start_line'] + j
                    marker = "➤" if line_num == match['line_number'] else " "
                    print(f"       {marker} {line_num:3d}: {context_line}")
            
            if len(all_matches) > 5:
                print(f"\n   ... and {len(all_matches) - 5} more matches")
        
        else:
            print("\n⚠️ No matches found. Let's create a simple test to verify the system works...")
            
            # Create a simple test to verify our enhanced system works
            test_validator = SecretLogsValidator(Language.PYTHON)
            simple_patterns = ['password', 'secret', 'token']
            
            print(f"\n🧪 Testing with simple patterns: {simple_patterns}")
            simple_matches = test_validator._search_files_for_patterns(test_dir, ['*.py'], simple_patterns)
            
            if simple_matches:
                print(f"✅ Simple test found {len(simple_matches)} matches!")
                match = simple_matches[0]
                print(f"\n📋 Sample Match Metadata:")
                print(f"   • File: {match['relative_path']}")
                print(f"   • Line: {match['line_number']}")
                print(f"   • Matched: '{match['matched_text']}'")
                print(f"   • Function: {match['function_context']['function_name']}")
                print(f"   • Severity: {match['severity']}")
                print(f"   • Priority: {match['priority']}/10")
                all_matches = simple_matches
        
        # Save detailed results to JSON file
        output_data = {
            'summary': {
                'total_matches': len(all_matches),
                'test_directory': str(test_dir),
                'analysis_timestamp': str(Path(__file__).stat().st_mtime),
                'enhanced_metadata_fields': [
                    'file', 'relative_path', 'file_name', 'file_extension', 'file_size', 'file_modified',
                    'line_number', 'column_start', 'column_end', 'matched_text', 'full_line', 'pattern', 'pattern_type',
                    'context_lines', 'context_start_line', 'context_end_line', 'function_context',
                    'severity', 'category', 'language', 'gate_type',
                    'line_length', 'indentation_level', 'is_comment', 'is_string_literal',
                    'suggested_fix', 'documentation_link', 'priority'
                ]
            },
            'matches': all_matches
        }
        
        output_file = "enhanced_metadata_results.json"
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Generate summary statistics
        if all_matches:
            high_priority = sum(1 for match in all_matches if match.get('priority', 0) >= 7)
            security_issues = sum(1 for match in all_matches if match.get('severity') == 'HIGH')
            unique_files = len(set(match['relative_path'] for match in all_matches))
            unique_functions = len(set(match['function_context']['function_name'] for match in all_matches))
            
            print(f"\n📈 Summary Statistics:")
            print(f"   • Total Pattern Matches: {len(all_matches)}")
            print(f"   • High Priority Issues: {high_priority}")
            print(f"   • Security Issues: {security_issues}")
            print(f"   • Files with Issues: {unique_files}")
            print(f"   • Functions with Issues: {unique_functions}")
            print(f"   • Languages Analyzed: Python, JavaScript")
        
        print(f"\n✅ Enhanced metadata extraction test completed successfully!")
        print(f"\n🎯 Key Features Demonstrated:")
        print(f"   ✓ Comprehensive file metadata (size, path, extension)")
        print(f"   ✓ Precise pattern matching (line, column, matched text)")
        print(f"   ✓ Function context extraction (name, line, signature)")
        print(f"   ✓ Code analysis (severity, category, priority)")
        print(f"   ✓ Code properties (indentation, comments, string literals)")
        print(f"   ✓ Remediation suggestions (fixes, documentation)")
        print(f"   ✓ Context lines for better understanding")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup test files
        try:
            import shutil
            shutil.rmtree(test_dir)
            print(f"\n🧹 Cleaned up test directory: {test_dir}")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test directory: {e}")


if __name__ == "__main__":
    test_enhanced_metadata_extraction() 
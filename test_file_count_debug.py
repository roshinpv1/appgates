#!/usr/bin/env python3
"""
Debug script to check file counting issues
"""

import sys
import json
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def debug_file_counts():
    """Debug file counting issues"""
    print("🔍 Debugging File Count Issues")
    print("=" * 50)
    
    try:
        from utils.file_scanner import scan_directory
        from nodes import ValidateGatesNode
        
        # Test with a sample repository path
        test_repo_path = "/Users/roshinpv/Downloads/spring-petclinic-main"  # Adjust this path
        
        if not Path(test_repo_path).exists():
            print(f"❌ Test repository not found: {test_repo_path}")
            print("Please update the test_repo_path variable to point to a valid repository")
            return False
        
        print(f"📁 Scanning repository: {test_repo_path}")
        
        # Scan the repository
        metadata = scan_directory(test_repo_path, max_files=5000)
        
        print(f"\n📊 Metadata Summary:")
        print(f"   Total Files: {metadata.get('total_files', 0)}")
        print(f"   Total Lines: {metadata.get('total_lines', 0)}")
        print(f"   File List Length: {len(metadata.get('file_list', []))}")
        print(f"   Languages: {list(metadata.get('languages', {}).keys())}")
        
        # Check file type distribution
        file_types = metadata.get('file_types', {})
        print(f"\n📋 File Type Distribution:")
        for file_type, count in file_types.items():
            print(f"   {file_type}: {count} files")
        
        # Check language distribution
        language_stats = metadata.get('language_stats', {})
        print(f"\n🌐 Language Distribution:")
        for language, stats in language_stats.items():
            print(f"   {language}: {stats.get('files', 0)} files ({stats.get('percentage', 0)}%)")
        
        # Test the relevant files calculation
        print(f"\n🔍 Testing Relevant Files Calculation:")
        
        # Create a mock ValidateGatesNode to test the method
        validate_node = ValidateGatesNode()
        
        # Test for different gate types
        test_gates = ["STRUCTURED_LOGS", "AUTOMATED_TESTS", "ERROR_LOGS"]
        
        for gate_name in test_gates:
            print(f"\n   Testing {gate_name}:")
            
            # Get relevant files for source code
            source_files = validate_node._get_improved_relevant_files(
                metadata, 
                file_type="Source Code", 
                gate_name=gate_name
            )
            
            # Get relevant files for test code
            test_files = validate_node._get_improved_relevant_files(
                metadata, 
                file_type="Test Code", 
                gate_name=gate_name
            )
            
            print(f"     Source Code Files: {len(source_files)}")
            print(f"     Test Code Files: {len(test_files)}")
            
            # Show some sample files
            if source_files:
                print(f"     Sample Source Files:")
                for file_info in source_files[:3]:
                    print(f"       - {file_info['relative_path']} ({file_info['language']})")
                if len(source_files) > 3:
                    print(f"       ... and {len(source_files) - 3} more")
        
        # Check if there are any discrepancies
        total_files_in_list = len(metadata.get('file_list', []))
        total_files_counted = metadata.get('total_files', 0)
        
        print(f"\n🔍 File Count Verification:")
        print(f"   Files in file_list: {total_files_in_list}")
        print(f"   Total files counted: {total_files_counted}")
        
        if total_files_in_list != total_files_counted:
            print(f"   ⚠️ DISCREPANCY FOUND: {total_files_in_list} vs {total_files_counted}")
        else:
            print(f"   ✅ File counts match")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_file_counts()
    
    if success:
        print("\n✅ Debug completed successfully")
    else:
        print("\n❌ Debug failed") 
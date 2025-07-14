#!/usr/bin/env python3
"""
Fix indentation error in nodes.py
"""

from pathlib import Path

def fix_indentation():
    """Fix the indentation error in the _find_pattern_matches_with_config method"""
    
    nodes_file = Path("gates/nodes.py")
    if not nodes_file.exists():
        print("❌ gates/nodes.py not found")
        return False
    
    content = nodes_file.read_text()
    
    # Find the problematic line
    lines = content.split('\n')
    
    # Find the method definition
    method_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("def _find_pattern_matches_with_config"):
            method_start = i
            break
    
    if method_start is None:
        print("❌ Could not find method definition")
        return False
    
    # Fix the indentation of the docstring
    if method_start + 1 < len(lines):
        docstring_line = lines[method_start + 1]
        if docstring_line.strip().startswith('"""') and not docstring_line.startswith('        """'):
            # Fix the indentation
            lines[method_start + 1] = '        """Find pattern matches in appropriate files with improved coverage and error handling"""'
    
    # Write the fixed content
    fixed_content = '\n'.join(lines)
    nodes_file.write_text(fixed_content)
    
    print("✅ Fixed indentation error")
    return True

if __name__ == "__main__":
    print("🔧 Fixing indentation error...")
    if fix_indentation():
        print("✅ Indentation fixed successfully!")
    else:
        print("❌ Failed to fix indentation") 
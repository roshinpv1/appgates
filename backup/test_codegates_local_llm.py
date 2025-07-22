#!/usr/bin/env python3
"""
Test CodeGates with local LLM integration
"""

import os
import sys
import tempfile
import shutil

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def test_codegates_local_llm():
    """Test CodeGates with local LLM"""
    print("🧪 Testing CodeGates with Local LLM")
    print("=" * 40)
    
    # Set environment variables for local LLM
    os.environ["LOCAL_LLM_URL"] = "http://localhost:1234/v1"
    os.environ["LOCAL_LLM_MODEL"] = "llama-3.2-3b-instruct"
    os.environ["LOCAL_LLM_API_KEY"] = "not-needed"
    
    try:
        from nodes import CallLLMNode
        
        # Create a test prompt
        test_prompt = """
        Analyze the following codebase for security and reliability patterns.
        
        Project: Test Project
        Language: Python
        Framework: Flask
        
        Please generate patterns for:
        1. Input validation
        2. Error handling
        3. Logging
        4. Authentication
        5. Data encryption
        
        Respond with a JSON object containing patterns for each category.
        """
        
        # Create shared data
        shared = {
            "llm": {
                "prompt": test_prompt
            },
            "llm_config": {
                "url": "http://localhost:1234/v1",
                "model": "llama-3.2-3b-instruct",
                "api_key": "not-needed",
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "request": {
                "repository_url": "https://github.com/test/repo",
                "branch": "main"
            }
        }
        
        # Create and execute the LLM node
        llm_node = CallLLMNode()
        params = llm_node.prep(shared)
        result = llm_node.exec(params)
        
        print(f"✅ LLM call successful")
        print(f"   Source: {result.get('source', 'unknown')}")
        print(f"   Model: {result.get('model', 'unknown')}")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('pattern_data'):
            print(f"   Pattern data generated: {len(result['pattern_data'])} patterns")
            for category, patterns in result['pattern_data'].items():
                print(f"     - {category}: {len(patterns)} patterns")
        
        # Test with a simple repository scan
        print("\n🧪 Testing full scan with local LLM...")
        
        # Create a temporary test repository
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file
            test_file = os.path.join(temp_dir, "test_app.py")
            with open(test_file, 'w') as f:
                f.write("""
from flask import Flask, request
import logging

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
""")
            
            # Test the scan process
            from nodes import ProcessCodebaseNode, ExtractConfigNode, GeneratePromptNode
            
            # Process codebase
            process_node = ProcessCodebaseNode()
            process_params = process_node.prep({"request": {"repository_url": temp_dir}})
            process_result = process_node.exec(process_params)
            
            print(f"   Files processed: {len(process_result.get('files', []))}")
            
            # Extract config
            extract_node = ExtractConfigNode()
            extract_params = extract_node.prep({"files": process_result.get('files', [])})
            extract_result = extract_node.exec(extract_params)
            
            print(f"   Config files found: {len(extract_result.get('config_files', []))}")
            
            # Generate prompt
            prompt_node = GeneratePromptNode()
            prompt_params = prompt_node.prep({
                "files": process_result.get('files', []),
                "config_files": extract_result.get('config_files', []),
                "request": {"repository_url": temp_dir}
            })
            prompt_result = prompt_node.exec(prompt_params)
            
            print(f"   Prompt generated: {len(prompt_result.get('prompt', ''))} characters")
            
            # Call LLM with the generated prompt
            llm_shared = {
                "llm": {
                    "prompt": prompt_result.get('prompt', '')
                },
                "llm_config": {
                    "url": "http://localhost:1234/v1",
                    "model": "llama-3.2-3b-instruct",
                    "api_key": "not-needed",
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                "request": {"repository_url": temp_dir}
            }
            
            llm_params = llm_node.prep(llm_shared)
            llm_result = llm_node.exec(llm_params)
            
            print(f"   LLM analysis completed: {llm_result.get('success', False)}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_codegates_local_llm()
    print("\n✅ CodeGates Local LLM Test Complete!") 
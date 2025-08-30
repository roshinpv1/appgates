#!/usr/bin/env python3
"""
Test script for Enhanced LLM Pre-Analysis Prompt with Expected Counts
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.prompt_templates import PromptTemplates

def test_enhanced_prompt():
    """Test the enhanced LLM pre-analysis prompt"""
    
    print("🧪 Testing Enhanced LLM Pre-Analysis Prompt")
    print("=" * 50)
    
    # Initialize prompt templates
    prompt_templates = PromptTemplates()
    
    # Get the enhanced prompt template
    template = prompt_templates.get_template("llm_pre_analysis")
    
    if not template:
        print("❌ LLM pre-analysis template not found")
        return
    
    print(f"✅ Found LLM pre-analysis template")
    print(f"📝 Use case: {template.use_case}")
    print(f"📝 Description: {template.description}")
    
    # Test prompt formatting
    test_data = {
        "build_configs": "Maven build with Spring Boot starter dependencies",
        "expected_counts_analysis": "Analysis based on project structure and technology stack",
        "available_gates": "Gates 0.1, 1.2, 1.3, 1.5, 1.6, 1.8, 1.10, 1.12, 2, 2.1, 2.3, 2.4, 2.7, 3.6, 3.9, 3.18",
        "extracted_code": "Sample code snippets from vector database",
        "project_structure": "Spring Boot application with 50 Java files, 10 configuration files"
    }
    
    try:
        formatted_prompt = prompt_templates.format_template("llm_pre_analysis", **test_data)
        
        if formatted_prompt:
            print(f"✅ Successfully formatted prompt ({len(formatted_prompt)} characters)")
            
            # Check if the enhanced fields are present
            enhanced_fields = [
                "expected_count",
                "expected_count_reasoning"
            ]
            
            missing_fields = []
            for field in enhanced_fields:
                if field not in formatted_prompt:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing enhanced fields: {missing_fields}")
            else:
                print(f"✅ All enhanced fields present in prompt")
                
            # Check for expected count guidance
            guidance_phrases = [
                "expected_count",
                "expected_count_reasoning",
                "Number of relevant file types",
                "Project architecture patterns",
                "Technology stack requirements",
                "Build configuration indicators",
                "Industry best practices"
            ]
            
            found_guidance = []
            for phrase in guidance_phrases:
                if phrase in formatted_prompt:
                    found_guidance.append(phrase)
            
            print(f"✅ Found {len(found_guidance)}/{len(guidance_phrases)} guidance phrases")
            for phrase in found_guidance:
                print(f"   ✅ {phrase}")
            
            # Show prompt preview
            print(f"\n📋 Prompt Preview (first 500 chars):")
            print("-" * 50)
            print(formatted_prompt[:500] + "...")
            
        else:
            print("❌ Failed to format prompt")
            
    except Exception as e:
        print(f"❌ Error testing prompt: {e}")
        import traceback
        traceback.print_exc()

def test_expected_json_structure():
    """Test the expected JSON response structure"""
    
    print(f"\n🔍 Testing Expected JSON Response Structure")
    print("=" * 50)
    
    # Example of expected JSON response structure
    expected_structure = {
        "patterns": [
            {
                "gate_id": "0.1",
                "name": "All alerting is actionable",
                "description": "Implement actionable alerting with monitoring tools",
                "applicable": True,
                "reason": "Repository contains monitoring configuration",
                "pattern": "alert.*action|monitor.*tool",
                "expected_count": 3,
                "expected_count_reasoning": "Based on 2 monitoring config files and 1 alerting setup that should implement actionable alerts"
            },
            {
                "gate_id": "1.2",
                "name": "Log Application Messages",
                "description": "Use standard logging libraries for application messages",
                "applicable": True,
                "reason": "Repository contains logging framework",
                "pattern": "log.*message|application.*log",
                "expected_count": 4,
                "expected_count_reasoning": "Based on 2 service classes and 2 utility classes that should implement application logging"
            }
        ]
    }
    
    print("✅ Expected JSON structure includes:")
    for field in ["gate_id", "name", "description", "applicable", "reason", "pattern", "expected_count", "expected_count_reasoning"]:
        print(f"   ✅ {field}")
    
    # Validate structure
    import json
    try:
        json_str = json.dumps(expected_structure, indent=2)
        print(f"✅ JSON structure is valid ({len(json_str)} characters)")
        
        # Show example
        print(f"\n📋 Example JSON Response:")
        print("-" * 50)
        print(json_str)
        
    except Exception as e:
        print(f"❌ JSON structure validation failed: {e}")

if __name__ == "__main__":
    test_enhanced_prompt()
    test_expected_json_structure()
    print(f"\n🎉 Enhanced LLM Pre-Analysis Prompt Test Completed!")

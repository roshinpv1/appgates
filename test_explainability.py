#!/usr/bin/env python3
"""
Test script for Gate Explainability functionality
Tests the comprehensive explainability engine for gate validation results
"""

import sys
import json
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_explainability_engine():
    """Test the explainability engine with sample gate data"""
    print("🔍 Testing Gate Explainability Engine...")
    
    try:
        from utils.gate_explainability import gate_explainability_engine, GateValidationContext
        
        # Sample gate result data
        sample_gate_result = {
            "gate": "STRUCTURED_LOGS",
            "display_name": "Structured Logging",
            "description": "Ensure logs are structured and machine-readable",
            "category": "Auditability",
            "priority": "high",
            "weight": 1.0,
            "status": "FAIL",
            "score": 35.0,
            "patterns": [
                r"console\.log\(",
                r"print\(",
                r"System\.out\.println\("
            ],
            "matches": [
                {
                    "file": "src/main.js",
                    "line": 42,
                    "pattern": r"console\.log\(",
                    "context": "console.log('User logged in:', user.id);"
                },
                {
                    "file": "src/utils.js",
                    "line": 15,
                    "pattern": r"console\.log\(",
                    "context": "console.log('Processing request:', req.url);"
                }
            ],
            "validation_sources": {
                "llm_patterns": {"enabled": True, "count": 3, "matches": 2},
                "static_patterns": {"enabled": True, "count": 3, "matches": 2},
                "combined_confidence": "high"
            },
            "expected_coverage": {
                "percentage": 80.0,
                "reasoning": "Most application files should use structured logging",
                "confidence": "high"
            },
            "total_files": 50,
            "relevant_files": 30,
            "files_analyzed": 30
        }
        
        # Sample shared data
        sample_shared = {
            "repository": {
                "metadata": {
                    "primary_languages": ["JavaScript", "TypeScript"],
                    "frameworks": ["React", "Node.js"],
                    "build_tools": ["npm", "webpack"],
                    "deployment_platforms": ["AWS", "Docker"],
                    "commit_hash": "abc123def456",
                    "last_commit_date": "2024-01-15T10:30:00Z"
                }
            },
            "request": {
                "repository_url": "https://github.com/example/app-frontend",
                "branch": "main"
            }
        }
        
        print("✅ Sample data created successfully")
        
        # Test creating validation context
        print("\n📊 Creating validation context...")
        context = gate_explainability_engine.create_validation_context(sample_gate_result, sample_shared)
        
        print(f"✅ Context created for gate: {context.gate_name}")
        print(f"   • Status: {context.validation_status}")
        print(f"   • Score: {context.validation_score:.1f}%")
        print(f"   • Evidence Collectors: {len(context.evidence_collectors_used)}")
        print(f"   • Patterns Analyzed: {context.total_patterns}")
        print(f"   • Matches Found: {context.matched_patterns}")
        print(f"   • Coverage Gap: {context.coverage_gap:.1f}%")
        
        # Test generating explanation
        print("\n📝 Generating explanation...")
        explanation = gate_explainability_engine.generate_explanation(context)
        
        print("✅ Explanation generated successfully")
        print(f"   • Length: {len(explanation)} characters")
        print(f"   • Contains status: {'FAIL' in explanation}")
        print(f"   • Contains recommendations: {'Recommendations' in explanation}")
        
        # Test generating LLM prompt
        print("\n🤖 Generating LLM prompt...")
        llm_prompt = gate_explainability_engine.generate_llm_prompt(context)
        
        print("✅ LLM prompt generated successfully")
        print(f"   • Length: {len(llm_prompt)} characters")
        print(f"   • Contains gate info: {context.gate_name in llm_prompt}")
        print(f"   • Contains validation data: {'Validation Results' in llm_prompt}")
        print(f"   • Contains technology context: {'Technology Context' in llm_prompt}")
        
        # Test with different gate statuses
        print("\n🔄 Testing different gate statuses...")
        
        statuses_to_test = ["PASS", "WARNING", "NOT_APPLICABLE"]
        
        for status in statuses_to_test:
            # Create a copy of the sample data with different status
            test_gate = sample_gate_result.copy()
            test_gate["status"] = status
            
            # Adjust score based on status
            if status == "PASS":
                test_gate["score"] = 85.0
            elif status == "WARNING":
                test_gate["score"] = 65.0
            else:  # NOT_APPLICABLE
                test_gate["score"] = 0.0
            
            # Create context and generate explanation
            test_context = gate_explainability_engine.create_validation_context(test_gate, sample_shared)
            test_explanation = gate_explainability_engine.generate_explanation(test_context)
            
            print(f"   ✅ {status}: {len(test_explanation)} characters")
        
        print("\n🎉 All explainability tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Explainability test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_recommendations():
    """Test the enhanced recommendation generation"""
    print("\n🔍 Testing Enhanced Recommendation Generation...")
    
    try:
        from utils.gate_explainability import gate_explainability_engine
        
        # Sample gate data for recommendation testing
        sample_gate = {
            "gate": "ERROR_HANDLING",
            "display_name": "Error Handling",
            "description": "Ensure proper error handling throughout the application",
            "category": "Error Handling",
            "priority": "critical",
            "weight": 1.5,
            "status": "FAIL",
            "score": 25.0,
            "patterns": [
                r"try\s*\{",
                r"catch\s*\(",
                r"throw\s+new\s+Error"
            ],
            "matches": [
                {
                    "file": "src/api.js",
                    "line": 25,
                    "pattern": r"throw\s+new\s+Error",
                    "context": "throw new Error('Invalid input');"
                }
            ],
            "validation_sources": {
                "llm_patterns": {"enabled": True, "count": 3, "matches": 1},
                "static_patterns": {"enabled": True, "count": 3, "matches": 1},
                "combined_confidence": "medium"
            },
            "expected_coverage": {
                "percentage": 90.0,
                "reasoning": "All API endpoints should have proper error handling",
                "confidence": "high"
            },
            "total_files": 100,
            "relevant_files": 80,
            "files_analyzed": 80
        }
        
        sample_shared = {
            "repository": {
                "metadata": {
                    "primary_languages": ["JavaScript", "TypeScript"],
                    "frameworks": ["Express", "React"],
                    "build_tools": ["npm", "yarn"],
                    "deployment_platforms": ["Heroku", "Vercel"],
                    "commit_hash": "def456ghi789",
                    "last_commit_date": "2024-01-16T14:20:00Z"
                }
            },
            "request": {
                "repository_url": "https://github.com/example/api-service",
                "branch": "develop"
            }
        }
        
        # Create context and generate LLM prompt
        context = gate_explainability_engine.create_validation_context(sample_gate, sample_shared)
        llm_prompt = gate_explainability_engine.generate_llm_prompt(context)
        
        print("✅ Enhanced recommendation prompt generated")
        print(f"   • Prompt length: {len(llm_prompt)} characters")
        print(f"   • Contains root cause analysis request: {'Root Cause Analysis' in llm_prompt}")
        print(f"   • Contains impact assessment request: {'Impact Assessment' in llm_prompt}")
        print(f"   • Contains specific recommendations request: {'Specific Recommendations' in llm_prompt}")
        print(f"   • Contains code examples request: {'Code Examples' in llm_prompt}")
        print(f"   • Contains best practices request: {'Best Practices' in llm_prompt}")
        print(f"   • Contains priority actions request: {'Priority Actions' in llm_prompt}")
        
        # Test violation details extraction
        print("\n📋 Testing violation details extraction...")
        violation_details = context.violation_details
        print(f"   ✅ Extracted {len(violation_details)} violation details")
        
        for i, violation in enumerate(violation_details):
            print(f"      • Violation {i+1}: {violation['file']}:{violation['line']} - {violation['type']} ({violation['severity']})")
        
        # Test code examples extraction
        print("\n💻 Testing code examples extraction...")
        code_examples = context.code_examples
        print(f"   ✅ Extracted {len(code_examples)} code examples")
        
        for i, example in enumerate(code_examples):
            print(f"      • Example {i+1}: {example['file']}:{example['line']} ({example['language']})")
        
        print("\n🎉 Enhanced recommendation tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced recommendation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all explainability tests"""
    print("🚀 Starting Gate Explainability Tests")
    print("=" * 50)
    
    # Test basic explainability engine
    test1_passed = test_explainability_engine()
    
    # Test enhanced recommendations
    test2_passed = test_enhanced_recommendations()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   • Explainability Engine: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • Enhanced Recommendations: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Explainability functionality is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
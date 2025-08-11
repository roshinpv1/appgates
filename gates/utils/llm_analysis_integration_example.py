"""
LLM Analysis Integration Example
Shows how to integrate LLM analysis with existing gate evaluation to generate better recommendations
"""

from typing import Dict, Any, List
from .llm_analysis_node import LLMAnalysisNode, integrate_llm_analysis_with_gate_evaluation, batch_process_gate_results


def example_integration_with_existing_system():
    """
    Example showing how to integrate LLM analysis with existing gate evaluation results
    """
    
    # Simulate gate evaluation results (similar to what ValidateGatesNode produces)
    gate_results = [
        {
            "gate": "STRUCTURED_LOGS",
            "status": "PASS",
            "score": 85.0,
            "details": ["Found structured logging in 12 files", "All critical files have proper logging"],
            "matches": [
                {"file": "src/main/java/com/app/Controller.java", "pattern": "logger.info"},
                {"file": "src/main/java/com/app/Service.java", "pattern": "structured.*log"}
            ],
            "patterns_used": 3,
            "matches_found": 15,
            "recommendations": []  # Empty - will be replaced by LLM analysis
        },
        {
            "gate": "ALERTING_ACTIONABLE",
            "status": "FAIL",
            "score": 30.0,
            "details": ["Missing Splunk integration", "AppDynamics not configured"],
            "matches": [],
            "patterns_used": 0,
            "matches_found": 0,
            "recommendations": []  # Empty - will be replaced by LLM analysis
        },
        {
            "gate": "AVOID_LOGGING_SECRETS",
            "status": "PASS",
            "score": 95.0,
            "details": ["No secrets found in logging statements"],
            "matches": [],
            "patterns_used": 5,
            "matches_found": 0,
            "recommendations": []  # Empty - will be replaced by LLM analysis
        },
        {
            "gate": "AUTO_SCALE",
            "status": "FAIL",
            "score": 25.0,
            "details": ["Missing replica configurations", "No connection pooling setup", "Found in SpringConfig"],
            "matches": [
                {"file": "src/main/java/com/app/SpringConfig.java", "pattern": "replica", "context": "Missing replica configuration"}
            ],
            "patterns_used": 2,
            "matches_found": 1,
            "recommendations": []  # Empty - will be replaced by LLM analysis
        }
    ]
    
    # Simulate pattern data (similar to what LLM pattern generation produces)
    pattern_data = {
        "STRUCTURED_LOGS": {
            "patterns": ["logger.info", "structured.*log", "json.*log"],
            "description": "Structured logging patterns for Java applications",
            "significance": "Critical for monitoring and debugging"
        },
        "ALERTING_ACTIONABLE": {
            "patterns": [],
            "description": "Database integration check",
            "significance": "Ensures alerting is actionable"
        },
        "AVOID_LOGGING_SECRETS": {
            "patterns": ["password.*log", "secret.*log", "token.*log"],
            "description": "Security patterns to prevent secret logging",
            "significance": "Critical for security compliance"
        },
        "AUTO_SCALE": {
            "patterns": ["replica", "connection.*pool", "autoscale"],
            "description": "Auto-scaling and replica configuration patterns",
            "significance": "Critical for infrastructure scalability"
        }
    }
    
    print("🚀 Starting LLM Analysis Integration Example...")
    print(f"   📊 Processing {len(gate_results)} gate results")
    
    # Method 1: Direct integration
    print("\n📋 Method 1: Direct Integration")
    print("=" * 50)
    
    try:
        # Create LLM analysis node
        llm_analysis_node = LLMAnalysisNode()
        
        # Process gate results with LLM analysis
        processed_results = llm_analysis_node.process_gate_results(gate_results, pattern_data)
        
        # Show results
        for result in processed_results:
            gate_name = result["gate"]
            status = result["status"]
            recommendations = result.get("llm_recommendations", result.get("recommendations", []))
            
            print(f"\n🔍 {gate_name} ({status}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
            
            # Show if fallback was used
            if result.get("llm_analysis_fallback"):
                print(f"   ⚠️ Used fallback recommendations (LLM not available)")
            elif result.get("llm_analysis_error"):
                print(f"   ❌ LLM analysis error: {result['llm_analysis_error']}")
            else:
                print(f"   ✅ LLM analysis completed successfully")
    
    except Exception as e:
        print(f"❌ Direct integration failed: {e}")
    
    # Method 2: Convenience function
    print("\n📋 Method 2: Convenience Function")
    print("=" * 50)
    
    try:
        processed_results = integrate_llm_analysis_with_gate_evaluation(gate_results, pattern_data)
        
        # Show results
        for result in processed_results:
            gate_name = result["gate"]
            status = result["status"]
            recommendations = result.get("llm_recommendations", result.get("recommendations", []))
            
            print(f"\n🔍 {gate_name} ({status}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
    
    except Exception as e:
        print(f"❌ Convenience function failed: {e}")
    
    # Method 3: Batch processing
    print("\n📋 Method 3: Batch Processing")
    print("=" * 50)
    
    try:
        batch_result = batch_process_gate_results(gate_results, pattern_data)
        
        print(f"📊 Batch Processing Results:")
        print(f"   Total gates: {batch_result['total_gates']}")
        print(f"   Successful batches: {batch_result['successful_batches']}")
        print(f"   LLM analysis enabled: {batch_result['llm_analysis_enabled']}")
        
        # Show sample results
        processed_results = batch_result["processed_results"]
        for result in processed_results[:2]:  # Show first 2 results
            gate_name = result["gate"]
            status = result["status"]
            recommendations = result.get("llm_recommendations", result.get("recommendations", []))
            
            print(f"\n🔍 {gate_name} ({status}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
    
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")


def show_prompt_examples():
    """Show examples of the prompts that would be generated"""
    
    print("\n📝 LLM Analysis Prompt Examples")
    print("=" * 50)
    
    # Example gate result
    gate_result = {
        "gate": "AUTO_SCALE",
        "status": "FAIL",
        "score": 25.0,
        "details": ["Missing replica configurations", "No connection pooling setup", "Found in SpringConfig"],
        "matches": [
            {"file": "src/main/java/com/app/SpringConfig.java", "pattern": "replica", "context": "Missing replica configuration"}
        ]
    }
    
    pattern_data = {
        "AUTO_SCALE": {
            "patterns": ["replica", "connection.*pool", "autoscale"],
            "description": "Auto-scaling and replica configuration patterns",
            "significance": "Critical for infrastructure scalability"
        }
    }
    
    # Create LLM analysis node
    llm_analysis_node = LLMAnalysisNode()
    
    # Generate prompt
    prompt = llm_analysis_node._generate_analysis_prompt(gate_result, pattern_data)
    
    print("Generated Prompt for AUTO_SCALE (FAIL):")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    # Example success case
    success_gate_result = {
        "gate": "STRUCTURED_LOGS",
        "status": "PASS",
        "score": 85.0,
        "details": ["Found structured logging in 12 files"],
        "matches": [
            {"file": "src/main/java/com/app/Controller.java", "pattern": "logger.info"}
        ]
    }
    
    success_pattern_data = {
        "STRUCTURED_LOGS": {
            "patterns": ["logger.info", "structured.*log", "json.*log"],
            "description": "Structured logging patterns for Java applications",
            "significance": "Critical for monitoring and debugging"
        }
    }
    
    success_prompt = llm_analysis_node._generate_analysis_prompt(success_gate_result, success_pattern_data)
    
    print("\nGenerated Prompt for STRUCTURED_LOGS (PASS):")
    print("-" * 40)
    print(success_prompt)
    print("-" * 40)


def compare_recommendations():
    """Compare static vs LLM-based recommendations"""
    
    print("\n🔄 Comparing Static vs LLM-based Recommendations")
    print("=" * 60)
    
    # Example gate result
    gate_result = {
        "gate": "AUTO_SCALE",
        "status": "FAIL",
        "score": 25.0,
        "details": ["Missing replica configurations", "No connection pooling setup", "Found in SpringConfig"],
        "matches": [
            {"file": "src/main/java/com/app/SpringConfig.java", "pattern": "replica", "context": "Missing replica configuration"}
        ]
    }
    
    pattern_data = {
        "AUTO_SCALE": {
            "patterns": ["replica", "connection.*pool", "autoscale"],
            "description": "Auto-scaling and replica configuration patterns",
            "significance": "Critical for infrastructure scalability"
        }
    }
    
    # Create LLM analysis node
    llm_analysis_node = LLMAnalysisNode()
    
    # Generate static recommendations
    static_recommendations = llm_analysis_node._generate_fallback_recommendations_for_gate(gate_result)
    
    print("📋 Static Recommendations:")
    for i, rec in enumerate(static_recommendations, 1):
        print(f"   {i}. {rec}")
    
    print("\n🤖 LLM-based Recommendations (if available):")
    print("   (Would be generated by calling LLM with structured prompt)")
    print("   - More detailed and contextual")
    print("   - Based on actual code patterns found")
    print("   - Specific to the technology stack")
    print("   - Actionable with concrete steps")
    
    # Show the prompt that would be used
    prompt = llm_analysis_node._generate_analysis_prompt(gate_result, pattern_data)
    print(f"\n📝 LLM Prompt Length: {len(prompt)} characters")
    print(f"📝 Prompt Preview: {prompt[:200]}...")


if __name__ == "__main__":
    print("🎯 LLM Analysis Integration Example")
    print("=" * 50)
    
    # Show prompt examples
    show_prompt_examples()
    
    # Compare recommendations
    compare_recommendations()
    
    # Run integration example
    example_integration_with_existing_system()
    
    print("\n🎉 Example completed!") 
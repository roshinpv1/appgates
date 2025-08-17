"""
LLM Analysis Node for Gate Evaluation
Integrates LLM analysis prompts with gate evaluation to generate better recommendations
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import time
import threading

from .llm_analysis_prompts import (
    generate_success_prompt,
    generate_failure_prompt,
    LLMAnalysisPromptGenerator
)
from .llm_client import LLMClient, LLMConfig, LLMProvider, create_llm_client_from_env


class LLMAnalysisNode:
    """Node to generate LLM-based recommendations for gate evaluation results"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or create_llm_client_from_env()
        self.timeout = 30  # 30 seconds timeout for LLM calls
    
    def process_gate_results(self, gate_results: List[Dict[str, Any]], pattern_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process gate results and generate LLM-based recommendations
        
        Args:
            gate_results: List of gate evaluation results
            pattern_data: Pattern data for all gates
            
        Returns:
            Updated gate results with LLM-based recommendations only
        """
        
        print("🤖 Generating LLM-based recommendations for gate results...")
        
        if not self.llm_client or not self.llm_client.is_available():
            print("   ❌ LLM client not available - cannot generate recommendations")
            return self._add_fallback_recommendations(gate_results)
        
        processed_results = []
        
        for i, gate_result in enumerate(gate_results):
            gate_name = gate_result.get("gate", "UNKNOWN")
            status = gate_result.get("status", "FAIL")
            
            print(f"   🔍 Processing {gate_name} ({status})... ({i+1}/{len(gate_results)})")
            
            try:
                # Generate LLM analysis prompt
                prompt = self._generate_analysis_prompt(gate_result, pattern_data)
                
                # Call LLM for analysis
                llm_recommendations = self._call_llm_for_analysis(prompt, gate_name, status)
                
                # Update gate result with LLM recommendations only
                updated_result = gate_result.copy()
                updated_result["llm_recommendations"] = llm_recommendations
                updated_result["recommendations"] = llm_recommendations  # Replace static recommendations
                updated_result["llm_analysis_prompt"] = prompt
                updated_result["llm_analysis_used"] = True
                
                processed_results.append(updated_result)
                
                print(f"   ✅ {gate_name}: Generated {len(llm_recommendations)} LLM recommendations")
                
            except Exception as e:
                print(f"   ❌ {gate_name}: LLM analysis failed - {e}")
                # Use empty recommendations instead of fallback
                empty_result = gate_result.copy()
                empty_result["llm_recommendations"] = []
                empty_result["recommendations"] = []
                empty_result["llm_analysis_error"] = str(e)
                empty_result["llm_analysis_failed"] = True
                processed_results.append(empty_result)
        
        print(f"✅ Completed LLM analysis for {len(processed_results)} gates")
        return processed_results
    
    def _generate_analysis_prompt(self, gate_result: Dict[str, Any], pattern_data: Dict[str, Any]) -> str:
        """Generate LLM analysis prompt for a gate result"""
        
        gate_name = gate_result.get("gate", "UNKNOWN")
        status = gate_result.get("status", "FAIL")
        score = gate_result.get("score", 0.0)
        details = gate_result.get("details", [])
        matches = gate_result.get("matches", [])
        
        # Prepare evaluation details
        evaluation_details = f"Gate: {gate_name}, Status: {status}, Score: {score:.1f}%"
        if details:
            evaluation_details += f"\nDetails: {'; '.join(details)}"
        
        # Prepare condition message
        if status == "PASS":
            condition_message = f"Gate passed with {len(matches)} matches found"
            pattern_data_str = None
            if gate_name in pattern_data:
                patterns = pattern_data[gate_name].get("patterns", [])
                pattern_data_str = f"Patterns used: {', '.join(patterns)}"
            
            return generate_success_prompt(
                gate_name=gate_name,
                success_condition_message=condition_message,
                evaluation_details=evaluation_details,
                pattern_data=pattern_data_str
            )
        else:
            condition_message = f"Gate failed with {len(matches)} matches found"
            pattern_data_str = None
            if gate_name in pattern_data:
                patterns = pattern_data[gate_name].get("patterns", [])
                pattern_data_str = f"Patterns used: {', '.join(patterns)}"
            
            return generate_failure_prompt(
                gate_name=gate_name,
                failed_condition_message=condition_message,
                evaluation_details=evaluation_details,
                pattern_data=pattern_data_str
            )
    
    def _call_llm_for_analysis(self, prompt: str, gate_name: str, status: str) -> List[str]:
        """Call LLM for analysis and parse recommendations"""
        
        if not self.llm_client:
            raise Exception("LLM client not available")
        
        # Use threading with timeout to prevent hanging
        result_container = {"response": "", "error": None, "completed": False}
        
        def llm_call_with_timeout():
            try:
                response = self.llm_client.call_llm(
                    prompt,
                    gate_name=gate_name,
                    conversation_type="gate_analysis",
                    context={"gate_status": status},
                    metadata={"analysis_type": "gate_evaluation"}
                )
                result_container["response"] = response
                result_container["completed"] = True
            except Exception as e:
                result_container["error"] = str(e)
                result_container["completed"] = True
        
        # Start LLM call in a separate thread
        thread = threading.Thread(target=llm_call_with_timeout)
        thread.daemon = True
        thread.start()
        
        # Wait for completion with timeout
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            raise Exception(f"LLM call timed out after {self.timeout} seconds")
        
        if result_container["error"]:
            raise Exception(f"LLM call failed: {result_container['error']}")
        
        # Parse the LLM response into recommendations
        return self._parse_llm_response(result_container["response"])
    
    def _parse_llm_response(self, response: str) -> List[str]:
        """Parse LLM response into structured recommendations"""
        
        if not response:
            return []
        
        # Split response into lines and extract recommendations
        lines = response.strip().split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are just section headers or formatting
            if line.startswith('-') and len(line) > 10:
                # This looks like a recommendation
                recommendation = line[1:].strip()  # Remove the dash
                if recommendation:
                    recommendations.append(recommendation)
            elif line.startswith('•') and len(line) > 10:
                # This looks like a recommendation with bullet point
                recommendation = line[1:].strip()  # Remove the bullet
                if recommendation:
                    recommendations.append(recommendation)
            elif len(line) > 20 and not line.startswith('#'):
                # This might be a standalone recommendation
                recommendations.append(line)
        
        # If no structured recommendations found, treat the whole response as one recommendation
        if not recommendations:
            # Clean up the response and split into sentences
            cleaned_response = response.replace('\n', ' ').strip()
            if len(cleaned_response) > 50:
                recommendations = [cleaned_response]
            else:
                recommendations = []
        
        return recommendations[:5]  # Limit to 5 recommendations max
    
    def _add_fallback_recommendations(self, gate_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add empty recommendations when LLM is not available"""
        
        print("   ⚠️ LLM not available - using empty recommendations")
        
        updated_results = []
        for gate_result in gate_results:
            updated_result = gate_result.copy()
            updated_result["llm_recommendations"] = []
            updated_result["recommendations"] = []
            updated_result["llm_analysis_unavailable"] = True
            updated_results.append(updated_result)
        
        return updated_results
    
    def _generate_fallback_recommendations_for_gate(self, gate_result: Dict[str, Any]) -> List[str]:
        """Generate empty recommendations - no static fallback"""
        return []


def integrate_llm_analysis_with_gate_evaluation(gate_results: List[Dict[str, Any]], pattern_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convenience function to integrate LLM analysis with gate evaluation results
    
    Args:
        gate_results: Results from gate evaluation
        pattern_data: Pattern data for all gates
        
    Returns:
        Updated gate results with LLM-based recommendations only
    """
    
    llm_analysis_node = LLMAnalysisNode()
    return llm_analysis_node.process_gate_results(gate_results, pattern_data)


def batch_process_gate_results(gate_results: List[Dict[str, Any]], pattern_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process gate results in batches for better performance
    
    Args:
        gate_results: Results from gate evaluation
        pattern_data: Pattern data for all gates
        
    Returns:
        Dictionary with processed results and metadata
    """
    
    llm_analysis_node = LLMAnalysisNode()
    
    # Process in batches of 5 to avoid overwhelming the LLM
    batch_size = 5
    processed_results = []
    total_batches = (len(gate_results) + batch_size - 1) // batch_size
    
    print(f"🔄 Processing {len(gate_results)} gates in {total_batches} batches...")
    
    for i in range(0, len(gate_results), batch_size):
        batch = gate_results[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"   📦 Processing batch {batch_num}/{total_batches} ({len(batch)} gates)...")
        
        try:
            batch_results = llm_analysis_node.process_gate_results(batch, pattern_data)
            processed_results.extend(batch_results)
            
            print(f"   ✅ Batch {batch_num} completed successfully")
            
        except Exception as e:
            print(f"   ❌ Batch {batch_num} failed: {e}")
            # Add empty recommendations for this batch
            for gate_result in batch:
                empty_result = gate_result.copy()
                empty_result["llm_recommendations"] = []
                empty_result["recommendations"] = []
                empty_result["llm_analysis_error"] = str(e)
                empty_result["llm_analysis_failed"] = True
                processed_results.append(empty_result)
    
    return {
        "processed_results": processed_results,
        "total_gates": len(gate_results),
        "successful_batches": total_batches,
        "llm_analysis_enabled": True
    } 
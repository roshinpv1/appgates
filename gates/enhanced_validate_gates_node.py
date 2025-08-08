"""
Enhanced ValidateGatesNode with CriteriaEvaluator Integration
Provides both legacy and enhanced evaluation modes
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from base import Node
from datetime import datetime

# Import the new criteria evaluator
try:
    from .criteria_evaluator import EnhancedGateEvaluator, CriteriaEvaluator, migrate_legacy_gate
except ImportError:
    from criteria_evaluator import EnhancedGateEvaluator, CriteriaEvaluator, migrate_legacy_gate

# Import existing utilities
try:
    from .utils.git_operations import clone_repository, cleanup_repository
    from .utils.file_scanner import scan_directory
    from .utils.hard_gates import HARD_GATES
    from .utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider
    from .utils.gate_applicability import gate_applicability_analyzer
except ImportError:
    from utils.git_operations import clone_repository, cleanup_repository
    from utils.file_scanner import scan_directory
    from utils.hard_gates import HARD_GATES
    from utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider
    from utils.gate_applicability import gate_applicability_analyzer


class EnhancedValidateGatesNode(Node):
    """Enhanced node to validate gates using criteria-based evaluation with fallback to legacy system"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare validation parameters with enhanced evaluation support"""
        # Get LLM patterns if available, otherwise use empty dict
        llm_patterns = shared["llm"].get("patterns", {})
        pattern_data = shared["llm"].get("pattern_data", {})
        
        # If no LLM patterns are available, use fallback patterns
        if not llm_patterns:
            print("   ⚠️ No LLM patterns available, using static patterns only")
            # Generate fallback patterns for each gate
            fallback_patterns = {}
            fallback_data = {}
            for gate in shared["hard_gates"]:
                gate_name = gate["name"]
                fallback_patterns[gate_name] = []
                fallback_data[gate_name] = {
                    "description": f"Static pattern analysis for {gate['display_name']}",
                    "significance": "Important for code quality and compliance",
                    "expected_coverage": {
                        "percentage": 10,
                        "reasoning": "Standard expectation for this gate type",
                        "confidence": "medium"
                    }
                }
            llm_patterns = fallback_patterns
            pattern_data = fallback_data
        
        # Analyze gate applicability based on codebase type
        metadata = shared["repository"]["metadata"]
        applicability_summary = gate_applicability_analyzer.get_applicability_summary(metadata)
        applicable_gates = gate_applicability_analyzer.determine_applicable_gates(metadata)
        
        print(f"🔍 Gate Applicability Analysis:")
        print(f"   📊 Codebase Type: {applicability_summary['codebase_characteristics']['primary_technology']}")
        print(f"   📋 Languages: {', '.join(applicability_summary['codebase_characteristics']['languages'][:5])}")
        print(f"   ✅ Applicable Gates: {applicability_summary['applicable_gates']}/{applicability_summary['total_gates']}")
        print(f"   ❌ Non-Applicable Gates: {applicability_summary['non_applicable_gates']}")
        
        if applicability_summary['non_applicable_details']:
            print(f"   📝 Non-Applicable Details:")
            for gate in applicability_summary['non_applicable_details']:
                print(f"      - {gate['name']} ({gate['category']}): {gate['reason']}")
        
        # Check if enhanced pattern library exists
        enhanced_pattern_library_path = Path("patterns/enhanced_pattern_library.json")
        use_enhanced_evaluation = enhanced_pattern_library_path.exists()
        
        if use_enhanced_evaluation:
            print("   🚀 Enhanced criteria-based evaluation available")
        else:
            print("   ⚠️ Enhanced pattern library not found, using legacy evaluation")
        
        return {
            "repo_path": shared["repository"]["local_path"],
            "metadata": shared["repository"]["metadata"],
            "patterns": llm_patterns,
            "pattern_data": pattern_data,
            "hard_gates": shared["hard_gates"],
            "all_hard_gates": shared["hard_gates"],
            "threshold": shared["request"]["threshold"],
            "shared": shared,
            "applicability_summary": applicability_summary,
            "use_enhanced_evaluation": use_enhanced_evaluation
        }
    
    def exec(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate gates using enhanced criteria-based evaluation with legacy fallback"""
        print("🎯 Validating gates with enhanced criteria-based evaluation...")
        
        repo_path = Path(params["repo_path"])
        metadata = params["metadata"]
        use_enhanced_evaluation = params.get("use_enhanced_evaluation", False)
        
        if use_enhanced_evaluation:
            return self._evaluate_with_enhanced_system(params)
        else:
            return self._evaluate_with_legacy_system(params)
    
    def _evaluate_with_enhanced_system(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate gates using the new criteria-based system"""
        print("   🔧 Using enhanced criteria-based evaluation system")
        
        repo_path = Path(params["repo_path"])
        metadata = params["metadata"]
        
        # Load enhanced pattern library
        try:
            with open("patterns/enhanced_pattern_library.json", "r") as f:
                enhanced_pattern_library = json.load(f)
        except FileNotFoundError:
            print("   ❌ Enhanced pattern library not found, falling back to legacy system")
            return self._evaluate_with_legacy_system(params)
        
        # Prepare codebase files and contents for enhanced evaluator
        codebase_files, file_contents = self._prepare_codebase_for_enhanced_evaluation(repo_path, metadata)
        
        # Initialize enhanced evaluator
        evaluator = EnhancedGateEvaluator(codebase_files, file_contents)
        
        # Get gates from enhanced pattern library
        enhanced_gates = enhanced_pattern_library.get("gates", {})
        
        # Map legacy gates to enhanced gates
        legacy_gates = params["hard_gates"]
        gate_results = []
        
        print(f"   🎯 Starting enhanced evaluation of {len(legacy_gates)} gates...")
        
        for i, legacy_gate in enumerate(legacy_gates):
            gate_name = legacy_gate["name"]
            
            # Check if enhanced gate exists
            if gate_name in enhanced_gates:
                print(f"   🔍 Evaluating {gate_name} with enhanced criteria-based system... ({i+1}/{len(legacy_gates)})")
                enhanced_gate_config = enhanced_gates[gate_name]
                
                try:
                    # Evaluate using enhanced system
                    enhanced_result = evaluator.evaluate_gate(gate_name, enhanced_gate_config)
                    
                    # Convert enhanced result to legacy format for compatibility
                    legacy_result = self._convert_enhanced_result_to_legacy_format(
                        enhanced_result, legacy_gate, metadata
                    )
                    
                    gate_results.append(legacy_result)
                    print(f"   ✅ {gate_name} evaluation complete: {legacy_result.get('status', 'UNKNOWN')} ({legacy_result.get('score', 0):.1f}%)")
                    
                except Exception as e:
                    print(f"   ❌ Error evaluating {gate_name}: {e}")
                    # Fall back to legacy evaluation for this gate
                    legacy_result = self._evaluate_single_gate_legacy(legacy_gate, params)
                    gate_results.append(legacy_result)
                
            else:
                print(f"   ⚠️ Enhanced config not found for {gate_name}, using legacy evaluation... ({i+1}/{len(legacy_gates)})")
                # Fall back to legacy evaluation for this gate
                legacy_result = self._evaluate_single_gate_legacy(legacy_gate, params)
                gate_results.append(legacy_result)
        
        print(f"   🎉 Enhanced evaluation complete: {len(gate_results)} gates processed")
        return gate_results
    
    def _evaluate_with_legacy_system(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate gates using the legacy pattern matching system"""
        print("   🔧 Using legacy pattern matching system")
        
        # This is a simplified version of the legacy evaluation
        # In a full implementation, you would copy the entire legacy logic here
        repo_path = Path(params["repo_path"])
        llm_patterns = params["patterns"]
        pattern_data = params["pattern_data"]
        metadata = params["metadata"]
        
        gate_results = []
        
        for gate in params["hard_gates"]:
            legacy_result = self._evaluate_single_gate_legacy(gate, params)
            gate_results.append(legacy_result)
        
        return gate_results
    
    def _evaluate_single_gate_legacy(self, gate: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single gate using legacy pattern matching"""
        gate_name = gate["name"]
        print(f"   🔍 Evaluating {gate_name} with legacy system...")
        
        # Get pattern information from params
        llm_patterns = params.get("patterns", {})
        pattern_data = params.get("pattern_data", {})
        llm_gate_patterns = llm_patterns.get(gate_name, [])
        gate_pattern_info = pattern_data.get(gate_name, {})
        
        # Calculate actual pattern count
        patterns_used = len(llm_gate_patterns)
        
        # For this simplified fallback, return a basic result with proper pattern counting
        return {
            "gate": gate_name,
            "display_name": gate["display_name"],
            "description": gate["description"],
            "category": gate["category"],
            "priority": gate["priority"],
            "patterns_used": patterns_used,  # Use actual pattern count
            "pattern_count": patterns_used,  # Also set pattern_count for UI consistency
            "patterns": llm_gate_patterns,  # Include actual patterns array
            "matches_found": 0,
            "matches": [],
            "score": 0.0,
            "status": "FAIL",
            "details": [f"Legacy evaluation fallback - {patterns_used} patterns available"],
            "evidence": f"Legacy pattern matching with {patterns_used} patterns",
            "recommendations": ["Enhanced criteria-based evaluation recommended"],
            "confidence": 50.0,
            "files_with_matches": 0,
            "total_files": 1,
            "relevant_files": 0,
            "validation_sources": {
                "llm_patterns": {"count": patterns_used, "matches": 0, "source": "legacy_fallback"},
                "static_patterns": {"count": 0, "matches": 0, "source": "legacy_fallback"},
                "combined_confidence": "Medium",
            }
        }
    
    def _prepare_codebase_for_enhanced_evaluation(self, repo_path: Path, metadata: Dict[str, Any]) -> tuple[List[str], Dict[str, str]]:
        """Prepare codebase files and contents for enhanced evaluation"""
        print("   📁 Preparing codebase for enhanced evaluation...")
        
        codebase_files = []
        file_contents = {}
        
        # Get all files from metadata - handle different metadata structures
        files_info = metadata.get("file_list", [])  # Changed from "files" to "file_list"
        
        if not files_info:
            # If no files in metadata, scan the repository directly
            print("   ⚠️ No files in metadata, scanning repository directly...")
            for file_path in repo_path.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        relative_path = str(file_path.relative_to(repo_path))
                        codebase_files.append(relative_path)
                        
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            file_contents[relative_path] = content
                    except Exception as e:
                        print(f"   ⚠️ Could not read {file_path}: {e}")
        else:
            # Process files from metadata
            for file_info in files_info:
                if isinstance(file_info, dict):
                    file_path = file_info.get("path", "")
                    relative_path = file_info.get("relative_path", "")
                else:
                    file_path = str(file_info)
                    relative_path = ""
                
                if file_path:
                    # Convert to relative path
                    try:
                        if os.path.isabs(file_path):
                            relative_path = os.path.relpath(file_path, repo_path)
                        elif not relative_path:
                            relative_path = file_path
                        
                        codebase_files.append(relative_path)
                        
                        # Read file content
                        full_path = repo_path / relative_path
                        if full_path.exists():
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                file_contents[relative_path] = content
                        else:
                            file_contents[relative_path] = ""
                    except Exception as e:
                        print(f"   ⚠️ Could not read {relative_path}: {e}")
                        file_contents[relative_path] = ""
        
        print(f"   📊 Prepared {len(codebase_files)} files for enhanced evaluation")
        return codebase_files, file_contents
    
    def _convert_enhanced_result_to_legacy_format(self, enhanced_result: Dict[str, Any], legacy_gate: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert enhanced evaluation result to legacy format for compatibility"""
        
        # Extract enhanced result data
        score = enhanced_result.get("score", 0.0)
        status = enhanced_result.get("status", "FAIL")
        matches = enhanced_result.get("matches", [])
        condition_results = enhanced_result.get("condition_results", [])
        
        # Convert matches to legacy format
        legacy_matches = []
        for match in matches:
            legacy_matches.append({
                "file": match.file,
                "pattern": match.pattern,
                "match": match.context or f"Pattern: {match.pattern}",
                "line": match.line_number or 0,
                "language": self._detect_language_from_file(match.file),
                "source": "enhanced_criteria"
            })
        
        # Generate details from condition results
        details = []
        for condition in condition_results:
            condition_status = "✅ PASS" if condition.passed else "❌ FAIL"
            details.append(f"{condition.condition_name}: {condition_status}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations_from_enhanced_result(enhanced_result, legacy_gate)
        
        # Create legacy format result
        return {
            "gate": enhanced_result.get("gate_name", legacy_gate["name"]),
            "display_name": enhanced_result.get("display_name", legacy_gate["display_name"]),
            "description": enhanced_result.get("description", legacy_gate.get("description", "")),
            "category": enhanced_result.get("category", legacy_gate.get("category", "Unknown")),
            "priority": legacy_gate.get("priority", "Medium"),
            "patterns_used": len(matches),
            "matches_found": len(legacy_matches),
            "matches": legacy_matches,
            "patterns": [match.pattern for match in matches],
            "score": score,
            "status": status,
            "details": details,
            "evidence": f"Enhanced criteria evaluation: {len(matches)} matches found",
            "recommendations": recommendations,
            "pattern_description": legacy_gate.get("description", "Enhanced criteria-based analysis"),
            "pattern_significance": legacy_gate.get("significance", "Important for code quality"),
            "expected_coverage": legacy_gate.get("expected_coverage", {
                "percentage": 25,
                "reasoning": "Standard expectation for enhanced evaluation",
                "confidence": "high"
            }),
            "total_files": metadata.get("total_files", 1),
            "relevant_files": len(set(match.file for match in matches)),
            "validation_sources": {
                "llm_patterns": {"count": len(matches), "matches": len(matches), "source": "enhanced_criteria"},
                "static_patterns": {"count": 0, "matches": 0, "source": "enhanced_criteria"},
                "combined_confidence": "high"
            },
            # Enhanced data for future use
            "enhanced_data": {
                "criteria_score": enhanced_result.get("criteria_score", 0.0),
                "coverage_score": enhanced_result.get("coverage_score", 0.0),
                "condition_results": [
                    {
                        "name": condition.condition_name,
                        "type": condition.type,
                        "operator": condition.operator,
                        "passed": condition.passed,
                        "weight": condition.weight,
                        "matches_count": len(condition.matches)
                    }
                    for condition in condition_results
                ]
            }
        }
    
    def _detect_language_from_file(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            ".java": "Java",
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".cs": "C#",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".rb": "Ruby",
            ".scala": "Scala",
            ".kt": "Kotlin",
            ".swift": "Swift"
        }
        return language_map.get(ext, "Unknown")
    
    def _generate_recommendations_from_enhanced_result(self, enhanced_result: Dict[str, Any], legacy_gate: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on enhanced evaluation results"""
        recommendations = []
        
        score = enhanced_result.get("score", 0.0)
        status = enhanced_result.get("status", "FAIL")
        condition_results = enhanced_result.get("condition_results", [])
        
        if status == "PASS":
            recommendations.append("✅ Gate requirements met successfully")
        else:
            recommendations.append("❌ Gate requirements not met")
        
        # Add specific recommendations based on condition results
        for condition in condition_results:
            if not condition.passed:
                recommendations.append(f"⚠️ Condition '{condition.condition_name}' failed - review implementation")
            else:
                recommendations.append(f"✅ Condition '{condition.condition_name}' passed")
        
        # Add general recommendations
        if score < 50:
            recommendations.append("🔧 Consider improving implementation to meet higher standards")
        elif score < 80:
            recommendations.append("📈 Good implementation, consider minor improvements")
        else:
            recommendations.append("🎉 Excellent implementation")
        
        return recommendations
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: List[Dict[str, Any]]) -> str:
        """Store gate validation results in shared store"""
        shared["gate_validation"] = {
            "results": exec_res,
            "timestamp": datetime.now().isoformat(),
            "evaluation_mode": "enhanced" if prep_res.get("use_enhanced_evaluation") else "legacy"
        }
        
        # Calculate summary statistics
        total_gates = len(exec_res)
        passed_gates = sum(1 for result in exec_res if result.get("status") == "PASS")
        failed_gates = total_gates - passed_gates
        
        print(f"✅ Gate validation completed:")
        print(f"   📊 Total gates: {total_gates}")
        print(f"   ✅ Passed: {passed_gates}")
        print(f"   ❌ Failed: {failed_gates}")
        print(f"   🎯 Success rate: {(passed_gates/total_gates*100):.1f}%")
        
        return "default" 
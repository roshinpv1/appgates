"""
Enhanced Validation Node
Integrates configurable gates with evidence collection for comprehensive validation
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..utils.gate_config_loader import GateConfigLoader, ValidationType, get_all_gates, get_gate_config
from ..utils.unified_evidence_collector import EvidenceManager, collect_evidence_for_gate, is_evidence_available
from ..utils.db_integration import fetch_alerting_integrations_status
from ..utils.llm_client import create_llm_client_from_env
from .base_node import Node


@dataclass
class ValidationResult:
    """Result of a validation check"""
    gate_name: str
    validation_type: ValidationType
    success: bool
    score: float
    evidence: Dict[str, Any]
    details: List[str]
    recommendations: List[str]


class EnhancedValidationNode(Node):
    """Enhanced validation node with configurable gates and evidence collection"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the enhanced validation node"""
        super().__init__()
        self.config_loader = GateConfigLoader(config_path)
        self.evidence_available = is_evidence_available()
        
        if not self.evidence_available:
            print("⚠️ Evidence collection not available. Install required dependencies for full functionality.")
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare validation parameters"""
        print("🔧 Preparing enhanced validation with configurable gates...")
        
        # Get all enabled gates from configuration
        gates = get_all_gates()
        print(f"   📋 Loaded {len(gates)} gates from configuration")
        
        # Categorize gates by validation type
        gates_by_type = {}
        for val_type in ValidationType:
            gates_by_type[val_type] = self.config_loader.get_gates_by_validation_type(val_type)
            print(f"   {val_type.value}: {len(gates_by_type[val_type])} gates")
        
        # Extract app domain for evidence collection
        app_domain = self._extract_app_domain(shared)
        
        return {
            "gates": gates,
            "gates_by_type": gates_by_type,
            "app_domain": app_domain,
            "repo_path": shared["repository"]["local_path"],
            "metadata": shared["repository"]["metadata"],
            "shared": shared
        }
    
    def exec(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute enhanced validation with all validation types"""
        print("🎯 Executing enhanced validation with configurable gates...")
        
        gates = params["gates"]
        gates_by_type = params["gates_by_type"]
        app_domain = params["app_domain"]
        repo_path = Path(params["repo_path"])
        metadata = params["metadata"]
        
        all_results = []
        
        # Process each gate with its configured validation types
        for gate in gates:
            print(f"   🔍 Validating gate: {gate.name}")
            
            gate_result = self._validate_single_gate(gate, gates_by_type, app_domain, repo_path, metadata, params)
            all_results.append(gate_result)
        
        print(f"   ✅ Enhanced validation complete: {len(all_results)} gates processed")
        return all_results
    
    def _validate_single_gate(self, gate, gates_by_type: Dict, app_domain: str, 
                             repo_path: Path, metadata: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single gate using unified evidence collection"""
        if not self.evidence_available:
            return {
                "gate": gate.name,
                "display_name": gate.display_name,
                "description": gate.description,
                "category": gate.category,
                "priority": gate.priority,
                "weight": gate.weight,
                "score": 0.0,
                "status": "FAIL",
                "evidence": {},
                "details": ["Evidence collection not available"],
                "recommendations": ["Install required dependencies for evidence collection"],
                "validation_results": [],
                "total_files": metadata.get("total_files", 1),
                "validation_sources": {
                    "unified_evidence_collector": {"enabled": False, "methods": []}
                }
            }
        
        try:
            # Use unified evidence collector
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            evidence_results = loop.run_until_complete(
                collect_evidence_for_gate(gate, app_domain, repo_path, metadata)
            )
            loop.close()
            
            # Calculate overall score from all evidence methods
            total_score = 0.0
            evidence_count = 0
            all_evidence = {}
            all_details = []
            all_recommendations = []
            validation_results = []
            
            for method_name, evidence_result in evidence_results.items():
                if evidence_result.success:
                    total_score += evidence_result.score
                    evidence_count += 1
                
                all_evidence[method_name] = evidence_result.data
                all_details.append(f"{method_name}: {evidence_result.score:.1f}%")
                
                if evidence_result.error:
                    all_details.append(f"{method_name} error: {evidence_result.error}")
                
                validation_results.append({
                    "type": method_name,
                    "success": evidence_result.success,
                    "score": evidence_result.score,
                    "evidence": evidence_result.data,
                    "details": [f"{method_name} evidence collection completed"]
                })
            
            # Calculate overall score
            overall_score = total_score / evidence_count if evidence_count > 0 else 0.0
            
            # Determine status based on scoring configuration
            scoring_config = gate.scoring
            pass_threshold = scoring_config.get('pass_threshold', 20.0)
            status = "PASS" if overall_score >= pass_threshold else "FAIL"
            
            return {
                "gate": gate.name,
                "display_name": gate.display_name,
                "description": gate.description,
                "category": gate.category,
                "priority": gate.priority,
                "weight": gate.weight,
                "score": overall_score,
                "status": status,
                "evidence": all_evidence,
                "details": all_details,
                "recommendations": list(set(all_recommendations)),
                "validation_results": validation_results,
                "total_files": metadata.get("total_files", 1),
                "validation_sources": {
                    "unified_evidence_collector": {
                        "enabled": True, 
                        "methods": list(evidence_results.keys()),
                        "successful_methods": [k for k, v in evidence_results.items() if v.success]
                    }
                }
            }
            
        except Exception as e:
            return {
                "gate": gate.name,
                "display_name": gate.display_name,
                "description": gate.description,
                "category": gate.category,
                "priority": gate.priority,
                "weight": gate.weight,
                "score": 0.0,
                "status": "FAIL",
                "evidence": {},
                "details": [f"Evidence collection failed: {str(e)}"],
                "recommendations": ["Check evidence collection configuration"],
                "validation_results": [],
                "total_files": metadata.get("total_files", 1),
                "validation_sources": {
                    "unified_evidence_collector": {"enabled": False, "error": str(e)}
                }
            }
    
    def _extract_app_domain(self, shared: Dict[str, Any]) -> str:
        """Extract application domain from repository URL or configuration"""
        repo_url = shared.get('request', {}).get('repository_url', '')
        
        # Try to extract domain from repository URL
        if 'github.com' in repo_url:
            parts = repo_url.split('/')
            if len(parts) >= 5:
                return f"{parts[3]}-{parts[4]}.example.com"
        
        # Default domain
        return "app.example.com" 
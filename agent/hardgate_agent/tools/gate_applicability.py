"""
Gate Applicability Analysis Tool
Analyzes codebase to determine which hard gates are applicable and relevant
"""

import os
import sys
import re
from typing import Dict, Any, List, Set, Optional
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from google.adk.tools.base_tool import BaseTool
    from google.adk.tools import ToolContext
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("⚠️ Google ADK not available")


class GateApplicabilityAnalyzer:
    """Analyzes codebase to determine which gates are applicable"""
    
    def __init__(self):
        # Technology mappings
        self.frontend_technologies = {
            "javascript", "typescript", "html", "css", "scss", "sass", "jsx", "tsx", "vue", "angular", "react"
        }
        
        self.backend_technologies = {
            "python", "java", "csharp", "php", "ruby", "go", "rust", "scala", "kotlin", "swift", "nodejs"
        }
        
        self.mobile_technologies = {
            "swift", "kotlin", "java", "react-native", "flutter", "xamarin", "ionic"
        }
        
        self.database_technologies = {
            "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb"
        }
        
        self.cloud_technologies = {
            "aws", "azure", "gcp", "kubernetes", "docker", "terraform", "helm", "jenkins", "gitlab"
        }
        
        # Gate applicability rules
        self.gate_applicability_rules = {
            "STRUCTURED_LOGS": {
                "applies_to": ["backend", "frontend", "mobile"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "All applications should implement structured logging"
            },
            "AVOID_LOGGING_SECRETS": {
                "applies_to": ["backend", "frontend", "mobile"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "All applications should avoid logging sensitive information"
            },
            "ALERTING_ACTIONABLE": {
                "applies_to": ["backend", "frontend", "mobile"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "All applications should have actionable alerting"
            },
            "AUDIT_TRAIL": {
                "applies_to": ["backend", "frontend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend and frontend applications should maintain audit trails"
            },
            "CORRELATION_ID": {
                "applies_to": ["backend", "frontend", "mobile"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "All applications should implement correlation IDs for request tracing"
            },
            "LOG_API_CALLS": {
                "applies_to": ["backend", "frontend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend and frontend applications should log API calls"
            },
            "CLIENT_UI_ERRORS": {
                "applies_to": ["frontend", "mobile"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Frontend and mobile applications should handle UI errors properly"
            },
            "RETRY_LOGIC": {
                "applies_to": ["backend", "frontend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend and frontend applications should implement retry logic"
            },
            "TIMEOUT_IO": {
                "applies_to": ["backend", "frontend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend and frontend applications should implement proper timeouts"
            },
            "THROTTLING": {
                "applies_to": ["backend", "frontend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend and frontend applications should implement throttling"
            },
            "CIRCUIT_BREAKERS": {
                "applies_to": ["backend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend applications should implement circuit breakers"
            },
            "HTTP_ERROR_CODES": {
                "applies_to": ["backend", "frontend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend and frontend applications should use proper HTTP error codes"
            },
            "URL_MONITORING": {
                "applies_to": ["backend", "frontend"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Backend and frontend applications should implement URL monitoring"
            },
            "AUTOMATED_TESTS": {
                "applies_to": ["backend", "frontend", "mobile"],
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "All applications should have automated tests"
            },
            "AUTO_SCALE": {
                "applies_to": ["backend"],
                "required_technologies": ["kubernetes", "docker", "aws", "azure", "gcp"],
                "excluded_technologies": [],
                "description": "Backend applications in cloud environments should implement auto-scaling"
            }
        }
    
    def analyze_codebase_type(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the codebase to determine its type and characteristics"""
        languages = metadata.get("languages", {})
        language_counts = metadata.get("language_counts", {})
        technologies = metadata.get("technologies", {})
        
        # Determine primary technology
        primary_technology = self._get_primary_technology(languages, language_counts)
        
        # Determine codebase characteristics
        characteristics = {
            "primary_technology": primary_technology,
            "languages": list(languages.keys()),
            "language_counts": language_counts,
            "technologies": technologies,
            "is_frontend": any(lang in self.frontend_technologies for lang in languages),
            "is_backend": any(lang in self.backend_technologies for lang in languages),
            "is_mobile": any(lang in self.mobile_technologies for lang in languages),
            "has_database": any(tech in self.database_technologies for tech in technologies),
            "has_cloud": any(tech in self.cloud_technologies for tech in technologies),
            "is_web_application": self._is_web_application(languages, technologies),
            "is_api_service": self._is_api_service(languages, technologies),
            "is_microservice": self._is_microservice(technologies),
            "is_monolithic": self._is_monolithic(technologies)
        }
        
        return characteristics
    
    def determine_applicable_gates(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine which gates are applicable for the given codebase"""
        characteristics = self.analyze_codebase_type(metadata)
        applicable_gates = []
        
        for gate_name, rules in self.gate_applicability_rules.items():
            applicability = self._check_gate_applicability(gate_name, rules, characteristics)
            
            if applicability["is_applicable"]:
                applicable_gates.append({
                    "gate_name": gate_name,
                    "display_name": gate_name.replace("_", " ").title(),
                    "applicability_reason": applicability["reason"],
                    "codebase_characteristics": characteristics,
                    "priority": self._determine_gate_priority(gate_name, characteristics),
                    "effort_level": self._determine_effort_level(gate_name, characteristics)
                })
        
        return applicable_gates
    
    def get_applicability_summary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of gate applicability analysis"""
        characteristics = self.analyze_codebase_type(metadata)
        applicable_gates = self.determine_applicable_gates(metadata)
        
        # Count gates by category
        gate_categories = {
            "logging": ["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS", "LOG_API_CALLS"],
            "monitoring": ["ALERTING_ACTIONABLE", "URL_MONITORING"],
            "security": ["AUDIT_TRAIL", "CORRELATION_ID"],
            "resilience": ["RETRY_LOGIC", "TIMEOUT_IO", "THROTTLING", "CIRCUIT_BREAKERS"],
            "quality": ["HTTP_ERROR_CODES", "CLIENT_UI_ERRORS", "AUTOMATED_TESTS"],
            "scaling": ["AUTO_SCALE"]
        }
        
        category_counts = {}
        for category, gates in gate_categories.items():
            category_counts[category] = len([g for g in applicable_gates if g["gate_name"] in gates])
        
        return {
            "codebase_characteristics": characteristics,
            "applicable_gates": len(applicable_gates),
            "total_gates": len(self.gate_applicability_rules),
            "non_applicable_gates": len(self.gate_applicability_rules) - len(applicable_gates),
            "category_breakdown": category_counts,
            "primary_technology": characteristics["primary_technology"],
            "technology_stack": characteristics["technologies"]
        }
    
    def _get_primary_technology(self, languages: Set[str], language_counts: Dict[str, int]) -> str:
        """Determine the primary technology based on file counts"""
        if not language_counts:
            return "unknown"
        
        # Find the language with the most files
        primary_lang = max(language_counts.items(), key=lambda x: x[1])[0]
        
        # Map to technology category
        if primary_lang in self.frontend_technologies:
            return "frontend"
        elif primary_lang in self.backend_technologies:
            return "backend"
        elif primary_lang in self.mobile_technologies:
            return "mobile"
        else:
            return "other"
    
    def _is_web_application(self, languages: Set[str], technologies: Set[str]) -> bool:
        """Determine if this is a web application"""
        return (
            any(lang in self.frontend_technologies for lang in languages) or
            any(tech in ["react", "angular", "vue", "django", "flask", "spring"] for tech in technologies)
        )
    
    def _is_api_service(self, languages: Set[str], technologies: Set[str]) -> bool:
        """Determine if this is an API service"""
        return (
            any(lang in self.backend_technologies for lang in languages) and
            any(tech in ["fastapi", "express", "spring", "asp.net"] for tech in technologies)
        )
    
    def _is_microservice(self, technologies: Set[str]) -> bool:
        """Determine if this is a microservice architecture"""
        return any(tech in ["kubernetes", "docker", "helm", "istio"] for tech in technologies)
    
    def _is_monolithic(self, technologies: Set[str]) -> bool:
        """Determine if this is a monolithic application"""
        return not self._is_microservice(technologies)
    
    def _check_gate_applicability(self, gate_name: str, rules: Dict[str, Any], 
                                 characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a gate is applicable based on codebase characteristics"""
        applies_to = rules.get("applies_to", [])
        required_technologies = rules.get("required_technologies", [])
        excluded_technologies = rules.get("excluded_technologies", [])
        
        # Check if primary technology is in applies_to
        primary_tech = characteristics["primary_technology"]
        if primary_tech not in applies_to:
            return {
                "is_applicable": False,
                "reason": f"Gate {gate_name} does not apply to {primary_tech} applications"
            }
        
        # Check required technologies
        if required_technologies:
            has_required = any(tech in characteristics["technologies"] for tech in required_technologies)
            if not has_required:
                return {
                    "is_applicable": False,
                    "reason": f"Gate {gate_name} requires technologies: {', '.join(required_technologies)}"
                }
        
        # Check excluded technologies
        if excluded_technologies:
            has_excluded = any(tech in characteristics["technologies"] for tech in excluded_technologies)
            if has_excluded:
                return {
                    "is_applicable": False,
                    "reason": f"Gate {gate_name} is not applicable with technologies: {', '.join(excluded_technologies)}"
                }
        
        return {
            "is_applicable": True,
            "reason": f"Gate {gate_name} is applicable for {primary_tech} applications"
        }
    
    def _determine_gate_priority(self, gate_name: str, characteristics: Dict[str, Any]) -> str:
        """Determine the priority level for a gate"""
        high_priority_gates = ["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS", "ALERTING_ACTIONABLE"]
        medium_priority_gates = ["AUDIT_TRAIL", "CORRELATION_ID", "AUTOMATED_TESTS", "HTTP_ERROR_CODES"]
        
        if gate_name in high_priority_gates:
            return "High"
        elif gate_name in medium_priority_gates:
            return "Medium"
        else:
            return "Low"
    
    def _determine_effort_level(self, gate_name: str, characteristics: Dict[str, Any]) -> str:
        """Determine the effort level required to implement a gate"""
        high_effort_gates = ["AUTO_SCALE", "CIRCUIT_BREAKERS", "AUTOMATED_TESTS"]
        medium_effort_gates = ["ALERTING_ACTIONABLE", "URL_MONITORING", "THROTTLING"]
        
        if gate_name in high_effort_gates:
            return "High"
        elif gate_name in medium_effort_gates:
            return "Medium"
        else:
            return "Low"


class GateApplicabilityTool(BaseTool):
    """Tool for analyzing gate applicability"""
    
    name = "gate_applicability"
    description = "Analyze codebase to determine which hard gates are applicable and relevant"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
        self.analyzer = GateApplicabilityAnalyzer()
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Analyze gate applicability"""
        try:
            repository_path = args.get("repository_path")
            metadata = args.get("metadata", {})
            
            if not repository_path:
                return {
                    "success": False,
                    "error": "Repository path is required"
                }
            
            # Analyze codebase characteristics
            characteristics = self.analyzer.analyze_codebase_type(metadata)
            
            # Determine applicable gates
            applicable_gates = self.analyzer.determine_applicable_gates(metadata)
            
            # Get applicability summary
            summary = self.analyzer.get_applicability_summary(metadata)
            
            return {
                "success": True,
                "repository_path": repository_path,
                "codebase_characteristics": characteristics,
                "applicable_gates": applicable_gates,
                "summary": summary
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Gate applicability analysis failed: {str(e)}"
            }


# Create wrapper function for Google ADK compatibility
def gate_applicability(repository_path: str, metadata: Optional[Dict[str, Any]] = None, 
                      tool_context = None) -> Dict[str, Any]:
    """
    Analyze codebase to determine which hard gates are applicable and relevant.
    
    Args:
        repository_path: Path to the repository
        metadata: Repository metadata (languages, technologies, etc.)
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing applicability analysis results
    """
    try:
        if not repository_path:
            return {
                "success": False,
                "error": "Repository path is required"
            }
        
        analyzer = GateApplicabilityAnalyzer()
        metadata = metadata or {}
        
        # Analyze codebase characteristics
        characteristics = analyzer.analyze_codebase_type(metadata)
        
        # Determine applicable gates
        applicable_gates = analyzer.determine_applicable_gates(metadata)
        
        # Get applicability summary
        summary = analyzer.get_applicability_summary(metadata)
        
        return {
            "success": True,
            "repository_path": repository_path,
            "codebase_characteristics": characteristics,
            "applicable_gates": applicable_gates,
            "summary": summary
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Gate applicability analysis failed: {str(e)}"
        } 
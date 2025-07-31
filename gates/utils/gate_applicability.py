"""
Gate Applicability Logic
Determines which gates are applicable based on codebase type and technology stack
"""

from typing import Dict, List, Any, Set
from .hard_gates import HARD_GATES


class GateApplicabilityAnalyzer:
    """Analyzes codebase to determine which gates are applicable"""
    
    def __init__(self):
        # Define technology categories
        self.frontend_technologies = {
            "JavaScript", "TypeScript", "HTML", "CSS", "SCSS", "SASS", 
            "React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt.js"
        }
        
        self.backend_technologies = {
            "Java", "Python", "C#", "C++", "C", "Go", "Rust", "Kotlin", 
            "Scala", "PHP", "Ruby", "Node.js", "Spring", "Django", "Flask"
        }
        
        self.mobile_technologies = {
            "Swift", "Kotlin", "React Native", "Flutter", "Xamarin"
        }
        
        self.api_technologies = {
            "REST", "GraphQL", "gRPC", "SOAP", "OpenAPI", "Swagger"
        }
        
        # Define gate applicability rules
        self.gate_applicability_rules = {
            "UI_ERRORS": {
                "required_technologies": ["frontend"],
                "excluded_technologies": [],
                "description": "Only applicable for frontend/client-side applications"
            },
            "UI_ERROR_TOOLS": {
                "required_technologies": ["frontend"],
                "excluded_technologies": [],
                "description": "Only applicable for frontend applications with client-side error tracking"
            },
            "HTTP_CODES": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services that return HTTP responses"
            },
            "LOG_API_CALLS": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services that handle API calls"
            },
            "STRUCTURED_LOGS": {
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Applicable for all codebases with logging requirements"
            },
            "ERROR_LOGS": {
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Applicable for all codebases with error handling"
            },
            "CORRELATION_ID": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services that handle requests"
            },
            "LOG_APPLICATION_MESSAGES": {
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Applicable for all codebases with application logging"
            },
            "CIRCUIT_BREAKERS": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services with external dependencies"
            },
            "TIMEOUTS": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services with I/O operations"
            },
            "RETRY_LOGIC": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services with external calls"
            },
            "THROTTLING": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services with rate limiting needs"
            },
            "AUTOMATED_TESTS": {
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Applicable for all codebases"
            },
            "API_LOGS": {
                "required_technologies": ["api"],
                "excluded_technologies": [],
                "description": "Applicable for API/backend services"
            },
            "BACKGROUND_JOBS": {
                "required_technologies": ["backend"],
                "excluded_technologies": [],
                "description": "Applicable for backend services with async processing"
            },
            "AVOID_LOGGING_SECRETS": {
                "required_technologies": [],
                "excluded_technologies": [],
                "description": "Applicable for all codebases (security requirement)"
            }
        }
    
    def analyze_codebase_type(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze codebase to determine its type and characteristics"""
        language_stats = metadata.get("language_stats", {})
        
        # Collect all languages and their file counts
        all_languages = set()
        language_counts = {}
        
        for lang, stats in language_stats.items():
            file_count = stats.get("files", 0)
            if file_count > 0:
                all_languages.add(lang)
                language_counts[lang] = file_count
        
        # Determine codebase characteristics
        characteristics = {
            "languages": list(all_languages),
            "language_counts": language_counts,
            "is_frontend": self._has_frontend_technologies(all_languages, language_counts),
            "is_backend": self._has_backend_technologies(all_languages),
            "is_api": self._has_api_characteristics(metadata),
            "is_mobile": self._has_mobile_technologies(all_languages),
            "is_backend_only": self._is_backend_only(all_languages, language_counts),
            "is_frontend_only": self._is_frontend_only(all_languages, language_counts),
            "is_fullstack": self._is_fullstack(all_languages, language_counts),
            "primary_technology": self._get_primary_technology(all_languages, language_counts)
        }
        
        return characteristics
    
    def _has_frontend_technologies(self, languages: Set[str], language_counts: Dict[str, int] = None) -> bool:
        """Check if codebase has frontend technologies with proportion consideration"""
        frontend_langs = languages & self.frontend_technologies
        
        if not frontend_langs:
            return False
        
        # If we have language counts, check the proportion
        if language_counts:
            total_files = sum(language_counts.values())
            frontend_files = sum(language_counts.get(lang, 0) for lang in frontend_langs)
            
            # Consider it frontend only if frontend files are more than 10% of total
            # This prevents documentation HTML from being considered frontend
            # Also check if there are actual frontend frameworks present
            has_frontend_frameworks = any(lang in ['JavaScript', 'TypeScript', 'React', 'Vue', 'Angular', 'Svelte'] 
                                        for lang in frontend_langs)
            
            if frontend_files > 0 and (frontend_files / total_files) > 0.10 and has_frontend_frameworks:
                return True
            else:
                return False
        
        # Fallback to simple presence check if no counts available
        return bool(frontend_langs)
    
    def _has_backend_technologies(self, languages: Set[str]) -> bool:
        """Check if codebase has backend technologies"""
        return bool(languages & self.backend_technologies)
    
    def _has_mobile_technologies(self, languages: Set[str]) -> bool:
        """Check if codebase has mobile technologies"""
        return bool(languages & self.mobile_technologies)
    
    def _has_api_characteristics(self, metadata: Dict[str, Any]) -> bool:
        """Check if codebase has API characteristics"""
        # Check for API-related files or patterns
        config_files = metadata.get("config", {}).get("config_files", {})
        
        # Look for API-related configuration files
        api_indicators = [
            "swagger", "openapi", "api", "rest", "graphql", 
            "controller", "endpoint", "route"
        ]
        
        for file_type, files in config_files.items():
            for file in files:
                file_lower = file.lower()
                if any(indicator in file_lower for indicator in api_indicators):
                    return True
        
        # Check if backend technologies are present (likely to have APIs)
        language_stats = metadata.get("language_stats", {})
        backend_langs = set(language_stats.keys()) & self.backend_technologies
        return len(backend_langs) > 0
    
    def _is_backend_only(self, languages: Set[str], language_counts: Dict[str, int] = None) -> bool:
        """Check if codebase is backend-only (no frontend)"""
        return (self._has_backend_technologies(languages) and 
                not self._has_frontend_technologies(languages, language_counts))
    
    def _is_frontend_only(self, languages: Set[str], language_counts: Dict[str, int] = None) -> bool:
        """Check if codebase is frontend-only (no backend)"""
        return (self._has_frontend_technologies(languages, language_counts) and 
                not self._has_backend_technologies(languages))
    
    def _is_fullstack(self, languages: Set[str], language_counts: Dict[str, int] = None) -> bool:
        """Check if codebase is fullstack (both frontend and backend)"""
        return (self._has_frontend_technologies(languages, language_counts) and 
                self._has_backend_technologies(languages))
    
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
    
    def determine_applicable_gates(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine which gates are applicable for the given codebase"""
        characteristics = self.analyze_codebase_type(metadata)
        applicable_gates = []
        
        for gate in HARD_GATES:
            gate_name = gate["name"]
            applicability = self._check_gate_applicability(gate_name, characteristics)
            
            if applicability["is_applicable"]:
                applicable_gates.append({
                    **gate,
                    "applicability_reason": applicability["reason"],
                    "codebase_characteristics": characteristics
                })
        
        return applicable_gates
    
    def _check_gate_applicability(self, gate_name: str, characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a specific gate is applicable based on codebase characteristics"""
        
        # Default: all gates are applicable unless specified otherwise
        if gate_name not in self.gate_applicability_rules:
            return {
                "is_applicable": True,
                "reason": "Applicable to all codebases"
            }
        
        rule = self.gate_applicability_rules[gate_name]
        
        # Check required technologies
        required_techs = rule.get("required_technologies", [])
        excluded_techs = rule.get("excluded_technologies", [])
        
        # Check if codebase has required characteristics
        has_required = True
        if required_techs:
            has_required = any(
                characteristics.get(f"is_{tech}", False) 
                for tech in required_techs
            )
        
        # Check if codebase is excluded
        is_excluded = False
        if excluded_techs:
            is_excluded = any(
                characteristics.get(f"is_{tech}", False) 
                for tech in excluded_techs
            )
        
        is_applicable = has_required and not is_excluded
        
        return {
            "is_applicable": is_applicable,
            "reason": rule.get("description", "Custom applicability rule"),
            "required_technologies": required_techs,
            "excluded_technologies": excluded_techs,
            "has_required": has_required,
            "is_excluded": is_excluded
        }
    
    def get_applicability_summary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of gate applicability analysis"""
        characteristics = self.analyze_codebase_type(metadata)
        applicable_gates = self.determine_applicable_gates(metadata)
        
        # Categorize gates by applicability
        applicable_by_category = {}
        non_applicable_gates = []
        
        for gate in HARD_GATES:
            gate_name = gate["name"]
            applicability = self._check_gate_applicability(gate_name, characteristics)
            
            if applicability["is_applicable"]:
                category = gate["category"]
                if category not in applicable_by_category:
                    applicable_by_category[category] = []
                applicable_by_category[category].append(gate_name)
            else:
                non_applicable_gates.append({
                    "name": gate_name,
                    "display_name": gate["display_name"],
                    "category": gate["category"],
                    "reason": applicability["reason"]
                })
        
        return {
            "codebase_characteristics": characteristics,
            "total_gates": len(HARD_GATES),
            "applicable_gates": len(applicable_gates),
            "non_applicable_gates": len(non_applicable_gates),
            "applicable_by_category": applicable_by_category,
            "non_applicable_details": non_applicable_gates,
            "applicable_gate_names": [gate["name"] for gate in applicable_gates]
        }


# Global instance for easy access
gate_applicability_analyzer = GateApplicabilityAnalyzer() 
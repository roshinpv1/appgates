"""
Intelligent Expected Count Calculator

This module provides sophisticated expected count calculations based on:
1. Actual codebase structure analysis
2. Framework-specific patterns
3. Project complexity assessment
4. Real-world implementation patterns for each gate
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List


class ExpectedCountCalculator:
    """Intelligent expected count calculator based on codebase analysis"""
    
    def __init__(self):
        self.gate_patterns = {
            # Auditability gates
            "1.1": {"name": "Log system errors", "category": "auditability", "type": "logging"},
            "1.3": {"name": "Use HTTP standard error codes", "category": "auditability", "type": "error_handling"},
            "1.5": {"name": "Timeouts", "category": "auditability", "type": "timeout"},
            "1.6": {"name": "Log API Calls", "category": "auditability", "type": "logging"},
            "1.8": {"name": "Log Application Messages", "category": "auditability", "type": "logging"},
            "1.10": {"name": "Avoid Logging Sensitive Data", "category": "auditability", "type": "security"},
            "2.7": {"name": "UI Error Handling", "category": "auditability", "type": "ui_error"},
            
            # Error Handling gates
            "2.4": {"name": "Include Client error tracking", "category": "error_handling", "type": "error_tracking"},
            
            # Availability gates
            "1.12": {"name": "Retry Logic", "category": "availability", "type": "retry"},
            "3.6": {"name": "Throttling, drop request", "category": "availability", "type": "throttling"},
            "3.9": {"name": "Set circuit breakers on outgoing requests", "category": "availability", "type": "circuit_breaker"},
            "3.18": {"name": "Auto Scale", "category": "availability", "type": "auto_scale"},
            
            # Testing gates
            "2": {"name": "Automated Regression Testing", "category": "testing", "type": "testing"},
        }
    
    def calculate_expected_count(self, gate_id: str, metadata: Dict[str, Any]) -> int:
        """Calculate intelligent expected count for a specific gate"""
        try:
            # Get metadata
            tech_stack = metadata.get("tech_stack", {})
            file_types = metadata.get("file_types", {})
            total_files = metadata.get("total_files", 0)
            main_repo = metadata.get("main_repo", {})
            repo_path = main_repo.get("local_path", "")
            
            # Analyze actual codebase structure
            codebase_structure = self._analyze_codebase_structure(repo_path, file_types)
            
            # Gate-specific expected count calculations
            expected_count = self._calculate_gate_specific_expected_count(
                gate_id, tech_stack, file_types, total_files, codebase_structure
            )
            
            print(f"   📊 Gate {gate_id} expected count: {expected_count} (structure: {codebase_structure.get('type', 'unknown')}, complexity: {codebase_structure.get('complexity', 'basic')})")
            
            return expected_count
            
        except Exception as e:
            print(f"⚠️ Error calculating expected count for gate {gate_id}: {e}")
            return 1  # Default fallback
    
    def _analyze_codebase_structure(self, repo_path: str, file_types: Dict[str, int]) -> Dict[str, Any]:
        """Analyze the actual codebase structure to determine project type and complexity"""
        try:
            structure = {
                "type": "unknown",
                "complexity": "basic",
                "layers": [],
                "frameworks": [],
                "components": {},
                "architecture": "monolithic"
            }
            
            if not repo_path or not os.path.exists(repo_path):
                return structure
            
            repo_path_obj = Path(repo_path)
            
            # Analyze directory structure
            java_files = file_types.get("java", 0)
            py_files = file_types.get("py", 0)
            js_files = file_types.get("js", 0) + file_types.get("ts", 0)
            
            # Check for Spring Boot structure
            if java_files > 0:
                if (repo_path_obj / "src" / "main" / "java").exists():
                    structure["type"] = "spring_boot"
                    structure["frameworks"].append("spring_boot")
                    
                    # Analyze Spring layers
                    java_src = repo_path_obj / "src" / "main" / "java"
                    if java_src.exists():
                        for package_dir in java_src.iterdir():
                            if package_dir.is_dir():
                                package_name = package_dir.name.lower()
                                if "controller" in package_name or "web" in package_name:
                                    structure["layers"].append("controller")
                                elif "service" in package_name or "business" in package_name:
                                    structure["layers"].append("service")
                                elif "repository" in package_name or "dao" in package_name or "data" in package_name:
                                    structure["layers"].append("repository")
                                elif "config" in package_name or "configuration" in package_name:
                                    structure["layers"].append("config")
                                elif "model" in package_name or "entity" in package_name or "dto" in package_name:
                                    structure["layers"].append("model")
                    
                    # Count components by layer
                    for layer in structure["layers"]:
                        layer_path = None
                        for package_dir in java_src.iterdir():
                            if package_dir.is_dir() and layer in package_dir.name.lower():
                                layer_path = package_dir
                                break
                        
                        if layer_path:
                            structure["components"][layer] = len([f for f in layer_path.rglob("*.java") if f.is_file()])
            
            # Check for Python web framework
            elif py_files > 0:
                if (repo_path_obj / "manage.py").exists():
                    structure["type"] = "django"
                    structure["frameworks"].append("django")
                elif any((repo_path_obj / f).exists() for f in ["app.py", "main.py", "application.py"]):
                    structure["type"] = "flask"
                    structure["frameworks"].append("flask")
                else:
                    structure["type"] = "python"
            
            # Check for Node.js/JavaScript framework
            elif js_files > 0:
                if (repo_path_obj / "package.json").exists():
                    structure["type"] = "nodejs"
                    structure["frameworks"].append("nodejs")
                    
                    # Check for specific frameworks
                    package_json = repo_path_obj / "package.json"
                    if package_json.exists():
                        try:
                            with open(package_json, 'r') as f:
                                pkg_data = json.load(f)
                                dependencies = pkg_data.get("dependencies", {})
                                
                                if "express" in dependencies:
                                    structure["frameworks"].append("express")
                                if "react" in dependencies:
                                    structure["frameworks"].append("react")
                                if "angular" in dependencies:
                                    structure["frameworks"].append("angular")
                                if "vue" in dependencies:
                                    structure["frameworks"].append("vue")
                        except:
                            pass
            
            # Determine complexity based on structure
            total_components = sum(structure["components"].values())
            if total_components > 20:
                structure["complexity"] = "complex"
            elif total_components > 10:
                structure["complexity"] = "medium"
            else:
                structure["complexity"] = "basic"
            
            return structure
            
        except Exception as e:
            print(f"⚠️ Error analyzing codebase structure: {e}")
            return {"type": "unknown", "complexity": "basic", "layers": [], "frameworks": [], "components": {}}
    
    def _calculate_gate_specific_expected_count(self, gate_id: str, tech_stack: Dict[str, int], 
                                              file_types: Dict[str, int], total_files: int, 
                                              codebase_structure: Dict[str, Any]) -> int:
        """Calculate expected count based on specific gate requirements and codebase structure"""
        
        gate_info = self.gate_patterns.get(gate_id, {})
        gate_type = gate_info.get("type", "unknown")
        
        # Gate-specific calculation logic
        if gate_type == "logging":
            return self._calculate_logging_expected_count(gate_id, codebase_structure, file_types)
        
        elif gate_type == "error_handling":
            return self._calculate_error_handling_expected_count(gate_id, codebase_structure, file_types)
        
        elif gate_type == "timeout":
            return self._calculate_timeout_expected_count(codebase_structure, file_types)
        
        elif gate_type == "security":
            return self._calculate_security_expected_count(gate_id, codebase_structure, file_types)
        
        elif gate_type == "ui_error":
            return self._calculate_ui_error_expected_count(codebase_structure, file_types)
        
        elif gate_type == "error_tracking":
            return self._calculate_error_tracking_expected_count(codebase_structure, file_types)
        
        elif gate_type == "retry":
            return self._calculate_retry_expected_count(codebase_structure, file_types)
        
        elif gate_type == "throttling":
            return self._calculate_throttling_expected_count(codebase_structure, file_types)
        
        elif gate_type == "circuit_breaker":
            return self._calculate_circuit_breaker_expected_count(codebase_structure, file_types)
        
        elif gate_type == "auto_scale":
            return self._calculate_auto_scale_expected_count(codebase_structure, file_types)
        
        elif gate_type == "testing":
            return self._calculate_testing_expected_count(codebase_structure, file_types)
        
        else:
            # Default calculation
            return self._calculate_default_expected_count(gate_id, codebase_structure, file_types)
    
    def _calculate_logging_expected_count(self, gate_id: str, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected logging implementations based on codebase structure"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Spring Boot typically has logging in multiple layers
            layers = codebase_structure.get("layers", [])
            if "controller" in layers:
                base_count += codebase_structure["components"].get("controller", 0) // 2  # Every 2 controllers
            if "service" in layers:
                base_count += codebase_structure["components"].get("service", 0) // 3  # Every 3 services
            if "repository" in layers:
                base_count += codebase_structure["components"].get("repository", 0) // 4  # Every 4 repositories
            
            # Add config-based logging
            if "config" in layers or file_types.get("properties", 0) > 0:
                base_count += 1
            
            # Gate-specific adjustments
            if gate_id == "1.1":  # System errors - more critical
                base_count = max(base_count, 2)
            elif gate_id == "1.6":  # API calls - typically in controllers
                if "controller" in layers:
                    base_count = codebase_structure["components"].get("controller", 0) // 2
                else:
                    base_count = max(1, file_types.get("java", 0) // 4)
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Python web apps typically have logging in views/controllers and services
            base_count = max(2, file_types.get("py", 0) // 5)  # Every 5 Python files
        
        elif codebase_structure["type"] == "nodejs":
            # Node.js apps typically have logging in routes and services
            base_count = max(2, file_types.get("js", 0) // 4)  # Every 4 JS files
        
        return max(1, min(base_count, 5))  # Cap between 1-5
    
    def _calculate_error_handling_expected_count(self, gate_id: str, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected error handling implementations"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Spring Boot has controllers and global exception handlers
            if "controller" in codebase_structure.get("layers", []):
                base_count += codebase_structure["components"].get("controller", 0) // 3
            # Global exception handler
            base_count += 1
            
            # Gate-specific adjustments
            if gate_id == "1.3":  # HTTP error codes - typically in controllers
                if "controller" in codebase_structure.get("layers", []):
                    base_count = codebase_structure["components"].get("controller", 0) // 2
                else:
                    base_count = max(1, file_types.get("java", 0) // 4)
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Python web apps have error handlers and views
            base_count = max(2, file_types.get("py", 0) // 4)
        
        elif codebase_structure["type"] == "nodejs":
            # Node.js apps have error middleware and route handlers
            base_count = max(2, file_types.get("js", 0) // 3)
        
        return max(1, min(base_count, 4))
    
    def _calculate_timeout_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected timeout implementations"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Spring Boot has timeout configs in properties and service calls
            if file_types.get("properties", 0) > 0:
                base_count += 1
            if "service" in codebase_structure.get("layers", []):
                base_count += codebase_structure["components"].get("service", 0) // 5
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Python apps have timeout configs and async operations
            base_count = max(1, file_types.get("py", 0) // 6)
        
        elif codebase_structure["type"] == "nodejs":
            # Node.js apps have timeout configs and HTTP client timeouts
            base_count = max(1, file_types.get("js", 0) // 5)
        
        return max(1, min(base_count, 3))
    
    def _calculate_security_expected_count(self, gate_id: str, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected security implementations"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Spring Security configurations
            if "config" in codebase_structure.get("layers", []):
                base_count += 1
            if "controller" in codebase_structure.get("layers", []):
                base_count += codebase_structure["components"].get("controller", 0) // 4
            
            # Gate-specific adjustments
            if gate_id == "1.10":  # Sensitive data logging - typically in services
                if "service" in codebase_structure.get("layers", []):
                    base_count = codebase_structure["components"].get("service", 0) // 3
                else:
                    base_count = max(1, file_types.get("java", 0) // 5)
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Python security middleware and decorators
            base_count = max(1, file_types.get("py", 0) // 6)
        
        elif codebase_structure["type"] == "nodejs":
            # Node.js security middleware
            base_count = max(1, file_types.get("js", 0) // 5)
        
        return max(1, min(base_count, 3))
    
    def _calculate_ui_error_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected UI error handling implementations"""
        base_count = 1
        
        # Check for frontend files
        frontend_files = file_types.get("html", 0) + file_types.get("css", 0) + file_types.get("js", 0)
        
        if frontend_files > 0:
            base_count = max(1, frontend_files // 10)
        
        # Check for specific frameworks
        if "react" in codebase_structure.get("frameworks", []):
            base_count += 1
        if "angular" in codebase_structure.get("frameworks", []):
            base_count += 1
        if "vue" in codebase_structure.get("frameworks", []):
            base_count += 1
        
        return max(1, min(base_count, 3))
    
    def _calculate_error_tracking_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected error tracking implementations"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Global exception handlers and logging
            if "controller" in codebase_structure.get("layers", []):
                base_count += 1
            if "config" in codebase_structure.get("layers", []):
                base_count += 1
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Error handlers and logging
            base_count = max(1, file_types.get("py", 0) // 5)
        
        elif codebase_structure["type"] == "nodejs":
            # Error middleware and logging
            base_count = max(1, file_types.get("js", 0) // 4)
        
        return max(1, min(base_count, 3))
    
    def _calculate_retry_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected retry logic implementations"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Retry in services and external calls
            if "service" in codebase_structure.get("layers", []):
                base_count += codebase_structure["components"].get("service", 0) // 4
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Retry in services and external calls
            base_count = max(1, file_types.get("py", 0) // 6)
        
        elif codebase_structure["type"] == "nodejs":
            # Retry in services and external calls
            base_count = max(1, file_types.get("js", 0) // 5)
        
        return max(1, min(base_count, 3))
    
    def _calculate_throttling_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected throttling implementations"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Rate limiting in controllers and config
            if "controller" in codebase_structure.get("layers", []):
                base_count += 1
            if "config" in codebase_structure.get("layers", []):
                base_count += 1
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Rate limiting middleware
            base_count = max(1, file_types.get("py", 0) // 8)
        
        elif codebase_structure["type"] == "nodejs":
            # Rate limiting middleware
            base_count = max(1, file_types.get("js", 0) // 6)
        
        return max(1, min(base_count, 2))
    
    def _calculate_circuit_breaker_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected circuit breaker implementations"""
        base_count = 1
        
        if codebase_structure["type"] == "spring_boot":
            # Circuit breakers in services and external calls
            if "service" in codebase_structure.get("layers", []):
                base_count += codebase_structure["components"].get("service", 0) // 5
        
        elif codebase_structure["type"] in ["django", "flask"]:
            # Circuit breakers in services
            base_count = max(1, file_types.get("py", 0) // 8)
        
        elif codebase_structure["type"] == "nodejs":
            # Circuit breakers in services
            base_count = max(1, file_types.get("js", 0) // 7)
        
        return max(1, min(base_count, 2))
    
    def _calculate_auto_scale_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected auto-scaling implementations"""
        base_count = 1
        
        # Check for deployment configs
        deployment_files = file_types.get("yml", 0) + file_types.get("yaml", 0) + file_types.get("dockerfile", 0)
        
        if deployment_files > 0:
            base_count += 1
        
        # Check for cloud-specific configs
        if any(f in str(file_types.keys()) for f in ["kubernetes", "helm", "docker"]):
            base_count += 1
        
        return max(1, min(base_count, 2))
    
    def _calculate_testing_expected_count(self, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate expected testing implementations"""
        base_count = 1
        
        # Check for existing test files
        test_files = sum([
            file_types.get("test", 0),
            file_types.get("spec", 0),
            file_types.get("specs", 0)
        ])
        
        if test_files > 0:
            base_count = test_files // 2  # Every 2 test files
        else:
            # Estimate based on main code files
            main_files = file_types.get("java", 0) + file_types.get("py", 0) + file_types.get("js", 0)
            base_count = max(1, main_files // 4)  # Every 4 main files
        
        return max(1, min(base_count, 5))
    
    def _calculate_default_expected_count(self, gate_id: str, codebase_structure: Dict[str, Any], file_types: Dict[str, int]) -> int:
        """Calculate default expected count for unknown gates"""
        base_count = 1
        
        # Adjust based on codebase complexity
        if codebase_structure["complexity"] == "complex":
            base_count = 3
        elif codebase_structure["complexity"] == "medium":
            base_count = 2
        
        # Adjust based on file count
        total_files = sum(file_types.values())
        if total_files > 50:
            base_count += 1
        elif total_files < 10:
            base_count = max(1, base_count - 1)
        
        return base_count

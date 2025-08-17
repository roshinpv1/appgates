# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Repository Analysis Tool - Analyzes repository structure and identifies technologies"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional
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

# Import existing CodeGates functionality
try:
    from gates.utils.hard_gates import HARD_GATES, get_gate_number, GATE_NUMBER_MAPPING
    from gates.utils.file_scanner import scan_directory
    CODEGATES_AVAILABLE = True
except ImportError as e:
    CODEGATES_AVAILABLE = False
    print(f"⚠️ CodeGates functionality not available: {e}")

from agent.hardgate_agent.util.codegates_bridge import ensure_local_repo as _bridge_ensure_local_repo


class RepositoryAnalysisTool(BaseTool):
    """Tool for comprehensive repository analysis and technology identification"""
    
    name = "analyze_repository"
    description = "Analyze repository structure, identify technologies, and determine applicable hard gates for security analysis"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Analyze repository structure and identify technologies"""
        try:
            repository_url = args.get("repository_url")
            branch = args.get("branch", "main")
            github_token = args.get("github_token")
            repository_path = args.get("repository_path")
            
            if not repository_path and not repository_url:
                return {
                    "success": False,
                    "error": "Either repository_path or repository_url is required"
                }
            
            # Resolve local path using the shared bridge (aligns with gates utils)
            local_path, temp_dir, created_temp = _bridge_ensure_local_repo(
                repository_path=repository_path,
                repository_url=repository_url,
                branch=branch,
                github_token=github_token
            )
            
            # Perform comprehensive analysis
            analysis = await self._perform_comprehensive_analysis(local_path)
            
            return {
                "success": True,
                "repository_url": repository_url,
                "repository_path": local_path,
                "branch": branch,
                "analysis": analysis,
                "temporary": created_temp,
                "temp_dir": temp_dir,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Repository analysis failed: {str(e)}"
            }
    
    async def _clone_repository(self, repository_url: str, branch: str, github_token: Optional[str]) -> str:
        """Clone repository from URL"""
        # This is a simplified version - in practice, you'd use git operations
        import tempfile
        import subprocess
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="hardgate_analysis_")
        
        # Clone command
        clone_cmd = ["git", "clone", "-b", branch, repository_url, temp_dir]
        
        # Add authentication if token provided
        if github_token and "github.com" in repository_url:
            auth_url = repository_url.replace("https://", f"https://{github_token}@")
            clone_cmd = ["git", "clone", "-b", branch, auth_url, temp_dir]
        
        try:
            result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            return temp_dir
        except Exception as e:
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    async def _perform_comprehensive_analysis(self, repository_path: str) -> Dict[str, Any]:
        """Perform comprehensive repository analysis"""
        analysis = {
            "repository_path": repository_path,
            "structure": await self._analyze_structure(repository_path),
            "technologies": await self._identify_technologies(repository_path),
            "security_analysis": await self._analyze_security_posture(repository_path),
            "applicable_gates": await self._determine_applicable_gates(repository_path),
            "code_metrics": await self._calculate_code_metrics(repository_path),
            "dependencies": await self._analyze_dependencies(repository_path),
            "configuration": await self._analyze_configuration(repository_path)
        }
        
        return analysis
    
    async def _analyze_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository structure"""
        structure = {
            "total_files": 0,
            "directories": [],
            "file_types": {},
            "main_components": [],
            "architecture_patterns": []
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv']]
                
                # Count files by extension
                for file in files:
                    structure["total_files"] += 1
                    ext = os.path.splitext(file)[1].lower()
                    structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Identify main directories
                if root == repo_path:
                    structure["directories"] = dirs
            
            # Identify architecture patterns
            structure["architecture_patterns"] = self._identify_architecture_patterns(repo_path)
            
            # Identify main components
            structure["main_components"] = self._identify_main_components(repo_path)
            
        except Exception as e:
            print(f"Error analyzing structure: {str(e)}")
        
        return structure
    
    async def _identify_technologies(self, repo_path: str) -> Dict[str, Any]:
        """Identify technologies used in the repository"""
        technologies = {
            "programming_languages": [],
            "frameworks": [],
            "databases": [],
            "cloud_services": [],
            "security_tools": [],
            "monitoring_tools": [],
            "build_tools": [],
            "testing_frameworks": []
        }
        
        try:
            # Analyze file extensions for programming languages
            file_extensions = self._get_file_extensions(repo_path)
            
            # Map extensions to languages
            language_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".java": "Java",
                ".cs": "C#",
                ".php": "PHP",
                ".rb": "Ruby",
                ".go": "Go",
                ".rs": "Rust",
                ".cpp": "C++",
                ".c": "C",
                ".swift": "Swift",
                ".kt": "Kotlin",
                ".scala": "Scala"
            }
            
            for ext in file_extensions:
                if ext in language_map:
                    technologies["programming_languages"].append(language_map[ext])
            
            # Identify frameworks and tools
            technologies.update(await self._identify_frameworks_and_tools(repo_path))
            
        except Exception as e:
            print(f"Error identifying technologies: {str(e)}")
        
        return technologies
    
    async def _identify_frameworks_and_tools(self, repo_path: str) -> Dict[str, List[str]]:
        """Identify frameworks and tools used in the repository"""
        frameworks_and_tools = {
            "frameworks": [],
            "databases": [],
            "cloud_services": [],
            "security_tools": [],
            "monitoring_tools": [],
            "build_tools": [],
            "testing_frameworks": []
        }
        
        # Common patterns for technology identification
        patterns = {
            "frameworks": {
                "python": ["django", "flask", "fastapi", "tornado", "bottle"],
                "javascript": ["react", "vue", "angular", "express", "next", "nuxt"],
                "java": ["spring", "hibernate", "struts", "play", "quarkus"],
                "csharp": ["asp.net", "entity framework", "xamarin", "blazor"],
                "php": ["laravel", "symfony", "codeigniter", "yii", "zend"],
                "ruby": ["rails", "sinatra", "hanami", "grape"],
                "go": ["gin", "echo", "fiber", "gorilla", "chi"]
            },
            "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb"],
            "cloud_services": ["aws", "azure", "gcp", "heroku", "digitalocean", "kubernetes", "docker"],
            "security_tools": ["jwt", "oauth", "oauth2", "saml", "ldap", "kerberos", "bcrypt", "argon2"],
            "monitoring_tools": ["splunk", "appdynamics", "thousandeyes", "datadog", "newrelic", "prometheus", "grafana"],
            "build_tools": ["maven", "gradle", "npm", "yarn", "pip", "cargo", "go.mod"],
            "testing_frameworks": ["junit", "pytest", "jest", "mocha", "rspec", "phpunit", "go test"]
        }
        
        try:
            # Scan for technology patterns
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.lower() in ["requirements.txt", "package.json", "pom.xml", "build.gradle", "cargo.toml", "go.mod"]:
                        file_path = os.path.join(root, file)
                        await self._analyze_dependency_file(file_path, frameworks_and_tools, patterns)
        
        except Exception as e:
            print(f"Error identifying frameworks and tools: {str(e)}")
        
        return frameworks_and_tools
    
    async def _analyze_dependency_file(self, file_path: str, frameworks_and_tools: Dict[str, List[str]], patterns: Dict[str, Any]):
        """Analyze dependency files for technology identification"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            # Check for frameworks
            for language, frameworks in patterns["frameworks"].items():
                for framework in frameworks:
                    if framework in content:
                        frameworks_and_tools["frameworks"].append(framework.title())
            
            # Check for other technologies
            for category, tech_list in patterns.items():
                if category != "frameworks":
                    for tech in tech_list:
                        if tech in content:
                            frameworks_and_tools[category].append(tech.title())
        
        except Exception as e:
            print(f"Error analyzing dependency file {file_path}: {str(e)}")
    
    async def _analyze_security_posture(self, repo_path: str) -> Dict[str, Any]:
        """Analyze security posture of the repository"""
        security_analysis = {
            "authentication_implemented": False,
            "authorization_implemented": False,
            "input_validation": "Unknown",
            "encryption_used": False,
            "logging_implemented": False,
            "monitoring_configured": False,
            "security_headers": False,
            "ssl_tls_configured": False,
            "secret_management": False,
            "vulnerability_scanning": False
        }
        
        try:
            # Scan for security patterns
            security_patterns = {
                "authentication": ["jwt", "oauth", "saml", "login", "auth", "authentication"],
                "authorization": ["authorization", "permission", "role", "access control"],
                "input_validation": ["validation", "sanitize", "escape", "input check"],
                "encryption": ["encrypt", "hash", "bcrypt", "argon2", "aes", "rsa"],
                "logging": ["logger", "logging", "log4j", "winston", "pino"],
                "monitoring": ["monitoring", "alerting", "splunk", "appdynamics", "thousandeyes"],
                "security_headers": ["security headers", "csp", "hsts", "x-frame-options"],
                "ssl_tls": ["ssl", "tls", "https", "certificate"],
                "secret_management": ["vault", "secrets", "environment variables", "config"],
                "vulnerability_scanning": ["snyk", "owasp", "vulnerability", "security scan"]
            }
            
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if any(file.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".yaml", ".yml", ".json"]):
                        file_path = os.path.join(root, file)
                        await self._check_security_patterns(file_path, security_patterns, security_analysis)
        
        except Exception as e:
            print(f"Error analyzing security posture: {str(e)}")
        
        return security_analysis
    
    async def _check_security_patterns(self, file_path: str, security_patterns: Dict[str, List[str]], security_analysis: Dict[str, Any]):
        """Check for security patterns in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            for category, patterns in security_patterns.items():
                for pattern in patterns:
                    if pattern in content:
                        if category == "authentication":
                            security_analysis["authentication_implemented"] = True
                        elif category == "authorization":
                            security_analysis["authorization_implemented"] = True
                        elif category == "input_validation":
                            security_analysis["input_validation"] = "Partial"
                        elif category == "encryption":
                            security_analysis["encryption_used"] = True
                        elif category == "logging":
                            security_analysis["logging_implemented"] = True
                        elif category == "monitoring":
                            security_analysis["monitoring_configured"] = True
                        elif category == "security_headers":
                            security_analysis["security_headers"] = True
                        elif category == "ssl_tls":
                            security_analysis["ssl_tls_configured"] = True
                        elif category == "secret_management":
                            security_analysis["secret_management"] = True
                        elif category == "vulnerability_scanning":
                            security_analysis["vulnerability_scanning"] = True
        
        except Exception as e:
            print(f"Error checking security patterns in {file_path}: {str(e)}")
    
    async def _determine_applicable_gates(self, repo_path: str) -> List[str]:
        """Determine which hard gates are applicable to this repository"""
        applicable_gates = []
        
        if CODEGATES_AVAILABLE:
            # Use the actual hard gates from the main application
            applicable_gates = list(GATE_NUMBER_MAPPING.keys())
        else:
            # Fallback to default gates
            applicable_gates = [
                "ALERTING_ACTIONABLE",
                "STRUCTURED_LOGS", 
                "AVOID_LOGGING_SECRETS",
                "AUDIT_TRAIL",
                "CORRELATION_ID",
                "LOG_API_CALLS",
                "CLIENT_UI_ERRORS",
                "RETRY_LOGIC",
                "TIMEOUT_IO",
                "THROTTLING",
                "CIRCUIT_BREAKERS",
                "HTTP_ERROR_CODES",
                "URL_MONITORING",
                "AUTOMATED_TESTS",
                "AUTO_SCALE"
            ]
        
        return applicable_gates
    
    async def _calculate_code_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Calculate code metrics"""
        metrics = {
            "total_lines": 0,
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "complexity": "Low",
            "maintainability": "Good"
        }
        
        try:
            code_extensions = [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".rs", ".cpp", ".c"]
            
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if any(file.endswith(ext) for ext in code_extensions):
                        file_path = os.path.join(root, file)
                        await self._analyze_file_metrics(file_path, metrics)
        
        except Exception as e:
            print(f"Error calculating code metrics: {str(e)}")
        
        return metrics
    
    async def _analyze_file_metrics(self, file_path: str, metrics: Dict[str, Any]):
        """Analyze metrics for a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            metrics["total_lines"] += len(lines)
            
            for line in lines:
                stripped = line.strip()
                if stripped == "":
                    metrics["blank_lines"] += 1
                elif stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                    metrics["comment_lines"] += 1
                else:
                    metrics["code_lines"] += 1
        
        except Exception as e:
            print(f"Error analyzing file metrics for {file_path}: {str(e)}")
    
    async def _analyze_dependencies(self, repo_path: str) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {
            "python": [],
            "javascript": [],
            "java": [],
            "other": []
        }
        
        try:
            # Look for dependency files
            dependency_files = {
                "requirements.txt": "python",
                "package.json": "javascript",
                "pom.xml": "java",
                "build.gradle": "java",
                "cargo.toml": "other",
                "go.mod": "other"
            }
            
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file in dependency_files:
                        file_path = os.path.join(root, file)
                        category = dependency_files[file]
                        dependencies[category].append(file_path)
        
        except Exception as e:
            print(f"Error analyzing dependencies: {str(e)}")
        
        return dependencies
    
    async def _analyze_configuration(self, repo_path: str) -> Dict[str, Any]:
        """Analyze configuration files"""
        configuration = {
            "environment_files": [],
            "config_files": [],
            "deployment_files": [],
            "monitoring_config": []
        }
        
        try:
            config_patterns = {
                "environment_files": [".env", ".env.local", ".env.production", ".env.development"],
                "config_files": ["config.json", "config.yaml", "config.yml", "settings.py", "application.properties"],
                "deployment_files": ["dockerfile", "docker-compose.yml", "kubernetes.yaml", "helm", "terraform"],
                "monitoring_config": ["prometheus.yml", "grafana", "datadog", "newrelic"]
            }
            
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    file_lower = file.lower()
                    for category, patterns in config_patterns.items():
                        if any(pattern in file_lower for pattern in patterns):
                            configuration[category].append(os.path.join(root, file))
        
        except Exception as e:
            print(f"Error analyzing configuration: {str(e)}")
        
        return configuration
    
    def _get_file_extensions(self, repo_path: str) -> List[str]:
        """Get all file extensions in the repository"""
        extensions = set()
        
        try:
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        extensions.add(ext)
        except Exception as e:
            print(f"Error getting file extensions: {str(e)}")
        
        return list(extensions)
    
    def _identify_architecture_patterns(self, repo_path: str) -> List[str]:
        """Identify architecture patterns in the repository"""
        patterns = []
        
        try:
            # Check for common architecture patterns
            if os.path.exists(os.path.join(repo_path, "src")):
                patterns.append("Layered Architecture")
            
            if os.path.exists(os.path.join(repo_path, "api")) or os.path.exists(os.path.join(repo_path, "controllers")):
                patterns.append("MVC Pattern")
            
            if os.path.exists(os.path.join(repo_path, "services")):
                patterns.append("Service Layer Pattern")
            
            if os.path.exists(os.path.join(repo_path, "microservices")) or os.path.exists(os.path.join(repo_path, "services")):
                patterns.append("Microservices")
            
            if os.path.exists(os.path.join(repo_path, "components")):
                patterns.append("Component-Based Architecture")
        
        except Exception as e:
            print(f"Error identifying architecture patterns: {str(e)}")
        
        return patterns
    
    def _identify_main_components(self, repo_path: str) -> List[str]:
        """Identify main components in the repository"""
        components = []
        
        try:
            # Look for common component directories
            component_dirs = ["api", "controllers", "models", "services", "utils", "helpers", "middleware", "routes"]
            
            for component in component_dirs:
                if os.path.exists(os.path.join(repo_path, component)):
                    components.append(f"{component.title()} Layer")
            
            # Look for specific technology components
            if os.path.exists(os.path.join(repo_path, "frontend")) or os.path.exists(os.path.join(repo_path, "client")):
                components.append("Frontend Application")
            
            if os.path.exists(os.path.join(repo_path, "backend")) or os.path.exists(os.path.join(repo_path, "server")):
                components.append("Backend Application")
            
            if os.path.exists(os.path.join(repo_path, "database")) or os.path.exists(os.path.join(repo_path, "db")):
                components.append("Database Layer")
        
        except Exception as e:
            print(f"Error identifying main components: {str(e)}")
        
        return components


# Create tool instance
repository_analysis_tool = RepositoryAnalysisTool()


# Create wrapper functions for Google ADK compatibility
def analyze_repository(repository_url: Optional[str] = None, branch: str = "main", github_token: Optional[str] = None, repository_path: Optional[str] = None, tool_context = None) -> Dict[str, Any]:
    """
    Analyze repository structure and identify technologies for security analysis.
    
    Args:
        repository_url: URL of the repository to analyze
        branch: Branch to analyze
        github_token: GitHub token for private repositories
        repository_path: Local path to repository
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing repository analysis results
    """
    try:
        if not repository_path and not repository_url:
            return {
                "success": False,
                "error": "Either repository_path or repository_url is required"
            }
        
        # If repository_path is provided, use it directly
        if repository_path:
            local_path = repository_path
        else:
            # Clone repository if URL is provided
            local_path = _clone_repository(repository_url, branch, github_token)
        
        # Perform comprehensive analysis using actual hard gates logic
        analysis = _perform_comprehensive_analysis(local_path)
        
        return {
            "success": True,
            "repository_url": repository_url,
            "repository_path": local_path,
            "branch": branch,
            "analysis": analysis
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Repository analysis failed: {str(e)}"
        }


def _clone_repository(repository_url: str, branch: str, github_token: Optional[str]) -> str:
    """Clone repository from URL"""
    import tempfile
    import subprocess
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="hardgate_analysis_")
    
    # Clone command
    clone_cmd = ["git", "clone", "-b", branch, repository_url, temp_dir]
    
    # Add authentication if token provided
    if github_token and "github.com" in repository_url:
        auth_url = repository_url.replace("https://", f"https://{github_token}@")
        clone_cmd = ["git", "clone", "-b", branch, auth_url, temp_dir]
    
    try:
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")
        
        return temp_dir
    except Exception as e:
        raise Exception(f"Failed to clone repository: {str(e)}")


def _perform_comprehensive_analysis(repository_path: str) -> Dict[str, Any]:
    """Perform comprehensive repository analysis using actual hard gates logic"""
    analysis = {
        "repository_path": repository_path,
        "structure": _analyze_structure(repository_path),
        "technologies": _identify_technologies(repository_path),
        "security_analysis": _analyze_security_posture(repository_path),
        "applicable_gates": _determine_applicable_gates(repository_path),
        "code_metrics": _calculate_code_metrics(repository_path),
        "dependencies": _analyze_dependencies(repository_path),
        "configuration": _analyze_configuration(repository_path)
    }
    
    return analysis


def _analyze_structure(repo_path: str) -> Dict[str, Any]:
    """Analyze repository structure using actual file scanner"""
    try:
        # Use the actual file scanner from the main application
        if CODEGATES_AVAILABLE:
            from gates.utils.file_scanner import scan_directory
            scan_result = scan_directory(repo_path)
            
            structure = {
                "total_files": scan_result.get("total_files", 0),
                "directories": scan_result.get("directories", []),
                "file_types": scan_result.get("file_types", {}),
                "main_components": _identify_main_components(repo_path),
                "architecture_patterns": _identify_architecture_patterns(repo_path),
                "languages": scan_result.get("languages", {}),
                "total_lines": scan_result.get("total_lines", 0),
                "total_size": scan_result.get("total_size", 0)
            }
        else:
            # Fallback to basic analysis
            structure = {
                "total_files": 0,
                "directories": [],
                "file_types": {},
                "main_components": [],
                "architecture_patterns": []
            }
            
            for root, dirs, files in os.walk(repo_path):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv']]
                
                # Count files by extension
                for file in files:
                    structure["total_files"] += 1
                    ext = os.path.splitext(file)[1].lower()
                    structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Identify main directories
                if root == repo_path:
                    structure["directories"] = dirs
            
            # Identify architecture patterns
            structure["architecture_patterns"] = _identify_architecture_patterns(repo_path)
            structure["main_components"] = _identify_main_components(repo_path)
        
        return structure
        
    except Exception as e:
        print(f"Error analyzing structure: {str(e)}")
        return {
            "total_files": 0,
            "directories": [],
            "file_types": {},
            "main_components": [],
            "architecture_patterns": []
        }


def _identify_technologies(repo_path: str) -> Dict[str, Any]:
    """Identify technologies used in the repository"""
    technologies = {
        "programming_languages": [],
        "frameworks": [],
        "databases": [],
        "cloud_services": [],
        "security_tools": [],
        "monitoring_tools": [],
        "build_tools": [],
        "testing_frameworks": []
    }
    
    try:
        # Analyze file extensions for programming languages
        file_extensions = _get_file_extensions(repo_path)
        
        # Map extensions to languages
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".cs": "C#",
            ".php": "PHP",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala"
        }
        
        for ext in file_extensions:
            if ext in language_map:
                technologies["programming_languages"].append(language_map[ext])
        
        # Identify frameworks and tools
        technologies.update(_identify_frameworks_and_tools(repo_path))
        
    except Exception as e:
        print(f"Error identifying technologies: {str(e)}")
    
    return technologies


def _identify_frameworks_and_tools(repo_path: str) -> Dict[str, List[str]]:
    """Identify frameworks and tools used in the repository"""
    frameworks_and_tools = {
        "frameworks": [],
        "databases": [],
        "cloud_services": [],
        "security_tools": [],
        "monitoring_tools": [],
        "build_tools": [],
        "testing_frameworks": []
    }
    
    # Common patterns for technology identification
    patterns = {
        "frameworks": {
            "python": ["django", "flask", "fastapi", "tornado", "bottle"],
            "javascript": ["react", "vue", "angular", "express", "next", "nuxt"],
            "java": ["spring", "hibernate", "struts", "play", "quarkus"],
            "csharp": ["asp.net", "entity framework", "xamarin", "blazor"],
            "php": ["laravel", "symfony", "codeigniter", "yii", "zend"],
            "ruby": ["rails", "sinatra", "hanami", "grape"],
            "go": ["gin", "echo", "fiber", "gorilla", "chi"]
        },
        "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb"],
        "cloud_services": ["aws", "azure", "gcp", "heroku", "digitalocean", "kubernetes", "docker"],
        "security_tools": ["jwt", "oauth", "oauth2", "saml", "ldap", "kerberos", "bcrypt", "argon2"],
        "monitoring_tools": ["splunk", "appdynamics", "thousandeyes", "datadog", "newrelic", "prometheus", "grafana"],
        "build_tools": ["maven", "gradle", "npm", "yarn", "pip", "cargo", "go.mod"],
        "testing_frameworks": ["junit", "pytest", "jest", "mocha", "rspec", "phpunit", "go test"]
    }
    
    try:
        # Scan for technology patterns
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.lower() in ["requirements.txt", "package.json", "pom.xml", "build.gradle", "cargo.toml", "go.mod"]:
                    file_path = os.path.join(root, file)
                    _analyze_dependency_file(file_path, frameworks_and_tools, patterns)
    
    except Exception as e:
        print(f"Error identifying frameworks and tools: {str(e)}")
    
    return frameworks_and_tools


def _analyze_dependency_file(file_path: str, frameworks_and_tools: Dict[str, List[str]], patterns: Dict[str, Any]):
    """Analyze dependency files for technology identification"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
        
        # Check for frameworks
        for language, frameworks in patterns["frameworks"].items():
            for framework in frameworks:
                if framework in content:
                    frameworks_and_tools["frameworks"].append(framework.title())
        
        # Check for other technologies
        for category, tech_list in patterns.items():
            if category != "frameworks":
                for tech in tech_list:
                    if tech in content:
                        frameworks_and_tools[category].append(tech.title())
    
    except Exception as e:
        print(f"Error analyzing dependency file {file_path}: {str(e)}")


def _analyze_security_posture(repo_path: str) -> Dict[str, Any]:
    """Analyze security posture of the repository"""
    security_analysis = {
        "authentication_implemented": False,
        "authorization_implemented": False,
        "input_validation": "Unknown",
        "encryption_used": False,
        "logging_implemented": False,
        "monitoring_configured": False,
        "security_headers": False,
        "ssl_tls_configured": False,
        "secret_management": False,
        "vulnerability_scanning": False
    }
    
    try:
        # Scan for security patterns
        security_patterns = {
            "authentication": ["jwt", "oauth", "saml", "login", "auth", "authentication"],
            "authorization": ["authorization", "permission", "role", "access control"],
            "input_validation": ["validation", "sanitize", "escape", "input check"],
            "encryption": ["encrypt", "hash", "bcrypt", "argon2", "aes", "rsa"],
            "logging": ["logger", "logging", "log4j", "winston", "pino"],
            "monitoring": ["monitoring", "alerting", "splunk", "appdynamics", "thousandeyes"],
            "security_headers": ["security headers", "csp", "hsts", "x-frame-options"],
            "ssl_tls": ["ssl", "tls", "https", "certificate"],
            "secret_management": ["vault", "secrets", "environment variables", "config"],
            "vulnerability_scanning": ["snyk", "owasp", "vulnerability", "security scan"]
        }
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".yaml", ".yml", ".json"]):
                    file_path = os.path.join(root, file)
                    _check_security_patterns(file_path, security_patterns, security_analysis)
    
    except Exception as e:
        print(f"Error analyzing security posture: {str(e)}")
    
    return security_analysis


def _check_security_patterns(file_path: str, security_patterns: Dict[str, List[str]], security_analysis: Dict[str, Any]):
    """Check for security patterns in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
        
        for category, patterns in security_patterns.items():
            for pattern in patterns:
                if pattern in content:
                    if category == "authentication":
                        security_analysis["authentication_implemented"] = True
                    elif category == "authorization":
                        security_analysis["authorization_implemented"] = True
                    elif category == "input_validation":
                        security_analysis["input_validation"] = "Partial"
                    elif category == "encryption":
                        security_analysis["encryption_used"] = True
                    elif category == "logging":
                        security_analysis["logging_implemented"] = True
                    elif category == "monitoring":
                        security_analysis["monitoring_configured"] = True
                    elif category == "security_headers":
                        security_analysis["security_headers"] = True
                    elif category == "ssl_tls":
                        security_analysis["ssl_tls_configured"] = True
                    elif category == "secret_management":
                        security_analysis["secret_management"] = True
                    elif category == "vulnerability_scanning":
                        security_analysis["vulnerability_scanning"] = True
    
    except Exception as e:
        print(f"Error checking security patterns in {file_path}: {str(e)}")


def _determine_applicable_gates(repo_path: str) -> List[str]:
    """Determine which hard gates are applicable to this repository"""
    if CODEGATES_AVAILABLE:
        # Use the actual hard gates from the main application
        return list(GATE_NUMBER_MAPPING.keys())
    else:
        # Fallback to default gates
        return [
        "ALERTING_ACTIONABLE",
        "STRUCTURED_LOGS", 
        "AVOID_LOGGING_SECRETS",
        "AUDIT_TRAIL",
        "CORRELATION_ID",
        "LOG_API_CALLS",
        "CLIENT_UI_ERRORS",
        "RETRY_LOGIC",
        "TIMEOUT_IO",
        "THROTTLING",
        "CIRCUIT_BREAKERS",
        "HTTP_ERROR_CODES",
        "URL_MONITORING",
        "AUTOMATED_TESTS",
        "AUTO_SCALE"
    ]
    

def _calculate_code_metrics(repo_path: str) -> Dict[str, Any]:
    """Calculate code metrics"""
    metrics = {
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "complexity": "Low",
        "maintainability": "Good"
    }
    
    try:
        code_extensions = [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".rs", ".cpp", ".c"]
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    _analyze_file_metrics(file_path, metrics)
    
    except Exception as e:
        print(f"Error calculating code metrics: {str(e)}")
    
    return metrics


def _analyze_file_metrics(file_path: str, metrics: Dict[str, Any]):
    """Analyze metrics for a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        metrics["total_lines"] += len(lines)
        
        for line in lines:
            stripped = line.strip()
            if stripped == "":
                metrics["blank_lines"] += 1
            elif stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                metrics["comment_lines"] += 1
            else:
                metrics["code_lines"] += 1
    
    except Exception as e:
        print(f"Error analyzing file metrics for {file_path}: {str(e)}")


def _analyze_dependencies(repo_path: str) -> Dict[str, Any]:
    """Analyze project dependencies"""
    dependencies = {
        "python": [],
        "javascript": [],
        "java": [],
        "other": []
    }
    
    try:
        # Look for dependency files
        dependency_files = {
            "requirements.txt": "python",
            "package.json": "javascript",
            "pom.xml": "java",
            "build.gradle": "java",
            "cargo.toml": "other",
            "go.mod": "other"
        }
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file in dependency_files:
                    file_path = os.path.join(root, file)
                    category = dependency_files[file]
                    dependencies[category].append(file_path)
    
    except Exception as e:
        print(f"Error analyzing dependencies: {str(e)}")
    
    return dependencies


def _analyze_configuration(repo_path: str) -> Dict[str, Any]:
    """Analyze configuration files"""
    configuration = {
        "environment_files": [],
        "config_files": [],
        "deployment_files": [],
        "monitoring_config": []
    }
    
    try:
        config_patterns = {
            "environment_files": [".env", ".env.local", ".env.production", ".env.development"],
            "config_files": ["config.json", "config.yaml", "config.yml", "settings.py", "application.properties"],
            "deployment_files": ["dockerfile", "docker-compose.yml", "kubernetes.yaml", "helm", "terraform"],
            "monitoring_config": ["prometheus.yml", "grafana", "datadog", "newrelic"]
        }
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                file_lower = file.lower()
                for category, patterns in config_patterns.items():
                    if any(pattern in file_lower for pattern in patterns):
                        configuration[category].append(os.path.join(root, file))
    
    except Exception as e:
        print(f"Error analyzing configuration: {str(e)}")
    
    return configuration


def _get_file_extensions(repo_path: str) -> List[str]:
    """Get all file extensions in the repository"""
    extensions = set()
    
    try:
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    extensions.add(ext)
    except Exception as e:
        print(f"Error getting file extensions: {str(e)}")
    
    return list(extensions)


def _identify_architecture_patterns(repo_path: str) -> List[str]:
    """Identify architecture patterns in the repository"""
    patterns = []
    
    try:
        # Check for common architecture patterns
        if os.path.exists(os.path.join(repo_path, "src")):
            patterns.append("Layered Architecture")
        
        if os.path.exists(os.path.join(repo_path, "api")) or os.path.exists(os.path.join(repo_path, "controllers")):
            patterns.append("MVC Pattern")
        
        if os.path.exists(os.path.join(repo_path, "services")):
            patterns.append("Service Layer Pattern")
        
        if os.path.exists(os.path.join(repo_path, "microservices")) or os.path.exists(os.path.join(repo_path, "services")):
            patterns.append("Microservices")
        
        if os.path.exists(os.path.join(repo_path, "components")):
            patterns.append("Component-Based Architecture")
    
    except Exception as e:
        print(f"Error identifying architecture patterns: {str(e)}")
    
    return patterns


def _identify_main_components(repo_path: str) -> List[str]:
    """Identify main components in the repository"""
    components = []
    
    try:
        # Look for common component directories
        component_dirs = ["api", "controllers", "models", "services", "utils", "helpers", "middleware", "routes"]
        
        for component in component_dirs:
            if os.path.exists(os.path.join(repo_path, component)):
                components.append(f"{component.title()} Layer")
        
        # Look for specific technology components
        if os.path.exists(os.path.join(repo_path, "frontend")) or os.path.exists(os.path.join(repo_path, "client")):
            components.append("Frontend Application")
        
        if os.path.exists(os.path.join(repo_path, "backend")) or os.path.exists(os.path.join(repo_path, "server")):
            components.append("Backend Application")
        
        if os.path.exists(os.path.join(repo_path, "database")) or os.path.exists(os.path.join(repo_path, "db")):
            components.append("Database Layer")
    
    except Exception as e:
        print(f"Error identifying main components: {str(e)}")
    
    return components 
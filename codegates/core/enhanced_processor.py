"""
Enhanced Processor for CodeGates - Generates comprehensive prompts for LLM pattern generation
"""

import os
import json
import re
import xml.etree.ElementTree as ET
import collections
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..models import Language, GateType
from .gate_validators import GateValidatorFactory


@dataclass
class TechnologyContext:
    """Technology context for LLM analysis"""
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    build_tools: List[str]
    containerization: List[str]
    frontend: List[str]
    testing: List[str]
    code_quality: List[str]
    custom_libraries: Dict[str, Dict[str, Any]]


class EnhancedProcessor:
    """Enhanced processor for generating LLM prompts and processing responses"""
    
    def __init__(self):
        self.validator_factory = GateValidatorFactory()
        self.custom_library_summaries = self._load_custom_library_summaries()
    
    def analyze_codebase_for_llm(self, target_path: Path, languages: List[Language]) -> Dict[str, Any]:
        """Analyze codebase and generate comprehensive context for LLM"""
        
        print(f"🔍 Analyzing codebase: {target_path}")
        
        # Scan codebase structure
        file_structure = self._scan_file_structure(target_path)
        
        # Extract build and config files
        build_analysis = self._analyze_build_files(target_path)
        
        # Detect technologies
        tech_context = self._detect_technologies(target_path, build_analysis)
        
        # Generate comprehensive analysis
        analysis = {
            "codebase_summary": self._generate_codebase_summary(target_path, file_structure),
            "technology_context": tech_context,
            "build_analysis": build_analysis,
            "file_structure": file_structure,
            "custom_libraries": self._detect_custom_libraries(build_analysis.get('all_detected_libraries', []))
        }
        
        return analysis
    
    def generate_llm_pattern_prompt(self, analysis: Dict[str, Any], hard_gates: List[str]) -> str:
        """Generate comprehensive prompt for LLM pattern generation"""
        
        tech_context = analysis['technology_context']
        custom_libraries = analysis['custom_libraries']
        
        prompt_parts = []
        prompt_parts.append("You are an expert code analyzer specializing in hard gate validation patterns.")
        prompt_parts.append("Analyze the following codebase and generate specific regex patterns for each hard gate.")
        
        # Technology Summary
        prompt_parts.append("\n--- TECHNOLOGY SUMMARY ---")
        prompt_parts.append(f"Languages: {', '.join(tech_context.languages)}")
        prompt_parts.append(f"Frameworks: {', '.join(tech_context.frameworks)}")
        prompt_parts.append(f"Databases: {', '.join(tech_context.databases)}")
        prompt_parts.append(f"Build Tools: {', '.join(tech_context.build_tools)}")
        prompt_parts.append(f"Containerization: {', '.join(tech_context.containerization)}")
        prompt_parts.append(f"Frontend: {', '.join(tech_context.frontend)}")
        prompt_parts.append(f"Testing: {', '.join(tech_context.testing)}")
        prompt_parts.append(f"Code Quality: {', '.join(tech_context.code_quality)}")
        
        # Custom Libraries
        if custom_libraries:
            prompt_parts.append("\n--- CUSTOM LIBRARIES ---")
            for lib_key, lib_info in custom_libraries.items():
                prompt_parts.append(f"{lib_key}:")
                prompt_parts.append(f"  - Category: {lib_info['category']}")
                prompt_parts.append(f"  - Description: {lib_info['description']}")
                prompt_parts.append(f"  - Hard Gate Implications:")
                for gate, implications in lib_info['hard_gate_implications'].items():
                    prompt_parts.append(f"    * {gate}: {implications}")
        
        # Hard Gates
        prompt_parts.append("\n--- HARD GATES FOR ANALYSIS ---")
        for gate in hard_gates:
            prompt_parts.append(f"- {gate}")
        
        # Task Instructions
        prompt_parts.append("\n--- TASK ---")
        prompt_parts.append("For each hard gate, provide:")
        prompt_parts.append("1. Brief analysis of how this gate applies to the detected technologies")
        prompt_parts.append("2. 3-5 specific regex patterns to detect implementation")
        prompt_parts.append("3. Patterns should be case-insensitive and comprehensive")
        prompt_parts.append("4. Consider both positive (implementation found) and negative (missing implementation) patterns")
        
        # Response Format
        prompt_parts.append("\n--- EXPECTED RESPONSE FORMAT ---")
        prompt_parts.append("Provide a JSON response with this structure:")
        prompt_parts.append("""
{
  "tech_summary": {
    "languages": ["list", "of", "languages"],
    "frameworks": ["list", "of", "frameworks"],
    "databases": ["list", "of", "databases"],
    "build_tools": ["list", "of", "build", "tools"],
    "containerization": ["list", "of", "containerization"],
    "frontend": ["list", "of", "frontend", "technologies"],
    "testing": ["list", "of", "testing", "frameworks"],
    "code_quality": ["list", "of", "code", "quality", "tools"]
  },
  "hard_gates_analysis_short": {
    "Gate Name": {
      "analysis": "Brief analysis of how this gate applies to the technologies",
      "patterns": [
        "(?i)regex_pattern_1",
        "(?i)regex_pattern_2",
        "(?i)regex_pattern_3"
      ]
    }
  }
}
""")
        
        return "\n".join(prompt_parts)
    
    def parse_llm_pattern_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract patterns"""
        
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            # Validate structure
            if 'hard_gates_analysis_short' not in data:
                raise ValueError("Missing 'hard_gates_analysis_short' in LLM response")
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM response as JSON: {e}")
            return self._fallback_pattern_parsing(response)
        except Exception as e:
            print(f"⚠️ Error parsing LLM response: {e}")
            return self._fallback_pattern_parsing(response)
    
    def convert_llm_patterns_to_gate_config(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LLM patterns to CodeGates gate configuration format"""
        
        gate_config = {
            "hard_gates": []
        }
        
        hard_gates_analysis = llm_response.get('hard_gates_analysis_short', {})
        
        for gate_name, gate_data in hard_gates_analysis.items():
            gate_entry = {
                "name": gate_name,
                "description": gate_data.get('analysis', f'LLM-generated patterns for {gate_name}'),
                "validation_method": f"LLM-generated patterns for {gate_name}",
                "patterns": {
                    "llm_generated": gate_data.get('patterns', [])
                }
            }
            gate_config["hard_gates"].append(gate_entry)
        
        return gate_config
    
    def _load_custom_library_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Load custom library summaries"""
        return {
            "eser": {
                "category": "Enterprise Security Event Reporting",
                "description": "ESER provides standardized logging for enterprise applications",
                "hard_gate_implications": {
                    "Logs Searchable/Available": "ESER provides structured logging with standardized event types",
                    "Create Audit Trail Logs": "ESER is specifically designed for audit trail logging",
                    "Tracking ID for Logs": "ESER includes correlation IDs through MDC and request headers"
                },
                "common_patterns": [
                    "eser", "ESEREventFactoryWrapperAPI", "ESEREventFactory", "ESERLoggingAugmenter",
                    "SearoseESERLoggingAugmenter", "LoglibConfiguration", "ApplicationLifecycleEvent"
                ]
            },
            "ebssh": {
                "category": "Enterprise Business Security and Shared Hosting",
                "description": "EBSSH provides enterprise-grade security and hosting capabilities",
                "hard_gate_implications": {
                    "Logs Searchable/Available": "EBSSH LogLib Starters provide enterprise logging",
                    "Avoid Logging Confidential Data": "EBSSH AuthX Starters provide secure authentication",
                    "Create Audit Trail Logs": "EBSSH provides comprehensive audit logging"
                },
                "common_patterns": [
                    "ebssh", "ebssh-loglib-starter", "ebssh-auth-starter", "ebssh-cloud-config-starter"
                ]
            },
            "orchestra": {
                "category": "Enterprise Framework",
                "description": "Orchestra Framework provides enterprise-grade application framework",
                "hard_gate_implications": {
                    "Logs Searchable/Available": "Orchestra Loglib provides structured logging",
                    "Create Audit Trail Logs": "Orchestra Framework supports comprehensive audit logging",
                    "Tracking ID for Logs": "Orchestra includes correlation ID support"
                },
                "common_patterns": [
                    "orchestra", "orchestra-loglib", "orchestra-framework", "LoglibConfiguration"
                ]
            }
        }
    
    def _scan_file_structure(self, target_path: Path) -> Dict[str, Any]:
        """Scan file structure of the codebase"""
        structure = {}
        
        for root, dirs, files in os.walk(target_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'target', 'build']]
            
            relative_path = os.path.relpath(root, target_path)
            if relative_path == '.':
                relative_path = ''
            
            if relative_path not in structure:
                structure[relative_path] = []
            
            for file in files:
                if not file.startswith('.'):
                    structure[relative_path].append(file)
        
        return structure
    
    def _analyze_build_files(self, target_path: Path) -> Dict[str, Any]:
        """Analyze build and configuration files"""
        build_files = {
            'pom.xml': [],
            'build.gradle': [],
            'package.json': [],
            'requirements.txt': [],
            'go.mod': [],
            'Gemfile': [],
            '*.csproj': [],
            'all_detected_libraries': []
        }
        
        # Scan for build files
        for file_path in target_path.rglob('*'):
            if file_path.is_file():
                filename = file_path.name
                
                if filename == 'pom.xml':
                    build_files['pom.xml'] = self._extract_maven_dependencies(file_path)
                elif filename == 'build.gradle':
                    build_files['build.gradle'] = self._extract_gradle_dependencies(file_path)
                elif filename == 'package.json':
                    build_files['package.json'] = self._extract_npm_dependencies(file_path)
                elif filename == 'requirements.txt':
                    build_files['requirements.txt'] = self._extract_python_requirements(file_path)
                elif filename == 'go.mod':
                    build_files['go.mod'] = self._extract_go_dependencies(file_path)
                elif filename == 'Gemfile':
                    build_files['Gemfile'] = self._extract_ruby_gems(file_path)
                elif filename.endswith('.csproj'):
                    build_files['*.csproj'].extend(self._extract_csproj_dependencies(file_path))
        
        # Combine all detected libraries
        all_libs = []
        for libs in build_files.values():
            if isinstance(libs, list):
                all_libs.extend(libs)
        
        build_files['all_detected_libraries'] = list(set(all_libs))
        
        return build_files
    
    def _detect_technologies(self, target_path: Path, build_analysis: Dict[str, Any]) -> TechnologyContext:
        """Detect technologies from build analysis and file structure"""
        
        languages = []
        frameworks = []
        databases = []
        build_tools = []
        containerization = []
        frontend = []
        testing = []
        code_quality = []
        
        # Detect from build files
        if build_analysis.get('pom.xml'):
            languages.append('Java')
            build_tools.append('Maven')
            frameworks.append('Spring Boot')
        
        if build_analysis.get('build.gradle'):
            languages.append('Java')
            build_tools.append('Gradle')
            frameworks.append('Spring Boot')
        
        if build_analysis.get('package.json'):
            languages.append('JavaScript')
            build_tools.append('NPM')
            frameworks.append('Node.js')
        
        if build_analysis.get('requirements.txt'):
            languages.append('Python')
            build_tools.append('pip')
        
        if build_analysis.get('*.csproj'):
            languages.append('C#')
            build_tools.append('NuGet')
            frameworks.append('ASP.NET Core')
        
        # Detect from libraries
        all_libs = build_analysis.get('all_detected_libraries', [])
        
        for lib in all_libs:
            lib_lower = lib.lower()
            
            # Database detection
            if any(db in lib_lower for db in ['mysql', 'postgresql', 'h2', 'hibernate']):
                databases.append(lib)
            
            # Testing detection
            if any(test in lib_lower for test in ['junit', 'test', 'mockito', 'pytest']):
                testing.append(lib)
            
            # Frontend detection
            if any(front in lib_lower for front in ['react', 'angular', 'vue', 'bootstrap']):
                frontend.append(lib)
            
            # Code quality detection
            if any(qual in lib_lower for qual in ['checkstyle', 'sonar', 'eslint']):
                code_quality.append(lib)
        
        # Detect containerization
        if (target_path / 'Dockerfile').exists():
            containerization.append('Docker')
        if (target_path / 'docker-compose.yml').exists():
            containerization.append('Docker Compose')
        
        return TechnologyContext(
            languages=languages,
            frameworks=frameworks,
            databases=databases,
            build_tools=build_tools,
            containerization=containerization,
            frontend=frontend,
            testing=testing,
            code_quality=code_quality,
            custom_libraries={}
        )
    
    def _detect_custom_libraries(self, all_libraries: List[str]) -> Dict[str, Dict[str, Any]]:
        """Detect custom libraries from the library list"""
        detected = {}
        
        for lib in all_libraries:
            for lib_key, lib_info in self.custom_library_summaries.items():
                common_patterns = lib_info.get('common_patterns', [])
                
                for pattern in common_patterns:
                    if pattern.lower() in lib.lower():
                        detected[lib_key] = {
                            'library_name': lib,
                            'category': lib_info.get('category', 'Unknown'),
                            'description': lib_info.get('description', ''),
                            'hard_gate_implications': lib_info.get('hard_gate_implications', {}),
                            'matched_pattern': pattern
                        }
                        break
        
        return detected
    
    def _generate_codebase_summary(self, target_path: Path, file_structure: Dict[str, Any]) -> str:
        """Generate codebase summary"""
        total_files = sum(len(files) for files in file_structure.values())
        total_dirs = len(file_structure)
        
        return f"Codebase contains {total_files} files across {total_dirs} directories"
    
    def _extract_maven_dependencies(self, filepath: Path) -> List[str]:
        """Extract Maven dependencies"""
        dependencies = []
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            dep_elements = root.findall('.//maven:dependency', namespace)
            
            for dep in dep_elements:
                group_id = dep.find('maven:groupId', namespace)
                artifact_id = dep.find('maven:artifactId', namespace)
                
                if group_id is not None and artifact_id is not None:
                    dependencies.append(f"{group_id.text}:{artifact_id.text}")
        
        except Exception as e:
            print(f"Error parsing Maven file: {e}")
        
        return dependencies
    
    def _extract_gradle_dependencies(self, filepath: Path) -> List[str]:
        """Extract Gradle dependencies"""
        dependencies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple regex extraction
            dep_patterns = re.findall(r'implementation\s+[\'"]([^\'"]+)[\'"]', content)
            dependencies.extend(dep_patterns)
        
        except Exception as e:
            print(f"Error parsing Gradle file: {e}")
        
        return dependencies
    
    def _extract_npm_dependencies(self, filepath: Path) -> List[str]:
        """Extract NPM dependencies"""
        dependencies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in data:
                    for package, version in data[dep_type].items():
                        dependencies.append(f"{package}@{version}")
        
        except Exception as e:
            print(f"Error parsing NPM file: {e}")
        
        return dependencies
    
    def _extract_python_requirements(self, filepath: Path) -> List[str]:
        """Extract Python requirements"""
        dependencies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies.append(line)
        
        except Exception as e:
            print(f"Error parsing Python requirements: {e}")
        
        return dependencies
    
    def _extract_go_dependencies(self, filepath: Path) -> List[str]:
        """Extract Go dependencies"""
        dependencies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            require_matches = re.findall(r'require\s+([^\s]+)\s+([^\s]+)', content)
            for module, version in require_matches:
                dependencies.append(f"{module}@{version}")
        
        except Exception as e:
            print(f"Error parsing Go module: {e}")
        
        return dependencies
    
    def _extract_ruby_gems(self, filepath: Path) -> List[str]:
        """Extract Ruby gems"""
        dependencies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            gem_matches = re.findall(r"gem\s*['\"]([^'\"]+)['\"]", content)
            dependencies.extend(gem_matches)
        
        except Exception as e:
            print(f"Error parsing Gemfile: {e}")
        
        return dependencies
    
    def _extract_csproj_dependencies(self, filepath: Path) -> List[str]:
        """Extract C# project dependencies"""
        dependencies = []
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            package_refs = root.findall('.//PackageReference')
            for pkg_ref in package_refs:
                include = pkg_ref.get('Include')
                if include:
                    dependencies.append(f"NuGet:{include}")
        
        except Exception as e:
            print(f"Error parsing C# project: {e}")
        
        return dependencies
    
    def _fallback_pattern_parsing(self, response: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON LLM responses"""
        print("⚠️ Using fallback pattern parsing")
        
        # Try to extract JSON from the response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            try:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            except:
                pass
        
        # Return minimal structure
        return {
            "tech_summary": {
                "languages": ["Unknown"],
                "frameworks": [],
                "databases": [],
                "build_tools": [],
                "containerization": [],
                "frontend": [],
                "testing": [],
                "code_quality": []
            },
            "hard_gates_analysis_short": {}
        } 
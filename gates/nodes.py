"""
CodeGates Nodes - PocketFlow Implementation
All nodes for the hard gate validation workflow
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from base import Node 
from datetime import datetime
import tempfile
import uuid

# Import utilities
try:
    # Relative imports (when run as module)
    from .utils.git_operations import clone_repository, cleanup_repository
    from .utils.file_scanner import scan_directory
    from .utils.hard_gates import HARD_GATES, get_gate_number
    from .utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider
    from .utils.gate_applicability import gate_applicability_analyzer
    # Import enhanced criteria evaluator
    from .criteria_evaluator import EnhancedGateEvaluator, CriteriaEvaluator, migrate_legacy_gate
except ImportError:
    # Fall back to absolute imports (when run directly)
    from utils.git_operations import clone_repository, cleanup_repository
    from utils.file_scanner import scan_directory
    from utils.hard_gates import HARD_GATES, get_gate_number
    from utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider
    from utils.gate_applicability import gate_applicability_analyzer
    # Import enhanced criteria evaluator
    from criteria_evaluator import EnhancedGateEvaluator, CriteriaEvaluator, migrate_legacy_gate


class FetchRepositoryNode(Node):
    """Node to fetch/clone repository"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare repository fetch parameters"""
        return {
            "repository_url": shared["request"]["repository_url"],
            "branch": shared["request"]["branch"],
            "github_token": shared["request"].get("github_token"),
            "temp_dir": shared["temp_dir"]
        }
    
    def exec(self, params: Dict[str, Any]) -> str:
        """Fetch repository from URL or use local path, including -cd variant if available"""
        repo_url = params["repository_url"]
        branch = params["branch"]
        github_token = params["github_token"]
        
        # Check if it's a local path
        if os.path.exists(repo_url):
            print(f"📁 Using local repository: {repo_url}")
            return repo_url
        
        # Otherwise, clone from remote
        print(f"🔄 Fetching repository: {repo_url}")
        
        # Create target directory
        target_dir = os.path.join(tempfile.gettempdir(), f"codegates_{uuid.uuid4().hex[:8]}")
        os.makedirs(target_dir, exist_ok=True)
        print(f"📁 Target directory created: {target_dir}")
        
        # Clone main repository
        main_repo_path = clone_repository(
            repo_url=repo_url,
            branch=branch,
            github_token=github_token,
            target_dir=target_dir
        )
        
        # Try to clone the -cd variant
        cd_repo_path = None
        try:
            # Construct -cd variant URL
            if repo_url.endswith('.git'):
                cd_repo_url = repo_url[:-4] + '-cd.git'
            else:
                cd_repo_url = repo_url + '-cd'
            
            print(f"🔄 Attempting to fetch -cd variant: {cd_repo_url}")
            
            # Create subdirectory for -cd variant
            cd_target_dir = os.path.join(target_dir, 'cd-variant')
            os.makedirs(cd_target_dir, exist_ok=True)
            
            cd_repo_path = clone_repository(
                repo_url=cd_repo_url,
                branch=branch,
                github_token=github_token,
                target_dir=cd_target_dir
            )
            
            print(f"✅ Successfully fetched -cd variant: {cd_repo_path}")
            
        except Exception as e:
            print(f"⚠️ -cd variant not available or failed to fetch: {e}")
            cd_repo_path = None
        
        # If we have both repositories, merge them
        if cd_repo_path and os.path.exists(cd_repo_path):
            print(f"🔄 Merging main repository with -cd variant...")
            
            # Copy -cd variant files to main repository (avoiding conflicts)
            import shutil
            from pathlib import Path
            
            main_path = Path(main_repo_path)
            cd_path = Path(cd_repo_path)
            
            # Copy files from -cd variant to main repository
            for item in cd_path.rglob('*'):
                if item.is_file():
                    # Calculate relative path from cd_path
                    relative_path = item.relative_to(cd_path)
                    target_path = main_path / relative_path
                    
                    # Create parent directories if they don't exist
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file if it doesn't exist in main repo, or if it's different
                    if not target_path.exists():
                        shutil.copy2(item, target_path)
                        print(f"📄 Copied: {relative_path}")
                    else:
                        # If file exists, append -cd suffix to filename
                        stem = target_path.stem
                        suffix = target_path.suffix
                        new_name = f"{stem}-cd{suffix}"
                        new_target_path = target_path.parent / new_name
                        shutil.copy2(item, new_target_path)
                        print(f"📄 Copied with -cd suffix: {relative_path} -> {new_name}")
            
            print(f"✅ Successfully merged repositories")
        
        return main_repo_path
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        """Store repository path in shared store"""
        shared["repository"]["local_path"] = exec_res
        print(f"✅ Repository fetched to: {exec_res}")
        return "default"


class ProcessCodebaseNode(Node):
    """Node to process codebase and extract metadata"""
    
    def prep(self, shared: Dict[str, Any]) -> str:
        """Get repository path"""
        repo_path = shared["repository"]["local_path"]
        if not repo_path or not os.path.exists(repo_path):
            raise ValueError("Repository path not found or invalid")
        return repo_path
    
    def exec(self, repo_path: str) -> Dict[str, Any]:
        """Scan repository and extract metadata"""
        print(f"📊 Processing codebase: {repo_path}")
        
        metadata = scan_directory(repo_path, max_files=5000)
        
        return metadata
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Dict[str, Any]) -> str:
        """Store metadata in shared store"""
        shared["repository"]["metadata"] = exec_res
        print(f"✅ Processed {exec_res['total_files']} files, {exec_res['total_lines']} lines")
        return "default"


class ExtractConfigNode(Node):
    """Node to extract configuration and build file contents"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare config extraction parameters"""
        return {
            "repo_path": shared["repository"]["local_path"],
            "build_files": shared["repository"]["metadata"].get("build_files", []),
            "config_files": shared["repository"]["metadata"].get("config_files", [])
        }
    
    def exec(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract config and build file contents"""
        print("🔧 Extracting configuration and build files...")
        
        repo_path = Path(params["repo_path"])
        config_data = {
            "build_files": {},
            "config_files": {},
            "dependencies": []
        }
        
        # Extract build file contents
        for build_file in params["build_files"]:
            file_path = repo_path / build_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    config_data["build_files"][build_file] = {
                        "content": content[:2000],  # Limit content size
                        "size": len(content),
                        "type": self._get_build_file_type(build_file)
                    }
                    
                    # Extract dependencies
                    deps = self._extract_dependencies(build_file, content)
                    config_data["dependencies"].extend(deps)
                    
                except Exception as e:
                    print(f"⚠️ Error reading build file {build_file}: {e}")
        
        # Extract config file contents
        for config_file in params["config_files"]:
            file_path = repo_path / config_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    config_data["config_files"][config_file] = {
                        "content": content[:2000],  # Limit content size
                        "size": len(content),
                        "type": self._get_config_file_type(config_file)
                    }
                except Exception as e:
                    print(f"⚠️ Error reading config file {config_file}: {e}")
        
        # Remove duplicates from dependencies
        config_data["dependencies"] = list(set(config_data["dependencies"]))
        
        return config_data
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Store config data in shared store"""
        shared["config"] = exec_res
        print(f"✅ Extracted {len(exec_res['build_files'])} build files, {len(exec_res['config_files'])} config files")
        print(f"   Found {len(exec_res['dependencies'])} dependencies")
        return "default"
    
    def _get_build_file_type(self, filename: str) -> str:
        """Get build file type"""
        if filename == "package.json":
            return "npm"
        elif filename in ["pom.xml"]:
            return "maven"
        elif "gradle" in filename:
            return "gradle"
        elif filename in ["requirements.txt", "setup.py", "pyproject.toml"]:
            return "python"
        elif filename == "Cargo.toml":
            return "rust"
        elif filename == "go.mod":
            return "go"
        return "unknown"
    
    def _get_config_file_type(self, filename: str) -> str:
        """Get config file type"""
        if "application" in filename:
            return "application"
        elif "log" in filename:
            return "logging"
        elif filename.startswith(".env"):
            return "environment"
        return "general"
    
    def _extract_dependencies(self, filename: str, content: str) -> List[str]:
        """Extract dependencies from build file content"""
        dependencies = []
        
        try:
            if filename == "package.json":
                data = json.loads(content)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                dependencies.extend(list(deps.keys()))
                dependencies.extend(list(dev_deps.keys()))
            
            elif filename == "requirements.txt":
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before version specifiers)
                        package = re.split(r'[>=<~!]', line)[0].strip()
                        if package:
                            dependencies.append(package)
            
            elif filename == "pom.xml":
                # Simple regex to extract Maven dependencies
                import re
                artifact_pattern = r'<artifactId>([^<]+)</artifactId>'
                matches = re.findall(artifact_pattern, content)
                dependencies.extend(matches)
        
        except Exception as e:
            print(f"⚠️ Error extracting dependencies from {filename}: {e}")
        
        return dependencies


class GeneratePromptNode(Node):
    """Node to generate comprehensive LLM prompt"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare prompt generation data"""
        return {
            "metadata": shared["repository"]["metadata"],
            "config": shared["config"],
            "hard_gates": shared["hard_gates"],
            "repo_url": shared["request"]["repository_url"]
        }
    
    def exec(self, data: Dict[str, Any]) -> str:
        """Generate comprehensive LLM prompt"""
        print("📋 Generating LLM prompt...")
        
        # Build comprehensive prompt similar to processor.py
        prompt_parts = []
        
        prompt_parts.append("You are an expert code analyzer specializing in hard gate validation patterns for enterprise security and compliance.")
        prompt_parts.append("")
        prompt_parts.append("## CODEBASE ANALYSIS")
        prompt_parts.append("")
        
        # Repository overview
        metadata = data["metadata"]
        prompt_parts.append("### Repository Overview")
        prompt_parts.append(f"- Repository: {data['repo_url']}")
        prompt_parts.append(f"- Total Files: {metadata.get('total_files', 0)}")
        prompt_parts.append(f"- Total Lines: {metadata.get('total_lines', 0)}")
        prompt_parts.append(f"- Languages: {', '.join(metadata.get('languages', {}).keys())}")
        prompt_parts.append("")
        
        # Language statistics
        language_stats = metadata.get('language_stats', {})
        if language_stats:
            prompt_parts.append("### Language Distribution")
            prompt_parts.append("```json")
            prompt_parts.append(json.dumps(language_stats, indent=2))
            prompt_parts.append("```")
            prompt_parts.append("")
        
        # File structure metadata
        directory_structure = metadata.get('directory_structure', {})
        if directory_structure:
            prompt_parts.append("### Codebase File Structure")
            prompt_parts.append("```yaml")
            prompt_parts.append(self._convert_structure_to_yaml(directory_structure))
            prompt_parts.append("```")
            prompt_parts.append("")
        
        # Build files
        config = data["config"]
        if config["build_files"]:
            prompt_parts.append("### Build Files Detected")
            for filename, info in config["build_files"].items():
                prompt_parts.append(f"**{filename}** ({info['type']})")
                prompt_parts.append(f"```")
                prompt_parts.append(info["content"][:1000])  # First 1000 chars
                prompt_parts.append(f"```")
                prompt_parts.append("")
        
        # Config files
        if config["config_files"]:
            prompt_parts.append("### Configuration Files")
            for filename, info in config["config_files"].items():
                prompt_parts.append(f"**{filename}** ({info['type']})")
                prompt_parts.append(f"```")
                prompt_parts.append(info["content"][:1000])  # First 1000 chars for config files
                prompt_parts.append(f"```")
                prompt_parts.append("")
        
        # Dependencies
        if config["dependencies"]:
            prompt_parts.append("### Dependencies")
            deps_str = ", ".join(config["dependencies"][:50])  # First 50 deps
            prompt_parts.append(f"- {deps_str}")
            if len(config["dependencies"]) > 50:
                prompt_parts.append(f"- ... and {len(config['dependencies']) - 50} more")
            prompt_parts.append("")
        
        # File type distribution
        file_types = metadata.get('file_types', {})
        if file_types:
            prompt_parts.append("### File Type Distribution")
            prompt_parts.append("```json")
            prompt_parts.append(json.dumps(file_types, indent=2))
            prompt_parts.append("```")
            prompt_parts.append("")
        
        # Hard gates
        prompt_parts.append("## HARD GATES TO ANALYZE")
        for gate in data["hard_gates"]:
            prompt_parts.append(f"- **{gate['name']}**: {gate['description']}")
        prompt_parts.append("")
        
        # Task description
        prompt_parts.append("## TASK")
        prompt_parts.append("Generate comprehensive regex patterns for each hard gate that would be effective for this specific codebase.")
        prompt_parts.append("Consider the detected languages, frameworks, dependencies, and file structure when formulating patterns.")
        prompt_parts.append("Use the file structure metadata to understand the project organization and target patterns appropriately.")
        prompt_parts.append("")
        prompt_parts.append("## CRITICAL PATTERN REQUIREMENTS")
        prompt_parts.append("**MUST FOLLOW THESE RULES:**")
        prompt_parts.append("1. **NO COMPLEX REGEX**: Use simple, readable patterns that actually work")
        prompt_parts.append("2. **REAL-WORLD FOCUSED**: Patterns must match actual code, not theoretical examples")
        prompt_parts.append("3. **TECHNOLOGY-SPECIFIC**: Tailor patterns to the detected frameworks and libraries")
        prompt_parts.append("4. **IMPORT PATTERNS**: Include import/using statements for comprehensive coverage")
        prompt_parts.append("5. **FLEXIBLE MATCHING**: Use \\b\\w*pattern\\w* for flexible name matching")
        prompt_parts.append("")
        prompt_parts.append("## TECHNOLOGY-SPECIFIC PATTERN GUIDELINES")
        
        # Add technology-specific guidelines based on detected languages
        primary_languages = metadata.get('language_stats', {})
        if 'Java' in primary_languages:
            prompt_parts.append("### Java/Spring Boot Patterns:")
            prompt_parts.append("- **Imports**: r'import\\s+org\\.slf4j\\.Logger', r'import\\s+org\\.slf4j\\.LoggerFactory'")
            prompt_parts.append("- **Annotations**: r'@Slf4j', r'@RestController', r'@Service', r'@Component'")
            prompt_parts.append("- **Logging**: r'log\\.(info|debug|error|warn|trace)\\(', r'logger\\.(info|debug|error|warn|trace)\\('")
            prompt_parts.append("- **Spring**: r'LoggerFactory\\.getLogger\\(', r'private\\s+static\\s+final\\s+Logger'")
            prompt_parts.append("")
        
        if 'Python' in primary_languages:
            prompt_parts.append("### Python Patterns:")
            prompt_parts.append("- **Imports**: r'import\\s+logging', r'from\\s+logging\\s+import', r'import\\s+structlog'")
            prompt_parts.append("- **Logging**: r'logging\\.(info|debug|error|warning|critical)', r'logger\\.(info|debug|error|warning|critical)'")
            prompt_parts.append("- **Framework**: r'app\\.logger\\.', r'flask\\.logging', r'django\\.utils\\.log'")
            prompt_parts.append("")
        
        if 'JavaScript' in primary_languages or 'TypeScript' in primary_languages:
            prompt_parts.append("### JavaScript/TypeScript Patterns:")
            prompt_parts.append("- **Imports**: r'import\\s+\\w*[Ll]og\\w*\\s+from', r'const\\s+\\w*[Ll]og\\w*\\s*=\\s*require'")
            prompt_parts.append("- **Logging**: r'console\\.(log|info|debug|error|warn)', r'winston\\.', r'pino\\.'")
            prompt_parts.append("- **Modern**: r'winston\\.createLogger\\(', r'pino\\(\\)', r'bunyan\\.createLogger\\('")
            prompt_parts.append("")
        
        if 'C#' in primary_languages:
            prompt_parts.append("### C#/.NET Patterns:")
            prompt_parts.append("- **Imports**: r'using\\s+Microsoft\\.Extensions\\.Logging', r'using\\s+Serilog'")
            prompt_parts.append("- **Logging**: r'ILogger<\\w+>', r'Log\\.(Information|Debug|Error|Warning|Critical)'")
            prompt_parts.append("- **Framework**: r'AddSerilog\\(\\)', r'AddLogging\\(\\)', r'LoggerFactory'")
            prompt_parts.append("")
        
        prompt_parts.append("## OUTPUT FORMAT")
        prompt_parts.append("Provide a JSON response with patterns, descriptions, significance, and expected coverage analysis for each gate:")
        prompt_parts.append("```json")
        prompt_parts.append("{")
        prompt_parts.append('  "GATE_NAME": {')
        prompt_parts.append('    "patterns": [')
        prompt_parts.append('      "r\'import\\\\s+org\\\\.slf4j\\\\.Logger\'",')
        prompt_parts.append('      "r\'@Slf4j\'",')
        prompt_parts.append('      "r\'log\\\\.(info|debug|error|warn|trace)\\\\(\'",')
        prompt_parts.append('      "r\'logger\\\\.(info|debug|error|warn|trace)\\\\(\'"')
        prompt_parts.append('    ],')
        prompt_parts.append('    "description": "Comprehensive logging patterns for this technology stack",')
        prompt_parts.append('    "significance": "Critical for monitoring and debugging in production environments",')
        prompt_parts.append('    "expected_coverage": {')
        prompt_parts.append('      "percentage": 25,')
        prompt_parts.append('      "reasoning": "Based on project structure and framework usage patterns",')
        prompt_parts.append('      "confidence": "high"')
        prompt_parts.append('    }')
        prompt_parts.append('  }')
        prompt_parts.append("}")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("**IMPORTANT**: If a gate is not applicable to the detected technology stack or project type, respond with:")
        prompt_parts.append("```json")
        prompt_parts.append('  "GATE_NAME": {')
        prompt_parts.append('    "patterns": [],')
        prompt_parts.append('    "description": "Not Applicable",')
        prompt_parts.append('    "significance": "This gate is not applicable to the current technology stack and project type",')
        prompt_parts.append('    "expected_coverage": {')
        prompt_parts.append('      "percentage": 0,')
        prompt_parts.append('      "reasoning": "Not applicable to this technology stack",')
        prompt_parts.append('      "confidence": "high"')
        prompt_parts.append('    }')
        prompt_parts.append('  }')
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("## PATTERN EFFECTIVENESS REQUIREMENTS")
        prompt_parts.append("Focus on patterns that are:")
        prompt_parts.append("- **Specific to the detected technology stack and libraries used**")
        prompt_parts.append("- **Based on actual import statements and framework usage**")
        prompt_parts.append("- **Comprehensive in coverage but simple in implementation**")
        prompt_parts.append("- **Practical for real-world codebases**")
        prompt_parts.append("- **Security and compliance-focused**")
        prompt_parts.append("- **Contextually aware of the project structure and organization**")
        prompt_parts.append("- **FLEXIBLE and INCLUSIVE**: Patterns should catch real-world variations")
        prompt_parts.append("")
        prompt_parts.append("**PATTERN EXAMPLES FOR COMMON SCENARIOS:**")
        
        # Add specific examples based on detected technologies
        if 'Java' in primary_languages:
            prompt_parts.append("**Java/Spring Boot Examples:**")
            prompt_parts.append("- Logging: r'import\\s+org\\.slf4j\\.Logger', r'@Slf4j', r'log\\.(info|debug|error|warn|trace)\\('")
            prompt_parts.append("- API: r'@RestController', r'@GetMapping', r'@PostMapping', r'@RequestMapping'")
            prompt_parts.append("- Error: r'try\\s*\\{', r'catch\\s*\\(\\w+\\s+\\w+\\)', r'throw\\s+new\\s+\\w+Exception'")
            prompt_parts.append("- Tests: r'@Test', r'@MockBean', r'@SpringBootTest', r'import\\s+org\\.junit'")
            prompt_parts.append("")
        
        if 'Python' in primary_languages:
            prompt_parts.append("**Python Examples:**")
            prompt_parts.append("- Logging: r'import\\s+logging', r'logging\\.(info|debug|error|warning|critical)', r'logger\\s*=\\s*logging\\.getLogger'")
            prompt_parts.append("- API: r'@app\\.route', r'@api\\.route', r'from\\s+flask\\s+import', r'from\\s+fastapi\\s+import'")
            prompt_parts.append("- Error: r'try:', r'except\\s+\\w+:', r'raise\\s+\\w+Error'")
            prompt_parts.append("- Tests: r'import\\s+unittest', r'import\\s+pytest', r'def\\s+test_\\w+'")
            prompt_parts.append("")
        
        if 'JavaScript' in primary_languages or 'TypeScript' in primary_languages:
            prompt_parts.append("**JavaScript/TypeScript Examples:**")
            prompt_parts.append("- Logging: r'console\\.(log|info|debug|error|warn)', r'winston\\.', r'import\\s+\\w*[Ll]og\\w*\\s+from'")
            prompt_parts.append("- API: r'app\\.(get|post|put|delete)', r'router\\.(get|post|put|delete)', r'@Controller', r'@Get'")
            prompt_parts.append("- Error: r'try\\s*\\{', r'catch\\s*\\(\\w+\\)', r'throw\\s+new\\s+Error'")
            prompt_parts.append("- Tests: r'describe\\(', r'it\\(', r'test\\(', r'expect\\('")
            prompt_parts.append("")
        
        prompt_parts.append("**CRITICAL: AVOID THESE PATTERN MISTAKES:**")
        prompt_parts.append("- ❌ DON'T use: r'\\blogger\\.([a-zA-Z]+)\\.([a-zA-Z]+)\\(' (too restrictive)")
        prompt_parts.append("- ✅ DO use: r'\\b\\w*logger\\w*\\.(info|debug|error|warn|trace)\\(' (flexible)")
        prompt_parts.append("- ❌ DON'T use: r'\\bsecret\\.[a-zA-Z]+' (won't match real code)")
        prompt_parts.append("- ✅ DO use: r'(password|secret|token|key)\\s*[=:]' (matches assignments)")
        prompt_parts.append("- ❌ DON'T use: Complex nested groups without clear purpose")
        prompt_parts.append("- ✅ DO use: Simple, readable patterns that match actual code")
        prompt_parts.append("")
        prompt_parts.append("For each gate, provide:")
        prompt_parts.append("- **patterns**: Array of regex patterns optimized for the detected technology stack")
        prompt_parts.append("- **description**: 1-2 sentence explanation of what the patterns detect and why")
        prompt_parts.append("- **significance**: 2-3 sentence explanation of importance for this specific technology stack")
        prompt_parts.append("- **expected_coverage**: Intelligent analysis based on project characteristics")
        prompt_parts.append("  - **percentage**: Realistic percentage based on project type and size")
        prompt_parts.append("  - **reasoning**: Detailed explanation considering:")
        prompt_parts.append("    - Project architecture and detected frameworks")
        prompt_parts.append("    - Technology stack and library dependencies")
        prompt_parts.append("    - File types and their distribution")
        prompt_parts.append("    - Common implementation patterns for this gate type")
        prompt_parts.append("    - Industry standards and best practices")
        prompt_parts.append("  - **confidence**: High/medium/low based on pattern specificity and technology match")
        prompt_parts.append("")
        prompt_parts.append("**COVERAGE ANALYSIS GUIDELINES:**")
        prompt_parts.append("- **Consider the specific technology stack**: Different frameworks have different patterns")
        prompt_parts.append("- **Account for project size and complexity**: Larger projects may have lower percentages but higher absolute counts")
        prompt_parts.append("- **Factor in architectural patterns**: Microservices vs monolith affects distribution")
        prompt_parts.append("- **Consider file type distribution**: Some patterns only apply to specific file types")
        prompt_parts.append("- **Account for library usage**: Imported libraries may provide built-in implementations")
        prompt_parts.append("- **Be realistic**: Not every file needs every pattern, estimate based on actual usage scenarios")
        prompt_parts.append("- **Provide reasoning that shows understanding of the codebase structure and technology choices**")
        prompt_parts.append("")
        prompt_parts.append("**REMEMBER**: Generate patterns that will actually find real code in this specific project!")
        
        prompt_parts.append("## CRITICAL INFRASTRUCTURE PATTERN DETECTION")
        prompt_parts.append("**SPECIAL ANALYSIS REQUIRED:**")
        prompt_parts.append("")
        prompt_parts.append("### CENTRALIZED LOGGING FRAMEWORKS")
        prompt_parts.append("If you detect ANY of these centralized logging frameworks, set coverage to 100% for STRUCTURED_LOGS:")
        prompt_parts.append("- **Java**: Logback, Log4j2, SLF4J with structured output")
        prompt_parts.append("- **Python**: structlog, python-json-logger, loguru")
        prompt_parts.append("- **JavaScript**: Winston, Pino, Bunyan with JSON format")
        prompt_parts.append("- **C#**: Serilog, NLog with structured logging")
        prompt_parts.append("- **Enterprise**: ELK Stack, Splunk, DataDog, New Relic")
        prompt_parts.append("")
        prompt_parts.append("### RESILIENCE PATTERNS")
        prompt_parts.append("If you detect ANY of these resilience patterns, set coverage to 100% for the corresponding gates:")
        prompt_parts.append("- **Circuit Breakers**: Hystrix, Resilience4j, Polly, pybreaker → CIRCUIT_BREAKERS = 100%")
        prompt_parts.append("- **Retry Logic**: Spring Retry, Polly Retry, tenacity, retrying → RETRY_LOGIC = 100%")
        prompt_parts.append("- **Timeouts**: HttpClient.Timeout, RestTemplate timeout, aiohttp timeout → TIMEOUTS = 100%")
        prompt_parts.append("- **Throttling**: RateLimiter, Bucket4j, express-rate-limit → THROTTLING = 100%")
        prompt_parts.append("")
        prompt_parts.append("### DETECTION CRITERIA")
        prompt_parts.append("Look for these specific indicators:")
        prompt_parts.append("- **Dependencies**: Check package.json, pom.xml, requirements.txt, .csproj")
        prompt_parts.append("- **Configuration**: Check logging config files, application.properties, appsettings.json")
        prompt_parts.append("- **Imports**: Look for framework-specific import statements")
        prompt_parts.append("- **Usage**: Check for actual usage patterns in code")
        prompt_parts.append("")
        prompt_parts.append("### COVERAGE RULES")
        prompt_parts.append("**When infrastructure patterns are detected:**")
        prompt_parts.append("- Set expected_coverage.percentage = 100")
        prompt_parts.append("- Set expected_coverage.confidence = 'high'")
        prompt_parts.append("- Set expected_coverage.reasoning = 'Infrastructure framework detected'")
        prompt_parts.append("- Include comprehensive patterns for the detected framework")
        prompt_parts.append("")
        prompt_parts.append("**Example for detected centralized logging:**")
        prompt_parts.append("```json")
        prompt_parts.append('  "STRUCTURED_LOGS": {')
        prompt_parts.append('    "patterns": [')
        prompt_parts.append('      "r\'import\\\\s+org\\\\\\.slf4j\\\\\\.Logger\'",')
        prompt_parts.append('      "r\'@Slf4j\'",')
        prompt_parts.append('      "r\'logback\\.xml\'",')
        prompt_parts.append('      "r\'logback-spring\\.xml\'"')
        prompt_parts.append('    ],')
        prompt_parts.append('    "description": "Centralized logging framework (Logback/SLF4J) detected",')
        prompt_parts.append('    "significance": "Enterprise-grade structured logging infrastructure in place",')
        prompt_parts.append('    "expected_coverage": {')
        prompt_parts.append('      "percentage": 100,')
        prompt_parts.append('      "reasoning": "Centralized logging framework (Logback/SLF4J) detected in dependencies and configuration",')
        prompt_parts.append('      "confidence": "high"')
        prompt_parts.append('    }')
        prompt_parts.append('  }')
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("## CRITICAL PATTERN REQUIREMENTS")
        
        prompt = "\n".join(prompt_parts)
        return prompt
    
    def _convert_structure_to_yaml(self, structure: Dict[str, Any], indent: int = 0) -> str:
        """Convert directory structure to YAML format with only file names"""
        yaml_lines = []
        indent_str = "  " * indent
        
        for name, content in structure.items():
            if isinstance(content, dict):
                if content.get('type') == 'file':
                    # It's a file - just add the filename
                    yaml_lines.append(f"{indent_str}- {name}")
                else:
                    # It's a directory - add directory name and recurse
                    yaml_lines.append(f"{indent_str}{name}:")
                    yaml_lines.append(self._convert_structure_to_yaml(content, indent + 1))
            else:
                # Fallback for other types
                yaml_lines.append(f"{indent_str}- {name}")
        
        return "\n".join(yaml_lines)
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        """Store prompt in shared store"""
        shared["llm"]["prompt"] = exec_res
        
        # Log the final prompt
        print(f"✅ Generated LLM prompt ({len(exec_res)} characters)")
        
        # Save prompt to log file for debugging
        try:
            import os
            from datetime import datetime
            
            # Get logs directory from shared context
            logs_dir = shared.get("directories", {}).get("logs", "./logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Generate timestamp for log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_id = shared["request"].get("scan_id", "unknown")
            
            # Save prompt to file
            prompt_log_file = os.path.join(logs_dir, f"prompt_{scan_id}_{timestamp}.txt")
            with open(prompt_log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("CODEGATES LLM PROMPT LOG\n")
                f.write("=" * 80 + "\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Scan ID: {scan_id}\n")
                f.write(f"Repository: {shared['request'].get('repository_url', 'unknown')}\n")
                f.write(f"Branch: {shared['request'].get('branch', 'unknown')}\n")
                f.write(f"Prompt Length: {len(exec_res)} characters\n")
                f.write("=" * 80 + "\n\n")
                f.write(exec_res)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("END OF PROMPT\n")
                f.write("=" * 80 + "\n")
            
            print(f"📝 Prompt logged to: {prompt_log_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to log prompt: {e}")
        
        return "default"


class CallLLMNode(Node):
    """Node to call LLM for pattern generation using comprehensive LLM client"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare LLM call parameters"""
        return {
            "prompt": shared["llm"]["prompt"],
            "llm_config": shared.get("llm_config", {}),
            "request": shared["request"]
        }
    
    def exec(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM to generate patterns using the comprehensive LLM client"""
        print("🤖 Calling LLM for pattern generation...")
        
        # Set a timeout for the entire LLM operation
        import signal
        import threading
        
        # Timeout configuration
        LLM_TIMEOUT = int(os.getenv("CODEGATES_LLM_TIMEOUT", "500"))  # 2 minutes default
        print(f"   ⏱️ LLM timeout set to {LLM_TIMEOUT} seconds")
        
        # Try to create LLM client from environment first
        llm_client = create_llm_client_from_env()
        
        # If no client from env, try to create from shared config
        if not llm_client:
            llm_config = params["llm_config"]
            if llm_config.get("url") or llm_config.get("api_key"):
                try:
                    # Determine provider based on config
                    if llm_config.get("url") and "apigee" in str(llm_config.get("url", "")):
                        provider = LLMProvider.APIGEE
                    elif llm_config.get("url") and "enterprise" in str(llm_config.get("url", "")):
                        provider = LLMProvider.ENTERPRISE
                    elif llm_config.get("url"):
                        provider = LLMProvider.LOCAL
                    else:
                        provider = LLMProvider.OPENAI  # Default
                    
                    config = LLMConfig(
                        provider=provider,
                        model=llm_config.get("model", "gpt-4"),
                        api_key=llm_config.get("api_key"),
                        base_url=llm_config.get("url"),
                        temperature=llm_config.get("temperature", 0.1),
                        max_tokens=llm_config.get("max_tokens", 4000),
                        timeout=LLM_TIMEOUT
                    )
                    
                    llm_client = LLMClient(config)
                    
                except Exception as e:
                    print(f"⚠️ Failed to create LLM client from config: {e}")
                    llm_client = None
        
        # If we have a working LLM client, use it with timeout protection
        if llm_client and llm_client.is_available():
            try:
                print(f"🔗 Using {llm_client.config.provider.value} LLM provider")
                print(f"   Model: {llm_client.config.model}")
                
                # Use threading with timeout to prevent hanging
                result = {"success": False, "response": "", "error": ""}
                
                def llm_call_with_timeout():
                    try:
                        response = llm_client.call_llm(params["prompt"])
                        result["success"] = True
                        result["response"] = response
                    except Exception as e:
                        result["error"] = str(e)
                
                # Start LLM call in a separate thread
                llm_thread = threading.Thread(target=llm_call_with_timeout)
                llm_thread.daemon = True
                llm_thread.start()
                
                # Wait for completion with timeout
                llm_thread.join(timeout=LLM_TIMEOUT)
                
                if llm_thread.is_alive():
                    print(f"⚠️ LLM call timed out after {LLM_TIMEOUT} seconds, using fallback")
                    result["error"] = f"LLM call timed out after {LLM_TIMEOUT} seconds"
                
                if result["success"]:
                    # Try to parse JSON response with enhanced format
                    pattern_data = self._parse_enhanced_llm_response(result["response"])
                    
                    return {
                        "success": True,
                        "pattern_data": pattern_data,
                        "source": llm_client.config.provider.value,
                        "model": llm_client.config.model,
                        "response": result["response"][:10000] + "..." if len(result["response"]) > 10000 else result["response"]
                    }
                else:
                    print(f"⚠️ LLM call failed: {result['error']}")
                    # Fall back to pattern generation
                    pass
                
            except Exception as e:
                print(f"⚠️ LLM call failed: {e}")
                # Fall back to pattern generation
                pass
        
        # Fallback to pattern generation
        print("🔄 LLM not available or failed, using fallback pattern generation")
        pattern_data = self._generate_fallback_pattern_data()
        
        return {
            "success": True,
            "pattern_data": pattern_data,
            "source": "fallback",
            "model": "built-in",
            "response": "Generated fallback patterns based on hard gate definitions"
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Store LLM response and pattern data in shared store"""
        shared["llm"]["response"] = exec_res["response"]
        shared["llm"]["pattern_data"] = exec_res["pattern_data"]
        shared["llm"]["source"] = exec_res["source"]
        shared["llm"]["model"] = exec_res["model"]
        
        # Extract patterns for backward compatibility
        patterns = {}
        for gate_name, gate_data in exec_res["pattern_data"].items():
            patterns[gate_name] = gate_data.get("patterns", [])
        shared["llm"]["patterns"] = patterns
        
        pattern_count = sum(len(gate_data.get("patterns", [])) for gate_data in exec_res["pattern_data"].values())
        print(f"✅ Generated {pattern_count} patterns for {len(exec_res['pattern_data'])} gates")
        print(f"   Source: {exec_res['source']} ({exec_res['model']})")
        
        # Log the LLM response using environment-based paths
        try:
            # Get logs directory from shared context
            logs_dir = shared.get("directories", {}).get("logs", "./logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Generate timestamp for log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_id = shared["request"].get("scan_id", "unknown")
            
            # Save LLM response to file
            response_log_file = os.path.join(logs_dir, f"llm_response_{scan_id}_{timestamp}.txt")
            with open(response_log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("CODEGATES LLM RESPONSE LOG\n")
                f.write("=" * 80 + "\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Scan ID: {scan_id}\n")
                f.write(f"Repository: {shared['request'].get('repository_url', 'unknown')}\n")
                f.write(f"Branch: {shared['request'].get('branch', 'unknown')}\n")
                f.write(f"LLM Source: {exec_res['source']}\n")
                f.write(f"LLM Model: {exec_res['model']}\n")
                f.write(f"Response Length: {len(exec_res['response'])} characters\n")
                f.write(f"Patterns Generated: {pattern_count}\n")
                f.write(f"Gates Processed: {len(exec_res['pattern_data'])}\n")
                f.write("=" * 80 + "\n\n")
                f.write("RAW LLM RESPONSE:\n")
                f.write("-" * 40 + "\n")
                f.write(exec_res["response"])
                f.write("\n\n" + "-" * 40 + "\n")
                f.write("PARSED PATTERN DATA:\n")
                f.write("-" * 40 + "\n")
                import json
                f.write(json.dumps(exec_res["pattern_data"], indent=2))
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("END OF RESPONSE\n")
                f.write("=" * 80 + "\n")
            
            print(f"📝 LLM response logged to: {response_log_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to log LLM response: {e}")
        
        return "default"
    
    def _parse_enhanced_llm_response(self, response: str) -> Dict[str, Dict[str, Any]]:
        """Parse enhanced LLM response with expected coverage and maximum files analysis"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                try:
                    data = json.loads(response)
                    return self._validate_and_enhance_json_data(data)
                except json.JSONDecodeError:
                    pass
            
            # Fallback to text parsing
            return self._extract_patterns_from_text(response)
            
        except Exception as e:
            print(f"   ⚠️ Error parsing LLM response: {e}")
            return self._generate_fallback_pattern_data()
    
    def _validate_and_enhance_json_data(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Validate and enhance JSON data with maximum files analysis"""
        enhanced_data = {}
        
        for gate_name, gate_data in data.items():
            if isinstance(gate_data, dict):
                # Extract patterns
                patterns = gate_data.get("patterns", [])
                if isinstance(patterns, list):
                    patterns = self._clean_and_validate_patterns(patterns)
                
                # Extract expected coverage with enhanced analysis
                expected_coverage = gate_data.get("expected_coverage", {})
                if isinstance(expected_coverage, dict):
                    # Add maximum files analysis
                    max_files_expected = self._calculate_max_files_expected(gate_name, expected_coverage)
                    expected_coverage["max_files_expected"] = max_files_expected
                
                # Extract other fields
                description = gate_data.get("description", "")
                significance = gate_data.get("significance", "")
                confidence = gate_data.get("confidence", "medium")
                
                enhanced_data[gate_name] = {
                    "patterns": patterns,
                    "description": description,
                    "significance": significance,
                    "expected_coverage": expected_coverage,
                    "confidence": confidence
                }
        
        return enhanced_data
    
    def _calculate_max_files_expected(self, gate_name: str, expected_coverage: Dict[str, Any]) -> int:
        """Calculate maximum number of files expected for validation based on gate type and coverage"""
        percentage = expected_coverage.get("percentage", 10)
        reasoning = expected_coverage.get("reasoning", "")
        
        # Gate-specific maximum file expectations
        gate_max_files = {
            "STRUCTURED_LOGS": 200,
            "AVOID_LOGGING_SECRETS": 100,  # Security gate - reasonable expectation
            "AUDIT_TRAIL": 100,
            "LOG_API_CALLS": 120,
            "LOG_APPLICATION_MESSAGES": 180,
            "ERROR_LOGS": 160,
            "UI_ERRORS": 80,
            "UI_ERROR_TOOLS": 60,
            "AUTOMATED_TESTS": 100,
            "INPUT_VALIDATION": 200,
            "OUTPUT_SANITIZATION": 150,
            "SQL_INJECTION_PREVENTION": 120,
            "XSS_PREVENTION": 140,
            "CSRF_PROTECTION": 80,
            "AUTHENTICATION": 100,
            "AUTHORIZATION": 120,
            "SECURE_COMMUNICATION": 60,
            "SECURE_STORAGE": 80,
            "SECURE_CONFIGURATION": 100,
            "SECURE_DEPLOYMENT": 60
        }
        
        # Get base maximum files for this gate
        base_max_files = gate_max_files.get(gate_name, 100)
        
        # Special handling for security gates
        if gate_name == "AVOID_LOGGING_SECRETS" or "security" in reasoning.lower():
            # For security gates, use a reasonable expectation regardless of percentage
            return base_max_files
        
        # Adjust based on expected coverage percentage
        if percentage == 100:
            # Infrastructure patterns - expect high coverage
            max_files = int(base_max_files * 0.8)  # 80% of base
        elif percentage >= 50:
            # High coverage expectations
            max_files = int(base_max_files * 0.6)  # 60% of base
        elif percentage >= 25:
            # Medium coverage expectations
            max_files = int(base_max_files * 0.4)  # 40% of base
        else:
            # Low coverage expectations
            max_files = int(base_max_files * 0.2)  # 20% of base
        
        # Ensure minimum of 1 file
        return max(1, max_files)
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues in LLM responses"""
        # Remove trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Fix unescaped quotes in strings
        json_str = re.sub(r'(?<!\\)"(?![,}\]])', '\\"', json_str)
        
        # Fix single quotes to double quotes
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        
        # Fix missing quotes around keys
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        return json_str
    
    def _clean_and_validate_patterns(self, patterns: List[str]) -> List[str]:
        """Clean and validate regex patterns from LLM"""
        cleaned_patterns = []
        
        for pattern in patterns:
            if not pattern or not isinstance(pattern, str):
                continue
                
            # Remove common LLM formatting artifacts
            pattern = pattern.strip()
            
            # Remove r' prefix and ' suffix if present
            if pattern.startswith("r'") and pattern.endswith("'"):
                pattern = pattern[2:-1]
            elif pattern.startswith('r"') and pattern.endswith('"'):
                pattern = pattern[2:-1]
            elif pattern.startswith("'") and pattern.endswith("'"):
                pattern = pattern[1:-1]
            elif pattern.startswith('"') and pattern.endswith('"'):
                pattern = pattern[1:-1]
            
            # Skip empty patterns
            if not pattern:
                continue
            
            # Basic validation - try to compile the regex
            try:
                re.compile(pattern)
                cleaned_patterns.append(pattern)
            except re.error as e:
                print(f"⚠️ Invalid regex pattern skipped: {pattern} - {e}")
                # Try to fix common issues
                fixed_pattern = self._fix_regex_pattern(pattern)
                if fixed_pattern:
                    try:
                        re.compile(fixed_pattern)
                        cleaned_patterns.append(fixed_pattern)
                        print(f"✅ Fixed pattern: {pattern} → {fixed_pattern}")
                    except re.error:
                        print(f"⚠️ Could not fix pattern: {pattern}")
        
        return cleaned_patterns
    
    def _fix_regex_pattern(self, pattern: str) -> str:
        """Attempt to fix common regex pattern issues"""
        # Fix unescaped dots
        pattern = re.sub(r'(?<!\\)\.(?![*+?{])', r'\\.', pattern)
        
        # Fix unescaped parentheses in contexts where they should be literal
        pattern = re.sub(r'(?<!\\)\((?![^)]*\|)', r'\\(', pattern)
        pattern = re.sub(r'(?<!\\)\)(?![*+?{])', r'\\)', pattern)
        
        # Fix missing word boundaries
        if not pattern.startswith(r'\b') and pattern.startswith(r'\w'):
            pattern = r'\b' + pattern
        
        return pattern
    
    def _extract_patterns_from_text(self, response: str) -> Dict[str, Dict[str, Any]]:
        """Extract patterns from unstructured text response"""
        pattern_data = {}
        
        # Look for gate sections in the response - improved pattern to handle various formats
        # This handles both **GATE_NAME** and ** GATE_NAME ** formats
        gate_sections = re.findall(r'\*\*\s*([A-Z_]+)\s*\*\*.*?(?=\*\*\s*[A-Z_]+\s*\*\*|\Z)', response, re.DOTALL)
        
        # If no sections found with the above pattern, try alternative patterns
        if not gate_sections:
            # Try pattern for sections that start with **GATE_NAME** followed by content
            gate_sections = re.findall(r'\*\*\s*([A-Z_]+)\s*\*\*.*?(?=\*\*\s*[A-Z_]+\s*\*\*|\Z)', response, re.DOTALL)
        
        # If still no sections, try to extract from the entire response
        if not gate_sections:
            # Look for any **GATE_NAME** patterns in the response
            gate_names = re.findall(r'\*\*\s*([A-Z_]+)\s*\*\*', response)
            for gate_name in gate_names:
                # Extract content after this gate name until the next gate or end
                pattern = rf'\*\*\s*{re.escape(gate_name)}\s*\*\*.*?(?=\*\*\s*[A-Z_]+\s*\*\*|\Z)'
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    gate_sections.append(match.group(0))
        
        # Process each gate section
        for section in gate_sections:
            lines = section.split('\n')
            gate_name = None
            
            # Extract gate name from the first line
            for line in lines:
                gate_match = re.search(r'\*\*\s*([A-Z_]+)\s*\*\*', line)
                if gate_match:
                    gate_name = gate_match.group(1)
                    break
            
            if not gate_name:
                continue
            
            # Extract patterns from the section
            patterns = []
            description = "Pattern analysis for this gate"
            significance = "Important for code quality and compliance"
            percentage = 10
            confidence = "medium"
            
            # Process each line in the section
            for line in lines[1:]:
                line = line.strip()
                
                # Look for patterns in various formats
                if line.startswith('- **patterns**:') or line.startswith('* **patterns**:'):
                    # Extract patterns from this line and following lines
                    pattern_text = line.split(':', 1)[1].strip() if ':' in line else ""
                    patterns.extend(self._extract_patterns_from_line(pattern_text))
                elif line.startswith('*   **Patterns**') or line.startswith('-   **Patterns**'):
                    # Handle the format used by the local LLM
                    pattern_text = line.split('**Patterns**', 1)[1].strip() if '**Patterns**' in line else ""
                    patterns.extend(self._extract_patterns_from_line(pattern_text))
                elif line.startswith('*   `') or line.startswith('-   `'):
                    # Handle individual pattern lines
                    pattern_text = line.strip('* - `').strip('`')
                    patterns.extend(self._extract_patterns_from_line(pattern_text))
                elif line.startswith('- **description**:') or line.startswith('* **description**:'):
                    description = line.split(':', 1)[1].strip() if ':' in line else description
                elif line.startswith('*   **Description**') or line.startswith('-   **Description**'):
                    description = line.split('**Description**', 1)[1].strip() if '**Description**' in line else description
                elif line.startswith('- **significance**:') or line.startswith('* **significance**:'):
                    significance = line.split(':', 1)[1].strip() if ':' in line else significance
                elif line.startswith('*   **Significance**') or line.startswith('-   **Significance**'):
                    significance = line.split('**Significance**', 1)[1].strip() if '**Significance**' in line else significance
                elif line.startswith('- **expected_coverage**:') or line.startswith('* **expected_coverage**:'):
                    # Try to extract percentage
                    percentage_match = re.search(r'(\d+)%', line)
                    if percentage_match:
                        percentage = int(percentage_match.group(1))
                elif '**Percentage**' in line:
                    # Try to extract percentage from the format used by local LLM
                    percentage_match = re.search(r'(\d+)', line)
                    if percentage_match:
                        percentage = int(percentage_match.group(1))
            
            # Only add if we found patterns for this specific gate
            if patterns:
                pattern_data[gate_name] = {
                    "patterns": patterns,
                    "description": description,
                    "significance": significance,
                    "expected_coverage": {
                        "percentage": percentage,
                        "reasoning": "Extracted from text analysis",
                        "confidence": confidence
                    }
                }
        
        # If no patterns found, try a more aggressive extraction
        if not pattern_data:
            # Look for any patterns in the entire response
            all_patterns = self._extract_patterns_from_line(response)
            if all_patterns:
                # Try to associate patterns with gate names
                gate_names = re.findall(r'\*\*\s*([A-Z_]+)\s*\*\*', response)
                for gate_name in gate_names:
                    pattern_data[gate_name] = {
                        "patterns": all_patterns[:3],  # Take first 3 patterns
                        "description": "Pattern analysis for this gate",
                        "significance": "Important for code quality and compliance",
                        "expected_coverage": {
                            "percentage": 10,
                            "reasoning": "Extracted from text analysis",
                            "confidence": "medium"
                        }
                    }
        
        # If still no patterns found, return fallback
        if not pattern_data:
            return self._generate_fallback_pattern_data()
        
        return pattern_data
    
    def _extract_patterns_from_line(self, line: str) -> List[str]:
        """Extract regex patterns from a line of text"""
        patterns = []
        
        # Look for patterns in various formats
        # Pattern 1: r'pattern' format
        pattern_matches = re.findall(r'r[\'"]([^\'\"]+)[\'"]', line)
        patterns.extend(pattern_matches)
        
        # Pattern 2: `pattern` format (backticks)
        pattern_matches = re.findall(r'`([^`]+)`', line)
        for match in pattern_matches:
            # Clean up the pattern - remove r' prefix if present
            if match.startswith("r'") and match.endswith("'"):
                match = match[2:-1]
            elif match.startswith('r"') and match.endswith('"'):
                match = match[2:-1]
            patterns.append(match)
        
        # Pattern 3: Look for patterns without r prefix but with quotes
        pattern_matches = re.findall(r'[\'"]([^\'\"]+)[\'"]', line)
        for match in pattern_matches:
            if match not in patterns and len(match) > 3:  # Avoid short strings
                # Skip if it looks like a description rather than a pattern
                if not any(keyword in match.lower() for keyword in ['description', 'significance', 'reasoning', 'confidence']):
                    patterns.append(match)
        
        # Pattern 4: Look for patterns that start with common regex patterns
        # This handles cases where the pattern is not properly quoted
        regex_patterns = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*\s*[=:]\s*[^\s,;]+)', line)
        for match in regex_patterns:
            if len(match) > 5 and match not in patterns:  # Avoid very short matches
                patterns.append(match)
        
        # Clean up patterns - remove duplicates and empty patterns
        cleaned_patterns = []
        for pattern in patterns:
            pattern = pattern.strip()
            if pattern and len(pattern) > 2 and pattern not in cleaned_patterns:
                # Basic validation - try to compile the regex
                try:
                    re.compile(pattern)
                    cleaned_patterns.append(pattern)
                except re.error:
                    # If it's not a valid regex, it might be a simple pattern
                    # Convert it to a simple word boundary pattern
                    simple_pattern = r'\b' + re.escape(pattern) + r'\b'
                    try:
                        re.compile(simple_pattern)
                        cleaned_patterns.append(simple_pattern)
                    except re.error:
                        # Skip invalid patterns
                        continue
        
        return cleaned_patterns
    
    def _parse_llm_response(self, response: str) -> Dict[str, List[str]]:
        """Parse LLM response to extract patterns (legacy method)"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'(\{.*?\})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse JSON
            patterns = json.loads(json_str)
            
            # Validate that all patterns are lists of strings
            validated_patterns = {}
            for gate_name, gate_patterns in patterns.items():
                if isinstance(gate_patterns, list):
                    validated_patterns[gate_name] = [str(p) for p in gate_patterns if p]
                else:
                    validated_patterns[gate_name] = [str(gate_patterns)] if gate_patterns else []
            
            return validated_patterns
            
        except Exception as e:
            print(f"⚠️ Failed to parse LLM response: {e}")
            print(f"Response preview: {response[:200]}...")
            # Return fallback patterns
            return self._generate_fallback_patterns()
    
    def _generate_fallback_pattern_data(self) -> Dict[str, Dict[str, Any]]:
        """Generate fallback pattern data when LLM fails"""
        fallback_patterns = self._generate_fallback_patterns()
        
        pattern_data = {}
        for gate_name, patterns in fallback_patterns.items():
            pattern_data[gate_name] = {
                "patterns": patterns,
                "description": f"Fallback patterns for {gate_name} - basic implementation patterns",
                "significance": "These are fallback patterns when LLM analysis is unavailable. They provide basic coverage but may not be optimized for your specific technology stack.",
                "expected_coverage": {
                    "percentage": 10,  # Conservative default
                    "reasoning": "Fallback expectation - LLM analysis unavailable for technology-specific estimation",
                    "confidence": "low"
                }
            }
        
        return pattern_data
    
    def _generate_fallback_patterns(self) -> Dict[str, List[str]]:
        """Generate fallback patterns from hard gate definitions"""
        patterns = {}
        
        for gate in HARD_GATES:
            gate_patterns = []
            
            # Use patterns from gate definition
            if "patterns" in gate:
                gate_patterns.extend(gate["patterns"].get("positive", []))
                gate_patterns.extend(gate["patterns"].get("violations", []))
            
            # Add some basic patterns if none exist
            if not gate_patterns:
                gate_name_lower = gate["name"].lower()
                gate_patterns = [gate_name_lower, gate_name_lower.replace("_", ".*")]
            
            patterns[gate["name"]] = gate_patterns
        
        return patterns


class ValidateGatesNode(Node):
    """Node to validate all gates using generated patterns (Map-Reduce)"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare validation parameters with gate applicability analysis"""
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
        from utils.gate_applicability import gate_applicability_analyzer
        
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
        
        # Check if enhanced pattern library exists for criteria-based evaluation
        enhanced_pattern_library_path = Path("patterns/enhanced_pattern_library.json")
        use_enhanced_evaluation = enhanced_pattern_library_path.exists()
        
        if use_enhanced_evaluation:
            print("   🚀 Enhanced criteria-based evaluation available - using enhanced pattern library")
        else:
            print("   ⚠️ Enhanced pattern library not found, using legacy evaluation")
        
        return {
            "repo_path": shared["repository"]["local_path"],
            "metadata": shared["repository"]["metadata"],
            "patterns": llm_patterns,
            "pattern_data": pattern_data,
            "hard_gates": shared["hard_gates"],  # Include all gates for validation
            "all_hard_gates": shared["hard_gates"],  # Keep original for reference
            "threshold": shared["request"]["threshold"],
            "shared": shared,  # Pass shared context for configuration
            "applicability_summary": applicability_summary,
            "use_enhanced_evaluation": use_enhanced_evaluation
        }
    
    def exec(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate all gates against the codebase using weighted pattern validation"""
        print("🎯 Validating gates against codebase with weighted pattern validation...")
        
        repo_path = Path(params["repo_path"])
        llm_patterns = params["patterns"]
        pattern_data = params["pattern_data"]
        metadata = params["metadata"]
        use_enhanced_evaluation = params.get("use_enhanced_evaluation", False)
        
        # Check if enhanced evaluation should be used
        if use_enhanced_evaluation:
            print("   🔧 Using enhanced criteria-based evaluation system")
            return self._evaluate_with_enhanced_system(params)
        else:
            print("   🔧 Using legacy pattern matching system")
            return self._evaluate_with_legacy_system(params)
    
    def _evaluate_with_enhanced_system(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate gates using the new criteria-based system"""
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
            
            # Check gate applicability using the applicability analyzer
            from utils.gate_applicability import gate_applicability_analyzer
            characteristics = gate_applicability_analyzer.analyze_codebase_type(metadata)
            applicability = gate_applicability_analyzer._check_gate_applicability(gate_name, characteristics)
            
            # Check if gate is not applicable
            is_not_applicable = not applicability["is_applicable"]
            
            if is_not_applicable:
                # Handle Not Applicable gate
                gate_result = {
                    "gate": gate_name,
                    "display_name": legacy_gate["display_name"],
                    "description": legacy_gate["description"],
                    "category": legacy_gate["category"],
                    "priority": legacy_gate["priority"],
                    "patterns_used": 0,
                    "matches_found": 0,
                    "score": 0.0,
                    "status": "NOT_APPLICABLE",
                    "details": [f"This gate is not applicable: {applicability['reason']}"],
                    "recommendations": [f"Not applicable to this technology stack: {applicability['reason']}"],
                    "pattern_description": f"Not applicable: {applicability['reason']}",
                    "pattern_significance": applicability["reason"],
                    "expected_coverage": {
                        "percentage": 0,
                        "reasoning": applicability["reason"],
                        "confidence": "high"
                    },
                    "total_files": metadata.get("total_files", 1),
                    "validation_sources": {
                        "llm_patterns": {"count": 0, "matches": 0, "source": "not_applicable"},
                        "static_patterns": {"count": 0, "matches": 0, "source": "not_applicable"},
                        "combined_confidence": "high"
                    }
                }
                print(f"   {gate_name} marked as NOT_APPLICABLE: {applicability['reason']}")
                gate_results.append(gate_result)
                continue
            
            # Check if enhanced gate exists
            if gate_name in enhanced_gates:
                print(f"   🔍 Evaluating {gate_name} with enhanced criteria-based system... ({i+1}/{len(legacy_gates)})")
                enhanced_gate_config = enhanced_gates[gate_name]
                
                # Special handling for ALERTING_ACTIONABLE - use database integration
                if gate_name == "ALERTING_ACTIONABLE":
                    print(f"   🔗 Using database integration for {gate_name}")
                    # Use fetch_alerting_integrations_status to determine status
                    from utils.db_integration import fetch_alerting_integrations_status
                    # Try to get app_id from params, else extract from repo URL
                    app_id = params.get('shared', {}).get('request', {}).get('app_id')
                    if not app_id:
                        repo_url = params.get('shared', {}).get('request', {}).get('repository_url', '')
                        from utils.db_integration import extract_app_id_from_url
                        app_id = extract_app_id_from_url(repo_url) or '<APP ID>'
                    print(f"   [DEBUG] Calling fetch_alerting_integrations_status for app_id={app_id}")
                    try:
                        integration_status = fetch_alerting_integrations_status(app_id)
                        print(f"   [DEBUG] Integration status: {integration_status}")
                    except Exception as ex:
                        print(f"   [ERROR] fetch_alerting_integrations_status failed: {ex}")
                        integration_status = {"Splunk": False, "AppDynamics": False, "ThousandEyes": False}
                    present = [k for k, v in integration_status.items() if v]
                    missing = [k for k, v in integration_status.items() if not v]
                    all_present = all(integration_status.values())
                    # Only include App ID in evidence/details if it is not '<APP ID>' or empty
                    app_id_str = f"; App ID: {app_id}" if app_id and app_id != '<APP ID>' else ""
                    evidence_str = f"Present: {', '.join(present) if present else 'None'}; Missing: {', '.join(missing) if missing else 'None'}{app_id_str}"
                    
                    # Create enhanced result format for ALERTING_ACTIONABLE
                    enhanced_result = {
                        "gate_name": gate_name,
                        "score": 100.0 if all_present else 0.0,
                        "status": "PASS" if all_present else "FAIL",
                        "evidence": evidence_str,
                        "details": [
                            f"Present: {', '.join(present) if present else 'None'}",
                            f"Missing: {', '.join(missing) if missing else 'None'}" + (f"; App ID: {app_id}" if app_id and app_id != '<APP ID>' else "")
                        ],
                        "recommendations": [
                            "All integrations detected and actionable" if all_present else f"Missing integrations: {', '.join(missing)}"
                        ],
                        "condition_results": [
                            {
                                "name": "database_integration",
                                "type": "database",
                                "status": "PASS" if all_present else "FAIL",
                                "weight": 1.0,
                                "details": evidence_str
                            }
                        ],
                        "coverage_score": 100.0 if all_present else 0.0,
                        "criteria_score": 100.0 if all_present else 0.0,
                        "matches_found": 1 if all_present else 0,
                        "total_files": metadata.get("total_files", 1),
                        "relevant_files": 1
                    }
                    
                    # Create legacy result directly for ALERTING_ACTIONABLE (avoid conversion issues)
                    legacy_result = {
                        "gate": gate_name,
                        "display_name": legacy_gate["display_name"],
                        "description": legacy_gate["description"],
                        "category": legacy_gate["category"],
                        "priority": legacy_gate["priority"],
                        "patterns_used": 0,
                        "matches_found": 1 if all_present else 0,
                        "matches": [],
                        "patterns": [],
                        "score": 100.0 if all_present else 0.0,
                        "status": "PASS" if all_present else "FAIL",
                        "details": [
                            f"Present: {', '.join(present) if present else 'None'}",
                            f"Missing: {', '.join(missing) if missing else 'None'}" + (f"; App ID: {app_id}" if app_id and app_id != '<APP ID>' else "")
                        ],
                        "evidence": evidence_str,
                        "recommendations": [
                            "All integrations detected and actionable" if all_present else f"Missing integrations: {', '.join(missing)}"
                        ],
                        "pattern_description": legacy_gate.get("description", "Database integration analysis"),
                        "pattern_significance": "Critical for monitoring and alerting",
                        "expected_coverage": {
                            "percentage": 100,
                            "reasoning": "All integrations should be present",
                            "confidence": "high"
                        },
                        "total_files": metadata.get("total_files", 1),
                        "relevant_files": 1,
                        "validation_sources": {
                            "llm_patterns": {"count": 0, "matches": 0, "source": "db_integration"},
                            "static_patterns": {"count": 0, "matches": 0, "source": "db_integration"},
                            "combined_confidence": "high"
                        }
                    }
                    
                    gate_results.append(legacy_result)
                    print(f"   ✅ {gate_name} evaluation complete: {legacy_result.get('status', 'UNKNOWN')} ({legacy_result.get('score', 0):.1f}%)")
                    continue
                
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
        """Evaluate gates using the legacy pattern matching system with file-centric optimization"""
        repo_path = Path(params["repo_path"])
        llm_patterns = params["patterns"]
        pattern_data = params["pattern_data"]
        metadata = params["metadata"]
        
        # Get pattern matching configuration
        config = self._get_pattern_matching_config(params.get("shared", {}))
        print(f"   📋 Pattern matching config: max_files={config['max_files']}, max_size={config['max_file_size_mb']}MB, lang_threshold={config['language_threshold_percent']}%")
        
        # Get primary technologies for pattern selection
        primary_technologies = self._get_primary_technologies(metadata)
        
        # Check gate applicability first
        applicable_gates = []
        not_applicable_results = []
        
        for gate in params["hard_gates"]:
            gate_name = gate["name"]
            
            # Check gate applicability using the applicability analyzer
            from utils.gate_applicability import gate_applicability_analyzer
            characteristics = gate_applicability_analyzer.analyze_codebase_type(metadata)
            applicability = gate_applicability_analyzer._check_gate_applicability(gate_name, characteristics)
            
            # Check if gate is not applicable
            is_not_applicable = not applicability["is_applicable"]
            
            if is_not_applicable:
                # Handle Not Applicable gate
                gate_result = {
                    "gate": gate_name,
                    "display_name": gate["display_name"],
                    "description": gate["description"],
                    "category": gate["category"],
                    "priority": gate["priority"],
                    "patterns_used": 0,
                    "matches_found": 0,
                    "score": 0.0,
                    "status": "NOT_APPLICABLE",
                    "details": [f"This gate is not applicable: {applicability['reason']}"],
                    "recommendations": [f"Not applicable to this technology stack: {applicability['reason']}"],
                    "pattern_description": f"Not applicable: {applicability['reason']}",
                    "pattern_significance": applicability["reason"],
                    "expected_coverage": {
                        "percentage": 0,
                        "reasoning": applicability["reason"],
                        "confidence": "high"
                    },
                    "total_files": metadata.get("total_files", 1),
                    "validation_sources": {
                        "llm_patterns": {"count": 0, "matches": 0, "source": "not_applicable"},
                        "static_patterns": {"count": 0, "matches": 0, "source": "not_applicable"},
                        "combined_confidence": "high"
                    }
                }
                print(f"   {gate_name} marked as NOT_APPLICABLE: {applicability['reason']}")
                not_applicable_results.append(gate_result)
            else:
                applicable_gates.append(gate)
        
        print(f"   🎯 Processing {len(applicable_gates)} applicable gates with file-centric optimization...")
        
        # Use file-centric processing for applicable gates
        gate_results = self._process_gates_file_centric(
            applicable_gates, llm_patterns, pattern_data, metadata, 
            repo_path, config, params
        )
        
        # Combine results
        all_results = not_applicable_results + gate_results
        return all_results

    def _process_gates_file_centric(self, gates: List[Dict[str, Any]], llm_patterns: Dict[str, List[str]], 
                                   pattern_data: Dict[str, Any], metadata: Dict[str, Any], 
                                   repo_path: Path, config: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process all gates using file-centric approach for maximum performance"""
        
        # Pre-compile all patterns for all gates
        gate_patterns = {}
        all_compiled_patterns = {}
        
        print(f"   🔧 Pre-compiling patterns for {len(gates)} gates...")
        
        for gate in gates:
            gate_name = gate["name"]
            patterns = llm_patterns.get(gate_name, [])
            
            # Compile patterns for this gate
            compiled_patterns = []
            for pattern in patterns:
                try:
                    compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    compiled_patterns.append((pattern, compiled_pattern))
                except re.error as e:
                    print(f"   ⚠️ Invalid regex pattern for {gate_name}: {pattern} - {e}")
            
            gate_patterns[gate_name] = patterns
            all_compiled_patterns[gate_name] = compiled_patterns
        
        # Get relevant files once (shared across all gates)
        print(f"   📁 Getting relevant files for all gates...")
        relevant_files = self._get_improved_relevant_files(metadata, file_type="Source Code", config=config)
        max_files = min(len(relevant_files), config["max_files"])
        relevant_files = relevant_files[:max_files]
        
        print(f"   📊 Processing {len(relevant_files)} files for {len(gates)} gates...")
        
        # Initialize results storage for each gate
        gate_matches = {gate["name"]: [] for gate in gates}
        gate_stats = {gate["name"]: {"files_processed": 0, "files_skipped": 0, "files_too_large": 0, "files_read_errors": 0} for gate in gates}
        
        # Process each file once, applying all gates/patterns
        max_file_size = config["max_file_size_mb"] * 1024 * 1024
        max_matches_per_file = config.get("max_matches_per_file", 50)
        
        for file_idx, file_info in enumerate(relevant_files):
            if file_idx % 10 == 0 and file_idx > 0:
                print(f"   📊 Processing file {file_idx}/{len(relevant_files)}...")
            
            file_path = repo_path / file_info["relative_path"]
            if not file_path.exists():
                for gate_name in gate_matches:
                    gate_stats[gate_name]["files_skipped"] += 1
                continue
            
            try:
                file_size = file_path.stat().st_size
                if file_size > max_file_size:
                    for gate_name in gate_matches:
                        gate_stats[gate_name]["files_too_large"] += 1
                    continue
                
                # Process this file for all gates using streaming
                file_matches = self._process_file_for_all_gates(
                    file_path, file_info, all_compiled_patterns, 
                    max_matches_per_file, gates
                )
                
                # Distribute matches to respective gates
                for gate_name, matches in file_matches.items():
                    gate_matches[gate_name].extend(matches)
                    gate_stats[gate_name]["files_processed"] += 1
                
            except Exception as e:
                for gate_name in gate_matches:
                    gate_stats[gate_name]["files_read_errors"] += 1
                continue
        
        # Generate results for each gate
        gate_results = []
        for gate in gates:
            gate_name = gate["name"]
            matches = gate_matches[gate_name]
            stats = gate_stats[gate_name]
            
            print(f"   📊 {gate_name}: {len(matches)} matches from {stats['files_processed']} files")
            
            # Process Splunk integration if applicable
            splunk_matches = []
            splunk_reference = None
            gates_with_splunk = {"STRUCTURED_LOGS", "CORRELATION_ID", "LOG_APPLICATION_MESSAGES"}
            
            if gate_name in gates_with_splunk:
                splunk_data = params.get("shared", {}).get("splunk", {})
                if splunk_data and splunk_data.get("status") == "success":
                    # Filter Splunk events for this gate
                    gate_patterns_list = gate_patterns[gate_name]
                    filtered_events = []
                    for event in splunk_data.get("results", []):
                        match_text = event.get("_raw") or event.get("message") or str(event)
                        for pattern in gate_patterns_list:
                            try:
                                if re.search(pattern, match_text, re.IGNORECASE):
                                    file_hint = event.get("source") or event.get("host") or "SplunkEvent"
                                    line_hint = event.get("line") or 0
                                    language_hint = event.get("sourcetype") or "Splunk"
                                    filtered_events.append({
                                        "file": file_hint,
                                        "pattern": pattern,
                                        "match": match_text,
                                        "line": line_hint,
                                        "language": language_hint,
                                        "source": "Splunk"
                                    })
                                    break
                            except Exception:
                                continue
                    splunk_matches = filtered_events
                    if splunk_matches:
                        splunk_reference = {
                            "query": splunk_data.get("query", ""),
                            "job_id": splunk_data.get("job_id", ""),
                            "message": splunk_data.get("message", "")
                        }
            
            # Combine file matches with Splunk matches
            all_matches = matches + splunk_matches
            
            # Calculate gate score and generate result
            gate_result = self._evaluate_single_gate_legacy(gate, {
                **params,
                "matches": all_matches,
                "splunk_reference": splunk_reference,
                "stats": stats
            })
            
            gate_results.append(gate_result)
        
        return gate_results

    def _process_file_for_all_gates(self, file_path: Path, file_info: Dict[str, Any], 
                                   all_compiled_patterns: Dict[str, List[tuple]], 
                                   max_matches_per_file: int, gates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process a single file for all gates using streaming"""
        
        file_matches = {gate["name"]: [] for gate in gates}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Check if any gate has reached its match limit
                    all_gates_at_limit = all(
                        len(file_matches[gate["name"]]) >= max_matches_per_file 
                        for gate in gates
                    )
                    if all_gates_at_limit:
                        break
                    
                    # Apply all patterns for all gates to this line
                    for gate in gates:
                        gate_name = gate["name"]
                        
                        # Skip if this gate has reached its match limit
                        if len(file_matches[gate_name]) >= max_matches_per_file:
                            continue
                        
                        # Apply patterns for this gate
                        compiled_patterns = all_compiled_patterns[gate_name]
                        for pattern, compiled_pattern in compiled_patterns:
                            if len(file_matches[gate_name]) >= max_matches_per_file:
                                break
                            
                            try:
                                if compiled_pattern.search(line):
                                    file_matches[gate_name].append({
                                        "file": file_info["relative_path"],
                                        "pattern": pattern,
                                        "match": line.strip(),
                                        "line": line_num,
                                        "language": file_info["language"],
                                        "source": "file_centric"
                                    })
                            except Exception:
                                continue
        except Exception:
            # File read error - return empty matches for all gates
            pass
        
        return file_matches
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: List[Dict[str, Any]]) -> str:
        """Store validation results and calculate overall weighted score with enhanced statistics"""
        shared["validation"]["gate_results"] = exec_res
        
        # Store applicability information
        applicability_summary = prep_res.get("applicability_summary", {})
        shared["validation"]["applicability_summary"] = applicability_summary
        
        # Recalculate applicability summary from actual gate results for consistency
        total_gates = len(exec_res)
        applicable_gates = len([r for r in exec_res if r["status"] != "NOT_APPLICABLE"])
        non_applicable_gates = len([r for r in exec_res if r["status"] == "NOT_APPLICABLE"])
        
        # Get codebase characteristics from metadata
        metadata = shared["repository"]["metadata"]
        from utils.gate_applicability import gate_applicability_analyzer
        characteristics = gate_applicability_analyzer.analyze_codebase_type(metadata)
        
        # Create consistent applicability summary
        applicability_summary = {
            "codebase_characteristics": characteristics,
            "total_gates": total_gates,
            "applicable_gates": applicable_gates,
            "non_applicable_gates": non_applicable_gates,
            "applicable_gate_names": [r["gate"] for r in exec_res if r["status"] != "NOT_APPLICABLE"],
            "non_applicable_details": [
                {
                    "name": r["gate"],
                    "display_name": r["display_name"],
                    "category": r["category"],
                    "reason": "Not applicable to this technology stack"
                }
                for r in exec_res if r["status"] == "NOT_APPLICABLE"
            ]
        }
        
        shared["validation"]["applicability_summary"] = applicability_summary
        
        # Calculate overall weighted score (Reduce phase) - exclude NOT_APPLICABLE gates
        applicable_gates = [result for result in exec_res if result["status"] != "NOT_APPLICABLE"]
        
        if applicable_gates:
            # Simple weighted scoring calculation
            total_score = 0.0
            total_weight = 0.0
            
            for gate in applicable_gates:
                score = gate.get("score", 0.0)
                weight = gate.get("weight", 1.0)
                total_score += score * weight
                total_weight += weight
            
            overall_score = total_score / total_weight if total_weight > 0 else 0.0
            
            scoring_summary = {
                "total_weight": total_weight,
                "weighted_score": total_score,
                "average_score": overall_score
            }
            
            shared["validation"]["overall_score"] = overall_score
            shared["validation"]["weighted_scoring_summary"] = scoring_summary
        else:
            overall_score = 0.0
            shared["validation"]["overall_score"] = overall_score
            shared["validation"]["weighted_scoring_summary"] = {}
        
        # Count status distribution
        passed = len([r for r in exec_res if r["status"] == "PASS"])
        failed = len([r for r in exec_res if r["status"] == "FAIL"])
        warnings = len([r for r in exec_res if r["status"] == "WARNING"])
        not_applicable = len([r for r in exec_res if r["status"] == "NOT_APPLICABLE"])
        
        # Calculate hybrid validation statistics
        hybrid_stats = self._calculate_hybrid_validation_stats(exec_res)
        shared["validation"]["hybrid_stats"] = hybrid_stats
        
        # Add simple pattern statistics
        pattern_stats = {
            "total_patterns": sum(len(gate.get("patterns", [])) for gate in applicable_gates),
            "total_matches": sum(gate.get("matches_found", 0) for gate in applicable_gates),
            "average_patterns_per_gate": sum(len(gate.get("patterns", [])) for gate in applicable_gates) / len(applicable_gates) if applicable_gates else 0
        }
        shared["validation"]["pattern_statistics"] = pattern_stats
        
        print(f"✅ Enhanced validation complete: {overall_score:.1f}% overall (based on {len(applicable_gates)} applicable gates)")
        print(f"   Passed: {passed}, Failed: {failed}, Warnings: {warnings}, Not Applicable: {not_applicable}")
        print(f"   Pattern Sources: Enhanced criteria-based evaluation")
        print(f"   Total Gate Weight: {scoring_summary.get('total_weight', 0):.1f}")
        
        # Print applicability summary
        print(f"🔍 Applicability Summary:")
        print(f"   📊 Codebase Type: {characteristics['primary_technology']}")
        print(f"   ✅ Applicable Gates: {applicable_gates}/{total_gates}")
        print(f"   ❌ Not Applicable Gates: {non_applicable_gates}")
        
        return "default"
    
    def _calculate_hybrid_validation_stats(self, gate_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for enhanced validation"""
        stats = {
            "total_enhanced_patterns": 0,
            "total_enhanced_matches": 0,
            "total_criteria_evaluations": 0,
            "total_condition_results": 0,
            "coverage_improvement": 0.0,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        applicable_gates = [g for g in gate_results if g["status"] != "NOT_APPLICABLE"]
        
        for gate in applicable_gates:
            # Count enhanced evaluation results
            condition_results = gate.get("condition_results", [])
            matches = gate.get("matches", [])
            
            stats["total_criteria_evaluations"] += 1
            stats["total_condition_results"] += len(condition_results)
            stats["total_enhanced_matches"] += len(matches)
            
            # Count patterns from condition results
            for condition in condition_results:
                if condition.get("type") == "pattern":
                    stats["total_enhanced_patterns"] += 1
            
            # Determine confidence based on score
            score = gate.get("score", 0.0)
            if score >= 80:
                stats["confidence_distribution"]["high"] += 1
            elif score >= 50:
                stats["confidence_distribution"]["medium"] += 1
            else:
                stats["confidence_distribution"]["low"] += 1
        
        # Calculate coverage improvement (simplified)
        if stats["total_enhanced_matches"] > 0:
            stats["coverage_improvement"] = 15.0  # Assume 15% improvement from enhanced evaluation
        
        return stats
    
    def _find_pattern_matches_with_config(self, repo_path: Path, patterns: List[str], metadata: Dict[str, Any], gate: Dict[str, Any], config: Dict[str, Any], source: str = "LLM") -> List[Dict[str, Any]]:
        """Find pattern matches in appropriate files with streaming processing for improved performance"""
        matches = []
        # Add timeout protection for file processing
        import time
        import threading
        # Timeout configuration for file processing
        FILE_PROCESSING_TIMEOUT = int(os.getenv("CODEGATES_FILE_PROCESSING_TIMEOUT", "300"))  # 5 minutes default
        print(f"   ⏱️ File processing timeout set to {FILE_PROCESSING_TIMEOUT} seconds")
        
        # Filter files based on gate type with improved logic
        gate_name = gate.get("name", "")
        if gate_name == "AUTOMATED_TESTS":
            # For automated tests gate, look at test files across all languages
            target_files = self._get_improved_relevant_files(metadata, file_type="Test Code", gate_name=gate_name, config=config)
            print(f"   Looking at {len(target_files)} relevant test files for {gate_name}")
        else:
            # For all other gates, look at source code files with more inclusive filtering
            target_files = self._get_improved_relevant_files(metadata, file_type="Source Code", gate_name=gate_name, config=config)
            print(f"   Looking at {len(target_files)} relevant source code files for {gate_name}")
        
        # Pre-compile patterns for efficiency (fix pattern recompilation issue)
        compiled_patterns = []
        invalid_patterns = []
        for pattern in patterns:
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                compiled_patterns.append((pattern, compiled_pattern))
            except re.error as e:
                invalid_patterns.append((pattern, str(e)))
                print(f"   ⚠️ Invalid regex pattern skipped: {pattern} - {e}")
        
        # Report pattern compilation results
        if invalid_patterns:
            print(f"   ⚠️ Skipped {len(invalid_patterns)} invalid patterns out of {len(patterns)} total")
        
        # Process files with improved limits and error handling
        files_processed = 0
        files_skipped = 0
        files_too_large = 0
        files_read_errors = 0
        
        # Configurable limits with performance optimizations
        max_files = min(len(target_files), config["max_files"])
        max_file_size = config["max_file_size_mb"] * 1024 * 1024  # Convert MB to bytes
        max_matches_per_file = config.get("max_matches_per_file", 50)  # New limit for matches per file
        
        # Use threading with timeout to prevent hanging
        processing_result = {
            "matches": [],
            "files_processed": 0,
            "files_skipped": 0,
            "files_too_large": 0,
            "files_read_errors": 0,
            "error": None
        }
        
        def process_files_with_timeout():
            try:
                local_matches = []
                local_files_processed = 0
                local_files_skipped = 0
                local_files_too_large = 0
                local_files_read_errors = 0
                
                for i, file_info in enumerate(target_files[:max_files]):
                    # Add progress logging every 10 files
                    if i % 10 == 0 and i > 0:
                        actual_files_to_process = min(len(target_files), max_files)
                        print(f"   📊 Processing file {i}/{actual_files_to_process} for {gate_name}...")
                    
                    file_path = repo_path / file_info["relative_path"]
                    if not file_path.exists():
                        local_files_skipped += 1
                        continue
                    
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > max_file_size:
                            local_files_too_large += 1
                            if config.get("enable_detailed_logging", True):
                                print(f"   ⚠️ Skipping large file ({file_size/1024/1024:.1f}MB): {file_info['relative_path']}")
                            continue
                        
                        # Use streaming processing instead of loading entire file
                        file_matches = self._process_file_streaming(
                            file_path, 
                            compiled_patterns, 
                            file_info, 
                            source, 
                            max_matches_per_file
                        )
                        local_matches.extend(file_matches)
                        local_files_processed += 1
                        
                        # Early termination if we have enough matches
                        if len(local_matches) >= max_matches_per_file * 10:  # 10x files worth of matches
                            print(f"   ✅ Early termination: Found sufficient matches for {gate_name}")
                            break
                            
                    except Exception as e:
                        local_files_read_errors += 1
                        if config.get("enable_detailed_logging", True):
                            print(f"   ⚠️ Error reading file {file_info['relative_path']}: {e}")
                        continue
                
                # Update result
                processing_result["matches"] = local_matches
                processing_result["files_processed"] = local_files_processed
                processing_result["files_skipped"] = local_files_skipped
                processing_result["files_too_large"] = local_files_too_large
                processing_result["files_read_errors"] = local_files_read_errors
            except Exception as e:
                processing_result["error"] = str(e)
        
        # Start file processing in a separate thread
        processing_thread = threading.Thread(target=process_files_with_timeout)
        processing_thread.daemon = True
        processing_thread.start()
        
        # Wait for completion with timeout
        processing_thread.join(timeout=FILE_PROCESSING_TIMEOUT)
        if processing_thread.is_alive():
            print(f"   ⚠️ File processing timed out after {FILE_PROCESSING_TIMEOUT} seconds for {gate_name}")
            processing_result["error"] = f"File processing timed out after {FILE_PROCESSING_TIMEOUT} seconds"
        
        if processing_result["error"]:
            print(f"   ⚠️ File processing failed for {gate_name}: {processing_result['error']}")
            return []
        
        # Report processing statistics
        if config.get("enable_detailed_logging", True):
            actual_files_to_process = min(len(target_files), max_files)
            print(f"   📊 File processing stats for {gate_name}: {processing_result['files_processed']} processed, {processing_result['files_skipped']} skipped, {processing_result['files_too_large']} too large, {processing_result['files_read_errors']} read errors (out of {actual_files_to_process} eligible files)")
            print(f"   🎯 Found {len(processing_result['matches'])} matches using streaming processing")
        
        if len(target_files) > max_files:
            print(f"   ⚠️ File limit reached: processed {max_files} out of {len(target_files)} eligible files for {gate_name}")
        
        return processing_result["matches"]
    
    def _process_file_streaming(self, file_path: Path, compiled_patterns: List[tuple], file_info: Dict[str, Any], source: str, max_matches_per_file: int = 50) -> List[Dict[str, Any]]:
        """Process a single file using streaming to avoid loading entire content into memory"""
        matches = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Check if we've reached the match limit
                    if len(matches) >= max_matches_per_file:
                        break
                    
                    # Apply all patterns to this line
                    for pattern, compiled_pattern in compiled_patterns:
                        if len(matches) >= max_matches_per_file:
                            break
                        
                        try:
                            # Use search() instead of finditer() for single line
                            if compiled_pattern.search(line):
                                matches.append({
                                    "file": file_info["relative_path"],
                                    "pattern": pattern,
                                    "match": line.strip(),
                                    "line": line_num,
                                    "language": file_info["language"],
                                    "source": source
                                })
                        except Exception as e:
                            # Skip problematic patterns
                            continue
        except Exception as e:
            # File read error - return empty matches
            pass
        
        return matches
    
    def _get_technology_relevant_files(self, metadata: Dict[str, Any], file_type: str = "Source Code") -> List[Dict[str, Any]]:
        """Get files that are relevant to the primary technology stack"""
        all_files = [f for f in metadata.get("file_list", []) 
                    if f["type"] == file_type and not f["is_binary"]]
        
        # Additional filter to exclude documentation files
        doc_extensions = ['.md', '.txt', '.rst', '.adoc', '.asciidoc', '.doc', '.docx', '.pdf', '.rtf']
        doc_patterns = ['README', 'CHANGELOG', 'LICENSE', 'CONTRIBUTING', 'CONTRIBUTE']
        
        def is_doc_file(file_info):
            file_name = file_info.get("name", "").upper()
            file_ext = file_info.get("extension", "").lower()
            
            # Check for documentation extensions
            if file_ext in doc_extensions:
                return True
            
            # Check for documentation file names
            if any(pattern in file_name for pattern in doc_patterns):
                return True
            
            return False
        
        # Filter out documentation files
        relevant_files = [f for f in all_files if not is_doc_file(f)]
        
        # Determine primary technologies from language distribution
        primary_technologies = self._get_primary_technologies(metadata)
        
        if not primary_technologies:
            # Fallback to all files if no primary technology detected
            print(f"   No primary technology detected, using all {len(relevant_files)} {file_type.lower()} files")
            return relevant_files
        
        # Filter files to only include primary technology files
        technology_relevant_files = [f for f in relevant_files 
                                   if f["language"] in primary_technologies]
        
        primary_tech_str = ", ".join(primary_technologies)
        print(f"   Primary technologies: {primary_tech_str}")
        print(f"   Filtered to {len(technology_relevant_files)} relevant files (from {len(relevant_files)} total {file_type.lower()} files)")
        
        return technology_relevant_files
    
    def _get_primary_technologies(self, metadata: Dict[str, Any]) -> List[str]:
        """Get primary technologies from metadata"""
        language_stats = metadata.get("language_stats", {})
        total_files = metadata.get("total_files", 1)
        
        # Use hardcoded defaults since pattern_loader is removed
        primary_languages = set(["java", "python", "javascript", "typescript", "csharp", "go", "rust"])
        primary_threshold = 20.0
        secondary_threshold = 10.0
        
        primary_technologies = []
        
        # Find languages that make up significant portion of the codebase
        for language, stats in language_stats.items():
            file_count = stats.get("files", 0)
            percentage = (file_count / total_files) * 100
            
            if language in primary_languages and percentage >= primary_threshold:
                primary_technologies.append(language)
        
        # If no primary technology found, take the most dominant
        if not primary_technologies:
            dominant_primary = None
            max_percentage = 0
            
            for language, stats in language_stats.items():
                if language in primary_languages:
                    file_count = stats.get("files", 0)
                    percentage = (file_count / total_files) * 100
                    if percentage > max_percentage and percentage >= secondary_threshold:
                        max_percentage = percentage
                        dominant_primary = language
            
            if dominant_primary:
                primary_technologies.append(dominant_primary)
        
        return primary_technologies
    
    def _calculate_gate_score(self, gate: Dict[str, Any], matches: List[Dict[str, Any]], metadata: Dict[str, Any]) -> float:
        """
        Simplified scoring: score = min(actual / expected, 1.0) * 100
        """
        gate_name = gate["name"]
        primary_technologies = metadata.get("primary_technologies", [])
        expected = self._get_min_expected_implementation(gate_name, primary_technologies)
        actual = len(set(m["file"] for m in matches)) if matches else 0
        if expected == 0:
            return 0.0
        score = min(actual / expected, 1.0) * 100
        return score

    def _determine_status(self, score: float, gate: Dict[str, Any]) -> str:
        """
        Determine gate status based on score and gate configuration
        Uses hardcoded defaults since pattern_loader is removed
        """
        # Use hardcoded defaults since pattern_loader is removed
        security_pass_threshold = 100.0
        pass_threshold = 20.0
        
        # Get gate-specific scoring config
        scoring_config = gate.get("scoring", {})
        is_security_gate = scoring_config.get("is_security_gate", False) or gate.get("name") == "AVOID_LOGGING_SECRETS"
        
        if is_security_gate:
            # Security gates need 100% score to pass
            return "PASS" if score >= security_pass_threshold else "FAIL"
        else:
            # Regular gates use configurable threshold
            return "PASS" if score >= pass_threshold else "FAIL"
    
    def _generate_gate_details(self, gate: Dict[str, Any], matches: List[Dict[str, Any]]) -> List[str]:
        """Generate details for gate result including expected coverage analysis"""
        details = []
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        confidence = expected_coverage.get("confidence", "medium")
        max_files_expected = expected_coverage.get("max_files_expected", gate.get("relevant_files", 1))
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        files_with_matches = len(set(m['file'] for m in matches)) if matches else 0
        scoring_config = gate.get("scoring", {})
        is_security_gate = scoring_config.get("is_security_gate", False) or gate["name"] == "AVOID_LOGGING_SECRETS"
        
        # Check for enhanced data with violation matches
        enhanced_data = gate.get("enhanced_data", {})
        violation_matches = enhanced_data.get("violation_matches", [])
        
        # Use violation_matches for security gates if available
        if is_security_gate and violation_matches:
            actual_matches = violation_matches
            files_with_violations = len(set(m.file for m in violation_matches)) if violation_matches else 0
        else:
            actual_matches = matches
            files_with_violations = files_with_matches
        
        if is_security_gate:
            if len(actual_matches) == 0:
                details.append(f"✅ No security violations found - perfect implementation")
            else:
                details.append(f"❌ Security violations found - immediate attention required")
        actual_percentage = (files_with_matches / max_files_expected) * 100 if max_files_expected > 0 else 0
        if expected_percentage == 100:
            details.append(f"🎯 Infrastructure Framework Analysis:")
            details.append(f"Expected Coverage: 100% ({coverage_reasoning})")
            if files_with_matches > 0:
                details.append(f"✅ Framework Detected & Implemented: {files_with_matches}/{max_files_expected} expected files")
                details.append(f"Framework: {coverage_reasoning}")
            else:
                details.append(f"⚠️ Framework Detected but Not Implemented: 0/{max_files_expected} expected files")
                details.append(f"Framework: {coverage_reasoning}")
                details.append(f"Recommendation: Implement the detected framework throughout your codebase")
        else:
            details.append(f"Expected Coverage: {expected_percentage}% ({coverage_reasoning})")
            details.append(f"Maximum Files Expected: {max_files_expected} files")
            traditional_coverage = (files_with_matches / relevant_files) * 100 if relevant_files > 0 else 0
        if relevant_files != total_files:
            details.append(f"Technology Filter: Using {relevant_files} relevant files (from {total_files} total files)")
        details.append(f"Confidence: {confidence}")
        if actual_matches:
            if is_security_gate:
                details.append(f"Found {len(actual_matches)} security violations across {files_with_violations} files")
            else:
                details.append(f"Found {len(actual_matches)} matches across {files_with_matches} files")
            # Show first few matches
            for match in actual_matches[:3]:
                if hasattr(match, 'file'):  # Enhanced match object
                    details.append(f"  {match.file}:{match.line_number or 0} - {match.context or match.pattern}")
                else:  # Legacy match object
                    details.append(f"  {match['file']}:{match['line']} - {match['match'][:50]}")
            if len(actual_matches) > 3:
                details.append(f"  ... and {len(actual_matches) - 3} more matches")
        else:
            if is_security_gate:
                details.append(f"No security violations found for {gate['display_name']}")
            else:
                details.append(f"No matches found for {gate['display_name']}")
        return details
    
    def _generate_gate_recommendations(self, gate: Dict[str, Any], matches: List[Dict[str, Any]], score: float) -> List[str]:
        """Generate recommendations for gate based on expected coverage analysis with maximum files context"""
        recommendations = []
        
        # Get expected coverage information
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        confidence = expected_coverage.get("confidence", "medium")
        max_files_expected = expected_coverage.get("max_files_expected", gate.get("relevant_files", 1))
        
        # Calculate actual coverage using maximum files expected
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        files_with_matches = len(set(m['file'] for m in matches)) if matches else 0
        
        # Check if this is a security gate
        scoring_config = gate.get("scoring", {})
        is_security_gate = scoring_config.get("is_security_gate", False) or gate["name"] == "AVOID_LOGGING_SECRETS"
        
        # Check for enhanced data with violation matches
        enhanced_data = gate.get("enhanced_data", {})
        violation_matches = enhanced_data.get("violation_matches", [])
        
        # Use violation_matches for security gates if available
        if is_security_gate and violation_matches:
            actual_matches = violation_matches
            files_with_violations = len(set(m.file for m in violation_matches)) if violation_matches else 0
        else:
            actual_matches = matches
            files_with_violations = files_with_matches
        
        if is_security_gate:
            # For security gates, focus on violations rather than coverage
            if len(actual_matches) == 0:
                recommendations.append(f"✅ {gate['display_name']} is well implemented")
                recommendations.append(f"No security violations found - perfect implementation")
            else:
                recommendations.append(f"❌ Critical: {gate['display_name']} violations found")
                recommendations.append(f"Found {len(actual_matches)} security violations across {files_with_violations} files")
                recommendations.append(f"Immediate action required: {coverage_reasoning}")
                
                # Provide specific guidance based on violation count
                if len(actual_matches) > 100:
                    recommendations.append(f"Major Security Issue: {len(actual_matches)} violations require immediate remediation")
                elif len(actual_matches) > 50:
                    recommendations.append(f"Significant Security Issue: {len(actual_matches)} violations need urgent attention")
                elif len(actual_matches) > 10:
                    recommendations.append(f"Security Issue: {len(actual_matches)} violations should be addressed")
                else:
                    recommendations.append(f"Minor Security Issue: {len(actual_matches)} violations to fix")
        else:
            # Calculate coverage using maximum files expected for more accurate assessment
            actual_percentage = (files_with_matches / max_files_expected) * 100 if max_files_expected > 0 else 0
            
            # Calculate coverage gap for all cases
            coverage_gap = expected_percentage - actual_percentage
            
            # Special recommendations for infrastructure patterns
            if expected_percentage == 100:
                if files_with_matches > 0:
                    recommendations.append(f"✅ Infrastructure Framework Implemented: {coverage_reasoning}")
                    recommendations.append(f"Current Usage: {files_with_matches}/{max_files_expected} expected files ({actual_percentage:.1f}%)")
                    if actual_percentage < 50:
                        recommendations.append(f"Recommendation: Extend {gate['display_name']} implementation to more files")
                    else:
                        recommendations.append(f"Recommendation: {gate['display_name']} is well implemented")
                else:
                    recommendations.append(f"🎯 Infrastructure Framework Detected: {coverage_reasoning}")
                    recommendations.append(f"Critical: Implement {gate['display_name']} throughout your codebase")
                    recommendations.append(f"Framework: {coverage_reasoning}")
                    recommendations.append(f"Expected Implementation: {max_files_expected} files")
            else:
                # Generate recommendations based on coverage gap with maximum files context
                if score < 50.0:
                    recommendations.append(f"Critical: Implement {gate['display_name']} throughout your codebase")
                    recommendations.append(f"Expected {expected_percentage}% coverage, currently at {actual_percentage:.1f}% (based on {max_files_expected} expected files)")
                    recommendations.append(f"Focus on {gate['description'].lower()}")
                    
                    # Provide specific guidance based on coverage gap
                    if coverage_gap > 50:
                        recommendations.append(f"Major Gap: Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                    elif coverage_gap > 25:
                        recommendations.append(f"Significant Gap: Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                    else:
                        recommendations.append(f"Moderate Gap: Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                elif score < 70.0:
                    recommendations.append(f"Improve: Enhance {gate['display_name']} implementation")
                    recommendations.append(f"Current: {actual_percentage:.1f}% coverage, Target: {expected_percentage}% coverage")
                    recommendations.append(f"Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                else:
                    recommendations.append(f"Good: {gate['display_name']} is well implemented")
                    recommendations.append(f"Achieved: {actual_percentage:.1f}% coverage (Target: {expected_percentage}%)")
                    
                    if actual_percentage > expected_percentage:
                        recommendations.append(f"Exceeds expectations by {actual_percentage - expected_percentage:.1f}%")
        
        # Add context about maximum files expected
        if max_files_expected != relevant_files:
            recommendations.append(f"Note: Analysis based on {max_files_expected} expected files (from {relevant_files} relevant files)")
        
        return recommendations
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches based on file and line"""
        seen = set()
        unique_matches = []
        for match in matches:
            key = (match["file"], match["line"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        return unique_matches
    
    def _calculate_combined_confidence(self, llm_matches: int, static_matches: int, unique_matches: int) -> str:
        """Calculate combined confidence based on LLM, static, and unique matches"""
        total_matches = llm_matches + static_matches + unique_matches
        if total_matches == 0:
            return "low"
        elif llm_matches > 0 and static_matches > 0 and unique_matches > 0:
            return "high"
        elif llm_matches > 0 or static_matches > 0 or unique_matches > 0:
            return "medium"
        else:
            return "low"

    def _get_pattern_matching_config(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Get configurable pattern matching parameters with streaming optimizations"""
        # Default configuration with performance optimizations
        default_config = {
            "max_files": 100,  # Reduced from 500 for better performance
            "max_file_size_mb": 2,  # Reduced from 5 for better performance
            "max_matches_per_file": 50,  # New limit for matches per file
            "language_threshold_percent": 5.0,
            "config_threshold_percent": 1.0,
            "min_languages": 1,
            "enable_detailed_logging": True,
            "skip_binary_files": True,
            "process_large_files": False,
            # New streaming performance settings
            "enable_streaming": True,
            "enable_early_termination": True,
            "max_matches_before_termination": 500,  # Stop processing after 500 total matches
            "chunk_size_kb": 64,  # For future chunked processing
        }
        
        # Override with request-specific config if available
        request_config = shared.get("request", {}).get("pattern_matching", {})
        config = {**default_config, **request_config}
        
        # Validate configuration
        config["max_files"] = max(50, min(config["max_files"], 2000))  # Between 50-2000
        config["max_file_size_mb"] = max(1, min(config["max_file_size_mb"], 50))  # Between 1-50 MB
        config["max_matches_per_file"] = max(10, min(config["max_matches_per_file"], 200))  # Between 10-200
        config["language_threshold_percent"] = max(0.5, min(config["language_threshold_percent"], 50.0))  # Between 0.5-50%
        
        return config

    def _get_improved_relevant_files(self, metadata: Dict[str, Any], file_type: str = "Source Code", gate_name: str = "", config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get files that are relevant with improved, less aggressive filtering"""
        all_files = [f for f in metadata.get("file_list", []) 
                    if f["type"] == file_type and not f["is_binary"]]
        
        # Additional filter to exclude documentation files
        doc_extensions = ['.md', '.txt', '.rst', '.adoc', '.asciidoc', '.doc', '.docx', '.pdf', '.rtf']
        doc_patterns = ['README', 'CHANGELOG', 'LICENSE', 'CONTRIBUTING', 'CONTRIBUTE']
        
        def is_doc_file(file_info):
            file_name = file_info.get("name", "").upper()
            file_ext = file_info.get("extension", "").lower()
            
            # Check for documentation extensions
            if file_ext in doc_extensions:
                return True
            
            # Check for documentation file names
            if any(pattern in file_name for pattern in doc_patterns):
                return True
            
            return False
        
        # Filter out documentation files
        relevant_files = [f for f in all_files if not is_doc_file(f)]
        
        # Use hardcoded defaults since pattern_loader is removed
        file_config = {
            "language_threshold_percent": 5.0,
            "config_threshold_percent": 2.0,
            "min_languages": 1,
            "test_threshold_multiplier": 0.8,
            "min_test_threshold": 5.0
        }
        
        tech_config = {
            "primary_languages": ["java", "python", "javascript", "typescript", "csharp", "go", "rust"],
            "config_languages": ["yaml", "json", "xml", "properties", "toml", "ini"],
            "web_languages": ["html", "css", "scss", "sass", "less"],
            "script_languages": ["bash", "sh", "ps1", "bat", "cmd"]
        }
        
        # Use global config defaults if none provided
        if config is None:
            config = {
                "language_threshold_percent": file_config.get("language_threshold_percent", 5.0),
                "config_threshold_percent": file_config.get("config_threshold_percent", 2.0),
                "min_languages": file_config.get("min_languages", 1),
                "test_threshold_multiplier": file_config.get("test_threshold_multiplier", 0.8),
                "min_test_threshold": file_config.get("min_test_threshold", 5.0)
            }
        
        # Get language statistics for intelligent filtering
        language_stats = metadata.get("language_stats", {})
        total_files = sum(stats.get("files", 0) for stats in language_stats.values())
        
        if not language_stats or total_files == 0:
            print(f"   No language statistics available, using all {len(all_files)} {file_type.lower()} files")
            return all_files
        
        # Get technology categories from global config
        primary_languages = set(tech_config.get("primary_languages", ["java", "python", "javascript", "typescript", "csharp", "go", "rust"]))
        config_languages = set(tech_config.get("config_languages", ["yaml", "json", "xml", "properties", "toml", "ini"]))
        web_languages = set(tech_config.get("web_languages", ["html", "css", "scss", "sass", "less"]))
        script_languages = set(tech_config.get("script_languages", ["bash", "sh", "ps1", "bat", "cmd"]))
        
        # Calculate language percentages
        language_percentages = {}
        for language, stats in language_stats.items():
            file_count = stats.get("files", 0)
            percentage = (file_count / total_files) * 100
            language_percentages[language] = percentage
        
        # Determine relevant languages based on gate type and configurable thresholds
        relevant_languages = set()
        
        # Get configurable thresholds
        primary_threshold = config["language_threshold_percent"]
        config_threshold = config["config_threshold_percent"]
        
        # Gate-specific logic for better relevance
        if gate_name in ["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS", "AUDIT_TRAIL", "LOG_API_CALLS", "LOG_APPLICATION_MESSAGES", "ERROR_LOGS"]:
            # Logging-related gates: include primary languages + config files
            for language, percentage in language_percentages.items():
                if language in primary_languages and percentage >= primary_threshold:
                    relevant_languages.add(language)
                elif language in config_languages and percentage >= config_threshold:
                    relevant_languages.add(language)
        elif gate_name in ["UI_ERRORS", "UI_ERROR_TOOLS"]:
            # UI-related gates: include web languages + primary languages
            for language, percentage in language_percentages.items():
                if language in web_languages and percentage >= config_threshold:
                    relevant_languages.add(language)
                elif language in primary_languages and percentage >= primary_threshold:
                    relevant_languages.add(language)
        elif gate_name == "AUTOMATED_TESTS":
            # Test-related gates: include all primary languages with lower threshold
            test_threshold = max(primary_threshold * config.get("test_threshold_multiplier", 0.8), config.get("min_test_threshold", 5.0))
            for language, percentage in language_percentages.items():
                if language in primary_languages and percentage >= test_threshold:
                    relevant_languages.add(language)
        else:
            # Other gates: include primary languages with configurable threshold
            for language, percentage in language_percentages.items():
                if language in primary_languages and percentage >= primary_threshold:
                    relevant_languages.add(language)
                elif language in script_languages and percentage >= config_threshold * 2:
                    relevant_languages.add(language)
        
        # If no languages meet the threshold, include the most dominant ones
        if not relevant_languages:
            sorted_languages = sorted(language_percentages.items(), key=lambda x: x[1], reverse=True)
            
            # Include top languages or languages with >2% representation
            min_languages = config.get("min_languages", 1)
            for language, percentage in sorted_languages[:max(min_languages, 3)]:
                if language in primary_languages or percentage >= 2.0:
                    relevant_languages.add(language)
        
        # Always include the dominant language if it's a primary language
        if language_percentages:
            dominant_language = max(language_percentages.items(), key=lambda x: x[1])[0]
            if dominant_language in primary_languages:
                relevant_languages.add(dominant_language)
        
        # Filter files to include relevant languages
        if relevant_languages:
            relevant_files = [f for f in all_files 
                             if f["language"] in relevant_languages]
        else:
            # Fallback: use all files if no relevant languages found
            relevant_files = all_files
        
        # Sort files by relevance (prioritize larger files and common patterns)
        relevant_files.sort(key=lambda f: (
            f["language"] in primary_languages,  # Primary languages first
            f["size"],  # Larger files first
            not f["relative_path"].startswith("test"),  # Non-test files first (except for test gates)
            f["relative_path"]  # Alphabetical as tiebreaker
        ), reverse=True)
        
        # Report filtering results
        relevant_langs_str = ", ".join(sorted(relevant_languages))
        print(f"   Relevant languages: {relevant_langs_str}")
        print(f"   Filtered to {len(relevant_files)} relevant files (from {len(all_files)} total {file_type.lower()} files)")
        
        # Show percentage breakdown
        if len(all_files) > 0:
            coverage_percentage = (len(relevant_files) / len(all_files)) * 100
            print(f"   Coverage: {coverage_percentage:.1f}% of {file_type.lower()} files")
        
        return relevant_files

    def _get_min_expected_implementation(self, gate_name: str, primary_technologies: list) -> int:
        """Get minimum expected implementation count for a gate"""
        # Use hardcoded fallback since pattern_loader is removed
        # Fallback minimum
        return 5

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
        
        # Check if this is a security gate with NOT operators
        gate_name = enhanced_result.get("gate_name", legacy_gate["name"])
        is_security_gate = gate_name == "AVOID_LOGGING_SECRETS"
        
        # For security gates with NOT operators, matches represent violations
        # If the gate passed (status == "PASS"), there should be no violations
        if is_security_gate and status == "PASS":
            # Gate passed means no violations found, so clear matches
            legacy_matches = []
            violation_matches = matches  # Keep original matches for violation reporting
        else:
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
            violation_matches = matches
        
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
            "evidence": f"Enhanced criteria evaluation: {len(legacy_matches)} matches found",
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
                ],
                "violation_matches": violation_matches  # Keep original matches for violation reporting
            }
        }
    
    def _evaluate_single_gate_legacy(self, gate: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single gate using legacy pattern matching with file-centric results"""
        gate_name = gate["name"]
        metadata = params["metadata"]
        matches = params.get("matches", [])
        splunk_reference = params.get("splunk_reference")
        stats = params.get("stats", {})
        
        print(f"   🔍 Processing results for {gate_name}...")
        
        # Handle ALERTING_ACTIONABLE gate specially
        if gate_name == "ALERTING_ACTIONABLE":
            return self._evaluate_alerting_actionable_gate(gate, params)
        
        # Get pattern information
        llm_patterns = params.get("patterns", {})
        pattern_data = params.get("pattern_data", {})
        llm_gate_patterns = llm_patterns.get(gate_name, [])
        gate_pattern_info = pattern_data.get(gate_name, {})
        
        # Deduplicate matches
        all_matches = self._deduplicate_matches(matches)
        
        # Calculate gate score
        score = self._calculate_gate_score(gate, all_matches, metadata)
        
        # Determine status
        status = self._determine_status(score, gate)
        
        # Generate details and recommendations
        details = self._generate_gate_details(gate, all_matches)
        recommendations = self._generate_gate_recommendations(gate, all_matches, score)
        
        # Calculate combined confidence
        combined_confidence = self._calculate_combined_confidence(
            len(llm_gate_patterns), 0, len(all_matches)  # No static patterns in file-centric approach
        )
        
        # Get relevant files count from stats
        relevant_files = stats.get("files_processed", 0)
        
        # Create gate result
        gate_result = {
            "gate": gate_name,
            "display_name": gate["display_name"],
            "description": gate["description"],
            "category": gate["category"],
            "priority": gate["priority"],
            "patterns_used": len(llm_gate_patterns),
            "matches_found": len(all_matches),
            "matches": all_matches,
            "patterns": llm_gate_patterns,
            "score": score,
            "status": status,
            "details": details,
            "evidence": f"Found {len(all_matches)} matches across {relevant_files} relevant files",
            "recommendations": recommendations,
            "pattern_description": gate_pattern_info.get("description", gate.get("description", "Pattern analysis for this gate")),
            "pattern_significance": gate_pattern_info.get("significance", gate.get("significance", "Important for code quality and compliance")),
            "expected_coverage": gate_pattern_info.get("expected_coverage", gate.get("expected_coverage", {
                "percentage": 10,
                "reasoning": "Standard expectation for this gate type",
                "confidence": "medium"
            })),
            "total_files": metadata.get("total_files", 1),
            "relevant_files": relevant_files,
            "validation_sources": {
                "llm_patterns": {"count": len(llm_gate_patterns), "matches": len(all_matches), "source": "file_centric"},
                "static_patterns": {"count": 0, "matches": 0, "source": "file_centric"},
                "combined_confidence": combined_confidence,
                "splunk_reference": splunk_reference
            }
        }
        
        return gate_result

    def _evaluate_alerting_actionable_gate(self, gate: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Special evaluation for ALERTING_ACTIONABLE gate using database integration"""
        gate_name = gate["name"]
        
        # Use fetch_alerting_integrations_status to determine status
        from utils.db_integration import fetch_alerting_integrations_status
        # Try to get app_id from params, else extract from repo URL
        app_id = params.get('shared', {}).get('request', {}).get('app_id')
        if not app_id:
            repo_url = params.get('shared', {}).get('request', {}).get('repository_url', '')
            from utils.db_integration import extract_app_id_from_url
            app_id = extract_app_id_from_url(repo_url) or '<APP ID>'
        
        print(f"   🔗 Using database integration for {gate_name} (app_id={app_id})")
        
        try:
            integration_status = fetch_alerting_integrations_status(app_id)
            print(f"   [DEBUG] Integration status: {integration_status}")
        except Exception as ex:
            print(f"   [ERROR] fetch_alerting_integrations_status failed: {ex}")
            integration_status = {"Splunk": False, "AppDynamics": False, "ThousandEyes": False}
        
        present = [k for k, v in integration_status.items() if v]
        missing = [k for k, v in integration_status.items() if not v]
        all_present = all(integration_status.values())
        
        # Only include App ID in evidence/details if it is not '<APP ID>' or empty
        app_id_str = f"; App ID: {app_id}" if app_id and app_id != '<APP ID>' else ""
        evidence_str = f"Present: {', '.join(present) if present else 'None'}; Missing: {', '.join(missing) if missing else 'None'}{app_id_str}"
        
        gate_result = {
            "gate": gate_name,
            "display_name": gate["display_name"],
            "description": gate["description"],
            "category": gate["category"],
            "priority": gate["priority"],
            "patterns_used": 0,
            "matches_found": 0,
            "matches": [],
            "patterns": [],
            "score": 100.0 if all_present else 0.0,
            "status": "PASS" if all_present else "FAIL",
            "details": [
                f"Present: {', '.join(present) if present else 'None'}",
                f"Missing: {', '.join(missing) if missing else 'None'}" + (f"; App ID: {app_id}" if app_id and app_id != '<APP ID>' else "")
            ],
            "evidence": evidence_str,
            "recommendations": [
                "All integrations detected and actionable" if all_present else f"Missing integrations: {', '.join(missing)}"
            ],
            "pattern_description": gate.get("description", "Pattern analysis for this gate"),
            "pattern_significance": gate.get("significance", "Important for code quality and compliance"),
            "expected_coverage": gate.get("expected_coverage", {
                "percentage": 100,
                "reasoning": "All integrations should be present",
                "confidence": "high"
            }),
            "total_files": params["metadata"].get("total_files", 1),
            "relevant_files": 1,
            "validation_sources": {
                "llm_patterns": {"count": 0, "matches": 0, "source": "db_integration"},
                "static_patterns": {"count": 0, "matches": 0, "source": "db_integration"},
                "combined_confidence": "high"
            }
        }
        
        return gate_result
    
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


class GenerateReportNode(Node):
    """Node to generate HTML and JSON reports using the same template as original report.py"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare report generation parameters"""
        return {
            "validation_results": shared["validation"],
            "metadata": shared["repository"]["metadata"],
            "config": shared["config"],
            "request": shared["request"],
            "llm_info": {
                "source": shared["llm"].get("source", "unknown"),
                "model": shared["llm"].get("model", "unknown")
            },
            "scan_id": shared["request"]["scan_id"],
            "splunk_results": shared.get("splunk", {})
        }
    
    def exec(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Generate reports using the same template as original report.py"""
        print("📄 Generating reports with original template...")
        
        scan_id = params["scan_id"]
        output_dir = params["request"].get("output_dir", "./reports")
        report_format = params["request"].get("report_format", "both")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        report_paths = {}
        
        # Generate JSON report
        if report_format in ["json", "both"]:
            try:
                json_path = os.path.join(output_dir, f"codegates_report_{scan_id}.json")
                json_data = self._generate_json_report(params)
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                
                report_paths["json"] = json_path
                print(f"✅ JSON report generated: {json_path}")
            except Exception as e:
                print(f"❌ Failed to generate JSON report: {e}")
        
        # Generate HTML report with timeout
        if report_format in ["html", "both"]:
            try:
                html_path = os.path.join(output_dir, f"codegates_report_{scan_id}.html")
                
                # Add timeout for HTML generation
                import signal
                import threading
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("HTML report generation timed out")
                
                # Set timeout to 5 minutes
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(300)  # 5 minutes timeout
                
                try:
                    print(f"🔍 Debug: Generating HTML report...")
                    html_content = self._generate_html_report(params)
                    print(f"🔍 Debug: HTML content length: {len(html_content)}")
                    
                    if html_content:
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        # Verify file was written correctly
                        file_size = os.path.getsize(html_path)
                        print(f"🔍 Debug: HTML file size: {file_size} bytes")
                        
                        if file_size == 0:
                            print("⚠️ Warning: HTML file is empty!")
                        else:
                            print(f"✅ HTML file written successfully")
                        
                        report_paths["html"] = html_path
                        print(f"✅ HTML report generated: {html_path}")
                    else:
                        print("⚠️ Warning: HTML content is empty!")
                        
                finally:
                    signal.alarm(0)  # Cancel the alarm
                    
            except TimeoutError:
                print("⚠️ HTML report generation timed out after 5 minutes")
                print("💡 Consider reducing the amount of data or using JSON format only")
            except Exception as e:
                print(f"❌ Failed to generate HTML report: {e}")
                import traceback
                traceback.print_exc()
        
        return report_paths
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, str]) -> str:
        """Store report paths in shared store"""
        shared["reports"]["json_path"] = exec_res.get("json")
        shared["reports"]["html_path"] = exec_res.get("html")
        
        # Get server info for URL generation
        server_info = shared.get("server", {})
        server_url = server_info.get("url", "http://localhost:8000")
        scan_id = shared["request"]["scan_id"]
        
        print(f"✅ Reports generated:")
        for format_type, path in exec_res.items():
            print(f"   {format_type.upper()}: {path}")
            
            # Print URL for HTML report
            if format_type == "html" and path:
                report_url = f"{server_url}/api/v1/scan/{scan_id}/report/html"
                print(f"   🌐 HTML Report URL: {report_url}")
            elif format_type == "json" and path:
                report_url = f"{server_url}/api/v1/scan/{scan_id}/report/json"
                print(f"   🌐 JSON Report URL: {report_url}")
        
        return "default"
    
    def _generate_json_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON report with same structure as original plus weighted validation info"""
        
        validation = params["validation_results"]
        metadata = params["metadata"]
        llm_info = params["llm_info"]
        
        # Use the new data structure directly
        gate_results = validation["gate_results"]
        hybrid_stats = validation.get("hybrid_stats", {})
        weighted_scoring = validation.get("weighted_scoring_summary", {})
        pattern_stats = validation.get("pattern_statistics", {})
        
        # Calculate summary statistics from new data
        stats = self._calculate_summary_stats_from_new_data(gate_results)
        
        # Extract App Id, project name, and branch for consistency
        app_id = self._extract_app_id(params["request"]["repository_url"])
        project_name = self._extract_project_name(params["request"]["repository_url"])
        branch_name = params["request"]["branch"]
        project_display_name = f"{app_id} - {project_name} ({branch_name})"
        
        return {
            "scan_id": params.get("scan_id", "unknown"),
            "project_name": project_display_name,
            "repository_url": params["request"]["repository_url"],
            "branch": params["request"]["branch"],
            "scan_timestamp": self._get_timestamp(),
            "scan_timestamp_formatted": self._get_timestamp_formatted(),
            "overall_score": validation["overall_score"],
            "threshold": params["request"]["threshold"],
            "status": "PASS" if validation["overall_score"] >= params["request"]["threshold"] else "FAIL",
            
            # Summary statistics
            "summary": {
                "total_gates": stats["total_gates"],
                "passed_gates": stats["passed_gates"],
                "failed_gates": stats["failed_gates"],
                "warning_gates": stats["warning_gates"],
                "not_applicable_gates": stats["not_applicable_gates"],
                "total_files": metadata.get("total_files", 0),
                "total_lines": metadata.get("total_lines", 0)
            },
            
            # Gate results with enhanced information
            "gates": gate_results,
            
            # Metadata
            "metadata": {
                "file_count": metadata.get("total_files", 0),
                "line_count": metadata.get("total_lines", 0),
                "language_distribution": metadata.get("language_stats", {}),
                "primary_technologies": self._get_primary_technologies(metadata),
                "scan_duration": params.get("scan_duration", 0),
                "pattern_library_version": "2.0.0"
            },
            
            # LLM information
            "llm_info": {
                "provider": llm_info.get("provider", "none"),
                "model": llm_info.get("model", "none"),
                "patterns_generated": hybrid_stats.get("total_llm_patterns", 0),
                "patterns_matched": hybrid_stats.get("total_llm_matches", 0),
                "confidence": llm_info.get("confidence", "low")
            },
            
            # Enhanced weighted validation statistics
            "weighted_validation": {
                "enabled": True,
                "statistics": hybrid_stats,
                "pattern_library_version": "2.0.0",
                "static_patterns_used": hybrid_stats.get("total_static_patterns", 0),
                "llm_patterns_used": hybrid_stats.get("total_llm_patterns", 0),
                "coverage_improvement": hybrid_stats.get("coverage_improvement", 0.0),
                "confidence_distribution": hybrid_stats.get("confidence_distribution", {}),
                "weighted_scoring": {
                    "total_weight": weighted_scoring.get("total_weight", 0.0),
                    "applicable_gates": weighted_scoring.get("applicable_gates", 0),
                    "gate_scores": weighted_scoring.get("gate_scores", {}),
                    "overall_weighted_score": weighted_scoring.get("overall_score", 0.0)
                },
                "pattern_statistics": {
                    "total_gates": pattern_stats.get("total_gates", 0),
                    "total_patterns": pattern_stats.get("total_patterns", 0),
                    "supported_technologies": pattern_stats.get("supported_technologies", []),
                    "technology_coverage": pattern_stats.get("technology_coverage", {})
                }
            },
            
            # Gate applicability information
            "applicability": {
                "enabled": True,
                "codebase_characteristics": validation.get("applicability_summary", {}).get("codebase_characteristics", {}),
                "total_gates": validation.get("applicability_summary", {}).get("total_gates", 0),
                "applicable_gates": validation.get("applicability_summary", {}).get("applicable_gates", 0),
                "non_applicable_gates": validation.get("applicability_summary", {}).get("non_applicable_gates", 0),
                "applicable_by_category": validation.get("applicability_summary", {}).get("applicable_by_category", {}),
                "non_applicable_details": validation.get("applicability_summary", {}).get("non_applicable_details", []),
                "applicable_gate_names": validation.get("applicability_summary", {}).get("applicable_gate_names", [])
            },
            
            # Splunk integration results
            "splunk_integration": {
                "enabled": True,
                "query_executed": params.get("splunk_results", {}).get("status") != "skipped",
                "status": params.get("splunk_results", {}).get("status", "skipped"),
                "message": params.get("splunk_results", {}).get("message", "No Splunk query provided"),
                "total_results": params.get("splunk_results", {}).get("total_results", 0),
                "execution_time": params.get("splunk_results", {}).get("execution_time", 0),
                "analysis": params.get("splunk_results", {}).get("analysis", {}),
                "query": params.get("splunk_results", {}).get("query", "")
            }
        }
    
    def _generate_html_report(self, params: Dict[str, Any]) -> str:
        """Generate HTML report using exact same template as original report.py with hybrid validation info"""
        
        try:
            validation = params["validation_results"]
            metadata = params["metadata"]
            llm_info = params["llm_info"]
            
            # Use the new data structure directly
            gate_results = validation["gate_results"]
            hybrid_stats = validation.get("hybrid_stats", {})
            
            # Limit the amount of data to prevent hanging
            limited_gate_results = []
            for gate in gate_results:
                try:
                    limited_gate = gate.copy()
                    
                    # Limit matches to prevent HTML from becoming too large
                    if "matches" in limited_gate and isinstance(limited_gate["matches"], list) and len(limited_gate["matches"]) > 100:
                        original_matches_count = len(limited_gate["matches"])
                        limited_gate["matches"] = limited_gate["matches"][:100]
                        limited_gate["matches_found"] = len(limited_gate["matches"])
                        if "details" in limited_gate and isinstance(limited_gate["details"], list):
                            limited_gate["details"] = limited_gate["details"][:5]  # Limit details too
                            limited_gate["details"].append(f"... and {original_matches_count - 100} more matches (truncated for performance)")
                    
                    # Limit details to prevent HTML from becoming too large
                    if "details" in limited_gate and isinstance(limited_gate["details"], list) and len(limited_gate["details"]) > 10:
                        limited_gate["details"] = limited_gate["details"][:10]
                        limited_gate["details"].append("... (details truncated for performance)")
                    
                    limited_gate_results.append(limited_gate)
                except Exception as e:
                    print(f"Warning: Error processing gate {gate.get('gate', 'unknown')}: {e}")
                    # Add a safe fallback
                    limited_gate_results.append({
                        "gate": gate.get("gate", "unknown"),
                        "display_name": gate.get("display_name", "Unknown Gate"),
                        "description": gate.get("description", ""),
                        "category": gate.get("category", "Unknown"),
                        "priority": gate.get("priority", "medium"),
                        "score": gate.get("score", 0.0),
                        "status": gate.get("status", "UNKNOWN"),
                        "matches_found": 0,
                        "matches": [],
                        "details": ["Error processing gate data"],
                        "recommendations": ["Unable to generate recommendations due to data processing error"]
                    })
            
            # Calculate summary statistics from limited data
            stats = self._calculate_summary_stats_from_new_data(limited_gate_results)
            
            # Extract App Id, project name, and branch
            app_id = self._extract_app_id(params["request"]["repository_url"])
            project_name = self._extract_project_name(params["request"]["repository_url"])
            branch_name = params["request"]["branch"]
            # Create display name with App Id, Repo Url, and Branch
            project_display_name = f"{app_id} - {project_name} ({branch_name})"
            
            # Get current timestamp
            timestamp = self._get_timestamp_formatted()
            
            # Report type display
            report_type_display = "Hybrid Validation"
            
            # Get overall score safely
            overall_score = validation.get("overall_score", 0.0)
            
            # Generate gates table HTML
            gates_table_html = self._generate_gates_table_html_from_new_data(limited_gate_results)
            
            # Generate applicability summary HTML
            applicability_html = self._generate_applicability_summary_html(validation.get("applicability_summary", {}))
            
            # JavaScript for details toggle
            toggle_script = """
            <script>
            function toggleDetails(button, detailsId) {
                const details = document.getElementById(detailsId);
                const isExpanded = button.getAttribute('aria-expanded') === 'true';
                
                button.setAttribute('aria-expanded', !isExpanded);
                details.setAttribute('aria-hidden', isExpanded);
                
                // Smooth scroll to expanded content
                if (!isExpanded) {
                    setTimeout(() => {
                        details.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 100);
                }
            }
            </script>
            """
            
            # Create a simpler, more robust HTML template
            llm_source = llm_info.get('source', '')
            llm_model = llm_info.get('model', '')
            if llm_source and llm_source != 'unknown':
                llm_line = f"Generated with {llm_source} ({llm_model}) + Static Pattern Library"
            else:
                llm_line = "Generated with Static Pattern Library"
            html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hard Gate Assessment ({report_type_display}) - {project_display_name}</title>
    <style>
        {self._get_extension_css_styles()}
    </style>
    {toggle_script}
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>{project_display_name}</h1>
            <div class="report-badge summary-badge">{report_type_display} Report</div>
            <p style="color: #2563eb; margin-bottom: 30px; font-weight: 500;">Hard Gate Assessment Report</p>
            <!--<p style="color: #6b7280; margin-bottom: 20px;">{llm_line}</p>-->
        </div>
        
        <h2>Executive Summary</h2>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_gates', 0)}</div>
                <div class="stat-label">Total Gates Evaluated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('passed_gates', 0)}</div>
                <div class="stat-label">Gates Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('warning_gates', 0)}</div>
                <div class="stat-label">Partially Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('failed_gates', 0)}</div>
                <div class="stat-label">Not Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('not_applicable_gates', 0)}</div>
                <div class="stat-label">Not Applicable</div>
            </div>
        </div>
        
        <h3>Overall Compliance</h3>
        <div class="compliance-bar">
            <div class="compliance-fill" style="width: {overall_score:.1f}%"></div>
        </div>
        <p><strong>{overall_score:.1f}% Hard Gates Compliance</strong></p>
        <p style="color: #6b7280; font-size: 0.9em; margin-top: 5px;">
            <em>Percentage calculated based on {stats.get('total_gates', 0)} applicable gates (excluding {stats.get('not_applicable_gates', 0)} N/A gates)</em>
        </p>
        
        {applicability_html}
        
        <h2>Hard Gates Analysis</h2>
        {gates_table_html}
        
        <footer style="margin-top: 50px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            <p>Hard Gate Assessment {report_type_display} Report generated on {timestamp}</p>
        </footer>
    </div>
</body>
</html>"""
            
            return html_template
        except Exception as e:
            print(f"⚠️ Failed to generate HTML report: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _generate_hybrid_validation_summary_html(self, hybrid_stats: Dict[str, Any]) -> str:
        """Generate HTML summary for hybrid validation statistics"""
        if not hybrid_stats:
            return ""
        
        confidence_dist = hybrid_stats.get("confidence_distribution", {})
        coverage_improvement = hybrid_stats.get("coverage_improvement", 0.0)
        
        return f"""
        <h3>Hybrid Validation Summary</h3>
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{hybrid_stats.get('total_llm_patterns', 0)}</div>
                <div class="stat-label">LLM Patterns</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{hybrid_stats.get('total_static_patterns', 0)}</div>
                <div class="stat-label">Static Patterns</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{hybrid_stats.get('total_unique_matches', 0)}</div>
                <div class="stat-label">Unique Matches</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{coverage_improvement:.1f}%</div>
                <div class="stat-label">Coverage Improvement</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{confidence_dist.get('high', 0)}</div>
                <div class="stat-label">High Confidence Gates</div>
            </div>
        </div>
        <p style="color: #6b7280; font-size: 0.9em; margin-top: 10px;">
            <em>Hybrid validation combines LLM-generated patterns with comprehensive static pattern library for enhanced coverage and accuracy</em>
        </p>
        """
    
    def _get_extension_css_styles(self) -> str:
        """Get CSS styles that exactly match the original report.py"""
        return """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f3f4f6; }
        h1 { font-size: 2em; color: #1f2937; border-bottom: 3px solid #2563eb; padding-bottom: 15px; margin-bottom: 30px; }
        h2 { color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 40px; }
        h3 { color: #374151; margin-top: 30px; }
        
        /* Report Badge Styles */
        .report-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: 15px;
        }
        .summary-badge { background: #059669; color: #fff; }
        .detailed-badge { background: #1f2937; color: #fff; }
        
        /* Summary Stats */
        .summary-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .stat-card { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2563eb; }
        .stat-label { color: #6b7280; margin-top: 5px; }
        
        /* Compliance Bar */
        .compliance-bar { width: 100%; height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .compliance-fill { height: 100%; background: linear-gradient(90deg, #dc2626 0%, #d97706 50%, #059669 100%); transition: width 0.3s ease; }
        
        /* Gates Analysis Styling */
        .gates-analysis { margin-top: 30px; }
        .gate-category-section { margin-bottom: 40px; }
        .category-title {
            color: #1f2937;
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }
        .category-content {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        /* Table Styles */
        table { width: 100%; border-collapse: collapse; margin: 0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #2563eb; color: #fff; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        tr:hover { background: #f9fafb; }
        
        /* Status Styles */
        .status-pass { color: #059669 !important; background: #ecfdf5; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-warning { color: #d97706 !important; background: #fffbeb; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-fail { color: #dc2626 !important; background: #fef2f2; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-not_applicable { color: #6b7280 !important; background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        
        /* Expandable Details Styling */
        .details-toggle {
            background: none;
            border: none;
            color: #2563eb;
            cursor: pointer;
            padding: 4px 8px;
            font-size: 1.1em;
            transition: transform 0.2s;
        }
        .details-toggle:hover { color: #1d4ed8; }
        .details-toggle[aria-expanded="true"] { transform: rotate(45deg); }
        
        .gate-details {
            display: none;
            background: #f8fafc;
            border-top: 1px solid #e5e7eb;
            padding: 0;
            margin: 0;
        }
        .gate-details[aria-hidden="false"] { display: table-row; }
        
        .details-content {
            padding: 16px;
            color: #4b5563;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }
        
        .metric-card {
            background: white;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
        }
        
        /* New Metric Box Styles */
        .gate-metrics {
            margin: 16px 0;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .metric-box {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: box-shadow 0.2s ease;
        }
        
        .metric-box:hover {
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        }
        
        .metric-label {
            display: block;
            font-size: 0.75rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        
        .metric-value {
            display: block;
            font-size: 1.25rem;
            font-weight: 700;
            color: #1f2937;
        }
        
        .metric-value.score-pass { color: #059669; }
        .metric-value.score-warning { color: #d97706; }
        .metric-value.score-fail { color: #dc2626; }
        .metric-value.status-pass { color: #059669; }
        .metric-value.status-warning { color: #d97706; }
        .metric-value.status-fail { color: #dc2626; }
        .metric-value.status-not_applicable { color: #6b7280; }
        
        /* Enhanced Metrics Section */
        .enhanced-metrics {
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
        }
        
        .enhanced-metrics h4 {
            font-size: 1rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
        }
        
        /* Condition Results */
        .condition-results {
            margin-top: 16px;
        }
        
        .condition-results h5 {
            font-size: 0.875rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
        }
        
        .condition-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .condition-item {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 0.875rem;
        }
        
        .condition-item.condition-pass {
            background: #ecfdf5;
            border-color: #a7f3d0;
        }
        
        .condition-item.condition-fail {
            background: #fef2f2;
            border-color: #fecaca;
        }
        
        .condition-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }
        
        .condition-icon {
            font-size: 0.75rem;
        }
        
        .condition-name {
            font-weight: 600;
            color: #374151;
        }
        
        .condition-type {
            color: #6b7280;
            font-size: 0.75rem;
        }
        
        .condition-details {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: #6b7280;
        }
        
        .condition-matches {
            font-weight: 500;
        }
        
        .condition-weight {
            font-weight: 500;
        }
        """
    
    def _transform_gates_for_template(self, gate_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform gate results to match original template format"""
        transformed_gates = []
        
        for gate_result in gate_results:
            # Map new format to original format
            gate = {
                "name": gate_result["gate"],
                "status": gate_result["status"],
                "score": gate_result["score"],
                "details": gate_result["details"],
                "expected": gate_result.get("patterns_used", 0),
                "found": gate_result.get("matches_found", 0),
                "coverage": gate_result["score"],  # Use score as coverage
                "quality_score": gate_result["score"],
                "matches": []  # Could be populated with actual matches if needed
            }
            transformed_gates.append(gate)
        
        return transformed_gates
    
    def _calculate_summary_stats(self, result_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate summary statistics like the original"""
        gates = result_data.get("gates", [])
        
        implemented_gates = len([g for g in gates if g.get("status") == "PASS"])
        partial_gates = len([g for g in gates if g.get("status") == "WARNING"])
        not_implemented_gates = len([g for g in gates if g.get("status") == "FAIL"])
        
        return {
            "total_gates": len(gates),
            "implemented_gates": implemented_gates,
            "partial_gates": partial_gates,
            "not_implemented_gates": not_implemented_gates
        }
    
    def _calculate_summary_stats_from_new_data(self, gate_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate summary statistics from new gate results structure"""
        total_gates = len(gate_results)
        passed_gates = len([g for g in gate_results if g.get("status") == "PASS"])
        failed_gates = len([g for g in gate_results if g.get("status") == "FAIL"])
        warning_gates = len([g for g in gate_results if g.get("status") == "WARNING"])
        not_applicable_gates = len([g for g in gate_results if g.get("status") == "NOT_APPLICABLE"])
        
        return {
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "failed_gates": failed_gates,
            "warning_gates": warning_gates,
            "not_applicable_gates": not_applicable_gates
        }

    def _extract_project_name(self, repository_url: str) -> str:
        """Extract project name from repository URL"""
        try:
            # Handle various URL formats
            if repository_url.endswith('.git'):
                repository_url = repository_url[:-4]
            
            # Split by / and get the last part
            parts = repository_url.rstrip('/').split('/')
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
            elif len(parts) >= 1:
                return parts[-1]
            else:
                return "Repository Scan Results"
        except Exception:
            return "Repository Scan Results"
    
    def _get_timestamp(self) -> str:
        """Get ISO timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_timestamp_formatted(self) -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _get_new_gate_categories(self) -> Dict[str, List[str]]:
        """Get gate categories matching the new data structure"""
        return {
            'Auditability': ['STRUCTURED_LOGS', 'AVOID_LOGGING_SECRETS', 'AUDIT_TRAIL', 'CORRELATION_ID', 'LOG_API_CALLS', 'LOG_APPLICATION_MESSAGES', 'UI_ERRORS'],
            'Availability': ['RETRY_LOGIC', 'TIMEOUTS', 'THROTTLING', 'CIRCUIT_BREAKERS'],
            'Error Handling': ['ERROR_LOGS', 'HTTP_CODES', 'UI_ERROR_TOOLS'],
            'Testing': ['AUTOMATED_TESTS']
        }

    def _get_status_info_from_new_data(self, status: str, gate: Dict[str, Any] = None) -> Dict[str, str]:
        """Get status info for display from new data structure"""
        if gate:
            matches_found = gate.get("matches_found", 0)
            
            # Special handling for avoid_logging_secrets
            if matches_found > 0 and gate.get("gate") == 'AVOID_LOGGING_SECRETS':
                return {'class': 'not-implemented', 'display': '✗ Violations Found'}
        
        # Default status mapping
        if status == 'PASS':
            return {'class': 'implemented', 'display': '✓ Implemented'}
        elif status == 'WARNING':
            return {'class': 'partial', 'display': '⚬ Partial'}
        elif status == 'NOT_APPLICABLE':
            return {'class': 'not-applicable', 'display': 'N/A'}
        else:
            return {'class': 'not-implemented', 'display': '✗ Missing'}

    def _format_evidence_from_new_data(self, gate: Dict[str, Any]) -> str:
        """Format evidence for display from new data structure"""
        if gate.get("gate") == "ALERTING_ACTIONABLE" or gate.get("name") == "ALERTING_ACTIONABLE":
            # Use the evidence field if present, else a default message
            return gate.get("evidence") or "Status check from VISTA monitoring system"
        if gate.get("status") == 'NOT_APPLICABLE':
            return 'Not applicable to this technology stack'
        matches_found = gate.get("matches_found", 0)
        score = gate.get("score", 0)
        if matches_found > 0:
            return f"Found {matches_found} implementations with {score:.1f}% coverage"
        else:
            return 'No relevant patterns found in codebase'

    def _get_recommendation_from_new_data(self, gate: Dict[str, Any]) -> str:
        """Get recommendation for display from new data structure"""
        matches_found = gate.get("matches_found", 0)
        status = gate.get("status")
        display_name = gate.get("display_name", "")
        
        # Use existing recommendations if available
        recommendations = gate.get("recommendations", [])
        if recommendations:
            return recommendations[0]  # Use first recommendation
        
        # Special handling for NOT_APPLICABLE
        if status == 'NOT_APPLICABLE':
            return 'Not applicable to this technology stack'
        
        # Special handling for avoid_logging_secrets
        if matches_found > 0:
            if gate.get("gate") == 'AVOID_LOGGING_SECRETS':
                return f"Fix confidential data logging violations in {display_name.lower()}"
            elif status == 'PASS':
                return f"Address identified issues in {display_name.lower()}"
        
        # Default recommendation mapping
        if status == 'PASS':
            return 'Continue maintaining good practices'
        elif status == 'WARNING':
            return f"Expand implementation of {display_name.lower()}"
        else:
            return f"Implement {display_name.lower()}"
    
    def _get_gate_categories(self) -> Dict[str, List[str]]:
        """Get gate categories matching original format"""
        return {
            'Auditability': ['STRUCTURED_LOGS', 'AVOID_LOGGING_SECRETS', 'AUDIT_TRAIL', 'CORRELATION_ID', 'LOG_API_CALLS', 'LOG_APPLICATION_MESSAGES', 'UI_ERRORS'],
            'Availability': ['RETRY_LOGIC', 'TIMEOUTS', 'THROTTLING', 'CIRCUIT_BREAKERS'],
            'Error Handling': ['ERROR_LOGS', 'HTTP_CODES', 'UI_ERROR_TOOLS'],
            'Testing': ['AUTOMATED_TESTS']
        }
    
    def _get_gate_name_map(self) -> Dict[str, str]:
        """Get gate name mapping to display names"""
        return {
            'STRUCTURED_LOGS': 'Logs Searchable Available',
            'AVOID_LOGGING_SECRETS': 'Avoid Logging Confidential Data',
            'AUDIT_TRAIL': 'Create Audit Trail Logs',
            'CORRELATION_ID': 'Tracking ID For Log Messages',
            'LOG_API_CALLS': 'Log Rest API Calls',
            'LOG_APPLICATION_MESSAGES': 'Log Application Messages',
            'UI_ERRORS': 'Client UI Errors Logged',
            'RETRY_LOGIC': 'Retry Logic',
            'TIMEOUTS': 'Set Timeouts IO Operations',
            'THROTTLING': 'Throttling Drop Request',
            'CIRCUIT_BREAKERS': 'Circuit Breakers Outgoing Requests',
            'ERROR_LOGS': 'Log System Errors',
            'HTTP_CODES': 'Use HTTP Standard Error Codes',
            'UI_ERROR_TOOLS': 'Include Client Error Tracking',
            'AUTOMATED_TESTS': 'Automated Regression Testing'
        }
    
    def _format_gate_name(self, name: str) -> str:
        """Format gate name for display"""
        gate_name_map = self._get_gate_name_map()
        if name in gate_name_map:
            return gate_name_map[name]
        # Fallback formatting
        return ' '.join(word.capitalize() for word in name.split('_'))
    
    def _get_status_info(self, status: str, gate: Dict[str, Any] = None) -> Dict[str, str]:
        """Get status info for display"""
        if gate:
            found = gate.get("found", 0)
            
            # Special handling for avoid_logging_secrets
            if found > 0 and gate.get("name") == 'AVOID_LOGGING_SECRETS':
                return {'class': 'not-implemented', 'text': '✗ Violations Found'}
        
        # Default status mapping
        if status == 'PASS':
            return {'class': 'implemented', 'text': '✓ Implemented'}
        elif status == 'WARNING':
            return {'class': 'partial', 'text': '⚬ Partial'}
        elif status == 'NOT_APPLICABLE':
            return {'class': 'partial', 'text': 'N/A'}
        else:
            return {'class': 'not-implemented', 'text': '✗ Missing'}
    
    def _format_evidence(self, gate: Dict[str, Any]) -> str:
        """Format evidence for display"""
        if gate.get("status") == 'NOT_APPLICABLE':
            return 'Not applicable to this project type'
        
        found = gate.get("found", 0)
        score = gate.get("score", 0)
        
        if found > 0:
            return f"Found {found} implementations with {score:.1f}% coverage"
        else:
            return 'No relevant patterns found in codebase'
    
    def _get_recommendation(self, gate: Dict[str, Any], gate_name: str) -> str:
        """Get recommendation for display"""
        found = gate.get("found", 0)
        status = gate.get("status")
        
        # Special handling for avoid_logging_secrets
        if found > 0:
            if gate.get("name") == 'AVOID_LOGGING_SECRETS':
                return f"Fix confidential data logging violations in {gate_name.lower()}"
            elif status == 'PASS':
                return f"Address identified issues in {gate_name.lower()}"
        
        # Default recommendation mapping
        if status == 'PASS':
            return 'Continue maintaining good practices'
        elif status == 'WARNING':
            return f"Expand implementation of {gate_name.lower()}"
        elif status == 'NOT_APPLICABLE':
            return 'Not applicable to this project type'
        else:
            return f"Implement {gate_name.lower()}"
    
    def _generate_gates_table_html(self, result_data: Dict[str, Any]) -> str:
        """Generate gates table HTML with categories like original"""
        gates = result_data.get("gates", [])
        gate_categories = self._get_gate_categories()
        
        html = """<div class=\"gates-analysis\">"""
        
        for category_name, gate_names in gate_categories.items():
            category_gates = [g for g in gates if g.get("name") in gate_names]
            
            if not category_gates:
                continue
            
            html += f"""
                <div class=\"gate-category-section\">
                    <h3 class=\"category-title\">{category_name}</h3>
                    <div class=\"category-content\">
                        <table class=\"gates-table\">
                            <thead>
                                <tr>
                                    <th style=\"width: 30px\"></th>
                                    <th>Practice</th>
                                    <th>Status</th>
                                    <th>Evidence</th>
                                    <th>Recommendation</th>
                                </tr>
                            </thead>
                            <tbody>"""
            
            for i, gate in enumerate(category_gates):
                gate_id = f"{category_name.lower()}-{gate.get('name', '')}-{i}"
                gate_name = self._format_gate_name(gate.get("name", ""))
                status_info = self._get_status_info(gate.get("status", ""), gate)
                # OVERRIDE: Evidence for ALERTING_ACTIONABLE
                if gate.get("name") == "ALERTING_ACTIONABLE" and gate.get("evidence"):
                    evidence = gate["evidence"]
                else:
                    evidence = self._format_evidence(gate)
                recommendation = self._get_recommendation(gate, gate_name)
                
                # Generate detailed content
                details_content = self._generate_gate_details(gate)
                
                html += f"""
                                <tr>
                                    <td style=\"text-align: center\">
                                        <button class=\"details-toggle\" onclick=\"toggleDetails(this, 'details-{gate_id}')\" aria-expanded=\"false\" aria-label=\"Show details for {gate_name}\">+</button>
                                    </td>
                                    <td><strong>{gate_name}</strong></td>
                                    <td><span class=\"status-{status_info['class']}\">{status_info['text']}</span></td>
                                    <td>{evidence}</td>
                                    <td>{recommendation}</td>
                                </tr>"""
                
                # Add details row (hidden by default)
                html += f"""
                                <tr id=\"details-{gate_id}\" class=\"gate-details\" aria-hidden=\"true\">
                                    <td colspan=\"5\" class=\"details-content\">
                                        {details_content}
                                    </td>
                                </tr>"""
            
            html += """
                            </tbody>
                        </table>
                    </div>
                </div>"""
        
        html += """</div>"""
        return html
    
    def _generate_gate_details(self, gate: Dict[str, Any], matches: List[Dict[str, Any]]) -> List[str]:
        """Generate details for gate result including expected coverage analysis"""
        details = []
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        confidence = expected_coverage.get("confidence", "medium")
        max_files_expected = expected_coverage.get("max_files_expected", gate.get("relevant_files", 1))
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        files_with_matches = len(set(m['file'] for m in matches)) if matches else 0
        scoring_config = gate.get("scoring", {})
        is_security_gate = scoring_config.get("is_security_gate", False) or gate["name"] == "AVOID_LOGGING_SECRETS"
        
        # Check for enhanced data with violation matches
        enhanced_data = gate.get("enhanced_data", {})
        violation_matches = enhanced_data.get("violation_matches", [])
        
        # Use violation_matches for security gates if available
        if is_security_gate and violation_matches:
            actual_matches = violation_matches
            files_with_violations = len(set(m.file for m in violation_matches)) if violation_matches else 0
        else:
            actual_matches = matches
            files_with_violations = files_with_matches
        
        if is_security_gate:
            if len(actual_matches) == 0:
                details.append(f"✅ No security violations found - perfect implementation")
            else:
                details.append(f"❌ Security violations found - immediate attention required")
        actual_percentage = (files_with_matches / max_files_expected) * 100 if max_files_expected > 0 else 0
        if expected_percentage == 100:
            details.append(f"🎯 Infrastructure Framework Analysis:")
            details.append(f"Expected Coverage: 100% ({coverage_reasoning})")
            if files_with_matches > 0:
                details.append(f"✅ Framework Detected & Implemented: {files_with_matches}/{max_files_expected} expected files")
                details.append(f"Framework: {coverage_reasoning}")
            else:
                details.append(f"⚠️ Framework Detected but Not Implemented: 0/{max_files_expected} expected files")
                details.append(f"Framework: {coverage_reasoning}")
                details.append(f"Recommendation: Implement the detected framework throughout your codebase")
        else:
            details.append(f"Expected Coverage: {expected_percentage}% ({coverage_reasoning})")
            details.append(f"Maximum Files Expected: {max_files_expected} files")
            traditional_coverage = (files_with_matches / relevant_files) * 100 if relevant_files > 0 else 0
        if relevant_files != total_files:
            details.append(f"Technology Filter: Using {relevant_files} relevant files (from {total_files} total files)")
        details.append(f"Confidence: {confidence}")
        if actual_matches:
            if is_security_gate:
                details.append(f"Found {len(actual_matches)} security violations across {files_with_violations} files")
            else:
                details.append(f"Found {len(actual_matches)} matches across {files_with_matches} files")
            # Show first few matches
            for match in actual_matches[:3]:
                if hasattr(match, 'file'):  # Enhanced match object
                    details.append(f"  {match.file}:{match.line_number or 0} - {match.context or match.pattern}")
                else:  # Legacy match object
                    details.append(f"  {match['file']}:{match['line']} - {match['match'][:50]}")
            if len(actual_matches) > 3:
                details.append(f"  ... and {len(actual_matches) - 3} more matches")
        else:
            if is_security_gate:
                details.append(f"No security violations found for {gate['display_name']}")
            else:
                details.append(f"No matches found for {gate['display_name']}")
        return details
    
    def _generate_gate_recommendations(self, gate: Dict[str, Any], matches: List[Dict[str, Any]], score: float) -> List[str]:
        """Generate recommendations for gate based on expected coverage analysis with maximum files context"""
        recommendations = []
        
        # Get expected coverage information
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        confidence = expected_coverage.get("confidence", "medium")
        max_files_expected = expected_coverage.get("max_files_expected", gate.get("relevant_files", 1))
        
        # Calculate actual coverage using maximum files expected
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        files_with_matches = len(set(m['file'] for m in matches)) if matches else 0
        
        # Check if this is a security gate
        scoring_config = gate.get("scoring", {})
        is_security_gate = scoring_config.get("is_security_gate", False) or gate["name"] == "AVOID_LOGGING_SECRETS"
        
        # Check for enhanced data with violation matches
        enhanced_data = gate.get("enhanced_data", {})
        violation_matches = enhanced_data.get("violation_matches", [])
        
        # Use violation_matches for security gates if available
        if is_security_gate and violation_matches:
            actual_matches = violation_matches
            files_with_violations = len(set(m.file for m in violation_matches)) if violation_matches else 0
        else:
            actual_matches = matches
            files_with_violations = files_with_matches
        
        if is_security_gate:
            # For security gates, focus on violations rather than coverage
            if len(actual_matches) == 0:
                recommendations.append(f"✅ {gate['display_name']} is well implemented")
                recommendations.append(f"No security violations found - perfect implementation")
            else:
                recommendations.append(f"❌ Critical: {gate['display_name']} violations found")
                recommendations.append(f"Found {len(actual_matches)} security violations across {files_with_violations} files")
                recommendations.append(f"Immediate action required: {coverage_reasoning}")
                
                # Provide specific guidance based on violation count
                if len(actual_matches) > 100:
                    recommendations.append(f"Major Security Issue: {len(actual_matches)} violations require immediate remediation")
                elif len(actual_matches) > 50:
                    recommendations.append(f"Significant Security Issue: {len(actual_matches)} violations need urgent attention")
                elif len(actual_matches) > 10:
                    recommendations.append(f"Security Issue: {len(actual_matches)} violations should be addressed")
                else:
                    recommendations.append(f"Minor Security Issue: {len(actual_matches)} violations to fix")
        else:
            # Calculate coverage using maximum files expected for more accurate assessment
            actual_percentage = (files_with_matches / max_files_expected) * 100 if max_files_expected > 0 else 0
            
            # Calculate coverage gap for all cases
            coverage_gap = expected_percentage - actual_percentage
            
            # Special recommendations for infrastructure patterns
            if expected_percentage == 100:
                if files_with_matches > 0:
                    recommendations.append(f"✅ Infrastructure Framework Implemented: {coverage_reasoning}")
                    recommendations.append(f"Current Usage: {files_with_matches}/{max_files_expected} expected files ({actual_percentage:.1f}%)")
                    if actual_percentage < 50:
                        recommendations.append(f"Recommendation: Extend {gate['display_name']} implementation to more files")
                    else:
                        recommendations.append(f"Recommendation: {gate['display_name']} is well implemented")
                else:
                    recommendations.append(f"🎯 Infrastructure Framework Detected: {coverage_reasoning}")
                    recommendations.append(f"Critical: Implement {gate['display_name']} throughout your codebase")
                    recommendations.append(f"Framework: {coverage_reasoning}")
                    recommendations.append(f"Expected Implementation: {max_files_expected} files")
            else:
                # Generate recommendations based on coverage gap with maximum files context
                if score < 50.0:
                    recommendations.append(f"Critical: Implement {gate['display_name']} throughout your codebase")
                    recommendations.append(f"Expected {expected_percentage}% coverage, currently at {actual_percentage:.1f}% (based on {max_files_expected} expected files)")
                    recommendations.append(f"Focus on {gate['description'].lower()}")
                    
                    # Provide specific guidance based on coverage gap
                    if coverage_gap > 50:
                        recommendations.append(f"Major Gap: Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                    elif coverage_gap > 25:
                        recommendations.append(f"Significant Gap: Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                    else:
                        recommendations.append(f"Moderate Gap: Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                elif score < 70.0:
                    recommendations.append(f"Improve: Enhance {gate['display_name']} implementation")
                    recommendations.append(f"Current: {actual_percentage:.1f}% coverage, Target: {expected_percentage}% coverage")
                    recommendations.append(f"Need to implement in {int(coverage_gap * max_files_expected / 100)} more files")
                else:
                    recommendations.append(f"Good: {gate['display_name']} is well implemented")
                    recommendations.append(f"Achieved: {actual_percentage:.1f}% coverage (Target: {expected_percentage}%)")
                    
                    if actual_percentage > expected_percentage:
                        recommendations.append(f"Exceeds expectations by {actual_percentage - expected_percentage:.1f}%")
        
        # Add context about maximum files expected
        if max_files_expected != relevant_files:
            recommendations.append(f"Note: Analysis based on {max_files_expected} expected files (from {relevant_files} relevant files)")
        
        return recommendations
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches based on file and line"""
        seen = set()
        unique_matches = []
        for match in matches:
            key = (match["file"], match["line"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        return unique_matches
    
    def _calculate_combined_confidence(self, llm_matches: int, static_matches: int, unique_matches: int) -> str:
        """Calculate combined confidence based on LLM, static, and unique matches"""
        total_matches = llm_matches + static_matches + unique_matches
        if total_matches == 0:
            return "low"
        elif llm_matches > 0 and static_matches > 0 and unique_matches > 0:
            return "high"
        elif llm_matches > 0 or static_matches > 0 or unique_matches > 0:
            return "medium"
        else:
            return "low"

    def _get_pattern_matching_config(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Get configurable pattern matching parameters"""
        # Default configuration
        default_config = {
            "max_files": 100,  # Reduced from 500 for better performance
            "max_file_size_mb": 2,  # Reduced from 5 for better performance
            "max_matches_per_file": 50,  # New limit for matches per file
            "language_threshold_percent": 5.0,
            "config_threshold_percent": 1.0,
            "min_languages": 1,
            "enable_detailed_logging": True,
            "skip_binary_files": True,
            "process_large_files": False,
            # New streaming performance settings
            "enable_streaming": True,
            "enable_early_termination": True,
            "max_matches_before_termination": 500,  # Stop processing after 500 total matches
            "chunk_size_kb": 64,  # For future chunked processing
        }
        
        # Override with request-specific config if available
        request_config = shared.get("request", {}).get("pattern_matching", {})
        config = {**default_config, **request_config}
        
        # Validate configuration
        config["max_files"] = max(50, min(config["max_files"], 2000))  # Between 50-2000
        config["max_file_size_mb"] = max(1, min(config["max_file_size_mb"], 50))  # Between 1-50 MB
        config["max_matches_per_file"] = max(10, min(config["max_matches_per_file"], 200))  # Between 10-200
        config["language_threshold_percent"] = max(0.5, min(config["language_threshold_percent"], 50.0))  # Between 0.5-50%
        
        return config

    def _get_improved_relevant_files(self, metadata: Dict[str, Any], file_type: str = "Source Code", gate_name: str = "", config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get files that are relevant with improved, less aggressive filtering"""
        all_files = [f for f in metadata.get("file_list", []) 
                    if f["type"] == file_type and not f["is_binary"]]
        
        # Additional filter to exclude documentation files
        doc_extensions = ['.md', '.txt', '.rst', '.adoc', '.asciidoc', '.doc', '.docx', '.pdf', '.rtf']
        doc_patterns = ['README', 'CHANGELOG', 'LICENSE', 'CONTRIBUTING', 'CONTRIBUTE']
        
        def is_doc_file(file_info):
            file_name = file_info.get("name", "").upper()
            file_ext = file_info.get("extension", "").lower()
            
            # Check for documentation extensions
            if file_ext in doc_extensions:
                return True
            
            # Check for documentation file names
            if any(pattern in file_name for pattern in doc_patterns):
                return True
            
            return False
        
        # Filter out documentation files
        relevant_files = [f for f in all_files if not is_doc_file(f)]
        
        # Use hardcoded defaults since pattern_loader is removed
        file_config = {
            "language_threshold_percent": 5.0,
            "config_threshold_percent": 2.0,
            "min_languages": 1,
            "test_threshold_multiplier": 0.8,
            "min_test_threshold": 5.0
        }
        
        tech_config = {
            "primary_languages": ["java", "python", "javascript", "typescript", "csharp", "go", "rust"],
            "config_languages": ["yaml", "json", "xml", "properties", "toml", "ini"],
            "web_languages": ["html", "css", "scss", "sass", "less"],
            "script_languages": ["bash", "sh", "ps1", "bat", "cmd"]
        }
        
        # Use global config defaults if none provided
        if config is None:
            config = {
                "language_threshold_percent": file_config.get("language_threshold_percent", 5.0),
                "config_threshold_percent": file_config.get("config_threshold_percent", 2.0),
                "min_languages": file_config.get("min_languages", 1),
                "test_threshold_multiplier": file_config.get("test_threshold_multiplier", 0.8),
                "min_test_threshold": file_config.get("min_test_threshold", 5.0)
            }
        
        # Get language statistics for intelligent filtering
        language_stats = metadata.get("language_stats", {})
        total_files = sum(stats.get("files", 0) for stats in language_stats.values())
        
        if not language_stats or total_files == 0:
            print(f"   No language statistics available, using all {len(all_files)} {file_type.lower()} files")
            return all_files
        
        # Get technology categories from global config
        primary_languages = set(tech_config.get("primary_languages", ["java", "python", "javascript", "typescript", "csharp", "go", "rust"]))
        config_languages = set(tech_config.get("config_languages", ["yaml", "json", "xml", "properties", "toml", "ini"]))
        web_languages = set(tech_config.get("web_languages", ["html", "css", "scss", "sass", "less"]))
        script_languages = set(tech_config.get("script_languages", ["bash", "sh", "ps1", "bat", "cmd"]))
        
        # Calculate language percentages
        language_percentages = {}
        for language, stats in language_stats.items():
            file_count = stats.get("files", 0)
            percentage = (file_count / total_files) * 100
            language_percentages[language] = percentage
        
        # Determine relevant languages based on gate type and configurable thresholds
        relevant_languages = set()
        
        # Get configurable thresholds
        primary_threshold = config["language_threshold_percent"]
        config_threshold = config["config_threshold_percent"]
        
        # Gate-specific logic for better relevance
        if gate_name in ["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS", "AUDIT_TRAIL", "LOG_API_CALLS", "LOG_APPLICATION_MESSAGES", "ERROR_LOGS"]:
            # Logging-related gates: include primary languages + config files
            for language, percentage in language_percentages.items():
                if language in primary_languages and percentage >= primary_threshold:
                    relevant_languages.add(language)
                elif language in config_languages and percentage >= config_threshold:
                    relevant_languages.add(language)
        elif gate_name in ["UI_ERRORS", "UI_ERROR_TOOLS"]:
            # UI-related gates: include web languages + primary languages
            for language, percentage in language_percentages.items():
                if language in web_languages and percentage >= config_threshold:
                    relevant_languages.add(language)
                elif language in primary_languages and percentage >= primary_threshold:
                    relevant_languages.add(language)
        elif gate_name == "AUTOMATED_TESTS":
            # Test-related gates: include all primary languages with lower threshold
            test_threshold = max(primary_threshold * config.get("test_threshold_multiplier", 0.8), config.get("min_test_threshold", 5.0))
            for language, percentage in language_percentages.items():
                if language in primary_languages and percentage >= test_threshold:
                    relevant_languages.add(language)
        else:
            # Other gates: include primary languages with configurable threshold
            for language, percentage in language_percentages.items():
                if language in primary_languages and percentage >= primary_threshold:
                    relevant_languages.add(language)
                elif language in script_languages and percentage >= config_threshold * 2:
                    relevant_languages.add(language)
        
        # If no languages meet the threshold, include the most dominant ones
        if not relevant_languages:
            sorted_languages = sorted(language_percentages.items(), key=lambda x: x[1], reverse=True)
            
            # Include top languages or languages with >2% representation
            min_languages = config.get("min_languages", 1)
            for language, percentage in sorted_languages[:max(min_languages, 3)]:
                if language in primary_languages or percentage >= 2.0:
                    relevant_languages.add(language)
        
        # Always include the dominant language if it's a primary language
        if language_percentages:
            dominant_language = max(language_percentages.items(), key=lambda x: x[1])[0]
            if dominant_language in primary_languages:
                relevant_languages.add(dominant_language)
        
        # Filter files to include relevant languages
        if relevant_languages:
            relevant_files = [f for f in all_files 
                             if f["language"] in relevant_languages]
        else:
            # Fallback: use all files if no relevant languages found
            relevant_files = all_files
        
        # Sort files by relevance (prioritize larger files and common patterns)
        relevant_files.sort(key=lambda f: (
            f["language"] in primary_languages,  # Primary languages first
            f["size"],  # Larger files first
            not f["relative_path"].startswith("test"),  # Non-test files first (except for test gates)
            f["relative_path"]  # Alphabetical as tiebreaker
        ), reverse=True)
        
        # Report filtering results
        relevant_langs_str = ", ".join(sorted(relevant_languages))
        print(f"   Relevant languages: {relevant_langs_str}")
        print(f"   Filtered to {len(relevant_files)} relevant files (from {len(all_files)} total {file_type.lower()} files)")
        
        # Show percentage breakdown
        if len(all_files) > 0:
            coverage_percentage = (len(relevant_files) / len(all_files)) * 100
            print(f"   Coverage: {coverage_percentage:.1f}% of {file_type.lower()} files")
        
        return relevant_files

    def _generate_gates_table_html_from_new_data(self, gate_results: List[Dict[str, Any]]) -> str:
        """Generate gates table HTML from new data structure with proper categories and table format"""
        
        if not gate_results:
            return "<p>No gate results available.</p>"
        
        # Use the predefined 4 categories
        predefined_categories = {
            'Alerting': ['ALERTING_ACTIONABLE'],
            'Auditability': ['STRUCTURED_LOGS', 'AVOID_LOGGING_SECRETS', 'AUDIT_TRAIL', 'CORRELATION_ID', 'LOG_API_CALLS', 'LOG_APPLICATION_MESSAGES', 'UI_ERRORS'],
            'Availability': ['RETRY_LOGIC', 'TIMEOUTS', 'THROTTLING', 'CIRCUIT_BREAKERS', 'AUTO_SCALE'],
            'Error Handling': ['ERROR_LOGS', 'HTTP_CODES', 'UI_ERROR_TOOLS'],
            'Testing': ['AUTOMATED_TESTS']
        }
        
        # Group gates by predefined categories
        categories = {}
        for category_name, gate_names in predefined_categories.items():
            categories[category_name] = []
            for gate in gate_results:
                if gate.get("gate") in gate_names:
                    categories[category_name].append(gate)
        
        html_parts = []
        html_parts.append('<div class="gates-analysis">')
        
        # Generate HTML for each predefined category (always show all 4)
        for category_name, gates in categories.items():
            html_parts.append(f'''
                <div class="gate-category-section">
                    <h3 class="category-title">{category_name}</h3>
                    <div class="category-content">
                        <table class="gates-table">
                            <thead>
                                <tr>
                                    <th style="width: 80px">Gate #</th>
                                    <th>Practice</th>
                                    <th>Status</th>
                                    <th>Evidence</th>
                                    <th>Recommendation</th>
                                </tr>
                            </thead>
                            <tbody>''')
            
            if gates:
                # Generate rows for each gate in this category
                for i, gate in enumerate(gates):
                    try:
                        gate_name = gate.get("gate", "Unknown")
                        display_name = gate.get("display_name", gate_name)
                        description = gate.get("description", "")
                        priority = gate.get("priority", "medium")
                        score = gate.get("score", 0.0)
                        status = gate.get("status", "UNKNOWN")
                        matches_found = gate.get("matches_found", 0)
                        matches = gate.get("matches", [])
                        details = gate.get("details", [])
                        recommendations = gate.get("recommendations", [])
                        
                        # Ensure details and recommendations are lists
                        if not isinstance(details, list):
                            details = [str(details)] if details else []
                        if not isinstance(recommendations, list):
                            recommendations = [str(recommendations)] if recommendations else []
                        if not isinstance(matches, list):
                            matches = []
                        
                        # Get status info
                        status_info = self._get_status_info_from_new_data(status, gate)
                        
                        # Format evidence
                        evidence = self._format_evidence_from_new_data(gate)
                        
                        # Get recommendation
                        recommendation = self._get_recommendation_from_new_data(gate)
                        
                        # Generate metrics for details
                        metrics_html = self._generate_gate_metrics_html(gate)
                        
                        # Generate details content
                        details_content = self._generate_gate_details_content(gate, matches, details, recommendations)
                        
                        # Generate the table row
                        gate_html = f'''
                                    <tr>
                                        <td style="text-align: center">
                                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                                <button class="details-toggle" onclick="toggleDetails(this, 'details-{category_name.lower().replace(' ', '-')}-{gate_name}-{i}')" aria-expanded="false" aria-label="Show details for {display_name}">+</button>
                                                <span style="font-weight: bold; color: #374151; font-size: 0.9em;">{get_gate_number(gate_name)}</span>
                                            </div>
                                        </td>
                                        <td><strong>{display_name}</strong></td>
                                        <td><span class="status-{status.lower()}">{status_info.get('display', status)}</span></td>
                                        <td>{evidence}</td>
                                        <td>{recommendation}</td>
                                    </tr>
                                    <tr id="details-{category_name.lower().replace(' ', '-')}-{gate_name}-{i}" class="gate-details" aria-hidden="true">
                                        <td colspan="5" class="details-content">
                                            {metrics_html}
                                            {details_content}
                                        </td>
                                    </tr>'''
                        
                        html_parts.append(gate_html)
                        
                    except Exception as e:
                        print(f"Warning: Error generating HTML for gate {gate.get('gate', 'unknown')}: {e}")
                        # Add a fallback gate HTML
                        fallback_html = f'''
                                    <tr>
                                        <td style="text-align: center">
                                            <button class="details-toggle" onclick="toggleDetails(this, 'details-{category_name.lower().replace(' ', '-')}-unknown-{i}')" aria-expanded="false" aria-label="Show details for Unknown Gate">+</button>
                                        </td>
                                        <td><strong>{gate.get('display_name', 'Unknown Gate')}</strong></td>
                                        <td><span class="status-unknown">UNKNOWN</span></td>
                                        <td>Error processing gate data</td>
                                        <td>Unable to generate recommendation</td>
                                    </tr>
                                    <tr id="details-{category_name.lower().replace(' ', '-')}-unknown-{i}" class="gate-details" aria-hidden="true">
                                        <td colspan="5" class="details-content">
                                            <div class="details-section">
                                                <div class="details-section-title">Error:</div>
                                                <p>Unable to process gate data due to an error: {e}</p>
                                            </div>
                                        </td>
                                    </tr>'''
                        
                        html_parts.append(fallback_html)
            else:
                # Add a message for empty categories
                html_parts.append(f'''
                                    <tr>
                                        <td colspan="5" style="text-align: center; color: #6b7280; padding: 20px;">
                                            <em>No gates in this category were evaluated for this codebase.</em>
                                        </td>
                                    </tr>''')
            
            html_parts.append('''
                            </tbody>
                        </table>
                    </div>
                </div>''')
        
        html_parts.append('</div>')
        
        return "\n".join(html_parts)
    
    def _generate_gate_metrics_html(self, gate: Dict[str, Any]) -> str:
        """Generate metrics HTML for a gate with simple, elegant boxes"""
        score = gate.get("score", 0.0)
        status = gate.get("status", "FAIL")
        patterns_used = gate.get("patterns_used", 0)
        matches_found = gate.get("matches_found", 0)
        relevant_files = gate.get("relevant_files", 0)
        total_files = gate.get("total_files", 1)
        
        # Get enhanced data if available
        enhanced_data = gate.get("enhanced_data", {})
        criteria_score = enhanced_data.get("criteria_score", None)
        coverage_score = enhanced_data.get("coverage_score", None)
        condition_results = enhanced_data.get("condition_results", [])
        
        # Core metrics boxes
        metrics_html = f"""
        <div class="gate-metrics">
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-label">Score</div>
                    <div class="metric-value score-{status.lower()}">{score:.1f}%</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Status</div>
                    <div class="metric-value status-{status.lower()}">{status}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Patterns</div>
                    <div class="metric-value">{patterns_used}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Matches</div>
                    <div class="metric-value">{matches_found}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Relevant Files</div>
                    <div class="metric-value">{relevant_files}/{total_files}</div>
                </div>
            </div>
        </div>
        """
        
        # Add enhanced metrics if available
        if criteria_score is not None or coverage_score is not None:
            metrics_html += f"""
            <div class="enhanced-metrics">
                <h4>Enhanced Evaluation Metrics</h4>
                <div class="metrics-grid">
            """
            
            if criteria_score is not None:
                metrics_html += f"""
                    <div class="metric-box">
                        <div class="metric-label">Criteria Score</div>
                        <div class="metric-value">{criteria_score:.1f}%</div>
                    </div>
                """
            
            if coverage_score is not None:
                metrics_html += f"""
                    <div class="metric-box">
                        <div class="metric-label">Coverage Score</div>
                        <div class="metric-value">{coverage_score:.1f}%</div>
                    </div>
                """
            
            metrics_html += """
                </div>
            """
            
            # Add condition results if available
            if condition_results:
                metrics_html += """
                <div class="condition-results">
                    <h5>Condition Results:</h5>
                    <div class="condition-list">
                """
                
                for condition in condition_results:
                    condition_name = condition.get("name", "unknown")
                    condition_type = condition.get("type", "pattern")
                    operator = condition.get("operator", "OR")
                    passed = condition.get("passed", False)
                    weight = condition.get("weight", 1.0)
                    matches_count = condition.get("matches_count", 0)
                    
                    status_icon = "✅" if passed else "❌"
                    status_class = "condition-pass" if passed else "condition-fail"
                    
                    metrics_html += f"""
                    <div class="condition-item {status_class}">
                        <div class="condition-header">
                            <span class="condition-icon">{status_icon}</span>
                            <span class="condition-name">{condition_name}</span>
                            <span class="condition-type">({condition_type})</span>
                        </div>
                        <div class="condition-details">
                            <span class="condition-matches">{matches_count} matches</span>
                            <span class="condition-weight">weight: {weight:.1f}</span>
                        </div>
                    </div>
                    """
                
                metrics_html += """
                    </div>
                </div>
                """
            
            metrics_html += "</div>"
        
        return metrics_html
    
    def _generate_gate_details_content(self, gate: Dict[str, Any], matches: List[Dict[str, Any]], details: List[str], recommendations: List[str]) -> str:
        """Generate detailed content for gate expandable section (robust, context-aware, no contradictions)"""
        gate_name = gate.get("gate", "Unknown")
        display_name = gate.get("display_name", gate_name)
        description = gate.get("description", "")
        category = gate.get("category", "Unknown")
        priority = gate.get("priority", "medium")
        status = gate.get("status", "UNKNOWN")
        score = gate.get("score", 0.0)
        matches_found = gate.get("matches_found", 0)
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        confidence = expected_coverage.get("confidence", "medium")
        max_files_expected = expected_coverage.get("max_files_expected", relevant_files)
        patterns = gate.get("patterns", [])
        num_patterns = len(patterns) if isinstance(patterns, list) else 0
        # Only count files if file info is present in matches
        files_with_matches = len(set(m['file'] for m in matches if m.get('file'))) if matches else 0

        # 1. Summary section
        summary_color = "#6b7280"
        summary_icon = "?"
        if status == "PASS":
            summary_color = "#059669"  # green
            summary_icon = "✓"
        elif status == "WARNING":
            summary_color = "#d97706"  # orange
            summary_icon = "⚬"
        elif status == "FAIL":
            summary_color = "#dc2626"  # red
            summary_icon = "✗"
        elif status == "NOT_APPLICABLE":
            summary_color = "#6b7280"  # gray
            summary_icon = "?"
        # Remove summary text for no patterns/matches
        summary_text = ""
        if status == "NOT_APPLICABLE":
            summary_text = "Not applicable to this technology stack."
        elif matches_found == 0 and status == "PASS":
            summary_text = "No issues found. This gate is fully implemented."
        elif matches_found > 0 and status == "FAIL":
            summary_text = f"{matches_found} issue{'s' if matches_found != 1 else ''} found in {files_with_matches} file{'s' if files_with_matches != 1 else ''}"
        elif status == "WARNING":
            summary_text = f"Partial implementation. {matches_found} issue{'s' if matches_found != 1 else ''} remain."
        elif matches_found == 0 and status == "FAIL":
            summary_text = "No matches found for this gate."
        summary_html = f'''
        <!--<div class="details-section" style="background: #f8fafc; border-left: 5px solid {summary_color}; margin-bottom: 10px;">
            <div style="font-size: 1.1em; font-weight: 600; color: {summary_color}; margin-bottom: 4px;"><span style=\"color: {summary_color};\">{summary_icon} {summary_text}</span></div>
        </div>-->''' if summary_text else ""

        # 2. Patterns Used section (removed if 0 patterns)
        patterns_used_html = ""
        # 3. Matches Found section (removed if 0 patterns)
        matches_found_html = ""
        # 4. Sample Matches section (up to 3)
        sample_matches_html = ""
        if num_patterns > 0 and matches_found > 0:
            sample_matches_html = '''<div class="details-section"><div class="details-section-title">Sample Matches:</div><ul style="margin-bottom: 0;">'''
            for match in matches[:3]:
                file_path = match.get("file", "Unknown")
                line_number = match.get("line", "Unknown")
                pattern_match = match.get("match", "Unknown")
                sample_matches_html += f'<li><span style="font-family: monospace; color: #1f2937;">{file_path}:{line_number}</span> &rarr; <span style="font-family: monospace; color: #059669; background: #ecfdf5; border-radius: 3px; padding: 2px 4px;">{pattern_match}</span></li>'
            if matches_found > 3:
                sample_matches_html += f'<li style="color: #6b7280;">... and {matches_found - 3} more matches</li>'
            sample_matches_html += '</ul></div>'

        # 5. Matched patterns and files (full table, up to 100) (removed if 0 patterns)
        matched_patterns_html = ""
        if num_patterns > 0 and matches_found > 0:
            matched_patterns_html = f'''
            <div class="details-section" style="overflow-x: auto;">
                <div class="details-section-title">All Matched Patterns and Files:</div>
                <div style="max-height: 300px; overflow-y: auto; overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb;">
                    <table style="width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 0.9em;">
                        <thead>
                            <tr style="background: #f3f4f6;">
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 350px; white-space: pre-line;">File</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 80px; white-space: pre-line;">Line</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 250px; white-space: pre-line;">Pattern Match</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 250px; white-space: pre-line;">Actual Pattern</th>
                            </tr>
                        </thead>
                        <tbody>'''
            for match in matches[:100]:
                file_path = match.get("file", "Unknown")
                line_number = match.get("line", "Unknown")
                pattern_match = match.get("match", "Unknown")
                actual_pattern = match.get("pattern", "Unknown")
                matched_patterns_html += f'''
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; color: #1f2937; word-break: break-all; max-width: 350px; white-space: pre-line;">{file_path}</td>
                                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center; color: #6b7280; word-break: break-all; max-width: 80px; white-space: pre-line;">{line_number}</td>
                                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; color: #059669; background: #ecfdf5; border-radius: 3px; word-break: break-all; max-width: 250px; white-space: pre-line;">{pattern_match}</td>
                                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; color: #374151; background: #f3f4f6; border-radius: 3px; word-break: break-all; max-width: 250px; white-space: pre-line;">{actual_pattern}</td>
                                </tr>'''
            matched_patterns_html += '''
                        </tbody>
                    </table>
                </div>
            </div>'''

        # Splunk Reference Section (after sample matches)
        splunk_html = ""
        splunk_reference = gate.get("splunk_reference", {})
        if splunk_reference and splunk_reference.get("influenced"):
            splunk_query = splunk_reference.get("query", "")
            splunk_job_id = splunk_reference.get("job_id", "")
            splunk_message = splunk_reference.get("message", "")
            splunk_html = f'''
            <div class="details-section" style="background: #f3f4f6; border-left: 4px solid #4f46e5; margin-top: 10px;">
                <div class="details-section-title">Splunk Reference</div>
                <ul>
                    <li><strong>Query:</strong> <span style="font-family: monospace;">{splunk_query}</span></li>
                    <li><strong>Job ID:</strong> {splunk_job_id}</li>
                    <li><strong>Splunk Influence:</strong> Yes</li>
                    <li><strong>Message:</strong> {splunk_message}</li>
                </ul>
            </div>'''

        # 6. Recommendations (actionable)
        recommendations_html = ""
        if recommendations:
            filtered_recommendations = [
                rec for rec in recommendations
                if 'Achieved:' not in rec and 'Exceeds expectations' not in rec and 'coverage' not in rec.lower()
            ]
            if filtered_recommendations:
                recommendations_html = f'''<div class=\"details-section\"><div class=\"details-section-title\">Recommendations:</div><ul>{''.join([f'<li>{rec}</li>' for rec in filtered_recommendations[:5]])}</ul></div>'''

        # 7. Gate info (category, priority, description)
        gate_info_html = f'''
        <div class="details-section">
            <div class="details-section-title">Gate Information:</div>
            <ul>
                <li><strong>Category:</strong> {category}</li>
                <li><strong>Priority:</strong> {priority}</li>
                <li><strong>Description:</strong> {description}</li>
            </ul>
        </div>'''

        # Compose all sections in a logical order, but omit coverage_html and all 0-pattern/match sections
        return (
            summary_html +
            sample_matches_html +
            splunk_html +
            matched_patterns_html +
            recommendations_html +
            gate_info_html
        )

    def _generate_applicability_summary_html(self, applicability_summary: Dict[str, Any]) -> str:
        """Generate applicability summary HTML"""
        
        if not applicability_summary:
            return ""
        
        applicable_gates = applicability_summary.get("applicable_gates", [])
        not_applicable_gates = applicability_summary.get("not_applicable_gates", [])
        
        # Ensure these are lists, not integers
        if not isinstance(applicable_gates, list):
            applicable_gates = []
        if not isinstance(not_applicable_gates, list):
            not_applicable_gates = []
        
        html = """
        <h3>Gate Applicability</h3>
        <div class="applicability-summary">
        """
        
        if applicable_gates:
            html += f"""
            <div class="applicable-gates">
                <h4>Applicable Gates ({len(applicable_gates)})</h4>
                <ul>
                    {''.join([f'<li>{gate.get("display_name", gate.get("gate", "Unknown"))}</li>' for gate in applicable_gates])}
                </ul>
            </div>
            """
        
        if not_applicable_gates:
            html += f"""
            <div class="not-applicable-gates">
                <h4>Not Applicable Gates ({len(not_applicable_gates)})</h4>
                <ul>
                    {''.join([f'<li>{gate.get("display_name", gate.get("gate", "Unknown"))}</li>' for gate in not_applicable_gates])}
                </ul>
            </div>
            """
        
        html += """
        </div>
        """
        
        return html

    def _get_primary_technologies(self, metadata: Dict[str, Any]) -> List[str]:
        """Get primary technologies from metadata"""
        language_stats = metadata.get("language_stats", {})
        total_files = metadata.get("total_files", 1)
        
        # Use hardcoded defaults since pattern_loader is removed
        primary_languages = set(["java", "python", "javascript", "typescript", "csharp", "go", "rust"])
        primary_threshold = 20.0
        secondary_threshold = 10.0
        
        primary_technologies = []
        
        # Find languages that make up significant portion of the codebase
        for language, stats in language_stats.items():
            file_count = stats.get("files", 0)
            percentage = (file_count / total_files) * 100
            
            if language in primary_languages and percentage >= primary_threshold:
                primary_technologies.append(language)
        
        # If no primary technology found, take the most dominant
        if not primary_technologies:
            dominant_primary = None
            max_percentage = 0
            
            for language, stats in language_stats.items():
                if language in primary_languages:
                    file_count = stats.get("files", 0)
                    percentage = (file_count / total_files) * 100
                    if percentage > max_percentage and percentage >= secondary_threshold:
                        max_percentage = percentage
                        dominant_primary = language
            
            if dominant_primary:
                primary_technologies.append(dominant_primary)
        
        return primary_technologies

    def _extract_app_id(self, repository_url: str) -> str:
        """Extract App Id from repository URL using /app-XYZ/ pattern. Returns XYZ or <APP> if not found."""
        import re
        try:
            # Remove .git if present
            if repository_url.endswith('.git'):
                repository_url = repository_url[:-4]
            # Find /app-XYZ or /app-XYZ/ in the path
            match = re.search(r"/app-([A-Za-z0-9_-]+)(/|$)", repository_url)
            if match:
                return match.group(1)
            else:
                return "APP ID"
        except Exception:
            return "APP ID"


class CleanupNode(Node):
    """Node to cleanup temporary files and directories"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare cleanup parameters"""
        return {
            "temp_dir": shared["temp_dir"],
            "repo_path": shared["repository"]["local_path"]
        }
    
    def exec(self, params: Dict[str, Any]) -> bool:
        """Cleanup temporary files"""
        print("🧹 Cleaning up temporary files...")
        
        try:
            if params["repo_path"] and os.path.exists(params["repo_path"]):
                cleanup_repository(params["repo_path"])
            
            if params["temp_dir"] and os.path.exists(params["temp_dir"]):
                import shutil
                shutil.rmtree(params["temp_dir"])
                print(f"🧹 Cleaned up temp directory: {params['temp_dir']}")
            
            return True
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
            return False
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: bool) -> str:
        """Mark cleanup complete"""
        if exec_res:
            print("✅ Cleanup completed successfully")
        else:
            shared["errors"].append("Cleanup failed")
        
        return "default" 
    def _generate_simplified_prompt(self, data: Dict[str, Any]) -> str:
        """Generate a simplified prompt for local LLMs"""
        print("📋 Generating simplified LLM prompt for local LLM...")
        
        prompt_parts = []
        
        prompt_parts.append("You are a code analyzer. Generate regex patterns for hard gate validation.")
        prompt_parts.append("")
        
        # Basic repository info
        metadata = data["metadata"]
        prompt_parts.append(f"Repository: {data['repo_url']}")
        prompt_parts.append(f"Languages: {', '.join(metadata.get('languages', {}).keys())}")
        prompt_parts.append("")
        
        # Hard gates
        prompt_parts.append("Generate patterns for these gates:")
        for gate in data["hard_gates"]:
            prompt_parts.append(f"- {gate['name']}: {gate['description']}")
        prompt_parts.append("")
        
        # Simple instructions
        prompt_parts.append("Provide JSON response with patterns for each gate:")
        prompt_parts.append("```json")
        prompt_parts.append("{")
        prompt_parts.append('  "GATE_NAME": {')
        prompt_parts.append('    "patterns": ["r\'pattern1\'", "r\'pattern2\'"],')
        prompt_parts.append('    "description": "Brief description",')
        prompt_parts.append('    "expected_coverage": {')
        prompt_parts.append('      "percentage": 10,')
        prompt_parts.append('      "reasoning": "Brief reasoning"')
        prompt_parts.append('    }')
        prompt_parts.append('  }')
        prompt_parts.append("}")
        prompt_parts.append("```")
        
        return "\n".join(prompt_parts)


class SplunkQueryNode(Node):
    """Node to execute Splunk queries and analyze results during scan"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare Splunk query parameters"""
        return {
            "splunk_query": shared["request"].get("splunk_query"),
            "app_id": shared["request"].get("app_id"),
            "scan_id": shared["request"]["scan_id"]
        }
    
    def exec(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Splunk query and analyze results"""
        splunk_query = params.get("splunk_query")
        app_id = params.get("app_id")
        scan_id = params.get("scan_id")
        
        if not splunk_query:
            print("📊 No Splunk query provided - skipping Splunk analysis")
            return {
                "status": "skipped",
                "message": "No Splunk query provided",
                "results": [],
                "analysis": {},
                "execution_time": 0
            }
        
        print(f"🔍 Executing Splunk query for scan {scan_id}...")
        print(f"   Query: {splunk_query}")
        if app_id:
            print(f"   App ID: {app_id}")
        
        try:
            # Import Splunk integration
            from utils.splunk_integration import execute_splunk_query
            
            # Execute the query
            import time
            start_time = time.time()
            
            result = execute_splunk_query(splunk_query, app_id)
            
            execution_time = time.time() - start_time
            
            # Add execution time to result
            result["execution_time"] = execution_time
            
            if result["status"] == "success":
                print(f"✅ Splunk query executed successfully in {execution_time:.2f}s")
                print(f"   Results: {result.get('total_results', 0)} events")
                
                # Log analysis summary
                analysis = result.get("analysis", {})
                if analysis:
                    print(f"   Analysis: {analysis.get('total_events', 0)} total events")
                    print(f"   Errors: {analysis.get('error_count', 0)}")
                    print(f"   Warnings: {analysis.get('warning_count', 0)}")
                    print(f"   Info: {analysis.get('info_count', 0)}")
                    
                    error_types = analysis.get("error_types", [])
                    if error_types:
                        print(f"   Error types: {', '.join(error_types)}")
            else:
                print(f"⚠️ Splunk query failed: {result.get('message', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            print(f"❌ Splunk query execution failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Splunk query execution failed: {str(e)}",
                "results": [],
                "analysis": {},
                "execution_time": 0
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Store Splunk results in shared data"""
        shared["splunk"] = exec_res
        
        if exec_res["status"] == "success":
            return f"Splunk analysis completed: {exec_res.get('total_results', 0)} events analyzed"
        elif exec_res["status"] == "skipped":
            return "Splunk analysis skipped - no query provided"
        else:
            return f"Splunk analysis failed: {exec_res.get('message', 'Unknown error')}"

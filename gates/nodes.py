"""
CodeGates Nodes - PocketFlow Implementation
All nodes for the hard gate validation workflow
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from pocketflow import Node 

# Import utilities
from utils.git_operations import clone_repository, cleanup_repository
from utils.file_scanner import scan_directory
from utils.hard_gates import HARD_GATES
from utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider
from utils.static_patterns import get_static_patterns_for_gate, get_pattern_statistics


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
        """Clone the repository"""
        print(f"🔄 Fetching repository: {params['repository_url']}")
        
        # Create a more robust target directory
        temp_dir = params["temp_dir"]
        if not temp_dir or not os.path.exists(temp_dir):
            raise Exception(f"Invalid temp directory: {temp_dir}")
        
        target_dir = os.path.join(temp_dir, "repository")
        
        # Ensure the target directory path is valid
        try:
            os.makedirs(target_dir, exist_ok=True)
            print(f"📁 Target directory created: {target_dir}")
        except Exception as e:
            raise Exception(f"Failed to create target directory {target_dir}: {e}")
        
        repo_path = clone_repository(
            repo_url=params["repository_url"],
            branch=params["branch"],
            github_token=params["github_token"],
            target_dir=target_dir
        )
        
        return repo_path
    
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
                prompt_parts.append(info["content"][:500])  # First 500 chars for config files
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
        prompt_parts.append("## OUTPUT FORMAT")
        prompt_parts.append("Provide a JSON response with patterns, descriptions, significance, and expected coverage analysis for each gate:")
        prompt_parts.append("```json")
        prompt_parts.append("{")
        prompt_parts.append('  "GATE_NAME": {')
        prompt_parts.append('    "patterns": ["pattern1_regex", "pattern2_regex"],')
        prompt_parts.append('    "description": "Brief description of what these patterns meant to the gate and why it was suggested",')
        prompt_parts.append('    "significance": "Why the patterns are significant for this codebase and technology stack",')
        prompt_parts.append('    "expected_coverage": {')
        prompt_parts.append('      "percentage": 25,')
        prompt_parts.append('      "reasoning": "Based on the project structure and libraries, approximately 25% of files should implement this pattern",')
        prompt_parts.append('      "confidence": "high"')
        prompt_parts.append('    }')
        prompt_parts.append('  },')
        prompt_parts.append('  "ANOTHER_GATE": {')
        prompt_parts.append('    "patterns": ["pattern3_regex"],')
        prompt_parts.append('    "description": "Brief description of what these patterns meant to the gate and why it was suggested",')
        prompt_parts.append('    "significance": "Why the patterns are significant for this codebase and technology stack",')
        prompt_parts.append('    "expected_coverage": {')
        prompt_parts.append('      "percentage": 10,')
        prompt_parts.append('      "reasoning": "This pattern is typically found in configuration files and middleware, affecting about 10% of the codebase",')
        prompt_parts.append('      "confidence": "medium"')
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
        prompt_parts.append("Focus on patterns that are:")
        prompt_parts.append("- Specific to the detected technology stack and libraries used")
        prompt_parts.append("- Consider all common patterns and keywords as applicable")
        prompt_parts.append("- Comprehensive in coverage")
        prompt_parts.append("- Practical for real-world codebases")
        prompt_parts.append("- Security and compliance-focused")
        prompt_parts.append("- Contextually aware of the project structure and organization")
        prompt_parts.append("")
        prompt_parts.append("For each gate, provide:")
        prompt_parts.append("- **patterns**: Array of regex patterns as many as possible for the technology. Consider the libraries used for coming up with the relevant implementation as well. Usage like import should also be considered. Consider all known keywords and patterns as applicable.")
        prompt_parts.append("- **description**: 1-2 sentence explanation of reason of why the patterns suggested")
        prompt_parts.append("- **significance**: 2-3 sentence explanation of why the patterns matters for the specific technology stack and libraries used and project type")
        prompt_parts.append("- **expected_coverage**: Intelligent analysis of expected coverage based on:")
        prompt_parts.append("  - **percentage**: Expected percentage of files that should contain this pattern (0-100)")
        prompt_parts.append("  - **reasoning**: Detailed explanation of why this coverage percentage is expected based on:")
        prompt_parts.append("    - Project architecture and structure")
        prompt_parts.append("    - Technology stack and frameworks used")
        prompt_parts.append("    - Library dependencies and their typical usage patterns")
        prompt_parts.append("    - File types and their distribution")
        prompt_parts.append("    - Common implementation patterns for this gate type")
        prompt_parts.append("  - **confidence**: Confidence level in the estimate (high/medium/low)")
        prompt_parts.append("")
        prompt_parts.append("**COVERAGE ANALYSIS GUIDELINES:**")
        prompt_parts.append("- Consider the specific technology stack: different frameworks have different patterns")
        prompt_parts.append("- Account for project size and complexity: larger projects may have lower percentages but higher absolute counts")
        prompt_parts.append("- Factor in architectural patterns: microservices vs monolith affects distribution")
        prompt_parts.append("- Consider file type distribution: some patterns only apply to specific file types")
        prompt_parts.append("- Account for library usage: imported libraries may provide built-in implementations")
        prompt_parts.append("- Be realistic: not every file needs every pattern, estimate based on actual usage scenarios")
        prompt_parts.append("- Provide reasoning that shows understanding of the codebase structure and technology choices")
        
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
            
            # Create logs directory if it doesn't exist
            logs_dir = "logs"
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
                        max_tokens=llm_config.get("max_tokens", 4000)
                    )
                    
                    llm_client = LLMClient(config)
                    
                except Exception as e:
                    print(f"⚠️ Failed to create LLM client from config: {e}")
                    llm_client = None
        
        # If we have a working LLM client, use it
        if llm_client and llm_client.is_available():
            try:
                print(f"🔗 Using {llm_client.config.provider.value} LLM provider")
                print(f"   Model: {llm_client.config.model}")
                
                response = llm_client.call_llm(params["prompt"])
                
                # Try to parse JSON response with enhanced format
                pattern_data = self._parse_enhanced_llm_response(response)
                
                return {
                    "success": True,
                    "pattern_data": pattern_data,
                    "source": llm_client.config.provider.value,
                    "model": llm_client.config.model,
                    "response": response[:500] + "..." if len(response) > 500 else response
                }
                
            except Exception as e:
                print(f"⚠️ LLM call failed: {e}")
                # Fall back to pattern generation
                pass
        
        # Fallback to pattern generation
        print("🔄 LLM not available, using fallback pattern generation")
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
        
        # Log the LLM response
        try:
            import os
            from datetime import datetime
            
            # Create logs directory if it doesn't exist
            logs_dir = "logs"
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
        """Parse LLM response to extract patterns with descriptions, significance, and expected coverage"""
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
            raw_data = json.loads(json_str)
            
            # Validate and structure the data
            pattern_data = {}
            for gate_name, gate_info in raw_data.items():
                if isinstance(gate_info, dict):
                    # Enhanced format with expected coverage
                    expected_coverage = gate_info.get("expected_coverage", {})
                    if isinstance(expected_coverage, dict):
                        coverage_data = {
                            "percentage": expected_coverage.get("percentage", 10),  # Default 10%
                            "reasoning": expected_coverage.get("reasoning", "Standard expectation for this gate type"),
                            "confidence": expected_coverage.get("confidence", "medium")
                        }
                    else:
                        # Fallback if expected_coverage is not a dict
                        coverage_data = {
                            "percentage": 10,
                            "reasoning": "Standard expectation for this gate type",
                            "confidence": "medium"
                        }
                    
                    pattern_data[gate_name] = {
                        "patterns": gate_info.get("patterns", []),
                        "description": gate_info.get("description", "Pattern analysis for this gate"),
                        "significance": gate_info.get("significance", "Important for code quality and compliance"),
                        "expected_coverage": coverage_data
                    }
                elif isinstance(gate_info, list):
                    # Old format - just patterns
                    pattern_data[gate_name] = {
                        "patterns": gate_info,
                        "description": "Pattern analysis for this gate",
                        "significance": "Important for code quality and compliance",
                        "expected_coverage": {
                            "percentage": 10,
                            "reasoning": "Standard expectation for this gate type",
                            "confidence": "medium"
                        }
                    }
                else:
                    # Single pattern
                    pattern_data[gate_name] = {
                        "patterns": [str(gate_info)] if gate_info else [],
                        "description": "Pattern analysis for this gate",
                        "significance": "Important for code quality and compliance",
                        "expected_coverage": {
                            "percentage": 10,
                            "reasoning": "Standard expectation for this gate type",
                            "confidence": "medium"
                        }
                    }
            
            return pattern_data
            
        except Exception as e:
            print(f"⚠️ Failed to parse enhanced LLM response: {e}")
            print(f"Response preview: {response[:200]}...")
            # Return fallback patterns
            return self._generate_fallback_pattern_data()
    
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
        """Prepare validation parameters"""
        return {
            "repo_path": shared["repository"]["local_path"],
            "metadata": shared["repository"]["metadata"],
            "patterns": shared["llm"]["patterns"],
            "pattern_data": shared["llm"].get("pattern_data", {}),
            "hard_gates": shared["hard_gates"],
            "threshold": shared["request"]["threshold"]
        }
    
    def exec(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate all gates against the codebase using hybrid pattern validation"""
        print("🎯 Validating gates against codebase with hybrid pattern validation...")
        
        repo_path = Path(params["repo_path"])
        llm_patterns = params["patterns"]
        pattern_data = params["pattern_data"]
        metadata = params["metadata"]
        
        # Get primary technologies for static pattern selection
        primary_technologies = self._get_primary_technologies(metadata)
        
        gate_results = []
        
        # Validate each gate (Map phase)
        for gate in params["hard_gates"]:
            gate_name = gate["name"]
            llm_gate_patterns = llm_patterns.get(gate_name, [])
            gate_pattern_info = pattern_data.get(gate_name, {})
            
            print(f"   Validating {gate_name} with hybrid patterns...")
            
            # Check if gate is not applicable
            is_not_applicable = (
                gate_pattern_info.get("description", "").strip() == "Not Applicable" or
                (len(llm_gate_patterns) == 0 and gate_pattern_info.get("significance", "").find("not applicable") != -1)
            )
            
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
                    "details": ["This gate is not applicable to the current technology stack and project type"],
                    "recommendations": ["Not applicable to this project type"],
                    "pattern_description": gate_pattern_info.get("description", "Not Applicable"),
                    "pattern_significance": gate_pattern_info.get("significance", "This gate is not applicable to the current technology stack and project type"),
                    "expected_coverage": gate_pattern_info.get("expected_coverage", {
                        "percentage": 0,
                        "reasoning": "Not applicable to this technology stack",
                        "confidence": "high"
                    }),
                    "total_files": metadata.get("total_files", 1),
                    "validation_sources": {
                        "llm_patterns": {"count": 0, "matches": 0, "source": "not_applicable"},
                        "static_patterns": {"count": 0, "matches": 0, "source": "not_applicable"},
                        "combined_confidence": "high"
                    }
                }
                print(f"   {gate_name} marked as NOT_APPLICABLE")
            else:
                # Get static patterns for this gate and technology stack
                static_gate_patterns = get_static_patterns_for_gate(gate_name, primary_technologies)
                
                # Hybrid validation: LLM patterns + Static patterns
                llm_matches = self._find_pattern_matches(repo_path, llm_gate_patterns, metadata, gate, "LLM")
                static_matches = self._find_pattern_matches(repo_path, static_gate_patterns, metadata, gate, "Static")
                
                # Combine matches and remove duplicates based on file and line
                all_matches = llm_matches + static_matches
                unique_matches = self._deduplicate_matches(all_matches)
                
                # Calculate relevant file count for this gate type
                if gate_name == "AUTOMATED_TESTS":
                    relevant_files = self._get_technology_relevant_files(metadata, file_type="Test Code")
                else:
                    relevant_files = self._get_technology_relevant_files(metadata, file_type="Source Code")
                
                relevant_file_count = len(relevant_files)
                
                # Prepare gate with expected coverage for scoring
                gate_with_coverage = {
                    **gate,
                    "expected_coverage": gate_pattern_info.get("expected_coverage", {
                        "percentage": 10,
                        "reasoning": "Standard expectation for this gate type",
                        "confidence": "medium"
                    }),
                    "total_files": metadata.get("total_files", 1),
                    "relevant_files": relevant_file_count
                }
                
                # Calculate score based on gate type and combined matches
                score = self._calculate_gate_score(gate_with_coverage, unique_matches, metadata)
                
                # Determine combined confidence
                combined_confidence = self._calculate_combined_confidence(
                    len(llm_matches), len(static_matches), len(unique_matches)
                )
                
                gate_result = {
                    "gate": gate_name,
                    "display_name": gate["display_name"],
                    "description": gate["description"],
                    "category": gate["category"],
                    "priority": gate["priority"],
                    "patterns_used": len(llm_gate_patterns) + len(static_gate_patterns),
                    "matches_found": len(unique_matches),
                    "score": score,
                    "status": self._determine_status(score, gate),
                    "details": self._generate_gate_details(gate_with_coverage, unique_matches),
                    "recommendations": self._generate_gate_recommendations(gate_with_coverage, unique_matches, score),
                    # Add LLM-generated pattern information
                    "pattern_description": gate_pattern_info.get("description", "Pattern analysis for this gate"),
                    "pattern_significance": gate_pattern_info.get("significance", "Important for code quality and compliance"),
                    "expected_coverage": gate_pattern_info.get("expected_coverage", {
                        "percentage": 10,
                        "reasoning": "Standard expectation for this gate type",
                        "confidence": "medium"
                    }),
                    "total_files": metadata.get("total_files", 1),
                    "relevant_files": relevant_file_count,
                    # Enhanced validation tracking
                    "validation_sources": {
                        "llm_patterns": {
                            "count": len(llm_gate_patterns),
                            "matches": len(llm_matches),
                            "source": "llm_generated"
                        },
                        "static_patterns": {
                            "count": len(static_gate_patterns),
                            "matches": len(static_matches),
                            "source": "static_library"
                        },
                        "combined_confidence": combined_confidence,
                        "unique_matches": len(unique_matches),
                        "overlap_matches": len(llm_matches) + len(static_matches) - len(unique_matches)
                    }
                }
                
                # Log validation details
                print(f"   {gate_name}: LLM({len(llm_gate_patterns)} patterns, {len(llm_matches)} matches) + Static({len(static_gate_patterns)} patterns, {len(static_matches)} matches) = {len(unique_matches)} unique matches")
            
            gate_results.append(gate_result)
        
        return gate_results
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: List[Dict[str, Any]]) -> str:
        """Store validation results and calculate overall score with hybrid validation statistics"""
        shared["validation"]["gate_results"] = exec_res
        
        # Calculate overall score (Reduce phase) - exclude NOT_APPLICABLE gates
        applicable_gates = [result for result in exec_res if result["status"] != "NOT_APPLICABLE"]
        
        if applicable_gates:
            total_score = sum(result["score"] for result in applicable_gates)
            overall_score = total_score / len(applicable_gates)
        else:
            overall_score = 0.0
        
        shared["validation"]["overall_score"] = overall_score
        
        # Count status distribution
        passed = len([r for r in exec_res if r["status"] == "PASS"])
        failed = len([r for r in exec_res if r["status"] == "FAIL"])
        warnings = len([r for r in exec_res if r["status"] == "WARNING"])
        not_applicable = len([r for r in exec_res if r["status"] == "NOT_APPLICABLE"])
        
        # Calculate hybrid validation statistics
        hybrid_stats = self._calculate_hybrid_validation_stats(exec_res)
        shared["validation"]["hybrid_stats"] = hybrid_stats
        
        print(f"✅ Hybrid validation complete: {overall_score:.1f}% overall (based on {len(applicable_gates)} applicable gates)")
        print(f"   Passed: {passed}, Failed: {failed}, Warnings: {warnings}, Not Applicable: {not_applicable}")
        print(f"   Pattern Sources: LLM({hybrid_stats['total_llm_patterns']} patterns, {hybrid_stats['total_llm_matches']} matches) + Static({hybrid_stats['total_static_patterns']} patterns, {hybrid_stats['total_static_matches']} matches)")
        print(f"   Coverage Enhancement: {hybrid_stats['coverage_improvement']:.1f}% improvement from hybrid validation")
        
        return "default"
    
    def _calculate_hybrid_validation_stats(self, gate_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for hybrid validation"""
        stats = {
            "total_llm_patterns": 0,
            "total_static_patterns": 0,
            "total_llm_matches": 0,
            "total_static_matches": 0,
            "total_unique_matches": 0,
            "total_overlap_matches": 0,
            "coverage_improvement": 0.0,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        applicable_gates = [g for g in gate_results if g["status"] != "NOT_APPLICABLE"]
        
        for gate in applicable_gates:
            validation_sources = gate.get("validation_sources", {})
            
            # Pattern and match counts
            llm_info = validation_sources.get("llm_patterns", {})
            static_info = validation_sources.get("static_patterns", {})
            
            stats["total_llm_patterns"] += llm_info.get("count", 0)
            stats["total_static_patterns"] += static_info.get("count", 0)
            stats["total_llm_matches"] += llm_info.get("matches", 0)
            stats["total_static_matches"] += static_info.get("matches", 0)
            stats["total_unique_matches"] += validation_sources.get("unique_matches", 0)
            stats["total_overlap_matches"] += validation_sources.get("overlap_matches", 0)
            
            # Confidence distribution
            confidence = validation_sources.get("combined_confidence", "medium")
            stats["confidence_distribution"][confidence] += 1
        
        # Calculate coverage improvement
        if stats["total_llm_matches"] > 0:
            improvement = ((stats["total_unique_matches"] - stats["total_llm_matches"]) / stats["total_llm_matches"]) * 100
            stats["coverage_improvement"] = max(0, improvement)
        
        return stats
    
    def _find_pattern_matches(self, repo_path: Path, patterns: List[str], metadata: Dict[str, Any], gate: Dict[str, Any], source: str = "LLM") -> List[Dict[str, Any]]:
        """Find pattern matches in appropriate files based on gate type and primary technology"""
        matches = []
        
        # Filter files based on gate type and primary technology
        gate_name = gate.get("name", "")
        
        if gate_name == "AUTOMATED_TESTS":
            # For automated tests gate, only look at test files of the primary technology
            target_files = self._get_technology_relevant_files(metadata, file_type="Test Code")
            print(f"   Looking at {len(target_files)} relevant test files for {gate_name}")
        else:
            # For all other gates, only look at source code files of the primary technology
            target_files = self._get_technology_relevant_files(metadata, file_type="Source Code")
            print(f"   Looking at {len(target_files)} relevant source code files for {gate_name}")
        
        for pattern in patterns:
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                
                for file_info in target_files[:100]:  # Limit to first 100 files
                    file_path = repo_path / file_info["relative_path"]
                    
                    if file_path.exists() and file_path.stat().st_size < 1024 * 1024:  # Skip large files
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            
                            for match in compiled_pattern.finditer(content):
                                matches.append({
                                    "file": file_info["relative_path"],
                                    "pattern": pattern,
                                    "match": match.group(),
                                    "line": content[:match.start()].count('\n') + 1,
                                    "language": file_info["language"],
                                    "source": source
                                })
                        except Exception:
                            continue
            except re.error:
                # Skip invalid regex patterns
                continue
        
        return matches
    
    def _get_technology_relevant_files(self, metadata: Dict[str, Any], file_type: str = "Source Code") -> List[Dict[str, Any]]:
        """Get files that are relevant to the primary technology stack"""
        all_files = [f for f in metadata.get("file_list", []) 
                    if f["type"] == file_type and not f["is_binary"]]
        
        # Determine primary technologies from language distribution
        primary_technologies = self._get_primary_technologies(metadata)
        
        if not primary_technologies:
            # Fallback to all files if no primary technology detected
            print(f"   No primary technology detected, using all {len(all_files)} {file_type.lower()} files")
            return all_files
        
        # Filter files to only include primary technology files
        relevant_files = [f for f in all_files 
                         if f["language"] in primary_technologies]
        
        primary_tech_str = ", ".join(primary_technologies)
        print(f"   Primary technologies: {primary_tech_str}")
        print(f"   Filtered to {len(relevant_files)} relevant files (from {len(all_files)} total {file_type.lower()} files)")
        
        return relevant_files
    
    def _get_primary_technologies(self, metadata: Dict[str, Any]) -> List[str]:
        """Determine primary technologies based on language distribution"""
        language_stats = metadata.get("language_stats", {})
        
        if not language_stats:
            return []
        
        # Calculate total files
        total_files = sum(stats.get("files", 0) for stats in language_stats.values())
        
        if total_files == 0:
            return []
        
        # Define technology relevance mapping
        # Languages that are typically used for business logic and application code
        primary_languages = {
            "Java", "Python", "JavaScript", "TypeScript", "C#", "C++", "C", 
            "Go", "Rust", "Kotlin", "Scala", "Swift", "PHP", "Ruby"
        }
        
        # Languages that are typically configuration, markup, or data files
        secondary_languages = {
            "HTML", "CSS", "SCSS", "SASS", "XML", "JSON", "YAML", "SQL", 
            "Dockerfile", "Shell", "Batch", "Markdown", "Properties"
        }
        
        primary_technologies = []
        
        # Find languages that make up significant portion of the codebase
        for language, stats in language_stats.items():
            file_count = stats.get("files", 0)
            percentage = (file_count / total_files) * 100
            
            # Consider a language primary if:
            # 1. It's in the primary languages list AND
            # 2. It represents at least 20% of files OR is the dominant language
            if language in primary_languages:
                if percentage >= 20.0:
                    primary_technologies.append(language)
                    print(f"   Primary technology detected: {language} ({percentage:.1f}%, {file_count} files)")
        
        # If no primary technology found with 20% threshold, take the most dominant primary language
        if not primary_technologies:
            dominant_primary = None
            max_percentage = 0
            
            for language, stats in language_stats.items():
                if language in primary_languages:
                    file_count = stats.get("files", 0)
                    percentage = (file_count / total_files) * 100
                    if percentage > max_percentage:
                        max_percentage = percentage
                        dominant_primary = language
            
            if dominant_primary and max_percentage >= 10.0:  # At least 10% to be considered
                primary_technologies.append(dominant_primary)
                file_count = language_stats[dominant_primary].get("files", 0)
                print(f"   Dominant primary technology: {dominant_primary} ({max_percentage:.1f}%, {file_count} files)")
        
        return primary_technologies
    
    def _calculate_gate_score(self, gate: Dict[str, Any], matches: List[Dict[str, Any]], metadata: Dict[str, Any]) -> float:
        """Calculate score for a gate based on matches and LLM-provided expected coverage"""
        
        gate_name = gate["name"]
        
        # Use technology-relevant file count instead of total files
        relevant_file_count = gate.get("relevant_files", metadata.get("total_files", 1))
        
        # Get expected coverage from LLM analysis
        expected_coverage_data = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage_data.get("percentage", 10)  # Default 10%
        confidence = expected_coverage_data.get("confidence", "medium")
        
        # Convert percentage to decimal
        expected_coverage_ratio = expected_percentage / 100.0
        
        # Calculate confidence multiplier for score adjustment
        confidence_multiplier = {
            "high": 1.0,
            "medium": 0.9,
            "low": 0.8
        }.get(confidence, 0.9)
        
        if gate_name == "AVOID_LOGGING_SECRETS":
            # For security gates, fewer matches = better score
            if len(matches) == 0:
                return 100.0
            else:
                # Penalize based on number of violations
                violation_penalty = min(len(matches) * 10, 100)
                return max(0.0, 100.0 - violation_penalty)
        else:
            # For other gates, more matches = better score
            if len(matches) == 0:
                return 0.0
            else:
                # Score based on coverage vs expected coverage (using relevant files)
                files_with_matches = len(set(m["file"] for m in matches))
                actual_coverage = files_with_matches / relevant_file_count
                
                # Calculate expected files based on LLM analysis (using relevant files)
                expected_files = max(relevant_file_count * expected_coverage_ratio, 1)
                
                # Calculate coverage ratio (actual vs expected)
                coverage_ratio = min(files_with_matches / expected_files, 1.0)
                
                # Base score from coverage ratio
                base_score = coverage_ratio * 100.0
                
                # Apply confidence multiplier
                final_score = base_score * confidence_multiplier
                
                # Bonus for exceeding expectations (up to 10% bonus)
                if files_with_matches > expected_files:
                    excess_ratio = min((files_with_matches - expected_files) / expected_files, 0.1)
                    bonus = excess_ratio * 10.0
                    final_score = min(final_score + bonus, 100.0)
                
                return final_score
    
    def _determine_status(self, score: float, gate: Dict[str, Any]) -> str:
        """Determine gate status based on score"""
        
        if gate["priority"] == "critical":
            threshold_pass = 90.0
            threshold_warn = 70.0
        elif gate["priority"] == "high":
            threshold_pass = 70.0
            threshold_warn = 50.0
        else:
            threshold_pass = 50.0
            threshold_warn = 30.0
        
        if score >= threshold_pass:
            return "PASS"
        elif score >= threshold_warn:
            return "WARNING"
        else:
            return "FAIL"
    
    def _generate_gate_details(self, gate: Dict[str, Any], matches: List[Dict[str, Any]]) -> List[str]:
        """Generate details for gate result including expected coverage analysis"""
        details = []
        
        # Get expected coverage information
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        confidence = expected_coverage.get("confidence", "medium")
        
        # Calculate actual coverage using relevant files
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        files_with_matches = len(set(m['file'] for m in matches)) if matches else 0
        actual_percentage = (files_with_matches / relevant_files) * 100 if relevant_files > 0 else 0
        
        # Coverage analysis with technology-specific information
        details.append(f"Expected Coverage: {expected_percentage}% ({coverage_reasoning})")
        details.append(f"Actual Coverage: {actual_percentage:.1f}% ({files_with_matches}/{relevant_files} relevant files)")
        
        # Show technology filtering information if different from total
        if relevant_files != total_files:
            details.append(f"Technology Filter: Using {relevant_files} relevant files (from {total_files} total files)")
        
        details.append(f"Confidence: {confidence}")
        
        if matches:
            details.append(f"Found {len(matches)} matches across {files_with_matches} files")
            
            # Show sample matches
            for match in matches[:3]:
                details.append(f"  {match['file']}:{match['line']} - {match['match'][:50]}")
            
            if len(matches) > 3:
                details.append(f"  ... and {len(matches) - 3} more matches")
        else:
            details.append(f"No matches found for {gate['display_name']}")
        
        return details
    
    def _generate_gate_recommendations(self, gate: Dict[str, Any], matches: List[Dict[str, Any]], score: float) -> List[str]:
        """Generate recommendations for gate based on expected coverage analysis"""
        recommendations = []
        
        # Get expected coverage information
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        confidence = expected_coverage.get("confidence", "medium")
        
        # Calculate actual coverage using relevant files
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        files_with_matches = len(set(m['file'] for m in matches)) if matches else 0
        actual_percentage = (files_with_matches / relevant_files) * 100 if relevant_files > 0 else 0
        
        # Generate recommendations based on coverage gap
        coverage_gap = expected_percentage - actual_percentage
        
        if score < 50.0:
            recommendations.append(f"Critical: Implement {gate['display_name']} throughout your codebase")
            recommendations.append(f"Expected {expected_percentage}% coverage, currently at {actual_percentage:.1f}% (based on {relevant_files} relevant files)")
            recommendations.append(f"Focus on {gate['description'].lower()}")
            if coverage_reasoning:
                recommendations.append(f"Rationale: {coverage_reasoning}")
        elif score < 80.0:
            recommendations.append(f"Improve {gate['display_name']} coverage")
            if coverage_gap > 5:
                recommendations.append(f"Gap: Expected {expected_percentage}%, current {actual_percentage:.1f}% (based on {relevant_files} relevant files)")
            recommendations.append("Consider adding more comprehensive implementation")
        else:
            if actual_percentage >= expected_percentage:
                recommendations.append(f"Excellent implementation of {gate['display_name']}")
                recommendations.append(f"Coverage exceeds expectations ({actual_percentage:.1f}% vs {expected_percentage}%)")
            else:
                recommendations.append(f"Good implementation of {gate['display_name']}")
                recommendations.append("Consider optimizing existing patterns")
        
        # Add confidence-based recommendations
        if confidence == "low":
            recommendations.append("Note: Coverage estimate has low confidence - manual review recommended")
        elif confidence == "high" and coverage_gap > 10:
            recommendations.append("High confidence in coverage gap - prioritize implementation")
        
        # Add technology-specific note if filtering was applied
        if relevant_files != total_files:
            recommendations.append(f"Note: Analysis focused on {relevant_files} technology-relevant files (filtered from {total_files} total)")
        
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
            "scan_id": shared["request"]["scan_id"]
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
            json_path = os.path.join(output_dir, f"codegates_report_{scan_id}.json")
            json_data = self._generate_json_report(params)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            report_paths["json"] = json_path
        
        # Generate HTML report
        if report_format in ["html", "both"]:
            html_path = os.path.join(output_dir, f"codegates_report_{scan_id}.html")
            html_content = self._generate_html_report(params)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            report_paths["html"] = html_path
        
        return report_paths
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, str]) -> str:
        """Store report paths in shared store"""
        shared["reports"]["json_path"] = exec_res.get("json")
        shared["reports"]["html_path"] = exec_res.get("html")
        
        print(f"✅ Reports generated:")
        for format_type, path in exec_res.items():
            print(f"   {format_type.upper()}: {path}")
        
        return "default"
    
    def _generate_json_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON report with same structure as original plus hybrid validation info"""
        
        validation = params["validation_results"]
        metadata = params["metadata"]
        llm_info = params["llm_info"]
        
        # Use the new data structure directly
        gate_results = validation["gate_results"]
        hybrid_stats = validation.get("hybrid_stats", {})
        
        # Transform to match expected JSON format while preserving new data
        gates = []
        for gate_result in gate_results:
            expected_coverage = gate_result.get("expected_coverage", {})
            total_files = gate_result.get("total_files", 1)
            relevant_files = gate_result.get("relevant_files", total_files)
            files_with_matches = len(set(m.get('file', '') for m in gate_result.get("matches", []))) if gate_result.get("matches") else 0
            actual_coverage_percentage = (files_with_matches / relevant_files) * 100 if relevant_files > 0 else 0
            
            gate = {
                "name": gate_result["gate"],
                "display_name": gate_result["display_name"],
                "status": gate_result["status"],
                "score": gate_result["score"],
                "details": gate_result["details"],
                "category": gate_result["category"],
                "priority": gate_result["priority"],
                "description": gate_result["description"],
                "patterns_used": gate_result.get("patterns_used", 0),
                "matches_found": gate_result.get("matches_found", 0),
                "recommendations": gate_result.get("recommendations", []),
                "pattern_description": gate_result.get("pattern_description", ""),
                "pattern_significance": gate_result.get("pattern_significance", ""),
                # Enhanced coverage information with technology filtering
                "expected_coverage": {
                    "percentage": expected_coverage.get("percentage", 10),
                    "reasoning": expected_coverage.get("reasoning", "Standard expectation"),
                    "confidence": expected_coverage.get("confidence", "medium")
                },
                "actual_coverage": {
                    "percentage": round(actual_coverage_percentage, 1),
                    "files_with_matches": files_with_matches,
                    "relevant_files": relevant_files,
                    "total_files": total_files,
                    "technology_filtered": relevant_files != total_files
                },
                "coverage_analysis": {
                    "gap": round(expected_coverage.get("percentage", 10) - actual_coverage_percentage, 1),
                    "meets_expectation": actual_coverage_percentage >= expected_coverage.get("percentage", 10),
                    "confidence_level": expected_coverage.get("confidence", "medium"),
                    "analysis_basis": f"Based on {relevant_files} relevant files" + (f" (filtered from {total_files} total)" if relevant_files != total_files else "")
                },
                # Hybrid validation information
                "validation_sources": gate_result.get("validation_sources", {}),
                # For compatibility with old format
                "expected": gate_result.get("patterns_used", 0),
                "found": gate_result.get("matches_found", 0),
                "coverage": gate_result["score"],  # Use score as coverage
                "quality_score": gate_result["score"],
                "matches": []  # Could be populated with actual matches if needed
            }
            gates.append(gate)
        
        return {
            "report_metadata": {
                "scan_id": params["scan_id"],
                "repository_url": params["request"]["repository_url"],
                "branch": params["request"]["branch"],
                "generated_at": self._get_timestamp(),
                "version": "2.0.0",
                "llm_source": llm_info["source"],
                "llm_model": llm_info["model"],
                "validation_type": "hybrid"
            },
            "scan_metadata": {
                "scan_duration": 0,  # Could be tracked
                "total_files": metadata.get("total_files", 0),
                "total_lines": metadata.get("total_lines", 0),
                "timestamp": self._get_timestamp(),
                "project_name": self._extract_project_name(params["request"]["repository_url"]),
                "project_path": params["request"]["repository_url"],
                "repository_url": params["request"]["repository_url"]
            },
            "languages_detected": list(metadata.get("languages", {}).keys()),
            "gates": gates,
            "score": validation["overall_score"],
            "overall_score": validation["overall_score"],
            "passed_gates": len([g for g in gate_results if g["status"] == "PASS"]),
            "warning_gates": len([g for g in gate_results if g["status"] == "WARNING"]),
            "failed_gates": len([g for g in gate_results if g["status"] == "FAIL"]),
            "not_applicable_gates": len([g for g in gate_results if g["status"] == "NOT_APPLICABLE"]),
            "total_applicable_gates": len([g for g in gate_results if g["status"] != "NOT_APPLICABLE"]),
            "total_all_gates": len(gate_results),
            "critical_issues": [],
            "recommendations": [rec for gate in gate_results for rec in gate.get("recommendations", [])],
            # Enhanced hybrid validation statistics
            "hybrid_validation": {
                "enabled": True,
                "statistics": hybrid_stats,
                "pattern_library_version": "1.0.0",
                "static_patterns_used": hybrid_stats.get("total_static_patterns", 0),
                "llm_patterns_used": hybrid_stats.get("total_llm_patterns", 0),
                "coverage_improvement": hybrid_stats.get("coverage_improvement", 0.0),
                "confidence_distribution": hybrid_stats.get("confidence_distribution", {})
            }
        }
    
    def _generate_html_report(self, params: Dict[str, Any]) -> str:
        """Generate HTML report using exact same template as original report.py with hybrid validation info"""
        
        validation = params["validation_results"]
        metadata = params["metadata"]
        llm_info = params["llm_info"]
        
        # Use the new data structure directly
        gate_results = validation["gate_results"]
        hybrid_stats = validation.get("hybrid_stats", {})
        
        # Calculate summary statistics from new data
        stats = self._calculate_summary_stats_from_new_data(gate_results)
        
        # Extract project name
        project_name = self._extract_project_name(params["request"]["repository_url"])
        
        # Get current timestamp
        timestamp = self._get_timestamp_formatted()
        
        # Report type display
        report_type_display = "Hybrid Validation"
        
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
        
        # Generate hybrid validation summary
        hybrid_summary = self._generate_hybrid_validation_summary_html(hybrid_stats)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hard Gate Assessment ({report_type_display}) - {project_name}</title>
    <style>
        {self._get_extension_css_styles()}
    </style>
    {toggle_script}
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>{project_name}</h1>
            <div class="report-badge summary-badge">{report_type_display} Report</div>
            <p style="color: #2563eb; margin-bottom: 30px; font-weight: 500;">Hard Gate Assessment Report</p>
            <p style="color: #6b7280; margin-bottom: 20px;">Generated with {llm_info['source']} ({llm_info['model']}) + Static Pattern Library</p>
        </div>
        
        <h2>Executive Summary</h2>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{stats['total_gates']}</div>
                <div class="stat-label">Total Gates Evaluated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['implemented_gates']}</div>
                <div class="stat-label">Gates Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['partial_gates']}</div>
                <div class="stat-label">Partially Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['not_implemented_gates']}</div>
                <div class="stat-label">Not Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['not_applicable_gates']}</div>
                <div class="stat-label">Not Applicable</div>
            </div>
        </div>
        
        <h3>Overall Compliance</h3>
        <div class="compliance-bar">
            <div class="compliance-fill" style="width: {validation['overall_score']:.1f}%"></div>
        </div>
        <p><strong>{validation['overall_score']:.1f}% Hard Gates Compliance</strong></p>
        <p style="color: #6b7280; font-size: 0.9em; margin-top: 5px;">
            <em>Percentage calculated based on {stats['total_gates']} applicable gates (excluding {stats['not_applicable_gates']} N/A gates)</em>
        </p>
        
        {hybrid_summary}
        
        <h2>Hard Gates Analysis</h2>
        {self._generate_gates_table_html_from_new_data(gate_results)}
        
        <footer style="margin-top: 50px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            <p>Hard Gate Assessment {report_type_display} Report generated on {timestamp}</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html_template
    
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
        .status-implemented { color: #059669; background: #ecfdf5; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-partial { color: #d97706; background: #fffbeb; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-not-implemented { color: #dc2626; background: #fef2f2; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-not-applicable { color: #6b7280; background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        
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
        
        .metric-label {
            color: #6b7280;
            font-size: 0.9em;
            margin-bottom: 4px;
        }
        
        .metric-value {
            color: #1f2937;
            font-weight: 500;
            font-size: 1.1em;
        }
        
        .details-section {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
        }
        
        .details-section-title {
            color: #1f2937;
            font-weight: 500;
            margin-bottom: 8px;
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
        """Calculate summary statistics from new data structure"""
        implemented_gates = len([g for g in gate_results if g.get("status") == "PASS"])
        partial_gates = len([g for g in gate_results if g.get("status") == "WARNING"])
        not_implemented_gates = len([g for g in gate_results if g.get("status") == "FAIL"])
        not_applicable_gates = len([g for g in gate_results if g.get("status") == "NOT_APPLICABLE"])
        
        # Total applicable gates (excluding NOT_APPLICABLE)
        total_applicable_gates = len(gate_results) - not_applicable_gates
        
        return {
            "total_gates": total_applicable_gates,  # Only count applicable gates
            "implemented_gates": implemented_gates,
            "partial_gates": partial_gates,
            "not_implemented_gates": not_implemented_gates,
            "not_applicable_gates": not_applicable_gates,
            "total_all_gates": len(gate_results)  # Total including N/A for reference
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
                return {'class': 'not-implemented', 'text': '✗ Violations Found'}
        
        # Default status mapping
        if status == 'PASS':
            return {'class': 'implemented', 'text': '✓ Implemented'}
        elif status == 'WARNING':
            return {'class': 'partial', 'text': '⚬ Partial'}
        elif status == 'NOT_APPLICABLE':
            return {'class': 'not-applicable', 'text': 'N/A'}
        else:
            return {'class': 'not-implemented', 'text': '✗ Missing'}

    def _format_evidence_from_new_data(self, gate: Dict[str, Any]) -> str:
        """Format evidence for display from new data structure"""
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
        
        html = """<div class="gates-analysis">"""
        
        for category_name, gate_names in gate_categories.items():
            category_gates = [g for g in gates if g.get("name") in gate_names]
            
            if not category_gates:
                continue
            
            html += f"""
                <div class="gate-category-section">
                    <h3 class="category-title">{category_name}</h3>
                    <div class="category-content">
                        <table class="gates-table">
                            <thead>
                                <tr>
                                    <th style="width: 30px"></th>
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
                evidence = self._format_evidence(gate)
                recommendation = self._get_recommendation(gate, gate_name)
                
                # Generate detailed content
                details_content = self._generate_gate_details(gate)
                
                html += f"""
                                <tr>
                                    <td style="text-align: center">
                                        <button class="details-toggle" onclick="toggleDetails(this, 'details-{gate_id}')" aria-expanded="false" aria-label="Show details for {gate_name}">+</button>
                                    </td>
                                    <td><strong>{gate_name}</strong></td>
                                    <td><span class="status-{status_info['class']}">{status_info['text']}</span></td>
                                    <td>{evidence}</td>
                                    <td>{recommendation}</td>
                                </tr>"""
                
                # Add details row (hidden by default)
                html += f"""
                                <tr id="details-{gate_id}" class="gate-details" aria-hidden="true">
                                    <td colspan="5" class="details-content">
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
        
        # Get expected coverage information
        expected_coverage = gate.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 10)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        confidence = expected_coverage.get("confidence", "medium")
        
        # Calculate actual coverage using relevant files
        total_files = gate.get("total_files", 1)
        relevant_files = gate.get("relevant_files", total_files)
        files_with_matches = len(set(m['file'] for m in matches)) if matches else 0
        actual_percentage = (files_with_matches / relevant_files) * 100 if relevant_files > 0 else 0
        
        # Coverage analysis with technology-specific information
        details.append(f"Expected Coverage: {expected_percentage}% ({coverage_reasoning})")
        details.append(f"Actual Coverage: {actual_percentage:.1f}% ({files_with_matches}/{relevant_files} relevant files)")
        
        # Show technology filtering information if different from total
        if relevant_files != total_files:
            details.append(f"Technology Filter: Using {relevant_files} relevant files (from {total_files} total files)")
        
        details.append(f"Confidence: {confidence}")
        
        if matches:
            details.append(f"Found {len(matches)} matches across {files_with_matches} files")
            
            # Show sample matches
            for match in matches[:3]:
                details.append(f"  {match['file']}:{match['line']} - {match['match'][:50]}")
            
            if len(matches) > 3:
                details.append(f"  ... and {len(matches) - 3} more matches")
        else:
            details.append(f"No matches found for {gate['display_name']}")
        
        return details
    
    def _generate_gates_table_html_from_new_data(self, gate_results: List[Dict[str, Any]]) -> str:
        """Generate gates table HTML with categories using new data structure"""
        gate_categories = self._get_new_gate_categories()
        
        html = """<div class="gates-analysis">"""
        
        for category_name, gate_names in gate_categories.items():
            category_gates = [g for g in gate_results if g.get("gate") in gate_names]
            
            if not category_gates:
                continue
            
            html += f"""
                <div class="gate-category-section">
                    <h3 class="category-title">{category_name}</h3>
                    <div class="category-content">
                        <table class="gates-table">
                            <thead>
                                <tr>
                                    <th style="width: 30px"></th>
                                    <th>Practice</th>
                                    <th>Status</th>
                                    <th>Evidence</th>
                                    <th>Recommendation</th>
                                </tr>
                            </thead>
                            <tbody>"""
            
            for i, gate in enumerate(category_gates):
                gate_id = f"{category_name.lower()}-{gate.get('gate', '')}-{i}"
                display_name = gate.get("display_name", "Unknown Gate")
                status_info = self._get_status_info_from_new_data(gate.get("status", ""), gate)
                evidence = self._format_evidence_from_new_data(gate)
                recommendation = self._get_recommendation_from_new_data(gate)
                
                # Generate detailed content
                details_content = self._generate_gate_details_from_new_data(gate)
                
                html += f"""
                                <tr>
                                    <td style="text-align: center">
                                        <button class="details-toggle" onclick="toggleDetails(this, 'details-{gate_id}')" aria-expanded="false" aria-label="Show details for {display_name}">+</button>
                                    </td>
                                    <td><strong>{display_name}</strong></td>
                                    <td><span class="status-{status_info['class']}">{status_info['text']}</span></td>
                                    <td>{evidence}</td>
                                    <td>{recommendation}</td>
                                </tr>"""
                
                # Add details row (hidden by default)
                html += f"""
                                <tr id="details-{gate_id}" class="gate-details" aria-hidden="true">
                                    <td colspan="5" class="details-content">
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

    def _generate_gate_details_from_new_data(self, gate: Dict[str, Any]) -> str:
        """Generate detailed content for a gate using new data structure"""
        details = []
        
        # Metrics section
        metrics = [
            ('Score', f"{gate.get('score', 0):.1f}%"),
            ('Coverage', f"{gate.get('score', 0):.1f}%"),
            ('Patterns Used', f"{gate.get('patterns_used', 0)}"),
            ('Matches Found', f"{gate.get('matches_found', 0)}")
        ]
        
        metrics_html = '<div class="metrics-grid">'
        for label, value in metrics:
            metrics_html += f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>"""
        metrics_html += '</div>'
        details.append(metrics_html)
        
        # Gate information section
        gate_info_html = '<div class="details-section">'
        gate_info_html += '<div class="details-section-title">Gate Information:</div>'
        gate_info_html += f'<p><strong>Category:</strong> {gate.get("category", "Unknown")}</p>'
        gate_info_html += f'<p><strong>Priority:</strong> {gate.get("priority", "Unknown")}</p>'
        gate_info_html += f'<p><strong>Description:</strong> {gate.get("description", "No description available")}</p>'
        gate_info_html += '</div>'
        details.append(gate_info_html)
        
        # Pattern Analysis section - NEW
        pattern_description = gate.get("pattern_description", "")
        pattern_significance = gate.get("pattern_significance", "")
        
        if pattern_description or pattern_significance:
            pattern_html = '<div class="details-section">'
            pattern_html += '<div class="details-section-title">Pattern Analysis:</div>'
            
            if pattern_description:
                pattern_html += f'<p><strong>Pattern Description:</strong> {pattern_description}</p>'
            
            if pattern_significance:
                pattern_html += f'<p><strong>Significance:</strong> {pattern_significance}</p>'
            
            pattern_html += '</div>'
            details.append(pattern_html)
        
        # Details section
        gate_details = gate.get('details', [])
        if gate_details:
            details_html = '<div class="details-section">'
            details_html += '<div class="details-section-title">Analysis Details:</div>'
            details_html += '<ul>'
            for detail in gate_details[:5]:  # Show first 5 details
                details_html += f'<li>{detail}</li>'
            details_html += '</ul>'
            details_html += '</div>'
            details.append(details_html)
        
        # Recommendations section
        recommendations = gate.get('recommendations', [])
        if recommendations:
            rec_html = '<div class="details-section">'
            rec_html += '<div class="details-section-title">Recommendations:</div>'
            rec_html += '<ul>'
            for rec in recommendations[:3]:  # Show first 3 recommendations
                rec_html += f'<li>{rec}</li>'
            rec_html += '</ul>'
            rec_html += '</div>'
            details.append(rec_html)
        
        return ''.join(details)


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
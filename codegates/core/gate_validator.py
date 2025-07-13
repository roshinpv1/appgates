"""
Core Gate Validator - Orchestrates validation of all 15 hard gates
"""

import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models import (
    ValidationResult, GateScore, FileAnalysis, Language, 
    GateType, ScanConfig
)
from .language_detector import LanguageDetector
from .gate_validators import GateValidatorFactory
from .gate_scorer import GateScorer
from .llm_optimizer import FastLLMIntegrationManager


class GateValidator:
    """Main validator that coordinates all gate checks"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.language_detector = LanguageDetector()
        self.gate_scorer = GateScorer()
        self.validator_factory = GateValidatorFactory()
        
    def validate(self, target_path: Path, llm_manager=None, repository_url: Optional[str] = None) -> ValidationResult:
        """Validate all gates for a codebase"""
        
        # Start timing
        self._scan_start_time = time.time()
        
        # Initialize result
        result = ValidationResult(
            project_name=target_path.name,
            project_path=str(target_path),
            language=self.config.languages[0] if self.config.languages else Language.PYTHON,
            scan_duration=0.0  # Initialize with 0.0
        )
        
        try:
            # PHASE 1: Comprehensive Repository Analysis
            print("🔍 Phase 1: Analyzing repository structure and generating LLM patterns...")
            analysis_result = self._analyze_repository_and_generate_patterns(target_path, llm_manager)
            
            # PHASE 2: File Scanning
            print("📁 Phase 2: Scanning files...")
            file_analyses = self._scan_files(target_path)
            result.file_analyses = file_analyses
            
            # PHASE 3: Gate Validation with LLM-generated patterns
            print("🎯 Phase 3: Validating gates with LLM-generated patterns...")
            gate_scores = self._validate_all_gates(target_path, file_analyses, llm_manager, analysis_result)
            result.gate_scores = gate_scores
            
            # Calculate summary metrics
            self._calculate_summary_metrics(result)
            
            # Generate recommendations
            self._generate_recommendations(result)
            
            # Set repository URL if provided
            if repository_url:
                result.repository_url = repository_url
            
            # Update final scan duration
            result.scan_duration = time.time() - self._scan_start_time
            
            return result
            
        except Exception as e:
            print(f"❌ Validation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _analyze_repository_and_generate_patterns(self, target_path: Path, llm_manager=None) -> Dict[str, Any]:
        """Comprehensive repository analysis and LLM pattern generation"""
        
        print("📊 Starting comprehensive repository analysis...")
        
        # Step 1: Analyze repository structure
        file_structure = self._analyze_repository_structure(target_path)
        print(f"📁 Analyzed {len(file_structure)} files in repository structure")
        
        # Step 2: Extract config and build files
        config_files = self._extract_config_files(target_path)
        build_files = self._extract_build_files(target_path)
        dependencies = self._extract_dependencies(target_path)
        print(f"🔧 Found {len(config_files)} config files, {len(build_files)} build files, {len(dependencies)} dependencies")
        
        # Step 3: Detect technologies and custom libraries
        tech_context = self._detect_technologies_comprehensive(target_path, file_structure)
        custom_libraries = self._detect_custom_libraries_comprehensive(target_path, file_structure, dependencies)
        print(f"🏗️ Detected {len(tech_context.get('frameworks', []))} frameworks, {len(custom_libraries)} custom libraries")
        
        # Step 4: Generate comprehensive LLM prompt
        print("📋 Generating comprehensive LLM prompt...")
        llm_prompt = self._generate_comprehensive_llm_prompt(
            target_path=target_path,
            file_structure=file_structure,
            tech_context=tech_context,
            custom_libraries=custom_libraries,
            config_files=config_files,
            build_files=build_files,
            dependencies=dependencies
        )
        
        # Step 5: Call LLM for pattern generation
        llm_patterns = {}
        if llm_manager:
            print("🤖 Calling LLM for dynamic pattern generation...")
            try:
                # Use the correct LLM method - analyze code with context
                llm_response = llm_manager.analyze_code_with_context(
                    prompt=llm_prompt,
                    context={
                        'target_path': str(target_path),
                        'languages': [lang.value for lang in self.config.languages],
                        'file_structure': file_structure,
                        'tech_context': tech_context,
                        'custom_libraries': custom_libraries
                    },
                    analysis_type="pattern_generation"
                )
                if llm_response.get('success', False):
                    llm_patterns = llm_response.get('patterns', {})
                    print(f"✅ LLM generated patterns for {len(llm_patterns)} gates")
                else:
                    print("⚠️ LLM pattern generation failed, using fallback patterns")
                    llm_patterns = self._generate_fallback_patterns(tech_context)
            except Exception as e:
                print(f"⚠️ LLM call failed: {e}, using fallback patterns")
                llm_patterns = self._generate_fallback_patterns(tech_context)
        else:
            print("📋 No LLM available, using fallback patterns")
            llm_patterns = self._generate_fallback_patterns(tech_context)
        
        # Step 6: Return comprehensive analysis result
        analysis_result = {
            'file_structure': file_structure,
            'tech_context': tech_context,
            'custom_libraries': custom_libraries,
            'config_files': config_files,
            'build_files': build_files,
            'dependencies': dependencies,
            'llm_patterns': llm_patterns,
            'llm_prompt': llm_prompt,
            'llm_used': llm_manager is not None
        }
        
        print("✅ Repository analysis and pattern generation completed")
        return analysis_result
    
    def _scan_files(self, target_path: Path) -> List[FileAnalysis]:
        """Scan all files in the target directory"""
        
        analyses = []
        
        for lang in self.config.languages:
            lang_files = self._get_language_files(target_path, lang)
            
            # Use thread pool for parallel file analysis
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_file = {
                    executor.submit(self._analyze_file, file_path, lang): file_path
                    for file_path in lang_files[:5000]  # Limit to 100 files per language
                }
                
                for future in as_completed(future_to_file):
                    try:
                        analysis = future.result()
                        if analysis:
                            analyses.append(analysis)
                    except Exception as e:
                        # Log error but continue processing
                        pass
        
        return analyses
    
    def _get_language_files(self, target_path: Path, language: Language) -> List[Path]:
        """Get all files for a specific language"""
        
        extension_map = {
            Language.JAVA: ['.java'],
            Language.PYTHON: ['.py'],
            Language.JAVASCRIPT: ['.js', '.jsx'],
            Language.TYPESCRIPT: ['.ts', '.tsx'],
            Language.CSHARP: ['.cs'],
            Language.DOTNET: ['.cs', '.vb', '.fs']
        }
        
        extensions = extension_map.get(language, [])
        files = []
        
        for ext in extensions:
            files.extend(target_path.rglob(f"*{ext}"))
        
        # Apply exclude patterns
        filtered_files = []
        for file_path in files:
            if not self._should_exclude_file(file_path):
                filtered_files.append(file_path)
        
        return filtered_files
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded based on patterns"""
        
        path_str = str(file_path)
        
        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if pattern in path_str or file_path.match(pattern):
                return True
        
        # Check file size limit
        try:
            if file_path.stat().st_size > self.config.max_file_size:
                return True
        except OSError:
            return True
            
        return False
    
    def _analyze_file(self, file_path: Path, language: Language) -> Optional[FileAnalysis]:
        """Analyze a single file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            
            analysis = FileAnalysis(
                file_path=str(file_path),
                language=language,
                lines_of_code=lines_of_code
            )
            
            return analysis
            
        except Exception as e:
            return None
    
    def _validate_all_gates(self, target_path: Path, 
                          file_analyses: List[FileAnalysis], 
                          llm_manager=None, analysis_result: Dict[str, Any] = None) -> List[GateScore]:
        """Validate all 15 hard gates"""
        
        gate_scores = []
        
        # Detect UI components in the project
        has_ui_components = self._detect_ui_components(target_path, file_analyses)
        
        # Process each gate type
        for gate_type in GateType:
            if gate_type == GateType.LOG_BACKGROUND_JOBS:
                continue
            try:
                # Check if this gate is applicable to the project
                if not self._is_gate_applicable(gate_type, target_path, file_analyses, has_ui_components):
                    # Create "Not Applicable" gate score
                    gate_score = GateScore(
                        gate=gate_type,
                        expected=0,
                        found=0,
                        coverage=0.0,
                        quality_score=0.0,
                        final_score=0.0,
                        status="NOT_APPLICABLE",
                        details=[f"Gate {gate_type.value} is not applicable to this project type"],
                        recommendations=[f"No action needed - {gate_type.value} not relevant for this project"]
                    )
                    gate_scores.append(gate_score)
                    continue
                
                gate_score = self._validate_single_gate(
                    gate_type, target_path, file_analyses, llm_manager, analysis_result
                )
                gate_scores.append(gate_score)
                
            except Exception as e:
                print(f"❌ Gate validation failed for {gate_type.value}: {str(e)}")
                # Create error gate score
                gate_score = GateScore(
                    gate=gate_type,
                    expected=0,
                    found=0,
                    coverage=0.0,
                    quality_score=0.0,
                    final_score=0.0,
                    status="ERROR",
                    details=[f"Gate validation failed: {str(e)}"],
                    recommendations=["Check system configuration and try again"]
                )
                gate_scores.append(gate_score)
        
        return gate_scores
    
    def _validate_single_gate(self, gate_type: GateType, 
                            target_path: Path, 
                            file_analyses: List[FileAnalysis],
                            llm_manager=None, analysis_result: Dict[str, Any] = None) -> GateScore:
        """Validate a single gate type"""
        
        # Get appropriate validator for the gate
        validators = []
        for lang in self.config.languages:
            validator = self.validator_factory.get_validator(gate_type, lang)
            if validator:
                # Pass analysis result to validator for LLM pattern access
                if analysis_result:
                    validator._analysis_result = analysis_result
                validators.append(validator)
        
        if not validators:
            return GateScore(
                gate=gate_type,
                expected=0,
                found=0,
                coverage=0.0,
                quality_score=0.0,
                final_score=0.0,
                status="UNSUPPORTED",
                recommendations=[f"No validator available for {gate_type.value}"]
            )
        
        # Aggregate results from all validators
        total_expected = 0
        total_found = 0
        all_details = []
        all_recommendations = []
        all_matches = []
        
        for validator in validators:
            try:
                result = validator.validate(target_path, file_analyses)
                total_expected += result.expected
                total_found += result.found
                all_details.extend(result.details)
                all_recommendations.extend(result.recommendations)
                
                # Collect matches for detailed reporting
                if hasattr(result, 'matches') and result.matches:
                    all_matches.extend(result.matches)
                
            except Exception as e:
                # Log the specific error for debugging
                error_msg = f"Validator error for {gate_type.value}: {str(e)}"
                print(f"❌ {error_msg}")
                all_details.append(error_msg)
                
                # For security-critical gates, error should result in failure
                if gate_type == GateType.AVOID_LOGGING_SECRETS:
                    all_details.append("⚠️ Security validation failed due to processing error")
                    # Force failure status by setting negative scores
                    total_expected = 1
                    total_found = 999  # High violation count to ensure failure
                else:
                    # For other gates, validation error should not result in false PASS
                    all_details.append("⚠️ Validation incomplete due to processing error")
                    # Set conservative values that won't result in false PASS
                    if total_expected == 0:
                        total_expected = 1  # Prevent division by zero

        # Calculate coverage based on expected vs found
        if total_expected == 0:
            if total_found == 0:
                coverage = 100.0  # Perfect: no violations found
            else:
                # Security-critical gates: ANY violation should result in failure
                if gate_type == GateType.AVOID_LOGGING_SECRETS:
                    coverage = 0.0  # Any secrets violation = complete failure
                else:
                    coverage = max(0.0, 100.0 - (total_found * 10))  # Penalty for violations
        else:
            coverage = min((total_found / total_expected) * 100, 100.0)

        # Calculate final score using simplified scoring
        final_score = self.gate_scorer.calculate_gate_score(
            coverage, 0.0, gate_type  # Quality score is no longer used
        )
        
        # Determine status based on coverage
        status = self._determine_gate_status(final_score, gate_type, total_found)
        
        return GateScore(
            gate=gate_type,
            expected=total_expected,
            found=total_found,
            coverage=coverage,
            quality_score=0.0,  # Quality score is no longer used
            final_score=final_score,
            status=status,
            details=all_details,
            recommendations=all_recommendations,
            matches=all_matches
        )
    
    def _analyze_repository_structure(self, target_path: Path) -> Dict[str, Any]:
        """Analyze repository structure and file organization"""
        file_structure = {}
        
        # Get all files in the repository
        all_files = []
        for ext in ['*.java', '*.py', '*.js', '*.ts', '*.go', '*.rb', '*.php', '*.cs', '*.xml', '*.yml', '*.yaml', '*.json', '*.properties', '*.gradle', '*.pom']:
            all_files.extend(target_path.rglob(ext))
        
        # Organize by directory structure
        for file_path in all_files:
            try:
                relative_path = file_path.relative_to(target_path)
                path_parts = relative_path.parts
                
                current = file_structure
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Add file info
                current[path_parts[-1]] = {
                    'path': str(relative_path),
                    'size': file_path.stat().st_size,
                    'extension': file_path.suffix,
                    'language': self._detect_language_from_extension(file_path.suffix)
                }
                
            except Exception:
                continue
        
        return file_structure
    
    def _extract_config_files(self, target_path: Path) -> Dict[str, Any]:
        """Extract configuration files and their content"""
        config_files = {}
        
        config_patterns = {
            'Maven': ['pom.xml'],
            'Gradle': ['build.gradle', 'build.gradle.kts'],
            'npm': ['package.json'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml'],
            'application': ['application.properties', 'application.yml', 'application.yaml'],
            'logging': ['logback.xml', 'log4j.properties', 'log4j2.xml']
        }
        
        for tool, files in config_patterns.items():
            for file_name in files:
                file_path = target_path / file_name
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        config_files[tool] = {
                            'name': tool,
                            'file': file_name,
                            'content': content[:2000] if len(content) > 2000 else content,  # Limit content size
                            'size': len(content)
                        }
                        break
                    except Exception:
                        continue
        
        return config_files
    
    def _extract_build_files(self, target_path: Path) -> Dict[str, Any]:
        """Extract build files and their content"""
        build_files = {}
        
        build_patterns = {
            'Maven': ['pom.xml'],
            'Gradle': ['build.gradle', 'build.gradle.kts'],
            'npm': ['package.json'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml'],
            'cargo': ['Cargo.toml'],
            'go.mod': ['go.mod']
        }
        
        for tool, files in build_patterns.items():
            for file_name in files:
                file_path = target_path / file_name
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        build_files[tool] = {
                            'name': tool,
                            'file': file_name,
                            'content': content[:2000] if len(content) > 2000 else content,
                            'size': len(content)
                        }
                        break
                    except Exception:
                        continue
        
        return build_files
    
    def _extract_dependencies(self, target_path: Path) -> List[str]:
        """Extract dependencies from various dependency files"""
        dependencies = []
        
        # Check package.json
        package_json = target_path / 'package.json'
        if package_json.exists():
            try:
                import json
                content = package_json.read_text(encoding='utf-8', errors='ignore')
                data = json.loads(content)
                if 'dependencies' in data:
                    dependencies.extend(list(data['dependencies'].keys()))
                if 'devDependencies' in data:
                    dependencies.extend(list(data['devDependencies'].keys()))
            except Exception:
                pass
        
        # Check requirements.txt
        requirements_txt = target_path / 'requirements.txt'
        if requirements_txt.exists():
            try:
                content = requirements_txt.read_text(encoding='utf-8', errors='ignore')
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before version specifiers)
                        package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                        if package:
                            dependencies.append(package)
            except Exception:
                pass
        
        return list(set(dependencies))  # Remove duplicates
    
    def _detect_technologies_comprehensive(self, target_path: Path, file_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Detect technologies used in the codebase"""
        tech_context = {
            'languages': [],
            'frameworks': [],
            'build_tools': [],
            'databases': [],
            'containerization': [],
            'frontend': [],
            'testing': []
        }
        
        # Detect languages
        language_files = {}
        for ext in ['.java', '.py', '.js', '.ts', '.cs', '.go', '.rb', '.php']:
            language_files[ext] = list(target_path.rglob(f"*{ext}"))
        
        for ext, files in language_files.items():
            if files:
                lang = self._detect_language_from_extension(ext)
                if lang:
                    tech_context['languages'].append(lang)
        
        # Detect frameworks based on file patterns
        framework_patterns = {
            'Spring': ['@SpringBootApplication', '@Controller', '@Service'],
            'Django': ['from django', 'Django'],
            'Flask': ['from flask', 'Flask'],
            'Express': ['express', 'app.get', 'app.post'],
            'React': ['import React', 'React.', 'useState'],
            'Angular': ['@angular', '@Component', '@Injectable']
        }
        
        # Check for framework indicators in files
        for framework, patterns in framework_patterns.items():
            for ext, files in language_files.items():
                for file_path in files[:10]:  # Check first 10 files
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if any(pattern.lower() in content.lower() for pattern in patterns):
                            tech_context['frameworks'].append(framework)
                            break
                    except Exception:
                        continue
        
        return tech_context
    
    def _detect_custom_libraries_comprehensive(self, target_path: Path, file_structure: Dict[str, Any], dependencies: List[str]) -> Dict[str, Any]:
        """Detect custom libraries and frameworks"""
        custom_libraries = {}
        
        # ESER detection
        eser_patterns = ['ESER', 'EnterpriseSecurityEvent', 'SecurityEventReporting']
        # EBSSH detection
        ebssh_patterns = ['EBSSH', 'EnterpriseBusinessSecurity', 'BusinessSecurityService']
        
        # Check all files for custom library patterns
        for ext in ['.java', '.py', '.js', '.ts', '.cs']:
            files = list(target_path.rglob(f"*{ext}"))
            for file_path in files[:20]:  # Check first 20 files
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Check for ESER
                    if any(pattern.lower() in content.lower() for pattern in eser_patterns):
                        custom_libraries['ESER'] = {
                            'name': 'ESER',
                            'description': 'Enterprise Security Event Reporting',
                            'files': custom_libraries.get('ESER', {}).get('files', []) + [str(file_path.relative_to(target_path))]
                        }
                    
                    # Check for EBSSH
                    if any(pattern.lower() in content.lower() for pattern in ebssh_patterns):
                        custom_libraries['EBSSH'] = {
                            'name': 'EBSSH',
                            'description': 'Enterprise Business Security Service Hub',
                            'files': custom_libraries.get('EBSSH', {}).get('files', []) + [str(file_path.relative_to(target_path))]
                        }
                        
                except Exception:
                    continue
        
        return custom_libraries
    
    def _generate_comprehensive_llm_prompt(self, target_path: Path, file_structure: Dict[str, Any], 
                                         tech_context: Dict[str, Any], custom_libraries: Dict[str, Any],
                                         config_files: Dict[str, Any], build_files: Dict[str, Any], 
                                         dependencies: List[str]) -> str:
        """Generate comprehensive LLM prompt for pattern generation"""
        
        prompt = f"""You are an expert code analyzer specializing in hard gate validation patterns for enterprise security and compliance.

## CODEBASE ANALYSIS

### Technology Stack
- Languages: {', '.join(tech_context.get('languages', []))}
- Frameworks: {', '.join(tech_context.get('frameworks', []))}
- Build Tools: {', '.join(tech_context.get('build_tools', []))}
- Dependencies: {', '.join(dependencies[:20])}...

### File Structure Summary
"""
        
        # Add file structure information
        file_count = 0
        for root, files in self._walk_file_structure(file_structure):
            if file_count < 50:  # Limit to first 50 files
                prompt += f"- {root}: {len(files)} files\n"
                file_count += 1
        
        prompt += f"""
### Config Files Detected
"""
        if config_files:
            for tool_name, tool_info in config_files.items():
                prompt += f"""
**{tool_name}** ({tool_info.get('description', 'No description')})
- File: {tool_info.get('file', 'unknown')}
- Size: {tool_info.get('size', 0)} characters
- Content: {tool_info.get('content', '')[:500]}...
"""
        else:
            prompt += "No config files detected.\n"

        prompt += f"""
### Build Files Detected
"""
        if build_files:
            for tool_name, tool_info in build_files.items():
                prompt += f"""
**{tool_name}** ({tool_info.get('description', 'No description')})
- File: {tool_info.get('file', 'unknown')}
- Size: {tool_info.get('size', 0)} characters
- Content: {tool_info.get('content', '')[:500]}...
"""
        else:
            prompt += "No build files detected.\n"

        prompt += f"""
### Custom Libraries Detected
"""
        if custom_libraries:
            for lib_name, lib_info in custom_libraries.items():
                prompt += f"""
**{lib_name}** ({lib_info.get('description', 'No description')})
- Files: {', '.join(lib_info.get('files', [])[:5])}...
"""
        else:
            prompt += "No custom libraries detected.\n"
        
        prompt += f"""
## HARD GATES TO ANALYZE
{', '.join([gate.value for gate in GateType])}

## TASK
Generate comprehensive regex patterns for each hard gate that would be effective for this specific codebase. Consider:

1. **Technology-specific patterns**: Adapt patterns to the detected languages and frameworks
2. **Custom library integration**: If custom libraries are detected, include patterns that work with their specific APIs
3. **Framework-specific patterns**: Include patterns for detected frameworks (Spring, Django, Express, etc.)
4. **Security context**: Consider the security patterns already present in the codebase
5. **Logging patterns**: Consider existing logging patterns and adapt accordingly
6. **Configuration patterns**: Look at the config files provided and generate patterns for their specific formats
7. **Build tool patterns**: Consider the build tools detected and their specific patterns

## OUTPUT FORMAT
For each hard gate, provide:
1. **Pattern Name**: Descriptive name for the pattern
2. **Regex Pattern**: The actual regex pattern for matching
3. **Description**: What this pattern detects
4. **Technology Context**: Which languages/frameworks this pattern is designed for
5. **Custom Library Integration**: How this pattern works with detected custom libraries (if any)
6. **Reasoning**: Why this pattern is relevant for this specific codebase

Generate patterns that are:
- **Specific** to the detected technology stack
- **Comprehensive** in coverage
- **Practical** for real-world codebases
- **Customizable** for different contexts
- **Secure** and compliance-focused
- **Based on actual files** and configurations found in this codebase

Focus on patterns that would catch actual violations in this type of codebase."""

        return prompt
    
    def _walk_file_structure(self, file_structure: Dict[str, Any]) -> List[tuple]:
        """Walk through file structure and return (path, files) tuples"""
        result = []
        
        def walk_recursive(structure, current_path=""):
            files = []
            for key, value in structure.items():
                if isinstance(value, dict):
                    walk_recursive(value, f"{current_path}/{key}" if current_path else key)
                else:
                    files.append(key)
            
            if files:
                result.append((current_path, files))
        
        walk_recursive(file_structure)
        return result
    
    def _detect_language_from_extension(self, extension: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.java': 'java',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php'
        }
        return ext_map.get(extension.lower(), 'unknown')
    
    def _generate_fallback_patterns(self, tech_context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate fallback patterns when LLM is not available"""
        fallback_patterns = {}
        
        languages = tech_context.get('languages', [])
        frameworks = tech_context.get('frameworks', [])
        
        # Basic fallback patterns for each gate
        for gate in GateType:
            patterns = []
            
            # Add language-specific patterns
            for lang in languages:
                if lang == 'java':
                    patterns.extend([
                        f"(?i)({gate.value.lower().replace(' ', '|')})",
                        f"(?i)({gate.value.lower().replace(' ', '_')})"
                    ])
                elif lang == 'python':
                    patterns.extend([
                        f"(?i)({gate.value.lower().replace(' ', '|')})",
                        f"(?i)({gate.value.lower().replace(' ', '_')})"
                    ])
                elif lang == 'javascript':
                    patterns.extend([
                        f"(?i)({gate.value.lower().replace(' ', '|')})",
                        f"(?i)({gate.value.lower().replace(' ', '_')})"
                    ])
            
            if patterns:
                fallback_patterns[gate.value] = patterns[:5]  # Limit to 5 patterns
        
        return fallback_patterns
    
    def _determine_gate_status(self, score: float, gate_type: GateType = None, found: int = 0) -> str:
        """Determine gate status based on score with special handling for security gates"""
        
        # Special handling for security-critical gates
        if gate_type == GateType.AVOID_LOGGING_SECRETS and found > 0:
            return "FAIL"  # Any secrets violation = immediate failure
        
        # Standard score-based evaluation
        if score >= 50:
            return "PASS"
        elif score >= 40:
            return "WARNING" 
        else:
            return "FAIL"
    
    def _calculate_summary_metrics(self, result: ValidationResult):
        """Calculate overall summary metrics"""
        
        if not result.gate_scores:
            result.overall_score = 0.0
            return
        
        # Calculate file and line metrics
        result.total_files = len(result.file_analyses)
        result.total_lines = sum(f.lines_of_code for f in result.file_analyses)
        
        # Set scan duration
        result.scan_duration = time.time() - self._scan_start_time
        
        # Count gate statuses
        applicable_gates = []
        for gate_score in result.gate_scores:
            if gate_score.status == "PASS":
                result.passed_gates += 1
                applicable_gates.append(gate_score)
            elif gate_score.status == "WARNING":
                result.warning_gates += 1
                applicable_gates.append(gate_score)
            elif gate_score.status == "FAIL":
                result.failed_gates += 1
                applicable_gates.append(gate_score)
            elif gate_score.status == "FAILED":
                result.failed_gates += 1
                applicable_gates.append(gate_score)
            # NOT_APPLICABLE gates are not counted in any category
        
        # Calculate overall score only from applicable gates
        if applicable_gates:
            total_score = sum(gate.final_score for gate in applicable_gates)
            result.overall_score = total_score / len(applicable_gates)
        else:
            result.overall_score = 0.0
        
        # Add summary information about non-applicable gates
        not_applicable_count = len([g for g in result.gate_scores if g.status == "NOT_APPLICABLE"])
        if not_applicable_count > 0:
            result.recommendations.insert(0, 
                f"Note: {not_applicable_count} gates marked as 'Not Applicable' and excluded from scoring"
            )
    
    def _generate_recommendations(self, result: ValidationResult):
        """Generate high-level recommendations based on results"""
        
        recommendations = []
        critical_issues = []
        
        # Analyze failed gates
        failed_gates = [g for g in result.gate_scores if g.status == "FAIL"]
        warning_gates = [g for g in result.gate_scores if g.status == "WARNING"]
        
        if len(failed_gates) > 5:
            critical_issues.append(
                f"Multiple gate failures detected ({len(failed_gates)} gates failed)"
            )
            recommendations.append(
                "Focus on implementing basic logging and error handling first"
            )
        
        # Specific gate recommendations
        for gate in failed_gates[:3]:  # Top 3 failed gates
            if gate.gate == GateType.STRUCTURED_LOGS:
                recommendations.append(
                    "Implement structured logging with JSON format and consistent fields"
                )
            elif gate.gate == GateType.RETRY_LOGIC:
                recommendations.append(
                    "Add retry mechanisms with exponential backoff for I/O operations"
                )
            elif gate.gate == GateType.ERROR_LOGS:
                recommendations.append(
                    "Ensure all exceptions are logged with proper context"
                )
        
        # Coverage recommendations
        if result.overall_score < 50:
            critical_issues.append("Overall gate coverage is critically low")
            recommendations.append(
                "Consider implementing a gradual rollout of hard gates"
            )
        
        # Security recommendations
        secret_gate = next(
            (g for g in result.gate_scores if g.gate == GateType.AVOID_LOGGING_SECRETS),
            None
        )
        if secret_gate and secret_gate.status == "FAIL":
            critical_issues.append("Sensitive data detected in logs - security risk")
            recommendations.append("Immediately audit and remove sensitive data from logs")
        
        result.critical_issues = critical_issues
        result.recommendations = recommendations 
    
    def _detect_technologies_for_gate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> Dict[str, List[str]]:
        """Detect technologies relevant to the current gate validation"""
        
        technologies = {
            "frameworks": [],
            "logging": [],
            "testing": [],
            "databases": [],
            "web": []
        }
        
        # Simple technology detection based on file analysis
        for analysis in file_analyses[:10]:  # Sample first 10 files
            try:
                with open(analysis.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                
                # Framework detection
                if 'spring' in content or '@controller' in content:
                    technologies["frameworks"].append("Spring Boot")
                if 'flask' in content or 'from flask' in content:
                    technologies["frameworks"].append("Flask")
                if 'express' in content or 'app.get' in content:
                    technologies["frameworks"].append("Express.js")
                
                # Logging detection
                if 'logging' in content or 'logger' in content:
                    technologies["logging"].append("Standard Logging")
                if 'logback' in content or 'slf4j' in content:
                    technologies["logging"].append("SLF4J/Logback")
                if 'winston' in content:
                    technologies["logging"].append("Winston")
                
                # Testing detection
                if 'junit' in content or '@test' in content:
                    technologies["testing"].append("JUnit")
                if 'pytest' in content or 'unittest' in content:
                    technologies["testing"].append("Python Testing")
                if 'jest' in content or 'mocha' in content:
                    technologies["testing"].append("JavaScript Testing")
                
            except Exception:
                continue
        
        # Remove duplicates and empty lists
        return {k: list(set(v)) for k, v in technologies.items() if v} 
    
    def _detect_ui_components(self, target_path: Path, file_analyses: List[FileAnalysis]) -> bool:
        """Detect if the project has UI components"""
        
        ui_indicators = {
            # Frontend frameworks and libraries - more specific patterns
            'react': [r'import\s+React', r'from\s+["\']react["\']', r'React\.Component', r'\.jsx$', r'jsx'],
            'vue': [r'import.*Vue', r'Vue\.component', r'@Component', r'\.vue$'],
            'angular': [r'@angular/core', r'@Component', r'@Injectable.*Component', r'\.component\.ts$'],
            'svelte': [r'\.svelte$', r'import.*svelte'],
            
            # Web UI technologies - actual UI files
            'html_files': [r'\.html$', r'\.htm$'],
            'css_files': [r'\.css$', r'\.scss$', r'\.sass$', r'\.less$'],
            'frontend_js': [r'document\.getElementById', r'document\.querySelector', r'addEventListener', r'window\.'],
            
            # Mobile frameworks
            'react_native': [r'react-native', r'@react-native', r'StyleSheet\.create', r'View,', r'Text,'],
            'flutter': [r'import.*flutter', r'\.dart$', r'Widget.*build', r'StatelessWidget', r'StatefulWidget'],
            'xamarin': [r'Xamarin\.Forms', r'ContentPage', r'StackLayout'],
            
            # Desktop frameworks
            'electron': [r'electron', r'BrowserWindow', r'ipcRenderer'],
            'tkinter': [r'import tkinter', r'from tkinter', r'Tk\(\)', r'mainloop\(\)'],
            'pyqt': [r'PyQt', r'QApplication', r'QWidget', r'QMainWindow'],
            'wpf': [r'System\.Windows\.Controls', r'UserControl', r'Window\.xaml'],
            'winforms': [r'System\.Windows\.Forms', r'Form.*Designer', r'Button.*Click'],
        }
        
        # Check file extensions first
        ui_file_extensions = ['.html', '.htm', '.css', '.scss', '.sass', '.less', '.jsx', '.tsx', '.vue', '.svelte']
        for analysis in file_analyses:
            file_path = Path(analysis.file_path)
            if file_path.suffix.lower() in ui_file_extensions:
                print(f"🖥️ UI file detected: {file_path.name} (extension: {file_path.suffix})")
                return True
        
        # Check file content for UI indicators
        for analysis in file_analyses:
            file_path = Path(analysis.file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    for ui_type, patterns in ui_indicators.items():
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                                # Additional validation to avoid false positives
                                if ui_type == 'html_files' and not self._is_actual_html_content(content):
                                    continue
                                if ui_type == 'frontend_js' and not self._is_frontend_javascript(content):
                                    continue
                                    
                                print(f"🖥️ UI component detected: {ui_type} in {file_path.name}")
                                return True
                                
            except Exception:
                continue
        
        # Check for UI-specific directories (more restrictive)
        ui_directories = ['src/components', 'components', 'views', 'pages', 'static/css', 'static/js', 'public', 'assets/css', 'www']
        for ui_dir in ui_directories:
            ui_path = target_path / ui_dir
            if ui_path.exists() and any(ui_path.iterdir()):  # Directory exists and is not empty
                print(f"🖥️ UI directory detected: {ui_dir}")
                return True
        
        # Check package.json for UI dependencies (more specific)
        package_json = target_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    content = f.read().lower()
                    # More specific UI packages
                    ui_packages = ['react', 'vue', 'angular', '@angular', 'svelte', 'jquery', 'bootstrap', 'material-ui', 'antd', 'react-dom']
                    for package in ui_packages:
                        if f'"{package}"' in content or f"'{package}'" in content:
                            print(f"🖥️ UI package detected in package.json: {package}")
                            return True
            except Exception:
                pass
        
        print("📄 No UI components detected - backend/CLI project")
        return False
    
    def _is_actual_html_content(self, content: str) -> bool:
        """Check if content is actual HTML (not just contains HTML-like strings)"""
        content_lower = content.lower()
        # Look for actual HTML structure, not just HTML strings in code
        html_indicators = ['<html', '<head>', '<body>', '<div', '<span', '<p>', '<h1', '<h2', '<h3']
        tag_count = sum(1 for indicator in html_indicators if indicator in content_lower)
        return tag_count >= 2  # At least 2 HTML tags to be considered HTML content
    
    def _is_frontend_javascript(self, content: str) -> bool:
        """Check if JavaScript is frontend-related (not just server-side)"""
        content_lower = content.lower()
        # Avoid false positives from server-side code
        if any(keyword in content_lower for keyword in ['express', 'app.get', 'app.post', 'require(', 'module.exports']):
            return False
        # Look for actual DOM manipulation
        dom_indicators = ['getelementbyid', 'queryselector', 'addeventlistener', 'window.location']
        return any(indicator in content_lower for indicator in dom_indicators)
    
    def _is_gate_applicable(self, gate_type: GateType, target_path: Path, 
                          file_analyses: List[FileAnalysis], has_ui_components: bool) -> bool:
        """Determine if a gate is applicable to this project"""
        
        # UI-specific gates
        if gate_type in [GateType.UI_ERRORS, GateType.UI_ERROR_TOOLS]:
            return has_ui_components
        
        # Background job gates - make always applicable for better coverage
        # Projects should implement background job logging even if not currently using background jobs
        if gate_type == GateType.LOG_BACKGROUND_JOBS:
            return True  # Always applicable - encourages implementation
        
        # Logs Searchable/Available and Log Application Messages gates work together
        if gate_type in [GateType.STRUCTURED_LOGS, GateType.LOG_APPLICATION_MESSAGES]:
            return True  # Always applicable - work in conjunction
        
        # All other gates are applicable by default
        return True
    
    def _has_background_jobs(self, target_path: Path, file_analyses: List[FileAnalysis]) -> bool:
        """Detect if the project has background job processing"""
        
        background_indicators = {
            'celery': [r'import celery', r'@task', r'@shared_task'],
            'rq': [r'import rq', r'@job', r'Queue\('],
            'cron': [r'crontab', r'@cron', r'schedule\.'],
            'threading': [r'import threading', r'Thread\(', r'ThreadPoolExecutor'],
            'asyncio': [r'import asyncio', r'async def', r'await ', r'asyncio\.create_task'],
            'multiprocessing': [r'import multiprocessing', r'Process\(', r'Pool\('],
            'background_tasks': [r'background.*task', r'BackgroundTasks', r'@background'],
            'workers': [r'worker\.py', r'workers/', r'job.*queue'],
        }
        
        for analysis in file_analyses:
            try:
                with open(analysis.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    for bg_type, patterns in background_indicators.items():
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                                print(f"⚙️ Background processing detected: {bg_type}")
                                return True
                                
            except Exception:
                continue
        
        return False 
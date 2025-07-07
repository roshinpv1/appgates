"""
Core Gate Validator - Orchestrates validation of all 15 hard gates
"""

import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
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
            # Scan files first
            file_analyses = self._scan_files(target_path)
            result.file_analyses = file_analyses
            
            # Validate all gates
            gate_scores = self._validate_all_gates(target_path, file_analyses, llm_manager)
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
                          llm_manager=None) -> List[GateScore]:
        """Validate all 15 hard gates"""
        
        gate_scores = []
        
        # Detect UI components in the project
        has_ui_components = self._detect_ui_components(target_path, file_analyses)
        
        # Process each gate type
        for gate_type in GateType:
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
                    gate_type, target_path, file_analyses, llm_manager
                )
                gate_scores.append(gate_score)
                
            except Exception as e:
                # Create failed gate score
                gate_score = GateScore(
                    gate=gate_type,
                    expected=0,
                    found=0,
                    coverage=0.0,
                    quality_score=0.0,
                    final_score=0.0,
                    status="FAILED",
                    details=[f"Validation error: {str(e)}"],
                    recommendations=[f"Fix validation error for {gate_type.value}"]
                )
                gate_scores.append(gate_score)
        
        return gate_scores
    
    def _validate_single_gate(self, gate_type: GateType, 
                            target_path: Path, 
                            file_analyses: List[FileAnalysis],
                            llm_manager=None) -> GateScore:
        """Validate a single gate type"""
        
        # Get appropriate validator for the gate
        validators = []
        for lang in self.config.languages:
            validator = self.validator_factory.get_validator(gate_type, lang)
            if validator:
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
        quality_scores = []
        all_matches = []
        
        for validator in validators:
            try:
                result = validator.validate(target_path, file_analyses)
                total_expected += result.expected
                total_found += result.found
                all_details.extend(result.details)
                all_recommendations.extend(result.recommendations)
                quality_scores.append(result.quality_score)
                
                # Collect matches for LLM analysis and detailed reporting
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
                    # Don't increment total_found to avoid false failure due to error
        
        # Add detailed match information to details
        if all_matches:
            # Filter out non-matching patterns - only show actual matches
            actual_matches = []
            for match in all_matches:
                file_path = match.get('file_path', match.get('file', ''))
                matched_text = match.get('matched_text', match.get('match', ''))
                line_number = match.get('line_number', match.get('line', 0))
                
                # Only include actual matches (not pattern attempts)
                if (file_path and file_path != 'N/A - No matches found' and 
                    file_path != 'unknown' and matched_text.strip() and 
                    line_number > 0):
                    actual_matches.append(match)
            
            if actual_matches:
                all_details.append(f"Found {len(actual_matches)} actual pattern matches:")
                
                # Group matches by file for better organization
                matches_by_file = {}
                for match in actual_matches[:15]:  # Limit to first 15 actual matches
                    file_path = match.get('file_path', match.get('file', 'unknown'))
                    if file_path not in matches_by_file:
                        matches_by_file[file_path] = []
                    matches_by_file[file_path].append(match)
                
                # Add organized match details
                for file_path, file_matches in matches_by_file.items():
                    # Make file path relative to target for readability
                    try:
                        relative_path = Path(file_path).relative_to(target_path)
                    except ValueError:
                        relative_path = Path(file_path).name
                    
                    all_details.append(f"📁 {relative_path}:")
                    for match in file_matches[:5]:  # Limit to 5 matches per file
                        line_num = match.get('line_number', match.get('line', '?'))
                        match_text = match.get('matched_text', match.get('match', '')).strip()
                        pattern = match.get('pattern', '')
                        
                        # Truncate long matches for readability
                        if len(match_text) > 80:
                            match_text = match_text[:77] + "..."
                        
                        all_details.append(f"   Line {line_num}: {match_text}")
                        if pattern:
                            all_details.append(f"   Pattern: {pattern}")
                        
                        # Add additional metadata if available
                        if match.get('severity'):
                            all_details.append(f"   Severity: {match['severity']}")
                        if match.get('function_context'):
                            all_details.append(f"   Function: {match['function_context']}")
                    
                    if len(file_matches) > 5:
                        all_details.append(f"   ... and {len(file_matches) - 5} more matches in this file")
                
                if len(actual_matches) > 15:
                    all_details.append(f"... and {len(actual_matches) - 15} more matches in other files")
            else:
                all_details.append("No actual pattern matches found (only pattern attempts)")
        
        # Update all_matches to only include actual matches for further processing
        all_matches = actual_matches if 'actual_matches' in locals() else []
        
        # Calculate final scores
        coverage = (total_found / total_expected * 100) if total_expected > 0 else 0.0

        # Special handling for "negative" gates where lower found count is better
        # For gates where expected = 0 (like avoid_logging_secrets), 
        # found = 0 means perfect implementation (100% coverage)
        if total_expected == 0:
            if total_found == 0:
                coverage = 100.0  # Perfect: no violations found
            else:
                # Security-critical gates: ANY violation should result in failure
                if gate_type == GateType.AVOID_LOGGING_SECRETS:
                    coverage = 0.0  # Any secrets violation = complete failure
                else:
                    coverage = max(0.0, 100.0 - (total_found * 10))  # Penalty for violations

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Ensure avg_quality is never None and is within valid range
        if avg_quality is None:
            avg_quality = 0.0
        avg_quality = max(0.0, min(float(avg_quality), 100.0))
        
        final_score = self.gate_scorer.calculate_gate_score(
            coverage, avg_quality, gate_type
        )
        
        # Apply LLM enhancement if available
        if llm_manager and llm_manager.is_enabled():
            print(f"🤖 LLM analyzing gate: {gate_type.value}, matches: {len(all_matches)}")
            try:
                enhancement = llm_manager.enhance_gate_validation(
                    gate_type.value,
                    all_matches,
                    self.config.languages[0] if self.config.languages else Language.PYTHON,
                    self._detect_technologies_for_gate(target_path, file_analyses),
                    all_recommendations
                )
                
                if enhancement:
                    # Apply LLM enhancements
                    if 'enhanced_quality_score' in enhancement and enhancement['enhanced_quality_score'] is not None:
                        enhanced_score = float(enhancement['enhanced_quality_score'])
                        avg_quality = max(0.0, min(enhanced_score, 100.0))
                    
                    if 'llm_recommendations' in enhancement and enhancement['llm_recommendations']:
                        all_recommendations = enhancement['llm_recommendations']
                    
                    if 'code_examples' in enhancement and enhancement['code_examples']:
                        all_details.extend([f"💡 {example[:200]}..." for example in enhancement['code_examples'][:2]])
                    
                    if 'security_insights' in enhancement and enhancement['security_insights']:
                        all_details.extend([f"🔒 {insight}" for insight in enhancement['security_insights'][:2]])
                    
                    print(f"✅ LLM enhancement applied to {gate_type.value}")
                else:
                    print(f"⚠️ LLM returned empty enhancement for {gate_type.value}")
                    
            except Exception as e:
                print(f"⚠️ LLM enhancement failed for {gate_type.value}: {str(e)[:100]}...")
                # Continue with pattern-based analysis
        elif llm_manager:
            print(f"⚠️ LLM not available, using pattern-based analysis for {gate_type.value}")
        else:
            print(f"📊 Using pattern-based analysis for {gate_type.value}")
        
        # Determine status
        status = self._determine_gate_status(final_score, gate_type, total_found)
        
        return GateScore(
            gate=gate_type,
            expected=total_expected,
            found=total_found,
            coverage=coverage,
            quality_score=avg_quality,
            final_score=final_score,
            status=status,
            details=all_details,
            recommendations=all_recommendations,  # Don't use set() to avoid unhashable type error
            matches=all_matches  # Include enhanced metadata
        )
    
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
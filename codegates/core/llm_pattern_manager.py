"""
LLM Pattern Manager - Handles LLM calls for dynamic pattern generation
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .enhanced_processor import EnhancedProcessor
from .llm_analyzer import LLMAnalyzer, LLMConfig, LLMProvider
from ..models import Language, GateType
from ..utils.env_loader import EnvironmentLoader


class LLMPatternManager:
    """Manages LLM-based pattern generation for hard gates"""
    
    def __init__(self):
        self.processor = EnhancedProcessor()
        self.llm_analyzer = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM if available
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM analyzer if available"""
        try:
            env_loader = EnvironmentLoader()
            preferred_provider = env_loader.get_preferred_llm_provider()
            
            if preferred_provider:
                # Get the LLM configuration for the preferred provider
                llm_config_dict = env_loader.get_llm_config(preferred_provider)
                
                if llm_config_dict:
                    # Create LLMConfig object from the dictionary
                    llm_config = LLMConfig(
                        provider=LLMProvider(preferred_provider),
                        model=llm_config_dict.get('model', 'gpt-4'),
                        api_key=llm_config_dict.get('api_key', ''),
                        base_url=llm_config_dict.get('base_url'),
                        temperature=llm_config_dict.get('temperature', 0.1),
                        max_tokens=llm_config_dict.get('max_tokens', 4000)
                    )
                    
                    self.llm_analyzer = LLMAnalyzer(llm_config)
                    self.logger.info(f"LLM Pattern Manager initialized with {preferred_provider}")
                else:
                    self.logger.warning(f"No configuration found for provider: {preferred_provider}")
                    self.llm_analyzer = None
            else:
                self.logger.warning("No LLM provider configured - will use fallback patterns")
                self.llm_analyzer = None
                
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            self.llm_analyzer = None
    
    def generate_patterns_for_codebase(self, target_path: Path, languages: List[Language]) -> Dict[str, Any]:
        """Generate LLM-based patterns for a codebase with comprehensive analysis"""
        
        print(f"🤖 Generating comprehensive LLM patterns for: {target_path}")
        
        # Step 1: Comprehensive codebase analysis (similar to processor.py)
        try:
            print("📊 Performing comprehensive codebase analysis...")
            
            # Get all files in the codebase
            all_files = []
            for ext in ['*.java', '*.py', '*.js', '*.ts', '*.go', '*.rb', '*.php', '*.cs']:
                all_files.extend(target_path.rglob(ext))
            
            print(f"📁 Found {len(all_files)} code files")
            
            # Analyze file contents and structure
            file_analyses = []
            total_lines = 0
            language_stats = {}
            
            for file_path in all_files:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    total_lines += len(lines)
                    
                    # Determine language
                    lang = self._detect_language(file_path)
                    if lang:
                        language_stats[lang] = language_stats.get(lang, 0) + 1
                    
                    # Basic file analysis
                    file_analysis = {
                        'path': str(file_path.relative_to(target_path)),
                        'language': lang,
                        'lines': len(lines),
                        'size': len(content),
                        'content': content,  # Include content for framework detection
                        'has_logging': self._has_logging_statements(content, lang),
                        'has_security': self._has_security_patterns(content, lang),
                        'has_errors': self._has_error_handling(content, lang)
                    }
                    file_analyses.append(file_analysis)
                    
                except Exception as e:
                    print(f"⚠️ Error analyzing {file_path}: {e}")
            
            print(f"📈 Analysis complete: {total_lines} total lines across {len(file_analyses)} files")
            print(f"🌐 Languages detected: {language_stats}")
            
        except Exception as e:
            print(f"❌ Comprehensive analysis failed: {e}")
            return self._generate_fallback_patterns({}, [gate.value for gate in GateType])
        
        # Step 2: Enhanced config and build file analysis (like processor.py)
        try:
            print("🔧 Analyzing configuration and build files...")
            
            config_files = self._analyze_config_files(target_path)
            build_files = self._analyze_build_files(target_path)
            dependencies = self._extract_dependencies(target_path)
            
            print(f"📋 Config files: {len(config_files)} found")
            print(f"🔨 Build files: {len(build_files)} found")
            print(f"📦 Dependencies: {len(dependencies)} detected")
            
        except Exception as e:
            print(f"⚠️ Config/build analysis failed: {e}")
            config_files = {}
            build_files = {}
            dependencies = []
        
        # Step 3: Enhanced custom library detection (similar to processor.py)
        try:
            print("🔍 Detecting custom libraries and frameworks...")
            
            custom_libraries = self._detect_custom_libraries_comprehensive(target_path, file_analyses, dependencies)
            
            if custom_libraries:
                print(f"📚 Custom libraries detected: {list(custom_libraries.keys())}")
                for lib_name, lib_info in custom_libraries.items():
                    print(f"   - {lib_name}: {lib_info.get('description', 'No description')}")
            else:
                print("📚 No custom libraries detected")
                
        except Exception as e:
            print(f"⚠️ Custom library detection failed: {e}")
            custom_libraries = {}
        
        # Step 4: Enhanced technology context
        try:
            print("🔧 Building enhanced technology context...")
            
            tech_context = {
                'languages': list(language_stats.keys()),
                'total_files': len(file_analyses),
                'total_lines': total_lines,
                'language_distribution': language_stats,
                'custom_libraries': custom_libraries,
                'config_files': config_files,
                'build_files': build_files,
                'dependencies': dependencies,
                'frameworks': self._detect_frameworks(file_analyses),
                'build_tools': self._detect_build_tools(target_path),
                'deployment': self._detect_deployment_config(target_path)
            }
            
            print(f"🔧 Technology context: {len(tech_context['languages'])} languages, {len(tech_context.get('frameworks', []))} frameworks")
            
        except Exception as e:
            print(f"⚠️ Technology context building failed: {e}")
            tech_context = {'languages': languages}
        
        # Step 5: Generate comprehensive LLM prompt (similar to processor.py)
        try:
            hard_gates = [gate.value for gate in GateType]
            prompt = self._generate_comprehensive_llm_prompt(
                target_path=target_path,
                file_analyses=file_analyses,
                tech_context=tech_context,
                custom_libraries=custom_libraries,
                config_files=config_files,
                build_files=build_files,
                dependencies=dependencies,
                hard_gates=hard_gates
            )
            
            print(f"📋 Generated comprehensive prompt ({len(prompt)} characters)")
            
        except Exception as e:
            print(f"❌ Comprehensive prompt generation failed: {e}")
            return self._generate_fallback_patterns(tech_context, hard_gates)
        
        # Step 6: Call LLM with comprehensive prompt
        try:
            print("🤖 Calling LLM with comprehensive analysis...")
            llm_response = self._call_llm_for_patterns(prompt)
            
            if llm_response:
                print("✅ LLM response received successfully")
                
                # Parse the comprehensive response
                parsed_patterns = self._parse_comprehensive_llm_response(llm_response, hard_gates)
                
                # Convert to gate config format
                gate_config = self._convert_to_gate_config(parsed_patterns, hard_gates)
                
                return {
                    'success': True,
                    'llm_response': {
                        'raw_response': llm_response,
                        'parsed_patterns': parsed_patterns,
                        'hard_gates_analysis_short': gate_config
                    },
                    'gate_config': gate_config,
                    'analysis': {
                        'file_analyses': file_analyses,
                        'tech_context': tech_context,
                        'custom_libraries': custom_libraries,
                        'config_files': config_files,
                        'build_files': build_files,
                        'dependencies': dependencies
                    },
                    'prompt': prompt
                }
            else:
                raise ValueError("Empty LLM response")
                
        except Exception as e:
            print(f"❌ LLM pattern generation failed with detailed error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'llm_response': {},
                'gate_config': {},
                'analysis': {
                    'file_analyses': file_analyses,
                    'tech_context': tech_context,
                    'custom_libraries': custom_libraries,
                    'config_files': config_files,
                    'build_files': build_files,
                    'dependencies': dependencies
                },
                'prompt': prompt
            }
    
    def _log_llm_response(self, llm_response: str):
        """Log the raw LLM response for debugging"""
        
        print("\n" + "="*80)
        print("📋 RAW LLM RESPONSE")
        print("="*80)
        print(llm_response)
        print("="*80)
        
        # Also log to file for persistence
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"llm_response_{timestamp}.json"
            
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(llm_response)
            
            print(f"💾 Raw LLM response saved to: {log_filename}")
            
        except Exception as e:
            print(f"⚠️ Failed to save LLM response to file: {e}")
    
    def _log_parsed_patterns(self, parsed_response: Dict[str, Any]):
        """Log the parsed patterns for each gate"""
        
        print("\n" + "="*80)
        print("🎯 PARSED PATTERNS BY GATE")
        print("="*80)
        
        hard_gates_analysis = parsed_response.get('hard_gates_analysis_short', {})
        
        for gate_name, gate_data in hard_gates_analysis.items():
            print(f"\n🔍 Gate: {gate_name}")
            print(f"   Analysis: {gate_data.get('analysis', 'No analysis provided')}")
            print(f"   Patterns ({len(gate_data.get('patterns', []))}):")
            
            for i, pattern in enumerate(gate_data.get('patterns', []), 1):
                print(f"     {i}. {pattern}")
        
        # Log technology summary
        tech_summary = parsed_response.get('tech_summary', {})
        if tech_summary:
            print(f"\n🏗️  Technology Summary:")
            for tech_type, tech_list in tech_summary.items():
                if tech_list:
                    print(f"   {tech_type}: {', '.join(tech_list)}")
        
        print("="*80)
        
        # Save parsed patterns to file
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            patterns_filename = f"parsed_patterns_{timestamp}.json"
            
            with open(patterns_filename, 'w', encoding='utf-8') as f:
                json.dump(parsed_response, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Parsed patterns saved to: {patterns_filename}")
            
        except Exception as e:
            print(f"⚠️ Failed to save parsed patterns to file: {e}")
    
    def _log_pattern_usage(self, gate_type: GateType, patterns: List[str], matches: List[Dict[str, Any]]):
        """Log pattern usage and matches for a specific gate"""
        
        gate_name = gate_type.value
        print(f"\n🎯 Pattern Usage for {gate_name}:")
        print(f"   Patterns used: {len(patterns)}")
        print(f"   Matches found: {len(matches)}")
        
        for i, pattern in enumerate(patterns, 1):
            pattern_matches = [m for m in matches if m.get('pattern') == pattern]
            print(f"   Pattern {i}: '{pattern}' -> {len(pattern_matches)} matches")
            
            # Show sample matches
            for j, match in enumerate(pattern_matches[:3], 1):
                file_path = match.get('file', 'unknown')
                line_number = match.get('line_number', 'unknown')
                matched_text = match.get('matched_text', 'unknown')[:100]
                print(f"     Match {j}: {file_path}:{line_number} - {matched_text}...")
            
            if len(pattern_matches) > 3:
                print(f"     ... and {len(pattern_matches) - 3} more matches")
    
    def _log_llm_prompt(self, prompt: str):
        """Log the prompt sent to the LLM for debugging"""
        
        print("\n" + "="*80)
        print("📋 LLM PROMPT")
        print("="*80)
        print(prompt)
        print("="*80)
        
        # Also log to file for persistence
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_filename = f"llm_prompt_{timestamp}.txt"
            
            with open(prompt_filename, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            print(f"💾 LLM prompt saved to: {prompt_filename}")
            
        except Exception as e:
            print(f"⚠️ Failed to save LLM prompt to file: {e}")
    
    def _log_pattern_generation_summary(self, parsed_response: Dict[str, Any], gate_config: Dict[str, Any]):
        """Log a summary of the pattern generation results"""
        
        print("\n" + "="*80)
        print("📊 PATTERN GENERATION SUMMARY")
        print("="*80)
        
        hard_gates_analysis = parsed_response.get('hard_gates_analysis_short', {})
        tech_summary = parsed_response.get('tech_summary', {})
        
        # Technology summary
        print(f"🏗️  Detected Technologies:")
        for tech_type, tech_list in tech_summary.items():
            if tech_list:
                print(f"   {tech_type}: {len(tech_list)} items")
        
        # Pattern summary
        total_patterns = 0
        gates_with_patterns = 0
        
        for gate_name, gate_data in hard_gates_analysis.items():
            patterns = gate_data.get('patterns', [])
            if patterns:
                gates_with_patterns += 1
                total_patterns += len(patterns)
                print(f"   {gate_name}: {len(patterns)} patterns")
        
        print(f"\n📈 Statistics:")
        print(f"   Total gates processed: {len(hard_gates_analysis)}")
        print(f"   Gates with patterns: {gates_with_patterns}")
        print(f"   Total patterns generated: {total_patterns}")
        print(f"   Average patterns per gate: {total_patterns / max(gates_with_patterns, 1):.1f}")
        
        # Success rate
        success_rate = (gates_with_patterns / len(hard_gates_analysis)) * 100 if hard_gates_analysis else 0
        print(f"   Pattern generation success rate: {success_rate:.1f}%")
        
        print("="*80)
        
        # Save summary to file
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_filename = f"pattern_generation_summary_{timestamp}.json"
            
            summary_data = {
                "timestamp": timestamp,
                "technology_summary": tech_summary,
                "pattern_summary": {
                    "total_gates": len(hard_gates_analysis),
                    "gates_with_patterns": gates_with_patterns,
                    "total_patterns": total_patterns,
                    "average_patterns_per_gate": total_patterns / max(gates_with_patterns, 1),
                    "success_rate": success_rate
                },
                "gate_patterns": {
                    gate_name: {
                        "patterns_count": len(gate_data.get('patterns', [])),
                        "analysis": gate_data.get('analysis', ''),
                        "patterns": gate_data.get('patterns', [])
                    }
                    for gate_name, gate_data in hard_gates_analysis.items()
                }
            }
            
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Pattern generation summary saved to: {summary_filename}")
            
        except Exception as e:
            print(f"⚠️ Failed to save pattern generation summary to file: {e}")
    
    def _call_llm_for_patterns(self, prompt: str) -> str:
        """Call LLM for pattern generation with timeout handling"""
        
        try:
            print(f"📤 Sending prompt to LLM (length: {len(prompt)} characters)")
            
            # Check if LLM analyzer is properly initialized
            if not self.llm_analyzer:
                raise ValueError("LLM analyzer not initialized")
            
            # Use the LLM analyzer's call method
            response = self.llm_analyzer._call_llm(prompt)
            
            # Validate response
            if not response:
                raise ValueError("LLM returned empty response")
            
            if len(response.strip()) < 100:
                raise ValueError(f"LLM response too short ({len(response)} characters), expected at least 100 characters")
            
            print(f"📥 Received LLM response (length: {len(response)} characters)")
            
            return response
            
        except Exception as e:
            print(f"❌ LLM call failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _generate_fallback_patterns(self, analysis: Dict[str, Any], hard_gates: List[str]) -> Dict[str, Any]:
        """Generate fallback patterns when LLM is not available"""
        
        print("🔄 Generating fallback patterns...")
        
        # Create basic fallback patterns based on detected technologies
        tech_context = analysis.get('technology_context', {})
        
        # Handle both dict and TechnologyContext object
        if hasattr(tech_context, 'languages'):
            languages = tech_context.languages
        else:
            languages = tech_context.get('languages', [])
        
        fallback_patterns = {}
        
        for gate in hard_gates:
            patterns = self._get_fallback_patterns_for_gate(gate, languages)
            fallback_patterns[gate] = {
                "analysis": f"Fallback patterns for {gate} based on detected technologies",
                "patterns": patterns
            }
        
        return {
            'success': False,
            'llm_response': {
                "tech_summary": {
                    "languages": languages,
                    "frameworks": tech_context.get('frameworks', []) if isinstance(tech_context, dict) else getattr(tech_context, 'frameworks', []),
                    "databases": tech_context.get('databases', []) if isinstance(tech_context, dict) else getattr(tech_context, 'databases', []),
                    "build_tools": tech_context.get('build_tools', []) if isinstance(tech_context, dict) else getattr(tech_context, 'build_tools', []),
                    "containerization": tech_context.get('containerization', []) if isinstance(tech_context, dict) else getattr(tech_context, 'containerization', []),
                    "frontend": tech_context.get('frontend', []) if isinstance(tech_context, dict) else getattr(tech_context, 'frontend', []),
                    "testing": tech_context.get('testing', []) if isinstance(tech_context, dict) else getattr(tech_context, 'testing', []),
                    "code_quality": tech_context.get('code_quality', []) if isinstance(tech_context, dict) else getattr(tech_context, 'code_quality', [])
                },
                "hard_gates_analysis_short": fallback_patterns
            },
            'gate_config': self.processor.convert_llm_patterns_to_gate_config({
                "hard_gates_analysis_short": fallback_patterns
            }),
            'analysis': analysis,
            'prompt': "Fallback patterns generated without LLM"
        }
    
    def _get_fallback_patterns_for_gate(self, gate: str, languages: List[str]) -> List[str]:
        """Get fallback patterns for a specific gate based on languages"""
        
        # Basic fallback patterns by gate and language
        fallback_patterns = {
            "Logs Searchable/Available": {
                "Java": [
                    "(?i)(log\\.(info|debug|error|warn)|logger\\.(info|debug|error|warn))",
                    "(?i)(import\\s+org\\.slf4j|import\\s+ch\\.qos\\.logback)",
                    "(?i)(logback\\.xml|log4j\\.xml)"
                ],
                "Python": [
                    "(?i)(logging\\.(info|debug|error|warning)|logger\\.(info|debug|error|warning))",
                    "(?i)(import\\s+logging|import\\s+structlog)",
                    "(?i)(loguru|python-json-logger)"
                ],
                "JavaScript": [
                    "(?i)(console\\.(log|info|debug|error|warn))",
                    "(?i)(winston|bunyan|pino)",
                    "(?i)(import\\s+winston|import\\s+bunyan)"
                ]
            },
            "Avoid Logging Confidential Data": {
                "Java": [
                    "(?i)(log\\.(info|debug|warn|error)\\s*\\(.*(password|secret|token|ssn|creditCard|PII|credential|apiKey|auth).*\\))",
                    "(?i)(System\\.out\\.print(ln)?\\s*\\(.*(password|secret|token|ssn|creditCard|PII|credential|apiKey|auth).*\\))"
                ],
                "Python": [
                    "(?i)(logging\\.(info|debug|error|warning)\\s*\\(.*(password|secret|token|ssn|credit_card|pii|credential|api_key|auth).*\\))",
                    "(?i)(print\\s*\\(.*(password|secret|token|ssn|credit_card|pii|credential|api_key|auth).*\\))"
                ],
                "JavaScript": [
                    "(?i)(console\\.(log|info|debug|error|warn)\\s*\\(.*(password|secret|token|ssn|creditCard|pii|credential|apiKey|auth).*\\))"
                ]
            },
            "Create Audit Trail Logs": {
                "Java": [
                    "(?i)(@CreatedBy|@LastModifiedBy|@CreatedDate|@LastModifiedDate|@EnableJpaAuditing)",
                    "(?i)(Audit(Service|Log|Entry|Event)?|UserActivity)",
                    "(?i)(log\\.(info|debug|warn)\\s*\\(.*(user|activity|action|event|change|audit).*\\))"
                ],
                "Python": [
                    "(?i)(@audit|@track_changes|audit_log)",
                    "(?i)(logging\\.(info|debug|error|warning)\\s*\\(.*(user|activity|action|event|change|audit).*\\))"
                ],
                "JavaScript": [
                    "(?i)(auditLog|trackActivity|userActivity)",
                    "(?i)(console\\.(log|info|debug|error|warn)\\s*\\(.*(user|activity|action|event|change|audit).*\\))"
                ]
            },
            "Tracking ID for Logs": {
                "Java": [
                    "(?i)(MDC\\.(put|get|clear)|TraceId|SpanId|X-B3-TraceId|X-B3-SpanId)",
                    "(?i)(logging\\.pattern\\.level:.*%X\\{traceId\\}.*|logging\\.pattern\\.console:.*%X\\{traceId\\}.*)"
                ],
                "Python": [
                    "(?i)(trace_id|span_id|correlation_id)",
                    "(?i)(logging\\.(info|debug|error|warning)\\s*\\(.*(trace_id|span_id|correlation_id).*\\))"
                ],
                "JavaScript": [
                    "(?i)(traceId|spanId|correlationId)",
                    "(?i)(console\\.(log|info|debug|error|warn)\\s*\\(.*(traceId|spanId|correlationId).*\\))"
                ]
            },
            "Log REST API Calls": {
                "Java": [
                    "(?i)(@RestController|@Controller).*(log\\.(info|debug|warn|error)\\s*\\(.*(request|response|path|method|uri|status).*\\))",
                    "(?i)(FilterConfig|HandlerInterceptor|WebMvcConfigurer).*(log\\.(info|debug|warn|error).*HttpServletRequest)"
                ],
                "Python": [
                    "(?i)(@app\\.before_request|@app\\.after_request)",
                    "(?i)(logging\\.(info|debug|error|warning)\\s*\\(.*(request|response|path|method|uri|status).*\\))"
                ],
                "JavaScript": [
                    "(?i)(app\\.use.*logging|middleware.*logging)",
                    "(?i)(console\\.(log|info|debug|error|warn)\\s*\\(.*(request|response|path|method|uri|status).*\\))"
                ]
            },
            "Log Application Messages": {
                "Java": [
                    "(?i)(log\\.(info|debug|warn|error)\\s*\\(.*\\)|logger\\.(info|debug|warn|error)\\s*\\(.*\\))",
                    "(?i)System\\.out\\.print(ln)?\\s*\\(.*\\)"
                ],
                "Python": [
                    "(?i)(logging\\.(info|debug|error|warning)\\s*\\(.*\\)|logger\\.(info|debug|error|warning)\\s*\\(.*\\))",
                    "(?i)print\\s*\\(.*\\)"
                ],
                "JavaScript": [
                    "(?i)(console\\.(log|info|debug|error|warn)\\s*\\(.*\\))"
                ]
            },
            "Client UI Errors Logged": {
                "Java": [
                    "(?i)(onerror|console\\.error|window\\.addEventListener\\(['\"]error['\"])",
                    "(?i)(<div\\s+th:if=\"\\$\\{#fields\\.hasErrors\\(['\"]\\w+['\"]\\)\"|th:errors=\")"
                ],
                "Python": [
                    "(?i)(onerror|console\\.error|window\\.addEventListener\\(['\"]error['\"])"
                ],
                "JavaScript": [
                    "(?i)(onerror|console\\.error|window\\.addEventListener\\(['\"]error['\"])",
                    "(?i)(errorHandler|reportError|errorHandler\\.js)"
                ]
            },
            "Retry Logic": {
                "Java": [
                    "(?i)(@Retryable|RetryTemplate|RetryPolicy|BackOffPolicy)",
                    "(?i)(maxAttempts|initialInterval|multiplier|maxInterval)"
                ],
                "Python": [
                    "(?i)(@retry|tenacity|retry\\.decorator)",
                    "(?i)(max_attempts|initial_interval|multiplier|max_interval)"
                ],
                "JavaScript": [
                    "(?i)(retry|retryable|maxAttempts)",
                    "(?i)(axios-retry|retry-axios)"
                ]
            },
            "Timeouts in IO Ops": {
                "Java": [
                    "(?i)(connectionTimeout|readTimeout|socketTimeout|maxWait|loginTimeout)",
                    "(?i)(RestTemplateBuilder\\.setConnectTimeout|RestTemplateBuilder\\.setReadTimeout)"
                ],
                "Python": [
                    "(?i)(timeout|connect_timeout|read_timeout)",
                    "(?i)(requests\\.get.*timeout|urllib\\.request.*timeout)"
                ],
                "JavaScript": [
                    "(?i)(timeout|connectTimeout|readTimeout)",
                    "(?i)(axios.*timeout|fetch.*timeout)"
                ]
            },
            "Throttling & Drop Request": {
                "Java": [
                    "(?i)(rateLimit|throttle|TooManyRequestsException|RateLimiter)",
                    "(?i)(response\\.setStatus\\(429\\)|HttpStatus\\.TOO_MANY_REQUESTS)"
                ],
                "Python": [
                    "(?i)(rate_limit|throttle|TooManyRequestsException)",
                    "(?i)(response\\.status_code\\s*=\\s*429)"
                ],
                "JavaScript": [
                    "(?i)(rateLimit|throttle|TooManyRequestsException)",
                    "(?i)(response\\.status\\s*=\\s*429)"
                ]
            },
            "Circuit Breakers": {
                "Java": [
                    "(?i)(@CircuitBreaker|@EnableCircuitBreaker|CircuitBreakerFactory|HystrixCommand|@HystrixCommand)",
                    "(?i)(fallbackMethod|allowRequestVolumeThreshold|slidingWindowSize)"
                ],
                "Python": [
                    "(?i)(circuit_breaker|CircuitBreaker|fallback)",
                    "(?i)(pybreaker|circuitbreaker)"
                ],
                "JavaScript": [
                    "(?i)(circuitBreaker|CircuitBreaker|fallback)",
                    "(?i)(opossum|circuit-breaker)"
                ]
            },
            "Log System Errors": {
                "Java": [
                    "(?i)(@ControllerAdvice|@RestControllerAdvice|@ExceptionHandler)",
                    "(?i)(log\\.error\\s*\\(.*(Exception|Throwable)\\s*e.*\\)|e\\.printStackTrace\\(\\))"
                ],
                "Python": [
                    "(?i)(@app\\.errorhandler|try:\\s*.*\\s*except\\s+Exception)",
                    "(?i)(logging\\.error\\s*\\(.*(Exception|Error).*\\))"
                ],
                "JavaScript": [
                    "(?i)(app\\.use.*error|process\\.on\\(['\"]uncaughtException['\"])",
                    "(?i)(console\\.error\\s*\\(.*(Error|Exception).*\\))"
                ]
            },
            "HTTP Error Codes": {
                "Java": [
                    "(?i)(@ResponseStatus\\(\\s*HttpStatus\\.\\w+|new\\s+ResponseEntity<.*>\\(\\s*.*,\\s*HttpStatus\\.\\w+\\))",
                    "(?i)(HttpServletResponse\\.setStatus\\(\\s*\\d{3}\\s*\\))"
                ],
                "Python": [
                    "(?i)(return\\s+jsonify.*\\d{3}|abort\\(\\d{3}\\))",
                    "(?i)(response\\.status_code\\s*=\\s*\\d{3})"
                ],
                "JavaScript": [
                    "(?i)(res\\.status\\(\\d{3}\\)|response\\.status\\s*=\\s*\\d{3})"
                ]
            },
            "Client Error Tracking": {
                "Java": [
                    "(?i)(@PostMapping\\(['\"]/api/client-errors['\"]|@RequestMapping\\(['\"]/errors['\"],\\s*method\\s*=\\s*RequestMethod\\.POST\\))"
                ],
                "Python": [
                    "(?i)(@app\\.route\\(['\"]/api/client-errors['\"],\\s*methods=\\[['\"]POST['\"]\\]\\))"
                ],
                "JavaScript": [
                    "(?i)(fetch\\(['\"]/api/client-error-log['\"]|XMLHttpRequest\\.open\\(['\"]POST['\"],\\s*['\"]/errors['\"]\\))",
                    "(?i)(Sentry\\.init|trackJs\\.track)"
                ]
            },
            "Automated Tests": {
                "Java": [
                    "(?i)(@Test|@SpringBootTest|@ExtendWith|@RunWith|@Mock|@InjectMocks|@BeforeEach|@AfterEach)",
                    "(?i)import\\s+(org\\.junit|org\\.mockito|org\\.assertj)"
                ],
                "Python": [
                    "(?i)(def\\s+test_|@pytest|import\\s+pytest)",
                    "(?i)(unittest\\.TestCase|import\\s+unittest)"
                ],
                "JavaScript": [
                    "(?i)(describe\\(|it\\(|test\\(|import\\s+.*test)",
                    "(?i)(jest|mocha|chai|import\\s+.*test)"
                ]
            }
        }
        
        # Get patterns for the gate and detected languages
        gate_patterns = fallback_patterns.get(gate, {})
        all_patterns = []
        
        for language in languages:
            if language in gate_patterns:
                all_patterns.extend(gate_patterns[language])
        
        # Add generic patterns if no language-specific patterns found
        if not all_patterns:
            all_patterns = [
                f"(?i)({gate.lower().replace(' ', '|')})",
                f"(?i)({gate.lower().replace(' ', '_')})"
            ]
        
        return all_patterns[:5]  # Limit to 5 patterns
    
    def get_patterns_for_gate(self, gate_type: GateType, llm_response: Dict[str, Any]) -> List[str]:
        """Extract patterns for a specific gate from LLM response"""
        
        hard_gates_analysis = llm_response.get('hard_gates_analysis_short', {})
        gate_name = gate_type.value
        
        if gate_name in hard_gates_analysis:
            return hard_gates_analysis[gate_name].get('patterns', [])
        else:
            # Fallback to basic patterns
            return [f"(?i)({gate_name.lower().replace(' ', '|')})"]
    
    def is_llm_available(self) -> bool:
        """Check if LLM is available for pattern generation"""
        return self.llm_analyzer is not None
    
    def get_technology_summary(self, llm_response: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract technology summary from LLM response"""
        return llm_response.get('tech_summary', {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "build_tools": [],
            "containerization": [],
            "frontend": [],
            "testing": [],
            "code_quality": []
        }) 

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        lang_map = {
            '.java': 'java',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp'
        }
        return lang_map.get(ext, 'unknown')
    
    def _has_logging_statements(self, content: str, language: str) -> bool:
        """Check if file contains logging statements"""
        if language == 'java':
            patterns = [r'log\.', r'logger\.', r'Log\.', r'Logger\.', r'System\.out\.', r'System\.err\.']
        elif language == 'python':
            patterns = [r'logging\.', r'logger\.', r'print\s*\(', r'log\.']
        elif language == 'javascript':
            patterns = [r'console\.', r'logger\.', r'log\.']
        else:
            patterns = [r'log\.', r'logger\.', r'print\s*\(']
        
        import re
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _has_security_patterns(self, content: str, language: str) -> bool:
        """Check if file contains security-related patterns"""
        security_patterns = [
            r'authentication', r'auth', r'authorization', r'security',
            r'encrypt', r'decrypt', r'hash', r'password', r'token',
            r'jwt', r'oauth', r'saml', r'csrf', r'xss', r'sql\s*injection'
        ]
        
        import re
        for pattern in security_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _has_error_handling(self, content: str, language: str) -> bool:
        """Check if file contains error handling patterns"""
        if language == 'java':
            patterns = [r'try\s*\{', r'catch\s*\(', r'throws\s+', r'Exception']
        elif language == 'python':
            patterns = [r'try:', r'except:', r'raise\s+', r'Exception']
        elif language == 'javascript':
            patterns = [r'try\s*\{', r'catch\s*\(', r'throw\s+', r'Error']
        else:
            patterns = [r'try', r'catch', r'throw', r'Exception', r'Error']
        
        import re
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _detect_custom_libraries(self, target_path: Path, file_analyses: List[Dict]) -> Dict[str, Dict]:
        """Detect custom libraries and frameworks in the codebase"""
        custom_libraries = {}
        
        # ESER (Enterprise Security Event Reporting) detection
        eser_patterns = [
            r'ESER', r'EnterpriseSecurityEvent', r'SecurityEventReporting',
            r'security\.event', r'event\.reporting', r'audit\.log'
        ]
        
        # EBSSH (Enterprise Business Security Service Hub) detection
        ebssh_patterns = [
            r'EBSSH', r'EnterpriseBusinessSecurity', r'BusinessSecurityService',
            r'security\.service', r'business\.security', r'service\.hub'
        ]
        
        # Check all files for custom library patterns
        import re
        for analysis in file_analyses:
            if 'path' in analysis:
                file_path = target_path / analysis['path']
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Check for ESER patterns
                    for pattern in eser_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            custom_libraries['ESER'] = {
                                'name': 'ESER',
                                'description': 'Enterprise Security Event Reporting',
                                'patterns': eser_patterns,
                                'files': custom_libraries.get('ESER', {}).get('files', []) + [analysis['path']]
                            }
                            break
                    
                    # Check for EBSSH patterns
                    for pattern in ebssh_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            custom_libraries['EBSSH'] = {
                                'name': 'EBSSH',
                                'description': 'Enterprise Business Security Service Hub',
                                'patterns': ebssh_patterns,
                                'files': custom_libraries.get('EBSSH', {}).get('files', []) + [analysis['path']]
                            }
                            break
                            
                except Exception:
                    continue
        
        return custom_libraries
    
    def _detect_custom_libraries_comprehensive(self, target_path: Path, file_analyses: List[Dict], dependencies: List[str]) -> Dict[str, Dict]:
        """Detect custom libraries and frameworks in the codebase with comprehensive analysis"""
        custom_libraries = {}
        
        # ESER (Enterprise Security Event Reporting) detection
        eser_patterns = [
            r'ESER', r'EnterpriseSecurityEvent', r'SecurityEventReporting',
            r'security\.event', r'event\.reporting', r'audit\.log'
        ]
        
        # EBSSH (Enterprise Business Security Service Hub) detection
        ebssh_patterns = [
            r'EBSSH', r'EnterpriseBusinessSecurity', r'BusinessSecurityService',
            r'security\.service', r'business\.security', r'service\.hub'
        ]
        
        # Check all files for custom library patterns
        import re
        for analysis in file_analyses:
            if 'path' in analysis:
                file_path = target_path / analysis['path']
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Check for ESER patterns
                    for pattern in eser_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            custom_libraries['ESER'] = {
                                'name': 'ESER',
                                'description': 'Enterprise Security Event Reporting',
                                'patterns': eser_patterns,
                                'files': custom_libraries.get('ESER', {}).get('files', []) + [analysis['path']]
                            }
                            break
                    
                    # Check for EBSSH patterns
                    for pattern in ebssh_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            custom_libraries['EBSSH'] = {
                                'name': 'EBSSH',
                                'description': 'Enterprise Business Security Service Hub',
                                'patterns': ebssh_patterns,
                                'files': custom_libraries.get('EBSSH', {}).get('files', []) + [analysis['path']]
                            }
                            break
                            
                except Exception:
                    continue
        
        # Add dependencies to custom libraries
        for dep in dependencies:
            if dep not in custom_libraries:
                custom_libraries[dep] = {
                    'name': dep,
                    'description': f'Dependency: {dep}',
                    'patterns': [],
                    'files': []
                }
        
        return custom_libraries
    
    def _analyze_config_files(self, target_path: Path) -> Dict[str, Any]:
        """Analyze configuration files (e.g., pom.xml, application.properties)"""
        config_files = {}
        
        # Define common configuration file patterns
        config_patterns = {
            'Maven': ['pom.xml'],
            'Gradle': ['build.gradle', 'build.gradle.kts'],
            'npm': ['package.json'],
            'yarn': ['yarn.lock'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml'],
            'cargo': ['Cargo.toml'],
            'go.mod': ['go.mod'],
            'composer': ['composer.json'],
            'application.properties': ['application.properties', 'application.yml'],
            'application.yml': ['application.properties', 'application.yml'],
            'log4j.properties': ['log4j.properties', 'log4j2.xml'],
            'logback.xml': ['logback.xml', 'log4j2.xml'],
            'log4j2.xml': ['log4j.properties', 'logback.xml', 'log4j2.xml']
        }
        
        for tool, files in config_patterns.items():
            for file_name in files:
                if (target_path / file_name).exists():
                    config_files[tool] = {
                        'name': tool,
                        'description': f'Configuration file: {file_name}',
                        'files': [str(f.relative_to(target_path)) for f in target_path.rglob(file_name)]
                    }
                    break
        
        return config_files
    
    def _analyze_build_files(self, target_path: Path) -> Dict[str, Any]:
        """Analyze build files (e.g., build.gradle, package.json)"""
        build_files = {}
        
        # Define common build file patterns
        build_patterns = {
            'Maven': ['pom.xml'],
            'Gradle': ['build.gradle', 'build.gradle.kts'],
            'npm': ['package.json'],
            'yarn': ['yarn.lock'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml'],
            'cargo': ['Cargo.toml'],
            'go.mod': ['go.mod'],
            'composer': ['composer.json']
        }
        
        for tool, files in build_patterns.items():
            for file_name in files:
                if (target_path / file_name).exists():
                    build_files[tool] = {
                        'name': tool,
                        'description': f'Build file: {file_name}',
                        'files': [str(f.relative_to(target_path)) for f in target_path.rglob(file_name)]
                    }
                    break
        
        return build_files
    
    def _extract_dependencies(self, target_path: Path) -> List[str]:
        """Extract dependencies from common dependency files (e.g., package.json, Cargo.toml)"""
        dependencies = []
        
        # Define common dependency file patterns
        dependency_patterns = {
            'Maven': ['pom.xml'],
            'Gradle': ['build.gradle', 'build.gradle.kts'],
            'npm': ['package.json'],
            'yarn': ['yarn.lock'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml'],
            'cargo': ['Cargo.toml'],
            'go.mod': ['go.mod'],
            'composer': ['composer.json']
        }
        
        for tool, files in dependency_patterns.items():
            for file_name in files:
                if (target_path / file_name).exists():
                    try:
                        content = (target_path / file_name).read_text(encoding='utf-8', errors='ignore')
                        # Simple regex to find dependency names
                        import re
                        matches = re.findall(r'name\s*=\s*["\'](.*?)["\']', content)
                        if matches:
                            dependencies.extend(matches)
                        matches = re.findall(r'package\s*=\s*["\'](.*?)["\']', content)
                        if matches:
                            dependencies.extend(matches)
                        matches = re.findall(r'dependencies\s*=\s*\[.*?\]', content, re.DOTALL)
                        if matches:
                            # This is a more complex regex, might need a proper parser
                            # For now, we'll just capture the name if it's a simple package name
                            for match in re.findall(r'name\s*=\s*["\'](.*?)["\']', matches[0]):
                                if match and match not in dependencies:
                                    dependencies.append(match)
                    except Exception:
                        continue
        
        return list(set(dependencies))
    
    def _detect_frameworks(self, file_analyses: List[Dict]) -> List[str]:
        """Detect frameworks used in the codebase"""
        frameworks = []
        
        # Check for common frameworks
        framework_patterns = {
            'Spring': [r'@SpringBootApplication', r'@Controller', r'@Service', r'@Repository'],
            'Django': [r'from django', r'@django', r'Django'],
            'Flask': [r'from flask', r'@app\.route', r'Flask'],
            'Express': [r'express\.', r'app\.get', r'app\.post', r'Express'],
            'React': [r'import React', r'React\.', r'useState', r'useEffect'],
            'Angular': [r'@angular', r'@Component', r'@Injectable', r'Angular'],
            'Vue': [r'vue\.', r'@vue', r'Vue\.'],
            'Laravel': [r'Laravel', r'@laravel', r'Illuminate'],
            'ASP.NET': [r'@asp\.net', r'@Controller', r'@Service', r'ASP\.NET']
        }
        
        import re
        for framework, patterns in framework_patterns.items():
            for analysis in file_analyses:
                if 'path' in analysis and 'content' in analysis:
                    # Use content from analysis instead of reading file again
                    content = analysis['content']
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            frameworks.append(framework)
                            break
                elif 'path' in analysis:
                    # Fallback: read file content
                    try:
                        file_path = Path(analysis['path'])
                        if file_path.exists():
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    frameworks.append(framework)
                                    break
                    except Exception:
                        continue
        
        return list(set(frameworks))
    
    def _detect_build_tools(self, target_path: Path) -> List[str]:
        """Detect build tools and package managers"""
        build_tools = []
        
        build_files = {
            'Maven': ['pom.xml'],
            'Gradle': ['build.gradle', 'build.gradle.kts'],
            'npm': ['package.json'],
            'yarn': ['yarn.lock'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml'],
            'cargo': ['Cargo.toml'],
            'go.mod': ['go.mod'],
            'composer': ['composer.json']
        }
        
        for tool, files in build_files.items():
            for file_name in files:
                if (target_path / file_name).exists():
                    build_tools.append(tool)
                    break
        
        return build_tools
    
    def _detect_deployment_config(self, target_path: Path) -> Dict[str, Any]:
        """Detect deployment configuration"""
        deployment_config = {}
        
        # Check for common deployment files
        deployment_files = {
            'Docker': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
            'Kubernetes': ['k8s', 'kubernetes', '.yaml', '.yml'],
            'Terraform': ['.tf', 'terraform'],
            'Ansible': ['ansible', 'playbook'],
            'Jenkins': ['Jenkinsfile', 'jenkins'],
            'GitHub Actions': ['.github/workflows'],
            'GitLab CI': ['.gitlab-ci.yml'],
            'Heroku': ['Procfile', 'app.json'],
            'AWS': ['serverless.yml', 'sam.yaml', 'cloudformation']
        }
        
        for platform, patterns in deployment_files.items():
            for pattern in patterns:
                if list(target_path.rglob(pattern)):
                    deployment_config[platform] = True
                    break
        
        return deployment_config
    
    def _generate_comprehensive_llm_prompt(self, target_path: Path, file_analyses: List[Dict], 
                                         tech_context: Dict, custom_libraries: Dict, 
                                         config_files: Dict, build_files: Dict, dependencies: List[str],
                                         hard_gates: List[str]) -> str:
        """Generate comprehensive LLM prompt similar to processor.py"""
        
        # Build file structure summary
        file_structure = {}
        for analysis in file_analyses:
            path_parts = analysis['path'].split('/')
            current = file_structure
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[path_parts[-1]] = analysis
        
        # Build summary statistics
        total_files = len(file_analyses)
        total_lines = sum(f.get('lines', 0) for f in file_analyses)
        languages = tech_context.get('languages', [])
        frameworks = tech_context.get('frameworks', [])
        
        prompt = f"""You are an expert code analyzer specializing in hard gate validation patterns for enterprise security and compliance.

## CODEBASE ANALYSIS

### Technology Stack
- Languages: {', '.join(languages)}
- Total Files: {total_files}
- Total Lines: {total_lines}
- Frameworks: {', '.join(frameworks)}
- Build Tools: {', '.join(tech_context.get('build_tools', []))}
- Deployment: {', '.join(tech_context.get('deployment', {}).keys())}

### File Structure Summary
"""
        
        # Add file structure information
        for analysis in file_analyses[:20]:  # Limit to first 20 files for brevity
            prompt += f"- {analysis['path']} ({analysis['language']}, {analysis['lines']} lines)\n"
        
        if len(file_analyses) > 20:
            prompt += f"... and {len(file_analyses) - 20} more files\n"
        
        prompt += f"""
### Config Files Detected
"""
        if config_files:
            for tool_name, tool_info in config_files.items():
                prompt += f"""
**{tool_name}** ({tool_info.get('description', 'No description')})
- Files: {', '.join(tool_info.get('files', [])[:5])}...
"""
                
                # Add config file content for important files
                for file_path in tool_info.get('files', [])[:3]:  # Limit to first 3 files
                    try:
                        config_content = (target_path / file_path).read_text(encoding='utf-8', errors='ignore')
                        # Truncate content to avoid huge prompts
                        if len(config_content) > 500:
                            config_content = config_content[:500] + "..."
                        prompt += f"- Content of {file_path}:\n```\n{config_content}\n```\n"
                    except Exception:
                        continue
        else:
            prompt += "No config files detected.\n"

        prompt += f"""
### Build Files Detected
"""
        if build_files:
            for tool_name, tool_info in build_files.items():
                prompt += f"""
**{tool_name}** ({tool_info.get('description', 'No description')})
- Files: {', '.join(tool_info.get('files', [])[:5])}...
"""
                
                # Add build file content for important files
                for file_path in tool_info.get('files', [])[:3]:  # Limit to first 3 files
                    try:
                        build_content = (target_path / file_path).read_text(encoding='utf-8', errors='ignore')
                        # Truncate content to avoid huge prompts
                        if len(build_content) > 500:
                            build_content = build_content[:500] + "..."
                        prompt += f"- Content of {file_path}:\n```\n{build_content}\n```\n"
                    except Exception:
                        continue
        else:
            prompt += "No build files detected.\n"

        prompt += f"""
### Dependencies Detected
"""
        if dependencies:
            prompt += f"""
- Dependencies: {', '.join(dependencies[:20])}...
"""
        else:
            prompt += "No dependencies detected.\n"
        
        prompt += f"""
### Custom Libraries Detected
"""
        if custom_libraries:
            for lib_name, lib_info in custom_libraries.items():
                prompt += f"""
**{lib_name}** ({lib_info.get('description', 'No description')})
- Files: {', '.join(lib_info.get('files', [])[:5])}...
- Patterns: {', '.join(lib_info.get('patterns', [])[:3])}...
"""
        else:
            prompt += "No custom libraries detected.\n"
        
        prompt += f"""
### File Analysis Summary
- Files with logging: {len([f for f in file_analyses if f.get('has_logging', False)])}
- Files with security patterns: {len([f for f in file_analyses if f.get('has_security', False)])}
- Files with error handling: {len([f for f in file_analyses if f.get('has_errors', False)])}

## HARD GATES TO ANALYZE
{', '.join(hard_gates)}

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

## EXAMPLE FORMAT
```json
{{
  "structured_logs": {{
    "patterns": [
      {{
        "name": "Spring Boot Logging",
        "pattern": "log\\.(info|warn|error|debug)\\([^)]*\\)",
        "description": "Detects Spring Boot logging statements",
        "technology": ["java", "spring"],
        "custom_library": "ESER",
        "reasoning": "Spring Boot is detected in the codebase, so we need patterns for its logging framework"
      }}
    ]
  }}
}}
```

Generate patterns that are:
- **Specific** to the detected technology stack
- **Comprehensive** in coverage
- **Practical** for real-world codebases
- **Customizable** for different contexts
- **Secure** and compliance-focused
- **Based on actual files** and configurations found in this codebase

Focus on patterns that would catch actual violations in this type of codebase."""

        return prompt 

    def _parse_comprehensive_llm_response(self, llm_response: str, hard_gates: List[str]) -> Dict[str, Any]:
        """Parse comprehensive LLM response with detailed pattern information"""
        
        try:
            # Try to extract JSON from the response
            import re
            import json
            
            # Look for JSON blocks in the response
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            json_matches = re.findall(json_pattern, llm_response, re.DOTALL)
            
            if json_matches:
                # Use the first JSON block found
                json_str = json_matches[0]
                # Clean up common JSON issues
                json_str = self._clean_json_string(json_str)
                parsed = json.loads(json_str)
                print(f"✅ Parsed comprehensive LLM response with {len(parsed)} gate patterns")
                return parsed
            else:
                # Fallback: try to parse the entire response as JSON
                try:
                    cleaned_response = self._clean_json_string(llm_response)
                    parsed = json.loads(cleaned_response)
                    print(f"✅ Parsed LLM response as JSON with {len(parsed)} gate patterns")
                    return parsed
                except json.JSONDecodeError:
                    print("⚠️ Could not parse LLM response as JSON, using fallback parsing")
                    return self._parse_fallback_response(llm_response, hard_gates)
                    
        except Exception as e:
            print(f"❌ Comprehensive response parsing failed: {e}")
            return self._parse_fallback_response(llm_response, hard_gates)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean up common JSON formatting issues from LLM responses"""
        
        import re
        
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix common escape character issues
        json_str = json_str.replace('\\"', '"')
        json_str = json_str.replace('\\/', '/')
        json_str = json_str.replace('\\\\', '\\')
        
        # Fix unescaped quotes in strings
        json_str = re.sub(r'([^\\])"([^"]*?)([^\\])"', r'\1"\2\3"', json_str)
        
        # Remove any non-printable characters except newlines and tabs
        json_str = ''.join(char for char in json_str if char.isprintable() or char in '\n\t\r')
        
        # Fix common JSON syntax issues
        json_str = re.sub(r'(["\w])\s*:\s*(["\w])', r'\1": "\2', json_str)
        json_str = re.sub(r'(["\w])\s*,\s*(["\w])', r'\1", "\2', json_str)
        
        return json_str
    
    def _parse_fallback_response(self, llm_response: str, hard_gates: List[str]) -> Dict[str, Any]:
        """Fallback parsing for LLM response when JSON parsing fails"""
        
        parsed = {}
        
        # Extract patterns using regex for each gate
        for gate in hard_gates:
            patterns = []
            
            # Look for pattern-like content in the response
            import re
            
            # Common pattern indicators
            pattern_indicators = [
                r'pattern["\']?\s*:\s*["\']([^"\']+)["\']',
                r'regex["\']?\s*:\s*["\']([^"\']+)["\']',
                r'["\']([^"\']*log[^"\']*)["\']',
                r'["\']([^"\']*error[^"\']*)["\']',
                r'["\']([^"\']*security[^"\']*)["\']'
            ]
            
            for indicator in pattern_indicators:
                matches = re.findall(indicator, llm_response, re.IGNORECASE)
                for match in matches:
                    if match and len(match) > 5:  # Basic validation
                        patterns.append({
                            'name': f'Fallback Pattern {len(patterns) + 1}',
                            'pattern': match,
                            'description': f'Fallback pattern for {gate}',
                            'technology': ['generic'],
                            'custom_library': None
                        })
            
            if patterns:
                parsed[gate] = {'patterns': patterns}
        
        return parsed
    
    def _validate_and_clean_patterns(self, patterns: List[str]) -> List[str]:
        """Validate and clean regex patterns to prevent compilation errors"""
        
        import re
        valid_patterns = []
        
        for pattern in patterns:
            try:
                # Test compile the pattern
                re.compile(pattern, re.IGNORECASE)
                valid_patterns.append(pattern)
            except re.error as e:
                print(f"⚠️ Invalid regex pattern removed: {pattern[:50]}... (error: {e})")
                # Try to fix common issues
                try:
                    # Fix common escape issues
                    fixed_pattern = pattern.replace('\\', '\\\\')
                    re.compile(fixed_pattern, re.IGNORECASE)
                    valid_patterns.append(fixed_pattern)
                    print(f"✅ Fixed pattern: {fixed_pattern[:50]}...")
                except re.error:
                    print(f"❌ Could not fix pattern: {pattern[:50]}...")
                    continue
        
        print(f"🔍 [DEBUG] Validated {len(valid_patterns)} patterns out of {len(patterns)} total")
        return valid_patterns
    
    def _convert_to_gate_config(self, parsed_patterns: Dict[str, Any], hard_gates: List[str]) -> Dict[str, Any]:
        """Convert parsed patterns to gate configuration format with validation"""
        
        gate_config = {}
        
        for gate in hard_gates:
            if gate in parsed_patterns:
                gate_data = parsed_patterns[gate]
                
                # Extract patterns from the parsed data
                patterns = []
                if 'patterns' in gate_data:
                    for pattern_info in gate_data['patterns']:
                        if isinstance(pattern_info, dict):
                            # Extract the actual regex pattern
                            pattern = pattern_info.get('pattern', '')
                            if pattern:
                                patterns.append(pattern)
                        elif isinstance(pattern_info, str):
                            # Direct pattern string
                            patterns.append(pattern_info)
                
                if patterns:
                    # Validate and clean patterns
                    valid_patterns = self._validate_and_clean_patterns(patterns)
                    if valid_patterns:
                        gate_config[gate] = valid_patterns
                        print(f"✅ Converted {len(valid_patterns)} valid patterns for {gate}")
                    else:
                        print(f"⚠️ No valid patterns found for {gate}")
                else:
                    print(f"⚠️ No patterns found for {gate}")
            else:
                print(f"⚠️ No data found for gate: {gate}")
        
        return gate_config 
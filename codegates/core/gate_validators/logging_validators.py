"""
Logging Gate Validators - Validators for logging-related hard gates
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from ...models import Language, FileAnalysis
from .base import BaseGateValidator, GateValidationResult


class StructuredLogsValidator(BaseGateValidator):
    """Validates structured logging implementation"""
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate structured logging implementation"""
        
        # Detect technologies first
        detected_technologies = self._detect_technologies(target_path, file_analyses)
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for structured logging patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('structured_logging', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details
        details = self._generate_details(matches, detected_technologies)
        
        # Generate basic recommendations (will be enhanced by LLM if available)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            technologies=detected_technologies,
            matches=matches
        )
    
    def enhance_with_llm(self, result: GateValidationResult, llm_manager=None) -> GateValidationResult:
        """Enhance validation result with LLM-powered recommendations"""
        if llm_manager and llm_manager.is_enabled():
            try:
                llm_recommendations = self._generate_llm_recommendations(
                    gate_name="structured_logs",
                    matches=result.matches,
                    expected=result.expected,
                    detected_technologies=result.technologies,
                    llm_manager=llm_manager
                )
                if llm_recommendations:
                    result.recommendations = llm_recommendations
                    print(f"✅ LLM recommendations generated for structured_logs")
                else:
                    print(f"⚠️ LLM returned empty recommendations for structured_logs")
            except Exception as e:
                print(f"⚠️ LLM recommendation generation failed for structured_logs: {e}")
        
        return result
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get language-specific patterns for structured logging"""
        
        if self.language == Language.PYTHON:
            return {
                'structured_logging': [
                    r'logger\.info\s*\(\s*["\'][^"\']*["\']],?\s*extra\s*=',
                    r'logger\.error\s*\(\s*["\'][^"\']*["\']],?\s*extra\s*=',
                    r'logger\.warning\s*\(\s*["\'][^"\']*["\']],?\s*extra\s*=',
                    r'structlog\.get_logger\s*\(',
                    r'logging\.getLogger\s*\([^)]*\)\.info\s*\([^)]*\{',
                    r'json\.dumps\s*\([^)]*\)\s*.*logger',
                    r'logger\.\w+\s*\([^)]*json\.',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'structured_logging': [
                    r'logger\.info\s*\(\s*["\'][^"\']*\{\}[^"\']*["\']',
                    r'logger\.error\s*\(\s*["\'][^"\']*\{\}[^"\']*["\']',
                    r'Markers\.\w+\(',
                    r'MDC\.put\s*\(\s*["\']correlation',
                    r'MDC\.put\s*\(\s*["\']request',
                    r'UUID\.randomUUID\(\)',
                    r'ThreadLocal',
                    r'@Slf4j.*@JsonLog',
                    r'ObjectMapper\s*\(\)\.writeValueAsString',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'structured_logging': [
                    r'console\.log\s*\(\s*JSON\.stringify\s*\(',
                    r'logger\.info\s*\(\s*\{[^}]*\}',
                    r'winston\.createLogger\s*\(',
                    r'bunyan\.createLogger\s*\(',
                    r'pino\s*\(\s*\{',
                    r'log\.\w+\s*\(\s*\{[^}]*\}',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'structured_logging': [
                    r'_logger\.LogInformation\s*\([^)]*\{[^}]*\}',
                    r'_logger\.LogError\s*\([^)]*\{[^}]*\}',
                    r'ILogger<\w+>',
                    r'Serilog\.Log\.\w+\s*\([^)]*\{[^}]*\}',
                    r'LogContext\.PushProperty\s*\(',
                    r'Log\.ForContext\s*\(',
                ]
            }
        else:
            return {'structured_logging': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get configuration file patterns for structured logging"""
        
        if self.language == Language.PYTHON:
            return {
                'logging_config': [
                    'logging.conf', 'logging.yaml', 'logging.json',
                    'loguru.conf', 'structlog.conf'
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'logging_config': [
                    'logback.xml', 'logback-spring.xml', 'log4j2.xml',
                    'log4j.properties', 'logging.properties'
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'logging_config': [
                    'winston.config.js', 'logging.config.js',
                    'bunyan.config.json', 'pino.config.js'
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'logging_config': [
                    'appsettings.json', 'appsettings.*.json',
                    'serilog.json', 'nlog.config'
                ]
            }
        else:
            return {}
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected structured logging instances"""
        
        # Estimate based on file count and lines of code
        # Assume each file should have some logging, plus business logic logging
        
        base_expectation = max(file_count // 2, 1)  # At least half of files should log
        
        # Add expectation based on LOC (1 structured log per 100 LOC)
        loc_expectation = total_loc // 100
        
        # Service/controller files should have more logging
        service_files = len([f for f in lang_files 
                           if any(keyword in f.file_path.lower() 
                                 for keyword in ['service', 'controller', 'handler', 'manager'])])
        service_expectation = service_files * 3
        
        return base_expectation + loc_expectation + service_expectation
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess quality of structured logging implementation"""
        
        quality_scores = {}
        
        # Check for proper field usage
        json_structured = len([m for m in matches if 'json' in m['matched_text'].lower()])
        if json_structured > 0:
            quality_scores['json_format'] = min(json_structured * 5, 15)
        
        # Check for context fields (correlation IDs, user IDs, etc.)
        context_patterns = ['correlation', 'request_id', 'user_id', 'trace_id', 'session']
        context_matches = len([m for m in matches 
                             if any(pattern in m['matched_text'].lower() for pattern in context_patterns)])
        if context_matches > 0:
            quality_scores['context_fields'] = min(context_matches * 3, 10)
        
        # Check for consistent logging across files
        unique_files = len(set(m['file'] for m in matches))
        if unique_files >= 3:
            quality_scores['consistency'] = min(unique_files * 2, 10)
        
        # Check for proper log levels usage
        level_patterns = ['error', 'warn', 'info', 'debug']
        level_matches = len([m for m in matches 
                           if any(level in m['matched_text'].lower() for level in level_patterns)])
        if level_matches > 0:
            quality_scores['log_levels'] = min(level_matches * 2, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no structured logging found"""
        
        if self.language == Language.PYTHON:
            return [
                "Implement structured logging using Python's logging module with extra fields",
                "Consider using structlog for better structured logging support",
                "Add JSON formatting to your log handlers",
                "Include context fields like request_id, user_id in log messages"
            ]
        elif self.language == Language.JAVA:
            return [
                "Implement structured logging using SLF4J with Logback",
                "Use MDC (Mapped Diagnostic Context) for context fields",
                "Configure JSON formatting in logback.xml",
                "Add structured arguments to log statements"
            ]
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return [
                "Implement structured logging using Winston or Pino",
                "Use JSON format for log output",
                "Add context objects to log statements",
                "Configure proper log levels and transports"
            ]
        elif self.language == Language.CSHARP:
            return [
                "Implement structured logging using ILogger with Serilog",
                "Use structured logging templates with property placeholders",
                "Configure JSON formatting in appsettings.json",
                "Add context using LogContext.PushProperty"
            ]
        else:
            return ["Implement structured logging for your language stack"]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations when partial structured logging found"""
        
        return [
            "Extend structured logging to more files and functions",
            "Ensure consistent context fields across all log statements",
            "Add proper error context in exception handling",
            "Implement log correlation across service boundaries"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving structured logging quality"""
        
        return [
            "Standardize log message format and field names",
            "Add more context fields (user_id, request_id, correlation_id)",
            "Implement proper log levels (ERROR, WARN, INFO, DEBUG)",
            "Configure centralized log aggregation and parsing"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]], 
                         detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Generate detailed findings"""
        
        if not matches:
            return ["No structured logging patterns found"]
        
        details = []
        
        # Get unique files with structured logging
        try:
            files_with_structured = len(set(match.get('file', match.get('relative_path', 'unknown')) for match in matches))
        except Exception:
            files_with_structured = 0
        
        details.append(f"Found structured logging in {files_with_structured} files")
        
        # Show top files with most logging
        sorted_files = sorted(matches, key=lambda m: len(m['matched_text']), reverse=True)
        
        for match in sorted_files[:3]:
            file_path = match['file']
            details.append(f"  {file_path}: {len(match['matched_text'])} structured log statements")
        
        # Add technology detection details
        details.append("\n📊 Detected Technologies:")
        for tech, tech_files in detected_technologies.items():
            details.append(f"  {tech}: {len(tech_files)} files")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on structured logging findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()
    
    def generate_llm_recommendations(self, matches: List[Dict[str, Any]], expected: int, 
                                   detected_technologies: Dict[str, List[str]], 
                                   llm_manager=None) -> List[str]:
        """Generate LLM-powered recommendations for structured logging"""
        return self._generate_llm_recommendations(
            gate_name="structured_logs",
            matches=matches,
            expected=expected,
            detected_technologies=detected_technologies,
            llm_manager=llm_manager
        )


# Placeholder classes for other logging validators
class SecretLogsValidator(BaseGateValidator):
    """Validates that sensitive data is not logged"""
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate that no secrets are logged"""
        
        # Estimate expected count (should be 0 - no secrets should be logged)
        expected = 0
        
        # Search for potential secret logging patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('secret_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Quality score - lower is better for this gate
        quality_score = 100.0 if found == 0 else max(0, 100 - (found * 10))
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get patterns that might indicate secret logging"""
        
        # Comprehensive confidential data patterns
        confidential_patterns = [
            # Authentication & Authorization
            r'.*access_token([_\-]?[a-z0-9]*)?.*',
            r'.*auth_cooki([_\-]?[a-z0-9]*)?.*',
            r'.*auth_token([_\-]?[a-z0-9]*)?.*',
            r'.*bearer_token([_\-]?[a-z0-9]*)?.*',
            r'.*client_key([_\-]?[a-z0-9]*)?.*',
            r'.*client_secret([_\-]?[a-z0-9]*)?.*',
            r'.*consumer_key([_\-]?[a-z0-9]*)?.*',
            r'.*csrf([_\-]?[a-z0-9]*)?.*',
            r'.*csrf_token([_\-]?[a-z0-9]*)?.*',
            r'.*id_token([_\-]?[a-z0-9]*)?.*',
            r'.*jwt_secret([_\-]?[a-z0-9]*)?.*',
            r'.*login_token([_\-]?[a-z0-9]*)?.*',
            r'.*refresh_token([_\-]?[a-z0-9]*)?.*',
            r'.*security_token([_\-]?[a-z0-9]*)?.*',
            r'.*session_id([_\-]?[a-z0-9]*)?.*',
            r'.*session_token([_\-]?[a-z0-9]*)?.*',
            r'.*token([_\-]?[a-z0-9]*)?.*',
            r'.*xsrf([_\-]?[a-z0-9]*)?.*',
            r'.*xsrf_token([_\-]?[a-z0-9]*)?.*',
            
            # API Keys & Service Credentials
            r'.*api\-key([_\-]?[a-z0-9]*)?.*',
            r'.*api_key([_\-]?[a-z0-9]*)?.*',
            r'.*apikey([_\-]?[a-z0-9]*)?.*',
            r'.*appkey([_\-]?[a-z0-9]*)?.*',
            r'.*aws_access_key([_\-]?[a-z0-9]*)?.*',
            r'.*aws_secret_key([_\-]?[a-z0-9]*)?.*',
            r'.*aws_session_token([_\-]?[a-z0-9]*)?.*',
            r'.*azure_client_id([_\-]?[a-z0-9]*)?.*',
            r'.*azure_client_secret([_\-]?[a-z0-9]*)?.*',
            r'.*azure_key([_\-]?[a-z0-9]*)?.*',
            r'.*azure_tenant_id([_\-]?[a-z0-9]*)?.*',
            r'.*gcp_api_key([_\-]?[a-z0-9]*)?.*',
            
            # Passwords & Credentials
            r'.*cred([_\-]?[a-z0-9]*)?.*',
            r'.*credenti([_\-]?[a-z0-9]*)?.*',
            r'.*database_password([_\-]?[a-z0-9]*)?.*',
            r'.*db_password([_\-]?[a-z0-9]*)?.*',
            r'.*db_user([_\-]?[a-z0-9]*)?.*',
            r'.*ftp_password([_\-]?[a-z0-9]*)?.*',
            r'.*login_id([_\-]?[a-z0-9]*)?.*',
            r'.*loginpass([_\-]?[a-z0-9]*)?.*',
            r'.*loginpwd([_\-]?[a-z0-9]*)?.*',
            r'.*pass([_\-]?[a-z0-9]*)?.*',
            r'.*passwd([_\-]?[a-z0-9]*)?.*',
            r'.*password([_\-]?[a-z0-9]*)?.*',
            r'.*pwd([_\-]?[a-z0-9]*)?.*',
            r'.*redis_password([_\-]?[a-z0-9]*)?.*',
            r'.*smtp_password([_\-]?[a-z0-9]*)?.*',
            r'.*user([_\-]?[a-z0-9]*)?.*',
            r'.*user_id([_\-]?[a-z0-9]*)?.*',
            r'.*userid([_\-]?[a-z0-9]*)?.*',
            r'.*usernam([_\-]?[a-z0-9]*)?.*',
            r'.*userpass([_\-]?[a-z0-9]*)?.*',
            r'.*userpwd([_\-]?[a-z0-9]*)?.*',
            
            # Encryption Keys & Secrets
            r'.*aes_key([_\-]?[a-z0-9]*)?.*',
            r'.*decryption_key([_\-]?[a-z0-9]*)?.*',
            r'.*encryption_key([_\-]?[a-z0-9]*)?.*',
            r'.*gpg_key([_\-]?[a-z0-9]*)?.*',
            r'.*key_materi([_\-]?[a-z0-9]*)?.*',
            r'.*pem_key([_\-]?[a-z0-9]*)?.*',
            r'.*private_key([_\-]?[a-z0-9]*)?.*',
            r'.*private_secret([_\-]?[a-z0-9]*)?.*',
            r'.*public_key([_\-]?[a-z0-9]*)?.*',
            r'.*rsa_key([_\-]?[a-z0-9]*)?.*',
            r'.*secret([_\-]?[a-z0-9]*)?.*',
            r'.*secret_key([_\-]?[a-z0-9]*)?.*',
            r'.*secrettoken([_\-]?[a-z0-9]*)?.*',
            r'.*shared_secret([_\-]?[a-z0-9]*)?.*',
            r'.*signing_key([_\-]?[a-z0-9]*)?.*',
            r'.*ssh_key([_\-]?[a-z0-9]*)?.*',
            
            # Financial Information
            r'.*account_numb([_\-]?[a-z0-9]*)?.*',
            r'.*bank_account([_\-]?[a-z0-9]*)?.*',
            r'.*bic([_\-]?[a-z0-9]*)?.*',
            r'.*card_numb([_\-]?[a-z0-9]*)?.*',
            r'.*cc_number([_\-]?[a-z0-9]*)?.*',
            r'.*ccv([_\-]?[a-z0-9]*)?.*',
            r'.*credit_card([_\-]?[a-z0-9]*)?.*',
            r'.*cvc([_\-]?[a-z0-9]*)?.*',
            r'.*cvv([_\-]?[a-z0-9]*)?.*',
            r'.*exp_dat([_\-]?[a-z0-9]*)?.*',
            r'.*expiry_d([_\-]?[a-z0-9]*)?.*',
            r'.*iban([_\-]?[a-z0-9]*)?.*',
            r'.*pin([_\-]?[a-z0-9]*)?.*',
            r'.*routing_numb([_\-]?[a-z0-9]*)?.*',
            r'.*social_security_numb([_\-]?[a-z0-9]*)?.*',
            r'.*ssn([_\-]?[a-z0-9]*)?.*',
            r'.*swift_cod([_\-]?[a-z0-9]*)?.*',
            r'.*tax_id([_\-]?[a-z0-9]*)?.*',
            r'.*vat_id([_\-]?[a-z0-9]*)?.*',
            
            # Personal Information
            r'.*address([_\-]?[a-z0-9]*)?.*',
            r'.*birthdat([_\-]?[a-z0-9]*)?.*',
            r'.*countri([_\-]?[a-z0-9]*)?.*',
            r'.*dob([_\-]?[a-z0-9]*)?.*',
            r'.*email([_\-]?[a-z0-9]*)?.*',
            r'.*first_nam([_\-]?[a-z0-9]*)?.*',
            r'.*full_nam([_\-]?[a-z0-9]*)?.*',
            r'.*last_nam([_\-]?[a-z0-9]*)?.*',
            r'.*locat([_\-]?[a-z0-9]*)?.*',
            r'.*mobil([_\-]?[a-z0-9]*)?.*',
            r'.*name([_\-]?[a-z0-9]*)?.*',
            r'.*phone([_\-]?[a-z0-9]*)?.*',
            r'.*postal_cod([_\-]?[a-z0-9]*)?.*',
            r'.*zipcod([_\-]?[a-z0-9]*)?.*',
            
            # Connection Strings & URLs
            r'.*connection_str([_\-]?[a-z0-9]*)?.*',
            r'.*jdbc_url([_\-]?[a-z0-9]*)?.*',
            r'.*mongo_uri([_\-]?[a-z0-9]*)?.*',
            r'.*sql_connection_str([_\-]?[a-z0-9]*)?.*',
            
            # Cookies & Web Security
            r'.*cooki([_\-]?[a-z0-9]*)?.*',
            r'.*cookie_valu([_\-]?[a-z0-9]*)?.*',
        ]
        
        # Language-specific logging patterns combined with confidential data
        logging_patterns = []
        
        if self.language == Language.PYTHON:
            for pattern in confidential_patterns:
                # Python logging patterns
                logging_patterns.extend([
                    f'logger\\.\\w+\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'print\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'log\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'logging\\.\\w+\\s*\\([^)]*{pattern}[^)]*\\)',
                ])
        elif self.language == Language.JAVA:
            for pattern in confidential_patterns:
                # Java logging patterns
                logging_patterns.extend([
                    f'logger\\.\\w+\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'log\\.\\w+\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'System\\.out\\.print\\w*\\s*\\([^)]*{pattern}[^)]*\\)',
                ])
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            for pattern in confidential_patterns:
                # JavaScript/TypeScript logging patterns
                logging_patterns.extend([
                    f'console\\.\\w+\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'logger\\.\\w+\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'log\\s*\\([^)]*{pattern}[^)]*\\)',
                ])
        elif self.language == Language.CSHARP:
            for pattern in confidential_patterns:
                # C# logging patterns
                logging_patterns.extend([
                    f'_logger\\.Log\\w+\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'Console\\.Write\\w*\\s*\\([^)]*{pattern}[^)]*\\)',
                    f'Debug\\.Write\\w*\\s*\\([^)]*{pattern}[^)]*\\)',
                ])
        
        # Add basic patterns that might indicate secret logging
        basic_patterns = [
            r'log.*["\'].*password.*["\']',
            r'log.*["\'].*token.*["\']',
            r'log.*["\'].*secret.*["\']',
            r'log.*["\'].*key.*["\']',
            r'log.*["\'].*api_key.*["\']',
            r'log.*["\'].*auth.*["\']',
            r'print.*password',
            r'print.*token',
            r'console\.log.*password',
            r'console\.log.*token',
        ]
        
        return {'secret_patterns': logging_patterns + basic_patterns}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """No specific config patterns for secret detection"""
        return {}
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Expected count should always be 0 for secrets"""
        return 0
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Quality decreases with more secret logging found"""
        
        if not matches:
            return {}
        
        # Categorize violations by type
        violation_categories = {
            'authentication': ['token', 'auth', 'bearer', 'session', 'csrf', 'jwt'],
            'credentials': ['password', 'secret', 'key', 'credential', 'user', 'login'],
            'financial': ['card', 'account', 'bank', 'credit', 'cvv', 'pin', 'ssn'],
            'personal': ['name', 'email', 'phone', 'address', 'birth', 'dob'],
            'api_keys': ['api_key', 'apikey', 'aws_', 'azure_', 'gcp_'],
        }
        
        category_counts = {}
        for category, keywords in violation_categories.items():
            count = len([match for match in matches 
                        if any(keyword in match['matched_text'].lower() for keyword in keywords)])
            if count > 0:
                category_counts[category] = count
        
        # Calculate severity score (negative because violations are bad)
        total_violations = len(matches)
        severity_multiplier = {
            'authentication': -15,  # Most critical
            'credentials': -12,
            'api_keys': -10,
            'financial': -8,
            'personal': -5,
        }
        
        severity_score = 0
        for category, count in category_counts.items():
            severity_score += count * severity_multiplier.get(category, -3)
        
        return {
            'total_violations': total_violations,
            'severity_score': severity_score,
            'categories_affected': len(category_counts),
            **{f'{cat}_violations': count for cat, count in category_counts.items()}
        }
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no secret logging found (good!)"""
        return [
            "✅ Excellent! No confidential data logging patterns detected",
            "Continue to avoid logging sensitive data like passwords, tokens, API keys",
            "Implement log sanitization filters as a preventive measure",
            "Use structured logging to better control what gets logged",
            "Consider implementing automated secret scanning in CI/CD pipeline",
            "Train developers on secure logging practices"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Not applicable for this validator"""
        return []
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations when secrets are being logged"""
        return [
            "🚨 CRITICAL: Remove sensitive data from log statements immediately",
            "Implement log sanitization to filter out secrets automatically",
            "Use placeholders or masked values for sensitive fields (e.g., 'password: ***')",
            "Review all logging statements for potential data leaks",
            "Implement automated secret detection in code reviews",
            "Set up log monitoring to detect accidental secret exposure",
            "Create secure logging guidelines for the development team",
            "Consider using structured logging with explicit field filtering"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate details about secret logging violations"""
        
        if not matches:
            return ["✅ No confidential data logging patterns detected"]
        
        details = [f"🚨 Found {len(matches)} potential confidential data logging violations:"]
        
        # Categorize violations
        violation_categories = {
            'Authentication & Tokens': ['token', 'auth', 'bearer', 'session', 'csrf', 'jwt'],
            'Credentials & Passwords': ['password', 'secret', 'key', 'credential', 'user', 'login'],
            'Financial Information': ['card', 'account', 'bank', 'credit', 'cvv', 'pin', 'ssn', 'iban'],
            'Personal Information': ['name', 'email', 'phone', 'address', 'birth', 'dob'],
            'API Keys & Service Credentials': ['api_key', 'apikey', 'aws_', 'azure_', 'gcp_'],
            'Database & Connection Info': ['db_', 'database', 'connection', 'jdbc', 'mongo'],
        }
        
        category_counts = {}
        categorized_matches = {}
        
        for match in matches:
            match_text = match['matched_text'].lower()
            categorized = False
            
            for category, keywords in violation_categories.items():
                if any(keyword in match_text for keyword in keywords):
                    if category not in categorized_matches:
                        categorized_matches[category] = []
                        category_counts[category] = 0
                    categorized_matches[category].append(match)
                    category_counts[category] += 1
                    categorized = True
                    break
            
            if not categorized:
                if 'Other' not in categorized_matches:
                    categorized_matches['Other'] = []
                    category_counts['Other'] = 0
                categorized_matches['Other'].append(match)
                category_counts['Other'] += 1
        
        # Show breakdown by category
        details.append("\n📊 Violations by Category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            severity = "🔴 CRITICAL" if count >= 5 else "🟡 HIGH" if count >= 2 else "🟠 MEDIUM"
            details.append(f"  {severity} {category}: {count} violations")
        
        # Show specific examples (top 5 most critical)
        details.append("\n🔍 Examples of violations found:")
        shown_count = 0
        for category in ['Authentication & Tokens', 'Credentials & Passwords', 'API Keys & Service Credentials']:
            if category in categorized_matches and shown_count < 5:
                for match in categorized_matches[category][:min(2, 5-shown_count)]:
                    file_name = Path(match['file']).name
                    details.append(f"   {file_name}:{match.get('line_number', match.get('line', '?'))} - {match.get('matched_text', match.get('match', ''))[:60]}...")
                    shown_count += 1
                    if shown_count >= 5:
                        break
        
        if len(matches) > 5:
            details.append(f"  ... and {len(matches) - 5} more violations")
        
        details.append("\n⚠️  These violations pose serious security risks and should be addressed immediately!")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on violations found"""
        
        if not matches:
            return self._get_zero_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class AuditTrailValidator(BaseGateValidator):
    """Validates audit trail logging for critical operations"""
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate audit trail implementation"""
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for audit logging patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('audit_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get audit trail logging patterns"""
        
        if self.language == Language.PYTHON:
            return {
                'audit_patterns': [
                    r'audit_logger\.',
                    r'log.*audit',
                    r'logger\.info.*\b(create|update|delete|login|logout)\b',
                    r'logger\.info.*\b(admin|user|access)\b',
                    r'security_log\.',
                    r'access_log\.',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'audit_patterns': [
                    r'auditLogger\.',
                    r'log.*audit',
                    r'logger\.info.*\b(create|update|delete|login|logout)\b',
                    r'SecurityContextHolder\.',
                    r'@Audit',
                    r'AuditEvent\(',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'audit_patterns': [
                    r'auditLog\.',
                    r'log.*audit',
                    r'logger\.info.*\b(create|update|delete|login|logout)\b',
                    r'audit\.',
                    r'securityLog\.',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'audit_patterns': [
                    r'_auditLogger\.',
                    r'Log.*audit',
                    r'_logger\.LogInformation.*\b(Create|Update|Delete|Login|Logout)\b',
                    r'AuditLog\.',
                    r'\[Audit\]',
                ]
            }
        else:
            return {'audit_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get audit configuration patterns"""
        return {
            'audit_config': [
                'audit.conf', 'audit.json', 'audit.yaml',
                'security.conf', 'compliance.conf'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected audit logging instances"""
        
        # Look for files that likely contain business operations
        business_files = len([f for f in lang_files 
                            if any(keyword in f.file_path.lower() 
                                  for keyword in ['service', 'controller', 'handler', 'manager', 
                                                 'repository', 'dao', 'model', 'entity'])])
        
        # Estimate 2-3 audit points per business file
        return max(business_files * 2, 5)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess audit trail quality"""
        
        quality_scores = {}
        
        # Check for different types of audit events
        event_types = ['create', 'update', 'delete', 'login', 'logout', 'access']
        covered_events = len([match for match in matches 
                            if any(event in match['matched_text'].lower() for event in event_types)])
        
        if covered_events > 0:
            quality_scores['event_coverage'] = min(covered_events * 5, 20)
        
        # Check for user context in audit logs
        user_context = len([match for match in matches 
                          if any(ctx in match['matched_text'].lower() for ctx in ['user', 'admin', 'actor'])])
        
        if user_context > 0:
            quality_scores['user_context'] = min(user_context * 3, 15)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no audit trail found"""
        
        return [
            "Implement audit logging for critical business operations",
            "Log user actions like create, update, delete operations",
            "Include user context (user ID, role) in audit logs",
            "Log authentication events (login, logout, failed attempts)",
            "Consider using a dedicated audit logging framework"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial audit implementation"""
        
        return [
            "Extend audit logging to all critical business operations",
            "Ensure consistent audit log format across the application",
            "Add more context to audit logs (timestamps, user details, IP addresses)",
            "Implement audit log retention and archival policies"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving audit quality"""
        
        return [
            "Standardize audit log message format",
            "Include more context in audit events",
            "Implement audit log integrity protection",
            "Set up audit log monitoring and alerting"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate audit trail details"""
        
        if not matches:
            return ["No audit trail logging patterns found"]
        
        details = [f"Found {len(matches)} audit logging statements"]
        
        # Get unique files with audit logging
        try:
            files_with_audit = len(set(match.get('file', match.get('relative_path', 'unknown')) for match in matches))
        except Exception:
            files_with_audit = 0
        
        details.append(f"Audit logging present in {files_with_audit} files")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on audit findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class CorrelationIdValidator(BaseGateValidator):
    """Validates correlation ID implementation for request tracing"""
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate correlation ID implementation"""
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for correlation ID patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('correlation_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get correlation ID patterns"""
        
        if self.language == Language.PYTHON:
            return {
                'correlation_patterns': [
                    r'correlation_id',
                    r'request_id',
                    r'trace_id',
                    r'transaction_id',
                    r'x-correlation-id',
                    r'x-request-id',
                    r'uuid\.uuid4\(\)',
                    r'threading\.local\(\)',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'correlation_patterns': [
                    r'correlationId',
                    r'requestId',
                    r'traceId',
                    r'MDC\.put\s*\(\s*["\']correlation',
                    r'MDC\.put\s*\(\s*["\']request',
                    r'UUID\.randomUUID\(\)',
                    r'ThreadLocal',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'correlation_patterns': [
                    r'correlationId',
                    r'requestId',
                    r'traceId',
                    r'x-correlation-id',
                    r'x-request-id',
                    r'uuid\.v4\(\)',
                    r'crypto\.randomUUID\(\)',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'correlation_patterns': [
                    r'CorrelationId',
                    r'RequestId',
                    r'TraceId',
                    r'Guid\.NewGuid\(\)',
                    r'Activity\.Current',
                    r'HttpContext\.TraceIdentifier',
                ]
            }
        else:
            return {'correlation_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get correlation ID config patterns"""
        return {
            'correlation_config': [
                'correlation.conf', 'tracing.conf', 'middleware.conf'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected correlation ID usage"""
        
        # Look for web/API related files
        web_files = len([f for f in lang_files 
                        if any(keyword in f.file_path.lower() 
                              for keyword in ['controller', 'handler', 'router', 'middleware', 
                                             'api', 'web', 'http'])])
        
        # Expect correlation ID in most web-facing components
        return max(web_files, 3)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess correlation ID implementation quality"""
        
        quality_scores = {}
        
        # Check for proper ID generation
        generation_patterns = ['uuid', 'guid', 'random']
        id_generation = len([match for match in matches 
                           if any(pattern in match['matched_text'].lower() for pattern in generation_patterns)])
        
        if id_generation > 0:
            quality_scores['id_generation'] = min(id_generation * 5, 15)
        
        # Check for HTTP header usage
        header_patterns = ['x-correlation-id', 'x-request-id', 'header']
        header_usage = len([match for match in matches 
                          if any(pattern in match['matched_text'].lower() for pattern in header_patterns)])
        
        if header_usage > 0:
            quality_scores['header_usage'] = min(header_usage * 5, 15)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no correlation ID found"""
        
        return [
            "Implement correlation ID for request tracing",
            "Generate unique IDs for each request/transaction",
            "Pass correlation IDs through HTTP headers (X-Correlation-ID)",
            "Include correlation IDs in all log statements",
            "Propagate correlation IDs to downstream services"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial correlation ID implementation"""
        
        return [
            "Extend correlation ID usage to all request handlers",
            "Ensure correlation IDs are propagated to all services",
            "Include correlation IDs in error responses",
            "Implement correlation ID middleware for automatic handling"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving correlation ID quality"""
        
        return [
            "Standardize correlation ID format across services",
            "Implement automatic correlation ID injection",
            "Add correlation ID validation and error handling",
            "Set up distributed tracing with correlation IDs"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate correlation ID details"""
        
        if not matches:
            return ["No correlation ID patterns found"]
        
        details = [f"Found {len(matches)} correlation ID implementations"]
        
        # Check for different types
        types = []
        if any('correlation' in match['matched_text'].lower() for match in matches):
            types.append('correlation_id')
        if any('request' in match['matched_text'].lower() for match in matches):
            types.append('request_id')
        if any('trace' in match['matched_text'].lower() for match in matches):
            types.append('trace_id')
        
        if types:
            details.append(f"Types found: {', '.join(types)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on correlation ID findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class ApiLogsValidator(BaseGateValidator):
    """Validates API endpoint logging (entry/exit)"""
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate API logging implementation"""
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for API logging patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('api_log_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get API logging patterns"""
        
        if self.language == Language.PYTHON:
            return {
                'api_log_patterns': [
                    r'@app\.route.*\n.*logger\.',
                    r'@router\.\w+.*\n.*logger\.',
                    r'def \w+.*request.*:.*\n.*logger\.',
                    r'logger\.info.*request',
                    r'logger\.info.*response',
                    r'logger\.info.*endpoint',
                    r'access_log\.',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'api_log_patterns': [
                    r'@RequestMapping.*\n.*logger\.',
                    r'@GetMapping.*\n.*logger\.',
                    r'@PostMapping.*\n.*logger\.',
                    r'@RestController.*\n.*logger\.',
                    r'logger\.info.*request',
                    r'logger\.info.*response',
                    r'logger\.info.*endpoint',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'api_log_patterns': [
                    r'app\.\w+\s*\([^)]*,.*logger\.',
                    r'router\.\w+\s*\([^)]*,.*logger\.',
                    r'express\(\).*logger\.',
                    r'logger\.info.*request',
                    r'logger\.info.*response',
                    r'console\.log.*req\.',
                    r'console\.log.*res\.',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'api_log_patterns': [
                    r'\[HttpGet\].*\n.*_logger\.',
                    r'\[HttpPost\].*\n.*_logger\.',
                    r'\[Route.*\].*\n.*_logger\.',
                    r'_logger\.LogInformation.*request',
                    r'_logger\.LogInformation.*response',
                    r'_logger\.LogInformation.*endpoint',
                ]
            }
        else:
            return {'api_log_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get API logging config patterns"""
        return {
            'api_log_config': [
                'api.conf', 'access.conf', 'middleware.conf'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected API logging instances"""
        
        # Look for API/controller files
        api_files = len([f for f in lang_files 
                        if any(keyword in f.file_path.lower() 
                              for keyword in ['controller', 'handler', 'router', 'api', 
                                             'endpoint', 'resource'])])
        
        # Expect 2-3 log points per API file (entry/exit)
        return max(api_files * 2, 5)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess API logging quality"""
        
        quality_scores = {}
        
        # Check for request/response logging
        request_logs = len([match for match in matches 
                          if 'request' in match['matched_text'].lower()])
        response_logs = len([match for match in matches 
                           if 'response' in match['matched_text'].lower()])
        
        if request_logs > 0:
            quality_scores['request_logging'] = min(request_logs * 3, 10)
        if response_logs > 0:
            quality_scores['response_logging'] = min(response_logs * 3, 10)
        
        # Check for endpoint identification
        endpoint_logs = len([match for match in matches 
                           if any(pattern in match['matched_text'].lower() 
                                 for pattern in ['endpoint', 'route', 'path'])])
        
        if endpoint_logs > 0:
            quality_scores['endpoint_identification'] = min(endpoint_logs * 2, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no API logging found"""
        
        return [
            "Implement API endpoint logging for all routes",
            "Log incoming requests with method, path, and parameters",
            "Log outgoing responses with status codes and timing",
            "Include correlation IDs in API logs",
            "Consider using middleware for automatic API logging"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial API logging implementation"""
        
        return [
            "Extend API logging to all endpoints",
            "Ensure consistent log format across all API routes",
            "Add request/response timing information",
            "Include user context in API logs"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving API logging quality"""
        
        return [
            "Standardize API log message format",
            "Add more context to API logs (user agent, IP address)",
            "Implement API access pattern monitoring",
            "Set up API performance monitoring through logs"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate API logging details"""
        
        if not matches:
            return ["No API logging patterns found"]
        
        details = [f"Found {len(matches)} API logging statements"]
        
        # Check for different types
        request_count = len([m for m in matches if 'request' in m['matched_text'].lower()])
        response_count = len([m for m in matches if 'response' in m['matched_text'].lower()])
        
        if request_count > 0:
            details.append(f"Request logging: {request_count} instances")
        if response_count > 0:
            details.append(f"Response logging: {response_count} instances")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on API logging findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class BackgroundJobLogsValidator(BaseGateValidator):
    """Validates background job execution logging"""
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate background job logging implementation"""
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for background job logging patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('job_log_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get background job logging patterns"""
        
        if self.language == Language.PYTHON:
            return {
                'job_log_patterns': [
                    r'celery.*logger\.',
                    r'@task.*\n.*logger\.',
                    r'@periodic_task.*\n.*logger\.',
                    r'job_logger\.',
                    r'logger\.info.*job',
                    r'logger\.info.*task',
                    r'logger\.info.*worker',
                    r'scheduler\.',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'job_log_patterns': [
                    r'@Scheduled.*\n.*logger\.',
                    r'@Component.*Job.*\n.*logger\.',
                    r'Quartz.*logger\.',
                    r'logger\.info.*job',
                    r'logger\.info.*task',
                    r'logger\.info.*scheduled',
                    r'JobExecutionContext',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'job_log_patterns': [
                    r'cron\.',
                    r'setInterval.*logger\.',
                    r'setTimeout.*logger\.',
                    r'queue\.',
                    r'worker\.',
                    r'logger\.info.*job',
                    r'logger\.info.*task',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'job_log_patterns': [
                    r'IHostedService.*_logger\.',
                    r'BackgroundService.*_logger\.',
                    r'Timer.*_logger\.',
                    r'_logger\.LogInformation.*job',
                    r'_logger\.LogInformation.*task',
                    r'Hangfire\.',
                ]
            }
        else:
            return {'job_log_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get background job config patterns"""
        return {
            'job_config': [
                'celery.conf', 'scheduler.conf', 'jobs.conf',
                'cron.conf', 'worker.conf'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected background job logging instances"""
        
        # Look for job/task/worker related files
        job_files = len([f for f in lang_files 
                        if any(keyword in f.file_path.lower() 
                              for keyword in ['job', 'task', 'worker', 'scheduler', 
                                             'cron', 'background', 'queue'])])
        
        # If no obvious job files, estimate based on service files
        if job_files == 0:
            service_files = len([f for f in lang_files 
                               if any(keyword in f.file_path.lower() 
                                     for keyword in ['service', 'manager'])])
            job_files = max(service_files // 3, 1)  # Some services might have background jobs
        
        return max(job_files * 2, 3)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess background job logging quality"""
        
        quality_scores = {}
        
        # Check for job lifecycle logging
        lifecycle_patterns = ['start', 'complete', 'failed', 'retry']
        lifecycle_logs = len([match for match in matches 
                            if any(pattern in match['matched_text'].lower() for pattern in lifecycle_patterns)])
        
        if lifecycle_logs > 0:
            quality_scores['lifecycle_logging'] = min(lifecycle_logs * 3, 15)
        
        # Check for error handling
        error_patterns = ['error', 'exception', 'failed']
        error_logs = len([match for match in matches 
                        if any(pattern in match['matched_text'].lower() for pattern in error_patterns)])
        
        if error_logs > 0:
            quality_scores['error_handling'] = min(error_logs * 2, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no background job logging found"""
        
        return [
            "Implement logging for background job execution",
            "Log job start, completion, and failure events",
            "Include job parameters and execution time in logs",
            "Add error handling and retry logging for failed jobs",
            "Consider using structured logging for job metrics"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial background job logging implementation"""
        
        return [
            "Extend logging to all background jobs and tasks",
            "Ensure consistent job log format across all workers",
            "Add job performance metrics to logs",
            "Implement job failure alerting through logs"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving background job logging quality"""
        
        return [
            "Standardize job log message format",
            "Add more context to job logs (queue name, job ID)",
            "Implement job monitoring dashboards from logs",
            "Set up job performance alerting"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate background job logging details"""
        
        if not matches:
            return ["No background job logging patterns found"]
        
        details = [f"Found {len(matches)} background job logging statements"]
        
        # Check for different job types
        job_types = []
        if any('celery' in match['matched_text'].lower() for match in matches):
            job_types.append('Celery')
        if any('scheduled' in match['matched_text'].lower() for match in matches):
            job_types.append('Scheduled')
        if any('cron' in match['matched_text'].lower() for match in matches):
            job_types.append('Cron')
        if any('queue' in match['matched_text'].lower() for match in matches):
            job_types.append('Queue')
        
        if job_types:
            details.append(f"Job types found: {', '.join(job_types)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on background job logging findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations() 
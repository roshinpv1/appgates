"""
Logging Gate Validators - Validators for logging-related quality gates
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from ...models import Language, FileAnalysis, GateType
from .base import BaseGateValidator, GateValidationResult


class StructuredLogsValidator(BaseGateValidator):
    """Validates logging implementation - both structured and standard formats"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.STRUCTURED_LOGS):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def _perform_validation(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Perform the actual validation logic"""
        
        print(f"🔍 [DEBUG] _perform_validation called for {self.gate_type.value} ({self.language.value})")
        
        # Always get patterns at validation time
        print(f"🔍 [DEBUG] Calling _get_patterns...")
        patterns_dict = self._get_patterns(target_path)
        print(f"🔍 [DEBUG] Received patterns_dict: {list(patterns_dict.keys()) if patterns_dict else 'empty'}")
        
        all_patterns = []
        
        # Handle LLM-generated patterns
        if 'llm_generated' in patterns_dict:
            all_patterns.extend(patterns_dict['llm_generated'])
            print(f"🎯 [LLM] Using {len(patterns_dict['llm_generated'])} LLM-generated patterns")
        
        # Handle traditional pattern structure
        for category, category_patterns in patterns_dict.items():
            if category == 'llm_generated':
                continue
            if isinstance(category_patterns, list):
                all_patterns.extend(category_patterns)
                print(f"🔍 [DEBUG] Added {len(category_patterns)} patterns from category: {category}")
        
        # Fallback to hardcoded patterns if no patterns available
        if not all_patterns:
            hardcoded_patterns = self._get_hardcoded_patterns()
            all_patterns = hardcoded_patterns.get('logging_patterns', [])
            print(f"📋 [Hardcoded] Using {len(all_patterns)} hardcoded patterns as fallback")
        
        print(f"🔍 [DEBUG] Total patterns to search: {len(all_patterns)}")
        
        # Search for patterns
        matches = self._search_files_for_patterns(
            target_path, 
            self._get_file_extensions(), 
            all_patterns
        )
        
        # Log pattern match results
        self._log_pattern_match(matches)
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Filter out invalid matches
        actual_matches = self._filter_actual_matches(matches)
        
        # Log filtered results
        self._log_pattern_match(actual_matches, "After filtering")
        
        # Estimate expected count based on non-test files
        non_test_files = [f for f in file_analyses if not self._is_test_file(f.file_path)]
        expected = self._estimate_expected_count(non_test_files)
        
        # Calculate quality score based on actual matches
        quality_score = self._calculate_quality_score(actual_matches, expected)
        
        # Generate details and recommendations based on actual matches
        details = self._generate_details(actual_matches)
        recommendations = self._generate_recommendations_from_matches(actual_matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=len(actual_matches),
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=actual_matches  # Store actual matches
        )
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get hardcoded language-specific patterns for both structured and standard logging"""
        
        if self.language == Language.PYTHON:
            return {
                'logging_patterns': [
                    # Standard logging patterns
                    r'logging\.(info|debug|error|warning|critical)\s*\(',
                    r'logger\.(info|debug|error|warning|critical)\s*\(',
                    r'log\.(info|debug|error|warning|critical)\s*\(',
                    r'print\s*\([^)]*\)',  # Basic print statements
                    
                    # Framework-specific logging
                    r'app\.logger\.',
                    r'flask\.current_app\.logger\.',
                    r'django\.core\.logging\.',
                    
                    # Structured logging patterns
                    r'logger\.(info|debug|error|warning|critical)\s*\(\s*["\'][^"\']*["\']],?\s*extra\s*=',
                    r'structlog\.get_logger\s*\(',
                    r'logging\.getLogger\s*\([^)]*\)\.info\s*\([^)]*\{',
                    r'json\.dumps\s*\([^)]*\)\s*.*logger',
                    r'logger\.\w+\s*\([^)]*json\.',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'logging_patterns': [
                    # Standard logging patterns
                    r'System\.(out|err)\.print(ln)?\s*\(',
                    r'logger\.(info|debug|error|warn|trace)\s*\(',
                    r'log\.(info|debug|error|warn|trace)\s*\(',
                    r'Logger\.(getLogger|getAnonymousLogger)\s*\(',
                    
                    # Framework logging
                    r'LoggerFactory\.getLogger\s*\(',
                    r'@Slf4j',
                    r'Commons.*Log',
                    
                    # Structured logging patterns
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
                'logging_patterns': [
                    # Standard logging patterns
                    r'console\.(log|info|debug|error|warn)\s*\(',
                    r'logger\.(info|debug|error|warn)\s*\(',
                    r'log\.(info|debug|error|warn)\s*\(',
                    
                    # Framework logging
                    r'winston\.',
                    r'bunyan\.',
                    r'pino\(',
                    r'log4js\.',
                    
                    # Structured logging patterns
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
                'logging_patterns': [
                    # Standard logging patterns
                    r'Console\.(WriteLine|Write)\s*\(',
                    r'Debug\.(WriteLine|Write)\s*\(',
                    r'_logger\.(LogInformation|LogDebug|LogError|LogWarning|LogCritical)\s*\(',
                    r'ILogger.*Log\w+\s*\(',
                    
                    # Framework logging
                    r'Log\.(Information|Debug|Error|Warning|Critical)\s*\(',
                    r'Serilog\.',
                    r'NLog\.',
                    
                    # Structured logging patterns
                    r'_logger\.LogInformation\s*\([^)]*\{[^}]*\}',
                    r'_logger\.LogError\s*\([^)]*\{[^}]*\}',
                    r'ILogger<\w+>',
                    r'Serilog\.Log\.\w+\s*\([^)]*\{[^}]*\}',
                    r'LogContext\.PushProperty\s*\(',
                    r'Log\.ForContext\s*\(',
                ]
            }
        else:
            return {'logging_patterns': []}
    
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
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected structured logging instances"""
        
        # Estimate based on file count and lines of code
        # Assume each file should have some logging, plus business logic logging
        
        base_expectation = max(len(lang_files) // 2, 1)  # At least half of files should log
        
        # Add expectation based on LOC (1 structured log per 100 LOC)
        loc_expectation = sum(f.lines_of_code for f in lang_files) // 100
        
        # Service/controller files should have more logging
        service_files = len([f for f in lang_files 
                           if any(keyword in f.file_path.lower() 
                                 for keyword in ['service', 'controller', 'handler', 'manager'])])
        service_expectation = service_files * 3
        
        return max(base_expectation + loc_expectation + service_expectation, 5)  # At least 5 logs minimum
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess quality of structured logging implementation"""
        
        quality_scores = {}
        
        # Check for proper field usage
        json_structured = len([m for m in matches if 'json' in m.get('matched_text', m.get('match', '')).lower()])
        if json_structured > 0:
            quality_scores['json_format'] = min(json_structured * 5, 15)
        
        # Check for context fields (correlation IDs, user IDs, etc.)
        context_patterns = ['correlation', 'request_id', 'user_id', 'trace_id', 'session']
        context_matches = len([m for m in matches 
                             if any(pattern in m.get('matched_text', m.get('match', '')).lower() for pattern in context_patterns)])
        if context_matches > 0:
            quality_scores['context_fields'] = min(context_matches * 3, 10)
        
        # Check for consistent logging across files
        unique_files = len(set(m.get('file_path', m.get('file', 'unknown')) for m in matches))
        if unique_files >= 3:
            quality_scores['consistency'] = min(unique_files * 2, 10)
        
        # Check for proper log levels usage
        level_patterns = ['error', 'warn', 'info', 'debug']
        level_matches = len([m for m in matches 
                           if any(level in m.get('matched_text', m.get('match', '')).lower() for level in level_patterns)])
        if level_matches > 0:
            quality_scores['log_levels'] = min(level_matches * 2, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no logging found"""
        return [
            "Implement logging throughout your codebase",
            "Use either standard logging or structured logging with consistent formats",
            "Configure proper log handlers and formatters",
            "Include context fields in log messages",
            "Consider using structured logging for better searchability"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial logging implementation"""
        return [
            "Extend logging coverage to more components",
            "Ensure consistent logging patterns across all modules",
            "Add more context to log messages",
            "Consider using structured logging where appropriate",
            "Configure centralized log aggregation"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving logging quality"""
        return [
            "Standardize log message formats across the application",
            "Add more contextual information to log messages",
            "Consider using structured logging for complex data",
            "Set up log aggregation and monitoring",
            "Review and optimize log levels for production"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate structured logging details"""
        
        if not matches:
            return super()._generate_details([])
        
        # Add to details set for uniqueness
        self._details_set.add(f"Found {len(matches)} logging implementations")
        
        # Group by file
        files_with_logs = len(set(match.get('file_path', match.get('file', 'unknown')) for match in matches))
        self._details_set.add(f"Logging present in {files_with_logs} files")
        
        # Check for different types of logging
        types = set()  # Use set for unique types
        if any('structured' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Structured logging')
        if any('json' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('JSON logging')
        if any('logger' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Standard logging')
        
        if types:
            self._details_set.add(f"Logging types: {', '.join(sorted(types))}")
        
        # Add detailed match information using the standardized method
        if matches:
            self._details_set.add("")  # Add spacing
            
            # Define categories for logging
            category_keywords = {
                'Structured Logging': ['structured', 'json', 'extra', 'context'],
                'Standard Logging': ['logger', 'logging', 'log.', 'console'],
                'Framework Logging': ['winston', 'bunyan', 'pino', 'serilog', 'nlog'],
                'Debug Logging': ['debug', 'trace', 'verbose'],
                'Error Logging': ['error', 'exception', 'critical'],
                'Info Logging': ['info', 'information', 'notice']
            }
            
            detailed_matches = self._generate_detailed_match_info(
                matches, 
                max_items=15,
                show_categories=True,
                category_keywords=category_keywords
            )
            self._details_set.update(detailed_matches)
        
        return list(self._details_set)
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on logging findings"""
        
        if len(matches) == 0:
            recommendations = self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            recommendations = self._get_partial_implementation_recommendations()
        else:
            recommendations = self._get_quality_improvement_recommendations()
    
        # Add recommendations to set for uniqueness
        self._recommendations_set.update(recommendations)
        return list(self._recommendations_set)


class SecretLogsValidator(BaseGateValidator):
    """Validates that sensitive data is not logged"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.AVOID_LOGGING_SECRETS):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def _perform_validation(self, target_path: Path, 
                          file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Perform the actual validation logic"""
        return self.validate(target_path, file_analyses)
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate that secrets are not logged"""
        
        # For secrets, we want to find 0 instances (violations)
        expected = 0
        
        # Search for secret logging patterns
        extensions = self._get_file_extensions()
        
        # Get patterns dynamically
        patterns_dict = self._get_patterns(target_path)
        all_patterns = []
        
        # Handle LLM-generated patterns
        if 'llm_generated' in patterns_dict:
            all_patterns.extend(patterns_dict['llm_generated'])
        
        # Handle traditional pattern structure
        for category, category_patterns in patterns_dict.items():
            if category == 'llm_generated':
                continue
            if isinstance(category_patterns, list):
                all_patterns.extend(category_patterns)
        
        # Fallback to hardcoded patterns if no patterns available
        if not all_patterns:
            hardcoded_patterns = self._get_hardcoded_patterns()
            all_patterns = hardcoded_patterns.get('secret_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, all_patterns)
        
        # Log initial pattern matches
        self._log_pattern_match(matches)
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Filter out invalid matches
        actual_matches = self._filter_actual_matches(matches)
        
        # Log filtered results
        self._log_pattern_match(actual_matches, "After filtering")
        
        found = len(actual_matches)
        
        # For secrets, quality score is inverted (fewer findings = better)
        quality_score = max(0, 100 - (found * 10))  # Penalize each secret found
        
        # Generate details and recommendations based on actual matches
        details = self._generate_details(actual_matches)
        recommendations = self._generate_recommendations_from_matches(actual_matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=actual_matches  # Store actual matches
        )
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get hardcoded patterns that might indicate secret logging as fallback"""
        
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
        
        # Create language-specific logging patterns
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
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
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
                        if any(keyword in match.get('matched_text', match.get('match', '')).lower() for keyword in keywords)])
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
        """Generate secret logging details"""
        
        if not matches:
            return super()._generate_details([])
        
        # Add to details set for uniqueness
        self._details_set.add(f"Found {len(matches)} potential secret logging instances")
            
        # Group by file
        files_with_secrets = len(set(match.get('file_path', match.get('file', 'unknown')) for match in matches))
        self._details_set.add(f"Potential secrets found in {files_with_secrets} files")
        
        # Check for different types of secrets
        types = set()  # Use set for unique types
        if any('password' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Passwords')
        if any('token' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Tokens')
        if any('key' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Keys')
        if any('secret' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Secrets')
        
        if types:
            self._details_set.add(f"Secret types detected: {', '.join(sorted(types))}")
        
        # Add detailed match information using the standardized method
        if matches:
            self._details_set.add("")  # Add spacing
            
            # Define categories for secrets
            category_keywords = {
                'Passwords': ['password', 'passwd', 'pwd'],
                'Tokens': ['token', 'jwt', 'bearer'],
                'Keys': ['key', 'apikey', 'secret_key'],
                'Credentials': ['credential', 'auth', 'login'],
                'Certificates': ['cert', 'certificate', 'pem'],
                'Other Secrets': ['secret', 'private', 'sensitive']
            }
            
            detailed_matches = self._generate_detailed_match_info(
                matches, 
                max_items=15,
                show_categories=True,
                category_keywords=category_keywords
            )
            self._details_set.update(detailed_matches)
        
        return list(self._details_set)
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on secret findings"""
        
        if len(matches) == 0:
            recommendations = self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            recommendations = self._get_partial_implementation_recommendations()
        else:
            recommendations = self._get_quality_improvement_recommendations()
            
        # Add recommendations to set for uniqueness
        self._recommendations_set.update(recommendations)
        return list(self._recommendations_set)


class AuditTrailValidator(BaseGateValidator):
    """Validates audit trail logging for critical operations"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.AUDIT_TRAIL):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def _perform_validation(self, target_path: Path, 
                          file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Perform the actual validation logic"""
        return self.validate(target_path, file_analyses)
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate audit trail implementation"""
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for audit logging patterns
        extensions = self._get_file_extensions()
        # Get patterns dynamically
        patterns_dict = self._get_patterns(target_path)
        patterns = []
        
        # Handle LLM-generated patterns
        if 'llm_generated' in patterns_dict:
            patterns.extend(patterns_dict['llm_generated'])
        
        # Handle traditional pattern structure
        for category, category_patterns in patterns_dict.items():
            if category == 'llm_generated':
                continue
            if isinstance(category_patterns, list):
                patterns.extend(category_patterns)
        
        # Fallback to hardcoded patterns if no patterns available
        if not patterns:
            hardcoded_patterns = self._get_hardcoded_patterns()
            patterns = hardcoded_patterns.get('audit_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        
        # Log initial pattern matches
        self._log_pattern_match(matches)
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Filter out invalid matches
        actual_matches = self._filter_actual_matches(matches)
        
        # Log filtered results
        self._log_pattern_match(actual_matches, "After filtering")
        
        found = len(actual_matches)
        
        # Calculate quality score based on actual matches
        quality_score = self._calculate_quality_score(actual_matches, expected)
        
        # Generate details and recommendations based on actual matches
        details = self._generate_details(actual_matches)
        recommendations = self._generate_recommendations_from_matches(actual_matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=actual_matches  # Store actual matches
        )
    
    def enhance_with_llm(self, result: GateValidationResult, llm_manager=None) -> GateValidationResult:
        """Enhance validation result with LLM-powered recommendations"""
        if llm_manager and llm_manager.is_enabled():
            try:
                llm_recommendations = self._generate_llm_recommendations(
                    gate_name="audit_trail",
                    matches=result.matches,
                    expected=result.expected,
                    detected_technologies=result.technologies,
                    llm_manager=llm_manager
                )
                if llm_recommendations:
                    result.recommendations = llm_recommendations
                    print(f"✅ LLM recommendations generated for audit_trail")
                else:
                    print(f"⚠️ LLM returned empty recommendations for audit_trail")
            except Exception as e:
                print(f"⚠️ LLM recommendation generation failed for audit_trail: {e}")
        
        return result
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get hardcoded audit trail logging patterns as fallback"""
        
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
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """DEPRECATED: Use _get_hardcoded_patterns instead"""
        return self._get_hardcoded_patterns()
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get audit configuration patterns"""
        return {
            'audit_config': [
                'audit.conf', 'audit.json', 'audit.yaml',
                'security.conf', 'compliance.conf'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected audit logging instances"""
        
        # Look for files that likely contain business operations
        business_files = len([f for f in lang_files ])
        
        # Estimate 2-3 audit points per business file
        return max(business_files * 2, 5)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess audit trail quality"""
        
        quality_scores = {}
        
        # Check for different types of audit events
        event_types = ['create', 'update', 'delete', 'login', 'logout', 'access']
        covered_events = len([match for match in matches 
                            if any(event in match.get('matched_text', match.get('match', '')).lower() for event in event_types)])
        
        if covered_events > 0:
            quality_scores['event_coverage'] = min(covered_events * 5, 20)
        
        # Check for user context in audit logs
        user_context = len([match for match in matches 
                          if any(ctx in match.get('matched_text', match.get('match', '')).lower() for ctx in ['user', 'admin', 'actor'])])
        
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
            return super()._generate_details([])
        
        # Add to details set for uniqueness
        self._details_set.add(f"Found {len(matches)} audit trail implementations")
        
        # Group by file
        files_with_audit = len(set(match.get('file_path', match.get('file', 'unknown')) for match in matches))
        self._details_set.add(f"Audit logging present in {files_with_audit} files")
        
        # Check for different types of audit events
        types = set()  # Use set for unique types
        if any('create' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Create events')
        if any('update' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Update events')
        if any('delete' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Delete events')
        if any('access' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Access events')
        
        if types:
            self._details_set.add(f"Audit event types: {', '.join(sorted(types))}")
        
        # Add detailed match information using the standardized method
        if matches:
            self._details_set.add("")  # Add spacing
            
            # Define categories for audit events
            category_keywords = {
                'Data Changes': ['create', 'update', 'delete', 'modify'],
                'Access Events': ['access', 'view', 'read', 'download'],
                'Security Events': ['login', 'logout', 'auth', 'permission'],
                'System Events': ['startup', 'shutdown', 'config', 'deploy'],
                'User Actions': ['user', 'account', 'profile', 'settings']
            }
            
            detailed_matches = self._generate_detailed_match_info(
                matches, 
                max_items=15,
                show_categories=True,
                category_keywords=category_keywords
            )
            self._details_set.update(detailed_matches)
        
        return list(self._details_set)
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on audit findings"""
        
        if len(matches) == 0:
            recommendations = self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            recommendations = self._get_partial_implementation_recommendations()
        else:
            recommendations = self._get_quality_improvement_recommendations()
            
        # Add recommendations to set for uniqueness
        self._recommendations_set.update(recommendations)
        return list(self._recommendations_set)


class CorrelationIdValidator(BaseGateValidator):
    """Validates correlation ID implementation for request tracing"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.CORRELATION_ID):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def _perform_validation(self, target_path: Path, 
                          file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Perform the actual validation logic"""
        return self.validate(target_path, file_analyses)
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate correlation ID implementation"""
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for correlation ID patterns
        extensions = self._get_file_extensions()
        # Get patterns dynamically
        patterns_dict = self._get_patterns(target_path)
        patterns = []
        
        # Handle LLM-generated patterns
        if 'llm_generated' in patterns_dict:
            patterns.extend(patterns_dict['llm_generated'])
        
        # Handle traditional pattern structure
        for category, category_patterns in patterns_dict.items():
            if category == 'llm_generated':
                continue
            if isinstance(category_patterns, list):
                patterns.extend(category_patterns)
        
        # Fallback to hardcoded patterns if no patterns available
        if not patterns:
            hardcoded_patterns = self._get_hardcoded_patterns()
            patterns = hardcoded_patterns.get('correlation_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        
        # Log initial pattern matches
        self._log_pattern_match(matches)
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Filter out invalid matches
        actual_matches = self._filter_actual_matches(matches)
        
        # Log filtered results
        self._log_pattern_match(actual_matches, "After filtering")
        
        found = len(actual_matches)
        
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
    
    def enhance_with_llm(self, result: GateValidationResult, llm_manager=None) -> GateValidationResult:
        """Enhance validation result with LLM-powered recommendations"""
        if llm_manager and llm_manager.is_enabled():
            try:
                llm_recommendations = self._generate_llm_recommendations(
                    gate_name="correlation_id",
                    matches=result.matches,
                    expected=result.expected,
                    detected_technologies=result.technologies,
                    llm_manager=llm_manager
                )
                if llm_recommendations:
                    result.recommendations = llm_recommendations
                    print(f"✅ LLM recommendations generated for correlation_id")
                else:
                    print(f"⚠️ LLM returned empty recommendations for correlation_id")
            except Exception as e:
                print(f"⚠️ LLM recommendation generation failed for correlation_id: {e}")
        
        return result
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get hardcoded correlation ID patterns as fallback"""
        
        if self.language == Language.PYTHON:
            return {
                'correlation_patterns': [
                    r'correlation_id',
                    r'request_id',
                    r'trace_id',
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
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'correlation_patterns': [
                    r'CorrelationId',
                    r'RequestId',
                    r'TraceId',
                ]
            }
        else:
            return {'correlation_patterns': []}
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """DEPRECATED: Use _get_hardcoded_patterns instead"""
        return self._get_hardcoded_patterns()
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get correlation ID config patterns"""
        return {
            'correlation_config': [
                'correlation.conf', 'tracing.conf', 'middleware.conf'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected correlation ID instances"""
        
        # Look for files that likely need correlation IDs
        service_files = len([f for f in lang_files 
                           if any(keyword in f.file_path.lower() 
                                 for keyword in ['service', 'controller', 'handler', 'manager', 
                                               'client', 'api', 'http', 'rest'])])
        
        # Estimate correlation ID points needed:
        # - At least 1 correlation ID per service file
        # - Additional points based on LOC (1 per 200 LOC in service files)
        base_points = service_files
        loc_based_points = sum(f.lines_of_code for f in lang_files) // 200
        
        return max(base_points + loc_based_points, 3)  # At least 3 correlation ID points minimum
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess correlation ID implementation quality"""
        
        quality_scores = {}
        
        # Check for proper ID generation
        generation_patterns = ['uuid', 'guid', 'random']
        id_generation = len([match for match in matches 
                           if any(pattern in match.get('matched_text', match.get('match', '')).lower() for pattern in generation_patterns)])
        
        if id_generation > 0:
            quality_scores['id_generation'] = min(id_generation * 5, 15)
        
        # Check for HTTP header usage
        header_patterns = ['x-correlation-id', 'x-request-id', 'header']
        header_usage = len([match for match in matches 
                          if any(pattern in match.get('matched_text', match.get('match', '')).lower() for pattern in header_patterns)])
        
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
            return super()._generate_details([])
        
        # Add to details set for uniqueness
        self._details_set.add(f"Found {len(matches)} correlation ID implementations")
            
        # Group by file
        files_with_correlation = len(set(match.get('file_path', match.get('file', 'unknown')) for match in matches))
        self._details_set.add(f"Correlation ID handling present in {files_with_correlation} files")
        
        # Check for different types of correlation handling
        types = set()  # Use set for unique types
        if any('header' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('HTTP header propagation')
        if any('context' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Context propagation')
        if any('generate' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('ID generation')
        
        if types:
            self._details_set.add(f"Correlation handling types: {', '.join(sorted(types))}")
        
        # Add detailed match information using the standardized method
        if matches:
            self._details_set.add("")  # Add spacing
            
            # Define categories for correlation ID handling
            category_keywords = {
                'ID Generation': ['generate', 'create', 'new', 'uuid'],
                'HTTP Headers': ['header', 'x-correlation-id', 'x-request-id'],
                'Context Handling': ['context', 'scope', 'async'],
                'Logging Integration': ['logger', 'log', 'trace'],
                'Error Handling': ['error', 'exception', 'catch']
            }
            
            detailed_matches = self._generate_detailed_match_info(
                matches, 
                max_items=15,
                show_categories=True,
                category_keywords=category_keywords
            )
            self._details_set.update(detailed_matches)
        
        return list(self._details_set)
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on correlation ID findings"""
        
        if len(matches) == 0:
            recommendations = self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            recommendations = self._get_partial_implementation_recommendations()
        else:
            recommendations = self._get_quality_improvement_recommendations()
            
        # Add recommendations to set for uniqueness
        self._recommendations_set.update(recommendations)
        return list(self._recommendations_set)


class ApiLogsValidator(BaseGateValidator):
    """Validates API endpoint logging (entry/exit)"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.LOG_API_CALLS):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def _perform_validation(self, target_path: Path, 
                          file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Perform the actual validation logic"""
        return self.validate(target_path, file_analyses)
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate API logging implementation"""
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for API logging patterns
        extensions = self._get_file_extensions()
        # Get patterns dynamically
        patterns_dict = self._get_patterns(target_path)
        patterns = []
        
        # Handle LLM-generated patterns
        if 'llm_generated' in patterns_dict:
            patterns.extend(patterns_dict['llm_generated'])
        
        # Handle traditional pattern structure
        for category, category_patterns in patterns_dict.items():
            if category == 'llm_generated':
                continue
            if isinstance(category_patterns, list):
                patterns.extend(category_patterns)
        
        # Fallback to hardcoded patterns if no patterns available
        if not patterns:
            hardcoded_patterns = self._get_hardcoded_patterns()
            patterns = hardcoded_patterns.get('api_log_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        
        # Log initial pattern matches
        self._log_pattern_match(matches)
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Filter out invalid matches
        actual_matches = self._filter_actual_matches(matches)
        
        # Log filtered results
        self._log_pattern_match(actual_matches, "After filtering")
        
        found = len(actual_matches)
        
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
    
    def enhance_with_llm(self, result: GateValidationResult, llm_manager=None) -> GateValidationResult:
        """Enhance validation result with LLM-powered recommendations"""
        if llm_manager and llm_manager.is_enabled():
            try:
                llm_recommendations = self._generate_llm_recommendations(
                    gate_name="log_api_calls",
                    matches=result.matches,
                    expected=result.expected,
                    detected_technologies=result.technologies,
                    llm_manager=llm_manager
                )
                if llm_recommendations:
                    result.recommendations = llm_recommendations
                    print(f"✅ LLM recommendations generated for log_api_calls")
                else:
                    print(f"⚠️ LLM returned empty recommendations for log_api_calls")
            except Exception as e:
                print(f"⚠️ LLM recommendation generation failed for log_api_calls: {e}")
        
        return result
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get hardcoded API logging patterns as fallback"""
        
        if self.language == Language.PYTHON:
            return {
                'api_log_patterns': [
                    r'@app\.route.*\n.*logger\.',
                    r'@router\..*\n.*logger\.',
                    r'def.*api.*\n.*logger\.',
                    r'logger\.info.*request',
                    r'logger\.info.*response',
                    r'logger\.info.*endpoint',
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
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'api_log_patterns': [
                    r'app\.get.*\n.*logger\.',
                    r'app\.post.*\n.*logger\.',
                    r'router\..*\n.*logger\.',
                    r'logger\.info.*request',
                    r'logger\.info.*response',
                    r'logger\.info.*endpoint',
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
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """DEPRECATED: Use _get_hardcoded_patterns instead"""
        return self._get_hardcoded_patterns()
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get API logging config patterns"""
        return {
            'api_log_config': [
                'api.conf', 'access.conf', 'middleware.conf'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected API logging instances"""
        
        # Look for API/controller files
        api_files = len([f for f in lang_files 
                        if any(keyword in f.file_path.lower() 
                              for keyword in ['controller', 'handler', 'router', 'api', 
                                             'endpoint', 'resource'])])
        
        # Expect 2-3 log points per API file (entry/exit)
        return max(api_files , 5)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess API logging quality"""
        
        quality_scores = {}
        
        # Check for request/response logging
        request_logs = len([match for match in matches 
                          if 'request' in match.get('matched_text', match.get('match', '')).lower()])
        response_logs = len([match for match in matches 
                           if 'response' in match.get('matched_text', match.get('match', '')).lower()])
        
        if request_logs > 0:
            quality_scores['request_logging'] = min(request_logs * 3, 10)
        if response_logs > 0:
            quality_scores['response_logging'] = min(response_logs * 3, 10)
        
        # Check for endpoint identification
        endpoint_logs = len([match for match in matches 
                           if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
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
            return super()._generate_details([])
        
        # Add to details set for uniqueness
        self._details_set.add(f"Found {len(matches)} API logging implementations")
        
        # Group by file
        files_with_api_logs = len(set(match.get('file_path', match.get('file', 'unknown')) for match in matches))
        self._details_set.add(f"API logging present in {files_with_api_logs} files")
        
        # Check for different types of API logging
        types = set()  # Use set for unique types
        if any('request' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Request logging')
        if any('response' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Response logging')
        if any('error' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Error logging')
        
        if types:
            self._details_set.add(f"API logging types: {', '.join(sorted(types))}")
        
        # Add detailed match information using the standardized method
        if matches:
            self._details_set.add("")  # Add spacing
            
            # Define categories for API logging
            category_keywords = {
                'Request Logging': ['request', 'payload', 'body', 'headers'],
                'Response Logging': ['response', 'result', 'status'],
                'Error Logging': ['error', 'exception', 'fail'],
                'Performance Logging': ['timing', 'duration', 'latency'],
                'Security Logging': ['auth', 'token', 'permission']
            }
            
            detailed_matches = self._generate_detailed_match_info(
                matches, 
                max_items=15,
                show_categories=True,
                category_keywords=category_keywords
            )
            self._details_set.update(detailed_matches)
        
        return list(self._details_set)
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on API logging findings"""
        
        if len(matches) == 0:
            recommendations = self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            recommendations = self._get_partial_implementation_recommendations()
        else:
            recommendations = self._get_quality_improvement_recommendations()

        # Add recommendations to set for uniqueness
        self._recommendations_set.update(recommendations)
        return list(self._recommendations_set)


class ApplicationLogsValidator(StructuredLogsValidator):
    """Validates application message logging implementation using structured logging validation approach"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.LOG_APPLICATION_MESSAGES):
        """Initialize with application logging gate type but use structured logging validation"""
        # Initialize with STRUCTURED_LOGS gate type to ensure identical scoring
        super().__init__(language, GateType.STRUCTURED_LOGS)
        # Store original gate type for reference
        self._application_gate_type = gate_type
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate using structured logging approach but report as application logging"""
        # Get validation result using structured logging validation
        result = super().validate(target_path, file_analyses)
        
        # Only modify the details to reflect application logging context
        if result.details:
            result.details = [d.replace('structured logging', 'application logging') 
                            for d in result.details]
            
            # Add application logging specific context
            result.details.append("\nNote: This gate uses the same validation criteria as Structured Logs")
            result.details.append(f"\nDebug: Using gate type {GateType.STRUCTURED_LOGS} for scoring")
        
        # Ensure recommendations are application-logging focused
        if result.recommendations:
            result.recommendations = [r.replace('structured logging', 'application logging') 
                                    for r in result.recommendations]
        
        return result

# Keep the old class name for backward compatibility
BackgroundJobLogsValidator = ApplicationLogsValidator
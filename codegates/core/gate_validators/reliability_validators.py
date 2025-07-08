"""
Reliability Gate Validators - Validators for reliability-related quality gates
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from ...models import Language, FileAnalysis, GateType
from .base import BaseGateValidator, GateValidationResult


class RetryLogicValidator(BaseGateValidator):
    """Validates retry mechanisms implementation"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.RETRY_LOGIC):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate retry logic implementation"""
        
        # Get all patterns from loaded configuration
        all_patterns = []
        for category_patterns in self.patterns.values():
            if isinstance(category_patterns, list):
                all_patterns.extend(category_patterns)
        
        if not all_patterns:
            # Fallback to hardcoded patterns
            all_patterns = self._get_hardcoded_patterns().get('retry_patterns', [])
        
        # Search for patterns
        matches = self._search_files_for_patterns(
            target_path, 
            self._get_file_extensions(), 
            all_patterns
        )
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Filter out pattern attempts and count only actual matches
        actual_matches = self._filter_actual_matches(matches)
        
        # Calculate expected count based on non-test files
        non_test_files = [f for f in file_analyses if not self._is_test_file(f.file_path)]
        expected = self._estimate_expected_count(non_test_files)
        
        # Calculate quality score based on actual matches
        quality_score = self._calculate_quality_score(actual_matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(actual_matches)
        recommendations = self._generate_recommendations_from_matches(actual_matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=len(actual_matches),
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches  # Keep all matches for debugging
        )
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get hardcoded retry logic patterns for each language as fallback"""
        
        if self.language == Language.PYTHON:
            return {
                'retry_patterns': [
                    r'@retry\s*\(',
                    r'retrying\.',
                    r'tenacity\.',
                    r'for\s+attempt\s+in\s+range\s*\(',
                    r'while\s+retries\s*<',
                    r'time\.sleep\s*\(',
                    r'random\.uniform\s*\(',
                    r'backoff\.',
                    r'max_retries\s*=',
                    r'retry_count\s*=',
                    r'exponential.*backoff',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'retry_patterns': [
                    r'@Retryable',
                    r'@Retry',
                    r'Resilience4j.*Retry',
                    r'for\s*\(\s*int\s+retries\s*=',
                    r'while\s*\(\s*retries\s*<',
                    r'Thread\.sleep\s*\(',
                    r'TimeUnit\.\w+\.sleep\s*\(',
                    r'RetryPolicy',
                    r'maxRetries\s*=',
                    r'retryCount\s*=',
                    r'exponentialBackoff',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'retry_patterns': [
                    r'retry\s*\(',
                    r'p-retry',
                    r'async-retry',
                    r'for\s*\(\s*let\s+attempt\s*=',
                    r'while\s*\(\s*retries\s*<',
                    r'setTimeout\s*\(',
                    r'delay\s*\(',
                    r'maxRetries\s*:',
                    r'retryCount\s*:',
                    r'exponentialBackoff',
                    r'backoff\s*:',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'retry_patterns': [
                    r'\[Retry\]',
                    r'Polly\.',
                    r'RetryPolicy',
                    r'for\s*\(\s*int\s+retries\s*=',
                    r'while\s*\(\s*retries\s*<',
                    r'Task\.Delay\s*\(',
                    r'Thread\.Sleep\s*\(',
                    r'MaxRetries\s*=',
                    r'RetryCount\s*=',
                    r'ExponentialBackoff',
                    r'WaitAndRetry',
                ]
            }
        else:
            return {'retry_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get retry configuration patterns"""
        return {
            'retry_config': [
                'retry.conf', 'backoff.conf', 'resilience.conf'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected retry logic instances"""
        
        # Look for files that likely make external calls
        external_files = len([f for f in lang_files 
                            if any(keyword in f.file_path.lower() 
                                  for keyword in ['client', 'service', 'api', 'http', 'rest', 
                                                 'repository', 'dao', 'connector'])])
        
        # Estimate retry mechanisms needed:
        # - At least 1 retry mechanism per external service file
        # - Additional mechanisms based on LOC (1 per 200 LOC in external files)
        base_mechanisms = external_files
        loc_based_mechanisms = 0 #sum(f.lines_of_code for f in lang_files) // 200
        
        return max(base_mechanisms + loc_based_mechanisms, 0)  # At least 3 retry mechanisms minimum
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess retry logic quality"""
        
        quality_scores = {}
        
        # Check for proper retry patterns
        decorator_patterns = ['@retry', '@retryable', 'retry_template']
        decorator_matches = len([match for match in matches 
                               if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                     for pattern in decorator_patterns)])
        
        if decorator_matches > 0:
            quality_scores['retry_decorators'] = min(decorator_matches * 5, 15)
        
        # Check for backoff strategies
        backoff_patterns = ['backoff', 'exponential', 'linear', 'delay']
        backoff_matches = len([match for match in matches 
                             if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                   for pattern in backoff_patterns)])
        
        if backoff_matches > 0:
            quality_scores['backoff_strategy'] = min(backoff_matches * 3, 10)
        
        # Check for retry configuration
        config_patterns = ['max_retries', 'retry_count', 'retry_limit']
        config_matches = len([match for match in matches 
                            if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                  for pattern in config_patterns)])
        
        if config_matches > 0:
            quality_scores['retry_config'] = min(config_matches * 3, 10)
        
        # Check for error handling in retry logic
        error_patterns = ['catch', 'exception', 'error', 'failure']
        error_matches = len([match for match in matches 
                           if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                 for pattern in error_patterns)])
        
        if error_matches > 0:
            quality_scores['error_handling'] = min(error_matches * 3, 10)
        
        # Check for retry logging
        log_patterns = ['log', 'trace', 'debug', 'info']
        log_matches = len([match for match in matches 
                         if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                               for pattern in log_patterns)])
        
        if log_matches > 0:
            quality_scores['retry_logging'] = min(log_matches * 3, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no retry logic found"""
        
        return [
            "Implement retry logic for external service calls",
            "Add exponential backoff for failed requests",
            "Use retry libraries like Tenacity (Python) or Polly (.NET)",
            "Configure maximum retry attempts and timeout limits",
            "Implement circuit breaker pattern for cascading failures"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial retry implementation"""
        
        return [
            "Extend retry logic to all external service integrations",
            "Implement exponential backoff for better performance",
            "Add jitter to prevent thundering herd problems",
            "Configure appropriate retry counts for different operations"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving retry quality"""
        
        return [
            "Use sophisticated retry libraries with built-in strategies",
            "Implement different retry policies for different error types",
            "Add monitoring and metrics for retry attempts",
            "Configure proper timeout and circuit breaker integration"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate retry implementation details"""
        
        if not matches:
            return [
                "No retry logic implementations found",
                "Consider implementing retry mechanisms for external service calls"
            ]
        
        details = []
        
        # Basic count information
        found_count = len(matches)
        details.append(f"Found {found_count} retry logic implementations")
        
        # Implementation types
        impl_types = {
            'Decorator-based': ['@retry', '@retryable'],
            'Manual retry': ['for', 'while', 'attempt'],
            'Library-based': ['tenacity', 'polly', 'resilience4j', 'retry-axios']
        }
        
        type_counts = {}
        for match in matches:
            match_text = match.get('matched_text', match.get('match', '')).lower()
            for impl_type, patterns in impl_types.items():
                if any(pattern in match_text for pattern in patterns):
                    type_counts[impl_type] = type_counts.get(impl_type, 0) + 1
        
        if type_counts:
            details.append("\nImplementation types:")
            for impl_type, count in sorted(type_counts.items()):
                details.append(f"  - {impl_type}: {count}")
        
        # Backoff strategies
        backoff_types = {
            'Exponential': ['exponential', 'exp_backoff'],
            'Linear': ['linear', 'fixed_delay'],
            'Random': ['random', 'jitter'],
            'Custom': ['custom_backoff', 'strategy']
        }
        
        backoff_counts = {}
        for match in matches:
            match_text = match.get('matched_text', match.get('match', '')).lower()
            for backoff_type, patterns in backoff_types.items():
                if any(pattern in match_text for pattern in patterns):
                    backoff_counts[backoff_type] = backoff_counts.get(backoff_type, 0) + 1
        
        if backoff_counts:
            details.append("\nBackoff strategies:")
            for backoff_type, count in sorted(backoff_counts.items()):
                details.append(f"  - {backoff_type}: {count}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on retry findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class TimeoutsValidator(BaseGateValidator):
    """Validates timeout configuration"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.TIMEOUTS):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate timeout implementation"""
        
        # Get all patterns from loaded configuration
        all_patterns = []
        for category_patterns in self.patterns.values():
            if isinstance(category_patterns, list):
                all_patterns.extend(category_patterns)
        
        if not all_patterns:
            # Fallback to hardcoded patterns
            all_patterns = self._get_hardcoded_patterns().get('timeout_patterns', [])
        
        # Search for patterns
        matches = self._search_files_for_patterns(
            target_path, 
            self._get_file_extensions(), 
            all_patterns
        )
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Calculate expected count based on non-test files
        non_test_files = [f for f in file_analyses if not self._is_test_file(f.file_path)]
        expected = self._estimate_expected_count(non_test_files)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=len(matches),
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get timeout patterns for each language"""
        
        if self.language == Language.PYTHON:
            return {
                'timeout_patterns': [
                    r'timeout\s*=\s*\d+',
                    r'requests\.get\s*\([^)]*timeout\s*=',
                    r'requests\.post\s*\([^)]*timeout\s*=',
                    r'urllib\.request\.[^(]*timeout\s*=',
                    r'socket\.settimeout\s*\(',
                    r'asyncio\.wait_for\s*\(',
                    r'concurrent\.futures\.[^(]*timeout\s*=',
                    r'@timeout\s*\(',
                    r'signal\.alarm\s*\(',
                    r'threading\.Timer\s*\(',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'timeout_patterns': [
                    r'setTimeout\s*\(',
                    r'setConnectTimeout\s*\(',
                    r'setReadTimeout\s*\(',
                    r'timeout\s*=\s*\d+',
                    r'TimeUnit\.\w+\s*,\s*\d+',
                    r'@Timeout\s*\(',
                    r'CompletableFuture\.get\s*\([^)]*TimeUnit',
                    r'ExecutorService.*timeout',
                    r'HttpClient.*timeout',
                    r'RestTemplate.*timeout',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'timeout_patterns': [
                    r'setTimeout\s*\(',
                    r'timeout\s*:\s*\d+',
                    r'axios\.[^(]*timeout\s*:',
                    r'fetch\s*\([^)]*timeout',
                    r'AbortController\s*\(',
                    r'signal\s*:\s*AbortSignal',
                    r'Promise\.race\s*\(',
                    r'setInterval\s*\(',
                    r'clearTimeout\s*\(',
                    r'request\.[^(]*timeout',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'timeout_patterns': [
                    r'Timeout\s*=\s*\d+',
                    r'HttpClient.*Timeout',
                    r'CancellationToken\.',
                    r'Task\.Delay\s*\(',
                    r'Task\.WaitAll\s*\([^)]*TimeSpan',
                    r'Task\.WaitAny\s*\([^)]*TimeSpan',
                    r'ManualResetEvent.*timeout',
                    r'AutoResetEvent.*timeout',
                    r'SemaphoreSlim.*timeout',
                    r'Timer\s*\(',
                ]
            }
        else:
            return {'timeout_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get timeout configuration patterns"""
        return {
            'timeout_config': [
                'timeout.conf', 'timeouts.yaml', 'network.conf'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected timeout instances"""
        
        # Look for files that likely need timeouts, excluding test files
        timeout_files = len([f for f in lang_files 
                           if any(keyword in f.file_path.lower() 
                                 for keyword in ['client', 'service', 'api', 'http', 'rest', 
                                               'repository', 'dao', 'connector', 'network'])
                           and not self._is_test_file(f.file_path)])  # Exclude test files
        
        # Estimate timeout mechanisms needed:
        # - At least 1 timeout per external service file
        # - Additional timeouts based on LOC (1 per 200 LOC in service files)
        base_timeouts = timeout_files
        loc_based_timeouts = sum(f.lines_of_code for f in lang_files) // 200
        
        return max(base_timeouts + loc_based_timeouts, 3)  # At least 3 timeout mechanisms minimum
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess timeout implementation quality"""
        
        quality_scores = {}
        
        # Check for connection timeouts
        connection_patterns = ['connect', 'connection']
        connection_matches = len([match for match in matches 
                                if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                      for pattern in connection_patterns)])
        
        if connection_matches > 0:
            quality_scores['connection_timeouts'] = min(connection_matches * 3, 10)
        
        # Check for read timeouts
        read_patterns = ['read', 'response', 'socket']
        read_matches = len([match for match in matches 
                          if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                for pattern in read_patterns)])
        
        if read_matches > 0:
            quality_scores['read_timeouts'] = min(read_matches * 3, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no timeouts found"""
        
        return [
            "Configure connection timeouts for all HTTP clients",
            "Set read timeouts for socket operations",
            "Implement request timeouts for external service calls",
            "Use appropriate timeout values based on SLA requirements",
            "Consider different timeout strategies for different operations"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial timeout implementation"""
        
        return [
            "Extend timeout configuration to all I/O operations",
            "Ensure both connection and read timeouts are configured",
            "Add timeout handling for database operations",
            "Implement timeout monitoring and alerting"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving timeout quality"""
        
        return [
            "Fine-tune timeout values based on performance metrics",
            "Implement adaptive timeout strategies",
            "Add timeout configuration to application properties",
            "Set up timeout monitoring and dashboards"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate timeout details"""
        
        # Filter out non-matching patterns - only show actual matches
        actual_matches = []
        for match in matches:
            file_path = match.get('file_path', match.get('file', ''))
            matched_text = match.get('matched_text', match.get('match', ''))
            line_number = match.get('line_number', match.get('line', 0))
            
            # Only include actual matches (not pattern attempts)
            if (file_path and file_path != 'N/A - No matches found' and 
                file_path != 'unknown' and matched_text.strip() and 
                line_number > 0):
                actual_matches.append(match)
        
        if not actual_matches:
            return ["No timeout implementations found"]
        
        details = [f"Found {len(actual_matches)} timeout implementations"]
        
        # Check for different timeout types
        timeout_types = []
        if any('connect' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            timeout_types.append('Connection')
        if any('read' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            timeout_types.append('Read')
        if any('request' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            timeout_types.append('Request')
        
        if timeout_types:
            details.append(f"Timeout types found: {', '.join(timeout_types)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on timeout findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class ThrottlingValidator(BaseGateValidator):
    """Validates throttling/rate limiting"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.THROTTLING):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate throttling implementation"""
        
        # Get all patterns from loaded configuration
        all_patterns = []
        for category_patterns in self.patterns.values():
            if isinstance(category_patterns, list):
                all_patterns.extend(category_patterns)
        
        if not all_patterns:
            # Fallback to hardcoded patterns
            all_patterns = self._get_hardcoded_patterns().get('throttling_patterns', [])
        
        # Search for patterns
        matches = self._search_files_for_patterns(
            target_path, 
            self._get_file_extensions(), 
            all_patterns
        )
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Calculate expected count based on non-test files
        non_test_files = [f for f in file_analyses if not self._is_test_file(f.file_path)]
        expected = self._estimate_expected_count(non_test_files)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=len(matches),
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get throttling patterns for each language"""
        
        if self.language == Language.PYTHON:
            return {
                'throttling_patterns': [
                    r'@throttle\s*\(',
                    r'@rate_limit\s*\(',
                    r'RateLimiter\s*\(',
                    r'TokenBucket\s*\(',
                    r'time\.sleep\s*\(',
                    r'rate_limit\s*=',
                    r'throttle\s*=',
                    r'slowapi\.',
                    r'flask_limiter\.',
                    r'ratelimit\s*\(',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'throttling_patterns': [
                    r'@RateLimited',
                    r'@Throttle',
                    r'RateLimiter\.',
                    r'Semaphore\s*\(',
                    r'Thread\.sleep\s*\(',
                    r'rateLimit\s*=',
                    r'throttle\s*=',
                    r'bucket4j\.',
                    r'guava.*RateLimiter',
                    r'resilience4j.*RateLimiter',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'throttling_patterns': [
                    r'throttle\s*\(',
                    r'rateLimit\s*\(',
                    r'express-rate-limit',
                    r'express-slow-down',
                    r'bottleneck\.',
                    r'p-throttle',
                    r'setTimeout\s*\(',
                    r'setInterval\s*\(',
                    r'rate.*limit',
                    r'throttle.*middleware',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'throttling_patterns': [
                    r'\[RateLimit\]',
                    r'\[Throttle\]',
                    r'SemaphoreSlim\s*\(',
                    r'RateLimiter\.',
                    r'Task\.Delay\s*\(',
                    r'Thread\.Sleep\s*\(',
                    r'RateLimit\s*=',
                    r'Throttle\s*=',
                    r'AspNetCoreRateLimit',
                    r'FirewallRules',
                ]
            }
        else:
            return {'throttling_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get throttling configuration patterns"""
        return {
            'throttling_config': [
                'ratelimit.conf', 'throttle.conf', 'limits.yaml'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected throttling instances"""
        
        # Look for files that likely need throttling, excluding test files
        api_files = len([f for f in lang_files 
                        if any(keyword in f.file_path.lower() 
                              for keyword in ['api', 'controller', 'endpoint', 'route', 
                                            'service', 'handler', 'resource'])
                        and not self._is_test_file(f.file_path)])  # Exclude test files
        
        # Estimate throttling mechanisms needed:
        # - At least 1 throttle per API endpoint file
        # - Additional throttles based on LOC (1 per 300 LOC in API files)
        base_throttles = api_files
        loc_based_throttles = sum(f.lines_of_code for f in lang_files) // 300
        
        return max(base_throttles + loc_based_throttles, 2)  # At least 2 throttling mechanisms minimum
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess throttling implementation quality"""
        
        quality_scores = {}
        
        # Check for rate limiting decorators/annotations
        decorator_patterns = ['@', 'decorator', 'middleware']
        decorator_matches = len([match for match in matches 
                               if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                     for pattern in decorator_patterns)])
        
        if decorator_matches > 0:
            quality_scores['rate_limit_decorators'] = min(decorator_matches * 5, 15)
        
        # Check for sophisticated rate limiting libraries
        library_patterns = ['bucket4j', 'resilience4j', 'slowapi', 'express-rate-limit']
        library_matches = len([match for match in matches 
                             if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                   for pattern in library_patterns)])
        
        if library_matches > 0:
            quality_scores['rate_limit_libraries'] = min(library_matches * 3, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no throttling found"""
        
        return [
            "Implement rate limiting middleware for API endpoints",
            "Add throttling to prevent abuse and ensure fair usage",
            "Use token bucket or sliding window algorithms",
            "Configure different rate limits for different user tiers",
            "Implement proper error responses for rate limit exceeded"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial throttling implementation"""
        
        return [
            "Extend rate limiting to all public API endpoints",
            "Implement different throttling strategies for different operations",
            "Add rate limiting based on user authentication levels",
            "Configure appropriate rate limit windows and thresholds"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving throttling quality"""
        
        return [
            "Use distributed rate limiting for multi-instance deployments",
            "Implement adaptive rate limiting based on system load",
            "Add rate limiting metrics and monitoring",
            "Configure proper rate limit headers in responses"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate throttling details"""
        
        # Filter out non-matching patterns - only show actual matches
        actual_matches = []
        for match in matches:
            file_path = match.get('file_path', match.get('file', ''))
            matched_text = match.get('matched_text', match.get('match', ''))
            line_number = match.get('line_number', match.get('line', 0))
            
            # Only include actual matches (not pattern attempts)
            if (file_path and file_path != 'N/A - No matches found' and 
                file_path != 'unknown' and matched_text.strip() and 
                line_number > 0):
                actual_matches.append(match)
        
        if not actual_matches:
            return ["No throttling implementations found"]
        
        details = [f"Found {len(actual_matches)} throttling implementations"]
        
        # Check for different throttling approaches
        throttling_types = []
        if any('@' in match.get('matched_text', match.get('match', '')) for match in actual_matches):
            throttling_types.append('Decorator-based')
        if any('middleware' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            throttling_types.append('Middleware-based')
        if any('library' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            throttling_types.append('Library-based')
        
        if throttling_types:
            details.append(f"Throttling types found: {', '.join(throttling_types)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on throttling findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class CircuitBreakerValidator(BaseGateValidator):
    """Validates circuit breaker pattern"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.CIRCUIT_BREAKERS):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate circuit breaker implementation"""
        
        # Get all patterns from loaded configuration
        all_patterns = []
        for category_patterns in self.patterns.values():
            if isinstance(category_patterns, list):
                all_patterns.extend(category_patterns)
        
        if not all_patterns:
            # Fallback to hardcoded patterns
            all_patterns = self._get_hardcoded_patterns().get('circuit_breaker_patterns', [])
        
        # Search for patterns
        matches = self._search_files_for_patterns(
            target_path, 
            self._get_file_extensions(), 
            all_patterns
        )
        
        # Filter out test files
        matches = self._filter_non_test_files(matches)
        
        # Calculate expected count based on non-test files
        non_test_files = [f for f in file_analyses if not self._is_test_file(f.file_path)]
        expected = self._estimate_expected_count(non_test_files)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=len(matches),
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get circuit breaker patterns for each language"""
        
        if self.language == Language.PYTHON:
            return {
                'circuit_breaker_patterns': [
                    r'@circuit_breaker\s*\(',
                    r'CircuitBreaker\s*\(',
                    r'pybreaker\.',
                    r'circuit.*breaker',
                    r'failure_threshold\s*=',
                    r'recovery_timeout\s*=',
                    r'half_open\s*=',
                    r'@circuitbreaker',
                    r'breaker\s*=',
                    r'state.*OPEN',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'circuit_breaker_patterns': [
                    r'@CircuitBreaker',
                    r'CircuitBreaker\.',
                    r'resilience4j\.circuitbreaker',
                    r'hystrix\.',
                    r'@HystrixCommand',
                    r'failureThreshold\s*=',
                    r'recoveryTimeout\s*=',
                    r'halfOpenAfter\s*=',
                    r'CircuitBreakerConfig\.',
                    r'State\.OPEN',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'circuit_breaker_patterns': [
                    r'CircuitBreaker\s*\(',
                    r'opossum\.',
                    r'circuit.*breaker',
                    r'failureThreshold\s*:',
                    r'timeout\s*:',
                    r'resetTimeout\s*:',
                    r'halfOpen\s*:',
                    r'breaker\s*=',
                    r'state.*OPEN',
                    r'fallback\s*:',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'circuit_breaker_patterns': [
                    r'\[CircuitBreaker\]',
                    r'CircuitBreaker\.',
                    r'Polly\.CircuitBreaker',
                    r'FailureThreshold\s*=',
                    r'DurationOfBreak\s*=',
                    r'CircuitBreakerPolicy',
                    r'State\.Open',
                    r'State\.HalfOpen',
                    r'HandleResult\s*<',
                    r'OrResult\s*<',
                ]
            }
        else:
            return {'circuit_breaker_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get circuit breaker configuration patterns"""
        return {
            'circuit_breaker_config': [
                'circuitbreaker.conf', 'resilience.conf', 'hystrix.conf'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected circuit breaker instances"""
        
        # Look for files that likely need circuit breakers, excluding test files
        service_files = len([f for f in lang_files 
                           if any(keyword in f.file_path.lower() 
                                 for keyword in ['client', 'service', 'api', 'http', 'rest', 
                                               'repository', 'dao', 'connector', 'gateway'])
                           and not self._is_test_file(f.file_path)])  # Exclude test files
        
        # Estimate circuit breakers needed:
        # - At least 1 circuit breaker per external service file
        # - Additional breakers based on LOC (1 per 400 LOC in service files)
        base_breakers = service_files
        loc_based_breakers = sum(f.lines_of_code for f in lang_files) // 400
        
        return max(base_breakers + loc_based_breakers, 2)  # At least 2 circuit breakers minimum
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess circuit breaker implementation quality"""
        
        quality_scores = {}
        
        # Check for proper circuit breaker libraries
        library_patterns = ['resilience4j', 'hystrix', 'polly', 'opossum', 'pybreaker']
        library_matches = len([match for match in matches 
                             if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                   for pattern in library_patterns)])
        
        if library_matches > 0:
            quality_scores['circuit_breaker_libraries'] = min(library_matches * 5, 15)
        
        # Check for configuration parameters
        config_patterns = ['threshold', 'timeout', 'recovery', 'fallback']
        config_matches = len([match for match in matches 
                            if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                  for pattern in config_patterns)])
        
        if config_matches > 0:
            quality_scores['circuit_breaker_config'] = min(config_matches * 2, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no circuit breakers found"""
        
        return [
            "Implement circuit breakers for external service calls",
            "Use circuit breaker libraries like Resilience4j or Hystrix",
            "Configure failure thresholds and recovery timeouts",
            "Implement fallback mechanisms for when circuits are open",
            "Add monitoring and alerting for circuit breaker state changes"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial circuit breaker implementation"""
        
        return [
            "Extend circuit breakers to all external service integrations",
            "Implement proper fallback strategies for each circuit",
            "Configure appropriate failure thresholds for different services",
            "Add circuit breaker metrics and dashboards"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving circuit breaker quality"""
        
        return [
            "Implement bulkhead pattern alongside circuit breakers",
            "Use different circuit breaker configurations for different services",
            "Add circuit breaker health checks and auto-recovery",
            "Implement circuit breaker state persistence for restarts"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate circuit breaker details"""
        
        # Filter out non-matching patterns - only show actual matches
        actual_matches = []
        for match in matches:
            file_path = match.get('file_path', match.get('file', ''))
            matched_text = match.get('matched_text', match.get('match', ''))
            line_number = match.get('line_number', match.get('line', 0))
            
            # Only include actual matches (not pattern attempts)
            if (file_path and file_path != 'N/A - No matches found' and 
                file_path != 'unknown' and matched_text.strip() and 
                line_number > 0):
                actual_matches.append(match)
        
        if not actual_matches:
            return ["No circuit breaker implementations found"]
        
        details = [f"Found {len(actual_matches)} circuit breaker implementations"]
        
        # Check for different circuit breaker libraries
        libraries = []
        if any('resilience4j' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            libraries.append('Resilience4j')
        if any('hystrix' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            libraries.append('Hystrix')
        if any('polly' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            libraries.append('Polly')
        if any('opossum' in match.get('matched_text', match.get('match', '')).lower() for match in actual_matches):
            libraries.append('Opossum')
        
        if libraries:
            details.append(f"Circuit breaker libraries found: {', '.join(libraries)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on circuit breaker findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations() 
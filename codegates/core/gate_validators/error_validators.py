"""
Error Handling Gate Validators - Validators for error-related hard gates
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from ...models import Language, FileAnalysis
from .base import BaseGateValidator, GateValidationResult


class ErrorLogsValidator(BaseGateValidator):
    """Validates error logging and exception handling"""
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate error logging implementation"""
        
        # Detect technologies first
        detected_technologies = self._detect_technologies(target_path, file_analyses)
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for error logging patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('error_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches, detected_technologies)
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
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get error logging patterns for each language"""
        
        if self.language == Language.PYTHON:
            return {
                'error_patterns': [
                    r'except\s+\w+.*:.*\n.*logger\.',
                    r'except\s+Exception.*:.*\n.*logger\.',
                    r'try:.*\n.*except.*:.*\n.*log',
                    r'logger\.error\s*\(',
                    r'logger\.exception\s*\(',
                    r'logging\.error\s*\(',
                    r'logging\.exception\s*\(',
                    r'raise.*\n.*logger\.',
                    r'traceback\.format_exc\(\)',
                    r'sys\.exc_info\(\)',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'error_patterns': [
                    r'catch\s*\([^)]*Exception[^)]*\).*\{.*\n.*logger\.',
                    r'catch\s*\([^)]*\).*\{.*\n.*log\.',
                    r'logger\.error\s*\(',
                    r'log\.error\s*\(',
                    r'throw new.*Exception.*\n.*logger\.',
                    r'printStackTrace\(\)',
                    r'ExceptionUtils\.getStackTrace\(',
                    r'@ExceptionHandler',
                    r'@ControllerAdvice',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'error_patterns': [
                    r'catch\s*\([^)]*\).*\{.*\n.*console\.error',
                    r'catch\s*\([^)]*\).*\{.*\n.*logger\.',
                    r'\.catch\s*\([^)]*\).*=>.*console\.error',
                    r'\.catch\s*\([^)]*\).*=>.*logger\.',
                    r'console\.error\s*\(',
                    r'logger\.error\s*\(',
                    r'throw new Error.*\n.*console\.',
                    r'throw new Error.*\n.*logger\.',
                    r'process\.on\s*\(\s*["\']uncaughtException',
                    r'window\.onerror\s*=',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'error_patterns': [
                    r'catch\s*\([^)]*Exception[^)]*\).*\{.*\n.*_logger\.',
                    r'catch\s*\([^)]*\).*\{.*\n.*Log\.',
                    r'_logger\.LogError\s*\(',
                    r'Log\.Error\s*\(',
                    r'throw new.*Exception.*\n.*_logger\.',
                    r'ex\.ToString\(\)',
                    r'ex\.StackTrace',
                    r'\[ExceptionFilter\]',
                    r'IExceptionHandler',
                ]
            }
        else:
            return {'error_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get error handling config patterns"""
        return {
            'error_config': [
                'error.conf', 'exception.conf', 'logging.conf',
                'sentry.conf', 'errorhandling.conf'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected error logging instances"""
        
        # Look for files that likely contain business logic
        business_files = len([f for f in lang_files 
                            if any(keyword in f.file_path.lower() 
                                  for keyword in ['service', 'controller', 'handler', 'manager', 
                                                 'repository', 'dao', 'api', 'web'])])
        
        # Estimate 1-2 error handling blocks per business file
        return max(business_files * 2, file_count // 3)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess error logging quality"""
        
        quality_scores = {}
        
        # Check for proper exception handling patterns
        exception_patterns = ['exception', 'error', 'catch', 'try']
        exception_matches = len([match for match in matches 
                               if any(pattern in match['match'].lower() for pattern in exception_patterns)])
        
        if exception_matches > 0:
            quality_scores['exception_handling'] = min(exception_matches * 3, 15)
        
        # Check for stack trace logging
        stack_patterns = ['traceback', 'stacktrace', 'stack_trace', 'tostring']
        stack_matches = len([match for match in matches 
                           if any(pattern in match['match'].lower() for pattern in stack_patterns)])
        
        if stack_matches > 0:
            quality_scores['stack_traces'] = min(stack_matches * 2, 10)
        
        # Check for structured error logging
        structured_patterns = ['json', 'structured', 'context']
        structured_matches = len([match for match in matches 
                                if any(pattern in match['match'].lower() for pattern in structured_patterns)])
        
        if structured_matches > 0:
            quality_scores['structured_errors'] = min(structured_matches * 2, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no error logging found"""
        
        return [
            "Implement comprehensive error logging in try-catch blocks",
            "Log exceptions with full stack traces for debugging",
            "Include contextual information in error logs",
            "Set up proper exception handling middleware",
            "Consider using structured logging for errors"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial error logging implementation"""
        
        return [
            "Extend error logging to all exception handling blocks",
            "Ensure consistent error log format across the application",
            "Add more context to error logs (user ID, request ID, etc.)",
            "Implement proper error categorization and severity levels"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving error logging quality"""
        
        return [
            "Standardize error log message format",
            "Include correlation IDs in error logs",
            "Implement error aggregation and monitoring",
            "Set up error alerting for critical exceptions"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]], 
                         detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Generate error logging details"""
        
        if not matches:
            return ["No error logging patterns found"]
        
        details = [f"Found {len(matches)} error logging implementations"]
        
        # Group by file
        files_with_errors = len(set(match['file'] for match in matches))
        details.append(f"Error logging present in {files_with_errors} files")
        
        # Check for different types of error handling
        types = []
        if any('exception' in match['match'].lower() for match in matches):
            types.append('Exception handling')
        if any('catch' in match['match'].lower() for match in matches):
            types.append('Try-catch blocks')
        if any('throw' in match['match'].lower() for match in matches):
            types.append('Error throwing')
        
        if types:
            details.append(f"Error handling types: {', '.join(types)}")
        
        # Add technology detection details
        if detected_technologies:
            details.append("\n🔧 Detected Technologies:")
            for category, techs in detected_technologies.items():
                if techs:
                    details.append(f"  {category.title()}: {', '.join(techs)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on error logging findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class UiErrorsValidator(BaseGateValidator):
    """Validates UI error handling"""
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate UI error handling implementation"""
        
        # Detect technologies first
        detected_technologies = self._detect_technologies(target_path, file_analyses)
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for UI error patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('ui_error_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches, detected_technologies)
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
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get UI error handling patterns"""
        
        if self.language == Language.PYTHON:
            return {
                'ui_error_patterns': [
                    r'@app\.errorhandler\s*\(',
                    r'@bp\.errorhandler\s*\(',
                    r'flask\.abort\s*\(',
                    r'render_template.*error',
                    r'flash\s*\([^)]*error',
                    r'return.*error.*template',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'ui_error_patterns': [
                    r'@ExceptionHandler',
                    r'@ControllerAdvice',
                    r'ModelAndView.*error',
                    r'return.*error.*view',
                    r'ResponseEntity\..*error',
                    r'@ErrorPage',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'ui_error_patterns': [
                    r'componentDidCatch\s*\(',
                    r'ErrorBoundary',
                    r'try.*catch.*setState.*error',
                    r'\.catch.*setError',
                    r'useState.*error',
                    r'error.*state',
                    r'window\.onerror',
                    r'addEventListener.*error',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'ui_error_patterns': [
                    r'\[ExceptionFilter\]',
                    r'IExceptionHandler',
                    r'HandleErrorAsync',
                    r'return.*View.*Error',
                    r'ViewResult.*Error',
                    r'RedirectToAction.*Error',
                ]
            }
        else:
            return {'ui_error_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get UI error config patterns"""
        return {
            'ui_error_config': [
                'error-pages.conf', 'ui-errors.conf', 'frontend-errors.conf'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected UI error handling instances"""
        
        # Look for UI/web related files
        ui_files = len([f for f in lang_files 
                       if any(keyword in f.file_path.lower() 
                             for keyword in ['view', 'template', 'component', 'page', 
                                            'ui', 'frontend', 'web', 'controller'])])
        
        return max(ui_files // 2, 1)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess UI error handling quality"""
        
        quality_scores = {}
        
        # Check for error boundaries (React/frontend)
        boundary_patterns = ['errorboundary', 'componentdidcatch', 'error.*boundary']
        boundary_matches = len([match for match in matches 
                              if any(pattern in match['match'].lower() for pattern in boundary_patterns)])
        
        if boundary_matches > 0:
            quality_scores['error_boundaries'] = min(boundary_matches * 5, 15)
        
        # Check for user-friendly error handling
        friendly_patterns = ['user.*friendly', 'message', 'alert', 'notification']
        friendly_matches = len([match for match in matches 
                              if any(pattern in match['match'].lower() for pattern in friendly_patterns)])
        
        if friendly_matches > 0:
            quality_scores['user_friendly'] = min(friendly_matches * 3, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no UI error handling found"""
        
        if self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return [
                "Implement React Error Boundaries for component error handling",
                "Add global error handlers for unhandled promise rejections",
                "Create user-friendly error messages and fallback UIs",
                "Implement error state management in components"
            ]
        else:
            return [
                "Implement global error handlers for web applications",
                "Create custom error pages for different error types",
                "Add user-friendly error messages",
                "Implement proper error state management"
            ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial UI error implementation"""
        
        return [
            "Extend error handling to all UI components",
            "Ensure consistent error message formatting",
            "Add error recovery mechanisms where possible",
            "Implement error logging for UI errors"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving UI error quality"""
        
        return [
            "Improve error message clarity and user experience",
            "Add error tracking and analytics",
            "Implement progressive error disclosure",
            "Create error handling documentation for users"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]], 
                         detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Generate UI error handling details"""
        
        if not matches:
            return ["No UI error handling patterns found"]
        
        details = [f"Found {len(matches)} UI error handling implementations"]
        
        # Add technology detection details
        if detected_technologies:
            details.append("\n🎨 Detected Technologies:")
            for category, techs in detected_technologies.items():
                if techs:
                    details.append(f"  {category.title()}: {', '.join(techs)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on UI error findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class HttpCodesValidator(BaseGateValidator):
    """Validates proper HTTP status code usage"""
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate HTTP status code implementation"""
        
        # Detect technologies first
        detected_technologies = self._detect_technologies(target_path, file_analyses)
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for HTTP status code patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('http_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches, detected_technologies)
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
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get HTTP status code patterns"""
        
        if self.language == Language.PYTHON:
            return {
                'http_patterns': [
                    r'return.*status_code\s*=\s*\d{3}',
                    r'abort\s*\(\s*\d{3}',
                    r'HTTPException\s*\(\s*status_code\s*=\s*\d{3}',
                    r'Response\s*\([^)]*status\s*=\s*\d{3}',
                    r'status\s*=\s*HTTP_\d+',
                    r'return.*\d{3}',  # Simple status return
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'http_patterns': [
                    r'ResponseEntity\.\w+\(\)',
                    r'HttpStatus\.\w+',
                    r'@ResponseStatus\s*\([^)]*\d{3}',
                    r'response\.setStatus\s*\(\s*\d{3}',
                    r'return.*status\s*\(\s*\d{3}',
                    r'ResponseEntity\.status\s*\(\s*\d{3}',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'http_patterns': [
                    r'res\.status\s*\(\s*\d{3}',
                    r'response\.status\s*=\s*\d{3}',
                    r'\.status\s*\(\s*\d{3}\)',
                    r'statusCode\s*:\s*\d{3}',
                    r'return.*status\s*:\s*\d{3}',
                    r'throw.*status\s*:\s*\d{3}',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'http_patterns': [
                    r'return.*StatusCode\s*\(\s*\d{3}',
                    r'HttpStatusCode\.\w+',
                    r'return.*Ok\s*\(\)',
                    r'return.*BadRequest\s*\(',
                    r'return.*NotFound\s*\(',
                    r'return.*Unauthorized\s*\(',
                    r'Response\.StatusCode\s*=\s*\d{3}',
                ]
            }
        else:
            return {'http_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get HTTP config patterns"""
        return {
            'http_config': [
                'http.conf', 'status-codes.conf', 'api.conf'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected HTTP status code usage"""
        
        # Look for API/web related files
        api_files = len([f for f in lang_files 
                        if any(keyword in f.file_path.lower() 
                              for keyword in ['controller', 'handler', 'router', 'api', 
                                             'endpoint', 'resource', 'web'])])
        
        return max(api_files * 3, 5)  # 3 status codes per API file
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess HTTP status code quality"""
        
        quality_scores = {}
        
        # Check for different status code categories
        status_categories = {
            '2xx': [r'2\d{2}', r'ok', r'created', r'accepted'],
            '4xx': [r'4\d{2}', r'badrequest', r'unauthorized', r'notfound'],
            '5xx': [r'5\d{2}', r'internalservererror', r'badgateway']
        }
        
        for category, patterns in status_categories.items():
            category_matches = len([match for match in matches 
                                  if any(re.search(pattern, match['match'].lower()) for pattern in patterns)])
            if category_matches > 0:
                quality_scores[f'{category}_codes'] = min(category_matches * 2, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no HTTP status codes found"""
        
        return [
            "Implement proper HTTP status codes for all API endpoints",
            "Use appropriate 2xx codes for successful operations",
            "Return 4xx codes for client errors (validation, authentication)",
            "Return 5xx codes for server errors",
            "Follow REST API status code conventions"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial HTTP status code implementation"""
        
        return [
            "Extend HTTP status code usage to all API endpoints",
            "Ensure consistent status code usage across the application",
            "Add more specific status codes for different error scenarios",
            "Document API status code meanings"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving HTTP status code quality"""
        
        return [
            "Use more specific HTTP status codes where appropriate",
            "Implement consistent error response format with status codes",
            "Add status code documentation to API specs",
            "Consider implementing custom status code middleware"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]], 
                         detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Generate HTTP status code details"""
        
        if not matches:
            return ["No HTTP status code patterns found"]
        
        details = [f"Found {len(matches)} HTTP status code implementations"]
        
        # Analyze status code distribution
        status_codes = []
        for match in matches:
            # Extract status codes from matches
            import re
            codes = re.findall(r'\b[2-5]\d{2}\b', match['match'])
            status_codes.extend(codes)
        
        if status_codes:
            unique_codes = set(status_codes)
            details.append(f"Status codes used: {', '.join(sorted(unique_codes))}")
        
        # Add technology detection details
        if detected_technologies:
            details.append("\n🌐 Detected Technologies:")
            for category, techs in detected_technologies.items():
                if techs:
                    details.append(f"  {category.title()}: {', '.join(techs)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on HTTP status code findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations()


class UiErrorToolsValidator(BaseGateValidator):
    """Validates UI error monitoring tools like Sentry"""
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate UI error monitoring tools implementation"""
        
        # Detect technologies first
        detected_technologies = self._detect_technologies(target_path, file_analyses)
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for error monitoring tool patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('error_tool_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches, detected_technologies)
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
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get error monitoring tool patterns"""
        
        if self.language == Language.PYTHON:
            return {
                'error_tool_patterns': [
                    r'import sentry_sdk',
                    r'sentry_sdk\.init',
                    r'sentry_sdk\.capture_exception',
                    r'import rollbar',
                    r'rollbar\.init',
                    r'import bugsnag',
                    r'bugsnag\.configure',
                    r'import airbrake',
                    r'from honeybadger import honeybadger',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'error_tool_patterns': [
                    r'import.*sentry',
                    r'Sentry\.init',
                    r'Sentry\.captureException',
                    r'import.*rollbar',
                    r'import.*bugsnag',
                    r'import.*airbrake',
                    r'@SentryTransaction',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'error_tool_patterns': [
                    r'import.*@sentry',
                    r'Sentry\.init',
                    r'Sentry\.captureException',
                    r'import.*rollbar',
                    r'import.*bugsnag',
                    r'import.*@bugsnag',
                    r'import.*airbrake',
                    r'ErrorBoundary.*Sentry',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'error_tool_patterns': [
                    r'using Sentry',
                    r'SentrySdk\.Init',
                    r'SentrySdk\.CaptureException',
                    r'using Rollbar',
                    r'using Bugsnag',
                    r'using Airbrake',
                ]
            }
        else:
            return {'error_tool_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get error monitoring config patterns"""
        return {
            'error_tool_config': [
                'sentry.conf', 'rollbar.conf', 'bugsnag.conf',
                '.sentryclirc', 'sentry.properties'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected error monitoring tool usage"""
        
        # Either you have error monitoring or you don't
        return 1
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess error monitoring tool quality"""
        
        quality_scores = {}
        
        # Check for different error monitoring tools
        tools = {
            'sentry': [r'sentry'],
            'rollbar': [r'rollbar'],
            'bugsnag': [r'bugsnag'],
            'airbrake': [r'airbrake'],
        }
        
        for tool, patterns in tools.items():
            tool_matches = len([match for match in matches 
                              if any(pattern in match['match'].lower() for pattern in patterns)])
            if tool_matches > 0:
                quality_scores[f'{tool}_integration'] = 20  # High value for having monitoring
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no error monitoring tools found"""
        
        return [
            "Implement error monitoring tools like Sentry, Rollbar, or Bugsnag",
            "Set up real-time error tracking and alerting",
            "Configure error grouping and deduplication",
            "Add contextual information to error reports",
            "Set up error monitoring dashboards"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial error monitoring implementation"""
        
        return [
            "Extend error monitoring to all application components",
            "Configure proper error filtering and sampling",
            "Add user context to error reports",
            "Set up error monitoring alerts and notifications"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving error monitoring quality"""
        
        return [
            "Fine-tune error monitoring configuration",
            "Add custom error tags and context",
            "Implement error monitoring best practices",
            "Set up error monitoring analytics and reporting"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]], 
                         detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Generate error monitoring tool details"""
        
        if not matches:
            return ["No error monitoring tools found"]
        
        details = [f"Found {len(matches)} error monitoring tool implementations"]
        
        # Identify specific tools
        tools_found = []
        for match in matches:
            match_text = match['match'].lower()
            if 'sentry' in match_text:
                tools_found.append('Sentry')
            elif 'rollbar' in match_text:
                tools_found.append('Rollbar')
            elif 'bugsnag' in match_text:
                tools_found.append('Bugsnag')
            elif 'airbrake' in match_text:
                tools_found.append('Airbrake')
        
        if tools_found:
            unique_tools = list(set(tools_found))
            details.append(f"Tools detected: {', '.join(unique_tools)}")
        
        # Add technology detection details
        if detected_technologies:
            details.append("\n📊 Detected Technologies:")
            for category, techs in detected_technologies.items():
                if techs:
                    details.append(f"  {category.title()}: {', '.join(techs)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on error monitoring findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations() 
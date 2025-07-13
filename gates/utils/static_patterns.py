"""
Static Pattern Library for Hard Gate Validation
Comprehensive technology-specific patterns as secondary validation
"""

STATIC_PATTERN_LIBRARY = {
    "STRUCTURED_LOGS": {
        "java": [
            # More flexible logger patterns to catch real-world variations
            r'\b\w*logger\w*\.(info|debug|error|warn|trace|fatal)',
            r'\b\w*log\w*\.(info|debug|error|warn|trace|fatal)', 
            r'\bLogger\.(getLogger|info|debug|error|warn|trace)',
            r'\bLoggerFactory\.getLogger',
            r'\.getLogger\(',
            r'getLogger\(',
            # Configuration patterns
            r'<encoder.*class=.*JsonEncoder.*>',
            r'<appender.*class=.*ConsoleAppender.*>',
            r'<appender.*class=.*FileAppender.*>',
            r'logback\.xml',
            r'log4j2\.xml',
            r'log4j\.properties',
            # Framework-specific patterns
            r'@Slf4j',
            r'slf4j',
            r'logback'
        ],
        "csharp": [
            # More flexible .NET logging patterns
            r'\b\w*[Ll]og\w*\.(Information|Debug|Error|Warning|Critical|Trace|Fatal)',
            r'\b\w*[Ll]ogger\w*\.(Information|Debug|Error|Warning|Critical|Trace|Fatal)',
            r'Log\.Logger\s*=\s*new\s+LoggerConfiguration\(\)',
            r'WriteTo\.Console\(\)',
            r'WriteTo\.File\(\)',
            r'AddSerilog\(\)',
            r'AddConsole\(\)',
            r'AddLogging\(\)',
            r'appsettings\.json.*Logging',
            r'ILogger<',
            r'ILoggerFactory',
            r'CreateLogger\('
        ],
        "python": [
            # More flexible Python logging patterns
            r'\b\w*log\w*\.(info|debug|error|warning|critical|exception)',
            r'\b\w*logger\w*\.(info|debug|error|warning|critical|exception)',
            r'logging\.(getLogger|info|debug|error|warning|critical)',
            r'getLogger\(',
            r'structlog\.',
            r'loguru\.',
            r'python-json-logger',
            r'\.log\(',
            r'logging\.basicConfig',
            r'logging\.config'
        ],
        "javascript": [
            # More flexible JavaScript logging patterns
            r'\b\w*log\w*\.(log|info|debug|error|warn|trace)',
            r'\b\w*logger\w*\.(log|info|debug|error|warn|trace)',
            r'console\.(log|info|debug|error|warn|trace)',
            r'winston\.',
            r'bunyan\.',
            r'pino\.',
            r'log4js\.',
            r'debug\(',
            r'createLogger\(',
            r'getLogger\('
        ],
        "typescript": [
            # More flexible TypeScript logging patterns
            r'\b\w*log\w*\.(log|info|debug|error|warn|trace)',
            r'\b\w*logger\w*\.(log|info|debug|error|warn|trace)',
            r'console\.(log|info|debug|error|warn|trace)',
            r'winston\.',
            r'bunyan\.',
            r'pino\.',
            r'log4js\.',
            r'debug\(',
            r'createLogger\(',
            r'getLogger\('
        ],
        "standard_logging": [
            # Generic flexible patterns for any language
            r'\b\w*log\w*\.(info|debug|error|warning|critical|warn|trace|fatal)',
            r'\b\w*logger\w*\.(info|debug|error|warning|critical|warn|trace|fatal)',
            r'console\.(log|info|debug|error|warn)',
            r'getLogger\(',
            r'createLogger\(',
            r'\.log\('
        ],
        "structured_logging": [
            # Structured logging patterns
            r'\b\w*logger\w*\.\w+\s*\([^)]*\{[^}]*\}',
            r'JSON\.stringify',
            r'structlog\.get_logger',
            r'structured.*log',
            r'json.*log'
        ],
        "framework_logging": [
            # Framework-specific logging patterns
            r'app\.logger',
            r'flask\.current_app\.logger',
            r'django\.core\.logging',
            r'winston',
            r'bunyan',
            r'pino',
            r'log4js',
            r'Serilog',
            r'NLog',
            r'logback',
            r'slf4j'
        ]
    },
    
    "AVOID_LOGGING_SECRETS": {
        "java": [
            r'(?i)\b(logger|log|slf4jLogger|log4jLogger|auditLogger)\.(info|debug|warn|error|trace|fatal)\s*\(\s*".*?(password|secret|token|apikey|access[_-]?key|auth(entication)?|credential).*?"\s*(?:,|\+)',
            r'(?i)\b(logger|log|slf4jLogger|log4jLogger|auditLogger)\.(info|debug|warn|error|trace|fatal)\s*\(\s*".*?"\s*,\s*.*(password|secret|token|apikey|credential).*?\)',
            r'(?i)"(password|secret|token|apikey|access[_-]?key)"\s*[:=]\s*["\'][^"\']{6,}["\']',
            r'(?i)\bSystem\.out\.println\s*\(\s*".*?(password|token|secret).*?"\s*(?:,|\+)',
            r'(?i)\b(logger|log)\.(info|debug|warn|error|trace)\s*\(\s*".*?(mongodb|mysql|postgresql|oracle|mssql):\/\/[^:]+:[^@]+@[^"\']+["\']?'
        ],
        "javascript": [
            r'(?i)\b(console|logger|log|winston|pino|bunyan|debug|log4js|loggly|logdna|logrocket)\.(log|info|debug|warn|error|trace)\s*\(\s*["\'\`].*?(password|secret|token|apikey|access[_-]?key|credential).*?["\'\`]\s*(?:,|\+)',
            r'(?i)\b(console|logger|log|winston|pino|bunyan|debug)\.(log|info|debug|warn|error)\s*\(\s*.*?(password|secret|token|apikey|access[_-]?key).*?'
        ],
        "typescript": [
            r'(?i)\b(console|logger|log|winston|pino|bunyan|debug|log4js|loggly|logdna|logrocket)\.(log|info|debug|warn|error|trace)\s*\(\s*["\'\`].*?(password|secret|token|apikey|access[_-]?key|credential).*?["\'\`]\s*(?:,|\+)',
            r'(?i)\b(console|logger|log|winston|pino|bunyan|debug)\.(log|info|debug|warn|error)\s*\(\s*.*?(password|secret|token|apikey|access[_-]?key).*?'
        ],
        "python": [
            r'(?i)\b(logging|logger|log|audit_logger|app_logger)\.(debug|info|warning|warn|error|critical|exception)\s*\(\s*f?["\'].*?(password|secret|token|apikey|access[_-]?key|credential).*?["\'].*?\)',
            r'(?i)\bprint\s*\(\s*f?["\'].*?(password|secret|token|apikey|access[_-]?key|credential).*?["\']',
            r'(?i)\bloguru\.logger\.(debug|info|warning|error|critical)\s*\(\s*f?["\'].*?(password|token|secret).*?["\']'
        ],
        "csharp": [
            r'(?i)\b(_logger|logger|log|logFactory|serilog|nlog)\.(LogInformation|LogDebug|LogWarning|LogError|LogCritical|LogTrace|Information|Debug|Warning|Error|Trace|Fatal)\s*\(\s*".*?(password|secret|token|apikey|credential).*?"',
            r'(?i)\bConsole\.Write(Line)?\s*\(\s*".*?(password|token|secret).*?"'
        ],
        "all_languages": [
            r'(?i)"(password|secret|token|apikey|credential)"\s*[:=]\s*["\'][^"\']{6,}["\']',
            r'(?i)\b(?:sk_live_|pk_live_|sk_test_|pk_test_)[A-Za-z0-9]{20,}\b',
            r'(?i)\bgithub_pat_[A-Za-z0-9_]{20,}\b',
            r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
            r'-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
            r'-----BEGIN\s+CERTIFICATE-----',
            r'-----END\s+CERTIFICATE-----'
        ]
    },
    
    "AUDIT_TRAIL": {
        "java": [
            # More flexible logger patterns to catch real-world variations
            r'\b\w*logger\w*\.(info|debug|error|warn|trace|fatal)',
            r'\b\w*log\w*\.(info|debug|error|warn|trace|fatal)', 
            r'\bLogger\.(getLogger|info|debug|error|warn|trace)',
            r'\bLoggerFactory\.getLogger',
            r'\.getLogger\(',
            r'getLogger\(',
            # Configuration patterns
            r'<encoder.*class=.*JsonEncoder.*>',
            r'<appender.*class=.*ConsoleAppender.*>',
            r'<appender.*class=.*FileAppender.*>',
            r'logback\.xml',
            r'log4j2\.xml',
            r'log4j\.properties',
            # Audit-specific patterns
            r'audit.*log',
            r'audit.*trail',
            r'business.*log',
            r'transaction.*log'
        ],
        "csharp": [
            # More flexible .NET logging patterns
            r'\b\w*[Ll]og\w*\.(Information|Debug|Error|Warning|Critical|Trace|Fatal)',
            r'\b\w*[Ll]ogger\w*\.(Information|Debug|Error|Warning|Critical|Trace|Fatal)',
            r'Log\.Logger\s*=\s*new\s+LoggerConfiguration\(\)',
            r'WriteTo\.Console\(\)',
            r'WriteTo\.File\(\)',
            r'AddSerilog\(\)',
            r'AddConsole\(\)',
            r'AddLogging\(\)',
            r'appsettings\.json.*Logging',
            r'ILogger<',
            r'ILoggerFactory',
            r'CreateLogger\('
        ],
        "python": [
            # More flexible Python logging patterns
            r'\b\w*log\w*\.(info|debug|error|warning|critical|exception)',
            r'\b\w*logger\w*\.(info|debug|error|warning|critical|exception)',
            r'logging\.(getLogger|info|debug|error|warning|critical)',
            r'getLogger\(',
            r'structlog\.',
            r'loguru\.',
            r'python-json-logger',
            r'\.log\(',
            r'logging\.basicConfig',
            r'logging\.config'
        ],
        "javascript": [
            # More flexible JavaScript logging patterns
            r'\b\w*log\w*\.(log|info|debug|error|warn|trace)',
            r'\b\w*logger\w*\.(log|info|debug|error|warn|trace)',
            r'console\.(log|info|debug|error|warn|trace)',
            r'winston\.',
            r'bunyan\.',
            r'pino\.',
            r'log4js\.',
            r'debug\(',
            r'createLogger\(',
            r'getLogger\('
        ],
        "typescript": [
            # More flexible TypeScript logging patterns
            r'\b\w*log\w*\.(log|info|debug|error|warn|trace)',
            r'\b\w*logger\w*\.(log|info|debug|error|warn|trace)',
            r'console\.(log|info|debug|error|warn|trace)',
            r'winston\.',
            r'bunyan\.',
            r'pino\.',
            r'log4js\.',
            r'debug\(',
            r'createLogger\(',
            r'getLogger\('
        ]
    },
    
    "CORRELATION_ID": {
        "java": [
            r'MDC\.put\(.*correlationId.*\)',
            r'MDC\.put\(.*requestId.*\)',
            r'MDC\.put\(.*transactionId.*\)',
            r'MDC\.put\(.*traceId.*\)',
            r'X-Request-ID',
            r'X-Correlation-ID',
            r'X-Transaction-ID',
            r'X-Trace-ID',
            r'@Bean.*HandlerInterceptor',
            r'HandlerInterceptorAdapter',
            r'OncePerRequestFilter',
            r'request.getHeader\(.*X-Request-ID.*\)',
            r'request.getHeader\(.*X-Correlation-ID.*\)'
        ],
        "csharp": [
            r'context\.TraceIdentifier',
            r'HttpContext\.TraceIdentifier',
            r'Activity\.Current\.Id',
            r'AddCorrelationId',
            r'X-Request-ID',
            r'X-Correlation-ID',
            r'X-Transaction-ID',
            r'X-Trace-ID',
            r'logger\.Log.*correlationId',
            r'logger\.Log.*requestId',
            r'logger\.Log.*traceId'
        ],
        "python": [
            r'request\.headers\.get\(.*X-Request-ID.*\)',
            r'request\.headers\.get\(.*X-Correlation-ID.*\)',
            r'request\.headers\.get\(.*X-Transaction-ID.*\)',
            r'request\.headers\.get\(.*X-Trace-ID.*\)',
            r'request_id',
            r'correlation_id',
            r'transaction_id',
            r'trace_id',
            r'logging\.LoggerAdapter',
            r'structlog.*correlation_id',
            r'structlog.*request_id',
            r'structlog.*trace_id'
        ],
        "javascript": [
            r'req\.headers\["x-request-id"\]',
            r'req\.headers\["x-correlation-id"\]',
            r'req\.headers\["x-transaction-id"\]',
            r'req\.headers\["x-trace-id"\]',
            r'correlationId',
            r'requestId',
            r'transactionId',
            r'traceId',
            r'winston.*correlationId',
            r'winston.*requestId',
            r'winston.*traceId'
        ],
        "typescript": [
            r'req\.headers\["x-request-id"\]',
            r'req\.headers\["x-correlation-id"\]',
            r'req\.headers\["x-transaction-id"\]',
            r'req\.headers\["x-trace-id"\]',
            r'correlationId',
            r'requestId',
            r'transactionId',
            r'traceId',
            r'winston.*correlationId',
            r'winston.*requestId',
            r'winston.*traceId'
        ]
    },
    
    "LOG_API_CALLS": {
        "java": [
            r'@RequestMapping',
            r'@GetMapping',
            r'@PostMapping',
            r'@PutMapping',
            r'@DeleteMapping',
            r'RestTemplate',
            r'WebClient',
            r'logger\.(info|debug|error|warn)\s*\(.*(request|response)',
            r'\blogger\.(info|debug|error|warn|trace)'
        ],
        "csharp": [
            r'\[HttpGet\]',
            r'\[HttpPost\]',
            r'\[HttpPut\]',
            r'\[HttpDelete\]',
            r'HttpClient',
            r'ILogger.*Log.*(request|response)'
        ],
        "python": [
            r'@app\.route',
            r'@router\.get',
            r'@router\.post',
            r'requests\.',
            r'aiohttp\.',
            r'logging\.(info|debug|error|warning|critical)\s*\(.*(request|response)',
            r'log(?:ger)?\.info\(.*request.*',
            r'log(?:ger)?\.info\(.*response.*'
        ],
        "javascript": [
            r'app\.get\(',
            r'app\.post\(',
            r'app\.put\(',
            r'app\.delete\(',
            r'axios\.',
            r'fetch\(',
            r'console\.(log|info|debug|error)\s*\(.*(request|response)'
        ],
        "typescript": [
            r'app\.get\(',
            r'app\.post\(',
            r'app\.put\(',
            r'app\.delete\(',
            r'axios\.',
            r'fetch\(',
            r'console\.(log|info|debug|error)\s*\(.*(request|response)'
        ]
    },
    
    "LOG_APPLICATION_MESSAGES": {
        "java": [
            # More flexible logger patterns to catch real-world variations
            r'\b\w*logger\w*\.(info|debug|error|warn|trace|fatal)',
            r'\b\w*log\w*\.(info|debug|error|warn|trace|fatal)', 
            r'\bLogger\.(getLogger|info|debug|error|warn|trace)',
            r'\bLoggerFactory\.getLogger',
            r'\.getLogger\(',
            r'getLogger\(',
            # Configuration patterns
            r'<encoder.*class=.*JsonEncoder.*>',
            r'<appender.*class=.*ConsoleAppender.*>',
            r'<appender.*class=.*FileAppender.*>',
            r'logback\.xml',
            r'log4j2\.xml',
            r'log4j\.properties',
            # Application-specific patterns
            r'application.*log',
            r'app.*log',
            r'business.*event',
            r'state.*change'
        ],
        "csharp": [
            # More flexible .NET logging patterns
            r'\b\w*[Ll]og\w*\.(Information|Debug|Error|Warning|Critical|Trace|Fatal)',
            r'\b\w*[Ll]ogger\w*\.(Information|Debug|Error|Warning|Critical|Trace|Fatal)',
            r'Log\.Logger\s*=\s*new\s+LoggerConfiguration\(\)',
            r'WriteTo\.Console\(\)',
            r'WriteTo\.File\(\)',
            r'AddSerilog\(\)',
            r'AddConsole\(\)',
            r'AddLogging\(\)',
            r'appsettings\.json.*Logging',
            r'ILogger<',
            r'ILoggerFactory',
            r'CreateLogger\('
        ],
        "python": [
            # More flexible Python logging patterns
            r'\b\w*log\w*\.(info|debug|error|warning|critical|exception)',
            r'\b\w*logger\w*\.(info|debug|error|warning|critical|exception)',
            r'logging\.(getLogger|info|debug|error|warning|critical)',
            r'getLogger\(',
            r'structlog\.',
            r'loguru\.',
            r'python-json-logger',
            r'\.log\(',
            r'logging\.basicConfig',
            r'logging\.config'
        ],
        "javascript": [
            # More flexible JavaScript logging patterns
            r'\b\w*log\w*\.(log|info|debug|error|warn|trace)',
            r'\b\w*logger\w*\.(log|info|debug|error|warn|trace)',
            r'console\.(log|info|debug|error|warn|trace)',
            r'winston\.',
            r'bunyan\.',
            r'pino\.',
            r'log4js\.',
            r'debug\(',
            r'createLogger\(',
            r'getLogger\('
        ],
        "typescript": [
            # More flexible TypeScript logging patterns
            r'\b\w*log\w*\.(log|info|debug|error|warn|trace)',
            r'\b\w*logger\w*\.(log|info|debug|error|warn|trace)',
            r'console\.(log|info|debug|error|warn|trace)',
            r'winston\.',
            r'bunyan\.',
            r'pino\.',
            r'log4js\.',
            r'debug\(',
            r'createLogger\(',
            r'getLogger\('
        ]
    },
    
    "UI_ERRORS": {
        "javascript": [
            r'window\.onerror',
            r'console\.error',
            r'Sentry\.captureException',
            r'ErrorBoundary',
            r'try\s*{.*}\s*catch\s*\('
        ],
        "typescript": [
            r'window\.onerror',
            r'console\.error',
            r'Sentry\.captureException',
            r'ErrorBoundary',
            r'try\s*{.*}\s*catch\s*\('
        ]
    },
    
    "RETRY_LOGIC": {
        "java": [
            r'@Retryable',
            r'RetryTemplate',
            r'try\s*{.*}\s*catch\s*\('
        ],
        "csharp": [
            r'Polly',
            r'RetryPolicy',
            r'try\s*{.*}\s*catch\s*\('
        ],
        "python": [
            r'@retry',
            r'tenacity',
            r'retrying',
            r'try:',
            r'except '
        ],
        "javascript": [
            r'axios-retry',
            r'retry\(',
            r'try\s*{.*}\s*catch\s*\('
        ],
        "typescript": [
            r'axios-retry',
            r'retry\(',
            r'try\s*{.*}\s*catch\s*\('
        ]
    },
    
    "TIMEOUTS": {
        "java": [
            r'RestTemplateBuilder.*setConnectTimeout',
            r'HttpClientBuilder.*setConnectionTimeToLive',
            r'WebClient.*responseTimeout',
            r'DataSource.*setLoginTimeout',
            r'HikariConfig.*setConnectionTimeout'
        ],
        "csharp": [
            r'HttpClient.Timeout',
            r'SqlConnection.ConnectionTimeout',
            r'Task.Delay'
        ],
        "python": [
            r'requests\..*timeout=',
            r'aiohttp\..*timeout=',
            r'pymysql.connect.*connect_timeout=',
            r'psycopg2.connect.*connect_timeout='
        ],
        "javascript": [
            r'axios\.timeout',
            r'fetch\(.*,\s*\{.*timeout:',
            r'setTimeout\('
        ],
        "typescript": [
            r'axios\.timeout',
            r'fetch\(.*,\s*\{.*timeout:',
            r'setTimeout\('
        ]
    },
    
    "THROTTLING": {
        "java": [
            r'Bucket4j',
            r'Resilience4j.*RateLimiter',
            r'@RateLimiter',
            r'RateLimiterConfig'
        ],
        "csharp": [
            r'AspNetCoreRateLimit',
            r'RateLimiter',
            r'IAsyncRateLimitPolicy'
        ],
        "python": [
            r'ratelimit',
            r'limits',
            r'flask-limiter'
        ],
        "javascript": [
            r'express-rate-limit',
            r'rate-limiter-flexible',
            r'bottleneck'
        ],
        "typescript": [
            r'express-rate-limit',
            r'rate-limiter-flexible',
            r'bottleneck'
        ]
    },
    
    "CIRCUIT_BREAKERS": {
        "java": [
            r'@CircuitBreaker',
            r'HystrixCommand',
            r'Resilience4j.*CircuitBreaker'
        ],
        "csharp": [
            r'Polly.CircuitBreaker',
            r'CircuitBreakerPolicy'
        ],
        "python": [
            r'pybreaker',
            r'circuitbreaker'
        ],
        "javascript": [
            r'opossum',
            r'circuit-breaker-js'
        ],
        "typescript": [
            r'opossum',
            r'circuit-breaker-js'
        ]
    },
    
    "ERROR_LOGS": {
        "java": [
            r'@ControllerAdvice',
            r'@ExceptionHandler',
            r'logger\.error\(',
            r'try\s*{.*}\s*catch\s*\('
        ],
        "csharp": [
            r'UseExceptionHandler',
            r'ILogger.*LogError',
            r'try\s*{.*}\s*catch\s*\('
        ],
        "python": [
            r'logging\.error\(',
            r'try:',
            r'except ',
            r'log(?:ger)?\.error\(.*(?:exc_info=True|traceback|exception)',
            r'log(?:ger)?\.exception\(',
            r'\btraceback\.format_exc\(\)',
            r'\btraceback\.print_exc\(\)'
        ],
        "javascript": [
            r'console\.error\(',
            r'try\s*{.*}\s*catch\s*\('
        ],
        "typescript": [
            r'console\.error\(',
            r'try\s*{.*}\s*catch\s*\('
        ]
    },
    
    "HTTP_CODES": {
        "java": [
            r'@ExceptionHandler',
            r'ResponseEntity\.status\(HttpStatus\.',
            r'throw new ResponseStatusException'
        ],
        "csharp": [
            r'StatusCode\(',
            r'return BadRequest\(',
            r'return NotFound\(',
            r'return StatusCode\('
        ],
        "python": [
            r'abort\(',
            r'return jsonify.*status=',
            r'make_response\(',
            r'status_code\s*=\s*(?:200|201|202|204|301|302|304|400|401|403|404|405|409|422|429|500|502|503|504)',
            r'HTTPStatus\.(?:OK|CREATED|ACCEPTED|NO_CONTENT|BAD_REQUEST|UNAUTHORIZED|FORBIDDEN|NOT_FOUND|INTERNAL_SERVER_ERROR)'
        ],
        "javascript": [
            r'res\.status\(',
            r'res\.sendStatus\(',
            r'next\(createError'
        ],
        "typescript": [
            r'res\.status\(',
            r'res\.sendStatus\(',
            r'next\(createError'
        ]
    },
    
    "UI_ERROR_TOOLS": {
        "javascript": [
            r'Sentry\.init\(',
            r'trackError\(',
            r'datadogRum\.init\(',
            r'bugsnag\.start\('
        ],
        "typescript": [
            r'Sentry\.init\(',
            r'trackError\(',
            r'datadogRum\.init\(',
            r'bugsnag\.start\('
        ]
    },
    
    "AUTOMATED_TESTS": {
        "java": [
            r'@Test',
            r'JUnit',
            r'TestNG',
            r'Mockito'
        ],
        "csharp": [
            r'\[TestMethod\]',
            r'\[Fact\]',
            r'\[Theory\]',
            r'NUnit',
            r'Xunit'
        ],
        "python": [
            r'def test_',
            r'pytest',
            r'unittest',
            r'nose'
        ],
        "javascript": [
            r'describe\(',
            r'it\(',
            r'jest',
            r'mocha',
            r'chai'
        ],
        "typescript": [
            r'describe\(',
            r'it\(',
            r'jest',
            r'mocha',
            r'chai'
        ]
    }
}

def get_static_patterns_for_gate(gate_name: str, primary_technologies: list) -> list:
    """
    Get static patterns for a specific gate and technology stack
    
    Args:
        gate_name: Name of the gate (e.g., 'STRUCTURED_LOGS')
        primary_technologies: List of primary technologies detected
    
    Returns:
        List of regex patterns for the gate and technologies
    """
    patterns = []
    
    if gate_name not in STATIC_PATTERN_LIBRARY:
        return patterns
    
    gate_patterns = STATIC_PATTERN_LIBRARY[gate_name]
    
    # Add patterns for detected technologies
    for tech in primary_technologies:
        tech_key = tech.lower()
        if tech_key in gate_patterns:
            patterns.extend(gate_patterns[tech_key])
    
    # Add generic patterns if available
    for generic_key in ['standard_logging', 'structured_logging', 'framework_logging', 'all_languages']:
        if generic_key in gate_patterns:
            patterns.extend(gate_patterns[generic_key])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for pattern in patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)
    
    return unique_patterns

def get_all_static_patterns_for_gate(gate_name: str) -> dict:
    """
    Get all static patterns for a gate organized by technology
    
    Args:
        gate_name: Name of the gate
    
    Returns:
        Dictionary with technology as key and patterns as values
    """
    if gate_name not in STATIC_PATTERN_LIBRARY:
        return {}
    
    return STATIC_PATTERN_LIBRARY[gate_name]

def get_supported_technologies() -> list:
    """
    Get list of all supported technologies in the static pattern library
    
    Returns:
        List of supported technology names
    """
    technologies = set()
    
    for gate_patterns in STATIC_PATTERN_LIBRARY.values():
        for tech in gate_patterns.keys():
            if tech not in ['standard_logging', 'structured_logging', 'framework_logging', 'all_languages']:
                technologies.add(tech)
    
    return sorted(list(technologies))

def get_pattern_statistics() -> dict:
    """
    Get statistics about the static pattern library
    
    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_gates': len(STATIC_PATTERN_LIBRARY),
        'total_technologies': len(get_supported_technologies()),
        'total_patterns': 0,
        'patterns_by_gate': {},
        'patterns_by_technology': {}
    }
    
    for gate_name, gate_patterns in STATIC_PATTERN_LIBRARY.items():
        gate_pattern_count = 0
        for tech, patterns in gate_patterns.items():
            pattern_count = len(patterns)
            gate_pattern_count += pattern_count
            stats['total_patterns'] += pattern_count
            
            if tech not in stats['patterns_by_technology']:
                stats['patterns_by_technology'][tech] = 0
            stats['patterns_by_technology'][tech] += pattern_count
        
        stats['patterns_by_gate'][gate_name] = gate_pattern_count
    
    return stats  